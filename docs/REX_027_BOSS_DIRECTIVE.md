# REX 指示書 #027 — REX_AI\ 配下リポジトリ構造変更および Trade_System ドキュメント整合性回復
# 発行者: ボス（Minato）
# 起草: Advisor（Claude Opus 4.7・相談役）
# 宛先: Rex-Evaluator（Opus 4.6） / Rex-Planner（Sonnet 4.6）共用
# 発行日: 2026-04-18
# 思考フラグ: think harder（アーキテクチャ全体に影響する構造変更）

---

## 本指示書の位置づけ

本指示書は通常の #NNN spec とは異なり、**ボスからの直接指示**として
以下の性質を持つ:

1. **Trade_System の実装ロジック変更ではない**
   - 凍結ファイル 4 本には一切触れない
   - window_scanner.py / exit_simulator.py にも触れない
   - バックテスト結果（PF 4.54 / 勝率 60% / +150.6p）は変化しない

2. **REX_AI\ 配下の全体構造変更である**
   - Trade_System リポと新設 Trade_Brain リポの 2 リポ間調整
   - NLM ノートブック 1 件の改名 + 1 件の新設
   - Obsidian Vault ディレクトリ 1 ルートの新設

3. **Evaluator / Planner 双方が関与する**
   - Evaluator: ADR 採番（D-11 / F-7）、Vault 関連承認、指示書全体の最終監査
   - Planner: Trade_System ドキュメント改訂の実装指示書起草

4. **本タスクの起点はボスの判断**
   - データ移行（Trade_System/logs/gm/ + versions/distilled/ → Trade_Brain/）は
     2026-04-18 時点でボス実施により完了済み
   - 以降の整合性回復・Wiki 構築が本指示書のスコープ

---

## 0. 背景と目的

### 0-1. なぜこの変更が必要か

#026d 完了により Trade System のコアロジックが数値的に収束した。
これは「データ整合性が取れている最後の静的点」であり、以降は
フィルター追加・Phase D（出来高）で構造が動的に変化していく。

静的な今のうちにナレッジシステム基盤を固めないと:

- Trade_System リポに蓄積される raw/distilled データが肥大化
- 「実装リポに戦略データが混在」という論理矛盾が深まる
- 複雑化してからの分離コストは数倍になる

ボスの判断: **今が分離タイミング**

### 0-2. 本指示書が扱う範囲

```
✅ 扱う:
  - Trade_Brain リポ立ち上げ完了確認
  - Trade_System ドキュメントの整合性回復
  - NLM ノートブック改名・新設
  - ADR.md への追記（F-7 / D-11）
  - adr_reservation.md の更新
  - Vault 側 wiki/trade_brain/ の構築指針

❌ 扱わない:
  - Trade_System のロジック変更（凍結ファイルは触らない）
  - バックテスト再実行（数値は変わらない）
  - Trade_Brain の Strategy_Wiki/ 本体構築（別タスク・REX_028 想定）
  - Trade_System の Vault wiki/trade_system/ 構築（REX_027 本来の Vault 構築・別タスク）
```

### 0-3. 完了済みの作業（2026-04-18 時点）

本指示書発行前に以下は完了している:

```
✅ Trade_Brain リポジトリ新設（Minato33440/Trade_Brain）
✅ raw/ データ移行（daily/2026/ + weekly/2025-2026/ + boss's-weeken-Report/）
✅ distilled/ データ移行（2025/ + 2026/）
✅ Trade_Brain/CLAUDE.md / README.md / docs/ 初期構築（Advisor 起草）
✅ Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md（Vault 構造提言書）
```

本指示書は**これ以降の作業**を対象とする。

---

## 1. 現状と残課題

### 1-1. Trade_System リポの現状

```
✅ 物理削除完了:
  - Trade_System/logs/gm/ （ミナトが git rm 実施）
  - Trade_System/versions/distilled/ （同上）

⚠️ ドキュメント記述が残存:
  - CLAUDE.md（「logs/gm/」への参照なし、ただし整合性確認が必要）
  - docs/SYSTEM_OVERVIEW.md（ディレクトリツリーに「logs/」記載あり）
  - docs/ADR.md（Trade_Brain 分離の記録なし・F-7 / D-11 未記載）
  - docs/REX_BRAIN_SYSTEM_GUIDE.md（NLM ノートブック名が旧名のまま）
  - 各種 docs/*.md で「versions/distilled/」参照があれば要修正

⚠️ adr_reservation.md（Vault 側）:
  - F-7（Vault 構造標準化）の予約未実施
  - D-11（Trade_Brain 分離）の予約未実施
```

