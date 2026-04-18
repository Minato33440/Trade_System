# REX 指示書 #027 — REX_AI\ 配下リポジトリ構造変更および Trade_System ドキュメント整合性回復
# 発行者: ボス（Minato）
# 起草: Advisor（Claude Opus 4.7・相談役）
# 宛先: Rex-Evaluator（Opus 4.6） / Rex-Planner（Sonnet 4.6）共用
# 発行日: 2026-04-18（v2 改訂版）
# 思考フラグ: think harder（アーキテクチャ全体に影響する構造変更 + RAG 汚染排除 + ロジック漏れ根本対策）

---

## 改訂履歴

| 版 | 日付 | SHA | 主な変更点 |
|---|---|---|---|
| v1 | 2026-04-18 午前 | `06b0d04` | 初版。Trade_Brain 分離と Trade_System ドキュメント整合性回復。Task A〜D を定義 |
| **v2** | **2026-04-18 夜** | **本版** | **ボス判断による大幅改訂:**<br>① §0-1 に **RAG 汚染排除**の本質理由を追記<br>② §0-3 に NLM **新規構築済み**（旧は MCP 切り離し）を追加<br>③ §1-2 NLM 現状を「改名前提」→「新規構築済み」に全面書き換え<br>④ §2 **Task B** を「改名タスク」→「実施済み記録化＋旧 NLM の MCP 切り離し」に全面書き換え<br>⑤ §2 **Task E を新規追加**（ロジック漏れ洗い出し＋MTF ロジック管理ツール設計）<br>⑥ §7-2 に v1→v2 の経緯と Advisor 判断の修正説明を追加 |

### なぜ v2 を起こしたか

v1 起草時、Advisor は「既存 NLM ノートブックの改名で RAG を引き継ぐ」という前提で Task B を設計した。
しかしこれは **RAG 汚染という本質的リスクを軽視した判断** だった。

ボスが v1 発行後の実運用検証を通じて「改名では過去の却下案・修正前の不完全実装の
混入が解消されず、ClaudeCode がクエリ応答で旧情報を引いて再発バグを誘発するリスクが
残る」と判断し、**NLM ノートブックをゼロから新規構築**する方針を決定した。

Advisor はこのボス判断を正しいと評価し、v1 の方針を撤回して v2 を発行する。
旧 NLM ノートブックは Claude-MCP 接続先から外す運用（物理削除ではない・1 次履歴は
Git で参照可能）。

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
   - NLM ノートブックの全面再構築（旧は MCP 切り離し・新規 2 件作成）
   - Obsidian Vault ディレクトリ 1 ルートの新設

3. **RAG 汚染排除とロジック漏れ根本対策を含む（v2 で追加）**
   - 過去の RAG に混入していた旧情報・却下案の影響排除
   - これまでの手動運用で頻発したロジック漏れの体系的洗い出し
   - MTF（マルチタイムフレーム）ロジックの時間足縦串管理ツール整備

4. **Evaluator / Planner 双方が関与する**
   - Evaluator: ADR 採番（D-11 / F-7）、Vault 関連承認、ロジック漏れ監査主導、指示書全体の最終監査
   - Planner: Trade_System ドキュメント改訂および MTF ロジックマトリクスの実装指示書起草

5. **本タスクの起点はボスの判断**
   - データ移行（Trade_System/logs/gm/ + versions/distilled/ → Trade_Brain/）は
     2026-04-18 時点でボス実施により完了済み
   - NLM ノートブック全面再構築も 2026-04-18 夜時点でボス実施済み
   - 以降の整合性回復・Wiki 構築・Task E が本指示書のスコープ

---

## 0. 背景と目的

### 0-1. なぜこの変更が必要か

#### 第一の理由: 静的点での構造分離

#026d 完了により Trade System のコアロジックが数値的に収束した。
これは「データ整合性が取れている最後の静的点」であり、以降は
フィルター追加・Phase D（出来高）で構造が動的に変化していく。

静的な今のうちにナレッジシステム基盤を固めないと:

- Trade_System リポに蓄積される raw/distilled データが肥大化
- 「実装リポに戦略データが混在」という論理矛盾が深まる
- 複雑化してからの分離コストは数倍になる

ボスの判断: **今が分離タイミング**

#### 第二の理由: RAG 汚染の排除（v2 で明記）

これまでの REX_Trade_Brain（旧 NLM）は、手動運用によるロジック漏れ・意思疎通ミスの
修正履歴・却下された中間案・バグ修正前の不完全実装が時系列で蓄積されていた。

**観測されていたリスク**:

```
例 1: #021 の窓左端スキャンバグ（全 13 件誤検出）の途中実装記述
      → クエリ「過去の window_scanner 実装は何件検出したか？」に
        「13 件」と誤回答する可能性

例 2: #016 の旧 neck_4h 設計（4H SH 直接採用・★★★ 成立不能）の経緯記述
      → クエリ「neck_4h の定義は？」に旧設計を引く可能性

例 3: PCT 方式（#014 以前廃止）の記述
      → 現行の固定ネック原則と競合する回答を生成
```

NLM の RAG は **ノートブック内の全ソースを横断ベクトル検索** するため、
**却下された中間案と確定結論を LLM は区別できない**。
ClaudeCode がこれらを引いて実装に入ると、確定済みロジック（#026d）を壊す
「再発バグ」を誘発する。

**ボスの判断**: 実装/結果の 1 次履歴は Git 上に保全した上で、
NLM RAG データは **今回の Obsidian-Wiki ナレッジシステム導入を起点に
ゼロから正式に蓄積** する。

#### 第三の理由: ロジック漏れの根本対策（v2 で明記）

