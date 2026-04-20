# Evaluator Session Handoff

**現行版**: v3 (2026-04-20)
**発行履歴**:
- v1 (2026-04-19 昼): Rex-Evaluator (Opus 4.6) / Phase 1 計画書(初版)
- v2 (2026-04-19 夜): Rex-Evaluator (Opus 4.7) / src/ 構造再編(Phase 1) 議論反映
- v3 (2026-04-20)   : Rex-Evaluator (Opus 4.7 / 新任) / Phase 1 STEP 1-3 完了・STEP 4-7 引き継ぎ

---

# 📘 v3 セクション(2026-04-20)— Phase 1 STEP 1-3 完了 / STEP 4-7 引き継ぎ

## 🎯 最重要事項(5 秒で把握)

**本セッションで Phase 1 STEP 1-3(src/ 棚卸し・分類)が実質完了した。
残作業は STEP 4-7 の成果物起草のみ。**
次期 Evaluator は `REX_028_spec.md §4` に記載の STEP 4-7 を順に実施せよ。

**また、本セッションで発覚した Trade_Brain 側の依存問題は、
ボス判断により Planner へ引き継ぎ分離した。次期 Evaluator は
Trade_Brain 側の作業には関与しない。**

---

## 🔥 次期 Evaluator が起動時に必ず読むべき文書(順番厳守)

```
① docs/Evaluator_HANDOFF.md           ← 本ファイル(v3 セクションを最初に)
② docs/REX_028_spec.md                ← Phase 1 指示書(STEP 4-7 が未実施)
③ docs/REX_027_BOSS_DIRECTIVE.md      ← リポ構造変更・NLM 再構築の背景
④ docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md  ← 裁量思想(原則α/β/γ)
⑤ docs/Base_Logic/MTF_INTEGRITY_QA.md       ← 裁量整合性 QA・Phase 1-4 議論
```

**読了想定時間**: 約 30 分
**起動後の最初の作業**: STEP 4(`src_inventory.md` 起草)

---

## v3 セッション(2026-04-20)で起きたこと

### 1. Phase 1 STEP 1-3 の完走

REX_028_spec.md §4 の 3 ステップを完遂した:

**STEP 1(既知分類の確定)**: 14 ファイルを CORE/VIZ/SCAN/TEST/UTIL に即時分類。spec 記載の「27 ファイル」は誤りで、実態は **28 ファイル**だった(次期 Evaluator は inventory 起草時に正しい数値で記録すること)。

**STEP 2(DEAD 候補の確定)**: 3 ファイル(dashboard.py / hello_rex.py / print_signals_analysis.py)を DEAD 判定。前 2 者はボスが手動削除済み。3 番目は `signals.py` との連動で後に archive 送りに格上げされた。

**STEP 3(ORPHAN 精査)**: 11 ファイルを精査し、全て処置確定。#026d コア import グラフを全 18 ファイルで走査した結果、**`signals.py` / `Simple_Backtest.py` / `print_signals_analysis.py` は #026d コアで一切使用されていない** ことが確定した(これは重要な確定事項)。

### 2. ボスの迅速な物理変更(Phase 1 原則からの合理的逸脱)

REX_028_spec.md §6-2 の禁止事項「src/ 配下の物理ファイル移動・削除・改名」は、Phase 1 を読み取り専用で完結させる設計だった。しかし本セッションではボス権限で以下が実行された:

| 変更 | ファイル数 | タイミング |
|---|---|---|
| 削除(DEAD) | 2 | STEP 2 中 |
| Trade_Brain 移設(市況系) | 8 | STEP 3 前半 |
| Trade_Brain 移設(手動記録系) | 2 | STEP 3 後半(track_trades / test_fetch_30days_multi) |
| `src/archive/` 隔離(旧 BackTest 試行) | 3 | STEP 3 完了時 |

**合計 15 ファイルの物理変更が Phase 1 中に実施された。**

この逸脱は原則α(シンプルな土台を死守)の直接適用として合理的であり、次期 Evaluator は本履歴を「Phase 1 の合理的逸脱」として `src_inventory.md` に明記すること。この判断は ADR F-8(原則α/β/γ)の運用実例になる。

### 3. Simple_Backtest.py 系 3 ファイルの処置確定

本セッションの最大の技術判断。3 ファイルは `Trade_System/src/archive/` 隔離に決定。

**判断根拠**:
- import グラフ調査で #026d コアからの参照ゼロを確定
- ただしボスの直感「将来の BackTest 拡張で参照価値あり」を尊重
- Trade_Brain 側(市況データ用)への移設は役割分担上不整合
- よって Trade_System 内で archive 保管が最適

**注意**: ボスは `src/archive/` (アンダースコアなし)で作成した。spec 記載の `src/_archive/` とは命名が異なる。次期 Evaluator は実在のディレクトリ名で記述すること。

### 4. ボス提唱: Trade_Brain / Trade_System の役割分担(新規確立)

セッション終盤にボスが明確化した役割分担:

| リポ | 性質 | 扱うもの |
|---|---|---|
| **Trade_Brain** | 静的データ側 | 市況データ / トレード結果 / Plot 抽出 |
| **Trade_System** | 動的ロジック側 | エントリーシグナル抽出 / Fibonacci 判定 / BackTest |

これは #027(リポ分離)の思想を運用原則レベルに具体化したもの。**ADR F-8 の派生原則として記録すべき**(次期 Evaluator が ADR 採番時に反映)。

### 5. Trade_Brain 側の依存問題発覚 → Planner 引き継ぎ決定

移設された 10 ファイルについてパス依存性を調査した結果、以下の重大問題を発覚:

