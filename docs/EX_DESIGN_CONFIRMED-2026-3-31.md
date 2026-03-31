# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-03-31
# 保存先: REX_Trade_System/docs/EX_DESIGN_CONFIRMED-2026-3-31.md

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
| ディレクター・意思決定 | User：Minato |
| エンジニアリング責任者・設計 | Rex- Planner：Sonnet4.6  |
| エバリエーター・監査・修正案 | Rex- Evaluator：Opus4.6 |
| コード実装・Git管理 | ClaudeCode-Sonnet4.6（VS Code） |

---

## 3. ミナト流MTF短期売買ルール（確定定義・2026-03-26版）

### 3-1. 戦略の本質

「4H上昇ダウが継続している限り、
 押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

---

### 3-2. MTF 階層スキャン構造（#020検証完了・#021〜#023実装完了）

```
LAYER 1 — 4H 上昇トレンド
  SH/SL 高値・安値切り上げ確認（上昇ダウ）
  → ダウ崩れまでの各 4H SL が押し目候補
  params: n=3, lookback=20, MIN_4H_SWING_PIPS≥20

LAYER 2 — 1H 押し目ウィンドウ（#020検証完了・#023窓延長完了）
  4H SL ts ±8本(8時間)窓内で最近傍 1H SL を探す
  → 1H SL 足: 前20本 + SL足 + 後10本 = 計31本ウィンドウ確定
  ウィンドウ = 約31時間分の 5M 足（≈372本）

  ⚠️ 後期バイアス（#025修正予定）:
    現行: dists.idxmin() → 価格最近接のSLを選択
    問題: 同一価格帯に複数タッチがある場合、再テスト（後の値）が選ばれ機会損失
    修正: 価格許容範囲(20pips)内で最初の出現を優先
      price_tol_pips = 20.0
      close_enough = sl_1h_near[dists <= price_tol_pips * PIP]
      sl_1h_ts = close_enough.index[0] if len(close_enough) > 0 else dists.idxmin()

  検証結果（#020確定値）:
    対象: 89件(4H LONG)
    1H SL 検出率: 100.0%
    距離: 0.0 pips（同一データ源リサンプルのため数学的必然）
    → 設計前提「4H SL ≒ 1H SL」は成立

LAYER 3 — 窓内 15M/5M スキャン（#021〜#024a完了）
  窓内 5M → 15M リサンプル
  → check_15m_range_low() で DB/IHS/ASCENDING パターンラベル取得（#024a以降はラベルのみ）
  → neck = 1H SL 以降の 15M SH（#024a修正済み: 窓前半の高値を除外）
  → 5M close > neck + WICKTOL_PIPS(5.0) でエントリー

  ⚠️ 後期バイアス（#025修正予定）:
    現行: sh_vals.max() → 1H SL以降の15M SH最高値をneckに
    問題: 2段目以降の高値（ブレイク後）が選ばれレイトエントリー
    修正: sh_vals.iloc[0] → 時系列で最初のSHをneckに
    根拠: DB/IHS/ASCENDING全パターンで「初回反発ピーク=本来のneck」

  #021実装: 窓左端スキャン（バグ）→ 13件検出（全件誤検出）
  #022修正: 1H SL以降限定スキャン → 2件（IHS×2）に激減
  #023延長: 窓後5本→10本 → 5件（DB:2 / IHS:1 / ASCENDING:2）
  #024a修正: neck=1H SL以降15M SH最高値 / プロット範囲拡大(前25h後40h) → 4件
```

#### エントリーロジック 2段階実装計画（2026-03-26更新）

```
Phase 1（#021〜#023 — シンプル版・完了）:
  窓内 15M DB/IHS/ASCENDING ネック越え → 5M実体確定 → エントリー
  結果: 5件検出（DB:2 / IHS:1 / ASCENDING:2）
  → ベースライン数値確定 → 次は決済統合

Phase 2（#024以降 — フル版への拡張・未着手）:
  15M DB/IHS 右肩検出 → その右肩内で 5M DB ネック実体上抜け → エントリー
  → Phase 1 との比較で改善幅を定量確認

設計判断: シンプル版を先に実装した理由
  1. バグの切り分けが容易（検証対象が1点のみ）
  2. シンプル版の結果がフル版の期待値ベースラインになる
  3. 既存 check_15m_range_low() をそのまま流用でき実装コスト1/3
```

