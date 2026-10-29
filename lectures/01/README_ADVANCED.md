# Day1 発展課題: Gemini の応答時間とトークン数を比較する

この追加コードは、AIエンジニアリング実践講座2026の第1回発展課題の実装です。**今回の提出では、実施済みの18試行をまとめた [answer.md](answer.md) を収録しています。**

## 提出した実験と、公開する記録

- 実行ID：`20261019T152041Z_1d808e4c`。
- 実行時間帯：2026年10月20日 00:20:42.562〜00:24:57.982（日本時間）。
- 2モデル × 3設問 × 3反復の18試行を実施。`gemini-3.5-flash-lite` は9/9正常完了、`gemini-3.8-flash` は9/9でHTTP 503。
- [answer.md](answer.md) に、実験条件、成功回答の応答時間・トークン集計、回答内容の考察、全18試行の回答・状態・応答時間を保存。
- 一方のモデルに成功回答がないため、モデル間の回答品質・生成速度の優劣は結論づけていません。
- 利用階層とプロジェクト固有の上限は未確認。[day1_quota_notes.md](day1_quota_notes.md) に、確認できた実行結果と未確認事項を整理しています。

元の `plan.json`・`responses.jsonl`・`summary.csv` は、この提出には未添付です。既存の実測レポートを根拠として公開し、元JSONからの再集計にはその原ファイルの追加が必要です。実行ソースのSHA-256は `96e157463dc0c5a8f3fb59c08cbe0e593dc43148c813622f53765ffbb272ea73` で、収録した `app/benchmark_day1.py` と一致します。

以下は、条件を変えて再実験する際の手順です。今回の提出作業ではAPIを追加実行していません。

## 1. 今回の実験

| 項目 | 今回の設定 |
|---|---|
| モデル | `gemini-3.5-flash-lite` と `gemini-3.8-flash` |
| 質問 | 短いLoRA説明、長めのRAGとファインチューニングの比較、講座固有の宿題ルール |
| 繰り返し | 各条件3回。2モデル × 3質問 × 3回 = 18回、各モデル9回 |
| 出力上限 | 同一の `max_output_tokens=2048` |
| 会話履歴・外部検索 | 使用しない。質問ごとに独立した呼び出し |
| 実行順 | 反復ごとに質問とモデルの順序を回転 |
| 間隔 | 全リクエストの開始間隔を最低15秒にする |
| 応答時間 | API呼び出し直前から、非ストリーミング応答の受信完了まで |
| 主要集計 | 完了した応答の中央値・最小・最大、トークン数、失敗件数 |

3回は発展課題の必須回数ではありません。残枠が少ない場合は、両モデルを同じ条件で比較できるよう、`--repeats 2` とすれば計12回・各6回になります。2質問で3回ずつ測る場合は `--question-ids short long --repeats 3` とします。

モデル名は2026-10-19にGoogle公式モデル一覧で確認しました。`gemini-3.5-flash`（liteなし）は非推奨で別モデルへ転送されるため使いません。今回の2モデルでは非推奨になった `temperature`、`top_p`、`top_k` を明示指定しません。

## 2. 初めて取り組む場合の環境準備

