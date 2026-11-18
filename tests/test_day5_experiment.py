"""Offline pipeline tests. Mock outputs are never benchmark measurements."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from day5_lab.experiment import (build_task_plan, create_run, preflight, prepare_main,
                                run_trials, validate_resume)
from day5_lab.gemini import ApiError
from day5_lab.io_utils import data_dir, read_json, read_records, verify_data, write_json
from day5_lab.reporting import make_review_template
from day5_lab.retrieval import Corpus


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class FakeClient:
    """Synthetic page-vector input tests control flow, not question performance."""

    def __init__(self, corpus, fail_generation=None):
        self.corpus = corpus
        self.fail_generation = fail_generation
        self.embedded_questions = []
        self.generated_questions = []

    def embed(self, text):
        self.embedded_questions.append(text)
        return {"vector": self.corpus.vectors["lec02-main-p052"], "model": "OFFLINE_TEST",
                "usage_metadata": {}, "elapsed_seconds": 0.01, "request_count": 0}

    def generate(self, question, pages, model, **kwargs):
        self.generated_questions.append(question)
        if self.fail_generation == len(self.generated_questions):
            raise ApiError("OFFLINE_TEST rate limit", status_code=429)
        return {"answer": "OFFLINE_TESTの仮応答。第2回・PDF p.52。実測結果ではありません。",
                "usage": {"input_tokens": 100, "output_tokens": 10, "thinking_tokens": 0,
                          "cached_input_tokens": 0, "total_tokens": 110},
                "cost_estimate": {"usd": 0.000055, "basis": "OFFLINE_TEST"},
                "elapsed_seconds": 0.02, "request_count": 0, "finish_reason": "STOP",
                "model_requested": model, "model_version": "OFFLINE_TEST", "request_sha256": "OFFLINE_TEST"}


@unittest.skipUnless(os.getenv("DAY5_TEST_DATA"), "Set DAY5_TEST_DATA to the pinned downloaded corpus for offline integration tests")
class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="day5-offline-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root,
                        ignore=shutil.ignore_patterns("__pycache__", ".cache", "results", "*.zip"))
        destination = data_dir(self.root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(Path(os.environ["DAY5_TEST_DATA"]), destination)
        self.corpus = Corpus(destination)
        self.cases = read_json(self.root / "lectures/05/questions.json")["cases"]
        self.data = verify_data(self.root)
        self.args = SimpleNamespace(model="gemini-3.5-flash-lite", repeats=1,
                                    max_output_tokens=4096, pause_seconds=0, timeout_seconds=120)

    def new_run(self):
        return create_run(self.root, self.cases, self.data, self.args)

    def quiet_run(self, directory, config, client):
        with contextlib.redirect_stdout(io.StringIO()):
            return run_trials(self.root, directory, config, self.corpus, client, sleep=lambda _: None)

    def test_balanced_order_over_two_repetitions(self):
        plan = build_task_plan(self.cases, 2)
        for case in self.cases:
            first = [x["method"] for x in plan if x["case_id"] == case["id"] and x["repeat"] == 1]
            second = [x["method"] for x in plan if x["case_id"] == case["id"] and x["repeat"] == 2]
            self.assertEqual(first, list(reversed(second)))
        self.assertEqual(len({row['task_id'] for row in plan}), 16)

    def test_preflight_is_offline_and_does_not_construct_client(self):
        with patch("day5_lab.experiment.GeminiClient", side_effect=AssertionError("No API client in preflight")), \
             patch("urllib.request.urlopen", side_effect=AssertionError("Pinned local data needs no HTTP")), \
             contextlib.redirect_stdout(io.StringIO()):
            _, cases, verified = preflight(self.root, download=False, model=self.args.model, repeats=2)
        self.assertEqual(len(cases), 4)
        self.assertEqual(verified, self.data)

    def test_failure_is_saved_and_resume_skips_successes(self):
        directory, config = self.new_run()
        first = FakeClient(self.corpus, fail_generation=2)
        stopped = self.quiet_run(directory, config, first)
        self.assertFalse(stopped["completed"])
        self.assertEqual(stopped["completed_trials"], 1)
        self.assertEqual(stopped["status"], "failed")
        self.assertTrue((directory / "report.md").exists())
        with zipfile.ZipFile(self.root / stopped["archive_path"]) as archive:
            self.assertTrue(any(name.endswith("records.jsonl") for name in archive.namelist()))
            self.assertFalse(any(".cache" in name or name.endswith("index.sqlite3") for name in archive.namelist()))
        recovered = validate_resume(self.root, directory, self.data)
        second = FakeClient(self.corpus)
        outcome = self.quiet_run(directory, recovered, second)
        self.assertTrue(outcome["completed"])
        self.assertEqual(len(second.generated_questions), 7)
        self.assertEqual(len(read_records(directory / "records.jsonl")), 9)
        self.assertFalse(outcome["ready_for_submission"])
        self.assertEqual(outcome["human_review_status"], "pending")

    def test_resume_rejects_modified_implementation(self):
        directory, _ = self.new_run()
        with (self.root / "day5_lab/gemini.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# OFFLINE_TEST changed implementation\n")
        with self.assertRaisesRegex(ValueError, "変更"):
            validate_resume(self.root, directory, self.data)

    def test_prepare_requires_review_and_preserves_exercise(self):
        directory, config = self.new_run()
        self.quiet_run(directory, config, FakeClient(self.corpus))
        answer = self.root / "lectures/05/answer.md"
        before = answer.read_text()
        with patch("sys.argv", ["prepare_day5_answer.py", "--run", str(directory)]), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(prepare_main(self.root), 2)
        self.assertEqual(answer.read_text(), before)
        review = make_review_template(config)
        review["status"] = "reviewed"
        review["reviewer"] = "OFFLINE_TEST synthetic reviewer"
        review["reviewed_at"] = "2026-11-17T00:00:00+09:00"
        for item in review["records"]:
            item["answer_correct"] = "unsure"
            item["citations_supported"] = "unsure"
            if item["abstention_ok"] != "not_applicable":
                item["abstention_ok"] = "unsure"
            item["notes"] = "OFFLINE_TEST fixture; not actual model quality."
        for key in review["observations"]:
            review["observations"][key] = "OFFLINE_TEST fixture; no real API was executed."
        write_json(directory / "human_review.json", review)
        with patch("sys.argv", ["prepare_day5_answer.py", "--run", str(directory)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(prepare_main(self.root), 0)
        final = answer.read_text()
        self.assertEqual(final.split("\n## 宿題\n", 1)[0], before.split("\n## 宿題\n", 1)[0])
        self.assertIn("OFFLINE_TEST", final)
        self.assertTrue(read_json(directory / "result.json")["ready_for_submission"])
        self.assertTrue((self.root / "lectures/05/quri_answers.md").exists())

    def test_unknown_generation_cost_remains_unknown(self):
        directory, config = self.new_run()
        client = FakeClient(self.corpus)
        original = client.generate
        def unknown(*args, **kwargs):
            result = original(*args, **kwargs)
            result["cost_estimate"] = {"usd": None, "reason": "OFFLINE_TEST unknown"}
            return result
        client.generate = unknown
        self.quiet_run(directory, config, client)
        report = (directory / "report.md").read_text()
        self.assertIn("算定不可", report)
        self.assertNotIn("$0.000000", report)


if __name__ == "__main__":
    unittest.main()
