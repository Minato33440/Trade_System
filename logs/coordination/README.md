# logs/coordination/ — 実装ループ & 整理オペ 調整ディレクトリ

## 目的

指示書と実装結果、および governance 整理オペを時系列で追跡・保管する
Git 管理ディレクトリ。全 engine 共有の coordination 領域（append-only）。

スレッドをまたいでも「何を指示して何が実装されたか」「どの整理オペをいつ実施したか」を
原文で参照できる。

---

## ディレクトリ構造

```
logs/coordination/
├── README.md              ← 本ファイル（ディレクトリ説明）
├── INDEX.md               ← 実装ループ索引（指示書・実行結果の時系列一覧・手動更新）
├── maintenance_log.md     ← governance整理オペ ログ（D-x・append-only）
├── instructions/          ← 指示書原文
└── execution_results/     ← 実装結果原文（報告書）
```
> 実装ループ（instructions/・execution_results/・INDEX）と整理オペ（maintenance_log）は
> 別系統。索引は INDEX が実装ループ専用、maintenance_log が整理オペ専用。混ぜない。

---

## 運用ルール

```
1. 指示書は engine に投入する前に instructions/ にコピーを配置する
2. 実装結果の報告は execution_results/ に保存する
3. INDEX.md を更新してから push する（実装ループの場合）
4. 命名規則:
   指示書:    REX_<タスク番号>_spec.md  （例: REX_026d_spec.md）
   実装結果:  <タスク番号>_result.md    （例: 026d_result.md）
5. commit メッセージ: "Docs: #<番号> 指示書追加" / "Docs: #<番号> 結果記録"
6. 書き込みは append-only。既存の実装ループ記録・整理オペ記録は書き換えない
  （歴史的帰属の温存。現行構成への移行注記は末尾 append で行う）
```

---

## logs/ 内の他領域との関係
logs/coordination/   ← 本ディレクトリ（実装ループ + 整理オペ・全engine共有）
logs/scratch/<engine>/ ← 各engineの検索/探索ログ（claude/codex/grok レーン別）
logs/archive/        ← 旧版canon/governanceの凍結退避（参照禁止）
logs/docs_archive/   ← 旧版設計文書（参照禁止）

---

## 将来予定（要望7）

```
優先度: 低（Obsidian MCP実装後）
内容: 毎コミット後に instructions/ と execution_results/ を走査して
      INDEX.md を自動更新するスクリプト
      パス案: update_coordination_index.py
```
