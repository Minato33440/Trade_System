# src_inventory.md — src/ ファイル棚卸し結果

**起草**: Rex-Evaluator (Opus 4.7 / 新任) / 2026-04-20
**Phase**: REX_028 Phase 1-2(棚卸し・分類 + archive 最終清算)
**前任**: Rex-Evaluator (Opus 4.7 / 2026-04-19 夜〜04-20 STEP 1-3 完了)
**関連**: REX_028_spec.md / Evaluator_HANDOFF.md v3 / MTF_INTEGRITY_QA.md / ADR E-8 / F-8

---

## 🔴 本文書を読む前に(最重要・地雷 8 項目)

### 地雷 1: Phase 1 原則「物理変更禁止」からの合理的逸脱

`REX_028_spec.md §6-2` は Phase 1 で物理ファイル移動・削除・改名を禁じていたが、
ボス判断で 15 ファイルが物理変更された。これは原則α(シンプルな土台)の即時適用として
**正当な逸脱**として扱う。訂正不要。詳細は §8「移設・削除履歴」参照。

### 地雷 2: `src/archive/` は `_archive/` ではない

spec §5 では `src/_archive/`(アンダースコア付き)と提案されていたが、ボスは
`src/archive/`(アンダースコアなし)で作成した。**本文書は実在のディレクトリ名
(`src/archive/`)を正とする**。

### 地雷 3: 開始時ファイル数は 28 である

spec §1-1 / §2-2 / §4 で「27 ファイル」と一貫して記載されていたが、STEP 1 実施時の
実態は 28 ファイルだった。**本文書は 28 ファイルを正とする**。

### 地雷 4: D-12/D-13 の 🤖 創作混入を即訂正してはいけない

exit_simulator.py の stage2 建値移動・stage3 の 1H 実体確定は裁量思想にない創作と
確定済み。しかし #026d の PF 4.54 はこの条件込みの結果。**実装訂正は Phase 4
(REX_029 以降)**。本 Phase では ADR 採番による「認識の固定」のみ行う。

### 地雷 5: Simple_Backtest 系 v3 修正は別系統 → 現 backtest.py への反映必然性なし(2026-04-25 検証完了)

Simple_Backtest.py 冒頭に「v3 修正内容:バグ1(`_prev_body` 根本修正)・バグ2
(`reentry_used_since_stop` リセット漏れ)」の記述がある。