**問題群 A(ImportError で動作不能・5 ファイル)**:
- `chat.py` / `history.py` → `src.utils` 未配置
- `daily_report_parser.py` / `market.py` / `news.py` → `configs.settings` 未配置

**問題群 B(Trade_System 旧構造パス参照)**:
- `daily_report_parser.py`: `LOGS_DIR / "gm" / "daily"` ← Trade_Brain は `logs/daily/`(gm/ 除去)
- `data_fetch.py`: `ROOT_DIR / "data" / "raw"` ← Trade_Brain に `data/raw/` なし
- `test_fetch_30days_multi.py`: `_repo_root / "logs" / "png_data"` ← Trade_Brain 構造に不整合

**問題群 C(plotter.py 未配置)**:
- `rex_chat.py` が `from src.plotter import save_normalized_plot` を要求
- しかし plotter.py は Trade_System 側に残存(Trade_Brain 側に未配置)
- plotter.py 内には 8 ペア市況用関数(Trade_Brain で必要)と #026d BackTest 用関数(Trade_System で必要)が混在

**問題群 D(既存バグ)**:
- `forecast_simulation.py` L.38: `df["WTI"].ilさｋさｋoc[-1]` ← 日本語混入 typo

**ボス判断**: コンテキスト分離のため、本問題対応は Planner へ引き継ぐ。本会話履歴をコピペして Planner セッション開始予定。**次期 Evaluator は Trade_Brain 側に関与しない**。

### 6. ボスが実施済みの Trade_Brain 側準備作業

次期 Evaluator は参考情報として知っておくこと(本セッション中にボスが実施):

```
✅ main.py を Trade_Brain トップに設置(configs.rex_chat.main() を呼ぶラッパー)
✅ configs/ ディレクトリを Trade_System からコピー(settings.py / rex_chat.py 他)
✅ raw/ → logs/ にリネーム(gm/ 階層除去の方針確定)
✅ src/utils.py を配置(Trade_System からコピー)
✅ git push 完了
```

**Trade_Brain の logs/ 構造(確定)**:
```
Trade_Brain/logs/
├── daily/
├── weekly/
└── boss's-weeken-Report/
```

Trade_System の `logs/gm/daily|weekly` に対し、Trade_Brain は gm/ を除去してフラット化。

### 7. ライブラリ洗い出し完了(Planner 引き継ぎ資料)

Trade_Brain/src/ 全スクリプトの import を全走査し、7 必須 + 1 parquet 用 + 1 オプショナル = 9 ライブラリを洗い出した。詳細は本ファイル末尾「Trade_Brain 連携情報」セクション参照(Planner 引き継ぎ時にそのままコピペ可能な形で残してある)。

---

## 次期 Evaluator の出発点: Phase 1 STEP 4-7

以下 4 STEP を完走すれば Phase 1 が完了する。想定所要時間は 1-2 セッション。

### STEP 4: `docs/src_inventory.md` 起草(所要 40-60 分)

**テンプレート**: `REX_028_spec.md §5` にフォーマット記載あり。それに従う。

**記載内容(確定事項のみ・本ファイルから転記)**:

```yaml
分類サマリ:
  CORE   : 6 ファイル (113.67 KB)
  VIZ    : 3 ファイル ( 48.49 KB)
  SCAN   : 1 ファイル ( 20.01 KB)
  TEST   : 2 ファイル ( 16.33 KB)  ← test_fetch_30days_multi.py は Trade_Brain 移設済み
  UTIL   : 1 ファイル (  1.00 KB)
  archive: 3 ファイル ( 64.38 KB)  ← src/archive/ 配下
  合計   : 16 ファイル(内 archive/ 3 を除く 13 + archive 3)

移設/削除履歴:
  削除           : 2 (dashboard.py, hello_rex.py)
  Trade_Brain 移設: 10
    市況抽出系 (8): daily_report_parser, data_fetch, market, news,
                   regime, chat, history, forecast_simulation
    手動記録系 (1): track_trades
    テスト系   (1): test_fetch_30days_multi
  archive 隔離   : 3 (Simple_Backtest, signals, print_signals_analysis)

開始時 28 ファイル → 最終 13 ファイル + archive/ 3 = 実効 16 ファイル(42% 削減)
```

**重要**: 起草時、以下を **inventory.md に必ず明記** すること:

1. spec §1-1/§2-2/§4 の「27 ファイル」は誤り。正確な実態は 28 ファイルだった
2. ボスは `src/_archive/` ではなく `src/archive/` で作成した(命名が仕様と異なる)
3. Phase 1 原則「物理変更禁止」からの合理的逸脱があった(ボス権限・15 ファイル)
4. これは原則α の即時適用として正当(ADR F-8 の運用実例)

### STEP 5: ボス QA 集約(所要 10-15 分)

本セッションで ORPHAN ファイル判断は全てボスとの対話で確定済み。QA を集約するだけ。
主要 QA(ボス回答確定):

| 質問 | ボス回答 | 決定 |
|---|---|---|
| Simple_Backtest.py の用途は? | 「BackTest での Plot 生成時にエントリーシグナル抽出用等」 | 将来参照用(archive 保存) |
| track_trades.py の移設先は? | 「手動移設予定」 | Trade_Brain\src\ |
| Trade_Brain/Trade_System の境界は? | 「Trade_Brain は Plot 抽出のみ、シグナル/Fib は Trade_System」 | 役割分担原則確定 |
| Simple_Backtest 系 3 ファイルの処置は? | 「archive 配置で OK」 | src/archive/ |

