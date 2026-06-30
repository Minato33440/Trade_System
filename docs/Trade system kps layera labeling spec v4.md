# Trade_System ── KPS 整理仕様（層A ラベリング ＋ 層B governance）

> v4 / 2026-06-30
> 対象: `C:\Python\REX_AI\Trade_System`（純マルチAgent Tradeアルゴ開発リポ・開発段階）
> 親教材: [[Knowledge_Production_System_lecture_v2]] / [[Local orchestration lecture]]

> **v4 変更点（実態反映）**
> - 実行順が計画と逆転 ── 緊急度から **層B governance(D-1/D-2)を先に完了**、層A(領域ヘッダ・scratch/・領域マップ節)は**未着手**。§0.5 実施状況を新設。
> - **D-1 の実態を修正** ── 本丸は `.CLAUDE.md` ではなく **`REX_BRAIN_SYSTEM_GUIDE.md`**(汚染NLMを現役クエリ先として案内)。退避＋`SYSTEM_OVERVIEW.md` のdangling 1行除去で解決。
> - **§1 Vault行を訂正** ── REX_System_Brain=`da84715f`(Trade_System用・現状空) / REX_Trade_Brain=`4abc25a0`(姉妹リポ用)。
> - **archive 慣行を記録** ── 旧版退避先は `logs/archive/`。governance整理ログは `logs/claudecode/maintenance_log.md`(新設チャンネル)。
> - **D-3 を選別方針へ** ── 標準役割権威は除去・歴史的帰属は温存。

---

## 0. この仕様の約束（境界）

- **層A ＝ add-only**（領域ヘッダ付与・`scratch/`新設・領域マップ節追加・`CLAUDE.md`シム化）。既存canonの中身は触らない。
- **層B ＝ 中身改訂・除去**（昇格判定経由・1件ずつ・改訂前に現物を `logs/archive/` へ凍結退避）。
- 適用はボスの **GitHub MCP 経路**で（リポ規約: MCP接続セッションの filesystem write は禁止）。本書は設計図、実書込はボス。

---

## 0.5 実施状況サマリ（2026-06-30 時点）

| 項目 | 状態 | 備考 |
|---|---|---|
| **D-1** 汚染NLM遮断 | ✅ **完了** | `REX_BRAIN_SYSTEM_GUIDE.md` → `logs/archive/` 退避 ＋ `SYSTEM_OVERVIEW.md` のdangling 1行除去。AGENTS.md は元から正記載 |
| **D-2** governance単一源化 | ✅ **完了** | `AGENTS.md`=源（中立化・`logs/claudecode`パス修正・思考フラグ表撤去）／`CLAUDE.md`=`@AGENTS.md`シム／`.CLAUDE.md`=削除。旧全文は `logs/archive/` へ |
| **D-3** 役割地の文除去 | 🔶 **一部** | AGENTS.md チーム表は撤去済。docs/配下の Rex-Advisor/Planner/Evaluator(著者・QA帰属)は**継続**（§6 D-3・選別方針） |
| **D-4** Handover退避 | ⬜ 未着手 | `Handover.md`（旧UCAR_Dialyパス）→ `logs/archive/` |
| **D-6** 週次系除去 | 🔶 一部 | `.CLAUDE.md`週次節は削除で消滅／`REDIUM.md`・`logs/gm`参照は**残**（要除去） |
| **層A** 領域ヘッダ付与 | ⬜ 未着手 | §3 雛形を docs/直下・凍結src・coordination に貼る |
| **層A** `scratch/` 新設 | ⬜ 未着手 | §4 |
| **層A** AGENTS.md 領域マップ節 | ⬜ 未着手 | §5-3。現AGENTS.mdは「セッション開始手順＋docs参照ルール」で代替中（明示の領域マップは未挿入） |

> 新設済みインフラ: **`logs/claudecode/maintenance_log.md`**（governance整理オペの時系列ログ・append-only）／**`logs/archive/`**（旧版凍結退避先）。

---

## 1. 領域分類（単一ドメイン: アルゴ開発）

