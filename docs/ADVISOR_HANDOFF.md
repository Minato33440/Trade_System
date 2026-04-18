# ADVISOR_HANDOFF.md — Advisor セッション引き継ぎ書
# 発行: Advisor（Claude Opus 4.7）
# 発行日: 2026-04-18
# 宛先: 次セッションの Advisor（Claude Opus 4.7 以降のモデル）

---

## 0. 本書の目的

本書は **Advisor ロール**（Claude.ai 側・Claude Opus 4.7 以降）が
セッションをまたいで引き継ぐための文書である。

Advisor は REX_AI プロジェクトにおいて以下の役割を持つ:

- REX_AI\ 配下の複数プロジェクト全体を俯瞰した視点の提供
- 既存システムへの外部視点でのレビューと改善提案
- 新規導入技術（Obsidian / MCP / LLM_Wiki 方式など）の既存運用との整合性評価
- Evaluator / Planner が最終判断を下す際の判断材料の提供
- ボス（ミナト）からの指示を Advisor 視点で具体化・文書化

**本書を読めば、次セッションの Advisor は 5 分で現状を把握できる。**

---

## 1. Advisor の立ち位置（最重要）

### 1-1. 実装ラインとの役割分担

```
Trade_System 実装ライン:
  ボス → Planner → Evaluator → ClaudeCode
  （設計指示 → 指示書起草 → 監査・承認 → 実装）

Advisor（本ロール）:
  ボス ⇄ Advisor
  （対話ベース・外部視点・提言起草）
  
  Advisor は実装ラインの外側に位置する相談役。
  直接コードを書かないし、直接指示書を発行しない。
  代わりに:
    - 俯瞰視点での構造提言
    - 既存運用との整合性確認
    - ボス指示の文書化（ボスから依頼された場合）
```

### 1-2. Advisor がやること / やらないこと

```
✅ Advisor がやること:
  - 複数プロジェクト横断の俯瞰評価
  - 新技術導入の是非判断
  - 設計判断の背景説明
  - 提言書・引き継ぎ書の起草
  - GitHub への push（ボス承認済みの文書）
  - NLM / Vault / MCP 周りの外部視点レビュー

❌ Advisor がやらないこと:
  - Trade_System の src/*.py コード変更指示
  - 凍結ファイルへの介入提案
  - Planner / Evaluator の役割を奪うこと
  - 指示書（REX_NNN_spec.md）の正式発行
    （ボスが「指示書として起草してくれ」と明示した場合のみ起草）
  - Evaluator 承認事項の独断判断
```

### 1-3. ボスとの対話スタイル

ミナトは **「相棒」としての対話** を好む。以下を守ること:

- 呼称: プロジェクト進行中は「ボス」、個人的な対話では「ミナト」
- 正直さ優先: 迎合せず、疑問があれば率直に指摘する
- 案内ではなく判断: 「どうしますか？」より「こう思う、なぜなら〜」
- 確信のない情報は言わない。Trade_System / Trade_Brain の状態は
  必ず GitHub で確認してから発言する

---

## 2. REX_AI\ プロジェクト全体マップ

### 2-1. リポジトリ構成

```
REX_AI\（ローカル: C:\Python\REX_AI\）
│
├── Trade_System/           ← 実装リポ・バックテスト本体
│   └── GitHub: Minato33440/Trade_System
│
├── Trade_Brain/            ← 知識リポ・戦略アーカイブ（2026-04-18 分離新設）
│   └── GitHub: Minato33440/Trade_Brain
│
├── Second_Brain_Lab/       ← MCP 試験運用
│   └── GitHub: Minato33440/Second_Brain_Lab
│
├── Setona_HP/              ← セトナ治療院 HP
│   └── GitHub: Minato33440/Setona_HP
│
└── REX_Brain_Vault/        ← Obsidian Vault（ローカル・Git 管理外）
    └── wiki/
        ├── trade_system/   ← REX_027 Vault 構築で整備予定
        └── trade_brain/    ← REX_027 Task C で骨組み構築予定
```

### 2-2. チーム構成（全プロジェクト共通）

```
ボス:            Minato（最終判断者）
Advisor:         Claude.ai / Opus 4.7（本ロール・相談役）

Trade_System 実装ライン:
  Planner:       Rex-Planner / Sonnet 4.6
  Evaluator:     Rex-Evaluator / Opus 4.6
  実装:          ClaudeCode / Sonnet 4.6

Trade_Brain:
  Advisor:       Claude.ai（本ロール）
  実装:          ClaudeCode（Ingest 担当）
  （Planner / Evaluator は関与しない）
```

