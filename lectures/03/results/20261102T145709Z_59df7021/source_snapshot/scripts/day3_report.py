"""実測だけを Markdown にまとめる。モデル API は呼び出さない。"""

from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

LABELS = {"pydantic_ai": "Pydantic AI", "adk": "Google ADK"}
STATUSES = {"completed": "完了", "failed": "失敗", "not_started": "未実行", "interrupted": "中断"}
SOURCE_PATHS = [
    "adk_agent/glossary_agent/__init__.py",
    "adk_agent/glossary_agent/agent.py",
    "scripts/run_day3_comparison.py",
    "scripts/day3_pydantic_worker.py",
    "scripts/day3_trace.py",
    "scripts/day3_report.py",
    "scripts/prepare_day3_answer.py",
    "tests/test_day3_trace.py",
    "tests/test_day3_submission.py",
    "lectures/03/comparison_cases.json",
    "lectures/03/README_day3.md",
    "app/agent.py",
    "app/tools.py",
    "app/config.py",
    "data/glossary.json",
    "data/lectures/01.md",
    "data/lectures/02.md",
    "data/lectures/03.md",
    "pyproject.toml",
    "uv.lock",
]


def code_block(text: str, language: str = "text") -> str:
    """回答中にコードフェンスがあっても文書を壊さず、原文を保持する。"""
    longest = max((len(x) for x in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def cell(value: object) -> str:
    if value is None:
        return "未取得"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(data: dict) -> str:
    completed = [r for r in data["runs"] if r["status"] == "completed"]
    planned = len(data["runs"])
    lines = [
        "# Day3 発展(a) 実行記録",
        "",
        f"- 実施状態：{STATUSES.get(data['status'], data['status'])}（{len(completed)}/{planned} 件の質問実行が完了）",
        f"- 実行ID：`{data['run_id']}`",
        f"- 開始日時（UTC）：{data['started_at']}",
        f"- モデル：`{data['model']}`（両版共通）",
        f"- 実行開始時の Git コミット：`{data.get('git_commit', '未取得')}`",
        "- 各質問を別プロセス・新規会話で1回ずつ実行。先に動かすフレームワークは質問ごとに交互。",
        "- 共通の指示と関数本体を直接インポート。各フレームワークによるプロンプトやツール定義の組み立てまで同一とは限らない。",
        "- HTTPリクエストは60秒、SDKのHTTP試行は1回。1質問の実行は120秒、LLM呼び出しは最大8回。外側でも起動込み150秒で停止。",
        "- 所要秒数はプロセス起動を含む。速度の優劣を判断する指標にはしていない。",
        "",
        "## ライブラリ",
        "",
        "| 項目 | 実行環境の値 |",
        "|---|---|",
    ]
    lines.extend(f"| {cell(k)} | {cell(v)} |" for k, v in data.get("versions", {}).items())
    lines += [
        "",
        "## 実行の集計",
        "",
        "| 質問 | 実装 | 状態 | ツール呼出数 | requests | モデル応答イベント数 | 起動込み秒数 |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for run in data["runs"]:
        usage = run.get("usage") or {}
        seconds = run.get("elapsed_seconds")
        seconds_text = f"{seconds:.2f}" if seconds is not None else "未取得"
        calls_text = str(len(run.get("tool_calls", []))) if run["status"] != "not_started" else "未取得"
        lines.append(
            f"| {run['question_id']} | {LABELS[run['framework']]} | {STATUSES.get(run['status'], run['status'])} "
            f"| {calls_text} "
            f"| {cell(usage.get('requests'))} | {cell(usage.get('model_response_events'))} "
            f"| {seconds_text} |"
        )
    lines += [
        "",
        "`requests` はPydantic AIが報告した値。ADKでは同じ定義の値を取得していないため「未取得」とし、JSONLのモデル応答イベント数を別欄に記録した。両者を同一のAPI課金リクエスト数として比較しない。",
        "",
        "## 質問ごとの回答とツール履歴",
        "",
    ]
    for case in data["cases"]:
        lines += [f"### {case['id']}：{case['question']}", "", f"**観察の観点：** {case['observe']}", ""]
        for run in (r for r in data["runs"] if r["question_id"] == case["id"]):
            lines += [f"#### {LABELS[run['framework']]}", "", f"状態：{STATUSES.get(run['status'], run['status'])}", ""]
            if run.get("command"):
                lines += ["実行コマンド（引数配列）：", "", code_block(json.dumps(run["command"], ensure_ascii=False), "json"), ""]
            if run.get("final_answer"):
                lines += ["取得した回答：", "", code_block(run["final_answer"]), ""]
            else:
                lines += ["最終回答は取得できていません。", ""]
            for title, field in (("ツール呼び出し", "tool_calls"), ("ツールの戻り値", "tool_results")):
                lines += [title + "：", "", code_block(json.dumps(run.get(field, []), ensure_ascii=False, indent=2), "json"), ""]
            if run.get("errors"):
                lines += ["エラー（回答の品質とは区別する）：", "", code_block("\n".join(run["errors"])), ""]
            if run.get("usage", {}).get("measurement_note"):
                lines += [run["usage"]["measurement_note"], ""]
    lines += [
        "## 読み取り上の注意",
        "",
        "- ツール呼出数は観測値であり、正解率ではない。LoRAの1回の検索でQLoRAの定義も返る場合がある。",
        "- 各4問・各1回の事例であり、確率的な生成のゆらぎを分離できない。フレームワーク全体の優劣は断定しない。",
        "- 回答の正確さ・根拠の扱いは、回答原文とツールの戻り値を読み、本人が確認する。自動採点は行っていない。",
        "- この記録は実際に取得した内容の整形であり、失敗・未実行を成功に置き換えていない。",
        "",
    ]
    return "\n".join(lines)


def save_result(run_dir: Path, data: dict) -> None:
    temporary = run_dir / "result.json.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(run_dir / "result.json")
    (run_dir / "report.md").write_text(render_report(data), encoding="utf-8")


def build_archive(root: Path, run_dir: Path) -> Path:
    """明示した提出物だけを同梱する。再現用のソースは実行時に snapshot 済み。"""
    target = root / "lectures/03" / f"day3_results_{run_dir.name}.zip"
    candidates = [run_dir / "result.json", run_dir / "report.md"]
    candidates += [run_dir / "source_snapshot" / p for p in SOURCE_PATHS]
    candidates += [
        run_dir / f"q{i}_{framework}.{stream}.log"
        for i in range(1, 5) for framework in LABELS for stream in ("stdout", "stderr")
    ]
    answer = root / "lectures/03/answer.md"
    if answer.is_file() and not answer.is_symlink():
        candidates.append(answer)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(candidates):
            if path.is_file() and not path.is_symlink():
                archive.write(path, path.relative_to(root).as_posix())
    return target
