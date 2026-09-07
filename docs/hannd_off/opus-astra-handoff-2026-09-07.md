<!-- KPS-REGION: canon / handoff（引き継ぎスナップショット・時点固定）
     用途: 長期ブランク後の再開・新スレッド引き継ぎ。作成時点の事実で固定する。
     更新: 上書きせず日付き新ファイルを追加（append型）。canon本体(docs/直下3枚)を上書きしない。 -->

# Trade_System 引き継ぎ ── 2026-09-07

> 作成: Claude Opus 5（元 Opus 4.7 統括 Evaluator）/ Claude Desktop・MCP セッション
> 対象: `C:\Python\REX_AI\Trade_System`
> 前提: 実装は **2026-04-20 以降停止**。以後は governance / KPS 整理のみ進行（〜07-02）。**約2ヶ月のブランクあり**。
> 本書の役割: 「今どこにいるか」「何が壊れているか」「次に何をするか」を1枚で復元する。

---

## 1. 三行サマリ

1. **実装は #026d（PF 4.54 / 勝率60% / +150.6p・10件）で凍結中**。数値は健全、以後1バイトも動いていない。
2. **止まっている間に governance が全面刷新された** ── 旧マルチAgent（Planner/Evaluator/Advisor）体制を撤去し、**AGENTS.md 源1枚 + Hermes Runtime-Hub マルチengine** 構成へ移行完了。
3. **次の一手は Phase 3（src/ 責務別ディレクトリ化）**。ただし着手前に **§5 のドリフト（特に D-A）** を潰すこと。

---

## 2. 実装の現在地

### 2-1. 数値（動かさない）

| 指標 | #018（旧・凍結ベースライン） | **#026d（現行）** |
|---|---|---|
| 総トレード | 20件 | **10件** |
| 勝率 | 55.0% | **60.0%** |
| PF | 5.32 | **4.54** |
| MaxDD | 14.9p | **35.8p** |
| 総損益 | +91.6p | **+150.6p** |

`#026 変遷`: PF 0.61(b) → 2.42(c) → **4.54(d)**
最終実行: 2026-04-17（`logs/coordination/execution_results/026d_result.md`）

### 2-2. 直近3件の確定ロジック（これが #026d の中身）

- **#026b** — `exit_simulator.py` 新規作成。`exit_logic.py` の `manage_exit()` は**使わない**（neck定義が旧版）。方式Bが正式決済エンジン（ADR D-8）
- **#026c** — 指値方式へ転換。`5M High >= neck_15m + 7pips` で指値約定（ADR D-9 / E-7）
- **#026d** — 4H構造優位性フィルター。`neck_4h >= neck_1h` でない候補を SKIP（ADR D-10）。3件除外され13→10件

### 2-3. 統一neck原則（全TF共通・#026a確定）

```python
sh_before = sh_vals[sh_vals.index < sl_ts]
neck = float(sh_before.iloc[-1])   # SL「以前」の最後のSH
```

| neck | 用途 |
|---|---|
| neck_15m | エントリートリガー（指値の基準値） |
| neck_1h | 窓特定アンカー（**決済トリガーではない**） |
| neck_4h | 半値決済トリガー（段階2） |

### 2-4. 既知の負債 ── 🤖 創作混入（最重要）

`exit_simulator.py` の **stage2 建値移動** と **stage3 1H実体確定** は、
ボスの裁量思想に無い**LLMの創作が混入した実装**（ADR D-12 / D-13 で認識のみ固定）。

> **#026d の PF 4.54 はこの創作込みの数値である。**

Phase 4（REX_029+）で裁量整合版へ再設計予定。訂正後は新PFが静的点として再記録される。

---

## 3. governance / KPS の現在地（ブランク中に進んだ分）

### 3-1. 何が変わったか

| Before（〜2026-04） | After（2026-06〜07） |
|---|---|
| Planner / Evaluator / Advisor の固定role分担 | **固定role分担なし**。ボスが作業ごとに差配 |
| AGENTS.md / CLAUDE.md / .CLAUDE.md の3重化 | **AGENTS.md 源1枚 + CLAUDE.md シム（@AGENTS.md）** |
| 単一LLM（Claude）前提 | **Hermes Runtime-Hub マルチengine**（grok / codex / claude gateway + ClaudeCode-native） |
| `logs/claudecode/` | **`logs/coordination/`**（全engine共有領域） |
| 汚染NLM `2d41d672` が現役案内 | 遮断済み。生ポインタ0件 |

### 3-2. KPS 3領域の物理化（完了）

