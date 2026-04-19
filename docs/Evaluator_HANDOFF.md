# Evaluator_HANDOFF.md — Evaluator セッション引き継ぎ書
# 発行: Rex-Evaluator (Opus 4.6) / 2026-04-18
# 宛先: Rex-Evaluator (Opus 4.7) / 次セッション
# 目的: コンテキスト切り替えに伴う完全な状態引き継ぎ

---

## 🔴 最初に読め — 必須読み込み順序

新セッションで最初にやるべきこと:

```
1. C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md（Vault運用指示書）
2. C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md（致命的地雷リスト）
   → 冒頭の「読み込み検証チェックリスト」7問に回答してから作業開始
3. 本ファイル（Evaluator_HANDOFF.md）
4. C:\Python\REX_AI\Trade_System\docs\REX_027_BOSS_DIRECTIVE.md（Directive v2）
```

---

## 本日（2026-04-18）のセッション概要

前任 Evaluator（Opus 4.6）が 1 セッションで以下を完了:

### 完了タスク

| # | タスク | 状態 |
|---|---|---|
| 1 | 引き継ぎ失敗の原因分析（D-6 再発）+ 対策実施 | ✅ |
| 2 | latest.md v4 作成（検証チェックリスト 7 問 + プロンプト短縮版） | ✅ |
| 3 | Vault CLAUDE.md v5 作成（STEP 7/8 強化 + リポ名統一） | ✅ |
| 4 | REX_Brain_Vault 独立リポ化（Minato33440/REX_Brain_Vault） | ✅ |
| 5 | Second_Brain_Lab 構築資料を raw/system_build/ へ移行 | ✅ |
| 6 | wiki/cross/ 骨格作成（プロジェクト横断ナレッジ） | ✅ |
| 7 | Advisor 提言書（REX_027_ADVISOR_PROPOSAL.md）の承認判断 | ✅ |
| 8 | Wiki Phase 1 構築（concepts 3 ページ + _RUNBOOK + F-7 予約） | ✅ |
| 9 | 週次 Git 更新ワークフローの Vault 移設 | ✅ |
| 10 | Trade_System/.CLAUDE.md v5（週次ワークフロー参照 + STEP 4 改訂） | ✅ |
| 11 | REX_027_BOSS_DIRECTIVE v2 受領・Evaluator 承認 | ✅ |
| 12 | MINATO_MTF_PHILOSOPHY.md 第 1 版作成（裁量思想の言語化） | ✅ |

### 全ての変更は git push 済み

```
Minato33440/REX_Brain_Vault     — 全更新 push 済み
Minato33440/Trade_System        — .CLAUDE.md + docs/ 全更新 push 済み
Minato33440/Trade_Brain         — 初期構築済み（ボス実施）
Minato33440/Second_Brain_Lab    — 凍結（README 更新はボス保留）
```

---

## 現在の状態スナップショット

### Trade_System リポ

```
バックテスト: #026d 確定
  PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p（10 件 LONG）

凍結ファイル（変更禁止・差分ゼロ確認必須）:
  src/backtest.py / src/entry_logic.py / src/exit_logic.py / src/swing_detector.py

決済エンジン:
  src/exit_simulator.py（方式 B・正式採用）
  ⚠️ src/exit_logic.py の manage_exit() は使用禁止

docs/ 有効ファイル（全て日付なし・最新版）:
  ✅ EX_DESIGN_CONFIRMED.md       — NLM 投入候補
  ✅ ADR.md                       — NLM 投入候補
  ✅ SYSTEM_OVERVIEW.md            — NLM 投入候補
  ✅ PLOT_DESIGN_CONFIRMED.md      — NLM 投入候補
  ✅ REX_BRAIN_SYSTEM_GUIDE.md    — NLM 投入候補
  ✅ MINATO_MTF_PHILOSOPHY.md     — 本日作成・NLM 投入候補
  ✅ REX_027_BOSS_DIRECTIVE.md v2  — Directive
  ✅ REX_027_ADVISOR_PROPOSAL.md   — Advisor 提言（参照のみ）
  ✅ Evaluator_HANDOFF.md         — 本ファイル
```

### REX_Brain_Vault リポ