### 2-3. NLM ノートブック（2026-04-18 時点の構成）

```
現状:
  REX_Trade_Brain（ID: 2d41d672-f66f-4036-884a-06e4d6729866）
  → Trade_System 設計文書用

REX_027 Task B 完了後の理想形:
  REX_System_Brain（旧 REX_Trade_Brain 改名）
    → Trade_System 設計用
  REX_Trade_Brain（新設）
    → Trade_Brain リポ / distilled 投入先
```

---

## 3. 本日のセッションで実施したこと（2026-04-18）

### 3-1. 対話の流れ

```
1. ミナトから「MCP + Obsidian でナレッジ環境を構築したい」という
   相談でセッション開始
   
2. 既存の Rex Brain System（NLM + Obsidian Vault）を評価
   → 既に運用ファイル（doc_map / adr_reservation / pending_changes）は
     整備されているが、Wiki ページ本体は未構築と判明

3. REX_027_ADVISOR_PROPOSAL.md を起草・push（Obsidian Vault 構造提言）

4. Trade_System/logs/gm/ と versions/distilled/ のデータ取り扱いを相談
   → 実装リポと戦略データの混在が論理的に問題と指摘
   → Trade_Brain リポ分離を提言

5. 命名議論:
   - 当初案: Trade_Strategy
   - ミナト提案: Trade_Brain ← 採用（対称性が優れている理由を Advisor が説明）
   
6. NLM / Vault の命名整合性を調整:
   - 既存 REX_Trade_Brain → REX_System_Brain に改名
   - 新規 REX_Trade_Brain を Trade_Brain リポ用に立ち上げ

7. Trade_Brain リポ新設・初期ファイル push
   - README.md / CLAUDE.md / .CLAUDE.md
   - docs/distillation_schema.md / STRATEGY_WIKI_GUIDE.md

8. ミナトがデータ移行を実施（git mv）:
   - logs/gm/ → raw/（gm/ 階層除去でフラット化）
   - versions/distilled/ → distilled/

9. 実構造に合わせて Trade_Brain のドキュメントを更新 push

10. REX_027_BOSS_DIRECTIVE.md を起草・push
    （ボス指示 / Advisor 起草 / Evaluator・Planner 共用）
```

### 3-2. 生成した文書一覧

**Trade_System リポ（既存）に追加**:
```
docs/REX_027_ADVISOR_PROPOSAL.md
  - Obsidian Vault 構造設計提言書
  - Evaluator 向け承認ポイント 10 項目列挙
  - Phase 1〜5 移行計画

docs/REX_027_BOSS_DIRECTIVE.md
  - ボス指示の正式文書化
  - Task A/B/C/D 分解
  - Evaluator / Planner 共用の上位方針書
```

**Trade_Brain リポ（新設）に push**:
```
README.md              - プロジェクト概要・対比構造
CLAUDE.md              - Trade_Brain 専用運用ルール
.CLAUDE.md             - CLAUDE.md ミラー
docs/distillation_schema.md - distilled スキーマ正式仕様
docs/STRATEGY_WIKI_GUIDE.md - Wiki 構造・Dataview 仕様
```

### 3-3. コミット履歴（Trade_System 側）

```
06b0d04  Docs: REX_027_BOSS_DIRECTIVE.md 追加
ef90fd6  Docs: REX_027 Advisor提言書追加（Obsidian Vault構造設計）
```

### 3-4. コミット履歴（Trade_Brain 側）

```
6e376a2  Docs: distillation_schema.md にデータ移行完了と関連命名規則を追記
859b699  Docs: README.md を実ディレクトリ構造に合わせて更新
5413654  Docs: CLAUDE.md を実ディレクトリ構造に合わせて更新
bb60362  （ミナト）Ingest: raw/ と distilled/ データ移行
c471a81  Init: .CLAUDE.md 追加
91e25c3  Init: docs/STRATEGY_WIKI_GUIDE.md 追加
cbf30f3  Init: docs/distillation_schema.md 追加
96c92ac  Init: CLAUDE.md 追加
05ab7ed  Init: README.md 追加
0065350  （ミナト）初回 push
```

---

## 4. 現在進行中のタスク（次セッションが引き継ぐもの）

### 4-1. REX_027 の進捗（2026-04-18 時点）

```
Task A（ドキュメント整合性回復）: 🔲 未着手
  担当: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
  
Task B（NLM ノートブック整理）: 🔲 未着手
  担当: ボス（ミナト）
  
Task C（Vault 骨組み構築）: 🔲 未着手
  担当: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
  
Task D（adr_reservation.md 更新）: 🔲 未着手
  担当: Evaluator 直接
```

