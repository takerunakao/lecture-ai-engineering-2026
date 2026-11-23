#!/usr/bin/env python3
"""Day6比較用JSONと提出項目を静的に確認する。通信・MCP起動は行わない。"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
CASES = (
    ("course_stdio.json", "mcpServers", "stdio", "course"),
    ("course_http.json", "mcpServers", "http", "course"),
    ("vscode_copilot_stdio.json", "mcpServers", "stdio", "copilot"),
    ("vscode_copilot_http.json", "mcpServers", "http", "copilot"),
    ("vscode_legacy_stdio.json", "servers", "stdio", "legacy"),
    ("vscode_legacy_http.json", "servers", "http", "legacy"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "JSONのキーが重複しています")
        obj[key] = value
    return obj


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_case(filename, root_key, transport, family):
    path = HERE / "examples" / filename
    data = read_json(path)
    require(isinstance(data, dict) and set(data) == {root_key},
            filename + ": この比較例ではトップレベルを " + root_key + " にそろえてください")
    servers = data[root_key]
    require(isinstance(servers, dict) and len(servers) == 1,
            filename + ": 比較するサーバーを1つ記載してください")
    name, spec = next(iter(servers.items()))
    require(isinstance(spec, dict), filename + ": サーバー設定はオブジェクトにしてください")
    require(("command" in spec) != ("url" in spec),
            filename + ": command / url は片方だけ指定してください")
    if family != "course":
        require(spec.get("type") == transport, filename + ": typeが通信方式と一致しません")
    if transport == "stdio":
        require(name == "glossary", filename + ": 比較対象はglossaryです")
        require(isinstance(spec.get("command"), str) and bool(spec["command"].strip()),
                filename + ": commandを文字列で指定してください")
        require(isinstance(spec.get("args"), list)
                and all(isinstance(arg, str) for arg in spec["args"]),
                filename + ": argsを文字列の配列で指定してください")
        if family == "copilot":
            require(isinstance(spec.get("cwd"), str) and spec["cwd"].startswith("/"),
                    filename + ": この例ではcwdに実行ホストの絶対パスを使います")
        elif family == "legacy":
            require(spec.get("cwd") == "${workspaceFolder}",
                    filename + ": この例では従来形式の変数を比較します")
    else:
        require(name == "aws", filename + ": 比較対象はawsです")
        require(isinstance(spec.get("url"), str), filename + ": urlが必要です")
        parsed = urlsplit(spec["url"])
        require(parsed.scheme == "https" and bool(parsed.netloc)
                and parsed.username is None and parsed.password is None,
                filename + ": 認証情報を含まないHTTPSのURLを指定してください")
    if family == "copilot":
        require(spec.get("tools") == ["*"], filename + ": この比較例ではtoolsを[\"*\"]にそろえます")
    return spec, {"file": "examples/" + filename, "root_key": root_key,
                  "transport": transport, "format": family, "status": "passed",
                  "sha256": sha256(path)}


def atomic_json(path, value):
    require(not path.is_symlink(), "結果の保存先がシンボリックリンクです")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".day6-check-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(temporary, 0o644)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-result", action="store_true", help="検査結果をvalidation.jsonへ保存")
    options = parser.parse_args()
    specs, results, errors = {}, [], []
    for case in CASES:
        try:
            spec, result = check_case(*case)
            specs[case[0]] = spec
            results.append(result)
            print("PASS  examples/" + case[0])
        except (OSError, ValueError, TypeError) as error:
            errors.append(str(error))
    q3_length = None
    if not errors:
        try:
            commands = [(specs[name]["command"], specs[name]["args"])
                        for name, _, mode, _ in CASES if mode == "stdio"]
            require(all(value == commands[0] for value in commands), "3形式の起動コマンドが異なります")
            urls = [specs[name]["url"] for name, _, mode, _ in CASES if mode == "http"]
            require(len(set(urls)) == 1, "3形式の接続URLが異なります")
            answer = (HERE / "answer.md").read_text(encoding="utf-8")
            require("## 宿題" in answer and "取り組んだレベル：発展" in answer,
                    "answer.mdの宿題欄・レベルを確認してください")
            quri = (HERE / "quri_answers.md").read_text(encoding="utf-8")
            require("## Q3\n\n" in quri, "quri_answers.mdにQ3がありません")
            q3 = quri.split("## Q3\n\n", 1)[1].split("\n\n", 1)[0].strip()
            q3_length = len(q3)
            require(0 < q3_length <= 300, "Q3を1〜300文字にしてください")
            manifest = read_json(HERE / "source_manifest.json")
            require(manifest.get("research_date_jst") == "2026-11-23",
                    "出典一覧の調査日を確認してください")
            print("PASS  3形式で起動コマンド・接続URLが一致")
            print(f"PASS  Q3: {q3_length} / 300文字")
        except (OSError, ValueError, TypeError) as error:
            errors.append(str(error))
    result = {
        "status": "failed" if errors else "passed",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_kind": "offline_static_checks_for_these_six_examples",
        "mcp_connection_executed": False,
        "model_api_called": False,
        "official_full_schema_validation": False,
        "examples_checked": len(results),
        "examples": results,
        "q3_characters": q3_length,
        "checker_sha256": sha256(Path(__file__)),
        "errors": errors,
    }
    if options.write_result:
        atomic_json(HERE / "validation.json", result)
        print("保存先: lectures/06/validation.json")
    if errors:
        for error in errors:
            print("FAIL  " + error, file=sys.stderr)
        return 1
    print("静的チェック: PASS（6設定例）")
    print("確認範囲: JSON構文・比較項目。MCP接続やモデルAPIの呼び出しは行っていません。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print("確認できませんでした: " + str(error), file=sys.stderr)
        raise SystemExit(1)