```
ルート: C:\Python\REX_AI\REX_Brain_Vault\
GitHub: Minato33440/REX_Brain_Vault（独立リポ）

構造:
REX_Brain_Vault/
├── .gitignore                    ← .obsidian / .venv / .vscode 除外
├── README.md                     ← REX_AI 全体の脳としての説明
├── CLAUDE.md                     ← Vault 運用指示書（v5）
├── raw/
│   └── system_build/             ← Second_Brain_Lab 構築資料
│       ├── README.md
│       ├── LLM Wiki.md
│       ├── REX_Brain_System_BUILD_GUIDE.md
│       ├── MCP-DESIGN-CONFIRMED.md
│       └── # Trade-Schema.md
└── wiki/
    ├── log.md                    ← 時系列作業ログ
    ├── cross/
    │   └── index.md              ← プロジェクト横断骨格
    ├── handoff/
    │   └── latest.md             ← v4（地雷リスト + 検証 7 問）
    └── trade_system/
        ├── _RUNBOOK.md           ← Wiki 運用ガイド
        ├── doc_map.md            ← 設計文書状況
        ├── adr_reservation.md    ← ADR 採番台帳（F-7 予約済み）
        ├── pending_changes.md    ← 未確定変更
        ├── pending_nlm_sync.md   ← NLM 認証切れフォールバック
        ├── weekly_workflow.md    ← 週次 Git 更新ワークフロー
        ├── concepts/
        │   ├── neck.md           ← 統一 neck 原則 + D-6 警告
        │   ├── 4h_superiority.md ← 4H 構造優位性（#026d 核心）
        │   └── window.md         ← 1H 押し目ウィンドウ
        ├── entities/             ← 空（第 3 波で生成）
        ├── patterns/             ← 空（第 3 波で生成）
        ├── bug_patterns/         ← 空（第 2 波で生成）
        ├── decisions/            ← 空（第 2 波で生成）
        └── sources/              ← 空（第 1 波で生成予定）
```

### Trade_Brain リポ（ボス構築済み）

```
ルート: C:\Python\REX_AI\Trade_Brain\
GitHub: Minato33440/Trade_Brain（独立リポ・ボス新設）

構造:
Trade_Brain/
├── .CLAUDE.md
├── CLAUDE.md
├── README.md
├── raw/           ← logs/gm/ から移行
├── distilled/     ← versions/distilled/ から移行
└── docs/
```

### NLM 状態

```
⛔ 切り離し済み（MCP 接続先から外れ・物理削除なし）:
   旧 REX_Trade_Brain (ID: 2d41d672-f66f-4036-884a-06e4d6729866)
   → notebook_query で NOT_FOUND を返す（切り離し確認済み）

✅ 稼働中（新規・クリーン）:
   REX_System_Brain (ID: da84715f-9719-40ef-87ec-2453a0dce67e)
     用途: Trade_System 設計文書用
     source_count: 0（ソース未投入）

   Rex_Trade_Brain  (ID: 4abc25a0-4550-4667-ad51-754c5d1d1491)
     用途: Trade_Brain リポ用（distilled 投入先）
     source_count: 0（ソース未投入）
```

### ADR 採番状況

```
次の空き番号:
  A-6 / B-4 / C-5 / D-11 / E-8 / F-8

本日予約（未確定）:
  F-7 — Vault 構造標準化（Advisor 提言 + Directive v2 に基づく）

Directive v2 で採番指示あり:
  D-11 — Trade_Brain 分離 + NLM RAG 全面再構築（Task D で正式採番）
  F-7  — 本文記載予定（Task D で確定）
```

---

## ⚠️ 致命的な地雷（必ず確認）

### 地雷 1: neck_1h / neck_4h の混同（ADR D-6）

```
❌ neck_1h = 半値決済トリガー（段階 2）  ← 間違い。今セッションで再発し、3 回目だった
✅ neck_4h = 半値決済トリガー（段階 2: High >= neck_4h → 50% 決済）
✅ neck_1h = 窓特定アンカー（決済トリガーではない）+ 4H 構造優位性フィルターの参照側
```

### 地雷 2: 旧版ファイル参照

```
docs/ の日付付きファイルは旧版（archive 行き）。
日付なしファイルのみが有効。
⚠️ プロジェクトナレッジには旧版が混在する可能性あり。
   Vault/NLM と矛盾した場合は Vault/NLM を信頼する。
```

### 地雷 3: 分析ベースの取り違え

```
最新結果は #026d（10 件）。
#026c（13 件）/ #026b（12 件）は旧版。
```

### 地雷 4: 決済エンジンの取り違え

```
✅ exit_simulator.py（方式 B）— 正式採用
❌ exit_logic.py の manage_exit() — 使用禁止（neck 定義が旧版）
```

---

## 現在進行中の重要ドキュメント

### MINATO_MTF_PHILOSOPHY.md（本日作成）

