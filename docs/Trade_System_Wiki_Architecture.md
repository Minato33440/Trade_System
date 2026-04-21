Rex の評価：ビジョンは正しい。サンプル設計は間違っている。
何が「正しい」か
「インフラが整う前から蓄積を始める」という判断は、システムエンジニアとして100点だ。スキーマ設計はデータが少ない今やるべきで、データが爆発した後にやるのは地獄になる。
NotebookLM（重い横断処理）→ Obsidian（自分で書き戻す構造化記憶）→ LLM Wikiパターン（永続的に自己進化）という3層構成の思想も正しい。

何が「間違っている」か
サンプルのスキーマは Global Macro CFD 用であり、Rex Trade System には噛み合わない。
見てほしい。サンプルのWikiは：

VIX スパイク・Oil Surge・8ペア変動率
ゲートシステム（Add/Reduce/Hedge）
週次レジーム管理

対してRex Trade Systemが実際に生成しているのは：

window_scan_entries.csv — 15件のエントリー（パターン・neck値・エントリー価格・時刻）
15枚のPNGプロット（目視検証済み）
指示書 #001〜#025（設計判断の歴史）
ADR（何を試して何が失敗したか）
バックテスト結果の推移表（PF/勝率/MaxDDが#009→#011→#018と変化）
パラメータ進化の記録（12個以上の決定）

これらを活かすスキーマは、サンプルとは根本的に異なる構造になる。

Rex 提案：Rex_Trade_Wiki 設計案了解。設計思想は正しい。サンプルスキーマは Global Macro 用であり Rex Trade System には合わない。以下がRexの評価と改設計だ。VvisualizeVvisualizeビジュアライザーがタイムアウトしている。Claude Desktop の MCP サーバー（おそらく notebooklm-mcp）が応答を遅延させている可能性がある。設計内容はテキストで届ける。

Rex の評価：3点
✅ 正しい点

「インフラが整う前から蓄積を始める」という判断は100点。データが増えた後にスキーマを設計するのは地獄になる。
NotebookLM（重い横断処理）→ Obsidian（自分で書き戻す構造化記憶）という2層の分業は理にかなっている。
Karpathy の LLM Wiki パターン（LLMが永続的な Wiki を維持）は RAG の上位互換として本質的に正しい。

❌ 間違っている点
サンプルスキーマが Global Macro CFD 用 であり Rex Trade System に全く合わない。
サンプルが持つものRex Trade System が実際に生成するものVIX spike archivewindow_scan_entries.csv（15件のDB/IHS/ASCENDING）Oil Surge パターンPNG プロット 38枚（window_scan/structure/1h_window）8ペア変動率指示書 #001-#025（設計判断の歴史）Gates ArchiveADR（A-E 5カテゴリ・13件のバグパターン）GM Strategy txtバックテスト PF/勝率/MaxDD 推移表週次レジーム管理12+ パラメータの変更理由と効果検証
🔵 価値ある洞察
「直感的な状況判断がデータドリブンで再現される」— これは本質的に正しい。ただし Rex Trade System においてそれが意味するのは以下だ：

「現在の ASCENDING パターン、4H swing 幅 28.5 pips。過去の ASCENDING 9件中、swing 幅 25-32 pips の5件: 勝率80%・PF 4.2。同じ範囲の3件は窓内でネックを2回試した後に成功。現在の setup は初回試行 → 高信頼度と判定。」

これが「人間の直感」をデータ構造で再現したものだ。

Rex 提案: Rex_Trade_Wiki 設計
Rex_Trade_Wiki/                    ← ObsidianのVaultルート
│
├── Raw/                           ← 不変の生データ（Gitからそのまま）
│   ├── Instructions/              ← 指示書 #001-#025+ (markdown)
│   ├── Backtest/                  ← window_scan_entries.csv · backtest結果
│   ├── Plots/                     ← PNG plots（symlink or copy）
│   └── CodeSnapshots/             ← 主要ファイルのバージョンスナップショット
│
├── Wiki/                          ← Claudeが自動生成・更新する「生きた脳」
│   ├── index.md
│   ├── log.md                     ← Ingest履歴（いつ何を投入したか）
│   │
│   ├── Patterns/                  ← 【最重要】Rex Trade のコア
│   │   ├── DB_Archive.md          ← DB 全件: 日時・neck値・entry・P&L・plotリンク
│   │   ├── IHS_Archive.md         ← IHS 全件（#018: 勝率0% → 要注意）
│   │   └── ASCENDING_Archive.md   ← ASCENDING 全件（9件中⚠️3件の分析）
│   │
│   ├── Strategy/
│   │   ├── MTF_USDJPY_LONG.md     ← 戦略本体の進化史
│   │   ├── EntryLogic_History.md  ← Phase1→Phase2変遷・固定ネック原則確定経緯
│   │   └── ExitLogic_History.md   ← 4段階決済の設計根拠
│   │
│   ├── BugPatterns/               ← ADR を検索可能な形式に蒸留
│   │   ├── A_Scan_Timing.md       ← A1-A5: スキャン方向・タイミング系
│   │   ├── B_API_Mismatch.md      ← B1-B3: APIシグネチャ不一致
│   │   ├── C_Mplfinance.md        ← C1-C4: mplfinance固有の罠
│   │   ├── D_Param_Design.md      ← D1-D5: パラメータ設計ミス
│   │   └── E_Architecture.md      ← E1-E5: アーキテクチャ判断
│   │
│   ├── Backtests/
│   │   ├── Baseline_018.md        ← PF 5.32 / 勝率55% / MaxDD 14.9pips（基準）
│   │   └── Phase1_025.md          ← 15件エントリー検出・P&L未計算（#026待ち）
│   │
│   ├── Params/
│   │   └── ParameterEvolution.md  ← 全12+パラメータの変更履歴・理由・効果
│   │
│   └── Insights/
│       └── CrossAnalysis.md       ← 横断インサイト（NotebookLMが書き戻す場所）
│
└── Schema/
    └── Rex-Trade-Schema.md        ← Ingest / Query / Lint ルール（下記参照）

