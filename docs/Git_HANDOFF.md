【週末GM Git更新】依頼フロー

1.基準週
今週末の日付: YYYY-MM-DD（例: 2026-3-14）
週ID: YYYY-MM-DD_wkNN（例: 2026-3-14_wk04。既存の _index の wk 番号に合わせる）

2.フォーマット参照
先週の週フォルダ（例: 2026-3-7_wk03）の各ファイル形式に合わせて、今週用の YYYY-MM-DD_wkNN フォルダを新規作成すること。

3.作成するファイル
note.md … 市況（下記「4」）とGMポートフォリオ口座情報（下記「5」）を、先週の note の見出し・構成に合わせて記載。
meta.yaml … week / snapshot（必要銘柄の bias・key_levels） / signals / decision_bias / portfolio_snapshot_YYYYMMDD。
review.md … 結論・先週の材料・Evidence（8ペア30日＋プロット＋ポートフォリオ）・来週のシナリオ・実務・監視項目。
charts.md … 8ペア30日は charts/8pair_30d_YYYY-MM-DD.txt と charts/multi_pairs_plot_8.png を参照する形で記載。
_index.md … logs/gm/weekly/YYYY/_index.md に、今週の週（YYYY-MM-DD_wkNN）の見出し・Regime・1行・Key gates・note/meta/review/charts リンクを追加する。

4.データの保存（手動・rex_chat.py はAPIチャット兼用のためスクリプト変更なし）
8ペア30日テキスト
python configs/rex_chat.py --trade（必要なら --news も）を実行する。
コンソールに表示された数値・日付範囲を、review/note の Evidence に反映する。
同じコンソール出力を、当該週の charts/ に 8pair_30d_YYYY-MM-DD.txt（週末日付）のファイル名で手動保存する。
プロット画像
png_data/ の multi_pairs_plot_8.png を YYYY-MM-DD_wkNN/charts/ に 同名（multi_pairs_plot_8.png） でコピーして保存する。

5.市況テキスト（ここに週末時点の市況を貼る）
（週末○/○時点の市況をここに記述。イラン・原油・ドル円・介入・日銀・中国・米国指標・アノマリー・資金温存などの要点を含める。来週の重要指標の有無も書く。）

6.GMポートフォリオ口座情報（ここにスクショを貼る）
（資産残高・評価損益・内訳・主な保有銘柄を、その週末時点でスクショ添付。）
同名のままcharts/ にコピーして保存する。

7.注意
週ID（wkNN）は、既存の _index.md の並びと整合させる。
日付範囲は「その週の月〜週末」で統一（例: 2026-03-09 → 2026-03-14）。