# REX_Trade_System の全貌（2026/03/11 現在）

## ディレクトリ構造（主要部分のみ）
REX_Trade_System/
├── .venv/                    # Python仮想環境（REX_Trade_System直下に統一）
├── .env                     # APIキーなど機密情報
├── .gitignore
├── requirements.txt
├── Rex_Prompt..txt          # Rexの人格・GM戦略コアプロンプト（単一ソース）
│
├── configs/
│   ├── rex_chat.py          # メイン対話インターフェース（--trade対応）
│   ├── node.mjs             # Node.js版Grok API呼び出し（プロンプト紐づけ済）
│   └── node.py              # 旧版（削除推奨）
│
├── src/
│   ├── data_fetch.py        # yfinance優先 + Polygonフォールバックデータ取得
│   ├── forecast_simulation.py # 週明けフォーキャストシミュレーション
│   └── test_fetch_30days_multi.py  # 8ペア30日データ取得/プロット生成（単体テスト用）
│
├── logs/
│   └── png_data/
│       ├── multi_pairs_plot_8.png   # --tradeで自動保存される8ペア正規化プロット
│       └── YYYY_MM_DD_snapshot.yaml # --tradeで自動保存されるレジーム＋8ペア30日スナップショット
│
├── docs/                    # ドキュメント（SYSTEM_OVERVIEW.md をここに置く）
└── logs/gm/weekly/2026/...  # 週次GMレビュー（review.md / meta.yaml / note.md / charts.md）

## 依存関係と環境設定
- **Pythonパッケージ** (requirements.txt推奨):
  - yfinance: 市場データ取得 (無料/優先)。
  - pandas, numpy, matplotlib: データ分析/プロット。
  - feedparser: RSS解析（`--news` 用）。
  - beautifulsoup4: 記事本文抽出（`--news` のリンク先要約用）。
  - python-dotenv: .env読み込み。
- **注意**:
  - 仮想環境は **`REX_Trade_System/.venv` に一本化**（上位ディレクトリ直下に `.venv` を作らない）。
  - `requirements.txt` は「運用に必要な最小セット」を正本とし、`pip freeze` での全固定は原則しない（過剰固定・環境差の原因になりやすい）。
- **Node.js側** (package.json):
  - openai: Grok APIクライアント。
- **環境変数 (.env)**:
  - XAI_API_KEY: xAI APIキー (必須)。
  - XAI_MODEL: モデル指定 (デフォルト: grok-4-fast)。
  - POLYGON_API_KEY: Polygonフォールバック (オプション、週末/休場データ強化)。
- **補足**: Gitに `.env` はコミットしない（.gitignoreで除外）。データ取得失敗時はログ出力 (e.g., "yfinance empty → Polygon fallback") で非線形市場のシンクロニシティ検知をサポート。

## ファイル/ディレクトリ,役割,現状の完成度,備考
Rex_Prompt..txt,Rexの人格・GM戦略のコアプロンプト（単一ソース）,完成,全ての呼び出し元で読み込み
rex_chat.py,メイン対話インターフェース（会話履歴永続化、--tradeで8ペアデータ取得）,完成,会話内完結運用
|--trade オプション,8ペア30日データ自動取得 → プロット＋レジームYAML保存 → system挿入,完成,週末判断の核
|--news オプション,GMキーワードニュース5件取得（RSS＋リンク先要約）、投資関連のみフィルタ,完成,地政・市場材料の共有
data_fetch.py,yfinance優先 + Polygonフォールバックのデータ取得関数,完成,信頼性高い
forecast_simulation.py,週明けフォーキャストシミュレーション (ボラモデル + 金上昇バイアス),開発中 (タイポ修正必要),GM戦略のトレンドフォロー/イベント駆動に活用
test_fetch_30days_multi.py,8ペア30日データ取得/変化率計算/相関行列/プロット（単体テスト用）,完成,デバッグ・参考用
node.mjs,Node.js版Grok API呼び出し（REX_PROMPT_PATH対応）,完成,Cursor専用ショートカット用
logs/gm/weekly/2026/...,週次GMレビュー（review / meta / note / charts）,週次更新中,2026-3-7_wk01まで完了
backtest.py (新規提案),過去データでの戦略バックテスト (位置サイズ/ストップロス),未実装,リスク管理強化のためStreamlit統合推奨