MTF（4H〜5M）ロジックは時間足が増えるほど管理複雑性が指数関数的に上がる。
これまで手動管理の限界により、時間足をまたぐロジック漏れが繰り返し発生してきた。

スレ引き継ぎ時に **スクリプトだけでなく、各時間足の裁量構造別ロジックを
縦串で確認できるツール** が必要。

現状の `EX_DESIGN_CONFIRMED §5` パラメータ表は「用途別」（横串）であり、
時間足別の全責務・全パラメータを一覧する視点が欠落している。

この欠落を埋めるため **Task E** を新規追加する。

---

### 0-2. 本指示書が扱う範囲

```
✅ 扱う:
  - Trade_Brain リポ立ち上げ完了確認
  - Trade_System ドキュメントの整合性回復
  - NLM ノートブック再構築の記録化（旧の MCP 切り離し含む）
  - ADR.md への追記（F-7 / D-11）
  - adr_reservation.md の更新
  - Vault 側 wiki/trade_brain/ の構築指針
  - ロジック漏れ洗い出しと MTF ロジック管理ツール設計（v2 追加）

❌ 扱わない:
  - Trade_System のロジック変更（凍結ファイルは触らない）
  - バックテスト再実行（数値は変わらない）
  - Trade_Brain の Strategy_Wiki/ 本体構築（別タスク・REX_028 想定）
  - Trade_System の Vault wiki/trade_system/ 本体構築（REX_027 Phase 2-5・別タスク）
```

### 0-3. 完了済みの作業（2026-04-18 夜時点）

本指示書 v2 発行時点で以下は完了している:

```
✅ Trade_Brain リポジトリ新設（Minato33440/Trade_Brain）
✅ raw/ データ移行（daily/2026/ + weekly/2025-2026/ + boss's-weeken-Report/）
✅ distilled/ データ移行（2025/ + 2026/）
✅ Trade_Brain/CLAUDE.md / README.md / docs/ 初期構築（Advisor 起草）
✅ Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md（Vault 構造提言書）
✅ NLM ノートブック全面再構築（v2 追加）
   - 旧 REX_Trade_Brain（ID: 2d41d672-...）を Claude-MCP 接続先から切り離し
   - 新規 REX_System_Brain をクリーン状態で作成
   - 新規 REX_Trade_Brain をクリーン状態で作成
```

本指示書は **これ以降の作業** を対象とする。

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
  - D-11（Trade_Brain 分離＋NLM 再構築）の予約未実施

⚠️ ロジック漏れ対策（v2 追加）:
  - 過去のロジック漏れ事例の体系化（LOGIC_LEAK_AUDIT.md）未作成
  - MTF ロジックマトリクス（MTF_LOGIC_MATRIX.md）未作成
```

### 1-2. NLM 側の現状（v2 で全面書き換え）

```
【旧構成・廃止】
  REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）
  状態: Claude-MCP 接続先から切り離し（2026-04-18 ボス実施）
  廃止理由: 過去の却下案・修正前の不完全実装が混入し、
           RAG 汚染による「再発バグ」の誘発リスクが確認されたため
  1 次履歴の参照先: Trade_System リポの Git コミット履歴
                    （#001〜#026d の採番済み spec 文書と ADR.md）

【新構成・稼働中（2026-04-18 ボス実施済み）】
  REX_System_Brain（新規作成・クリーン状態）
    用途: Trade_System 設計文書用（#026d 以降の正式蓄積）
    投入基準:
      ✅ 含める: #026d 時点で確定済みの設計文書のみ
         （CLAUDE.md / ADR.md / EX_DESIGN_CONFIRMED.md /
           SYSTEM_OVERVIEW.md / REX_BRAIN_SYSTEM_GUIDE.md）
      ❌ 含めない: 廃止された過去設計、却下された中間案、
                  #018 以前のバックテスト結果、試行錯誤の途中データ

  REX_Trade_Brain（新規作成・クリーン状態）
    用途: Trade_Brain リポ用（distilled 投入先）
    投入基準:
      ✅ 含める: Trade_Brain/distilled/2025/ および 2026/（確定済み蒸留データ）
      ❌ 含めない: raw/daily/ / raw/weekly/（生データは Git で参照）
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

#### A-1. CLAUDE.md

```
現状確認:
  grep -n "logs/gm\|versions/distilled" CLAUDE.md

修正:
  - もし参照があれば全て削除
  - 「外部リソース参照先」セクションに Trade_Brain リポへの言及を追加
  - NLM ノートブック名を REX_System_Brain に更新
```

#### A-2. docs/SYSTEM_OVERVIEW.md

```
修正:
  - ディレクトリツリーから logs/gm/ / versions/distilled/ を削除
  - 末尾に「データ移行履歴」セクション追加:

    | 日付 | 内容 |
    |---|---|
    | 2026-04-18 | logs/gm/ を Trade_Brain/raw/ に移行 |
    | 2026-04-18 | versions/distilled/ を Trade_Brain/distilled/ に移行 |
    | 2026-04-18 | NLM 全面再構築（旧 REX_Trade_Brain を MCP 切り離し、新規 2 件作成） |
    | 2026-04-18 | 詳細は Trade_Brain リポの CLAUDE.md および本指示書 REX_027_BOSS_DIRECTIVE.md 参照 |

  - 「外部リソース参照先」セクションに Trade_Brain 追加
```

#### A-3. docs/ADR.md

