# Day3 発展（a）：Pydantic AI と Google ADK の比較

同じ指示文と同じ関数ツールを Google ADK でも使い、Pydantic AI 版と書き方・ツール呼び出し・回答を比較する取り組みです。

実行前に用意したコードと手順を説明しています。**実施状態は、`lectures/03/results/` の結果ファイルと [answer.md](answer.md) の実測結果欄を参照してください。** 本番コマンドを実行し、保存された回答とログを確認してから、本人の観察欄と提出フォームを完成させます。

## 課題の参照元

この fork にある [problem.md](problem.md) は、発展（a）の比較方法を `adk web` とする旧版です。2026-11-02 に確認した[講座 upstream の最新課題](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/fae899a409e2c99feee9d44a3789f936f5fc64ee/lectures/03/problem.md)と配布された演習説明 PDF では `adk run` を使うため、今回はその指定に従います。比較の基になる `app/` のコードは同一です。配布 PDF の内容は、このリポジトリに転載していません。

確認したコミットは、講座 upstream が `fae899a409e2c99feee9d44a3789f936f5fc64ee`、今回の fork の開始点が `bb810b0f851ef7d45f339d9a5e27df15927ca03e` です。

## 今回作ったもの

- [adk_agent/glossary_agent/agent.py](../../adk_agent/glossary_agent/agent.py)：ADK が読み込む `root_agent`。
- [adk_agent/glossary_agent/__init__.py](../../adk_agent/glossary_agent/__init__.py)：エージェントの Python パッケージ。
- [scripts/run_day3_comparison.py](../../scripts/run_day3_comparison.py)：4 問を両版で実行し、結果とログを保存する比較用スクリプト。
- [scripts/prepare_day3_answer.py](../../scripts/prepare_day3_answer.py)：完了した実測結果から `answer.md` の結果欄を更新するスクリプト。

### 再利用する指示とツール

`app/` は変更せず、ADK 版から次を直接 import します。

| 対象 | 元の定義 | ADK での利用 |
|---|---|---|
| 指示文 | `app.agent.INSTRUCTIONS` | `instruction=INSTRUCTIONS` |
| 用語検索 | `app.tools.search_glossary` | `tools` のリストに関数を直接登録 |
| 各回の要約 | `app.tools.get_lecture_summary` | `tools` のリストに関数を直接登録 |
| モデル名 | `app.config.MODEL` | 同じ値を Gemini モデルに指定 |

関数本体、型ヒント、docstring を二重に作らず、同じ定義を両版から使います。今回の対象はこの **2 ツール**です。演習欄にある `make_quiz` の追加は行っていません。

### 書き方の比較

Pydantic AI 版の登録部分は、次の形です。以下のコードは比較のための抜粋です。

```python
agent = Agent(instructions=INSTRUCTIONS)
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)
```

ADK 版は、CLI が見つける名前を `root_agent` とし、指示とツールをコンストラクタに渡します。

```python
root_agent = Agent(
    model=Gemini(model=MODEL, client_kwargs=client_options),
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary],
)
```

Pydantic AI の `instructions` は複数形、ADK の `instruction` は単数形です。ツールの登録も、`tool_plain(...)` を呼ぶ方法と `tools=[...]` を渡す方法で異なります。どちらも、モデルの要求に応じて関数を呼び、その結果を含めて次の応答を作る処理をフレームワークが担います。

## 実行環境と比較条件

講座の Python 要件は **3.12 以上**です。`uv` が使える講座の Codespaces などで実行します。

| 項目 | 設定 |
|---|---|
| Google ADK | `google-adk==2.13.0` |
| Gemini SDK | `google-genai==2.31.0` |
| Pydantic AI | `pydantic-ai-slim[google,mcp]==2.57.0` |
| モデル | `app.config.MODEL`。環境変数 `AIE_MODEL` で両版を同時に変更可能 |
| API キー | 環境変数 `GEMINI_API_KEY` |
| HTTP リクエストの timeout | 60 秒 |
| SDK の HTTP 試行回数 | `HttpRetryOptions(attempts=1)`。初回のみ |
| 1 質問当たりの上限 | 各版でモデル呼び出しを最大 8 回に制限 |
| 評価する質問 | `lectures/03/comparison_cases.json` に固定した 4 問 |
| 実行単位 | 1 質問・1 版ごとに新しいプロセスとセッション |
| 実行順 | 質問ごとに Pydantic AI→ADK、ADK→Pydantic AI を交互にする |

