# Day3 発展(a) 実行記録

- 実施状態：失敗（1/8 件の質問実行が完了）
- 実行ID：`20261102T143017Z_a7d4cd79`
- 開始日時（UTC）：2026-11-02T14:30:17.034096+00:00
- モデル：`gemini-3.5-flash-lite`（両版共通）
- 実行開始時の Git コミット：`bb810b0f851ef7d45f339d9a5e27df15927ca03e`
- 各質問を別プロセス・新規会話で1回ずつ実行。先に動かすフレームワークは質問ごとに交互。
- 共通の指示と関数本体を直接インポート。各フレームワークによるプロンプトやツール定義の組み立てまで同一とは限らない。
- HTTPリクエストは60秒、SDKのHTTP試行は1回。1質問の実行は120秒、LLM呼び出しは最大8回。外側でも起動込み150秒で停止。
- 所要秒数はプロセス起動を含む。速度の優劣を判断する指標にはしていない。

## ライブラリ

| 項目 | 実行環境の値 |
|---|---|
| python | 3.12.16 |
| pydantic-ai-slim | 2.57.0 |
| google-genai | 2.31.0 |
| google-adk | 2.13.0 |
| httpx | 0.28.1 |

## 実行の集計

| 質問 | 実装 | 状態 | ツール呼出数 | requests | モデル応答イベント数 | 起動込み秒数 |
|---|---|---|---:|---:|---:|---:|
| q1 | Pydantic AI | 完了 | 1 | 2 | 2 | 31.64 |
| q1 | Google ADK | 失敗 | 0 | 未取得 | 0 | 150.08 |
| q2 | Google ADK | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |
| q2 | Pydantic AI | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |
| q3 | Pydantic AI | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |
| q3 | Google ADK | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |
| q4 | Google ADK | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |
| q4 | Pydantic AI | 未実行 | 未取得 | 未取得 | 未取得 | 未取得 |

`requests` はPydantic AIが報告した値。ADKでは同じ定義の値を取得していないため「未取得」とし、JSONLのモデル応答イベント数を別欄に記録した。両者を同一のAPI課金リクエスト数として比較しない。

## 質問ごとの回答とツール履歴

### q1：AIE2026の講座の宿題にある「3レベル」とは何ですか？

**観察の観点：** 用語集を確認し、基礎・実装・発展と、どれか1つで完了することを説明できたか。関連回は第1回。

#### Pydantic AI

状態：完了

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "AIE2026の講座の宿題にある「3レベル」とは何ですか？"]
```

取得した回答：

```text
AIE2026の宿題における「3レベル」とは、宿題の難易度や取り組み方の構成のことです。

具体的には以下の3つの段階に分かれており、ご自身の学習状況や目標に合わせて**どれか1つ**に取り組めば、その回の宿題は完了となります。

1. **基礎**：講義内容の確認
2. **実装**：自分でコードを書く
3. **発展**：調査や試行

なお、原則として宿題の採点は行われませんので、ご自身のペースに合わせて無理のないレベルから取り組んでみてくださいね。

関係する回：第1回
```

ツール呼び出し：

```json
[
  {
    "name": "search_glossary",
    "arguments": {
      "query": "3レベル"
    },
    "call_id": "call_496204"
  }
]
```

ツールの戻り値：

```json
[
  {
    "name": "search_glossary",
    "result": "[{\"term\": \"宿題の3レベル\", \"lecture\": 1, \"definition\": \"AIE2026の宿題の構成。「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階があり、どれか1つに取り組めばその回の宿題は完了。原則として採点はしない。\", \"related\": [\"answer-md\"]}]",
    "call_id": "call_496204"
  }
]
```

requests は Pydantic AI RunUsage.requests。model_response_events は取得した ModelResponse 数。input_tokens/output_tokens は RunUsage 報告値だが、全応答に正の値があり完了した場合のみ採用。SDKは欠測を0に変換するため、0は実測0と区別できず null とする。output_tokens は思考トークンを含み得るため、ADK candidatesTokenCount と同じ定義ではない。

#### Google ADK

状態：失敗

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "AIE2026の講座の宿題にある「3レベル」とは何ですか？"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

エラー（回答の品質とは区別する）：

```text
ADK complete final answer was not found.
プロセス終了コード=143, timeout=True, interrupted=False
```

ADK requests は未取得。model_response_events は partial でない role=model の出力イベント数であり、HTTP/APIリクエスト数ではない。input_tokens/output_tokens はその全イベントの usageMetadata が各項目について揃う場合だけ合計する。candidatesTokenCount は思考トークン等を含む総出力トークンの代用ではない。

### q2：LoRAとQLoRAの違いは？

**観察の観点：** 小さな行列を学習するLoRAと、ベース重みの量子化も利用するQLoRAを区別できたか。関連回は第2回。LoRAの検索だけでQLoRAの定義も返り得るので、検索回数だけで良否を決めない。

#### Google ADK

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "LoRAとQLoRAの違いは？"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

#### Pydantic AI

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "LoRAとQLoRAの違いは？"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

### q3：第3回では何を学びますか？

**観察の観点：** get_lecture_summary(lecture=3)の利用と、モデル・ループ・ツールという説明を確認する。

#### Pydantic AI

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "第3回では何を学びますか？"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

#### Google ADK

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "第3回では何を学びますか？"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

### q4：DoRAとは何ですか？この講座での扱いも教えてください。

**観察の観点：** 用語集にないことを明示できたか。根拠なしに講座での採用や講義回を断定しなかったか。一般知識を加える場合、用語集の根拠と区別したか。

#### Google ADK

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "adk", "run", "--jsonl", "--in_memory", "--timeout", "120s", "--log_level", "error", "adk_agent/glossary_agent", "DoRAとは何ですか？この講座での扱いも教えてください。"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

#### Pydantic AI

状態：未実行

実行コマンド（引数配列）：

```json
["uv", "run", "--frozen", "--with", "google-adk==2.13.0", "python", "scripts/day3_pydantic_worker.py", "DoRAとは何ですか？この講座での扱いも教えてください。"]
```

最終回答は取得できていません。

ツール呼び出し：

```json
[]
```

ツールの戻り値：

```json
[]
```

## 読み取り上の注意

- ツール呼出数は観測値であり、正解率ではない。LoRAの1回の検索でQLoRAの定義も返る場合がある。
- 各4問・各1回の事例であり、確率的な生成のゆらぎを分離できない。フレームワーク全体の優劣は断定しない。
- 回答の正確さ・根拠の扱いは、回答原文とツールの戻り値を読み、本人が確認する。自動採点は行っていない。
- この記録は実際に取得した内容の整形であり、失敗・未実行を成功に置き換えていない。