```
追記項目:

■ D-11 を新設（D セクション末尾）
  D-11. Trade_Brain 分離によるリポ構造最適化 + NLM RAG 汚染排除
        （2026-04-18 確定）

  症状:
    (1) Trade_System/logs/gm/ と versions/distilled/ に戦略データが蓄積され、
        実装リポと戦略データが混在する論理矛盾が発生
    (2) 旧 NLM REX_Trade_Brain に過去の却下案・修正前の不完全実装が混在し、
        RAG クエリ応答で ClaudeCode が旧情報を引いて「再発バグ」を誘発する
        リスクが観測された

  対応:
    (1) Trade_Brain リポを新設し、以下を物理移行:
        - logs/gm/ → Trade_Brain/raw/（gm/ 階層除去してフラット化）
        - versions/distilled/ → Trade_Brain/distilled/
    (2) NLM ノートブック全面再構築:
        - 旧 REX_Trade_Brain（ID: 2d41d672-...）を Claude-MCP 接続先から切り離し
          （物理削除せず、1 次履歴は Git コミット履歴として保全）
        - 新規 REX_System_Brain を Trade_System 確定文書のみでクリーン構築
        - 新規 REX_Trade_Brain を Trade_Brain/distilled/ のみでクリーン構築

  教訓:
    (1) 実装ロジックが収束した「静的点」で関連データの分離判断を行う。
        構造が動的化してからの分離コストは数倍になる。
    (2) データの性質（静的/動的）でリポを分けることで運用ルール（CLAUDE.md）の
        独立性が保たれる。
    (3) RAG は「過去の全記録を残す場所」ではなく「現行の正しい知識を参照する
        場所」。1 次履歴（Git）と知識参照層（RAG）は目的が違うので分離運用する。
    (4) 静的点が取れたタイミングで RAG を再構築することで、古い履歴と現行
        知識の混在による誤参照を防ぐ。

■ F-7 を新設（F セクション末尾）
  F-7. Vault 構造標準化 および RAG 管理方針（2026-04-18 確定）

  根拠文書:
    - Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md（Vault 構造）
    - Trade_System/docs/REX_027_BOSS_DIRECTIVE.md v2（RAG 管理方針）

  方針 (Vault):
    - Vault ルート: REX_Brain_Vault/wiki/
    - Trade_System 用: wiki/trade_system/
    - Trade_Brain 用:  wiki/trade_brain/
    - 共通: wiki/shared/（将来のレジームフィルター連携等）

  方針 (RAG 管理):
    - NLM ノートブックへの投入は確定済み文書のみ
    - 廃止された過去設計・却下された中間案・試行錯誤の途中データは投入しない
    - 静的点（例: #026d）で RAG をリセットし、それ以降の蓄積のみを正統とする
    - 1 次履歴は Git コミット履歴で保全し、RAG には含めない

  実装順序: REX_027_ADVISOR_PROPOSAL.md §9 Phase 1〜5 に準拠。

■ 「#026 シリーズ最終結果」表の下に新セクション追加:

  ## 2026-04-18 リポ構造変更 + NLM 再構築

  | 項目 | 内容 |
  |---|---|
  | 変更種別 | リポジトリ分離（実装/知識）+ NLM 全面再構築 |
  | 影響範囲 | Trade_System ディレクトリ構造・NLM・Vault |
  | 実装ロジック影響 | なし（凍結ファイル・バックテスト数値すべて不変） |
  | 関連 ADR | D-11 / F-7 |
  | 根拠文書 | REX_027_ADVISOR_PROPOSAL.md / REX_027_BOSS_DIRECTIVE.md v2 |
```

#### A-4. docs/REX_BRAIN_SYSTEM_GUIDE.md

```
修正項目:

■ §1「何が使えるか」の REX_Trade_Brain セクションを全面書き換え

  【廃止】
  旧 REX_Trade_Brain（ID: 2d41d672-...）は 2026-04-18 に RAG 汚染排除のため
  Claude-MCP 接続先から切り離された。
  1 次履歴は Trade_System リポの Git コミット履歴で参照可能。
  詳細: docs/ADR.md D-11 / docs/REX_027_BOSS_DIRECTIVE.md v2 参照

  【稼働中】
  REX_System_Brain（2026-04-18 新規作成）
    ノートブック ID: {Task B 完了時に Evaluator が追記}
    用途: Trade_System 設計文書用（#026d 以降の正式蓄積）
    投入基準: 本指示書 §1-2 参照

  REX_Trade_Brain（2026-04-18 新規作成）
    ノートブック ID: {Task B 完了時に Evaluator が追記}
    用途: Trade_Brain リポ用（distilled 投入先）
    詳細: Minato33440/Trade_Brain の CLAUDE.md 参照

■ §2「REX_Trade_Brain に入っている設計ソース」を
  「REX_System_Brain に入っている設計ソース」に改題

■ §8「参照先マップ」にエントリー追加:
  Trade_Brain リポの状況      → Minato33440/Trade_Brain/README.md
  戦略アーカイブの検索         → REX_Trade_Brain（NLM）
  旧 NLM の参照（切り離し済）  → Git コミット履歴のみ
```

**Task A 完了条件**:
```
□ Trade_System/CLAUDE.md に logs/gm または versions/distilled 参照なし
□ Trade_System/docs/SYSTEM_OVERVIEW.md にデータ移行履歴セクション追加
□ Trade_System/docs/ADR.md に D-11 / F-7 追記（v2 本文準拠）
□ Trade_System/docs/REX_BRAIN_SYSTEM_GUIDE.md で NLM 全面更新
□ その他 docs/ 配下で logs/gm/ または versions/distilled/ への参照ゼロ
□ Trade_System のコード（src/*.py）に一切変更なし
□ バックテスト数値（PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p）不変確認
□ git commit -m "Docs: #027 Trade_Brain 分離・NLM 再構築に伴う整合性回復"
```

---

### Task B（✅ ボス実施済み・記録化タスク / v2 で全面書き換え）: NLM 再構築の記録化