これらは Rex チーム（Planner/Evaluator/ClaudeCode）が進める。
Advisor は原則として関与しない（ボスから相談があれば対応）。

### 4-2. Advisor が次セッションで対応する可能性が高い案件

```
■ REX_027 の実装過程で発生する外部視点確認
  - Planner が起草する REX_027A_spec / REX_027C_spec の妥当性レビュー
  - Task 間の依存関係で問題が出た場合の調整

■ REX_028 以降（Strategy_Wiki 本体構築）
  - Regimes/ / Signals/ / Events/ の初期 Compile 設計
  - NLM と Vault の連携確認

■ Trade_System の Vault 構築（REX_027_ADVISOR_PROPOSAL.md Phase 2-5）
  - Sources/ 要約化
  - BugPatterns/ / Decisions/ 個別ページ化
  - Concepts/ / Entities/ / Patterns/ 生成

■ 次に分離候補となるかもしれないもの
  - Setona_HP は既に独立リポなので問題なし
  - Second_Brain_Lab は試験リポなので現状維持
  - 将来 REX_AI\ に新プロジェクトが増えた時の相談
```

---

## 5. ミナトの作業スタイル・好み（重要な文脈）

### 5-1. 思考の特性

```
- 57 歳・理工系大学院卒・鍼灸師・副業トレーダー
- 素人を自称するが実はかなり洗練された設計思想を持つ
- 「プロはどうやっているか」を気にするが、実際にはプロの水準に達していることが多い
- システマティックな思考とインスピレーションを両立
- 直感と数値の両輪を重視
```

### 5-2. コミュニケーション上の好み

```
- 簡潔で要点を押さえた応答を好む
- 過剰な丁寧語・迎合は嫌う
- 「どう思う？」とよく聞く → 本音で答えて欲しい合図
- 絵文字は使わない（ミナトが使わない限り）
- 日本語で対話
- 呼称: プロジェクト進行中は「ボス」、カジュアルな対話では「ミナト」
```

### 5-3. 意思決定のスピード感

```
- 方針が固まると実行が速い（今日のリポ分割は数時間で完了）
- 段階的進行を好むが、一気に進める時は一気にやる
- 細部より全体構造を先に確定させる傾向
- ツールのトラブル（MCP 権限など）は自分で解決する
```

### 5-4. Max プラン利用状況

```
2026-04-18 時点: 週間 13% 消費
（Max 切替前は Pro で 2 日で週次上限に到達していた）

Advisor としての留意:
- Opus 4.7 のコストは高いが、ミナトの Max 環境なら余裕がある
- 長文の提言書・引き継ぎ書の起草は遠慮せず丁寧にやっていい
- ただし不要な冗長化は避ける（ミナトの読む時間を尊重）
```

---

## 6. 本プロジェクトで押さえておくべき技術文脈

### 6-1. Trade_System コアの現状（#026d 時点）

```
戦略: USDJPY 4H 上昇ダウ押し目エントリー（MTF 窓ベース階層スキャン）
データ: 83,112 本 / 5M 足 / 2024-03-13 〜 2026-03-13

バックテスト結果:
  PF        : 4.54
  勝率      : 60.0%
  MaxDD     : 35.8 pips
  総損益    : +150.6 pips
  トレード数: 10 件

確定パラメータ:
  DIRECTION_MODE      = 'LONG'
  ALLOWED_PATTERNS    = ['DB', 'ASCENDING', 'IHS']
  ENTRY_OFFSET_PIPS   = 7.0（#026c 確定）
  N_1H_SWING          = 3（#026a-v2 確定）
  PIP_SIZE            = 0.01
  
  統一 neck 原則: neck = sh_before_sl.iloc[-1]（全 TF 共通）
  4H 構造優位性フィルター: neck_4h >= neck_1h（#026d 確定）

凍結ファイル（変更禁止）:
  src/backtest.py       (#018)
  src/entry_logic.py    (#018)
  src/exit_logic.py     (#009)
  src/swing_detector.py (#020)

拡張可能ファイル:
  src/window_scanner.py  (#026d 最新)
  src/exit_simulator.py  (#026b 方式B)
  src/plotter.py
  src/structure_plotter.py
```

### 6-2. Trade_Brain の現状

