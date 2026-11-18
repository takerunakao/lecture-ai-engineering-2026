# Day5 比較実行レポート

<!-- DAY5_FINAL_REVIEW_NOTICE -->

> **引用集計の補足**：以下の自動抽出IDの表は、併記された後続ページを数え落とす参考値です。本文照合では合計39件（基本19・Graph20）で、すべて取得本文内に存在しました。意味的な裏付けの判定は別に行っています。[確認済みの引用一覧・判定根拠・集計の補足](review_addendum.md)を参照してください。

**実行状態：実行完了（16/16件）。人手確認：完了。**

記録された状態：`completed`。全試行記録16件。実行完了は、回答の正しさや発展課題の合格を意味しない。

## 比較条件

- 実行ID：`20261117T234818Z_3c60667f`／開始：2026-11-18T08:48:18+09:00
- 対象：第1〜3回本講義の214ページ。両方式で同じ資料・索引・埋め込みモデルを使用。
- 質問：4問、各方式2回。1回答につき検索1回、生成API1回の比較。元のエージェントによるツール呼び出しループの比較ではない。
- 生成モデル：`gemini-3.5-flash-lite`／temperature=0／出力上限=4096。共通の回答指示を使用。
- 返却本文：両方式5ページ。件数を揃え、ページの本文長や入力トークン数の違いは実測して記録。
- 各試行で同じ原文の質問を独立に埋め込み、ベクトルのハッシュも記録。総時間は埋め込み・取得・生成を含み、環境準備と試行間の待機を除く。
- 実行順は質問ごとに方式を交互にし、次の反復では順を逆転。温度0でも回答や処理時間の一致は保証しない。
- 根拠ページ・期待事実・採点基準は事前登録した評価専用情報で、検索器や生成プロンプトに渡していない。
- 教材の参照コミット：`1ce722c2816b70ef62891a6378b2478af555e3fd`。コード・資料のハッシュと実際の順番は`config.json`に記録。

応答で返されたmodel_version：`gemini-3.5-flash-lite`（取得16/16件）。

## 成功試行の集計

| 方式 | 完了/計画 | 平均総時間 秒（有効件数） | 入力tokens合計 | 出力tokens合計 | 思考tokens合計 | 生成API推定USD合計 |
|---|---:|---:|---:|---:|---:|---:|
| 基本RAG | 8/8 | 4.585（8/8件） | 17268（8/8件） | 1016（8/8件） | 未取得（0/8件） | $0.007720（8/8件） |
| 改良Graph | 8/8 | 4.582（8/8件） | 17268（8/8件） | 1256（8/8件） | 未取得（0/8件） | $0.008320（8/8件） |

集計は各予定タスクの最新の成功試行のみ。括弧内は取得できた値の件数/成功件数で、欠測値は0に置き換えない。未完了なら方式間の集計対象も揃っていない。
生成API推定費用は有料Standardの公表単価による概算で、請求額ではない。クエリ埋め込み・索引構築、失敗・再試行による追加消費、無料枠を含む総費用を表さない。出力と思考トークンは分けて記録し、料金では思考分も考慮する。

## 予定タスク別の測定

| 実行ID | 状態 | 総時間 秒 | 埋込/検索/生成 秒 | 参照グループ取得 | 自動抽出IDの文脈内一致（参考） | 生成API推定USD |
|---|---|---:|---|---:|---:|---:|
| r1_q1_baseline | 完了・試行1 | 3.947 | 1.410/0.015/2.486 | 1/1 | 1/1 | $0.000878 |
| r1_q1_graph | 完了・試行1 | 3.906 | 1.386/0.035/2.477 | 1/1 | 1/1 | $0.000916 |
| r1_q2_graph | 完了・試行1 | 5.235 | 2.406/0.025/2.796 | 3/3 | 3/3 | $0.001088 |
| r1_q2_baseline | 完了・試行1 | 4.114 | 1.351/0.015/2.741 | 3/3 | 2/2 | $0.000976 |
| r1_q3_baseline | 完了・試行1 | 5.251 | 1.408/0.015/3.821 | 2/2 | 2/2 | $0.001227 |
| r1_q3_graph | 完了・試行1 | 5.446 | 2.371/0.024/3.043 | 2/2 | 3/3 | $0.001332 |
| r1_q4_graph | 完了・試行1 | 4.869 | 1.411/0.031/3.419 | 対象外 | 1/1 | $0.000821 |
| r1_q4_baseline | 完了・試行1 | 4.474 | 1.364/0.015/3.086 | 対象外 | 1/1 | $0.000816 |
| r2_q1_graph | 完了・試行1 | 3.541 | 1.350/0.022/2.160 | 1/1 | 1/1 | $0.000948 |
| r2_q1_baseline | 完了・試行1 | 5.698 | 1.381/0.015/4.291 | 1/1 | 1/1 | $0.000916 |
| r2_q2_baseline | 完了・試行1 | 4.498 | 1.365/0.015/3.110 | 3/3 | 2/2 | $0.001023 |
| r2_q2_graph | 完了・試行1 | 4.889 | 1.384/0.025/3.471 | 3/3 | 2/2 | $0.001068 |
| r2_q3_graph | 完了・試行1 | 4.294 | 1.377/0.024/2.879 | 2/2 | 3/3 | $0.001330 |
| r2_q3_baseline | 完了・試行1 | 5.239 | 1.363/0.015/3.853 | 2/2 | 2/2 | $0.001122 |
| r2_q4_baseline | 完了・試行1 | 3.456 | 1.352/0.015/2.080 | 対象外 | 3/3 | $0.000761 |
| r2_q4_graph | 完了・試行1 | 4.476 | 2.403/0.030/2.034 | 対象外 | 1/1 | $0.000816 |

参照グループ取得率は事前に選んだ非網羅的な根拠集合の代理指標。引用ID一致は、重複を除いた引用ページが取得本文に含まれるかの確認に限る。回答の正しさ・引用本文の裏付けは自動判定していない。資料に答えのない質問の参照取得率は対象外。

## 質問と事前の確認基準

### q1：single_page

第2回の説明では、LoRAは何を固定し、何を学習しますか。QLoRAはLoRAに何を加えますか。講義資料の根拠ページを示して説明してください。

- LoRAとQLoRAの学習対象：lec02-main-p051 または lec02-main-p052。LoRAは元の重みを固定し、低ランクの小さな追加行列を学習する。QLoRAは元の重みの4bit量子化を組み合わせ、必要メモリを抑える。

回答基準：

