# REX 指示書 #026c — エントリー価格を指値方式（neck_15m + 7pips）に変更
# 発行: Rex-Evaluator（Opus）→ ClaudeCode 直接
# 承認: ボス（2026-04-15）
# think hard

---

## ⛔ 実装前に必ず実行

```bash
# 1. window_scanner.py のエントリー判定箇所を確認
grep -n "WICKTOL\|neck_15m\|entry_price\|min(.*open.*close" src/window_scanner.py

# 2. exit_simulator.py の entry_price 参照箇所を確認
grep -n "entry_price\|entry_level" src/exit_simulator.py

# 3. 現在のCSVカラム構成
head -2 logs/window_scan_entries.csv
```

---

## 目的

エントリー価格の決定方式を「確定足の次足始値」から
「neck_15m + 7pips の指値」に変更する。

**変更理由（ボス判断・2026-04-15）**:
- 初動SLが15Mダウ崩れなので、エントリー位置はneck基準で固定すべき
- 次足始値だと急騰時にneckから80pips以上離れた価格でエントリーしてしまう
- 指値方式なら損切幅が安定し、裁量との整合性も取れる

---

## 変更対象ファイル

```
① src/window_scanner.py — エントリー価格の計算方式変更
② src/exit_simulator.py — 変更なし（CSVから読むだけなので自動で反映）
```

**変更禁止**: backtest.py / entry_logic.py / exit_logic.py / swing_detector.py

---

## 変更内容

### window_scanner.py の変更（2箇所）

#### 変更1: 定数追加（ファイル上部）

```python
# 変更前
WICKTOL_PIPS = 5.0

# 変更後（WICKTOL は残してもよいが、エントリー判定では使わない）
WICKTOL_PIPS = 5.0          # ← 既存（他で使っている場合に備えて残す）
ENTRY_OFFSET_PIPS = 7.0     # ← 追加: neck_15m からのエントリー固定オフセット
```

#### 変更2: エントリー判定ロジック

実ファイルを read してエントリー判定箇所を特定すること。
概ね以下のようなコードがあるはず:

```python
# ===== 変更前（次足始値方式）=====
# 5M実体がneckを越えた足を検出 → 次足始値でエントリー
if min(bar['open'], bar['close']) > neck_15m + WICKTOL_PIPS * PIP_SIZE:
    # 確定足の次足始値
    entry_price = df_5m_win.iloc[j + 1]['open']
    confirm_ts = bar_ts
    entry_ts = df_5m_win.index[j + 1]

# ===== 変更後（指値方式）=====
# 5M足のHighがneck+7pipsに到達 → その価格でエントリー成立
entry_level = neck_15m + ENTRY_OFFSET_PIPS * PIP_SIZE
if bar['high'] >= entry_level:
    entry_price = entry_level   # ← 固定価格
    confirm_ts = bar_ts         # 到達した足 = 確定足
    entry_ts = bar_ts           # 指値なので到達足でエントリー成立
```

**重要な違い**:
- `entry_price` は `next_bar['open']` ではなく `entry_level`（固定値）
- `entry_ts` は「次足」ではなく「到達した足自体」（指値は到達時点で約定）
- `confirm_ts` と `entry_ts` は同一になる

**注意**: 実ファイルの変数名・構造が上記と異なる場合は、
実ファイルに合わせて変更すること。ロジックの意味（指値到達判定）を維持する。

---

## 変更しないもの

```
❌ neck_15m の計算方式（SL以前の最後のSH — 統一neck原則）
❌ check_15m_range_low() の呼び出し
❌ sl_1h_ts 以降からの走査開始位置（ADR A-1）
❌ neck_1h / neck_4h の計算方式
❌ CSV のカラム構成（12カラムのまま。entry_price の値が変わるだけ）
❌ プロット生成ロジック（entry_price を参照しているだけなので自動で反映）
❌ exit_simulator.py（CSVを読むだけなので変更不要）
```

---

## 実行手順

```bash
# 1. window_scanner.py を修正
# 2. CSV + プロット再生成
python src/window_scanner.py

# 3. exit_simulator.py を再実行（window_scanner.py の新CSVを読む）
python src/exit_simulator.py

# 4. 禁止ファイル差分チェック
git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py

# 5. コミット
git add src/window_scanner.py logs/
git commit -m "Fix: #026c entry price to limit order neck+7pips"
```

---

## 完了条件

```
✅ python src/window_scanner.py エラーなし実行
✅ logs/window_scan_entries.csv 再生成（entry_price が全件 neck_15m + 7pips）
✅ logs/window_scan_plots/*.png 再生成
✅ python src/exit_simulator.py エラーなし再実行
✅ logs/window_scan_exits.csv 再生成
✅ 禁止ファイル差分ゼロ
✅ git commit 完了
```

---

## 結果報告フォーマット

```
=== #026c 結果報告 ===

■ エントリー価格変更の確認
ENTRY_OFFSET_PIPS = 7.0
全エントリーの entry_price = neck_15m + 7pips であること:
#  | neck_15m  | entry_price | 差分(pips) | 期待値との一致
01 | XXX.XXX   | XXX.XXX     | 7.0        | ✅/❌
...

■ エントリー検出数の変動
#026a-v2: 12件 → #026c: ?件
（entry_levelに到達しない足がある場合、件数が減る可能性あり）

■ exit_simulator 再実行結果
指標          | #026c   | #026b   | #018    
総トレード    |         | 12件    | 20件
勝率          |         | 25.0%   | 55.0%
PF            |         | 0.61    | 5.32
MaxDD         |         | 138.4p  | 14.9p
総損益        |         | -61.3p  | +91.6p

■ 決済段階別
exit_phase | #026c件数 | #026b件数
initial    |           | 0
stage1     |           | 7
stage2     |           | 4
stage3     |           | 1
data_end   |           | 0

■ 全件詳細
#  | pat  | neck_15m | entry | exit  | reason | phase | pnl
01 | ...  | ...      | ...   | ...   | ...    | ...   | ...
...
```

---

**発行: Rex-Evaluator / 2026-04-15**
