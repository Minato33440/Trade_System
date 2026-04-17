# REX_Trade_System — システム概要
# 最終更新: 2026-04-17（#026d完了版）
# 日付なし・常に最新版として運用

---

## チーム役割分担

| 役割 | 担当 | 権限 |
|---|---|---|
| ディレクター | Minato（ボス） | 全ての最終判断 |
| Planner | Rex-Planner（Sonnet 4.6） | 指示書作成・設計 |
| Evaluator | Rex-Evaluator（Opus 4.6） | 監査・承認・ADR管理 |
| 実装 | ClaudeCode（Sonnet 4.6） | コード実装・Git管理 |

---

## ディレクトリ構造（#026d時点）

```
Trade_System/
├── .CLAUDE.md                    # ClaudeCode自動読込（プロジェクトルール）
├── .env                          # APIキー等（機密）
├── .gitignore
├── .venv/                        # Python仮想環境
├── main.py
├── requirements.txt
│
├── src/                          # コアモジュール
│   [凍結ファイル]
│   ├── swing_detector.py         # [FROZEN #020] Swing検出・resample_tf
│   ├── entry_logic.py            # [FROZEN #018] エントリー3ステップ検証
│   ├── exit_logic.py             # [FROZEN #009] 旧決済ロジック（呼び出し禁止）
│   ├── backtest.py               # [FROZEN #018] 旧版バックテスト（PF 5.32）
│
│   [拡張可能ファイル]
│   ├── window_scanner.py         # [拡張可能] 窓ベース階層スキャン（#026d最新）
│   │                               4H SL/SH -> 1H窓 -> 15M/5Mスキャン
│   │                               12カラムCSV出力（neck_15m/neck_1h/neck_4h含む）
│   │                               4H構造優位性フィルター（neck_4h >= neck_1h）
│   ├── exit_simulator.py         # [拡張可能] 方式B決済エンジン（#026b新設・正式採用）
│   │                               exit_logic.pyに依存しない独立実装
│   │                               4段階決済シミュレーション
│   ├── plotter.py                # [拡張可能] チャート生成（#020-fix適用済み）
│   ├── structure_plotter.py      # [拡張可能] 4H+1H構造確認プロット（#019）
│
│   [完了・参照用]
│   ├── base_scanner.py           # 4H+15M基礎スキャナー（#015）
│   ├── test_1h_coincidence.py    # 1H-4H一致検証（#020 v2・89件100%）
│   ├── verify_4h1h_structure.py  # 4H/1H構造検証プロット（#026a-verify）
│
│   [未着手]
│   ├── volume_alert.py           # 出来高急増検知+LINE通知（Phase D）
│
│   [廃止方向]
│   └── signals.py                # 旧MTFシグナルエンジン（廃止予定）
│
├── data/
│   └── raw/
│       └── usdjpy_multi_tf_2years.parquet  # 83,112本 / 5M足
│
├── logs/
│   ├── claudecode/
│   │   ├── instructions/         # 指示書ファイル群（ClaudeCode参照）
│   │   ├── execution_results/    # 実行結果ファイル群
│   │   ├── INDEX.md              # 指示書インデックス
│   │   └── README.md             # 運用ルール
│   ├── window_scan_entries.csv   # 12カラムCSV（#026a-v2最終版）
│   ├── window_scan_exits.csv     # 決済シミュレーション結果（#026b）
│   ├── window_scan_plots/        # プロット群（#026d最新）
│   ├── verify_4h1h/              # 4H/1H構造検証プロット
│   └── docs_archive/             # 旧版設計文書（参照禁止）
│
└── docs/
    ├── EX_DESIGN_CONFIRMED.md    # 設計確定文書（最新版・本ファイルと併読）
    ├── ADR-2026-04-14_2_2.md     # バグパターン集+方針ガイド（Evaluator統合作業中）
    ├── PLOT_DESIGN_CONFIRMED-2026-3-31.md  # プロット設計（有効）
    ├── REX_BRAIN_SYSTEM_GUIDE.md # セカンドブレインシステム利用ガイド（有効）
    └── SYSTEM_OVERVIEW.md        # 本ファイル
```

---

## ファイル変更ポリシー

