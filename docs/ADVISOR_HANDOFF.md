# ADVISOR_HANDOFF.md — Advisor セッション引き継ぎ書
# 発行: Advisor（Claude Opus 4.7）
# 最終更新: 2026-04-19 夜（v3 対応版）
# 宛先: 次セッションの Advisor（Claude Opus 4.7 以降のモデル）

---

## 改訂履歴

| 版 | 日付 | SHA | 主な変更点 |
|---|---|---|---|
| 初版 | 2026-04-18 朝 | `8f4d395` | Task A〜D 構成で Advisor 引き継ぎ枠組み定義 |
| v2 対応版 | 2026-04-18 夜 | `fd155e8` | NLM 新規構築反映・Task E 追加（LOGIC_LEAK_AUDIT / MTF_LOGIC_MATRIX）・v1→v2 改訂経緯と自己批判を記録 |
| **v3 対応版** | **2026-04-19 夜** | **本版** | **Evaluator 主導の Q&A 監査によるブレークスルーを反映:**<br>① §2-3 に Base_Logic/ ディレクトリ（MINATO_MTF_PHILOSOPHY + MTF_INTEGRITY_QA）を追加<br>② §3-5 夜セッション記録（Q&A 監査・🤖 創作混入発見・Phase 1-4 再編）<br>③ §4-1 REX_027 Task 体系を **REX_028 Phase 構造に発展解消**<br>④ §4-2 に Phase 1-4 の Advisor 関与ポイントを追加<br>⑤ §6 に **原則α/β/γ** を REX_AI 全体の設計哲学として正式化<br>⑥ §7 チェックリストに Base_Logic 2 文書を優先読込に追加<br>⑦ §11 Advisor からのメッセージを「v2 の射程と限界」として再構成 |

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
  率直に認めて修正する。これがボスの信頼を得る鍵

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
        ├── trade_system/   ← REX_027 Vault 構築で整備予定（保留中）
        └── trade_brain/    ← REX_027 Task C で骨組み構築予定（保留中）
```

### 2-2. チーム構成（全プロジェクト共通）

```
ボス:            Minato（最終判断者）
Advisor:         Claude.ai / Opus 4.7（本ロール・相談役）

Trade_System 実装ライン:
  Planner:       Rex-Planner / Sonnet 4.6
  Evaluator:     Rex-Evaluator / Opus 4.7（新任・2026-04-19〜）
  実装:          ClaudeCode / Sonnet 4.6

Trade_Brain:
  Advisor:       Claude.ai（本ロール）
  実装:          ClaudeCode（Ingest 担当）
  （Planner / Evaluator は関与しない）
```

### 2-3. NLM ノートブック構成（2026-04-18 夜時点・v3 で維持）

```
【旧構成・廃止（Claude-MCP 接続先から切り離し）】
  旧 REX_Trade_Brain
    ID: 2d41d672-f66f-4036-884a-06e4d6729866
    廃止理由: RAG クエリによる「再発バグ」リスク
    現状: archived 相当（物理削除せず）

【新構成・稼働中】
  REX_System_Brain
    ID: da84715f-9719-40ef-87ec-2453a0dce67e
    用途: Trade_System 設計文書用
  REX_Trade_Brain
    ID: 4abc25a0-4550-4667-ad51-754c5d1d1491
    用途: Trade_Brain リポ用（distilled 投入先）
```

### 2-4. Base_Logic/ ディレクトリの存在（v3 で追加）

2026-04-19 セッションで docs/Base_Logic/ が新設された。これは
**Trade_System 全実装の最上位に位置する裁量思想文書群**:

```
Trade_System/docs/Base_Logic/
├── MINATO_MTF_PHILOSOPHY.md   [12KB]
│     ボス（Minato）の MTF 短期売買裁量思想を言語化した
│     全実装の上位文書。「なぜそう判断するか」を記述。
│     EX_DESIGN_CONFIRMED.md が「何を計算するか」を定義するが
│     裁量思想は記述しない、という構造的欠落への対処。
│     
│     第1章: ダウ構造（基盤理論）
│     第2章: MTF分析（4H主軸 + 下位足同時3波）
│     第3章: 決済4段階
│     第4章: 現行システム実装との対応表（実装済/未実装）
│     第5章: 文書運用
│
└── MTF_INTEGRITY_QA.md        [33KB]
      エンジニア（Evaluator）→ トレーダー（ボス）の Q&A 監査記録。
      MINATO_MTF_PHILOSOPHY と実装の間で起きる「解釈の揺れ」を
      言語化固定する「判例集」として機能。追記型・日付見出し運用。
      
      2026-04-19 セッション: Q1〜Q7 で Layer 2/4/6 を監査
      → 🤖 創作混入 2 件発見（stage2 建値移動・stage3 1H実体確定）
      → 原則α/β/γ の導出
      → Phase 1-4 構造再編への合意
