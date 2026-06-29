# REX_BRAIN_SYSTEM_GUIDE.md
# Planner / Evaluator 向け — セカンドブレインシステム利用ガイド
# 作成: 2026-04-15 / 更新: 2026-04-16（要望1〜5対応）
# 管理: REX_Brain_System（Minato）

---

## このファイルの目的

新スレッド開始時に Planner / Evaluator が読むことで、
「どこに何があるか」「設計判断に迷ったらどこを調べるか」を
ゼロから説明し直さずに把握できるようにする。

**所要時間: このファイルを読むだけで現状把握が完了する（約3分）。**

---

## 0. セッション開始チェックリスト（必須）

スレッド開始時に以下を順番に実行すること。

```
□ STEP 0-A: NLM 認証チェック（⚠️ 最初に実行）
   notebook_list を試行する。
   → 成功: 通常通り作業開始
   → 認証切れエラー: ボスに「nlm login をお願いします」と伝えてから作業開始
   
   認証切れ時のフォールバック:
   - wiki/trade_system/pending_nlm_sync.md に「追加待ちソース」を記録
   - nlm login 完了後にまとめて source_add する

□ STEP 0-B: doc_map.md を読む
   wiki/trade_system/doc_map.md で「最新の有効設計文書」を確認
   → ⚠️ マークの文書は陳腐化済み（読み込まない・NLM にクエリする）

□ STEP 0-C: wiki/log.md の末尾5件を確認
   前回セッションからの変更点を把握

□ STEP 0-D: pending_changes.md を確認
   wiki/trade_system/pending_changes.md で「決まっているが未反映の変更」を把握
```

---

## 1. 何が使えるか

### REX_Trade_Brain（NotebookLM）

Claudeが直接クエリできる知識ベース。
設計文書が投入済みで、自然言語で設計の根拠や経緯を質問できる。

```
ノートブックID: 2d41d672-f66f-4036-884a-06e4d6729866
ノートブック名: REX_Trade_Brain
```

### REX_Brain_Vault（Obsidian wiki）

ローカル知識ベース。filesystem MCP でアクセス可能。

```
パス: C:\Python\REX_AI\REX_Brain_Vault\
主要ファイル:
  wiki/trade_system/doc_map.md        ← 設計文書状況
  wiki/trade_system/adr_reservation.md← ADR採番台帳（要望1対応）
  wiki/trade_system/pending_changes.md← 決定済み未確定変更（要望3対応）
```

---

## 2. REX_Trade_Brain に入っている設計ソース

| ソース | 更新日 | 何が分かるか | クエリの例 |
|---|---|---|---|
| **EX_DESIGN_CONFIRMED-2026-3-31** | 2026-03-31 | MTF戦略全体・エントリー/決済ロジック | "neck_4hの半値決済条件は？" |
| **ADR-2026-04-14_2_2** | 2026-04-14 | 過去のバグパターン・設計方針F章（**最重要**） | "F章の設計方針を教えて" |
| **SYSTEM_OVERVIEW 2026-3-26** | 2026-03-27 | ファイル構成・依存関係（部分陳腐化） | "window_scanner.pyは変更してよいか？" |
| **PLOT_DESIGN_CONFIRMED-2026-3-31** | 2026-03-31 | プロット関数設計・mplfinance不変ルール | "addplotを使うべきか？" |
| **REX_026d_spec** | 2026-04-15 | #026d 指示書（4H構造優位性フィルター） | "#026dの実装内容は？" |
| **REX_BRAIN_SYSTEM_GUIDE** | 2026-04-16 | このシステム自体の利用方法 | "セッション開始時に何をする？" |
| HP-DESIGN-CONFIRMED_6 | 2026-04-09 | セトナHP構築記録（HP専用） | （HP作業時のみ） |

---

## 3. 設計判断で迷ったら何を調べるか

```
STEP 1: ADR の F章（設計方針ガイド）を確認
STEP 2: ADR の A〜E章で類似バグ・過去判断を確認
STEP 3: EX_DESIGN の 3-5節（決済ロジック）を確認
STEP 4: pending_changes.md で「決まっているが未反映」を確認
STEP 5: 解決しなければボス（Minato）に確認
```

**NLM クエリの使い方**:
巨大な MD を全部読み込まず、必要な情報だけ NLM に質問する。
コンテキストを節約するために NLM を積極的に使うこと。

---

## 4. ADR 採番ルール（要望1対応）

**新しい ADR 番号（D/E/F カテゴリ）を使う前に必ず確認:**

```
1. wiki/trade_system/adr_reservation.md を開く
2. 使いたいカテゴリの「次の番号」を確認
3. 予約エントリーを追加（担当者・トピック・ステータス=予約）
4. その後、実装・ドラフト作成を開始

未予約番号の使用は採番衝突とみなす。
採番権限: D/E/F = Evaluator 最終決定 / A/B/C = Planner 追記可
```