| 領域 | 実体 | 所有 / 手 |
|---|---|---|
| **canon**（確定） | `docs/` 直下（ADR.md・EX_DESIGN_CONFIRMED.md・PLOT_DESIGN_CONFIRMED・SYSTEM_OVERVIEW・LOGIC_CONSISTENCY_MATRIX・REX_026d/028_spec・BRANCH_MAP・src_inventory）＋ 確定パラメータ(#026d)＋ **凍結src**（backtest/entry/exit/swing.py） | 単一所有スロット（昇格判定経由） |
| **coordination**（追記） | `logs/claudecode/instructions/`＋`execution_results/`＋`maintenance_log.md` | append-only。`INDEX.md`=実装ループ索引／`maintenance_log.md`=整理オペlog |
| **scratch**（隔離） | 現状なし → **新設** `scratch/grok\|gpt\|claude/` | engine別私的 |
| **Vault**（横断・長期） | `REX_Brain_Vault/bridges/trade_system/`＋NLM | Curator（最上段）。開発段階では軽め |

**NLM（AGENTS.md 外部リソース参照先と一致）:**
- `REX_System_Brain` = `da84715f-9719-40ef-87ec-2453a0dce67e` ← **Trade_System 用・現状空（RAG未稼働）**
- `REX_Trade_Brain` = `4abc25a0-4550-4667-ad51-754c5d1d1491` ← 姉妹リポ Trade_Brain 用
- 旧 `REX_Trade_Brain (2d41d672-…)` = RAG汚染・MCP切離済（D-11）。死亡注記としてのみ残す

**scope外**: regime判定・GM週次・distilled（Trade_Brain領分）／ Trade_Brain×Trade_System 統合（→§8 将来 Vault層）。

### KPS外（ラベル不要）
`src/`（非凍結コード）, `data/`, `tests/`, `node_modules/`, `.venv/`, `package.json`, `install.cmd`, `*.code-workspace`, `Rex_Prompt..txt`

---

## 2. ドリフト検出と状態

| # | 深刻度 | 内容 | 解決 | 状態 |
|---|---|---|---|---|
| **D-1** | 🔴 | **`REX_BRAIN_SYSTEM_GUIDE.md`** が汚染NLM`2d41d672`を「現役クエリ先」として案内（pre-migration・旧役割同居） | `logs/archive/`退避＋`SYSTEM_OVERVIEW.md`dangling除去 | ✅完了 |
| **D-2** | 高 | governance3重化（AGENTS/CLAUDE/.CLAUDE が別内容） | AGENTS.md源＋CLAUDE.mdシム＋.CLAUDE.md削除 | ✅完了 |
| **D-3** | 高 | 旧役割（Advisor/Planner/Evaluator）が地の文で焼かれている | 標準役割権威は除去・歴史帰属は温存（選別） | 🔶一部 |
| **D-4** | 中 | `Handover.md` が旧パス(`UCAR_Dialy`)を指す歴史スナップショット | `logs/archive/`へ | ⬜ |
| **D-6** | 中 | Trade_Brain週次系の紛れ込み（`REDIUM.md`／`logs/gm`参照） | Trade_System から除去 | 🔶一部 |

> ※ v3で D-1 を「`.CLAUDE.md`の汚染NLM」と誤同定していた。実物スイープで本丸は `REX_BRAIN_SYSTEM_GUIDE.md` と判明・訂正。`.CLAUDE.md` は別件（重複dotfile）で D-2 にて削除。

---

## 3. 領域ヘッダ雛形（層A・add-only / 各ファイル冒頭に貼る）※未着手

HTMLコメント形式 ── レンダリングに出ず、生テキストを読むengineには見える。canon本文を汚さない。

### canon（docs/直下・凍結src）
```
<!-- KPS-REGION: canon
     所有: 単一所有スロット（substrate管理） / 書込: 昇格判定(ボス承認)経由のみ
     読み方: 確定事実。全engineはこれに従う。
     ※ canonの権威はこの内容そのものにある（誰が確定したかは問わない） -->
```

### coordination（logs/claudecode/）
```
<!-- KPS-REGION: coordination
     性質: append-only・書き換え禁止 / 全engineが追記可
     velocity対策: 高頻度追記は World_Tracker パターン（日付partition + SHA1 dedup）に倣う
     ※ ここは"作業の痕跡"。確定していない（canonではない） -->
```

### scratch（scratch/<engine>/）
```
<!-- KPS-REGION: scratch（engine隔離）
     所有: 各engine私的 / 他engineは読まない（声隔離）
     ※ 供給viewに他engineのscratchを混ぜないこと（声隔離は供給バルブ側で強制） -->
```

---

## 4. `scratch/` 新設（層A・add-only）※未着手

```
Trade_System/scratch/
├── README.md
├── grok/      （.gitkeep）
├── gpt/       （.gitkeep）
└── claude/    （.gitkeep）
```

`scratch/README.md`:
```
# scratch/ — engine別 隔離作業区画（KPS: scratch）

- 各engineは自分のサブフォルダにのみ書く（grok/ gpt/ claude/）
- 他engineのサブフォルダは読まない（声隔離＝多様性の保存）
- ここは私的下書き。確定は canon、共有作業は coordination へ
- 昇格(canon化)は昇格判定（和解→ボス承認）を経る。直接 canon に書かない
```

> 注: scratchフォルダを切るのは"整理"であって、声隔離を**強制しない**。声隔離を効かせる実体は供給viewの組成規則（他engineのscratchをviewに混ぜない）＝バルブ側。

---

## 5. Governance ファイル構成（確定形・D-2で適用済）

### 5-1. AGENTS.md は2階層（混同しない・両方読む）

| 階層 | 場所 | 役 | KPS | 扱い |
|---|---|---|---|---|
| **Profile AGENTS.md** | `Hermes\Profile\<engine>\` | engineの**人格・常時ルール**。project非依存 | Profile Memory（隔離） | 本リポ管理外（各Profile側） |
| **Project AGENTS.md** | `Trade_System\AGENTS.md` | この**仕事場のcanon地図**。engine非依存 | Project canon の索引 | 本書が扱う |

### 5-2. 誰がどう読むか（源は1枚・入口2系統）※適用済

| engine | harness | 到達経路 |
|---|---|---|
| grok | Hermes gateway | Hermes dir-scope **注入** → AGENTS.md |
| codex | Hermes gateway | Hermes dir-scope 注入（＋Codex native）→ AGENTS.md |
| claude（gateway） | Hermes管理engine（ACP-Hermes-Desktop） | Hermes dir-scope **注入** → AGENTS.md |
| ClaudeCode（自走harness・端末実装） | ローカル起動 | root `CLAUDE.md` → `@AGENTS.md` → AGENTS.md |

```
                       ┌──────────────────────────────┐
Profile AGENTS.md ───▶ │ grok / codex / claude(gateway) │─[Hermes dir-scope 注入]─┐
(人格・隔離/Profile側)   └──────────────────────────────┘                        ▼
                                                                   Trade_System\AGENTS.md
                        ┌───────────────────────┐                  (Project canon・唯一の源)
                        │ ClaudeCode-native(実装) │─[root CLAUDE.md ─@AGENTS.md→]─┘
                        └───────────────────────┘        （シム＝同一canonへの配管・新情報ゼロ）
```

> 注入境界は **課金方式でなく harness が決める** ── Hermesがloopの主(gateway)ならAGENTS.md注入が効く（APIでも）。ClaudeCodeが自走harnessのときは注入が届かず、シムが配管になる。

### 5-3. Project AGENTS.md に入れる「領域マップ＋整合チェック」節（判事不可視）※未挿入

> 現AGENTS.mdは「セッション開始手順＋docs参照ルール」で代替中。明示の領域マップを足すなら下記（任意・層A）。

```
## KPS 領域マップ（どこに何があるか・全engine共通）
- canon（従うべき確定事実）       : docs/直下 + 凍結src
- coordination（作業ログ・追記のみ）: logs/claudecode/（指示書・結果・maintenance_log）
- scratch（各自私的・他engineは読まない）: scratch/<自分のengine名>/
  ※ 本リポはアルゴ開発専用。regime / 市況 / 週次 は扱わない（Trade_Brain の領分）。

## 開始時 整合チェック（必須・作業前）
1. EX_DESIGN_CONFIRMED.md / INDEX.md（canon索引）が指す実ファイルが存在・最新か
2. 凍結src の git diff がゼロか
3. logs の最新結果が canon「最終更新」より後でないか（後なら canon未反映＝drift）
→ 判定を「整合」/「要更新:〈食い違い〉」で明示。要更新ならボス承認後に本作業。
```

### 5-4. `CLAUDE.md` シム ※適用済
```
# CLAUDE.md — REX AI Trade System
# Project canon は AGENTS.md に単一ソース化。ClaudeCode はこのファイル経由で読む。
@AGENTS.md
```
> 将来 ClaudeCode-native を引退させ実装も gateway に寄せたら → CLAUDE.md は削除可。

### 5-5. claude固有の道具は `.claude/` へ
`.claude/`（`agents/ commands/ skills/`・現状空）は claude私的の道具置き場。skill/command/subagent はここへ。**governance memory は置かない**（ClaudeCodeの自動ロードは root）。

---

## 6. 層Bキュー（残り・昇格判定経由・1件ずつ・改訂前に `logs/archive/` へ凍結退避）

完了: ~~D-1~~ ✅ ／ ~~D-2~~ ✅

1. **D-3（継続・選別）**: docs/配下の `Rex-Advisor/Planner/Evaluator`。**全置換ではなく選別**：
   - **標準役割権威**（生きた権限表・「Evaluator承認後のみ」等の地の文）→ 中立化（ボス承認/昇格判定へ）
   - **歴史的帰属**（日付き仕様の「作成:Rex-Planner/監査:Rex-Evaluator」、`MTF_INTEGRITY_QA.md`等の追記型QA対話の発言者）→ **温存**（coordination同様の履歴。書き換えは記録破壊）
   - 対象候補: `ADR.md` / `EX_DESIGN_CONFIRMED.md` / `REX_026d/028_spec` / `LOGIC_CONSISTENCY_MATRIX` / `SYSTEM_OVERVIEW`（生きた権限記述があれば）。`Base_Logic/*`・`logs/*` は履歴側
2. **D-6（継続）**: `REDIUM.md` ＋ `logs/gm` 参照を Trade_System から除去（`logs/archive/` へ）。Trade_Brain領分の純化
3. **D-4**: `Handover.md` → `logs/archive/`（「歴史記録」と明記）
4. （随伴）`logs/archive/` の参照禁止運用を維持（正しい archive 衛生）

各件: **ボス承認 → `maintenance_log.md` に追記 → canon改訂**、の昇格判定で。

---

## 7. 残りの適用手順（ボス側）

1. **層A**（任意の順）: §3 領域ヘッダ付与 ／ §4 `scratch/` 新設 ／ §5-3 領域マップ節を AGENTS.md へ挿入 ── すべて add-only・GitHub MCP
2. **層B**: §6 を D-3継続 → D-6 → D-4 の順で（各件 maintenance_log 追記）
3. 各着手後にスイープで検証（汚染ID/旧パス/governance重複/dangling）

---

## 8. 将来拡張（scope外・備忘）

Trade_System が**リアルトレードとして機能した段階**で、`REX_BRAIN_VAULT` 上に **Trade_Brain × Trade_System 統合運用環境を別途構築**：
- 越境 regime（Trade_Brain所有・distilled）を決済判断へ供給（生産者所有・消費者読み・Vault bridge・鮮度タグ live/stale）
- 統合の Memory Broker は **Vault層（substrate）** に置く（上位Hubが両canonを束ねる）

**この統合は本リポ設計に含めない。** Trade_System は今、純アルゴ開発の単一ドメインとして閉じる。

---

*到達: D-1/D-2 完了で governance は「源1枚(AGENTS.md)＋シム(CLAUDE.md)、汚染NLM遮断、整理ログ(maintenance_log)」に収束。*
*残: D-3継続(選別)・D-6・D-4・層A(ラベル/scratch/領域マップ)。canon の事実は1バイトも壊さず進める。*