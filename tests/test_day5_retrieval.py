"""Offline integrity and retrieval-behavior tests; no model API is contacted.

Synthetic embeddings below are test fixtures, not real question embeddings or
evidence of an improvement on the homework questions.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sqlite3
import struct
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from day5_lab.retrieval import (  # noqa: E402
    Corpus, DIMENSIONS, DOCUMENT_COUNTS, MAX_CANDIDATES, MAX_HOPS, alias_in_query,
)


def make_fixture(directory: Path, *, opaque_ids: bool = False) -> list[str]:
    documents, nodes, edges, rows, ids = [], [], [], [], []
    for document_id, count in DOCUMENT_COUNTS.items():
        document = {"id": document_id, "title": document_id,
                    "content": [{"section": "Synthetic section", "content": []}]}
        previous = None
        for number in range(1, count + 1):
            index = len(ids)
            page_id = f"opaque-{index:03d}" if opaque_ids else f"{document_id}-p{number:03d}"
            ids.append(page_id)
            title, content = f"Page {index}", f"Synthetic fixture page {index}."
            document["content"][0]["content"].append({
                "id": page_id, "page": number, "title": title, "content": content,
            })
            nodes.append({"id": page_id, "kind": "page", "title": title, "page": number})
            if previous:
                edges.append({"source": previous, "target": page_id, "relation": "next_page"})
            previous = page_id
            angle = index * 0.004
            vector = [math.cos(angle), math.sin(angle)] + [0.0] * (DIMENSIONS - 2)
            rows.append((page_id, document_id, int(document_id[3:5]), document_id,
                         "Synthetic section", title, number, content,
                         struct.pack(f"<{DIMENSIONS}f", *vector)))
        documents.append(document)
    definitions = [
        ("term:lora", "LoRA", ["LoRA"], [0, 1, 2, 20, 40]),
        ("term:qlora", "QLoRA", ["QLoRA"], [20, 30]),
        ("term:memory", "メモリ", ["memory", "メモリ"], [2, 15, 25]),
        ("term:common", "Common", ["common"], list(range(40))),
    ]
    for term_id, title, aliases, page_indices in definitions:
        nodes.append({"id": term_id, "kind": "term", "title": title, "aliases": aliases})
        for index in page_indices:
            edges.append({"source": ids[index], "target": term_id, "relation": "mentions"})
    # An invalid cross-document edge must never become an adjacency shortcut.
    edges.append({"source": ids[72], "target": ids[73], "relation": "next_page"})
    # Related-term edges exist in the source format but are intentionally unused.
    edges.append({"source": "term:lora", "target": "term:common", "relation": "related_term"})
    (directory / "lectures.json").write_text(json.dumps(documents), encoding="utf-8")
    (directory / "graph.json").write_text(json.dumps({"nodes": nodes, "edges": edges}), encoding="utf-8")
    connection = sqlite3.connect(directory / "index.sqlite3")
    connection.execute("""CREATE TABLE chunks (
        page_id TEXT PRIMARY KEY, document_id TEXT, lecture INTEGER,
        document_title TEXT, section TEXT, title TEXT, page INTEGER,
        content TEXT, embedding BLOB)""")
    connection.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return ids


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.ids = make_fixture(self.directory, opaque_ids=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_alias_boundaries_and_unicode(self):
        self.assertFalse(alias_in_query("LoRA", "QLoRA"))
        self.assertFalse(alias_in_query("LoRA", "unlorated"))
        self.assertTrue(alias_in_query("LoRA", "LoRAとQLoRA"))
        self.assertTrue(alias_in_query("LoRA", "ＬｏＲＡ の比較"))
        self.assertTrue(alias_in_query("メモリ", "外部メモリについて"))
        self.assertFalse(alias_in_query("API", "capital"))

    def test_baseline_cosine_order_and_page_budget(self):
        corpus = Corpus(self.directory)
        query = [1.0, 0.0] + [0.0] * (DIMENSIONS - 2)
        ranked = corpus.rank(query)
        self.assertEqual([p["page_id"] for p in ranked[:5]], self.ids[:5])
        self.assertAlmostEqual(ranked[20]["distance"], 1 - math.cos(20 * 0.004), places=6)
        for method in ("baseline", "graph"):
            result = corpus.retrieve("LoRA QLoRA", query, method)
            self.assertEqual(len(result["pages"]), 5)
            self.assertEqual(len({p["page_id"] for p in result["pages"]}), 5)
            json.dumps(result, allow_nan=False)

    def test_graph_can_cover_missing_query_facet_without_gold_ids(self):
        corpus = Corpus(self.directory)
        query = list(corpus.vectors[self.ids[0]])
        baseline = corpus.retrieve("LoRA と QLoRA の比較", query, "baseline")
        graph = corpus.retrieve("LoRA と QLoRA の比較", query, "graph")
        self.assertNotIn(self.ids[20], [p["page_id"] for p in baseline["pages"]])
        self.assertIn(self.ids[20], [p["page_id"] for p in graph["pages"]])
        self.assertEqual(graph["pages"][0]["page_id"], self.ids[0])
        selected = next(p for p in graph["pages"] if p["page_id"] == self.ids[20])
        self.assertTrue(any(p["relations"] == ["mentions", "mentions"]
                            for p in selected["provenance"]["paths"]))
        self.assertEqual(graph, corpus.retrieve("LoRA と QLoRA の比較", query, "graph"))

    def test_hop_limits_and_high_degree_filter(self):
        corpus = Corpus(self.directory)
        query = list(corpus.vectors[self.ids[0]])
        result = corpus.retrieve("common LoRA メモリ", query, "graph")
        trace = result["trace"]
        self.assertLessEqual(trace["candidate_count_after_cap"], MAX_CANDIDATES)
        self.assertIn({"term_id": "term:common", "title": "Common", "degree": 40,
                       "reason": "high_degree"}, trace["ignored_query_terms"])
        for candidate in trace["candidates"]:
            for path in candidate["paths"]:
                self.assertLessEqual(path["hops"], MAX_HOPS)
                self.assertNotIn("term:common", path["nodes"])
                self.assertNotIn("related_term", path["relations"])

    def test_cross_document_adjacency_is_not_followed(self):
        corpus = Corpus(self.directory)
        result = corpus.retrieve("unknown", list(corpus.vectors[self.ids[72]]), "graph")
        self.assertEqual(result["trace"]["rejected_cross_document_next_page_edges"], 1)
        for candidate in result["trace"]["candidates"]:
            for path in candidate["paths"]:
                if path["kind"] == "adjacent_page":
                    documents = {corpus.pages[node]["document_id"] for node in path["nodes"]}
                    self.assertEqual(len(documents), 1)

    def test_db_source_mismatch_fails_before_retrieval(self):
        connection = sqlite3.connect(self.directory / "index.sqlite3")
        connection.execute("UPDATE chunks SET content = 'changed' WHERE page_id = ?", (self.ids[0],))
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(ValueError, "differ"):
            Corpus(self.directory)

    def test_missing_db_row_and_nonfinite_vectors_fail(self):
        connection = sqlite3.connect(self.directory / "index.sqlite3")
        connection.execute("DELETE FROM chunks WHERE page_id = ?", (self.ids[-1],))
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(ValueError, "do not match"):
            Corpus(self.directory)
        # A query supplied by the API must also be validated before ranking.
        (self.directory / "index.sqlite3").unlink()
        make_fixture(self.directory, opaque_ids=True)
        corpus = Corpus(self.directory)
        with self.assertRaises(ValueError):
            corpus.rank([float("nan")] + [0.0] * (DIMENSIONS - 1))
        with self.assertRaises(ValueError):
            corpus.rank([0.0] * DIMENSIONS)
        with self.assertRaises(ValueError):
            corpus.rank([1.0] * (DIMENSIONS - 1))

    def test_wrong_embedding_blob_length_fails(self):
        connection = sqlite3.connect(self.directory / "index.sqlite3")
        connection.execute("UPDATE chunks SET embedding = ? WHERE page_id = ?",
                           (b"short", self.ids[0]))
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(ValueError, "dimensions"):
            Corpus(self.directory)


class CourseDataSmokeTests(unittest.TestCase):
    def test_pinned_real_corpus_without_network(self):
        configured = os.getenv("DAY5_TEST_DATA")
        if not configured:
            self.skipTest("Set DAY5_TEST_DATA to the downloaded course data directory.")
        corpus = Corpus(Path(configured))
        self.assertEqual(len(corpus.pages), 214)
        self.assertEqual(len(corpus.vectors), 214)
        # A page vector is used solely to validate the retrieval mechanics.
        page_id = sorted(corpus.pages)[0]
        for method in ("baseline", "graph"):
            result = corpus.retrieve("LLM メモリ", list(corpus.vectors[page_id]), method)
            self.assertEqual(len(result["pages"]), 5)
            self.assertTrue(all(p["document_id"] in DOCUMENT_COUNTS for p in result["pages"]))
            json.dumps(result, ensure_ascii=False, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
