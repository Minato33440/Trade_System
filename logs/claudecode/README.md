# logs/claudecode/ — ClaudeCode 実装管理ディレクトリ

## 目的

Planner / Evaluator が発行した指示書と、ClaudeCode による実装結果を
時系列で追跡・保管するための Git 管理ディレクトリ。

スレッドをまたいでも「何を指示して何が実装されたか」を原文で参照できる。

---

## ディレクトリ構造

```
logs/claudecode/
├── README.md              ← 本ファイル（ディレクトリ説明）
├── INDEX.md               ← 全指示書・実装結果の時系列一覧（手動更新）
├── instructions/          ← 指示書原文（Planner / Evaluator 発行）
└── execution_results/     ← ClaudeCode 実装結果原文（報告書）
```

---

## 運用ルール

```
1. 指示書は ClaudeCode に投入前に instructions/ にコピーを配置する
2. ClaudeCode の結果報告は execution_results/ に保存する
3. INDEX.md を更新してから git commit する
4. 命名規則:
   指示書:    REX_<タスク番号>_spec.md  （例: REX_026d_spec.md）
   実装結果:  <タスク番号>_result.md    （例: 026d_result.md）
5. git commit メッセージ: "Docs: #<番号> 指示書追加" / "Docs: #<番号> 結果記録"
```

---

## 将来予定（要望7）

```
優先度: 低（Obsidian MCP実装後）
内容: 毎コミット後に instructions/ と execution_results/ を走査して
      INDEX.md を自動更新するスクリプト
      パス案: tools/update_claudecode_index.py
```
