# REX 指示書 #027 — 設計文書整理・完全版作成
# 発行: Rex（設計責任者）→ Rex-Planner（Sonnet）
# 承認: ボス（2026-04-17）
# 対象: Claude.ai アプリ Plannerスレ（ClaudeCodeではない）
# think hard

---

## 目的

#026シリーズ完了を受けて設計文書を現状に同期させる。
ClaudeCodeが「docs/の旧版を誤参照する」リスクを物理的に排除し、
NLMのソース精度を最新状態に引き上げる。

---

## 前提確認（作業開始前に必ず実行）

```
1. NLM認証チェック（notebook_list を試行）
2. wiki/trade_system/doc_map.md を読む
3. wiki/trade_system/pending_changes.md を読む
4. docs/ のファイル一覧を把握する
```

**現在のdocs/に存在する旧版ファイル（整理対象）:**
```
EX_DESIGN_CONFIRMED-2026-3-31.md   ← #025完了版・#026で更新必要
ADR_APPENDIX_DRAFT_2026-04-15.md   ← 追記ドラフト・本体統合後に archive
SYSTEM_OVERVIEW 2026-3-26.md       ← exit_simulator未反映・更新必要
ADR-2026-04-14_2_2.md              ← D-8～D-10/E-7未統合・Evaluatorが更新
```

**整理不要（そのまま有効）:**
```
PLOT_DESIGN_CONFIRMED-2026-3-31.md ← 変更なし・有効
REX_BRAIN_SYSTEM_GUIDE.md          ← v2有効
```

---

## Phase A — docs/ 旧版アーカイブ

### A-1. logs/docs_archive/ ディレクトリ作成

```bash
# Trade_System リポ内に作成
mkdir -p logs/docs_archive
```

### A-2. 旧版ファイルを archive に移動

filesystem MCPで以下を実行（コピーではなく移動）:

```
移動対象:
  docs/EX_DESIGN_CONFIRMED-2026-3-31.md
    → logs/docs_archive/EX_DESIGN_CONFIRMED-2026-3-31.md

  docs/SYSTEM_OVERVIEW 2026-3-26.md
    → logs/docs_archive/SYSTEM_OVERVIEW-2026-3-26.md
    （スペースをハイフンに変換）

  docs/ADR_APPENDIX_DRAFT_2026-04-15.md
    → logs/docs_archive/ADR_APPENDIX_DRAFT_2026-04-15.md
    （ADR本体統合完了後に移動・Evaluator作業待ち）
```

⚠️ `ADR-2026-04-14_2_2.md` はEvaluatorが新ADR.mdに統合するまでdocs/に残す。
⚠️ archive移動後は docs/ に `EX_DESIGN_CONFIRMED.md`（新版）のみ残る状態にすること。

### A-3. 完了条件

```bash
# docs/ 直下の有効設計文書が以下のみであること
ls docs/*.md
# 期待値:
#   docs/EX_DESIGN_CONFIRMED.md       ← 新版（Phase Bで作成）
#   docs/ADR-2026-04-14_2_2.md        ← Evaluator統合待ち
#   docs/PLOT_DESIGN_CONFIRMED-2026-3-31.md
#   docs/REX_BRAIN_SYSTEM_GUIDE.md
```

---

## Phase B — 新 EX_DESIGN_CONFIRMED.md 完全版作成

### B-1. ベースとなる情報源

以下を全て読んでから作成すること:

```
1. docs/EX_DESIGN_CONFIRMED-2026-3-31.md（旧版・構造を継承）
2. wiki/handoff/latest.md（#026d確定パラメータ）
3. Trade_System/.CLAUDE.md（確定パラメータシ・neck定義・決済ロジック）
4. NLMクエリ: 「#026シリーズで変更・確定した設計要素をまとめて」
```

### B-2. 新版に必ず反映する差分

**エントリーロジック変更（#026a～d）:**
```
neck定義の統一（全TF）:
  旧: TFごとにバラバラ
  新: neck = sh_before_sl.iloc[-1]（統一neck原則）

エントリー方式変更（#026c）:
  旧: 実体越え（High > neck_15m）
  新: 指値方式（ENTRY_OFFSET_PIPS = 7.0）
  条件: 5M High >= neck_15m + 7pips で指値約定

4H構造優位性フィルター追加（#026d）:
  条件: neck_4h >= neck_1h
  SKIPしたエントリーは window_scan_entries.csv に SKIP(4H優位性なし) で記録

1H Swing粒度変更（#026a-v2）:
  旧: N_1H_SWING = 2
  新: N_1H_SWING = 3
```