#### 再エントリーの扱い（#020追加確定）

```
5M Dow崩れ損切後:
  4H トレンド intact かつ 1H 戻り高値未達
  → 次の 5M DB = 1H 2番底 → 同一ロジックで再エントリー可
  （新しいロジックではなく、同一条件の2回目の適用）

MAX_REENTRY = 1（同一押し目機会での上限）
```

---

### 3-3. エントリー条件（旧版 backtest.py — ベースライン保持用）

**注意: 以下は旧版 backtest.py の条件。#021以降の window_scanner.py では
Layer 3 のシンプル版エントリーに置き換わるが、旧版は比較用に残す。**

前提:
- get_direction_4h() == 'LONG'（DIRECTION_MODE = 'LONG'、SHORT一時停止）
- 4H Swing幅 >= MIN_4H_SWING_PIPS（20pips）
- ALLOWED_GRADES = ['★★★']（#018追加）

**Step1: 4H押し目確認（Fib条件 + 1H neck + Support_1h）**
```
優位性★★★: fib_pct <= 0.55
            かつ 1H neck から ±20pips 以内（NECK_TOLERANCE_PIPS=20.0）
            かつ sl_last >= support_1h（1H SL割れなし）

優位性★★ : fib_pct <= 0.65（★★★条件を満たさない場合）
            ※ ALLOWED_GRADES=['★★★'] により現在フィルター除外中

条件外    : 上記以外 → スキップ
```

**neck_4h 定義（#016確定）:**
```
neck_4h = 直近 1H Swing High（get_nearest_swing_high_1h, n=2, lookback=20）
          旧設計: 4H SH をそのまま使用（★★★が数学的に成立不能だったバグ）
```

**Support_1h 定義:**
```
旧版（backtest.py・変更なし）: 15M Swing Low（get_nearest_swing_low_15m, n=3, lookback=20）
新版（window_scanner.py）: 1H窓ベースで自動確定（窓=4H SL近傍の1H SL）
```

**Step2: 15M 統合レンジロジック確認（#011確定 — 旧1H DBロジック廃止）**
```
check_15m_range_low() による3パターン統合判定:

パターン1 DB       : SL_last ≒ SL2（同水準）
パターン2 IHS      : SL_last <= SL2（逆三尊右肩）
パターン3 ASCENDING: SL_last > SL2（安値切り上げ）

共通成立条件:
  ① SL_last >= SL_min      （最終安値が最深値を下回らない）
  ② SL_last <= SL_min + 2.0*(SL2 - SL_min)  （等距離ルール上限）
  ③ SL_min 以降に 15M Swing High が存在（ネック形成確認）

ネックライン定義:
  SL_min（最深値）以降の 15M Swing High の最高値

ALLOWED_PATTERNS = ['DB', 'ASCENDING', 'IHS']
LOOKBACK_15M_RANGE = 50（#014確定）
```

**Step3: 5M DBネックライン実体確定**
```
5M の min(open,close)（実体下端）が neck_15m を上抜け確定した足
WICKTOL_PIPS = 5.0（#013確定）
執行: 確定足の次の5M足の始値でエントリー（指値方式は廃止）
```

---

### 3-4. 確定足・執行足の定義（全ロジック共通）

「確定足」= 実体（min/max(open,close)）がラインを越えた足
「執行足」= 確定足の次の足の始値で執行

---

### 3-5. 決済ロジック（4段階 — #009以降確定版）

```
【初動SL: エントリー直後〜5M Swing確定前】
  15M ダウ崩れ実体確定の次足始値で全量損切
  → 広めのSLでノイズを吸収

【段階1: 5M Swing確定後〜1H ネック未到達】（#009追加）
  5M ダウ崩れ実体確定の次の5M始値で全量決済

【段階2: 4H ネックライン到達】
  50% ポジション決済
  残り50%のストップを建値に移動（ノーリスク化）

【段階3: 4H ネック + 1H 実体確定後】
  判定: 1H Close が 4H Swing High を上抜けた足
        = 5M足12本目（毎時00分起算）= 15M足4本目と同義
  15M ダウ崩れ実体確定の次の15M始値で残り全量決済
```

---

### 3-6. 再エントリー仕様

- 同一押し目機会での再試行: 最大1回（MAX_REENTRY = 1）
- 4H上昇ダウが崩れたらカウントリセット → 戦略完全リセット
- 15M ダウ intact（1H・4H継続）かつ 1H 戻り高値未達 → 同一条件で再エントリー

