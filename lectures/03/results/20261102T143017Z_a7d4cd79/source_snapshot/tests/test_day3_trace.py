"""Offline checks for evidence parsing and the real pinned SDK/CLI boundary.

The SDK integration tests replace model generation or HTTP with local fixtures.
They never use a real API key or send a model request to an external service.
"""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.day3_trace import empty_result, parse_adk_jsonl, parse_pydantic_json


def event(parts, *, role="model", usage=None, **extra):
    item = {"author": "glossary_agent", "content": {"role": role, "parts": parts}, **extra}
    if usage is not None:
        item["usageMetadata"] = usage
    return item


def jsonl(*events):
    return "\n".join(json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else item for item in events)


def tokens(prompt, output):
    return {"promptTokenCount": prompt, "candidatesTokenCount": output}


CALL = {"functionCall": {"name": "search_glossary", "args": {"query": "LoRA"}, "id": "call-1"}}
RETURN = {"functionResponse": {"name": "search_glossary", "response": {"result": "用語集の定義"}, "id": "call-1"}}


class TraceParserTests(unittest.TestCase):
    def test_adk_camelcase_calls_results_and_final_answer(self):
        result = parse_adk_jsonl(jsonl(
            event([CALL, {"text": "調べます"}], usage=tokens(10, 2)),
            event([RETURN], role="user"),
            event([{"text": "回答です。第2回。"}], usage=tokens(30, 6), finishReason="STOP"),
        ))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_answer"], "回答です。第2回。")
        self.assertEqual(result["tool_calls"], [{"name": "search_glossary", "arguments": {"query": "LoRA"}, "call_id": "call-1"}])
        self.assertEqual(result["tool_results"][0]["result"], {"result": "用語集の定義"})
        self.assertIsNone(result["usage"]["requests"])
        self.assertEqual(result["usage"]["model_response_events"], 2)
        self.assertEqual(result["usage"]["input_tokens"], 40)
        self.assertEqual(result["usage"]["output_tokens"], 8)

    def test_missing_usage_is_not_zero_or_a_partial_sum(self):
        result = parse_adk_jsonl(jsonl(
            event([CALL], usage=tokens(10, 2)),
            event([RETURN], role="user"),
            event([{"text": "回答"}], usage={"promptTokenCount": 0}),
        ))
        self.assertEqual(result["usage"]["input_tokens"], 10)
        self.assertIsNone(result["usage"]["output_tokens"])
        zero = parse_adk_jsonl(jsonl(event([{"text": "fixture"}], usage=tokens(0, 0))))
        self.assertEqual(zero["usage"]["input_tokens"], 0)
        self.assertEqual(zero["usage"]["output_tokens"], 0)
        absent = parse_adk_jsonl(jsonl(event([{"text": "回答"}])))
        self.assertIsNone(absent["usage"]["input_tokens"])

    def test_call_with_text_and_unresolved_call_are_not_final_answers(self):
        for events in [
            [event([CALL, {"text": "検索します"}])],
            [event([CALL]), event([{"text": "結果をまだ受け取っていない文章"}])],
            [event([{"text": "以前の候補"}]), event([CALL])],
        ]:
            with self.subTest(events=events):
                result = parse_adk_jsonl(jsonl(*events))
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["final_answer"], "")
                self.assertTrue(result["errors"])

    def test_thought_parts_are_not_user_facing_answers_or_events(self):
        result = parse_adk_jsonl(jsonl(event([
            {"text": "内部の思考", "thought": True}, {"text": "公開回答"},
        ])))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_answer"], "公開回答")
        self.assertNotIn("内部の思考", json.dumps(result, ensure_ascii=False))
        thought_only = parse_adk_jsonl(jsonl(event([{"text": "思考", "thought": True}])))
        self.assertEqual(thought_only["status"], "failed")

    def test_partial_events_are_kept_but_not_double_counted(self):
        result = parse_adk_jsonl(jsonl(
            event([CALL], partial=True, usage=tokens(999, 999)),
            event([CALL], usage=tokens(10, 2)),
            event([RETURN], role="user"),
            event([{"text": "途中"}], partial=True),
            event([{"text": "完成した回答"}], usage=tokens(20, 3)),
        ))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["events"]), 5)
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["usage"]["model_response_events"], 2)
        self.assertEqual(result["usage"]["input_tokens"], 30)
        self.assertEqual(parse_adk_jsonl(jsonl(event([{"text": "途中"}], partial=True)))["status"], "failed")
        self.assertEqual(parse_adk_jsonl(jsonl(event([{"text": "以前の候補"}]), event([CALL], partial=True)))["status"], "failed")

    def test_errors_and_truncation_cannot_be_completed(self):
        for failure in [
            {"author": "glossary_agent", "errorCode": "503", "errorMessage": "service unavailable"},
            event([{"text": "途切れた回答"}], finishReason="MAX_TOKENS"),
            event([{"text": "中断"}], interrupted=True),
        ]:
            with self.subTest(failure=failure):
                result = parse_adk_jsonl(jsonl(failure))
                self.assertEqual(result["status"], "failed")
                self.assertTrue(result["errors"])
        result = parse_adk_jsonl(jsonl(event([{"text": "一度出た文章"}]), failure))
        self.assertEqual(result["status"], "failed")

    def test_stdout_noise_is_retained_without_false_failure(self):
        result = parse_adk_jsonl(jsonl("Loaded agent.", "[notice] local logging", event([{"text": "回答"}])))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["events"][0], {"kind": "stdout", "text": "Loaded agent."})
        self.assertEqual(result["errors"], [])

    def test_pydantic_payload_keeps_explicit_zero_and_missing_values(self):
        payload = empty_result("fixture")
        payload.update(status="completed", final_answer="回答")
        payload["usage"].update(requests=1, input_tokens=0, model_response_events=1)
        result = parse_pydantic_json("Loaded fixture.\n" + json.dumps(payload))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["usage"]["input_tokens"], 0)
        self.assertIsNone(result["usage"]["output_tokens"])
        self.assertEqual(result["events"][-1]["kind"], "stdout")

    def test_pydantic_failure_and_invalid_completed_payload(self):
        payload = empty_result()
        payload["errors"] = ["ModelHTTPError: 429"]
        self.assertEqual(parse_pydantic_json(json.dumps(payload))["errors"], payload["errors"])
        payload.update(status="completed", errors=[])
        self.assertEqual(parse_pydantic_json(json.dumps(payload))["status"], "failed")
        payload["final_answer"] = "回答"
        payload["usage"]["requests"] = True
        self.assertEqual(parse_pydantic_json(json.dumps(payload))["status"], "failed")
        for text in ["not JSON", '{"status":"completed","final_answer":"回答"}', jsonl(payload, payload)]:
            with self.subTest(text=text):
                self.assertEqual(parse_pydantic_json(text)["status"], "failed")


