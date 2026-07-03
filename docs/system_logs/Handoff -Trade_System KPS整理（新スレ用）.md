# Handoff — Trade_System KPS整理 完了 → Hermes実運用フェーズへ

作成: 2026-07-03 / 前スレ: Trade_System KPS整理（canon中立化・coordination化）
次スレの主題: **Hermes-Agent（grok/codex/claude gateway）による Trade_System の具体運用**

---

## このスレで完了したこと（KPS層B・governance整理の総仕上げ）

前スレから引き継いだ D-3（role中立化）を完遂し、canon全体を Hermes-Hub 構成に揃えた。

### canon 3枚の role中立化（旧マルチAgent → 現行構成）
- **SYSTEM_OVERVIEW.md**: チーム役割分担表→運用構成表（最終判断=ボス/正本=AGENTS.md/固定role分担なし）。Evaluator権限拡張節・承認ゲート除去
- **EX_DESIGN_CONFIRMED.md**: §2チーム役割分担を削除・§番号繰り上げ。Rex register除去。設計事実（neck定義/パラメータ/決済4段階/数値）は完全保持
- **ADR.md**: 生きたrole権限を全抜き（発行責任者/F章管轄/更新ルール/運用ガイド/予約記述）→ ボス+AGENTS.md参照に収束。失敗パターン集・ボス証言・数値は不変。歴史的帰属のrole名は過去形で温存
- 旧版は全て `logs/archive/` に日付き凍結退避（記録破壊なし）

### coordination化（全engine共有領域）
- `logs/claudecode/` → `logs/coordination/` にリネーム（ClaudeCode専用の名を実態=全engine共有に）
- `logs/scratch/<engine>/`（claude/codex/grok）新設 — 各engineの検索/探索ログ
- 全ルート追従: AGENTS.md（STEP3/結果出力先/logs領域分担節）、README、canon 2枚のツリー、INDEXタイトル

### 指示書の歴史化（temporal温存）
- #026d/#027×2/#028 に HISTORICAL-RECORD ヘッダ挿入（完了済み・role無効・AGENTS.md正本を明示）
- INDEX.md 末尾に role分担無効の移行注記を append（発行者列は歴史記録として温存）

### Fable5レビュー反映（M-4）+ 精度修正
- 別モデル（Fable5）に canon をレビューさせ5件検出 → A中立化漏れ/B番号空間衝突/Cツリー実態ズレ/D日付ズレ/E宛先名残存 を修正
- maintenance採番を **D-x → M-x** に切替（ADR D章との衝突解消）
- `docs_archive`（実在しない退避先）参照を全canonから一掃 → `logs/archive/` に統一
- トップ `README.md` 新規作成（リポ入口導線）

### 地層整理
- 地層C（旧UCAR時代）: BRANCH_MAP/REMOTE_CONTROL/LOGIC_CONSISTENCY_MATRIX/SIGNALS_SHORT → archive、Wiki_Architecture/RTK → Vault
- REDIUM.md（Trade_Brain用旧版）→ Trade_Brain\docs\archive\ へ移設

---

## 現在の到達状態（新スレの前提）

- **governance**: AGENTS.md 1枚に収束。全engineが同一canonに従う。固定role分担なし・最終判断はボス
- **canon**: docs/直下（SYSTEM_OVERVIEW/EX_DESIGN/ADR/PLOT_DESIGN/Base_Logic）が現在有効な設計。role register 除去済み
- **coordination**: logs/coordination/（instructions/・execution_results/・INDEX・maintenance_log M-x）が全engine共有の作業ログ・append-only
- **scratch**: logs/scratch/<engine>/ は空（各レーン未使用）
- **実装ロジック**: #026d（PF 4.54 / 60% / +150.6p）不変。src/構造再編は Phase 1-2 完了、Phase 3-4 未着手

---

## 次スレの主題: Hermes-Agent による実運用

canon整備が済んだので、次は **Hermes Runtime-Hub の各gateway（grok/codex/claude）が実際に Trade_System で作業する運用**に進む。想定される最初の論点:

1. **各engineのセッション起動フローの実地確認**
   - grok/codex が Hermes dir-scope で AGENTS.md 自動注入 → セッション開始手順（STEP1-5）通りに動くか
   - claude gateway（メタード lane）の起動と、ClaudeCode-native（CLAUDE.md シム経由）の使い分け
2. **編集経路の実運用検証**
   - MCP接続セッション = GitHub MCP のみ / ローカル実装 = git pull --rebase 先行。二系統pushの単方向フローが実際に守れるか
   - filesystem write禁止ルールが各engineで効くか
3. **scratch レーンの運用開始**
   - grok/codex が検索/探索を scratch/<engine>/ に書き始める。使い方が定まったら層A（scratch運用ルール）を AGENTS.md に追記（現状は「早すぎる構造化」回避で保留中）
4. **Broker による distill/昇格の実装**
   - coordination → canon の蒸留を、ボス設定の LLM Broker が担う設計。この経路の具体化

---

## 未処理の残課題（実運用と並行 or 次段）

- **層A**: scratch運用ルールの AGENTS.md 追記（grok/codex が実際に使い始めてから）
- **README トップ**: 構成ツリーのコードフェンス（```）巻き直し（次touch時・軽微）
- **system_logs/ RTK重複**: docs/system_logs/ 配下の RTK コピー確認
- **Phase 3-4**: src/責務別ディレクトリ化（Phase 3）、D-12/D-13創作混入の裁量整合版訂正（Phase 4・REX_029+）
- **D-4/D-6の名残**: Handover.md（旧UCARパス）、GM週次系の最終確認（大半は処理済）

---

## 引き継ぎの型（このスレで確立した作業原則）

新スレの engine / Rex が踏襲すべきこと:
- **記憶で書かない**: canon・パスは必ず実物を read してから触る。今スレでも複数回これに救われた
- **判断の型**: 生きた権限記述=中立化 / 歴史的帰属=温存。canonは"確定した現在の事実"、履歴保管はGit+archive
- **書込経路**: Rexはリポに直接書かない。実書込は全てボスのGitHub MCP経路。改訂前は旧版をarchiveへ凍結退避
- **採番**: 整理オペは maintenance_log に M-x で記録（append-only）。実装ループは INDEX に #番号
- **外部レビュー**: canon整理後は別モデルにレビューさせると取りこぼしを拾える（Fable5がA/Bを検出した実績）