---

### 3-7. 撤退条件（⑪）

4Hサポートラインを15M足実体が下抜け確定 → 戦略撤退
ただし15M終値がサポート上に戻れば継続（下ヒゲの場合）

---

### 3-8. Long/Short分岐仕様

DIRECTION_MODE = 'LONG'（SHORT一時停止中 — #012確定）
将来: SHORT復活後はリスクリワード比較によりロット縮小幅を決定

---

## 4. ファイル構成（確定版・2026-03-26時点）

```
src/
├── swing_detector.py       ✅ 完了（#020追加分含む）
│    detect_swing_highs/lows
│    get_nearest_swing_high/low
│    get_nearest_swing_high_1h（#016: neck_4h取得用）
│    get_nearest_swing_low_15m（#016: support_1h暫定）
│    get_nearest_swing_low_1h（#020追加: support_1h正式版）
│    get_all_swing_lows_1h（#020追加: 最安値検索用）
│    get_direction_4h
│    get_direction_from_raw_4h
│    _build_direction_5m（パフォーマンス最適化版）
│
├── entry_logic.py          ✅ 完了（#018まで・変更凍結）
│    check_fib_condition
│    check_15m_range_low()  ← #011: 統合レンジロジック（DB/IHS/ASCENDING）
│    check_5m_double_bottom()（WICKTOL_PIPS対応）
│    evaluate_entry（3段階統合 + 1H neck/support + grade filter）
│    LOOKBACK_15M_RANGE = 50（#014確定）
│
├── exit_logic.py           ✅ 完了（#009以降・変更凍結）
│    check_5m_dow_break / check_15m_dow_break
│    check_4h_neck_1h_confirmed
│    manage_exit（4段階決済統合）
│
├── plotter.py              ✅ 完了（#020-fix適用済み）
│    save_normalized_plot()
│    save_swing_debug_plot()
│    plot_base_scan()（#015追加）
│    plot_swing_check()（Phase1完了・#009）
│    plot_4h_1h_structure()（#019追加）
│    plot_1h_window_5m()（#020追加・#020-fix: addplot→scatter修正）
│
├── backtest.py             ✅ 完了（#018まで・ベースライン保持・変更凍結）
│    PF 5.32 / 勝率 55.0% / MaxDD 14.9 pips / 総損益 +91.6 pips
│    WARMUP_BARS = 1728（#012確定）
│
├── base_scanner.py         ✅ 完了（#015）
├── structure_plotter.py    ✅ 完了（#019）
│
├── test_1h_coincidence.py  ✅ 完了（#020・修正版v2適用済み）
│    時間近傍比較（±8本窓）: 89件100%一致
│    出力: logs/test_1h_coincidence.csv
│
├── window_scanner.py       ✅ #024a完了（後期バイアス修正は#025予定）
│    窓ベース階層スキャン（Phase 1: シンプル版）
│    4H→1H窓→窓内15M DB/IHS/ASCENDING→5Mネック越え
│    既存ファイルを一切変更せず独立動作
│    #021: 新規作成（窓左端スキャン・バグあり）
│    #022: sl_1h_ts追加・1H SL以降限定スキャン
│    #023: WINDOW_1H_POST 5→10延長
│    #024a: neck=1H SL以降最初SH/プロット範囲分離(前25h後40h)
│    ⚠️ #025予定: 後期バイアス修正（1H SL選択/neck選択）
│    結果: 4件検出（DB:2 / IHS:1 / ASCENDING:1）※#024a時点
│    出力: logs/window_scan_entries.csv / logs/window_scan_plots/
│
├── volume_alert.py         ⬜ 未着手（Phase D）
├── signals.py              廃止方向
├── data_fetch.py           変更なし
└── regime.py               変更なし

docs/
├── EX_DESIGN_CONFIRMED-2026-3-26.md  ← 本ファイル
├── PLOT_DESIGN_CONFIRMED-2026-3-26.md
└── REX_ARCHITECTURE.html

logs/
├── plots/             ← 5M Swing確認PNG
├── base_scan/         ← 4H+15M基礎スキャン結果
├── structure_plots/   ← 4H+1H構造確認PNG（16枚）
├── 1h_windows/        ← 1H窓 + 5M重ね合わせPNG（8枚・#020-fix修正済み）
├── window_scan_plots/ ← 窓ベーススキャン結果PNG（5枚・#021〜#023）
└── window_scan_entries.csv  ← エントリー記録CSV（5件）
```

