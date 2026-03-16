# 週末 Git データ更新工程（REX 参照用）

週末に「来週向け」の週次フォルダ `Y-M-D_wk--` を更新する際の手順を整理。Rex 自身が後から見返して実行できるよう、入力元・出力先・チェック項目を明示する。

---

## 1. 僕（Minato）からの提供データ

週次更新前に、以下のいずれかで渡す想定。

| 項目 | 内容 | 用途 |
|------|------|------|
| **市況** | 週末時点のマクロ・地政・為替・株・商品の認識 | review.md / note.md の「先週動いた材料」「Evidence」 |
| **GMポートフォリオ口座情報** | 資産残高・評価損益・内訳（国内株/米国株/預り金等）・保有銘柄メモ | meta.yaml の `portfolio_snapshot_YYYYMMDD`、note.md の「GMポートフォリオ口座」 |
| **チャット上のトレード結果** | エントリー/決済の相談内容（symbol, direction, entry/exit, PnL, tag, notes） | private_trades.csv 追記の元。未記録分は track_trades.py add で反映 |

**注意**: トレード結果は随時 `private_trades.csv` に記録しておく。週末時点で未登録分があれば、ここで一括で `track_trades.py add` するか、Rex がチャットログから抽出して追記する。

---

## 2. rex_chat.py フラグから抽出するデータ

週末前に `python configs/rex_chat.py --trade --news` を実行し、以下を利用する。

### 2.1 `--trade` から得るもの

| 抽出物 | 保存場所（元） | 週次フォルダでの利用先 |
|--------|----------------|------------------------|
| **8ペア30日プロット** | `logs/png_data/multi_pairs_plot_8.png` | `charts/` にコピー or 参照。ファイル名は日付付き推奨（例: `Portforio-2026-03-09.png`） |
| **8ペア変動率テキスト** | ターミナル出力（取得期間・各ペア最新値・30日変化%） | `charts/` 内の .txt（例: `Market conditions -YYYY-M-D.txt`）や `GM Strategy-YYYY-M-D~.txt` に貼り付け or 保存 |
| **レジームスナップショット** | `logs/png_data/YYYY_MM_DD_snapshot.yaml` | 市況・レジーム判定の根拠。charts/ にコピー or review/note で参照 |

### 2.2 `--news` から得るもの

| 抽出物 | 内容 | 週次での利用 |
|--------|------|----------------|
| GMキーワードニュース | RSS から取得した投資・地政系ヘッドライン＋サマリ | `charts/Market conditions -YYYY-M-D.txt` などに「ニュース1〜5」として追記 or 別 .txt に保存 |

### 2.3 `private_trades.csv` から抽出するもの

| 抽出物 | 内容 | 週次での利用 |
|--------|------|----------------|
| **当週のトレード一覧** | 該当週の opened_at でフィルタした全件 | `track_trades.py summary` で Markdown 生成 → `trade_results.md` と review.md の「Trades of the Week」 |

**charts/ 内の利用ファイル（例）**

- `multi_pairs_plot_8.png` → 週次用に日付リネームして `charts/Portforio-YYYY-MM-DD.png` などで保存
- `YYYY_MM_DD_snapshot.yaml` → そのまま `charts/` にコピー（例: `2026_03_09_snapshot.yaml`）

---

## 3. 先週フォーマットに基づく「Y-M-D_wk--」用ファイル新規作成

対象フォルダ: `logs/gm/weekly/2026/YYYY-M-D_wkNN/`（例: `2026-3-14_wk03`）。

「先週」の同フォルダ（例: `2026-3-7_wk02`）をテンプレートにし、以下を新規作成 or 更新する。

### 3.1 作成するファイル一覧

| ファイル | 内容の主な参照元 | 備考 |
|----------|------------------|------|
| **meta.yaml** | 先週の meta.yaml 構造、今週の regime/snapshot/portfolio | week, created, updated, snapshot, signals, decision_bias, portfolio_snapshot_YYYYMMDD |
| **review.md** | 僕の市況＋Evidence＋Implication、8ペア/プロット、ポートフォリオ、**Trades of the Week** | 結論・先週材料・Evidence・Implication・GM実務・監視項目。末尾に「Trades of the Week」セクションを追加 |
| **note.md** | 市況・マクロ、Key takeaways、Key gates、ポートフォリオ口座、Portfolio action | Macro/Regime・takeaways・gates・本日追記・Portfolio action・口座サマリ |
| **charts.md** | 先週の charts.md 構造 | 今週のチャート画像・データリンク（charts/ 内の .png, .yaml, .txt）を列挙 |
| **trade_results.md** | `track_trades.py summary --start YYYY-MM-DD --end YYYY-MM-DD` の出力 | 当週のトレード一覧＋概要（件数・勝率・合計PnL）。詳細検証用 |

### 3.2 charts/ サブフォルダに置くもの

