<!-- KPS-REGION: coordination / maintenance（governance整理オペの時系列ログ・append-only）
     実装ループ(instructions/・execution_results/)とは別系統。書き換え禁止・追記のみ。
     索引は INDEX.md（#番号の実装ループ専用）。本ファイルは整理オペ(D-x)専用チャンネル。 -->

# maintenance_log.md — Governance / 整理オペ 時系列ログ

> 用途: KPS 層B（governance整理・ドリフト解消 D-1〜）の時系列記録。append-only。
> 実装ループ（指示書#XXX・結果#XXX）は INDEX.md 系統。混ぜない。
> 各エントリ: 日付 / 対象 / 実施 / 理由 / 残課題。

---

## 2026-06-29 D-1 汚染NLM遮断

- **対象**: `docs/REX_BRAIN_SYSTEM_GUIDE.md`（pre-migration・旧Planner/Evaluator表記・汚染NLM `2d41d672` を「現役クエリ先」として案内・STEP 0-A で開始時読込指定）
- **実施**: `logs/docs_archive/` へ退避（ボス実施）
- **canon源は改訂不要**: AGENTS.md / CLAUDE.md / SYSTEM_OVERVIEW.md は `2d41d672 = 切離済・廃止` と既に正記載
- **随伴修正**: SYSTEM_OVERVIEW.md の docs/ ファイルツリーから `REX_BRAIN_SYSTEM_GUIDE.md` 行を除去（退避に伴う dangling 解消）
- **残存 `2d41d672`（触らない）**: REX_027_BOSS_DIRECTIVE / 027_doc_cleanup_spec / repo_fix_report＝履歴、AGENTS/CLAUDE/SYSTEM_OVERVIEW＝死亡注記、退避済GUIDE＝dead storage、`.CLAUDE.md`＝無効dotfile(→D-2で削除)
- **検証**: `2d41d672` 生ポインタ = 0件（content search で確認）
- **理由**: engine セッション開始時の汚染NLMクエリ経路を遮断
- **残課題**: なし（D-1クローズ）。`.CLAUDE.md` の同ID残存は D-2 の削除で解消