# REX_027_ADVISOR_PROPOSAL.md
# Obsidian Vault 構造設計に関する提言書
# 発行: Advisor（Claude Opus 4.7）
# 宛先: Rex-Evaluator（Opus 4.6）
# 発行日: 2026-04-18
# 対象タスク: REX_027_doc_cleanup_spec（ナレッジシステム環境構築）

---

## 本書の位置づけ

本書は Advisor（Claude Opus 4.7・Claude.ai 側セッション）から、
プロジェクト責任者である Rex-Evaluator（Opus 4.6）に宛てた
**提言書**である。

Advisor は本プロジェクトの実装ライン（Planner / Evaluator / ClaudeCode）
の外側に位置する相談役であり、以下の役割を担う:

- REX_AI\ 配下の複数プロジェクト全体を俯瞰した視点の提供
- 既存システムへの外部視点でのレビューと改善提案
- 新規導入技術（Obsidian / MCP / LLM_Wiki 方式など）の
  既存運用との整合性評価
- Evaluator が最終判断を下す際の判断材料の提供

**本書は決定文書ではない。** Evaluator の承認・修正・却下を経て、
確定事項は ADR F 章および adr_reservation.md に反映される。

---

## 0. 提言のサマリー

**背景**:
#026d 完了により Trade System のコアロジックが数値的に収束した
（PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p / 10件）。
これは「データ整合性が取れている最後の静的点」であり、
以降はフィルター追加・Phase D（出来高）で構造が動的に変化していく。

**提言**:
静的な今のうちに Obsidian Vault を LLM_Wiki 方式の
「自己増殖型ナレッジベース」として立ち上げることを提言する。
以降の変更履歴は全て Vault に積み上がる形となり、
複雑化してからでは失われる基準点を保全できる。

**本書の範囲**:
- Vault 配下のディレクトリ構造確定
- ページ種別・命名規則・YAML フロントマター仕様
- Ingest / Compile / Lint 運用フロー
- ClaudeCode MCP 接続経路の設計
- 既存 docs/ からの移行計画（Phase 分け）

**非対象**:
- NLM ソース追加フロー（既存運用を継続）
- ADR 本文の改訂（本書は構造提言であり内容改訂はしない）
- 凍結ファイルの変更

---

## 1. 現状評価（Advisor 視点）

### 1-1. 既存 Rex Brain System の成熟度

Advisor として既存システムを評価したところ、以下は **既にプロの水準**
に達していると判断する:

| 評価項目 | 現状 | 評価 |
|---|---|---|
| 役割分担（Planner/Evaluator/ClaudeCode） | 確立済み | ◎ |
| 凍結ファイル方針（F-4） | 4ファイル明示 | ◎ |
| ADR 採番予約制 | adr_reservation.md | ◎ |
| NLM 認証切れフォールバック | pending_nlm_sync.md | ○ |
| Lint 3 点チェック | 実装済み | ○ |
| セッション開始プロトコル | 5 分把握設計 | ◎ |
| wrap-up フロー | 7 ステップ定義 | ○ |
| Acceptance Criteria 運用 | Evaluator 管理 | ◎ |

特に「採番衝突が実際に発生（2026-04-15）してから予約制を導入した」
という運用エンジニアリング的な反射神経は高く評価できる。

### 1-2. 現状の欠落（本書が扱う範囲）

既存 REX_BRAIN_SYSTEM_GUIDE.md に定義されている運用は完成しているが、
**運用ファイルのみ**が存在し、**知識ページ本体**が Vault 内に存在しない。

```
現状の Vault:
  wiki/trade_system/doc_map.md          ← メタ情報（何があるか）
  wiki/trade_system/adr_reservation.md  ← 採番管理
  wiki/trade_system/pending_changes.md  ← 変更記録
  wiki/trade_system/pending_nlm_sync.md ← 認証切れフォールバック

欠落している層:
  wiki/trade_system/Concepts/    ← 概念ページ（neck / window / ダウ）
  wiki/trade_system/Entities/    ← エンティティページ（関数・ファイル）
  wiki/trade_system/Patterns/    ← パターンページ（DB / IHS / ASCENDING）
  wiki/trade_system/BugPatterns/ ← バグパターンページ（ADR A〜D を個別化）
  wiki/trade_system/Decisions/   ← 意思決定ページ（ADR E を個別化）
  wiki/trade_system/Sources/     ← 生ソース要約
```

