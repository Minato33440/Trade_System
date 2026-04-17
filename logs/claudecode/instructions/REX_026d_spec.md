# REX 指示書 #026d — 4H構造優位性フィルター追加
# 発行: Rex-Planner（Sonnet）→ ClaudeCode 直接
# 承認: ボス（2026-04-15）
# think hard

---

## ⛔ 実装前に必ず実行

```bash
# 1. run_window_scan() の neck_4h 確定〜entries.append() 周辺を確認
grep -n "neck_4h\|neck_1h\|entries.append\|None ガード" src/window_scanner.py

# 2. 現在の CSV カラム構成と件数確認
head -2 logs/window_scan_entries.csv
wc -l logs/window_scan_entries.csv
```

---

## 背景と目的

### #026c で判明した構造問題

#026c（指値エントリー）の結果報告で以下のエントリーに異常が発覚:

```
#07: ASCENDING / entry=158.222 / PnL=-13.10 / stage2_breakeven_stop
#11: ASCENDING / entry=148.174 / PnL=+5.00  / stage2_breakeven_stop
```

`stage2_breakeven_stop` の PnL 計算:
```
PnL = 50% × (neck_4h - entry_price) + 50% × 0
```

`#07 が -13.10` → `neck_4h < entry_price` が確定。
**半値決済ターゲット（neck_4h）がエントリー価格より下にある**という構造的欠陥。

### 原因: 4H neck ブレイク後の裏確認パターン

```
価格
 ↑
 |  neck_1h (1H SH) ─────────────
 |       ↑                        ← ブレイク後に 1H が新高値を形成
 |  neck_4h (旧 4H SH) ────────── ← すでにブレイクされた水準 = 裏確認対象
 |       ↑
 |  sl ≈ sl_4h ≈ sl_1h ─────────
 |       ↑下長ヒゲで SL タッチ → 15M DB 形成
 |       ↑entry = neck_15m + 7pips（neck_4h を上回ってしまう）
```

4H SH（neck_4h）はすでにブレイクされた水準にあり、
entry_price が neck_4h を上回る or neck_4h に対する余白がゼロに近い。
4H 上昇ダウとしては有効な動き（裏確認 → 継続）だが、
**現在の決済ロジックで neck_4h を半値ターゲットとして機能させられない**。

### フィルター条件（ボス確定・2026-04-15）

```
4H-SwgH の値幅 >= 1H-SwgH の値幅
→ #020検証済み（sl_4h ≈ sl_1h、数学的必然）により:
→ neck_4h >= neck_1h  に等価
```

MTF 支配原則（ADR F-1）の直接応用:
**4H 構造が 1H 構造を上回っていることがエントリーの前提条件**

---

## 変更対象ファイル

```
① src/window_scanner.py — フィルター 1 行追加（+ デバッグ出力）
```

**変更禁止**:
```
backtest.py / entry_logic.py / exit_logic.py / swing_detector.py
exit_simulator.py（CSV が変わるので再実行は必要だが、ファイル内容は変更しない）
```

---

## 変更内容

### window_scanner.py の変更（1 箇所のみ）

**挿入場所**: `run_window_scan()` 内の None ガード直後、`entries.append()` の直前

現在のコード（変更前）:
```python
        # ---- None ガード（#026a-v2 必須）----
        neck_15m = entry.get('neck_15m')
        neck_1h = entry.get('neck_1h')
        if neck_15m is None or neck_1h is None or neck_4h is None:
            print(
                f"  → SKIP(neck=None): "
                f"neck15m={neck_15m}, n1h={neck_1h}, n4h={neck_4h}"
            )
            skip_none += 1
            continue

        # ---- 全 neck が揃った: エントリー確定 ----
        entry['neck_4h']  = neck_4h
        entry['ts_4h']    = ts_4h
        entry['sl_4h_ts'] = sl_4h_ts
        entry['sl_1h_ts'] = sl_1h_ts
        entry['window']   = f"{win_start} ~ {win_end}"
        entries.append(entry)
```

変更後（追加部分を ★ で示す）:
```python
        # ---- None ガード（#026a-v2 必須）----
        neck_15m = entry.get('neck_15m')
        neck_1h = entry.get('neck_1h')
        if neck_15m is None or neck_1h is None or neck_4h is None:
            print(
                f"  → SKIP(neck=None): "
                f"neck15m={neck_15m}, n1h={neck_1h}, n4h={neck_4h}"
            )
            skip_none += 1
            continue

        # ★ ---- 4H構造優位性フィルター (#026d) ----
        # 条件: neck_4h >= neck_1h
        # 根拠: 4H-SwgH の値幅 >= 1H-SwgH の値幅
        #       sl_4h ≈ sl_1h（#020 検証済み）なので neck_4h >= neck_1h に等価
        # 除外: 4H neck ブレイク後の裏確認パターン（#026c #07/#11 型）
        #       neck_4h < neck_1h = 4H が 1H を支配できていない = エントリー不適格
        if neck_4h < neck_1h:
            print(
                f"  → SKIP(4H優位性なし): "
                f"neck_4h={neck_4h:.3f} < neck_1h={neck_1h:.3f}"
            )
            continue

        # ---- 全 neck が揃った: エントリー確定 ----
        entry['neck_4h']  = neck_4h
        entry['ts_4h']    = ts_4h
        entry['sl_4h_ts'] = sl_4h_ts
        entry['sl_1h_ts'] = sl_1h_ts
        entry['window']   = f"{win_start} ~ {win_end}"
        entries.append(entry)
```

