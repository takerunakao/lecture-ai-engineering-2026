# Day2 発展：用語集でLoRA学習し、学習前後と検索を比較する

## 現在の状態

**GPU学習と学習前後の評価が正常に完了しました。実測ログに基づく `answer.md` と、298文字のQ3も完成しています。**

実行IDは `20261026T182827Z_9d9332f8`。Tesla T4で3エポック・48更新を完了し、学習時間は170.50秒でした。24問の形式遵守率は学習前0%から学習後100%へ改善しましたが、必須語句と確認要求ラベルによる内容正解率は12.5%で、用語名・別名検索の83.3%を下回りました。採点の限界と不正確な回答の具体例も [提出レポート](answer.md) に記載しています。

**今回の提出用データは完成しており、追加のGPU学習は不要です。GitHubへの反映は未完了です。** 前回のGitHub連携は書き込み権限エラー（403）で停止したため、以下の手順で自分の公開forkへ反映してください。

このREADMEと考察・Q3は、実験完了後に提出用として更新しました。学習・評価コード、データ、実測ログはその実験で使用・生成された内容を保持しています。元の実行時ソースを含むZIPは最終配布ZIP内の `evidence/original_colab_submission.zip` に保存し、結果フォルダにも元のマニフェストを残しています。提出時の説明更新と、実験時点のソース記録を区別できます。

## 今回の提出に使うファイル

配布された **`submit_day2_final.py` だけを** 自分のforkのルートにアップロードして実行します。検証済みの元ZIPと完成した考察・Q3を内蔵しているため、結果ZIPの別指定は不要です。

```bash
python submit_day2_final.py --check
python submit_day2_final.py
```

コード・データ・完了ログ・最終版の `answer.md`・Q3を配置します。元ログを検証し、回答原文から再採点して表を作るため、ZIP内の集計値だけを信用して取り込む処理ではありません。既存の演習欄と手書きメモを保持し、手を加えていない演習テンプレートだけ今回実施した範囲の説明に更新します。GPU学習、ネットワーク接続、gitのcommit・pushは行いません。

`day2_submission_final.zip` は最終成果物と元実験記録をまとめた閲覧・保存用の一式です。**この最終ZIPを旧 `install_day2.py --results` に渡さないでください。** 旧インストーラーは新しい実験の取り込み用であり、今回整理した考察・Q3を反映する入口は `submit_day2_final.py` です。

## 2026年10月27日の修正

初回配布版には、`transformers==5.18.0` の `apply_chat_template()` が既定で返す `BatchEncoding` を、整数token ID列として扱う不具合がありました。その結果、辞書の2項目を「2トークン」と数え、学習前評価の最初の入力で `TypeError` となりました。修正版は `return_dict=False` と `return_tensors=None` を明示し、非空・一次元の整数列であることもモデルを読み込む前に検査します。

今回は学習本体の `tokenize_all()` を固定tokenizerで直接実行し、学習124件の最大229トークン、評価24件の入力最大144トークンを確認しました。以前の独立したtokenizer検証に加え、実際に学習本体が使う経路を回帰検証しています。検証記録は `data/tokenizer_validation.json` の `runner_regression_validation` に含めています。

旧版ですでに失敗した場合は、同時配布の `day2_repair_colab.py` を現在のColabへアップロードし、`runpy.run_path()` で実行できます。このスクリプトは新しい作業フォルダに修正版を展開し、前評価・学習・後評価・レポート・ZIPまで実行します。旧フォルダと失敗ログは保持し、同じランタイムのモデルキャッシュを利用します。**この再実行スクリプトを使った後は、旧ノートブックの残りのセルを実行せず、スクリプトからダウンロードされる新しいZIPを使ってください。**

通常の例外も本文を `result.json`、詳細を `traceback.txt` に残し、子プロセスの出力を画面と `console.log` に記録するよう修正しました。修正版での再実行は正常に完了し、今回の結果フォルダに実測ログを保存しています。

## 再実験用ノートブック