現状は「索引だけあって本棚が空」の状態。
NLM で引けば内容は取得できるが、Vault 側でクロスリンクを張れないため、
ClaudeCode がローカルで設計思考を辿ることができない。

---

## 2. 設計原則（Evaluator 承認事項）

### 原則 1: NLM は「リサーチ・エンジン」、Vault は「構造化記憶」

```
NLM の役割:
  - 大量ソースからの RAG 検索
  - 自然言語クエリ応答
  - ソースの真正性保持（読み取り専用記憶）

Vault の役割:
  - 構造化された設計思考（概念・関係・判断）
  - ClaudeCode が直接 read/write できるローカル記憶
  - クロスリンクによる関連性の可視化
  - Dataview による動的集計
```

両者は競合しない。NLM は source の真正性、Vault は整理された知識。

### 原則 2: 凍結セクション / 拡張可能セクションの区別を Vault にも適用

既存 ADR F-4 のファイル変更ポリシーを Vault にも持ち込む。

```
■ 凍結ページ（内容変更禁止・archived フロントマター付与）
  - Concepts/archived/   ← 仕様凍結された設計原則
  - Decisions/closed/    ← 決定済み ADR（採番確定後）
  - Patterns/baseline/   ← #018 ベースライン時点のパターン

■ 拡張可能ページ
  - Concepts/active/     ← 現在進行中の概念定義
  - Entities/            ← ファイル・関数の仕様（コード変更と同期）
  - BugPatterns/         ← 新バグ発見で追記
```

### 原則 3: LLM が書き、人間は読むだけ（LLM_Wiki 原則）

ミナトは Wiki ページを手書きしない。ClaudeCode（またはこのセッションの
Claude）が Ingest/Compile 時にページを生成・更新する。
ミナトは Obsidian で**読む・グラフを眺める・クエリ結果を確認する**のみ。

**例外**: adr_reservation.md / pending_changes.md など運用ファイルは
ミナトも編集可。

### 原則 4: Source-of-Truth 単一化

```
設計の Source of Truth:
  コード実装     → src/*.py（凍結）
  設計文書       → docs/EX_DESIGN_CONFIRMED.md
  意思決定       → docs/ADR.md
  パラメータ     → CLAUDE.md

Vault の役割:
  上記 4 つから派生した「整理された解釈層」
  Source が更新されたら Vault が追従する（逆ではない）
```

Vault で新たな事実を発明してはならない。Source を解釈・整理するのみ。

---

## 3. Vault ディレクトリ構造（提案）

