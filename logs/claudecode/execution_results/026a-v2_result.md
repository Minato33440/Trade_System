=== #026a-v2 結果報告 ===
# 実装日: 2026-04-14 / commit: 71cf705

■ パラメータ変更
1H Swing n: 2 → 3（N_1H_SWING = 3 は既に実装済みだったため差分なし）

■ 基本統計
スキャン窓数 : 33件（#026a初版: 33件）
エントリー検出数 : 12件（#026a初版: 12件）
パターン別: DB=2 / IHS=0 / ASCENDING=10
neck=Noneでスキップした窓数: 0件

■ neck_15m 変更比較（全件 — 差分 0.0）
01 | DB        | neck=151.396 → 差分 0.0
02 | ASCENDING | neck=157.519 → 差分 0.0
03 | ASCENDING | neck=142.368 → 差分 0.0
04 | ASCENDING | neck=151.790 → 差分 0.0
05 | ASCENDING | neck=157.890 → 差分 0.0
06 | ASCENDING | neck=158.152 → 差分 0.0
07 | DB        | neck=144.940 → 差分 0.0
08 | ASCENDING | neck=144.430 → 差分 0.0
09 | ASCENDING | neck=147.312 → 差分 0.0
10 | ASCENDING | neck=148.104 → 差分 0.0
11 | ASCENDING | neck=156.997 → 差分 0.0
12 | ASCENDING | neck=158.086 → 差分 0.0

■ 新規カラム確認
neck_1h の範囲: min=142.928 / max=158.416
neck_4h の範囲: min=143.943 / max=158.602

■ 構造の妥当性
neck_15m < neck_1h が成立: 10/12件
neck_4h が全件で最大値: 9/12件

■ 完了条件チェック
✅ python src/window_scanner.py エラーなし実行
✅ logs/window_scan_entries.csv 再生成（12件）
✅ logs/window_scan_plots/*.png 再生成（12枚）
✅ 禁止ファイル差分ゼロ
✅ commit 71cf705: Feat: #026a-v2 unified neck + 1H n=3 + structure columns