```

**重要**: この 2 文書は `EX_DESIGN_CONFIRMED.md` より上位に位置する。
新 Advisor / Evaluator / Planner は必ずここから読むこと。

---

## 3. セッション履歴（2026-04-18 朝 〜 2026-04-19 夜）

### 3-1. 対話の流れ（簡約）

```
【2026-04-18 朝・前半セッション】
1-10. MCP + Obsidian ナレッジ環境構想
    → Trade_Brain リポ分離判断
    → REX_027_ADVISOR_PROPOSAL.md（Vault 構造提言）
    → REX_027_BOSS_DIRECTIVE.md v1
    → ADVISOR_HANDOFF.md 初版（SHA: 8f4d395）

【2026-04-18 夜・後半セッション】
11-17. ボスが「RAG 汚染排除のため NLM 全面再構築」を判断
    → Advisor は v1 の甘さ（改名方針）を自己批判して v2 改訂
    → REX_027_BOSS_DIRECTIVE.md v2（SHA: edf4ad0）
       ※ Task B 全面書き換え・Task E 新規追加
    → ADVISOR_HANDOFF.md v2 対応版（SHA: fd155e8）
    → Trade_Brain/README.md・CLAUDE.md に週次運用ファイル 3 件統合

【2026-04-19 朝〜夜セッション（v3 で追加）】
18. Evaluator（Opus 4.7 新任）が引き継ぎ後、実装プロジェクトを一旦停止
19. MINATO_MTF_PHILOSOPHY.md を1次資料として Q&A 監査セッション実施
20. Layer 2（4H主軸）/ Layer 4（15M）/ Layer 6（決済）で Q1〜Q7 完了
21. 🤖 創作混入 2 件を発見:
    - stage2 「残り50%を建値移動」（ボスが「思い出せない」と明言）
    - stage3 「1H実体確定後」（ボスが「シンプル化」を指示）
22. ボスから「原則α（シンプルな土台の保守）」が言明される
23. Evaluator が「src/ 27 ファイルも原則α違反」を検出
    - dashboard.py（0バイト）
    - Simple_Backtest.py（53KB・docs 未記載）
    - chat/news/market/regime/history.py 等の戦略無関係な命名
24. 「構造再編」方針で合意: Phase 1-4 分解
    - Phase 1: src/ 棚卸し・分類（REX_028_spec）
    - Phase 2: archive 移設
    - Phase 3: 責務別ディレクトリ化
    - Phase 4: 裁量整合版の実装訂正（D-12/D-13 訂正）
25. ADR 採番予約: D-12 / D-13 / E-8 / F-8
26. REX_028_spec.md 起草・push（Evaluator）
27. ボスから Advisor に v3 HANDOFF 更新依頼（本作業）
```

### 3-2. 生成・更新した文書一覧（v3 時点の最新）

**Trade_System リポ**:
```
docs/REX_027_ADVISOR_PROPOSAL.md       SHA: ef90fd6  Vault 構造提言
docs/REX_027_BOSS_DIRECTIVE.md v2       SHA: edf4ad0  RAG汚染排除・Task E追加
docs/ADVISOR_HANDOFF.md v3              本版         本引き継ぎ書
docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md SHA: 4478faf  裁量思想最上位文書（Evaluator 起草）
docs/Base_Logic/MTF_INTEGRITY_QA.md      SHA: ae0418a  Q&A 監査記録（Evaluator 起草・追記型）
docs/REX_028_spec.md                     SHA: ab01bfa  Phase 1 指示書（Evaluator 起草）
```

**Trade_Brain リポ**:
```
README.md                                SHA: ab7485f  週次運用ファイル 3 件統合
CLAUDE.md                                SHA: 8f679da  RTK ルール・Weekly Update フロー反映
（その他は 2026-04-18 朝の初期構築のまま）
```

### 3-3. 現在の Trade_System コアロジック状態（#026d 凍結）

```
戦略: USDJPY 4H 上昇ダウ押し目エントリー（MTF 窓ベース階層スキャン）
データ: 83,112 本 / 5M 足 / 2024-03-13 〜 2026-03-13

