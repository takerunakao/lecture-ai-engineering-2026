"""Day5: cosine top-k and a query-aware, bounded page/term graph retriever.

Both methods use the same 214 course pages, embedding model, question text, and final page
budget. ``baseline`` follows the course cosine-distance ordering. We decode
the supplied float32 SQLite vectors with the standard library; double-precision
accumulation can differ slightly from sqlite-vec's floating-point arithmetic.

``graph`` keeps the first vector hit, then reranks a bounded pool. The pool
contains the vector top-k and graph paths from the first three vector hits:
up to two same-document next_page edges, or page -> term -> page. A term is
expanded only when one of its aliases occurs in the query and it occurs on no
more than 32 corpus pages. Thus a ubiquitous term cannot pull in the entire
corpus. contains and related_term edges are deliberately not traversed.

Greedy selection combines semantic relevance, newly covered query terms, and
redundancy with already selected pages. The final page count is unchanged.
The 24-candidate pool and rank-50 expansion bound are fixed design choices,
not learned on the evaluation questions. No expected answer or gold page ID
is accepted by this module. Trace paths explain retrieval, not truthfulness.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import unicodedata


DOCUMENT_COUNTS = {"lec01-main": 73, "lec02-main": 70, "lec03-main": 71}
DIMENSIONS = 768
PAGE_COUNT = sum(DOCUMENT_COUNTS.values())
SEED_COUNT = 3
MAX_HOPS = 2
MAX_TERM_DEGREE = 32
MAX_CANDIDATES = 24
MAX_EXPANSION_RANK = 50
PAGE_FIELDS = (
    "page_id", "document_id", "lecture", "document_title", "section", "title",
    "page", "content",
)


def _normal_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def alias_in_query(alias: str, query: str) -> bool:
    """Match Latin aliases as words, while allowing Japanese substring matches.

    In particular, LoRA does not match QLoRA, nor does API match capitalized
    English words containing those letters. NFKC also handles fullwidth Latin.
    """
    alias = _normal_text(alias).strip()
    query = _normal_text(query)
    if not alias:
        return False
    left = r"(?<![a-z0-9_])" if re.match(r"[a-z0-9_]", alias[0]) else ""
    right = r"(?![a-z0-9_])" if re.match(r"[a-z0-9_]", alias[-1]) else ""
    return re.search(left + re.escape(alias) + right, query) is not None


def _unit_vector(values, *, as_float32: bool = False) -> tuple[float, ...]:
    try:
        vector = tuple(float(v) for v in values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Embedding must contain finite numbers.") from exc
    if len(vector) != DIMENSIONS or not all(math.isfinite(v) for v in vector):
        raise ValueError(f"Embedding must contain {DIMENSIONS} finite numbers.")
    length = math.sqrt(math.fsum(v * v for v in vector))
    if not math.isfinite(length) or length <= 0:
        raise ValueError("Embedding must have a finite, nonzero norm.")
    vector = tuple(v / length for v in vector)
    if as_float32:
        # The original course serializes the normalized query as float32.
        vector = struct.unpack(f"<{DIMENSIONS}f", struct.pack(f"<{DIMENSIONS}f", *vector))
        length = math.sqrt(math.fsum(v * v for v in vector))
        vector = tuple(v / length for v in vector)
    return vector


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return min(1.0, max(-1.0, math.fsum(x * y for x, y in zip(a, b))))


class Corpus:
    """Read and validate the pinned course corpus. Construction makes no API call."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        source = json.loads((self.data_dir / "lectures.json").read_text(encoding="utf-8"))
        self.pages: dict[str, dict] = {}
        documents_seen = set()
        for document in source:
            document_id = document["id"]
            if document_id not in DOCUMENT_COUNTS:
                continue
            if document_id in documents_seen:
                raise ValueError(f"Duplicate document: {document_id}")
            documents_seen.add(document_id)
            for section in document["content"]:
                for page in section["content"]:
                    page_id = page["id"]
                    if page_id in self.pages:
                        raise ValueError(f"Duplicate page: {page_id}")
                    if not isinstance(page["content"], str) or not page["content"].strip():
                        raise ValueError(f"Missing page content: {page_id}")
                    self.pages[page_id] = {
                        "page_id": page_id, "document_id": document_id,
                        "lecture": int(document_id[3:5]),
                        "document_title": document["title"],
                        "section": section["section"], "title": page["title"],
                        "page": page["page"], "content": page["content"],
                    }
        counts = dict(Counter(p["document_id"] for p in self.pages.values()))
        if counts != DOCUMENT_COUNTS or len(self.pages) != PAGE_COUNT:
            raise ValueError(f"Expected the 214-page course corpus; found {counts}.")
        for document_id, count in DOCUMENT_COUNTS.items():
            numbers = [p["page"] for p in self.pages.values() if p["document_id"] == document_id]
            if sorted(numbers) != list(range(1, count + 1)):
                raise ValueError(f"Page numbers are missing or duplicated: {document_id}")

        database = self.data_dir / "index.sqlite3"
        if not database.is_file():
            raise FileNotFoundError(f"Search database is missing: {database}")
        self.vectors: dict[str, tuple[float, ...]] = {}
        connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            columns = {r[1] for r in connection.execute("PRAGMA table_info(chunks)")}
            if not set(PAGE_FIELDS + ("embedding",)).issubset(columns):
                raise ValueError("Search database has an unexpected chunks schema.")
            for row in connection.execute("SELECT " + ", ".join(PAGE_FIELDS) + ", embedding FROM chunks"):
                page_id = row["page_id"]
                if page_id not in self.pages or page_id in self.vectors:
                    raise ValueError(f"Unexpected or duplicate database page: {page_id}")
                if any(row[field] != self.pages[page_id][field] for field in PAGE_FIELDS):
                    raise ValueError(f"Database and source page differ: {page_id}")
                blob = row["embedding"]
                if not isinstance(blob, bytes) or len(blob) != DIMENSIONS * 4:
                    raise ValueError(f"Invalid embedding dimensions: {page_id}")
                self.vectors[page_id] = _unit_vector(struct.unpack(f"<{DIMENSIONS}f", blob))
        finally:
            connection.close()
        if self.vectors.keys() != self.pages.keys():
            raise ValueError("Database page IDs do not match the source corpus.")

        graph = json.loads((self.data_dir / "graph.json").read_text(encoding="utf-8"))
        nodes = {}
        for node in graph["nodes"]:
            if node["id"] in nodes:
                raise ValueError(f"Duplicate graph node: {node['id']}")
            nodes[node["id"]] = node
        if any(page_id not in nodes or nodes[page_id]["kind"] != "page" for page_id in self.pages):
            raise ValueError("Graph is missing corpus page nodes.")
        self.terms = {key: node for key, node in nodes.items() if node["kind"] == "term"}
        self.page_terms = defaultdict(set)
        self.term_pages = defaultdict(set)
        self.adjacent_pages = defaultdict(set)
        self.rejected_cross_document_adjacency = 0
        for edge in graph["edges"]:
            a, b, relation = edge["source"], edge["target"], edge["relation"]
            if a not in nodes or b not in nodes:
                raise ValueError("Graph edge references a missing node.")
            if relation == "next_page" and a in self.pages and b in self.pages:
                pa, pb = self.pages[a], self.pages[b]
                if pa["document_id"] != pb["document_id"]:
                    self.rejected_cross_document_adjacency += 1
                    continue
                if abs(pa["page"] - pb["page"]) != 1:
                    raise ValueError(f"next_page edge is not between adjacent PDF pages: {a}, {b}")
                self.adjacent_pages[a].add(b)
                self.adjacent_pages[b].add(a)
            elif relation == "mentions":
                if a in self.pages and b in self.terms:
                    page_id, term_id = a, b
                elif b in self.pages and a in self.terms:
                    page_id, term_id = b, a
                else:
                    continue
                self.page_terms[page_id].add(term_id)
                self.term_pages[term_id].add(page_id)

    def rank(self, query_vector: list[float]) -> list[dict]:
        """Return every corpus page ordered by cosine distance then page ID."""
        vector = _unit_vector(query_vector, as_float32=True)
        result = [
            {**page, "distance": 1.0 - _cosine(vector, self.vectors[page_id])}
            for page_id, page in self.pages.items()
        ]
        return sorted(result, key=lambda item: (item["distance"], item["page_id"]))

    def _query_terms(self, query: str) -> tuple[dict[str, dict], list[dict]]:
        active, ignored = {}, []
        for term_id, term in sorted(self.terms.items()):
            aliases = list(term.get("aliases", [])) + [term["title"]]
            if not any(alias_in_query(alias, query) for alias in aliases):
                continue
            degree = len(self.term_pages[term_id])
            info = {"term_id": term_id, "title": term["title"], "degree": degree}
            if not degree or degree > MAX_TERM_DEGREE:
                ignored.append({**info, "reason": "no_corpus_pages" if not degree else "high_degree"})
            else:
                active[term_id] = {**info, "weight": math.log((PAGE_COUNT + 1) / (degree + 1))}
        return active, ignored

    def retrieve(self, query: str, query_vector: list[float], method: str, top_k: int = 5) -> dict:
        """Retrieve exactly top_k unique pages; no answer/gold information is used."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a nonempty string.")
        if method not in {"baseline", "graph"}:
            raise ValueError(f"Unknown retrieval method: {method}")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 10:
            raise ValueError("top_k must be an integer between 1 and 10.")
        ranked = self.rank(query_vector)
        ranked_by_id = {p["page_id"]: p for p in ranked}
        ranks = {p["page_id"]: i + 1 for i, p in enumerate(ranked)}
        baseline_ids = [p["page_id"] for p in ranked[:top_k]]
        if method == "baseline":
            pages = [
                {**ranked_by_id[page_id], "provenance": {
                    "kind": "vector_top_k", "vector_rank": ranks[page_id],
                    "paths": [{"nodes": [page_id], "relations": [], "hops": 0}],
                }} for page_id in baseline_ids
            ]
            return {"method": method, "pages": pages, "trace": {
                "algorithm": "course_cosine_top_k_stdlib", "corpus_size": PAGE_COUNT,
                "top_k": top_k, "selected_page_ids": baseline_ids,
                "distance_note": "Cosine distance is not a probability of correctness.",
            }}

        query_terms, ignored_terms = self._query_terms(query)
        total_weight = sum(info["weight"] for info in query_terms.values())
        seed_ids = [p["page_id"] for p in ranked[:min(SEED_COUNT, top_k)]]
        routes: dict[str, list[dict]] = defaultdict(list)
        for page_id in baseline_ids:
            routes[page_id].append({"kind": "vector_top_k", "nodes": [page_id], "relations": [], "hops": 0})

        def add_route(page_id: str, route: dict) -> None:
            if ranks[page_id] <= MAX_EXPANSION_RANK and route not in routes[page_id]:
                routes[page_id].append(route)

        for seed in seed_ids:
            queue = deque([(seed, [seed])])
            visited = {seed}
            while queue:
                current, path = queue.popleft()
                if len(path) - 1 >= MAX_HOPS:
                    continue
                for neighbor in sorted(self.adjacent_pages[current]):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    route = path + [neighbor]
                    add_route(neighbor, {"kind": "adjacent_page", "seed": seed,
                                        "nodes": route, "relations": ["next_page"] * (len(route) - 1),
                                        "hops": len(route) - 1})
                    queue.append((neighbor, route))
            for term_id in sorted(self.page_terms[seed] & query_terms.keys()):
                for page_id in sorted(self.term_pages[term_id]):
                    if page_id == seed:
                        continue
                    add_route(page_id, {"kind": "query_term", "seed": seed,
                                        "nodes": [seed, term_id, page_id],
                                        "relations": ["mentions", "mentions"], "hops": 2})

        def coverage(page_id: str, covered: set[str]) -> float:
            if not total_weight:
                return 0.0
            new_terms = (self.page_terms[page_id] & query_terms.keys()) - covered
            return sum(query_terms[t]["weight"] for t in new_terms) / total_weight

        candidate_ids = set(routes)
        before_cap = len(candidate_ids)
        expansion_ids = candidate_ids - set(baseline_ids)
        pool_order = sorted(expansion_ids, key=lambda p: (
            -(0.8 * (1 - ranked_by_id[p]["distance"]) + 0.2 * coverage(p, set())), ranks[p], p,
        ))
        candidate_ids = set(baseline_ids) | set(pool_order[:max(0, MAX_CANDIDATES - len(baseline_ids))])
        selected = [baseline_ids[0]]
        covered = self.page_terms[selected[0]] & query_terms.keys()
        selection = [{"step": 1, "page_id": selected[0], "kept_top_vector_hit": True,
                      "score": None, "new_query_terms": sorted(covered)}]
        while len(selected) < top_k:
            scores = {}
            for page_id in candidate_ids - set(selected):
                relevance = 1 - ranked_by_id[page_id]["distance"]
                novelty = coverage(page_id, covered)
                redundancy = max(_cosine(self.vectors[page_id], self.vectors[old]) for old in selected)
                scores[page_id] = (0.72 * relevance + 0.23 * novelty - 0.05 * redundancy,
                                   relevance, novelty, redundancy)
            winner = min(scores, key=lambda p: (-scores[p][0], ranks[p], p))
            score, relevance, novelty, redundancy = scores[winner]
            new_terms = (self.page_terms[winner] & query_terms.keys()) - covered
            selection.append({"step": len(selected) + 1, "page_id": winner,
                              "kept_top_vector_hit": False, "score": score,
                              "relevance": relevance, "new_term_coverage": novelty,
                              "redundancy": redundancy, "new_query_terms": sorted(new_terms)})
            selected.append(winner)
            covered |= new_terms

        selected_scores = {s["page_id"]: s["score"] for s in selection}
        result_pages = [
            {**ranked_by_id[page_id], "provenance": {
                "kind": "query_aware_graph", "vector_rank": ranks[page_id],
                "paths": routes[page_id], "selection_score": selected_scores[page_id],
                "matched_query_terms": sorted(self.page_terms[page_id] & query_terms.keys()),
            }} for page_id in selected
        ]
        trace_candidates = [
            {"page_id": page_id, "vector_rank": ranks[page_id],
             "distance": ranked_by_id[page_id]["distance"], "paths": routes[page_id],
             "matched_query_terms": sorted(self.page_terms[page_id] & query_terms.keys())}
            for page_id in sorted(candidate_ids, key=lambda p: (ranks[p], p))
        ]
        return {"method": method, "pages": result_pages, "trace": {
            "algorithm": "query_aware_bounded_graph_v1", "corpus_size": PAGE_COUNT,
            "top_k": top_k, "seed_page_ids": seed_ids, "baseline_top_k": baseline_ids,
            "query_terms": list(query_terms.values()), "ignored_query_terms": ignored_terms,
            "limits": {"max_hops": MAX_HOPS, "max_term_degree": MAX_TERM_DEGREE,
                       "max_candidates": MAX_CANDIDATES, "max_expansion_vector_rank": MAX_EXPANSION_RANK},
            "relations_used": ["next_page", "mentions"],
            "relations_not_used": ["contains", "related_term"],
            "candidate_count_before_cap": before_cap, "candidate_count_after_cap": len(candidate_ids),
            "rejected_cross_document_next_page_edges": self.rejected_cross_document_adjacency,
            "candidates": trace_candidates, "selection": selection,
            "selected_page_ids": selected,
            "weights": {"relevance": 0.72, "new_query_term_coverage": 0.23, "redundancy_penalty": 0.05},
            "distance_note": "Cosine distance and reranking scores are not correctness probabilities.",
        }}