**追加コードの要点**:
- `neck_1h` は None ガード内で既に取得済みのローカル変数をそのまま使う
- 新しいカウンタ変数は不要（SKIP ログで件数は追跡できる）
- CSV カラム構成・プロット生成ロジックへの変更なし
- exit_simulator.py への変更なし（新 CSV を読むだけで自動反映）

---

## 変更しないもの

```
❌ neck_4h の計算方式（sl_4h_ts 以前の最後の 4H SH）
❌ neck_1h の計算方式（SL 以前の最後の 1H SH）
❌ neck_15m の計算方式（統一ネック原則）
❌ ENTRY_OFFSET_PIPS = 7.0（#026c 確定値）
❌ scan_window_entry() の内部ロジック
❌ CSV の 12 カラム構成
❌ プロット生成ロジック
❌ exit_simulator.py（変更不要・新 CSV で再実行するだけ）
❌ 凍結ファイル 4 本
```

---

## 実行手順

```bash
# 1. window_scanner.py を修正（上記の 1 箇所のみ）

# 2. CSV + プロット再生成
python src/window_scanner.py
# → SKIP(4H優位性なし) ログが #07/#11 該当件で出ること

# 3. exit_simulator.py を再実行（新 CSV を読む）
python src/exit_simulator.py

# 4. 禁止ファイル差分チェック（0 行であること）
git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py \
            src/swing_detector.py src/exit_simulator.py

# 5. コミット
git add src/window_scanner.py logs/
git commit -m "Feat: #026d 4H superiority filter (neck_4h >= neck_1h)"
```

---

## 完了条件

```
✅ python src/window_scanner.py エラーなし実行
✅ SKIP(4H優位性なし) ログが少なくとも 1 件以上出力される
✅ logs/window_scan_entries.csv 再生成（13件 → N件に減少）
✅ logs/window_scan_plots/*.png 再生成
✅ python src/exit_simulator.py エラーなし再実行
✅ logs/window_scan_exits.csv 再生成
✅ 禁止ファイル差分ゼロ
✅ git commit 完了
```

---

## 結果報告フォーマット

```
=== #026d 結果報告 ===

■ フィルター適用状況
4H優位性フィルター除外件数: N件
対象エントリー番号（#026c基準）:

■ エントリー数変動
#026c: 13件 → #026d: ?件

■ 除外件確認
以下の SKIP ログが出力されたこと:
  → SKIP(4H優位性なし): neck_4h=XXX.XXX < neck_1h=XXX.XXX
  （#026c の #07 / #11 に相当する件が除外されているか確認）

■ exit_simulator 再実行結果
指標          | #026d   | #026c   | #018
総トレード    |         | 13件    | 20件
勝率          |         | 46.2%   | 55.0%
PF            |         | 2.42    | 5.32
MaxDD         |         | 69.4p   | 14.9p
総損益        |         | +113.3p | +91.6p

■ 決済段階別
exit_phase | #026d件数 | #026c件数
stage1     |           | 7
stage2     |           | 2
stage3     |           | 4
data_end   |           | 0

■ 全件詳細
 # | pat       | neck_4h  | neck_1h  | 4H優位 | entry   | exit    | reason | phase  | pnl
01 | ...       | ...      | ...      | OK/NG  | ...     | ...     | ...    | ...    | ...
（neck_4h >= neck_1h の NG 件は除外されているため、全件 OK のみ表示）
```

---

## 設計根拠メモ（ADR D-8 向け・Evaluator 追記用）

```
D-8: 4H-SwgH < 1H-SwgH によるエントリー不正検出（#026d）

症状: stage2_breakeven_stop で PnL がマイナス（#026c #07 型）
      neck_4h < entry_price（半値決済ターゲットがエントリー価格以下）

原因: 4H neck ブレイク後の下長髭裏確認パターン
      neck_4h（旧 4H SH）は ブレイクされた水準 = entry より下の可能性がある
      このとき neck_4h < neck_1h（1H が新高値 = neck_1h > 旧 neck_4h）という
      MTF 逆転状態が成立している

修正: neck_4h < neck_1h の場合はエントリー除外
      4H-SwgH の値幅 >= 1H-SwgH の値幅（sl_4h ≈ sl_1h により neck_4h >= neck_1h に等価）

教訓: neck_4h が半値決済として機能するには neck_4h >= neck_1h（4H が 1H を支配）が前提
      これは ADR F-1（トップダウン原則）のエントリー検証への直接応用
      追加パラメータゼロ・閾値チューニング不要のシンプルな構造条件
```

---

## ClaudeCode 不変ルール（全指示書共通）

```
1. 既存関数を呼ぶ前に必ず実ファイルの def 行を read する
2. 凍結ファイルは変更しない（backtest / entry_logic / exit_logic / swing_detector）
3. exit_simulator.py も変更しない（新 CSV で再実行するだけ）
4. resample_tf は label='right', closed='right' で統一。変更禁止
5. git diff で禁止ファイルの差分ゼロを完了条件に含める
6. エラーが出たら自分で「想像で」修正しない。ボスに報告して停止
```

---

**発行: Rex-Planner / 2026-04-15**
