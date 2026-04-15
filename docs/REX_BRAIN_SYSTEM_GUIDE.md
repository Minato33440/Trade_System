# REX_BRAIN_SYSTEM_GUIDE.md
# Planner / Evaluator 向け — セカンドブレインシステム利用ガイド
# 作成: 2026-04-15 / 管理: REX_Brain_System（Minato）

---

## このファイルの目的

新スレッド開始時に Planner / Evaluator が読むことで、
「どこに何があるか」「設計判断に迷ったらどこを調べるか」を
ゼロから説明し直さずに把握できるようにする。

**所要時間: このファイルを読むだけで現状把握が完了する（約2分）。**

---

## 1. 何が使えるか

### REX_Trade_Brain（NotebookLM）
Claudeが直接クエリできる知識ベース。
設計文書5本が投入済みで、自然言語で設計の根拠や経緯を質問できる。

**接続方法**: Claude Desktop → connectors → notebooklm-mcp が有効なこと。
切れていたら Minato に `nlm login` を依頼する。

```
ノートブックID: 2d41d672-f66f-4036-884a-06e4d6729866
ノートブック名: REX_Trade_Brain
```

### REX_Brain_Vault（Obsidian wiki）
ローカル知識ベース。filesystem MCP でアクセス可能。

```
パス: C:\Python\REX_AI\REX_Brain_Vault\
```

---

## 2. REX_Trade_Brain に入っている5本のソース

| ソース | 更新日 | 何が分かるか | クエリの例 |
|---|---|---|---|
| **EX_DESIGN_CONFIRMED-2026-3-31** | 2026-03-31 | MTF戦略全体・エントリー/決済ロジック・#025完了版 | "neck_4hの半値決済条件は？" |
| **ADR-2026-04-14_2_2** | 2026-04-14 | 過去のバグパターン・設計方針F章（**最重要**） | "D-6は何の修正か？" / "F章の設計方針を教えて" |
| **SYSTEM_OVERVIEW 2026-3-26** | 2026-03-27 | ファイル構成・依存関係・凍結/拡張可能ファイルの区分 | "window_scanner.pyは変更してよいか？" |
| **PLOT_DESIGN_CONFIRMED-2026-3-31** | 2026-03-31 | プロット関数設計・mplfinance不変ルール | "addplotを使うべきか？" |
| **HP-DESIGN-CONFIRMED_6** | 2026-04-09 | セトナHP構築記録（HP専用・Trade Systemとは無関係） | （HPタスクの時のみ参照） |

---

## 3. 設計判断で迷ったら何を調べるか

```
STEP 1: ADR の F章（設計方針ガイド）を確認
        → 迷ったときの優先順位がF-1〜F-6で定義されている

STEP 2: ADR の A〜E章で類似バグ・過去判断を確認
        → 同じ地雷を踏まないために

STEP 3: EX_DESIGN の 3-5節（決済ロジック）を確認
        → neck定義・段階定義はここが唯一の正

STEP 4: 上記で解決しなければ Minato（ボス）に確認
```

**NLM クエリの使い方**:
スレッド開始時に巨大なMDを全部読み込む必要はない。
「ADRのF章の設計方針を要約して」「D-6の修正内容は？」と
NLM に聞けば該当箇所だけ取得できる。
**コンテキストを節約するためにNLMを積極的に使うこと。**

---

## 4. 現在の実装状況（2026-04-15時点）

```
#025 完了 ✅
  固定ネック原則確定（sh_vals.iloc[0]）/ 15件検出

#026a 実装中 🔴
  window_scanner.py に sh_4h / neck_1h カラムを追加
  → CSV再生成（15件 + 新カラム）
  
  重要確定事項（ADR D-6 / F-6 / E-6 参照）:
  ・neck_4h = 4H SH = 半値決済トリガー（段階2）
  ・neck_1h = 窓特定アンカー（決済トリガーではない）
  ・1H Swing n=3（n=2から変更確定 / ADR D-7）
  ・統一neck原則: neck = sh_before_sl.iloc[-1]（全TF共通）

#026b 未着手 ⬜
  exit_simulator.py 新規作成
  → CSV読み込み → manage_exit() → P&L算出
```