**担当**: ボス実施済み。本指示書は実施内容の記録化のみ。
**新ノートブック ID の追記**: Evaluator が Task A-4 反映時に追記

#### B-1. ボス実施内容の記録

```
【2026-04-18 実施】
1. 旧 REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）を
   Claude-MCP 接続先から切り離し
   - 物理削除せず、archived 相当の扱い
   - 参照停止により RAG 汚染源を遮断
   - 1 次履歴は Git コミット履歴で保全

2. REX_System_Brain を新規作成（クリーン状態）
   - Trade_System 設計用
   - 投入基準: §1-2 参照

3. REX_Trade_Brain を新規作成（クリーン状態）
   - Trade_Brain/distilled/ 投入先
   - 投入基準: §1-2 参照
```

#### B-2. Evaluator が確認・記録すべき項目

```
□ Claude Desktop で現在の NLM ノートブック一覧を取得:
  「現在の NLM ノートブック一覧を表示してください」

□ 新ノートブック ID を取得:
  - REX_System_Brain の ID: ____________________
  - REX_Trade_Brain の ID: ____________________

□ 旧 REX_Trade_Brain が MCP 接続先から外れていることを確認
  （接続一覧に表示されない、またはアーカイブ扱い）

□ 新 REX_System_Brain に投入されたソース一覧を確認:
  確認方法: 「REX_System_Brain に登録されている全ソースを表示してください」
  期待: 確定済み設計文書のみ（§1-2 投入基準に準拠）
  NG:   廃止設計・却下案・試行錯誤ログが混入している場合

□ 新 REX_Trade_Brain に投入されたソース一覧を確認:
  期待: Trade_Brain/distilled/2025/*.md + 2026/*.md のみ
  NG:   raw/ 系ファイルが混入している場合

□ RAG テストクエリで正常動作確認:
  (1) REX_System_Brain: 「neck_4h の定義は？」
      → 期待: 統一 neck 原則（sh_before_sl.iloc[-1]）
      → NG:   旧設計（4H SH 直接採用）が返答されたら要調査

  (2) REX_Trade_Brain: 「2026-04-17_wk03 の regime は？」
      → 期待: Gold Bid
```

**Task B 完了条件**:
```
□ 上記 B-2 全項目のチェック完了
□ 新ノートブック ID が Task A-4 の REX_BRAIN_SYSTEM_GUIDE.md に反映
□ RAG テストで旧情報の混入が観測されないことを確認
```

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

**Task C の詳細設計**: `REX_027_ADVISOR_PROPOSAL.md §9 Phase 1` に準拠。

---

### Task D（🟢 通常優先）: adr_reservation.md 更新

**担当**: Evaluator

**対象**: `REX_Brain_Vault/wiki/trade_system/adr_reservation.md`

**追記項目**:
```
1. D-11 を予約エントリーとして記録（本文は v2 拡張版）
   - カテゴリ: D（構造変更＋RAG 管理）
   - 担当: Advisor 起草 / Evaluator 承認
   - ステータス: 確定（2026-04-18）
   - トピック: Trade_Brain 分離 + NLM RAG 全面再構築

2. F-7 を予約エントリーとして記録（本文は v2 拡張版）
   - カテゴリ: F（設計方針ガイド）
   - 担当: Advisor 起草 / Evaluator 承認
   - ステータス: 確定（2026-04-18）
   - トピック: Vault 構造標準化 および RAG 管理方針
```

**Task D 完了条件**:
```
□ adr_reservation.md に D-11 / F-7 の確定エントリー追加
□ Task A-3 の ADR.md 記述と整合性一致
```

---

### Task E（🟡 中優先・v2 で新規追加）: ロジック漏れ洗い出し + MTF ロジック管理ツール設計

**目的**: これまでの手動管理で頻発した「ロジック漏れ」の根本対策として、
(1) 過去事例の体系化と (2) MTF ロジックの時間足縦串管理ツールを整備する。

**背景**: 
- 手動運用によるロジック漏れ・意思疎通ミスが #001〜#026d の履歴で繰り返し発生
- スレ引き継ぎ時に全時間足のロジックを再把握するコストが高い
- 現状の `EX_DESIGN_CONFIRMED §5` は「用途横串」のパラメータ表のみで、
  時間足別の全責務・全パラメータを縦串で見る視点が欠落

**担当**: 
- E-1: Evaluator 主導（過去履歴への深い理解が必要）
- E-2: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
- E-3: 記述のみ（将来の移行計画を Task E 内で明示）

#### E-1: ロジック漏れ案件のヒストリカル洗い出し

**アウトプット**: `Trade_System/docs/LOGIC_LEAK_AUDIT.md`（新規作成）

**担当**: Evaluator

**想定構造**（Evaluator が最終確定）:

