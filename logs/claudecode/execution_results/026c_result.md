=== #026c 結果報告 ===
# 実装日: 2026-04-15

■ エントリー価格変更の確認
ENTRY_OFFSET_PIPS = 7.0 / 全13件 OK

 # | neck_15m  | entry_price | 差分(pips)
01 | 151.396   | 151.466     | 7.0
02 | 157.519   | 157.589     | 7.0
03 | 157.930   | 158.000     | 7.0
04 | 142.368   | 142.438     | 7.0
05 | 151.790   | 151.860     | 7.0
06 | 157.890   | 157.960     | 7.0
07 | 158.152   | 158.222     | 7.0
08 | 144.940   | 145.010     | 7.0
09 | 144.430   | 144.500     | 7.0
10 | 147.312   | 147.382     | 7.0
11 | 148.104   | 148.174     | 7.0
12 | 156.997   | 157.067     | 7.0
13 | 158.086   | 158.156     | 7.0

■ エントリー検出数の変動
#026a-v2: 12件 → #026c: 13件（+1件）

■ exit_simulator 再実行結果
指標          | #026c   | #026b   | #018
総トレード    | 13件    | 12件    | 20件
勝率          | 46.2%   | 25.0%   | 55.0%
PF            | 2.42    | 0.61    | 5.32
MaxDD         | 69.4p   | 138.4p  | 14.9p
総損益        | +113.3p | -61.3p  | +91.6p

■ 決済段階別
exit_phase | #026c件数 | #026b件数
stage1     | 7         | 7
stage2     | 2         | 4
stage3     | 4         | 1

■ 全13件詳細
 # | pat       | entry   | exit    | reason                 | phase  | pnl
 1 | DB        | 151.466 | 151.399 | stage1_5m_dow          | stage1 |   -6.70
 2 | ASCENDING | 157.589 | 157.595 | stage1_5m_dow          | stage1 |   +0.60
 3 | DB        | 158.000 | 157.999 | stage1_5m_dow          | stage1 |   -0.10
 4 | ASCENDING | 142.438 | 143.934 | stage3_15m_dow         | stage3 | +150.05
 5 | ASCENDING | 151.860 | 152.111 | stage3_15m_dow         | stage3 |  +28.55
 6 | ASCENDING | 157.960 | 157.654 | stage1_5m_dow          | stage1 |  -30.60
 7 | ASCENDING | 158.222 | 158.222 | stage2_breakeven_stop  | stage2 |  -13.10
 8 | DB        | 145.010 | 145.010 | stage3_breakeven_stop  | stage3 |  -20.55
 9 | ASCENDING | 144.500 | 144.448 | stage1_5m_dow          | stage1 |   -5.20
10 | ASCENDING | 147.382 | 147.463 | stage1_5m_dow          | stage1 |   +8.10
11 | ASCENDING | 148.174 | 148.174 | stage2_breakeven_stop  | stage2 |   +5.00
12 | ASCENDING | 157.067 | 157.067 | stage3_breakeven_stop  | stage3 |   -3.70
13 | ASCENDING | 158.156 | 158.165 | stage1_5m_dow          | stage1 |   +0.90

■ 主な変化
PF: 0.61 → 2.42（大幅改善）
総損益: -61.3p → +113.3p（+174.6p改善）
MaxDD: 138.4p → 69.4p（半減）
stage3到達: 1件 → 4件
