"""Offline behavior tests for the Day1 benchmark.

Run with ``python -m unittest discover -s tests -p test_benchmark_day1.py``
or the course repository's ``uv run pytest -q``. All API responses are
synthetic test fixtures, never homework measurements. The two SDK tests
use an in-memory HTTP transport and are skipped if the SDK is absent.
"""
from __future__ import annotations

import builtins
from collections import Counter
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "benchmark_day1.py"
SPEC = importlib.util.spec_from_file_location("_day1_benchmark_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


@contextmanager
def no_sdk_or_network():
    """Fail immediately if an offline operation imports the SDK or connects."""
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "google" or name.startswith("google."):
            raise AssertionError("An offline operation tried to import the SDK")
        return original_import(name, *args, **kwargs)

    with mock.patch("builtins.__import__", side_effect=guarded_import), \
            mock.patch("socket.create_connection", side_effect=AssertionError("Unexpected network")), \
            mock.patch("socket.socket.connect", side_effect=AssertionError("Unexpected network")):
        yield


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeClient:
    def __init__(self, clock, outcomes, durations=None):
        self.models = self
        self.clock = clock
        self.outcomes = list(outcomes)
        self.durations = list(durations or [1.0] * len(self.outcomes))
        self.calls = []
        self.starts = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        self.starts.append(self.clock())
        self.clock.now += self.durations.pop(0)
        result = self.outcomes.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class HttpFailure(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def answer(text="fixture answer", reason="STOP", usage=None):
    return SimpleNamespace(
        text=text,
        candidates=[SimpleNamespace(finish_reason=reason)],
        usage_metadata=usage,
        model_version="fixture-model-version",
    )


def sdk_available():
    try:
        return importlib.util.find_spec("google.genai") is not None
    except (ImportError, ModuleNotFoundError):
        return False


class BenchmarkBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="day1-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def plan(self, models=("model-a", "model-b"), questions=("short",), repeats=1, interval=15):
        args = benchmark.make_parser().parse_args([
            "--models", *models, "--question-ids", *questions,
            "--repeats", str(repeats), "--interval", str(interval),
        ])
        return benchmark.build_plan(args)

    def prepare_run(self, plan):
        path = self.root / "run"
        path.mkdir()
        benchmark.json_write(path / "plan.json", plan)
        return path

    def run_fake(self, plan, outcomes, durations=None):
        run_dir = self.prepare_run(plan)
        clock = FakeClock()
        client = FakeClient(clock, outcomes, durations)
        output = io.StringIO()
        with redirect_stdout(output):
            state = benchmark.run_experiment(
                plan, run_dir, client, {"max_output_tokens": 2048},
                clock=clock, sleeper=clock.sleep,
            )
        records, warnings = benchmark.load_records(run_dir)
        self.assertEqual(warnings, [])
        return state, records, client, clock, run_dir, output.getvalue()

    def test_plan_balances_model_question_pairs_and_rotates_order(self):
        trials = benchmark.build_trials(["model-a", "model-b"], ["short", "long", "course"], 3)
        self.assertEqual(len(trials), 18)
        self.assertEqual(len({row["trial_id"] for row in trials}), 18)
        counts = Counter((row["requested_model"], row["question_id"]) for row in trials)
        self.assertEqual(len(counts), 6)
        self.assertEqual(set(counts.values()), {3})
        orders = []
        for repeat in (1, 2, 3):
            rows = [row for row in trials if row["repeat"] == repeat]
            order = [(row["requested_model"], row["question_id"]) for row in rows]
            self.assertEqual(len(set(order)), 6)
            orders.append(order)
        self.assertNotEqual(orders[0], orders[1])
        for row in trials:
            self.assertEqual(row["question_text"], benchmark.QUESTIONS[row["question_id"]])

    def test_dry_run_needs_no_key_sdk_network_or_output_directory(self):
        target = self.root / "must-not-exist"
        output = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), no_sdk_or_network(), redirect_stdout(output):
            code = benchmark.main(["--dry-run", "--run-dir", str(target)])
        self.assertEqual(code, 0)
        self.assertFalse(target.exists())
        self.assertIn("DRY RUN", output.getvalue())
        self.assertIn("18回", output.getvalue())

    def test_unavailable_metadata_stays_missing_and_real_zero_stays_zero(self):
        trial = benchmark.build_trials(["model-a"], ["short"], 1)[0]
        missing = benchmark.response_record(trial, answer(), "fixture-time", 1.0)
        self.assertTrue(all(missing[field] is None for field in benchmark.TOKEN_FIELDS))
        response = {
            "text": "fixture answer", "candidates": [{"finish_reason": "STOP"}],
            "usage_metadata": {"prompt_token_count": 0, "candidates_token_count": None,
                               "thoughts_token_count": 0, "total_token_count": 0},
        }
        record = benchmark.response_record(trial, response, "fixture-time", 1.0)
        self.assertEqual(record["prompt_token_count"], 0)
        self.assertEqual(record["thoughts_token_count"], 0)
        self.assertEqual(record["total_token_count"], 0)
        self.assertIsNone(record["candidates_token_count"])
        self.assertIsNone(record["cached_content_token_count"])

    def test_completed_truncated_empty_and_unfinished_outputs_are_distinct(self):
        trial = benchmark.build_trials(["model-a"], ["short"], 1)[0]
        cases = [
            (answer(reason="STOP"), "success"),
            (answer(reason="MAX_TOKENS"), "truncated"),
            (answer(reason="SAFETY"), "incomplete"),
            (answer(reason=None), "incomplete"),
            (answer(text=" \n ", reason="STOP"), "empty"),
            (SimpleNamespace(candidates=None, text=None), "empty"),
        ]
        for response, expected in cases:
            with self.subTest(expected=expected, response=response):
                record = benchmark.response_record(trial, response, "fixture-time", 1.0)
                self.assertEqual(record["status"], expected)

    def test_provider_total_is_preserved_with_thought_and_cached_tokens(self):
        trial = benchmark.build_trials(["model-a"], ["short"], 1)[0]
        usage = SimpleNamespace(prompt_token_count=11, candidates_token_count=7,
                                thoughts_token_count=5, cached_content_token_count=3,
                                total_token_count=23)
        record = benchmark.response_record(trial, answer(usage=usage), "fixture-time", 2.0)
        self.assertEqual(record["total_token_count"], 23)
        self.assertEqual(record["thoughts_token_count"], 5)
        self.assertEqual(record["cached_content_token_count"], 3)
        self.assertEqual(record["model_version"], "fixture-model-version")

    def test_request_spacing_is_excluded_from_measured_duration(self):
        plan = self.plan(interval=15)
        state, records, client, clock, _, _ = self.run_fake(plan, [answer(), answer()], [2.0, 4.0])
        self.assertEqual(client.starts, [0.0, 15.0])
        self.assertEqual(clock.sleeps, [13.0])
        self.assertEqual([row["elapsed_seconds"] for row in records], [2.0, 4.0])
        self.assertEqual(state["attempted_calls"], 2)
        self.assertEqual(state["status"], "completed")

    def test_429_is_logged_once_then_halts_without_leaking_exception_text(self):
        secret = "DUMMY_SECRET_MUST_NOT_APPEAR"
        failure = HttpFailure(429, f"URL?key={secret}; Authorization: Bearer {secret}")
        plan = self.plan()
        state, records, client, _, run_dir, output = self.run_fake(plan, [failure, answer()])
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "error")
        self.assertEqual(records[0]["http_code"], 429)
        self.assertTrue(all(records[0][field] is None for field in benchmark.TOKEN_FIELDS))
        self.assertEqual(state["status"], "stopped")
        self.assertIn("429", state["stop_reason"])
        self.assertEqual(sum(row["not_attempted"] for row in benchmark.summarize(plan, records)), 1)
        text = output + "".join(path.read_text(encoding="utf-8") for path in run_dir.iterdir())
        self.assertNotIn(secret, text)
        self.assertIn("部分実測", (run_dir / "answer.generated.md").read_text(encoding="utf-8"))

    def test_503_is_not_retried_or_misclassified_as_a_quota_stop(self):
        plan = self.plan()
        state, records, client, _, _, _ = self.run_fake(plan, [HttpFailure(503, "unavailable"), answer()])
        self.assertEqual(len(client.calls), 2)
        self.assertEqual([call["model"] for call in client.calls], ["model-a", "model-b"])
        self.assertEqual(records[0]["http_code"], 503)
        self.assertEqual(records[0]["status"], "error")
        self.assertEqual(records[1]["status"], "success")
        self.assertEqual(state["status"], "completed")
        self.assertIsNone(state["stop_reason"])

    def test_summary_uses_only_successes_and_counts_missing_tokens(self):
        plan = self.plan(models=("model-a",), repeats=4)
        rows = [
            benchmark.response_record(plan["trials"][0], answer(usage={"prompt_token_count": 0}), "t", 2.0),
            benchmark.response_record(plan["trials"][1], answer(), "t", 4.0),
            benchmark.response_record(plan["trials"][2], answer(reason="MAX_TOKENS"), "t", 1000.0),
            benchmark.error_record(plan["trials"][3], HttpFailure(503, "error"), "t", 2000.0),
        ]
        summary = benchmark.summarize(plan, rows)[0]
        self.assertEqual(summary["attempted"], 4)
        self.assertEqual(summary["success"], 2)
        self.assertEqual(summary["truncated"], 1)
        self.assertEqual(summary["error"], 1)
        self.assertEqual(summary["elapsed_seconds_median"], 3.0)
        self.assertEqual(summary["elapsed_seconds_min"], 2.0)
        self.assertEqual(summary["elapsed_seconds_max"], 4.0)
        self.assertEqual(summary["prompt_token_count_median"], 0)
        self.assertEqual(summary["prompt_token_count_missing"], 1)
        self.assertIsNone(summary["candidates_token_count_median"])
        self.assertEqual(summary["candidates_token_count_missing"], 2)

    def test_report_only_reuses_logs_with_no_key_sdk_or_api_calls(self):
        plan = self.plan()
        _, _, _, _, run_dir, _ = self.run_fake(plan, [answer(), answer()], [2.0, 4.0])
        raw_before = (run_dir / "responses.jsonl").read_bytes()
        output = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), no_sdk_or_network(), \
                mock.patch.object(benchmark, "run_experiment", side_effect=AssertionError("Unexpected API run")), \
                redirect_stdout(output):
            code = benchmark.main(["--report", str(run_dir)])
        self.assertEqual(code, 0)
        self.assertEqual((run_dir / "responses.jsonl").read_bytes(), raw_before)
        with (run_dir / "summary.csv").open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([float(row["elapsed_seconds_median"]) for row in rows], [2.0, 4.0])

    def test_empty_log_produces_an_unmeasured_report_without_zero_measurements(self):
        plan = self.plan()
        run_dir = self.prepare_run(plan)
        with no_sdk_or_network():
            report = benchmark.generate_report(run_dir)
        self.assertIn("実行状態：未実測", report.read_text(encoding="utf-8"))
        with (run_dir / "summary.csv").open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row["attempted"], "0")
            self.assertEqual(row["elapsed_seconds_median"], "")
            self.assertEqual(row["prompt_token_count_median"], "")
        self.assertFalse((run_dir / "responses.jsonl").exists())

    def test_existing_result_directory_is_protected_before_sdk_import(self):
        target = self.root / "existing"
        target.mkdir()
        sentinel = target / "keep.txt"
        sentinel.write_text("previous experiment", encoding="utf-8")
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "not-a-real-key"}, clear=True), \
                mock.patch.object(benchmark.importlib.metadata, "version", return_value=benchmark.SDK_VERSION), \
                no_sdk_or_network(), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = benchmark.main(["--run-dir", str(target)])
        self.assertNotEqual(code, 0)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "previous experiment")
        self.assertEqual([path.name for path in target.iterdir()], ["keep.txt"])

    def test_interrupt_saves_partial_evidence_and_does_not_call_next_trial(self):
        plan = self.plan()
        state, records, client, _, run_dir, _ = self.run_fake(plan, [KeyboardInterrupt(), answer()])
        self.assertEqual(state["status"], "interrupted")
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(records[0]["status"], "interrupted")
        self.assertTrue((run_dir / "run.json").is_file())
        self.assertTrue((run_dir / "summary.csv").is_file())
        self.assertIn("部分実測", (run_dir / "answer.generated.md").read_text(encoding="utf-8"))


