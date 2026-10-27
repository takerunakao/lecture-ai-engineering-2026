"""Day2 advanced: transparent, offline scoring and glossary-name retrieval.

No gold label or term_id is given to the retriever. The keyword score follows
the lecture's metric; it is a proxy, not an exhaustive factuality assessment.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import time
import unicodedata

SYSTEM = (
    'あなたはAIエンジニアリング実践講座2026の用語集回答係です。'
    '講座の用語集に基づき、必ずJSONで答えてください。'
    '形式は {"answer": 文字列, "needs_review": 真偽値} です。'
    '用語集の登録語については定義を説明し、needs_reviewをfalseにしてください。'
    '用語集に根拠があると確認できない質問には、answerに「確認が必要」と書き、'
    'needs_reviewをtrueにしてください。'
)
REVIEW_ANSWER = 'この用語集には記載がありません。確認が必要です。'
CATEGORIES = ('known', 'paraphrase', 'out_of_glossary')


def load_jsonl(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def load_cases(path: str | Path) -> list[dict]:
    cases = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(cases, list) or not cases:
        raise ValueError('eval_cases.json must be a nonempty list')
    return cases


def normalize(text: str) -> str:
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text).casefold())


def check_format(raw: str) -> tuple[bool, str, dict | None]:
    """Keep the lecture's JSON keys/type criterion; do not repair the output."""
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return False, 'json_error', None
    if not isinstance(obj, dict):
        return False, 'not_object', None
    if set(obj) - {'answer', 'needs_review'}:
        return False, 'extra_keys', obj
    if set(obj) != {'answer', 'needs_review'}:
        return False, 'missing_key', obj
    if not isinstance(obj['answer'], str) or type(obj['needs_review']) is not bool:
        return False, 'wrong_type', obj
    return True, '', obj


def score_answer(raw: str, case: dict) -> dict:
    format_ok, reason, obj = check_format(raw)
    loose = obj
    if not format_ok:
        # Same separation of format and content as the lecture. This extraction
        # is used only for content scoring, never to make format_ok true.
        match = re.search(r'\{.*\}', raw, re.S)
        try:
            loose = json.loads(match.group(0)) if match else None
        except (TypeError, ValueError):
            loose = None
    gold = case['gold']
    answer = loose.get('answer') if isinstance(loose, dict) else None
    pred = loose.get('needs_review') if isinstance(loose, dict) else None
    if type(pred) is not bool:
        pred = None
    review_ok = pred is not None and pred is gold['needs_review']
    content_ok = bool(review_ok and isinstance(answer, str) and all(w in answer for w in gold['must_include']))
    unsupported = gold['needs_review'] is True and pred is False
    over_refusal = gold['needs_review'] is False and pred is True
    if not format_ok:
        failure = 'format_error'
    elif unsupported:
        failure = 'unsupported_assertion'
    elif over_refusal:
        failure = 'over_refusal'
    elif not content_ok:
        failure = 'content_mismatch'
    else:
        failure = 'pass'
    return {
        'format_ok': format_ok, 'format_reason': reason,
        'content_ok': content_ok, 'both_ok': bool(format_ok and content_ok),
        'review_ok': review_ok, 'gold_needs_review': gold['needs_review'],
        'needs_review': pred, 'parsed_answer': answer,
        'failure_type': failure, 'unsupported_assertion': unsupported,
        'over_refusal': over_refusal,
    }


def _rates(rows: list[dict]) -> dict:
    n = len(rows)
    return {
        'n': n,
        **{target: sum(bool(row[key]) for row in rows) / n if n else None
           for target, key in [('format_rate', 'format_ok'), ('content_rate', 'content_ok'),
                               ('both_rate', 'both_ok'), ('review_accuracy', 'review_ok')]},
        'unsupported_assertions': sum(bool(r.get('unsupported_assertion')) for r in rows),
        'over_refusals': sum(bool(r.get('over_refusal')) for r in rows),
    }


def summarize(rows: list[dict], label: str) -> dict:
    return {'label': label, **_rates(rows),
            'by_category': {category: _rates([r for r in rows if r['category'] == category])
                            for category in CATEGORIES}}


def retrieve_glossary(question: str, terms: list[dict]) -> dict:
    """Name/ID/alias matching, without semantic search or generative rewriting.

    Longer names suppress a contained short name. Latin names have ASCII word
    boundaries so, for example, AdaLoRA does not silently resolve to LoRA.
    Queries with zero or multiple distinct matches produce a review request.
    """
    query = normalize(question)
    hits: list[tuple[int, int, str, str]] = []
    by_id = {t['id']: t for t in terms}
    for term in terms:
        names = {normalize(n) for n in [term['term'], term['id'], *term.get('aliases', [])]}
        for name in names:
            if not name:
                continue
            # 'r' is too broad in a sentence, but an exact one-letter query is safe.
            if len(name) == 1 and query != name:
                continue
            start = 0
            while True:
                pos = query.find(name, start)
                if pos < 0:
                    break
                end = pos + len(name)
                start = pos + 1
                latin_left = name[0].isascii() and (name[0].isalnum() or name[0] == '_')
                latin_right = name[-1].isascii() and (name[-1].isalnum() or name[-1] == '_')
                if latin_left and pos and re.match(r'[a-z0-9_-]', query[pos - 1]):
                    continue
                if latin_right and end < len(query) and re.match(r'[a-z0-9_-]', query[end]):
                    continue
                hits.append((pos, end, term['id'], name))
    maximal = [h for h in hits if not any(
        other[0] <= h[0] and h[1] <= other[1]
        and other[1] - other[0] > h[1] - h[0]
        for other in hits)]
    matched_ids = sorted({h[2] for h in maximal})
    if len(matched_ids) == 1:
        term = by_id[matched_ids[0]]
        answer = {'answer': term['definition'], 'needs_review': False}
        reason = 'unique_name_or_alias'
    else:
        answer = {'answer': REVIEW_ANSWER, 'needs_review': True}
        reason = 'no_match' if not matched_ids else 'ambiguous_names'
    return {'raw': json.dumps(answer, ensure_ascii=False), 'matched_term_ids': matched_ids,
            'retrieval_reason': reason, 'matched_names': sorted({h[3] for h in maximal})}


def evaluate_search(cases: list[dict], terms: list[dict]) -> dict:
    rows = []
    started = time.perf_counter()
    for case in cases:
        t0 = time.perf_counter()
        found = retrieve_glossary(case['question'], terms)
        elapsed = time.perf_counter() - t0
        rows.append({'id': case['id'], 'category': case['category'], 'question': case['question'],
                     **found, **score_answer(found['raw'], case), 'elapsed_seconds': elapsed})
    summary = summarize(rows, 'search')
    summary['seconds'] = time.perf_counter() - started
    return {'summary': summary, 'rows': rows}
