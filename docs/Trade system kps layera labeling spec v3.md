# Trade_System ── KPS 層A ラベリング仕様（マルチAgent Tradeアルゴ開発リポ）

> v3 / 2026-06-28
> 対象: `C:\Python\REX_AI\Trade_System`
> 位置づけ: **純粋なマルチAgent Tradeアルゴ開発リポ**（システム開発段階）
> 親教材: [[Knowledge_Production_System_lecture_v2]] / [[Local orchestration lecture]]

> **v3 変更点（governance 確定）**
> - §5 を全面再構成 ── **governance ファイル構成の確定形**を明文化。
> - **AGENTS.md は2階層**（Profile=人格・隔離 / Project=現場canon）。混同しない・両方読む。
> - **源は `Trade_System\AGENTS.md` 1枚**。gateway勢はHermes dir-scope注入で到達、ClaudeCode-nativeは **`CLAUDE.md`→`@AGENTS.md` シム**で同一canonへ自力到達。
> - §6 D-2/D-3 を確定方針で書き換え（3重化解消・役割地の文はProfileへ）。

---

## 0. この仕様の約束（層Aの境界）

- **層A ＝ add-only。** 既存ファイルの中身は1行も書き換えない。やるのは: (a) 領域ヘッダを*足す* / (b) `scratch/` を*切る* / (c) Project AGENTS.md に領域マップ節を*足す* / (d) `CLAUDE.md` を `@AGENTS.md` シムに*する*。
- **削除・改訂・役割の書き直し・週次log系の除去は全部 層B**（昇格判定経由・1件ずつ）。末尾「§6 層Bキュー」に積む。
- 適用はボスの **GitHub MCP 経路**で（リポ規約: Claude.ai/Codex.ai セッションの filesystem write は禁止）。本書は設計図で、実書込はしない。

---

## 1. 領域分類（単一ドメイン: アルゴ開発）

