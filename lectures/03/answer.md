# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：本提出はPydantic AI版とGoogle ADK版の比較を対象とする。素のLLMとの追加比較は、今回の実験の対象に含めていない。
- ツール呼び出しの記録：本比較ではPydantic AIのメッセージ履歴とADKの`--jsonl`を保存した。元の`--trace`コマンドの追加実行ログは含めていない。各質問のツール名・引数は下表と回答原文に記載する。
- 1つの質問でのLLM呼び出し回数：Pydantic AIの`requests`は4問とも2。ADKは同じ定義の`requests`を未取得とし、モデル応答イベント数を別に記録した（4問とも2）。
- 追加したツールとdocstring：新規の`make_quiz`は追加していない。既存の`search_glossary`と`get_lecture_summary`を、関数本体・型ヒント・docstringごとADK版でも再利用した。

## 宿題

- **取り組んだレベル：発展（a）— Google ADKへの移植とPydantic AI版との比較。**
- **実施結果：4問×2版、計8実行が完了。** 全件で終了コード0、`errors=[]`、最終回答を取得した。これは実行完了の確認であり、回答の正しさや指示への適合を自動で合格としたものではない。
- 比較対象の実行ID：`20261102T145709Z_59df7021`。
- 実行日時：2026年11月2日 23:57:09〜23:58:31（日本時間）。
- ログに基づく提出文の整理日：2026年11月3日（日本時間）。
- 証拠：[result.json](results/20261102T145709Z_59df7021/result.json)、[report.md](results/20261102T145709Z_59df7021/report.md)、同フォルダの質問別ログと`source_snapshot/`。

### 1. 実装と書き方の比較

配布された`app/`を変更せず、[ADK版のagent.py](../../adk_agent/glossary_agent/agent.py)から`app.agent.INSTRUCTIONS`、`app.tools.search_glossary`、`app.tools.get_lecture_summary`を直接インポートした。指示文・関数を複製せず、同じ定義を両版で利用することで、比較時の内容のずれを抑えた。