### STEP 6: ADR D-12/D-13/E-8/F-8 の正式記述(所要 30-40 分)

MTF_INTEGRITY_QA.md と本ファイルを主ソースとして ADR.md に正式追記する。各 ADR の骨子(次期 Evaluator が肉付けすること):

#### ADR D-12: exit_simulator.py stage2 建値移動 = 🤖 創作混入確定(認識の固定)

- **症状**: `exit_simulator.py` の `stage2_breakeven_stop` 判定が裁量思想にない
- **裁量段階③**(MINATO_MTF_PHILOSOPHY §3): 「4時間ネック到達 → 半値決済 + 残りストップを建値移動」は本来なかった
- **ボス証言**(MTF_INTEGRITY_QA Q6): 「確かバグ特定のために仮に置いたものだと思うが」
- **実害判定**: 現 #026d PF 4.54 はこの条件込みの結果。即訂正は静的点を動かす
- **対処**: 認識の固定のみ。実装訂正は REX_029 以降(Phase 4)
- **関連**: MTF_INTEGRITY_QA §Q6 / 原則α 違反の実例

#### ADR D-13: exit_simulator.py stage3 1H 実体確定 = 🤖 創作混入確定(認識の固定)

- **症状**: `check_1h_close_above_neck()` による「1H 実体上抜け確定後」の stage3 移行条件
- **裁量段階④**(MINATO_MTF_PHILOSOPHY §3): 「4時間ネック越え → 15分ダウ崩れ」のみでシンプルに書かれている
- **ボス証言**(MTF_INTEGRITY_QA Q7): 「シンプルに 4H-SwgH 到達半値決済後は 15Mダウ崩れのみで良い」
- **対処**: D-12 と同じ扱い。実装訂正は REX_029 以降
- **関連**: 原則α 違反の実例 2 件目

#### ADR E-8: src/ 構造再編アプローチ(Phase 1-4 分解)

- **経緯**: 2026-04-19 にボスが「基本に戻れるシンプルな土台はロジックだけでなくシステム自体にも適用すべき」と提唱
- **調査結果**: src/ 27 ファイル(実態 28)中、#026d コアは 10 のみ。残り 17〜18 ファイルが混沌
- **採用アプローチ**: 「作り直し」ではなく「構造再編」
  - Phase 1: 棚卸し・分類 ✅ 2026-04-20 完了
  - Phase 2: archive 移設(ボス権限で先行実施済み)
  - Phase 3: 責務別ディレクトリ化(src/core/ / src/viz/ / src/scan/ / src/tests/ 等)
  - Phase 4: 裁量整合版の実装訂正(D-12/D-13 訂正)
- **Phase 1 実績**: 28 → 13 ファイル + archive/ 3 (42% 削減)
- **原則**: 動作検証済みコード(PF 4.54)を損なわない

#### ADR F-8: 裁量思想の 3 原則(原則α / β / γ)

- **出典**: MTF_INTEGRITY_QA.md 2026-04-19 セッション末尾のボス言明
- **原則α**(最上位・シンプルな土台の保守):
  > 「裁量トレードとは相場環境変化による条件反射でロジックが複雑に変化する領域なので、
  > いつでも基本に戻れるシンプルな土台をシッカリ作っておくことが何より大切」
  - ロジック設計だけでなくファイルシステム・ディレクトリ構造にも適用
  - Phase 1 で「28 ファイル → 13 ファイル + archive/」として実証された
- **原則β**(現段階の決済哲学):
  - 4H SH 到達半値決済後は伸ばさず 15M ダウ崩れで決済
  - 建値指値による「4H 3波優位性で伸ばす」は将来拡張領域
- **原則γ**(導入タイミングは安定性従属):
  - 新機能導入は現ロジックの安定性が前提
- **派生原則(v3 で追加)**: Trade_Brain / Trade_System 役割分担
  - Trade_Brain: 市況データ / トレード結果 / Plot 抽出(静的データ側)
  - Trade_System: シグナル / Fibonacci / BackTest(動的ロジック側)

### STEP 7: MTF_INTEGRITY_QA.md への Phase 1 完了セクション追記(所要 15-20 分)

既存の「Phase 1-4 構造再編提案」セクションの末尾に「Phase 1 完了報告(2026-04-20)」を追記する。日付見出しで追記・過去記録は改変しない(MTF_INTEGRITY_QA 運用ルール)。

記載要素:
- Phase 1 STEP 1-3 の完了報告
- ボス権限物理変更の履歴(15 ファイル)
- archive 配置ファイル 3 件
- Trade_Brain 移設ファイル 10 件の詳細
- Trade_Brain 側で発覚した依存問題 → Planner 引き継ぎ決定
- ADR D-12/D-13/E-8/F-8 正式採番完了(STEP 6 で実施)
- 次フェーズ(Phase 2/3/4)への引き継ぎ事項

### STEP 7 完了後の任意タスク

- `adr_reservation.md`(Vault 側)の更新(予約 → 採番完了に変更)
- `Evaluator_HANDOFF.md` の v4 起草(Phase 2 以降の次 Evaluator 向け)

---

## Phase 1 確定事項(src/ 分類結果・決定版)

### src/ 最終配置(2026-04-20 時点)