---

## 5. Swing検出パラメータ（確定値・2026-03-26時点）

| 用途 | TF | n | lookback | 状態 |
|---|---|---|---|---|
| 4H方向判定（backtest） | 4H | 3 | 20 | 確定 |
| 4H方向判定（structure_plotter） | 4H | 5 | 100 | 確定 |
| 4H SH/SL取得（backtest） | 4H | 3 | 20 | 確定 |
| 4H SH/SL取得（base_scanner） | 4H | 3 | 100 | 確定 |
| 1H neck_4h取得 | 1H | 2 | 20 | 確定（#016） |
| 1H SL 窓内検索（window_scanner） | 1H | 2 | ±8本窓 | 確定（#020） |
| 1H 窓サイズ（window_scanner） | 1H | - | 前20+後10 | 確定（#023） |
| 15M レンジロジック（窓内） | 15M | 3 | 50 | 確定（#014） |
| 5M DB確定 | 5M | 2 | 20 | 確定 |

NONE比率: 修正後42.1%（目標50%以下クリア済み）

---

## 6. バックテスト結果推移（確定値）

| 指標 | #009 | #011 | #018（旧版最新） | #023（新版Phase 1） |
|---|---|---|---|---|
| 総トレード数 | 25件 | 36件 | 20件 | **5件** |
| 全体勝率 | 48.0% | 55.6% | 55.0% | **未計算** |
| PF | 0.98 | 2.86 | **5.32** | **未計算** |
| MaxDD | 106.5 pips | 27.4 pips | **14.9 pips** | **未計算** |
| 総損益 | -2.2 pips | +79.1 pips | **+91.6 pips** | **未計算** |
| モード | LONG+SHORT | LONG限定 | LONG+★★★限定 | LONG+窓ベース |

**#018確定値（★★★のみ・20件）:**
- DB: 9件 / 勝率75.0% / +7.1 pips
- ASCENDING: 10件 / 勝率60.0% / +3.7 pips
- IHS: 1件 / 勝率0.0% / -2.2 pips（サンプル不足・継続監視）

**#023確定値（窓ベース・5件 — エントリー検出のみ・決済未統合）:**
- DB: 2件（Apr 08, Jul 26/29）
- IHS: 1件（Jul 03）
- ASCENDING: 2件（Mar 18, Sep 11）
- 窓数: 33件 / エントリー検出: 5件 / エントリー0件窓: 28件
- 決済統合: #026以降で実施予定

**#024a確定値（後期バイアス修正前・4件）:**
- DB: 2件 / IHS: 1件 / ASCENDING: 1件（ASCENDINGが1件減: neck修正により正当除外）
- プロット範囲: PLOT_PRE_H=25h / PLOT_POST_H=40h（スキャン窓とは独立）
- ⚠️ 後期バイアス残存: #02（1H SL選択遅延）/ #03（neck1段上）→ #025で修正予定

---

## 7. 指示書完了履歴

