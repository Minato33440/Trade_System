# REX 指示書 #026a — neck統一原則の適用 + 上位足カラム追加
# 発行: Rex-Evaluator（Opus） / 宛先: Rex-Planner（Sonnet）
# 承認: ボス（2026-04-13）
# think harder

---

## 本指示書の位置づけ

Evaluator が設計方針を確定し、Planner に ClaudeCode 用指示書の
作成を依頼するもの。Planner は本指示書の内容をそのまま
ClaudeCode 用フォーマットに変換して発行すること。

**ADR参照必須**: ADR-2026-04-13.md の E-6, F-1, F-2, F-4 を事前に読むこと。

---

## 1. 設計原則（確定・変更不可）

### 1-1. neck統一原則（全TF共通）

```
neck = 「SL直前（時系列で左側）の最後のSH」

全てのタイムフレームで同一の原則を適用する:

  15M neck: sl_1h_ts 直前の最後の 15M SH（窓内限定）
  1H neck:  sl_1h_ts 直前の最後の 1H SH（窓内限定）
  4H neck:  sl_4h_ts 直前の最後の 4H SH（データ全体から取得可）
```

**テクニカル的根拠（ボス確認済み）**:
DBの教科書的構造では、neckは「2つの底の間にある戻り高値」であり、
SL（底）の**前**に位置する。#025の `sh_vals.iloc[0]`（SL以降の初SH）は
方向が逆だった。

```
価格
 ↑
 |  neck(SH) ─────── ← SL直前の最後のSH = これが正しいneck
 |  /           \      /
 | /  Bottom1    \ Bottom2(=SL)
 |                \  /
 +──────────────────→ 時間
```

**ワンボトム対応**: 1H DBだけでなくワンボトム（直接反発）の場合も
SL直前のSHがneckになる。テスト段階ではこの統一原則で網羅する。

### 1-2. 窓内限定の原則（ADR A-2 再発防止）

```
15M neck / 1H neck は必ず「窓内 かつ SL以前」に限定する。

理由: 窓外のデータまで遡ると、全く別の波のSHを拾ってしまう。
      これは ADR A-2（別の波の底を比較した事例）と同じ構造の罠。

4H neck は窓外から取得してOK。
理由: 4H SH は scan_4h_events() が走査する4H構造の中で
      既に確定している情報。窓とは独立した上位構造。
```

### 1-3. SHが存在しないケースのガード

```
窓内かつSL以前に該当するSHが0本の場合:
  → neck = None
  → そのエントリーはスキップ（エントリーなし扱い）

理由: neckが定義できない = 構造が成立していない。
      無理にフォールバック値を使うと D-3（フォールバック値問題）の再発になる。
```

---

## 2. 変更対象

```
変更ファイル: src/window_scanner.py（1ファイルのみ）
変更の性質:
  ① neck_15m の計算ロジック変更（SL以降 → SL以前）
  ② neck_1h カラム追加（新規）
  ③ sh_4h（= neck_4h）カラム追加（新規）
  ④ CSV再生成 + プロット再生成

禁止:
  backtest.py / entry_logic.py / exit_logic.py / swing_detector.py は変更しない
```

---

## 3. 変更内容の詳細

### 3-1. neck_15m の計算変更

```python
# ===== 変更前（#025・SL以降の初SH）=====
sh_vals = df_5m_win.loc[df_5m_win.index >= sl_1h_ts, 'sh_15m']  # ← SL「以降」
sh_vals = sh_vals.dropna()
if len(sh_vals) > 0:
    neck_15m = float(sh_vals.iloc[0])   # ← 最初（最も左）

# ===== 変更後（SL以前の最後のSH・窓内限定）=====
sh_before = df_5m_win.loc[df_5m_win.index < sl_1h_ts, 'sh_15m']  # ← SL「以前」
sh_before = sh_before.dropna()
if len(sh_before) > 0:
    neck_15m = float(sh_before.iloc[-1])  # ← 最後（最も右 = SLに最も近い）
else:
    neck_15m = None  # SHが存在しない → エントリーなし
```

**重要**: `df_5m_win` は窓内データ（前20h + SL足 + 後10h）。
窓外のデータは含まれていないので、この切り出しで窓内限定が保証される。

