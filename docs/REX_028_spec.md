# REX_028_spec.md — Phase 1: src/ 棚卸し・分類

**発行**: Rex-Evaluator (Opus 4.7) / 2026-04-19
**実施担当**: Rex-Evaluator（単独・コード生成なし）
**思考フラグ**: think harder（判断を伴う分類作業）
**前提**: Trade_System コアロジック #026d 凍結状態・MTF_INTEGRITY_QA 完了

---

## 1. 背景と位置づけ

### 1-1. なぜこの作業が必要か

2026-04-19 セッションで、ボスが以下の原則を言明した:

> 「基本に戻れるシンプルな土台」とはロジックだけでなくシステムそのものがそうでなければならない

これは `MINATO_MTF_PHILOSOPHY.md` の原則α（シンプルな土台の保守）を
**ファイルシステム・ディレクトリ構造にも適用する**ことを意味する。

現状の `src/` は 27 ファイル構成で、以下の問題を抱えている:

- `dashboard.py` — **0バイトの空ファイル**
- `Simple_Backtest.py` — **53KB だが docs/ のどこにも記載なし**
- `chat.py` `news.py` `market.py` `regime.py` `history.py` — 戦略コアと無関係な名前群
- 27 ファイル中、#026d コアロジックは 10 ファイル（183KB）のみで、残り 17 ファイル（126KB超）は用途不明または派生

この状態のまま Obsidian Wiki + NLM RAG 蓄積を開始すると、**綺麗な新 NLM に汚染データが混入する**リスクがある。

### 1-2. 構造再編の Phase 分解（全体像）
Phase 1: 棚卸しと分類          ← 本指示書
→ src/ の 27 ファイルを CORE / ORPHAN / TEST / UTIL / DEAD に分類
→ 物理移動は禁止（分類するだけ）
→ 成果物: src_inventory.md
Phase 2: archive 移設          ← 次々スレ予定
→ 死んだコード・用途不明ファイルを src/_archive/ へ隔離
→ 削除せず git mv で履歴保全
Phase 3: 責務別ディレクトリ化   ← その後
→ src/core/ / src/viz/ / src/scan/ / src/tests/ に階層化
→ #026d バックテスト再実行で数値不変を完了条件
Phase 4: 裁量整合版の実装訂正   ← REX_029 以降
→ stage2 建値移動削除（🤖 創作混入 D-12）
→ stage3 1H実体確定削除（🤖 創作混入 D-13）

本指示書は **Phase 1 のみ**を扱う。Phase 2 以降は Phase 1 完了後に別指示書で起草する。

---

## 2. Phase 1 の目的・スコープ

### 2-1. 目的

`src/` 配下の全ファイルを以下の 5 分類に振り分け、根拠と共に記録する:

| 分類 | 定義 | Phase 2 での扱い |
|---|---|---|
| **CORE** | #026d バックテストで直接使用されるコアロジック | src/core/ に移設（Phase 3） |
| **VIZ** | 可視化・プロット生成ファイル | src/viz/ に移設（Phase 3） |
| **SCAN** | 構造検証・スキャン系補助ファイル | src/scan/ に移設（Phase 3） |
| **TEST** | テストコード・整合性検証コード | src/tests/ に移設（Phase 3） |
| **UTIL** | 汎用ユーティリティ | src/ 直下維持または src/utils/ |
| **ORPHAN** | 用途不明・docs に記載なし・要ボス確認 | QA 項目として集約 |
| **DEAD** | 空ファイル・初期テストコード・明らかに不要 | _archive/ 直行候補 |

### 2-2. スコープ

**対象**: `src/*.py` 全 27 ファイル

**対象外**:
- `src/_archive/`（まだ存在しない・Phase 2 で作成）
- `logs/`, `docs/`, `data/`, `tests/`（リポジトリ直下の tests/ があれば別途扱う）

### 2-3. 原則

1. **物理移動禁止**: Phase 1 では git mv も rm も一切行わない
2. **削除判断の留保**: DEAD 分類でも削除は Phase 2 でボス承認後
3. **不明は ORPHAN**: 判断に確信がなければ ORPHAN に分類しボス確認
4. **Evaluator 単独作業**: Planner / ClaudeCode への指示書起草は不要（本作業は判断のみ）