@unittest.skipUnless(sdk_available(), "Optional google-genai SDK is not installed")
class RealSdkOfflineTests(unittest.TestCase):
    def test_real_sdk_response_maps_tokens_and_finish_enum_without_network(self):
        import httpx
        from google import genai
        from google.genai import types

        calls = []

        def handle(request):
            calls.append(request)
            return httpx.Response(200, json={
                "candidates": [{"content": {"role": "model", "parts": [{"text": "模擬回答"}]},
                                "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5,
                                  "thoughtsTokenCount": 3, "totalTokenCount": 18},
                "modelVersion": "fixture-sdk-model-version",
            })

        http = httpx.Client(transport=httpx.MockTransport(handle))
        client = genai.Client(api_key="not-a-real-key", vertexai=False,
                              http_options=types.HttpOptions(httpx_client=http,
                                                            retry_options=types.HttpRetryOptions(attempts=1)))
        self.addCleanup(client.close)
        response = client.models.generate_content(model="fixture-model", contents="fixture prompt")
        trial = benchmark.build_trials(["fixture-model"], ["short"], 1)[0]
        record = benchmark.response_record(trial, response, "fixture-time", 1.25)
        self.assertEqual(len(calls), 1)
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["finish_reason"], "STOP")
        self.assertEqual(record["response_text"], "模擬回答")
        self.assertEqual(record["prompt_token_count"], 10)
        self.assertEqual(record["candidates_token_count"], 5)
        self.assertEqual(record["thoughts_token_count"], 3)
        self.assertEqual(record["total_token_count"], 18)
        self.assertIsNone(record["cached_content_token_count"])
        self.assertEqual(record["model_version"], "fixture-sdk-model-version")

    def test_cli_real_sdk_429_uses_one_http_attempt_and_redacts_provider_message(self):
        import httpx
        from google import genai
        from google.genai import types

        secret = "DUMMY_SDK_SECRET_MUST_NOT_APPEAR"
        calls, settings = [], []
        real_client = genai.Client

        def handle(request):
            calls.append(request)
            return httpx.Response(429, json={"error": {
                "code": 429, "message": f"fixture quota error with key={secret}",
                "status": "RESOURCE_EXHAUSTED",
            }})

        def client_factory(*args, **kwargs):
            options = kwargs["http_options"]
            settings.append((options.retry_options.attempts, options.timeout))
            kwargs["http_options"] = types.HttpOptions(
                timeout=options.timeout, retry_options=options.retry_options,
                httpx_client=httpx.Client(transport=httpx.MockTransport(handle)),
            )
            return real_client(*args, **kwargs)

        with tempfile.TemporaryDirectory(prefix="day1-sdk-test-") as directory:
            target = Path(directory) / "run"
            output = io.StringIO()
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": secret}, clear=True), \
                    mock.patch.object(genai, "Client", side_effect=client_factory), \
                    redirect_stdout(output), redirect_stderr(output):
                code = benchmark.main([
                    "--models", "model-a", "model-b", "--question-ids", "short",
                    "--repeats", "1", "--interval", "0", "--timeout", "7.5", "--run-dir", str(target),
                ])
            self.assertEqual(code, 1)
            self.assertEqual(settings, [(1, 7500)])
            self.assertEqual(len(calls), 1)
            records, warnings = benchmark.load_records(target)
            self.assertEqual(warnings, [])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["status"], "error")
            self.assertEqual(records[0]["http_code"], 429)
            contents = output.getvalue() + "".join(path.read_text(encoding="utf-8") for path in target.iterdir())
            self.assertNotIn(secret, contents)


if __name__ == "__main__":
    unittest.main()