```
REX_Brain_Vault/
├── wiki/
│   ├── index.md                          # 全ページの一覧カタログ
│   ├── log.md                            # 時系列ログ（ingest/query/lint）
│   │
│   └── trade_system/
│       ├── _RUNBOOK.md                   # Planner/Evaluator 向け運用手順
│       ├── doc_map.md                    # [既存] 設計文書状況
│       ├── adr_reservation.md            # [既存] ADR 採番台帳
│       ├── pending_changes.md            # [既存] 決定済み未反映変更
│       ├── pending_nlm_sync.md           # [既存] NLM 認証切れ待ち
│       │
│       ├── Concepts/                     # 概念ページ
│       │   ├── active/
│       │   │   ├── neck.md               # neck の定義（統一neck原則）
│       │   │   ├── window.md             # 1H窓の構造
│       │   │   ├── dow.md                # ダウ理論の採用範囲
│       │   │   ├── fixed_neck.md         # 固定ネック原則（#025）
│       │   │   └── 4h_superiority.md     # 4H構造優位性（#026d）
│       │   └── archived/
│       │       └── pct_tolerance.md      # PCT方式（廃止・参照用）
│       │
│       ├── Entities/                     # ファイル・関数ページ
│       │   ├── files/
│       │   │   ├── window_scanner.md
│       │   │   ├── exit_simulator.md
│       │   │   ├── swing_detector.md
│       │   │   └── ...
│       │   └── functions/
│       │       ├── scan_4h_events.md
│       │       ├── get_1h_window_range.md
│       │       ├── check_15m_range_low.md
│       │       └── ...
│       │
│       ├── Patterns/                     # 戦略パターン
│       │   ├── active/
│       │   │   ├── double_bottom.md
│       │   │   ├── inverse_head_shoulders.md
│       │   │   └── ascending.md
│       │   └── baseline/
│       │       └── 018_baseline.md       # #018 基準スナップショット
│       │
│       ├── BugPatterns/                  # バグパターン集（ADR A〜D 個別化）
│       │   ├── A_scan_direction/
│       │   │   ├── A-1_window_left_scan.md
│       │   │   ├── A-2_different_wave_bottom.md
│       │   │   ├── A-3_short_lookback.md
│       │   │   ├── A-4_late_bias_1h_sl.md
│       │   │   └── A-5_late_bias_neck.md
│       │   ├── B_api_mismatch/
│       │   ├── C_mplfinance/
│       │   └── D_parameter/
│       │
│       ├── Decisions/                    # 意思決定（ADR E 個別化）
│       │   ├── closed/
│       │   │   ├── E-6_neck_csv_storage.md
│       │   │   └── E-7_limit_order_entry.md
│       │   └── open/                     # 検討中
│       │
│       ├── Sources/                      # 原典ソース要約
│       │   ├── EX_DESIGN_summary.md
│       │   ├── ADR_summary.md
│       │   ├── SYSTEM_OVERVIEW_summary.md
│       │   └── CLAUDE_md_summary.md
│       │
│       ├── Instructions/                 # 指示書のミラー
│       │   ├── REX_025_summary.md
│       │   ├── REX_026a_summary.md
│       │   ├── REX_026b_summary.md
│       │   ├── REX_026c_summary.md
│       │   ├── REX_026d_summary.md
│       │   └── REX_027_summary.md        # 本タスク
│       │
│       └── Handoff/
│           └── latest.md                 # 次セッション引き継ぎプロンプト
│
└── .obsidian/                            # Obsidian 設定
    ├── plugins/
    │   ├── dataview/                     # 必須
    │   └── templater/                    # 推奨（フロントマター自動生成）
    └── hotkeys.json
```

---

## 4. ページ種別と YAML フロントマター仕様

### 4-1. Concept ページ

```yaml
---
type: concept
status: active | archived
category: neck | window | dow | ...
related_files: [window_scanner.py, exit_simulator.py]
related_patterns: [DB, IHS]
introduced_in: "#025"
confirmed_in: "#026a"
superseded_by: ""   # 廃止時に後継ページリンク
last_updated: 2026-04-17
---
```

### 4-2. Entity ページ（ファイル）

```yaml
---
type: entity
entity_kind: file
path: src/window_scanner.py
status: frozen | extensible | new
frozen_version: ""   # 凍結時のみ
last_modified_instruction: "#026d"
depends_on: [swing_detector.py, entry_logic.py]
depended_by: [exit_simulator.py]
---
```

### 4-3. Pattern ページ

```yaml
---
type: pattern
pattern_name: DB | IHS | ASCENDING
status: active | baseline
detection_function: check_15m_range_low
neck_rule: unified_neck
sample_count_026d: 3
win_rate_026d: 0.60
last_updated: 2026-04-17
---
```

### 4-4. BugPattern ページ

```yaml
---
type: bug_pattern
adr_id: A-1 | A-2 | ... | D-10
category: scan_direction | api_mismatch | mplfinance | parameter
severity: critical | high | medium
discovered_in: "#021"
fixed_in: "#022"
fix_complexity: "3 lines"
lesson_keywords: [timing, lookback, neck_selection]
last_updated: 2026-04-14
---
```

### 4-5. Decision ページ

```yaml
---
type: decision
adr_id: E-6 | E-7 | ...
status: open | closed | superseded
decided_at: 2026-04-17
rejected_alternatives: ["A: entry upper cap", "B: pre-neck_1h entry"]
accepted_alternative: "C: limit order method"
decided_by: Minato
approved_by: Rex-Evaluator
rationale_summary: "損切幅の安定化と裁量再現性"
---
```

### 4-6. Source ページ

```yaml
---
type: source
source_file: docs/EX_DESIGN_CONFIRMED.md
nlm_source_id: "2d41d672-..."
version_date: 2026-04-17
summary_generated: 2026-04-18
sync_status: current | stale | superseded
---
```