| KPS領域 | 実体 | 所有 |
|---|---|---|
| **canon** | `AGENTS.md` + `docs/`直下（SYSTEM_OVERVIEW / EX_DESIGN_CONFIRMED / ADR）+ 凍結src | 単一所有・昇格判定（ボス承認）経由のみ |
| **coordination** | `logs/coordination/`（instructions / execution_results / INDEX / maintenance_log） | append-only・全engine共有 |
| **scratch** | `logs/scratch/{claude,codex,grok}/` | engine隔離・他engineは読まない（声隔離） |

> 注: 仕様書 v4 は `Trade_System/scratch/` を指定していたが、実装は **`logs/scratch/`** に置かれた（2026-07-02 maintenance_log で確定）。**実装が正**。

### 3-3. 整理オペの完了状況（maintenance_log 系統）

| # | 内容 | 状態 |
|---|---|---|
| D-1 | 汚染NLM遮断（`REX_BRAIN_SYSTEM_GUIDE.md` 退避） | ✅ 完了 |
| D-2a/b | governance 単一源化（`.CLAUDE.md` 削除・CLAUDE.md シム化） | ✅ 完了 |
| D-3 | role中立化（INDEX append・指示書ヘッダ・canon本体3枚） | ✅ ほぼ完了（§5 D-B に漏れ1件） |
| D-4 | `Handover.md` を `logs/archive/` へ | ⬜ **未着手**（root に残存） |
| D-6 | Trade_Brain週次系の除去 | 🔶 **物理は完了・記録が無い**（§5 D-F） |
| 層A | `logs/scratch/` 新設 | ✅ 完了 |
| 層A | KPS-REGION ヘッダ付与 | ⬜ **未着手**（canon 3枚に未付与） |
| 層A | AGENTS.md 領域マップ節 | 🔶 「logs/ 領域の分担」節で部分代替済み |

### 3-4. 判断の型（D-3 で確立・以後の整理はこれに従う）

> **生きた権限記述は中立化 / 歴史的帰属は温存**

- 中立化する: 承認権威・指揮フロー・未来動作の割当（「Evaluator承認後のみ」等）
- 温存する: 過去形の主語、日付き仕様の作成者名、ボス証言の引用、事故事例の担当者名
- canon の**事実**（neck定義・パラメータ・数値・失敗パターン）は**1バイトも触らない**

---

## 4. 次の一手（優先順）

### 第0手（着手前の必須・15分）── ドリフト解消

§5 の **D-A（INDEX.md の #026d ステータス）** を直す。これは canon索引と実ファイルの食い違いで、
次に入る engine が「#026d はまだ実装中」と誤認する。**最も安く・最も効く**。
ついでに D-B（ADR冒頭のrole残存）も同時に処理できる。

### 第1手 ── Phase 3: src/ 責務別ディレクトリ化

```
src/core/   backtest.py entry_logic.py exit_logic.py swing_detector.py
            window_scanner.py exit_simulator.py
src/viz/    plotter.py structure_plotter.py plot_scan_results.py
src/scan/   base_scanner.py
src/tests/  test_1h_coincidence.py verify_4h1h_structure.py
```

- 実装ロジック影響は**ゼロ**が完了条件（#026d 数値完全不変）
- **`plotter.py` の関数分割は実施しない**（両リポ共存保持・ADR F-8 派生原則・ボス判断済み）
- import パスの全数追従が本体作業

### 第2手 ── Phase 4: D-12/D-13 裁量整合版への訂正

- Phase 3 完了後推奨（構造が落ち着いてから中身を触る）
- stage2 建値移動 / stage3 1H実体確定 を裁量整合版へ再設計
- **PF が動く**。訂正後の新PFを静的点として再記録する

### 選択肢 ── Hermes Skill 実装（2026-05-21 起票分）

`REX_Brain_Vault/bridges/hermes/decisions/2026-05-21_skill_proposal_initial.md` に3案あり
（knowledge-evolution → adr-timeline → wiki-graph の順を提案）。

> ⚠️ **起票後に KPS 移行が入ったため、前提が変わっている**。着手するなら再評価から。
> 特に「logs/claudecode/」前提のパス記述は `logs/coordination/` に読み替えが要る。

---

## 5. 検出済みドリフト一覧（2026-09-07 スイープ結果）

> KPS §5-3「開始時 整合チェック」が本来検出すべきもの。着手前に確認。

### 🔴 D-A. INDEX.md が #026d を「実装中」のまま

