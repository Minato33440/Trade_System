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

---

## 2026-06-29 D-2a .CLAUDE.md 削除（重複dotfile・汚染NLM残）
- 対象: .CLAUDE.md（2026-04-18・先頭ドットで無効化済の旧コピー。どのharnessも読まない）
- 確認: 全内容が CLAUDE.md(4-25)/AGENTS.md の鏡像、D-6(Trade_Brain週次)、汚染NLM(2d41d672・死亡フラグ無し)のいずれか。固有の生情報なし
- 実施: git rm（履歴はGitに保全）
- 効果: ガバナンス3重化→2本／最後の非・死亡注記 2d41d672 残存を除去
- 残課題: CLAUDE.md→@AGENTS.mdシム化は D-2b（AGENTS.md 中立化・パス修正後）

---

## 2026-06-30 D-2b 完了確認
- CLAUDE.md → @AGENTS.md シム化 push 済（claudeレーンも新AGENTS.mdに収束）
- 旧 AGENTS.md/CLAUDE.md は logs/archive/ へ退避（snapshot/CLAUDE-2026-6-30）
- 検証: 生governance=AGENTS.md(源)+CLAUDE.md(シム)のみ／2d41d672 生ポインタ=0／logs/Codex 生参照=0
- 残: D-3継続（docs/の Rex役割の著者・QA帰属）／D-4 Handover／D-6 週次系

---

## 2026-07-02 D-3 role分担無効化（INDEX append＋指示書ヘッダ・書き換えゼロ）

- **対象**: `logs/claudecode/INDEX.md`／`instructions/` 配下の完了済み指示書（#026d・#027×2・#028）
- **背景**: docs/全体スイープで旧マルチAgent（Planner/Evaluator/Advisor）の生きた役割記述を洗い出し。指示書群は歴史的帰属＝温存側と確定（判断の型: 死亡注記・歴史帰属は温存／書き換えは⑩違反）
- **実施（全て書き換えゼロ・append/ヘッダ挿入のみ）**:
  - INDEX.md 末尾に移行注記を append ── 「発行者」列は旧構成の役割記録・現行はHermes Runtime-Hub・governance正本=AGENTS.md。表本体は実装ループ履歴として温存
  - `REX_026d_spec.md` に HISTORICAL-RECORD ヘッダ挿入＋承認表記を `ボス・Rex-Evaluator` → `ボス` に中立化
  - `REX_027_BOSS_DIRECTIVE.md`／`REX_027_doc_cleanup_spec.md` にヘッダ挿入（汚染ID `2d41d672` 死亡注記を同梱）
  - `REX_028_spec.md` にヘッダ挿入（04-19・Evaluator単独・§9起動テンプレ無効を明示。028に `2d41d672` は不在のため死亡注記行は含めない）
- **理由**: engine が指示書を読んでも旧role権限を生きた命令として拾わない状態にする（本文＝歴史は温存、生きた誤誘導のみ打ち消し）
- **残課題**: canon本体の role中立化（SYSTEM_OVERVIEW チーム表・Evaluator権限拡張節／ADR 発行責任者・F章管轄・更新ルール／EX_DESIGN §2 チーム表）＝最上位canon方針決定後。地層C（REMOTE_CONTROL/BRANCH_MAP/SIGNALS_SHORT/Wiki_Architecture/RTK）のarchive判断。D-4 Handover／D-6 週次系

---

## 2026-07-02 D-3 canon本体 role中立化（SYSTEM_OVERVIEW / EX_DESIGN / ADR）

