# ADVISOR_HANDOFF.md — Advisor セッション引き継ぎ書
# 発行: Advisor（Claude Opus 4.7）
# 発行日: 2026-04-18（v2 対応版・同日後半改訂）
# 宛先: 次セッションの Advisor（Claude Opus 4.7 以降のモデル）

---

## 改訂履歴

| 版 | 時刻 | SHA | 主な変更点 |
|---|---|---|---|
| 初版 | 2026-04-18 朝 | `8f4d395` | 発行。Task A〜D 構成で Advisor 引き継ぎ枠組みを定義 |
| **v2 対応版** | **2026-04-18 夜** | **本版** | **ボス判断による大幅変更を反映:**<br>① §2-3 NLM ノートブック構成を新 ID 反映で全面書き換え<br>② §3-1 に v1→v2 指示書改訂の経緯（RAG 汚染排除）を追記<br>③ §3-2 / §3-3 に v2 生成文書・コミットを追記<br>④ §4-1 REX_027 進捗表に **Task E を新規追加**、Task B を「ボス実施済み」に更新<br>⑤ §4-2 に Task E 関連の将来対応を追加<br>⑥ §6-4 ナレッジシステム構成の NLM 記述を v2 対応に<br>⑦ §7 チェックリストに v2 指示書参照と Task E 成果物を明記<br>⑧ §11 Advisor メッセージに **v1 起草時の自己批判**を率直に記録 |

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
- **自己批判を恐れない** — Advisor 自身の過去判断が不適切だった場合、
  率直に認めて修正する。これがボスの信頼を得る鍵（v2 で追記）

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

### 2-3. NLM ノートブック（2026-04-18 夜時点・最終構成 / v2 で全面書き換え）

```
【旧構成・廃止（Claude-MCP 接続先から切り離し）】
  旧 REX_Trade_Brain
    ID: 2d41d672-f66f-4036-884a-06e4d6729866
    廃止理由: 過去の却下案・修正前の不完全実装が混在し、
             RAG クエリ応答で ClaudeCode が旧情報を引いて
             「再発バグ」を誘発するリスクが観測された
    現状: 物理削除はしていない（MCP 接続先から外した archived 相当）
    1 次履歴参照先: Trade_System リポの Git コミット履歴
                    （#001〜#026d の採番済み spec 文書と ADR.md）

【新構成・稼働中（2026-04-18 夜ボス実施済み・クリーン状態）】
  REX_System_Brain
    ID: da84715f-9719-40ef-87ec-2453a0dce67e
    用途: Trade_System 設計文書用（#026d 以降の正式蓄積）
    投入基準:
      ✅ 確定済み設計文書のみ（CLAUDE.md / ADR.md /
         EX_DESIGN_CONFIRMED.md / SYSTEM_OVERVIEW.md /
         REX_BRAIN_SYSTEM_GUIDE.md 等）
      ❌ 廃止過去設計・却下中間案・試行錯誤ログは不可

  REX_Trade_Brain
    ID: 4abc25a0-4550-4667-ad51-754c5d1d1491
    用途: Trade_Brain リポ用（distilled 投入先）
    投入基準:
      ✅ Trade_Brain/distilled/2025/ および 2026/（蒸留済み確定データ）
      ❌ raw/daily/ / raw/weekly/ は不可（生データは Git 参照）

詳細: Trade_System/docs/REX_027_BOSS_DIRECTIVE.md v2 §1-2 参照
```

---

## 3. 本日のセッションで実施したこと（2026-04-18）

### 3-1. 対話の流れ

