# REX 指示書 #026a-v2 — 上位足構造正確化 + neck統一原則 + カラム追加
# 発行: Rex-Evaluator（Opus） / 宛先: Rex-Planner（Sonnet）
# 承認: ボス（2026-04-14）
# think harder
#
# 本指示書は #026a（初版）を置き換える。#026a初版は破棄すること。

---

## 本指示書の位置づけ

Evaluator が設計方針を確定し、Planner に ClaudeCode 用指示書の
作成を依頼するもの。Planner は本指示書の内容をそのまま
ClaudeCode 用フォーマットに変換して発行すること。

**ADR参照必須**: ADR-2026-04-13.md の E-6, F-1〜F-5 を事前に読むこと。

---

## 背景（なぜv2が必要になったか）

#026a（初版）実行後、ボスがTVチャートとの比較で2つの問題を発見:

1. **4H SLの位置ズレ疑惑** → #026a-verify で検証 → 4H n=3 は合格
2. **1H SH/SL が細かすぎる** → #026a-verify-v2 で検証 → **1H n=2→3 に変更確定**

さらに、決済トリガーの認識修正（ボス指摘・2026-04-14）:
- **半値決済トリガー = neck_4h（4H SH）** ← 正しい定義
- **neck_1h の主目的 = 窓特定のアンカー**（決済トリガーではない）

---

## 1. 設計原則（確定・変更不可）

### 1-1. neck統一原則（全TF共通）

```
neck = 「SL直前（時系列で左側）の最後のSH」（窓内限定）

全てのタイムフレームで同一の原則を適用する:

  15M neck: 窓内 かつ sl_1h_ts以前 の最後の 15M SH
  1H neck:  窓内 かつ sl_1h_ts以前 の最後の 1H SH
  4H neck:  sl_4h_ts以前 の最後の 4H SH（データ全体から取得可）
```

### 1-2. 窓内限定の原則（ADR A-2 再発防止）

```
15M neck / 1H neck は必ず「窓内 かつ SL以前」に限定する。
窓外のデータまで遡ると、別の波のSHを拾ってしまう（ADR A-2）。
4H neck は窓外から取得OK（scan_4h_events の構造データ）。
```

### 1-3. Noneガード

```
窓内かつSL以前に該当するSHが0本の場合:
  → neck = None → エントリーなし（CSV除外）
```

### 1-4. 各neckの用途定義（2026-04-14 ボス確認済み）

```
neck_15m — エントリートリガー（5M実体越え判定）
neck_1h  — 窓特定のアンカー / 段階1判定の参考値
neck_4h  — 半値決済トリガー（段階2: High >= neck_4h → 50%決済）
```

---

## 2. 変更一覧（全て window_scanner.py のみ）

| # | 変更内容 | 性質 |
|---|---|---|
| ① | 1H Swing n=2→3 に変更 | パラメータ変更 |
| ② | neck_15m 計算変更（SL以降→SL以前） | ロジック変更 |
| ③ | neck_1h カラム追加 | 新規カラム |
| ④ | neck_4h（= sh_4h）カラム追加 | 新規カラム |
| ⑤ | CSV再生成 + プロット再生成 | 出力更新 |

**禁止**: backtest.py / entry_logic.py / exit_logic.py / swing_detector.py は変更しない

---

## 3. 変更内容の詳細

### 3-1. 1H Swing パラメータ変更（n=2→3）

```python
# get_1h_window_range() 内、または1H SL検出に使っている箇所

# 変更前
sl_1h = detect_swing_lows(df_1h['Low'], n=2)
sh_1h = detect_swing_highs(df_1h['High'], n=2)

# 変更後
sl_1h = detect_swing_lows(df_1h['Low'], n=3)
sh_1h = detect_swing_highs(df_1h['High'], n=3)
```

**重要**: 実ファイルを read して、1H Swing 検出が行われている全箇所を確認すること。
`n=2` がハードコードされている箇所を全て `n=3` に変更する。
定数化（`N_1H_SWING = 3`）してファイル上部で定義するのが望ましい。

✖**影響**: 1H SL の検出数が減少し、4H SL との対応が見つからない窓が
増える可能性がある。これは正常動作（小さすぎる波を無視した結果）。
✖これに関しては無視でOK
1H n=3にすると小さな1H SLが消えるリスクについては、そもそも４H-SwgLの最安値を１H-SwngLが拾わないはずがないので無視(ボスより)

### 3-2. neck_15m の計算変更