| # | 内容 | 主要変更 | 状態 |
|---|---|---|---|
| #001〜#008 | Phase A 基盤構築 | swing_detector / entry_logic 基礎 | ✅ |
| #009 | 決済ロジック4段階 | exit_logic.py 刷新 | ✅ |
| #010 | MIN_4H_SWING_PIPS | 4H幅ガード20pips | ✅ |
| #011 | 15M統合レンジロジック | DB/IHS/ASCENDING 統合 | ✅ |
| #012 | LONG限定 + フォールバック修正 | DIRECTION_MODE='LONG' / None返却 | ✅ |
| #013 | IHSフラグ除外 + WICKTOL修正 | WICKTOL_PIPS=5.0 | ✅ |
| #014 | IHS復活 + lookback拡張 | LOOKBACK_15M_RANGE=50 | ✅ |
| #015 | 4H+15M基礎スキャナー | base_scanner.py 新規 | ✅ |
| #016 | 1Hロジック導入 | neck_4h=1H SH / support_1h=15M SL | ✅ |
| #017 | ネック許容 pips基準修正 | NECK_TOLERANCE_PIPS=20.0 | ✅ |
| #018 | ★★★限定 + クロス集計 | ALLOWED_GRADES / debug m/n | ✅ |
| #019 | 4H+1H構造確認プロット | plot_4h_1h_structure() / structure_plotter.py | ✅ |
| #020 | 1H-4H一致検証 + 窓プロット | test_1h_coincidence(v2) / plot_1h_window_5m | ✅ |
| #020-fix | プロットレンダリングバグ修正 | addplot→scatter / CJK→英語タイトル | ✅ |
| #021 | 窓ベース階層スキャン Phase 1 | window_scanner.py 新規作成 | ✅ **完了** |
| #022 | タイミングバグ修正 | sl_1h_ts追加・1H SL以降限定（3箇所修正） | ✅ **完了** |
| #023 | 1H窓サイズ延長 | WINDOW_1H_POST 5→10（後5本→10本） | ✅ **完了** |
| #024a | neck修正 + プロット範囲拡大 | neck=1H SL以降初回SH / PLOT_PRE_H=25/POST_H=40 | ✅ **完了** |
| #025 | 後期バイアス修正（2箇所） | 1H SL選択を初回優先 / neck=iloc[0] | 🔄 **修正予定** |
| #026 | 決済シミュレーション統合 | manage_exit()統合 → P&L/PF/勝率計算 | ⬜ #025後 |

---

## 8. #021〜#023 完了結果（2026-03-26確定）

### #021 — window_scanner.py 新規作成

```
作業内容:
  ① scan_4h_events() — 4H LONG期間スキャン
  ② get_1h_window_range() — 1H窓確定（前20+SL+後5=26本）
  ③ scan_window_entry() — 窓内15M/5Mスキャン

結果:
  スキャン窓数: 33件
  エントリー検出: 13件（DB:1 / IHS:7 / ASCENDING:5）
  
バグ発見:
  全13件が「底を打つ前」にエントリー
  原因: 窓左端（底より20時間前）からスキャン開始
```

### #022 — タイミングバグ修正

```
修正内容（3箇所のみ）:
  ① def scan_window_entry(df_5m_win, sl_4h_val, sl_1h_ts)  # 引数追加
  ② sl_1h_idx = df_5m_win.index.searchsorted(sl_1h_ts)
     for j in range(sl_1h_idx, len(df_5m_win) - 1):        # 1H SL以降限定
  ③ scan_window_entry(df_5m_win, sl_4h_val, sl_1h_ts)       # 呼び出し修正

結果:
  13件 → 2件（IHS×2のみ）
  エントリー0件窓: 31/33件
  DB 0件 / ASCENDING 0件 → 窓の右端5本（5時間）が短すぎる
```

### #023 — 窓サイズ延長

```
修正内容（1行のみ）:
  WINDOW_1H_POST = 5 → 10  # 後5本 → 後10本に延長

結果:
  2件 → 5件（+150%）
  DB: 0件 → 2件
  IHS: 2件 → 1件（入替）
  ASCENDING: 0件 → 2件
  エントリー0件窓: 28/33件
  
窓構造:
  前20本 + SL足 + 後10本 = 31時間（約1.3日分）
```

### プロット目視確認結果（5枚）

全5件で以下を確認:
- ✅ 全件が1H SL以降（底を打った後）のエントリー
- ✅ IHS: 右肩形成後のネック越え（典型的）
- ✅ DB: 2番底形成後のネック越え
- ✅ ASCENDING: 安値切り上げ完了後のネック越え
- ⚠️ 窓幅の不一致問題（一部の窓が77時間）→ 実害なし・Phase 2で調整

---

## 9. #020 完了結果（2026-03-25確定）

### 作業② 一致検証（修正版v2: 時間近傍比較）

```
対象サンプル (4H LONG) : 89 件
1H SL 検出率（±8本窓） : 89/89 = 100.0%
距離: mean 0.0 / median 0.0 pips（数学的必然）
一致率: <=5pips 100% / <=10pips 100% / <=20pips 100%
```

旧版バグ: `get_all_swing_lows_1h(lookback=240).min()` で10日間の絶対最安値を取得
→ 別の波の底と比較していたため median 206 pips
修正版: 4H SL タイムスタンプ ±8本窓内で最近傍1H SLを探す方式に変更

### 作業③ 窓プロット（修正版）

```
ヒット件数: 20件（ユニーク8窓）
PNG: 8枚 → logs/1h_windows/
```