上記の 3 ライブラリについて、指定版を保った依存解決と同一環境での import を確認しています。ADK は `uv run --with google-adk==2.13.0` で追加して使います。実行時の環境・設定も結果に記録し、後から条件を確認できるようにします。

**4 問 × 2 版で、計 8 回のエージェント実行です。** 1 回の実行中にも、ツールの呼び出しと結果の読み取りに伴って複数のモデル API リクエストが発生することがあります。8 回の実行を「API リクエスト 8 回」とは数えません。

### 比較する 4 問

設問の原文と観察の観点は [comparison_cases.json](comparison_cases.json) に保存しています。

| ID | 質問 | 確認する観点 |
|---|---|---|
| q1 | AIE2026の講座の宿題にある「3レベル」とは何ですか？ | 講座固有の言葉を用語集で確認するか |
| q2 | LoRAとQLoRAの違いは？ | 検索結果を使って両者を区別するか |
| q3 | 第3回では何を学びますか？ | `get_lecture_summary(lecture=3)` を使うか |
| q4 | DoRAとは何ですか？この講座での扱いも教えてください。 | 用語集にない内容と講座で確認できる内容を区別するか |

ツールの呼び出し回数だけで回答の良否を決めません。例えば、LoRA を 1 回検索した結果に QLoRA の定義も含まれる場合があります。回答の正確さは、回答原文と関数の戻り値を本人が照合します。

## 実行手順

すべて、`pyproject.toml` がある**リポジトリのルート**から実行します。

### 1. API を使わずに構成を確認する

```bash
python scripts/run_day3_comparison.py --check
```

実モデル API は呼びません。必要な依存ライブラリを `uv` で取得するため、初回はネットワーク接続が必要になることがあります。この確認に成功しても、実モデルの比較が完了したことにはなりません。

### 2. API キーを設定する

講座で設定済みの `GEMINI_API_KEY` を使用します。Codespaces の場合は、自分の fork を対象にした Codespaces secret に登録します。設定後に起動した環境から実行してください。キーの値をコード・ログ・提出物に書き込む必要はありません。

モデルを変更する場合は、実行前に `AIE_MODEL` を設定します。両版とも `app.config.MODEL` を読むため、同じモデル名で比較できます。

### 3. 実モデルで比較する

```bash
python scripts/run_day3_comparison.py
```

このコマンドはモデル API を利用します。4 問を両版で順次実行し、各実行の回答・ツール呼び出し・usage・経過時間と標準出力／標準エラーを保存します。途中で失敗した場合は、失敗を記録して停止します。失敗を含む実行を完了結果として扱いません。

成功した記録と失敗した記録は、実行ごとのフォルダで確認できます。再実行すると追加の API 利用が発生するので、先に失敗した実行のログを確認してください。

### 4. 結果を読み、回答欄を更新する

```bash
python scripts/prepare_day3_answer.py
```

最新の実行が **8 回すべて完了**している場合に限り、[answer.md](answer.md) の `DAY3_RESULTS_START` と `DAY3_RESULTS_END` の間を実測値で更新します。本人の観察欄は、保存された回答とログを読んで追記してください。

この処理は、更新した `answer.md` を含めて ZIP も作り直します。本人の観察を追記した後にもう一度実行すると、追記部分を保ったまま ZIP にも反映できます。

### 保存先