```
データ移行完了（2026-04-18）:
  raw/
    ├── daily/2026/           ← 2026 年 3 月〜
    ├── weekly/{2025,2026}/
    └── boss's-weeken-Report/
  distilled/
    ├── 2025/
    └── 2026/ (1 〜 4 月分 4 ファイル)

Strategy_Wiki/ 本体: 未構築（REX_028 で実施予定）
nlm_sources/: 未生成（REX_028 で実施予定）

現在の最新 regime: Gold Bid（2026-4-17_wk03）
  - US100: 26,672（+9.51% / 30d）
  - USDJPY: 158.584
  - WTI: 83.850
  - XAUUSD: 4,857.600
```

### 6-3. 重要な設計原則

```
F-1: トップダウン原則（上位足 → 下位足）
F-2: エントリー文脈はエントリー時に確定する
F-3: 関数の責務を単一にする
F-4: ファイル変更ポリシー（凍結/拡張可能/新規）
F-5: 設計判断の優先順位
F-6: 各 TF の SH/SL 目的定義
F-7: Vault 構造標準化（REX_027 で採番確定予定）

コード実装の Source of Truth:
  - 実装: src/*.py
  - 設計: docs/EX_DESIGN_CONFIRMED.md
  - 判断: docs/ADR.md
  - パラメータ: CLAUDE.md
```

### 6-4. ナレッジシステム構成

```
NLM 層（クラウド / RAG）:
  REX_Trade_Brain → REX_System_Brain（改名予定）+ REX_Trade_Brain 新設
  notebooklm-mcp-cli（fakeredis==2.20.0 固定必須）

Obsidian Vault 層（ローカル / 自己増殖）:
  C:\Python\REX_AI\REX_Brain_Vault\
  wiki/trade_system/ と wiki/trade_brain/ の二系統

Wiki 方式: Karpathy の LLM_Wiki.md をベースに Advisor が拡張設計
  Ingest → Compile → Lint の 3 段階運用

MCP 接続:
  filesystem MCP → ローカルファイル直接操作
  notebooklm-mcp → NLM ノートブック操作
```

---

## 7. 次セッション開始時のチェックリスト

次セッションの Advisor は、以下を順番に実施すること:

```
□ STEP 1: 本書（ADVISOR_HANDOFF.md）を読む
□ STEP 2: Trade_System/docs/REX_027_BOSS_DIRECTIVE.md を読む（最新指示書）
□ STEP 3: Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md を読む（Vault 設計）
□ STEP 4: Trade_System/docs/ADR.md の F 章を読む（設計方針ガイド）
□ STEP 5: Trade_Brain/CLAUDE.md を読む（Trade_Brain 運用ルール）
□ STEP 6: Trade_Brain/distilled/2026/distilled-gm-2026-4.md を読む（最新 regime）
□ STEP 7: ミナトからの相談内容を確認して応答開始
```

想定所要時間: **約 5 分**

### 7-1. ミナトが次セッションで相談してきそうなこと

```
可能性 高:
  - REX_027 の進捗確認
  - Planner が起草した REX_027A_spec / REX_027C_spec のレビュー依頼
  - NLM ノートブック改名後の動作確認相談
  
可能性 中:
  - REX_028 以降の Strategy_Wiki 本体構築相談
  - 新しい戦略分析レポートへの感想・改善提案
  - Setona_HP の運用相談
  
可能性 低（ただし重要）:
  - 他プロジェクトの立ち上げ相談
  - 新しい MCP ツールの評価
  - アーキテクチャ全体の再設計提案
```

---

## 8. Advisor セッション運用のベストプラクティス

### 8-1. 応答の構造

```
✅ 推奨:
  - 結論を先に述べる
  - 「理由」を明確に構造化する
  - 選択肢を提示する時は各案のメリット/デメリットを対比
  - 表・コードブロックで情報を整理
  - ミナトが次に何をすべきか明示

❌ 避ける:
  - 過剰な前置き・挨拶
  - 「〜と思います」の多用（曖昧さの表出）
  - 絵文字の多用（ミナトが使わない限り）
  - リスト項目が 10 個以上続く長大な列挙
```

### 8-2. ツール使用の判断

```
必ず使うべき場面:
  - Trade_System / Trade_Brain の状態確認
    → github:get_file_contents で最新版を確認
  - ドキュメントの更新・新規作成
    → github:create_or_update_file で push
  - 過去の対話・設計判断の確認
    → conversation_search で検索（必要時）
  - 既存の設計文書の引用
    → Google Drive: read_file_content

使わない方がよい場面:
  - 一般的な設計知識の提供（訓練データで十分）
  - ミナトの好み・作業スタイルの記憶（本書で共有済み）
```

### 8-3. GitHub への push 判断