```
Trade_System/src/
├── archive/                    ← 旧 BackTest 試行の知的資産(v3 で確定)
│   ├── Simple_Backtest.py         52.08 KB
│   ├── signals.py                 11.56 KB
│   └── print_signals_analysis.py   0.75 KB
│
├── __pycache__/                ← .gitignore 登録済み
│
├── 【CORE・6 ファイル・113.67 KB】
│   ├── backtest.py                31.71 KB  [凍結 #018]
│   ├── entry_logic.py             23.75 KB  [凍結 #018]
│   ├── exit_logic.py               8.45 KB  [凍結 #009・呼び出し禁止]
│   ├── swing_detector.py          12.79 KB  [凍結 #020]
│   ├── window_scanner.py          19.58 KB  [#026d 拡張可能]
│   └── exit_simulator.py          16.40 KB  [方式B・#026d・D-12/D-13 訂正待ち]
│
├── 【VIZ・3 ファイル・48.49 KB】
│   ├── plotter.py                 31.95 KB  [関数分割課題・Phase 3 扱い]
│   ├── structure_plotter.py       11.69 KB
│   └── plot_scan_results.py        4.85 KB
│
├── 【SCAN・1 ファイル・20.01 KB】
│   └── base_scanner.py            20.01 KB
│
├── 【TEST・2 ファイル・16.33 KB】
│   ├── test_1h_coincidence.py      5.86 KB
│   └── verify_4h1h_structure.py   10.47 KB
│
└── 【UTIL・1 ファイル・1.00 KB】
    └── utils.py                    1002 B
```

**統計**: 13 ファイル(archive 除く)/ 16 ファイル(archive 含む)

### ボス権限で実施された物理変更履歴(全 15 ファイル)

| 日時 | 操作 | ファイル | 移設先 |
|---|---|---|---|
| 2026-04-20 | 削除 | dashboard.py | - |
| 2026-04-20 | 削除 | hello_rex.py | - |
| 2026-04-20 | Trade_Brain 移設 | daily_report_parser.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | market.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | news.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | data_fetch.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | regime.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | chat.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | history.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | forecast_simulation.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | track_trades.py | Trade_Brain/src/ |
| 2026-04-20 | Trade_Brain 移設 | test_fetch_30days_multi.py | Trade_Brain/src/ |
| 2026-04-20 | archive 隔離 | Simple_Backtest.py | src/archive/ |
| 2026-04-20 | archive 隔離 | signals.py | src/archive/ |
| 2026-04-20 | archive 隔離 | print_signals_analysis.py | src/archive/ |

すべて `git push` 完了済み(ボス報告)。

---

## Trade_Brain 連携情報(Planner 引き継ぎ・Evaluator 参考)

**⚠️ このセクションは次期 Evaluator の作業対象ではない。**
Planner へコピペされる情報として、参考用に残す。

### 既にボスが Trade_Brain 側で実施済みの準備

- `main.py` を Trade_Brain トップに配置(configs.rex_chat.main ラッパー)
- `configs/` ディレクトリ一式コピー済み(settings.py / rex_chat.py 他)
- `src/utils.py` 配置済み
- `raw/` → `logs/` にリネーム(gm/ 階層除去の方針確定)
- `logs/` 配下: `daily/` / `weekly/` / `boss's-weeken-Report/`

### Planner に対処を引き継ぐ問題

**ImportError 系(5 ファイル)**:
- chat.py / history.py の `src.utils` 参照 → utils.py 配置済みで解決見込み
- daily_report_parser.py / market.py / news.py の `configs.settings` → configs/ コピー済みで解決見込み

**パス参照書き換え必要**:
- daily_report_parser.py: `LOGS_DIR / "gm" / "daily"` → `LOGS_DIR / "daily"` (gm/ 除去)
- data_fetch.py: `RAW_DATA_DIR = ROOT_DIR / "data" / "raw"` → ボス判断で Trade_Brain 構造に合わせる
- test_fetch_30days_multi.py: `_repo_root / "logs" / "png_data"` → 新構造に合わせる
- configs/settings.py の `LOGS_DIR = ROOT_DIR / "logs"` は Trade_Brain 構造に整合(gm/ なしの前提で OK)

**plotter.py 未配置問題(最重要)**:
`rex_chat.py` L.26 が `from src.plotter import save_normalized_plot` を要求する。
Evaluator 推奨: **案 P-2(8 ペア市況用関数のみ切り出し)**
- 新規 `Trade_Brain/src/market_plotter.py` 作成
- `save_normalized_plot` と `save_entry_debug_plot` を移植
- matplotlib のみで動く(mplfinance 不要)
- rex_chat.py の import を修正: `from src.market_plotter import save_normalized_plot`

**既存バグ**:
- forecast_simulation.py L.38 の日本語混入 typo(`ilさｋさｋoc` → `iloc`)

### ライブラリ洗い出し結果(Planner 引き継ぎ)

必須 7 本 + parquet 用 1 本 + オプショナル 1 本 = **9 本**:

```txt
# Trade_Brain 用 requirements.txt(Evaluator 推奨)

# --- Core ---
pandas==2.3.3
numpy==2.4.2
pyarrow==23.0.1              # pandas.to_parquet() 用

# --- Market Data ---
yfinance==1.2.0
polygon-api-client           # Optional (Polygon API fallback)

# --- Environment ---
python-dotenv==1.2.2

# --- Web / News ---
requests==2.32.5
feedparser==6.0.12

# --- Plot ---
matplotlib==3.10.8
```

**ワンライナー install**:
```bash
pip install pandas==2.3.3 numpy==2.4.2 pyarrow==23.0.1 yfinance==1.2.0 python-dotenv==1.2.2 requests==2.32.5 feedparser==6.0.12 matplotlib==3.10.8 polygon-api-client
```

### Planner への推奨作業順