```python
# ===== 変更前（#025・SL以降の初SH）=====
sh_vals = df_5m_win.loc[df_5m_win.index >= sl_1h_ts, 'sh_15m']
sh_vals = sh_vals.dropna()
if len(sh_vals) > 0:
    neck_15m = float(sh_vals.iloc[0])    # SL以降の最初

# ===== 変更後（SL以前の最後のSH・窓内限定）=====
sh_before = df_5m_win.loc[df_5m_win.index < sl_1h_ts, 'sh_15m']
sh_before = sh_before.dropna()
if len(sh_before) > 0:
    neck_15m = float(sh_before.iloc[-1])  # SL以前の最後（SLに最も近い）
else:
    neck_15m = None  # → エントリーなし
```

**注意**: `'sh_15m'` カラムの生成方法は実ファイルで確認すること。
窓内5Mデータを15Mにリサンプルし `detect_swing_highs()` で検出しているはず。
**実装前に必ず実ファイルの処理フローを read する（ADR B-1）。**

### 3-3. neck_1h の算出と CSV カラム追加

```python
# 窓内5Mデータを1Hにリサンプル
df_1h_win = resample_tf(df_5m_win, '1h')  # label='right', closed='right' 厳守

# 1H SH を検出（n=3 に統一）
sh_1h_flags = detect_swing_highs(df_1h_win['High'], n=3)
sh_1h_vals = df_1h_win['High'][sh_1h_flags]

# SL以前 かつ 窓内 の最後の1H SH
sh_1h_before = sh_1h_vals[sh_1h_vals.index < sl_1h_ts]
if len(sh_1h_before) > 0:
    neck_1h = float(sh_1h_before.iloc[-1])
else:
    neck_1h = None
```

### 3-4. neck_4h（= sh_4h）の算出と CSV カラム追加

```python
# scan_4h_events() の中で、4H SL と同時に 4H SH も取得
#
# 4H上昇ダウ: SH1→SL1→SH2→SL2→...
# 各SLの neck_4h = そのSL直前の最後の4H SH
#
# 実装: sl_4h_ts 直前の最新の 4H SH を取得
sh_4h_before = sh_4h_series[sh_4h_series.index < sl_4h_ts]
if len(sh_4h_before) > 0:
    neck_4h = float(sh_4h_before.iloc[-1])
else:
    neck_4h = None  # 最初のSL（SHがまだ無い）→ エントリー除外
```

**4H は窓内限定不要**。scan_4h_events() が4H全体を走査しているため。

### 3-5. CSV出力フォーマット

```
変更前（#026a初版: 12カラム）:
  pattern, neck_15m, neck_1h, neck_4h, confirm_ts, entry_ts, entry_price,
  sl_4h, ts_4h, sl_4h_ts, sl_1h_ts, window

変更後（#026a-v2: 同じ12カラム、ただし全値が変わる可能性あり）:
  pattern, neck_15m, neck_1h, neck_4h, confirm_ts, entry_ts, entry_price,
  sl_4h, ts_4h, sl_4h_ts, sl_1h_ts, window
```

**neck_15m / neck_1h / neck_4h のいずれかが None → CSV除外。**

### 3-6. エントリー判定のフロー（変更後の全体像）

```
① 4H LONG期間スキャン → 各4H SL に対して neck_4h も取得（3-4）
② 4H SL → 1H窓確定（1H n=3 に変更・3-1）
③ 窓内15Mリサンプル → check_15m_range_low() → パターンラベル取得（変更なし）
④ neck_15m = 窓内 かつ sl_1h_ts以前 の最後の15M SH（3-2）
⑤ neck_1h  = 窓内 かつ sl_1h_ts以前 の最後の1H SH（3-3）
⑥ いずれかが None → スキップ
⑦ 5M min(open,close) > neck_15m + WICKTOL_PIPS * PIP → エントリー確定
   （走査は sl_1h_ts 以降から開始 — ADR A-1 遵守）
```

---

## 4. プロット更新

水平線の構成:

