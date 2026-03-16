# HANDOFF.md — UCAR-GM / Trade_Record 引継ぎ（Weekly Ops）
version: 1.0
updated: 2025-12-20 (JST)

このファイルは、新スレッド／別環境へ移行しても「週次レビュー運用」を崩さず継続するための引継ぎ手順です。  
目的は **GM（グローバルマクロ）運用の精度向上** と、**Trade_Recordを巡れる地図（STATUS → _index → weekly → review/meta/charts）** として蓄積すること。

---

## 0) 1行目的
- **GMの週次レビューを定型化し、判断更新点を再利用可能な形でGitにストックする。**

---

## 1) 固定運用ループ（毎週これだけ）
### 平日（随時）
1. 相場変化・戦略変更の「追記が必要な事実」だけメモ
2. `note.md` に **facts** を追記（必要なら **decision** も追記）
3. チャートURLは週末にまとめて `charts.md` に集約（正本）

### 週末（Fri close〜Sat）
1. 週終値が確定
2. 「入力パッケージ」を UCAR に送付
3. UCAR が「出力セット」を生成
4. ミナトが Git へ push
5. 週明け：UCARと次週シナリオ構築 → `STATUS.md` と `note.md` に反映 → 平日運用へ戻る

## 1.5) Monday AM（週明け朝）ラベル付け（※行動トリガー禁止）
- 月曜朝は薄商いで“狩り”混入率が高いので、A/B/Cの寄り推定だけ行う（売買判断はしない）。
- 実行判断は終値ゲート（Tokyo close / NY close）で確定。
- 記録：
  - 月曜朝ラベル → 該当週 note.md 冒頭テンプレに記入
  - 終値（Tokyo/NY）→ note.md の Facts 欄に追記
  - 週末まとめ → review.md

---

## 2) フォルダ規約（推奨・固定）
例：`Trade_Record/logs/gm/weekly/2025/2025-12-15_wk50/`

- `Trade_Record/STATUS.md`
  - プロジェクト現在地（最新Brief）

- `Trade_Record/logs/gm/weekly/YYYY/_index.md`
  - 週フォルダ一覧・導線（1行追記で増やす）

- `Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/`
  - `note.md`（週内メモ：facts/decisions）
  - `review.md`（週末確定レビュー：結果/評価/来週行動）
  - `meta.yaml`（機械拾い用タグ）
  - `charts.md`（チャート共有リンクの正本）
  - `charts/`（任意：ローカル画像を置くなら）

- `Trade_Record/versions/distilled/YYYY/`
  - `distilled-gm-YYYY-MM.md`（月次 distilled の正本：週末に追記していく）

---

## 3) チャート運用ルール（重要）
### 3.1 チャート画像の時間足
- 原則：**週足／日足 の2枚を1枚画像にして統一**

### 3.2 GoogleDriveリンクの貼り先（正本）
- **チャートURLは `charts.md` に集約（正本）**
- `note.md` / `review.md` からは、URLを直貼りせず **`./charts.md` への相対リンク**で参照する

> 例：note.mdの「Attachments / Chart refs」にはこう書く  
> `- charts.md: ./charts.md`

### 3.3 charts.md の置き場所
- `note.md` と同じ週フォルダ直下が最適  
  (`YYYY-MM-DD_wkNN/charts.md`)

---

## 4) 週末入力パッケージ（ミナト → UCAR）
週末に UCAR へ送るもの（同一週フォルダの内容として渡す）

1. `Trade_Record/STATUS.md`
2. `Trade_Record/logs/gm/weekly/YYYY/_index.md`
3. `Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/note.md`
4. `Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/meta.yaml`（未完成でもOK／無くてもOK）
5. ポートフォリオ写メ（評価損益が分かるもの）
6. 週足+日足チャート画像（主要）
   - USDJPY
   - JP225
   - SPX（or US100）
   - BTC
   - XAU
   - 2243
   - 2638