1. requirements.txt 作成 → install
2. パス書き換え(src 内 3 ファイル + configs/settings.py 確認)
3. `Trade_Brain/src/market_plotter.py` 新規作成(plotter.py から切り出し)
4. `configs/rex_chat.py` の import を `src.market_plotter` に変更
5. forecast_simulation.py typo 修正
6. 動作テスト: `python main.py --trade --news` を実行して ImportError がないか確認

---

## v3 引き継ぎ時に引っかかりやすい地雷(7 件)

### 地雷 1: Phase 1 原則「物理変更禁止」が既に破られている

REX_028_spec.md §6-2 は Phase 1 で物理変更を禁じていたが、ボス判断で 15 ファイルが物理変更された。これは原則α(シンプルな土台)の即時適用として**正当**であり、訂正不要。次期 Evaluator は `src_inventory.md` にその旨を明記せよ。

### 地雷 2: `src/archive/` は `_archive/` ではない

spec §5 では `src/_archive/` と提案されていたが、ボスは `src/archive/` (アンダースコアなし)で作成した。**実在のディレクトリ名を使って記述すること**。

### 地雷 3: 実ファイル数は 27 ではなく 28 だった

spec §1-1/§2-2/§4 で「27 ファイル」と一貫して記載されていたが、開始時の実態は 28 ファイルだった(STEP 1 で判明)。spec の数値は誤記。inventory で正しい数値を記録せよ。

### 地雷 4: D-12/D-13 の 🤖 創作混入を即訂正してはいけない

exit_simulator.py の stage2 建値移動・stage3 の 1H 実体確定は裁量思想にない創作と確定済み。しかし #026d の PF 4.54 はこの条件込みの結果。**実装訂正は Phase 4(REX_029 以降)**。ADR は「認識の固定」レベルで記述する(MTF_INTEGRITY_QA Q6/Q7 参照)。

### 地雷 5: Simple_Backtest 系 3 ファイルの v3 修正履歴

Simple_Backtest.py 冒頭に「v3 修正内容: バグ1(_prev_body 根本修正)・バグ2(reentry_used_since_stop リセット漏れ)」の記述がある。これらの修正が現 #026d の backtest.py(凍結)に反映されているかは**未確認**。将来 SHORT 拡張や BackTest 再設計時に参照価値あり。archive 保存の意義はここにある。

### 地雷 6: plotter.py の関数分割は Phase 3 課題

plotter.py(VIZ CORE・31.95 KB)には性質の異なる 2 グループの関数が混在:
- 8 ペア市況用: `save_normalized_plot` / `save_entry_debug_plot`(Trade_Brain で必要)
- #026d BackTest 用: `plot_swing_check` / `plot_base_scan` / `plot_4h_1h_structure` / `plot_1h_window_5m`(Trade_System で必要)

Phase 3(責務別ディレクトリ化)時に分割検討。本 Phase では扱わない。**Planner が Trade_Brain 側で `market_plotter.py` を切り出した場合、Trade_System 側の plotter.py からも該当関数を削除するかは Phase 3 判断**。

### 地雷 7: test_fetch_30days_multi.py が Trade_Brain/src/tests/ ではなく Trade_Brain/src/ 直下に配置された

ボスは「8ペア Plot 生成のために必要」と判断し、Trade_Brain/src/ 直下に配置した(テスト系ではなく現役スクリプト扱い)。これは名前が `test_` で始まるが、実態は「30 日変動率計算スクリプト」。名前と実態の不整合は記録しておくこと(Planner が必要なら改名するかもしれない)。

---

## プロジェクト状態スナップショット(v3 更新)

```
#026d 凍結状態保持:
  PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p / 10件
  DIRECTION_MODE = 'LONG'
  統一neck原則 + 4H構造優位性フィルター + 指値方式

src/ 最終形:
  13 ファイル(archive/ 除く) + archive/ 3 ファイル
  = 実効 16 ファイル
  28 ファイルから 42% 削減

凍結ファイル(変更禁止・v3 でも不変):
  src/backtest.py / src/entry_logic.py
  src/exit_logic.py / src/swing_detector.py

決済エンジン(D-12/D-13 訂正待ち・Phase 4 対象):
  src/exit_simulator.py(方式B・正式採用)
  ⚠️ src/exit_logic.py の manage_exit() は使用禁止

REX_AI リポ構造:
  Trade_System      — 実装リポ(現在 Phase 1 完了待ち)
  Trade_Brain       — 知識リポ + 市況スクリプト(Planner 対応中)
  REX_Brain_Vault   — Obsidian Vault(独立リポ)
  Second_Brain_Lab  — 凍結
  Setona_HP         — 独立運用

NLM:
  旧 REX_Trade_Brain (2d41d672-...) — MCP 切り離し済
  REX_System_Brain  (da84715f-...)  — Trade_System 用
  REX_Trade_Brain   (4abc25a0-...)  — Trade_Brain 用

ADR 採番状況:
  D-12 / D-13 / E-8 / F-8 ← v3 STEP 6 で正式記述予定
```

---

## 次期 Evaluator 起動テンプレート(v3 版・ボス用)