| 要素 | 色 | スタイル | 用途 |
|---|---|---|---|
| neck_15m | 黄緑 (#ADFF2F) | 破線 | エントリートリガー |
| neck_1h | オレンジ (#FFA500) | 破線 | 窓アンカー（参考表示） |
| neck_4h | 赤紫 (#DA70D6) | 破線 | 半値決済トリガー |
| 4H SL | 青 (#1E90FF) | 破線 | 損切基準 |
| 1H SL | シアン (#00CED1) | 点線（垂直） | 窓中心 |
| Entry | 赤 (#FF4444) | 実線（垂直） | エントリー時刻 |

neck_4h がプロット表示範囲外の場合は凡例にのみ記載。

---

## 5. 完了条件

```
✅ python src/window_scanner.py がエラーなし実行
✅ logs/window_scan_entries.csv が再生成（12カラム）
✅ logs/window_scan_plots/*.png が再生成
✅ neck_15m / neck_1h / neck_4h が全エントリーで値あり（None除外済み）
✅ git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py
   差分ゼロ
✅ git commit -m "Feat: #026a-v2 unified neck + 1H n=3 + structure columns"
```

---

## 6. 結果報告フォーマット（必須）

```
=== #026a-v2 結果報告 ===

■ パラメータ変更
1H Swing n: 2 → 3

■ 基本統計
スキャン窓数        : （#026a初版: 33件 → ?件）
 ※ 1H n変更で窓数自体が変わる可能性あり
エントリー検出数    : （#026a初版: 12件 → ?件）
パターン別:
  DB       :    件（#026a初版: 2件）
  IHS      :    件（#026a初版: 0件）
  ASCENDING:    件（#026a初版: 10件）
neck=Noneでスキップした窓数:

■ neck_15m の変更比較
（#026a初版の12件と対応できるエントリーがあれば比較）
#  | pattern   | #026a初版 neck | v2 neck  | 差分(pips)
01 | ...       | ...            | ...      | ...

■ 新規カラム確認
neck_1h の範囲: min=XXX.XXX / max=XXX.XXX
neck_4h の範囲: min=XXX.XXX / max=XXX.XXX

■ 構造の妥当性
neck_15m < neck_1h が成立: ?/?件
neck_4h が全件で最大値: ?/?件

■ 1H n変更の影響
1H SL検出数の変化（推定）:
4H SLとの対応が見つからなくなった窓数:
```

---

## 7. Planner への注意事項

### 7-1. ClaudeCode 用指示書の必須記載事項

```
① 冒頭に「実ファイルを read してから実装」（ADR B-1/B-2）
② resample_tf は label='right', closed='right' 厳守（ADR不変ルール#3）
③ detect_swing_highs/lows のシグネチャを実ファイルで確認
④ 1H n=2 がハードコードされている箇所を全て n=3 に変更
   → grep "n=2" src/window_scanner.py で検索させること
⑤ None ガードの実装を明示
⑥ 禁止ファイル一覧を明記
```

### 7-2. 想定されるリスクと対処

```
リスク1: 窓数が33件から減少
  原因: 1H n=3 で小さな1H SLが検出されなくなり、
        4H SLに対応する1H SLが見つからない窓が増える
  対処: 正常動作。窓数とエントリー数を報告に含める。
        窓数が20件以下に激減した場合は Evaluator に相談。

リスク2: エントリー数が大幅減少
  原因: neck_15m が高くなる（SL直前のSHが高い位置にある場合）
       + 1H n=3 で窓数減少の複合効果
  対処: 5件以下の場合は Evaluator に相談。

リスク3: neck_15m / neck_1h のNoneが多発
  原因: 窓内かつSL以前にSHが存在しない
  対処: 正常動作。None窓数を報告に含める。

リスク4: 1H n=2 の箇所を見落とす
  対処: grep で全箇所を検索し、変更前/変更後を報告に含める。
```

### 7-3. 変更してはいけないもの

```
❌ check_15m_range_low() の呼び出し方・引数・用途
❌ 5Mネック越えの走査開始位置（sl_1h_ts以降 — ADR A-1）
❌ WICKTOL_PIPS / MIN_4H_SWING_PIPS / LOOKBACK_15M_RANGE の値
❌ PLOT_PRE_H / PLOT_POST_H の値
❌ WINDOW_1H_PRE / WINDOW_1H_POST の値
❌ 4H Swing の n=3（変更なし）
❌ 15M Swing の n=3（変更なし）
❌ 5M Swing の n=2（変更なし）
```

---

## 8. #026a-v2 完了後の次ステップ

```
結果を Evaluator が検証:

  → エントリー数・neck値が妥当
  → ADR 更新（D-6/D-7/A-6 追記、Swingパラメータ表更新）
  → #026b（exit_simulator.py 新規作成）に進む

#026b では:
  ① CSV（12カラム）を読み込み
  ② position dict を構築:
     - entry_price, direction='LONG'
     - neck_4h = 半値決済トリガー（段階2）
     - neck_1h = 段階1判定の参考値
     - exit_phase = 'pre_1h'（初期値）
  ③ manage_exit() の実APIを read してから呼び出し
  ④ P&L / PF / 勝率 / MaxDD を算出
  ⑤ #018ベースライン（PF 5.32）と比較
```

---

## 9. Swingパラメータ一覧（#026a-v2 適用後の想定）

| 用途 | TF | n | 状態 |
|---|---|---|---|
| 4H SH/SL（scan_4h_events） | 4H | 3 | 確定（verify合格） |
| 1H SH/SL（window_scanner） | 1H | **3** | **#026a-v2 で変更** |
| 15M パターン検出 | 15M | 3 | 確定（#014） |
| 5M エントリー確定 | 5M | 2 | 確定 |

---

**発行: Rex-Evaluator / 2026-04-14 / ADR-2026-04-13準拠**
**#026a初版は本指示書で置換。Planner は本v2のみを参照すること。**