- 元のモデルの重みを固定することと、小さな追加行列・低ランクの差分を学習することを区別する。
- QLoRAが元の重みを4bitに量子化することを説明する。
- 元の重みをすべて学習する、または単に入力文を保存する方法だとは説明しない。
- 回答の根拠となる講義回とページを引用する。

### q2：multi_page

第3回の講義資料では、コンパクションとセッションをまたぐメモリはどう違いますか。また、紹介されたOpenClawの例では、日々のメモはすべて長期メモリに移されますか。それぞれの根拠ページを示してください。

- コンパクションの対象：lec03-main-p039。コンパクションは同じセッション内の古い履歴を要約に置き換え、コンテキストを詰める。
- セッションをまたぐ外部メモリ：lec03-main-p013 または lec03-main-p039。メモリは情報をファイルやデータベースなどの外部保存先に書き出し、新しい会話のコンテキストへ読み戻す。
- 日々のメモからの選別：lec03-main-p040。紹介されたOpenClawの例は日々のメモを見直し、基準を超えたものだけを長期メモリに残す。全てを移すわけではない。

回答基準：

- 同じセッションの履歴の要約と、セッションをまたぐ外部保存・読み戻しを区別する。
- 紹介されたOpenClawの例では全てを長期メモリに移さず、選別して残すことを説明する。
- 一度きりの調べもの等が日々のメモにとどまるという例、または基準を満たすものだけ移すという手順で選別の意味を説明する。
- 資料に記載された実装例の説明として述べ、全ての製品・実装が同じ動作をするとは一般化しない。
- コンパクションと長期メモリへの選別について、それぞれを支えるページを引用する。

### q3：cross_lecture

第2回のLoRAと、第3回のセッションをまたぐメモリは、どちらも過去の情報を活かすように見えます。この二つは、何を変更・保存する点で異なりますか。モデルで固定するものと学習するもの、外に保存して次の会話へ戻すものを分け、両方の講義から根拠を示して説明してください。

- LoRAの固定パラメータと学習パラメータ：lec02-main-p051 または lec02-main-p052。LoRAは元の重みを固定し、重みの変化を表す低ランクの追加行列を学習する。
- 外部保存から次のコンテキストへの読み戻し：lec03-main-p013 または lec03-main-p039。セッションをまたぐメモリは情報を外部保存し、必要な内容を次の会話のコンテキストへ戻す仕組みである。

回答基準：

- LoRAで元の重みは固定し、追加の低ランク行列を学習することを説明する。
- 外部メモリで保存するのはメモ等の情報であり、それを後から会話の入力・コンテキストへ戻すことを説明する。
- 追加パラメータを学習することと、情報を保存・再提示することの違いを明示する。
- メモリを読み戻しただけでモデルの重みが学習・更新されたとは述べない。
- 第2回と第3回の両方から、比較に使った事実を支えるページを引用する。

### q4：unanswerable

今回この環境で実行した講義資料RAGの実測平均応答時間と正答率は、それぞれいくつですか。講義資料だけを根拠に教えてください。

- 根拠グループなし。資料に測定記録がないことを踏まえた回答保留を確認する。

回答基準：

- 講義資料だけでは、今回の環境における実測平均応答時間と正答率を確認できないと明示する。
- 今回の測定値として秒数・割合を作り出さない。講義内の例や他の環境の数値を今回の実測値に置き換えない。
- 必要に応じて、今回の実行ログ、評価対象、正答判定などを確認する必要があると説明する。

## 各試行の記録

### 1. r1_q1_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:48:18+00:00
- 総時間：3.947秒。埋め込み：1.410秒／取得：0.015秒／生成：2.486秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2403、出力=63、思考=未取得、キャッシュ入力=未取得、合計=2466
- 生成API推定費用：$0.000878。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | vector_top_k / vector_rank=1 / lec02-main-p052 |
| 2 | lec02-main-p051 | PEFT ：モデル全体ではなく、一部だけを学習する | vector_top_k / vector_rank=2 / lec02-main-p051 |
| 3 | lec02-main-p060 | 今日の演習： QLoRA で出力形式を矯正し、効果を測る | vector_top_k / vector_rank=3 / lec02-main-p060 |
| 4 | lec02-main-p061 | 演習の進め方と提出物（仮） | vector_top_k / vector_rank=4 / lec02-main-p061 |
| 5 | lec02-main-p047 | 根拠と諸説：知識の追加は RAG が効きやすい | vector_top_k / vector_rank=5 / lec02-main-p047 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> LoRAは元の重みを固定し、小さな差分（小さな行列A・B）だけを学習します（第2回・PDF p.52）。また、QLoRAはLoRAに加えて元の重みを4bitに圧縮します（第2回・PDF p.52）。

### 2. r1_q1_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:48:32+00:00
- 総時間：3.906秒。埋め込み：1.386秒／取得：0.035秒／生成：2.477秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2403、出力=78、思考=未取得、キャッシュ入力=未取得、合計=2481
- 生成API推定費用：$0.000916。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | query_aware_graph / vector_rank=1 / lec02-main-p052; lec02-main-p051 → lec02-main-p052; lec02-main-p051 → term:lora → lec02-main-p052; lec02-main-p051 → term:qlora → lec02-main-p052; lec02-main-p060 → term:qlora → lec02-main-p052 |
| 2 | lec02-main-p051 | PEFT ：モデル全体ではなく、一部だけを学習する | query_aware_graph / vector_rank=2 / lec02-main-p051; lec02-main-p052 → lec02-main-p051; lec02-main-p052 → term:lora → lec02-main-p051; lec02-main-p052 → term:qlora → lec02-main-p051; lec02-main-p060 → term:qlora → lec02-main-p051 |
| 3 | lec02-main-p060 | 今日の演習： QLoRA で出力形式を矯正し、効果を測る | query_aware_graph / vector_rank=3 / lec02-main-p060; lec02-main-p052 → term:qlora → lec02-main-p060; lec02-main-p051 → term:qlora → lec02-main-p060 |
| 4 | lec02-main-p061 | 演習の進め方と提出物（仮） | query_aware_graph / vector_rank=4 / lec02-main-p061; lec02-main-p052 → term:qlora → lec02-main-p061; lec02-main-p051 → term:qlora → lec02-main-p061; lec02-main-p060 → lec02-main-p061; lec02-main-p060 → term:qlora → lec02-main-p061 |
| 5 | lec02-main-p047 | 根拠と諸説：知識の追加は RAG が効きやすい | query_aware_graph / vector_rank=5 / lec02-main-p047; lec02-main-p052 → term:lora → lec02-main-p047; lec02-main-p051 → term:lora → lec02-main-p047 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec02-main-p052", "lec02-main-p051", "lec02-main-p060"], "query_terms": [{"degree": 6, "term_id": "term:lora", "title": "LoRA", "weight": 3.4247278790723494}, {"degree": 7, "term_id": "term:qlora", "title": "QLoRA", "weight": 3.2911964864478267}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 11, "candidate_count_after_cap": 11, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第2回の説明において、LoRAは元の重みを固定し、小さな行列（差分や追加部分）を学習します（第2回・PDF p.51, p.52）。また、QLoRAはLoRAに加えて、元の重みを4bitに圧縮します（第2回・PDF p.51, p.52）。

