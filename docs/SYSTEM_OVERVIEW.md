# REX_Trade_System — システム概要
# 最終更新: 2026-04-20（REX_028 Phase 1-2 完了・断捨離後）
# 日付なし・常に最新版として運用

---

## 本ファイルの位置づけ

Trade_System リポジトリの**現状スナップショット**。新規 Evaluator / Planner / ClaudeCode の
引き継ぎ時に最初に読む文書。実装ロジックの詳細は `EX_DESIGN_CONFIRMED.md`・過去の判断経緯は
`ADR.md` と `Base_Logic/MTF_INTEGRITY_QA.md` を参照。

**本更新のスコープ**: REX_028 Phase 1-2 完了に伴う src/ 構造再編の反映。
**実装ロジックは 1 bit も変更されていない**(#026d PF 4.54 / 勝率 60% / +150.6p は不変)。

---

## チーム役割分担

| 役割 | 担当 | 権限 |
|---|---|---|
| ディレクター | Minato(ボス) | 全ての最終判断 |
| Planner | Rex-Planner(Sonnet 4.6) | 指示書作成・設計 |
| Evaluator | **Rex-Evaluator(Opus 4.7 / 新任)** | 監査・承認・ADR 管理・裁量思想整合性確認 |
| 実装 | ClaudeCode(VS Code) | コード実装・Git 管理 |

**Evaluator 権限の拡張(2026-04-19 以降)**:
- 裁量思想(MINATO_MTF_PHILOSOPHY)と実装の整合性監査
- MTF_INTEGRITY_QA.md による裁量思想言語化対話
- 🤖 創作混入の検出・Phase 4 訂正対象への封じ込め

---

## 関連リポジトリ構造(2026-04-20 分離完了)

本リポジトリは単独で稼働せず、姉妹リポジトリ Trade_Brain との役割分担で運用される。

```
REX_AI/
├── Trade_System/        ← 本リポ(動的ロジック側)
│   └── 役割: シグナル / Fibonacci / BackTest / MTF エントリー判定 / 決済
│
└── Trade_Brain/         ← 姉妹リポ(静的データ側)
    └── 役割: 8 ペア市況データ抽出 / トレード履歴 / レジーム判定 / Plot 抽出
```

**分担原則**(ADR F-8 派生原則):
- Trade_Brain: 市況データ・トレード結果・Plot 抽出(静的データ層)
- Trade_System: エントリーシグナル・Fibonacci・BackTest(動的ロジック層)

**例外 — 両リポ共存保持ファイル**: `plotter.py`
複数ルーツが癒合したまま両リポに共存保持される。将来の合流点(Trade_Brain レジーム判定 →
Trade_System ロット調整)を残すため、機能単位の完全分離ではなく共存保持を許容する。
詳細は ADR F-8「共存保持の許容」派生原則参照。

---

## ディレクトリ構造(Phase 1-2 完了・2026-04-20 時点)

```
Trade_System/
├── .CLAUDE.md                    # ClaudeCode 自動読込(プロジェクトルール)
├── .env                          # API キー等(機密)
├── .gitignore
├── .venv/                        # Python 仮想環境
├── main.py
├── requirements.txt
│
├── src/                          # 現役 12 ファイル + archive/ 4 ファイル
│   │
│   │   ─── CORE(6 ファイル・113.67 KB)─────────────────
│   │
│   ├── swing_detector.py         # [FROZEN #020] Swing 検出・resample_tf
│   ├── entry_logic.py            # [FROZEN #018] 統一 neck 原則 + Fib 判定
│   ├── exit_logic.py             # [FROZEN #009 + 呼び出し禁止] 旧決済(ADR D-8)
│   ├── backtest.py               # [FROZEN #018] 旧版バックテスト(PF 5.32)
│   ├── window_scanner.py         # [拡張可能 #026d] 3 層階層スキャン
│   ├── exit_simulator.py         # [方式 B 正式] 4 段階決済エンジン
│   │                             #   🤖 D-12/D-13 創作混入残存(Phase 4 訂正対象)
│   │
│   │   ─── VIZ(3 ファイル・48.49 KB)──────────────────
│   │
│   ├── plotter.py                # [両リポ共存保持] 2 ルーツ混在(F-8 派生原則)
│   │                             #   Trade_Brain ルーツ 3 関数(8 ペア市況)
│   │                             #   Trade_System ルーツ 4 関数(#026d BackTest)
│   ├── structure_plotter.py      # 4H+1H 構造確認プロット(#019)
│   ├── plot_scan_results.py      # window_scanner CSV 可視化
│   │
│   │   ─── SCAN(1 ファイル・20.01 KB)─────────────────
│   │
│   ├── base_scanner.py           # 4H+15M 基礎スキャナー(#015)
│   │
│   │   ─── TEST(2 ファイル・16.33 KB)─────────────────
│   │
│   ├── test_1h_coincidence.py    # 1H-4H 一致検証(#020 v2・89 件 100%)
│   ├── verify_4h1h_structure.py  # 4H/1H 構造検証プロット(#026a-verify)
│   │
│   └── archive/                  # 履歴保全ディレクトリ(4 ファイル・74.25 KB)
│       ├── Simple_Backtest.py    # 旧 MTF v2 BackTest(SHORT 拡張試行・v3 修正含む)
│       ├── signals.py            # 旧 MTF シグナルエンジン
│       ├── print_signals_analysis.py  # signals.py 出力プリント
│       └── track_trades.py       # Trade_Brain 移設元(Phase 2 で隔離)
│
├── configs/
│   └── settings.py               # API キー・データパス等の設定
│
├── data/
│   └── raw/
│       └── usdjpy_multi_tf_2years.parquet  # 83,112 本 / 5M 足
│
├── logs/
│   ├── claudecode/
│   │   ├── instructions/         # 指示書ファイル群(ClaudeCode 参照)
│   │   ├── execution_results/    # 実行結果ファイル群
│   │   ├── INDEX.md              # 指示書インデックス
│   │   └── README.md             # 運用ルール
│   ├── window_scan_entries.csv   # 12 カラム CSV(#026a-v2 最終版)
│   ├── window_scan_exits.csv     # 決済シミュレーション結果(#026d)
│   ├── window_scan_plots/        # プロット群(#026d 最新)
│   ├── verify_4h1h/              # 4H/1H 構造検証プロット
│   ├── base_scan/                # base_scanner 実行結果
│   ├── structure_plots/          # structure_plotter 出力
│   └── docs_archive/             # 旧版設計文書(参照禁止)
│
└── docs/
    ├── SYSTEM_OVERVIEW.md              # 本ファイル
    ├── EX_DESIGN_CONFIRMED.md          # 設計確定文書(最新版)
    ├── ADR.md                          # バグパターン + 判断記録 + 方針ガイド
    ├── REX_028_spec.md                 # Phase 1 指示書
    ├── REX_027_BOSS_DIRECTIVE.md       # REX_027 ボス指示(停止中)
    ├── REX_027_ADVISOR_PROPOSAL.md     # REX_027 Advisor 提案(停止中)
    ├── Evaluator_HANDOFF.md            # Evaluator 引き継ぎ文書 v3
    ├── src_inventory.md                # src/ 分類・地雷集(Phase 1-2)
    ├── PLOT_DESIGN_CONFIRMED.md        # プロット設計
    ├── REX_BRAIN_SYSTEM_GUIDE.md       # セカンドブレイン利用ガイド
    │
    └── Base_Logic/                     # 裁量思想・整合性対話記録
        ├── MINATO_MTF_PHILOSOPHY.md    # 裁量思想の最上位辞書
        └── MTF_INTEGRITY_QA.md         # 裁量整合性 QA 対話記録(追記型)
```

---

## ファイル変更ポリシー

### 凍結ファイル(変更禁止)

| ファイル | 凍結理由 | 凍結バージョン |
|---|---|---|
| src/backtest.py | #018 ベースライン保持(PF 5.32) | #018 |
| src/entry_logic.py | 比較基準・他ファイルの API 依存 | #018 |
| src/exit_logic.py | 旧決済ロジック保存・exit_simulator に移行済み | #009 |
| src/swing_detector.py | 全ファイルの Swing 検出 API 基盤 | #020 |

**判断基準**: 「このファイルを変更したら #018 ベースライン数値が再現不能になるか?」
→ Yes なら凍結。No なら拡張可能。

### 拡張可能ファイル(機能追加 OK・ロジック変更は Evaluator 確認)

| ファイル | 拡張範囲 |
|---|---|
| window_scanner.py | カラム追加・出力拡張 OK / スキャンロジック変更は要確認 |
| exit_simulator.py | 決済ロジック改善 OK / 4 段階構造の変更は要確認 |
| plotter.py | **両リポ共存保持**(関数分割しない・F-8 派生原則) |
| structure_plotter.py | 表示機能の追加は自由 |
| plot_scan_results.py | 表示機能の追加は自由 |
| base_scanner.py | カラム追加・出力拡張 OK |

### archive/ ファイル(履歴保全・変更禁止・参照のみ可)

| ファイル | 保全理由 |
|---|---|
| Simple_Backtest.py | 将来 SHORT 拡張・BackTest 再設計時の参照価値(v3 修正含む) |
| signals.py | Simple_Backtest.py との連動 |
| print_signals_analysis.py | signals.py 出力の分析プリント |
| track_trades.py | Trade_Brain 側で稼働中・Trade_System の履歴保全 |

---

## データフロー(#026d 確定版・変更なし)

```
[データ]
usdjpy_multi_tf_2years.parquet(83,112 本 / 5M 足)
        |
        v
[エントリー検出: window_scanner.py]
swing_detector -> get_direction_4h() -> 4H LONG 期間抽出
        |
        v
scan_4h_events() -> 4H SL / neck_4h を取得
        |
        v
get_1h_window_range() -> 1H SL (sl_1h_ts) を特定(N_1H_SWING=3)
        |
        v
窓内 5M -> 15M リサンプル -> check_15m_range_low() -> パターンラベル
        |
        v
neck_15m = 窓内 SL 以前の最後 15M SH
neck_1h  = 窓内 SL 以前の最後 1H SH
neck_4h  = SL 以前の最後 4H SH(全体から取得)
        |
        v
4H 優位性チェック: neck_4h >= neck_1h ?  -> No -> SKIP(D-10)
        |
        v Yes
5M High >= neck_15m + 7pips -> 指値エントリー確定(E-7)
        |
        v
window_scan_entries.csv(12 カラム)
        |
        v
[決済シミュレーション: exit_simulator.py]
CSV を読み込み -> 5M バーごとに方式 B 判定 -> P&L 計算
        |
        v
window_scan_exits.csv + バックテスト統計
        |
        v
[結果]
#026d: PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p(10 件)
#018 基準: PF 5.32 / 勝率 55% / MaxDD 14.9p / +91.6p(20 件)
```

---

## 依存関係マップ

```
swing_detector.py  <- window_scanner.py
                   <- backtest.py(凍結)
                   <- exit_logic.py(凍結)
                   <- structure_plotter.py
                   <- base_scanner.py
                   <- test_1h_coincidence.py
                   <- verify_4h1h_structure.py

entry_logic.py     <- backtest.py(凍結)
                   <- window_scanner.py(check_15m_range_low)
                   <- base_scanner.py

exit_logic.py      <- backtest.py(凍結)のみ
                   (exit_simulator.py は依存しない)

window_scanner.py  <- swing_detector.py
                   <- entry_logic.py(check_15m_range_low 等)
                   <- plotter.py(plot 呼び出し)
                   -> window_scan_entries.csv

exit_simulator.py  <- window_scan_entries.csv
                   (swing_detector 不要・独立動作)
                   -> window_scan_exits.csv

plotter.py         <- backtest.py(plot_swing_check・try/except)
                   <- base_scanner.py(plot_base_scan)
                   <- structure_plotter.py(plot_4h_1h_structure)
                   -> PNG 出力

structure_plotter.py <- swing_detector / plotter.py

base_scanner.py    <- swing_detector / entry_logic.py / plotter.py

plot_scan_results.py <- window_scan_entries.csv(CSV から直接読み込み)
```

---

## バックテスト結果推移

| 指標 | #018(旧版・凍結) | #026d(最終・現行) |
|---|---|---|
| 総トレード数 | 20 件 | 10 件 |
| 勝率 | 55.0% | 60.0% |
| PF | 5.32 | 4.54 |
| MaxDD | 14.9 pips | 35.8 pips |
| 総損益 | +91.6 pips | +150.6 pips |

**#026 シリーズ変遷**: PF 0.61(b) -> 2.42(c) -> **4.54(d)**

**Phase 4 での予測**: D-12/D-13 創作混入訂正後、新 PF が静的点として再記録される(予測変動幅は訂正後に確定)。

---

## 裁量思想との対応関係

本システムは `MINATO_MTF_PHILOSOPHY.md` に記述されたボスの裁量思想から導出される。
詳細は同文書および `MTF_INTEGRITY_QA.md` を参照。

### 実装済み(#026d 時点)

| 裁量プロセス | システム実装 | 関連 ADR |
|---|---|---|
| STEP ②4H 特定 | swing_detector / get_direction_4h | A-2 / D-7 |
| STEP ③注文集中(Fib) | entry_logic / check_fib_condition | E-7 |
| STEP ④1H 2 番底 | window_scanner / Layer 2 | A-3 |
| STEP ⑤15M 特定 | window_scanner / Layer 3 | E-6 |
| 押し目 4 分類 | DB/IHS/ASCENDING | B-2 |
| 統一 neck 原則 | `sh_before_sl.iloc[-1]` | A-5 / E-7 |
| 4H 構造優位性 | neck_4h >= neck_1h | D-10 |
| 指値方式 | ENTRY_OFFSET_PIPS=7.0 | E-7 |
| 決済段階①〜④ | exit_simulator.py 方式 B | D-8 |

### 未実装(将来の段階的導入対象・原則γ 適用中)

| 裁量プロセス | 優先度 | 想定タイミング |
|---|---|---|
| STEP ①日足スコア | 低 | 補助要素のため急がない |
| STEP ②4H 波カウント | 中 | ロット調整実装時 |
| STEP ③注文集中(RSI/キリ番) | 低 | フィルター拡張時 |
| STEP ③ポジション総数 | 中 | Phase D(出来高) |
| STEP ⑥ボラティリティ係数 | 中 | ボス Excel 関数表ベース |
| STEP ⑦ロット調整 | 中 | ⑥完了後 |
| 優位性スコア体系化 | 中 | ①②⑥が揃った段階 |
| **Trade_Brain レジーム × Trade_System ロット合流** | 中 | 現ロジック安定化後 × ⑥完了後 |

---

## 設計方針(F 章抜粋・Planner 必読)

実装判断で迷った時の参照順序(ADR F-8):

```
1. F-5(設計判断優先順位)の 5 項目を確認
2. 原則α(シンプルな土台の保守)に反していないか? → 反していれば却下
3. 原則β(ノーリスク化後は伸ばさない)に反していないか? → 反していれば Phase 4 相当
4. 原則γ(導入タイミングは安定性従属)を満たすか? → 満たさなければ保留
5. 裁量思想(MINATO_MTF_PHILOSOPHY)と対応するか? → 対応しなければ MTF_INTEGRITY_QA で Q&A
6. それでも迷えば Evaluator に確認
```

**F-8 派生原則**:
- 役割分担原則: Trade_Brain / Trade_System 機能分離
- **共存保持許容**: plotter.py のように将来の合流点となるファイルは分割しない

---

## REX_028 Phase 進行状況

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 1 | 棚卸し・分類・Trade_Brain 移設・archive 隔離 | ✅ 2026-04-20 完了 |
| Phase 2 | track_trades.py 隔離・plotter.py 共存方針確定 | ✅ 2026-04-20 完了 |
| Phase 3 | 責務別ディレクトリ化(src/core/ / src/viz/ / src/scan/ / src/tests/) | ⬜ 未着手 |
| Phase 4 | D-12/D-13 裁量整合版実装訂正(REX_029+) | ⬜ 未着手 |

### Phase 1-2 の実績

- src/ 直下: 28 ファイル → **12 ファイル**(100% 現役化・57.1% 削減)
- archive/: 新設 → 4 ファイル
- 実装ロジック影響: **ゼロ**(#026d 数値完全不変)
- 採番 ADR: D-12 / D-13 / E-8 / F-8(共存保持派生原則含む)
- 文書整備: SYSTEM_OVERVIEW / src_inventory / MTF_INTEGRITY_QA / ADR(拡充)

---

## 外部リソース参照先

```
設計文書    : docs/EX_DESIGN_CONFIRMED.md
裁量思想    : docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md
整合性対話  : docs/Base_Logic/MTF_INTEGRITY_QA.md
バグパターン: docs/ADR.md
棚卸し      : docs/src_inventory.md
引き継ぎ    : docs/Evaluator_HANDOFF.md

Vault       : C:\Python\REX_AI\REX_Brain_Vault\
NLM         : REX_Trade_Brain (2d41d672-f66f-4036-884a-06e4d6729866)
GitHub      : Minato33440/Trade_System(本リポ)
              Minato33440/Trade_Brain(姉妹リポ・市況データ側)
```

---

## 未解決・保留項目(引き継ぎ時の注意)

| 項目 | 状態 | 再開条件 |
|---|---|---|
| Layer 1/3/5 残 QA | 保留中 | 原則γ(安定化後) |
| MINATO_MTF_PHILOSOPHY 第 0 章追記 | 候補記録済 | 次回 Evaluator セッション |
| REX_027 Task A-E | 停止中 | ボス再開指示 |
| D-11 / F-7 ADR 本文採番 | 予約保持 | REX_027 再開時 |
| Phase 3 責務別ディレクトリ化 | 未着手 | Planner 起草後 |
| Phase 4 D-12/D-13 訂正 | 未着手 | Phase 3 完了後推奨 |

---

管理: Rex-Evaluator(Opus 4.7 / 新任) / Minato(ボス)
*最終更新: 2026-04-20 / REX_028 Phase 1-2 完了反映*