`'sh_15m'` カラムが存在しない場合は、窓内5Mデータを15Mにリサンプルし
`detect_swing_highs()` で検出する（既存処理と同様）。
**実装時に必ず実ファイルを read して現在の処理フローを確認すること（ADR B-1）。**

### 3-2. neck_1h の算出と CSV カラム追加

```python
# 窓内5Mデータを1Hにリサンプル
df_1h_win = resample_tf(df_5m_win, '1h')  # label='right', closed='right' 厳守

# 1H SH を検出
sh_1h = detect_swing_highs(df_1h_win['High'], n=2)

# SL以前 かつ 窓内 の最後の1H SH
sh_1h_before = sh_1h[sh_1h.index < sl_1h_ts].dropna()
if len(sh_1h_before) > 0:
    neck_1h = float(sh_1h_before.iloc[-1])
else:
    neck_1h = None  # 1H SH が窓内SL以前に存在しない
```

**注意**: `resample_tf` は `label='right', closed='right'` で統一（ADR不変ルール#3）。
Planner が ClaudeCode 用指示書に書く際、この点を明記すること。

### 3-3. sh_4h（= neck_4h）の算出と CSV カラム追加

```python
# scan_4h_events() の中で、4H SL と同時に 4H SH も取得する
#
# 現在の処理:
#   4H上昇ダウ期間を走査 → 各4H SLのts/price を記録
#
# 追加する処理:
#   各4H SLに対して、その直前の4H SH（= 高値切り上げ点）も記録
#
# 4H上昇ダウの構造上、各SLには必ず対応するSHが存在する:
#
#   SH1    SH2    SH3
#    /\    /\     /\
#   /  \  /  \   /  \
#  /    \/    \ /    \
#       SL1    SL2    SL3
#
# SL1 の neck_4h = SH1（SL1直前の最後の4H SH）
# SL2 の neck_4h = SH2
#
# 実装: sl_4h_ts 直前の最新の 4H SH を取得
sh_4h_before = sh_4h_series[sh_4h_series.index < sl_4h_ts].dropna()
if len(sh_4h_before) > 0:
    neck_4h = float(sh_4h_before.iloc[-1])
else:
    neck_4h = None  # 最初のSL（SHがまだ無い）
```

**4H は窓内限定不要**: scan_4h_events() が4H全体を走査しているので、
窓ではなく4Hデータ全体から取得して正しい。

### 3-4. CSV出力フォーマット（変更後）

```
変更前（10カラム）:
  pattern, neck_15m, confirm_ts, entry_ts, entry_price,
  sl_4h, ts_4h, sl_4h_ts, sl_1h_ts, window

変更後（12カラム — 2カラム追加）:
  pattern, neck_15m, neck_1h, neck_4h, confirm_ts, entry_ts, entry_price,
  sl_4h, ts_4h, sl_4h_ts, sl_1h_ts, window
```

**neck_15m / neck_1h / neck_4h のいずれかが None のエントリーは
CSV に含めない（エントリー不成立として除外）。**

### 3-5. エントリー判定のフロー（変更後の全体像）

```
① check_15m_range_low() → パターンラベル取得（変更なし）
② neck_15m = 窓内 かつ sl_1h_ts以前 の最後の15M SH（変更あり）
③ neck_1h  = 窓内 かつ sl_1h_ts以前 の最後の1H SH（新規）
④ neck_4h  = sl_4h_ts以前 の最後の4H SH（新規）
⑤ いずれかが None → そのエントリーはスキップ
⑥ 5M min(open,close) > neck_15m + WICKTOL_PIPS * PIP → エントリー確定
   （この走査は sl_1h_ts 以降から開始 — ADR A-1 遵守）
```

---

## 4. プロット更新

プロット表示要素に以下を追加:

```
追加する水平線:
  neck_1h  — オレンジ破線（半値決済トリガー水準の視認用）
  neck_4h  — 赤紫破線（post_4h移行トリガー水準の視認用）

既存の水平線（変更なし）:
  neck_15m — 黄緑破線
  4H SL   — 青破線
  1H SL   — シアン点線
  Entry   — 赤実線
```

neck_4h がプロット表示範囲外（上方向にはみ出す）の場合は
凡例にのみ記載し、線は描画しなくてよい。

