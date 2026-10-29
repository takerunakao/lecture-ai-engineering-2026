"""Generate the Day2 homework section from real, complete experiment records.

python scripts/prepare_day2_answer.py --run-dir lectures/02/results/<run-id>
python scripts/prepare_day2_answer.py --pending   # preparation status only
Without arguments, use the latest completed run. No model inference is run here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.day2_eval import CATEGORIES, load_cases, score_answer, summarize

BASE = ROOT / 'lectures' / '02'
START = '<!-- DAY2_ADVANCED_REPORT_START -->'
END = '<!-- DAY2_ADVANCED_REPORT_END -->'
CATEGORY_NAMES = {'known': '既知語', 'paraphrase': '言い換え', 'out_of_glossary': '用語集にない語'}
LABEL_NAMES = {'before': '学習前', 'after': 'LoRA学習後', 'search': '用語名・別名検索'}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def percent(value) -> str:
    return '未実行' if value is None else f'{100 * value:.1f}%'


def number(value, digits=3) -> str:
    return '未記録' if value is None else f'{value:.{digits}f}'


def verify_payload(payload: dict, cases: list[dict], label: str) -> dict:
    rows = payload['rows']
    if [r['id'] for r in rows] != [c['id'] for c in cases]:
        raise ValueError(f'{label}: missing/reordered/duplicate evaluation IDs')
    verified_rows = []
    for row, case in zip(rows, cases):
        if row['question'] != case['question'] or row['category'] != case['category']:
            raise ValueError(f'{label}: evaluation inputs differ from fixed cases')
        scored = score_answer(row['raw'], case)
        for key in ['format_ok', 'content_ok', 'both_ok', 'review_ok']:
            if row[key] != scored[key]:
                raise ValueError(f'{label}: saved score does not match raw response: {row["id"]}/{key}')
        verified_rows.append({**row, **scored})
    recomputed = summarize(verified_rows, label)
    for key in ['n', 'format_rate', 'content_rate', 'both_rate', 'review_accuracy']:
        if payload['summary'][key] != recomputed[key]:
            raise ValueError(f'{label}: summary mismatch for {key}')
    # Only measured timing is carried over. Every score, category count and
    # failure classification used in prose is derived again from the raw text.
    for key in ['seconds', 'generation_seconds']:
        if key in payload['summary']:
            recomputed[key] = payload['summary'][key]
    if all('truncated' in row for row in verified_rows):
        recomputed['truncated_n'] = sum(row['truncated'] for row in verified_rows)
    return {**payload, 'rows': verified_rows, 'summary': recomputed}


def select_run(run_dir: Path | None) -> Path:
    if run_dir:
        return run_dir.resolve()
    available = []
    for path in sorted((BASE / 'results').glob('*/result.json')):
        result = read_json(path)
        if result.get('completed') is True and result.get('status') == 'completed':
            available.append(path.parent)
    if not available:
        raise ValueError('完了した学習結果がありません。先にColabで学習を実行してください。準備状況のみなら --pending を指定します。')
    return available[-1]


def fenced(text: str) -> str:
    # Preserve a generated code fence as data rather than breaking the report.
    marker = '`' * max(3, max((len(part) for part in __import__('re').findall(r'`+', text)), default=0) + 1)
    return f'{marker}text\n{text}\n{marker}'


def build_report(run_dir: Path | None, pending: bool = False) -> tuple[str, str | None]:
    manifest = read_json(BASE / 'data' / 'manifest.json')
    cases = load_cases(BASE / 'data' / 'eval_cases.json')
    current_eval_hash = hashlib.sha256((BASE / 'data' / 'eval_cases.json').read_bytes()).hexdigest()
    current_train_hash = hashlib.sha256((BASE / 'data' / 'glossary_sft.jsonl').read_bytes()).hexdigest()
    if current_eval_hash != manifest['eval_cases_sha256'] or current_train_hash != manifest['train_dataset_sha256']:
        raise ValueError('データとmanifestのハッシュが一致しません。条件変更を確認してください。')
    result = None
    outputs = {}
    q3 = None
    if pending:
        outputs['search'] = verify_payload(read_json(BASE / 'data' / 'search_baseline.json'), cases, 'search')
        status = '**発展：データ・実装・検索の評価まで実施。GPUによるLoRA学習とモデルの前後評価は未実行。**'
        artifacts = '[検索の実測記録](data/search_baseline.json)'
    else:
        run_dir = select_run(run_dir)
        result = read_json(run_dir / 'result.json')
        if result.get('status') != 'completed' or result.get('completed') is not True or result.get('executed_training_myself') is not True:
            raise ValueError('未完了・中断・参考値の実験を完了した本人の学習結果として提出用に取り込むことはできません。')
        if result.get('dataset_sha256') != current_train_hash or result.get('eval_cases_sha256') != current_eval_hash:
            raise ValueError('学習時と現在のデータハッシュが違います。結果とデータを同じ版に揃えてください。')
        for label in ['before', 'after', 'search']:
            outputs[label] = verify_payload(read_json(run_dir / f'eval_{label}.json'), cases, label)
        status = '**発展：自分の実行環境でLoRA学習と学習前・学習後・用語集検索の比較を実施。**'
        rel = run_dir.relative_to(BASE).as_posix()
        artifacts = f'[result.json]({rel}/result.json) ／ [学習前]({rel}/eval_before.json) ／ [学習後]({rel}/eval_after.json) ／ [検索]({rel}/eval_search.json) ／ [学習ログ]({rel}/train_log.json)'

    lines = [START, status, '', '### 1. 取り組んだ内容', '',
        '取り組んだレベルは**発展**。講座の用語集からQ&Aを生成してLoRAで学習し、学習前・学習後・用語集検索を、同じ評価問題で比較する実験を実装した。', '',
        '元の `scripts/make_sft_dataset.py` は変更せずに実行し、その出力を `data/glossary_sft_raw.jsonl` に保存した。'
        '元のassistant出力は通常の文章なので、演習の評価形式に合わせて `{"answer": 定義, "needs_review": false}` に変換し、学習・推論で共通のsystem指示を追加した。', '',
        f'用語集{manifest["glossary_terms"]}語×2種類の質問で{manifest["positive_records"]}件を生成し、'
        f'用語集にない語に確認を求める例を{manifest["negative_records"]}件加え、計{manifest["train_records"]}件を学習データとした。'
        '追加した語は「' + '・'.join(manifest['negative_training_terms']) + '」。評価用の範囲外8語とは分けた。', '',
        '### 2. 評価問題と比較条件', '',
        '| 区分 | 件数 | 設計 |', '|---|---:|---|',
        '| 既知語 | 8 | 用語集に載る8概念。学習時と異なる質問文で定義を尋ねる |',
        '| 言い換え | 8 | 同じ8概念のうち、登録済み別名を使う4問と、用語名を出さない説明型4問 |',
        '| 用語集にない語 | 8 | DoRA、AdaLoRA、DPO、RLHF、RoPE、知識蒸留、MoE、ビームサーチ |', '',
        '評価用の質問と正解は学習前に固定した。質問文の重複は0件だが、既知語・言い換えの対象概念と定義は学習データに含まれる。'
        'そのため、測っているのは学習した概念に対する新しい聞き方への対応であり、未学習概念への一般化ではない。', '',
        '`needs_review` の正解は「この講座用語集に回答の根拠があるか」に基づく。用語集にない語をモデルが事前学習で知っている可能性はあり、'
        'その語について正しい一般知識を説明できても、本実験の範囲限定ルールでは確認要求が必要となる。', '',
        '学習前・学習後には同じsystemと質問だけを渡し、用語集本文をプロンプトに入れない。'
        '検索方式は同じ質問から用語名・ID・別名を検出し、一意に見つかった場合に原定義をJSONへ整形する。'
        'goldや正解のterm_idを検索に渡さない。名称が見つからない場合や複数候補の場合は確認要求を返す。'
        'これは名称照合による検索・抽出であり、埋め込み検索やLLMによるRAG生成を評価したものではない。', '',
        '形式遵守率はJSONの必須キー・余分なキーの有無・型で判定する。内容正解率は、真偽値の `needs_review` が正解と一致し、'
        '`answer` に各問題の必須語句をすべて含む割合とする。コードブロックなど形式違反があってもJSON部分を読める場合は内容だけ別に採点する。'
        '必須語句による判定は言い換えを取りこぼしたり、誤った説明でも語句だけ揃って通したりするため、完全な意味的正しさの評価ではない。', '',
        '[評価問題と正解](data/eval_cases.json) ／ [学習データ](data/glossary_sft.jsonl) ／ [条件・ハッシュ](data/manifest.json)', '',
        '### 3. 学習設定', '',
        'モデルは講義と同じ `Qwen/Qwen3.5-0.8B`、revisionは `2fc06364715b967f1860aea9cf38778875588b17`。'
        '量子化せずfloat32でLoRA学習する。`r=16`、`alpha=32`、`lr=2e-4`、seed=42、batch=4、勾配累積=2、warmup=6。'
        '用語集データは元のFAQより多いため、epochを20から3へ変更した。1 GPUでは48更新を予定し、実測の更新回数は実行ログで確定する。', '',
        '会話全体の上限は512トークンとし、学習前に全例をtokenizeして超過があれば停止する。'
        '生成は学習前後とも貪欲生成・`enable_thinking=False`・最大256トークン。元の96から256へ増やしたのは用語定義が長いためで、上限到達も個別に記録する。'
        '学習前の評価はadapterを取り付ける前に実行し、両評価で `eval()` を使用する。'
        '損失は講義と同様にsystem/userを含む会話全体に対して計算し、assistant部分だけの損失とはしない。', '',
        '依存版は講義の `transformers==5.18.0`、`peft==0.21.1`、`trl==1.14.2`、`accelerate==1.15.0`、`datasets==5.1.0` に固定する。'
        'torchはColab同梱版を使用し、実行時の版を記録する。', '',
        '### 4. 結果', '',
        '| 方式 | 評価件数 | 形式遵守率 | 内容正解率 | 形式・内容とも正解 | needs_review一致率 |',
        '|---|---:|---:|---:|---:|---:|']
    for label in ['before', 'after', 'search']:
        s = outputs.get(label, {}).get('summary')
        lines.append(f'| {LABEL_NAMES[label]} | ' + ('— | 未実行 | 未実行 | 未実行 | 未実行 |' if s is None else
            f'{s["n"]} | {percent(s["format_rate"])} | {percent(s["content_rate"])} | {percent(s["both_rate"])} | {percent(s["review_accuracy"])} |'))
    lines += ['', '| 評価区分 | 学習前の内容正解率 | 学習後の内容正解率 | 検索の内容正解率 |', '|---|---:|---:|---:|']
    for category in CATEGORIES:
        cells = [percent(outputs[label]['summary']['by_category'][category]['content_rate']) if label in outputs else '未実行'
                 for label in ['before', 'after', 'search']]
        lines.append('| ' + ' | '.join([CATEGORY_NAMES[category], *cells]) + ' |')
    lines += ['', artifacts, '', '### 5. 結果から分かることと限界', '']
    search_rows = outputs['search']['rows']
    misses = [row['id'] for row in search_rows if not row['both_ok']]
    lines.append(f'名称照合による検索は{sum(row["both_ok"] for row in search_rows)}/{len(search_rows)}問で形式・内容とも正解だった。'
                 'JSONはプログラムで組み立てるため、検索の形式遵守率は生成モデルの形式学習能力と同じ意味ではない。')
    if misses:
        lines += ['', '検索が通らなかった問題：`' + '`、`'.join(misses) + '`。'
            'この方式は用語名や別名を質問中から見つける仕組みなので、名前を出さない説明型の質問への対応が弱い。'
            'この結果を意味検索やRAGを含む検索一般の限界として扱わない。']
    if pending:
        lines += ['', 'GPU学習とモデルの生成はまだ実行していない。したがって、学習によって形式・内容が改善したか、'
                      '確認要求が増減したか、検索よりよい回答が得られたかは未確認である。検索結果だけからLoRAの効果を結論づけない。']
    else:
        before, after = outputs['before'], outputs['after']
        b, a = before['summary'], after['summary']
        regressed = [br['id'] for br, ar in zip(before['rows'], after['rows']) if br['both_ok'] and not ar['both_ok']]
        improved = [br['id'] for br, ar in zip(before['rows'], after['rows']) if not br['both_ok'] and ar['both_ok']]
        lines += ['', f'学習前後で、形式遵守率は{percent(b["format_rate"])}→{percent(a["format_rate"])}、'
                      f'内容正解率は{percent(b["content_rate"])}→{percent(a["content_rate"])}だった。'
                      f'形式・内容とも不合格から合格になった問題は{len(improved)}問、合格から不合格への退行は{len(regressed)}問だった。', '',
                  '改善した問題：' + ('`' + '`、`'.join(improved) + '`' if improved else 'なし') + '。',
                  '退行した問題：' + ('`' + '`、`'.join(regressed) + '`' if regressed else 'なし') + '。', '',
                  f'学習後、範囲外の質問に `needs_review=false` と答えた例は{a["unsupported_assertions"]}問、'
                  f'根拠のある質問に `needs_review=true` と答えた例は{a["over_refusals"]}問だった。'
                  'これらは読めた真偽値に基づく分類で、形式崩れで真偽値を取得できない例は含めない。']
        train = result.get('train', {})
        lines += ['', '#### 学習の実測記録', '',
                  '| 項目 | 値 |', '|---|---|',
                  f'| 学習更新回数 | {train.get("global_step", "未記録")} |',
                  f'| 実行epoch | {train.get("epoch", "未記録")} |',
                  f'| 学習時間（秒） | {number(train.get("seconds"))} |',
                  f'| 最後に記録されたloss | {number(train.get("final_logged_loss"), 6)} |',
                  f'| 最後のlossの記録step | {train.get("final_logged_loss_step", "未記録")} |',
                  f'| 全学習の平均train_loss | {number(train.get("train_loss"), 6)} |', '',
                  '最後にログへ出た区間のlossと、全学習を通した平均train_lossは区別した。lossが下がっても評価問題の正解率が上がるとは限らない。', '',
                  '| 方式 | 評価全体の経過秒 | 生成上限による打切り |', '|---|---:|---:|']
        for label in ['before', 'after', 'search']:
            payload = outputs[label]
            trunc = '対象外' if label == 'search' else str(sum(row['truncated'] for row in payload['rows'])) if all('truncated' in row for row in payload['rows']) else '未記録'
            lines.append(f'| {LABEL_NAMES[label]} | {number(payload["summary"].get("seconds"))} | {trunc} |')
        lines += ['', '生成はGPU、名称照合はCPUで実行するため、経過秒はこの構成で利用した場合の所要時間として読み、同じ計算量に対する純粋な速度比較とはしない。', '',
                  '実行時設定（予定値よりこちらを優先）：', '```json', json.dumps(result.get('config', {}), ensure_ascii=False, indent=2), '```', '',
                  '実行時ライブラリ：', '```json', json.dumps(result.get('versions', {}), ensure_ascii=False, indent=2), '```']
        q3 = (f'講座用語集58語から116件のQ&Aを生成し、確認要求の8例を加えてLoRA学習しました。'
              f'学習と重複しない24問を既知語・言い換え・範囲外に分け、学習前後と用語名検索を比較しました。'
              f'形式遵守率は{percent(b["format_rate"])}から{percent(a["format_rate"])}、内容正解率は{percent(b["content_rate"])}から{percent(a["content_rate"])}でした。'
              f'形式と内容を別々に採点し、学習後の退行{len(regressed)}問や範囲外への断定も記録しました。'
              '検索に正解語を渡さず、用語名を含まない質問も設け、データ重複・adapter混入・生成打切りを確認できる設計を工夫しました。')
        if len(q3) > 400:
            raise ValueError('Q3 exceeded 400 characters')
    lines += ['', '### 6. ファインチューニングが向く場面・向かない場面', '',
        '設計上、JSON形式や定型的な応答方針を多数の質問に共通して適用したい場合は、ファインチューニングを検討する余地がある。'
        '一方、講座の期限・設定・定義などを頻繁に更新し、どの資料に基づくかを確認したい用途では、用語集を更新して検索・参照する構成が扱いやすいと考える。'
        '今回の比較は24問・1 seedの小規模実験なので、一般的なモデルの優劣や「学習すれば未知語を適切に断れる」といった保証には使わない。', '',
        '特に、質問の言い換え、形式の維持、根拠の範囲の判断は別の能力として見る必要がある。'
        '実利用では、学習による形式の調整と、検索による更新可能な根拠の供給を組み合わせる構成も候補になるが、今回その組合せの効果は測定していない。', '',
        '### 7. AI支援と確認範囲', '',
        'ChatGPTを、評価問題案、データ変換・採点・学習・レポート生成コードの作成とレビューに使用した。'
        'ローカルで実行した検索結果と、Colabで実行するモデル学習の結果を区別して保存する。'
        '講師の参考結果や期待される改善率を自分の測定値として流用しない。', '',
        f'`executed_training_myself`: `{str(not pending).lower()}`。'
        + ('現時点ではGPU学習未実行。' if pending else '実行ログに基づいて学習・前後評価の完了を確認した。'), '',
        '学習データSHA-256：`' + current_train_hash + '`。',
        '評価データSHA-256：`' + current_eval_hash + '`。', '',
        '参考： [講義のDay2課題](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/662cddd52724b330f3f4cd15123d1e55cb474874/lectures/02/problem.md)、'
        '[講義ノートブック](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/f9ab3d5288ba5d4cd6fecd5e30515192a5cb05b6/notebooks/lora_format_tuning.ipynb)、'
        '[TRL 1.14.2 SFTTrainer](https://huggingface.co/docs/trl/v1.14.2/sft_trainer)。', '',
        '### 付録：質問ごとの出力', '']
    for i, case in enumerate(cases):
        lines += [f'#### {case["id"]}（{CATEGORY_NAMES[case["category"]]}）', '', case['question'], '',
                  '正解のneeds_review：`' + str(case['gold']['needs_review']).lower() + '`。必須語句：' + '、'.join(case['gold']['must_include']) + '。', '']
        for label in ['before', 'after', 'search']:
            if label not in outputs:
                continue
            row = outputs[label]['rows'][i]
            lines += [f'**{LABEL_NAMES[label]}**：形式={row["format_ok"]}、内容={row["content_ok"]}。', '', fenced(row['raw']), '']
    lines.append(END)
    return '\n'.join(lines) + '\n', q3


def write_answer(section: str) -> Path:
    target = BASE / 'answer.md'
    existing = target.read_text(encoding='utf-8')
    if START in existing and END in existing:
        prefix, rest = existing.split(START, 1)
        _, suffix = rest.split(END, 1)
        updated = prefix + section.rstrip() + suffix
    else:
        before, sep, homework = existing.partition('## 宿題')
        if not sep:
            raise ValueError('answer.mdに「## 宿題」がありません。既存内容は変更していません。')
        empty_template = ('- 取り組んだレベル：基礎 / 実装 / 発展\n'
                          '- 変えた設定やデータ：\n'
                          '- 結果（比較表や数字）：\n'
                          '- ファインチューニングが向く場面・向かない場面についての考察：')
        kept = '' if homework.strip() == empty_template else homework.strip() + '\n\n'
        updated = before + sep + '\n\n' + kept + section
    target.write_text(updated.rstrip() + '\n', encoding='utf-8')
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--pending', action='store_true', help='Write preparation status without claiming GPU execution')
    args = parser.parse_args()
    if args.pending and args.run_dir:
        parser.error('--pending and --run-dir cannot be combined')
    try:
        section, q3 = build_report(args.run_dir, args.pending)
        target = write_answer(section)
        if q3 is not None:
            (BASE / 'submission_q3.txt').write_text(q3 + '\n', encoding='utf-8')
        print(f'更新しました: {target.relative_to(ROOT)}')
        if q3:
            print(f'Q3: {len(q3)}文字 / 400文字以内')
        elif args.pending:
            print('これは準備状況の記録です。GPU学習・モデル前後評価・提出用Q3は未完了です。')
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'取り込みを中止しました: {exc}\n')


if __name__ == '__main__':
    main()