### 3. r1_q2_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:48:46+00:00
- 総時間：5.235秒。埋め込み：2.406秒／取得：0.025秒／生成：2.796秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=1911、出力=206、思考=未取得、キャッシュ入力=未取得、合計=2117
- 生成API推定費用：$0.001088。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p040 | 実装例：OpenClaw | query_aware_graph / vector_rank=1 / lec03-main-p040; lec03-main-p039 → lec03-main-p040; lec03-main-p039 → term:memory → lec03-main-p040; lec03-main-p065 → term:memory → lec03-main-p040 |
| 2 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | query_aware_graph / vector_rank=3 / lec03-main-p065; lec03-main-p040 → term:memory → lec03-main-p065; lec03-main-p039 → term:memory → lec03-main-p065 |
| 3 | lec03-main-p039 | 実装例：Claude | query_aware_graph / vector_rank=2 / lec03-main-p039; lec03-main-p040 → lec03-main-p039; lec03-main-p040 → term:memory → lec03-main-p039; lec03-main-p065 → term:memory → lec03-main-p039 |
| 4 | lec03-main-p038 | メモリがないと、毎回ゼロからやり直しになる | query_aware_graph / vector_rank=4 / lec03-main-p038; lec03-main-p040 → lec03-main-p039 → lec03-main-p038; lec03-main-p040 → term:memory → lec03-main-p038; lec03-main-p039 → lec03-main-p038; lec03-main-p039 → term:memory → lec03-main-p038; lec03-main-p065 → term:memory → lec03-main-p038 |
| 5 | lec03-main-p041 | Skill：繰り返す作業の手順をファイルに保存しておく | query_aware_graph / vector_rank=5 / lec03-main-p041; lec03-main-p040 → lec03-main-p041; lec03-main-p040 → term:memory → lec03-main-p041; lec03-main-p039 → lec03-main-p040 → lec03-main-p041; lec03-main-p039 → term:memory → lec03-main-p041; lec03-main-p065 → term:memory → lec03-main-p041 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec03-main-p040", "lec03-main-p039", "lec03-main-p065"], "query_terms": [{"degree": 17, "term_id": "term:memory", "title": "メモリ", "weight": 2.480266270231498}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 15, "candidate_count_after_cap": 15, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第3回の講義資料によると、コンパクションとセッションをまたぐメモリの違いは以下の通りです。
> 
> - **コンパクション**：同じセッションのコンテキストの中で、古い履歴を要約して詰めるものです（第3回・PDF p.39、p.65）。「ループの中の履歴」の圧縮に当たります（第3回・PDF p.65）。
> - **セッションをまたぐメモリ**：外の保存先を利用し、セッションをまたいで効く記録（メモリツールなど）です（第3回・PDF p.39、p.65）。
> 
> また、紹介されたOpenClawの例では、日々のメモはすべて長期メモリに移されるわけではありません。毎晩自動で見直しを行い、基準を超えたものだけが残され、一度きりの調べものは日々のメモに残るだけで長期メモリは膨らまない仕組みになっています（第3回・PDF p.40）。

### 4. r1_q2_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:49:01+00:00
- 総時間：4.114秒。埋め込み：1.351秒／取得：0.015秒／生成：2.741秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=1911、出力=161、思考=未取得、キャッシュ入力=未取得、合計=2072
- 生成API推定費用：$0.000976。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p040 | 実装例：OpenClaw | vector_top_k / vector_rank=1 / lec03-main-p040 |
| 2 | lec03-main-p039 | 実装例：Claude | vector_top_k / vector_rank=2 / lec03-main-p039 |
| 3 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | vector_top_k / vector_rank=3 / lec03-main-p065 |
| 4 | lec03-main-p038 | メモリがないと、毎回ゼロからやり直しになる | vector_top_k / vector_rank=4 / lec03-main-p038 |
| 5 | lec03-main-p041 | Skill：繰り返す作業の手順をファイルに保存しておく | vector_top_k / vector_rank=5 / lec03-main-p041 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> コンパクションは同じセッションの中（コンテキストの中）で古い履歴を要約に置き換えて詰めるものであるのに対し、セッションをまたぐメモリ（外の保存先）は、メモリツールなどを用いてセッションをまたいで情報を残す仕組みです（第3回・PDF p.39）。
> 
> また、OpenClawの例では、日々のメモ（10/24や10/25などのメモ）のすべてが長期メモリに移されるわけではなく、毎晩自動で見直しを行い、基準を超えたものだけが残されます（第3回・PDF p.40）。一度きりの調べものは日々のメモに残るだけであり、全部は残されません（第3回・PDF p.40）。

### 5. r1_q3_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:49:15+00:00
- 総時間：5.251秒。埋め込み：1.408秒／取得：0.015秒／生成：3.821秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2074、出力=242、思考=未取得、キャッシュ入力=未取得、合計=2316
- 生成API推定費用：$0.001227。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p013 | メモリ | vector_top_k / vector_rank=1 / lec03-main-p013 |
| 2 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | vector_top_k / vector_rank=2 / lec03-main-p065 |
| 3 | lec03-main-p039 | 実装例：Claude | vector_top_k / vector_rank=3 / lec03-main-p039 |
| 4 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | vector_top_k / vector_rank=4 / lec02-main-p052 |
| 5 | lec03-main-p040 | 実装例：OpenClaw | vector_top_k / vector_rank=5 / lec03-main-p040 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> 第2回のLoRAと、第3回のセッションをまたぐメモリの違いは以下の通りです。
> 
> - **LoRA**
>   - **固定するもの**: 元の重み（Pretrained Weights $W$）は固定し、学習しません（第2回・PDF p.52）。
>   - **学習するもの**: 小さな行列 $A$・$B$（変化分を表す小さな「差分」）だけを学習します（第2回・PDF p.52）。
>   - **外に保存して次の会話へ戻すもの**: 資料からは確認できません。
> 
> - **セッションをまたぐメモリ**
>   - **固定するもの・学習するもの**: 「覚えている ≠ 学習」であり、モデルの重み等の学習は行いません（第3回・PDF p.13, p.65）。
>   - **外に保存して次の会話へ戻すもの**: 過去のチャット情報をファイルやデータベースなどの外の保存先に書き出し（メモリ）、それを新しいコンテキスト（次の会話）へ戻します（第3回・PDF p.13, p.39）。