---

## 5. 完了条件

```
✅ python src/window_scanner.py がエラーなし実行
✅ logs/window_scan_entries.csv が再生成されている（12カラム）
✅ logs/window_scan_plots/*.png が再生成されている
✅ neck_1h / neck_4h が全エントリーで値を持っている（Noneは除外済み）
✅ git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py
   差分ゼロ
✅ git commit -m "Feat: #026a unified neck principle + 1H/4H neck columns"
```

---

## 6. 結果報告フォーマット（必須）

```
=== #026a 結果報告 ===

■ 基本統計
スキャン窓数        :
エントリー検出数    : （#025の15件 → ?件に変化）
パターン別:
  DB       :    件（#025: 3件 → ?件）
  IHS      :    件（#025: 3件 → ?件）
  ASCENDING:    件（#025: 9件 → ?件）
エントリー0件だった窓数:
neck=Noneでスキップした窓数:

■ neck_15m 変更前後の比較（全件）
#  | pattern   | 旧neck(#025) | 新neck(#026a) | 差分(pips) | entry変化
01 | ...       | ...          | ...           | ...        | ...
02 | ...       | ...          | ...           | ...        | ...
...

■ 新規カラム確認
neck_1h の範囲: min=XXX.XXX / max=XXX.XXX
neck_4h の範囲: min=XXX.XXX / max=XXX.XXX
neck_4h > neck_1h > neck_15m の順序が成立しているか: はい/いいえ（件数）
```

---

## 7. Planner への注意事項（Evaluator より）

### 7-1. ClaudeCode 用指示書を書く際の必須記載事項

```
① 「実ファイルを read してから実装」を冒頭に明記（ADR B-1/B-2）
② resample_tf は label='right', closed='right' 厳守と明記（ADR不変ルール#3）
③ detect_swing_highs() のシグネチャを実ファイルで確認する指示を含める
④ None ガードの実装を明示する
⑤ 禁止ファイル一覧を明記する
```

### 7-2. 想定されるリスクと対処

```
リスク1: エントリー数が大幅減少（15件 → 5件以下）
  → 正常動作の可能性あり。窓内SL以前にSHが無い窓が多い場合。
  → 結果報告の「neck=Noneでスキップした窓数」で原因を特定可能。
  → 減少が著しい場合は Evaluator に相談してから #026b に進むこと。

リスク2: neck_15m が従来より高くなり、エントリーが遅くなるケース
  → 「SL直前のSH」が「SL直後の初SH」より高い場合に発生。
  → これは正常動作。テクニカル的に正しいneckを採用した結果。
  → プロット目視で構造が妥当か確認する。

リスク3: searchsorted の TypeError
  → sl_1h_ts と df_5m_win.index のタイムゾーン不一致。
  → #022 で対応済みのはずだが、念のためエラー時の報告手順を含める。

リスク4: 15Mリサンプルと1Hリサンプルで参照するデータ範囲の不一致
  → 両方とも df_5m_win（窓内データ）からリサンプルすること。
  → 別々のデータソースからリサンプルしない。
```

### 7-3. この指示書で変更してはいけないもの

```
❌ check_15m_range_low() の呼び出し方・引数・用途
❌ エントリー確定の走査開始位置（sl_1h_ts以降 — ADR A-1）
❌ WICKTOL_PIPS / MIN_4H_SWING_PIPS / LOOKBACK_15M_RANGE の値
❌ プロット表示範囲（PLOT_PRE_H=25 / PLOT_POST_H=40）
❌ 窓サイズ（WINDOW_1H_PRE=20 / WINDOW_1H_POST=10）
```

---

## 8. #026a 完了後の次ステップ

```
#026a の結果を Evaluator が検証した後:
  → エントリー数・neck値が妥当と判断された場合
  → #026b（exit_simulator.py 新規作成）に進む

#026b では:
  ① CSV（12カラム）を読み込み
  ② position dict を構築（neck_1h / neck_4h を含む）
  ③ manage_exit() を5Mバーごとに呼び出し
  ④ P&L / PF / 勝率 / MaxDD を算出
  ⑤ #018ベースライン（PF 5.32）と比較
```

---

**発行: Rex-Evaluator / 2026-04-13 / ADR-2026-04-13準拠**
