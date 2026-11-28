#!/usr/bin/env python3
"""Day3の提出用ファイルを、自分のforkのlec03へ配置します。

Python 3.10以降の標準ライブラリとGitを使用します。
  python3 install_day3.py --prepare-branch  # originを取得しlec03を準備して配置
  python3 install_day3.py --check           # 配置予定だけ確認
  python3 install_day3.py --verify          # 配置した内容を確認

通信は --prepare-branch のGit fetchだけです。API実行・依存パッケージの
インストール・commit・push・PR作成は行いません。未知の既存内容は上書きしません。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import urlsplit
import zlib

REPOSITORY = 'takerunakao/lecture-ai-engineering-2026'
BRANCH = 'lec03'
ANSWER = 'lectures/03/answer.md'

PAYLOAD_BYTES = 88926
PAYLOAD_SHA256 = '6c2a15e3986637aa1dd717636d0f099e7296b6cec1d25a6486064cbb076c87b9'
PAYLOAD = (
    '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'
)


def fail(message: str) -> None:
    raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_name(name: str) -> None:
    if not isinstance(name, str):
        fail('配置先は相対パスの文字列にしてください。')
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or '\x00' in name
            or path.is_absolute() or path.as_posix() != name
            or any(p in ('', '.', '..', '.git') for p in name.split('/'))):
        fail('不正な配置先です: ' + repr(name))
    if (path.parts[0] == 'app' or name in ('pyproject.toml', 'uv.lock')
            or path.parts[:2] in (('lectures', '01'), ('lectures', '02'))):
        fail('本体または以前の講義ファイルは変更できません: ' + name)


def target_path(root: Path, name: str) -> Path:
    validate_name(name)
    current = root
    parts = PurePosixPath(name).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            fail('シンボリックリンクには書き込みません: ' + name)
        if current.exists() and index < len(parts) - 1 and not current.is_dir():
            fail('親パスがディレクトリではありません: ' + name)
    if current.exists() and not current.is_file():
        fail('通常ファイルではありません: ' + name)
    return current


def package_files() -> tuple[dict[str, bytes], str | None]:
    raw = zlib.decompress(base64.b64decode(PAYLOAD, validate=True))
    if len(raw) != PAYLOAD_BYTES or sha(raw) != PAYLOAD_SHA256:
        fail('内蔵データが一致しません。スクリプトを取り直してください。')
    package = json.loads(raw)
    if package.get('schema_version') != 1 or not isinstance(package.get('files'), dict) or not package['files']:
        fail('内蔵データの形式が不正です。')
    files = {}
    for name, item in package['files'].items():
        validate_name(name)
        data = item['content'].encode('utf-8')
        if sha(data) != item['sha256']:
            fail('内蔵ファイルのハッシュが一致しません: ' + name)
        files[name] = data
    original = package.get('answer_template_sha256')
    if original is not None and not re.fullmatch(r'[0-9a-f]{64}', original):
        fail('空のanswer.mdの原本ハッシュが不正です。')
    return files, original


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    # --check / --verifyではGitの任意のindex更新も抑止する。
    environment = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    process = subprocess.run(['git', '-C', str(root), *arguments], capture_output=True,
                             text=True, encoding='utf-8', errors='replace', env=environment)
    if check and process.returncode:
        detail = process.stderr.strip() or process.stdout.strip()
        detail = re.sub(r'(https?://)[^/\s@]+@', r'\1***@', detail)
        fail('Gitの操作に失敗しました: git ' + ' '.join(arguments) + '\n' + detail)
    return process


def same_repository(url: str) -> bool:
    if url.startswith('git@github.com:'):
        path = url[len('git@github.com:'):]
    else:
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'ssh') or parsed.hostname != 'github.com':
            return False
        path = parsed.path.lstrip('/')
    path = path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    return path.lower() == REPOSITORY.lower()


def repository_root() -> Path:
    root = Path.cwd().resolve()
    project = root / 'pyproject.toml'
    if not project.is_file() or project.is_symlink() or not re.search(
        r'(?m)^name\s*=\s*[\"\']aie2026-exercises[\"\']\s*$',
        project.read_text(encoding='utf-8'),
    ):
        fail('講座forkのpyproject.tomlがあるルートで実行してください。')
    actual = Path(git(root, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()
    if root != actual:
        fail('Gitリポジトリの一番上のフォルダで実行してください。')
    for option in ((), ('--push',)):
        urls = git(root, 'remote', 'get-url', *option, '--all', 'origin').stdout.splitlines()
        if not urls or not all(same_repository(url) for url in urls):
            fail('originの取得先と送信先を、自分のfork ' + REPOSITORY + ' にしてください。')
    for operation in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        location = Path(git(root, 'rev-parse', '--git-path', operation).stdout.strip())
        if not location.is_absolute():
            location = root / location
        if location.exists():
            fail('進行中のGit操作があります。先に元の作業を完了してください。')
    return root


def current_branch(root: Path) -> str:
    return git(root, 'branch', '--show-current').stdout.strip()


def ref_exists(root: Path, ref: str) -> bool:
    return git(root, 'show-ref', '--verify', '--quiet', ref, check=False).returncode == 0


def changed_paths(root: Path, *arguments: str) -> set[str]:
    return set(filter(None, git(root, *arguments).stdout.split('\0')))


def check_branch_scope(root: Path, ref: str, files: dict[str, bytes]) -> None:
    if not ref_exists(root, 'refs/remotes/origin/main'):
        fail('origin/mainがありません。--prepare-branch で取得してください。')
    changed = changed_paths(root, 'diff', '--no-renames', '--name-only', '-z', 'origin/main...' + ref)
    unexpected = changed - set(files)
    if unexpected:
        fail('既存のlec03には今回の提出対象以外のcommit差分があります。resetせず停止します:\n  '
             + '\n  '.join(sorted(unexpected)))


def prepare_branch(root: Path, files: dict[str, bytes]) -> None:
    print('自分のforkのブランチ情報を取得します。', flush=True)
    git(root, 'fetch', '--no-tags', 'origin')
    if not ref_exists(root, 'refs/remotes/origin/main'):
        fail('自分のforkのmainが見つかりません。')
    if current_branch(root) == BRANCH:
        check_branch_scope(root, 'HEAD', files)
        return
    if ref_exists(root, 'refs/heads/' + BRANCH):
        check_branch_scope(root, BRANCH, files)
        git(root, 'switch', '--no-overwrite-ignore', BRANCH)
    elif ref_exists(root, 'refs/remotes/origin/' + BRANCH):
        check_branch_scope(root, 'origin/' + BRANCH, files)
        git(root, 'switch', '--no-overwrite-ignore', '--track', '-c', BRANCH, 'origin/' + BRANCH)
    else:
        # 現在のlec02等を基点にしない。Gitが保持できない既存変更は切替時に拒否する。
        git(root, 'switch', '--no-overwrite-ignore', '--no-track', '-c', BRANCH, 'origin/main')
    print('作業ブランチ: ' + current_branch(root))


def change_plan(root: Path, files: dict[str, bytes], original: str | None) -> dict[str, bytes]:
    dirty = changed_paths(root, 'diff', '--no-renames', '--name-only', '-z')
    dirty |= changed_paths(root, 'diff', '--cached', '--no-renames', '--name-only', '-z')
    if changed_paths(root, 'diff', '--name-only', '--diff-filter=U', '-z'):
        fail('未解決のGit競合があります。先に元の作業を完了してください。')
    changes, conflicts = {}, []
    for name, desired in files.items():
        target = target_path(root, name)
        old = target.read_bytes() if target.exists() else None
        if old == desired:
            continue
        # 配置対象外の変更はそのまま残す。配置対象の未commit変更は上書きしない。
        if name in dirty:
            conflicts.append(name + '（未commitの変更）')
        elif old is not None and not (name == ANSWER and original is not None and sha(old) == original):
            conflicts.append(name + '（既存内容が異なる）')
        changes[name] = desired
    if conflicts:
        fail('既存内容と衝突するため、提出用ファイルは一切変更していません:\n  '
             + '\n  '.join(conflicts))
    return changes


def atomic_write(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
    with tempfile.NamedTemporaryFile(prefix='.day3-', dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.chmod(mode)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-branch', action='store_true', help='originを取得しlec03を準備して配置')
    mode.add_argument('--check', action='store_true', help='ファイル・ブランチを変更せず配置予定を確認')
    mode.add_argument('--verify', action='store_true', help='配置した全ファイルと内蔵版を照合')
    args = parser.parse_args()
    files, original = package_files()
    root = repository_root()
    if args.prepare_branch:
        prepare_branch(root, files)
    if current_branch(root) != BRANCH:
        fail('現在のブランチはlec03ではありません。--prepare-branch を付けて実行してください。')
    check_branch_scope(root, 'HEAD', files)
    if args.verify:
        different = [name for name, desired in files.items()
                     if not target_path(root, name).is_file() or target_path(root, name).read_bytes() != desired]
        if different:
            fail('未配置または内蔵版と異なるファイルがあります:\n  ' + '\n  '.join(different))
        print(f'配置確認完了: 提出用{len(files)}ファイルが内蔵版と一致しています。')
        print('確認したのは配置内容です。実験の実行・commit・pushを確認するものではありません。')
        return
    changes = change_plan(root, files, original)
    print(f'作業ブランチ: {BRANCH} / 配置対象: {len(files)} / 変更対象: {len(changes)}')
    for name in changes:
        print('  ' + name)
    if args.check:
        print('確認のみ。ファイル・ブランチは変更していません。')
        return
    for name, data in changes.items():
        atomic_write(target_path(root, name), data)
    print('配置しました。既存のapp/、pyproject.toml、uv.lockは変更していません。')
    print('実験・commit・push・PR作成は、同梱の手順に従って進めてください。')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, UnicodeError, zlib.error) as exc:
        raise SystemExit('配置を中止しました: ' + str(exc))