### 6. r1_q3_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:49:31+00:00
- 総時間：5.446秒。埋め込み：2.371秒／取得：0.024秒／生成：3.043秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2074、出力=284、思考=未取得、キャッシュ入力=未取得、合計=2358
- 生成API推定費用：$0.001332。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p013 | メモリ | query_aware_graph / vector_rank=1 / lec03-main-p013; lec03-main-p065 → term:memory → lec03-main-p013; lec03-main-p039 → term:memory → lec03-main-p013 |
| 2 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | query_aware_graph / vector_rank=4 / lec02-main-p052 |
| 3 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | query_aware_graph / vector_rank=2 / lec03-main-p065; lec03-main-p013 → term:memory → lec03-main-p065; lec03-main-p039 → term:memory → lec03-main-p065 |
| 4 | lec03-main-p039 | 実装例：Claude | query_aware_graph / vector_rank=3 / lec03-main-p039; lec03-main-p013 → term:memory → lec03-main-p039; lec03-main-p065 → term:memory → lec03-main-p039 |
| 5 | lec03-main-p040 | 実装例：OpenClaw | query_aware_graph / vector_rank=5 / lec03-main-p040; lec03-main-p013 → term:memory → lec03-main-p040; lec03-main-p065 → term:memory → lec03-main-p040; lec03-main-p039 → lec03-main-p040; lec03-main-p039 → term:memory → lec03-main-p040 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec03-main-p013", "lec03-main-p065", "lec03-main-p039"], "query_terms": [{"degree": 6, "term_id": "term:lora", "title": "LoRA", "weight": 3.4247278790723494}, {"degree": 17, "term_id": "term:memory", "title": "メモリ", "weight": 2.480266270231498}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 13, "candidate_count_after_cap": 13, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第2回のLoRAと、第3回のセッションをまたぐメモリ（メモリツールなど）は、モデルの変更・保存先・学習の有無において以下のように異なります。
> 
> **第2回：LoRA**
> - **モデルで固定するもの**: 元の重み $W$ は固定し、学習しません（第2回・PDF p.52）。
> - **学習するもの**: 小さな行列 $A$ と $B$（変化分を表す低ランクの差分）だけを学習します（第2回・PDF p.52）。
> - **外に保存して次の会話へ戻すもの**: 資料には、外の保存先へ保存して次の会話へ戻すという仕組みは記載されていません。
> 
> **第3回：セッションをまたぐメモリ**
> - **モデルで固定するもの**: 重みは変わりません（第3回・PDF p.65）。
> - **学習するもの**: 学習は行わず、「覚えている ≠ 学習」とされています（第3回・PDF p.13）。
> - **外に保存して次の会話へ戻すもの**: 過去のチャット情報をファイルなどの外の保存先（メモリ）に書き出し、必要に応じて読み戻して次のコンテキストへ戻します（第3回・PDF p.13, p.39）。

### 7. r1_q4_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:49:46+00:00
- 総時間：4.869秒。埋め込み：1.411秒／取得：0.031秒／生成：3.419秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2246、出力=59、思考=未取得、キャッシュ入力=未取得、合計=2305
- 生成API推定費用：$0.000821。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p013 | 帰結①：同じ質問でも、答えは毎回変わる | query_aware_graph / vector_rank=1 / lec02-main-p013; lec01-main-p019 → term:rag → lec02-main-p013 |
| 2 | lec01-main-p019 | 研究室の実例：大規模講義の質問に答えるチャットボット | query_aware_graph / vector_rank=2 / lec01-main-p019; lec02-main-p013 → term:rag → lec01-main-p019 |
| 3 | lec03-main-p064 | 補足：長時間タスクの実行能力の最新動向 | query_aware_graph / vector_rank=3 / lec03-main-p064 |
| 4 | lec01-main-p049 | [3] 例題のチャットボットは RAG ：検索してから答える | query_aware_graph / vector_rank=4 / lec01-main-p049; lec02-main-p013 → term:rag → lec01-main-p049; lec01-main-p019 → term:rag → lec01-main-p049 |
| 5 | lec02-main-p003 | チャットボットを作ると、すぐにこんな「厄介さ」に出会う | query_aware_graph / vector_rank=5 / lec02-main-p003; lec02-main-p013 → term:rag → lec02-main-p003; lec01-main-p019 → term:rag → lec02-main-p003 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec02-main-p013", "lec01-main-p019", "lec03-main-p064"], "query_terms": [{"degree": 30, "term_id": "term:rag", "title": "RAG", "weight": 1.9366508236425166}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 23, "candidate_count_after_cap": 23, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 資料からは確認できません（第2回・PDF p.13などでは「RAGって何ですか？」を5回聞いて5回中3回正しいといった例や説明はありますが、今回この環境で実行した実測平均応答時間や正答率についての記載はありません）。

### 8. r1_q4_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:50:01+00:00
- 総時間：4.474秒。埋め込み：1.364秒／取得：0.015秒／生成：3.086秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2246、出力=57、思考=未取得、キャッシュ入力=未取得、合計=2303
- 生成API推定費用：$0.000816。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p013 | 帰結①：同じ質問でも、答えは毎回変わる | vector_top_k / vector_rank=1 / lec02-main-p013 |
| 2 | lec01-main-p019 | 研究室の実例：大規模講義の質問に答えるチャットボット | vector_top_k / vector_rank=2 / lec01-main-p019 |
| 3 | lec03-main-p064 | 補足：長時間タスクの実行能力の最新動向 | vector_top_k / vector_rank=3 / lec03-main-p064 |
| 4 | lec01-main-p049 | [3] 例題のチャットボットは RAG ：検索してから答える | vector_top_k / vector_rank=4 / lec01-main-p049 |
| 5 | lec02-main-p003 | チャットボットを作ると、すぐにこんな「厄介さ」に出会う | vector_top_k / vector_rank=5 / lec02-main-p003 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> 資料からは確認できません（第2回・PDF p.13などには「RAGって何ですか？」を5回聞いて3回正しいという説明例の記載はありますが、今回この環境で実行した実測平均応答時間や正答率についての記載はありません）。

