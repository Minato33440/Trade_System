# 週末 Git データ更新工程（REX 参照用）

週末に「来週向け」の週次フォルダ `Y-M-D_wk--` を更新する際の手順を整理。Rex 自身が後から見返して実行できるよう、入力元・出力先・チェック項目を明示する。

---

## 🦀 RTK（Rust Token Killer）使用ルール（ClaudeCode 必読・全工程共通）

**すべてのターミナルコマンドは `rtk` プレフィックスを必須とする。**

```bash
# ❌ 間違い
git status
git add .
git commit -m "msg"
git push
python main.py --trade --news

# ✅ 正しい
rtk git status
rtk git add logs/gm/weekly/...
rtk git commit -m "msg"
rtk git push origin main
python main.py --trade --news   # ← python は rtk 対象外（パススルー）
```

**Windows環境での注意**:
- Unix系の自動フックは使用不可（Mac/Linux専用）。
- `~/.claude/CLAUDE.md` の指示経由で ClaudeCode が手動で `rtk` を付ける方式が唯一の動作モード。
- `&&` でチェーンする場合も各コマンドに `rtk` を付ける：
  ```bash
  rtk git add . && rtk git commit -m "msg" && rtk git push
  ```
- `python` / `rtk init` / `rtk gain` などの RTK メタコマンド自体は `rtk` 不要。

---

## ⚠️ 作業開始前の最初の一言（ClaudeCode 必読）

週末Git更新の依頼を受けたら、**市況テキストの受け取りより先に**、以下をMianto に依頼すること。

> 「`python main.py --trade --news` を実行して、ターミナル出力とスナップショット結果をこのチャットに貼り付けてください。」

**理由**: `--trade --news` の実測値（8ペア最新値・30日変化率・レジームラベル・GMニュース）なしにファイルを作成すると、推定値で一度作成した後に実データで全ファイルを再更新する二度手間が発生する。市況テキストと実測データは**同時に**揃えてからファイル作成に入る。

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

## 2. データ取得コマンド（2026-03-21更新）

### ⚠️ 重要: コマンドの変更

旧コマンド（廃止）: `python configs/rex_chat.py --trade --news`
**新コマンド（確定）: `python main.py --trade --news`**

> 理由: システム構成変更により `configs/rex_chat.py` の直接実行では --trade/--news フラグが発動しなくなった。
> `main.py` が `configs/rex_chat.py` の `main()` を呼び出すエントリポイントとなっており、こちらから実行する。

### 2.1 `--trade` から得るもの

| 抽出物 | 保存場所（元） | 週次フォルダでの利用先 |
|--------|----------------|------------------------|
| **8ペア30日プロット** | `logs/png_data/multi_pairs_plot_8.png` | `charts/Portforio-YYYY-MM-DD.png` にコピー保存 |
| **8ペア変動率テキスト** | ターミナル出力（取得期間・各ペア最新値・30日変化%） | `charts/YYYY-MM-DD 〜 YYYY-MM-DD.txt` として保存（日付は取得期間）|
| **レジームスナップショット** | `logs/png_data/YYYY_MM_DD_snapshot.yaml` | `charts/YYYY_MM_DD_snapshot.yaml` にコピー保存 |

取得期間のファイル名例: `2026-02-19 〜 2026-03-21.txt`（取得期間をそのままファイル名に使う）

### 2.2 `--news` から得るもの

| 抽出物 | 内容 | 週次での利用 |
|--------|------|----------------|
| GMキーワードニュース | RSS から取得した投資・地政系ヘッドライン＋サマリ | `charts/Market conditions -YYYY-M-D~.txt` に市況テキストと合わせて保存 |

> **運用メモ**: `Market conditions -YYYY-M-D~.txt` には Minato の市況テキストも先頭に追記してから `--news` 出力を続けて貼ると一元管理しやすい。

### 2.3 `private_trades.csv` から抽出するもの

| 抽出物 | 内容 | 週次での利用 |
|--------|------|----------------|
| **当週のトレード一覧** | 該当週の opened_at でフィルタした全件 | `track_trades.py summary` で Markdown 生成 → `trade_results.md` と review.md の「Trades of the Week」 |

**charts/ 内の利用ファイル（確定パターン）**

