# Handoff ── Trade_System KPS整理（新スレ用）

> 作成: 2026-06-30 / 前スレからの引き継ぎ
> **正本は `Trade_System\docs\Trade_System_KPS_spec_v4.md`**（§0.5 実施状況サマリが現在地の全て）。
> 本Handoffは要約。詳細・判断根拠は v4 を実物で読むこと（記憶より実物が確実）。

---

## 0. 最初の一手（新スレRexはここからでOK）

1. `Trade_System\docs\` の **spec v4 を実物で読む**（特に §0.5 実施状況・§6 層Bキュー）
2. **D-3継続**から再開 ── `ADR.md` / `EX_DESIGN_CONFIRMED.md` を実物で開き、「生きた権限記述」があるか確認
3. 着手前に該当ファイルを実物readしてから判断（記憶で書かない・前スレで2回それに救われた）

---

## 1. 何をやっているか（背景）

Trade_System を **単一モデル時代の地層 → マルチAgent(Hermes Runtime-Hub)構成**へ、canonを壊さず整理している。リポは **純アルゴ開発の単一ドメイン**（regime/GM週次/distilled は姉妹リポ Trade_Brain の領分・scope外）。

**3engine構成:** grok(OAuth gateway) / codex(OAuth gateway) / claude(API gateway)。各 Provider隔離 Gateway を ACP-Hermes-Desktop が起動。

---

## 2. 完了済み（✅ 触らない）

- **D-1 汚染NLM遮断**: `REX_BRAIN_SYSTEM_GUIDE.md`（汚染NLM`2d41d672`を現役クエリ先として案内していた）を `logs/archive/` 退避 ＋ `SYSTEM_OVERVIEW.md` のdangling 1行除去。生ポインタ=0。
- **D-2 governance単一源化**: `AGENTS.md`=唯一の源（harness中立・`logs/claudecode`パス修正・思考フラグ表撤去）／`CLAUDE.md`=`@AGENTS.md`シム／`.CLAUDE.md`=削除。旧全文は `logs/archive/`。

**確定したgovernance形（重要・前提知識）:**
- 源は `Trade_System\AGENTS.md` 1枚。grok/codex/claude(gateway)は **Hermes dir-scope注入**で、ClaudeCode-nativeは **CLAUDE.md→@AGENTS.md シム**で、同一AGENTS.mdに収束。
- **Profile AGENTS.md（人格・各Profile側）と Project AGENTS.md（現場canon・本リポ）は別物・両方読む。** 混同しない。
- AGENTS.md に **判事・役割権威は載せない**（register最小・権威はcanon自身）。

**新設インフラ:**
- `logs/claudecode/maintenance_log.md` … governance整理オペの時系列ログ（append-only・実装ループのINDEX.mdとは別系統）。**層Bの各件はここに追記**。
- `logs/archive/` … 旧版の凍結退避先。

---

## 3. 残作業（§6 層Bキュー・上から順に）

| # | 内容 | 状態 |
|---|---|---|
| **D-3継続** | docs/配下の `Rex-Advisor/Planner/Evaluator` を**選別**処理 | 🔶 次これ |
| **D-6** | `REDIUM.md`＋`logs/gm`参照（Trade_Brain週次系の紛れ込み）を `logs/archive/` へ除去 | 🔶 |
| **D-4** | `Handover.md`（旧UCAR_Dialyパス）→ `logs/archive/` | ⬜ |
| **層A** | 領域ヘッダ付与・`scratch/`新設・AGENTS.md領域マップ節（§3/4/5-3） | ⬜ |

---

## 4. 引き継ぐ判断の型（★これが一番大事）

D-1で確立し、D-3でもそのまま効く選別ルール：

> **生きたポインタ／権限は消す・中立化する。死亡注記と歴史的帰属は温存する。**

D-3継続での具体化：
- **標準役割権威**（生きた権限表・「Evaluator承認後のみ」等の地の文）→ **中立化**（「ボス承認/昇格判定経由」へ）
- **歴史的帰属**（日付き仕様の「作成:Rex-Planner/監査:Rex-Evaluator」、`Base_Logic/MTF_INTEGRITY_QA.md`等の**追記型QA対話の発言者**）→ **温存**（coordination同様の履歴。書き換えは記録破壊＝⑩違反）

---

## 5. 運用ルール（厳守）

- **Claude側はリポに書き込まない。** 実書込は全てボスがGitHub MCP経路（`create_or_update_file`全文渡し）。Rexは実物readで確認＋確定内容を渡すまで。
- **改訂前に現物を `logs/archive/` へ凍結退避。**
- **昇格判定の順序**: ボス承認 → `maintenance_log.md` 追記 → canon改訂。
- 各着手後に**スイープで検証**（汚染ID `2d41d672` / 旧パス `logs/Codex` / governance重複 / dangling参照）。read系ツール: filesystem MCP・Windows-MCP:FileSystem・Desktop Commander content search。

---

## 6. scope外（将来・触らない）

Trade_System がライブ化した段階で、`REX_BRAIN_VAULT` 上に Trade_Brain×Trade_System 統合運用を別建て（越境regime供給・統合BrokerはVault層）。**今は含めない。**

---

*前スレ到達点: governance の背骨が1本通った（源1枚＋シム・汚染遮断・整理ログ）。新スレは D-3継続の選別から。*