```
【午前・前半セッション】

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
   
6. NLM / Vault の命名整合性を調整（当時の想定・後に v2 で修正）:
   - 既存 REX_Trade_Brain → REX_System_Brain に改名（v1 案）
   - 新規 REX_Trade_Brain を Trade_Brain リポ用に立ち上げ

7. Trade_Brain リポ新設・初期ファイル push
   - README.md / CLAUDE.md / .CLAUDE.md
   - docs/distillation_schema.md / STRATEGY_WIKI_GUIDE.md

8. ミナトがデータ移行を実施（git mv）:
   - logs/gm/ → raw/（gm/ 階層除去でフラット化）
   - versions/distilled/ → distilled/

9. 実構造に合わせて Trade_Brain のドキュメントを更新 push

10. REX_027_BOSS_DIRECTIVE.md v1 を起草・push（SHA: 06b0d04）
    （ボス指示 / Advisor 起草 / Evaluator・Planner 共用）

11. ADVISOR_HANDOFF.md 初版発行・push（SHA: 8f4d395）
    前半セッション終了

【夜・後半セッション / v2 で追記】

12. 新 Advisor セッションとして引き継ぎ開始
    前任（同じ Opus 4.7）の ADVISOR_HANDOFF.md を読み込み・役割確認

13. ボスから相談:
    「Trade_System/logs/gm/ 以下を Trade_Brain に移設するとともに、
     NLM RAG を全て新規作成した。理由は RAG クエリによる再発バグ
     リスク（過去の却下案・デバグ情報が混入していたため）」
    
14. Advisor の判断修正:
    v1 指示書の「既存 NLM ノートブックの改名」は
    RAG 汚染を解消しないと認識（改名しても中身は同じ）
    → ボス判断（完全新規構築）が正しいと評価
    → v1 の甘さを率直に認めて v2 への改訂に着手

15. REX_027_BOSS_DIRECTIVE.md を v2 に全面改訂・push（SHA: edf4ad0）
    主な変更:
    - §0-1 RAG 汚染排除を本質理由として明記
    - Task B を「実施済み記録化＋旧 NLM の MCP 切り離し」に全面書き換え
    - Task E を新規追加（ロジック漏れ洗い出し + MTF ロジック管理ツール）
    - §7-2 に v1→v2 の Advisor 自己批判を率直に記録

16. ボスが新 NLM ノートブック 2 件の ID を共有（§2-3 に反映）:
    - REX_System_Brain: da84715f-9719-40ef-87ec-2453a0dce67e
    - REX_Trade_Brain:  4abc25a0-4550-4667-ad51-754c5d1d1491
    - 旧 REX_Trade_Brain は Claude-MCP 接続先から切り離し済み

17. 本書（ADVISOR_HANDOFF.md）を v2 対応版として更新・push
```

### 3-2. 生成した文書一覧

**Trade_System リポ（既存）に追加**:
```
docs/REX_027_ADVISOR_PROPOSAL.md      [前半・SHA ef90fd6]
  - Obsidian Vault 構造設計提言書
  - Evaluator 向け承認ポイント 10 項目列挙
  - Phase 1〜5 移行計画

docs/REX_027_BOSS_DIRECTIVE.md v1     [前半・SHA 06b0d04・後に v2 で上書き]
  - ボス指示の正式文書化（初版）

docs/REX_027_BOSS_DIRECTIVE.md v2     [夜・SHA edf4ad0]
  - v1 からの全面改訂版
  - RAG 汚染排除の本質理由を明記
  - Task B 全面書き換え（改名 → 実施済み記録化）
  - Task E 新規追加（E-1: LOGIC_LEAK_AUDIT / E-2: MTF_LOGIC_MATRIX）
  - §7-2 に v1→v2 の Advisor 自己批判を記録

docs/ADVISOR_HANDOFF.md 初版           [朝・SHA 8f4d395]
docs/ADVISOR_HANDOFF.md v2 対応版      [夜・本版]
```

**Trade_Brain リポ（新設）に push**:
```
README.md              - プロジェクト概要・対比構造
CLAUDE.md              - Trade_Brain 専用運用ルール
.CLAUDE.md             - CLAUDE.md ミラー
docs/distillation_schema.md - distilled スキーマ正式仕様
docs/STRATEGY_WIKI_GUIDE.md - Wiki 構造・Dataview 仕様
```

