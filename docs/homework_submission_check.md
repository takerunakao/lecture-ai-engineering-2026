# 宿題提出フローの確認メモ（2026-11-02）

運営が公開した「宿題提出までの流れ（全11ステップ）」の資料と、本リポジトリ・Omnicampus の状態を照合した結果をまとめる。

## 運営資料の要点（提出フロー 11 ステップ）

1. Codespaces で提出用ブランチを作成する
2. `lectures/<回>/answer.md` を編集し、ステージングする
3. コミットする
4. プッシュする
5. GitHub で「Compare & pull request」を押す
6. **Base repository に自分の fork（`<自分の名前>/lecture-ai-engineering-2026`）を選ぶ**。松尾研本家には出さない
7. base/compare の表示が自分の fork 内の `main` ← ブランチ になったことを確認する
8. 説明を書いて PR を作成する。**マージしてもしなくてもよい**
9. Omnicampus で該当回のクイズを選ぶ
10. Q1 に取り組んだレベル、Q2 に `https://github.com/<自分の名前>/lecture-ai-engineering-2026`（公開リポジトリ必須）、Q3 に工夫点（400 字以内）を入力して提出する
11. 提出状況が「採点待ちです」などになっていれば完了（「未提出」から変わっていればよい）

## 照合結果（Day1・Day2）

### GitHub 側

| 項目 | 状態 |
|---|---|
| fork の公開設定 | public（親: `matsuolab/lecture-ai-engineering-2026`） |
| ブランチ | `lec01`、`lec02` を作成・push 済み |
| PR #2（Day1 発展） | base = 自分の fork の `main`、2026-10-29 マージ済み |
| PR #1（Day2 発展） | base = 自分の fork の `main`、2026-10-29 マージ済み |
| 松尾研本家への PR | なし（正しい） |
| `answer.md` | `lectures/01`・`lectures/02` の編集が fork の `main` に反映済み |

### Omnicampus 側

| 項目 | Day1 | Day2 |
|---|---|---|
| 提出状況 | 提出済み／採点待ち | 提出済み／採点待ち |
| Q1（レベル） | 発展 | 発展 |
| Q2（URL） | fork のルート URL | fork のルート URL |
| Q3（文字数） | 243 字 | 298 字 |
| 受付終了 | 2026-11-02 17:00 | 2026-11-02 17:00 |

結論: Day1・Day2 とも資料どおりに提出できており、追加対応は不要。

## 今後の回で使うチェックリスト

- [ ] `git switch -c lecNN` でブランチを切る
- [ ] `lectures/NN/answer.md` を編集して commit・push する
- [ ] PR の base は **自分の fork** の `main` にする（本家には出さない）
- [ ] Omnicampus のクイズで Q1〜Q3 を入力し「提出する」を押す
- [ ] コーストップで提出状況が「採点待ちです」になったことを確認する
- [ ] fork の公開設定が public のままであることを確認する

## 補足

- fork は upstream より数コミット古いことがある（運営側の `problem.md` 説明文の更新など）。提出には影響しない。必要なら `git fetch upstream && git merge upstream/main` で追従する。