```markdown
# LOGIC_LEAK_AUDIT.md
# ロジック漏れ事例の体系的監査（#001〜#026d）

## 1. 監査範囲
- 対象期間: #001〜#026d
- 対象領域: window_scanner / entry_logic / exit_logic / swing_detector
- 除外: スタイル系の軽微修正、プロット装飾のみの変更

## 2. カテゴリ別分類（Evaluator が確定）

### カテゴリ I: 時間足取り違い / 混同
- 事例:
  - [#NNN] 症状 / 発見経緯 / 修正内容 / 教訓

### カテゴリ II: パラメータの時系列不整合
- 事例:
  - [#NNN] n=3 と n=2 の混在 等

### カテゴリ III: neck 定義の揺れ
- 事例:
  - [#016] 旧 neck_4h = 4H SH 直接採用 → ★★★ 成立不能
  - [#024a → #025] レンジ最高値 vs 初回反発ピーク（固定ネック原則）

### カテゴリ IV: エントリー条件の部分欠落

### カテゴリ V: 決済ロジックの段階省略

### カテゴリ VI: 再エントリーカウンターの不整合

### カテゴリ VII: 方向判定モードの混入（LONG-only なのに SHORT 条件残存）

### カテゴリ VIII: その他（Evaluator 判断で追加）

## 3. 根本原因分析
- 手動管理の限界
- 文書化の粒度不足
- スレ引き継ぎ時の情報損失
- MTF 縦串ビューの欠落
- RAG 汚染（← 本 REX_027 で対処済み）

## 4. 再発防止策
- 機械的チェック（grep / 静的解析）
- Lint ルール追加候補
- MTF_LOGIC_MATRIX.md（Task E-2）による縦串管理
- ADR への「発見経緯」セクション標準化
- 引き継ぎ書フォーマットの改善
```

**Task E-1 完了条件**:
```
□ LOGIC_LEAK_AUDIT.md が作成され、Evaluator により確定
□ カテゴリ I〜VII（または Evaluator 拡張）が埋まる
□ 各カテゴリに最低 1 件以上の具体事例（#採番付き）が記載
□ 再発防止策が Task E-2 の MTF_LOGIC_MATRIX 設計に反映される
```

#### E-2: MTF ロジックマスターテーブル

**アウトプット**: `Trade_System/docs/MTF_LOGIC_MATRIX.md`（新規作成）

**担当**: Planner 起草 → Evaluator 承認 → ClaudeCode 実装

**目的**: 4H / 1H / 15M / 5M 各時間足の裁量構造別ロジックを**縦串**で一覧化し、
スレ引き継ぎ時の再把握コストを最小化する。

**構造案**（Advisor 参考提示・Planner 最終設計）:

```markdown
# MTF_LOGIC_MATRIX.md
# 各時間足の責務・パラメータ・依存関係の縦串管理（#026d 時点）

---

## 4H 足の全責務

### 責務一覧
- 方向判定（LONG 継続判定）
- SH/SL 取得（4H 押し目候補抽出）
- 構造優位性判定（neck_4h vs neck_1h）

### パラメータ
| 用途 | 関数 | n | lookback | 確定指示書 |
|---|---|---|---|---|
| 方向判定（backtest） | get_direction_4h | 3 | 20 | #010 |
| 方向判定（structure_plotter） | get_direction_4h | 5 | 100 | #019 |
| SH/SL 取得（backtest） | detect_swing_highs/lows | 3 | 20 | #008 |
| SH/SL 取得（base_scanner） | detect_swing_highs/lows | 3 | 100 | #015 |

### neck 定義
統一 neck 原則: `neck_4h = sh_before_sl.iloc[-1]`
採用指示書: #025（固定ネック原則）→ #026d（4H 構造優位性フィルター）

### 依存関係
- 依存元: なし（最上位 TF）
- 依存先: 1H 足（4H SL から 1H 窓を確定）

### 凍結状態
- #026d 時点で確定（凍結）
- 関連凍結ファイル: swing_detector.py
- 関連拡張ファイル: window_scanner.py

### 関連 ADR / バグパターン
- A-1: 窓左端スキャンバグ
- A-4: 1H SL タイミングバグ
- E-6: neck CSV 保存方式
- F-6: 各 TF の SH/SL 目的定義
- D-11: リポ分離＋RAG 再構築（2026-04-18）

### 既知のロジック漏れ事例（E-1 から転記）
- [#016] 旧 neck_4h 設計（4H SH 直接採用）が★★★条件で数学的成立不能
  → #016 内で neck_4h = 1H SH への修正
- [その他、E-1 の監査結果を転記]

---

## 1H 足の全責務
（4H 同様の構造で縦串展開）

### 責務一覧
- 1H 窓の確定（4H SL 近傍 ±8 本）
- 1H SL 取得（押し目確認）
- neck_1h 取得（構造優位性判定の参照側）

### パラメータ
| 用途 | 関数 | n | lookback | 確定指示書 |
|---|---|---|---|---|
| 1H SL 窓内検索 | get_nearest_swing_low_1h | 2 | ±8 本窓 | #020 |
| 1H 窓サイズ | - | - | 前20+後10 | #023 |
| neck_1h 取得 | - | 3 | - | #026a-v2 |

### neck 定義
統一 neck 原則: `neck_1h = sh_before_sl.iloc[-1]`

### 依存関係
- 依存元: 4H 足（窓の基準点として 4H SL を使用）
- 依存先: 15M 足（窓内で 15M スキャン実行）

### 凍結状態
- #026d 時点で確定（凍結）

### 関連 ADR / バグパターン
（E-1 から転記）

### 既知のロジック漏れ事例
（E-1 から転記）

---

## 15M 足の全責務
（構造同じ）

### 責務一覧
- 統合レンジロジック判定（DB / IHS / ASCENDING）
- check_15m_range_low() による 3 パターン統合判定
- neck_15m 取得（1H SL 以降の初回反発ピーク）

### パラメータ
| 用途 | 関数 | n | lookback | 確定指示書 |
|---|---|---|---|---|
| 15M レンジロジック | check_15m_range_low | 3 | 50 | #014 |
| neck_15m 確定 | sh_vals.iloc[0] | - | 1H SL 以降 | #025 |

### 依存関係
- 依存元: 1H 足（1H 窓内で動作）
- 依存先: 5M 足（ネック越え確定）

### 既知のロジック漏れ事例
- [#021→#025] neck の取り方変遷（窓左端 → 1H SL 以降 → 固定ネック）

---

## 5M 足の全責務
（構造同じ）

### 責務一覧
- 5M DB ネックライン実体上抜け確認
- エントリー確定足の判定
- 執行足の決定（確定足の次足始値）

### パラメータ
| 用途 | 関数 | n | lookback | 確定指示書 |
|---|---|---|---|---|
| 5M DB 確定 | check_5m_double_bottom | 2 | 20 | #008 |
| WICKTOL_PIPS | - | - | 5.0 | #013 |
| ENTRY_OFFSET_PIPS | - | - | 7.0 | #026c |

---

## 依存関係マップ（全時間足）

```
4H 足（最上位）
  │
  ├─ 方向判定（LONG 継続）
  └─ SH/SL 取得
      │
      ↓ 4H SL から 1H 窓を取る
      │
