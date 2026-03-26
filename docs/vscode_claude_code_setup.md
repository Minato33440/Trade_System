# VS Code で Claude Code を使う設定手順

## 前提条件

- **Claude Pro プラン**（またはMax）に加入済みであること
- **Node.js** がインストールされていること（v18以上推奨）
- **VS Code** がインストールされていること

---

## Step 1：Claude Code をインストール

ターミナル（VS Code外でも可）で以下を実行します。

### macOS / Linux

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Windows（PowerShell）

```powershell
irm https://claude.ai/install.ps1 | iex
```

インストール後、以下のコマンドでバージョンを確認します。

```bash
claude --version
---

## Step 2：Claude アカウントでログイン

```bash
claude
```
はじめて起動するとブラウザが開くので、**claude.ai と同じアカウント**でログインします。

> ⚠️ `ANTHROPIC_API_KEY` 環境変数が設定されている場合、サブスクリプションではなく API キーが優先されます。Pro プランで使う場合はこの変数を削除またはコメントアウトしてください。

ログイン成功後、ターミナルに Claude のプロンプトが表示されれば OK です。

---

## Step 3：VS Code 拡張機能をインストール

VS Code の拡張機能パネル（`Cmd+Shift+X` / `Ctrl+Shift+X`）を開き、**「Claude Code」** で検索してインストールします。

拡張機能が見つからない場合は、VSIXファイルを手動でインストールします。

```bash
code --install-extension ~/.claude/local/node_modules/@anthropic-ai/claude-code/vendor/claude-code.vsix
```

---

## Step 4：VS Code の `code` コマンドをシェルに登録

VS Code のコマンドパレット（`Cmd+Shift+P` / `Ctrl+Shift+P`）を開き、以下を実行します。

```
Shell Command: Install 'code' command in PATH
```

これにより、VS Codeのパスが通り、Claude Code がIDE環境を正しく認識できるようになります。

---

## Step 5：VS Code のターミナルから Claude Code を起動

VS Code の統合ターミナル（`` Ctrl+` ``）を開き、以下を実行します。

```bash
claude
```

---

## 主な操作方法

| 操作 | ショートカット |
|------|--------------|
| Claude Code パネルを開く/閉じる | `Cmd+Esc`（Mac） / `Ctrl+Esc`（Win/Linux） |
| ファイルをコンテキストに追加 | `@ファイル名` と入力 |
| コマンドメニューを表示 | `/` を入力 |
| 会話をリセット | `/clear` |

---

## 使用量について

- Pro プランと Max プランは、claude.ai と Claude Code の利用量を**共有**しています
- 使用量が上限に近づくと警告メッセージが表示されます
- より多くの使用量が必要な場合は Max プランへのアップグレードを検討してください

---

## 参考リンク

- [Claude Code 公式ドキュメント](https://docs.claude.com/en/docs/claude-code/overview)
- [サポートセンター](https://support.claude.com)