7. 週末追記事項（テキスト1〜3行でOK）
   - 今週の新規売買（例：IONQ +4 / RGTI +5）
   - 余剰資金概算（例：20万→15万）
   - 特記事項（例：BOJ/CPI/会見での意思決定など）

---

## 5) 週末出力セット（UCAR → ミナト）
UCARが生成して返す（コピペ納品想定）

1. `review.md`（Weekly Review：週末確定・終値ベース）
2. `meta.yaml`（タグを整形し完成）
3. `_index.md` 追記1行（wkフォルダ導線）
4. `STATUS.md` 末尾：**次週Brief** 追記案
5. 次週 `note.md` 叩き台（wkNN+1）

---

## 6) meta.yaml の位置づけ（結論）
- **meta.yaml は “UCAR用” とみてOK**
- 目的：将来の検索／抽出／自動要約を高速化するための「機械タグ」
- ミナト側は完璧に書かなくてOK（週末にUCARが整形して完成させる前提）

### meta.yaml（雛形）
```yaml
week: 2025-12-15_wk50
asset:
  - USDJPY
  - JP225
  - SPX
  - BTC
  - XAU
  - 2243
  - 2638
regime:
  - risk-on
  - risk-off
trigger:
  - BOJ
  - CPI
event:
  - "2025-12-19 BOJ decision + Ueda presser"
decision:
  - "2243/2638を各20口圧縮し買付余力を確保"
evidence:
  - "終値ベース：USDJPY=__ / JP225=__ / SPX=__ / BTC=__ / XAU=__"
links:
  charts: "./charts.md"
```

---

## 7) 日次GMレポート連携（週末更新時）

週末の review / meta / distilled 更新時に、**日次GMレポート**（`logs/gm/daily/YYYY/gm_report/`）を活用して、AI連携による自動化を強化する。

### 7.1 フォルダ・パス

- **日次レポート**: `logs/gm/daily/YYYY/gm_report/YYYY-M-D.txt` または `YYYY-MM-DD.txt`
- **週次**: `logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/`
- **月次 distilled**: `versions/distilled/YYYY/distilled-gm-YYYY-M.md`

### 7.2 実行レベル（3段階）

| レベル | 説明 | 実施内容 |
|--------|------|----------|
| **半自動** | パーススクリプト | `python src/daily_report_parser.py --date 2026-3-14` でキーワード・数値・トレンドブロックを抽出 → JSON/Python dict を手動で review/meta に反映 |
| **AI連携** | Rex への一括投入 | 日次テキスト＋8ペアデータ＋レジーム＋パース結果を system に挿入し、Rex に「review.md / meta.yaml / distilled の該当ブロックを生成して」と依頼 |

### 7.3 AI連携フロー（推奨）

1. **データ取得**: `python configs/rex_chat.py --trade`（必要なら `--news` も）
2. **日次パース**: `python src/daily_report_parser.py --date YYYY-M-D --json` → 抽出結果を控える
3. **Rex へ投入**: 当該週の日次レポート全文（または要約）＋8ペア30日＋レジーム＋パース結果を system メッセージで渡す
4. **出力依頼**: 「このデータで review.md の Evidence／先週の材料、meta.yaml の event／trigger、distilled の今週サマリーを生成して」とプロンプト
5. **コピペ納品**: 出力を該当ファイルに貼り付け・整形

### 7.4 パーススクリプトの役割

`src/daily_report_parser.py` は次を抽出する：

- **トレンドブロック**: `【〇〇/中期トレンド判断(参考)】` 内の `<コア>` / `<サテライト>` 判断
- **キーワード**: イラン・ホルムズ・地政学・FRB・BOJ・CPI 等の GM キーワード
- **主要数値**: S&P500, VIX, WTI, ドル円, 米10年債, 日経平均 等
- **戦略要約**: `【〇〇のトレード戦略の考え方】`
- **重要指標カレンダー**: `▽〇月〇日〜〇日の予定`