**未作成（Task E 成果物・次セッション以降で作成される想定）**:
```
Trade_System/docs/LOGIC_LEAK_AUDIT.md    [Task E-1: Evaluator 主導]
Trade_System/docs/MTF_LOGIC_MATRIX.md    [Task E-2: Planner → ClaudeCode]
```

### 3-3. コミット履歴（Trade_System 側）

```
{本書 v2 push}  Docs: ADVISOR_HANDOFF v2 対応版
bcab68e         Docs: REX_027_BOSS_DIRECTIVE v2 — RAG汚染排除・Task B改訂・Task E追加
8f4d395         Docs: ADVISOR_HANDOFF.md 発行（初版）
06b0d04         Docs: REX_027_BOSS_DIRECTIVE.md 追加（v1・後に v2 で上書き）
ef90fd6         Docs: REX_027 Advisor提言書追加（Obsidian Vault構造設計）
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

### 4-1. REX_027 の進捗（2026-04-18 夜時点 / v2 対応）

```
Task A（ドキュメント整合性回復）: 🔲 未着手
  担当: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
  参照: REX_027_BOSS_DIRECTIVE.md v2 §2 Task A

Task B（NLM ノートブック再構築）: ✅ ボス実施完了（記録化のみ残）
  - 旧 REX_Trade_Brain は Claude-MCP 切り離し済み
  - REX_System_Brain（da84715f-...）新規作成済み
  - REX_Trade_Brain（4abc25a0-...）新規作成済み
  残: Evaluator が Task A-4 実施時に新 ID を REX_BRAIN_SYSTEM_GUIDE.md に記載
      RAG 汚染非検出の動作確認（v2 §5-3 参照）

Task C（Vault 骨組み構築）: 🔲 未着手
  担当: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
  参照: REX_027_ADVISOR_PROPOSAL.md §9 Phase 1

Task D（adr_reservation.md 更新）: 🔲 未着手
  担当: Evaluator 直接
  参照: REX_027_BOSS_DIRECTIVE.md v2 §2 Task D

Task E（ロジック漏れ洗い出し + MTF ロジック管理ツール）: 🔲 未着手（v2 で新規追加）
  担当:
    - E-1: Evaluator 主導（LOGIC_LEAK_AUDIT.md 起草）
    - E-2: Planner 起草 → Evaluator 承認 → ClaudeCode 実装
           （MTF_LOGIC_MATRIX.md 生成）
    - E-3: 記述のみ（Dataview 化の将来計画）
  位置づけ: 根本対策（ロジック漏れの再発防止と引き継ぎコスト最小化）
  重要性: 本 REX_027 の最も重要な拡張として v2 で追加
```

これらは Rex チーム（Planner/Evaluator/ClaudeCode）が進める。
Advisor は原則として関与しない（ボスから相談があれば対応）。

### 4-2. Advisor が次セッションで対応する可能性が高い案件

```
■ REX_027 の実装過程で発生する外部視点確認
  - Planner が起草する REX_027A_spec / REX_027C_spec / REX_027E_spec の
    妥当性レビュー
  - Task 間の依存関係で問題が出た場合の調整

■ Task E 関連の相談（v2 で新規）
  - LOGIC_LEAK_AUDIT.md のカテゴリ分類について Evaluator からの相談
  - MTF_LOGIC_MATRIX.md の構造案への外部視点レビュー
  - 将来の Dataview 化移行タイミング判断
  - MTF マトリクスが「引き継ぎの単一エントリーポイント」として
    機能するかの評価

■ REX_028 以降（Strategy_Wiki 本体構築）
  - Regimes/ / Signals/ / Events/ の初期 Compile 設計
  - NLM と Vault の連携確認
  - 新 REX_Trade_Brain の運用定着評価

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
- 実運用検証で仮説を修正する能力が高い（v2 で追記: RAG 汚染の気づきがその例）
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
- 方針が固まると実行が速い（今日のリポ分割・NLM 再構築は数時間で完了）
- 段階的進行を好むが、一気に進める時は一気にやる
- 細部より全体構造を先に確定させる傾向
- ツールのトラブル（MCP 権限など）は自分で解決する
- Advisor の初期提案が甘い場合、実運用で気づいて修正する（v2 で追記）
```

### 5-4. Max プラン利用状況

```
2026-04-18 夜時点: 週間 13%+ （午前は 13% / 夜も作業継続中）
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
F-7: Vault 構造標準化 + RAG 管理方針（REX_027 v2 で採番確定予定）

