"""Normalize the two Day3 CLI logs without making model or network calls.

ADK 2.13's ``run_once --jsonl`` emits public Event dictionaries with camelCase
fields.  Keep the event log separate from the derived answer and usage: an
event count is not an HTTP request count, and absent token metadata is not zero.
"""

from __future__ import annotations

import json
from typing import Any


def empty_result(note: str = "") -> dict[str, Any]:
    return {
        "status": "failed",
        "final_answer": "",
        "tool_calls": [],
        "tool_results": [],
        "usage": {
            "requests": None,
            "input_tokens": None,
            "output_tokens": None,
            "model_response_events": None,
            "measurement_note": note,
        },
        "errors": [],
        "events": [],
    }


def _field(value: dict, camel: str, snake: str) -> Any:
    return value.get(camel, value.get(snake))


def _count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _call_id(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _parts(event: dict) -> list[dict]:
    content = event.get("content")
    if not isinstance(content, dict) or not isinstance(content.get("parts"), list):
        return []
    return [p for p in content["parts"] if isinstance(p, dict) and p.get("thought") is not True]


def parse_adk_jsonl(text: str) -> dict[str, Any]:
    """Parse ADK's single-question log; process exit status is checked by caller.

    Non-JSON stdout is retained as an event and is not itself a failure.  Only a
    complete model text event without function calls/responses, unresolved tool
    calls, or a failure finish reason can supply the final answer.  Streaming
    partials are retained but never counted twice or treated as an answer.
    """
    result = empty_result(
        "ADK requests は未取得。model_response_events は partial でない role=model の"
        "出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens は"
        "その全イベントの usageMetadata が各項目について揃う場合だけ合計する。"
        "candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。"
    )
    responses: list[dict] = []
    pending: list[dict] = []
    answer = ""
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            event = None
        if not isinstance(event, dict):
            result["events"].append({"kind": "stdout", "text": line})
            continue
        # The original stdout is saved by the caller. Do not copy thought text
        # into the normalized, user-facing record.
        content = event.get("content")
        parts = _parts(event)
        if isinstance(content, dict) and isinstance(content.get("parts"), list):
            event = {**event, "content": {**content, "parts": parts}}
        result["events"].append(event)
        code = _field(event, "errorCode", "error_code")
        message = _field(event, "errorMessage", "error_message")
        if code or message:
            result["errors"].append(f"ADK error {code or ''}: {message or ''}".strip())
            answer = ""
        if event.get("interrupted"):
            result["errors"].append("ADK response was interrupted.")
            answer = ""
        if event.get("partial") is True:
            if isinstance(content, dict) and content.get("role") == "model" and event.get("author") != "user":
                answer = ""
            continue

        is_model = isinstance(content, dict) and content.get("role") == "model" and event.get("author") != "user"
        if is_model:
            responses.append(event)
            # A subsequent tool call/empty model response invalidates an earlier
            # text candidate; do not publish a stale intermediate answer.
            answer = ""

        has_call = False
        has_response = False
        for part in parts:
            call = _field(part, "functionCall", "function_call")
            if isinstance(call, dict):
                has_call = True
                if is_model:
                    arguments = call.get("args", {})
                    if not isinstance(arguments, (dict, str)):
                        arguments = json.dumps(arguments, ensure_ascii=False)
                    normalized = {
                        "name": str(call.get("name", "")),
                        "arguments": arguments,
                        "call_id": _call_id(call.get("id")),
                    }
                    result["tool_calls"].append(normalized)
                    pending.append(normalized)
            response = _field(part, "functionResponse", "function_response")
            if isinstance(response, dict):
                has_response = True
                normalized = {
                    "name": str(response.get("name", "")),
                    "result": response.get("response"),
                    "call_id": _call_id(response.get("id")),
                }
                result["tool_results"].append(normalized)
                for index, call in enumerate(pending):
                    id_matches = normalized["call_id"] is not None and call["call_id"] == normalized["call_id"]
                    name_matches = (normalized["call_id"] is None or call["call_id"] is None) and call["name"] == normalized["name"]
                    if id_matches or name_matches:
                        pending.pop(index)
                        break

        finish = _field(event, "finishReason", "finish_reason")
        bad_finish = finish not in (None, "", "STOP", "FINISH_REASON_UNSPECIFIED")
        if is_model and bad_finish:
            result["errors"].append(f"ADK finishReason={finish}; a complete final answer was not confirmed.")
        trailing_code = bool(parts and _field(parts[-1], "codeExecutionResult", "code_execution_result") is not None)
        if is_model and not (has_call or has_response or pending or bad_finish or trailing_code or code or message or event.get("interrupted")):
            answer = "".join(p["text"] for p in parts if isinstance(p.get("text"), str)).strip()

    result["final_answer"] = answer
    result["usage"]["model_response_events"] = len(responses)
    for field, camel, snake in [
        ("input_tokens", "promptTokenCount", "prompt_token_count"),
        ("output_tokens", "candidatesTokenCount", "candidates_token_count"),
    ]:
        counts = []
        for event in responses:
            metadata = _field(event, "usageMetadata", "usage_metadata")
            counts.append(_count(_field(metadata, camel, snake)) if isinstance(metadata, dict) else None)
        if counts and all(value is not None for value in counts):
            result["usage"][field] = sum(counts)
    if pending:
        result["errors"].append("ADK tool calls have no matching result: " + ", ".join(call["name"] for call in pending))
    if not answer:
        result["errors"].append("ADK complete final answer was not found.")
    result["errors"] = list(dict.fromkeys(result["errors"]))
    result["status"] = "completed" if answer and not result["errors"] else "failed"
    return result


def parse_pydantic_json(text: str) -> dict[str, Any]:
    """Validate the worker's JSON object, retaining unrelated stdout as events."""
    result = empty_result("Pydantic worker の使用量を採用。取得できない項目は null。")
    noise: list[dict] = []
    try:
        value = json.loads(text)
        candidates = [value] if isinstance(value, dict) else []
    except (json.JSONDecodeError, ValueError):
        candidates = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                value = None
            if isinstance(value, dict) and "status" in value and "final_answer" in value:
                candidates.append(value)
            else:
                noise.append({"kind": "stdout", "text": line})
    if len(candidates) != 1:
        result["errors"].append("Expected exactly one Pydantic worker JSON object.")
        result["events"] = noise or [{"kind": "stdout", "text": text}]
        return result
    payload = candidates[0]
    errors = result["errors"]
    if payload.get("status") not in ("completed", "failed"):
        errors.append("Invalid Pydantic worker status.")
    if isinstance(payload.get("final_answer"), str):
        result["final_answer"] = payload["final_answer"]
    else:
        errors.append("Pydantic final_answer must be a string.")
    for key in ("tool_calls", "tool_results", "events"):
        rows = payload.get(key)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            errors.append(f"Pydantic {key} must be a list of objects.")
        else:
            result[key] = rows
    for row in result["tool_calls"] + result["tool_results"]:
        if not isinstance(row.get("name"), str) or (row.get("call_id") is not None and not isinstance(row["call_id"], str)):
            errors.append("Invalid Pydantic tool name or call_id.")
    if any(not isinstance(row.get("arguments"), (dict, str)) for row in result["tool_calls"]):
        errors.append("Invalid Pydantic tool arguments.")
    if any("result" not in row for row in result["tool_results"]):
        errors.append("Missing Pydantic tool result.")
    usage = payload.get("usage")
    if isinstance(usage, dict):
        for key in ("requests", "input_tokens", "output_tokens", "model_response_events"):
            raw = usage.get(key)
            result["usage"][key] = _count(raw)
            if raw is not None and result["usage"][key] is None:
                errors.append(f"Invalid Pydantic usage.{key}.")
        if isinstance(usage.get("measurement_note"), str):
            result["usage"]["measurement_note"] = usage["measurement_note"]
    else:
        errors.append("Pydantic usage must be an object.")
    worker_errors = payload.get("errors")
    if isinstance(worker_errors, list) and all(isinstance(error, str) for error in worker_errors):
        errors.extend(worker_errors)
    else:
        errors.append("Pydantic errors must be a list of strings.")
    result["events"].extend(noise)
    if payload.get("status") == "completed" and not result["final_answer"].strip():
        errors.append("Pydantic complete final answer was not found.")
    if payload.get("status") == "failed" and not errors:
        errors.append("Pydantic worker reported failure.")
    result["status"] = "completed" if payload.get("status") == "completed" and not errors else "failed"
    return result