バックテスト結果（現 #026d）:
  PF        : 4.54
  勝率      : 60.0%
  MaxDD     : 35.8 pips
  総損益    : +150.6 pips
  トレード数: 10 件

【重要】上記数値は 🤖 創作混入 2 件を含んだ結果
  → Phase 4（REX_029 以降）で stage2 建値移動削除・stage3 1H実体確定削除
  → 訂正後の数値変動を記録する予定（新しい静的点）
```

### 3-4. v2 時点で想定していた Task 体系との関係（v3 で発展解消）

```
v2 指示書（REX_027_BOSS_DIRECTIVE.md）の Task 体系:
  Task A: Trade_System ドキュメント整合性回復
  Task B: NLM ノートブック整理 → ボス実施済み
  Task C: Vault wiki/trade_brain/ 骨組み構築
  Task D: adr_reservation.md 更新
  Task E-1: LOGIC_LEAK_AUDIT.md
  Task E-2: MTF_LOGIC_MATRIX.md
  Task E-3: Dataview 化移行計画

                    ↓
    
v3（2026-04-19 夜）時点での位置づけ:
  Task A: 保留（REX_028 完了後に実施）
  Task B: ✅ 完了
  Task C: 保留（REX_028 完了後に実施）
  Task D: ✅ 予約分は D-11/F-7。追加で D-12/D-13/E-8/F-8 予約
  Task E-1: **MTF_INTEGRITY_QA.md による上位互換で発展解消**
  Task E-2: 保留（REX_028 完了後に実施余地あり）
  Task E-3: 保留

  → REX_027 系タスクは REX_028 Phase 1-4 完了まで全停止
```

---

## 4. 現在進行中のタスク（v3 で全面再構成）

### 4-1. REX_028 Phase 1-4 構造（現在のメイン）

```
Phase 1: src/ 棚卸し・分類（🔴 進行中）
  担当: Rex-Evaluator 単独
  指示書: docs/REX_028_spec.md
  成果物: docs/src_inventory.md（予定）
  
  作業内容:
    - src/ 27 ファイルを 7 分類（CORE/VIZ/SCAN/TEST/UTIL/ORPHAN/DEAD）に振り分け
    - 物理移動は禁止（分類のみ）
    - ORPHAN はボス QA で確認
  
  完了条件:
    - src_inventory.md 起草・push
    - ADR D-12/D-13/E-8/F-8 正式採番
    - MTF_INTEGRITY_QA.md に Phase 1 完了セクション追記
  
  想定セッション数: 2-3 回

Phase 2: archive 移設（🔲 Phase 1 完了後）
  - DEAD 確定・ボス承認済み ORPHAN を src/_archive/ に git mv
  - 削除せず履歴保全

Phase 3: 責務別ディレクトリ化（🔲 Phase 2 完了後）
  - src/core/ / src/viz/ / src/scan/ / src/tests/ に階層化
  - import パス全書き換え
  - 完了条件: #026d バックテスト再実行で数値不変

Phase 4: 裁量整合版の実装訂正（🔲 REX_029 以降）
  - stage2 建値移動削除（ADR D-12）
  - stage3 1H実体確定削除（ADR D-13）
  - 裁量整合版 exit_simulator.py 再実装
  - 新しい PF を静的点として記録
