# 第6回 解答

## 演習

<!-- この提出には講義中の STEP 1〜4 の実行ログを収録していないため、実行結果を補完しない。 -->

- STEP 1 のツールの名前：
- STEP 2 の [tool call]：
- STEP 3 の [tool call]：
- STEP 4 の [tool call]：
- 気づき・疑問：以下の宿題では、MCPを利用するクライアントごとの設定方法を調査した。

## 宿題

- **取り組んだレベル：発展**
- **選んだソフトウェア：VS Code**。講座ではGitHub CodespacesのVS Code画面を使用している。今回は、調査時点で公式資料が新規設定に推奨する **Copilot向けのネイティブMCP設定**を主対象とし、従来のエディター管理形式も比較した。手元のVS Codeのバージョンや、選択中のエージェント実行環境を特定した調査ではない。
- **調査日：2026年11月23日（日本時間）**
- **やったこと：** 公式資料を読み、設定の場所、コマンド起動、URL接続、有効範囲の4項目を講座の `app/mcp_servers.json` と比較した。さらに、公式講座コードの読み込み処理と照合し、同じサーバーを表す6つの設定例を作成した。
- **結果：** 講座と現行のCopilot向け設定は、どちらも `mcpServers` を使う。ただし、設定を読むプログラム、配置場所、追加項目の扱いは異なる。従来のVS Code形式は `servers` を使い、現行形式と区別する必要がある。
- **気づき・疑問：** MCPの通信方式が共通でも、設定ファイルまで共通になるとは限らない。特に、JSONとして正しいこと、クライアントがその設定を読むこと、実際にツールを使えることは別々に確認する必要がある。

### 1. 必須4項目の比較

講座側は、公式リポジトリのコミット `03d0fd36d58ada1ac1366c0d485ac103ef44ca52` を比較対象に固定した。[S1][S2][S3]

| 比較項目 | 講座のエージェント | VS CodeのCopilot向けネイティブ設定 |
|---|---|---|
| 設定を書く場所 | `app/mcp_servers.json`。公式の `app/mcp_agent.py` が自分と同じディレクトリのファイルを読む。 | ワークスペース直下の `.mcp.json`。ユーザー共通は `$COPILOT_HOME/mcp-config.json`、未設定なら `~/.copilot/mcp-config.json`。 |
| コマンドで起動する書き方 | `mcpServers` の中に `command` と `args`。読み込み処理はstdioの接続を作り、必要なら `env` を渡す。 | `mcpServers` の中に `type: "stdio"`、`command`、`args`。作業ディレクトリは `cwd`、提供するツールの選択は `tools` で表す。 |
| URLで接続する書き方 | `mcpServers` の中に `url`。例は演習STEP 4のAWS Knowledge。 | `mcpServers` の中に `type: "http"` と `url`。HTTPヘッダーやツールの選択も指定できる。 |
| 有効になる範囲 | そのファイルを読む講座エージェント。VS Code全体の設定として自動登録されるものではない。 | `.mcp.json` は当該ワークスペース。ユーザー共通設定は同じホストでその設定を読むワークスペース・対応クライアントに及ぶ。別PCへの自動同期を意味しない。 |

VS Code側の根拠は公式設定リファレンスと導入手順。[S4][S5]

設定画面は `Chat: Open Customizations` → `MCP Servers` → `Add Server` から開ける。個人用は `Global` → `Copilot Global`。`.mcp.json` をGUIの保存先に出す機能は、調査時点では `chat.mcp.workspaceRootConfig.enabled` に依存する。既存ファイルの読み取りと、GUIでの選択肢の表示は区別されている。[S4][S5]

### 2. 同じサーバーを表す設定例

以下は**形式を比較するための例**で、すべて `examples/` に保存した。起動コマンドは講座の用語集サーバー、URLは演習STEP 4のAWS Knowledgeにそろえ、サーバーの違いが比較へ混ざらないようにした。[S1][S2]