1H 足
  │
  ├─ 1H 窓確定（±8 本）
  └─ 1H SL / neck_1h 取得
      │
      ↓ 1H 窓内で 15M スキャン
      │
15M 足
  │
  ├─ 統合レンジロジック判定（DB / IHS / ASCENDING）
  └─ neck_15m 確定（固定ネック原則）
      │
      ↓ 15M neck を 5M 実体が上抜け
      │
5M 足（最下位・エントリー実行）
  │
  └─ エントリー確定足 → 執行足
```

---

## 更新ルール

- 本マトリクスは #026d 確定版
- 以降の指示書（#028〜）で変更があった場合、該当時間足セクションを更新
- パラメータ変更時は「確定指示書」列を必ず更新
- 既知ロジック漏れ事例に新規発見があれば E-1（LOGIC_LEAK_AUDIT.md）にも反映
```

**Task E-2 完了条件**:
```
□ MTF_LOGIC_MATRIX.md が作成される
□ 4 時間足（4H / 1H / 15M / 5M）すべてのセクションが埋まる
□ 各時間足の「責務 / パラメータ / neck 定義 / 依存関係 / 凍結状態 /
  関連 ADR / 既知のロジック漏れ事例」の 7 項目がすべて記載される
□ 依存関係マップが視覚的に表現される
□ Task E-1 の監査結果と整合する
□ #026d 時点のバックテスト数値と矛盾しない（PF 4.54 / 勝率 60% 等）
```

#### E-3: 将来の Dataview 化移行計画（記述のみ）

初版の MTF_LOGIC_MATRIX.md は静的 Markdown として運用する。

Obsidian Vault 構築（REX_027_ADVISOR_PROPOSAL.md §9 Phase 2-4）完了後、
時間足別ページに YAML frontmatter を付与して Dataview で動的集計可能な
形式に移行する。

**移行後の構造案**:
```
wiki/trade_system/Concepts/TF/
├── 4h_logic.md        # frontmatter: {type: tf_logic, tf: "4h", ...}
├── 1h_logic.md        # frontmatter: {type: tf_logic, tf: "1h", ...}
├── 15m_logic.md       # frontmatter: {type: tf_logic, tf: "15m", ...}
└── 5m_logic.md        # frontmatter: {type: tf_logic, tf: "5m", ...}
```

**Dataview クエリ例**:
```dataview
TABLE tf, frozen_version, related_adrs, leak_cases
FROM "wiki/trade_system/Concepts/TF"
WHERE type = "tf_logic"
SORT tf ASC
```

**移行タイミング**: REX_027 Phase 4 完了後（REX_027C の発展として位置づける）

**Task E 全体完了条件**:
```
□ E-1: LOGIC_LEAK_AUDIT.md 確定
□ E-2: MTF_LOGIC_MATRIX.md 確定
□ E-3: Dataview 化移行計画が E-2 内に明記
□ 上記 3 件が docs/ 配下で push 完了
```

---

## 3. 実施順序

```
[完了済み]
Task B（ボス実施済み・記録化のみ）
  ↓
[これから]
Task A（Planner → Evaluator → ClaudeCode）
  │  並行可能
  ↓
Task D（Evaluator・Task A-3 と同時進行）
  ↓
Task E-1（Evaluator 主導・LOGIC_LEAK_AUDIT.md）
  ↓
Task E-2（Planner → Evaluator → ClaudeCode・MTF_LOGIC_MATRIX.md）
  ↓
Task C（Planner → Evaluator → ClaudeCode）
```

**並行可能性**:
- Task A と Task D は並行可（ADR.md の同期を取る）
- Task E-1 と Task A は並行可（異なるファイル群）
- Task E-2 は Task E-1 完了後に着手（監査結果を反映するため）
- Task C は Task A 完了後に着手推奨（REX_BRAIN_SYSTEM_GUIDE 参照先の整合確保）

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
❌ 旧 REX_Trade_Brain（ID: 2d41d672-...）を MCP 接続先に戻さない
❌ 新 REX_System_Brain / REX_Trade_Brain に §1-2 投入基準外のソースを追加しない
❌ LOGIC_LEAK_AUDIT.md に現在係争中の解釈を含めない（確定事例のみ）
❌ MTF_LOGIC_MATRIX.md の数値を #026d 以外の時点で記載しない
   （将来変更時は同文書内で履歴更新）
```

---

## 5. 検証手順

### 5-1. 実装ロジック不変の確認

```bash
cd C:\Python\REX_AI\Trade_System
git diff main -- src/

# 想定結果: 差分ゼロ
```

### 5-2. ドキュメント整合性の確認

```bash
cd C:\Python\REX_AI\Trade_System

# logs/gm または versions/distilled への参照が残っていないか
grep -rn "logs/gm\|versions/distilled" CLAUDE.md docs/

# 想定結果: 参照なし
```

### 5-3. NLM ノートブック確認（Task B 検証）

```
Claude Desktop で:
(1) 「現在の NLM ノートブック一覧を表示してください」