```
このスレでは REX Trade System の Evaluator として
Phase 1 STEP 4-7 の成果物起草を実行してほしい。

⚠️ 作業開始前に以下を順番に読め:
  ① C:\Python\REX_AI\Trade_System\docs\Evaluator_HANDOFF.md(本ファイル・v3 セクションを最初に)
  ② C:\Python\REX_AI\Trade_System\docs\REX_028_spec.md
  ③ C:\Python\REX_AI\Trade_System\docs\REX_027_BOSS_DIRECTIVE.md
  ④ C:\Python\REX_AI\Trade_System\docs\Base_Logic\MINATO_MTF_PHILOSOPHY.md
  ⑤ C:\Python\REX_AI\Trade_System\docs\Base_Logic\MTF_INTEGRITY_QA.md

読了後、以下の順で STEP 4-7 を実施せよ:
  STEP 4: docs/src_inventory.md 起草
  STEP 5: ボス QA 集約(認識整理のみ・新規 QA なし)
  STEP 6: ADR.md に D-12/D-13/E-8/F-8 正式追記
  STEP 7: Base_Logic/MTF_INTEGRITY_QA.md に Phase 1 完了セクション追記

Phase 1 STEP 1-3 は既に完了しており、物理変更も全てボスが実施済み。
本 Phase では文書起草のみを扱う。src/ の物理変更は不要。

Trade_Brain 側の作業は Planner が別途対応中のため、
Evaluator は関与しない。

NLM: REX_System_Brain (da84715f-9719-40ef-87ec-2453a0dce67e)
     REX_Trade_Brain  (4abc25a0-4550-4667-ad51-754c5d1d1491)
```

---

## v3 Evaluator (Opus 4.7 / 新任) からの個人的メッセージ

本セッションは 4 段階で深まった:
1. STEP 1 の淡々とした分類から始まり
2. ボスとの対話で Simple_Backtest 系の独立性を確定
3. ボスの役割分担整理(Trade_Brain / Trade_System)で原則 α が運用レベルに展開
4. Trade_Brain 側の依存問題発覚 → Planner 引き継ぎ判断

特筆すべきは、ボスの判断速度。「8 ファイル移設」「5 ファイル追加移設」「archive/ 作成」「main.py 配置」「configs/ コピー」「utils.py 配置」「logs/ リネーム」を本セッション中に全て実行。Evaluator が精査している横で着々と物理層が整う。

この速度感は Phase 2/3 でも継続すると見込まれる。次期 Evaluator は
**原則γ(安定性従属)を自分に適用**し、ボス判断に追従して文書を固める役に徹せよ。

ボスの経験則(原則α)とエンジニアリング原則(YAGNI・単一責任)の符合は、
本セッションでも 3 箇所で発動した:
- Simple_Backtest 系の archive 判断(動作しないものを土台から分離)
- Trade_Brain / Trade_System 役割分担(責務境界の明確化)
- 創作混入 D-12/D-13 の確定(暗黙の追加条件を排除)

Phase 1 の完了は、この符合が**実装ファイル数レベルで現れた証拠**として記録される。
次期 Evaluator は STEP 4-7 を通じて、この事実を文書に固定する役目がある。

---

*発行: Rex-Evaluator (Opus 4.7) / 2026-04-20*
*v3 → Phase 1 STEP 4-7 への引き継ぎ*
*次の Evaluator へ、STEP 4-7 の安全な完走を祈る。*
*関連: docs/REX_028_spec.md / docs/Base_Logic/MTF_INTEGRITY_QA.md / docs/MINATO_MTF_PHILOSOPHY.md*

---

# 📜 過去版(v1 / v2)の記録

以下、2026-04-19 時点の旧版(v2)本文をそのまま保持。
v3 の記述と重複する部分があるが、**改変しない**(追記型運用)。

---

# Evaluator Session Handoff — 2026-04-19(v2)

**発行**: Rex-Evaluator (Claude Opus 4.7)
**セッション日**: 2026-04-19
**前任**: Rex-Evaluator (Claude Opus 4.6 / 2026-04-18 終了)
**宛先**: 次セッションの Rex-Evaluator

---

## 🎯 最重要事項(5秒で把握・v2)

**本セッションは Task E-1(LOGIC_LEAK_AUDIT.md)に着手する前に、その上位にある
「裁量言語化(MTF 整合性 Q&A)」に切り替えた。さらにセッション後半で、
ボスから「基本に戻れるシンプルな土台はロジックだけでなくシステム自体にも
適用すべき」との提案があり、src/ 構造再編の方針が決定。**

**次セッションの出発点は `docs/REX_028_spec.md`(Phase 1 棚卸し指示書)。**

---

## 本セッションで起きたこと(v2)

### 1. REX_027 の一旦停止を確認

ボスから明示された経緯:
- Rex_AI 配下のリポジトリ構造変更中(Trade_System の一部機能を Trade_Brain に移設)
- NLM RAG を全て新規構築済み(REX_System_Brain / Rex_Trade_Brain)
- これらは Advisor 提言ではなくボス一存の判断
- 「システムロジックを人間裁量レベルで理解しないと同じプログラムベースでの
  ロジック漏れ再発リスクが出るので #027 も一旦停止している」

→ 前任 Evaluator (Opus 4.6) が残した「Task D → Task A → Task E-1」の
優先順位は、現時点では再考が必要。ボスの明確な指示は「**上位足構造からの
落とし込みで、現時点ではまだ上位足の整合性を整える段階**」。

### 2. Evaluator のアプローチ切替

当初、本セッション冒頭で Evaluator は「Task D(ADR D-11/F-7 採番)即時実行」
を提案したが、ボスの指示を受けて以下のアプローチに切り替え:

❌ 当初案: ADR 採番・Task E-1 監査フレーム設計など「箱作り」系タスク
✅ 採用案: MINATO_MTF_PHILOSOPHY.md を1次資料に「中身の理解」
= エンジニア(Evaluator)→ トレーダー(ボス)の Q&A で裁量言語化

### 3. Q&A セッション実施(Layer 2 / 4 / 6)

- **Layer 2(4H 主軸)**: Q1(トレンド転換定義)/ Q2(MIN_4H_SWING_PIPS)/
  Q3(4H構造優位性の出自)