| 項目 | Pydantic AI版 | Google ADK版 |
|---|---|---|
| 指示の登録 | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS, ...)` |
| ツールの登録 | `agent.tool_plain(...)`で関数を登録 | `tools=[...]`に同じ関数を渡す |
| エージェントの入口 | 配布された`app.agent.agent` | CLIが読み込む`root_agent` |
| この比較での実行・記録 | 既存agentを呼ぶ補助スクリプトとメッセージ履歴 | 実際の`adk run`コマンドとJSONLイベント |

発展(a)の要件は[講座upstreamの課題（確認時の版）](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/fae899a409e2c99feee9d44a3789f936f5fc64ee/lectures/03/problem.md)と配布資料で確認した。このfork内の旧版`problem.md`には`adk web`とあるが、今回参照した要件に合わせて`adk run`で比較した。

### 2. 比較条件

| 項目 | 条件 |
|---|---|
| モデル | 両版とも`gemini-3.5-flash-lite` |
| ライブラリ | Pydantic AI 2.57.0／Google ADK 2.13.0／google-genai 2.31.0 |
| Python | ユーザー実行環境は3.12.16 |
| 質問 | [comparison_cases.json](comparison_cases.json)の同じ4問 |
| 会話履歴 | 1質問・1版ごとに新しいプロセスと会話 |
| 回数・順序 | 成功した今回の比較では各条件1回。先に動かす版を質問ごとに交替 |
| 制限 | HTTPリクエスト60秒、SDKのHTTP試行は初回のみ。1質問120秒、LLM呼び出し最大8回。起動込み150秒でも停止 |
| 記録 | 指示のハッシュ、ソースのハッシュとスナップショット、バージョン、回答全文、ツール呼出し・戻り値、usage、終了状態 |

同じ指示文・関数・モデルを使っても、内部でのプロンプトやツール定義の組み立てまで同一とは限らない。その差を完全に分離した実験ではない。

### 3. 実測結果の要約

ツール名・引数・呼び出し回数は、4問すべてで両版が一致した。

| 質問 | 両版に共通したツール呼び出し | 回数（各版） | 回答から確認したこと |
|---|---|---:|---|
| q1：宿題の3レベル | `search_glossary(query="3レベル")` | 1 | 基礎・実装・発展と、どれか1つに取り組めば完了することを説明。第1回を示した。用語集の内容と整合する。 |
| q2：LoRAとQLoRA | `search_glossary(query="LoRA")`、`search_glossary(query="QLoRA")` | 2 | 両版とも低ランク行列の学習と、ベース重みの量子化という違いを説明。第2回を示した。 |
| q3：第3回の内容 | `get_lecture_summary(lecture=3)` | 1 | 講義要約を根拠に「モデル＋ループ＋ツール」などを説明。用語集検索は行われなかった。 |
| q4：DoRAと講座での扱い | `search_glossary(query="DoRA")` | 1 | 両版とも未登録と明示した後、取得結果に含まれない一般知識や講座情報を補足した。 |

#### 参考：起動を含む経過時間

| 質問 | Pydantic AI（秒） | Google ADK（秒） |
|---|---:|---:|
| q1 | 6.871 | 6.737 |
| q2 | 23.544 | 23.062 |
| q3 | 5.122 | 5.903 |
| q4 | 5.368 | 5.743 |

各条件1回の値で、プロセス起動・ツール処理・通信を含む。これだけでフレームワークの速度の優劣は判断しない。

### 4. 実行ログに基づく観察・考察

#### 4-1. ツールの選択・引数・順序

q1・q2・q4では用語検索、q3では講義要約が選ばれた。q2のログ上の呼出要求はLoRA、QLoRAの順だが、両方の要求が最初のモデル応答に含まれている。したがって、「LoRAの検索結果を読んでからQLoRAの検索を決めた」とは言えない。関数処理の実時間上の直列・並列性も、この記録だけでは判断しない。

また、`search_glossary("LoRA")`の戻り値にはLoRAだけでなくランクとQLoRAの定義も含まれていた。今回は両版とも2回検索したが、検索回数が多いほど正しいとは評価しない。取得した情報と回答内容の対応を見る必要がある。

根拠：[q2 Pydantic AIログ](results/20261102T145709Z_59df7021/q2_pydantic_ai.stdout.log)、[q2 ADKログ](results/20261102T145709Z_59df7021/q2_adk.stdout.log)。

#### 4-2. 内容の妥当性と指示への対応は分けて評価する

q3の回答は、取得した講義要約に沿ってエージェントの基本構造や安全性を説明していた。一方、共通指示には「用語や講座に固有のことを答える前に、必ずsearch_glossaryで用語集を確認する」とある。実際のq3では、両版とも`get_lecture_summary(3)`だけを使い、`search_glossary`は呼ばなかった。

「回の内容には要約ツールを使う」という指示を満たしていても、用語集検索を必須とする指示を字義通りには満たしていない。指示間の優先順位や例外を明確にする余地がある。ただし、今回は同じ指示を保つ比較なので、この改善案を反映した再実験は行っていない。

根拠：[q3 Pydantic AIログ](results/20261102T145709Z_59df7021/q3_pydantic_ai.stdout.log)、[q3 ADKログ](results/20261102T145709Z_59df7021/q3_adk.stdout.log)、[実行時のINSTRUCTIONS](results/20261102T145709Z_59df7021/source_snapshot/app/agent.py)。

#### 4-3. 「用語集にない」から言える範囲を超えない

q4で両版が取得した情報は、「用語集にDoRAは見つからない」という結果だけだった。両版ともその事実を明示したが、その後に一般的なDoRAの説明を加えている。この一般説明は検索結果に含まれておらず、今回の用語集を根拠として正しさを確認したものではない。

- Pydantic AI版は、一般的な機械学習の文脈での説明であることを明示した。その一方で、「主要なトピックとしては扱われていない可能性」と補足し、末尾に「第1回〜第12回」と記した。未登録という結果だけでは、講座内での扱いやこの回数範囲は裏付けられない。
- ADK版は特定の講義回の指定を割愛したが、その理由として「用語集やシラバスに記載がない」と述べた。この質問でシラバスを確認した記録はなく、講座でのLoRAの扱いについても追加の検索はなかった。

用語集の未登録、講座で扱わないこと、シラバスに記載がないことは別の事実である。今回のADK版は特定回の列挙を避けたが、完全に根拠に沿った回答だったとは評価できない。同じ検索結果でも、補足の仕方に差が生じることを確認した。

改善案としては、未登録時に「講座での扱いはこの用語集から確認できない」と回答し、一般知識を追加する条件と出典の示し方を明確にすることが考えられる。これは今回の観察から得た提案であり、改善効果を実測した結果ではない。

根拠：[q4 Pydantic AIログ](results/20261102T145709Z_59df7021/q4_pydantic_ai.stdout.log)、[q4 ADKログ](results/20261102T145709Z_59df7021/q4_adk.stdout.log)。

### 5. 工夫した点・難しかった点

指示・ツール・モデル・質問をそろえ、会話履歴を毎回分離した。回答全文とツールの戻り値も保存し、「ツールを使ったか」だけでなく「取得した情報を超えていないか」を後から確認できるようにした。完了状態と回答の品質を別に扱ったことを、特に評価してほしい点とする。

先行実行`20261102T143017Z_a7d4cd79`ではPydantic AIのq1は完了したが、ADKが初回の`Enable telemetry? [Y/n]:`という確認で入力待ちになり、150秒でタイムアウトした。これはADKのモデル応答の失敗ではなく、モデル処理に入る前の確認待ちだった。

ログから原因を特定し、AI支援で比較スクリプトの子プロセスに`stdin=subprocess.DEVNULL`を指定した。初回の確認設定を変更せず、質問を引数で渡すバッチ実行が端末入力を待たないようにした。親が端末入力を持つケースと、ADKの最上位CLIを通るケースの回帰テストも追加・修正した。その後の再実行で、今回の8件が完了した。前回の失敗ログは原因分析用に残し、上の比較表には成功した今回の実行だけを使っている。

根拠：[先行実行のADK出力](results/20261102T143017Z_a7d4cd79/q1_adk.stdout.log)、[先行実行の終了状態](results/20261102T143017Z_a7d4cd79/result.json)、[修正した比較スクリプト](../../scripts/run_day3_comparison.py)。

### 6. 測定の限界とAI支援の範囲

- 今回の比較は4問・各条件1回であり、生成のゆらぎや実行順の影響を分離していない。一般的な品質・速度の優劣は断定しない。
- Pydantic AIの`requests`は4問とも2で、ADKの`requests`は未取得。ADKのモデル応答イベント数2を、同じ定義のAPI課金リクエスト数として扱わない。
- 出力トークンの定義にも差がある。Pydantic AIの値は思考トークンを含み得るため、ADKの`candidatesTokenCount`と単純に比較して料金や効率を評価しない。
- 実装、実行手順、不具合修正、ログ分析、提出文の整理にAI支援を使用した。受講者がCodespacesで実行して取得したログを根拠に記載している。追加の指示変更実験や、統計的な繰り返し評価を実施したとは扱わない。

Quri用の回答は[quri_answers.md](quri_answers.md)、PRの概要は[PR_BODY.md](PR_BODY.md)にまとめた。

## 実測結果の全文

以下は提出用スクリプトが生成した区間で、今回のZIPから回答・ツール履歴をそのまま保持している。

<!-- DAY3_RESULTS_START -->

### Day3 発展(a) 実行記録

- 実施状態：完了（8/8 件の質問実行が完了）
- 実行ID：`20261102T145709Z_59df7021`
- 開始日時（UTC）：2026-11-02T14:57:09.588534+00:00
- モデル：`gemini-3.5-flash-lite`（両版共通）
- 実行開始時の Git コミット：`bb810b0f851ef7d45f339d9a5e27df15927ca03e`
- 各質問を別プロセス・新規会話で1回ずつ実行。先に動かすフレームワークは質問ごとに交互。
- 共通の指示と関数本体を直接インポート。各フレームワークによるプロンプトやツール定義の組み立てまで同一とは限らない。
- HTTPリクエストは60秒、SDKのHTTP試行は1回。1質問の実行は120秒、LLM呼び出しは最大8回。外側でも起動込み150秒で停止。
- 所要秒数はプロセス起動を含む。速度の優劣を判断する指標にはしていない。

#### ライブラリ

| 項目 | 実行環境の値 |
|---|---|
| python | 3.12.16 |
| pydantic-ai-slim | 2.57.0 |
| google-genai | 2.31.0 |
| google-adk | 2.13.0 |
| httpx | 0.28.1 |

#### 実行の集計

| 質問 | 実装 | 状態 | ツール呼出数 | requests | モデル応答イベント数 | 起動込み秒数 |
|---|---|---|---:|---:|---:|---:|
| q1 | Pydantic AI | 完了 | 1 | 2 | 2 | 6.87 |
| q1 | Google ADK | 完了 | 1 | 未取得 | 2 | 6.74 |
| q2 | Google ADK | 完了 | 2 | 未取得 | 2 | 23.06 |
| q2 | Pydantic AI | 完了 | 2 | 2 | 2 | 23.54 |
| q3 | Pydantic AI | 完了 | 1 | 2 | 2 | 5.12 |
| q3 | Google ADK | 完了 | 1 | 未取得 | 2 | 5.90 |
| q4 | Google ADK | 完了 | 1 | 未取得 | 2 | 5.74 |
| q4 | Pydantic AI | 完了 | 1 | 2 | 2 | 5.37 |

`requests` はPydantic AIが報告した値。ADKでは同じ定義の値を取得していないため「未取得」とし、JSONLのモデル応答イベント数を別欄に記録した。両者を同一のAPI課金リクエスト数として比較しない。

#### 質問ごとの回答とツール履歴

##### q1：AIE2026の講座の宿題にある「3レベル」とは何ですか？

**観察の観点：** 用語集を確認し、基礎・実装・発展と、どれか1つで完了することを説明できたか。関連回は第1回。

###### Pydantic AI

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "AIE2026の講座の宿題にある「3レベル」とは何ですか？"]
```

