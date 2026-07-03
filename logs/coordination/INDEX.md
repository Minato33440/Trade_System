# INDEX.md — coordination 実装ループ索引（指示書 instructions/ ・実行結果 execution_results/・全engine共有）
# 更新: 2026-04-16
# 手動更新（要望7: 自動化はObsidian MCP実装後）

---

## 指示書一覧（instructions/）

| # | ファイル名 | 発行者 | 承認日 | 内容 | 状態 |
|---|---|---|---|---|---|
| #026a-v2 | REX_026a-v2_FINAL.md | Planner + Evaluator | 2026-04-14 | 統一neck原則 + 1H n=3 + neck_4h/neck_1h カラム追加 | ✅ |
| #026b | REX_026b_spec.md | Evaluator | 2026-04-15 | exit_simulator.py 新規作成（決済シミュレーション） | ✅ |
| #026c | REX_026c_spec.md | Evaluator | 2026-04-15 | 指値エントリー方式（neck_15m + 7pips） | ✅ |
| #026d | REX_026d_spec.md | Planner | 2026-04-15 | 4H構造優位性フィルター（neck_4h >= neck_1h） | 🔴 実装中 |

---

## 実装結果一覧（execution_results/）

| # | ファイル名 | 実装日 | 主要結果 | 状態 |
|---|---|---|---|---|
| #026a-v2 | 026a-v2_result.md | 2026-04-14 | 12件検出ヾneck_1h/neck_4h カラム追加完了 | ✅ |
| #026b | 026b_result.md | 2026-04-15 | PF 0.61 / 総損益 -61.3p / 方式B採用 | ✅ |
| #026c | 026c_result.md | 2026-04-15 | PF 2.42 / 総損益 +113.3p / 13件 | ✅ |
| #026d | 026d_result.md | — | 実装中 | 🔴 待ち |

---

## タスク実装ステータス（クイック参照）

```
#026a-v2: 完了 ✅ — neck統一 + 1H n=3 + カラム追加
#026b:    完了 ✅ — exit_simulator.py（方式B）
#026c:    完了 ✅ — 指値エントリー（neck+7pips）/ PF 2.42
#026d:    実装中 🔴 — 4H構造優位性フィルター（neck_4h >= neck_1h）
```

---

## 更新ルール

```
指示書追加時:
  1. instructions/ にファイルを配置
  2. 本INDEXの「指示書一覧」に行を追加
  3. git commit -m "Docs: #026x 指示書追加"

実装結果記録時:
  1. execution_results/ にファイルを配置（命名: <番号>_result.md）
  2. 本INDEXの「実装結果一覧」を更新・ステータスを変更
  3. git commit -m "Docs: #026x 結果記録"
```

---

## 2026-07-02 運用構成の移行注記（append・履歴は温存）

本INDEX #026a-v2〜#026d の「発行者」列（Planner / Evaluator）は、
旧マルチAgent時代（プロンプトインジェクション期）の役割記録である。
現行は Hermes Runtime-Hub 構成に移行済みで、Planner/Evaluator/Advisor の
role分担は無効。governance正本は Trade_System\AGENTS.md（源1枚）。
以降のengine動作は AGENTS.md に従う。

上表は当時の実装ループの事実記録として温存する（書き換えない）。
「発行者」列は "誰が発行したか" の歴史的帰属であり、生きた権限記述ではない。
