# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-04-17
# バージョン: #026d完了版（日付なし・常に最新版として運用）
# 保存先: Trade_System/docs/EX_DESIGN_CONFIRMED.md

---

## 1. プロジェクト基本情報

- リポジトリ: GitHub Minato33440/Trade_System
- ローカルパス: C:\Python\REX_AI\Trade_System\
- 対象通貨ペア: USDJPY（将来的に他ペアへ拡張予定）
- データ: data/raw/usdjpy_multi_tf_2years.parquet
  83,112本 / 5M足 / 期間: 2024-03-13〜2026-03-13

---

## 2. チーム役割分担

| 役割 | 担当 |
|---|---|
| ディレクター・意思決定 | Minato（ボス） |
| Planner（設計・指示書作成） | Rex-Planner（Sonnet 4.6） |
| Evaluator（監査・ADR管理） | Rex-Evaluator（Opus 4.6） |
| コード実装・Git管理 | ClaudeCode（Sonnet 4.6 / VS Code） |

---

## 3. ミナト流MTF短期売買ルール（確定定義・#026d版）

### 3-1. 戦略の本質

「4H上昇ダウが継続している限り、押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

---

### 3-2. MTF 階層スキャン構造（#026d確定版）

```
LAYER 1 — 4H 上昇トレンド
  SH/SL 高値・安値切り上げ確認（上昇ダウ）
  → ダウ崩れまでの各 4H SL が押し目候補
  params: n=3, lookback=20, MIN_4H_SWING_PIPS>=20

LAYER 2 — 1H 押し目ウィンドウ（#026a-v2 1H n=3に変更確定）
  4H SL ts +-8本(8時間)窓内で最近傍 1H SL を探す
  -> 1H SL 足: 前20本 + SL足 + 後10本 = 計31本ウィンドウ確定
  ウィンドウ = 約31時間分の 5M 足（約372本）
  1H Swing検出粒度: n=3（#026a-v2 確定 / ADR D-7）

LAYER 3 — 窓内 15M/5M スキャン（#026a統一neck原則）
  窓内 5M -> 15M リサンプル
  -> check_15m_range_low() でDB/IHS/ASCENDINGパターンラベル取得
     （この関数はパターン判定のみ。neckは独立計算）
  -> neck_15m = 窓内 かつ sl_1h_ts以前 の最後の15M SH
  -> 5M High >= neck_15m + ENTRY_OFFSET_PIPS（指値方式 #026c）
```

---

### 3-3. 統一neck原則（#026a確定・全TF共通 / ADR F-6）

定義: neck = SL直前（時系列で左側）の最後のSH

```python
# 全タイムフレームで同一原則を適用
sh_before = sh_vals[sh_vals.index < sl_ts]
neck = float(sh_before.iloc[-1])  # 最後（SLに最も近いSH）
```

| TF | neck定義 | 窓限定 |
|---|---|---|
| neck_15m | 窓内 かつ sl_1h_ts以前 の最後の15M SH | 窓内のみ |
| neck_1h | 窓内 かつ sl_1h_ts以前 の最後の1H SH | 窓内のみ |
| neck_4h | sl_4h_ts以前 の最後の4H SH | 全体OK |

各neckの用途:
```
neck_15m — エントリートリガー（指値の基準値）
neck_1h  — 窓特定アンカー（決済トリガーではない）
neck_4h  — 半値決済トリガー（段階2: High >= neck_4h -> 50%決済）
```

旧定義（#025 固定ネック）との違い:
```
旧（#025）: neck = sh_vals.iloc[0]  <- SL「以降」の最初のSH（誤り）
新（#026a）: neck = sh_before_sl.iloc[-1]  <- SL「以前」の最後のSH（正）
```

---

### 3-4. エントリー方式（#026c確定 / ADR D-9）

指値方式（ENTRY_OFFSET_PIPS = 7.0）:
```
エントリー条件: 5M High >= neck_15m + 7pips
エントリー価格: neck_15m + 7pips（指値で約定）

旧方式（実体越え）との違い:
  旧: min(open,close) > neck_15m + WICKTOL（5pips）-> 次足始値で成行
  新: High >= neck_15m + 7pips -> 指値価格で直接約定
```

---

### 3-5. 4H構造優位性フィルター（#026d確定 / ADR D-10）

```python
# エントリー前に4H構造の優位性を確認
if neck_4h < neck_1h:
    # SKIP: 4H SH が 1H SH より低い = 上位足の抵抗が弱い
    result['skip_reason'] = 'SKIP(4H優位性なし)'
    continue
```

条件: neck_4h >= neck_1h が成立しているエントリーのみ有効

---

### 3-6. 決済ロジック（4段階 / exit_simulator.py 方式B / ADR D-8）

```
【初動SL: エントリー直後~5M Swing確定前】
  15M ダウ崩れ -> 全量損切

【段階1: 5M Swing確定後~neck_4h未到達】
  5M ダウ崩れ -> 全量決済

【段階2: High >= neck_4h 到達】
  50%決済 + 残り50%のストップを建値移動（ノーリスク化）

【段階3: 4H ネック + 1H 実体確定後】
  1H Close が 4H SH を上抜け -> 15M ダウ崩れで残り全量決済
```

WARNING: exit_logic.py の manage_exit() は使用しない
（旧版・凍結保持・呼び出し禁止）
-> exit_simulator.py の方式B（独自実装）が正式な決済エンジン

---

### 3-7. 再エントリー仕様

- 同一押し目機会での再試行: 最大1回（MAX_REENTRY = 1）
- 4H上昇ダウが崩れたらカウントリセット -> 戦略完全リセット