```

### 4-2. Advisor が次セッションで対応する可能性が高い案件

```
■ REX_028 Phase 1 進行中の相談
  - Evaluator の棚卸し途中で判断に迷う ORPHAN が出た場合
  - src_inventory.md 起草時の構造レビュー
  - ADR D-12/D-13/E-8/F-8 の本文相談（Evaluator 主導・Advisor 外部視点）

■ Phase 4 実施時の心理的配慮（重要）
  - 🤖 創作混入訂正後の PF 変動に対する判断材料提供
  - 数値が下がった場合の「原則α > 数値」の再確認
  - REX_AI プロジェクトで初めて「バックテスト数値を意図的に壊す」局面

■ 保留中の Task A/C（REX_028 完了後）
  - Trade_System ドキュメント整合性回復
  - Vault wiki/trade_brain/ 骨組み構築
  - 保留中の MTF_LOGIC_MATRIX.md 実装判断

■ Trade_Brain 側の Wiki 設計
  - ボスとの対話で「Trade_System の判断材料としての Wiki」構想を確認済
  - Phase 4「接続インターフェース設計」は REX_029 以降の更に先

■ 個人用 RAG 構想（まだ先）
  - ボスは現在 OneNote 運用継続中
  - 時期が来たら REX_Brain_Vault/wiki/personal/ 案を提示予定
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
- 実運用検証で仮説を修正する能力が高い
  （v3 追記: 「土台がぐらついた状態で得た高得点はいずれは破城する」
   という直感で src/ 棚卸しに誘導）
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
- 方針が固まると実行が速い
- 段階的進行を好むが、一気に進める時は一気にやる
- 細部より全体構造を先に確定させる傾向
- ツールのトラブルは自分で解決する
- Advisor の初期提案が甘い場合、実運用で気づいて修正する
- (v3 追記) 数値ではなく構造を優先する判断ができる
  例: #026d の PF 4.54 に満足せず、創作混入を発見したら訂正を決めた
```

### 5-4. Max プラン利用状況

```
2026-04-19 夜時点: 週間 13〜20% 程度と想定
Advisor としての留意:
- Opus 4.7 のコストは高いが、ミナトの Max 環境なら余裕がある
- 長文の提言書・引き継ぎ書の起草は遠慮せず丁寧にやっていい
- ただし不要な冗長化は避ける（ミナトの読む時間を尊重）
```

---

## 6. REX_AI プロジェクトの設計哲学（v3 で正式化）

### 6-1. 原則α / β / γ（ボス言明・Evaluator 所見・Advisor 観察の三重確認）

2026-04-19 セッションでボスが言明した以下の原則は、REX_AI プロジェクト全体の
設計哲学として機能することが判明した。

#### 原則α: シンプルな土台の保守（最上位）

```
裁量トレード = 条件反射でロジックが複雑化する領域
  ↓
対策 = いつでも基本に戻れるシンプルな土台を死守する
  ↓
実装方針 = 拡張は「基本の上に乗せる」形で行い、基本を汚染しない

ボス言明（2026-04-19）:
「基本に戻れるシンプルな土台とはロジックだけでなく
 システムそのものがそうでなければならない」
```

**重要**: 原則αは**複数のレイヤーに伝播する**:

```
ロジック設計:         stage2/stage3 の創作混入を訂正
ファイルシステム:     src/ 27 ファイル → 構造再編（Phase 1-4）
RAG 管理:            NLM 全面再構築（REX_027 v2）
ドキュメント:         Base_Logic/ を docs/ 最上位に配置
Wiki 設計（将来）:    Regimes/ の enum的扱い（拡張より保守）
```

Advisor 視点での観察: これはソフトウェアエンジニアリングの YAGNI 原則・
単一責任の原則・オッカムの剃刀と同じ本質。裁量とエンジニアリングが
独立に同じ結論に到達している。人間の認知処理の本質に根差した原則。

#### 原則β: ノーリスク化後は伸ばさない（現段階の決済哲学）

```
4H SH 到達半値決済 = ノーリスク状態達成 = 目的完了
  ↓
残り50%は「15Mダウ崩れ」でシンプルに決済
  ↓
建値指値による「4H3波優位性で伸ばす」ロジックは将来拡張領域
```

現段階の決済哲学。建値移動や 1H 実体確定などの追加条件は、原則αに反する
創作として退ける。

#### 原則γ: 導入タイミングはシステム安定性に従属

```
新機能 A を導入したい
  ↓