---

## 5. 設計変更の記録フロー（要望3対応）

**設計判断が確定したとき（タスク完了前でも）:**

```
1. pending_changes.md に決定事項を追記
   → ステータス: 🔴 実装中 or 🟡 検討中

2. タスク完了後:
   a. adr_reservation.md でドラフト番号を「確定」に更新
   b. 新しい設計確定 .md を作成（不変原則）
   c. NLM に source_add
   d. pending_changes.md のステータスを「✅ 完了」に更新
   e. doc_map.md の陳腐化トリガー処理
```

---

## 6. /wrap-up フロー（セッション終了時）

以下を順番に実行すること:

```
□ STEP 1: wiki/log.md に今日の決定事項・完了タスクを追記
□ STEP 2: wiki/trade_system/pending_changes.md を更新
□ STEP 3: wiki/trade_system/adr_reservation.md を更新
□ STEP 4: wiki/handoff/latest.md を更新（次スレ用引き継ぎプロンプト）
□ STEP 5: NLM に新規ソースを追加（認証切れなら pending_nlm_sync.md）
□ STEP 6: Second_Brain_Lab に GitHub push
□ STEP 7: ★ Claude.ai プロジェクトに添付ファイルをアップロード（要望4）
           新しい設計確定 .md や更新した ADR があれば手動でアップロード
           旧版は「ARCHIVED_xxxx」とリネームして管理
```

**STEP 7 注意**: Claude.ai プロジェクト添付はAPIで自動化できないため手動。
更新頻度の高い文書（EX_DESIGN / ADR）が対象。

---

## 7. Lint 運用（要望5対応）

**タスク完了時 + 週次 に以下を実行:**

### Lint-1: ADR 採番整合チェック

```
NLM に以下をクエリ:
「ADRのD番号で現在使用されている最大番号は何か？F章の項目数は？」

→ adr_reservation.md の「次の番号」と照合する
→ 食い違いがあれば採番衝突の可能性 → 設計責任者に報告
```

### Lint-2: pending_changes 整合チェック

```
pending_changes.md を読み、以下を確認:
□ 「✅ 完了」なのに NLM ソースに反映されていないものはないか
□ 「🔴 実装中」のタスクが想定以上に長期間放置されていないか
□ 「⏳ 待機中」の前提タスクが完了しているのに更新されていないか
```

### Lint-3: doc_map × NLM ソース整合チェック

```
doc_map.md の「NLM 投入済みソース」テーブルを確認:
□ 「✅」マークの source_id が実際に NLM に存在するか（source_get_content）
□ 「⚠️ 陳腐化」の文書で、最新版が NLM に追加されていない場合はフラグ
```

### Lint 実行ログ

| 日付 | Lint種別 | 結果 | 問題点 | 担当 |
|---|---|---|---|---|
| 2026-04-16 | 台帳作成時点 | 正常（採番衝突解消済み） | D-8/D-9 ドラフト番号は wrap-up 時に確定 | Rex |

---

## 8. 参照先マップ（早見表）

```
「何を知りたいか」          → 「どこを見るか」
─────────────────────────────────────────────────────
設計全体の現在地           → EX_DESIGN_CONFIRMED / doc_map.md
決まっているが未反映の変更 → pending_changes.md（要望3）
ADR 採番・次の番号         → adr_reservation.md（要望1）
過去のバグを踏まないために  → ADR の A〜D章
設計判断の基準             → ADR の F章
ファイルの役割と変更可否   → SYSTEM_OVERVIEW / ADR F-4
プロット関数の仕様         → PLOT_DESIGN_CONFIRMED
neck/決済の正確な定義      → EX_DESIGN 3-5節 / ADR D-6 / F-6
#026dの実装内容            → REX_026d_spec（NLM内）
NLM 認証切れ対処           → 本ファイル STEP 0-A
ADR採番衝突が起きたら      → adr_reservation.md + 設計責任者に報告
```

---

## 9. このシステムが解決している問題

| 問題 | 解決策 |
|---|---|
| スレッド引き継ぎ時の現状把握コスト | latest.md + doc_map.md で5分以内に把握 |
| 複数文書の更新日ズレによるロジック破綻 | NLM RAG + doc_map の⚠️フラグ |
| ADR 採番衝突（2026-04-15 発生） | adr_reservation.md による事前予約制 |
| NLM 認証切れによる記録漏れ | セッション開始時チェック + pending_nlm_sync.md |
| 「決まっているが書かれていない」情報 | pending_changes.md による仮記録 |
| Lint 未実施による健全性劣化 | 3点チェックリスト（タスク完了時 + 週次） |

---

*管理: Minato / REX_Brain_System*
*最終更新: 2026-04-16（Evaluator 要望1〜5対応）*
