# Claude Code Remote Control ガイド

updated: 2026-03-14

---

## 概要

ローカルPC（VS Code）を起動した状態で、iPhoneアプリからClaude Codeをリモート操作する手順。

---

## セットアップ手順

### 1. PC側（VS Code ターミナル）

```bash
claude --remote-control
```

起動すると以下が表示される：

```
/remote-control is active. Code in CLI or at
https://claude.ai/code/session_XXXXXXXXXXXXXXXX
```

### 2. スマホ側（iPhone）

表示されたURLにアクセス、またはClaudeアプリから同一アカウントのセッションを開く。

```
https://claude.ai/code/session_XXXXXXXXXXXXXXXX
```

---

## 環境情報（初回接続時）

| 項目 | 内容 |
|------|------|
| アカウント | tomtomaipro@gmail.com |
| 作業ディレクトリ | `C:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System` |
| モデル | Claude Sonnet 4.6 |
| プラン | Claude Pro |

---

## Web版 vs Remote Control 使い分け

| 状況 | 使う方法 |
|------|---------|
| PC停止中・外出先 | **Web版**（claude.ai から直接） |
| PC起動中・ローカル作業 | **Remote Control** |
| MCP・ローカルファイル操作 | **Remote Control 必須** |

---

## 注意事項

- PCのターミナルを閉じるとセッションが切れる
- Web版セッションで行った変更は、PC起動前に `git push` しておく
- PC起動時は `git pull` してからRemote Controlを起動する
- 同時並行作業はコンフリクトの原因になるので避ける

---

## 推奨ワークフロー（PC起動時）

```
PC起動
  ↓
git pull origin master
  ↓
claude --remote-control（VS Codeターミナル）
  ↓
iPhoneからセッションURLにアクセス
  ↓
作業
  ↓
git push（作業後）
```

---

## ナビ

- [Trade-Main](./Trade-Main.md)
- [BRANCH_MAP](./BRANCH_MAP.md)
- [STATUS](./STATUS.md)
