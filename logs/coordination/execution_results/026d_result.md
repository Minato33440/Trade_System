# #026d 結果報告
# ClaudeCode実行: 2026-04-17
# 指示書: docs/REX_026d_spec.md（Evaluator承認 2026-04-15）

---

=== #026d 結果報告 ===

## ■ フィルター適用状況

**4H優位性フィルター除外件数: 3件**

除外エントリー（SKIP ログ）:
```
SKIP(4H優位性なし): neck_4h=157.960 < neck_1h=158.416
SKIP(4H優位性なし): neck_4h=144.599 < neck_1h=145.025
SKIP(4H優位性なし): neck_4h=156.993 < neck_1h=156.997
```

※ #026c #07型（entry=158.222 / stage2_breakeven_stop / PnL=-13.10）に相当するエントリーが除外された。
  #026c #11型（entry=148.174 / stage2_breakeven_stop / PnL=+5.00）は neck_4h=148.274 >= neck_1h=148.112 のため保持（#026d #09として残存）。

---

## ■ エントリー数変動

```
#026c: 13件 → #026d: 10件（-3件）
```

パターン別:
| pattern   | #026d | #026c |
|-----------|-------|-------|
| DB        | 2件   | —     |
| IHS       | 0件   | —     |
| ASCENDING | 8件   | —     |

---

## ■ exit_simulator 再実行結果

| 指標       | #026d    | #026c    | #018     |
|-----------|----------|----------|----------|
| 総トレード | 10件     | 13件     | 20件     |
| 勝率       | 60.0%    | 46.2%    | 55.0%    |
| PF         | 4.54     | 2.42     | 5.32     |
| MaxDD      | 35.8p    | 69.4p    | 14.9p    |
| 総損益     | +150.6p  | +113.3p  | +91.6p   |

---

## ■ 決済段階別

| exit_phase | #026d件数 | #026c件数 |
|-----------|-----------|-----------|
| stage1    | 7         | 7         |
| stage2    | 1         | 2         |
| stage3    | 2         | 4         |
| data_end  | 0         | 0         |

---

## ■ 全件詳細

```
 # | pat       | neck_4h  | neck_1h  | entry   | exit    | reason                  | phase    |      pnl
  1 | DB        | 151.541  | 151.440  | 151.466 | 151.399 | stage1_5m_dow           | stage1   |    -6.70
  2 | ASCENDING | 158.270  | 157.657  | 157.589 | 157.595 | stage1_5m_dow           | stage1   |    +0.60
  3 | DB        | 158.230  | 157.930  | 158.000 | 157.999 | stage1_5m_dow           | stage1   |    -0.10
  4 | ASCENDING | 143.943  | 142.928  | 142.438 | 143.934 | stage3_15m_dow          | stage3   | +150.05
  5 | ASCENDING | 152.180  | 152.180  | 151.860 | 152.111 | stage3_15m_dow          | stage3   |  +28.55
  6 | ASCENDING | 158.090  | 157.890  | 157.960 | 157.654 | stage1_5m_dow           | stage1   |  -30.60
  7 | ASCENDING | 145.233  | 145.213  | 144.500 | 144.448 | stage1_5m_dow           | stage1   |    -5.20
  8 | ASCENDING | 148.181  | 148.181  | 147.382 | 147.463 | stage1_5m_dow           | stage1   |    +8.10
  9 | ASCENDING | 148.274  | 148.112  | 148.174 | 148.174 | stage2_breakeven_stop   | stage2   |    +5.00
 10 | ASCENDING | 158.602  | 158.257  | 158.156 | 158.165 | stage1_5m_dow           | stage1   |    +0.90
```

全件 neck_4h >= neck_1h であることを確認済み ✅

---

## ■ 完了条件チェック

```
✅ python src/window_scanner.py エラーなし実行
✅ SKIP(4H優位性なし) ログが 3件出力された（>=1件）
✅ logs/window_scan_entries.csv 再生成（13件 → 10件に減少）
✅ logs/window_scan_plots/*.png 再生成（10枚）
✅ python src/exit_simulator.py エラーなし再実行
✅ logs/window_scan_exits.csv 再生成（10件）
✅ 禁止ファイル差分ゼロ（backtest/entry_logic/exit_logic/swing_detector/exit_simulator）
✅ git commit 完了: "Feat: #026d 4H superiority filter (neck_4h >= neck_1h)"
```

---

## ■ 所感（Evaluator wrap-up用参考）

- MaxDD: 69.4p → 35.8p（-48.4%改善）
- 勝率: 46.2% → 60.0%（+13.8%改善）
- 総損益: +113.3p → +150.6p（+33%改善）
- PF: 2.42 → 4.54（+88%改善）
- #026c の stage2_breakeven_stop でマイナスだったパターンが完全除外された
- ADR D-10（4H構造優位性フィルター）の効果が数値として確認された
- #018（PF 5.32）との差は残るが、サンプル数10件での判断は留保（Evaluator判断）