**決済ロジック変更（#026b）:**
```
旧: exit_logic.py の manage_exit()
新: exit_simulator.py の方式B（独立運用）
  ⚠️ exit_logic.py は凍結保持・参照・呼び出し禁止

4段階決済（方式B）:
  初動SL: 15M ダウ崩れ → 全量損切
  段階1:  5M ダウ崩れ → 全量決済（neck_4h未到達時）
  段階2:  High >= neck_4h → 50%決済 + 残りストップを建値移動
  段階3:  1H Close > 4H SH確定後 → 15Mダウ崩れで残り全量決済
```

**neck用途定義（#026a/b/c）:**
```
neck_15m — エントリートリガー（指値の基準値）
neck_1h  — 窓特定アンカー（4H優位性フィルター基準値）
neck_4h  — 半値決済トリガー（段階2）+ 4H優位性フィルター対象値
```

**確定パラメータ（#026d時点）:**
```python
DIRECTION_MODE      = 'LONG'
ALLOWED_PATTERNS    = ['DB', 'ASCENDING', 'IHS']
ENTRY_OFFSET_PIPS   = 7.0
MIN_4H_SWING_PIPS   = 20.0
LOOKBACK_15M_RANGE  = 50
MAX_REENTRY         = 1
PIP_SIZE            = 0.01
N_1H_SWING          = 3
WINDOW_1H_PRE       = 20
WINDOW_1H_POST      = 10
PRICE_TOL_PIPS      = 20.0
PLOT_PRE_H          = 25
PLOT_POST_H         = 40
```

### B-3. ファイル命名規則

```
docs/EX_DESIGN_CONFIRMED.md
（日付なし・常に「現在の最新版」として上書き運用）
```

⚠️ 旧版は Phase A で archive 済みのため、docs/ に1ファイルのみが正しい状態。

### B-4. 完了条件

```
□ docs/EX_DESIGN_CONFIRMED.md が作成されている
□ #026a～d の全変更点が反映されている
□ #018ベースライン情報が保持されている（比較のため）
□ 旧版（-2026-3-31）が docs/ から消えている
```

---

## Phase C — 新 SYSTEM_OVERVIEW.md 作成

### C-1. ベース情報源

```
1. docs/SYSTEM_OVERVIEW 2026-3-26.md（旧版・構造継承）
2. Trade_System リポの src/ ファイル一覧（filesystem MCPで確認）
3. NLMクエリ: 「exit_simulator.pyはどのような役割か？」
```

### C-2. 旧版からの変更点

```
追加するファイル:
  src/exit_simulator.py — 方式B決済エンジン（#026b新設・正式採用）

凍結ステータス更新:
  src/backtest.py       — #018凍結（変更なし）
  src/entry_logic.py    — #018凍結（変更なし）
  src/exit_logic.py     — #009凍結（⚠️ exit_simulator.pyに移行済み）
  src/swing_detector.py — #020凍結（変更なし）

拡張可能ファイル更新:
  src/window_scanner.py — #026d最新（4H優位性フィルター追加）
  src/plotter.py        — 変更なし
  src/structure_plotter.py — 変更なし
```

### C-3. ファイル命名規則

```
docs/SYSTEM_OVERVIEW.md
（日付なし・常に最新版）
```

### C-4. 完了条件

```
□ docs/SYSTEM_OVERVIEW.md が作成されている
□ exit_simulator.py が正しく記載されている
□ 凍結ファイルの理由が明記されている
□ 旧版（2026-3-26）が archive に移動されている
```

---

## Phase D — NLM ソース更新

Phase B/C 完了後に実行する。

### D-1. 新規ソース追加

```
NLM ノートブック: REX_Trade_Brain
ID: 2d41d672-f66f-4036-884a-06e4d6729866

追加対象（Phase B/C 完了後）:
  1. docs/EX_DESIGN_CONFIRMED.md（新版）
  2. docs/SYSTEM_OVERVIEW.md（新版）

コマンド:
  notebooklm-mcp: source_add
    file_path: C:\Python\REX_AI\Trade_System\docs\EX_DESIGN_CONFIRMED.md
    source_type: file

  notebooklm-mcp: source_add
    file_path: C:\Python\REX_AI\Trade_System\docs\SYSTEM_OVERVIEW.md
    source_type: file
```

### D-2. 旧版ソース処理