### 1-2. NLM 側の現状

```
現状:
  REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）
  → Trade_System 設計文書用として運用中

理想の最終形:
  REX_System_Brain  ← 既存 REX_Trade_Brain の改名後
  REX_Trade_Brain   ← 新設（Trade_Brain リポ用・distilled 投入先）
```

### 1-3. Vault 側の現状

```
✅ 既存:
  REX_Brain_Vault/wiki/trade_system/
    - doc_map.md
    - adr_reservation.md
    - pending_changes.md
    - pending_nlm_sync.md

❌ 未設置:
  REX_Brain_Vault/wiki/trade_brain/
    （Trade_Brain 用の運用ファイル群）
```

---

## 2. タスク分解（優先順位付き）

### Task A（🔴 最優先）: Trade_System ドキュメント整合性回復

**担当**: Planner 起草 → Evaluator 承認 → ClaudeCode 実装

**対象ファイル**:
```
Trade_System/
├── CLAUDE.md
├── docs/SYSTEM_OVERVIEW.md
├── docs/ADR.md
├── docs/REX_BRAIN_SYSTEM_GUIDE.md
└── 他 docs/ 配下で logs/gm/ または versions/distilled/ への参照があるファイル全て
```

**具体的な修正内容**:

#### A-1. CLAUDE.md

```
現状確認:
  grep -n "logs/gm\|versions/distilled" CLAUDE.md

修正:
  - もし参照があれば全て削除
  - 「外部リソース参照先」セクションに Trade_Brain リポへの言及を追加
  - NLM ノートブック名を REX_System_Brain に更新（Task B 完了後）
```

#### A-2. docs/SYSTEM_OVERVIEW.md

```
現状確認:
  ディレクトリツリーセクションに logs/gm/ / versions/distilled/ の記載あり

修正:
  - ディレクトリツリーから両ディレクトリを削除
  - 末尾または適切な位置に「データ移行履歴」セクション追加:
    
    | 日付 | 内容 |
    |---|---|
    | 2026-04-18 | logs/gm/ を Trade_Brain/raw/ に移行 |
    | 2026-04-18 | versions/distilled/ を Trade_Brain/distilled/ に移行 |
    | 2026-04-18 | 詳細は Trade_Brain リポの CLAUDE.md を参照 |
  
  - 「外部リソース参照先」セクションに Trade_Brain 追加
```

#### A-3. docs/ADR.md

```
追記項目:

■ D-11 を新設（D セクション末尾）
  D-11. Trade_Brain 分離によるリポ構造最適化（2026-04-18 確定）
  
  症状: Trade_System/logs/gm/ と versions/distilled/ に戦略データが蓄積され、
        実装リポと戦略データが混在する論理矛盾が発生。
        #026d 完了により静的点が取れたタイミングで分離判断。
  
  対応: Trade_Brain リポを新設し、以下を物理移行:
        - logs/gm/ → Trade_Brain/raw/（gm/ 階層除去してフラット化）
        - versions/distilled/ → Trade_Brain/distilled/
  
  教訓: 実装ロジックが収束した「静的点」で関連データの分離判断を行う。
        構造が動的化してからの分離コストは数倍になる。
        データの性質（静的/動的）でリポを分けることで運用ルール（CLAUDE.md）の
        独立性が保たれる。

■ F-7 を新設（F セクション末尾）
  F-7. Vault 構造標準化（2026-04-18 確定）
  
  根拠文書: Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md
  
  方針:
    - Vault ルート: REX_Brain_Vault/wiki/
    - Trade_System 用: wiki/trade_system/
    - Trade_Brain 用:  wiki/trade_brain/
    - 共通: wiki/shared/（将来のレジームフィルター連携等）
  
  実装順序: REX_027_ADVISOR_PROPOSAL.md §9 Phase 1〜5 に準拠。
           Phase 1（骨組み構築）を最優先で実施。

■ 更新ルールセクションの「発行責任者」注記は変更なし
  （F-7 / D-11 の採番は Evaluator が adr_reservation.md で確定させる）

■ 「#026シリーズ最終結果」表の下に新セクション追加:
  
  ## 2026-04-18 リポ構造変更
  
  | 項目 | 内容 |
  |---|---|
  | 変更種別 | リポジトリ分離（実装/知識） |
  | 影響範囲 | Trade_System ディレクトリ構造・NLM・Vault |
  | 実装ロジック影響 | なし（凍結ファイル・バックテスト数値すべて不変） |
  | 関連 ADR | D-11 / F-7 |
  | 根拠文書 | REX_027_ADVISOR_PROPOSAL.md / REX_027_BOSS_DIRECTIVE.md |
```

