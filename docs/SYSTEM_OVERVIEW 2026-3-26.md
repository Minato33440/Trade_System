# REX_Trade_System の全貌（2026/03/27 現在）

> 最終更新: 2026-03-27
> 設計確定文書: `docs/EX_DESIGN_CONFIRMED-2026-3-26_2.md`（本ファイルと必ず併読）
> リポジトリ: GitHub `Minato33440/UCAR_DIALY`

---

## チーム役割分担

| 役割 | 担当 |
|------|------|
| ディレクター・意思決定 | Minato |
| エンジニアリング責任者・設計 | Rex（claude.ai） |
| コード実装・Git管理 | ClaudeCode（VS Code） |

---

## ディレクトリ構造

```
REX_Trade_System/
├── .env                          # APIキー等の機密情報
├── .gitignore
├── .venv/                        # Python仮想環境（プロジェクト直下に統一）
├── main.py                       # CLIエントリーポイント（rex_chat.py に委譲）
├── requirements.txt              # Pythonパッケージ（25本）
├── Rex_Prompt..txt               # Rexの人格・GM戦略コアプロンプト（単一ソース）
├── package.json                  # Node.js依存（最小限）
│
├── configs/
│   ├── rex_chat.py               # メイン対話インターフェース（--trade / --news 対応）
│   ├── settings.py               # グローバル定数（ティッカー・パス・キーワード）
│   ├── node.mjs                  # Node.js版Grok APIラッパー（Cursor専用）
│   └── node.py                   # 旧版（非推奨）
│
├── src/                          # コアトレーディングモジュール
│   ├── swing_detector.py         # ✅ スイング高値/安値検出（全TF対応）
│   ├── entry_logic.py            # ✅ エントリー3ステップ検証（#018まで・変更凍結）
│   ├── exit_logic.py             # ✅ エグジット4段階ステートマシン（#009以降・変更凍結）
│   ├── backtest.py               # ✅ 旧版バックテスト（#018・ベースライン保持・変更凍結）
│   ├── window_scanner.py         # ✅ 窓ベース階層スキャン（#021〜#023・新エンジン）
│   ├── base_scanner.py           # ✅ 4H+15M基礎スキャナー（#015）
│   ├── structure_plotter.py      # ✅ 4H+1H構造確認プロット（#019）
│   ├── test_1h_coincidence.py    # ✅ 1H-4H一致検証（#020・修正版v2）
│   ├── plotter.py                # ✅ チャート生成（#020-fix適用済み）
│   ├── signals.py                # ⚠️ 廃止方向（旧MTFシグナルエンジン）
│   ├── Simple_Backtest.py        # 簡易バックテスト分析
│   ├── data_fetch.py             # ✅ yfinance優先 + Polygonフォールバック
│   ├── market.py                 # ✅ マーケットスナップショット・マルチペア取得
│   ├── regime.py                 # ✅ 8ペアマクロレジーム検出
│   ├── chat.py                   # ✅ Grok (xAI) APIクライアント
│   ├── history.py                # ✅ 会話履歴JSON永続化
│   ├── news.py                   # ✅ GMキーワードニュース（RSS + og取得）
│   ├── utils.py                  # ✅ 共通ユーティリティ
│   ├── dashboard.py              # 🔲 Streamlitダッシュボード（実装中）
│   ├── forecast_simulation.py    # 🔲 ボラティリティフォーキャスト（実装中）
│   ├── volume_alert.py           # ⬜ 出来高急増検知（未着手・Phase D）
│   └── [その他テスト・ユーティリティ]
│
├── data/
│   ├── raw/
│   │   └── usdjpy_multi_tf_2years.parquet  # 2年分マルチTF USDJPYデータ
│   │       # 83,112本 / 5M足 / 期間: 2024-03-13〜2026-03-13
│   └── private_trades.csv
│
├── logs/
│   ├── png_data/
│   │   ├── multi_pairs_plot_8.png           # --trade 自動保存（8ペア正規化プロット）
│   │   └── YYYY_MM_DD_snapshot.yaml         # --trade 自動保存（レジーム + スナップショット）
│   ├── text_log/
│   │   └── conversation_history.json        # 会話履歴（永続化）
│   ├── plots/                               # 5M Swing確認PNG
│   ├── base_scan/                           # 4H+15M基礎スキャン結果
│   ├── structure_plots/                     # 4H+1H構造確認PNG（16枚）
│   ├── 1h_windows/                          # 1H窓 + 5M重ね合わせPNG（8枚）
│   ├── window_scan_plots/                   # 窓ベーススキャン結果PNG（5枚・#021〜#023）
│   └── window_scan_entries.csv              # エントリー記録CSV（5件）
│
└── docs/
    ├── SYSTEM_OVERVIEW.md                   # 本ファイル（概要・現状把握用）
    ├── EX_DESIGN_CONFIRMED-2026-3-26_2.md   # ★ 設計確定文書（詳細設計の正本）
    ├── PLOT_DESIGN_CONFIRMED-2026-3-26.md   # プロット設計
    ├── STATUS.md                            # 週次マーケットブリーフ + ポジション追跡
    ├── FILE_MAP.md                          # ファイルロールマッピング
    ├── BRANCH_MAP.md                        # Gitブランチ戦略
    ├── Backtest_template_v2.md              # バックテスト要件定義
    ├── WEEKLY_UPDATE_WORKFLOW.md            # 週末Git更新手順
    └── System_logs/                         # フェーズ別開発ログ（#006〜#0012）
```