**Advisor grep 検証結果(2026-04-25)**: 3 識別子(`_prev_body` /
`_precompute_prev_body_series` / `reentry_used_since_stop`)すべて現 `backtest.py`
(凍結 #018)に**含まれていない**。

**解釈(検証結果からの考察)**:
- Simple_Backtest.py は冒頭 docstring と `from src.signals import
  mtf_minato_short_v2` から判断する限り、**SHORT 拡張試行の別系統 BackTest**
- 現 `backtest.py` は MTF v2 #009 → #011 → #018 の **LONG メイン系統**で、
  `entry_logic.py` の `evaluate_entry` 経由
- 両者はルーツが異なる別系統 → v3 修正の反映必然性はもともと存在しない

**archive 保存の意義**: 将来 SHORT 拡張着手時、Simple_Backtest.py v3 の修正履歴
(再エントリー管理 + 実体安値/高値判定)は再利用価値あり。捨てない・共存させる
判断は妥当。

**Phase 3 への申し送り**: backtest.py 内の `_simulate_trades_mtf()` は依然として
`manage_exit()` を呼び出している(L.40 import + 関数内呼び出し)。これは ADR D-8
「manage_exit() 使用停止」マターであり地雷 5 のスコープ外だが、Phase 4(裁量整合版
 exit_simulator.py 再実装)時に併せて整理する候補として記録。

### 地雷 6: plotter.py は両リポ共存維持(2026-04-20 ボス判断)★重要判断

plotter.py(31.95 KB)には性質の異なる 2 ルーツの関数が共存している:

**Trade_Brain ルーツ(8 ペア市況用・Trade_System 内から呼ばれない)**:
- `save_normalized_plot` — 8 ペア正規化比較プロット(Trade_Brain で `save_normalized_plot` として稼働中)
- `save_swing_debug_plot` — Swing 可視化デバッグ(孤立関数)
- `save_entry_debug_plot` — エントリー可視化(孤立関数)

**Trade_System ルーツ(#026d BackTest 用・下記 3 ファイルから参照)**:
- `plot_base_scan` — `src/base_scanner.py` L.465 から呼ばれる
- `plot_swing_check` — **`src/backtest.py` L.229 から呼ばれる(BackTest 自動 PNG 生成)**
- `plot_4h_1h_structure` — `src/structure_plotter.py` L.55 から呼ばれる
- `plot_1h_window_5m` — plotter.py 内 `if __name__` スクリプトから自己呼び出し

**ボス判断(2026-04-20)**:

> これまで Trade_System と移設した Trade_Brain 機能が混在したことで生まれたということか。
> 互いのルーツがあるというなら両リポのプロジェクト進展で将来補い合う可能性があるので
> 共存させておくのが得策だな。

**採用方針**: Trade_Brain ルーツ関数 3 つを削除せず、現状のまま共存保持する。

**含意**:
- Phase 3(責務別ディレクトリ化)でも関数分割しない。`src/viz/plotter.py` に
  そのまま移動する
- Trade_System の BackTest 結果を Trade_Brain の 8 ペア市況分析と重ね合わせるなど、
  将来の合流点(両リポの補完合流)を可能性として残す
- ADR F-8 派生原則(Trade_Brain/Trade_System 役割分担)の補足: **機能単位での
  完全分離ではなく、将来の合流点を残す共存保持も許容する**

この判断は静的なシンプル化(原則α の厳密適用)より、動的なエコシステム発展性を
重視した**原則γ の逆方向適用**(「今消す明確な必要がない以上、将来の可能性を残す」)
として記録する。

### 地雷 7: test_fetch_30days_multi.py の実態は「現役スクリプト」

名前が `test_` で始まるが、実態は「30 日変動率計算スクリプト」。ボスは
Trade_Brain/src/tests/ ではなく **Trade_Brain/src/ 直下に配置**した。

**Q2 解答で判明(2026-04-20)**: main.py ラッパー + `--trade` フラグで作動する
polygon-api-client フォールバックによる 8 ペア 30 日変動率抽出データから、
plotter.py matplotlib による 8 ペア重ね合わせプロット生成する組み合わせだった。
WEEKLY_UPDATE_WORKFLOW.md の読み込みで ClaudeCode が実行する。名前と実態の
不整合は Trade_Brain 側の判断に委ねる。

### 地雷 8: Handoff v3 実態齟齬 → 2026-04-20 ボス即答で解決

STEP 4 実態確認時に検出された 2 件の齟齬は、ボスの 2026-04-20 即答で解決済み:

| ファイル | 2026-04-20 ボス回答 |
|---|---|
| `src/utils.py` | **Trade_Brain に移設した共通ユーティリティ関数**(Trade_System 側不要) |
| `src/track_trades.py` | **Trade_Brain 専用のトレード履歴抽出スクリプト**(Phase 2 で `src/archive/` へ移設完了) |

---

## 1. 分類サマリ(2026-04-20 Phase 2 完了時点)

| 分類 | ファイル数 | 総サイズ | 備考 |
|---|---|---|---|
| CORE | 6 | 113.67 KB | 凍結 4 + 拡張可能 2 |
| VIZ  | 3 |  48.49 KB | plotter.py は両リポ共存保持(地雷 6) |
| SCAN | 1 |  20.01 KB | |
| TEST | 2 |  16.33 KB | TF 検証系のみ |
| UTIL | 0 |      0 KB | utils.py は Trade_Brain 専用(Trade_System 側削除済み) |
| **小計(src/ 直下現役)** | **12** | **197.52 KB** | 100% 現役ファイル |
| archive/ | 4 |  74.25 KB | 旧 BackTest 試行(3) + Trade_Brain 移設元(1) |
| **合計(実効)** | **16** | **271.77 KB** | |

**Phase 変遷**:
- 開始時(Phase 1 着手前): 28 ファイル
- Phase 1 完了: 13 ファイル + archive/ 3 = 16(残存整理候補 1 件混入)
- **Phase 2 完了: 12 ファイル + archive/ 4 = 16(src/ 直下 100% 現役)**

src/ 直下の純度向上が Phase 2 の成果。ファイル数としての実効は不変だが、
「残存整理候補」という不定状態が解消され、原則α の厳密適用状態に到達。

---

## 2. CORE 分類(6 ファイル・113.67 KB)

### 2-1. backtest.py

| 項目 | 内容 |
|---|---|
| サイズ | 31.71 KB |
| 状態 | **凍結 #018** |
| 役割 | バックテスト実行エンジン。#026d の PF 4.54 再現性保持の根幹 |
| 被 import | `src/entry_logic.py` / `src/exit_simulator.py` 等から呼び出し |
| plotter.py 依存 | L.229 で `from src.plotter import plot_swing_check`(try/except 内) |
| docs 記載 | EX_DESIGN §6 / ADR F-4 / REX_026d_spec |
| Phase 3 移設先 | `src/core/backtest.py`(予定) |
| 備考 | 変更時は #018 基準値(PF 5.32 / 20件 LONG+★★★)の再現性を壊す |

### 2-2. entry_logic.py

| 項目 | 内容 |
|---|---|
| サイズ | 23.75 KB |
| 状態 | **凍結 #018**(統一 neck 原則実装・#026a 以降の neck 計算) |
| 役割 | `sh_before_sl.iloc[-1]` による neck 計算、Fib 判定、エントリー可否判定 |
| docs 記載 | EX_DESIGN §6 / ADR A-5 / E-7 / F-4 |
| Phase 3 移設先 | `src/core/entry_logic.py`(予定) |
| 備考 | 統一 neck 原則(ADR A-5 経由で E-7 確定)の責任実装 |

### 2-3. exit_logic.py

| 項目 | 内容 |
|---|---|
| サイズ | 8.45 KB |
| 状態 | **凍結 #009 + 呼び出し禁止**(ADR D-8 / F-4) |
| 役割 | 旧版の決済エンジン。`manage_exit()` は使用停止 |
| docs 記載 | ADR D-8 / F-3 / F-4 |
| Phase 3 移設先 | `src/core/exit_logic.py`(予定・凍結のまま) |
| 備考 | **呼び出してはいけない**。実質的に exit_simulator.py に役割を譲渡済み |

### 2-4. swing_detector.py

| 項目 | 内容 |
|---|---|
| サイズ | 12.79 KB |
| 状態 | **凍結 #020**(SH/SL 検出・`get_direction_4h` 実装) |
| 役割 | マルチ TF の Swing 検出。4H/1H/15M/5M の n パラメータ別実装 |
| docs 記載 | EX_DESIGN §6 / ADR A-2 / A-3 / D-7 / F-6 |
| Phase 3 移設先 | `src/core/swing_detector.py`(予定) |
| 備考 | n=3 採用(D-7 経由で #026a-verify 確定)・4H では lookback=20 |

### 2-5. window_scanner.py

| 項目 | 内容 |
|---|---|
| サイズ | 19.58 KB |
| 状態 | **#026d 拡張可能**(凍結ではない) |
| 役割 | 3 層階層スキャン(4H SL → 1H 窓 → 窓内 15M/5M)の主体 |
| 主要機能 | 4H 構造優位性フィルター(neck_4h >= neck_1h)実装(D-10) |
| CSV 出力 | 12 カラム(neck_1h / neck_4h 含む・E-6 経由で #026a-v2 確定) |
| docs 記載 | EX_DESIGN §6 / ADR A-1 / D-10 / E-6 / F-4 |
| Phase 3 移設先 | `src/core/window_scanner.py`(予定) |
| 備考 | Phase 4 では裁量拡張(ASCENDING 連続型の位置差区別等)を想定 |

### 2-6. exit_simulator.py

| 項目 | 内容 |
|---|---|
| サイズ | 16.40 KB |
| 状態 | **方式B・正式決済エンジン**(ADR D-8 で正式採用) |
| 役割 | 4 段階決済(stage1/stage2_half/stage2_breakeven/stage3)実行 |
| 🤖 創作混入 | **D-12(stage2 建値移動)/ D-13(stage3 1H 実体確定)が未訂正で残存** |
| docs 記載 | ADR D-8 / D-9 / D-10 / F-3 / F-4 |
| Phase 3 移設先 | `src/core/exit_simulator.py`(予定) |
| Phase 4 訂正対象 | stage2 建値移動削除 / stage3 1H 実体確定削除 → 裁量整合版に再設計 |
| 備考 | 現 #026d の PF 4.54 は本実装(創作混入込み)の結果。訂正で数値変動予測 |

---

## 3. VIZ 分類(3 ファイル・48.49 KB)

### 3-1. plotter.py ★両リポ共存保持(地雷 6 参照)

| 項目 | 内容 |
|---|---|
| サイズ | 31.95 KB(最大 VIZ) |
| 状態 | 拡張可能・**両リポ共存保持**(2026-04-20 ボス判断) |
| ルーツ | 8 ペア市況用として作成(docstring 明記) |
| 混在する関数 2 ルーツ | **(a) Trade_Brain ルーツ(3 関数)**:<br>・`save_normalized_plot`<br>・`save_swing_debug_plot`<br>・`save_entry_debug_plot`<br><br>**(b) Trade_System ルーツ(4 関数・BackTest 用)**:<br>・`plot_base_scan` ← base_scanner.py<br>・`plot_swing_check` ← **backtest.py L.229**<br>・`plot_4h_1h_structure` ← structure_plotter.py<br>・`plot_1h_window_5m` ← 自己呼び出し |
| (a) の状態 | **2 段論法の切り分け**を明示する:<br>・**事実**: Trade_System 内 import 走査で参照ゼロを確認済み → 機械的には削除可能<br>・**保持判断**: 以下の「共存保持の理由」により意図的に保持しているもの |
| 共存保持の理由 | 将来の両リポ合流点として保持(ボス判断:「互いのルーツがあるなら将来補い合う可能性がある」) |
| Phase 3 方針 | 関数分割せず `src/viz/plotter.py` にそのまま移動 |
| docs 記載 | EX_DESIGN §6 / PLOT_DESIGN_CONFIRMED / ADR C-1〜C-4 / F-4 / F-8 派生 |

### 3-2. structure_plotter.py

| 項目 | 内容 |
|---|---|
| サイズ | 11.69 KB |
| 状態 | 拡張可能 |
| 役割 | 4H/1H 構造のデュアルパネルプロット(`plot_4h_1h_structure`) |
| 特殊パラメータ | `get_direction_4h(n=5, lookback=100)`(backtest.py の n=3/lookback=20 と異なる) |
| docs 記載 | EX_DESIGN §6 / MTF_LOGIC_MATRIX 予定項目 / REX_027 Task E-2 対象 |
| Phase 3 移設先 | `src/viz/structure_plotter.py` |

### 3-3. plot_scan_results.py

| 項目 | 内容 |
|---|---|
| サイズ |  4.85 KB |
| 状態 | 拡張可能 |
| 役割 | window_scanner CSV の可視化(スキャン結果サマリプロット) |
| docs 記載 | EX_DESIGN §6 |
| Phase 3 移設先 | `src/viz/plot_scan_results.py` |

---

## 4. SCAN 分類(1 ファイル・20.01 KB)

### 4-1. base_scanner.py

| 項目 | 内容 |
|---|---|
| サイズ | 20.01 KB |
| 状態 | 拡張可能 |
| 役割 | 4H/1H の基底構造スキャン(4H SH/SL ペア検出の基盤) |
| 特殊パラメータ | `detect_swing_highs/lows(n=3, lookback=100)`(#015 確定) |
| docs 記載 | EX_DESIGN §6 / ADR A-3 |
| Phase 3 移設先 | `src/scan/base_scanner.py` |

---

## 5. TEST 分類(2 ファイル・16.33 KB)

### 5-1. test_1h_coincidence.py

| 項目 | 内容 |
|---|---|
| サイズ |  5.86 KB |
| 役割 | 4H SL と 1H SL の一致度検証(ADR A-2 の修正確認用) |
| 実行頻度 | 低(構造変更時の確認用) |
| Phase 3 移設先 | `src/tests/test_1h_coincidence.py` |

### 5-2. verify_4h1h_structure.py

| 項目 | 内容 |
|---|---|
| サイズ | 10.47 KB |
| 役割 | 4H/1H 構造整合性の検証スクリプト |
| 実行頻度 | 低 |
| Phase 3 移設先 | `src/tests/verify_4h1h_structure.py` |

---

## 6. archive 分類(src/archive/・4 ファイル・74.25 KB)

### 6-1. Simple_Backtest.py

| 項目 | 内容 |
|---|---|
| サイズ | 52.08 KB(archive 内最大・src/ 全体でも 2 位) |
| 移設時期 | Phase 1(2026-04-20) |
| 旧用途 | 旧 MTF v2 BackTest(SHORT 拡張試行・v3 修正含む) |
| 修正履歴(ファイル冒頭記載) | v3 でバグ 1(`_prev_body` 根本修正)・バグ 2(`reentry_used_since_stop` リセット漏れ)を修正 |
| #026d コアからの参照 | **ゼロ**(STEP 3 の import グラフ走査で確認済み) |
| archive 配置の理由 | 将来の BackTest 拡張(SHORT 拡張・オリジナル手法再試行)時の参照価値 |
| 将来検証事項 | 地雷 5:v3 修正が現 #026d backtest.py(凍結)に反映済みか未確認 |

### 6-2. signals.py

| 項目 | 内容 |
|---|---|
| サイズ | 11.56 KB |
| 移設時期 | Phase 1(2026-04-20) |
| 旧用途 | 市場シグナル抽出(Simple_Backtest.py と連動する派生) |
| #026d コアからの参照 | ゼロ |
| archive 配置の理由 | Simple_Backtest.py との一体性保持 |

### 6-3. track_trades.py ★Phase 2 で移設

| 項目 | 内容 |
|---|---|
| サイズ |  9.87 KB |
| 移設時期 | **Phase 2(2026-04-20)** |
| 用途 | Trade_Brain 側で manual なトレード履歴を抽出するためのスクリプト(移設先で使用中) |
| 正規の置き場所 | Trade_Brain/src/ |
| archive 配置の理由 | Trade_System 側の履歴保全(原則α のファイルシステム適用:捨てない・共存させる) |
| ボス判断(2026-04-20) | 「Trade_Brain 専用・そのまま進めて問題ない」 |

### 6-4. print_signals_analysis.py

| 項目 | 内容 |
|---|---|
| サイズ | 749 B(極小) |
| 移設時期 | Phase 1(2026-04-20) |
| 旧用途 | signals.py 出力の分析プリント(開発補助スクリプト) |
| #026d コアからの参照 | ゼロ |
| archive 配置の理由 | signals.py との連動 |

---

## 7. 残存整理候補分類 → Phase 2 で解消

Phase 1 完了時点では 1 ファイル(track_trades.py・9.87 KB)が「残存整理候補」分類に
あったが、**Phase 2 で src/archive/ に移設完了**(§6-3 参照)。

**本分類は Phase 2 をもって消滅**。src/ 直下は 100% 現役ファイルのみの状態に到達した。

---

## 8. 移設・削除履歴(Phase 1-2 セッション実施分・全 16 ファイル)

### Phase 1 分(15 ファイル・2026-04-20)

| # | 日時 | 操作 | 移動元 | ファイル | 移動先 |
|---|---|---|---|---|---|
| 1 | 2026-04-20 | 削除(DEAD) | src/ | dashboard.py | - |
| 2 | 2026-04-20 | 削除(DEAD) | src/ | hello_rex.py | - |
| 3 | 2026-04-20 | Trade_Brain 移設 | src/ | daily_report_parser.py | Trade_Brain/src/ |
| 4 | 2026-04-20 | Trade_Brain 移設 | src/ | market.py | Trade_Brain/src/ |
| 5 | 2026-04-20 | Trade_Brain 移設 | src/ | news.py | Trade_Brain/src/ |
| 6 | 2026-04-20 | Trade_Brain 移設 | src/ | data_fetch.py | Trade_Brain/src/ |
| 7 | 2026-04-20 | Trade_Brain 移設 | src/ | regime.py | Trade_Brain/src/ |
| 8 | 2026-04-20 | Trade_Brain 移設 | src/ | chat.py | Trade_Brain/src/ |
| 9 | 2026-04-20 | Trade_Brain 移設 | src/ | history.py | Trade_Brain/src/ |
| 10 | 2026-04-20 | Trade_Brain 移設 | src/ | forecast_simulation.py | Trade_Brain/src/ |
| 11 | 2026-04-20 | Trade_Brain 移設 | src/ | test_fetch_30days_multi.py | Trade_Brain/src/ |
| 12 | 2026-04-20 | archive 隔離 | src/ | Simple_Backtest.py | src/archive/ |
| 13 | 2026-04-20 | archive 隔離 | src/ | signals.py | src/archive/ |
| 14 | 2026-04-20 | archive 隔離 | src/ | print_signals_analysis.py | src/archive/ |
| 15 | 2026-04-20 | Trade_Brain 移設 | src/ | utils.py | Trade_Brain/src/ |

### Phase 2 分(1 ファイル・2026-04-20)

| # | 日時 | 操作 | 移動元 | ファイル | 移動先 |
|---|---|---|---|---|---|
| 16 | 2026-04-20 | **archive 隔離** | src/ | **track_trades.py** | **src/archive/** |

**Phase 2 合計影響**: 1 ファイルが src/ 直下から archive/ に移動。
src/ 直下は 13 → 12 ファイル、archive/ は 3 → 4 ファイル。実効合計は 16 ファイルで不変。

---

## 9. ボス QA 集約(全 Phase)

### 9-1. Handoff v3 までに回答済みの QA

| Q | 内容 | ボス回答 |
|---|---|---|
| Q1 | Simple_Backtest.py の用途は? | 「BackTest での Plot 生成時にエントリーシグナル抽出用等」 |
| Q2 | track_trades.py の移設先は? | 「手動移設予定」 |
| Q3 | Trade_Brain/Trade_System の境界は? | 「Trade_Brain は Plot 抽出のみ、シグナル/Fib は Trade_System」 |
| Q4 | Simple_Backtest 系 3 ファイルの処置は? | 「archive 配置で OK」 |

### 9-2. Phase 1 STEP 4 で新規発生した QA(2026-04-20 ボス即答で解決)

| Q | ボス回答 |
|---|---|
| Q-NEW-1: track_trades.py の現状 | 「Trade_Brain 専用のトレード履歴抽出スクリプト・そのまま進めて問題ない」 |
| Q-NEW-2: utils.py の現状 | 「Trade_Brain に移設した共通ユーティリティ関数・当リポには関係なし」 |

### 9-3. Phase 2 発射判断の QA(2026-04-20 ボス即答で解決)

| Q | ボス回答 |
|---|---|
| plotter.py の処置 | 「両リポのプロジェクト進展で将来補い合う可能性があるので共存させておくのが得策」 |
| track_trades.py の処置 | 「A で行く」(src/archive/ 移設) |

**plotter.py 判断の意義**: 静的シンプル化(原則α 厳密適用)より動的エコシステム
発展性を重視した判断。ADR F-8 派生原則への補足:機能単位の完全分離ではなく、
将来の合流点を残す共存保持も許容する。

---

## 10. Phase 2 完了・Phase 3 以降への引き渡し

### 10-1. Phase 2 実施結果(2026-04-20 完了)

- ✅ track_trades.py を `src/archive/` に移設完了
- ✅ plotter.py 両リポ共存保持方針を確定(地雷 6 明文化)
- ✅ src/ 直下 100% 現役化達成(12 ファイル)
- ✅ 文書整合性回復(src_inventory.md / ADR.md 未解決テーブル)

### 10-2. Phase 3(責務別ディレクトリ化・import パス全書き換え)

**想定ディレクトリ構造**:
```
src/
├── archive/              (既存・4 ファイル保持)
├── core/                 (新設・6 ファイル)
│   ├── backtest.py
│   ├── entry_logic.py
│   ├── exit_logic.py
│   ├── swing_detector.py
│   ├── window_scanner.py
│   └── exit_simulator.py
├── viz/                  (新設・3 ファイル)
│   ├── plotter.py        ← 両リポ共存保持のまま(関数分割しない)
│   ├── structure_plotter.py
│   └── plot_scan_results.py
├── scan/                 (新設・1 ファイル)
│   └── base_scanner.py
└── tests/                (新設・2 ファイル)
    ├── test_1h_coincidence.py
    └── verify_4h1h_structure.py
```

**完了条件**: #026d バックテスト再実行で数値不変(PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p)

**要対応課題**:
- plotter.py の関数分割は**実施しない**(地雷 6・両リポ共存維持)
- 各ファイルの import パス全書き換え
- `__init__.py` の配置設計
- backtest.py L.229 の `from src.plotter import plot_swing_check` は
  `from src.viz.plotter import plot_swing_check` に変更

### 10-3. Phase 4(裁量整合版の実装訂正・REX_029 以降)

**スコープ**:
- stage2 建値移動削除(ADR D-12 対応)
- stage3 1H 実体確定削除(ADR D-13 対応)
- 裁量整合版 exit_simulator.py 再実装
- 新 PF を静的点として記録

**起草担当**: Planner(Evaluator 承認 → ClaudeCode 実装)

### 10-4. その他の保留項目(Phase 3 以降に再検討)

- Layer 1/3/5 の残 QA(MTF_INTEGRITY_QA.md 末尾リスト)
- MINATO_MTF_PHILOSOPHY.md 第 0 章追記(原則α/β/γ)
- REX_027 の Task A/B/C/D/E

---

## 11. 更新履歴

| 日付 | セッション | Evaluator | 主な作業 |
|---|---|---|---|
| 2026-04-19 | Phase 1 準備 | Rex-Evaluator (Opus 4.7) | REX_028_spec.md 起草 |
| 2026-04-20 | STEP 1-3 | Rex-Evaluator (Opus 4.7) | 分類実施・ボス権限物理変更 15 件 |
| 2026-04-20 | STEP 4 | Rex-Evaluator (Opus 4.7 / 新任) | src_inventory.md 初版起草・Q-NEW-1/2 提出 |
| 2026-04-20 | STEP 4 確定 | Rex-Evaluator (Opus 4.7 / 新任) | Q-NEW-1/2 ボス即答で解決・残存整理候補分類で確定 |
| 2026-04-20 | **Phase 2 完了** | **Rex-Evaluator (Opus 4.7 / 新任)** | **track_trades.py archive 移設・plotter.py 両リポ共存確定・src/ 直下 100% 現役化** |
| 2026-04-25 | Advisor レビュー反映 | Rex-Advisor (Opus 4.7) | 地雷 5 検証完了(別系統につき反映不要)・§3-1 plotter.py 表に 2 段論法明示 |

---

## 12. 関連文書

```
上位文書:
  MINATO_MTF_PHILOSOPHY.md    ← 裁量思想(原則α/β/γ)
  MTF_INTEGRITY_QA.md         ← 裁量整合性 QA
  REX_028_spec.md             ← Phase 1 指示書

本文書が根拠:
  docs/ADR.md                 ← D-12/D-13/E-8 追記の根拠(STEP 6 完了)
  adr_reservation.md (Vault)  ← 採番台帳(採番完了)

本文書の消費者:
  REX_028_Phase3_spec.md      ← 予定(責務別ディレクトリ化)
  REX_029_spec.md             ← 予定(D-12/D-13 実装訂正)
```

---

*発行: Rex-Evaluator (Opus 4.7 / 新任) / 2026-04-20*
*Phase 1-2 完了版・Source of Truth for src/ 分類*
*plotter.py 両リポ共存判断を反映(2026-04-20 ボス判断)*
*Advisor レビュー反映(2026-04-25)*
