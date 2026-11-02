"""未実行の誤提出・手書きの消失・不要ファイルのZIP混入を防ぐ検査。"""

from pathlib import Path
import json
import os
import pty
import subprocess
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from day3_report import build_archive, code_block
from prepare_day3_answer import START, END, incorporate, validate_result


def successful_fixture():
    # 合成データ。実測結果ディレクトリには書き込まない。
    return {
        "status": "completed", "completed": True, "model_execution_attempted": True,
        "runs": [
            {"question_id": f"q{i}", "framework": framework, "status": "completed",
             "returncode": 0, "final_answer": "TEST FIXTURE", "errors": []}
            for i in range(1, 5) for framework in ("pydantic_ai", "adk")
        ],
    }


def test_all_eight_valid_answers_are_required():
    data = successful_fixture()
    validate_result(data)
    data["runs"].pop()
    with pytest.raises(ValueError):
        validate_result(data)


@pytest.mark.parametrize("change", [
    {"status": "failed"}, {"returncode": 1}, {"final_answer": ""},
    {"errors": ["429"]}, {"timed_out": True}, {"interrupted": True},
])
def test_partial_or_error_is_not_submittable(change):
    data = successful_fixture()
    data["runs"][0].update(change)
    with pytest.raises(ValueError):
        validate_result(data)


def test_dry_or_incomplete_run_is_not_real_completion():
    for change in ({"model_execution_attempted": False}, {"completed": False}, {"status": "running"}):
        data = successful_fixture()
        data.update(change)
        with pytest.raises(ValueError):
            validate_result(data)


def test_incorporation_preserves_manual_notes_and_literal_answer():
    old = f"# 自分の演習\n消してほしくない記録\n{START}\n前の結果\n{END}\n自分の観察：これも保持\n"
    raw = "# 回答に含まれる見出し\n```python\nprint('x')\n```"
    report = "# 結果\n\n" + code_block(raw) + "\n\n## 次の節\n"
    updated = incorporate(old, report)
    assert updated.startswith(old.split(START)[0])
    assert updated.endswith(old.split(END)[1])
    assert "### 結果" in updated and "#### 次の節" in updated
    assert raw in updated
    assert "前の結果" not in updated
    assert incorporate(updated, report) == updated


def test_missing_or_ambiguous_marker_stops_instead_of_overwriting():
    for text in ("手書きのみ", f"{START}{START}{END}", f"{END}{START}"):
        with pytest.raises(ValueError):
            incorporate(text, "# 記録")


def test_zip_contains_only_explicit_results_and_sources(tmp_path):
    run = tmp_path / "lectures/03/results/20261102T000000Z_12345678"
    run.mkdir(parents=True)
    for filename in ("result.json", "report.md", "q1_adk.stdout.log", ".env", "private-notes.txt"):
        (run / filename).write_text("TEST FIXTURE", encoding="utf-8")
    (run / "q1_adk.stderr.log").symlink_to(run / ".env")
    archive = build_archive(tmp_path, run)
    with zipfile.ZipFile(archive) as data:
        names = data.namelist()
    assert any(n.endswith("result.json") for n in names)
    assert any(n.endswith("q1_adk.stdout.log") for n in names)
    assert not any(n.endswith((".env", "private-notes.txt", "q1_adk.stderr.log")) for n in names)


def test_plan_uses_same_questions_new_processes_and_actual_adk_cli():
    from run_day3_comparison import plan

    cases = [{"id": f"q{i}", "question": f"QUESTION {i}"} for i in range(1, 5)]
    rows = plan(cases)
    assert len(rows) == 8
    for i, case in enumerate(cases):
        pair = rows[i * 2:i * 2 + 2]
        assert {r["framework"] for r in pair} == {"pydantic_ai", "adk"}
        assert all(r["command"][-1] == case["question"] for r in pair)
        adk = next(r for r in pair if r["framework"] == "adk")
        assert "adk" in adk["command"] and "run" in adk["command"]
        assert "--in_memory" in adk["command"] and "--replay" not in adk["command"]
        if i:
            assert pair[0]["framework"] != rows[(i - 1) * 2]["framework"]


def test_logged_text_redacts_known_key_and_url(monkeypatch):
    from run_day3_comparison import redact

    monkeypatch.setenv("GEMINI_API_KEY", "TEST_ONLY_SECRET")
    output = redact("secret=TEST_ONLY_SECRET https://example.invalid/?key=URL_TEST_SECRET&x=1")
    assert "TEST_ONLY_SECRET" not in output and "URL_TEST_SECRET" not in output
    assert "[REDACTED]" in output


def test_batch_closes_stdin_when_parent_is_a_real_terminal():
    """Codespaces同様に親がTTYでも、バッチ子プロセスを入力待ちにしない。

    旧版では子もTTYを継承し、read()で待ち続けてtimeoutする。
    模擬端末と標準ライブラリだけを使い、モデル/APIは呼ばない。
    """
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    driver = (
        "import sys,json; "
        f"sys.path.insert(0,{str(scripts)!r}); "
        "from run_day3_comparison import execute; "
        "assert sys.stdin.isatty(), 'regression fixture must have a TTY'; "
        "child=\"import sys,json; print(json.dumps({'isatty':sys.stdin.isatty(),'input':sys.stdin.read()}))\"; "
        "print(json.dumps(execute([sys.executable,'-c',child],timeout=2)))"
    )
    master, slave = pty.openpty()
    try:
        process = subprocess.run(
            [sys.executable, "-c", driver], stdin=slave, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=10,
        )
    finally:
        os.close(master)
        os.close(slave)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["timed_out"] is False
    assert result["returncode"] == 0
    observed = json.loads(result["stdout"])
    assert observed == {"isatty": False, "input": ""}