---

## 依存関係と環境設定

**Pythonパッケージ** (requirements.txt):
- `yfinance` / `pandas` / `numpy` / `pyarrow` — データ取得・分析・Parquet I/O
- `matplotlib` — チャートプロット
- `feedparser` / `beautifulsoup4` — RSSパース・記事スクレイピング
- `requests` / `python-dotenv` — HTTP・.env読み込み
- `streamlit` — Webダッシュボード（任意）
- `vectorbt` — バックテストメトリクス（Sharpe / PF / MaxDD、任意）

**環境変数 (.env)**:
- `XAI_API_KEY` — xAI APIキー（必須）
- `XAI_MODEL` — モデル指定（例: `grok-4-fast`）
- `XAI_REQUEST_TIMEOUT` — タイムアウト秒（デフォルト: 180）
- `XAI_MAX_RETRIES` — リトライ回数（デフォルト: 5）
- `POLYGON_API_KEY` — Polygonフォールバック（任意、無料枠 5 req/分）

---

## 戦略レイヤー：ミナト流 MTF 押し目買いルール（確定版）

**戦略の本質**:
「4H上昇ダウが継続している限り、押し目条件が揃うたびにエントリーを繰り返す構造」
エリオット波数カウント・「初動3波狙い」表現は使用しない。

### MTF 階層スキャン構造

```
LAYER 1 — 4H 上昇トレンド
  SH/SL の高値・安値切り上げ確認（上昇ダウ）
  params: n=3, lookback=20, MIN_4H_SWING_PIPS ≥ 20 pips

LAYER 2 — 1H 押し目ウィンドウ
  4H SL ts ±8本(8時間)窓内で最近傍 1H SL を探す
  窓サイズ: 前20本 + SL足 + 後10本 = 計31時間（≈372本の5M足）

LAYER 3 — 窓内 15M/5M スキャン
  窓内 5M → 15M リサンプル
  → check_15m_range_low() で DB / IHS / ASCENDING 判定
  → 15M ネック越え 5M 実体確定 → エントリー
```

### エントリー詳細条件

**Step 1: 4H 押し目確認（Fib + 1H neck + support_1h）**
- 優位性★★★: `fib_pct ≤ 0.55` かつ 1H neck ±20pips以内 かつ `sl_last ≥ support_1h`
- `ALLOWED_GRADES = ['★★★']` により★★は現在フィルター除外中

**Step 2: 15M 統合レンジロジック確認**
- DB（2番底）: `SL_last ≒ SL2`
- IHS（逆三尊右肩）: `SL_last ≤ SL2`
- ASCENDING（安値切り上げ）: `SL_last > SL2`
- 共通: SL_min 以降に 15M SH が存在（ネック形成確認）
- `LOOKBACK_15M_RANGE = 50`

**Step 3: 5M DB ネックライン実体確定**
- `min(open, close)` が neck_15m を上抜け確定した足
- `WICKTOL_PIPS = 5.0`
- 執行: 確定足の次の5M始値（指値方式は廃止）

### エグジット 4段階

| 段階 | トリガー | 決済内容 |
|------|---------|---------|
| **初動SL** | エントリー直後〜5M Swing確定前 | 15M ダウ崩れ実体確定→次足始値で全量損切 |
| **段階1** | 5M Swing確定後〜1H ネック未到達 | 5M ダウ崩れ実体確定→次の5M始値で全量決済 |
| **段階2** | 4H ネックライン到達 | 50%決済・残り50%のSLを建値移動（ノーリスク化） |
| **段階3** | 4H ネック + 1H 実体確定後 | 15M ダウ崩れ実体確定→次の15M始値で残り全量決済 |