| 種別 | 元ファイル（例） | 週次での名前（例） |
|------|------------------|---------------------|
| 8ペアプロット | `logs/png_data/multi_pairs_plot_8.png` | `Portforio-2026-03-09.png` 等 |
| レジームYAML | `logs/png_data/2026_03_09_snapshot.yaml` | `2026_03_09_snapshot.yaml`（そのままコピー可） |
| 市況・ニューステキスト | rex_chat --trade/--news の出力 or 手動メモ | `Market conditions -2026-3-7.txt` 等 |
| GM戦略テキスト | チャットで整理した戦略メモ | `GM Strategy-2026-3-9~.txt` 等 |
| その他チャート | 個別スクショ（JP225, US100, WTI 等） | 従来通り `charts/` に配置 |

### 3.3 review.md の「Trades of the Week」セクション

- **数値**: `track_trades.py summary` の「概要」を転記（トレード回数・勝ち/負け・勝率・合計PnL）。
- **代表トレード**: 1〜3件を要約（symbol, direction, pnl_%, tag, notes の要点）。
- **学び**: 今週の反省・改善点・来週の方針を 2〜3 行で記載。

---

## 4. 実行順（チェックリスト）

週末に、以下を上から順に実施する。

- [ ] **1. 僕からの提供データを確認**
  - 市況サマリ
  - GMポートフォリオ口座（残高・評価損益・内訳）
  - チャット上のトレード結果（未記録分は private_trades.csv に反映）

- [ ] **2. rex_chat.py でデータ取得**
  - `python configs/rex_chat.py --trade --news` を実行
  - ターミナル出力（8ペア変動率・レジーム）を保存 or コピー
  - `logs/png_data/multi_pairs_plot_8.png` と `logs/png_data/YYYY_MM_DD_snapshot.yaml` を確認

- [ ] **3. 当週トレードの Markdown 生成**
  - 当週の月曜〜日曜の日付を決める（例: 2026-03-09〜2026-03-14）
  - `python src/track_trades.py summary --start 2026-03-09 --end 2026-03-14` を実行
  - 出力を `trade_results.md` として当週フォルダに保存
  - 同じ出力から「Trades of the Week」用の要約を抜き出し

- [ ] **4. 来週フォルダの作成**
  - `logs/gm/weekly/2026/YYYY-M-D_wkNN/` を新規作成（例: 2026-3-14_wk03）
  - `charts/` サブフォルダを作成

- [ ] **5. charts/ へのコピー**
  - `multi_pairs_plot_8.png` → `charts/Portforio-YYYY-MM-DD.png`
  - `YYYY_MM_DD_snapshot.yaml` → `charts/YYYY_MM_DD_snapshot.yaml`
  - 市況・ニュース・GM戦略の .txt を配置

- [ ] **6. 各 .md / .yaml の作成・更新**
  - 先週フォルダをコピーしてリネームし、今週の日付・内容に差し替え
  - meta.yaml: week, date_range, created, updated, snapshot, signals, portfolio_snapshot
  - review.md: 結論・材料・Evidence・Implication・GM実務・監視項目・**Trades of the Week**
  - note.md: Macro・takeaways・gates・本日追記・Portfolio action・口座
  - charts.md: 今週の charts/ 内ファイルを列挙
  - trade_results.md: 手順 3 の Markdown をそのまま保存

- [ ] **7. Git 更新**
  - `git add logs/gm/weekly/2026/YYYY-M-D_wkNN/ data/private_trades.csv`（必要に応じて logs/png_data 等も追加）
  - `git commit -m "weekly: YYYY-M-D_wkNN review + trade_results + charts"`
  - `git push`

---

## 5. パス・コマンド早見

| 用途 | パス or コマンド |
|------|------------------|
| 週次ルート | `REX_Trade_System/logs/gm/weekly/2026/` |
| 当週フォルダ例 | `2026-3-14_wk03/` |
| プロット（元） | `logs/png_data/multi_pairs_plot_8.png` |
| スナップショット（元） | `logs/png_data/YYYY_MM_DD_snapshot.yaml` |
| トレードCSV | `data/private_trades.csv` |
| トレード追記 | `python src/track_trades.py add --opened-at ... --closed-at ... --symbol ... --direction long/short --size ... --entry ... --exit ... [--tag ...] [--notes ...]` |
| 週次サマリ出力 | `python src/track_trades.py summary --start YYYY-MM-DD --end YYYY-MM-DD` |

---

## 6. 足りない場合の追加メモ

- **週番号（wkNN）**: その週の月曜日を含む ISO 週番号、または「3月第2週」などの通し番号で統一するとよい。先週が `wk02` なら今週は `wk03`。
- **日付範囲**: review/meta の `date_range` は「その週の月曜〜日曜」で揃える（例: `2026-03-09 -> 2026-03-14`）。
- **作成日**: `created` は週末にファイルを作った日、`updated` は最終更新日（月曜の追記などがあれば更新）。

このドキュメントは、Rex が週末更新時に参照し、上記チェックリストとパスに従って作業できるようにするためのもの。