try:
    HAS_SDK = importlib.util.find_spec("google.adk") is not None and importlib.util.find_spec("pydantic_ai") is not None
except ModuleNotFoundError:
    HAS_SDK = False


@unittest.skipUnless(HAS_SDK, "Optional: run with the pinned google-adk/course SDK environment")
class SDKIntegrationTests(unittest.TestCase):
    def test_check_requires_no_key_or_client_and_compares_both_agents(self):
        from scripts import day3_pydantic_worker as worker
        from adk_agent.glossary_agent.agent import root_agent

        with patch.dict(os.environ, {}, clear=True), patch("google.genai.Client", side_effect=AssertionError("No client in --check")):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = worker.main(["--check"])
            value = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(value["status"], "ready")
            self.assertEqual(value["tools"], ["search_glossary", "get_lecture_summary"])
            with patch.object(root_agent, "instruction", "different"):
                with self.assertRaisesRegex(ValueError, "instructions differ"):
                    worker.check_configuration()

    def _run_http_fixture(self, handler):
        import httpx
        from google import genai
        from scripts import day3_pydantic_worker as worker

        original_client = genai.Client

        def fixture_client(**kwargs):
            self.assertIs(kwargs["enterprise"], False)
            self.assertEqual(kwargs["http_options"].timeout, 60_000)
            self.assertEqual(kwargs["http_options"].retry_options.attempts, 1)
            kwargs["http_options"].httpx_async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            return original_client(**kwargs)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "offline-dummy-key"}), patch("google.genai.Client", side_effect=fixture_client), patch("socket.socket.connect", side_effect=AssertionError("External networking is prohibited")):
            return worker.run_question("LoRAとは？")

    def test_real_pydantic_sdk_records_tool_roundtrip_with_mock_http_only(self):
        import httpx

        requests = []

        def handler(request):
            requests.append(request)
            parts = [{"functionCall": {"name": "search_glossary", "args": {"query": "LoRA"}, "id": "fixture-call"}}] if len(requests) == 1 else [{"text": "fixture: LoRA の回答。第2回。"}]
            return httpx.Response(200, json={
                "candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4, "totalTokenCount": 14},
            })

        value = self._run_http_fixture(handler)
        self.assertEqual(value["status"], "completed", value["errors"])
        self.assertEqual(len(requests), 2)
        self.assertEqual(value["usage"]["requests"], 2)
        self.assertEqual(value["usage"]["model_response_events"], 2)
        self.assertEqual(value["usage"]["input_tokens"], 20)
        self.assertEqual(value["usage"]["output_tokens"], 8)
        self.assertEqual(value["tool_calls"][0]["arguments"], {"query": "LoRA"})
        self.assertEqual(value["tool_results"][0]["name"], "search_glossary")
        self.assertEqual(parse_pydantic_json(json.dumps(value))["status"], "completed")

    def test_http_429_is_not_retried_and_error_does_not_expose_key(self):
        import httpx

        requests = []

        def handler(request):
            requests.append(request)
            return httpx.Response(429, json={"error": {"code": 429, "message": "fixture offline-dummy-key", "status": "RESOURCE_EXHAUSTED"}})

        value = self._run_http_fixture(handler)
        self.assertEqual(value["status"], "failed")
        self.assertEqual(len(requests), 1)
        self.assertEqual(value["final_answer"], "")
        self.assertIsNone(value["usage"]["input_tokens"])
        self.assertNotIn("offline-dummy-key", json.dumps(value))
        self.assertTrue(any("429" in error for error in value["errors"]))

    def test_worker_missing_sdk_metadata_does_not_report_measured_zero(self):
        import httpx

        def handler(request):
            return httpx.Response(200, json={
                "candidates": [{"content": {"role": "model", "parts": [{"text": "fixture"}]}, "finishReason": "STOP"}],
            })

        value = self._run_http_fixture(handler)
        self.assertEqual(value["status"], "completed", value["errors"])
        self.assertEqual(value["usage"]["requests"], 1)
        self.assertIsNone(value["usage"]["input_tokens"])
        self.assertIsNone(value["usage"]["output_tokens"])

    def test_worker_retains_tool_evidence_when_followup_request_fails(self):
        import httpx

        requests = []

        def handler(request):
            requests.append(request)
            if len(requests) == 1:
                return httpx.Response(200, json={
                    "candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": "search_glossary", "args": {"query": "LoRA"}}}]}, "finishReason": "STOP"}],
                    "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4, "totalTokenCount": 14},
                })
            return httpx.Response(503, json={"error": {"code": 503, "message": "fixture unavailable", "status": "UNAVAILABLE"}})

        value = self._run_http_fixture(handler)
        self.assertEqual(value["status"], "failed")
        self.assertEqual(len(requests), 2)
        self.assertEqual(len(value["tool_calls"]), 1)
        self.assertEqual(len(value["tool_results"]), 1)
        self.assertEqual(value["final_answer"], "")
        self.assertIsNone(value["usage"]["input_tokens"])
        self.assertTrue(any("503" in error for error in value["errors"]))

    def test_real_adk_cli_jsonl_with_fake_model_and_real_local_tool(self):
        from click.testing import CliRunner
        from google.adk.agents.run_config import RunConfig
        from google.adk.cli.cli_tools_click import main
        from google.adk.models import Gemini
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types

        calls = []

        async def fake_generate(self, llm_request, stream=False):
            calls.append(llm_request)
            parts = [types.Part(text="検索します"), types.Part(function_call=types.FunctionCall(name="search_glossary", args={"query": "LoRA"}, id="fixture-call"))] if len(calls) == 1 else [types.Part(text="fixture: 用語集に基づく回答。第2回。")]
            yield LlmResponse(
                content=types.Content(role="model", parts=parts),
                usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=10, candidates_token_count=4),
                finish_reason=types.FinishReason.STOP,
            )

        agent_path = Path(__file__).resolve().parents[1] / "adk_agent" / "glossary_agent"
        with patch.dict(os.environ, {"ADK_MAX_LLM_CALLS": "8"}), patch.object(Gemini, "generate_content_async", fake_generate), patch("google.genai.Client", side_effect=AssertionError("Fake model must not create an API client")), patch("socket.socket.connect", side_effect=AssertionError("External networking is prohibited")), patch("google.adk.cli.cli_tools_click.logs.log_to_tmp_folder"):
            self.assertEqual(RunConfig().max_llm_calls, 8)
            invoked = CliRunner().invoke(main.commands["run"], ["--in_memory", "--no_use_local_storage", "--jsonl", "--timeout", "10s", str(agent_path), "LoRAとは？"])
        self.assertEqual(invoked.exit_code, 0, f"{invoked.output}\n{invoked.exception!r}")
        parsed = parse_adk_jsonl(invoked.stdout)
        self.assertEqual(parsed["status"], "completed", parsed)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(parsed["tool_calls"]), 1)
        self.assertEqual(len(parsed["tool_results"]), 1)
        self.assertEqual(parsed["tool_calls"][0]["arguments"], {"query": "LoRA"})
        self.assertEqual(parsed["final_answer"], "fixture: 用語集に基づく回答。第2回。")
        self.assertEqual(parsed["usage"]["input_tokens"], 20)
        self.assertEqual(parsed["usage"]["output_tokens"], 8)
        self.assertIsNone(parsed["usage"]["requests"])
        self.assertEqual(parsed["usage"]["model_response_events"], 2)


if __name__ == "__main__":
    unittest.main()