---

## 5. Dataview クエリ運用例

Obsidian の Dataview プラグインで YAML フロントマターを SQL ライクに集計可能。

### 例 1: #026d 時点でアクティブな concept 一覧

```dataview
TABLE status, introduced_in, confirmed_in
FROM "wiki/trade_system/Concepts"
WHERE type = "concept" AND status = "active"
SORT confirmed_in DESC
```

### 例 2: 未解決 ADR 一覧

```dataview
TABLE severity, discovered_in, fixed_in
FROM "wiki/trade_system/BugPatterns"
WHERE fixed_in = "" OR fixed_in = null
```

### 例 3: 凍結ファイル一覧

```dataview
LIST path
FROM "wiki/trade_system/Entities/files"
WHERE status = "frozen"
```

### 例 4: ADR D カテゴリの最新番号

```dataview
TABLE WITHOUT ID max(adr_id) AS "latest_D"
FROM "wiki/trade_system/BugPatterns/D_parameter"
```

→ adr_reservation.md の採番チェックに利用（既存 Lint-1 の補強）。

---

## 6. 運用フロー（Ingest / Compile / Lint）

### 6-1. Ingest（新規ソース取り込み）

```
契機: 新しい指示書完了 / 新規設計文書作成 / 新バグ発見

手順:
  1. Source を docs/ に配置（既存フロー）
  2. ClaudeCode が Vault の Sources/ に要約ページを生成
  3. ClaudeCode が関連する Concepts / Entities / Patterns を更新
  4. 該当する BugPattern / Decision を追加（必要時）
  5. log.md に ingest エントリーを追記
  6. index.md を再生成

1回の Ingest で触るページ数: 5〜15 ページ（LLM_Wiki 想定通り）
```

### 6-2. Compile（既存ソースからの Wiki 構築）

```
契機: REX_027 本タスク（初回大規模 Compile）

手順:
  1. 既存 docs/ 全ファイルを Sources/ に要約化
  2. ADR.md を BugPatterns/* + Decisions/* に個別ページ化
  3. EX_DESIGN_CONFIRMED.md の設計概念を Concepts/ に抽出
  4. SYSTEM_OVERVIEW.md の依存関係を Entities/ に展開
  5. #025〜#026d の指示書を Instructions/ に要約ミラー
  6. index.md 初期生成
  7. graph view で孤立ページ確認

想定生成ページ数: 60〜80 ページ（初回 Compile）
所要時間: ClaudeCode で 1〜2 セッション（推定）
```

### 6-3. Lint（既存 3 点チェックを拡張）

既存の REX_BRAIN_SYSTEM_GUIDE の Lint-1〜3 に、Vault 構造の
健全性チェックを追加する。

```
Lint-1: ADR 採番整合（既存）
  → Dataview で BugPatterns/D_*/ の max(adr_id) を取得
  → adr_reservation.md と照合

Lint-2: pending_changes 整合（既存）
  → 変更なし

Lint-3: doc_map × NLM 整合（既存）
  → 変更なし

Lint-4: Vault 孤立ページ検出（新設）
  → graph view で inbound link 0 のページを検出
  → 意図的に孤立させたページ（log.md など）以外はフラグ

Lint-5: frontmatter 整合性（新設）
  → 全ページが type フィールドを持つか
  → related_files が実在するか
  → superseded_by のリンク切れチェック

Lint-6: Source-Vault 乖離検出（新設）
  → Sources/ の version_date と docs/ の更新日の比較
  → ズレがあれば Ingest 再実行を提案

Lint-7: 凍結ページの不正変更検出（新設）
  → status: archived | frozen | closed のページの
    last_updated が frontmatter の confirmed_in より後ならフラグ
```

実行タイミング: タスク完了時 + 週次（既存踏襲）

---

## 7. 既存システムとの統合

### 7-1. NLM × Vault の棲み分け

```
ユースケース                      → 使うべきツール
──────────────────────────────────────────────────
大量 PDF/ソースの内容検索         → NLM
「#026d で何が変わった？」        → NLM（自然言語クエリ）
「neck_4h と neck_1h の関係は？」  → Vault の Concepts/
「D カテゴリの最新番号は？」      → Vault の Dataview
「window_scanner.py が依存する    → Vault の Entities/
   ファイルは？」
設計判断で迷った時                → Vault (F章 + Decisions/)
認証切れ時の記録                  → Vault (pending_nlm_sync.md)
```

