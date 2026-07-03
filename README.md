# Trade_System — Minato流MTF USDJPY アルゴトレーディング

4H上昇ダウが継続する限り、押し目条件が揃うたびにエントリーを繰り返す構造を
窓ベース階層スキャンで検出するバックテストシステム。純アルゴ開発の単一ドメイン。

**現在地**: #026d（PF 4.54 / 勝率 60% / +150.6p・10件）。数値の正は `docs/SYSTEM_OVERVIEW.md`。

---

## 入口（新規セッションはここから読む）
```
| # | ファイル | 役割 |
|---|---|---|
| 1 | `AGENTS.md` | governance 正本（全engine必読・源1枚） |
| 2 | `docs/SYSTEM_OVERVIEW.md` | 現状スナップショット（最初に読む） |
| 3 | `docs/EX_DESIGN_CONFIRMED.md` | 設計確定（ロジック定義・パラメータ） |
| 4 | `docs/ADR.md` | 判断台帳（失敗パターン集 + 設計方針ガイド） |
| 5 | `docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md` | 裁量思想の最上位辞書 |
```
> ClaudeCode-native は root `CLAUDE.md`（@AGENTS.md シム）経由で AGENTS.md を読む。
> grok / codex は Hermes dir-scope で起動時に自動注入される。

---

```
Trade_System/
├── AGENTS.md              # governance 正本（全engine共有）
├── CLAUDE.md              # ClaudeCode-native 用シム（@AGENTS.md）
├── README.md              # 本ファイル（リポ入口導線）
├── src/                   # 実装（凍結4 + 拡張可能 + archive/）
├── docs/                  # canon — 現在有効な設計のみ
│   ├── SYSTEM_OVERVIEW.md        # 現状スナップショット
│   ├── EX_DESIGN_CONFIRMED.md    # 設計確定（ロジック・パラメータ）
│   ├── ADR.md                    # 判断台帳（失敗パターン + 方針ガイド）
│   └── Base_Logic/               # 裁量思想・整合性QA
├── configs/  data/        # 設定・データ（parquet）
└── logs/
    ├── coordination/      # 指示書・実行結果・整理オペ（全engine共有・append-only）
    ├── scratch/           # 各engineの検索/探索ログ（claude/codex/grok）
    └── archive/           # 旧版canon/governanceの凍結退避（参照禁止）
```
---

## 運用

- **最終判断はボス**。固定role分担は持たない。engine は AGENTS.md に従う
- 姉妹リポ **Trade_Brain**（市況データ・週次・distilled = 静的データ層）と分担。
  本リポは動的ロジック層（シグナル・Fibonacci・BackTest）
- **書き込み経路**: MCP接続セッションは GitHub MCP のみ使用（filesystem write 禁止）。
  詳細は AGENTS.md「編集経路」節。ローカル実装（ClaudeCode等）は `git pull --rebase` 先行
- **凍結ファイル**（backtest / entry_logic / exit_logic / swing_detector）は変更禁止。
  #018 ベースライン再現性の保持のため

---

## リポジトリ

- 本リポ: `Minato33440/Trade_System`（動的ロジック側）
- 姉妹リポ: `Minato33440/Trade_Brain`（市況データ・週次側）
- Vault: `C:\Python\REX_AI\REX_Brain_Vault\`（`Minato33440/REX_Brain_Vault`）

---

*本ファイルはリポの入口導線。設計の実体は docs/ 直下 canon が正本。*