### パラメータ確定値

| 定数 | 値 | 確定タイミング |
|------|----|--------------|
| `DIRECTION_MODE` | `'LONG'`（SHORT一時停止） | #012 |
| `MAX_REENTRY` | 1 | #020 |
| `WICKTOL_PIPS` | 5.0 | #013 |
| `MIN_4H_SWING_PIPS` | 20.0 | #010 |
| `NECK_TOLERANCE_PIPS` | 20.0 | #017 |
| `ALLOWED_PATTERNS` | DB / IHS / ASCENDING | #014 |
| `ALLOWED_GRADES` | ★★★ | #018 |
| `LOOKBACK_15M_RANGE` | 50 | #014 |
| `WARMUP_BARS` | 1728（120日×5M） | #012 |
| `WINDOW_1H_PRE` | 20本 | #020 |
| `WINDOW_1H_POST` | 10本 | #023 |

---

## データフロー

```
yfinance（優先）/ Polygon API（フォールバック、5 req/分）
        ↓
data_fetch.py :: fetch_multi_tf()
  └─ 5M / 15M / 1H / 4H / D → Parquet 保存
        ↓
前処理（UTC→JST変換・TFごとffill）

【旧エンジン — ベースライン保持・変更凍結】
        ↓
signals.py（廃止方向）
        ↓
entry_logic.py :: evaluate_entry()（3ステップ）
        ↓
backtest.py :: _simulate_trade()（バー毎P&L）
  → PF 5.32 / 勝率 55.0% / MaxDD 14.9 pips / 総損益 +91.6 pips（#018確定値）

【新エンジン — window_scanner.py（#021〜#023）】
        ↓
swing_detector :: get_direction_4h() → 4H LONG期間抽出
        ↓
window_scanner :: scan_4h_events() → 4H SL イベント収集（89件）
        ↓
window_scanner :: get_1h_window_range() → 1H窓確定（31時間）
        ↓
window_scanner :: scan_window_entry()
  └─ check_15m_range_low() → DB / IHS / ASCENDING 判定
  └─ 5M ネック実体確定 → エントリー記録
  → 5件検出（DB:2 / IHS:1 / ASCENDING:2）★ #023確定値
        ↓
【#024 — 未着手・最優先】
exit_logic :: manage_exit() 統合 → P&L・PF・勝率・MaxDD 計算
```

---

## バックテスト結果推移

| 指標 | #009 | #011 | #018（旧版・凍結） | #023（新版 Phase 1） |
|------|------|------|-------------------|---------------------|
| 総トレード数 | 25件 | 36件 | 20件 | 5件 |
| 勝率 | 48.0% | 55.6% | 55.0% | 未計算 |
| PF | 0.98 | 2.86 | **5.32** | 未計算（#024で実施） |
| MaxDD | 106.5 pips | 27.4 pips | **14.9 pips** | 未計算 |
| 総損益 | -2.2 pips | +79.1 pips | **+91.6 pips** | 未計算 |
| モード | LONG+SHORT | LONG限定 | LONG+★★★限定 | LONG+窓ベース |

**#018 パターン別（★★★のみ・20件）:**
- DB: 9件 / 勝率 75.0% / +7.1 pips
- ASCENDING: 10件 / 勝率 60.0% / +3.7 pips
- IHS: 1件 / 勝率 0.0% / -2.2 pips（サンプル不足・継続監視）

---

## --trade モード フロー（週末 GM レビュー）

```
python main.py --trade [--news]
        ↓
market.py :: fetch_trade_data()（8ペア 30日）
        ↓
regime.py :: build_regime_snapshot()
  └─ equities / volatility / oil / gold / crypto / yields を判定
  └─ ラベル例: "Geopolitical Risk-Off + Energy Shock"
        ↓
plotter.py :: save_normalized_plot()
  └─ logs/png_data/multi_pairs_plot_8.png 保存
        ↓
YAML スナップショット保存
  └─ logs/png_data/YYYY_MM_DD_snapshot.yaml
        ↓
rex_chat.py :: インタラクティブ対話
  └─ systemメッセージにレジーム・市場データを注入した状態で開始
```

---

## 現在の運用フロー（週末の理想形）

1. **データ取得 & Rex 対話**
   ```
   python main.py --trade [--news]
   ```
   → 8ペア30日データ取得・レジーム判定
   → `logs/png_data/` に `multi_pairs_plot_8.png` と `YYYY_MM_DD_snapshot.yaml` を自動保存
   → レジームサマリー注入済みで Rex との対話開始