### 7-2. CLAUDE.md 改訂案（STEP 4 に Vault 明示）

現状の CLAUDE.md STEP 4:
```
STEP 4: 不明点があれば Vault の設計文書を参照
         パス: C:\Python\REX_AI\REX_Brain_Vault\
         または @notebooklm-mcp にクエリ
```

改訂提案:
```
STEP 4a (概念・関係): Vault の Concepts/ または Entities/ を参照
STEP 4b (過去判断・バグ): Vault の BugPatterns/ または Decisions/ を参照
STEP 4c (大量ソースからの検索): @notebooklm-mcp にクエリ
STEP 4d (迷ったら): wiki/trade_system/_RUNBOOK.md を参照
```

### 7-3. wrap-up フロー統合

既存 STEP 1〜7 に Vault 更新を追加する。

```
既存:
  STEP 1: wiki/log.md に追記
  STEP 2: pending_changes.md 更新
  STEP 3: adr_reservation.md 更新
  STEP 4: handoff/latest.md 更新
  STEP 5: NLM ソース追加
  STEP 6: Second_Brain_Lab に push
  STEP 7: Claude.ai プロジェクトに手動アップロード

追加提案:
  STEP 2.5: Vault Ingest 実行
            - 今日触れた概念・ファイル・判断のページを更新
            - 新規 BugPattern/Decision があれば個別ページ作成
            - index.md 再生成
  STEP 4.5: Vault Lint 実行（Lint-4〜7）
            - 孤立ページ・frontmatter 不整合・Source 乖離をチェック
  STEP 6.5: Vault を Trade_System リポ（または別リポ）に push
```

---

## 8. ClaudeCode MCP 接続設計

### 8-1. 接続経路の二重化

```
ClaudeCode → MCP → Vault アクセス経路

経路 A: filesystem MCP
  用途: Vault ファイルの直接 read/write
  メリット: ファイル単位で高速・確実
  デメリット: ページ間クエリは自前実装

経路 B: notebooklm-mcp + Vault ソース同期
  用途: Vault のソースを NLM にも同期して RAG 検索
  メリット: 自然言語クエリ
  デメリット: 同期ラグ・NLM 認証依存

推奨: 経路 A をメインに使い、経路 B は補助
```