想定出力:
  - REX_System_Brain（新規 ID）
  - REX_Trade_Brain（新規 ID）
  - 旧 REX_Trade_Brain（ID: 2d41d672-...）は表示されない
    または archived 扱いで接続先に含まれない

(2) RAG 非汚染確認:
  「REX_System_Brain に neck_4h の定義を質問してください」

想定応答:
  統一 neck 原則（sh_before_sl.iloc[-1]）を返す
  旧設計（4H SH 直接採用）を返したら汚染未排除を疑う

(3) 旧情報非参照確認:
  「REX_System_Brain に #021 の window 左端スキャンの検出件数を質問してください」

想定応答:
  情報がないか、修正後（#022 以降）の内容を返す
  「13 件」と返したら旧情報が混入している
```

### 5-4. Task E 検証

```bash
# LOGIC_LEAK_AUDIT.md の存在確認
ls Trade_System/docs/LOGIC_LEAK_AUDIT.md

# MTF_LOGIC_MATRIX.md の存在確認と全時間足セクション確認
grep -c "^## [145]\{0,1\}[0-9]*[HM] 足の全責務" Trade_System/docs/MTF_LOGIC_MATRIX.md
# 想定: 4（4H / 1H / 15M / 5M）
```

---

## 6. 結果報告フォーマット

### 6-1. 共通

```
=== #027 v2 実施結果報告 ===

■ 実施者: {Planner / Evaluator / ClaudeCode / ボス}
■ 実施日時: YYYY-MM-DD HH:MM
■ 対象 Task: {A / B / C / D / E-1 / E-2 / E-3}
■ 参照版: REX_027_BOSS_DIRECTIVE.md v2（本書）

■ 変更ファイル一覧
（git diff --name-only の出力）

■ 変更内容サマリー（箇条書き 3〜5 項目）

■ 完了条件チェック
□ （該当 Task の完了条件を列挙・チェック）

■ 次のアクション
```

### 6-2. Task 別 追加項目

**Task A**: ドキュメント整合性確認
- `grep "logs/gm\|versions/distilled"` で該当ゼロ
- ADR.md の D-11 / F-7 が v2 本文と一致
- バックテスト数値不変確認（src/ 無変更のため自明だが明記）

**Task B**: NLM 動作確認
- 新ノートブック ID が REX_BRAIN_SYSTEM_GUIDE.md に反映
- RAG テスト（§5-3）全 3 問で想定応答
- 旧 NLM が MCP 接続先から外れていることを確認

**Task E-1**: LOGIC_LEAK_AUDIT.md 内容確認
- カテゴリ I〜VII + Evaluator 拡張が埋まる
- 各カテゴリに最低 1 件の具体事例

**Task E-2**: MTF_LOGIC_MATRIX.md 内容確認
- 4 時間足すべてのセクションが埋まる
- 7 項目（責務/パラメータ/neck/依存/凍結/ADR/漏れ事例）すべて記載
- 依存関係マップ記載

---

## 7. Evaluator / Planner への特記事項

### 7-1. 本指示書 v2 の特殊性

本指示書は v1（SHA: 06b0d04）の全面改訂版である。
通常の #NNN spec と異なり、**ボス判断による方針転換**を受けた改訂である。

Evaluator の役割:
- 本指示書 v2 の妥当性監査
- v1 から v2 への方針転換の論理的整合性確認
- Task A / D / E-1 の主導または承認
- ADR F-7 / D-11 の本文内容を最終確定

Planner の役割:
- Task A の実装指示書（REX_027A_spec.md 等）を起草
- Task C の実装指示書（REX_027C_spec.md 等）を起草
- Task E-2 の実装指示書（REX_027E_spec.md 等）を起草

### 7-2. v1 → v2 の変更経緯と Advisor 判断の修正

**率直な記録**:

v1 起草時、Advisor（同じ Opus 4.7）は以下の甘さを持っていた:

1. Task B を「既存ノートブック改名」として設計した
   → しかしこれは **RAG 汚染** を解消しない。
     改名しても中身（ソースデータ）は同じで、過去の却下案・修正前実装は残る。
     ClaudeCode が RAG クエリで旧情報を引いて「再発バグ」を起こすリスクを軽視した。

2. 「Evaluator 判断で難しければ妥協案（既存維持＋別名新設）でもOK」と書いた
   → 運用の柔軟性を優先し、RAG 汚染という本質的リスクを表面化しなかった。

3. ロジック漏れ根本対策を Task として立てなかった
   → 構造変更（リポ分離・NLM 再構築・Vault 構築）に注力し、
     そもそも「なぜロジック漏れが起きるか」の MTF 縦串管理不足に
     踏み込まなかった。

**ボスが実運用を通じて v1 の甘さを指摘し、以下の判断を下した**:

- 旧 NLM は改名ではなく **MCP 接続先から切り離し** する
- NLM は **ゼロから新規構築**（REX_System_Brain / REX_Trade_Brain）
- ロジック漏れの **ヒストリカル洗い出し** と **MTF ロジック管理ツール設計** を
  Task E として追加

Advisor はボスの判断を完全に正しいと評価し、v2 として起草した。
v1 を起草した Advisor と v2 を起草した Advisor は同一モデル（Opus 4.7）だが、
v2 は v1 の自己批判を含む。

**Evaluator へのメッセージ**: この改訂経緯自体が、ロジック漏れ（本ケースは
「運用リスク認識漏れ」）の一事例である。Task E-1 の LOGIC_LEAK_AUDIT.md に
「カテゴリ: 運用設計の認識漏れ」として本件を記録することを推奨する。

### 7-3. Task E の重要性と狙い

Task E は本指示書 v2 の**最も重要な拡張**である。

理由:
- Task A〜D は「今起きている構造変更」への対処（対症療法）
- Task E は「なぜロジック漏れが起きるか」への対処（根本療法）

MTF_LOGIC_MATRIX.md は「スレ引き継ぎ時の単一エントリーポイント」として機能させる。
現状、新スレッドで Trade_System の全容を把握するには EX_DESIGN_CONFIRMED §5
（用途横串）、ADR.md（時系列）、SYSTEM_OVERVIEW.md（ファイル依存）、各
REX_NNN_spec（指示書履歴）を全て追う必要がある。

MTF_LOGIC_MATRIX があれば、まずこれ 1 枚を読めば各時間足の責務が把握できる。
他文書は深掘り用の参照源として従属的な位置になる。

これは Advisor の役割である「ナレッジ環境の整備」と直結する。

### 7-4. 関連文書

```
REX_027_ADVISOR_PROPOSAL.md   ← Obsidian Vault 構造設計提言（Advisor 起草）
REX_027_BOSS_DIRECTIVE.md v2  ← 本指示書（ボス判断・Advisor 起草）
ADVISOR_HANDOFF.md            ← Advisor セッション引き継ぎ書
REX_027A_spec.md              ← Task A 実装指示書（Planner 起草予定）
REX_027C_spec.md              ← Task C 実装指示書（Planner 起草予定）
REX_027E_spec.md              ← Task E-2 実装指示書（Planner 起草予定・推奨）
LOGIC_LEAK_AUDIT.md           ← Task E-1 成果物（Evaluator 起草予定）
MTF_LOGIC_MATRIX.md           ← Task E-2 成果物（Planner/ClaudeCode 生成予定）
```

---

## 8. スケジュール目安

```
2026-04-18 夜: 本指示書 v2 発行（本日完了）
  ↓
