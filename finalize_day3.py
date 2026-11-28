#!/usr/bin/env python3
"""完了したDay3実測結果に基づく提出文を配置する（モデルAPIは使わない）。"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zlib

PAYLOAD_SHA256 = '80e7b6a31a4ee0fb70336b444babd2d57ef15eac52e2daf405b8856ff29f043f'
PAYLOAD = (
    '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'
    'Qolkhg=='
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='配置可能か確認するだけ')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if not (root / 'pyproject.toml').is_file():
        raise ValueError('講座リポジトリのルート（pyproject.tomlがある場所）で実行してください。')
    branch = subprocess.run(['git', 'branch', '--show-current'], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    if branch != 'lec03':
        raise ValueError(f'現在のブランチは {branch!r} です。lec03 で実行してください。')
    raw = zlib.decompress(base64.b64decode(PAYLOAD, validate=True))
    if digest(raw) != PAYLOAD_SHA256:
        raise ValueError('提出用データのハッシュが一致しません。ファイルを取り直してください。')
    package = json.loads(raw)
    result_path = root / 'lectures/03/results' / package['run_id'] / 'result.json'
    if not result_path.is_file() or digest(result_path.read_bytes()) != package['result_sha256']:
        raise ValueError('今回確認した完了済みresult.jsonがありません、または内容が変わっています。結果を消さず、この表示を共有してください。')
    data = json.loads(result_path.read_text(encoding='utf-8'))
    runs = data.get('runs', [])
    expected = {(f'q{i}', f) for i in range(1, 5) for f in ('pydantic_ai', 'adk')}
    if not (data.get('completed') is True and data.get('status') == 'completed' and len(runs) == 8
            and {(r.get('question_id'), r.get('framework')) for r in runs} == expected
            and all(r.get('status') == 'completed' and r.get('returncode') == 0 and not r.get('errors') and r.get('final_answer') for r in runs)):
        raise ValueError('成功した4問×2版の記録が揃っていません。')
    latest = result_path.parent.parent / 'latest.json'
    if latest.is_file() and json.loads(latest.read_text(encoding='utf-8')).get('run_id') != package['run_id']:
        raise ValueError('最新の実行IDが、今回共有されたZIPの実行IDと異なります。新しい結果を共有してください。')
    allowed = {'lectures/03/answer.md', 'lectures/03/PR_BODY.md', 'lectures/03/quri_answers.md'}
    if set(package['files']) != allowed or len(package['q3']) > 400:
        raise ValueError('提出用データの形式が不正です。')
    pending = []
    for name, content in package['files'].items():
        target = root / name
        if any(parent.is_symlink() for parent in (target, target.parent, target.parent.parent)):
            raise ValueError('シンボリックリンクへの配置は行いません: ' + name)
        desired = content.encode('utf-8')
        if target.exists():
            current = target.read_bytes()
            if current == desired:
                continue
            if name != 'lectures/03/answer.md' or digest(current) != package['answer_before_sha256']:
                raise ValueError('共有された版から独自の変更があります。上書きせず停止します: ' + name)
        elif name == 'lectures/03/answer.md':
            raise ValueError('取り込み済みのanswer.mdが見つかりません。')
        pending.append((target, desired))
    if args.check:
        print(f'8/8の実測結果と配置先を確認しました。変更予定: {len(pending)}ファイル。')
        print('確認のみ。モデルAPIの呼び出し・ファイルの変更は行っていません。')
        return
    for target, desired in pending:
        mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.day3-final-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(desired)
        try:
            temporary.chmod(mode)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print('配置: ' + target.relative_to(root).as_posix())
    print('提出用ファイルの反映が完了しました。モデルAPIは呼び出していません。')
    print('answer.mdの考察とquri_answers.mdのQ3を読んで確認し、GitHubへ保存してください。')
    print('PRタイトル: ' + package['pr_title'])
    print('Q3文字数: ' + str(len(package['q3'])))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, zlib.error, subprocess.SubprocessError) as exc:
        raise SystemExit('提出文の反映を中止しました: ' + str(exc))