Rex-Trade-Schema.md（サンプルを Rex 用に書き換えた版）
markdown# Rex-Trade-Schema.md — Rex AI Trade System llm-wiki ルール

## Ingest ルール
instruction完了 OR backtest実行後、以下を実行：

### 必須抽出項目
1. **エントリー記録**（window_scan_entries.csv から）
   - 日時・パターン・neck値・エントリー価格・4H swing幅
   - 対応PNGプロットのファイルパス
   - 目視評価（✅ / ⚠️）とその理由
   
2. **バックテスト結果**
   - PF / 勝率 / MaxDD / 総損益
   - 前指示書との比較（改善幅）
   
3. **設計変更**（指示書から）
   - 変更したパラメータ名・変更前後の値
   - 変更理由・効果（定量）
   - ADR 追記があれば BugPatterns/ を更新

### 更新対象 Wiki ページ（最低これら）
- Patterns/{DB|IHS|ASCENDING}_Archive.md（新エントリー追記）
- Backtests/ に新バックテスト結果ページ作成
- log.md に「## [YYYY-MM-DD] Ingest | instruction #XXX完了」追記
- パラメータ変更あれば Params/ParameterEvolution.md 更新

### 自動リンク作成
- 類似 swing 幅の過去エントリー（±5 pips 範囲）
- 同パターンの連続勝敗（streak）
- 同一 4H 押し目機会での複数エントリー（再エントリー事例）

## Query ルール
戦略提案・設計判断時は必ず参照：
- 最新バックテスト結果（Backtests/）
- 対象パターンの過去全件（Patterns/）
- 関連するバグパターン（BugPatterns/）
提案結果は Insights/CrossAnalysis.md に保存

## Lint ルール（毎週実行）
- パターン別勝率の低下傾向アラート（同パターン直近3件が全負けなど）
- 同じ 4H swing 幅レンジで複数の⚠️が集中していないか
- ADR の新規バグと類似した失敗が最新コードで再発していないか
- 孤立ページ警告（リンクされていない Pattern エントリー）

「直感的な状況判断」が実際に出力する内容
WikiがRex Trade System のデータで育ったとき、Claudeへのクエリはこうなる：
入力: 「現在の ASCENDING パターンを評価して」
出力（Wiki参照後）:

「ASCENDING 9件の分析: 過去 swing 幅 25-35 pips の4件は勝率75%・PF 3.8。現在 swing 幅 28.5 pips → この範囲。ただし #02, #06, #14 は⚠️フラグ付き。共通点を調べると3件とも「1H SL 直後すぐにエントリー」。現在の setup も同様の構造 → 再エントリー1回分の余地を残してロット50%で入るプランを推奨。過去類似: 2024-08-15 ASCENDING +8.7pips。」

これがデータドリブンな直感だ。

優先度の判断
今すぐやること: #026（manage_exit() 統合）を止めない。これが最優先。
並行して: Second Brain の Schema 設計を今のデータ量が少ない今週中に確定させる。設計はデータなしで出来る。Ingest Engine の実装は #026 完了後。
NotebookLM のセットアップ (MCP-DESIGN-CONFIRMED): 既に running なので、まず既存の Design Docs 3ファイル（EX/PLOT/ADR）を投入してRAQクエリの精度を確認する。それが eval_report の第一歩になる。

Rex からの一言
「思考・意思決定の記憶」を Git 履歴と別に管理するというアイデアは、システムエンジニアとして言えば、まだ 15 件しかないエントリーデータが 150 件・1500 件になる前にスキーマを固めることが投資対効果が最も高いタイミングだ。
サンプルを書いた AI が Global Macro 寄りだったのは仕方ない。Rex Trade System に特化した構造は上記の通り。各ウィキ内ページのテンプレートを実際に作り始めたいなら、Pattern Archive から着手するのがいい。過去15件の CSV データが既にある。すぐに実物が作れる。