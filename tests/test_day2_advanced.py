"""Offline safeguards for scoring, split integrity, retrieval and report import.

Synthetic model outputs here are unit-test fixtures only, never measurements.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.day2_eval import (REVIEW_ANSWER, evaluate_search, load_cases, load_jsonl,
                          normalize, retrieve_glossary, score_answer, summarize)
from scripts import prepare_day2_answer as report
from scripts import run_day2_training as runner

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'lectures/02/data'


class Day2EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terms = json.loads((ROOT / 'data/glossary.json').read_text())['terms']
        cls.cases = load_cases(DATA / 'eval_cases.json')
        cls.known = next(c for c in cls.cases if c['id'] == 'known_lora')
        cls.unknown = next(c for c in cls.cases if c['category'] == 'out_of_glossary')

    def test_gold_schema_and_required_keywords_are_self_consistent(self):
        for case in self.cases:
            raw = json.dumps({k: case['gold'][k] for k in ['answer', 'needs_review']}, ensure_ascii=False)
            self.assertTrue(score_answer(raw, case)['both_ok'], case['id'])

    def test_runner_requests_flat_ids_instead_of_default_encoding_mapping(self):
        class TokenizerWithMappingDefault:
            def __init__(self):
                self.calls = []

            def apply_chat_template(self, messages, *, return_dict=True, **kwargs):
                self.calls.append({'return_dict': return_dict, **kwargs})
                ids = [101, 102, 103, 104, 105]
                return {'input_ids': ids, 'attention_mask': [1] * len(ids)} if return_dict else ids

        tokenizer = TokenizerWithMappingDefault()
        training, evaluation, lengths = runner.tokenize_all(
            tokenizer, [{'messages': []}], [self.known])
        self.assertEqual(training[0]['input_ids'], [101, 102, 103, 104, 105])
        self.assertEqual(training[0]['attention_mask'], [1] * 5)
        self.assertEqual(evaluation[0], training[0]['input_ids'])
        self.assertEqual(lengths['training'][0]['tokens'], 5)
        self.assertEqual(lengths['evaluation'][0]['input_tokens'], 5)
        self.assertEqual([call['add_generation_prompt'] for call in tokenizer.calls], [False, True])
        for call in tokenizer.calls:
            self.assertIs(call['return_dict'], False)
            self.assertIsNone(call['return_tensors'])

    def test_runner_rejects_mapping_batch_and_noninteger_ids_before_gpu_work(self):
        class InvalidTokenizer:
            def __init__(self, value):
                self.value = value

            def apply_chat_template(self, *args, **kwargs):
                return self.value

        for value in ({'input_ids': [1, 2]}, [[1, 2]], ['1', '2'], [True, 2], [-1, 2], []):
            with self.subTest(value=value):
                with self.assertRaises(runner.ExperimentError):
                    runner.tokenize_ids(InvalidTokenizer(value), [], add_generation_prompt=False)

    def test_format_and_content_are_separate(self):
        target = json.dumps({'answer': self.known['gold']['answer'], 'needs_review': False}, ensure_ascii=False)
        scored = score_answer('```json\n' + target + '\n```', self.known)
        self.assertFalse(scored['format_ok'])
        self.assertTrue(scored['content_ok'])
        self.assertFalse(scored['both_ok'])

    def test_review_must_be_a_boolean_not_integer_or_string(self):
        for wrong in [1, 'true', None]:
            raw = json.dumps({'answer': REVIEW_ANSWER, 'needs_review': wrong}, ensure_ascii=False)
            scored = score_answer(raw, self.unknown)
            self.assertFalse(scored['format_ok'])
            self.assertFalse(scored['review_ok'])
            self.assertFalse(scored['content_ok'])

    def test_extra_key_does_not_turn_into_a_format_success(self):
        raw = json.dumps({'answer': self.known['gold']['answer'], 'needs_review': False, 'confidence': 1}, ensure_ascii=False)
        scored = score_answer(raw, self.known)
        self.assertFalse(scored['format_ok'])
        self.assertTrue(scored['content_ok'])

    def test_unknown_is_a_corpus_rule_not_general_knowledge(self):
        raw = json.dumps({'answer': 'DoRAは重みの大きさと方向を分ける手法です。', 'needs_review': False}, ensure_ascii=False)
        scored = score_answer(raw, self.unknown)
        self.assertTrue(scored['format_ok'])
        self.assertFalse(scored['content_ok'])
        self.assertTrue(scored['unsupported_assertion'])

    def test_name_boundaries_and_longer_names_prevent_wrong_hits(self):
        self.assertEqual(retrieve_glossary('AdaLoRAとは？', self.terms)['matched_term_ids'], [])
        self.assertEqual(retrieve_glossary('QLoRAについて説明して', self.terms)['matched_term_ids'], ['qlora'])
        self.assertEqual(retrieve_glossary('APIキーとは？', self.terms)['matched_term_ids'], ['api-key'])
        self.assertEqual(retrieve_glossary('API keyとは？', self.terms)['matched_term_ids'], ['api-key'])
        self.assertEqual(retrieve_glossary('learning rateを説明して', self.terms)['matched_term_ids'], ['learning-rate'])

    def test_ambiguous_question_requests_review(self):
        result = retrieve_glossary('学習率とエポックの両方を教えて', self.terms)
        self.assertEqual(result['retrieval_reason'], 'ambiguous_names')
        self.assertTrue(json.loads(result['raw'])['needs_review'])

    def test_retrieval_does_not_take_a_gold_term_id(self):
        original = evaluate_search([self.known], self.terms)['rows'][0]['raw']
        changed = deepcopy(self.known)
        changed['term_id'] = 'quantization'
        changed['gold']['answer'] = 'この正解欄を検索入力に利用してはいけない'
        new = evaluate_search([changed], self.terms)['rows'][0]['raw']
        self.assertEqual(original, new)

    def test_empty_summary_is_missing_not_zero_accuracy(self):
        summary = summarize([], 'before')
        self.assertEqual(summary['n'], 0)
        self.assertIsNone(summary['format_rate'])
        self.assertIsNone(summary['by_category']['known']['content_rate'])

    def test_training_questions_do_not_overlap_evaluation(self):
        train = load_jsonl(DATA / 'glossary_sft.jsonl')
        raw = load_jsonl(DATA / 'glossary_sft_raw.jsonl')
        self.assertEqual(len(raw), 116)
        self.assertEqual(len(train), 124)
        questions = {normalize(r['messages'][1]['content']) for r in train}
        self.assertEqual(len(questions), len(train))
        self.assertFalse(questions & {normalize(c['question']) for c in self.cases})
        for source, converted in zip(raw, train[:116]):
            self.assertEqual(source['messages'][-1]['content'], json.loads(converted['messages'][-1]['content'])['answer'])

    def test_import_rejects_scores_not_supported_by_raw_output(self):
        payload = evaluate_search(self.cases, self.terms)
        payload['rows'][0]['raw'] = 'not JSON'
        with self.assertRaisesRegex(ValueError, 'saved score'):
            report.verify_payload(payload, self.cases, 'search')

    def test_pending_report_has_no_training_claim_or_q3(self):
        text, q3 = report.build_report(None, pending=True)
        self.assertIn('GPUによるLoRA学習とモデルの前後評価は未実行', text)
        self.assertIn('`executed_training_myself`: `false`', text)
        self.assertIsNone(q3)

    def test_category_scores_and_failure_counts_are_recomputed_from_raw(self):
        payload = evaluate_search(self.cases, self.terms)
        payload['summary']['by_category']['known']['content_rate'] = 0.0
        payload['summary']['unsupported_assertions'] = 999
        payload['rows'][0]['unsupported_assertion'] = True
        verified = report.verify_payload(payload, self.cases, 'search')
        self.assertEqual(verified['summary']['by_category']['known']['content_rate'], 1.0)
        self.assertEqual(verified['summary']['unsupported_assertions'], 0)
        self.assertFalse(verified['rows'][0]['unsupported_assertion'])

    def test_incomplete_run_cannot_become_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / 'result.json').write_text(json.dumps({'status': 'failed', 'completed': False, 'executed_training_myself': False}))
            with self.assertRaisesRegex(ValueError, '未完了'):
                report.build_report(path)

    def test_complete_report_and_q3_from_synthetic_fixture_only(self):
        # Only a report-generation check. No synthetic outputs are published.
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            shutil.copytree(DATA, base / 'data')
            run_dir = base / 'results' / 'synthetic-unit-test'
            run_dir.mkdir(parents=True)
            manifest = json.loads((DATA / 'manifest.json').read_text())
            result = {'status': 'completed', 'completed': True, 'executed_training_myself': True,
                      'dataset_sha256': manifest['train_dataset_sha256'], 'eval_cases_sha256': manifest['eval_cases_sha256'],
                      'config': {'synthetic_fixture': True}, 'versions': {}, 'train': {}}
            (run_dir / 'result.json').write_text(json.dumps(result))
            for label in ['before', 'after', 'search']:
                payload = evaluate_search(self.cases, self.terms)
                payload['summary'] = summarize(payload['rows'], label)
                (run_dir / f'eval_{label}.json').write_text(json.dumps(payload, ensure_ascii=False))
            with patch.object(report, 'BASE', base):
                text, q3 = report.build_report(run_dir)
            self.assertIn('83.3%', text)
            self.assertIsNotNone(q3)
            self.assertLessEqual(len(q3), 400)

    def test_report_replacement_preserves_personal_notes(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            target = base / 'answer.md'
            target.write_text('# 第2回 解答\n\n## 演習\n\n私の演習記録\n\n## 宿題\n\n私の追加観察\n')
            with patch.object(report, 'BASE', base):
                report.write_answer(report.START + '\n初回自動部分\n' + report.END)
                report.write_answer(report.START + '\n更新した自動部分\n' + report.END)
            text = target.read_text()
            self.assertIn('私の演習記録', text)
            self.assertIn('私の追加観察', text)
            self.assertNotIn('初回自動部分', text)
            self.assertEqual(text.count(report.START), 1)


if __name__ == '__main__':
    unittest.main()