### 9. r2_q1_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:50:15+00:00
- 総時間：3.541秒。埋め込み：1.350秒／取得：0.022秒／生成：2.160秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2403、出力=91、思考=未取得、キャッシュ入力=未取得、合計=2494
- 生成API推定費用：$0.000948。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | query_aware_graph / vector_rank=1 / lec02-main-p052; lec02-main-p051 → lec02-main-p052; lec02-main-p051 → term:lora → lec02-main-p052; lec02-main-p051 → term:qlora → lec02-main-p052; lec02-main-p060 → term:qlora → lec02-main-p052 |
| 2 | lec02-main-p051 | PEFT ：モデル全体ではなく、一部だけを学習する | query_aware_graph / vector_rank=2 / lec02-main-p051; lec02-main-p052 → lec02-main-p051; lec02-main-p052 → term:lora → lec02-main-p051; lec02-main-p052 → term:qlora → lec02-main-p051; lec02-main-p060 → term:qlora → lec02-main-p051 |
| 3 | lec02-main-p060 | 今日の演習： QLoRA で出力形式を矯正し、効果を測る | query_aware_graph / vector_rank=3 / lec02-main-p060; lec02-main-p052 → term:qlora → lec02-main-p060; lec02-main-p051 → term:qlora → lec02-main-p060 |
| 4 | lec02-main-p061 | 演習の進め方と提出物（仮） | query_aware_graph / vector_rank=4 / lec02-main-p061; lec02-main-p052 → term:qlora → lec02-main-p061; lec02-main-p051 → term:qlora → lec02-main-p061; lec02-main-p060 → lec02-main-p061; lec02-main-p060 → term:qlora → lec02-main-p061 |
| 5 | lec02-main-p047 | 根拠と諸説：知識の追加は RAG が効きやすい | query_aware_graph / vector_rank=5 / lec02-main-p047; lec02-main-p052 → term:lora → lec02-main-p047; lec02-main-p051 → term:lora → lec02-main-p047 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec02-main-p052", "lec02-main-p051", "lec02-main-p060"], "query_terms": [{"degree": 6, "term_id": "term:lora", "title": "LoRA", "weight": 3.4247278790723494}, {"degree": 7, "term_id": "term:qlora", "title": "QLoRA", "weight": 3.2911964864478267}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 11, "candidate_count_after_cap": 11, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第2回の説明では、LoRAは元の重みを固定し、小さな追加部分（または細長い2つの小さな行列の積である差分・行列AとB）を学習します（第2回・PDF p.51, p.52）。また、QLoRAはLoRAに加えて、元の重みを4bitに圧縮します（第2回・PDF p.51, p.52）。

### 10. r2_q1_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:50:29+00:00
- 総時間：5.698秒。埋め込み：1.381秒／取得：0.015秒／生成：4.291秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2403、出力=78、思考=未取得、キャッシュ入力=未取得、合計=2481
- 生成API推定費用：$0.000916。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | vector_top_k / vector_rank=1 / lec02-main-p052 |
| 2 | lec02-main-p051 | PEFT ：モデル全体ではなく、一部だけを学習する | vector_top_k / vector_rank=2 / lec02-main-p051 |
| 3 | lec02-main-p060 | 今日の演習： QLoRA で出力形式を矯正し、効果を測る | vector_top_k / vector_rank=3 / lec02-main-p060 |
| 4 | lec02-main-p061 | 演習の進め方と提出物（仮） | vector_top_k / vector_rank=4 / lec02-main-p061 |
| 5 | lec02-main-p047 | 根拠と諸説：知識の追加は RAG が効きやすい | vector_top_k / vector_rank=5 / lec02-main-p047 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> LoRAは元の重みを固定し、小さな「差分」（細長い2つの小さな行列A・B）だけを学習します（第2回・PDF p.51, p.52）。
> QLoRAは、LoRAに加えて元の重みを4bitに圧縮します（第2回・PDF p.51, p.52）。

### 11. r2_q2_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:50:45+00:00
- 総時間：4.498秒。埋め込み：1.365秒／取得：0.015秒／生成：3.110秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=1911、出力=180、思考=未取得、キャッシュ入力=未取得、合計=2091
- 生成API推定費用：$0.001023。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p040 | 実装例：OpenClaw | vector_top_k / vector_rank=1 / lec03-main-p040 |
| 2 | lec03-main-p039 | 実装例：Claude | vector_top_k / vector_rank=2 / lec03-main-p039 |
| 3 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | vector_top_k / vector_rank=3 / lec03-main-p065 |
| 4 | lec03-main-p038 | メモリがないと、毎回ゼロからやり直しになる | vector_top_k / vector_rank=4 / lec03-main-p038 |
| 5 | lec03-main-p041 | Skill：繰り返す作業の手順をファイルに保存しておく | vector_top_k / vector_rank=5 / lec03-main-p041 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> コンパクションとセッションをまたぐメモリの違いについて、コンパクションは同じセッション内のコンテキスト（履歴）を要約して詰めるもので、古い履歴を要約に置き換えるものです（第3回・PDF p.39、p.65）。一方、セッションをまたぐメモリは外の保存先を利用し、ファイルに書き出すなどしてセッションをまたいで保持される仕組みです（第3回・PDF p.39）。
> 
> また、紹介されたOpenClawの例では、日々のメモはすべて長期メモリに移されるわけではなく、基準を超えたものだけが残されます（第3回・PDF p.40）。一度きりの調べものは日々のメモに残るだけで長期メモリには移されず、全部は残さない仕組みになっています（第3回・PDF p.40）。