---

## 3. 判断基準マトリクス

各ファイルについて、以下の 5 軸で評価する:

### 3-1. 軸 1: 凍結指定の有無

既知の凍結ファイル（EX_DESIGN_CONFIRMED.md §6 より）:
backtest.py       凍結 #018
entry_logic.py    凍結 #018
exit_logic.py     凍結 #009・呼び出し禁止
swing_detector.py 凍結 #020
→ これらは **CORE 確定**

### 3-2. 軸 2: #026d バックテストでの直接使用

拡張可能・#026d 最新として docs に記載:
window_scanner.py  拡張可能（4H優位性フィルター追加・12カラムCSV出力）
exit_simulator.py  方式B・正式採用
plotter.py         拡張可能
structure_plotter.py 拡張可能
→ これらは **CORE または VIZ 確定**

### 3-3. 軸 3: docs/ への記載状況

以下の docs を grep して記載状況を確認:
- `docs/EX_DESIGN_CONFIRMED.md`（§6 ファイル構成）
- `docs/ADR.md`（各 ADR 内の参照）
- `docs/MTF_INTEGRITY_QA.md`（関連記載）
- `docs/REX_027_BOSS_DIRECTIVE.md`

**判定**:
- 記載あり + 機能明確 → 分類確定
- 記載なし → **ORPHAN** 候補

### 3-4. 軸 4: import 関係の解析

各ファイルについて:
- **被 import**: 他のファイルから import されているか（CORE ロジックの一部か）
- **import 先**: 何を import しているか（依存関係の把握）

被 import がゼロかつ docs 記載なし → **DEAD** 候補

### 3-5. 軸 5: ファイルサイズ・最終更新日

- **0 バイト** → **DEAD** 確定（`dashboard.py`）
- **極小（1KB未満）+ docs 記載なし** → **DEAD** 候補（`hello_rex.py`, `print_signals_analysis.py`）
- **巨大（50KB超）+ docs 記載なし** → **ORPHAN 最優先**（`Simple_Backtest.py`）

---

## 4. 作業手順

### STEP 1: 既知分類の確定（判断不要・最速処理）

以下 4 ファイルは CORE 確定として記録:
backtest.py / entry_logic.py / exit_logic.py / swing_detector.py

以下 2 ファイルも CORE 確定:
window_scanner.py / exit_simulator.py

以下 3 ファイルは VIZ 確定:
plotter.py / structure_plotter.py / plot_scan_results.py

以下 1 ファイルは SCAN 確定:
base_scanner.py

以下 3 ファイルは TEST 確定:
test_1h_coincidence.py / test_fetch_30days_multi.py / verify_4h1h_structure.py

以下 1 ファイルは UTIL 確定:
utils.py

→ ここまでで 14 ファイル分類完了

### STEP 2: DEAD 候補の即時確定
dashboard.py          0バイト → DEAD
hello_rex.py          741B・初期テスト → DEAD 候補
print_signals_analysis.py  720B・単独実行スクリプト → DEAD 候補

→ ここまでで 17 ファイル

### STEP 3: ORPHAN 候補の精査（本 Phase の主作業）

残り 10 ファイルを以下のフォーマットで精査:
ファイル名: Simple_Backtest.py
サイズ: 53,332B
先頭 50 行の内容: [bash_tool で取得]
被 import: [grep で調査]
docs 記載: [grep で調査]
推定用途: [Evaluator の判断]
分類: ORPHAN / DEAD / 他カテゴリ
ボス確認事項: [あれば]

対象 10 ファイル:
Simple_Backtest.py       53,332B  ← 最優先調査
data_fetch.py            13,955B
daily_report_parser.py   11,165B
signals.py               11,842B
track_trades.py          10,104B
market.py                 5,553B
regime.py                 5,083B
news.py                   4,319B
chat.py                   3,461B
history.py                2,370B
forecast_simulation.py    2,387B

### STEP 4: `src_inventory.md` 起草

`docs/src_inventory.md` として成果物を作成。フォーマットは §5 参照。

### STEP 5: ボスへの QA 集約