- `multi_pairs_plot_8.png` → `charts/Portforio-YYYY-MM-DD.png`（実行日付でリネーム）
- `YYYY_MM_DD_snapshot.yaml` → `charts/YYYY_MM_DD_snapshot.yaml`（そのままコピー）
- 8ペア30日データ → `charts/YYYY-MM-DD 〜 YYYY-MM-DD.txt`（取得期間を〜でつなぐ）
- GM戦略 → `charts/GM Strategy-YYYY-M-DD.txt`

---

## 3. 先週フォーマットに基づく「Y-M-D_wk--」用ファイル新規作成

対象フォルダ: `logs/gm/weekly/2026/YYYY-M-D_wkNN/`（例: `2026-3-20_wk04`）。

「先週」の同フォルダをテンプレートにし、以下を新規作成 or 更新する。

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
| 8ペアプロット | `logs/png_data/multi_pairs_plot_8.png` | `Portforio-2026-03-21.png` |
| レジームYAML | `logs/png_data/2026_03_21_snapshot.yaml` | `2026_03_21_snapshot.yaml` |
| 30日データテキスト | `python main.py --trade` のターミナル出力 | `2026-02-19 〜 2026-03-21.txt` |
| 市況・ニューステキスト | Minato市況 + `python main.py --news` の出力 | `Market conditions -2026-3-21~.txt` |
| GM戦略テキスト | review/note/meta/30日データを統合して作成 | `GM Strategy-2026-3-21.txt` |
| その他チャート | 個別スクショ（JP225, US100, WTI 等） | 従来通り `charts/` に配置 |

### 3.3 review.md の「Trades of the Week」セクション

- **数値**: `track_trades.py summary` の「概要」を転記（トレード回数・勝ち/負け・勝率・合計PnL）。
- **代表トレード**: 1〜3件を要約（symbol, direction, pnl_%, tag, notes の要点）。
- **学び**: 今週の反省・改善点・来週の方針を 2〜3 行で記載。

---

## 4. 実行順（チェックリスト）

週末に、以下を上から順に実施する。

- [ ] **1. 僕からの提供データを確認**
  - ⚠️ **最初に `python main.py --trade --news` の実行を依頼すること**（市況テキストと同時に揃える）
  - 市況サマリ（チャット上で貼ってもらう）
  - GMポートフォリオ口座（残高・評価損益・内訳）
  - チャット上のトレード結果（未記録分は private_trades.csv に反映）

- [ ] **2. `python main.py --trade --news` でデータ取得**（⚠️ main.py から実行）
  - ターミナル出力（8ペア変動率・レジーム）を `charts/YYYY-MM-DD 〜 YYYY-MM-DD.txt` に保存
  - `logs/png_data/multi_pairs_plot_8.png` を `charts/Portforio-YYYY-MM-DD.png` にコピー
  - `logs/png_data/YYYY_MM_DD_snapshot.yaml` を `charts/` にコピー
  - `--news` の出力を Minato 市況テキストと合わせて `charts/Market conditions -YYYY-M-D~.txt` に保存

- [ ] **3. 当週トレードの Markdown 生成**
  - 当週の月曜〜日曜の日付を決める（例: 2026-03-16〜2026-03-21）
  - `python src/track_trades.py summary --start 2026-03-16 --end 2026-03-21` を実行
  - 出力を `trade_results.md` として当週フォルダに保存
  - 同じ出力から「Trades of the Week」用の要約を抜き出し

- [ ] **4. 週次フォルダの確認・作成**
  - `logs/gm/weekly/2026/YYYY-M-D_wkNN/` を新規作成（Minato がフォルダ作成）
  - `charts/` サブフォルダを確認

- [ ] **5. charts/ へのファイル配置**（手順2で既に実施済みなら確認のみ）
  - `Portforio-YYYY-MM-DD.png` ✓
  - `YYYY_MM_DD_snapshot.yaml` ✓
  - `YYYY-MM-DD 〜 YYYY-MM-DD.txt` ✓
  - `Market conditions -YYYY-M-D~.txt` ✓
  - `GM Strategy-YYYY-M-D.txt` ← ClaudeCode が作成

- [ ] **6. 各 .md / .yaml の作成・更新**（ClaudeCode が担当）
  - meta.yaml: week, date_range, created, updated, snapshot, signals, portfolio_snapshot
  - review.md: 結論・材料・Evidence・Implication・GM実務・監視項目・**Trades of the Week**
  - note.md: Macro・takeaways・gates・本日追記・Portfolio action・口座
  - charts.md: 今週の charts/ 内ファイルを列挙
  - trade_results.md: 手順 3 の Markdown をそのまま保存

