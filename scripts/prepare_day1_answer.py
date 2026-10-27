"""最新の実測レポートをanswer.mdへ安全に取り込む。APIは呼ばない。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile


ORIGINAL = """# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：
- 用語集の正しい意味と比べて気づいたこと：
- 表示できたトークン数（入力 / 出力）：

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
"""
MARKER = "<!-- DAY1_ADVANCED_IMPORTED -->"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    lecture = Path("lectures/01")
    if not Path("pyproject.toml").is_file() or not lecture.is_dir():
        raise SystemExit("講座リポジトリのルートで実行してください。")
    if args.run_dir:
        run_dir = args.run_dir
    else:
        candidates = list((lecture / "benchmark_results").glob("*/answer.generated.md"))
        if not candidates:
            raise SystemExit("実測レポートがありません。先にbenchmark_day1を実行してください。")
        run_dir = max(candidates, key=lambda p: p.stat().st_mtime_ns).parent
    report = run_dir / "answer.generated.md"
    log = run_dir / "responses.jsonl"
    if not report.is_file() or not log.is_file() or not log.read_text(encoding="utf-8").strip():
        raise SystemExit("レポートまたは試行ログがありません。未測定の下書きは取り込みません。")

    destination = lecture / "answer.md"
    previous = destination.read_text(encoding="utf-8") if destination.exists() else ""
    if MARKER in previous:
        raise SystemExit(
            "answer.mdには取り込み済みの発展レポートがあります。上書きしていません。\n"
            f"必要な変更は {report.as_posix()} と比較して手動で反映してください。"
        )
    body = report.read_text(encoding="utf-8")
    # runディレクトリ内の相対リンクが、answer.mdへ移した後も有効になるよう直す。
    relative_run = Path(os.path.relpath(run_dir.resolve(), lecture.resolve())).as_posix()
    for name in ("plan.json", "responses.jsonl", "summary.csv"):
        body = body.replace(f"]({name})", f"]({relative_run}/{name})")
    imported = f"{MARKER}\n\n{body.rstrip()}\n\n"
    imported += "## 自分の利用枠の確認記録\n\nTODO: [day1_quota_notes.md](day1_quota_notes.md)に、自分で確認した上限と使用量を記入する。\n"
    if previous:
        backup_dir = Path(tempfile.mkdtemp(prefix="aie-day1-answer-backup-"))
        backup = backup_dir / "answer.md"
        backup.write_text(previous, encoding="utf-8")
        print(f"元のanswer.mdを保存: {backup}")
    if previous.strip() and previous.strip() != ORIGINAL.strip():
        contents = previous.rstrip() + "\n\n---\n\n" + imported
    else:
        contents = imported
    destination.write_text(contents, encoding="utf-8")
    print(f"取り込んだrun: {run_dir}")
    print(f"更新したファイル: {destination}")
    print("TODOと利用枠の記録を、自分の観察で埋めてから提出してください。")


if __name__ == "__main__":
    main()