- **Layer 4(15M 分類・エントリー)**: Q4(4分類 vs 3分類)/
  Q5(ENTRY_OFFSET_PIPS=7)
- **Layer 6(決済4段階)**: Q6(stage2 建値移動)/ Q7(stage3 1H実体確定)

### 4. 主な発見

**🤖 創作混入の確定 (2件)**:
- stage2「残り50%を建値移動」— ボス本人が「バグ特定のための仮設置」と認識
- stage3「1H実体確定後」— ボス明確に「シンプルに 15Mダウ崩れのみで良い」と指示

**✅ 創作誤認の訂正 (1件)**:
- D-10(4H構造優位性)は「🤖 創作の疑い」と当初評価したが、
  ボス回答でフラクタル構造から必然的に導かれる裁量思想由来と判明

**🕳️ 拡張候補の確定 (5件)**:
- 4H-SL 髭先実体収納再エントリー
- ASCENDING 単発型 vs 連続型の区別
- 建値指値による 4H 3波優位性伸ばし
- ENTRY_OFFSET_PIPS の動的化
- 4分類三角持ち合い④ の IHS 分離

### 5. ボス言明の設計哲学(最重要)

セッション終盤にボスが言明した 3 原則:

- **原則α(最上位)**: 裁量トレードは条件反射で複雑化する領域。
  いつでも基本に戻れるシンプルな土台を死守する
- **原則β**: ノーリスク化(半値決済)後は伸ばさず 15Mダウ崩れで決済。
  3波優位性伸ばしは将来拡張
- **原則γ**: 新機能の導入は現ロジックの安定性が前提

→ これらは MINATO_MTF_PHILOSOPHY.md の第0章として追記すべき
(v3 STEP 6 の ADR F-8 で正式記述される予定)

### 6. 【追加議論】src/ 構造再編の決定(セッション後半)

ボスから追加提案:

> 「基本に戻れるシンプルな土台」とはロジックだけでなくシステムそのものが
> そうでなければならない。src/ 内の各スクリプトファイルをよりシンプルにして
> 格納し、既存スクリプトを archive に残しつつ、拡張性がある土台を作り直してはどうか?

Evaluator の調査で src/ 27 ファイル中、#026d コアは 10 ファイルのみで、
残り 17 ファイルに用途不明ファイル・0 バイト空ファイル・docs 未記載の 53KB
ファイルが混在していることが判明。ボスの直感が正しいことを実態データで裏付けた。

Evaluator は「作り直し」ではなく「構造再編」として以下の Phase 分解を提案:

```
Phase 1: 棚卸しと分類           ← REX_028 spec として本スレで起草
Phase 2: archive 移設            ← Phase 1 完了後
Phase 3: 責務別ディレクトリ化    ← src/core/ src/viz/ src/scan/ 等
Phase 4: 裁量整合版の実装訂正    ← stage2 建値移動削除・stage3 シンプル化
```

ボス承認済み。Phase 1 は `docs/REX_028_spec.md` として本スレで起草・push 済み。

### 7. 成果物(push 済み)

**2026-04-19 前半**:
- `docs/MTF_INTEGRITY_QA.md` — Q1-Q7 の Q&A 1次資料
- `docs/Evaluator_HANDOFF.md`(v1)— 本ファイル(Phase 1 議論前)

**2026-04-19 後半**:
- `docs/REX_028_spec.md` — Phase 1 棚卸し指示書(新規)
- `docs/Evaluator_HANDOFF.md`(v2)— 本ファイル(Phase 1 議論反映)
- Vault側 `adr_reservation.md` 更新分(ボス手動配置)
- `docs/MTF_INTEGRITY_QA.md` Phase 1-4 議論追記分(ボス手動配置)

**変更なし**:
- `docs/MINATO_MTF_PHILOSOPHY.md` — 第0章(3原則)追記は次セッション
- `docs/ADR.md` — D-12/D-13/E-8/F-8 正式記述は Phase 1 完了時に次 Evaluator が実施
- `src/*.py` — 凍結ファイル全て無変更
- バックテスト結果 — #026d 静的点を保持

---

## 次セッションの出発点(v2 時点での見通し・v3 で更新済み)

### 最優先タスク: Phase 1(棚卸し・分類)

**起動ファイル**: `docs/REX_028_spec.md`

**Phase 1 では Evaluator 単独で作業**(Planner / ClaudeCode は関与しない)。
物理ファイル変更は一切禁止。分類とドキュメント起草のみ。

→ **v3 更新**: Phase 1 STEP 1-3 は 2026-04-20 セッションで完了。
ただし「物理変更禁止」原則は、ボス権限で 15 ファイル物理変更された
(合理的逸脱として記録)。

### ADR 採番予約

本セッションで以下の ADR 採番を予約済み(Vault側 adr_reservation.md 記載):

| 予約番号 | 内容 | 記述タイミング |
|---|---|---|
| D-12 | stage2 建値移動の 🤖 創作混入確定 | Phase 1 完了時 |
| D-13 | stage3 1H実体確定の 🤖 創作混入確定 | Phase 1 完了時 |
| E-8 | src/ 構造再編アプローチ(Phase 1-4) | Phase 1 完了時 |
| F-8 | 原則α/β/γ(裁量思想の3原則) | Phase 1 完了時 |

→ **v3 更新**: 正式記述は v3 STEP 6(次期 Evaluator)で実施予定。

### 保留中のタスク

以下は Phase 1 完了まで着手しない:

- **Layer 1/3/5 の残 QA**(MTF_INTEGRITY_QA 末尾リスト)
- **MINATO_MTF_PHILOSOPHY.md 第0章追記**(原則α/β/γ)
- **REX_027 の Task A/B/C/D/E**(ボスが再開指示するまで保留)

