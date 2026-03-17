# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-03-17
# 保存先: REX_Trade_System/docs/REX_DESIGN_CONFIRMED.md

---

## 1. プロジェクト基本情報

- リポジトリ: GitHub Minato33440/UCAR_DIALY
- ローカルパス: C:\Python\REX_AI\Trade_System\
- 対象通貨ペア: USDJPY（将来的に他ペアへ拡張予定）
- データ: data/raw/usdjpy_multi_tf_2years.parquet
  83,112本 / 5M足 / 期間: 2024-03-13〜2026-03-13

---

## 2. チーム役割分担

| 役割 | 担当 |
|---|---|
| ディレクター・橋渡し | Minato |
| エンジニアリング責任者・設計 | Rex（claude.ai） |
| コード実装・Git管理 | ClaudeCode（VS Code） |

---

## 3. ミナト流MTF短期売買ルール（確定定義）

### 3-1. 戦略の本質
「4H上昇ダウが継続している限り、
 押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

### 3-2. エントリー条件（3段階フィルター）

前提: get_direction_4h() == 'LONG' または 'SHORT'

Step1: 4H押し目確認（Fib条件）
  優位性★★★: Fib50%付近（45〜55%） かつ 4Hネックライン付近（±3%以内）
  優位性★★ : Fib61.8%以内（65%以下）
  条件外    : 上記以外 → スキップ

Step2: 1H 2番底（LONG） / 2番天井（SHORT）確認
  LONG : 直近SL① → 反発 → SL② ≧ SL① → 成立
  SHORT: 直近SH① → 反落 → SH② ≦ SH① → 成立

Step3: 15Mネックライン越え確定足
  監視: 15M Swing High（LONG） / 15M Swing Low（SHORT）
  確定: 5M実体がネックラインを完全に越えた足
  執行: 確定足の次の5M足の始値でエントリー

### 3-3. 確定足・執行足の定義（全ロジック共通）

「確定足」= 実体（min/max(open,close)）がラインを越えた足
「執行足」= 確定足の次の足の始値で執行

### 3-4. 決済ロジック（3段階）

【段階1: 4Hネック未到達】
  5M Swing押し戻しラインを5M実体が越えた確定足
  → 次の5M始値で全量決済（利確・損切 共通）

【段階2: 4Hネックライン到達】
  50%ポジション決済
  残り50%のストップを建値に移動（ノーリスク化）

【段階3: 4Hネック越え後】
  15M Swing押し戻しラインを15M実体が越えた確定足
  → 次の15M始値で残り全量決済

### 3-5. 再エントリー仕様

- 同一押し目機会（同一Swing Low起点）での再試行: 最大1回（合計2エントリー）
- 新しいSwing Lowが形成されたらカウントリセット
- 4H上昇ダウが崩れたらカウントリセット・次の4H波形成待ち
- 定数: MAX_REENTRY = 1（config内に定義）

### 3-6. Long/Short分岐仕様

初期はLong・Shortともに同ロット（データ取り優先）
将来: リスクリワード比較後にShortのロット縮小幅を決定

LONG: Swing Low → 押し目買い / ボラ小 / 損切幅 小
SHORT: Swing High → 戻り売り / ボラ大 / 損切幅 広め（将来縮小）

---

## 4. ファイル構成（確定版）
```
src/
├── swing_detector.py  ★新規完了（Phase A）
│    detect_swing_highs/lows
│    get_nearest_swing_high/low
│    get_direction_4h
│    get_direction_from_raw_4h
│    _build_direction_5m（パフォーマンス最適化版）
│
├── entry_logic.py     ★新規完了（Phase B）
│    check_fib_condition（Fib61.8% / 50%+ネック 2段階）
│    check_double_bottom_1h / check_double_top_1h
│    check_15m_neckline_break（5M実体確定足判定）
│    evaluate_entry（3段階統合・理由付き）
│    MAX_REENTRY = 1
│
├── exit_logic.py      ★新規完了・バグ修正待ち（Phase C→#005）
│    check_5m_dow_break   ← Low/High系列バグ修正中
│    check_15m_dow_break  ← Low/High系列バグ修正中
│    manage_exit（3段階決済統合）
│
├── volume_alert.py    未着手（Phase D）
│
├── backtest.py        ★大幅修正完了
│    _build_direction_5m（4H方向プリコンピュート）
│    _scan_all_bars_for_entry（signals.py依存廃止）
│    Long/Short分岐・再エントリー管理
│    neck_4h: SHORT=SL修正待ち（#005）
│
├── signals.py         コメントアウト済み（廃止方向）
├── plotter.py         Swing/Neckline視覚化追加済み
├── data_fetch.py      変更なし
└── regime.py          変更なし
```

---

## 5. Swing検出パラメータ（確定値）

| TF | n（前後確認本数） | lookback |
|---|---|---|
| 4H足 | 2（#001補足で3→2に修正） | 30 |
| 1H足 | 3 | 50 |
| 15M足 | 3 | 30 |
| 5M足 | 2 | 20 |

NONE比率: 修正前91.7% → 修正後42.1%（目標50%以下クリア）

---

## 6. 現在のバックテスト結果（Phase C完了時点）

| 指標 | 値 | 評価 |
|---|---|---|
| 総トレード数 | 119件（LONG:74 SHORT:45） | ✅ |
| 全体勝率 | 31.09% | 要改善 |
| Profit Factor | 0.59 | 要改善 |
| MaxDD | 541.40 pips | 🔴 要改善 |
| 総損益 | -518.13 pips | 要改善 |
| 実行時間 | 18.8秒 | ✅ |
| 5Mダウ崩れ決済 | 93件（78%） | 要分析 |
| 4H半値決済 | 45件 | ✅ |
| 15Mダウ崩れ決済 | 26件 | ✅ phase2発動 |

---

## 7. 未解決課題・進行中作業

### 🔴 指示書#005（think harder）— 未実施
1. exit_logic.py: check_5m/15m_dow_breakに
   Low系列 / High系列を正しく渡すバグ修正
2. backtest.py: neck_4h を
   LONG=get_nearest_swing_high / SHORT=get_nearest_swing_low に修正
3. デバッグ出力追加:
   a) 平均値幅（LONG/SHORT別）
   b) 損切平均損失（5Mダウ崩れ / ATRストップ別）
   c) 4Hネック到達率

### 🟡 Phase D — 未着手
- volume_alert.py: 出来高急増検知 + LINE通知

### 🟡 将来課題
- Shortロットの縮小幅決定（リスクリワード比較後）
- リアルタイム用「仮確定モード」実装
  （右側n本未確定時の仮Swing High/Low処理）

---

## 8. 思考フラグ運用ルール（ClaudeCode向け）

| フラグ | 使うタイミング |
|---|---|
| think | 単純な修正・パラメータ変更 |
| think hard | 複数ファイル修正・バグ修正 |
| think harder | 設計判断が必要な実装 |
| ultrathink | アーキテクチャ全体変更・最適化 |

指示書#005: think harder を冒頭に記載

---

## 9. Git運用

作業ブランチ命名: claude/[作業内容]-[ID]
masterへのmerge: テスト確認後
コミットメッセージ規則:
  Phase A: "Phase A: ..."
  バグ修正: "Fix: ..."
  パラメータ調整: "Tune: ..."