"""Reporting unit tests use synthetic records and never call a model API."""

from copy import deepcopy
import unittest

from day5_lab.reporting import (
    automated_metrics, latest_successes, make_review_template, quri_text,
    render_answer, render_report, validate_review,
)


def fixture():
    cases = [
        {"id": f"q{i}", "kind": kind, "question": f"試験用の質問{i}",
         "reference_groups": [] if i == 4 else [{"label": "事実", "page_ids": ["lec02-main-p052"], "expected_fact": "試験用事実"}],
         "answer_criteria": ["試験用の基準"]}
        for i, kind in enumerate(["single_page", "multi_page", "cross_lecture", "unanswerable"], 1)
    ]
    plan = [{"task_id": f"r{repeat}_{case['id']}_{method}", "repeat": repeat, "case_id": case["id"], "method": method}
            for repeat in [1, 2] for case in cases for method in ["baseline", "graph"]]
    config = {"schema_version": 1, "run_id": "synthetic_unit_test", "started_at_jst": "2026-11-17T12:00:00+09:00",
              "cases": cases, "task_plan": plan, "model": "synthetic-model", "repeats": 2,
              "top_k": 5, "temperature": 0, "max_output_tokens": 4096, "upstream_commit": "abc123"}
    page = {"page_id": "lec02-main-p052", "title": "試験ページ", "content": "試験用本文",
            "provenance": {"kind": "unit_test", "vector_rank": 1,
                           "paths": [{"nodes": ["lec02-main-p052"], "hops": 0}]}}
    records = [{**task, "attempt": 1, "status": "completed", "stage": "completed", "elapsed_seconds": 1.5,
                "embedding": {"elapsed_seconds": 0.2},
                "retrieval": {"pages": [deepcopy(page)], "trace": {"algorithm": "test"}, "elapsed_seconds": 0.1},
                "generation": {"answer": "資料には今回の実測値がありません。" if task["case_id"] == "q4" else "試験用回答（第2回・PDF p.52）。",
                               "elapsed_seconds": 1.2, "finish_reason": "STOP", "request_count": 1,
                               "usage": {"input_tokens": 100, "output_tokens": 20, "thinking_tokens": 0,
                                         "cached_input_tokens": None, "total_tokens": 120},
                               "cost_estimate": {"usd": None, "reason": "単価未確認"}}}
               for task in plan]
    review = make_review_template(config)
    review.update(status="reviewed", reviewer="試験用確認者", reviewed_at="2026-11-17")
    for row in review["records"]:
        row.update(answer_correct="pass", citations_supported="pass", notes="単体試験用の確認メモ")
        if "_q4_" in row["task_id"]:
            row["abstention_ok"] = "pass"
    review["observations"] = {
        "comparison_summary": "これは単体試験の文章であり、実験結果ではない。",
        "improved_example": "試験用の同等例。", "remaining_failure_or_limitation": "試験データの限界。",
        "adoption_decision": "試験では採否を判断しない。", "adoption_reason": "実際の測定ではないため。",
        "q3": "これは単体試験用の文章です。",
    }
    return config, records, review