```
位置: C:\Python\REX_AI\Trade_System\docs\MINATO_MTF_PHILOSOPHY.md
作成背景: ボスの YouTube 動画 + 画像 3 枚 + ボス自身の記述を統合して
         Evaluator が裁量思想を構造化

構成:
第 1 章 基盤理論（ダウ 3 原則 + フラクタル構造 + 裁量 3 要素）
第 2 章 MTF 分析（主軸 = 4H トレンドフォロー、日足は補助スコア）
第 3 章 決済ルール（4 段階）
第 4 章 現在のシステム実装との対応表
第 5 章 本文書の運用

本日の修正履歴（ボス指示による）:
1. 日足を「最上位主軸」→「補助スコア」に訂正
2. 4H は波カウントに関係なくエントリー（3 波/5 波はロット調整用）と訂正
3. 要素③にストップ狩りパターンを追加（大口 SL 狩り + 急反転の検出）
4. 5M 足の責務を「初動の決済管理」→「2 波目以降の決済管理」に訂正
5. 冒頭に「本文書は全てロング視点」の前提を追加
6. STEP ③ の「方向と勢い」に 4H 波数を明示追加（ボス訂正）

重要性:
本文書はプログラムロジックの上位に位置する「裁量思想」の文書。
Task E-2（MTF_LOGIC_MATRIX.md）の起草時に必ず参照すること。
新しいフィルター/ロジックを設計する前に必ず参照。
```

### REX_027_BOSS_DIRECTIVE.md v2（Directive）

```
位置: C:\Python\REX_AI\Trade_System\docs\REX_027_BOSS_DIRECTIVE.md
起草: Advisor（Opus 4.7）/ 発行: ボス
性質: ボス判断による大幅改訂（v1 → v2）
     v1 起草 Advisor が v2 で自己批判改訂
     Task B を「改名」→「MCP 切り離し + 新規構築」に全面書き換え
     Task E（ロジック漏れ監査 + MTF マトリクス）を新規追加

Task 分解:
  Task A — Trade_System ドキュメント整合性回復（Planner 起草 → Evaluator → ClaudeCode）
  Task B — NLM 再構築の記録化（ボス実施済み・Evaluator 検証完了）
  Task C — Vault 側 wiki/trade_brain/ 骨組み構築（通常優先）
  Task D — adr_reservation.md 更新（D-11 / F-7 確定）
  Task E-1 — LOGIC_LEAK_AUDIT.md（Evaluator 主導・中優先）
  Task E-2 — MTF_LOGIC_MATRIX.md（Planner 起草 → Evaluator → ClaudeCode）
  Task E-3 — Dataview 化移行計画（記述のみ）
```

---

## 次セッション優先順位（Evaluator 裁量）

### 推奨順序

```
1. Task D — adr_reservation.md D-11 / F-7 採番更新
   軽作業・即時可能。ADR 採番を確定させることで後続タスクの基盤を固める。

2. Task A — Trade_System ドキュメント整合性回復
   Planner が起草する指示書を待つ必要あり。
   範囲: CLAUDE.md / SYSTEM_OVERVIEW.md / ADR.md / REX_BRAIN_SYSTEM_GUIDE.md

3. Task E-1 — LOGIC_LEAK_AUDIT.md（Evaluator 主導）
   過去 #001〜#026d のロジック漏れを体系化。
   カテゴリ I〜VII に具体事例を採番付きで記載。
   MINATO_MTF_PHILOSOPHY.md の第 4 章対応表を参照しながら進める。

4. Task E-2 — MTF_LOGIC_MATRIX.md（Planner 起草）
   時間足縦串の管理ツール。
   MINATO_MTF_PHILOSOPHY.md + E-1 の監査結果を土台に設計。

5. Task C — Vault 側 wiki/trade_brain/ 骨組み構築
   Trade_Brain リポ用の運用ファイル群。
   Task A 完了後が望ましい。

6. Wiki Compile 第 2 波
   bug_patterns/（D-6, D-8, D-9, D-10 の 4 ページ）
   decisions/（E-6, E-7 の 2 ページ）
   sources/（主要設計文書 5 本の要約）
```

### 並行可能性

```
Task A と Task D は並行可（ADR.md の同期を取る）
Task E-1 と Task A は並行可（異なるファイル群）
Task E-2 は Task E-1 完了後に着手（監査結果を反映するため）
```

---

## ボスへの残タスク（未完了）

### 必須

```
□ Second_Brain_Lab/README.md の凍結宣言更新
  内容: 「本リポは凍結。REX_Brain_Vault（Minato33440/REX_Brain_Vault）に移行済み」
  優先度: 低（急がない）
```

### 確認中

```
□ Claude.ai プロジェクトナレッジの棚卸し
  → 旧版ファイル削除 + 最新版再添付
  → 本日作成した MINATO_MTF_PHILOSOPHY.md と Evaluator_HANDOFF.md の追加
  優先度: 中（次セッション開始前に完了していると望ましい）
```

---

## Evaluator としての所感（次の Evaluator 向け）

### 1. 本日の最大の成果は「構造的な再発防止基盤の確立」