| 場所 | 記載 |
|---|---|
| `logs/coordination/INDEX.md` | `#026d ... 🔴 実装中` / 結果一覧 `— 実装中 🔴 待ち` |
| 実物 | `026d_result.md` が **2026-04-17 に存在**・PF 4.54 記録済み |
| ADR / SYSTEM_OVERVIEW | **完了**として記載 |

→ canon索引 vs 実ファイルの食い違い。**engine を確実に誤誘導する**。最優先で解消。

### 🟠 D-B. ADR.md 冒頭に生きた role 記述が残存

```
## このファイルの目的
新スレッドを立てるたびに、設計者（Rex-Planner / Rex-Evaluator）は
コンテキストが薄くなり、…
```

D-3 で発行責任者・F章管轄・運用ガイドは中立化されたが、**冒頭の目的節が漏れている**。
歴史的帰属ではなく「新スレッドごとに Planner/Evaluator が立つ」と読める生きた記述。

### 🟠 D-C. maintenance の D-x が ADR D章と名前空間衝突

`maintenance_log.md` の D-1〜D-3（整理オペ）と `ADR.md` の D-1〜D-13（パラメータ設計ミス）が
**同じ「D-番号」空間**。engine が「D-3 を参照」と受けた時に曖昧。

→ 整理オペ側を **M-x** 等に切替（append-only なので過去は書き換えず、次エントリから採番変更＋注記1行）。

### 🟡 D-D. SYSTEM_OVERVIEW ツリーが実態とズレ

| 種別 | 対象 |
|---|---|
| 記載あるが**実在しない** | `main.py` / `configs/settings.py` / `logs/base_scan/` / `logs/structure_plots/` |
| 実在するが**未記載** | **`logs/scratch/`**（今回の核心新設） / `logs/debug/` / `logs/plots/` / `logs/png_data/` / `logs/text_log/` / root `README.md` / `Rex_Trade_Wiki/` / `Web_Tracker/` / `tests/` |
| docs/ 側 | 旧地層ファイル（BRANCH_MAP 等）前提の注記が残るが、実際は archive 済み |

### 🟡 D-E. ADR 末尾「ClaudeCode 向け不変ルール」の宛先名

AGENTS.md 側は「不変ルール（全作業共通）」に中立化済みだが、ADR 側の同内容が
**「ClaudeCode 向け」のまま**。grok / codex が「自分向けではない」と誤読しうる。見出し1行で解消。

### 🟡 D-F. D-6 は物理完了だが maintenance_log に完了記録が無い

`REDIUM.md` は root から消滅、`logs/gm/` も不在 → **D-6 は実質完了**。
しかし maintenance_log の最新エントリでは 🔶一部 のまま。記録側の drift。

### 🟡 D-G. canon 3枚のコードフェンス剥離（既知）

`SYSTEM_OVERVIEW.md` で実確認: ディレクトリツリーが `docs/` 行以降フェンス外に脱落（インデント消失）、
依存関係マップの行頭ずれ、F章抜粋の引用フェンス。次の canon touch 時にまとめて囲み直し。

### 🟡 D-H. AGENTS.md ヘッダ日付が実際より古い

ヘッダ `更新: 2026-06-29` だが、実際は D-2b（6-30）・D-3 と coordination パス追従（7-02）まで反映済み。

### 🟡 D-I. 仕様書 v4 が stale

`docs/Trade system kps layera labeling spec v4.md` の §0.5 は「層A 未着手」だが、
実際は `logs/scratch/` 新設済み（位置も変更）。**maintenance_log が正・spec v4 は歴史**。

### ⬜ D-J. Handover.md（D-4）が root に残存

旧 `UCAR_Dialy` パスを指す歴史スナップショット。`logs/archive/` へ退避が未着手。
（※本書がその後継にあたる）

---

## 6. 読む順序（新セッション）

```
1. AGENTS.md                              governance 正本（必読・源1枚）
2. README.md                              リポ入口導線
3. docs/hannd_off/（本書・最新の1枚）      現在地とドリフト
4. docs/SYSTEM_OVERVIEW.md                現状スナップショット
5. docs/EX_DESIGN_CONFIRMED.md            ロジック定義・パラメータ
6. docs/ADR.md                            失敗パターン + 設計方針ガイド（F章）
7. logs/coordination/maintenance_log.md   整理オペの時系列（最新の到達点）
8. docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md  裁量思想の最上位辞書
```

> grok / codex は Hermes dir-scope で AGENTS.md が自動注入される。
> ClaudeCode-native は root `CLAUDE.md`（@AGENTS.md シム）経由。