class ReportingTests(unittest.TestCase):
    def test_empty_gold_and_no_citations_are_not_automatic_pass(self):
        result = automated_metrics({"reference_groups": []}, [], "確認できません。")
        self.assertIsNone(result["reference_groups_coverage"])
        self.assertIsNone(result["citation_in_context_rate"])
        self.assertEqual(result["reference_groups_total"], 0)
        self.assertNotIn("answer_correct", result)
        self.assertNotIn("citations_supported", result)

    def test_or_group_and_out_of_context_citation_are_separate(self):
        case = {"reference_groups": [{"page_ids": ["lec02-main-p051", "lec02-main-p052"]}]}
        result = automated_metrics(case, [{"page_id": "lec02-main-p051"}],
                                   "説明（第2回・PDF p.51、52）。")
        self.assertEqual(result["reference_groups_hit"], 1)
        self.assertEqual(result["reference_groups_coverage"], 1)
        self.assertEqual(result["citation_in_context_hits"], 1)
        self.assertEqual(result["citation_in_context_count"], 2)
        self.assertEqual(result["citation_in_context_rate"], 0.5)
        self.assertEqual(result["citation_out_of_context_page_ids"], ["lec02-main-p052"])

    def test_fullwidth_and_ranges_and_unique_citations(self):
        answer = "第３回・ＰＤＦ ｐ．３９–４０。第3回 PDF p.39。"
        result = automated_metrics({"reference_groups": []}, [], answer)
        self.assertEqual(result["citation_page_ids"], ["lec03-main-p039", "lec03-main-p040"])

    def test_later_failure_does_not_erase_success(self):
        a = {"task_id": "x", "attempt": 1, "status": "completed"}
        b = {"task_id": "x", "attempt": 2, "status": "completed"}
        c = {"task_id": "x", "attempt": 3, "status": "failed"}
        self.assertIs(latest_successes([a, b, c])["x"], b)

    def test_pending_review_cannot_produce_submission(self):
        config, records, _ = fixture()
        pending = make_review_template(config)
        self.assertTrue(validate_review(config, pending))
        with self.assertRaises(ValueError):
            render_answer(config, records, pending, "results/test")
        with self.assertRaises(ValueError):
            quri_text(pending)

    def test_review_requires_exact_tasks_notes_and_max_300_q3(self):
        config, _, review = fixture()
        self.assertEqual(validate_review(config, review), [])
        review["observations"]["q3"] = "あ" * 301
        review["records"][0]["notes"] = ""
        review["records"].append(deepcopy(review["records"][0]))
        errors = "\n".join(validate_review(config, review))
        self.assertIn("300文字", errors)
        self.assertIn("重複", errors)
        self.assertIn("notes", errors)

    def test_unanswerable_unsure_is_allowed_but_not_applicable_is_not(self):
        config, _, review = fixture()
        row = next(row for row in review["records"] if "_q4_" in row["task_id"])
        row["abstention_ok"] = "unsure"
        self.assertEqual(validate_review(config, review), [])
        row["abstention_ok"] = "not_applicable"
        self.assertTrue(validate_review(config, review))

    def test_partial_report_preserves_unknown_cost_and_incomplete_status(self):
        config, records, _ = fixture()
        report = render_report(config, records[:1], "failed")
        self.assertIn("未完了（1/16件）", report)
        self.assertIn("算定不可", report)
        self.assertNotIn("$0.000000", report)
        self.assertIn("人手確認：未完了", report)
        self.assertIn("未完了なら方式間の集計対象も揃っていない", report)

    def test_final_answer_rejects_missing_trial_or_empty_response(self):
        config, records, review = fixture()
        with self.assertRaises(ValueError):
            render_answer(config, records[:-1], review, "results/test")
        records[0]["generation"]["answer"] = ""
        with self.assertRaises(ValueError):
            render_answer(config, records, review, "results/test")

    def test_complete_report_and_answer_contain_auditable_evidence(self):
        config, records, review = fixture()
        report = render_report(config, records, "completed", review)
        self.assertIn("実行完了（16/16件）", report)
        self.assertIn("試験用回答", report)
        self.assertIn("lec02-main-p052", report)
        self.assertIn("human_review.json", report)
        self.assertIn("reference_pages.json", report)
        self.assertIn("vector_rank=1", report)
        self.assertIn("キャッシュ入力=未取得", report)
        for task in config["task_plan"]:
            self.assertIn(task["task_id"], report)
        answer = render_answer(config, records, review, "results/test")
        self.assertTrue(answer.startswith("## 宿題\n"))
        self.assertIn("results/test/report.md", answer)
        self.assertIn("results/test/human_review.json", answer)
        self.assertIn(review["observations"]["comparison_summary"], answer)
        self.assertIn("300文字以内", quri_text(review))

    def test_model_version_drift_and_single_repeat_are_disclosed(self):
        config, records, _ = fixture()
        config["repeats"] = 1
        records[0]["generation"]["model_version"] = "test-version-a"
        records[1]["generation"]["model_version"] = "test-version-b"
        report = render_report(config, records, "completed")
        self.assertIn("複数のモデル版が混在", report)
        self.assertIn("各問1回", report)
        self.assertIn("同一版だったとは確認できない", report)

    def test_malformed_verdict_types_return_errors_instead_of_crashing(self):
        config, _, review = fixture()
        review["records"][0]["answer_correct"] = []
        review["records"][1]["abstention_ok"] = {}
        review["records"][2]["task_id"] = []
        self.assertTrue(validate_review(config, review))


if __name__ == "__main__":
    unittest.main()