2026-04-19: Task A 起草（Planner）+ Task E-1 着手（Evaluator）並行
  ↓
2026-04-20: Task A 承認・実装（Evaluator → ClaudeCode）
            Task D（Evaluator による ADR 確定）
            Task E-1 完了
  ↓
2026-04-21〜22: Task E-2 起草・実装（MTF_LOGIC_MATRIX.md）
  ↓
2026-04-23〜: Task C（Vault 骨組み構築）
  ↓
全 Task 完了目標: 2026-04-25 前後

※ 以降、REX_028 として Strategy_Wiki/ 本体構築に着手
```

---

## 9. 本指示書 v2 の発行時検証チェックリスト

Evaluator が本指示書を受領した際に確認すること:

```
□ Trade_System のロジック・数値に一切影響がない構成であることを確認
□ 凍結ファイル 4 本（backtest.py / entry_logic.py / exit_logic.py / swing_detector.py）
  への変更指示を含まないことを確認
□ v1（SHA: 06b0d04）からの変更点が改訂履歴セクションで明示されていることを確認
□ Task 分解（A/B/C/D/E）の依存関係が論理的に整合していることを確認
□ ADR D-11 / F-7 の採番がカテゴリ定義と矛盾しないことを確認
  （D=パラメータ系だが構造変更＋RAG 管理を含むことの妥当性判断）
□ Trade_Brain リポ（Minato33440/Trade_Brain）の実在確認
□ 新 NLM ノートブック（REX_System_Brain / REX_Trade_Brain）の実在確認
□ 旧 NLM（ID: 2d41d672-...）が MCP 接続先から外れていることを確認
□ Task E-1 / E-2 の完了条件が実行可能であることを確認
□ 本指示書を docs/REX_027_BOSS_DIRECTIVE.md として保存することへの合意
```

---

## 10. ボスから Evaluator / Planner へのメッセージ

今回の REX_027 は Trade_System の効率化のために実施する REX_AI\ 全体の
構造変更です。#026d で PF 4.54 / +150.6p の静的点が取れた今、以降の
構造的な肥大化と RAG 汚染を防ぐために以下を実施しました:

1. **Trade_Brain 分離** — 実装リポと戦略データの混在を解消
2. **NLM 全面再構築** — 過去の却下案・不完全実装が混入した旧 RAG を
   Claude-MCP から切り離し、ゼロから正式に蓄積し直す
3. **Task E 追加** — これまで手動管理の限界で発生してきたロジック漏れを
   体系化し、MTF ロジックを時間足縦串で管理するツールを整備

Trade_System のコアロジックには一切触れていません。周辺のドキュメント、
ナレッジシステム基盤、そしてロジック漏れ根本対策の整備のみです。

v1 指示書（SHA: 06b0d04）を発行した後、実運用での検証を通じて私（ボス）の
判断で v2 に大幅改訂しました。v1 の Task B は「既存 NLM の改名」でしたが、
改名では RAG 汚染が解消されないため全面再構築としました。
また v1 にはなかったロジック漏れ根本対策（Task E）を追加しました。

Advisor（Opus 4.7）には改訂版の起草を依頼しました。
Evaluator は本指示書の監査、ADR 採番、Task E-1 の主導を、
Planner は Task A / C / E-2 の実装指示書起草をお願いします。

安全に、既存運用を壊さないように進めてください。

---

*発行: ボス（Minato）/ 2026-04-18 v2*
*起草: Advisor（Claude Opus 4.7・相談役）*
*宛先: Rex-Evaluator（Opus 4.6）/ Rex-Planner（Sonnet 4.6）共用*
*前版: v1（SHA: 06b0d04・2026-04-18 午前）*
*関連: docs/REX_027_ADVISOR_PROPOSAL.md / docs/ADVISOR_HANDOFF.md*