2. **バックテスト実行（確認用）**
   ```
   python src/backtest.py
   ```
   → 旧版 #018 ベースライン確認用（変更凍結）

3. **週末 Git 更新（手動）**
   - `multi_pairs_plot_8.png` → 当該週の `logs/gm/weekly/2026/YYYY-MM-DD_wkNN/charts/` にコピー
   - `YYYY_MM_DD_snapshot.yaml` の `regime.label` を `meta.yaml` の `signals` に追記
   - 詳細: `docs/WEEKLY_UPDATE_WORKFLOW.md` 参照

4. **レビュー生成**
   Rex に「このデータで週明け動向分析して」と依頼 → `review.md` / `meta.yaml` にコピペ

---

## 次のステップ（開発ロードマップ）

| 優先度 | # | 内容 |
|--------|---|------|
| 🔴 最優先 | #024 | `window_scanner.py` に `manage_exit()` を統合 → 5件の P&L シミュレーション・PF/MaxDD 計算 → 旧版 #018（PF 5.32）と比較 |
| 🟡 次フェーズ | Phase 2 | 15M 右肩内での 5M DB ネック実体上抜けによる精度向上版エントリー |
| 🟡 次フェーズ | 窓幅精査 | `get_1h_window_range()` の境界計算統一（実害なし・Phase 2 で対応） |
| ⬜ 将来 | Phase D | `volume_alert.py` — 出来高急増検知 + LINE 通知 |
| ⬜ 将来 | Phase 3 | Vision AI 自動チェック（PNG → Gemini/GPT-4o） |
| ⬜ 将来 | — | SHORT 運用再開（サンプル充足後） |
| ⬜ 将来 | — | マルチペア拡張（EUR/JPY・XAU/USD 等） |

---

## 開発履歴（フェーズサマリー）

| # | 主な内容 | 結果 |
|---|---------|------|
| #001〜#008 | Phase A 基盤構築（swing_detector / entry_logic 基礎） | 完了 |
| #009 | 決済ロジック 4段階実装（exit_logic.py 刷新） | 完了 |
| #010 | MIN_4H_SWING_PIPS=20 導入（4H幅ガード） | 完了 |
| #011 | 15M 統合レンジロジック（DB/IHS/ASCENDING 統合） | 完了 |
| #012 | LONG限定化・フォールバック修正・WARMUP_BARS=1728 | 完了 |
| #013 | WICKTOL_PIPS=5.0・IHSフラグ除外 | 完了 |
| #014 | IHS 復活・LOOKBACK_15M_RANGE=50 | 完了 |
| #015 | base_scanner.py 新規作成（4H+15M基礎スキャン） | 完了 |
| #016 | neck_4h=1H SH に修正（★★★が成立しないバグ修正） | 完了 |
| #017 | NECK_TOLERANCE_PIPS=20.0（pips 基準修正） | 完了 |
| #018 | ALLOWED_GRADES=['★★★']・クロス集計 → **PF 5.32 / MaxDD 14.9 pips** | 完了・凍結 |
| #019 | structure_plotter.py 新規・4H+1H構造確認（16枚） | 完了 |
| #020 | 1H-4H 一致検証（100%・数学的必然）・窓プロット | 完了 |
| #020-fix | plotter.py バグ修正（addplot→scatter / CJK→英語） | 完了 |
| #021 | window_scanner.py 新規作成（窓左端バグあり・13件誤検出） | 完了 |
| #022 | タイミングバグ修正（1H SL 以降限定）→ 2件 | 完了 |
| #023 | WINDOW_1H_POST=10 に延長 → **5件（DB:2/IHS:1/ASCENDING:2）** | 完了 |

---

## 思考フラグ運用ルール（ClaudeCode 向け）

| フラグ | 使うタイミング |
|--------|--------------|
| `think` | 単純な修正・パラメータ変更 |
| `think hard` | 複数ファイル修正・バグ修正 |
| `think harder` | 設計判断が必要な実装 |
| `ultrathink` | アーキテクチャ全体変更・最適化 |

---

## Git 運用

作業ブランチ命名: `claude/[作業内容]-[ID]`
mainへのマージ: テスト確認後

コミットメッセージ規則:
```
新機能:       Feat: #NNN ...
バグ修正:     Fix: #NNN ...
パラメータ:   Tune: #NNN ...
ドキュメント: Docs: ...
削除:         Remove: ...
```
