"""最新の完了した比較記録を answer.md の指定区間へ取り込む。"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from day3_report import build_archive, render_report

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- DAY3_RESULTS_START -->"
END = "<!-- DAY3_RESULTS_END -->"


def validate_result(data: dict) -> None:
    runs = data.get("runs", [])
    if not (data.get("status") == "completed" and data.get("completed") is True and data.get("model_execution_attempted") is True):
        raise ValueError("最新実行は未完了です。失敗を完了扱いにせず、results内のログを確認してください。")
    expected = {(f"q{i}", framework) for i in range(1, 5) for framework in ("pydantic_ai", "adk")}
    actual = {(r.get("question_id"), r.get("framework")) for r in runs}
    if len(runs) != 8 or actual != expected:
        raise ValueError("4問×2実装の結果が揃っていません。")
    for run in runs:
        if (run.get("status") != "completed" or run.get("returncode") != 0
                or not str(run.get("final_answer", "")).strip() or run.get("errors")
                or run.get("timed_out") or run.get("interrupted")):
            raise ValueError("成功した最終回答が全8件揃っていません。")


def incorporate(text: str, report: str) -> str:
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
        raise ValueError("answer.mdの自動生成区間がありません。手書きの内容を守るため停止します。")
    # 宿題の下に入れるので、レポートの見出しを2段深くする。
    rendered = []
    fence = ""
    for line in report.splitlines():
        marker = re.match(r"^(`{3,}|~{3,})", line)
        if marker and not fence:
            fence = marker.group(1)
        elif fence and line.strip() == fence:
            fence = ""
        elif not fence:
            line = re.sub(r"^(#{1,4}) ", r"##\1 ", line)
        rendered.append(line)
    report = "\n".join(rendered)
    return text[:text.index(START) + len(START)] + "\n\n" + report.rstrip() + "\n\n" + text[text.index(END):]


def main() -> int:
    try:
        results = ROOT / "lectures/03/results"
        run_id = json.loads((results / "latest.json").read_text(encoding="utf-8"))["run_id"]
        if not re.fullmatch(r"\d{8}T\d{6}Z_[0-9a-f]{8}", run_id):
            raise ValueError("latest.jsonの実行IDが不正です。")
        run_dir = results / run_id
        data = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        validate_result(data)
        answer = ROOT / "lectures/03/answer.md"
        text = incorporate(answer.read_text(encoding="utf-8"), render_report(data))
        tmp = answer.with_suffix(".md.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(answer)
        archive = build_archive(ROOT, run_dir)
        print("lectures/03/answer.md に8件の実測結果を取り込みました。")
        print("宿題欄末尾の「自分の観察」を確認・記入してください。演習欄と手書き部分は保持しました。")
        print(f"更新済みZIP: {archive.relative_to(ROOT)}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"取り込みを中止しました: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