- **対象**: docs/直下の最上位canon 3枚。各engine必読書＝供給viewに毎回載るため、履歴温存より「現engineが読んで正しく動く」を優先
- **方針**: 旧版を日付き `logs/archive/` へ凍結退避 → register(旧role分担)を外した現行版を新規作成。記録破壊なし（旧版はarchive+Gitで完全復元可）
- **実施**:
  - `SYSTEM_OVERVIEW.md` ── 「チーム役割分担」表→「運用構成」表(最終判断=ボス/正本=AGENTS.md/Hermes Runtime-Hub構成/固定role分担なし)。Evaluator権限拡張節を削除。拡張可能ファイルの承認ゲート("要確認"/"ボス承認")を除去(distill/昇格はボス設定のLLM Brokerが担うため承認ルート自体が不要)
  - `EX_DESIGN_CONFIRMED.md` ── §2チーム役割分担をセクションごと削除(役割固定が現状存在しないため)、以降§番号を繰り上げ。冒頭/末尾のRex register除去。設計事実(neck定義/パラメータ/決済4段階/数値)は完全保持
  - `ADR.md` ── 生きたrole権限を全抜き(案2)。発行責任者=Evaluator/Plannerへの指揮/F章管轄/更新ルール承認/F-8運用ルール/原則γ Evaluator適用/運用ガイド末尾/D-11・F-7・D-12のrole記述 → 全てボス+AGENTS.md参照に収束。台帳本体(A〜E章の失敗パターン・ボス証言引用・#026系数値)は1バイト不変。歴史的帰属のrole名(F-8「過去にEvaluator役が」等)は過去形固定で温存
- **判断の型**: 「生きた権限記述は中立化/歴史的帰属は温存」。canonは"確定した現在の事実"の領域で、履歴保管はGit(一次)+archiveが担うため二重温存不要。role名でも承認権威・指揮フロー・未来動作割当は抜き、過去の主語・ボス証言は残す
- **役割一元化**: 構成/役割情報はSYSTEM_OVERVIEWに一元化。MINATO_MTF_PHILOSOPHYは非紐づけ(ボス個人の裁量思想一次記録で層が違う)
- **残課題**: 地層Cは処理済(BRANCH_MAP/REMOTE_CONTROL/LOGIC_CONSISTENCY_MATRIX/SIGNALS_SHORT→archive、Wiki_Architecture/RTK→Vault)。層A(scratch/新設・AGENTS.md領域マップ節)は未着手。canon 3枚のコードフェンス(```)が新規作成時に一部剥離→次touch時に囲み直し。system_logs/配下のRTK重複コピー確認

---

## 2026-07-02 logs/claudecode → coordination リネーム（全engine共有領域化）

- **背景**: `claudecode/` は名がClaudeCode専用を示唆するが、実態はgrok/codex含む全engineが触る調整領域。名実不一致がengineを誤誘導（canon register問題と同型）
- **物理**: `git mv logs/claudecode logs/coordination`（綴り確定: coordination）。配下 instructions/・execution_results/・INDEX.md・maintenance_log.md・README.md ごと移動
- **併設**: `logs/scratch/<engine>/`（claude/codex/grok レーン別・各engineの検索/探索ログ）。coordination（実装ループ+整理オペ）と役割分離
- **生きたパス追従（全数）**:
  - AGENTS.md: STEP3 指示書パス／結果報告出力先 → coordination。新節「logs/ 領域の分担」追加（coordination/scratch/archive/docs_archive の棲み分け明記）
  - README.md: 全面現行版化（ClaudeCode専用→全engine共有coordination・role名除去・maintenance_log系統追記・append-only原則明記・scriptパス案 update_coordination_index.py）
  - SYSTEM_OVERVIEW.md／EX_DESIGN_CONFIRMED.md §5: ディレクトリツリーの logs/claudecode/ → coordination/
  - INDEX.md: タイトルを実態化（ClaudeCode専用索引→coordination 実装ループ索引・全engine共有）
- **温存（歴史的帰属・書き換えず）**: AGENTS.md ヘッダ更新行「logs/claudecode パス修正」／過去事故事例の Evaluator・Advisor 担当表記／本log D-3エントリの logs/claudecode パス（いずれも当時の事実記録）
- **理由**: 全engineが同一の調整領域名で収束。名前が「誰の領域か」でなく「何の領域か」を示す状態に
- **残課題**: 両canon（SYSTEM_OVERVIEW/EX_DESIGN）のコードフェンス剥離（push副作用でツリー・データフロー・依存マップ等が地の文化）→ 次のcanon編集時に ``` 再囲み。層A（AGENTS.md領域マップ節の拡充）は着手可。system_logs/配下RTK重複の確認