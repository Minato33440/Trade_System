# Σ:UCAR-Trade — Trade_Record（GM Weekly Ops）

このリポジトリは、**GM（グローバルマクロ）運用**を「週次レビュー → distilled（判断更新点）熟成」という形で蓄積し、  
将来の環境認識・検証・自動化（MCP/ローカル連携）に耐える **巡れる記録（STATUS → _index → weekly → review/meta/charts → distilled）** を作るためのものです。

---

## Quick Start（迷ったらここ）
1. **現在地（最新方針）**：`Trade_Record/STATUS.md`  
2. **運用ルール（憲法）**：`Trade_Record/Trade-Main.md`  
3. **引継ぎ（別スレ/別環境）**：`Trade_Record/HANDOFF.md`  
4. **全ファイル用途マップ**：`Trade_Record/FILE_MAP.md`  

---

## Directory Map（主要ディレクトリ）
- `Trade_Record/`
  - `STATUS.md`：最新のWeekly Brief（短く）
  - `Trade-Main.md`：目的・導線・週次ループ・禁止事項
  - `HANDOFF.md`：引継ぎ手順（入力パッケージ／出力セット）
  - `BRANCH_MAP.md`：Git運用（枝を切る条件・命名・合流ルール）
  - `FILE_MAP.md`：用途一覧（何がどこにあるか）

- `Trade_Record/logs/gm/weekly/YYYY/`
  - `_index.md`：週次一覧（年単位の導線）

- `Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/`
  - `note.md`：週内メモ（facts/decisions）＋ Monday AMラベル欄
  - `review.md`：週末確定レビュー（終値ベース）
  - `meta.yaml`：機械拾い用タグ（regime/trigger/levels/decision）
  - `charts.md`：チャートリンク正本（週足＋日足を基本）
  - `charts/`：任意（ローカル画像置き場）

- `Trade_Record/versions/distilled/YYYY/`
  - `distilled-gm-YYYY-MM.md`：月次 distilled（週ごとに追記で熟成）

- `Trade_Record/_archive/`
  - `source_threads_v1/`：一次資料（過去スレ原文・統合アーカイブ・raw）

---

## Workflow（週次ループ：固定）
### 平日（随時）
- 事実（facts）を `note.md` に追記（必要なら decision も1行）
- チャートURLは直貼りせず、週末に `charts.md` に集約

### 週末（Fri close〜Sat）
- 週終値確定後、該当週フォルダに
  - `review.md`（結果＋来週行動）
  - `meta.yaml`（タグ整形）
  - 年次 `_index.md` に1行追記
- 月次 `distilled-gm-YYYY-MM.md` に「判断更新点」を追記

---

## Monday AM（週明け朝）ラベル付け（重要：行動トリガー禁止）
- 月曜朝は薄商いで“狩り”が混ざりやすい前提で、**A/B/Cの寄り推定（ラベル付け）だけ**行う  
- 実行判断は **終値ゲート（Tokyo close / NY close）** で確定  
- 記録：
  - ラベル → 該当週 `note.md` 冒頭テンプレ
  - 終値（Tokyo/NY）→ `note.md` の Facts欄
  - 週末まとめ → `review.md`

---

## Canonical Policy（正本ポリシー）
- **main が正本**（STATUS / weekly logs / index / distilled）
- 週次ログ追加・軽微な追記は main で“積む”
- 大きな変更（スキーマ/構造/抽出パック/自動化PoC）は branch → PR → main

---

## Distilled（熟成の考え方）
distilled は「週の出来事まとめ」ではなく、**判断が変わった瞬間**だけを残すための核です。  
週が増えるほど「検索 → 再利用 → 精度向上」が効いてきます。

---

## Notes（免責）
本リポジトリの内容は投資助言ではなく、自己運用の記録・検証・改善のためのログです。  
最終判断は常に自己責任で行います。
