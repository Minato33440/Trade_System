# AGENTS.md — REX AI Trade System
# 更新: 2026-07-02（D-3: canon role中立化・logs/coordination リネーム追従・STEP3/結果パス修正・logs領域分担節追加。D-2b harness中立化は 6-30）
# このファイルは Project canon（全engine共有）。
#   - grok / codex … Hermes dir-scope で起動時に自動注入
#   - ClaudeCode  … root CLAUDE.md（@AGENTS.md シム）経由で読む
# 各engineはセッション開始時に必読。

---

## プロジェクト概要

USDJPY アルゴリズミック・トレーディングシステム（Minato流MTF短期売買）
データ: 83,112本 / 5M足 / 2024-03-13〜2026-03-13
戦略: 4H上昇ダウ継続中の押し目エントリー（窓ベース階層スキャン）

---

## 体制（最小）

- **最終判断**: Minato（ボス）
- **実装**: 各engine（Hermes gateway / ClaudeCode）
- **canon（ロジック・設計）の変更**: ボス承認（昇格判定）を経てのみ

> 役割・人格は各 Profile（Hermes\Profile\<engine>\）の管轄。本 Project canon には載せない（register最小・権威はcanon自身）。

---

## セッション開始手順

```
STEP 1: このファイル（AGENTS.md）を読む
        ← grok / codex は dir-scope 自動注入
        ← ClaudeCode は CLAUDE.md（@AGENTS.md シム）経由で読む
STEP 2: docs/ 直下のファイルを確認（最新版のみ存在するはず）
STEP 3: 指示書を確認（logs/coordination/instructions/ の該当ファイル）
STEP 4: 不明点があれば Vault の設計文書を参照
         パス: C:\Python\REX_AI\REX_Brain_Vault\
         または @notebooklm-mcp にクエリ（※ REX_System_Brain は現状空・RAG未稼働）
STEP 5: 不明点が解消しない場合はボスに報告して停止
```

---

## ❌ 凍結ファイル（変更禁止）

以下のファイルは絶対に変更しない。明示的な許可があっても慎重に。

```
src/backtest.py        — #018ベースライン保持（PF 5.32 / 55% / +91.6p）
src/entry_logic.py     — #018まで凍結
src/exit_logic.py      — #009以降凍結
src/swing_detector.py  — #020まで凍結
```

変更禁止の理由: これらは比較のベースラインや、他ファイルが依存するAPIを提供している。
変更するとベースライン数値が再現不能になるか、依存先が壊れる。

完了条件に必ず含めること:
```bash
git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py
# → 差分ゼロであること
```

---

## ⚠️ 拡張可能ファイル（機能追加OK・ロジック変更は要確認）

```
src/window_scanner.py   — カラム追加・出力OK / スキャンロジック変更は要ボス確認（昇格判定）
src/exit_simulator.py   — 方式Bとして独立運用 / exit_logic.pyと混同しない
src/plotter.py          — 表示機能の追加は自由
src/structure_plotter.py
```

---

## ✅ 新規作成（自由）

既存ファイルをimportして使うのはOK。既存ファイルの内部を書き換えるのはNG。

---

## 不変ルール（全作業共通）

```
1. 既存関数を呼ぶ前に必ず実ファイルの def 行を read する
2. 凍結ファイルは変更しない（上記4ファイル）
3. resample_tf は label='right', closed='right' で統一。変更禁止
4. mplfinance は returnfig=True パターンのみ
5. 全てのトレランスは pip ベース。PCT ベースは使わない
6. 指示書のコードをそのままコピペせず、実APIに合わせる
7. git diff で凍結ファイルの差分ゼロを完了条件に含める
8. エラーが出たら自分で「想像で」修正しない。ボスに報告して停止
9. window_scanner.py はカラム追加・出力OK。スキャンロジック変更は要確認
```

---

## logs/ 領域の分担
- logs/coordination/ … 実装ループ（instructions/ 指示書・execution_results/ 実行結果）＋整理オペ（maintenance_log）＋索引（INDEX）。全engine共有・append-only
- logs/scratch/<engine>/ … 各engineの検索/探索ログ（claude/codex/grok レーン別）
- logs/archive/ … 旧版canon/governance/設計文書の凍結退避（参照禁止）

---

## docs/ 参照ルール

