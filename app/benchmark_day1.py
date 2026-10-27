#!/usr/bin/env python3
"""Day1 発展課題: Gemini の応答・時間・トークンを再現可能に比較する。

準備: uv sync --frozen
計画: python app/benchmark_day1.py --dry-run
実測: python app/benchmark_day1.py
再集計: python app/benchmark_day1.py --report lectures/01/benchmark_results/RUN

API キーは環境変数 GEMINI_API_KEY からだけ読み、保存しない。
標準ライブラリだけで dry-run と再集計を実行できる。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any
import uuid

SDK_VERSION = "2.31.0"
DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
QUESTIONS = {
    "short": "LoRA（Low-Rank Adaptation）とは何ですか。大規模言語モデルの学習における役割と利点を、日本語で100字程度で説明してください。",
    "long": "RAGとファインチューニングの違いを、日本語で400字程度で説明してください。知識の更新、回答の根拠、学習コストの観点で比較し、それぞれが向く用途を一つずつ挙げてください。",
    "course": "AIエンジニアリング実践講座2026のDay1宿題で設定されている「基礎・実装・発展」の各要件を、日本語で200字程度で説明してください。公式資料を確認できない場合は、その点を明示し、推測で要件を作らないでください。",
}
TOKEN_FIELDS = (
    "prompt_token_count", "candidates_token_count", "total_token_count",
    "thoughts_token_count", "cached_content_token_count", "tool_use_prompt_token_count",
)
TOKEN_LABELS = ("入力", "候補出力", "総数", "思考", "キャッシュ入力", "ツール用入力")
STATUSES = ("success", "truncated", "empty", "incomplete", "error", "interrupted")
STOP_HTTP_CODES = {400, 401, 403, 404, 429}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def json_write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_trials(models: list[str], question_ids: list[str], repeats: int) -> list[dict]:
    """各反復で設問順とモデル順を巡回し、同数の呼び出しを計画する。"""
    trials = []
    for index in range(repeats):
        qi, mi = index % len(question_ids), index % len(models)
        questions = question_ids[qi:] + question_ids[:qi]
        ordered_models = models[mi:] + models[:mi]
        for question_id in questions:
            for model in ordered_models:
                trials.append({"trial_id": f"trial-{len(trials) + 1:03d}",
                               "repeat": index + 1, "question_id": question_id,
                               "question_text": QUESTIONS[question_id],
                               "requested_model": model})
    return trials


def build_plan(args: argparse.Namespace) -> dict:
    try:
        sdk_version = importlib.metadata.version("google-genai")
    except importlib.metadata.PackageNotFoundError:
        sdk_version = None
    try:
        proc = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"],
                              cwd=Path(__file__).resolve().parent.parent,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              text=True, timeout=3, check=False)
        git_commit = proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        git_commit = None
    return {
        "schema_version": 1, "created_at": utc_now(), "level": "発展",
        "models": args.models, "question_ids": args.question_ids,
        "questions": {key: QUESTIONS[key] for key in args.question_ids},
        "settings": {"repeats": args.repeats, "interval_seconds": args.interval,
                     "max_output_tokens": args.max_output_tokens,
                     "timeout_seconds": args.timeout, "sdk_attempts": 1,
                     "generation_parameters": {"max_output_tokens": args.max_output_tokens},
                     "provider_defaults": ["temperature", "top_p", "top_k", "thinking_config"],
                     "order": "反復ごとに設問順とモデル順を1つずつ巡回"},
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "google_genai_required": SDK_VERSION, "google_genai_installed": sdk_version,
                    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "git_commit": git_commit},
        "trials": build_trials(args.models, args.question_ids, args.repeats),
    }


def field(obj: Any, name: str) -> Any:
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def safe_token(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def finish_reason(response: Any) -> str | None:
    candidates = field(response, "candidates") or []
    reason = field(candidates[0], "finish_reason") if candidates else None
    reason = getattr(reason, "name", None) or getattr(reason, "value", reason)
    if not isinstance(reason, str):
        return None
    reason = reason.rsplit(".", 1)[-1].upper()
    return reason if re.fullmatch(r"[A-Z0-9_]+", reason) else None


def response_text(response: Any) -> str:
    try:
        text = field(response, "text")
    except (ValueError, AttributeError, TypeError):
        text = None
    if isinstance(text, str):
        return text
    candidates = field(response, "candidates") or []
    content = field(candidates[0], "content") if candidates else None
    parts = field(content, "parts") or []
    return "".join(field(part, "text") for part in parts
                   if isinstance(field(part, "text"), str) and not field(part, "thought"))


def base_record(trial: dict, started_at: str, elapsed: float) -> dict:
    record = dict(trial)
    record.update({"started_at": started_at, "elapsed_seconds": elapsed,
                   "model_version": None, "finish_reason": None,
                   "status": None, "error_type": None, "http_code": None, "response_text": ""})
    record.update({name: None for name in TOKEN_FIELDS})
    return record


def response_record(trial: dict, response: Any, started_at: str, elapsed: float) -> dict:
    record = base_record(trial, started_at, elapsed)
    text, reason = response_text(response), finish_reason(response)
    if not text.strip():
        status = "empty"
    elif reason == "STOP":
        status = "success"
    elif reason == "MAX_TOKENS":
        status = "truncated"
    else:
        status = "incomplete"
    record.update({"model_version": field(response, "model_version"), "finish_reason": reason,
                   "response_text": text, "status": status})
    usage = field(response, "usage_metadata")
    record.update({name: safe_token(field(usage, name)) for name in TOKEN_FIELDS})
    return record


def exception_code(exc: BaseException) -> int | None:
    for value in (getattr(exc, "code", None), getattr(exc, "status_code", None),
                  field(getattr(exc, "response", None), "status_code")):
        if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599:
            return value
        if isinstance(value, str) and re.fullmatch(r"[1-5][0-9]{2}", value):
            return int(value)
    return None


def error_record(trial: dict, exc: BaseException, started_at: str, elapsed: float,
                 status: str = "error") -> dict:
    """例外本文・URL・リクエストヘッダーはログに含めない。"""
    record = base_record(trial, started_at, elapsed)
    record.update({"status": status, "error_type": re.sub(r"[^A-Za-z0-9_]", "", type(exc).__name__)[:80],
                   "http_code": exception_code(exc)})
    return record


def run_experiment(plan: dict, run_dir: Path, client: Any, config: Any, *,
                   clock=time.perf_counter, sleeper=time.sleep) -> dict:
    """通信直前から戻るまでだけを測定。clock/sleeper は無通信テスト用に注入可。"""
    state = {"status": "completed", "stop_reason": None, "started_at": utc_now(),
             "planned_calls": len(plan["trials"]), "attempted_calls": 0}
    last_start = None
    try:
        with (run_dir / "responses.jsonl").open("a", encoding="utf-8") as log:
            for trial in plan["trials"]:
                if last_start is not None:
                    wait = plan["settings"]["interval_seconds"] - (clock() - last_start)
                    if wait > 0:
                        sleeper(wait)
                started_at = utc_now()
                request_start = clock()
                last_start = request_start
                try:
                    response = client.models.generate_content(
                        model=trial["requested_model"], contents=trial["question_text"], config=config)
                except KeyboardInterrupt as exc:
                    elapsed = clock() - request_start
                    record = error_record(trial, exc, started_at, elapsed, status="interrupted")
                except Exception as exc:
                    elapsed = clock() - request_start
                    record = error_record(trial, exc, started_at, elapsed)
                else:
                    elapsed = clock() - request_start
                    record = response_record(trial, response, started_at, elapsed)
                log.write(json.dumps(record, ensure_ascii=False) + "\n")
                log.flush()
                state["attempted_calls"] += 1
                print(f"{trial['trial_id']} {trial['requested_model']} {trial['question_id']}: "
                      f"{record['status']} {elapsed:.3f}s HTTP={record['http_code']}", flush=True)
                if record["status"] == "interrupted":
                    state.update(status="interrupted", stop_reason="KeyboardInterrupt")
                    break
                if record["http_code"] in STOP_HTTP_CODES:
                    state.update(status="stopped", stop_reason=f"HTTP {record['http_code']}")
                    break
    except KeyboardInterrupt:
        state.update(status="interrupted", stop_reason="KeyboardInterrupt（呼出間の停止）")
    finally:
        state["finished_at"] = utc_now()
        json_write(run_dir / "run.json", state)
        generate_report(run_dir)
    return state


def finite_numbers(values: list) -> list:
    return [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)]


def median_or_none(values: list) -> float | None:
    valid = finite_numbers(values)
    return statistics.median(valid) if valid else None


def summarize(plan: dict, records: list[dict]) -> list[dict]:
    rows = []
    for model in plan["models"]:
        for question_id in plan["question_ids"]:
            planned = [t for t in plan["trials"]
                       if t["requested_model"] == model and t["question_id"] == question_id]
            ids = {t["trial_id"] for t in planned}
            attempts = [r for r in records if r.get("trial_id") in ids]
            successes = [r for r in attempts if r.get("status") == "success"]
            elapsed = finite_numbers([r.get("elapsed_seconds") for r in successes])
            row = {"requested_model": model, "question_id": question_id, "planned": len(planned),
                   "attempted": len(attempts), **{s: sum(r.get("status") == s for r in attempts) for s in STATUSES},
                   "not_attempted": len(planned) - len(attempts),
                   "elapsed_seconds_median": median_or_none(elapsed),
                   "elapsed_seconds_min": min(elapsed) if elapsed else None,
                   "elapsed_seconds_max": max(elapsed) if elapsed else None}
            for name in TOKEN_FIELDS:
                tokens = [r.get(name) for r in successes]
                valid = finite_numbers(tokens)
                row[name + "_median"] = median_or_none(valid)
                row[name + "_missing"] = len(successes) - len(valid)
            rows.append(row)
    return rows


def md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def number(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".") if digits else f"{value:g}"


def load_records(run_dir: Path) -> tuple[list[dict], list[str]]:
    path = run_dir / "responses.jsonl"
    if not path.exists():
        return [], []
    records, warnings, seen = [], [], set()
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or not record.get("trial_id"):
                raise ValueError("Invalid record")
            if record["trial_id"] in seen:
                raise ValueError("Duplicate trial")
            seen.add(record["trial_id"])
            records.append(record)
        except (json.JSONDecodeError, ValueError):
            warnings.append(f"responses.jsonl の {index} 行目を集計できませんでした。元ログを確認してください。")
    return records, warnings


def generate_report(run_dir: Path) -> Path:
    """保存済み JSON だけから再集計する。API キー・SDK・ネットワークは不要。"""
    run_dir = Path(run_dir)
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    records, warnings = load_records(run_dir)
    rows = summarize(plan, records)
    run_path = run_dir / "run.json"
    state = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
    planned_n, attempted_n = len(plan["trials"]), len(records)
    success_n = sum(r.get("status") == "success" for r in records)
    partial = attempted_n < planned_n or state.get("status") in ("interrupted", "stopped") or bool(warnings)
    heading = "未実測" if not records else "部分実測・未完了" if partial else "全試行を実施"
    with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    settings = plan["settings"]
    lines = ["# Day1 宿題：発展 — Gemini API 比較実験", "", "取り組んだレベル: 発展", "",
             f"**実行状態：{heading}**", "",
             f"計画作成（UTC）：{md(plan['created_at'])}。",
             f"実行開始（UTC）：{md(state.get('started_at') or '記録なし')}。実行終了（UTC）：{md(state.get('finished_at') or '記録なし')}。", "",
             "このファイルは実測ログから作成した提出用の下書きです。TODOを自分の確認・考察で埋めてから提出してください。", "",
             f"計画 {planned_n} 回／試行 {attempted_n} 回／正常完了 {success_n} 回／未試行 {planned_n - attempted_n} 回。",
             f"停止理由：{md(state.get('stop_reason') or '記録なし')}。", ""]
    if not records:
        lines += ["API呼び出しの記録がないため、速度・品質・トークン数の実測結果はまだありません。", ""]
    if warnings:
        lines += ["## ログの注意", "", *[f"- {text}" for text in warnings], ""]
    lines += ["## 1. 目的と実験条件", "",
              "同じ設問を複数モデルへ送り、回答内容、応答時間、使用トークンを比較する。個人情報・社内資料を含まない固定の作成設問を使用した。", "",
              f"- モデル：{', '.join('`' + md(m) + '`' for m in plan['models'])}",
              f"- 各モデル・設問の反復数：{settings['repeats']} 回。順序：{settings['order']}。",
              f"- 全リクエストの開始間隔：最低 {settings['interval_seconds']} 秒。並列実行・自動再試行は行わない。",
              f"- `max_output_tokens={settings['max_output_tokens']}`、HTTPタイムアウト {settings['timeout_seconds']} 秒、SDKの最大試行回数 `1`。",
              "- `temperature`、`top_p`、`top_k`、`thinking_config` は指定せず、各モデルの既定値を使用する。",
              "- 通信呼び出しの前後を `time.perf_counter()` で測定。開始間隔の待機、記録、表示、集計は応答時間から除外する。",
              "- チャット履歴、検索、ファイル、ツールは渡さない。各リクエストは独立している。",
              f"- 実行環境：Python {md(plan['runtime']['python'])}／google-genai {md(plan['runtime']['google_genai_installed'])}（指定版 {SDK_VERSION}）。",
              f"- ソース SHA-256：`{plan['runtime']['script_sha256']}`。Git：`{plan['runtime']['git_commit'] or '取得なし'}`。",
              "", "完全な条件・設問・実行順は [plan.json](plan.json)、全応答は [responses.jsonl](responses.jsonl)、集計は [summary.csv](summary.csv) に保存。", "",
              "| 設問ID | 送信した文章 |", "|---|---|"]
    lines += [f"| {md(q)} | {md(plan['questions'][q])} |" for q in plan["question_ids"]]
    lines += ["", "`course` は資料未提供時の不確実性への対応を見る設問であり、講義資料の知識テストとして採点しない。文字数指定は目安で、出力長を一致させる制約ではない。", "",
              "## 2. 試行の内訳", "",
              "正常完了は「非空の本文があり、終了理由が `STOP`」の場合に限定した。`MAX_TOKENS` の非空回答は打切り、空本文は空回答、それ以外の非空回答はその他の未完了として別集計する。", "",
              "| モデル | 設問 | 計画 | 試行 | 正常完了 | 打切り | 空 | その他未完了 | エラー | 中断 | 未試行 |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        keys = ("planned", "attempted", "success", "truncated", "empty", "incomplete", "error", "interrupted", "not_attempted")
        lines.append(f"| {md(row['requested_model'])} | {row['question_id']} | " + " | ".join(str(row[k]) for k in keys) + " |")
    lines += ["", "## 3. 応答時間とトークン", "",
              "以下の統計は正常完了した試行だけを対象とする。エラー・打切り・空回答・未完了・中断の速さを、成功回答の速度として混ぜていない。", "",
              "| モデル | 設問 | 正常完了 n | 応答時間中央値（秒） | 最小（秒） | 最大（秒） |",
              "|---|---|---:|---:|---:|---:|"]
    for row in rows:
        values = [number(row["elapsed_seconds_" + stat]) for stat in ("median", "min", "max")]
        lines.append(f"| {md(row['requested_model'])} | {row['question_id']} | {row['success']} | " + " | ".join(values) + " |")
    lines += ["", "トークンはAPIのメタデータをそのまま保存した。欠測を0に変換せず、入力＋候補出力から総数を補完しない。各欄は「中央値（正常完了中の欠測数）」である。", "",
              "| モデル | 設問 | " + " | ".join(TOKEN_LABELS) + " |",
              "|---|---|" + "---:|" * len(TOKEN_FIELDS)]
    for row in rows:
        values = [f"{number(row[name + '_median'])}（欠測 {row[name + '_missing']}/{row['success']}）" for name in TOKEN_FIELDS]
        lines.append(f"| {md(row['requested_model'])} | {row['question_id']} | " + " | ".join(values) + " |")
    lines += ["", "### 記録から確認できること", ""]
    comparisons = 0
    for question_id in plan["question_ids"]:
        available = [r for r in rows if r["question_id"] == question_id and r["elapsed_seconds_median"] is not None]
        if len(available) > 1:
            lines.append(f"- 設問 `{question_id}` の成功応答時間の中央値：" + "、".join(
                f"`{r['requested_model']}` {number(r['elapsed_seconds_median'])}秒（n={r['success']}）" for r in available) + "。")
            comparisons += 1
    if not comparisons:
        lines.append("比較可能な複数モデルの成功記録が揃っていないため、速度差を結論づけない。")
    lines += ["", "## 4. 制限とエラーの観察", ""]
    errors = [r for r in records if r.get("status") in ("error", "interrupted")]
    if errors:
        lines += ["| 試行 | モデル | 状態 | 例外型 | HTTPコード |", "|---|---|---|---|---:|"]
        lines += [f"| {r['trial_id']} | {md(r['requested_model'])} | {r['status']} | {md(r['error_type'])} | {r['http_code'] if r['http_code'] is not None else '不明'} |" for r in errors]
    else:
        lines.append("エラーの記録はない。制限に到達したことを示す実測データもない。" if records else "未実測のため、エラーや制限到達の有無は未確認。")
    codes = {r.get("http_code") for r in errors}
    if 429 in codes:
        lines += ["", "HTTP 429を観測したため、その試行を保存して以後の呼び出しを停止した。429だけではRPM・入力TPM・RPDのどれに達したかは特定できない。AI Studioの当該プロジェクトの利用状況と制限表示を照合する。"]
    if 503 in codes:
        lines += ["", "HTTP 503を観測した。これはサービス過負荷・一時的利用不可の可能性を示すもので、日次クォータ超過の証拠として扱わない。自動再試行はせず、後続の計画試行が残っていれば所定の開始間隔で続行する仕様とした。"]
    lines += ["", "### 公式仕様の確認と自分のプロジェクトの記録", "",
              "Gemini APIの制限にはRPM（1分間のリクエスト数）、入力TPM（1分間の入力トークン数）、RPD（1日のリクエスト数）がある。制限はAPIキー単位ではなくプロジェクト単位で適用され、モデル・利用階層等で異なる。RPDのリセットは太平洋時間の午前0時で、日本時間の午前0時ではない。", "",
              "- TODO：AI Studioで確認した日時・利用階層・各モデルのRPM／入力TPM／RPDと当日の既存使用量を記載する（APIキーは記載しない）。",
              "- TODO：エラーを観測した場合は、利用状況との照合結果と解消方法を記載する。未到達なら『今回の試行範囲では未観測』と記載する。",
              "", "## 5. 考察と限界", "",
              "- TODO：`short`／`long` の回答を読み、正確さ・必要事項の充足・説明のわかりやすさ・文字数の違いを、具体的な試行IDを挙げて比較する。",
              "- TODO：`course` で資料不足を明示したか、未確認の講義要件を断定しなかったかを実際の回答で確認する。",
              "- TODO：測定した時間・トークン数と回答内容を根拠に、自分ならどの用途でどのモデルを選ぶか記載する。",
              f"- 反復は設定上 {settings['repeats']} 回であり、少数回の測定から一般的な性能の優劣や統計的な有意差を断定できない。ネットワークやサービス負荷の影響も残る。",
              "- 同じ最大出力トークン数でも、実際の文章量やモデルの思考予算が揃うとは限らない。生の応答時間を、同じ量の仕事に対する純粋な推論速度とは解釈しない。",
              "- 順序を巡回して偏りを減らしたが、完全な無作為化・均等な順序割付ではない。成功率が違う場合、成功のみの時間比較には選択の偏りがあり得る。",
              "- モデルの回答を正解資料として扱わず、必要な事実は公式資料等と照合する。自動生成した比較文に品質評価は含まれない。", "",
              "### AI支援の利用", "",
              "実験コードと本レポートの下書きの作成にChatGPTを使用した。TODO：提出前に実行条件・コード動作・応答内容・集計結果を確認し、確認・修正した箇所と自分の考察を記録する。", "",
              "## 6. 参考資料", "",
              "- [Gemini API：レート制限](https://ai.google.dev/gemini-api/docs/rate-limits)",
              "- [Google AI Studio](https://aistudio.google.com/)：使用したプロジェクトの現在の制限を確認",
              "- [Gemini API：トラブルシューティング](https://ai.google.dev/gemini-api/docs/troubleshooting)",
              "- [Gemini API：generateContent のトークン](https://ai.google.dev/gemini-api/docs/generate-content/tokens)",
              "- [Gemini API：モデル一覧と仕様](https://ai.google.dev/gemini-api/docs/models)",
              "- [Gemini API：更新履歴](https://ai.google.dev/gemini-api/docs/changelog)",
              "- [GenerateContentResponse API仕様](https://ai.google.dev/api/generate-content#v1beta.GenerateContentResponse)",
              "", "## 付録：各試行の回答", ""]
    for record in records:
        lines += [f"### {record['trial_id']} — {md(record['requested_model'])} / {record['question_id']} / 反復 {record['repeat']}", "",
                  f"状態：`{record['status']}`／終了理由：`{record['finish_reason'] or '不明'}`／応答時間：{number(record['elapsed_seconds'])}秒／応答モデル版：`{md(record.get('model_version') or '未返却')}`。", ""]
        text = record.get("response_text") or "（回答本文なし）"
        fence = "`" * max(3, max((len(s) for s in re.findall(r"`+", text)), default=0) + 1)
        lines += [fence + "text", text, fence, ""]
    destination = run_dir / "answer.generated.md"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--question-ids", nargs="+", choices=list(QUESTIONS), default=list(QUESTIONS))
    parser.add_argument("--interval", type=float, default=15.0, help="全リクエストの開始間隔（秒、既定15）")
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTPタイムアウト（秒）")
    parser.add_argument("--run-dir", type=Path, help="新規結果フォルダ。既存フォルダは拒否")
    parser.add_argument("--dry-run", action="store_true", help="実行計画だけ表示。SDK・キー・通信・出力ファイル不要")
    parser.add_argument("--report", type=Path, metavar="RUN_DIR", help="保存済みJSONだけからレポートとCSVを再生成")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.report:
        if args.dry_run:
            parser.error("--report と --dry-run は同時に指定できません。")
        try:
            print(f"再集計しました：{generate_report(args.report)}")
            return 0
        except Exception as exc:
            print(f"再集計できませんでした。ファイルを確認してください（{type(exc).__name__}）。", file=sys.stderr)
            return 2
    if args.repeats < 1 or args.max_output_tokens < 1:
        parser.error("--repeats と --max-output-tokens は1以上で指定してください。")
    if not math.isfinite(args.interval) or args.interval < 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--interval は0以上、--timeout は0より大きい有限の秒数で指定してください。")
    if len(set(args.models)) != len(args.models) or len(set(args.question_ids)) != len(args.question_ids):
        parser.error("モデル名と設問IDを重複させないでください。")
    plan = build_plan(args)
    per_model = len(args.question_ids) * args.repeats
    print(f"計画：{len(args.models)}モデル × {len(args.question_ids)}設問 × {args.repeats}反復 = {len(plan['trials'])}回（各モデル{per_model}回）。")
    print("実行前にAI Studioで現在の制限と当日の既存使用量を確認してください。授業時のGemini 3.8の例はRPD 10〜20回で、既存の利用も合算されます。")
    if args.dry_run:
        print("DRY RUN：API呼び出し・出力ファイル作成は行いません。")
        print(json.dumps({"settings": plan["settings"], "runtime": plan["runtime"], "questions": plan["questions"]}, ensure_ascii=False, indent=2))
        for trial in plan["trials"]:
            print(f"{trial['trial_id']}: repeat={trial['repeat']} model={trial['requested_model']} question={trial['question_id']}")
        return 0
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY を環境変数に設定してから実行してください。キーは保存・表示しません。", file=sys.stderr)
        return 2
    if plan["runtime"]["google_genai_installed"] != SDK_VERSION:
        print(f"この実験は google-genai=={SDK_VERSION} を使用します。講座リポジトリで uv sync --frozen を実行してください。", file=sys.stderr)
        return 2
    run_dir = args.run_dir or (Path("lectures/01/benchmark_results") /
                              (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]))
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("既存の結果フォルダは使用できません。--run-dirに新しいパスを指定してください。", file=sys.stderr)
        return 2
    json_write(run_dir / "plan.json", plan)
    client = None
    try:
        from google import genai  # 実測時だけSDKを読み込む。
        from google.genai import types
        client = genai.Client(api_key=api_key, vertexai=False, enterprise=False,
                              http_options=types.HttpOptions(timeout=int(args.timeout * 1000),
                                                            retry_options=types.HttpRetryOptions(attempts=1)))
        config = types.GenerateContentConfig(max_output_tokens=args.max_output_tokens)
        state = run_experiment(plan, run_dir, client, config)
    except KeyboardInterrupt:
        json_write(run_dir / "run.json", {"status": "interrupted", "stop_reason": "KeyboardInterrupt"})
        generate_report(run_dir)
        print(f"中断しました。部分結果：{run_dir}")
        return 130
    except Exception as exc:
        print(f"実行を完了できませんでした（{type(exc).__name__}）。保存済み結果：{run_dir}", file=sys.stderr)
        generate_report(run_dir)
        return 2
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as exc:
                print(f"クライアント終了時の通知：{type(exc).__name__}", file=sys.stderr)
    print(f"結果：{run_dir / 'answer.generated.md'}")
    if state["status"] != "completed":
        print(f"部分実測として保存しました。停止理由：{state['stop_reason']}")
    return 130 if state["status"] == "interrupted" else 1 if state["status"] == "stopped" else 0


if __name__ == "__main__":
    raise SystemExit(main())