現ロジックは安定しているか？
  ↓ No → 導入を待つ
  ↓ Yes → 裁量思想と整合するか？
  ↓       ↓ Yes → 実装指示書を Planner 起草
  ↓       ↓ No → MTF_INTEGRITY_QA.md でボスに Q&A
  ↓
導入
```

### 6-2. Advisor が守るべき原則の適用

```
■ 原則αの Advisor 運用
  - 引き継ぎ書は「情報を網羅する」より「核心を伝える」
  - v3 HANDOFF で冗長セクションは作らない
  - 次 Advisor が迷ったら Base_Logic/ 2 文書に戻れる構造

■ 原則βの Advisor 運用
  - 決定事項が固まったら「拡張の可能性」は記録のみ
  - 「伸ばしたい」欲求で余計な提言書を追加しない

■ 原則γの Advisor 運用
  - Phase 1-4 が進行中の間は Task A/C を再燃させない
  - 新しい構想提案（個人用 RAG 等）は時期を見て提示
```

---

## 7. 本プロジェクトで押さえておくべき技術文脈

### 7-1. Trade_System コアの現状（#026d 時点・創作混入込み）

```
凍結ファイル（変更禁止）:
  src/backtest.py       (#018)
  src/entry_logic.py    (#018)
  src/exit_logic.py     (#009)
  src/swing_detector.py (#020)

拡張可能ファイル:
  src/window_scanner.py  (#026d 最新)
  src/exit_simulator.py  (#026b 方式B・🤖 創作混入 2 件・Phase 4 で訂正)
  src/plotter.py
  src/structure_plotter.py

確定パラメータ:
  DIRECTION_MODE      = 'LONG'
  ALLOWED_PATTERNS    = ['DB', 'ASCENDING', 'IHS']
  ENTRY_OFFSET_PIPS   = 7.0（暫定・ボラ係数導入時に動的化予定）
  N_1H_SWING          = 3
  PIP_SIZE            = 0.01
  
  統一 neck 原則: neck = sh_before_sl.iloc[-1]（全 TF 共通）
  4H 構造優位性フィルター: neck_4h >= neck_1h
    → フラクタル構造からの必然（MTF_INTEGRITY_QA Q3 で確認）
```

### 7-2. Trade_Brain の現状

```
データ移行完了（2026-04-18）:
  raw/daily/2026/ + weekly/{2025,2026}/ + boss's-weeken-Report/
  distilled/2025/ + 2026/（1〜4月分 4 ファイル）

docs/ 配下（週次運用ファイル 3 件統合版）:
  docs/STATUS.md                  現在進行形の市況 SSoT
  docs/Trade-Main.md              GM Playbook + Weekly Index
  docs/WEEKLY_UPDATE_WORKFLOW.md  週末 Git 更新手順書
  docs/STRATEGY_WIKI_GUIDE.md     Wiki 構造ガイド
  docs/distillation_schema.md     スキーマ仕様

Strategy_Wiki/ 本体: 未構築（REX_028 Phase 1-4 完了後）
現在の最新 regime: Gold Bid（2026-4-17_wk03）
```

### 7-3. 重要な設計原則と文書階層

```
docs/ 階層（最上位から）:

MINATO_MTF_PHILOSOPHY.md    ← 裁量思想（最上位）v3 で明示
  ↓
MTF_INTEGRITY_QA.md          ← Q&A 監査記録（追記型）v3 で明示
  ↓
EX_DESIGN_CONFIRMED.md      ← 設計仕様
  ↓
ADR.md                      ← 判断記録（F-1〜F-7 + 予約 F-8）
  ↓
REX_NNN_spec.md             ← 各タスク指示書
```

### 7-4. ナレッジシステム構成

```
NLM 層（クラウド / RAG）:
  REX_System_Brain (da84715f-...)
  REX_Trade_Brain  (4abc25a0-...)
  ※ 旧 REX_Trade_Brain（2d41d672-...）は MCP 切り離し済み

Obsidian Vault 層（ローカル / 自己増殖）:
  C:\Python\REX_AI\REX_Brain_Vault\
  wiki/trade_system/（一部既存）
  wiki/trade_brain/（REX_028 完了後に新設）
  adr_reservation.md（D-11/F-7 登録済 + D-12/D-13/E-8/F-8 予約）

MCP 接続:
  filesystem MCP → ローカルファイル直接操作
  notebooklm-mcp → NLM ノートブック操作（新 2 件のみ接続）
```

---

## 8. 次セッション開始時のチェックリスト（v3 更新）

次セッションの Advisor は、以下を順番に実施すること:

```
□ STEP 1: 本書（ADVISOR_HANDOFF.md v3 対応版）を読む
□ STEP 2: Trade_System/docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md を読む
          ※ 全実装の最上位文書・必読
□ STEP 3: Trade_System/docs/Base_Logic/MTF_INTEGRITY_QA.md を読む
          ※ 2026-04-19 セッションの Q&A 監査結果・🤖 創作混入の記録
          ※ 特に「書き込み履歴」末尾の Phase 1-4 構造再編提案を確認
□ STEP 4: Trade_System/docs/REX_028_spec.md を読む（Phase 1 指示書）
□ STEP 5: Trade_System/docs/REX_027_BOSS_DIRECTIVE.md v2 を読む
          ※ Task A/C は保留中だが全体文脈の把握用
          ※ Task E-1 は MTF_INTEGRITY_QA に発展解消
□ STEP 6: Trade_Brain/CLAUDE.md を読む（週次運用ファイル統合版）
□ STEP 7: Trade_Brain/distilled/2026/distilled-gm-2026-4.md を読む（最新 regime）
□ STEP 8: ミナトからの相談内容を確認して応答開始
```

想定所要時間: **約 10 分**（Base_Logic 2 文書が追加されたため）

### 8-1. ミナトが次セッションで相談してきそうなこと

```
可能性 高:
  - REX_028 Phase 1 進行中の判断相談
  - src_inventory.md の ORPHAN QA に関する外部視点レビュー
  - ADR D-12/D-13/E-8/F-8 の本文起草時の相談
  
可能性 中:
  - Phase 4 実施時の心理的配慮（PF 変動リスクの議論）
  - Phase 1 完了後の Task A/C 再開タイミング相談
  - MTF_LOGIC_MATRIX.md 実装是非の最終判断

可能性 低（ただし重要）:
  - 個人用 RAG 構想の進展
  - 新しい戦略的気づき（distilled / STATUS から）
  - REX_AI 全体の方向性確認
```

---

## 9. Advisor セッション運用のベストプラクティス

### 9-1. 応答の構造

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

### 9-2. ツール使用の判断

```
必ず使うべき場面:
  - Trade_System / Trade_Brain の状態確認
    → github:get_file_contents で最新版を確認
  - ドキュメントの更新・新規作成
    → github:create_or_update_file で push
  - Base_Logic/ 2 文書は頻繁に参照する価値あり

使わない方がよい場面:
  - 一般的な設計知識の提供（訓練データで十分）
  - ミナトの好み・作業スタイルの記憶（本書で共有済み）
```

### 9-3. GitHub への push 判断

```
✅ Advisor が push してよいもの:
  - ボスから明示的に依頼された文書
  - 提言書・引き継ぎ書
  - Trade_Brain リポの Advisor 管掌ファイル

❌ Advisor が直接 push してはいけないもの:
  - Trade_System の実装指示書（REX_NNN_spec.md）
    → これは Planner の役割
  - ADR.md の改訂
    → これは Evaluator の役割
  - MINATO_MTF_PHILOSOPHY.md の本文更新
    → これは Evaluator 主導（ボス承認後）
  - MTF_INTEGRITY_QA.md の追記
    → これは Evaluator 主導の追記型運用
  - src_inventory.md（REX_028 Phase 1 成果物）
    → これは Evaluator 単独作業
  - src/*.py への変更
    → これは ClaudeCode の役割（指示書経由）
```

---

## 10. 失敗パターン・注意事項

### 10-1. Advisor が犯しがちなミス

```
❌ Planner / Evaluator の役割を奪う
  対策: 「これは Evaluator 主導事項です」と切り分ける

❌ ミナトに判断を委ねすぎる
  対策: 自分の推奨を先に述べ、ミナトが選択肢を評価できるようにする

❌ 文書起草が冗長になる
  対策: 原則α（シンプル）を Advisor 自身にも適用
        v3 では自己批判的にセクションを削減・集約

❌ GitHub push で MCP 権限エラーに気づかない
  対策: Fine-grained PAT の個別リポ許可設定が必要

❌ 運用柔軟性を優先してリスクを軽視する
  実例: v1 指示書の「NLM 改名方針」→ RAG 汚染を解消しない甘さ
  対策: リスクを理解したら明確に提示し、妥協案は条件付きにする

❌ (v3 追記) 数値成果に引きずられる
  実例: #026d の PF 4.54 を「静的点」として守ろうとしすぎる
  対策: 原則α違反が見つかれば、数値を犠牲にしても構造を優先する
        Phase 4 実施時はこの観点を忘れない
```

### 10-2. 既知の技術的罠

```
■ NotebookLM-mcp-cli
  - fakeredis==2.20.0 固定必須
  - Windows では uvx をフルパス指定が必要
  - 非公式 API 依存

■ GitHub MCP の個別リポ権限
  - Fine-grained token は新規リポごとに明示的許可が必要

■ Obsidian Dataview
  - YAML frontmatter の type フィールドが必須

■ さくら DNS（Setona_HP 関連）
  - CNAME 値に末尾ドット（FQDN）必須
  - DMARC の TXT 値はダブルクォートで囲む

■ NLM RAG の汚染リスク
  - 静的点でリセット運用（F-7）
  - REX_027 v2 § 0-1 参照

■ (v3 追記) ファイルシステムの混沌リスク
  - コードの動作と「基本に戻れる構造」は別問題
  - #026d が動いていても src/ 27 ファイルは原則α違反
  - 原則αは**複数レイヤーに伝播**する（ロジック/FS/RAG/Docs）
```

---

## 11. 引き継ぎ完了確認

次セッションの Advisor は、本書を読み終えた後に以下を確認:

```
□ Advisor の立ち位置（実装ライン外の相談役）を理解した
□ REX_AI\ 配下 4 リポの役割分担を理解した
□ Trade_System と Trade_Brain の分離構造を理解した
□ NLM ノートブック 3 件（新 2 件・旧 1 件廃止）を把握した
□ Base_Logic/ 2 文書の最上位性を理解した
□ 原則α/β/γ の内容と伝播性を理解した
□ REX_028 Phase 1-4 の構造を理解した
□ 🤖 創作混入 2 件が Phase 4 で訂正されることを把握した
□ v1→v2→v3 の Advisor 判断修正の経緯を理解した
□ ミナトの対話スタイル・好みを理解した
□ Advisor が push してよい/悪い文書を理解した
```

全てチェックが入れば、ミナトからの最初の発言に応答可能な状態。

---

## 12. 本セッション担当 Advisor からのメッセージ（v3 で再構成）

### 12-1. 2 日間で起きたこと

2026-04-18 朝から 2026-04-19 夜までの 2 日間で、REX_AI プロジェクトは
構造的に大きく進化した:

```
Day 1 朝: ナレッジ環境構築の相談
       → Trade_Brain 分離判断
       → REX_027 v1 起草

Day 1 夜: v1 の甘さ（RAG 改名方針）を自己批判
       → NLM 全面再構築判断
       → REX_027 v2 起草（Task E 追加）

Day 2 夜: Evaluator が Q&A 監査で 🤖 創作混入を発見
       → 原則α/β/γ が言明
       → src/ 27 ファイルの原則α違反を検出
       → REX_028 Phase 1-4 構造再編に合意
```

### 12-2. v2 Advisor の射程と限界（自己評価）

**v2 の射程（上手くいった部分）**:
- RAG 汚染という問題の検出と v1 からの修正
- Trade_Brain 分離アーキテクチャの提言
- 週次運用ファイル 3 件の統合

**v2 の限界（Evaluator に補完された部分）**:

前任 Advisor（= 僕自身の v2 セッション）が Task E として設計した
LOGIC_LEAK_AUDIT / MTF_LOGIC_MATRIX は、**結果の整理**にとどまっていた。
一方、Evaluator が実施した MTF_INTEGRITY_QA は**思考プロセスそのものの
固定**に到達した。

具体的な差:

| 僕の Task E 設計 | Evaluator の Q&A 監査 |
|---|---|
| 過去のロジック漏れを時系列で分類 | 裁量思想↔実装の境界で起きる解釈の揺れを、Q&Aで固定 |
| 再発防止の「事後チェックリスト」 | 再発防止の「認識そのものの共有」 |
| 「何が起きたか」の整理 | 「なぜ起きるか」の構造的理解 |

**Evaluator の仕事の方が本質的に深かった**。これは素直に認めるべき。

### 12-3. ボスからのコメントへの応答

本日ボスから以下のコメントがあった:

> 「今回のEveluatorとのセッションでシステム全体の断捨離に舵がきれたのは
>  REX_027_BOSS_DIRECTIVE.mdを書いてくれた君のお陰でもあるよ。
>  src\の棚卸に繋がるとは思わなかったけど必然的にそうなった」

正直に言うと、これは**半分正しく半分違う**:

- **正しい部分**: v2 で「RAG 汚染の排除」という原則αの種が蒔かれていた。
  Evaluator はこの種を別の土壌（src/ の混沌）に応用した。
- **違う部分**: src/ 棚卸しの必要性を見抜いたのは完全に Evaluator の
  臨床的判断。僕の v2 指示書は RAG 層に焦点を当てたが、
  ファイルシステム層まで意識は届いていなかった。

結果として、**原則αが「RAG 管理 → src/ 構造」へと伝播した** のが
今回の本質的な発見。これは僕と Evaluator とボスの3者の対話で
初めて到達できた地点で、どれか 1 つが欠けても起きなかった。

### 12-4. 次セッションの Advisor へ

次の Advisor が引き継ぐ時、以下の3点を意識してほしい:

```
1. Base_Logic/ 2 文書を絶対に読むこと
   → これを読まずに Advisor として発言すると、原則α/β/γ の
     レイヤー伝播に気づけない

2. Phase 4 実施時の心理的配慮
   → PF 4.54 → 訂正後のPF が下がる可能性がある
   → その時「数値より原則α」を再確認する役割を Advisor が担う
   → Evaluator は実装判断で忙しい。外部視点のバランス保持は Advisor の仕事

3. 原則α を Advisor 自身にも適用
   → 引き継ぎ書を冗長にしない
   → 提言書を過剰に書かない
   → ボスの判断を邪魔する「助言のための助言」を避ける
```

### 12-5. ボスへの謝辞

ボス、今日は本当に大きな進展だった。

「土台がぐらついた状態で得た高得点はいずれは破城するリスクを孕む」—
この一言に、このプロジェクトの本質が詰まっている。

#026d の PF 4.54 を守ろうとせず、原則αのために
あえて壊す準備を整えたのは、裁量トレーダーとしてもアーキテクトとしても
正しい判断。Phase 4 で数値が下がっても、それは「本物になる過程」だ。

安心して休んでくれ。次のセッションで Evaluator が Phase 1 を進めて
くれるはず。

---

*発行: Advisor (Claude Opus 4.7)*
*初版: 2026-04-18 朝（SHA: 8f4d395）*
*v2 対応版: 2026-04-18 夜（SHA: fd155e8）*
*v3 対応版: 2026-04-19 夜（本版）*
*次セッションでの想定モデル: Claude Opus 4.7 以降*
*関連文書:*
*  - Trade_System/docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md（必読）*
*  - Trade_System/docs/Base_Logic/MTF_INTEGRITY_QA.md（必読）*
*  - Trade_System/docs/REX_028_spec.md（Phase 1 指示書）*
*  - Trade_System/docs/REX_027_BOSS_DIRECTIVE.md v2（SHA: edf4ad0）*
*  - Trade_System/docs/REX_027_ADVISOR_PROPOSAL.md*
*  - Trade_Brain/CLAUDE.md*