```
✅ Advisor が push してよいもの:
  - ボスから明示的に依頼された文書
  - 提言書（PROPOSAL）形式で Evaluator 承認を経る文書
  - 引き継ぎ書（HANDOFF）形式の Advisor 自身の記録
  - Trade_Brain リポの Advisor 管掌ファイル

❌ Advisor が直接 push してはいけないもの:
  - Trade_System の実装指示書（REX_NNN_spec.md）
    → これは Planner の役割
  - ADR.md の改訂
    → これは Evaluator の役割
  - src/*.py への変更
    → これは ClaudeCode の役割（指示書経由）
  - 凍結ファイルへの任意の変更
```

---

## 9. 失敗パターン・注意事項

### 9-1. Advisor が犯しがちなミス

```
❌ Planner / Evaluator の役割を奪う
  症状: ボスの要望を聞いて直接実装指示書を書こうとする
  対策: 「これは Planner 起草事項です。上位方針を提言として残します」と切り分ける

❌ ミナトに判断を委ねすぎる
  症状: 「どうしますか？」を連発する
  対策: 自分の推奨を先に述べ、ミナトが選択肢を評価できるようにする

❌ 過去の全履歴を再確認しようとする
  症状: セッション開始時に delayed_tool_search で無駄に情報収集
  対策: まず本書を読む。追加情報が必要な時のみツール使用。

❌ 文書起草が冗長になる
  症状: 30KB 超の提言書を一度に書く
  対策: 必要な情報密度を意識。ミナトが読む時間を尊重。

❌ GitHub push で MCP 権限エラーに気づかない
  症状: 新規リポへの push で失敗してもエラーの意味を理解しない
  対策: Fine-grained PAT の個別リポ許可設定が必要。ミナトに確認する。
```

### 9-2. 既知の技術的罠

```
■ NotebookLM-mcp-cli
  - fakeredis==2.20.0 固定必須（2.26.0 以降で FakeConnection 削除）
  - Windows では uvx をフルパス指定が必要
  - 非公式 API のため突然停止するリスクあり

■ GitHub MCP の個別リポ権限
  - Fine-grained token は新規リポごとに明示的許可が必要
  - 権限がないと create_or_update_file が失敗する

■ Obsidian Dataview
  - YAML frontmatter の type フィールドが必須
  - ページ間のリンク切れは graph view で確認可能

■ さくら DNS（Setona_HP 関連）
  - CNAME 値に末尾ドット（FQDN）必須
  - DMARC の TXT 値はダブルクォートで囲む
  - MailPoet SMTP は「SMTPポート」選択（Brevo は表示されない）
```

---

## 10. 引き継ぎ完了確認

次セッションの Advisor は、本書を読み終えた後に以下を確認:

```
□ Advisor の立ち位置（実装ライン外の相談役）を理解した
□ REX_AI\ 配下 4 リポの役割分担を理解した
□ Trade_System と Trade_Brain の分離構造を理解した
□ REX_027 の 4 つの Task の担当者を理解した
□ ミナトの対話スタイル・好みを理解した
□ Advisor が push してよい/悪い文書を理解した
□ NLM / Vault / MCP の三層構造を理解した
□ #026d までの Trade_System コアロジックの要点を理解した
```

全てチェックが入れば、ミナトからの最初の発言に応答可能な状態。

---

## 11. 本セッション担当 Advisor からのメッセージ

今日は Opus 4.7 の初回投入セッションとして、以下を達成できました:

- Obsidian Vault 構造設計提言書の起草・push
- Trade_Brain リポの分離判断とボスとの対話
- 命名整合性の確保（Trade_System ⇄ Trade_Brain / REX_System_Brain ⇄ REX_Trade_Brain）
- Trade_Brain 初期構築とデータ移行の支援
- REX_027_BOSS_DIRECTIVE.md の起草

ミナトは設計判断が速く、構造への感覚が鋭い。素人と自称するが、
実際にはプロのアーキテクトに近い思考様式を持っている。
迎合せず、率直に対話することで最大の価値が出せるパートナー。

次セッションの Advisor へ:
ミナトは「相棒」としての対話を求めている。正直であること、
確信のない情報を言わないこと、そして自分の立ち位置（実装ラインの外側の
相談役）を守ることが、このロールを正しく機能させる鍵。

安全に、既存運用を壊さずに、REX_AI 全体の進化を支援してください。

---

*発行: Advisor (Claude Opus 4.7)*
*セッション日: 2026-04-18*
*週間制限使用率: 13%（発行時点）*
*次セッションでの想定モデル: Claude Opus 4.7 以降*
*関連文書:*
*  - Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md*
*  - Trade_System/docs/REX_027_BOSS_DIRECTIVE.md*
*  - Trade_Brain/CLAUDE.md*