---

## 5. ファイル変更ポリシー（必読）

```
■ 凍結ファイル（変更禁止）
  backtest.py / entry_logic.py / exit_logic.py / swing_detector.py

■ 拡張可能ファイル（カラム追加・出力拡張はOK / ロジック変更は要Evaluator確認）
  window_scanner.py / plotter.py / structure_plotter.py

■ 新規作成（自由）
  exit_simulator.py（#026bで作成予定）
```

完全な定義は ADR F-4 参照。
**「このファイルを変更したら#018ベースラインが再現不能になるか？」が凍結判定基準。**

---

## 6. セッション終了時のルール（/wrap-up）

タスクが完了したら以下を実施してほしい（Minato との取り決め）:

### 6-1. 設計文書の陳腐化チェック

| 完了したタスク | 必要なアクション |
|---|---|
| **#026a 完了** | `EX_DESIGN_CONFIRMED-2026-04-xx.md` を新規作成 → NLM に追加 |
| **#026b 完了** | 同上（P&L結果を含む最新版） |
| **新しいバグパターン発生** | ADR に追記（Evaluator担当） |
| **新しい .py ファイルが追加された** | `SYSTEM_OVERVIEW-YYYY-MM-DD.md` を新規作成 → NLM に追加 |

**重要**: 既存のMDを編集してはいけない。常に新しいファイルを作成する。
旧バージョンは NLM に残り続けるため、クエリで参照できる。

### 6-2. NLM への追加手順

```
1. docs/ に新ファイルを作成
2. notebooklm source_add（source_type=file）で追加
   notebook_id: 2d41d672-f66f-4036-884a-06e4d6729866
3. wiki/trade_system/doc_map.md の投入済みテーブルを更新
   パス: C:\Python\REX_AI\REX_Brain_Vault\wiki\trade_system\doc_map.md
4. wiki/log.md に記録を追記
5. Second_Brain_Lab に push（自動化済み・GitHub MCP使用）
```

これが実行できない場合は Minato に「NLM への追加が必要」と伝えること。

---

## 7. 参照先マップ（早見表）

```
「何を知りたいか」          → 「どこを見るか」
─────────────────────────────────────────────────────
設計全体の現在地           → EX_DESIGN_CONFIRMED-2026-3-31.md
過去のバグを踏まないために  → ADR の A〜D章
設計判断の基準             → ADR の F章
ファイルの役割と変更可否   → SYSTEM_OVERVIEW / ADR F-4
プロット関数の仕様         → PLOT_DESIGN_CONFIRMED
neck/決済の正確な定義      → EX_DESIGN 3-5節 / ADR D-6 / F-6
#026aの実装詳細            → EX_DESIGN のSTEP 3 / ADR E-6
ClaudeCode向け不変ルール   → ADR 末尾「ClaudeCode向け不変ルール」
設計文書の現在の有効性     → doc_map.md（Vaultの wiki/trade_system/）
```

---

## 8. このシステムが解決している問題

従来の課題:
- EX_DESIGN / ADR / SYSTEM_OVERVIEW が別々に更新されてきたため、
  スレッド引き継ぎ時に「どのファイルが最新か」「どの記述が正しいか」が
  分からなくなるロジック破綻が起きていた

現在の解決策:
- 全設計文書を NLM に投入 → クエリで矛盾なく横断参照できる
- doc_map.md が「どのファイルが有効か」を一元管理
- 「不変×新規作成原則」でバージョン混乱を防ぐ

このシステムにより、スレッド開始時に大量のMDを読み込む必要がなくなり、
**NLMへのクエリ → 必要な情報だけ取得 → 実装に集中** というフローが実現できる。

---

*管理: Minato / REX_Brain_System*
*NLM追加日: 2026-04-15*