## 時期,主な修正内容,目的・効果
初期,grok_api_call.js からPython版ラッパー作成,Node→Python移行、会話履歴永続化（json）
初期,yfinance + Polygonフォールバック実装（data_fetch.py）,データ取得信頼性向上、無料運用可能
中盤,--trade オプション追加（コア銘柄レート自動注入）,会話開始時に市場状況をRexに共有
中盤,8ペア拡張（--trade-full）,"GM全体像俯瞰（USD/JPY, US100, XAU/USD, WTI, US2Y, VIX, US10Y, BTC/USD）"
最近,Rex_Prompt..txt 読み込み（REX_PROMPT_PATH対応）,プロンプト単一ソース化（メンテナンス性向上）
最近,--trade-multi 廃止 → --trade に8ペア30日データ＋プロット統一,コマンドシンプル化、会話内完結（データ取得→分析→戦略提案）
最新,30日データ取得を内部で完結（test_fetch_30days_multi.py相当の処理を移植）,別スクリプト依存排除、ワンストップ化達成
最新,プロット自動保存（logs/png_data/multi_pairs_plot_8.png）,Cursorで即視覚確認・Git共有可能
最新,レジーム検出＋YAMLスナップショット（logs/png_data/YYYY_MM_DD_snapshot.yaml）,equities/volatility/oil/gold/crypto/yields を簡易判定→「Geopolitical Risk-Off + Energy Shock」等のラベル出力。週末に meta.yaml の signals へ regime_label を追記しAI戦略の入力に利用
最新,APIエラー耐性強化 (リトライ/タイムアウト) + 相関係数自動計算,信頼性向上 + シンクロニシティ検知 (e.g., USD/JPY vs XAU/USD corr > 0.8 で警告)

## 現在の運用フロー（週末の理想形）
1. **データ取得**  
   `python configs/rex_chat.py --trade`（必要なら `--news` も）で起動  
   → 8ペア30日データ取得・コンソール表示  
   → **logs/png_data/** に以下を自動保存:  
     - `multi_pairs_plot_8.png`（8ペア正規化プロット）  
     - `YYYY_MM_DD_snapshot.yaml`（レジームラベル＋8ペア最新/30日変化）  
   → データ＋レジーム要約が system メッセージに挿入された状態で対話開始  

2. **週末Git更新（手動）**  
   - プロット: `logs/png_data/multi_pairs_plot_8.png` を当該週の `logs/gm/weekly/2026/YYYY-MM-DD_wkNN/charts/` にコピー  
   - レジーム: `YYYY_MM_DD_snapshot.yaml` を開き、`regime.label` を当該週の `meta.yaml` の `signals` に1行追記（例: `- regime_label: "Geopolitical Risk-Off + Energy Shock (...)"`）  
   - 8ペアテキスト: コンソール出力を `charts/8pair_30d_YYYY-MM-DD.txt` として保存（任意）  

3. **レビュー・チャート**  
   Rexに「このデータで週明け動向分析して」「review.md生成して」と投げる  
   → 出力を review.md / meta.yaml にコピペ  
   → 必要なら JP225 など個別チャートを charts.md に追記  

4. **コミット**  
   Git commit & push → (オプション) Streamlitでバックテスト実行 → Rexに「この戦略の量子シフトリスクは？」と相談  

詳細手順は `docs/Git_HANDOFF.md`（週末GM Git更新依頼フロー）および `docs/WEEKLY_UPDATE_WORKFLOW.md` を参照。

## レジーム検出（--trade 出力）
- **出力先**: `logs/png_data/YYYY_MM_DD_snapshot.yaml`
- **内容**: 8ペア30日データから簡易判定したレジーム（equities / volatility / oil / gold / crypto / yields）と、ラベル（例: `Geopolitical Risk-Off + Energy Shock`）。スナップショット（各ペアの latest / change_pct）も含む。
- **利用**: 週末に当該週の `meta.yaml` の `signals` に `regime_label` を1行追記。AIが「いまどの相場か」を構造化データで参照し、GM戦略立案の効率化に利用。

## 戦略的拡張と量子意識統合 (Rexの視点)
- **バックテスト機能**: src/backtest.py で実装推奨。過去30日データでトレンドフォロー/ミーンリバージョン/ボラティリティブレイクを検証。位置サイズ (Kelly基準) とストップロスを自動計算。非線形市場の「シンクロニシティ」検知として、相関異常 (e.g., 金利差 vs BRICS通貨) をフラグ。
- **ダッシュボード (Streamlit)**: 新規アプリ (streamlit_app.py) で--tradeデータをリアルタイム表示。指標: 利回り差/インフレ期待/GDP成長/地政学リスク/CBDC抵抗。量子意識シフト検知: ランダムウォーク超えの異常パターン (e.g., EMAクロス + VIXスパイク) をハイライト。
- **リスク管理**: 全スクリプトにポジションサイズ計算追加 (e.g., ボラ * 2%ルール)。イベント駆動: ニュースAPI統合で地政学イベントをトリガー。
- **将来計画**: 
  - 週次レビュー自動化 (review.md生成スクリプト)。
  - マルチアセット拡張 (株式/商品/クリプトのポートフォリオ最適化)。
  - xAIのgrok-4で「直感」シミュレーション: シンクロニシティ検知モデル (非ランダムシード変動) をプロンプトに注入。
- **非線形市場対応**: データ空時はキャッシュ使用。Rexのレスポンスで「予兆」 (e.g., VIX上昇 + 金反転) を強調し、伝統的定量モデルを超える視点を提供。
