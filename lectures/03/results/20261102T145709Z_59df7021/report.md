# Day3 発展(a) 実行記録

- 実施状態：完了（8/8 件の質問実行が完了）
- 実行ID：`20261102T145709Z_59df7021`
- 開始日時（UTC）：2026-11-02T14:57:09.588534+00:00
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
| q1 | Pydantic AI | 完了 | 1 | 2 | 2 | 6.87 |
| q1 | Google ADK | 完了 | 1 | 未取得 | 2 | 6.74 |
| q2 | Google ADK | 完了 | 2 | 未取得 | 2 | 23.06 |
| q2 | Pydantic AI | 完了 | 2 | 2 | 2 | 23.54 |
| q3 | Pydantic AI | 完了 | 1 | 2 | 2 | 5.12 |
| q3 | Google ADK | 完了 | 1 | 未取得 | 2 | 5.90 |
| q4 | Google ADK | 完了 | 1 | 未取得 | 2 | 5.74 |
| q4 | Pydantic AI | 完了 | 1 | 2 | 2 | 5.37 |

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

#### Google ADK

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

### q2：LoRAとQLoRAの違いは？

**観察の観点：** 小さな行列を学習するLoRAと、ベース重みの量子化も利用するQLoRAを区別できたか。関連回は第2回。LoRAの検索だけでQLoRAの定義も返り得るので、検索回数だけで良否を決めない。

#### Google ADK

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

#### Pydantic AI

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

### q3：第3回では何を学びますか？

**観察の観点：** get_lecture_summary(lecture=3)の利用と、モデル・ループ・ツールという説明を確認する。

#### Pydantic AI

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

#### Google ADK

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

### q4：DoRAとは何ですか？この講座での扱いも教えてください。

**観察の観点：** 用語集にないことを明示できたか。根拠なしに講座での採用や講義回を断定しなかったか。一般知識を加える場合、用語集の根拠と区別したか。

#### Google ADK

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

#### Pydantic AI

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

## 読み取り上の注意

- ツール呼出数は観測値であり、正解率ではない。LoRAの1回の検索でQLoRAの定義も返る場合がある。
- 各4問・各1回の事例であり、確率的な生成のゆらぎを分離できない。フレームワーク全体の優劣は断定しない。
- 回答の正確さ・根拠の扱いは、回答原文とツールの戻り値を読み、本人が確認する。自動採点は行っていない。
- この記録は実際に取得した内容の整形であり、失敗・未実行を成功に置き換えていない。