| 保存先 | 内容 |
|---|---|
| `lectures/03/results/<run-id>/result.json` | 実行状態・比較条件・各回答・集計用データ |
| `lectures/03/results/<run-id>/report.md` | 読みやすい比較レポート |
| `lectures/03/results/<run-id>/*.stdout.log` | 各プロセスの標準出力。ADK は JSONL のイベント記録 |
| `lectures/03/results/<run-id>/*.stderr.log` | 各プロセスの標準エラー |
| `lectures/03/results/<run-id>/source_snapshot/` | 実行開始時の対象ソース。対応する SHA256 は `result.json` に保存 |
| `lectures/03/day3_results_<run-id>.zip` | 対象を限定したソースと実行記録の持ち出し用 ZIP |

ZIP に `.env`、配布 PDF、仮想環境は含めません。ZIP の有無だけで完了を判断せず、`result.json` の状態と 8 回分の結果を確認します。

## ADK を直接対話で試す場合

```bash
PYTHONPATH=. ADK_MAX_LLM_CALLS=8 uv run --frozen --with google-adk==2.13.0 adk run adk_agent/glossary_agent
```

`PYTHONPATH=.` は、ADK からリポジトリ内の `app` を import するための指定です。起動後に質問を入力して回答を確認し、終了するときは `exit` を入力します。

この対話を別途実行すると、比較スクリプトの 8 回に加えて API 利用が発生します。同じ対話セッションで複数の質問を続けると、それまでの履歴も共有されます。独立した質問の比較には、前述の比較スクリプトを使います。

## 結果を読むときの注意

- **同じ指示と関数を渡した比較です。** フレームワーク内部が追加するプロンプト、ツール定義の変換、履歴の組み立て、SDK の呼び出し方には違いが残ります。
- **各条件は 1 回ずつです。** 回答のゆらぎ、サービスの混雑、実行順の影響があるため、今回の 4 問だけで一般的な優劣を決めません。
- **呼び出し回数の項目を区別します。** Pydantic AI の `requests` は取得した usage の値です。ADK の `requests` は未取得として扱い、`model_response_events` は別の観測値として数えます。後者を API リクエスト回数に置き換えません。
- **時間はプロセス起動込みです。** `uv`・Python・フレームワークの起動、ツール処理、通信を含む経過時間として読みます。
- **usage が欠けた場合は未取得として読みます。** 欠測を 0 として、消費量やコストがなかったことにしません。
- **原文を確認します。** ツール名と引数、ツールの結果、最終回答を見比べ、用語集に根拠があるか、関連する回を示したかを本人の言葉で記録します。

## 提出の進め方

1. 実モデル比較を完了し、`result.json`、`report.md`、各ログを確認する。
2. `prepare_day3_answer.py` を実行し、[answer.md](answer.md) の観察欄 3 か所を本人の言葉で埋める。演習欄には、実際に取り組んだ内容だけを書く。ZIP を使う場合は、追記後にもう一度 `prepare_day3_answer.py` を実行する。
3. 変更と実測記録を `lec03` ブランチにコミットし、**自分の fork の `main` ← `lec03`** の向きで PR を作る。
4. 提出フォームの Q1 は、実施・確認を終えてから「発展」を選ぶ。Q2 は公開リポジトリのルート URL、[https://github.com/takerunakao/lecture-ai-engineering-2026](https://github.com/takerunakao/lecture-ai-engineering-2026) を記載する。
5. Q3 は、実測結果と本人の工夫・難しかった点を踏まえて **400 文字以内**にまとめる。実行前に成功や観察結果を記載しない。

## 参照

- [講座 upstream の Day3 課題（確認したコミット）](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/fae899a409e2c99feee9d44a3789f936f5fc64ee/lectures/03/problem.md)
- [Google ADK：Python Quickstart](https://adk.dev/get-started/python/)
- [Google ADK：CLI リファレンス](https://adk.dev/api-reference/cli/)
- [Google ADK 2.13.0](https://pypi.org/project/google-adk/2.13.0/)
- [Google ADK：実行回数などの RunConfig](https://adk.dev/runtime/runconfig/)

API と CLI の設定は、2026-11-02 時点の公式資料および ADK 2.13.0 の配布コードに照らして確認しました。