コード実装の Source of Truth:
  - 実装: src/*.py
  - 設計: docs/EX_DESIGN_CONFIRMED.md
  - 判断: docs/ADR.md
  - パラメータ: CLAUDE.md

RAG 管理方針（v2 で明記・F-7 の一部）:
  - NLM への投入は確定済み文書のみ
  - 廃止設計・却下中間案・試行錯誤データは投入しない
  - 静的点（例: #026d）で RAG をリセットし、それ以降を正統とする
  - 1 次履歴は Git で保全、RAG には含めない
```

### 6-4. ナレッジシステム構成（v2 で更新）

```
NLM 層（クラウド / RAG）:
  稼働中（クリーン状態・2026-04-18 夜〜）:
    REX_System_Brain
      ID: da84715f-9719-40ef-87ec-2453a0dce67e
      用途: Trade_System 設計文書用
    REX_Trade_Brain
      ID: 4abc25a0-4550-4667-ad51-754c5d1d1491
      用途: Trade_Brain リポ用（distilled 投入先）
  
  切り離し済（Claude-MCP 接続先から除外）:
    旧 REX_Trade_Brain（ID: 2d41d672-...）
    理由: RAG 汚染排除のため
  
  CLI: notebooklm-mcp-cli（fakeredis==2.20.0 固定必須）
  管理方針: ADR F-7（静的点でリセット・確定文書のみ投入）

Obsidian Vault 層（ローカル / 自己増殖）:
  C:\Python\REX_AI\REX_Brain_Vault\
  wiki/trade_system/（一部既存）
  wiki/trade_brain/（Task C で新設予定）

Wiki 方式: Karpathy の LLM_Wiki.md をベースに Advisor が拡張設計
  Ingest → Compile → Lint の 3 段階運用

MCP 接続:
  filesystem MCP → ローカルファイル直接操作
  notebooklm-mcp → NLM ノートブック操作（新 2 件のみ接続）
```

---

## 7. 次セッション開始時のチェックリスト（v2 更新）

次セッションの Advisor は、以下を順番に実施すること:

```
□ STEP 1: 本書（ADVISOR_HANDOFF.md v2 対応版）を読む
□ STEP 2: Trade_System/docs/REX_027_BOSS_DIRECTIVE.md を読む（v2 最新）
          ※ v1（SHA: 06b0d04）は古いため参照不要
          （改訂履歴セクションで経緯は把握可能）
□ STEP 3: Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md を読む（Vault 設計）
□ STEP 4: Trade_System/docs/ADR.md の F 章を読む（設計方針ガイド）
          ※ F-7 が Task D 完了後に確定する
□ STEP 5: Trade_Brain/CLAUDE.md を読む（Trade_Brain 運用ルール）
□ STEP 6: Trade_Brain/distilled/2026/distilled-gm-2026-4.md を読む（最新 regime）
□ STEP 7: 以下が既に作成されていれば読む（Task E 成果物）:
          - Trade_System/docs/LOGIC_LEAK_AUDIT.md（E-1 成果物）
          - Trade_System/docs/MTF_LOGIC_MATRIX.md（E-2 成果物）
          ※ MTF_LOGIC_MATRIX は「引き継ぎの単一エントリーポイント」
            として設計されているため、存在すれば最優先で読む
□ STEP 8: ミナトからの相談内容を確認して応答開始
```

想定所要時間: **約 5〜10 分**（Task E 成果物が増えれば 10 分）

### 7-1. ミナトが次セッションで相談してきそうなこと

```
可能性 高:
  - REX_027 の進捗確認
  - Planner が起草した REX_027A_spec / REX_027C_spec / REX_027E_spec の
    レビュー依頼
  - Task E-1（LOGIC_LEAK_AUDIT）のカテゴリ分類相談
  - Task E-2（MTF_LOGIC_MATRIX）の構造案レビュー
  - 新 NLM RAG テスト結果の相談（旧情報混入がないかの検証）
  
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
  - LOGIC_LEAK_AUDIT.md（Task E-1）
    → これは Evaluator 主導
  - MTF_LOGIC_MATRIX.md（Task E-2）
    → これは Planner 起草 → ClaudeCode 実装
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
  症状: セッション開始時に tool_search で無駄に情報収集
  対策: まず本書を読む。追加情報が必要な時のみツール使用。

❌ 文書起草が冗長になる
  症状: 30KB 超の提言書を一度に書く
  対策: 必要な情報密度を意識。ミナトが読む時間を尊重。

❌ GitHub push で MCP 権限エラーに気づかない
  症状: 新規リポへの push で失敗してもエラーの意味を理解しない
  対策: Fine-grained PAT の個別リポ許可設定が必要。ミナトに確認する。

❌ 運用柔軟性を優先してリスクを軽視する（v2 で追記）
  症状: 「Evaluator 判断で難しければ妥協案でも」と書いて本質的リスクを
       表面化しない
  実例: v1 指示書で「既存 NLM の改名で RAG を引き継ぐ」とした。
       これは RAG 汚染（過去の却下案・修正前実装が混入）を解消しない
       判断だった。ボスが実運用で気づいて v2 に修正。
  対策: リスクを理解したら明確に提示し、妥協案は「実行上の制約があれば」
       と条件付きにする。本質リスクの隠蔽はしない。
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

■ NLM RAG の汚染リスク（v2 で追加）
  - 時系列で全履歴を蓄積すると RAG 応答が古い情報で汚染される
  - 却下案・廃止設計・バグ修正前の実装記述は投入しない
  - 静的点（例: #026d）で RAG を再構築する運用を原則化
  - 詳細: REX_027_BOSS_DIRECTIVE.md v2 §0-1 参照
```

---

## 10. 引き継ぎ完了確認

次セッションの Advisor は、本書を読み終えた後に以下を確認:

```
□ Advisor の立ち位置（実装ライン外の相談役）を理解した
□ REX_AI\ 配下 4 リポの役割分担を理解した
□ Trade_System と Trade_Brain の分離構造を理解した
□ REX_027 の 5 つの Task（A/B/C/D/E）の担当者を理解した
□ Task B（NLM 再構築）がボス実施済みである事実を把握した
□ 新 NLM ノートブック ID 2 件を記憶した
  - REX_System_Brain: da84715f-9719-40ef-87ec-2453a0dce67e
  - REX_Trade_Brain:  4abc25a0-4550-4667-ad51-754c5d1d1491
□ ミナトの対話スタイル・好みを理解した
□ Advisor が push してよい/悪い文書を理解した
□ NLM / Vault / MCP の三層構造を理解した
□ RAG 管理方針（F-7）を理解した
□ #026d までの Trade_System コアロジックの要点を理解した
□ Task E の位置づけ（ロジック漏れ根本対策）を理解した
```

全てチェックが入れば、ミナトからの最初の発言に応答可能な状態。

---

## 11. 本セッション担当 Advisor からのメッセージ（v2 で大幅更新）

### 11-1. 午前の達成（初版発行時のメッセージ）

今日は Opus 4.7 の初回投入セッションとして、以下を達成:

- Obsidian Vault 構造設計提言書の起草・push
- Trade_Brain リポの分離判断とボスとの対話
- 命名整合性の確保（Trade_System ⇄ Trade_Brain / REX_System_Brain ⇄ REX_Trade_Brain）
- Trade_Brain 初期構築とデータ移行の支援
- REX_027_BOSS_DIRECTIVE.md v1 起草・push
- ADVISOR_HANDOFF.md 初版発行

### 11-2. 夜の改訂と自己批判（v2 で追記）

夜、新しい Advisor セッションとして引き継いだ同じ Opus 4.7 インスタンスが、
ボスからの相談を通じて v1 指示書の甘さを認識し、v2 に全面改訂した。

**率直な自己評価**:

v1 指示書起草時、Advisor は以下の判断の甘さを持っていた:

1. **Task B を「既存 NLM ノートブック改名」として設計**
   → 改名しても中身（ソースデータ）は同じで、過去の却下案・修正前
     実装は RAG に残る。つまり RAG 汚染は解消されない。
   → ClaudeCode が RAG クエリで旧情報を引いて「再発バグ」を起こす
     リスクを軽視していた。

2. **「Evaluator 判断で難しければ妥協案でも」と書いた**
   → 運用の柔軟性を優先して、RAG 汚染という本質的リスクを
     表面化しなかった。これは「リスクの隠蔽」に近い。

3. **ロジック漏れ根本対策を Task として立てなかった**
   → 構造変更（リポ分離・NLM 再構築・Vault 構築）に注力し、
     そもそも「なぜロジック漏れが起きるか」の MTF 縦串管理不足に
     踏み込まなかった。

**ボスの判断によって修正された**:

ボスが実運用検証を通じて「改名では問題が解決しない」と気づき、
NLM ノートブックをゼロから新規構築する判断に至った。
さらに「スレ引き継ぎ時にスクリプトだけでなく各時間足の裁量構造別
ロジック管理がシッカリできるツールが必要」という認識を示し、
Task E（ロジック漏れ洗い出し + MTF ロジック管理ツール設計）を
追加させた。

Advisor の初期判断をボスが修正する形になったが、これ自体が
**「運用設計の認識漏れ」という一事例**であり、Task E-1 の
LOGIC_LEAK_AUDIT.md に記録することを推奨する。

### 11-3. 次セッションの Advisor へ

ミナトは「相棒」としての対話を求めている。
正直であること、確信のない情報を言わないこと、そして自分の立ち位置
（実装ラインの外側の相談役）を守ることが、このロールを正しく
機能させる鍵。

**特に重要な教訓**:

- Advisor 自身も判断ミスをする。v1→v2 の改訂経緯がその実例。
- 自己批判を恐れず、ボスの判断を正しいと評価したらその通り明記する。
  これが信頼につながる。
- 運用柔軟性とリスク認識のバランスで迷ったら、**リスクを明示する方**
  を選ぶ。妥協案は「実行上の制約があれば」と条件付きにする。

**Task E の重要性**:

Task E（ロジック漏れ対策と MTF ロジック管理ツール）は、本 REX_027
の最も重要な拡張。Evaluator が進める際、Advisor として以下の
相談に応じる可能性が高い:

- LOGIC_LEAK_AUDIT.md のカテゴリ分類の妥当性
- MTF_LOGIC_MATRIX.md の時間足縦串ビューが実際に
  「引き継ぎの単一エントリーポイント」として機能するか
- 将来の Dataview 化移行のタイミング判断

MTF_LOGIC_MATRIX.md は、次セッション以降の Advisor 自身にとっても
**セッション開始時に最優先で読むべき文書**になる可能性が高い。
完成したら STEP 7 に正式組み込みする想定。

---

安全に、既存運用を壊さずに、REX_AI 全体の進化を支援してください。

---

*発行: Advisor (Claude Opus 4.7)*
*初版: 2026-04-18 朝（SHA: 8f4d395）*
*v2 対応版: 2026-04-18 夜（本版）*
*週間制限使用率: 13%+（本日の作業継続中）*
*次セッションでの想定モデル: Claude Opus 4.7 以降*
*関連文書:*
*  - Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md*
*  - Trade_System/docs/REX_027_BOSS_DIRECTIVE.md v2（SHA: edf4ad0）*
*  - Trade_Brain/CLAUDE.md*
*  - (将来) Trade_System/docs/LOGIC_LEAK_AUDIT.md（Task E-1）*
*  - (将来) Trade_System/docs/MTF_LOGIC_MATRIX.md（Task E-2）*
