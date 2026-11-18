"""Offline contract tests; all provider I/O is mocked."""

import io
import json
import math
import unittest
import urllib.error
from unittest.mock import Mock

from day5_lab.gemini import (
    ApiError, DEFAULT_MODEL, GeminiClient, estimate_cost, parse_usage, prompt_for,
)


KEY = "AIza" + "private_test_key_" * 3


def page(**extra):
    return {
        "page_id": "lec02-main-p052", "lecture": 2, "page": 52,
        "document_title": "講義", "section": "学習", "title": "LoRA",
        "content": "元の重みは固定し、小さな行列を学習する。", **extra,
    }


def response(data):
    handle = Mock()
    handle.__enter__ = Mock(return_value=handle)
    handle.__exit__ = Mock(return_value=False)
    handle.read.return_value = json.dumps(data).encode("utf-8")
    return handle


def generation(**extra):
    return {
        "candidates": [{"content": {"parts": [{"text": "元の重みは固定します（第2回・PDF p.52）。"}]}, "finishReason": "STOP"}],
        "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 10, "totalTokenCount": 130},
        "modelVersion": DEFAULT_MODEL, **extra,
    }


class GeminiTests(unittest.TestCase):
    def client(self, data):
        client = GeminiClient(KEY)
        client._open = Mock(return_value=response(data))
        return client

    def test_embedding_request_and_normalization(self):
        client = self.client({"embedding": {"values": [3.0, 4.0] + [0.0] * 766}})
        result = client.embed("LoRAとは？")
        request = client._open.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertNotIn(KEY, request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), KEY)
        payload = json.loads(request.data)
        self.assertEqual(payload["taskType"], "RETRIEVAL_QUERY")
        self.assertEqual(payload["outputDimensionality"], 768)
        self.assertIn("gemini-embedding-001:embedContent", request.full_url)
        self.assertAlmostEqual(result["vector"][0], 0.6)
        self.assertAlmostEqual(math.hypot(*result["vector"]), 1)
        self.assertEqual(client._open.call_count, 1)

    def test_embedding_invalid_dimension_and_zero(self):
        for values in ([1.0] * 767, [0.0] * 768):
            with self.subTest(length=len(values)):
                client = self.client({"embedding": {"values": values}})
                with self.assertRaises(ApiError):
                    client.embed("質問")
                self.assertEqual(client._open.call_count, 1)

    def test_prompt_does_not_include_ranking_or_gold(self):
        p = page(distance=0.0123, method="graph", gold="SECRET_GOLD", provenance="SECRET_PATH")
        prompt = prompt_for("質問", [p])
        self.assertNotIn("SECRET_GOLD", prompt)
        self.assertNotIn("SECRET_PATH", prompt)
        self.assertNotIn("distance", prompt)
        self.assertEqual(prompt, prompt_for("質問", [page()]))

    def test_generate_common_request_and_thoughts_not_stored(self):
        data = generation()
        data["candidates"][0]["content"]["parts"].insert(0, {"thought": True, "text": "PRIVATE_THOUGHT"})
        client = self.client(data)
        result = client.generate("LoRAとは？", [page()])
        request = client._open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["generationConfig"]["temperature"], 0)
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 4096)
        self.assertNotIn("PRIVATE_THOUGHT", json.dumps(result))
        self.assertNotIn(KEY, json.dumps(result))
        self.assertEqual(result["usage"]["thinking_tokens"], 10)
        self.assertEqual(result["cost_estimate"]["status"], "estimated")
        self.assertAlmostEqual(result["cost_estimate"]["usd"], (100 * 0.30 + 30 * 2.50) / 1_000_000)

    def test_cached_input_discount_and_thinking_cost(self):
        usage = parse_usage({"promptTokenCount": 1000, "candidatesTokenCount": 200, "thoughtsTokenCount": 300,
                             "cachedContentTokenCount": 400, "totalTokenCount": 1500})
        cost = estimate_cost(DEFAULT_MODEL, usage)
        self.assertAlmostEqual(cost["usd"], (600 * 0.30 + 400 * 0.03 + 500 * 2.50) / 1_000_000)

    def test_missing_counts_stay_null_and_cost_unknown(self):
        usage = parse_usage({})
        self.assertIsNone(usage["input_tokens"])
        self.assertIsNone(usage["thinking_tokens"])
        self.assertIsNone(estimate_cost(DEFAULT_MODEL, usage)["usd"])
        self.assertIsNone(estimate_cost("other-model", parse_usage(generation()["usageMetadata"]))["usd"])

    def test_missing_thinking_only_inferred_zero_if_total_confirms(self):
        known_zero = parse_usage({"promptTokenCount": 100, "candidatesTokenCount": 20, "totalTokenCount": 120})
        self.assertIsNone(known_zero["thinking_tokens"])
        self.assertEqual(estimate_cost(DEFAULT_MODEL, known_zero)["status"], "estimated")
        uncertain = parse_usage({"promptTokenCount": 100, "candidatesTokenCount": 20, "totalTokenCount": 150})
        self.assertIsNone(estimate_cost(DEFAULT_MODEL, uncertain)["usd"])

    def test_inconsistent_counts_do_not_produce_cost(self):
        cases = [
            {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 10, "totalTokenCount": 140},
            {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 10, "cachedContentTokenCount": 101},
            {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": -1, "totalTokenCount": 120},
            {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 0, "cachedContentTokenCount": "wrong"},
        ]
        for metadata in cases:
            self.assertIsNone(estimate_cost(DEFAULT_MODEL, parse_usage(metadata))["usd"])

    def test_truncated_answer_retained_as_partial_not_success(self):
        data = generation()
        data["candidates"][0]["finishReason"] = "MAX_TOKENS"
        client = self.client(data)
        with self.assertRaises(ApiError) as caught:
            client.generate("質問", [page()])
        partial = caught.exception.partial_result
        self.assertEqual(partial["finish_reason"], "MAX_TOKENS")
        self.assertTrue(partial["answer"])
        self.assertEqual(client._open.call_count, 1)

    def test_blocked_and_empty_answers_fail(self):
        blocked = generation(candidates=[], promptFeedback={"blockReason": "SAFETY"})
        empty = generation(candidates=[{"finishReason": "STOP", "content": {"parts": []}}])
        malformed = generation(candidates=[{"finishReason": "STOP", "content": {"parts": None}}])
        for data in (blocked, empty, malformed):
            with self.assertRaises(ApiError) as caught:
                self.client(data).generate("質問", [page()])
            self.assertIsNotNone(caught.exception.partial_result)

    def test_http_error_is_sanitized_and_not_retried(self):
        client = self.client({})
        raw = json.dumps({"error": {"message": "Bad key " + KEY}}).encode()
        client._open.side_effect = urllib.error.HTTPError("https://example.invalid", 403, "Forbidden", {}, io.BytesIO(raw))
        with self.assertRaises(ApiError) as caught:
            client.generate("質問", [page()])
        self.assertNotIn(KEY, str(caught.exception))
        self.assertIn("[API_KEY_REDACTED]", str(caught.exception))
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(client._open.call_count, 1)

    def test_model_validation_before_network(self):
        client = self.client({})
        for model in ("models/name", "../secret", "name?key=leak", "name\nheader"):
            with self.assertRaises(ValueError):
                client.generate("質問", [page()], model=model)
        client._open.assert_not_called()

    def test_invalid_question_before_network(self):
        client = self.client({})
        for question in ("", " " * 2, "x" * 2001):
            with self.assertRaises(ValueError):
                client.embed(question)
        client._open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