### 8-2. filesystem MCP 許可パス設定（提案）

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\Setona\\Desktop",
        "C:\\Users\\Setona\\Downloads",
        "C:\\Python\\REX_AI\\REX_Brain_Vault"
      ]
    }
  }
}
```

### 8-3. ClaudeCode による書き込み制限

ClaudeCode が Vault に自動書き込みできる範囲を明示する。

```
■ ClaudeCode が自動書き込み可能
  - wiki/log.md（追記のみ）
  - wiki/trade_system/Sources/*.md
  - wiki/trade_system/Instructions/*.md
  - wiki/trade_system/Entities/files/*.md
  - wiki/trade_system/Entities/functions/*.md

■ ClaudeCode は提案のみ（ミナト/Evaluator 承認後に書き込み）
  - wiki/trade_system/Concepts/*
  - wiki/trade_system/Decisions/*
  - wiki/trade_system/BugPatterns/*（新規 ADR 時）
  - wiki/trade_system/adr_reservation.md
  - wiki/trade_system/pending_changes.md

■ ClaudeCode は書き込み禁止
  - */archived/*
  - */closed/*
  - */baseline/*
  - .obsidian/（Obsidian 設定）
```

---

## 9. 移行計画（Phase 分け）

### Phase 1: 骨組み構築（REX_027 本タスク範囲・推定 1 セッション）

```
□ ディレクトリ構造の作成（空ディレクトリ含む）
□ _RUNBOOK.md の作成
□ index.md / log.md の初期化
□ テンプレートファイルの配置（.obsidian/templates/）
□ filesystem MCP の Vault パス追加
□ CLAUDE.md の STEP 4 改訂
```

Acceptance: ディレクトリツリーが本提案通り / Obsidian で開ける / 
ClaudeCode から filesystem MCP で read 可能。

### Phase 2: Sources 要約（推定 1 セッション）

```
□ docs/EX_DESIGN_CONFIRMED.md → Sources/EX_DESIGN_summary.md
□ docs/ADR.md → Sources/ADR_summary.md
□ docs/SYSTEM_OVERVIEW.md → Sources/SYSTEM_OVERVIEW_summary.md
□ CLAUDE.md → Sources/CLAUDE_md_summary.md
□ docs/PLOT_DESIGN_CONFIRMED-2026-3-31.md → Sources/PLOT_DESIGN_summary.md
```

Acceptance: 各 Source ページが frontmatter 完備 / 
sync_status: current で初期化。

### Phase 3: BugPatterns / Decisions 個別化（推定 1 セッション）

```
□ ADR.md の A-1〜A-5 を BugPatterns/A_scan_direction/*.md に展開
□ ADR.md の B-1〜B-3 を BugPatterns/B_api_mismatch/*.md に展開
□ ADR.md の C 統合を BugPatterns/C_mplfinance/*.md に展開
□ ADR.md の D-1〜D-10 を BugPatterns/D_parameter/*.md に展開
□ ADR.md の E-1〜E-7 を Decisions/closed/*.md に展開
```

Acceptance: 全ページが frontmatter 完備 / 
adr_reservation.md の台帳と照合一致 / Dataview クエリが正常動作。

### Phase 4: Concepts / Entities / Patterns 生成（推定 1〜2 セッション）

```
□ Concepts/active/neck.md, window.md, dow.md, fixed_neck.md, 4h_superiority.md
□ Entities/files/*.md（src/ 配下の全 .py に対応）
□ Entities/functions/*.md（主要関数）
□ Patterns/active/{DB, IHS, ASCENDING}.md
□ Patterns/baseline/018_baseline.md
```

Acceptance: graph view で主要ページがハブ化 / 孤立ページ < 5 / 
Concepts ↔ Entities の相互リンクが張られている。

### Phase 5: Lint 拡張と運用開始（推定 0.5 セッション）

```
□ Lint-4〜7 のチェックスクリプト（Python or Dataview）作成
□ wrap-up フローに Vault Ingest を組み込み
□ 初回 Lint 実行・問題点解消
□ REX_BRAIN_SYSTEM_GUIDE.md の改訂
```

Acceptance: Lint 7 項目全て pass / wrap-up 時に Vault 更新が自動記録される。

---

## 10. Acceptance Criteria（全 Phase 完了時）

```
□ Vault ディレクトリ構造が本提案通り構築されている
□ 既存 docs/ の主要 10 文書が Vault 内に対応ページを持つ
□ ADR.md の全エントリー（A-1〜A-5, B-1〜B-3, C, D-1〜D-10, E-1〜E-7）が
   個別ページ化されている
□ 全ページが type フィールドを含む YAML frontmatter を持つ
□ Dataview クエリ（本提案例 1〜4）が正常動作する
□ ClaudeCode が filesystem MCP 経由で Vault を read/write できる
□ CLAUDE.md の STEP 4 が改訂されている
□ wrap-up フローに Vault Ingest が統合されている
□ Lint-1〜7 全てが pass する
□ graph view で孤立ページ（意図的除外を除く）が 0
□ #026d 時点の Trade System 設計思想が Vault から完全に復元可能
  （= 新セッションで Vault だけ読めば #026d まで把握できる）
```

---

## 11. リスクと対策

| リスク | 影響 | 対策 |
|---|---|---|
| 移行中の情報断絶 | 中 | Phase 1〜5 を分離し、各 Phase 完了時に Acceptance で検証 |
| ClaudeCode の誤書き込み | 高 | 書き込み許可範囲を明示（§8-3）/ archived/closed は書込禁止 |
| Vault と docs/ の乖離 | 中 | Lint-6（Source-Vault 乖離検出）で定期チェック |
| 運用負荷増 | 低 | wrap-up フローに統合して自動化 / ミナトの手作業は増やさない |
| Dataview プラグイン依存 | 低 | Obsidian 標準機能で代替可（grep ベース fallback） |
| 初回 Compile のトークン消費 | 中 | Phase 分けで 1 セッションあたり 15 ページ程度に制限 |
| graph view の視認性悪化 | 低 | 原典ソースへの inbound link 集中を避ける設計 |

---

## 12. Advisor として検討し却下した選択肢

### 却下案 1: Vault を docs/ に統合して単一 Markdown ツリーとする

**理由**:
- Obsidian の Dataview / graph view / link 機能が活かせない
- docs/ は凍結方針のファイルが多く、Vault の Ingest 更新と衝突する
- NLM 側との棲み分けが不明瞭になる

### 却下案 2: ADR.md をそのまま保持し、個別ページ化しない

**理由**:
- Dataview クエリが使えず、採番整合 Lint が手動のまま
- 新 ADR 追加時に既存セクションの更新で衝突が起きやすい
- グラフ可視化ができず、関連性が見えない

### 却下案 3: Vault を完全新規リポとして分離

**理由**:
- Trade_System と密結合しているのに別リポにするのは管理負荷増
- 既存の CLAUDE.md / GitHub 運用との統合コストが高い
- ただし、Phase 5 以降で Vault が自律的に成長してから分離検討の余地あり
  （将来オプション）

---

## 13. Evaluator 承認ポイント（決定事項一覧）

本提案を進めるために Evaluator の承認が必要な項目:

```
承認項目 1: §2 設計原則 4 項目
            （NLM/Vault 棲み分け・凍結適用・LLM が書く・Source 単一化）
承認項目 2: §3 ディレクトリ構造案
承認項目 3: §4 YAML frontmatter 仕様（6 種のページ種別）
承認項目 4: §6 Ingest/Compile/Lint フロー
承認項目 5: §7-2 CLAUDE.md STEP 4 改訂案
承認項目 6: §7-3 wrap-up フロー統合
承認項目 7: §8-3 ClaudeCode 書き込み許可範囲
承認項目 8: §9 Phase 分け移行計画
承認項目 9: §10 Acceptance Criteria
承認項目 10: REX_027 を Phase 1 のみの範囲とするか全 Phase かの決定

その他 Evaluator 裁量:
  - Dataview 以外の Obsidian プラグイン利用可否
  - Vault の git 管理方針（Trade_System リポ配下 or 独立リポ）
  - Obsidian Web Clipper 等の補助ツール導入
```

---

## 14. 本提案の位置づけと次のアクション

本提言が採択された場合、Evaluator は以下を発行することを提案する:

```
1. adr_reservation.md に F-7（Vault 構造標準化）を予約エントリーとして記録
2. ADR.md の F 章に「F-7. Vault 構造標準化」を追記
3. pending_changes.md に「REX_027 Vault 構築」を 🔴 実装中 で記録
4. REX_027_doc_cleanup_spec.md の正式指示書を Planner が起草
   （本書の §9 Phase 分けを基礎とする）
```

---

## 15. Advisor 所感（Evaluator 向け補足）

Advisor として率直な所感を記す:

1. 既存 Rex Brain System の完成度は非常に高い。本書の提言は
   「ゼロから新規構築」ではなく「既に堅固な運用基盤の上に
   Wiki 層を追加する」もの。既存運用を壊す意図は一切ない。

2. タイミングとして #026d 完了直後が最適である理由は、
   コアロジックが数値的に収束しており、Wiki 化の基準点として
   最も安定しているため。以降のフィルター追加・Phase D 導入で
   構造が動的化すると、Wiki 化の作業コストは数倍に増える。

3. 本書で提案する Phase 1 のみ（骨組み構築）でも、
   以降の Ingest 運用は可能。全 Phase を REX_027 の
   範囲とするか、段階的に進めるかは Evaluator の裁量。

4. ClaudeCode の書き込み許可範囲（§8-3）は特に厳密に
   Evaluator の承認が必要。誤書き込みによる archived/closed
   ページの破壊は致命的なので、Phase 1 時点で許可パスを
   明示的に設定することを強く推奨する。

5. 本提案は Claude.ai 側セッション（Advisor: Opus 4.7）で
   起草された。ローカル側 ClaudeCode による実装時には、
   本書を CLAUDE.md 経由で参照することを想定している。

---

*提言者: Advisor (Claude Opus 4.7)*
*発行: 2026-04-18*
*宛先: Rex-Evaluator (Opus 4.6)*
*次のアクション: Evaluator による項目別承認 / Planner による REX_027 指示書起草*
