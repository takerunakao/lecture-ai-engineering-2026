# Day6 発展課題：提出までの手順

今回は、VS CodeのMCP設定を公式資料で調べ、講座の設定と比較する発展課題です。必要な成果物は調査レポートです。モデルAPIの呼び出しや、MCPへの実接続はこの課題の必須条件に含まれていません。

課題の公式案内：
https://github.com/matsuolab/lecture-ai-engineering-2026/blob/03d0fd36d58ada1ac1366c0d485ac103ef44ca52/lectures/06/problem.md

調査日：2026年11月23日。利用するブランチ：`lec06`。

## ① 提出用スクリプトをダウンロードする

チャットの添付ファイル `install_day6.py` をダウンロードします。提出ファイル一式が入っているため、まず必要なのはこの1ファイルです。

ZIPを利用する場合は、`day6_submission_pack.zip` を解凍し、中の同じ `install_day6.py` を使います。

## ② GitHubで作業画面を開く

1. 自分のリポジトリを開きます。  
   https://github.com/takerunakao/lecture-ai-engineering-2026
2. `Code` → `Codespaces` から、これまで使っていたCodespaceを開きます。
3. 作業画面でターミナルを開きます。通常の作業場所は `/workspaces/lecture-ai-engineering-2026` です。

## ③ ダウンロードしたファイルをアップロードする

Codespacesの左側のファイル一覧へ `install_day6.py` をドラッグしてアップロードします。

`pyproject.toml` や `README.md` と同じ階層に置いてください。ダウンロード時に名前へ `(1)` などが付いた場合は、`install_day6.py` に直します。

## ④ コードをコピーして、提出ファイルを配置する

リポジトリ直下のターミナルへ、以下をまとめて貼り付けて実行します。

```bash
git switch main &&
git pull --ff-only origin main &&
if git show-ref --verify --quiet refs/heads/lec06; then
  git switch lec06
elif git show-ref --verify --quiet refs/remotes/origin/lec06; then
  git switch --track -c lec06 origin/lec06
else
  git switch -c lec06
fi &&
python install_day6.py &&
python lectures/06/check_submission.py
```

`静的チェック: PASS（6設定例）` と表示され、入力待ちのプロンプトに戻れば、配置と検査が終わっています。

### 提出前に読むファイル

`lectures/06/answer.md` を開いてください。宿題欄に、4項目の比較、設定例、気づき、出典が入っています。

特に次の3点を公式資料・コードのリンクと照らし合わせて確認します。

1. 講座と現行のCopilot向け設定は、どちらもトップレベルが `mcpServers`。
2. 従来のVS Code形式は `servers` を使う。保存先や読み込むプログラムも区別が必要。
3. 講座の読み込み処理では `cwd` や `tools` を利用しない。JSONとして読み取れることと、その項目が使われることは別。

「気づき・疑問」が自分の理解と合うことを確認し、追記したい観察があれば編集して保存します。Q3の文章は `lectures/06/quri_answers.md` にあります。

設定例は比較資料として `lectures/06/examples/` に配置されます。追加の依存ライブラリのインストールは不要です。

## ⑤ GitHubへ保存する

以下をまとめて実行します。今回の対象は `lectures/06/` です。

```bash
test "$(git branch --show-current)" = "lec06" &&
python lectures/06/check_submission.py --write-result &&
git add -- lectures/06 &&
git --no-pager diff --cached --stat -- lectures/06 &&
if git diff --cached --quiet -- lectures/06; then
  echo "Day6の変更はコミット済みです。pushへ進みます。"
else
  git commit --only -m "Day6発展課題：VS CodeのMCP設定と講座設定を比較" -- lectures/06
fi &&
git push -u origin lec06
```

検査の実行時刻と結果は `lectures/06/validation.json` に記録されます。モデルAPIは使いません。

最後にpushの成功表示を確認してからPR作成画面へ進んでください。新規ブランチなら `lec06 -> lec06` や追跡設定のメッセージが表示されます。

## ⑥ PRを作成し、Quriへ入力する

### PRを作る

比較画面：
https://github.com/takerunakao/lecture-ai-engineering-2026/compare/main...lec06?expand=1

- リポジトリ：`takerunakao/lecture-ai-engineering-2026`
- base：`main`
- compare：`lec06`

タイトル：

```text
Day6発展課題：VS CodeのMCP設定と講座設定の比較
```

概要欄には `lectures/06/PR_BODY.md` の内容を貼り付け、`Create pull request` を押します。

`Files changed` に `lectures/06/answer.md`、設定例、`validation.json` が含まれることを確認します。内容を確認できたら、ご自身のforkの `main` へマージします。

### Quriへ入力する

`lectures/06/quri_answers.md` の内容を使います。

- **Q1：発展｜Advanced**
- **Q2：** `https://github.com/takerunakao/lecture-ai-engineering-2026`
- **Q3：** 同ファイルのQ3本文。日本語300文字以内です。

マージ後の回答確認先：
https://github.com/takerunakao/lecture-ai-engineering-2026/blob/main/lectures/06/answer.md

Q2はリポジトリURLを求められているため、上記のリポジトリ本体のURLを入力します。Quriで回答を送信し、提出済みの状態を確認します。

## 表示が想定と異なる場合

| 表示・状況 | 次に確認すること |
|---|---|
| `python: can't open file 'install_day6.py'` | ファイルの名前と置いた階層を確認する。 |
| 既存ファイルを保護して中止 | 既にあるDay6ファイルと内容が異なる。エラーメッセージと対象ファイルを共有して、保存済みの作業を確認する。 |
| `main and lec06 are identical` | ⑤のcommitとpushの終了表示を確認する。ブランチ作成だけでは比較する変更は増えない。 |
| `git pull` や `git switch` で中止 | 表示されたエラーを確認する。後続の配置処理は実行されない。 |

## ファイル一覧

| ファイル | 用途 |
|---|---|
| `answer.md` | 宿題の本文。必須4項目・調査日・出典を収録。 |
| `examples/` | 講座・現行Copilot・従来VS Codeの各stdio/HTTP例、計6件。 |
| `check_submission.py` | 標準ライブラリだけで実行する静的チェック。 |
| `validation.json` | `--write-result` で作る実行記録。 |
| `source_manifest.json` | 公式資料・講座コミット・参照ファイルのハッシュ。 |
| `PR_BODY.md` | 日本語のPR概要。 |
| `quri_answers.md` | Q1〜Q3の入力用回答。 |

スクリプトの検査範囲は同梱例のJSON構文・比較項目です。MCPの実接続結果としては扱いません。
