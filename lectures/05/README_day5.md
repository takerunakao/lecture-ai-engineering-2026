# Day5 発展の実行・提出手順

今回は、基本RAGと改良Graphの実際の比較が必要です。設計・コードの準備だけでは提出完成にしません。Q3は**300文字以内**です。

## 1. ファイルを配置する

`install_day5.py`を、Codespacesの`pyproject.toml`と同じ階層にアップロードします。ターミナルで実行します。

```bash
git switch main && \
git pull --ff-only origin main && \
git switch -c lec05 && \
python install_day5.py
```

すでに`lec05`がある場合は、次を使います。

```bash
git switch lec05 && \
python install_day5.py
```

既存のDay1〜4のコード・依存関係に手を入れず、Day5専用ファイルを配置します。現在のforkに残る旧MCP版のDay5空テンプレートは、新しいRAG課題に合わせて置き換えます。独自の追記があれば停止します。

## 2. 教材と構成を確認する（モデルAPIは呼びません）

```bash
python scripts/run_day5_comparison.py --setup
```

確定コミットの教材JSON・グラフ・検索DBを取得し、ハッシュと214ページの整合性を確認します。Python標準ライブラリだけを使うので、`uv sync`や追加パッケージのインストールは不要です。教材は`lectures/05/.cache`に保存し、Git管理から外します。

再度、ダウンロードせず確認する場合：

```bash
python scripts/run_day5_comparison.py --check
```

`GEMINI_API_KEY`は以前のCodespacesのSecretを使います。値をターミナルへ貼る必要はありません。未設定と表示された場合はGitHubのCodespaces Secretsを確認し、Codespaceを再起動します。

## 3. 質問と設計を確認する

- [questions.json](questions.json)：比較する4問と事前に確認した根拠。
- [design.md](design.md)：基本RAGとGraphの違い、比較条件、評価方法。

2方式とも同じ214ページ、同じ質問、同じモデル、取得5ページです。Graphは質問に現れる用語で候補を絞り、複数の話題を含むページを選びます。取得後は共通の生成処理を1回実行します。

## 4. 実際に比較する（ここでモデルAPIを呼びます）

```bash
python scripts/run_day5_comparison.py --run
```

既定では**4問×2方式×2回＝16回答**です。生成API16回と、質問の埋め込みAPI16回を呼びます。試行の間に10秒待機します。実行は数分以上かかることがあります。実行中のターミナルとCodespaceをそのままにしてください。

モデルは`AIE_MODEL`があればその値、なければ`gemini-3.5-flash-lite`です。既定モデルの有料Standard単価で生成費用を推定し、無料枠や実際の請求と区別します。モデルを変更した場合、確認済み単価がなければ費用は「算定不可」です。

途中で失敗しても、完了済みの試行とエラーを保存して停止します。自動的な再試行・別モデルへの変更はしません。

## 5. 結果ZIPをダウンロードして共有する

最後に次の形式の保存先を表示します。

```text
記録: lectures/05/results/日時_ID/report.md
ダウンロードするZIP: lectures/05/day5_results_日時_ID.zip
```

Codespaces左側で`lectures`→`05`を開き、表示されたZIPを右クリックして**Download**を選び、このチャットに添付してください。エラー時も同じZIPを共有できます。

ZIPには回答、取得根拠、経路、時間、使用量、条件、コードの写しが入ります。APIキー・環境変数・教材DB・他の宿題は入れません。

ZIPを確認してから、回答の正しさと引用の妥当性、改善例・残る失敗や制約、用途への採否をまとめます。改善が出なかった場合も実際の結果を記載します。

エラーの原因を確認した後、条件を変えずに続きを実行する場合：

```bash
python scripts/run_day5_comparison.py --resume latest
```

コード・質問・資料を変更した場合は、同じ実験として再開せず、新しい実行にします。

## 6. 観察を確定して、提出ファイルへ取り込む

この段階はZIPの確認後です。結果フォルダの`human_review.json`に、各回答の判定と根拠、考察、300文字以内のQ3を記録します。未確認の判定を成功として埋めません。

確認後に実行します。

```bash
python scripts/prepare_day5_answer.py
```

これで`answer.md`の「宿題」欄、`PR_BODY.md`、`quri_answers.md`を更新します。比較が未完了、または観察が未確認の場合は、提出完成版を生成せず停止します。

## 7. 自分のGitHubへ保存する

提出内容を読んでから、今回のファイルだけを保存します。

```bash
git add day5_lab \
  scripts/run_day5_comparison.py \
  scripts/prepare_day5_answer.py \
  lectures/05 \
  tests/test_day5_retrieval.py \
  tests/test_day5_gemini.py \
  tests/test_day5_reporting.py \
  tests/test_day5_experiment.py
git diff --cached --stat
```

`.cache`とZIPは除外されます。結果フォルダのログは提出対象です。

```bash
git commit -m "Day5 発展：基本RAGと改良Graphの実測比較" && \
git push -u origin lec05
```

## 8. PRとQuri

[PR作成画面](https://github.com/takerunakao/lecture-ai-engineering-2026/compare/main...lec05?expand=1)を開きます。自分のリポジトリの`main ← lec05`を指定します。

タイトル案：**Day5 発展：基本RAGと改良Graphの実測比較**

概要は`lectures/05/PR_BODY.md`をコピーします。PRのURLを共有して最終確認します。

- Q1：実行・考察完了後に「発展｜Advanced」。
- Q2：`https://github.com/takerunakao/lecture-ai-engineering-2026`
- Q3：確認後に生成された`quri_answers.md`の文。300文字以内。

最後にCodespacesの**Stop Current Codespace**で停止します。

## 検証について

配布前に、実際の教材の読込、取得方法、API応答の処理、途中失敗と再開、未確認結果を提出済みにしない処理をオフラインで検証しています。モックを使った確認は生成モデルの性能測定ではありません。このパッケージを作成する段階ではモデルAPIを呼び出していません。
