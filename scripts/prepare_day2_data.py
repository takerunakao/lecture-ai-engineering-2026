"""Build the advanced Day2 dataset from the unmodified course generator.

Run: python scripts/prepare_day2_data.py
No model, paid API, GPU, or external Python packages are needed.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.day2_eval import (CATEGORIES, REVIEW_ANSWER, SYSTEM, evaluate_search,
                          load_cases, normalize, score_answer)

DATA = ROOT / 'lectures' / '02' / 'data'
NEGATIVE_TERMS = [
    '損失関数', 'AdamW', '勾配降下法', '交差エントロピー',
    'バッチ正規化', 'ドロップアウト', '早期終了', '勾配クリッピング',
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def jsonl_bytes(rows: list[dict]) -> str:
    return ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)


def prepare() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    glossary = json.loads((ROOT / 'data' / 'glossary.json').read_text(encoding='utf-8'))
    terms = glossary['terms']
    by_id = {t['id']: t for t in terms}
    registered = {normalize(n) for t in terms for n in [t['id'], t['term'], *t.get('aliases', [])]}
    cases = load_cases(DATA / 'eval_cases.json')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Evaluation IDs must be unique')
    if Counter(c['category'] for c in cases) != Counter({c: 8 for c in CATEGORIES}):
        raise ValueError('Expected eight evaluation questions per category')

    # This runs exactly the course's script, with the same interpreter as this
    # command. Its unmodified output is retained for provenance and inspection.
    generated = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'make_sft_dataset.py')],
                               check=True, capture_output=True, text=True, encoding='utf-8')
    raw_rows = [json.loads(line) for line in generated.stdout.splitlines() if line.strip()]
    if len(raw_rows) != 2 * len(terms):
        raise ValueError('Unexpected source generator record count; review before training')
    rows = []
    for row in raw_rows:
        messages = row['messages']
        if [m['role'] for m in messages] != ['user', 'assistant']:
            raise ValueError('Unexpected source messages format')
        rows.append({'messages': [
            {'role': 'system', 'content': SYSTEM}, messages[0],
            {'role': 'assistant', 'content': json.dumps(
                {'answer': messages[1]['content'], 'needs_review': False}, ensure_ascii=False)},
        ]})
    for term in NEGATIVE_TERMS:
        if normalize(term) in registered:
            raise ValueError(f'Negative training term is registered: {term}')
        rows.append({'messages': [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': f'「{term}」という用語について、用語集に基づいて説明してください。'},
            {'role': 'assistant', 'content': json.dumps(
                {'answer': REVIEW_ANSWER, 'needs_review': True}, ensure_ascii=False)},
        ]})
    train_questions = [normalize(r['messages'][1]['content']) for r in rows]
    eval_questions = [normalize(c['question']) for c in cases]
    if len(set(train_questions)) != len(train_questions) or len(set(eval_questions)) != len(eval_questions):
        raise ValueError('Duplicate normalized questions')
    if set(train_questions) & set(eval_questions):
        raise ValueError('Training/evaluation question leakage')
    for case in cases:
        gold = case['gold']
        if type(gold['needs_review']) is not bool or not gold['must_include']:
            raise ValueError(f'Invalid gold schema: {case["id"]}')
        if any(not isinstance(w, str) or not w for w in gold['must_include']):
            raise ValueError(f'Invalid gold keyword: {case["id"]}')
        if case['category'] == 'out_of_glossary':
            if case['term_id'] is not None or not gold['needs_review']:
                raise ValueError('Out-of-glossary case must require review')
            for term in NEGATIVE_TERMS:
                if normalize(term) in normalize(case['question']):
                    raise ValueError('Unknown evaluation term leaked from negative training')
        elif case['term_id'] not in by_id or gold['needs_review']:
            raise ValueError('Known concept must have a registered term_id and false review label')
        elif gold['answer'] != by_id[case['term_id']]['definition']:
            raise ValueError('Gold definition must match the source glossary')
        if not score_answer(json.dumps({'answer': gold['answer'], 'needs_review': gold['needs_review']},
                                       ensure_ascii=False), case)['both_ok']:
            raise ValueError(f'Gold fails its own scoring criterion: {case["id"]}')

    (DATA / 'glossary_sft_raw.jsonl').write_text(generated.stdout, encoding='utf-8')
    (DATA / 'glossary_sft.jsonl').write_text(jsonl_bytes(rows), encoding='utf-8')
    # Inference inputs are separate from the gold file; no gold enters generation.
    (DATA / 'test.jsonl').write_text(jsonl_bytes(
        [{'id': c['id'], 'category': c['category'], 'question': c['question']} for c in cases]), encoding='utf-8')
    write_json(DATA / 'gold.json', {c['id']: c['gold'] for c in cases})
    manifest = {
        'schema_version': 1, 'glossary_version': glossary.get('version'),
        'glossary_terms': len(terms), 'source_records': len(raw_rows),
        'train_records': len(rows), 'positive_records': len(raw_rows),
        'negative_records': len(NEGATIVE_TERMS), 'negative_training_terms': NEGATIVE_TERMS,
        'evaluation_records': len(cases), 'evaluation_by_category': dict(Counter(c['category'] for c in cases)),
        'system': SYSTEM,
        'input_policy': 'Before/after: same system plus question; no glossary text. Search: same question plus source glossary.',
        'format_metric': 'JSON object containing exactly answer:str and needs_review:bool; same schema as the lecture.',
        'content_metric': 'Strict boolean needs_review match and all case-sensitive must_include substrings; keyword proxy, not complete factuality.',
        'split_policy': 'Evaluation questions are disjoint from train; known concepts are in training. Unknown evaluation terms differ from negative training terms.',
        'source_glossary_sha256': sha256(ROOT / 'data' / 'glossary.json'),
        'source_script_sha256': sha256(ROOT / 'scripts' / 'make_sft_dataset.py'),
        'raw_dataset_sha256': sha256(DATA / 'glossary_sft_raw.jsonl'),
        'train_dataset_sha256': sha256(DATA / 'glossary_sft.jsonl'),
        'eval_cases_sha256': sha256(DATA / 'eval_cases.json'),
        'provenance': 'Original make_sft_dataset.py output retained; definitions wrapped in JSON, a shared system added, eight disjoint review examples appended.',
    }
    write_json(DATA / 'manifest.json', manifest)
    search = evaluate_search(cases, terms)
    search['execution'] = {'kind': 'local_deterministic_search_only', 'executed_training_myself': False,
                           'python': platform.python_version(), 'platform': platform.system(),
                           'source_glossary_sha256': manifest['source_glossary_sha256'],
                           'eval_cases_sha256': manifest['eval_cases_sha256']}
    write_json(DATA / 'search_baseline.json', search)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    manifest = prepare()
    print(json.dumps({k: manifest[k] for k in ['glossary_terms', 'source_records', 'train_records',
                                              'negative_records', 'evaluation_records', 'evaluation_by_category']},
                     ensure_ascii=False, indent=2))
    print('データ作成と検索の評価が完了しました。LoRA学習はまだ実行していません。')


if __name__ == '__main__':
    main()