取得した回答：

```text
AIE2026の宿題における「3レベル」とは、宿題の難易度や取り組み方の構成のことです。

具体的には以下の3つの段階に分かれています：
1. **基礎**：講義内容の確認
2. **実装**：自分でコードを書く
3. **発展**：調査や試行

これら3つのうち**どれか1つ**に取り組めば、その回の宿題は完了となります。なお、原則として宿題の採点はありません。

第1回（関係する回：第1回）
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "3レベル"
    },
    "call_id": "call_663080"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": "[{\"term\": \"宿題の3レベル\", \"lecture\": 1, \"definition\": \"AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組めばその回の宿題は完了。原則として採点はしない。\", \"related\": [\"answer-md\"]}]",
    "call_id": "call_663080"
  }
]
```

requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。

###### Google ADK

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "AIE2026の講座の宿題にある「3レベル」とは何ですか？"]
```

取得した回答：

```text
AIE2026の講座における「3レベル」とは、宿題の構成を示す以下の3段階のことです。

1. **基礎**：講義内容の確認
2. **実装**：自分でコードを書く
3. **発展**：調査や試行

この3つのレベルから**どれか1つ**に取り組めば、その回の宿題は完了となります（原則として採点は行われません）。

第1回
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "3レベル"
    },
    "call_id": "call_584050"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": {
      "result": "[{\"term\": \"宿題の3レベル\", \"lecture\": 1, \"definition\": \"AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組めばその回の宿題は完了。原則として採点はしない。\", \"related\": [\"answer-md\"]}]"
    },
    "call_id": "call_584050"
  }
]
```

ADK requests は未取得。model_response_events は partial でない role=model の出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens はその全イベントの usageMetadata が各項目について揃う場合だけ合計する。candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。

##### q2：LoRAとQLoRAの違いは？

**観察の観点：** 小さな行列を学習するLoRAと、ベース重みの量子化も利用するQLoRAを区別できたか。関連回は第2回。LoRAの検索だけでQLoRAの定義も返り得るので、検索回数だけで良否を決めない。

###### Google ADK

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "LoRAとQLoRAの違いは？"]
```