---

## 4. 確定パラメータ一覧（#026d時点）

```python
# エントリー
DIRECTION_MODE      = 'LONG'
ALLOWED_PATTERNS    = ['DB', 'ASCENDING', 'IHS']
ENTRY_OFFSET_PIPS   = 7.0      # 指値方式（#026c確定）
MIN_4H_SWING_PIPS   = 20.0
LOOKBACK_15M_RANGE  = 50
MAX_REENTRY         = 1
PIP_SIZE            = 0.01

# Swing検出
N_1H_SWING          = 3        # 1H粒度（#026a-v2確定）

# 窓
WINDOW_1H_PRE       = 20
WINDOW_1H_POST      = 10
PRICE_TOL_PIPS      = 20.0

# プロット（窓と独立）
PLOT_PRE_H          = 25
PLOT_POST_H         = 40
```

---

## 5. Swing検出パラメータ一覧（#026d確定値）

| 用途 | TF | n | 状態 |
|---|---|---|---|
| 4H方向判定・SH/SL取得 | 4H | 3 | 確定（verify合格） |
| 1H SH/SL検出（window_scanner） | 1H | 3 | 確定（#026a-v2 / ADR D-7） |
| 15M パターン検出 | 15M | 3 | 確定（#014） |
| 5M エントリー確定 | 5M | 2 | 確定 |

---

## 6. ファイル構成（#026d時点）

```
src/
├── swing_detector.py       [FROZEN #020] 変更禁止
├── entry_logic.py          [FROZEN #018] 変更禁止
├── exit_logic.py           [FROZEN #009] 変更禁止・呼び出し禁止
│                              exit_simulator.py に移行済み
├── backtest.py             [FROZEN #018] 変更禁止
│                              PF 5.32 / 55.0% / MaxDD 14.9p / +91.6p
├── window_scanner.py       [拡張可能] #026d完了
│                              4H優位性フィルター追加 / 12カラムCSV出力
├── exit_simulator.py       [拡張可能] #026b新設・正式採用
│                              独立決済エンジン（方式B）
├── plotter.py              [拡張可能] 完了
├── structure_plotter.py    [拡張可能] 完了
├── base_scanner.py         完了（#015）
├── test_1h_coincidence.py  完了（#020 v2）
├── verify_4h1h_structure.py 完了（#026a-verify）
└── volume_alert.py         [未着手] Phase D予定

logs/
├── claudecode/
│   ├── instructions/       指示書ファイル群
│   ├── execution_results/  実行結果ファイル群
│   ├── INDEX.md
│   └── README.md
├── window_scan_entries.csv 12カラム（#026a-v2最終版）
├── window_scan_exits.csv   決済シミュレーション結果（#026b）
├── window_scan_plots/      プロット群（#026d最新）
├── verify_4h1h/            4H/1H構造検証プロット
└── docs_archive/           旧版設計文書の保管庫（参照禁止）
```

---

## 7. バックテスト結果推移（確定値）

| 指標 | #018（旧版・凍結） | #026b | #026c | #026d（最終） |
|---|---|---|---|---|
| 総トレード数 | 20件 | 12件 | 13件 | 10件 |
| 勝率 | 55.0% | 25.0% | 46.2% | 60.0% |
| PF | 5.32 | 0.61 | 2.42 | 4.54 |
| MaxDD | 14.9 pips | 138.4p | 69.4p | 35.8p |
| 総損益 | +91.6 pips | -61.3p | +113.3p | +150.6p |
| モード | LONG+★★★限定 | LONG+窓ベース | LONG+指値 | LONG+4H優位性 |

#026d パターン別（10件）:
- 4H構造優位性フィルター通過分のみ
- IHS: 0件（neckが逆転しやすいため・継続監視）

#018 パターン別（参照用・20件）:
- DB: 9件 / 勝率75.0% / ASCENDING: 10件 / 勝率60.0% / IHS: 1件 / 勝率0.0%

---

## 8. 指示書完了履歴

| # | 内容 | 主要変更 | 状態 |
|---|---|---|---|
| #001〜#025 | Phase A〜固定ネック原則確定 | 各種 | 完了 |
| #026a-verify | 4H/1H構造整合性検証 | verify_4h1h_structure.py | 完了 |
| #026a-v2 | 統一neck原則+上位足カラム追加 | sh_before_sl.iloc[-1] / 1H n=3 | 完了 |
| #026b | 決済シミュレーター新設 | exit_simulator.py（方式B） | 完了 |
| #026c | 指値方式エントリー | ENTRY_OFFSET_PIPS=7.0 | 完了 |
| #026d | 4H構造優位性フィルター | neck_4h >= neck_1h / PF 4.54 | 完了 |
| #027 | 設計文書整理・完全版作成 | 本ファイル作成 | 実行中 |

---

## 9. 次のステップ候補（ボス判断待ち）

1. 15M neck検出バグ改善（#06型プロット目視で指摘済み）
2. 4H SL検出精度改善
3. IHS専用neck算出の検討（IHS 0件化対応）
4. 15M SH密集フィルター（20260113_0545 TOPエントリー対応）
5. volume_alert.py（Phase D）
6. Phase 2（15M右肩内5M DBネスト）

---

## 10. docs/ 管理原則

- 不変原則: 一度確定した設計文書は編集しない
- 新規作成原則: 設計変更時は新ファイルを作成（旧版は logs/docs_archive/ へ）
- docs/ 直下のファイルのみが「現在有効な設計」
- logs/docs_archive/ は参照禁止

---

管理: Rex（設計責任者）/ Minato（ボス）
