#!/usr/bin/env python3
"""Day5実測の確認案を、提出者の確認後に提出ファイルへ取り込む。

標準ライブラリのみ。モデルAPI呼び出し、git commit/push、PR作成は行わない。
実行方法: python finalize_day5.py --accept-review
確認のみ: python finalize_day5.py
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import uuid
import zipfile

PAYLOAD = json.loads(r'''{
  "run_id": "20261117T234818Z_3c60667f",
  "configuration_sha256": "984097ccac54723a12f3cb2650d56c8c29f4a954e01930694c24ecd55d3acd7a",
  "records_sha256": "cbecf0e2164b92571c3ba7722dcbc0b151a6a756bc086d3da05f36afb950e380",
  "reference_pages_sha256": "2b309abcee580aceb92e14bbe9a505b9538be3ffeb42b895cf249292d939e697",
  "pending_review_sha256": "1749151617b6c5b33597af168217536025560fdf0f5222fc075852eed1f9fd05",
  "source_fingerprints": {
    "day5_lab/__init__.py": "490d542ca347c8563c4a05a33d660c15ff768a95b4db88b4a96c3091b50fbd1b",
    "day5_lab/experiment.py": "587d1fe7fb2032266d93d452416ecf07d686b5cff3a7fe61fba64795b022dbfd",
    "day5_lab/gemini.py": "f0b3088f511183fda665b400d73f2cfa57d4ec9181b7803de7f672d13d3f5ea7",
    "day5_lab/io_utils.py": "f65321ee9612b57b0ae5109321542e2b1fab05a9e4b1963a20c714300f92e84d",
    "day5_lab/reporting.py": "1155a25d340618d3e4b2f9464e656235a0eaca9ab8ee9933e5c85cb7b980619d",
    "day5_lab/retrieval.py": "f1cc281eb0882dd1148b7cf1ca260f8df2188e95bfb4df233a58e3a6bcae59ad",
    "scripts/run_day5_comparison.py": "dc92fad5164d231e5d6c1f373059e2b272e9d1a5f61acca5db00aae96bff7a29",
    "scripts/prepare_day5_answer.py": "052144f279965a5eb298fa266290ac9ffae384299b239be9eb63354926d151c5",
    "lectures/05/questions.json": "1cce9ea1fe01d099aba984a0154489d8eb902bb885f8fbb62078caf21f845047",
    "lectures/05/source_manifest.json": "73a71997ae8660b335cec91dd184e79162edd09942914525e946b9443bd74e09"
  },
  "initial_outputs_sha256": {
    "quri_answers.md": "c6eb9158b005422a58d8f69fe18265c6bb93c4eea420471ca4dfd44f4fd0157b",
    "PR_BODY.md": "2a5bdf68fe31564557cff1ba41b9427589c013ce64056b1ce2bc8a0f472bd702"
  },
  "initial_homework_sha256": "6652ef5e320cc313f7afa15bb1edcd5de91c92b4b311ec97b975dc8ecf9f06ee",
  "review": {
    "schema_version": 1,
    "run_id": "20261117T234818Z_3c60667f",
    "status": "pending",
    "reviewer": "",
    "reviewed_at": "",
    "records": [
      {
        "task_id": "r1_q1_baseline",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "元の重みの固定、小さな行列A・Bの学習、QLoRAの4bit圧縮を説明しており、第2回p.52がすべてを裏付ける。",
        "reviewed_citation_page_ids": [
          "lec02-main-p052"
        ]
      },
      {
        "task_id": "r1_q1_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "元の重みの固定、小さな差分の学習、QLoRAの4bit圧縮を説明しており、第2回p.51・52が支える。実引用2ページに対し自動抽出はp.51の1ページだけである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p051",
          "lec02-main-p052"
        ]
      },
      {
        "task_id": "r1_q2_graph",
        "answer_correct": "fail",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "同じセッション内の履歴要約と外部保存、OpenClawの選別保存は正しく、p.39・65・40が裏付ける。ただし事前基準の「次の会話のコンテキストへの読み戻し」を明示していないため、完全性の基準は未達。誤情報による不合格ではない。",
        "reviewed_citation_page_ids": [
          "lec03-main-p039",
          "lec03-main-p065",
          "lec03-main-p040"
        ]
      },
      {
        "task_id": "r1_q2_baseline",
        "answer_correct": "fail",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "コンパクション、外部保存、OpenClawの選別保存は正しく、p.39・40が裏付ける。ただし外部メモリの読み戻しと次のコンテキストへの再注入の説明が欠け、事前基準の一部を満たさない。",
        "reviewed_citation_page_ids": [
          "lec03-main-p039",
          "lec03-main-p040"
        ]
      },
      {
        "task_id": "r1_q3_baseline",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "第2回p.52のW固定・A/B学習と、第3回p.13・39・65の外部保存・読み戻しを区別し、メモリ利用を重みの学習と混同していない。実引用4ページに対し自動抽出は2ページである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p052",
          "lec03-main-p013",
          "lec03-main-p065",
          "lec03-main-p039"
        ]
      },
      {
        "task_id": "r1_q3_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "第2回p.52のW固定・低ランク行列の学習、第3回p.65の重み不変、p.13・39の保存と再注入を正しく比較する。実引用4ページは取得本文に裏付けられるが、自動抽出では3ページである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p052",
          "lec03-main-p065",
          "lec03-main-p013",
          "lec03-main-p039"
        ]
      },
      {
        "task_id": "r1_q4_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "pass",
        "notes": "今回の実測値を確認できないと明言し、数値を作っていない。第2回p.13の3/5を説明例として実測と区別する。引用はこの例を支えるもので、資料全体に記録がないことを証明するものではない。",
        "reviewed_citation_page_ids": [
          "lec02-main-p013"
        ]
      },
      {
        "task_id": "r1_q4_baseline",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "pass",
        "notes": "実測値を断定せず、第2回p.13の3/5を説明用の例と明確に区別する。例示への引用は本文と一致する。回答保留は適切だが、次に確認すべき実行ログや正答判定への案内はない。",
        "reviewed_citation_page_ids": [
          "lec02-main-p013"
        ]
      },
      {
        "task_id": "r2_q1_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "元の重みの固定、低ランクの差分の学習、QLoRAの4bit圧縮を正しく区別する。A/Bの詳細は第2回p.52にあり、p.51・52の併記が支える。実引用2ページに対し自動抽出は1ページである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p051",
          "lec02-main-p052"
        ]
      },
      {
        "task_id": "r2_q1_baseline",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "元の重みと小さな行列A・Bを区別し、QLoRAの4bit圧縮も説明する。第2回p.51・52が裏付ける。実引用2ページに対し、自動抽出はp.51の1ページだけである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p051",
          "lec02-main-p052"
        ]
      },
      {
        "task_id": "r2_q2_baseline",
        "answer_correct": "fail",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "同一セッションの要約、外部ファイルへの保存、メモの選別は正しく、p.39・65・40が裏付ける。ただし次の会話への読み戻しが欠ける。実引用3ページに対し自動抽出は2ページである。",
        "reviewed_citation_page_ids": [
          "lec03-main-p039",
          "lec03-main-p065",
          "lec03-main-p040"
        ]
      },
      {
        "task_id": "r2_q2_graph",
        "answer_correct": "fail",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "履歴要約と外部記録、OpenClawの見直し・選別は資料に沿うが、次のコンテキストへの読み戻しを明示していない。p.39・65・40は記述を支える。実引用3ページに対し自動抽出は2ページである。",
        "reviewed_citation_page_ids": [
          "lec03-main-p039",
          "lec03-main-p065",
          "lec03-main-p040"
        ]
      },
      {
        "task_id": "r2_q3_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "固定するW、学習するA/B、外部に保存して再注入する情報を区別できる。第2回p.52と第3回p.13・39・65が裏付ける。「A 和 B」は軽微な表記揺れ。実引用4ページに対し自動抽出は3ページである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p052",
          "lec03-main-p065",
          "lec03-main-p013",
          "lec03-main-p039"
        ]
      },
      {
        "task_id": "r2_q3_baseline",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "not_applicable",
        "notes": "第2回p.52のW固定・A/B学習と第3回p.13・39の外部保存・読み戻しを区別する。「会話の最初に」は資料の実装例の説明として解釈し、全メモリ実装のタイミングへ一般化しない。実引用3ページに対し自動抽出は2ページである。",
        "reviewed_citation_page_ids": [
          "lec02-main-p052",
          "lec03-main-p013",
          "lec03-main-p039"
        ]
      },
      {
        "task_id": "r2_q4_baseline",
        "answer_correct": "pass",
        "citations_supported": "unsure",
        "abstention_ok": "pass",
        "notes": "回答を保留し、秒数や正答率を作っていない。一方、第2回p.13、第1回p.19、第3回p.64を列挙するだけで、説明例・別システム・別指標と実測不明の判断との対応を説明していない。すべて取得済みだが、引用の意味的裏付けはunsureとした。",
        "reviewed_citation_page_ids": [
          "lec02-main-p013",
          "lec01-main-p019",
          "lec03-main-p064"
        ]
      },
      {
        "task_id": "r2_q4_graph",
        "answer_correct": "pass",
        "citations_supported": "pass",
        "abstention_ok": "pass",
        "notes": "第2回p.13の3/5を説明用の例と区別し、今回の実測値は確認できないとして保留する。数値の捏造はない。引用は説明例を支えるが、確認可能な範囲は取得資料に限られ、実測を答えるには別途今回のログが必要である。",
        "reviewed_citation_page_ids": [
          "lec02-main-p013"
        ]
      }
    ],
    "observations": {
      "comparison_summary": "4問×2方式×2回の16回答はすべて正常完了した。事前根拠グループはq1〜q3で両方式とも12/12取得し、q4は対象外とした。事前の回答基準をすべて満たす回答は双方6/8（75%、回答保留を含む）で、q2の各2回答は読み戻しの説明不足により未達だった。これは本評価セットでの完全性の集計であり、モデルの一般的な正答率ではない。取得5ページの集合は8比較ペアすべて同じで、新規根拠の採用は0件。平均総時間は基本4.584591秒、Graph4.581870秒で、速度差は確認できない。入力は各17,268tokens、出力は基本1,016・Graph1,256tokens、生成API推定費用合計はそれぞれ0.0077204・0.0083204米ドルだった。",
      "improved_example": "q3ではGraphがLoRAの根拠lec02-main-p052を4位から2位へ上げ、メモリの根拠の直後に置く動作を確認した。ただし基本RAGも同じページを取得し、両方式とも回答基準を満たしたため、取得率・回答品質の改善例とはしない。q2はp.39とp.65の順が入れ替わったが、両方式とも「外部保存した情報を次の会話へ読み戻す」という説明が欠けた。p.39には必要な根拠があるため、検索漏れではなく、回答へ必要事項を反映する段階の不足である。q4は全回答が実測値の作り話を避けた。基本RAGの反復2は引用を列挙するだけで判断との対応が不明瞭だったが、同一の取得内容からの生成差であり、Graphの優位とは結論しない。",
      "remaining_failure_or_limitation": "基本RAGの根拠取得がすでに100%で、この質問集合では取得率の改善余地がなかった。独立な質問は4問だけで、反復を増やした16回答を16種類の問題とは数えない。q1・q4は生成リクエストのハッシュまで同じでも回答が変わり、temperature=0でも生成の揺れが残った。平均総時間差は約0.00272秒、中央値は基本4.486秒・Graph4.672秒で、API側の変動と検索方式の影響を切り分けられない。Graphの推定生成費用は今回7.77%多かったが、入力は同数で、出力240tokensの差に対応する。一般的な費用増加とはしない。元の自動引用抽出は「p.13, p.39」の後続ページを落としていた。回答ごとの重複除外引用数は自動29件に対し本文照合39件（基本19、Graph20）で、欠落10件もすべて取得済みだった。原記録は変更せず、実引用一覧と見落としをreview_addendum.md・review_audit.jsonへ補足する。引用先の存在は39/39でも、意味的な裏付けは15回答pass・1回答unsureであり、100%正しい引用とは扱わない。",
      "adoption_decision": "今回の用途では基本RAGを当面採用し、Graph併用は比較実装として保管する。",
      "adoption_reason": "根拠取得・回答の完全性に改善を確認できず、時間も同等であるため、実装と保守が単純な基本RAGを選ぶ。Graphの検索候補拡張とq3の順位変更は動作したが、有効性の立証には至っていない。次は、関連根拠がベクトル上位5件から漏れる未使用の質問集合を事前に定め、関係種類・hop数・取得枠の比較を行いたい。q2の不足には、必要な説明要素を網羅したかを確かめる共通の生成・検証手順も検討する。これらは今後の案であり、今回実施済みの改善結果ではない。",
      "q3": "AI支援を用い、基本RAGとGraph併用RAGを同じ214ページ・モデル・取得5ページで4問×各2回比較しました。対象3問の根拠取得率は双方100%でも、問2は読み戻しの説明が欠け、事前基準を満たす回答は双方6/8件でした。Graphで根拠の順序は変わりましたが新規取得はなく、平均時間も約4.58秒で同等でした。引用抽出の見落としを本文との照合で補足し、取得・回答・引用を分けて評価しました。今回の結果では基本RAGを採用し、Graphは未使用の質問で再検証すると整理しました。"
    },
    "review_origin": "ChatGPTによる原回答・取得本文・事前基準の照合案。提出者が確認・採用するまでは人手確認完了と扱わない。",
    "rubric": "answer_correctのpassは、事前登録した回答基準の必須要素をすべて満たした場合。説明の省略はfail、判定不能はunsure。q4の適切な回答保留はpass。citations_supportedは引用対象の記述を裏付けるかを別に判定する。",
    "original_records_preserved": true
  }
}
''')
VERSION = 'day5-final-review-1.0.0'
RUN_ID = PAYLOAD['run_id']
RUN_REL = Path('lectures/05/results') / RUN_ID
JST = timezone(timedelta(hours=9))
MARKER = '<!-- DAY5_FINAL_REVIEW_NOTICE -->'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def checked_path(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('保存先の相対パスが不正です。')
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('シンボリックリンクの先には保存しません: ' + str(relative))
    if not current.resolve().is_relative_to(root):
        raise ValueError('作業先がリポジトリの外です。')
    return current


def atomic_bytes(path, raw):
    if path.is_symlink():
        raise ValueError('保存先がシンボリックリンクです。')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.day5-review-', dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def write_text(path, value):
    atomic_bytes(path, value.encode('utf-8'))


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git_read(root, *args):
    proc = subprocess.run(['git', *args], cwd=root, text=True, capture_output=True, check=False)
    if proc.returncode:
        raise ValueError('Gitの作業状態を確認できません。Codespacesのリポジトリ直下で実行してください。')
    return proc.stdout.strip()


def verify(root):
    if Path(git_read(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('pyproject.tomlのあるリポジトリ直下で実行してください。')
    if git_read(root, 'branch', '--show-current') != 'lec05':
        raise ValueError('lec05ブランチで実行してください。切り替えコマンド: git switch lec05')
    origin = git_read(root, 'remote', 'get-url', 'origin').rstrip('/')
    if origin not in {
        'https://github.com/takerunakao/lecture-ai-engineering-2026',
        'https://github.com/takerunakao/lecture-ai-engineering-2026.git',
        'git@github.com:takerunakao/lecture-ai-engineering-2026.git',
        'ssh://git@github.com/takerunakao/lecture-ai-engineering-2026.git',
    }:
        raise ValueError('作業先が提出用のtakerunakao/lecture-ai-engineering-2026ではありません。')
    directory = checked_path(root, RUN_REL)
    config = read_json(checked_path(root, RUN_REL/'config.json'))
    unsigned = {k: v for k, v in config.items() if k != 'configuration_sha256'}
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    if config.get('run_id') != RUN_ID or sha(canonical) != PAYLOAD['configuration_sha256']:
        raise ValueError('確認した実行設定と一致しません。今回のZIPに対応する結果フォルダが必要です。')
    if config.get('configuration_sha256') != PAYLOAD['configuration_sha256']:
        raise ValueError('設定ハッシュが一致しません。')
    for filename, expected in [('records.jsonl', PAYLOAD['records_sha256']), ('reference_pages.json', PAYLOAD['reference_pages_sha256'])]:
        if sha(checked_path(root, RUN_REL/filename).read_bytes()) != expected:
            raise ValueError(filename + 'が確認したZIPと異なります。上書きしていません。')
    if config.get('code_fingerprints') != PAYLOAD['source_fingerprints']:
        raise ValueError('実行コードの版が一致しません。')
    for name, expected in PAYLOAD['source_fingerprints'].items():
        for relative in [Path(name), RUN_REL/'source_snapshot'/name]:
            if sha(checked_path(root, relative).read_bytes()) != expected:
                raise ValueError('実行時からコード・質問が変更されています: ' + str(relative))
    records = [json.loads(line) for line in (directory/'records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    plan = {task['task_id'] for task in config['task_plan']}
    result = read_json(checked_path(root, RUN_REL/'result.json'))
    if (len(records) != 16 or len(plan) != 16 or {r['task_id'] for r in records} != plan
            or not result.get('completed') or result.get('status') != 'completed'
            or any(r.get('status') != 'completed' or r.get('generation', {}).get('finish_reason') != 'STOP' for r in records)):
        raise ValueError('16件の正常完了を確認できません。')
    return directory, config, records


def audit_records(config, records, review):
    reviews = {r['task_id']: r for r in review['records']}
    audit = {'schema_version': 1, 'run_id': RUN_ID, 'review_tool_version': VERSION,
             'records_sha256': PAYLOAD['records_sha256'], 'original_record_metrics_unchanged': True,
             'note': '引用一覧は回答本文を照合した補足。取得本文内のID一致と、引用内容の意味的裏付けは別の判定。',
             'methods': {}, 'page_comparisons': [], 'citations': []}
    for method in ['baseline', 'graph']:
        rows = [r for r in records if r['method'] == method]
        judgments = [reviews[r['task_id']] for r in rows]
        audit['methods'][method] = {
            'completed': len(rows),
            'answer_pass': sum(x['answer_correct'] == 'pass' for x in judgments),
            'answer_fail': sum(x['answer_correct'] == 'fail' for x in judgments),
            'citation_support_verdicts': dict(Counter(x['citations_supported'] for x in judgments)),
            'abstention_pass': sum(x['abstention_ok'] == 'pass' for x in judgments),
            'mean_seconds': statistics.fmean(r['elapsed_seconds'] for r in rows),
            'median_seconds': statistics.median(r['elapsed_seconds'] for r in rows),
            'min_seconds': min(r['elapsed_seconds'] for r in rows),
            'max_seconds': max(r['elapsed_seconds'] for r in rows),
            'mean_embedding_seconds': statistics.fmean(r['embedding']['elapsed_seconds'] for r in rows),
            'mean_retrieval_seconds': statistics.fmean(r['retrieval']['elapsed_seconds'] for r in rows),
            'mean_generation_seconds': statistics.fmean(r['generation']['elapsed_seconds'] for r in rows),
            'input_tokens': sum(r['generation']['usage']['input_tokens'] for r in rows),
            'output_tokens': sum(r['generation']['usage']['output_tokens'] for r in rows),
            'estimated_generation_usd': sum(r['generation']['cost_estimate']['usd'] for r in rows),
            'reference_groups_hit': sum(r['metrics']['reference_groups_hit'] for r in rows),
            'reference_groups_total': sum(r['metrics']['reference_groups_total'] for r in rows),
            'automatic_citation_count': sum(len(r['metrics']['citation_page_ids']) for r in rows),
            'reviewed_citation_count': sum(len(x['reviewed_citation_page_ids']) for x in judgments),
        }
    by_id = {r['task_id']: r for r in records}
    for repeat in range(1, config['repeats'] + 1):
        for case in config['cases']:
            a = by_id[f"r{repeat}_{case['id']}_baseline"]
            b = by_id[f"r{repeat}_{case['id']}_graph"]
            pa = [x['page_id'] for x in a['retrieval']['pages']]
            pb = [x['page_id'] for x in b['retrieval']['pages']]
            audit['page_comparisons'].append({
                'repeat': repeat, 'case_id': case['id'], 'baseline_pages': pa, 'graph_pages': pb,
                'same_set': set(pa) == set(pb), 'same_order': pa == pb,
                'new_graph_pages': [p for p in pb if p not in pa],
                'graph_candidates': b['retrieval']['trace'].get('candidate_count_after_cap'),
                'same_generation_request': a['generation']['request_sha256'] == b['generation']['request_sha256'],
            })
    for record in records:
        task = record['task_id']
        reviewed = reviews[task]['reviewed_citation_page_ids']
        automatic = record['metrics']['citation_page_ids']
        page_ids = {p['page_id'] for p in record['retrieval']['pages']}
        if len(reviewed) != len(set(reviewed)):
            raise ValueError('引用補足一覧に重複があります。')
        audit['citations'].append({
            'task_id': task, 'automatic_page_ids': automatic,
            'reviewed_page_ids': reviewed,
            'omitted_by_automatic_parser': [p for p in reviewed if p not in automatic],
            'reviewed_out_of_context': [p for p in reviewed if p not in page_ids],
            'citations_supported': reviews[task]['citations_supported'],
        })
    return audit


def addendum_text(audit):
    a, b = audit['methods']['baseline'], audit['methods']['graph']
    lines = [
        '# Day5 実測後の確認と集計の補足', '',
        f'実行ID：`{RUN_ID}`。生の回答・測定値は変更せず、AI支援で照合した判定と観察を追記した。', '',
        '## 結論', '',
        'この4問では、Graph併用による新規根拠の取得や回答の完全性の改善は確認できなかった。基本RAGを当面採用する。q2の説明不足と、引用IDの自動抽出の見落としを記録した。', '',
        '## 回答と測定値', '',
        '| 指標 | 基本RAG | Graph併用RAG |', '|---|---:|---:|',
        '| 正常完了 | 8/8 | 8/8 |',
        '| 事前基準を全て満たす回答（保留を含む） | 6/8 | 6/8 |',
        '| q1〜q3のみの回答基準達成 | 4/6 | 4/6 |',
        '| q4の適切な回答保留 | 2/2 | 2/2 |',
        '| 引用内容の裏付け（回答単位） | pass 7、unsure 1 | pass 8 |',
        '| q1〜q3の事前根拠グループ取得 | 12/12 | 12/12 |',
        f"| 総時間の平均（秒/回答） | {a['mean_seconds']:.6f} | {b['mean_seconds']:.6f} |",
        f"| 総時間の中央値（秒/回答） | {a['median_seconds']:.6f} | {b['median_seconds']:.6f} |",
        f"| 検索部分の平均（秒/回答） | {a['mean_retrieval_seconds']:.6f} | {b['mean_retrieval_seconds']:.6f} |",
        f"| 入力tokens合計 | {a['input_tokens']:,} | {b['input_tokens']:,} |",
        f"| 出力tokens合計 | {a['output_tokens']:,} | {b['output_tokens']:,} |",
        f"| 生成API推定費用（USD/8回答） | {a['estimated_generation_usd']:.7f} | {b['estimated_generation_usd']:.7f} |", '',
        '回答の合否は課題全体の合否や講座の採点結果ではない。q2は核心的な説明は正しいが、事前基準にある「保存先から次の会話のコンテキストへ読み戻す」という必須要素がないためfailとした。q4の回答保留は回答基準達成へ含め、根拠取得率の対象からは除外した。', '',
        '費用は実行ログに保存された有料Standard単価の概算で、請求額ではない。思考tokensは未返却で、total=input+outputの整合から料金推定時のみ0とした。キャッシュ欄も未返却のため通常入力単価を使用した。埋め込み・索引構築・無料枠を含めた総費用ではない。', '',
        '## 取得ページの差', '',
        '| 問 | Graph候補数 | 最終5ページの集合 | 順位の変化（両反復共通） |',
        '|---|---:|---|---|',
        '| q1 | 11 | 同一 | なし |',
        '| q2 | 15 | 同一 | 第3回p.39とp.65を入れ替え |',
        '| q3 | 13 | 同一 | 第2回p.52を4位から2位へ |',
        '| q4 | 23 | 同一 | なし |', '',
        '8比較ペアすべてで新規採用ページは0件。q3の順位変更は設計どおりの動作だが、基本RAGにも同じ根拠があり、回答品質改善の証拠とはならない。q1・q4は生成要求のハッシュまで同じでも回答が異なり、生成の揺れを確認した。', '',
        '## 引用IDの自動抽出と本文照合', '',
        '実行時の抽出器は「第3回・PDF p.13, p.39」のような後続のp.表記を落とす。回答ごとの重複除外引用数の合計は自動29件、本文照合39件（基本19、Graph20）だった。欠落10件も取得本文に含まれる。自動表は参考値として原記録を保ち、下表を引用一覧の補足とする。', '',
        'IDの文脈内一致39/39は内容の正しさを保証しない。意味的な裏付けは回答単位で15件pass・1件unsure。r2_q4_baselineは数値を捏造せず保留できたが、列挙した引用と不明という判断との対応が不明瞭なため、unsureを維持した。', '',
        '| 実行ID | 自動件数 | 本文照合件数 | 自動抽出で欠落したページ |',
        '|---|---:|---:|---|',
    ]
    for row in audit['citations']:
        missing = ', '.join(row['omitted_by_automatic_parser']) or 'なし'
        lines.append(f"| {row['task_id']} | {len(row['automatic_page_ids'])} | {len(row['reviewed_page_ids'])} | {missing} |")
    lines += ['', '## 判定の根拠', '',
              'q1：第2回p.51・52。元の重み固定、A/Bの学習、QLoRAの4bit圧縮。', '',
              'q2：第3回p.39に外部保存から次のコンテキストへ読み戻す説明がある。p.40はOpenClawで全てのメモを長期保存しないことを示す。p.65はコンパクションとセッションをまたぐ記録を区別する。', '',
              'q3：第2回p.52のパラメータ学習と、第3回p.13・39・65の情報保存・再注入を比較する。', '',
              'q4：第2回p.13の3/5は説明用の例である。第1回p.19は別のチャットボット事例、第3回p.64は別の評価指標で、今回の実測値として置き換えない。回答保留を支える不足判断と、資料全体に記載がないという証明は区別する。', '',
              '## 限界と次の検証', '',
              '独立な質問は4問であり、方式の反復を含む16回答を16種類の質問とは扱わない。基本RAGが根拠取得100%である上限効果があり、Graph全般の有効性は判断できない。時間差はほぼなく、費用差7.77%はこの実行の出力240tokensの差による。次は未使用の質問と判定基準を事前に固定して検証する。', '',
              '## 原記録への参照', '',
              '- [条件・事前の回答基準](config.json)',
              '- [全回答・取得本文・測定値](records.jsonl)',
              '- [事前の参照ページ本文](reference_pages.json)',
              '- [回答ごとの判定・実引用一覧](human_review.json)',
              '- [補足集計のJSON](review_audit.json)', '']
    return '\n'.join(lines)


def add_notice(text, addendum_link):
    if MARKER in text:
        return text
    first, rest = text.split('\n', 1)
    notice = (MARKER + '\n\n> **引用集計の補足**：以下の自動抽出IDの表は、併記された後続ページを数え落とす参考値です。'
              '本文照合では合計39件（基本19・Graph20）で、すべて取得本文内に存在しました。'
              '意味的な裏付けの判定は別に行っています。['
              '確認済みの引用一覧・判定根拠・集計の補足](' + addendum_link + ')を参照してください。\n')
    return first + '\n\n' + notice + rest.replace('引用IDの文脈内一致', '自動抽出IDの文脈内一致（参考）')


def archive_result(root, directory, config):
    dest = checked_path(root, Path('lectures/05')/f'day5_results_{RUN_ID}.zip')
    tmp = checked_path(root, Path(str(dest.relative_to(root)) + '.tmp'))
    names = ['config.json', 'result.json', 'records.jsonl', 'report.md', 'human_review.json',
             'reference_pages.json', 'progress.json', 'review_audit.json', 'review_addendum.md']
    try:
        with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
            for name in names:
                bundle.write(checked_path(root, RUN_REL/name), arcname=f'{RUN_ID}/{name}')
            for name in config['code_fingerprints']:
                bundle.write(checked_path(root, RUN_REL/'source_snapshot'/name), arcname=f'{RUN_ID}/source_snapshot/{name}')
            bundle.write(checked_path(root, 'scripts/finalize_day5.py'), arcname=f'{RUN_ID}/postrun_review_source/finalize_day5.py')
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accept-review', action='store_true', help='確認案・原回答を確認し、判定と観察を採用して提出ファイルへ反映する')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    directory, config, records = verify(root)
    receipt_path = checked_path(root, Path('lectures/05/.cache')/f'finalize_{RUN_ID}.json')
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        if receipt.get('tool_version') != VERSION or receipt.get('run_id') != RUN_ID:
            raise ValueError('既存の仕上げ記録と版が異なります。上書きしていません。')
        changed = [name for name, expected in receipt['output_sha256'].items()
                   if not checked_path(root, name).is_file() or sha(checked_path(root, name).read_bytes()) != expected]
        if changed:
            raise ValueError('仕上げ後に編集されたファイルがあります。編集を保護して停止しました: ' + ', '.join(changed))
        print('この実行の提出ファイルは取り込み済みです。変更せず終了します。')
        return 0
    if sha((directory/'human_review.json').read_bytes()) != PAYLOAD['pending_review_sha256']:
        raise ValueError('human_review.jsonに独自の記入があります。記入内容を保護して停止しました。')
    answer_path = checked_path(root, 'lectures/05/answer.md')
    original = answer_path.read_text(encoding='utf-8')
    if original.count('\n## 宿題\n') != 1 or '<!-- DAY5_GENERATED_HOMEWORK -->' not in original.split('\n## 宿題\n', 1)[1]:
        raise ValueError('answer.mdの宿題欄が自動生成テンプレートではありません。上書きしていません。')
    if sha(original.split('\n## 宿題\n', 1)[1].encode('utf-8')) != PAYLOAD['initial_homework_sha256']:
        raise ValueError('answer.mdの宿題欄に独自の記入があります。記入内容を保護して停止しました。')
    for filename, expected in PAYLOAD['initial_outputs_sha256'].items():
        if sha(checked_path(root, Path('lectures/05')/filename).read_bytes()) != expected:
            raise ValueError(filename + 'に独自の記入があります。上書きしていません。')
    managed = [RUN_REL/'human_review.json', RUN_REL/'result.json', RUN_REL/'report.md',
               RUN_REL/'review_audit.json', RUN_REL/'review_addendum.md',
               Path('lectures/05/answer.md'), Path('lectures/05/quri_answers.md'), Path('lectures/05/PR_BODY.md'),
               Path('lectures/05')/f'day5_results_{RUN_ID}.zip', Path('scripts/finalize_day5.py')]
    for relative in managed:
        checked_path(root, relative)
    checked_path(root, 'lectures/05/.cache/answer_backups')
    checked_path(root, 'lectures/05/.cache/finalization_backups')
    checked_path(root, Path('lectures/05')/f'day5_results_{RUN_ID}.zip.tmp')
    for relative in [RUN_REL/'review_audit.json', RUN_REL/'review_addendum.md']:
        if checked_path(root, relative).exists():
            raise ValueError('既存の補足ファイルがあります。上書きしていません: ' + str(relative))
    own_bytes = Path(__file__).read_bytes()
    stored_tool = checked_path(root, 'scripts/finalize_day5.py')
    if stored_tool.exists() and stored_tool.read_bytes() != own_bytes:
        raise ValueError('scripts/finalize_day5.pyに別のファイルがあります。')
    review = deepcopy(PAYLOAD['review'])
    audit = audit_records(config, records, review)
    print('16件の正常完了・設定・元データ・コードの一致を確認しました。')
    print('確認案: 回答基準達成は両方式6/8。q2は読み戻しの説明不足。')
    print('確認案: 最終取得ページ集合は全問同じ。Graphによる改善は未確認。')
    print('確認案: 引用自動抽出29件→本文照合39件。意味的裏付け1件はunsure。')
    print('確認案: 今回は基本RAGを採用。Q3は' + str(len(review['observations']['q3'])) + '文字。')
    if not args.accept_review:
        print('確認のみで終了しました。原回答と確認案を確認後、次を実行してください。')
        print('python finalize_day5.py --accept-review')
        return 0
    now = datetime.now(JST).isoformat(timespec='seconds')
    review.update(status='reviewed', reviewer='takerunakao（AI支援の確認案を読み、判定・観察を確認）',
                  reviewed_at=now, confirmation={'accepted_by_user_command': True, 'tool_version': VERSION,
                                                'command_flag': '--accept-review', 'accepted_at_jst': now})
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:6]
    backup = checked_path(root, Path('lectures/05/.cache/finalization_backups')/stamp)
    backup.mkdir(parents=True)
    previous = {}
    for relative in managed:
        path = checked_path(root, relative)
        previous[str(relative)] = path.read_bytes() if path.exists() else None
        if path.exists():
            destination = backup/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(previous[str(relative)])
    write_json(backup/'manifest.json', {'run_id': RUN_ID, 'created_at_jst': now,
                                     'existing_paths': [p for p, raw in previous.items() if raw is not None]})
    try:
        write_json(directory/'human_review.json', review)
        env = dict(os.environ)
        env.pop('GEMINI_API_KEY', None)
        subprocess.run([sys.executable, 'scripts/prepare_day5_answer.py', '--run', str(RUN_REL)], cwd=root, env=env, check=True)
        audit.update(reviewed_at=now, reviewer=review['reviewer'], tool_sha256=sha(own_bytes))
        write_json(directory/'review_audit.json', audit)
        write_text(directory/'review_addendum.md', addendum_text(audit))
        write_text(answer_path, add_notice(answer_path.read_text(encoding='utf-8'), f'results/{RUN_ID}/review_addendum.md'))
        report_path = directory/'report.md'
        write_text(report_path, add_notice(report_path.read_text(encoding='utf-8'), 'review_addendum.md'))
        pr_path = root/'lectures/05/PR_BODY.md'
        write_text(pr_path, pr_path.read_text(encoding='utf-8') + '\n## 評価時の補足\n\n'
                   '- q2は根拠を取得できても読み戻しの説明が欠け、事前基準では未達とした。\n'
                   '- 引用自動抽出の見落としは原ログを変更せず、本文照合の39件を別記録へ補足した。\n'
                   '- 取得IDの一致と引用内容の裏付けを区別し、1回答の引用判定はunsureを維持した。\n'
                   f'- 補足: `lectures/05/results/{RUN_ID}/review_addendum.md`\n')
        atomic_bytes(stored_tool, own_bytes)
        archive_result(root, directory, config)
        if sha((directory/'records.jsonl').read_bytes()) != PAYLOAD['records_sha256']:
            raise ValueError('原記録のハッシュが変わりました。')
        output_hashes = {str(p): sha(checked_path(root, p).read_bytes()) for p in managed}
        write_json(receipt_path, {'tool_version': VERSION, 'run_id': RUN_ID, 'confirmed_at_jst': now,
                                 'output_sha256': output_hashes, 'backup_directory': str(backup.relative_to(root))})
    except BaseException:
        for relative, raw in previous.items():
            path = checked_path(root, relative)
            if raw is None:
                path.unlink(missing_ok=True)
            else:
                atomic_bytes(path, raw)
        raise
    print('提出用ファイルを更新しました。モデルAPIは呼び出していません。')
    print('確認するファイル: lectures/05/answer.md')
    print('Quri入力用: lectures/05/quri_answers.md')
    print('PR概要: lectures/05/PR_BODY.md')
    print('バックアップ: ' + str(backup.relative_to(root)))
    print('GitHubへのcommit・push・PR作成は、続けてご自身で行ってください。')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('中断しました。更新中の提出ファイルは処理前の内容へ戻しました。', file=sys.stderr)
        raise SystemExit(130)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print('確認して停止しました: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