取得した回答：

```text
**LoRA**と**QLoRA**の主な違いは、ベースモデルの重みを量子化するかどうか（メモリをさらに節約するかどうか）にあります。

* **LoRA（Low-Rank Adaptation）**
  * 事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列（低ランク行列）の積で表し、その小さな行列だけを効率よく学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。
* **QLoRA（Quantized LoRA）**
  * ベースモデルの重みを4ビットなどの低いビット数に**量子化**してメモリを大幅に節約した状態で固定し、その上でLoRAと同様の低ランク行列を学習する手法です。これにより、より大きなモデルを小さなGPU環境でも扱えるようになります。

関係する回：第2回
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "LoRA"
    },
    "call_id": "call_734855"
  },
  {
    "name": "search_glossary",
    "arguments": {
      "query": "QLoRA"
    },
    "call_id": "call_734856"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": {
      "result": "[{\"term\": \"LoRA\", \"lecture\": 2, \"definition\": \"事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラメータが少なく、学習結果（アダプタ）も小さいファイルで保存できる。本講座の第2回演習ではLoRAを扱う。\", \"related\": [\"peft\", \"lora-rank\", \"qlora\"]}, {\"term\": \"ランク（LoRAのr）\", \"lecture\": 2, \"definition\": \"LoRAで使う低ランク行列の大きさを決めるハイパーパラメータ。大きいほど表現力が上がるが、学習するパラメータとメモリも増える。\", \"related\": [\"lora\"]}, {\"term\": \"QLoRA\", \"lecture\": 2, \"definition\": \"ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2回演習ではモデルがGPUに載るためLoRAで学習し、4ビットで読み込んだときのメモリと出力の違いを発展で比べる。\", \"related\": [\"lora\", \"quantization\"]}]"
    },
    "call_id": "call_734855"
  },
  {
    "name": "search_glossary",
    "result": {
      "result": "[{\"term\": \"QLoRA\", \"lecture\": 2, \"definition\": \"ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2回演習ではモデルがGPUに載るためLoRAで学習し、4ビットで読み込んだときのメモリと出力の違いを発展で比べる。\", \"related\": [\"lora\", \"quantization\"]}, {\"term\": \"LoRA\", \"lecture\": 2, \"definition\": \"事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラメータが少なく、学習結果（アダプタ）も小さいファイルで保存できる。本講座の第2回演習ではLoRAを扱う。\", \"related\": [\"peft\", \"lora-rank\", \"qlora\"]}]"
    },
    "call_id": "call_734856"
  }
]
```