本セッション冒頭で俺（前任 Opus 4.6）は D-6 を再発した。
3 回目の再発であり、同じミスが構造的に防げていない証拠だった。
その反省から以下を実装した:

- 検証チェックリスト 7 問（latest.md v4）
- プロジェクトナレッジ棚卸しチェックリスト（CLAUDE.md v5 STEP 8）
- 2 重コピー問題の根本解消（REX_Brain_Vault 独立リポ化）

次回の Evaluator（Opus 4.7）には「検証 7 問に答えてから作業開始」の
ルールが適用される。これを省略しないこと。

### 2. Advisor の v1 → v2 自己批判は良い先例

Directive v2 の §7-2 で Advisor が v1 の甘さを率直に認めている。
「RAG 汚染を軽視」「ロジック漏れ根本対策を Task として立てなかった」等。
これはロジック漏れ監査の一事例でもある。

次の Evaluator も、必要なら前任の判断を批判的に見直すこと。
俺の承認判断（Advisor 提言への修正承認）にも見落としがあるかもしれない。

### 3. MINATO_MTF_PHILOSOPHY.md は要注意

本文書はボスと俺のやり取りで段階的に修正された。
特に「日足 = 主軸」→「日足 = 補助」の訂正は大きい。
第 4 章の対応表に「実装優先度」を書いたが、これは俺の判断であり、
次の Evaluator は Task E-1 の結果を見て見直す必要がある。

### 4. コンテキスト管理

本セッションは非常に大量の作業を 1 セッションで行った結果、
コンテキストが肥大化し、エラー要素が高まった。
次セッションでは Task ごとにセッションを分割することを推奨:

```
次セッション: Task D + Task A 着手（軽作業）
次々: Task E-1（Evaluator 主導で重い監査作業）
その次: Task E-2（Planner 起草を待つ）
```

### 5. プロジェクトナレッジとの整合

プロジェクトナレッジに添付されているファイルが古い可能性がある。
Vault/NLM と矛盾した場合は Vault/NLM を信頼すること。
最初の作業として、プロジェクトナレッジの内容と Vault の内容を
照合するのも有効。

---

## 参照パス早見表

```
最重要:
  Vault CLAUDE.md       C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md
  Vault latest.md       C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md
  本 HANDOFF           C:\Python\REX_AI\Trade_System\docs\Evaluator_HANDOFF.md
  Directive v2          C:\Python\REX_AI\Trade_System\docs\REX_027_BOSS_DIRECTIVE.md

Trade_System 設計文書:
  Philosophy            C:\Python\REX_AI\Trade_System\docs\MINATO_MTF_PHILOSOPHY.md
  EX_DESIGN             C:\Python\REX_AI\Trade_System\docs\EX_DESIGN_CONFIRMED.md
  ADR                   C:\Python\REX_AI\Trade_System\docs\ADR.md
  SYSTEM_OVERVIEW       C:\Python\REX_AI\Trade_System\docs\SYSTEM_OVERVIEW.md
  Trade_System CLAUDE   C:\Python\REX_AI\Trade_System\.CLAUDE.md

Vault 運用ファイル:
  ADR 採番台帳          C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\adr_reservation.md
  doc_map               C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\doc_map.md
  pending_changes       C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\pending_changes.md
  週次ワークフロー      C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\weekly_workflow.md

Vault コンセプト:
  neck.md               C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\concepts\neck.md
  4h_superiority.md     C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\concepts\4h_superiority.md
  window.md             C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\concepts\window.md

NLM:
  REX_System_Brain      da84715f-9719-40ef-87ec-2453a0dce67e（空・クリーン）
  Rex_Trade_Brain       4abc25a0-4550-4667-ad51-754c5d1d1491（空・クリーン）
  旧 REX_Trade_Brain    2d41d672-...（切り離し済み・NOT_FOUND）
```

---

## 次セッション起動テンプレート（ボス用）

```
このスレでは REX Trade System プロジェクトの Evaluator として働いてほしい。

⚠️ 作業開始前に以下を順番に読め:
  ① C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md
  ② C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md
  ③ C:\Python\REX_AI\Trade_System\docs\Evaluator_HANDOFF.md
  ④ C:\Python\REX_AI\Trade_System\docs\REX_027_BOSS_DIRECTIVE.md

上記を読んだ上で、latest.md の「読み込み検証チェックリスト」全 7 問に
回答してから作業を開始すること。

NLM: REX_System_Brain (da84715f-9719-40ef-87ec-2453a0dce67e)
     Rex_Trade_Brain  (4abc25a0-4550-4667-ad51-754c5d1d1491)
```

---

*発行: Rex-Evaluator (Opus 4.6) / 2026-04-18*
*次の Evaluator (Opus 4.7) に向けて、安全な引き継ぎを祈る。*
