=== #026b 結果報告 ===
# 実装日: 2026-04-15 / commit: 58c526f

■ 実装方式
方式B（独自実装）
理由: manage_exit() は neck_1h を半値決済トリガーとするが、ADR D-6 は neck_4h を要求（仕様不一致）。

■ 統計指標
指標          | #026b   | #018    | 差分
総トレード    | 12件    | 20件    | -8件
勝率          | 25.0%   | 55.0%   | -30.0%
PF            | 0.61    | 5.32    | -4.71
MaxDD         | 138.4p  | 14.9p   | +123.5p
総損益        | -61.3p  | +91.6p  | -152.9p

■ 決済段階別
exit_phase | 件数 | 平均pnl
stage1     | 7    | -9.81p
stage2     | 4    | -20.07p
stage3     | 1    | +87.65p

■ 完了条件チェック
✅ python src/exit_simulator.py エラーなし実行
✅ logs/window_scan_exits.csv 生成（12件）
✅ 禁止ファイル差分ゼロ
✅ commit 58c526f