ADK requests は未取得。model_response_events は partial でない role=model の出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens はその全イベントの usageMetadata が各項目について揃う場合だけ合計する。candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。

###### Pydantic AI

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "LoRAとQLoRAの違いは？"]
```

取得した回答：

```text
講座の用語集によると、LoRAとQLoRAの違いは主に次の点にあります。

- **LoRA**
  事前学習済みの重みを固定したまま、重みの更新分を2つの小さな低ランク行列で近似し、その部分だけを学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。学習パラメータや保存ファイルを大幅に削減できます。

- **QLoRA**
  ベースモデルの重みを4ビットなどに**量子化**してメモリをさらに節約した上で、LoRAによる学習を行う手法です。これにより、より大きなモデルを比較的小さなGPUメモリでも扱えるようになります。

関係する回：第2回
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "LoRA"
    },
    "call_id": "call_789897"
  },
  {
    "name": "search_glossary",
    "arguments": {
      "query": "QLoRA"
    },
    "call_id": "call_789898"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": "[{\"term\": \"LoRA\", \"lecture\": 2, \"definition\": \"事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラメータが少なく、学習結果（アダプタ）も小さいファイルで保存できる。本講座の第2回演習ではLoRAを扱う。\", \"related\": [\"peft\", \"lora-rank\", \"qlora\"]}, {\"term\": \"ランク（LoRAのr）\", \"lecture\": 2, \"definition\": \"LoRAで使う低ランク行列の大きさを決めるハイパーパラメータ。大きいほど表現力が上がるが、学習するパラメータとメモリも増える。\", \"related\": [\"lora\"]}, {\"term\": \"QLoRA\", \"lecture\": 2, \"definition\": \"ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2回演習ではモデルがGPUに載るためLoRAで学習し、4ビットで読み込んだときのメモリと出力の違いを発展で比べる。\", \"related\": [\"lora\", \"quantization\"]}]",
    "call_id": "call_789897"
  },
  {
    "name": "search_glossary",
    "result": "[{\"term\": \"QLoRA\", \"lecture\": 2, \"definition\": \"ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2回演習ではモデルがGPUに載るためLoRAで学習し、4ビットで読み込んだときのメモリと出力の違いを発展で比べる。\", \"related\": [\"lora\", \"quantization\"]}, {\"term\": \"LoRA\", \"lecture\": 2, \"definition\": \"事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラメータが少なく、学習結果（アダプタ）も小さいファイルで保存できる。本講座の第2回演習ではLoRAを扱う。\", \"related\": [\"peft\", \"lora-rank\", \"qlora\"]}]",
    "call_id": "call_789898"
  }
]
```

requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。

##### q3：第3回では何を学びますか？

**観察の観点：** get_lecture_summary(lecture=3)の利用と、モデル・ループ・ツールという説明を確認する。

###### Pydantic AI

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "第3回では何を学びますか？"]
```

取得した回答：

```text
第3回では「AIエージェント」をテーマに学びます。

**主な内容：**
- **AIエージェントの基本構造**：「モデル ＋ ループ ＋ ツール」の組み合わせで自律的に動作する仕組みを理解する。
- **ツールとエージェントループ**：LLMがツールを選択・実行し、その結果をもとに次の行動を決定する仕組みや、コスト・注意点を学ぶ。
- **ハーネスとフレームワーク**：Pydantic AIやADKなどのフレームワークを活用し、実際にツールを使う学習支援エージェントの作成・動作確認を行う。
- **安全性**：ガードレールやHuman-in-the-loop（人の確認）の重要性を学ぶ。

第3回
```

ツール呼び出し：

```json
[
  {
    "name": "get_lecture_summary",
    "arguments": {
      "lecture": 3
    },
    "call_id": "call_1120532"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "get_lecture_summary",
    "result": "# 第3回 AIエージェント\n\n## この回のねらい\n\n- AIエージェントの基本構造が「モデル＋ループ＋ツール」であることを理解する\n- Pydantic AIで、ツールを使う学習支援エージェントを自分で作り、動かす\n\n## 要点\n\n1. **エージェントとは**：LLMがツールを呼び出し、結果を見て次の行動を決めるループで目的を達成するシステム。\n2. **ツール**：モデルはツールの名前・説明文・引数の型を見て呼び出しを依頼し、実行はプログラム側が行う。説明文の書き方で挙動が変わる。\n3. **エージェントループのコスト**：1つの質問でLLMを複数回呼ぶため、応答時間・料金・レート制限への影響が大きい。\n4. **ハーネス**：Claude CodeやPiのような、ループ・ツール・UIでLLMを包むプログラム。Piは組み込みツールを4つ（read・write・edit・bash）に絞った薄いハーネス。\n5. **フレームワーク**：Pydantic AI（本線）は型でツールや出力を定義でき、テスト用モデル（TestModel）でAPIを呼ばずに動作確認できる。ADKはGoogleのフレームワークで、adk web で動きを画面で追える。\n6. **ガードレールとHuman-in-the-loop**：書き込みなど取り消しにくい操作は、権限を絞ったり、人の確認を挟んだりする。\n\n## 演習で体験すること\n\n- 第1回と同じ質問を、用語集を検索できるエージェントに投げ、回答が改善することを確かめる\n- どのツールがどの引数で呼ばれたかを読む\n- ツールを1つ追加する\n\n## 関連用語\n\nAIエージェント / エージェントループ / ツール / ツールの説明文 / 構造化出力 / ハーネス / Pi / Pydantic AI / ADK / MCP / ガードレール / Human-in-the-loop / TestModel\n",
    "call_id": "call_1120532"
  }
]
```

requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。

###### Google ADK

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "第3回では何を学びますか？"]
```

取得した回答：

```text
第3回では**「AIエージェント」**について学びます。