### 凍結ファイル（変更禁止）

| ファイル | 凍結理由 | 凍結バージョン |
|---|---|---|
| src/backtest.py | #018ベースライン保持（PF 5.32） | #018 |
| src/entry_logic.py | 比較基準・他ファイルのAPI依存 | #018 |
| src/exit_logic.py | 旧決済ロジック保存・exit_simulatorに移行済み | #009 |
| src/swing_detector.py | 全ファイルのSwing検出API基盤 | #020 |

判断基準: 「このファイルを変更したら#018ベースライン数値が再現不能になるか？」
-> Yes なら凍結。No なら拡張可能。

### 拡張可能ファイル（機能追加OK・ロジック変更はEvaluator確認）

| ファイル | 拡張範囲 |
|---|---|
| window_scanner.py | カラム追加・出力拡張OK / スキャンロジック変更は要確認 |
| exit_simulator.py | 決済ロジック改善OK / 基本4段階構造の変更は要確認 |
| plotter.py | 表示機能の追加は自由 |
| structure_plotter.py | 表示機能の追加は自由 |

---

## データフロー（#026d確定版）

```
[データ]
usdjpy_multi_tf_2years.parquet（83,112本 / 5M足）
        |
        v
[エントリー検出: window_scanner.py]
swing_detector -> get_direction_4h() -> 4H LONG期間抽出
        |
        v
scan_4h_events() -> 4H SL / neck_4h を取得
        |
        v
get_1h_window_range() -> 1H SL (sl_1h_ts) を特定（N_1H_SWING=3）
        |
        v
窓内5M -> 15Mリサンプル -> check_15m_range_low() -> パターンラベル
        |
        v
neck_15m = 窓内 SL以前の最後15M SH
neck_1h  = 窓内 SL以前の最後1H SH
neck_4h  = SL以前の最後4H SH
        |
        v
4H優位性チェック: neck_4h >= neck_1h ?  -> No -> SKIP
        |
        v Yes
5M High >= neck_15m + 7pips -> エントリー確定
        |
        v
window_scan_entries.csv（12カラム）
        |
        v
[決済シミュレーション: exit_simulator.py]
CSVを読み込み -> 5Mバーごとに方式B判定 -> P&L計算
        |
        v
window_scan_exits.csv + バックテスト統計
        |
        v
[結果]
#026d: PF 4.54 / 勝率60% / MaxDD 35.8p / +150.6p（10件）
#018基準: PF 5.32 / 勝率55% / MaxDD 14.9p / +91.6p（20件）
```

---

## 依存関係マップ

```
swing_detector.py  <- window_scanner.py
                   <- backtest.py（凍結）
                   <- exit_logic.py（凍結）
                   <- structure_plotter.py
                   <- test_1h_coincidence.py
                   <- verify_4h1h_structure.py

entry_logic.py     <- backtest.py（凍結）のみ

exit_logic.py      <- backtest.py（凍結）のみ
                   （exit_simulator.pyは依存しない）

window_scanner.py  <- swing_detector.py
                   <- entry_logic.py（check_15m_range_low等）
                   -> window_scan_entries.csv

exit_simulator.py  <- window_scan_entries.csv
                   （swing_detector不要・独立動作）
                   -> window_scan_exits.csv
```

---

## バックテスト結果推移

| 指標 | #018（旧版・凍結） | #026d（最終） |
|---|---|---|
| 総トレード数 | 20件 | 10件 |
| 勝率 | 55.0% | 60.0% |
| PF | 5.32 | 4.54 |
| MaxDD | 14.9 pips | 35.8 pips |
| 総損益 | +91.6 pips | +150.6 pips |

#026シリーズ変遷: PF 0.61(b) -> 2.42(c) -> 4.54(d)

---

## 外部リソース参照先

```
設計文書: docs/EX_DESIGN_CONFIRMED.md
バグパターン: docs/ADR-2026-04-14_2_2.md（NLMにも投入済み）
Vault: C:\Python\REX_AI\REX_Brain_Vault\
NLM: REX_Trade_Brain (2d41d672-f66f-4036-884a-06e4d6729866)
GitHub: Minato33440/Trade_System
```

---

管理: Rex（設計責任者）/ Minato（ボス）