| 領域 | 実体 | 所有 / 手 |
|---|---|---|
| **canon**（確定） | `docs/` 直下（ADR.md・EX_DESIGN_CONFIRMED.md・PLOT_DESIGN_CONFIRMED・SYSTEM_OVERVIEW・LOGIC_CONSISTENCY_MATRIX・REX_026d/028_spec・BRANCH_MAP・src_inventory）＋ 確定パラメータ(#026d)＋ **凍結src**（backtest/entry/exit/swing.py） | 単一所有スロット（昇格判定経由） |
| **coordination**（追記） | `logs/claudecode/instructions/`＋`execution_results/` | append-only・全engine追記。`INDEX.md`は索引 |
| **scratch**（隔離） | 現状なし → **新設** `scratch/grok\|gpt\|claude/` | engine別私的 |
| **Vault**（横断・長期） | `REX_Brain_Vault/bridges/trade_system/`＋NLM(REX_System_Brain / REX_Trade_Brain=`4abc25a0`) | Curator（最上段）。開発段階では軽め |

**scope外（このリポでは扱わない）**: regime判定・GM週次・distilled（＝Trade_Brain の領分）／ Trade_Brain × Trade_System 統合運用（→ §8 将来 Vault層で別建て）。

### KPS外（ツール/設定・ラベル不要）

`src/`（非凍結＝実装対象コード）, `data/`, `tests/`, `node_modules/`, `.venv/`, `package.json`, `install.cmd`, `*.code-workspace`, `Rex_Prompt..txt`

---

## 2. ドリフト検出（→ 層Bキュー予告）

放置すると各engineが迷う/事故る食い違い。**全部 層B**（中身改訂・除去）なので層Aでは触らず §6 へ。

| # | 深刻度 | 内容 | 解決(→§6) |
|---|---|---|---|
| **D-1** | 🔴危険 | `.CLAUDE.md` が **RAG汚染で切離済みNLM `2d41d672`** を現役参照（正は`4abc25a0`） | .CLAUDE.md 削除 |
| **D-2** | 高 | ガバナンス3重化：`AGENTS.md`/`CLAUDE.md`/`.CLAUDE.md` が別々のチーム構成・日付・NLMを保持 | AGENTS.md源 + CLAUDE.mdシム + .CLAUDE.md削除 |
| **D-3** | 高 | 旧チーム構成（Advisor/Planner/Evaluator/実装＝単一モデル役割）が地の文で焼かれている。入口相対では古い | 役割地の文を Project canon から除去・人格は Profile へ |
| **D-4** | 中 | `Handover.md` が旧パス(`UCAR_Dialy`)・旧ファイルを指す歴史スナップショット | archived/ へ |
| **D-6** | 中 | **Trade_Brain 週次log系の紛れ込み**（`REDIUM.md`／`.CLAUDE.md`週次節／`logs/gm/`参照） | Trade_System から全除去 |

---

## 3. 領域ヘッダ雛形（層A・add-only / 各ファイル冒頭に貼る）

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

## 4. `scratch/` 新設（層A・add-only）

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

> 注: scratchフォルダを切るのは"整理"であって、声隔離を**強制しない**。声隔離を効かせる実体は §5-3 の供給viewの組成規則（他engineのscratchをviewに混ぜない）＝バルブ側。

---

## 5. Governance ファイル構成（確定形）

### 5-1. AGENTS.md は2階層（混同しない・両方読む）

| 階層 | 場所 | 役 | KPS | 本書での扱い |
|---|---|---|---|---|
| **Profile AGENTS.md** | `Hermes\Profile\<engine>\` | engineの**人格・常時ルール**（誰で・どう振る舞うか）。project非依存 | Profile Memory（隔離） | **本リポでは管理しない**（各Profile側） |
| **Project AGENTS.md** | `Trade_System\AGENTS.md` | この**仕事場のcanon地図**（canon所在・凍結・整合チェック）。engine非依存 | Project canon の索引 | **本書が扱う** |

人格(Profile)と現場(Project)は**どちらかではない。両方読む。** 性格だけで現場ルールを知らないengineは canon の所在が分からず迷う。

### 5-2. 誰がどう読むか（源は1枚・入口2系統）

| engine | harness | 到達経路 |
|---|---|---|
| grok | Hermes gateway | Hermes dir-scope **注入** → Project AGENTS.md |
| codex | Hermes gateway | Hermes dir-scope 注入（＋Codex native）→ Project AGENTS.md |
| claude（gateway） | Hermes管理engine（ACP-Hermes-Desktop） | Hermes dir-scope **注入** → Project AGENTS.md |
| ClaudeCode（実装役） | 自走harness（端末で main.py/rtk 等） | root `CLAUDE.md` → `@AGENTS.md` → Project AGENTS.md |

```
                       ┌──────────────────────────────┐
Profile AGENTS.md ───▶ │ grok / codex / claude(gateway) │─[Hermes dir-scope 注入]─┐
(人格・隔離/Profile側)   └──────────────────────────────┘                        ▼
                                                                   Trade_System\AGENTS.md
                        ┌───────────────────────┐                  (Project canon・唯一の源)
                        │ ClaudeCode-native(実装) │─[root CLAUDE.md ─@AGENTS.md→]─┘
                        └───────────────────────┘        （シム＝同一canonへの配管・新情報ゼロ）
```

**源は `Trade_System\AGENTS.md` 1枚。** gateway勢は注入で強制到達、ClaudeCode-nativeはシム経由で自力到達。届く先は1枚、経路が2系統。

### 5-3. Project AGENTS.md に入れる節（KPS領域マップ＋整合チェック・判事不可視）

> ここに **判事・席・和解は書かない**。各engineは「canonに従う・scratchに吐く」だけでよく、誰が蒸留しているかを知る必要がない（register最小・**権威はLLMでなくcanon**）。

```
## KPS 領域マップ（どこに何があるか・全engine共通）
- canon（従うべき確定事実）       : docs/直下 + 凍結src
- coordination（作業ログ・追記のみ）: logs/claudecode/（指示書・結果）
- scratch（各自私的・他engineは読まない）: scratch/<自分のengine名>/

  ※ 本リポはアルゴ開発専用。regime / 市況 / 週次 は扱わない（Trade_Brain の領分）。

## 開始時 整合チェック（必須・作業前）
1. EX_DESIGN_CONFIRMED.md / INDEX.md（canon索引）が指す実ファイルが存在・最新か
2. 凍結src の git diff がゼロか
3. logs の最新結果が canon「最終更新」より後でないか（後なら canon未反映＝drift）
→ 判定を「整合」/「要更新:〈食い違い〉」で明示。
  要更新なら更新案を出し、ボス承認を得てから本作業に入る。
```

### 5-4. `CLAUDE.md` シム（ClaudeCode-native 用の配管）

中身は実質1行。新canonを足さない＝**同一canonへの配管**。真実の源は AGENTS.md 1個のまま（単一所有を割らない）。

```
@AGENTS.md
```
（claude固有の数行が要るなら、この下に最小限だけ）

> 将来 ClaudeCode-native（端末実装役）を引退させ、実装も gateway に寄せたら → **CLAUDE.md は削除可**。残す理由は「ClaudeCode-native がまだ居るから」の一点。

### 5-5. claude固有の道具は `.claude/` へ

`.claude/`（`agents/ commands/ skills/` ── 現状空）は claude私的の**道具置き場**。skill / command / subagent はここに集約する。**governance memory（CLAUDE.md）はここに置かない**（ClaudeCodeの自動ロードは root。`.claude/CLAUDE.md`を読む少数説はあるが未確認 → 確実な root に置く）。

---

## 6. 層Bキュー（後で・昇格判定経由・1件ずつ・改訂前に現物を archived/ へ凍結退避）

1. **D-1**: `.CLAUDE.md` の汚染NLM参照(`2d41d672`)を除去 ── 下記 D-2 の `.CLAUDE.md削除`に統合して一掃 ── **最優先・安全寄り**
2. **D-2（governance 確定形へ）**:
   - `AGENTS.md`（root）= **Project canonical 源**。§5-3 の領域マップ＋整合チェックを内包
   - `CLAUDE.md`（root）= **`@AGENTS.md` シム**（§5-4）。実装役 ClaudeCode-native 用
   - `.CLAUDE.md` = **削除**（汚染NLM・重複）
3. **D-3**: 旧チーム構成テーブル（役割地の文）を **Project canon から除去** ── 人格は **Profile AGENTS.md（別レイヤー・各Profile側）** へ。全engine向け Project canon に "役割権威" を載せない（判事不可視）
4. **D-6**: **Trade_Brain 週次log系を全除去**（`REDIUM.md`／`.CLAUDE.md`週次節／`logs/gm/`参照を archive）。Trade_System を純アルゴ開発に純化
5. **D-4**: `Handover.md` → `archived/`（「202X年X月時点の歴史記録」と明記）
6. （随伴）`logs/docs_archive/` の "参照禁止" 運用は維持（正しい archive 衛生）

各件: **ボス承認 → coordination に追記 → canon改訂**、の昇格判定で。

---

## 7. 適用手順（ボス側）

1. 本仕様を確認・調整
2. 層A（§3ヘッダ・§4 scratch/・§5-3 Project AGENTS.md領域節・§5-4 CLAUDE.mdシム）を **GitHub MCP 経路で push**
3. 各engine（gateway勢＋ClaudeCode-native）が次セッションで同一 AGENTS.md に到達するか実機確認
   - 検証: `CLAUDE.md`無し・`AGENTS.md`だけの一時dirで claude gateway を起動し、AGENTS.md限定の事実を問う → 答えれば Hermes注入が効いている
4. 落ち着いてから §6 層Bキューを1件ずつ（D-1/D-2 から）

---

## 8. 将来拡張（scope外・備忘）

Trade_System が**リアルトレードシステムとして機能した段階**で、`REX_BRAIN_VAULT` 上に **Trade_Brain × Trade_System の統合運用環境を別途構築**する。そこで初めて：

- **越境 regime**（Trade_Brain 所有・distilled）を Trade_System の決済判断へ供給（生産者所有・消費者読み・Vault bridge・鮮度タグ live/stale）。
- 統合運用の Memory Broker は **Vault層（substrate）** に置く ── 個別リポではなく上位 REX_BRAIN_VAULT が両者の canon を束ねる Hub になる。

**この統合は本リポの設計には含めない。** Trade_System は今、純粋にアルゴ開発の単一ドメインとして閉じる。

---

*層Aが通れば、Trade_System は「単一モデルの地層を残したまま、マルチAgentが迷わない領域ラベルと、源1枚(AGENTS.md)に2系統で収束する governance を持つ、純アルゴ開発リポ」になる。*
*canon の事実は1バイトも触らず、住所表示・scratch・配管だけが増える ── 非破壊で骨が通る。*