### 12. r2_q2_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:50:59+00:00
- 総時間：4.889秒。埋め込み：1.384秒／取得：0.025秒／生成：3.471秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=1911、出力=198、思考=未取得、キャッシュ入力=未取得、合計=2109
- 生成API推定費用：$0.001068。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p040 | 実装例：OpenClaw | query_aware_graph / vector_rank=1 / lec03-main-p040; lec03-main-p039 → lec03-main-p040; lec03-main-p039 → term:memory → lec03-main-p040; lec03-main-p065 → term:memory → lec03-main-p040 |
| 2 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | query_aware_graph / vector_rank=3 / lec03-main-p065; lec03-main-p040 → term:memory → lec03-main-p065; lec03-main-p039 → term:memory → lec03-main-p065 |
| 3 | lec03-main-p039 | 実装例：Claude | query_aware_graph / vector_rank=2 / lec03-main-p039; lec03-main-p040 → lec03-main-p039; lec03-main-p040 → term:memory → lec03-main-p039; lec03-main-p065 → term:memory → lec03-main-p039 |
| 4 | lec03-main-p038 | メモリがないと、毎回ゼロからやり直しになる | query_aware_graph / vector_rank=4 / lec03-main-p038; lec03-main-p040 → lec03-main-p039 → lec03-main-p038; lec03-main-p040 → term:memory → lec03-main-p038; lec03-main-p039 → lec03-main-p038; lec03-main-p039 → term:memory → lec03-main-p038; lec03-main-p065 → term:memory → lec03-main-p038 |
| 5 | lec03-main-p041 | Skill：繰り返す作業の手順をファイルに保存しておく | query_aware_graph / vector_rank=5 / lec03-main-p041; lec03-main-p040 → lec03-main-p041; lec03-main-p040 → term:memory → lec03-main-p041; lec03-main-p039 → lec03-main-p040 → lec03-main-p041; lec03-main-p039 → term:memory → lec03-main-p041; lec03-main-p065 → term:memory → lec03-main-p041 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec03-main-p040", "lec03-main-p039", "lec03-main-p065"], "query_terms": [{"degree": 17, "term_id": "term:memory", "title": "メモリ", "weight": 2.480266270231498}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 15, "candidate_count_after_cap": 15, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第3回の講義資料によると、コンパクションとセッションをまたぐメモリの違いは以下の通りです。
> 
> * **コンパクション**：同じセッションのコンテキストの中で、古い履歴を要約して詰める機能です（第3回・PDF p.39、p.65）。
> * **セッションをまたぐメモリ**：外の保存先を利用して記録を保持する仕組みであり、講義本編の分類では「セッションをまたぐ記録（メモリツール）」に当たります（第3回・PDF p.39、p.65）。
> 
> また、紹介されたOpenClawの例では、日々のメモはすべて長期メモリに移されるわけではありません。毎晩の見直し（dreaming）において、基準を超えたものだけが残され、一度きりの調べものは日々のメモに残るだけで全部は残さない仕組みになっています（第3回・PDF p.40）。

### 13. r2_q3_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:51:14+00:00
- 総時間：4.294秒。埋め込み：1.377秒／取得：0.024秒／生成：2.879秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2074、出力=283、思考=未取得、キャッシュ入力=未取得、合計=2357
- 生成API推定費用：$0.001330。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p013 | メモリ | query_aware_graph / vector_rank=1 / lec03-main-p013; lec03-main-p065 → term:memory → lec03-main-p013; lec03-main-p039 → term:memory → lec03-main-p013 |
| 2 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | query_aware_graph / vector_rank=4 / lec02-main-p052 |
| 3 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | query_aware_graph / vector_rank=2 / lec03-main-p065; lec03-main-p013 → term:memory → lec03-main-p065; lec03-main-p039 → term:memory → lec03-main-p065 |
| 4 | lec03-main-p039 | 実装例：Claude | query_aware_graph / vector_rank=3 / lec03-main-p039; lec03-main-p013 → term:memory → lec03-main-p039; lec03-main-p065 → term:memory → lec03-main-p039 |
| 5 | lec03-main-p040 | 実装例：OpenClaw | query_aware_graph / vector_rank=5 / lec03-main-p040; lec03-main-p013 → term:memory → lec03-main-p040; lec03-main-p065 → term:memory → lec03-main-p040; lec03-main-p039 → lec03-main-p040; lec03-main-p039 → term:memory → lec03-main-p040 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec03-main-p013", "lec03-main-p065", "lec03-main-p039"], "query_terms": [{"degree": 6, "term_id": "term:lora", "title": "LoRA", "weight": 3.4247278790723494}, {"degree": 17, "term_id": "term:memory", "title": "メモリ", "weight": 2.480266270231498}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 13, "candidate_count_after_cap": 13, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 第2回のLoRAと第3回のメモリ（セッションをまたぐ記録）は、モデルの重みを変更するかどうか、および情報をどこに保存する点で異なります。
> 
> **第2回 LoRA**
> - **モデルで固定するもの**：元の重み $W$ は固定し、学習しません（第2回・PDF p.52）。
> - **学習するもの**：小さな行列 $A$ 和 $B$ （変化分を表す低ランクの差分）だけを学習します（第2回・PDF p.52）。
> - **外に保存して戻すもの**：資料には、外の保存先へ書き出して次の会話へ戻すという仕組みは確認できません。
> 
> **第3回 セッションをまたぐメモリ**
> - **モデルで固定するもの・学習するもの**：モデルの重みは変わりません（第3回・PDF p.65）。
> - **外に保存して戻すもの**：過去のチャット情報やメモなどを、ファイルやデータベースといった「外の保存先（メモリ）」に書き出し、必要に応じて次のコンテキスト（新しい会話）へ読み戻します（第3回・PDF p.13, p.39）。なお、資料では「覚えている ≠ 学習」とされています（第3回・PDF p.13）。

### 14. r2_q3_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:51:28+00:00
- 総時間：5.239秒。埋め込み：1.363秒／取得：0.015秒／生成：3.853秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2074、出力=200、思考=未取得、キャッシュ入力=未取得、合計=2274
- 生成API推定費用：$0.001122。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec03-main-p013 | メモリ | vector_top_k / vector_rank=1 / lec03-main-p013 |
| 2 | lec03-main-p065 | 補足：メモリと Context Engineering の最新動向 | vector_top_k / vector_rank=2 / lec03-main-p065 |
| 3 | lec03-main-p039 | 実装例：Claude | vector_top_k / vector_rank=3 / lec03-main-p039 |
| 4 | lec02-main-p052 | LoRA と QLoRA ：大きなモデルも GPU 1 台で調整できる | vector_top_k / vector_rank=4 / lec02-main-p052 |
| 5 | lec03-main-p040 | 実装例：OpenClaw | vector_top_k / vector_rank=5 / lec03-main-p040 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> LoRAとセッションをまたぐメモリの違いは以下の通りです。
> 
> - **モデルで固定するもの**
>   - LoRAでは、元の重み $W$ は固定して学習しません（第2回・PDF p.52）。
> - **モデルで学習するもの**
>   - LoRAでは、小さな「差分」を表す細長い2つの行列（A・B）だけを学習します（第2回・PDF p.52）。
> - **外に保存して次の会話へ戻すもの**
>   - セッションをまたぐメモリでは、ファイルやデータベースなどの外の保存先に書き出し（例：メモリツールによるファイル操作など）、次の会話（新しいコンテキスト）の最初に読み戻して使います（第3回・PDF p.13, p.39）。なお、第3回の資料では「覚えている ≠ 学習」とされています（第3回・PDF p.13）。