#### A-4. docs/REX_BRAIN_SYSTEM_GUIDE.md

```
修正項目:

■ §1「何が使えるか」の REX_Trade_Brain セクション
  現状:
    REX_Trade_Brain
    ノートブックID: 2d41d672-f66f-4036-884a-06e4d6729866
    ノートブック名: REX_Trade_Brain
  
  修正後:
    REX_System_Brain（旧: REX_Trade_Brain、2026-04-18 改名）
    ノートブックID: 2d41d672-f66f-4036-884a-06e4d6729866
    ノートブック名: REX_System_Brain
    用途: Trade_System 設計文書用
    
    【関連】
    REX_Trade_Brain（新設・2026-04-18）
    用途: Trade_Brain リポ用（distilled 投入先）
    詳細: Minato33440/Trade_Brain の CLAUDE.md 参照

■ §2「REX_Trade_Brain に入っている設計ソース」を
  「REX_System_Brain に入っている設計ソース」に改題

■ §8「参照先マップ」にエントリー追加:
  Trade_Brain リポの状況      → Minato33440/Trade_Brain/README.md
  戦略アーカイブの検索         → REX_Trade_Brain（NLM）
```

**Task A 完了条件**:
```
□ Trade_System/CLAUDE.md に logs/gm または versions/distilled 参照なし
□ Trade_System/docs/SYSTEM_OVERVIEW.md にデータ移行履歴セクション追加
□ Trade_System/docs/ADR.md に D-11 / F-7 追記
□ Trade_System/docs/REX_BRAIN_SYSTEM_GUIDE.md で NLM 名称更新
□ その他 docs/ 配下で logs/gm/ または versions/distilled/ への参照ゼロ
□ Trade_System のコード（src/*.py）に一切変更なし
□ バックテスト数値（PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p）不変確認
□ git commit -m "Docs: #027 Trade_Brain 分離に伴う整合性回復"
```

---

### Task B（🟡 中優先）: NLM ノートブック整理

**担当**: ボス（ミナト）実施・Claude Desktop 経由

**作業内容**:
```
1. 既存 REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）を改名
   → REX_System_Brain

2. 新規ノートブック REX_Trade_Brain を作成

3. Trade_Brain/distilled/ 配下を新 REX_Trade_Brain に source_add
   - distilled/2025/*.md（全て）
   - distilled/2026/*.md（distilled-gm-2026-1 〜 4）
```

**手順（Claude Desktop で実行）**:
```
Claude に向かって:
「REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）を
 REX_System_Brain に改名してください」

その後:
「REX_Trade_Brain という新しいノートブックを作成し、
 C:\Python\REX_AI\Trade_Brain\distilled\ 配下の全 .md ファイルを
 source_add してください」
```

**Task B 完了条件**:
```
□ 旧ノートブック名が REX_System_Brain に変更済み
□ 新 REX_Trade_Brain ノートブック作成済み
□ distilled/2025/*.md 全件投入済み
□ distilled/2026/*.md 全件投入済み（4 ファイル）
□ RAG テストクエリ: 「2026-04-17_wk03 の regime は？」→ gold_bid が返答
```

**注意**: Task B は Task A の docs/REX_BRAIN_SYSTEM_GUIDE.md 更新と連動する。
Task B 完了後、Task A-4 の NLM 名称更新を確定させる。

---

### Task C（🟢 通常優先）: Vault 側 wiki/trade_brain/ 骨組み構築

**担当**: Planner 起草 → Evaluator 承認 → ClaudeCode 実装

**対象**: `C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_brain\`

**作成ファイル（Phase 1 範囲のみ）**:
```
wiki/trade_brain/
├── _RUNBOOK.md                # Advisor 向け運用手順
├── doc_map.md                 # Trade_Brain 側の設計文書状況
├── pending_changes.md         # 決定済み未反映変更
└── pending_nlm_sync.md        # NLM 認証切れフォールバック