主な内容は以下の通りです。

- **AIエージェントの基本構造**：「モデル＋ループ＋ツール」の仕組みについて理解します。
- **ツールとエージェントループ**：LLMがツールを呼び出し、その結果を元に次の行動を決める仕組みや、ループに伴うコスト（応答時間・料金など）を学びます。
- **ハーネスとフレームワーク**：Pydantic AI（型による定義やテストが容易なフレームワーク）やPi、ADKなどを扱います。
- **ガードレールとHuman-in-the-loop**：取り消しにくい操作に対する人の確認の挟み方などを学びます。
- **演習**：用語集を検索できるAIエージェントを作り、実際に動かしてツールの呼び出しなどを体験します。

（第3回）
```

ツール呼び出し：

```json
[
  {
    "name": "get_lecture_summary",
    "arguments": {
      "lecture": 3
    },
    "call_id": "call_1112284"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "get_lecture_summary",
    "result": {
      "result": "# 第3回 AIエージェント\n\n## この回のねらい\n\n- AIエージェントの基本構造が「モデル＋ループ＋ツール」であることを理解する\n- Pydantic AIで、ツールを使う学習支援エージェントを自分で作り、動かす\n\n## 要点\n\n1. **エージェントとは**：LLMがツールを呼び出し、結果を見て次の行動を決めるループで目的を達成するシステム。\n2. **ツール**：モデルはツールの名前・説明文・引数の型を見て呼び出しを依頼し、実行はプログラム側が行う。説明文の書き方で挙動が変わる。\n3. **エージェントループのコスト**：1つの質問でLLMを複数回呼ぶため、応答時間・料金・レート制限への影響が大きい。\n4. **ハーネス**：Claude CodeやPiのような、ループ・ツール・UIでLLMを包むプログラム。Piは組み込みツールを4つ（read・write・edit・bash）に絞った薄いハーネス。\n5. **フレームワーク**：Pydantic AI（本線）は型でツールや出力を定義でき、テスト用モデル（TestModel）でAPIを呼ばずに動作確認できる。ADKはGoogleのフレームワークで、adk web で動きを画面で追える。\n6. **ガードレールとHuman-in-the-loop**：書き込みなど取り消しにくい操作は、権限を絞ったり、人の確認を挟んだりする。\n\n## 演習で体験すること\n\n- 第1回と同じ質問を、用語集を検索できるエージェントに投げ、回答が改善することを確かめる\n- どのツールがどの引数で呼ばれたかを読む\n- ツールを1つ追加する\n\n## 関連用語\n\nAIエージェント / エージェントループ / ツール / ツールの説明文 / 構造化出力 / ハーネス / Pi / Pydantic AI / ADK / MCP / ガードレール / Human-in-the-loop / TestModel\n"
    },
    "call_id": "call_1112284"
  }
]
```

ADK requests は未取得。model_response_events は partial でない role=model の出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens はその全イベントの usageMetadata が各項目について揃う場合だけ合計する。candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。

##### q4：DoRAとは何ですか？この講座での扱いも教えてください。

**観察の観点：** 用語集にないことを明示できたか。根拠なしに講座での採用や講義回を断定しなかったか。一般知識を加える場合、用語集の根拠と区別したか。

###### Google ADK

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "DoRAとは何ですか？この講座での扱いも教えてください。"]
```