```
以下は陈藴化済み・削除を検討:
  EX_DESIGN_CONFIRMED-2026-3-31.md（初回Ingestタsource_id未記録）
  SYSTEM_OVERVIEW 2026-3-26.md（source_id: c5ed4a03）

⚠️ NLMのソース削除はPlannerが判断せずEvaluatorに確認すること
   削除ではなく「新版で上書き」の運用でもよい
```

### D-3. doc_map.md 更新

追加完了後に以下を更新:
```
wiki/trade_system/doc_map.md
  NLM投入済みソーステーブルに新エントリーを追加
  旧版の状態を「⚠️ 陈藴化タarchive済み」に変更
```

---

## Phase E — pending_changes.md / log.md 更新

### E-1. pending_changes.md

各Phaseの完了に合わせてステータスを更新:
```
docs/旧版整理     → ✅ 完了（Phase A完了時）
新EX_DESIGN完全版 → ✅ 完了（Phase B完了時）
新SYSTEM_OVERVIEW → ✅ 完了（Phase C完了時）
```

### E-2. log.md に追記

```
## [2026-04-17] #027 設計文書整理・完全版作成

### Phase A: docs/旧版アーカイブ
- EX_DESIGN_CONFIRMED-2026-3-31.md → logs/docs_archive/ 移動
- SYSTEM_OVERVIEW 2026-3-26.md → logs/docs_archive/ 移動

### Phase B: 新EX_DESIGN_CONFIRMED.md 作成
- docs/EX_DESIGN_CONFIRMED.md 作成（#026a～d全変更反映）
- NLM投入完了（source_id: [取得した値]）

### Phase C: 新SYSTEM_OVERVIEW.md 作成
- docs/SYSTEM_OVERVIEW.md 作成（exit_simulator.py追加）
- NLM投入完了（source_id: [取得した値]）
```

---

## wrap-up（全Phase完了後）

```
□ wiki/log.md に完了記録を追記
□ wiki/trade_system/pending_changes.md を全✅に更新
□ wiki/trade_system/doc_map.md を更新
□ wiki/handoff/latest.md を更新（#027完了・#028待ち状態に）
□ Second_Brain_Lab に GitHub push
□ Trade_System に GitHub push（docs/の変更）
□ Evaluatorに「Phase A～C完了・ADR統合作業依頼」を報告
```

---

## Evaluator への引き渡し事項（Planner完了後）

Planner作業完了後、Evaluatorスレに以下を連絡すること:

```
【Evaluator作業依頼】
Phase A～C完了。以下をお願いしたい。

1. 新ADR.md完全版作成
   - ADR-2026-04-14_2_2.md をベースに
   - ADR_APPENDIX_D8-D10_E7の内容（D-8/D-9/D-10/E-7）を本体統合
   - docs/ADR.md として保存（日付なし）

2. NLM投入
   - docs/ADR.md を source_add
   - 旧版（ADR-2026-04-14_2_2.md）の扱いをご判断ください

3. 要望8: 3階層CLAUDE.md棲わ分けドキュメント化
   - ~/.claude/CLAUDE.md（グローバル）
   - Trade_System/CLAUDE.md（プロジェクト）
   - REX_Brain_Vault/CLAUDE.md（Vault）
   の棲わ分け原則をSYSTEM_GUIDEまたはVault CLAUDE.mdに明記
```

---

## 注意事項

```
⚠️ docs/ のファイルを「編集」しない。不変原則。
   → 旧版はarchiveに移動・新版を新規作成する

⚠️ ADR-2026-04-14_2_2.md はEvaluator作業完了まで docs/ に残す

⚠️ NLMソース削除はEvaluatorに確認してから実行

⚠️ GitHub push時は git pull を必ず先に実行
   （ローカルとGitHub MCP両方からpushが発生するため）
```

---

## 完了基準（全Phase）

```
□ docs/ に旧版ファイルが残っていない
□ docs/EX_DESIGN_CONFIRMED.md が#026d反映済みで存在する
□ docs/SYSTEM_OVERVIEW.md が exit_simulator.py反映済みで存在する
□ NLM に新版 2ファイルが投入済み
□ doc_map.md が最新状態に更新されている
□ pending_changes.md の 🔴 項目がすべて ✅ になっている
□ Evaluatorへの引き渡し連絡が完了している
```

---

*発行: Rex（設計責任者）/ 2026-04-17*
*次の指示書番号: #028（Evaluator ADR統合完了後）*