#### コマンド起動：講座の形式

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    }
  }
}
```

ファイル：[course_stdio.json](examples/course_stdio.json)。これは調査対象コミットの設定ファイルと同じ内容である。

#### コマンド起動：VS Codeの現行Copilot向け形式

```json
{
  "mcpServers": {
    "glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "cwd": "/workspaces/lecture-ai-engineering-2026",
      "tools": ["*"]
    }
  }
}
```

ファイル：[vscode_copilot_stdio.json](examples/vscode_copilot_stdio.json)。`cwd` は今回のCodespacesで使っている配置先を例示した。別の環境では実際の配置先に合わせる。`tools: ["*"]` は公開ツール全体を選ぶ指定であり、個々の実行承認を省く指定ではない。[S4]

#### URL接続：講座の形式

```json
{
  "mcpServers": {
    "aws": {
      "url": "https://knowledge-mcp.global.api.aws"
    }
  }
}
```

ファイル：[course_http.json](examples/course_http.json)。演習STEP 4からURL接続の項目だけを取り出した比較例。[S1]

#### URL接続：VS Codeの現行Copilot向け形式

```json
{
  "mcpServers": {
    "aws": {
      "type": "http",
      "url": "https://knowledge-mcp.global.api.aws",
      "tools": ["*"]
    }
  }
}
```

ファイル：[vscode_copilot_http.json](examples/vscode_copilot_http.json)。同じ接続先を、VS Code公式のHTTP設定形式で表した。[S4]

### 3. 追加で調べた違いと考察

#### 従来のVS Code形式との違い

従来の `.vscode/mcp.json` やプロファイルの `mcp.json` は、トップレベルに `servers` を使うエディター管理形式である。現在の公式資料ではLocal向けの互換設定として区別され、移行先はワークスペースの `.mcp.json` またはCopilotのユーザー設定になる。[S7]

比較用に [vscode_legacy_stdio.json](examples/vscode_legacy_stdio.json) と [vscode_legacy_http.json](examples/vscode_legacy_http.json) も用意した。したがって、「VS Codeは必ず `servers` を使う」とはまとめられない。**調査日と対象の実行環境を添え、現行設定と従来設定を分ける**必要がある。

#### 講座の読み込み処理を確認して分かったこと

公式の `read_config()` と `load_mcp_servers()` から、次のことが読み取れる。[S3]

- `json.loads(...)["mcpServers"]` で読むため、従来のVS Code形式をそのまま渡すと必要なキーがない。
- `url` があればURL接続へ分岐する。`command` と `url` の両方を書いた場合、コード上はURL側が優先される。今回の例では片方だけを記載した。
- stdioの場合に読むのは `command`、`args`、`env`。`type`、`cwd`、`tools`、`headers` を使う処理はこのローダーにはない。
- 不明な項目を一律に拒否する実装でもない。コピーした項目が読み取られず、設定したつもりの動作にならない可能性がある。

このため、現行Copilotと講座でトップレベルが一致しても、設定をそのまま交換できるとは判断できない。例えば上の `cwd` は、講座側にコピーしても作業ディレクトリ指定として利用されない。これは公開コードからの考察であり、実機で起動失敗を再現した結果ではない。

#### 環境変数と実行場所

従来のVS Codeに固有の入力変数や設定項目は、そのままCopilot設定へ移せるとは限らない。公式移行資料は入力プロンプトを環境変数へ置き換える場合も区別して説明している。[S7] 講座ローダーにも、JSON内のVS Code変数を展開する処理は見当たらなかった。[S3]

また、設定の「ユーザー共通」という範囲と、プロセスの「どこで動くか」は別の観点である。公式のRemote／Dev Containerの説明では、設定やコマンドの前提をエージェントが動くホストに合わせる。[S6][S7] この規則をCodespacesへ当てはめると、手元PCとコンテナのパスや実行環境を混同しない確認が必要になる。これは資料に基づく考察であり、この提出でリモート接続を実証したものではない。

### 4. 確認できる範囲と結果の記録

調査と設定例の作成にはAIの支援を利用した。根拠は以下の公式資料と公開コードである。実際のMCP接続、ツール呼び出し、モデルAPIの実行結果は、この提出には含めていない。

同梱のスクリプトをリポジトリ直下から実行すると、6つのJSON例の構文・トップレベル・通信方式に対応する項目を確認できる。さらに、3形式で起動コマンドとURLが同じであること、Q3が300文字以内であることを検査する。

```bash
python lectures/06/check_submission.py --write-result
```

結果は実行時刻・入力ファイルのSHA256とともに `validation.json` に保存される。これはこの提出用に定義した項目の**静的チェック**であり、VS Codeや講座クライアントによる完全な設定検証、接続成功の証明ではない。接続まで確認する場合は、公式手順のように、実際のツール呼び出しと返り値を別途観察する必要がある。[S5]

### 5. 参照資料

すべて2026年11月23日に確認。講座コードはコミットを固定し、Web資料は更新され得るため調査日を併記した。

- **[S1]** 松尾・岩澤研究室／Day6 演習・宿題（発展の進め方、STEP 4）  
  https://github.com/matsuolab/lecture-ai-engineering-2026/blob/03d0fd36d58ada1ac1366c0d485ac103ef44ca52/lectures/06/problem.md
- **[S2]** 松尾・岩澤研究室／`app/mcp_servers.json`  
  https://github.com/matsuolab/lecture-ai-engineering-2026/blob/03d0fd36d58ada1ac1366c0d485ac103ef44ca52/app/mcp_servers.json
- **[S3]** 松尾・岩澤研究室／`app/mcp_agent.py`（`MCP_CONFIG`、`read_config`、`load_mcp_servers`）  
  https://github.com/matsuolab/lecture-ai-engineering-2026/blob/03d0fd36d58ada1ac1366c0d485ac103ef44ca52/app/mcp_agent.py
- **[S4]** Microsoft／MCP configuration reference（Configure MCP for Copilot、Local compatibility）  
  https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- **[S5]** Microsoft／Add and use MCP servers in VS Code（設定方法、適用範囲、ツール呼び出しの確認）  
  https://code.visualstudio.com/docs/agent-customization/mcp-servers
- **[S6]** Microsoft／Manage and troubleshoot MCP servers（設定共有、Remote／Dev Container）  
  https://code.visualstudio.com/docs/agents/run/manage-mcp-servers
- **[S7]** Microsoft／Migrate customizations to the Copilot harness in VS Code（設定の移行先、非互換項目）  
  https://code.visualstudio.com/docs/agent-customization/migrate-customizations

出典の対応と講座ファイルのハッシュは [source_manifest.json](source_manifest.json) に記録した。