取得した回答：

```text
用語集には載っていませんでした。DoRA（Weight-Decomposed Low-Rank Adaptation）は、モデルの重みを方向（Direction）と大きさ（Magnitude）に分解してファインチューニングを行うPEFT手法の一つですが、本講座（AIE2026）の用語集には含まれていません。

なお、本講座の一般的なファインチューニング手法については、LoRAなどを扱う回で学ぶことができます（※関係する回の具体的な指定は、用語集やシラバスに記載がないため割愛します）。
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "DoRA"
    },
    "call_id": "call_596835"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": {
      "result": "用語集に「DoRA」は見つかりませんでした。"
    },
    "call_id": "call_596835"
  }
]
```

ADK requests は未取得。model_response_events は partial でない role=model の出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens はその全イベントの usageMetadata が各項目について揃う場合だけ合計する。candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。

###### Pydantic AI

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "DoRAとは何ですか？この講座での扱いも教えてください。"]
```

取得した回答：

```text
「DoRA」について講座の用語集を確認しましたが、用語集には登録されていませんでした。

推測での断定は避けますが、一般的なAI・機械学習の文脈におけるDoRA（Weight-Decomposed Low-Rank Adaptation）は、LoRAを拡張し、重み行列を「大きさ（magnitude）」と「方向（direction）」に分解してファインチューニングを行う手法として知られています。

ただし、本講座（AIE2026）の用語集には含まれていないため、講義の主要なトピックとしては扱われていない可能性があります。

関連する回：第1回〜第12回（※用語集に登録がないため特定の回は指定できません）
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "DoRA"
    },
    "call_id": "call_1201309"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": "用語集に「DoRA」は見つかりませんでした。",
    "call_id": "call_1201309"
  }
]
```

requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。

#### 読み取り上の注意

- ツール呼出数は観測値であり、正解率ではない。LoRAの1回の検索でQLoRAの定義も返る場合がある。
- 各4問・各1回の事例であり、確率的な生成のゆらぎを分離できない。フレームワーク全体の優劣は断定しない。
- 回答の正確さ・根拠の扱いは、回答原文とツールの戻り値を読み、本人が確認する。自動採点は行っていない。
- この記録は実際に取得した内容の整形であり、失敗・未実行を成功に置き換えていない。

<!-- DAY3_RESULTS_END -->