ORPHAN 分類のファイルについて、ボスに一括確認する質問リストを作成:
Q1: Simple_Backtest.py（53KB）は何のために存在するか？
Q2: data_fetch.py は #026d で使われているか？
...

ボスから「archive で良い」の回答を得たファイルは、Phase 2 で _archive/ 移設対象に昇格。

### STEP 6: ADR 採番（D-12/D-13/E-8/F-8 の正式記述）

Phase 1 完了と同時に ADR.md に以下を正式追記:
- **D-12**: stage2 建値移動の 🤖 創作混入確定（認識の固定・実装訂正は Phase 4）
- **D-13**: stage3 1H実体確定の 🤖 創作混入確定（認識の固定・実装訂正は Phase 4）
- **E-8**: src/ 構造再編アプローチ（Phase 1-4）
- **F-8**: 原則α/β/γ（裁量思想の3原則・設計方針ガイド）

ADR 本文の内容は `MTF_INTEGRITY_QA.md` と本指示書を参照して起草する。

### STEP 7: MTF_INTEGRITY_QA.md への Phase 1 完了セクション追記

日付見出しで「2026-MM-DD Phase 1 完了セッション」を追記:
- 分類結果サマリ
- ボス QA 結果
- Phase 2 への引き渡し事項

---

## 5. 成果物: `src_inventory.md` フォーマット

````markdown
# src_inventory.md — src/ ファイル棚卸し結果

**起草**: Rex-Evaluator (Opus 4.x) / YYYY-MM-DD
**Phase**: REX_028 Phase 1（棚卸し・分類）
**関連**: REX_028_spec.md / MTF_INTEGRITY_QA.md / ADR E-8

---

## 分類サマリ

| 分類 | ファイル数 | 総サイズ |
|---|---|---|
| CORE | N | N KB |
| VIZ | N | N KB |
| SCAN | N | N KB |
| TEST | N | N KB |
| UTIL | N | N KB |
| ORPHAN | N | N KB |
| DEAD | N | N KB |
| **合計** | 27 | 約 310 KB |

---

## CORE 分類

### backtest.py
- サイズ: 31,725B
- 状態: 凍結 #018
- 被 import: [調査結果]
- docs 記載: EX_DESIGN §6 / ADR 複数箇所
- Phase 3 移設先: src/core/backtest.py
- 備考: PF 5.32 ベースライン（LONG+★★★ 20件）再現性保持

[以下 CORE 各ファイル同様...]

---

## VIZ 分類
[同様フォーマット]

---

## ORPHAN 分類（ボス確認要）

### Simple_Backtest.py ★要確認
- サイズ: 53,332B（最大）
- 被 import: [調査結果]
- docs 記載: **なし**
- 先頭 30 行抜粋:
```python
  [bash_tool で取得した内容]
```
- 推定用途: [Evaluator の推定]
- ボス確認質問:
  Q: このファイルは何の目的で作成されたか？
  Q: #026d バックテスト以外の用途で使用されているか？
  Q: archive 移設して良いか？

[以下 ORPHAN 各ファイル同様...]

---

## DEAD 分類

### dashboard.py
- サイズ: 0B（空ファイル）
- 判定根拠: 内容ゼロ・プレースホルダー
- Phase 2 処理: _archive/ 移設推奨

[以下同様...]

---

## ボスへの QA 一覧（集約）

全 ORPHAN ファイルについての質問を以下に集約:

### Q1: Simple_Backtest.py
[質問内容]

### Q2: data_fetch.py
[質問内容]

[...]

---

## Phase 2 への引き渡し事項

Phase 2（archive 移設）で処理すべきファイル:
- DEAD 確定 N ファイル
- ORPHAN のうちボスが archive 承認した N ファイル
- 合計 N ファイルを src/_archive/ へ git mv

Phase 3（責務別ディレクトリ化）の対象:
- CORE N ファイル → src/core/
- VIZ N ファイル → src/viz/
- SCAN N ファイル → src/scan/
- TEST N ファイル → src/tests/
- UTIL N ファイル → src/utils/ または直下

---

## 更新履歴