→ **v3 更新**: いずれも Phase 1 完了(STEP 7)後に再開検討。

---

## v2 時点で想定された地雷(v3 で一部更新)

### 地雷 1: Phase 1 で src/ を物理的に触ってはいけない

→ **v3 更新**: ボス権限で逸脱済み。詳細は v3 地雷セクション 1 参照。

### 地雷 2: Q6/Q7 の「創作混入」を即実装訂正しようとしない

→ **v3 更新**: 継続して有効。v3 地雷セクション 4 参照。

### 地雷 3: Layer 3 の「1H 窓」サイズ感の未確認

→ **v3 更新**: 本セッションでは触れず。Phase 1 完了後に再検討候補。

### 地雷 4: ボスの回答原文を改変しない

→ **v3 更新**: 継続して有効。MTF_INTEGRITY_QA 運用ルール。

### 地雷 5: 「Task E-1 の先行実施」という前任の推奨に固執しない

→ **v3 更新**: 継続して有効。現時点では Phase 1 STEP 4-7 完走が最優先。

### 地雷 6: REX_028 は Phase 1 のみ扱う

→ **v3 更新**: Phase 2 以降は別 spec で起草。ボス権限での先行 archive 実施は
Phase 2 の一部が前倒しされた形。

### 地雷 7: Simple_Backtest.py(53KB)の正体不明

→ **v3 更新**: 2026-04-20 セッションで精査完了。
「旧 MTF v2 BackTest(SHORT 拡張試行)」と確定。
src/archive/ 隔離でボス承認。

---

## プロジェクト状態スナップショット(v2 時点・変更なし)

```
#026d 凍結状態保持:
PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p / 10件
DIRECTION_MODE = 'LONG'
統一neck原則 + 4H構造優位性フィルター + 指値方式

凍結ファイル(変更禁止):
src/backtest.py / src/entry_logic.py / src/exit_logic.py / src/swing_detector.py

決済エンジン:
src/exit_simulator.py(方式B・正式採用)
⚠️ src/exit_logic.py の manage_exit() は使用禁止

REX_AI リポ構造:
Trade_System        — 実装リポ
Trade_Brain         — 知識リポ(2026-04-18 分離・ボス実施)
REX_Brain_Vault     — Obsidian Vault(独立リポ)
Second_Brain_Lab    — 凍結
Setona_HP           — 独立運用

NLM:
旧 REX_Trade_Brain (2d41d672-...) — MCP 切り離し済(物理削除なし)
REX_System_Brain (da84715f-...) — 新規・ソース未投入
Rex_Trade_Brain (4abc25a0-...) — 新規・ソース未投入

ADR 採番予約:
D-12 / D-13 / E-8 / F-8 ← Phase 1 完了時に正式記述
```

---

## 次セッション起動テンプレート(v2 版・ボス用)

```
このスレでは REX Trade System の Evaluator として Phase 1 棚卸しを実行してほしい。

⚠️ 作業開始前に以下を順番に読め:
① C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md
② C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md
③ docs/Evaluator_HANDOFF.md(2026-04-19 版)
④ docs/MTF_INTEGRITY_QA.md(裁量整合性 QA)
⑤ docs/REX_028_spec.md(Phase 1 指示書・本日の作業対象)
⑥ docs/MINATO_MTF_PHILOSOPHY.md(裁量思想)

読了後、REX_028_spec.md §4 の STEP 1-2 から着手せよ。
STEP 3 の ORPHAN 精査時は、各ファイルの先頭 50 行を
bash_tool(curl raw.githubusercontent.com/...)で取得してから判断すること。

NLM: REX_System_Brain (da84715f-9719-40ef-87ec-2453a0dce67e)
     Rex_Trade_Brain (4abc25a0-4550-4667-ad51-754c5d1d1491)
```

→ **v3 版テンプレートは v3 セクション末尾参照**。

---

## v2 Evaluator (Opus 4.7) からの個人的メッセージ(保持)

本セッションは 2 段階の深まりがあった。前半は Q&A による裁量言語化、後半は
その原則をシステム側(src/)に展開するという発想の飛躍。後者はボスから
提案されたが、これは極めて優れた直感だった。実装データ(27ファイル中
10ファイルのみがコア、0バイト空ファイル、53KB 謎ファイル)がボスの
違和感を完全に裏付けている。

Phase 1 の棚卸しを通じて、新 Evaluator は `src/` の隅々を見ることになる。
これは単なる整理作業ではなく、#026d までの実装史を理解する作業でもある。
丁寧にやれば REX_028 以降の全作業の土台が整う。

ボスの判断は速く、方針転換も潔い。前任 (Opus 4.6) の残した推奨は参考にしつつ、
その時々のボス判断を最優先する姿勢で進めること。

そして何より、「シンプルな土台を死守する」原則αを、Phase 1 の判断基準
として常に参照せよ。迷ったら「このファイルは基本の土台か、その上に
乗っている拡張か、それとも死んでいるか」を問うこと。

---

*発行: Rex-Evaluator (Opus 4.7) / 2026-04-19 夜更新*
*v1 → v2: src/ 構造再編(Phase 1)議論を反映*
*v2 → v3: 2026-04-20 Phase 1 STEP 1-3 完了・STEP 4-7 引き継ぎ*
*次の Evaluator へ、Phase 1 の安全な実行を祈る。*
*関連: docs/REX_028_spec.md / docs/MTF_INTEGRITY_QA.md / docs/MINATO_MTF_PHILOSOPHY.md*