※ Strategy_Wiki/ 本体（Regimes / Signals / Events / ...）は REX_028 で実施
```

**Task C 完了条件**:
```
□ wiki/trade_brain/ ディレクトリ作成
□ 4 ファイル配置（frontmatter 完備）
□ filesystem MCP 許可パスに REX_Brain_Vault を追加
□ ClaudeCode から wiki/trade_brain/ 配下が read/write 可能
```

**Task C の詳細設計**: Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md §9 Phase 1 に準拠。

---

### Task D（🟢 通常優先）: adr_reservation.md 更新

**担当**: Evaluator

**対象**: `REX_Brain_Vault/wiki/trade_system/adr_reservation.md`

**追記項目**:
```
1. D-11 を予約エントリーとして記録
   - カテゴリ: D（パラメータ設計ミス）※ 正確には構造変更だが Trade_Brain 分離を D に含める
   - 担当: Advisor 起草 / Evaluator 承認
   - ステータス: 確定（2026-04-18）
   - トピック: Trade_Brain 分離によるリポ構造最適化

2. F-7 を予約エントリーとして記録
   - カテゴリ: F（設計方針ガイド）
   - 担当: Advisor 起草 / Evaluator 承認
   - ステータス: 確定（2026-04-18）
   - トピック: Vault 構造標準化
```

**Task D 完了条件**:
```
□ adr_reservation.md に D-11 / F-7 の確定エントリー追加
□ Task A-3 の ADR.md 記述と整合性一致
```

---

## 3. 実施順序

```
Task B（ミナト作業・並行可能）
    ↓
Task A（Planner → Evaluator → ClaudeCode）
    ↓
Task D（Evaluator）
    ↓