| 日付 | セッション | Evaluator | 主な作業 |
|---|---|---|---|
| YYYY-MM-DD | Phase 1 初回 | Rex-Evaluator (Opus 4.x) | 棚卸し完了 |
````

---

## 6. 完了条件

### 6-1. 必須条件

- [ ] `src_inventory.md` が起草され docs/ に push 済み
- [ ] 全 27 ファイルが 5 分類のいずれかに振り分けられている
- [ ] ORPHAN ファイルについてボス QA が集約されている
- [ ] ADR D-12/D-13/E-8/F-8 が ADR.md に正式記述されている
- [ ] MTF_INTEGRITY_QA.md に Phase 1 完了セクションが追記されている
- [ ] Vault 側 adr_reservation.md が更新されている（または更新予約が明記）

### 6-2. 禁止事項（致命的）

- ❌ src/ 配下の物理ファイル移動・削除・改名
- ❌ 凍結ファイルへの一切の変更
- ❌ バックテスト再実行（数値不変なので無意味）
- ❌ Planner / ClaudeCode への指示書起草（本 Phase は Evaluator 単独）
- ❌ ORPHAN 判断でボス確認をスキップした archive 移設判断

### 6-3. 想定所要時間・セッション数

- 1 セッション目: STEP 1-2（14+3=17 ファイル即時分類）+ STEP 3 前半（ORPHAN 5-6 ファイル精査）
- 2 セッション目: STEP 3 後半 + STEP 4（inventory.md 起草）+ STEP 5（QA 集約）
- 3 セッション目: ボス QA 回答を受けて分類確定 + STEP 6-7（ADR 採番 + QA 追記）

合計 2-3 セッションを想定。1 セッションで完走は推奨しない（判断品質が落ちる）。

---

## 7. 実行順序の注意

STEP 1-3 は読み取り専用の調査作業で、物理変更は一切発生しない。
STEP 4 で `src_inventory.md` を作成するが、これは新規 docs ファイルの追加のみ。
STEP 5 のボス QA は Evaluator がスレッド上でボスに提示し回答を得る形。
STEP 6-7 は確定事項の文書反映で、src/ には触らない。

**Phase 1 を通じて src/ 内のファイルは 1 バイトも変更されない。**
これが本 Phase の安全性を担保する設計。

---

## 8. 関連文書
本指示書の上位文書:
MINATO_MTF_PHILOSOPHY.md   ← 裁量思想（原則αがシステム側に適用）
MTF_INTEGRITY_QA.md        ← 2026-04-19 判断経緯
Evaluator_HANDOFF.md       ← セッション引き継ぎ
本指示書が作成する文書:
src_inventory.md           ← Phase 1 成果物
ADR.md への追記            ← D-12/D-13/E-8/F-8 正式採番
Phase 2 以降の予告:
REX_028_Phase2_spec.md     ← archive 移設指示書（Phase 1 完了後起草）
REX_028_Phase3_spec.md     ← 責務別ディレクトリ化指示書
REX_029_spec.md            ← 裁量整合版の実装訂正（Planner 起草必要）

---

## 9. ボスが新スレッドで起動する際のテンプレート
このスレでは REX Trade System の Evaluator として Phase 1 棚卸しを実行してほしい。
⚠️ 作業開始前に以下を順番に読め:
① C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md
② C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md
③ docs/Evaluator_HANDOFF.md（2026-04-19 版）
④ docs/MTF_INTEGRITY_QA.md（裁量整合性 QA）
⑤ docs/REX_028_spec.md（本 Phase 1 指示書・今回の作業対象）
⑥ docs/MINATO_MTF_PHILOSOPHY.md（裁量思想）
読了後、REX_028_spec.md §4 の STEP 1-2 から着手せよ。
STEP 3 の ORPHAN 精査時は、各ファイルの先頭 50 行を
bash_tool（curl raw.githubusercontent.com/...）で取得してから判断すること。
NLM: REX_System_Brain (da84715f-9719-40ef-87ec-2453a0dce67e)
Rex_Trade_Brain (4abc25a0-4550-4667-ad51-754c5d1d1491)

---

*発行: Rex-Evaluator (Opus 4.7) / 2026-04-19*
*Phase 1 着手後は本指示書を source of truth として参照せよ*