```
docs/ 直下のファイルのみが「現在有効な設計」
  - EX_DESIGN_CONFIRMED.md   — 設計確定文書（最新版）
  - ADR.md                   — バグパターン集 + 設計方針ガイド
  - PLOT_DESIGN_CONFIRMED.md — プロット設計
  - SYSTEM_OVERVIEW.md       — ファイル構成・依存関係

logs/archive/ は旧版 canon・設計文書の保管庫 — 参照禁止
複数バージョンが docs/ にある場合はボスに報告して停止
```

---

## 確定パラメータ（#026d時点）

```python
# エントリー
DIRECTION_MODE      = 'LONG'
ALLOWED_PATTERNS    = ['DB', 'ASCENDING', 'IHS']
ENTRY_OFFSET_PIPS   = 7.0      # neck_15m + 7pips 指値方式（#026c確定）
MIN_4H_SWING_PIPS   = 20.0
LOOKBACK_15M_RANGE  = 50
MAX_REENTRY         = 1
PIP_SIZE            = 0.01
N_1H_SWING          = 3        # 1H Swing検出粒度（#026a-v2確定）

# 窓
WINDOW_1H_PRE       = 20
WINDOW_1H_POST      = 10
PRICE_TOL_PIPS      = 20.0

# プロット（窓と独立）
PLOT_PRE_H          = 25
PLOT_POST_H         = 40

# neck定義（統一neck原則 #026a確定）
# 全TF共通: neck = SL直前の最後のSH (sh_before_sl.iloc[-1])

# フィルター
# 4H構造優位性: neck_4h >= neck_1h（#026d確定）
```

---

## neck の用途定義

```
neck_15m — エントリートリガー（5M high >= neck_15m + 7pips で指値約定）
neck_1h  — 窓特定アンカー（決済トリガーではない）
neck_4h  — 半値決済トリガー（段階2: High >= neck_4h → 50%決済）
```

---

## 決済ロジック（4段階・exit_simulator.py 方式B）

```
初動SL: 15M ダウ崩れ → 全量損切
段階1:  5M ダウ崩れ → 全量決済（neck_4h未到達時）
段階2:  High >= neck_4h → 50%決済 + 残りストップを建値移動
段階3:  1H Close > 4H SH 確定後 → 15M ダウ崩れで残り全量決済

⚠️ exit_logic.py の manage_exit() は使わない（neck_1h/neck_4h定義が旧版）
   → exit_simulator.py の方式B（独自実装）が正式な決済エンジン

⚠️ stage2 建値移動 / stage3 1H実体確定は 🤖 創作混入確定（ADR D-12 / D-13）
   → Phase 4（REX_029 以降）で裁量整合版に再設計予定。本 ADR 採番時点では
     認識の固定のみ。#026d の PF 4.54 はこの創作込みの結果である。
```

---

## ファイル管理ルール

### 結果報告の出力先
```
logs/coordination/execution_results/REX_{番号}_result.md
```

### Git コミット手順（ローカル実装：ClaudeCode 等の自走harness向け）
```bash
# ⚠️ 必ず最初に実行（MCP経由pushと競合防止）
git pull --rebase

git add src/ logs/
git commit -m "Feat: #{番号} {内容}"
git push
```

**git pull --rebase が必須の理由:**
MCP経由セッションとローカル実装の両方からpushが発生するため、
pull なしで push すると diverge（分岐）が起きる。
rebase を使うことでコミット履歴をクリーンに保つ。

### コミットメッセージ規則
```
Phase A: "Phase A: ..."
バグ修正: "Fix: ..."
パラメータ調整: "Tune: ..."
新機能: "Feat: ..."
ドキュメント: "Docs: ..."
```

---

## 編集経路（重要・事故防止）

### 編集経路の分離

| 起動形態 | 編集ツール | コミット経路 |
|---|---|---|
| ローカル実装（ClaudeCode 等の自走harness） | filesystem 直接 | ローカル `git pull --rebase` → `git commit` → `git push` |
| MCP接続セッション（全engine） | **GitHub MCP のみ使用** | `get_file_contents` で SHA → `create_or_update_file`（content 全文渡し）|

### 運用前提（ボス確認）

- 全リポ（Trade_System / Trade_Brain / REX_Brain_Vault / Setona_HP / Second_Brain_Lab）が
  Git リポ化 + MCP 接続済み → 全書き込みは GitHub MCP 経由で完結する