**以下は条件を変えて新しく実験する場合の手順です。今回の提出のために再実行する必要はありません。** 先に配布した `day2_advanced_colab.ipynb` には必要なコードとデータを内蔵しており、GitHubへの保存前でも実行できます。

1. [Google Colab](https://colab.research.google.com/) の「ファイル → ノートブックをアップロード」で `day2_advanced_colab.ipynb` を開き、自分のドライブにコピーを保存します。
2. 「ランタイム → ランタイムのタイプを変更 → T4 GPU」を選びます。
3. 「ランタイム → すべてのセルを実行」を選び、上から実行します。依存導入、内蔵ファイルの展開、データ作成、学習前評価、LoRA学習、学習後評価、レポート作成までコードに含まれています。Gemini APIキーは使いません。
4. 最後のセルで提出用のZIPがダウンロードされます。コード・データ・実行ログ・`answer.md`・400文字以内のQ3案を含み、モデル重みは含みません。ダウンロード許可が出た場合は許可してください。
5. ZIPの取り込みには、同時に配布した `install_day2.py --results <ZIP>` を使います。ZIPを既存forkへ丸ごと上書きせず、既存の演習欄とメモを残し、実測ログから宿題欄を再生成します。取り込み後、fork側の `lectures/02/answer.md` にある比較表と回答原文を読み、自動生成領域の外へ気づきを追記します。ChatGPTへZIPを添付して、結果の確認・考察・GitHub反映を続けることもできます。
6. 成功した結果と考察を反映してから、自分のforkの`main`向けPRを提出用に確認します。提出先は講義本体リポジトリではなく、自分のforkです。
7. 作業後は「ランタイム → ランタイムを接続解除して削除」を行います。

学習に失敗した場合は、最後のダウンロードセルを単独で実行すると残っている部分ログを保存できます。途中結果は未完了として保存され、実施済みの前後比較へは取り込まれません。GPUを確保できない場合は、時間を変えて再実行してください。講師の参考結果は今回の用語集データを学習した結果ではありません。

同じColab内に変更済みのファイルが残っている場合、展開セルは上書きせず停止します。必要な結果を保存してから、新しいランタイムでやり直してください。学習済みadapterが残った状態を学習前として測定することを避けるため、条件を変えるときも最初から実行します。

## 今回の完了結果を公開forkへ取り込んで提出する

### 1. 自分のforkでCodespacesを開き、`lec02`へ切り替える

[自分の公開fork](https://github.com/takerunakao/lecture-ai-engineering-2026) の「Code → Codespaces」からCodespaceを開きます。以下はリポジトリのルートにあるターミナルで実行します。

```bash
git remote -v
git status --short
git fetch origin
```

`origin` が `takerunakao/lecture-ai-engineering-2026` であることと、既存の作業状態を確認します。続いて、ローカルまたはGitHubに `lec02` があればそれを使い、なければ自分のforkの `main` から作成します。

```bash
if git show-ref --verify --quiet refs/heads/lec02; then
  git switch lec02
elif git show-ref --verify --quiet refs/remotes/origin/lec02; then
  git switch --track origin/lec02
else
  git switch main &&
  git pull --ff-only origin main &&
  git switch -c lec02
fi
```

未コミットの作業によって切り替えが拒否された場合は、その作業を元のブランチで保存してから再開します。Day1のコード・演習・メモを削除したり、強制的に上書きしたりする手順は含めていません。

### 2. 最終版スクリプトをアップロードして実行する

Codespacesのファイル一覧で、リポジトリのルートへ `submit_day2_final.py` をアップロードします。ZIPの展開や追加ライブラリのインストールは不要です。

```bash
python submit_day2_final.py --check
python submit_day2_final.py
```

| 実行方法 | 動作 |
|---|---|
| `python submit_day2_final.py` | コード・データ・検証済み完了ログ・最終版の考察とQ3を取り込む |
| `--check` | 対象と整合性を確認し、書き込まない |
| `--replace` | 自分で変更した既存Day2ファイルとの競合を、バックアップを残して更新する |

既存の演習欄と、自動生成領域の外のメモは保持します。今回の考察と同じ内容がすでにある場合は重複追加しません。前の準備版READMEは完了状態へ更新しますが、独自に編集したREADMEや今回の考察がある場合は通常実行で停止します。差異を確認し、更新すると判断した場合は次を使ってください。

```bash
python submit_day2_final.py --replace --check
python submit_day2_final.py --replace
```

同一の実行IDを持つログが異なる場合は `--replace` でも上書きしません。Day1のファイルは対象外です。バックアップ先は実行時に表示します。

### 3. 差分と考察を確認し、Day2の対象だけをcommit・pushする

```bash
git status --short
git diff --stat
git diff -- lectures/02/answer.md
```

演習欄と既存のメモが残っていること、学習結果が自分の実行ログと一致すること、考察・Q3が自分の理解に合うことを確認します。今回の考察とQ3は実測値と回答原文に基づいて完成しています。確認後、以下のDay2関連パスを指定してステージします。

```bash
git add -- .gitignore \
  app/day2_eval.py \
  scripts/prepare_day2_data.py \
  scripts/run_day2_training.py \
  scripts/prepare_day2_answer.py \
  tests/test_day2_advanced.py \
  notebooks/day2_advanced_glossary.ipynb \
  lectures/02/README_ADVANCED.md \
  lectures/02/problem.md \
  lectures/02/answer.md \
  lectures/02/data \
  lectures/02/results \
  lectures/02/submission_q3.txt
git diff --cached --name-only
git diff --cached --stat
```

以前にステージした別の作業が含まれていないことを確認してから、commitとpushを行います。

```bash
git commit -m "Complete Day2 advanced glossary LoRA comparison"
git push -u origin lec02
```

### 4. 自分のforkの`main`向けにPRを作成する

[自分のforkの比較画面](https://github.com/takerunakao/lecture-ai-engineering-2026/compare/main...lec02?expand=1) を開き、**base repository が `takerunakao/lecture-ai-engineering-2026`、base が `main`、compare が `lec02`**であることを確認して「Create pull request」を選びます。提出用のPRは自分のfork内に作成します。

PRでは、用語集データへの変更、学習前後と検索の比較、確認できた結果・限界を簡潔に説明します。今回の実行は学習と比較まで完了したため、Q1は「発展」、Q2は一式を反映した自分の公開forkのURL、Q3は完成した298文字の回答を記載します。

### GitHubへ保存した後の入口

`lec02` に一式を保存した後は、[リポジトリ版のノートブック](../../notebooks/day2_advanced_glossary.ipynb) または [Colabリンク](https://colab.research.google.com/github/takerunakao/lecture-ai-engineering-2026/blob/lec02/notebooks/day2_advanced_glossary.ipynb) も使えます。こちらは公開forkの `lec02` を取得する方式なので、ブランチが未公開の状態では実行できません。

## 宿題の要件と対応

| 発展課題の要件 | この実装での対応 |
|---|---|
| `scripts/make_sft_dataset.py`で用語集Q&A生成 | 元スクリプトを変更せず実行し、116件の元JSONLを保存 |
| FAQの代わりに学習 | 58語×2質問の116件をJSON回答に変換し、確認要求8件を加えた計124件 |
| 評価質問と正解を自作 | 既知語8問、言い換え8問、用語集にない語8問。計24問を学習前に固定 |
| 学習前後比較 | adapter装着前の基盤モデルと、LoRA学習後を同じ入力・生成条件で評価 |
| 用語集検索との比較 | 問題文から正規名・ID・別名を検出し、一意なら原定義を返す。正解IDは検索に渡さない |
| 数字と考察を提出 | 実測ログの再採点後、全回答の原文を照合して考察と298文字のQ3を完成 |

`make_sft_dataset.py` の元出力は通常の定義文です。そのままではJSON形式の評価目標と異なるため、`prepare_day2_data.py` でassistant出力を `{"answer": 定義, "needs_review": false}` に包み、共通のsystem指示を付けています。この変換をmanifestとレポートに明記しています。

用語集にない質問への望ましい出力は `{"answer": "この用語集には記載がありません。確認が必要です。", "needs_review": true}` です。学習用の範囲外8語と評価用の範囲外8語は分けています。`needs_review` は用語集に根拠があるかのラベルであり、モデルが一般知識としてその語を知っているかを表すラベルではありません。

## 実験条件

| 項目 | 設定 |
|---|---|
| モデル | `Qwen/Qwen3.5-0.8B` |
| revision | `2fc06364715b967f1860aea9cf38778875588b17` |
| 学習方式 | 非量子化float32のLoRA |
| LoRA | r=16、alpha=32、dropout=0.05 |
| 学習 | epoch=3、lr=2e-4、batch=4、勾配累積=2、warmup=6、cosine |
| 更新回数 | 124件、1 GPUで48回。今回の実行で48回・3エポックの完了を確認 |
| 入力上限 | 全会話512トークン。全件を事前に計数し、超過時は停止 |
| 生成 | greedy、最大256トークン、thinking無効、EOSはtokenizerの値を前後共通で明示 |
| 生成入力 | 共通systemと質問だけ。用語集本文・検索結果・goldは入れない |
| 損失の対象 | system/userを含む全会話（講義の既定と同じ） |
| seed | 42 |

元のFAQ実験は14件×20epochですが、用語集データは124件なので3epochに変更しています。元実験の「4〜5分」をこの実験の所要時間としては使いません。

固定版は、`transformers==5.18.0`、`peft==0.21.1`、`trl==1.14.2`、`accelerate==1.15.0`、`datasets==5.1.0`。torchはColab同梱版を維持します。

## 評価と実測結果

- `format_rate`：JSONが読め、キーが`answer`と`needs_review`だけで、型が文字列と真偽値になっている割合。
- `content_rate`：`needs_review`が正解と一致し、答えが指定の必須語句をすべて含む割合。形式が崩れていてもJSON部分を読める場合は内容を別に採点します。
- `both_rate`：形式・内容とも正解の割合。
- `review_accuracy`：確認要求の真偽値が正解と一致する割合。

必須語句による採点は意味的正しさの近似です。正しい言い換えを不正解としたり、語句だけ揃った誤回答を見逃したりする可能性があるので、全回答の原文も保存します。

### 学習前後と検索の比較

| 指標 | 学習前 | 学習後 | 用語名・別名検索 |
|---|---:|---:|---:|
| 形式遵守率 | 0/24（0%） | 24/24（100%） | 24/24（100%） |
| 内容正解率（語句・ラベル判定） | 0/24（0%） | 3/24（12.5%） | 20/24（83.3%） |
| 確認要求ラベルの正解率 | 15/24（62.5%） | 14/24（58.3%） | 20/24（83.3%） |

学習前の全回答にMarkdownのコードフェンスがあり、それを除くと22/24件は指定したJSONスキーマを満たしました。学習後の形式改善には、この余分な装飾を抑えた効果が含まれます。内容の自動判定で合格した3問にも不正確な記述があり、意味的に正しい回答が3問あったとは断定しません。用語集の範囲外8問では学習後に確認要求を一度も返せず、確認要求を返した2問は用語集内の語でした。

自動集計の退行0問は、学習前に形式・内容の両方で合格した回答が0問だったことによる限界があります。確認要求ラベルでは、SFTの言い換え問題1問が正答から誤答へ変化しました。詳しい例と解釈は [answer.md](answer.md)、根拠は [result.json](results/20261026T182827Z_9d9332f8/result.json) と同じフォルダの評価原文を参照してください。

### 用語名・別名検索の実測

| 区分 | 正解 | 内容正解率 |
|---|---:|---:|
| 既知語 | 8/8 | 100.0% |
| 言い換え | 4/8 | 50.0% |
| 用語集にない語 | 8/8 | 100.0% |
| 全体 | 20/24 | 83.3% |

形式遵守率は100%ですが、検索側はプログラムがJSONを組み立てるためです。用語名を出さない4問で確認要求を返しました。この限定的な検索方式の結果であり、意味検索やRAG一般の性能を示しません。

[検索の全出力](data/search_baseline.json)

### 固定tokenizerでのCPU検証

| 対象 | 件数 | 最大トークン数 |
|---|---:|---:|
| 学習の全会話 | 124 | 229 |
| 評価の入力 | 24 | 144 |
| 学習の正解出力（EOSまで） | 124 | 107 |
| 評価の正解出力（EOSまで） | 24 | 89 |

全148件で、推論プロンプトと学習用会話の先頭部分は文字列・token IDとも一致しました。これはtokenizerの検証であり、モデルの回答生成・GPU学習を実行した結果ではありません。

[tokenizer検証の実測記録](data/tokenizer_validation.json)

### オフライン検証

```bash
python3 -m unittest discover -s tests -p 'test_day2_advanced.py' -v
python3 scripts/run_day2_training.py --dry-run
```

採点の型、形式と内容の分離、学習・評価の重複、近い名称の誤検索、正解IDの検索への混入、未完了ログの取り込み拒否、rawからのカテゴリ再集計、手書きメモの保持などを検証します。モデル出力を模したユニットテスト用データは一時領域だけで使い、実測結果として保存・提出しません。

## 主なファイル

| ファイル | 役割 |
|---|---|
| `notebooks/day2_advanced_glossary.ipynb` | Colabで上から実行する入口 |
| `scripts/prepare_day2_data.py` | 元スクリプト実行、JSON教師化、データ整合性検査、検索評価 |
| `scripts/run_day2_training.py` | 学習前評価、LoRA学習、学習後評価、全ログの保存 |
| `app/day2_eval.py` | 共通の採点と検索 |
| `scripts/prepare_day2_answer.py` | 完了ログから宿題欄とQ3を生成 |
| `lectures/02/data/` | 学習・評価データ、条件、検索とtokenizerの実測記録 |
| `lectures/02/results/<実行ID>/` | Colab実行後に作られるモデルの実測ログ |

レポートだけを再生成するときは、リポジトリのルートで次を実行します。

```bash
python scripts/prepare_day2_answer.py
```

最新の完了した実験を使います。学習済み結果がないときは完了レポートを作りません。`answer.md` の自動生成部分以外に書いた考察・メモと演習欄は保持します。ただし、このコマンドは `submission_q3.txt` を一般的な自動生成案に更新するため、今回の提出版を使う場合は再生成せず、最終版スクリプトで配置したQ3を使ってください。別の実験を行った場合は、新しいログに合わせて考察とQ3を見直します。

## 提出欄

- Q1：「発展」を選択。今回のGPU学習と前後・検索比較は完了しています。
- Q2：[自分の公開リポジトリ](https://github.com/takerunakao/lecture-ai-engineering-2026)。講義本体のURLではありません。
- Q3：`lectures/02/submission_q3.txt` の完成版（298文字、末尾改行を除く）を確認して提出。

AIツールを実験設計・実装・文章整理に使用したことと、自分で実行・確認した範囲をレポートに記載します。

## 参考

- [2026年10月21日更新の講義課題](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/662cddd52724b330f3f4cd15123d1e55cb474874/lectures/02/problem.md)
- [講義の元ノートブック](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/f9ab3d5288ba5d4cd6fecd5e30515192a5cb05b6/notebooks/lora_format_tuning.ipynb)
- [TRL 1.14.2 SFTTrainer](https://huggingface.co/docs/trl/v1.14.2/sft_trainer)
- [固定revisionのQwenモデル](https://huggingface.co/Qwen/Qwen3.5-0.8B/tree/2fc06364715b967f1860aea9cf38778875588b17)