- [ ] **7. インデックス・ステータス・distilled の更新**（ClaudeCode が担当）
  - `logs/gm/weekly/2026/_index.md`: 当週エントリを末尾に追加（Regime / 1行 / Key gates / Links）
  - `docs/STATUS.md`: 最新 "Weekly Brief | YYYY-M-D_wkNN" セクションを末尾に追加
  - `docs/Trade-Main.md`: ① "2026 Weekly Index" に当週エントリを追加 ② "Distilled Logs" リンクを更新 ③ 末尾に "Weekly Brief" セクションを追加
  - `versions/distilled/2026/distilled-gm-2026-N.md`: 当週の distilled エントリを追記 or 新規作成
    - **命名ルール（重要）**: N は月番号。**同月内は必ず同じファイルに追記する。新月になった時点で新規ファイルを作成する。**
      - 例: 3月第1〜5週はすべて `distilled-gm-2026-3.md` に追記
      - 例: 4月第1週から `distilled-gm-2026-4.md` を新規作成
    - **週をまたいで新ファイルを作ってはいけない**（月内で -4, -5 のように分割しない）
    - 書式: regime / decision（判断変更点のみ） / evidence (close) / implication / tags

- [ ] **8. Git 更新**
  - 以下を一括ステージ（`charts/` 内 PNG は .gitignore で自動除外、テキスト・YAML のみ追跡される）
    ```
    git add logs/gm/weekly/2026/YYYY-M-D_wkNN/ \
            logs/gm/weekly/2026/_index.md \
            docs/STATUS.md \
            docs/Trade-Main.md \
            versions/distilled/2026/ \
            data/private_trades.csv
    ```
  - コミット＆プッシュ
    ```
    git commit -m "weekly: YYYY-M-D_wkNN review + trade_results + charts"
    git push origin main
    ```
  - **charts/ の Git 追跡ルール（2026-03-21〜）**
    - `*.txt` / `*.yaml` / `*.md` → **追跡対象**（上記 `git add` で自動包含）
    - `*.png` → **ローカル専用**（`.gitignore` で除外済み）
    - 新ファイルを charts/ に追加した場合も `git add YYYY-M-D_wkNN/` で一括追加できる

---

## 5. パス・コマンド早見

| 用途 | パス or コマンド |
|------|------------------|
| 週次ルート | `REX_Trade_System/logs/gm/weekly/2026/` |
| 当週フォルダ例 | `2026-3-20_wk04/` |
| **8ペアデータ取得（確定）** | **`python main.py --trade --news`** |
| プロット（元） | `logs/png_data/multi_pairs_plot_8.png` |
| スナップショット（元） | `logs/png_data/YYYY_MM_DD_snapshot.yaml` |
| トレードCSV | `data/private_trades.csv` |
| トレード追記 | `python src/track_trades.py add --opened-at ... --closed-at ... --symbol ... --direction long/short --size ... --entry ... --exit ... [--tag ...] [--notes ...]` |
| 週次サマリ出力 | `python src/track_trades.py summary --start YYYY-MM-DD --end YYYY-MM-DD` |

---

## 6. 足りない場合の追加メモ

- **週番号（wkNN）**: その週の月曜日を含む ISO 週番号、または「3月第2週」などの通し番号で統一するとよい。先週が `wk03` なら今週は `wk04`。
- **日付範囲**: review/meta の `date_range` は「その週の月曜〜金曜」で揃える（例: `2026-03-16 -> 2026-03-20`）。
- **作成日**: `created` は週末にファイルを作った日、`updated` は最終更新日（月曜の追記などがあれば更新）。
- **30日データテキストのファイル名**: `python main.py --trade` 出力冒頭の「取得期間: YYYY-MM-DD 〜 YYYY-MM-DD」をそのままファイル名に使う。
- **GM Strategyファイル**: 8ペア30日データ・レジーム・Minato市況・news を統合してClaudeCodeが作成。セクション構成: ①8ペアサマリ ②週末市況 ③ファンダ ④テクニカル ⑤シナリオ ⑥押し目戦略 ⑦アクション ⑧参照データ ⑨総合解説(A-G)。

このドキュメントは、Rex / ClaudeCode が週末更新時に参照し、上記チェックリストとパスに従って作業できるようにするためのもの。