- ボスは MCP接続セッション中にローカル実装を同時に動かさない（二系統 push の同時発生なし）
- セッション開始時は `nothing to commit, working tree clean` をボスが事前確認
- フローは「MCP接続セッションが GitHub MCP で push → ボスがローカルで pull」の単方向で完結

### MCP接続セッションの絶対ルール

GitHub MCP 接続リポ配下のファイルを **filesystem MCP の `write_file` / `edit_file`
で書き換えてはいけない**。

許容される filesystem MCP 操作（read 系のみ）:
- `read_text_file` / `read_multiple_files` / `read_file`
- `list_directory` / `get_file_info` / `read_media_file`

禁止される filesystem MCP 操作:
- `write_file` / `edit_file`（GitHub 接続リポでは事故の温床）

理由:
1. ボスが pull するタイミングを MCP接続セッション側が制御できない（diverge リスク）
2. `edit_file` は日本語 MD ファイルで連鎖失敗のリスク（過去事例参照）
3. GitHub MCP `create_or_update_file` の全文渡しなら文字化けバイト混入なく
   ファイル整合性が一括保証される

### 編集失敗時の停止ルール

**1 回失敗したら即停止してボスに報告**。連鎖試行で被害が雪だるま式に拡大する。
2 回目を試すならアプローチを変える（例: edit_file → 全文渡し push に切替）。
それでも失敗するならボスに報告して停止。

### 過去事故事例（歴史記録・教訓）

#### 2026-04-23: filesystem:edit_file 連鎖失敗による MTF_INTEGRITY_QA.md 末尾構造破損
- **当時の担当**: 第六代 Evaluator（Opus）
- **触発要因**: 過去セッションで残った文字化けバイト（\ufffd）が edit_file の oldText マッチを通らなかった
- **伝播経路**: 削除試行を 5 回以上連鎖 → 区切り線と見出しが消失 → 文書構造破損 → 次セッションで修復タスク発生
- **教訓**:
  - 日本語 MD ファイルの構造的修正は edit_file ではなく GitHub MCP `create_or_update_file` 全文渡しで行うこと
  - 1 回失敗で即停止する（連鎖試行禁止）

#### 2026-04-25: filesystem 経由ローカル編集による diverge リスク
- **当時の担当**: Advisor（Opus 4.7）
- **触発要因**: AGENTS.md 未読 + 編集経路が AGENTS.md に未記載
- **伝播経路**: filesystem:edit_file でローカルのみ編集 → リモート未反映 → ボスが git checkout で破棄 → GitHub MCP で push し直し
- **教訓**:
  - 全engineはセッション開始時に AGENTS.md を必ず読むこと（自動注入でない場合は手動で）
  - MCP接続セッションは filesystem write 系を使わず GitHub MCP のみ使うこと

---

## 推論深度の制御（harness側・canonには書かない）

推論の深さは各 harness 側で制御する。指示書ヘッダに思考フラグは書かない。
- **ClaudeCode**: `/effort low|medium|high|max`（恒久設定）。`ultrathink` は per-turn の簡易nudge
- **API（claude gateway 等）**: `output_config.effort` + `thinking:{type:adaptive}`（プロンプト内キーワードは無効）
- **grok / codex**: 各 provider 側の設定に従う（ClaudeCode キーワードは無効）

> 旧「思考フラグ表（think / think hard / think harder / ultrathink）」は ClaudeCode 専用かつ
> 2026-01 に階層が `/effort` へ刷新されたため、全engine共有 canon からは除去（D-2b）。

---

## 外部リソース参照先

```
Vault:      C:\Python\REX_AI\REX_Brain_Vault\（Git リポ化済み: Minato33440/REX_Brain_Vault）
NLM:        REX_System_Brain  (da84715f-9719-40ef-87ec-2453a0dce67e)  ← Trade_System 用（現状空）
            REX_Trade_Brain   (4abc25a0-4550-4667-ad51-754c5d1d1491)  ← 姉妹リポ Trade_Brain 用
            ※ 旧 REX_Trade_Brain (2d41d672-...) は RAG 汚染により MCP 切離済み（D-11 経由）
GitHub:     Minato33440/Trade_System
            Minato33440/Trade_Brain
            Minato33440/REX_Brain_Vault
            Minato33440/Setona_HP
            Minato33440/Second_Brain_Lab
```