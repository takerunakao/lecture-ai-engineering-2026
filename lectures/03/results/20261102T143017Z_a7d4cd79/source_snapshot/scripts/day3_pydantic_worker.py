"""Run one Day3 question in a fresh Pydantic AI process, or check without a key.

The course agent, instructions and registered function tools are imported intact.
Only transport retry/time limits and observation are configured here.  This
worker writes one JSON object to stdout; incidental library output goes to stderr.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stdout
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.day3_trace import empty_result


def _error_message(exc: BaseException) -> str:
    message = f"{type(exc).__name__}: {exc}"
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        secret = os.getenv(name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message


def check_configuration() -> dict[str, Any]:
    """Inspect both configurations without constructing an API client."""
    from app import tools
    from app.agent import INSTRUCTIONS, agent
    from app.config import MODEL
    from adk_agent.glossary_agent.agent import root_agent

    registered = agent._function_toolset.tools  # Checked against pinned Pydantic AI 2.57.
    names = list(registered)
    required = {"search_glossary", "get_lecture_summary"}
    if not required.issubset(registered) or not set(registered).issubset(required | {"make_quiz"}):
        raise ValueError("Unexpected course-agent tool registration; review both configurations.")
    functions = [registered[name].function for name in names]
    if any(function is not getattr(tools, name, None) for name, function in zip(names, functions)):
        raise ValueError("A registered Pydantic tool is not the original app.tools function.")
    if [item.instruction for item in agent._instructions] != [INSTRUCTIONS]:
        raise ValueError("The Pydantic agent instructions differ from app.agent.INSTRUCTIONS.")
    if root_agent.instruction != INSTRUCTIONS:
        raise ValueError("ADK and Pydantic instructions differ.")
    if len(root_agent.tools) != len(functions) or any(
        left is not right for left, right in zip(root_agent.tools, functions)
    ):
        raise ValueError("ADK and Pydantic tool functions/order differ (including optional make_quiz).")
    adk_model = root_agent.model if isinstance(root_agent.model, str) else root_agent.model.model
    if adk_model != MODEL:
        raise ValueError("ADK and Pydantic model names differ.")
    versions = {"python": platform.python_version()}
    for package in ("pydantic-ai-slim", "google-genai", "google-adk", "httpx"):
        versions[package] = importlib.metadata.version(package)
    return {
        "status": "ready",
        "model": MODEL,
        "versions": versions,
        "instructions_sha256": hashlib.sha256(INSTRUCTIONS.encode("utf-8")).hexdigest(),
        "tools": names,
    }


def _messages_into_record(record: dict, messages: list) -> None:
    from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelResponse, ToolCallPart, ToolReturnPart

    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                arguments = part.args
                if not isinstance(arguments, (dict, str)):
                    arguments = json.dumps(arguments, ensure_ascii=False)
                record["tool_calls"].append({
                    "name": part.tool_name,
                    "arguments": arguments,
                    "call_id": part.tool_call_id or None,
                })
            elif isinstance(part, ToolReturnPart):
                record["tool_results"].append({
                    "name": part.tool_name,
                    "result": part.content,
                    "call_id": part.tool_call_id or None,
                })
    serialized = ModelMessagesTypeAdapter.dump_python(messages, mode="json")
    for event in serialized:
        # Keep useful call/return/text evidence, without thought or system text.
        event["parts"] = [
            part for part in event.get("parts", [])
            if part.get("part_kind") in {"tool-call", "tool-return", "text", "retry-prompt"}
        ]
        if event["parts"]:
            event.pop("instructions", None)
            record["events"].append(event)
    record["usage"]["model_response_events"] = sum(isinstance(message, ModelResponse) for message in messages)


async def _invoke(question: str, model: Any, usage: Any, client: Any) -> Any:
    from app.agent import agent
    from pydantic_ai.usage import UsageLimits

    async with client.aio:
        async with asyncio.timeout(120):
            # No message_history: one fresh question in each worker process.
            return await agent.run(
                question,
                model=model,
                usage=usage,
                usage_limits=UsageLimits(request_limit=8),
            )


def run_question(question: str) -> dict[str, Any]:
    """Run once; retain captured tool events when a request or limit fails."""
    record = empty_result(
        "requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。"
        "input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。"
        "SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は"
        "思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。"
    )
    captured: list = []
    messages: list = []
    client = None
    usage = None
    try:
        from google import genai
        from google.genai.types import HttpOptions, HttpRetryOptions
        from pydantic_ai import capture_run_messages
        from pydantic_ai.messages import ModelResponse
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
        from pydantic_ai.usage import RunUsage
        from app.config import MODEL

        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured; --check needs no key.")
        usage = RunUsage()
        client = genai.Client(
            api_key=key,
            enterprise=False,
            http_options=HttpOptions(timeout=60_000, retry_options=HttpRetryOptions(attempts=1)),
        )
        model = GoogleModel(MODEL, provider=GoogleProvider(client=client))
        with capture_run_messages() as captured:
            result = asyncio.run(_invoke(question, model, usage, client))
        messages = result.all_messages()
        if not isinstance(result.output, str) or not result.output.strip():
            raise ValueError("Pydantic complete final answer was not found.")
        response_messages = [message for message in messages if isinstance(message, ModelResponse)]
        if response_messages and response_messages[-1].finish_reason not in (None, "stop"):
            raise ValueError(f"Pydantic incomplete final response: {response_messages[-1].finish_reason}")
        record["final_answer"] = result.output
        record["status"] = "completed"
        # Do not turn SDK defaults for absent metadata into measured zero.
        for name in ("input_tokens", "output_tokens"):
            counts = [getattr(message.usage, name, None) for message in response_messages]
            total = getattr(result.usage, name, None)
            if counts and all(type(value) is int and value > 0 for value in counts) and type(total) is int and total > 0:
                record["usage"][name] = total
    except (Exception, KeyboardInterrupt) as exc:
        record["errors"].append(_error_message(exc))
        record["status"] = "failed"
    finally:
        if not messages:
            messages = captured
        if usage is not None:
            value = usage.requests
            record["usage"]["requests"] = value if type(value) is int and value >= 0 else None
        if messages:
            try:
                _messages_into_record(record, messages)
            except Exception as exc:
                record["errors"].append("Could not serialize observed messages: " + _error_message(exc))
                record["status"] = "failed"
        elif usage is not None:
            record["usage"]["model_response_events"] = 0
        if client is not None:
            try:
                client.close()
            except Exception as exc:
                record["errors"].append("Client close failed: " + _error_message(exc))
                record["status"] = "failed"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?")
    parser.add_argument("--check", action="store_true", help="Check shared configuration without a key or model call")
    args = parser.parse_args(argv)
    with redirect_stdout(sys.stderr):
        try:
            if args.check:
                result = check_configuration()
            elif not args.question or not args.question.strip():
                raise ValueError("Provide one non-empty question, or use --check.")
            else:
                result = run_question(args.question)
        except (Exception, KeyboardInterrupt) as exc:
            result = empty_result()
            result["errors"].append(_error_message(exc))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in ("ready", "completed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
