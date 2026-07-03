# BRANCH_MAP

## 0) 役割（このファイルは何？）
- このリポジトリの「運用ルール」「どこに何があるか」「いつ枝を切るか」を1枚に固定する。
- 迷ったら **ここ → Trade-Main → STATUS → weekly/_index → 該当週** の順で辿る。

---

## 1) Canonical（正本）ポリシー
- **main が正本（canonical）**：日々の運用ログは main に集約する。
- 日々運用（ops）の正本はここ：
  - `Trade_Record/STATUS.md`
  - `Trade_Record/logs/gm/weekly/YYYY/_index.md`
  - `Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/{note.md,meta.yaml,review.md,charts.md}`
  - `Trade_Record/versions/distilled/YYYY/`（月次 distilled を置く）

---

## 2) Branch を切る条件（切らない条件）
### Branch を切る（枝を使う）
- フォルダ規約/スキーマ変更（meta.yamlの項目追加・命名変更など）
- 月次抽出パック作成（distilledの再構成、まとめ直し）
- 自動化PoC（MCP/ローカル連携、生成スクリプト導入など）
- 大きめのリファクタ（導線・命名・階層の整理）

### Branch を切らない（mainに直で良い）
- 週次ログ追加（wkNNフォルダ追加、note/review/meta/charts更新）
- STATUS更新
- _index.md への1行追記
- distilled への追記（既存ファイルに週のdistilledを追記するだけ）

---

## 3) Naming Conventions（ブランチ命名）
- `trade-gm-YYYY-MM` : 月次抽出 / distilled pack
- `schema-*` : meta.yaml / tags / folder rules changes
- `mcp-*` : MCP / automation experiments
- `fix-*` : one-off repair work
- `refactor-*` : structure cleanup / navigation improvements

---

## 4) Merge Rules（合流ルール）
- 重要変更は **PR → main**（自分用でもPRでログ残すのが強い）
- main で history rewrite しない（rebase強制しない）
- 週次ログは「積む」運用（過去週の大改変は極力しない）

---

## 5) Worktree の扱い（ローカル運用）
- `WORKTREES/` は **ローカル作業場**（必要なら置くが、原則repo正本は `Trade_Record/`）
- distilled の正本は **Trade_Record/versions/distilled/YYYY/** に置く
  - 例：`Trade_Record/versions/distilled/2025/distilled-gm-2025-12.md`
- worktree 側に同名distilledがある場合：
  - main側（Trade_Record）に統一し、worktree側は作業用にする（複製が正本にならないよう注意）

---

## 6) Release / Tag（任意だけど効く）
- 月末や四半期で区切るなら Git tag を推奨：
  - `gm-2025-12-close`（12月のdistilled確定）
  - `gm-2025-Q4-close`（四半期のまとめ確定）

---

## 7) 最短ナビ（迷子防止）
- 今日の現在地：`Trade_Record/STATUS.md`
- 週次一覧：`Trade_Record/logs/gm/weekly/YYYY/_index.md`
- 該当週：`Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/`
- 月次 distilled：`Trade_Record/versions/distilled/YYYY/`

