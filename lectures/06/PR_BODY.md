## 概要

Day6の発展課題として、VS CodeのMCP設定方法を公式資料で調べ、講座の `app/mcp_servers.json` と比較しました。

設定を書く場所・コマンド起動・URL接続・有効範囲の4項目を、`lectures/06/answer.md` の宿題欄に整理しています。

## 工夫した点

- 現行のCopilot向け設定と従来のエディター管理形式を分け、調査時点の公式案内に合わせた。
- 講座側はコミットを固定し、JSONの見た目だけでなく `app/mcp_agent.py` の読み込み処理と照合した。
- 同じ起動コマンド・URLを3形式で表す6つの設定例を用意し、比較条件をそろえた。
- 出典URL、調査日、静的チェックの範囲を明記した。

## 確認方法

```bash
python lectures/06/check_submission.py --write-result
```

実行記録は `lectures/06/validation.json` に保存します。確認対象はJSON構文と比較項目であり、MCPサーバーの実接続・ツール実行は含みません。

## 主な提出ファイル

- `lectures/06/answer.md`：発展課題の回答
- `lectures/06/examples/`：比較用の設定例6件
- `lectures/06/source_manifest.json`：公式資料と比較対象コミット
- `lectures/06/check_submission.py`、`validation.json`：静的チェックと実行記録
- `lectures/06/quri_answers.md`：Quri入力用の回答

調査日：2026年11月23日