1. [講座リポジトリ](https://github.com/matsuolab/lecture-ai-engineering-2026)を開き、Forkを押す。
2. Ownerを自分の個人アカウントにしてForkする。提出先は自分の公開fork。
3. [Google AI Studio](https://aistudio.google.com/apikey)でAPIキーを作成する。
4. GitHubのプロフィール画像 → Settings → Codespaces → Secrets → New secretで、名前を `GEMINI_API_KEY` にする。Valueにキーを入力し、Repository accessで自分のforkを選ぶ。キーをチャットやコードに書かない。
5. 自分のforkで Code → Codespaces → Create codespace on main。起動後にSecretを追加した場合はCodespacesを停止・再起動する。

この作業には新しいリポジトリを一から作る必要はありません。講座コードをForkして使います。

## 3. 再実験用コードの確認

このブランチには実装済みのコードが入っています。講座の依存環境を用意したうえで、通信を使わない動作確認から始めます。

```bash
uv run pytest -q tests/test_benchmark_day1.py tests/test_tools.py
uv run python -m app.benchmark_day1 --dry-run
```

`app/ask.py` にはAPIが返したトークン数の表示も追加しました。未返却の値は「未取得」と表示し、0と区別します。講座指定の `pyproject.toml` と `uv.lock` は変更していません。

`--dry-run` は計画を表示するだけです。APIキー・SDKの読み込み・API呼び出しは不要で、測定結果も作りません。

## 4. 無料枠を確認して実測

[AI Studioのレート制限画面](https://aistudio.google.com/rate-limit)で、自分のプロジェクトと対象モデルについて、RPM・入力TPM・RPDと、今日の使用量を確認します。確認した値と日時を `lectures/01/day1_quota_notes.md` に記録してください。

教材P.16の無料枠は「講座の実測値」です。自分のアカウントに対する保証値ではありません。3.8 Flashを9回測る場合、演習・動作確認・失敗した呼び出しを含めた残枠に注意します。利用tierが有料なら、このコードの呼び出しも課金対象になり得るため、利用tierも記録します。

基本案:

```bash
uv run python -m app.benchmark_day1 --repeats 3
```

残枠が少ない場合は、上のコマンドを実行する前に、次のどちらかへ変更します。

```bash
uv run python -m app.benchmark_day1 --repeats 2
```

```bash
uv run python -m app.benchmark_day1 --question-ids short long --repeats 3
```

これらを続けて全部実行する必要はありません。一つを選びます。標準の18回では、開始間隔だけで最短でも約4分15秒かかり、さらに最後の応答時間が必要です。長い応答がある場合はさらに時間がかかります。ターミナルが待機中でも異常ではありません。

モデルを変更するときは両方を指定できます。

```bash
uv run python -m app.benchmark_day1 --models gemini-3.5-flash-lite gemini-3.8-flash --repeats 3
```

`--models` は講座の `AIE_MODEL` と同じモデル選択を一つの実験内で行うための追加オプションです。選択したモデル名・返却されたmodel_version・生成設定は計画とログに保存します。

### エラーが出た場合

- **429**: 記録して停止します。RPM・入力TPM・RPDなど、何の制限かをAI Studioで確認します。1分待てば必ず解消するとは限りません。
- **503**: サービス側の利用不能として記録します。429とは区別します。
- **400/401/403/404など**: モデル名、APIの利用可否、Secret、設定を確認します。ログに記録された種類・コードを見て対応します。
- **途中停止**: 取得済みの行を残し、部分的な結果として扱います。次の実行は別runとして保存され、同じ条件の測定でも再びAPIを呼びます。

測定のために意図的に制限へ到達させる必要はありません。429が出なかった場合も「今回の条件では発生しなかった」と記述すれば、実測と仕様を区別した考察になります。

## 5. 結果を読む

実行ごとに `lectures/01/benchmark_results/<run名>/` ができます。

| ファイル | 役割 |
|---|---|
| `plan.json` | 正確な質問文、予定順序、モデル、反復数、生成・測定設定 |
| `responses.jsonl` | 試行ごとの回答本文、計測値、エラーの生ログ |
| `summary.csv` | モデル・質問ごとの集計 |
| `answer.generated.md` | 実測から作る提出用レポートの下書き |

生成された下書きにあるTODOへ、自分で確かめた比較・考察を追記します。数値の転記は集計表を参照し、実行していないことを実行済みと書かないでください。

APIを再び呼ばず、保存済みログから集計だけ作り直す場合:

```bash
uv run python -m app.benchmark_day1 --report lectures/01/benchmark_results/<実際のrun名>
```

これは `answer.generated.md` を再生成します。自分の文章を編集する前に、次の節のコマンドで `answer.md` へ取り込んでください。

### 測定値の解釈

- 記録する時間は通信やサーバー側の待ちを含む全体の応答時間です。モデル内部だけの推論時間や、最初のトークンが来るまでの時間（TTFT）ではありません。
- API呼び出しの前に行う15秒間隔の調整は、応答時間に含めません。ただしネットワーク接続などAPI呼び出し内の処理は含まれます。
- 入力・回答・思考・合計・キャッシュなどのトークン数は返却値をそのまま残します。未返却は欠損であり、0とは区別します。
- 合計トークンを「入力＋回答」だけで再計算しません。思考等も含まれ得ます。入力に含まれるキャッシュ数をもう一度加えません。
- 同じ出力上限でも、実際の回答長や思考量はそろいません。短い回答ほど速かった場合、モデルの優劣だけで説明しないようにします。
- 正常に完了した応答と、上限による切断・空の応答・API失敗を区別します。少数の成功例だけから安定性や優劣を断定しません。
- 3回の実験で出た中央値・範囲は探索的な観察です。統計的有意差や全用途での優劣は主張しません。
- 回答内容の正しさは別途読みます。特に講座の3レベルは `data/glossary.json` の `homework-levels` と照合します。速く短い回答であっても、内容が間違っていれば有用とはいえません。

## 6. 新しい実験をレポートとPRへ反映する

今回の `answer.md` は完成済みです。以下は新しい実験を行った場合の手順であり、今回の提出をやり直すための操作ではありません。新しいrunのレポートを取り込む場合、現在の完成レポートを保存してから進めます。

```bash
python scripts/prepare_day1_answer.py
```

未記入の講座テンプレートは置き換えます。演習などの記録がある場合は残して発展レポートを追加します。すでに追加済みのレポートがある場合は上書きせず停止します。runを指定するには `--run-dir lectures/01/benchmark_results/<run名>` を使います。

`lectures/01/answer.md` を開き、TODOを自分の観察に置き換えます。最低限、次を確認します。

1. どの質問でどちらのモデルが速かったか、または差が明確でなかったか。実際の数値を根拠にする。
2. 回答の長さ・トークン数・思考量が、時間差の解釈へどう影響したか。
3. AI Studioで確認した自分の上限と今回の呼び出し回数・入力トークン数との関係。429の有無を正直に書く。
4. 小規模試行、通信、モデルの既定設定などの限界。
5. AI支援の利用と、自分がコード・結果のどこを確認したか。

次のコマンドは、ファイルと内容を確認してから実行します。

```bash
uv run pytest -q tests/test_benchmark_day1.py tests/test_tools.py
git status --short
git add app/ask.py app/benchmark_day1.py tests/test_benchmark_day1.py scripts/prepare_day1_answer.py lectures/01/README_ADVANCED.md lectures/01/day1_quota_notes.md lectures/01/answer.md
git diff --cached --stat
git commit -m "Day1: compare Gemini response time and token usage"
git push -u origin lec01
```

新しい実験で `lectures/01/benchmark_results/` が生成された場合は、その実測ファイルも内容を確認して追加してください。今回の提出に存在しない原ログは、追加対象に指定していません。

自分のforkのGitHubページでPull requests → New pull requestを開きます。

- base repository: **自分のアカウントのfork**
- base branch: `main`
- compare branch: `lec01`

講座の `matsuolab/lecture-ai-engineering-2026` にPRを出さないよう、base repositoryを確認します。PRを作成したら、Q2には**自分の公開リポジトリのURL**を記載します。PRのURLは補足として記録できます。

提出後はCodespacesを停止します。教材P.18ではDay1の締切は原則2026-10-26とされています。提出フォームの案内が更新されていればそちらに従ってください。

## 7. Q1〜Q3

**Q1:** 今回の実測と考察に対応するレベルは「発展」です。

**Q2:** ご自身の公開forkは次のURLです。提出ファイルとPRが読めることを確認して記載します。

```text
https://github.com/takerunakao/lecture-ai-engineering-2026
```

**Q3:** 400文字以内で、実施した条件と観察を記載します。今回の結果では、Liteの9回成功とFlashの9回503、モデル間の性能優劣を判断できないこと、成功とエラー・欠測を分けた評価設計が要点です。本文の考察と一致する説明を使います。

## 8. 参照資料と作成時の検証範囲

- 講座の第1回演習資料 P.14–16、宿題資料（2026-10-19配布）
- [講座の第1回課題](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/main/lectures/01/problem.md)
- [講座の依存パッケージ](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/main/pyproject.toml)
- [Google: モデル一覧](https://ai.google.dev/gemini-api/docs/models)
- [Google: API変更履歴](https://ai.google.dev/gemini-api/docs/changelog)
- [Google: 3.6 Flash / 3.5 Flash-Liteの変更点](https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.6)
- [Google: UsageMetadata](https://ai.google.dev/api/generate-content#UsageMetadata)
- [Google: レート制限](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Google: Python SDK](https://github.com/googleapis/python-genai)

作成時のコード確認にはPython 3.12と講座指定のgoogle-genai 2.31.0を使用しています。追加テスト15件と講座の既存ツールのテスト7件、計22件が成功しました（6 subtestsも成功）。講座全体の確認コマンドは `uv run pytest -q` ですが、今回の実行環境では既存の `tests/test_agent.py` の待機が解消せず、全26件の検証は完了していません。原因は未特定で、講座の依存関係は変更していません。上の手順では検証が完了した対象を指定しています。

上記はコード作成時の検証記録です。提出準備時の再確認では、追加15テスト中13件が成功し、SDK未導入の環境のためSDK依存の2件はスキップしました。`--dry-run` もAPI接続なしで確認しています。実モデルの実測は今回の `answer.md` にまとめた18試行であり、テスト用の模擬応答とは区別しています。プロジェクト固有の利用枠は未確認です。講義PDFは配布物へ含めていません。