### 15. r2_q4_baseline／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:51:44+00:00
- 総時間：3.456秒。埋め込み：1.352秒／取得：0.015秒／生成：2.080秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2246、出力=35、思考=未取得、キャッシュ入力=未取得、合計=2281
- 生成API推定費用：$0.000761。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p013 | 帰結①：同じ質問でも、答えは毎回変わる | vector_top_k / vector_rank=1 / lec02-main-p013 |
| 2 | lec01-main-p019 | 研究室の実例：大規模講義の質問に答えるチャットボット | vector_top_k / vector_rank=2 / lec01-main-p019 |
| 3 | lec03-main-p064 | 補足：長時間タスクの実行能力の最新動向 | vector_top_k / vector_rank=3 / lec03-main-p064 |
| 4 | lec01-main-p049 | [3] 例題のチャットボットは RAG ：検索してから答える | vector_top_k / vector_rank=4 / lec01-main-p049 |
| 5 | lec02-main-p003 | チャットボットを作ると、すぐにこんな「厄介さ」に出会う | vector_top_k / vector_rank=5 / lec02-main-p003 |

経路の要約：

> {"algorithm": "course_cosine_top_k_stdlib"}


回答：

> 資料からは確認できません（第2回・PDF p.13、第1回・PDF p.19、第3回・PDF p.64）。

### 16. r2_q4_graph／試行1

- 状態：`completed`／段階：`completed`／開始UTC：2026-11-17T23:51:57+00:00
- 総時間：4.476秒。埋め込み：2.403秒／取得：0.030秒／生成：2.034秒。
- 生成要求数：1／終了理由：STOP／応答モデル版：gemini-3.5-flash-lite
- tokens：入力=2246、出力=57、思考=未取得、キャッシュ入力=未取得、合計=2303
- 生成API推定費用：$0.000816。paid Standard list-price estimate before unverified cache discounts; not an invoice
  - 推定の仮定：思考トークン欄は未返却。total = input + output のため推定計算では0とした。
  - 推定の仮定：キャッシュ欄は未返却。割引を確認できないため入力全量を通常単価で見積もった。

取得ページと経路：

| 順位 | ページID | タイトル | 取得経路 |
|---:|---|---|---|
| 1 | lec02-main-p013 | 帰結①：同じ質問でも、答えは毎回変わる | query_aware_graph / vector_rank=1 / lec02-main-p013; lec01-main-p019 → term:rag → lec02-main-p013 |
| 2 | lec01-main-p019 | 研究室の実例：大規模講義の質問に答えるチャットボット | query_aware_graph / vector_rank=2 / lec01-main-p019; lec02-main-p013 → term:rag → lec01-main-p019 |
| 3 | lec03-main-p064 | 補足：長時間タスクの実行能力の最新動向 | query_aware_graph / vector_rank=3 / lec03-main-p064 |
| 4 | lec01-main-p049 | [3] 例題のチャットボットは RAG ：検索してから答える | query_aware_graph / vector_rank=4 / lec01-main-p049; lec02-main-p013 → term:rag → lec01-main-p049; lec01-main-p019 → term:rag → lec01-main-p049 |
| 5 | lec02-main-p003 | チャットボットを作ると、すぐにこんな「厄介さ」に出会う | query_aware_graph / vector_rank=5 / lec02-main-p003; lec02-main-p013 → term:rag → lec02-main-p003; lec01-main-p019 → term:rag → lec02-main-p003 |

経路の要約：

> {"algorithm": "query_aware_bounded_graph_v1", "seed_page_ids": ["lec02-main-p013", "lec01-main-p019", "lec03-main-p064"], "query_terms": [{"degree": 30, "term_id": "term:rag", "title": "RAG", "weight": 1.9366508236425166}], "ignored_query_terms": [], "limits": {"max_candidates": 24, "max_expansion_vector_rank": 50, "max_hops": 2, "max_term_degree": 32}, "relations_used": ["next_page", "mentions"], "relations_not_used": ["contains", "related_term"], "candidate_count_before_cap": 23, "candidate_count_after_cap": 23, "weights": {"new_query_term_coverage": 0.23, "redundancy_penalty": 0.05, "relevance": 0.72}, "rejected_cross_document_next_page_edges": 0}


回答：

> 資料からは確認できません（第2回・PDF p.13などでは「RAGって何ですか？」を5回聞いて5回中3回正しいといった例や説明はありますが、実測平均応答時間や正答率の具体的な数値は記載されていません）。

## 人手確認

確認者：takerunakao（AI支援の確認案を読み、判定・観察を確認）／確認日：2026-11-18T09:17:23+09:00

