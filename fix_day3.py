#!/usr/bin/env python3
"""Day3比較の初回ADK入力待ちを修正する。モデルAPI・GitHubへの通信は行わない。

講座リポジトリ直下で python fix_day3.py を実行してください。
変更対象は比較スクリプト1つと回帰テスト2つです。
既知の旧版だけを更新し、独自の変更があれば一切上書きせず停止します。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib

PAYLOAD = (
    'eNrNfWt3G9XZ6F+ZmkU9orIiyXefpdPjJgZ8yO3YDqtg60xHmpE9tTQjZkaJjY/XimQCAcIi5X5Jm7ZACAkkpbylaUjhw/knR5Fj'
    'Pr1/4TzPs/ee2XORLXN7SYttzez97Mtzv+ytrSGv6lpN3zvitmzN0DdHtarTaOqu5Tl2rrk5NKNsDVXMmuOamremF8cn4MlQbbqq'
    'G6NmtVqoTo5OTExXxsZ1vTo2VjUm8mZ1tFacnJgq5osTo1M1A15M1sama5O1Sm1qXK9OTRqjQ1llSK/5pivBnJ42qqNT4wBtajxf'
    'LFSLhqFXzII5WqyNj45Njpvw33jeyOdrxWJxdDw/ZhSmCpX8WHWqYBYK00WEWXVs37R9BLdC/xvrvfnq/3272Lt1de+DC932rd3b'
    'b+zd2+l2Xuueb+9e+fT+3bvw8DGzYdmWMnt6vtv+GJv+5VK3/Xa3fW3v+jvfXvp7t/1ut/Ny93xnxV6xR0aqa2Z1Xem2b+9+/PLu'
    'xcvQ/8Ff7+7deKXb/nO3/QeAAKC7O3/t7rzQ3blJMG/3/nCv2/5bt32j236O4Hx7/r3enTtiqI+xyYef7775Nkzs/jd/7H32Dhu/'
    '176y+9lfg/F7z78iutzuXfwIRmYf549129dZD9E7nDHbCJh5zXUaiqbVWn4LcKkpVqPpuL6i27bj677l2B62Ek/dVaABz+TdDN03'
    'fathik7ic1bBn886thn0XNO9tbpVCT7/Hugo+OB4HGBT97GVgHcaPgaN3BAYgDI3pE8t36qHH61VW5c+tipN16manhc+2gz/xokG'
    'H1otywj2hIjeNekFf7946szC0Tnt9OzS44tZpdKy6oamu9U16yws2dPPmtDea9V9GYLv6tVgg2jzNN1Y13D99Sx/0Nw0dNu3qhrb'
    'lRV74dSpJaVE61cBN1YdMJPJAXCnftZUMznoBvTsLRfKK/aZJ6Hl8spQ6+wK0PrKEDAs+2NkBGbxrBl8OmfBbtLfq46zWjdHYB6l'
    'UjFXGM3lV4bKKzSyYdZgpw296qu+ueHPKJ7vZpSR/46/Z1ZsBf4B0yu2jli3FXVl6LG5E/Mn5zUgae2JuafYAI+dOvXY8bnwWYZ3'
    'xX9n9XrLhCk7Xs60z1ouyJNV01cRYiZsZdVYQ6kj/sM5QV/8BdvRrMPeqtQOR11emDs2e3Rp7lgZRmT9HlIWjz3RbV86s3C823nu'
    '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'
)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="修正可能か確認するだけ")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if not (root / "pyproject.toml").is_file() or not (root / "scripts/run_day3_comparison.py").is_file():
        raise ValueError("講座リポジトリのルート（pyproject.tomlがある場所）で実行してください。")
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    if branch != "lec03":
        raise ValueError(f"現在のブランチは {branch!r} です。lec03 で実行してください。")
    package = json.loads(zlib.decompress(base64.b64decode(PAYLOAD, validate=True)))
    expected_paths = {"scripts/run_day3_comparison.py", "tests/test_day3_submission.py", "tests/test_day3_trace.py"}
    if set(package) != expected_paths:
        raise ValueError("修正用データの対象ファイルが一致しません。")
    pending = []
    for name, item in package.items():
        path = root / name
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise ValueError(f"通常ファイルがありません: {name}")
        desired = item["content"].encode("utf-8")
        if digest(desired) != item["after_sha256"]:
            raise ValueError(f"修正用データが一致しません: {name}")
        current = path.read_bytes()
        if digest(current) == item["after_sha256"]:
            continue
        if digest(current) != item["before_sha256"]:
            raise ValueError(f"既知の旧版と異なる内容があります。独自の変更を守るため停止します: {name}")
        pending.append((path, desired))
    if args.check:
        print(f"修正可能です。変更予定: {len(pending)}ファイル。まだ書き換えていません。")
        return
    for path, desired in pending:
        mode = path.stat().st_mode & 0o777
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".day3-fix-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(desired)
        try:
            temporary.chmod(mode)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        print("修正: " + path.relative_to(root).as_posix())
    print("修正完了。自動実行の子プロセスが端末入力を待たない設定になりました。")
    print("既存の結果とanswer.mdはそのまま残しています。モデルAPIは呼んでいません。")
    print("次に python scripts/run_day3_comparison.py を実行してください。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError, zlib.error) as exc:
        raise SystemExit("修正を中止しました: " + str(exc))