Task C（Planner → Evaluator → ClaudeCode）
```

**並行可能性**:
- Task B はミナト作業なので Task A と完全並行可能
- Task A-4（NLM 名称更新）は Task B 完了後に確定
- Task C は Task A 完了後に着手推奨（重複作業防止）
- Task D は Task A-3 の ADR.md 改訂と同時進行

---

## 4. 禁止事項

```
❌ Trade_System の src/*.py には一切触れない（凍結ファイル保護）
❌ バックテスト再実行はしない（数値変わらないため無駄）
❌ window_scanner.py / exit_simulator.py も触らない
❌ logs/window_scan_entries.csv / window_scan_exits.csv の再生成はしない
❌ Trade_Brain リポの raw/ / distilled/ 配下は編集しない（Ingest のみ）
❌ 過去の distilled（distilled-gm-2026-1 〜 3）は凍結扱い
❌ Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md は参照のみ・改訂しない
   （本指示書 REX_027_BOSS_DIRECTIVE.md が正式な指示書）
```

---

## 5. 検証手順

### 5-1. 実装ロジック不変の確認

```bash
# Trade_System 側で実施
cd C:\Python\REX_AI\Trade_System

# コードファイル差分チェック
git diff main -- src/

# 想定結果: 差分ゼロ（本指示書ではコードを変更しないため）
```

### 5-2. ドキュメント整合性の確認

```bash
# Trade_System 側で実施
cd C:\Python\REX_AI\Trade_System

# logs/gm または versions/distilled への参照が残っていないか
grep -rn "logs/gm\|versions/distilled" CLAUDE.md docs/

# 想定結果: 参照なし（あれば Task A で修正対象）
```

### 5-3. NLM ノートブック確認（ミナト）

```
Claude Desktop で:
「現在の NLM ノートブック一覧を表示してください」

想定出力:
  - REX_System_Brain（ID: 2d41d672-...）← 改名確認
  - REX_Trade_Brain（新設）← 新ノートブック確認
```

---

## 6. 結果報告フォーマット

### 6-1. 共通

```
=== #027 実施結果報告 ===

■ 実施者: {Planner / Evaluator / ClaudeCode / ボス}
■ 実施日時: YYYY-MM-DD HH:MM
■ 対象 Task: {A / B / C / D}

■ 変更ファイル一覧
（git diff --name-only の出力）

■ 変更内容サマリー
（箇条書き 3〜5 項目）

■ 完了条件チェック
□ （該当 Task の完了条件を列挙・チェック）

■ 次のアクション
（次に何を誰がやるか）
```

### 6-2. Task A 専用

```
■ 追加: ドキュメント整合性確認
□ grep "logs/gm\|versions/distilled" で該当ゼロ
□ ADR.md の D-11 / F-7 が adr_reservation.md と整合
□ バックテスト数値確認:
  - PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p
  - 変化なしを確認（src/ 無変更のため自明だが明記）
```

### 6-3. Task B 専用

```
■ 追加: NLM 動作確認
□ REX_System_Brain（旧 REX_Trade_Brain）に既存ソース残存
□ REX_Trade_Brain（新設）に distilled 全件投入完了
□ RAG テスト: 「2026-04-17_wk03 の regime は？」→ gold_bid 返答
```

---

## 7. Evaluator への特記事項

Advisor（Claude Opus 4.7）として、以下を Evaluator に明確に伝えたい:

### 7-1. 本指示書の特殊性

本指示書は通常の #NNN spec と異なり、**リポ構造変更**を伴う。
通常の spec 発行フロー（Planner 起草 → Evaluator 承認 → ClaudeCode 実装）の
**前段階としてボス判断が先行**している。

Evaluator の役割:
- 本指示書の妥当性監査
- Task A（ドキュメント改訂）を Planner に起草させる
- Task D（ADR 採番）を自ら実施
- ADR F-7 / D-11 の本文内容を最終確定

Planner の役割:
- Task A の実装指示書（REX_027A_doc_cleanup_spec.md 等）を起草
- Task C の実装指示書（REX_027C_vault_skeleton_spec.md 等）を起草

### 7-2. Advisor 起草の立ち位置

本指示書はボス指示の具体化として Advisor が起草した。
ただし本指示書自体が**実装の正式な指示書ではない**:

```
本指示書 (REX_027_BOSS_DIRECTIVE.md)
    ↓
    ├── Task A → Planner が REX_027A_spec.md を起草 → Evaluator 承認 → ClaudeCode 実装
    ├── Task B → ボス実施（NLM 操作）
    ├── Task C → Planner が REX_027C_spec.md を起草 → Evaluator 承認 → ClaudeCode 実装
    └── Task D → Evaluator 直接実施
```

Task A / C の具体的な実装指示書は Planner が別途起草する。
本指示書はその**上位方針書**として機能する。

### 7-3. 関連文書

```
REX_027_ADVISOR_PROPOSAL.md   ← Obsidian Vault 構造設計提言（Advisor 起草）
REX_027_BOSS_DIRECTIVE.md     ← 本指示書（ボス判断・Advisor 起草）
REX_027A_spec.md              ← Task A 実装指示書（Planner 起草予定）
REX_027C_spec.md              ← Task C 実装指示書（Planner 起草予定）
```

---

## 8. スケジュール目安

```
本日（2026-04-18）: 本指示書発行
  ↓
2026-04-18 〜 19: Task B（ミナト作業・NLM 整理）
  ↓
2026-04-19 〜 20: Task A 起草（Planner）→ 承認（Evaluator）→ 実装（ClaudeCode）
  ↓
2026-04-20: Task D（Evaluator による ADR 確定）
  ↓
2026-04-21 〜: Task C（Vault 骨組み構築）

※ 全 Task 完了を目標日: 2026-04-24 前後
※ 以降、REX_028 として Strategy_Wiki/ 本体構築に着手
```

---

## 9. 本指示書の検証チェックリスト（発行時）

Evaluator が本指示書を受領した際に確認すること:

```
□ Trade_System のロジック・数値に一切影響がない構成であることを確認
□ 凍結ファイル 4 本（backtest.py / entry_logic.py / exit_logic.py / swing_detector.py）
  への変更指示を含まないことを確認
□ Task 分解（A/B/C/D）の依存関係が論理的に整合していることを確認
□ ADR D-11 / F-7 の採番がカテゴリ定義と矛盾しないことを確認
  （D=パラメータ系だが構造変更を含むことの妥当性判断）
□ Trade_Brain リポ（Minato33440/Trade_Brain）の実在確認
□ 本指示書を docs/REX_027_BOSS_DIRECTIVE.md として保存することへの合意
```

---

## 10. ボスから Evaluator / Planner へのメッセージ

今回の REX_027 は Trade_System の効率化のために実施する REX_AI\ 全体の
リポ構造変更です。#026d で PF 4.54 / +150.6p の静的点が取れた今、
以降の構造的な肥大化を防ぐために Trade_Brain を分離しました。

Trade_System のコアロジックには一切触れず、周辺のドキュメントと
ナレッジシステム基盤のみを整えるタスクです。安全に、既存運用を
壊さないように進めてください。

Advisor（Opus 4.7）には全体構造の整合性確認と文書起草を依頼しました。
Evaluator は本指示書の監査と ADR 採番を、Planner は Task A / C の
実装指示書起草をお願いします。

---

*発行: ボス（Minato）/ 2026-04-18*
*起草: Advisor（Claude Opus 4.7・相談役）*
*宛先: Rex-Evaluator（Opus 4.6）/ Rex-Planner（Sonnet 4.6）共用*
*関連: docs/REX_027_ADVISOR_PROPOSAL.md（Vault 構造設計提言）*