| 実行ID | 回答の正しさ | 引用内容の裏付け | 回答保留 | 判断メモ |
|---|---|---|---|---|
| r1_q1_baseline | pass | pass | not_applicable | 元の重みの固定、小さな行列A・Bの学習、QLoRAの4bit圧縮を説明しており、第2回p.52がすべてを裏付ける。 |
| r1_q1_graph | pass | pass | not_applicable | 元の重みの固定、小さな差分の学習、QLoRAの4bit圧縮を説明しており、第2回p.51・52が支える。実引用2ページに対し自動抽出はp.51の1ページだけである。 |
| r1_q2_graph | fail | pass | not_applicable | 同じセッション内の履歴要約と外部保存、OpenClawの選別保存は正しく、p.39・65・40が裏付ける。ただし事前基準の「次の会話のコンテキストへの読み戻し」を明示していないため、完全性の基準は未達。誤情報による不合格ではない。 |
| r1_q2_baseline | fail | pass | not_applicable | コンパクション、外部保存、OpenClawの選別保存は正しく、p.39・40が裏付ける。ただし外部メモリの読み戻しと次のコンテキストへの再注入の説明が欠け、事前基準の一部を満たさない。 |
| r1_q3_baseline | pass | pass | not_applicable | 第2回p.52のW固定・A/B学習と、第3回p.13・39・65の外部保存・読み戻しを区別し、メモリ利用を重みの学習と混同していない。実引用4ページに対し自動抽出は2ページである。 |
| r1_q3_graph | pass | pass | not_applicable | 第2回p.52のW固定・低ランク行列の学習、第3回p.65の重み不変、p.13・39の保存と再注入を正しく比較する。実引用4ページは取得本文に裏付けられるが、自動抽出では3ページである。 |
| r1_q4_graph | pass | pass | pass | 今回の実測値を確認できないと明言し、数値を作っていない。第2回p.13の3/5を説明例として実測と区別する。引用はこの例を支えるもので、資料全体に記録がないことを証明するものではない。 |
| r1_q4_baseline | pass | pass | pass | 実測値を断定せず、第2回p.13の3/5を説明用の例と明確に区別する。例示への引用は本文と一致する。回答保留は適切だが、次に確認すべき実行ログや正答判定への案内はない。 |
| r2_q1_graph | pass | pass | not_applicable | 元の重みの固定、低ランクの差分の学習、QLoRAの4bit圧縮を正しく区別する。A/Bの詳細は第2回p.52にあり、p.51・52の併記が支える。実引用2ページに対し自動抽出は1ページである。 |
| r2_q1_baseline | pass | pass | not_applicable | 元の重みと小さな行列A・Bを区別し、QLoRAの4bit圧縮も説明する。第2回p.51・52が裏付ける。実引用2ページに対し、自動抽出はp.51の1ページだけである。 |
| r2_q2_baseline | fail | pass | not_applicable | 同一セッションの要約、外部ファイルへの保存、メモの選別は正しく、p.39・65・40が裏付ける。ただし次の会話への読み戻しが欠ける。実引用3ページに対し自動抽出は2ページである。 |
| r2_q2_graph | fail | pass | not_applicable | 履歴要約と外部記録、OpenClawの見直し・選別は資料に沿うが、次のコンテキストへの読み戻しを明示していない。p.39・65・40は記述を支える。実引用3ページに対し自動抽出は2ページである。 |
| r2_q3_graph | pass | pass | not_applicable | 固定するW、学習するA/B、外部に保存して再注入する情報を区別できる。第2回p.52と第3回p.13・39・65が裏付ける。「A 和 B」は軽微な表記揺れ。実引用4ページに対し自動抽出は3ページである。 |
| r2_q3_baseline | pass | pass | not_applicable | 第2回p.52のW固定・A/B学習と第3回p.13・39の外部保存・読み戻しを区別する。「会話の最初に」は資料の実装例の説明として解釈し、全メモリ実装のタイミングへ一般化しない。実引用3ページに対し自動抽出は2ページである。 |
| r2_q4_baseline | pass | unsure | pass | 回答を保留し、秒数や正答率を作っていない。一方、第2回p.13、第1回p.19、第3回p.64を列挙するだけで、説明例・別システム・別指標と実測不明の判断との対応を説明していない。すべて取得済みだが、引用の意味的裏付けはunsureとした。 |
| r2_q4_graph | pass | pass | pass | 第2回p.13の3/5を説明用の例と区別し、今回の実測値は確認できないとして保留する。数値の捏造はない。引用は説明例を支えるが、確認可能な範囲は取得資料に限られ、実測を答えるには別途今回のログが必要である。 |

### 比較の観察

4問×2方式×2回の16回答はすべて正常完了した。事前根拠グループはq1〜q3で両方式とも12/12取得し、q4は対象外とした。事前の回答基準をすべて満たす回答は双方6/8（75%、回答保留を含む）で、q2の各2回答は読み戻しの説明不足により未達だった。これは本評価セットでの完全性の集計であり、モデルの一般的な正答率ではない。取得5ページの集合は8比較ペアすべて同じで、新規根拠の採用は0件。平均総時間は基本4.584591秒、Graph4.581870秒で、速度差は確認できない。入力は各17,268tokens、出力は基本1,016・Graph1,256tokens、生成API推定費用合計はそれぞれ0.0077204・0.0083204米ドルだった。

### 改善・同等・悪化の具体例

q3ではGraphがLoRAの根拠lec02-main-p052を4位から2位へ上げ、メモリの根拠の直後に置く動作を確認した。ただし基本RAGも同じページを取得し、両方式とも回答基準を満たしたため、取得率・回答品質の改善例とはしない。q2はp.39とp.65の順が入れ替わったが、両方式とも「外部保存した情報を次の会話へ読み戻す」という説明が欠けた。p.39には必要な根拠があるため、検索漏れではなく、回答へ必要事項を反映する段階の不足である。q4は全回答が実測値の作り話を避けた。基本RAGの反復2は引用を列挙するだけで判断との対応が不明瞭だったが、同一の取得内容からの生成差であり、Graphの優位とは結論しない。

### 残る失敗・限界

基本RAGの根拠取得がすでに100%で、この質問集合では取得率の改善余地がなかった。独立な質問は4問だけで、反復を増やした16回答を16種類の問題とは数えない。q1・q4は生成リクエストのハッシュまで同じでも回答が変わり、temperature=0でも生成の揺れが残った。平均総時間差は約0.00272秒、中央値は基本4.486秒・Graph4.672秒で、API側の変動と検索方式の影響を切り分けられない。Graphの推定生成費用は今回7.77%多かったが、入力は同数で、出力240tokensの差に対応する。一般的な費用増加とはしない。元の自動引用抽出は「p.13, p.39」の後続ページを落としていた。回答ごとの重複除外引用数は自動29件に対し本文照合39件（基本19、Graph20）で、欠落10件もすべて取得済みだった。原記録は変更せず、実引用一覧と見落としをreview_addendum.md・review_audit.jsonへ補足する。引用先の存在は39/39でも、意味的な裏付けは15回答pass・1回答unsureであり、100%正しい引用とは扱わない。

### 採否

今回の用途では基本RAGを当面採用し、Graph併用は比較実装として保管する。

### 採否の理由

根拠取得・回答の完全性に改善を確認できず、時間も同等であるため、実装と保守が単純な基本RAGを選ぶ。Graphの検索候補拡張とq3の順位変更は動作したが、有効性の立証には至っていない。次は、関連根拠がベクトル上位5件から漏れる未使用の質問集合を事前に定め、関係種類・hop数・取得枠の比較を行いたい。q2の不足には、必要な説明要素を網羅したかを確かめる共通の生成・検証手順も検討する。これらは今後の案であり、今回実施済みの改善結果ではない。

### Quri Q3

AI支援を用い、基本RAGとGraph併用RAGを同じ214ページ・モデル・取得5ページで4問×各2回比較しました。対象3問の根拠取得率は双方100%でも、問2は読み戻しの説明が欠け、事前基準を満たす回答は双方6/8件でした。Graphで根拠の順序は変わりましたが新規取得はなく、平均時間も約4.58秒で同等でした。引用抽出の見落としを本文との照合で補足し、取得・回答・引用を分けて評価しました。今回の結果では基本RAGを採用し、Graphは未使用の質問で再検証すると整理しました。

## 原記録

- [実行設定と事前登録した評価基準](config.json)
- [全試行・取得本文・完全な経路・応答・使用量](records.jsonl)
- [人手確認用の参照ページ本文](reference_pages.json)
- [人手判定と観察](human_review.json)

実測していない値は未取得・算定不可として残す。未知の料金を0ドル、未知の判定を合格として扱わない。