#020-fix: addplot が axes[1]（白帯パネル）を生成しローソク足を覆い隠していたバグ
→ addplot廃止 → ax.scatter()で整数x軸に直接描画
→ CJK豆腐 → 英語タイトルに変更

### プロット目視確認結果（5枚 + debug_test）

全5枚で以下を確認:
- 5Mローソク足・SH/SLマーカー: 全件正常描画
- 4H SL水平線: 全件正確な位置
- 1H SL垂直線: 全件表示
- **15M DB/IHS構造が窓内で視認できた**（設計仮説の裏付け）

---

## 10. #019 検証結果（累計）

### structure_plotter 初回（2026-03-22）

- 16件（LONG:13 / SHORT:3）→ 9枚目視で合格率90%

### structure_plotter 追加検証（2026-03-25）

- 7枚追加目視（LONG:4 / SHORT:3）→ **全件OK（100%）**
- 累計合格率: 16/17（94%）— NG 1件は 20260113_0545 TOPエントリーのみ

---

## 11. 未解決課題・次のステップ

### 🔴 #025（最優先）— 後期バイアス修正（2箇所・window_scanner.pyのみ）

```
修正①: get_1h_window_range() — 1H SL選択を「最初の出現」優先に（ADR A-4）
  price_tol_pips = 20.0
  close_enough   = sl_1h_near[dists <= price_tol_pips * PIP]
  sl_1h_ts = close_enough.index[0] if len(close_enough) > 0 else dists.idxmin()

修正②: scan_window_entry() — neck = 最初のSH に変更（ADR A-5）
  neck_15m = float(sh_vals.iloc[0])   # max() → iloc[0]

期待効果:
  #02: sl_1h_ts が Jul26 08:50 に前倒し → 当日エントリー機会を捕捉
  #03: neck が 153.913 → 153.75 付近に低下 → 約18pips改善
  #01/#04: 変化なし
```

### 🔴 #026（#025完了後）— 決済シミュレーション統合

```
window_scanner.py に manage_exit() を統合
  ① エントリー後の5M足を順次スキャン
  ② 初動SL / 段階1 / 段階2 / 段階3 の決済判定
  ③ 損益・PF・勝率・MaxDD 計算
  ④ 旧版 backtest.py（PF 5.32）と比較
```

```
15M DB/IHS 右肩検出 → 右肩内で 5M DB ネック実体上抜け
Phase 1（シンプル版）との比較で改善幅を定量確認
```

### 🟡 窓幅問題の精査（必要に応じて）

```
CSV上の窓幅が統一されていない（77時間 vs 30時間）
原因候補: get_1h_window_range() の境界計算
実害: 現状プロット目視では問題なし
対応: Phase 2 で厳密化
```

### ⬜ 将来課題

- 15M SH 密集フィルター: 4本以上密集時はエントリー見送り
- SHORT 運用再開: サンプル充足後にリスクリワード比較
- volume_alert.py: 出来高急増検知 + LINE通知（Phase D）
- Vision AI 自動チェック: PNG → Gemini/GPT-4o（Phase 3）

---

## 12. 思考フラグ運用ルール（ClaudeCode向け）

| フラグ | 使うタイミング |
|---|---|
| think | 単純な修正・パラメータ変更 |
| think hard | 複数ファイル修正・バグ修正 |
| think harder | 設計判断が必要な実装 |
| ultrathink | アーキテクチャ全体変更・最適化 |

---

## 13. Git運用

作業ブランチ命名: claude/[作業内容]-[ID]
masterへのmerge: テスト確認後

コミットメッセージ規則:
```
Phase A: "Phase A: ..."
バグ修正: "Fix: ..."
パラメータ調整: "Tune: ..."
新機能: "Feat: ..."
ドキュメント: "Docs: ..."
```

---

## 14. プロット設計（参照先）

詳細は `REX_Trade_System/docs/PLOT_DESIGN_CONFIRMED-2026-3-26.md` を参照。

---

## 15. 設計管理ファイル

```
docs/REX_ARCHITECTURE.html
  全設計を俯瞰する Live ドキュメント（ブラウザで開く）

スレッド引き継ぎ時の手順:
  1. EX_DESIGN_CONFIRMED-{日付}.md を読み込む（本ファイル）
  2. PLOT_DESIGN_CONFIRMED-{日付}.md を読み込む
  3. ultrathink フラグを付与して新スレッド開始
```
