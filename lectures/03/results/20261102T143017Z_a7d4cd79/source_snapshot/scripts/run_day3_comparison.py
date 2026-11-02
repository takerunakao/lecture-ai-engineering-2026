"""4問×2実装の比較を、本人のGemini APIで実行して記録する。

--check は構成の確認だけで、モデルAPIは呼ばない。
通常実行では失敗を保存して停止する。再実行は別の実行IDとして保存する。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid

from day3_report import SOURCE_PATHS, build_archive, save_result
from day3_trace import parse_adk_jsonl, parse_pydantic_json

ROOT = Path(__file__).resolve().parents[1]
UV = ["uv", "run", "--frozen", "--with", "google-adk==2.13.0"]


def redact(text: str) -> str:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(name)
        if value:
            text = text.replace(value, "[REDACTED]")
    # SDKがURLやHTTPヘッダーをエラーへ含めた場合の補助。環境変数一覧は記録しない。
    text = re.sub(r"(?i)([?&](?:key|api_key)=)[^\s&\"']+", r"\1[REDACTED]", text)
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", text)
    return text


def child_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("GOOGLE_API_KEY", None)
    env.update({
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "GOOGLE_GENAI_USE_VERTEXAI": "false",
        "ADK_MAX_LLM_CALLS": "8",
        "ADK_DISABLE_LOCAL_STORAGE": "1",
        "OTEL_SDK_DISABLED": "true",
    })
    return env


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)


def execute(command: list[str], timeout: int) -> dict:
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, env=child_environment(), text=True,
        encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True,
    )
    timed_out = interrupted = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop_process(process)
        stdout, stderr = process.communicate()
    except KeyboardInterrupt:
        interrupted = True
        stop_process(process)
        stdout, stderr = process.communicate()
    return {
        "returncode": process.returncode,
        "stdout": redact(stdout),
        "stderr": redact(stderr),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "timed_out": timed_out,
        "interrupted": interrupted,
    }


def preflight() -> dict:
    if shutil.which("uv") is None:
        raise RuntimeError("uv がありません。講座のGitHub Codespacesで実行してください。")
    print("構成を確認中です。初回はADKの取得に時間がかかります。", flush=True)
    result = execute(UV + ["python", "scripts/day3_pydantic_worker.py", "--check"], timeout=300)
    if result["returncode"] != 0 or result["timed_out"] or result["interrupted"]:
        raise RuntimeError("環境の確認に失敗しました。\n" + result["stdout"][-5000:] + "\n" + result["stderr"][-5000:])
    try:
        info = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise RuntimeError("構成確認のJSONを読み取れませんでした。\n" + result["stdout"][-5000:]) from exc
    if info.get("status") != "ready":
        raise RuntimeError("指示・ツール・モデルの共通条件を確認できませんでした。\n" + result["stdout"][-5000:])
    return info


def git_value(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, timeout=10)
    return proc.stdout.strip() if proc.returncode == 0 else "未取得"


def plan(cases: list[dict]) -> list[dict]:
    runs = []
    for i, case in enumerate(cases):
        order = ("pydantic_ai", "adk") if i % 2 == 0 else ("adk", "pydantic_ai")
        for framework in order:
            command = UV + (
                ["python", "scripts/day3_pydantic_worker.py", case["question"]]
                if framework == "pydantic_ai" else
                ["adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", case["question"]]
            )
            runs.append({
                "question_id": case["id"], "question": case["question"],
                "framework": framework, "command": command, "status": "not_started",
                "final_answer": "", "tool_calls": [], "tool_results": [], "usage": {}, "errors": [],
            })
    return runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="APIを呼ばず、依存ライブラリと構成だけを確認")
    args = parser.parse_args()
    if not args.check and not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY がありません。GitHubのCodespaces secretで自分のforkへの利用を許可し、Codespacesを再起動してください。キー自体をチャットやファイルに貼る必要はありません。", file=sys.stderr)
        return 2
    try:
        info = preflight()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 2
    print(f"構成確認OK / model={info['model']} / tools={', '.join(info['tools'])}", flush=True)
    if args.check:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        print("モデルAPIは呼び出していません。")
        return 0

    cases = json.loads((ROOT / "lectures/03/comparison_cases.json").read_text(encoding="utf-8"))
    if len(cases) != 4 or len({c["id"] for c in cases}) != 4:
        raise ValueError("比較用の4設問を読み取れません。comparison_cases.jsonを確認してください。")
    started = datetime.now(timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    run_dir = ROOT / "lectures/03/results" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for relative in SOURCE_PATHS:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"必要な通常ファイルがありません: {relative}")
        content = source.read_bytes()
        hashes[relative] = hashlib.sha256(content).hexdigest()
        target = run_dir / "source_snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    data = {
        "schema_version": 1, "run_id": run_id,
        "started_at": started.isoformat(), "status": "running", "completed": False,
        "model_execution_attempted": False,
        "model": info["model"], "versions": info["versions"],
        "preflight": info, "git_commit": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "source_sha256": hashes, "cases": cases, "runs": plan(cases),
    }
    latest = run_dir.parent / "latest.json"
    latest.write_text(json.dumps({"run_id": run_id}, ensure_ascii=False) + "\n", encoding="utf-8")
    save_result(run_dir, data)
    print(f"結果の保存先: {run_dir.relative_to(ROOT)}", flush=True)
    print("4問×2実装を実行します。ツール利用により、APIリクエストは8回より多くなることがあります。", flush=True)
    for index, row in enumerate(data["runs"]):
        print(f"[{index + 1}/8] {row['question_id']} / {row['framework']}", flush=True)
        print("  " + shlex.join(row["command"]), flush=True)
        data["model_execution_attempted"] = True
        try:
            result = execute(row["command"], timeout=150)
        except OSError as exc:
            result = {"returncode": -1, "stdout": "", "stderr": redact(str(exc)), "elapsed_seconds": 0, "timed_out": False, "interrupted": False}
        base = f"{row['question_id']}_{row['framework']}"
        for stream in ("stdout", "stderr"):
            (run_dir / f"{base}.{stream}.log").write_text(result[stream], encoding="utf-8")
        parsed = parse_adk_jsonl(result["stdout"]) if row["framework"] == "adk" else parse_pydantic_json(result["stdout"])
        row.update(parsed)
        row.update({key: result[key] for key in ("returncode", "elapsed_seconds", "timed_out", "interrupted")})
        if result["returncode"] != 0 or result["timed_out"] or result["interrupted"]:
            row["status"] = "interrupted" if result["interrupted"] else "failed"
            row["errors"].append(f"プロセス終了コード={result['returncode']}, timeout={result['timed_out']}, interrupted={result['interrupted']}")
            if result["stderr"].strip():
                row["errors"].append(result["stderr"][-6000:])
        save_result(run_dir, data)
        print(f"  → {row['status']}", flush=True)
        if row["status"] != "completed":
            data["status"] = row["status"]
            print("実行を停止しました。失敗した内容も保存します。自動の再試行は行いません。", flush=True)
            break
    else:
        data["status"] = "completed"
        data["completed"] = True
    data["finished_at"] = datetime.now(timezone.utc).isoformat()
    save_result(run_dir, data)
    archive = build_archive(ROOT, run_dir)
    print(f"\n記録: {(run_dir / 'report.md').relative_to(ROOT)}")
    print(f"ダウンロードするZIP: {archive.relative_to(ROOT)}")
    if data["completed"]:
        print("8/8完了しました。次に python scripts/prepare_day3_answer.py を実行してください。")
        return 0
    print("未完了です。ZIPを共有すると、ログを確認して続きの対応を決められます。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