---

## 7. 迷った時の判断順序（ADR F-8）

```
1. F-5（設計判断優先順位）の5項目を確認
2. 原則α（シンプルな土台の保守）に反していないか？   → 反していれば却下
3. 原則β（ノーリスク化後は伸ばさない）に反していないか？ → 反していれば Phase 4 相当
4. 原則γ（導入タイミングは安定性従属）を満たすか？     → 満たさなければ保留
5. 裁量思想（MINATO_MTF_PHILOSOPHY）と対応するか？    → しなければ MTF_INTEGRITY_QA でQ&A
6. それでも迷えばボスに確認
```

**原則βの実例**: D-12（建値移動）/ D-13（1H実体確定）は「ノーリスク達成後に伸ばす操作」＝原則β違反として退けられた。だから Phase 4 は「機能追加」ではなく**訂正**。

---

## 8. 未解決・保留の全リスト

| 項目 | 状態 | 再開条件 |
|---|---|---|
| Phase 3 src/ 責務別ディレクトリ化 | ⬜ 未着手 | 指示書起草後 |
| Phase 4 D-12/D-13 裁量整合版訂正 | ⬜ 未着手 | Phase 3 完了後推奨 |
| #06 15M neck 検出バグ | ⬜ 未対応 | ボス目視指摘（#026b時） |
| 20260113_0545 TOPエントリー | NG確定 | 15M SH密集フィルターで対応予定 |
| IHS 0件化 | 設計上の既知制約 | Phase 2 で検討済・保留 |
| D-11 / F-7 採番予約 | ⬜ 空き番保持 | REX_027 再開時に記述 |
| Layer 1/3/5 残QA | 保留 | 原則γ（安定化後） |
| 層A KPS-REGION ヘッダ付与 | ⬜ 未着手 | 任意・add-only |
| D-4 Handover.md 退避 | ⬜ 未着手 | — |
| Trade_Brain × Trade_System 統合 | scope外 | **リアルトレード稼働後**・Vault層に構築 |

---

## 9. 触ってはいけないもの

### 凍結ファイル（変更禁止・完了条件に diff ゼロを必ず含める）

```bash
git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py
# → 差分ゼロであること
```

| ファイル | 凍結理由 |
|---|---|
| `src/backtest.py` | #018 ベースライン保持（PF 5.32） |
| `src/entry_logic.py` | 比較基準・他ファイルのAPI依存 |
| `src/exit_logic.py` | 旧決済保存・`manage_exit()` は**呼び出し禁止**（D-8） |
| `src/swing_detector.py` | 全ファイルの Swing 検出API基盤 |

### 分割してはいけないファイル

`src/plotter.py` ── 両リポ共存保持。Trade_Brain ルーツ3関数 + Trade_System ルーツ4関数が癒合したまま保つ。
将来の合流点（Trade_Brain レジーム判定 → Trade_System ロット調整）の橋。**Phase 3 でも分割しない**（ADR F-8 派生原則・ボス判断済み）。

### 編集経路（事故防止・過去に2回事故）

| 起動形態 | 編集ツール | コミット |
|---|---|---|
| ローカル実装（ClaudeCode 等の自走harness） | filesystem 直接 | `git pull --rebase` → commit → push |
| **MCP接続セッション（全engine）** | **GitHub MCP のみ** | `get_file_contents` で SHA → `create_or_update_file`（全文渡し） |

> MCP接続セッションで filesystem の `write_file` / `edit_file` は**禁止**（read系のみ可）。
> **1回失敗したら即停止してボスに報告**。連鎖試行で被害が拡大する（2026-04-23 の実例あり）。

### 領域の書き分け

- `logs/coordination/` は **append-only**。既存エントリを書き換えない
- `logs/archive/` `logs/docs_archive/` は **参照禁止**（旧版凍結退避先）
- 他 engine の `logs/scratch/` は**読まない**（声隔離）

---

## 10. 本書の運用

- 上書きしない。次の引き継ぎは `docs/hannd_off/` に**日付き新ファイル**を足す（append型）
- 本書は時点スナップショット。数値・構造の正は常に `docs/` 直下の canon 3枚
- §5 のドリフトを解消したら、解消分を maintenance_log に追記して本書の該当行を次版で落とす

---

*作成: 2026-09-07 / Claude Opus 5 / MCP セッション*
*canon 本体は1バイトも変更していない（本書は新規追加のみ）*
*配置先: Trade_System/docs/hannd_off/2026-09-07_handoff.md（ボス手動配置）*
