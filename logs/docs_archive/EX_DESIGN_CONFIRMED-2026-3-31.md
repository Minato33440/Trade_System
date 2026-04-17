# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-03-31
# 保存先: REX_Trade_System/docs/EX_DESIGN_CONFIRMED-2026-3-31.md

---

## 1. プロジェクト基本情報

- リポジトリ: GitHub Minato33440/Trade_System
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

## 3. ミナト流MTF短期売買ルール（確定定義・2026-03-31版）

### 3-1. 戦略の本質

「4H上昇ダウが継続している限り、
 押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

---

### 3-2. MTF 階層スキャン構造（#020検証完了・#021〜#025実装完了）

```
LAYER 1 — 4H 上昇トレンド
  SH/SL 高値・安値切り上げ確認（上昇ダウ）
  → ダウ崩れまでの各 4H SL が押し目候補
  params: n=3, lookback=20, MIN_4H_SWING_PIPS≥20

LAYER 2 — 1H 押し目ウィンドウ（#020検証完了・#023窓延長・#025完了）
  4H SL ts ±8本(8時間)窓内で最近傍 1H SL を探す
  → 1H SL 足: 前20本 + SL足 + 後10本 = 計31本ウィンドウ確定
  ウィンドウ = 約31時間分の 5M 足（≈372本）

  検証結果（#020確定値）:
    対象: 89件(4H LONG)
    1H SL 検出率: 100.0%
    距離: 0.0 pips（同一データ源リサンプルのため数学的必然）
    → 設計前提「4H SL ≒ 1H SL」は成立

LAYER 3 — 窓内 15M/5M スキャン（#021〜#025完了）
  窓内 5M → 15M リサンプル
  → check_15m_range_low() で DB/IHS/ASCENDING パターンラベル取得
  → **neck = 1H SL 以降の最初の 15M SH（#025確定・固定ネック原則）**
  → 5M close > neck + WICKTOL_PIPS(5.0) でエントリー

  **固定ネック原則（#025で確定）:**
  ```python
  # 1H SL以降の15M SHを時系列順に取得
  sh_vals = df_5m_win.loc[df_5m_win.index >= sl_1h_ts, 'sh_5m']
  sh_vals = sh_vals.dropna()
  
  # 最初のSH = 初回反発ピーク = ネックとして確定
  neck_15m = sh_vals.iloc[0]  # ← 一度確定したら変わらない
  ```

  **重要な設計思想:**
  1. ネックは固定 — 初回反発ピークが確定したら変更されない
  2. 以降のより低いピーク（ピークB, ピークC...）は新しいネックにならない
  3. エントリー判定は常に「初回反発ピーク上抜け」のみ
  4. これにより、三尊・レンジ形成時も正確なエントリータイミングを捕捉

  実装履歴:
    #021: 窓左端スキャン（バグ）→ 13件検出（全件誤検出）
    #022: 1H SL以降限定スキャン → 2件（IHS×2）に激減
    #023: 窓後5本→10本延長 → 5件（DB:2 / IHS:1 / ASCENDING:2）
    #024a: neck=1H SL以降最初SH / プロット範囲分離 → 4件
    #025: 固定ネック原則確定 → 15件（DB:3 / IHS:3 / ASCENDING:9）
```

#### エントリーロジック 2段階実装計画（2026-03-31更新）

```
Phase 1（#021〜#025 — シンプル版・完了）:
  窓内 15M DB/IHS/ASCENDING ネック越え → 5M実体確定 → エントリー
  #025結果: 15件検出（DB:3 / IHS:3 / ASCENDING:9）
  → ベースライン数値確定 → 次は決済統合（#026）

Phase 2（#027以降 — フル版への拡張・未着手）:
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

## 4. ファイル構成（確定版・2026-03-31時点）

```
src/
├── swing_detector.py       ✅ 完了（#020追加分含む）
├── entry_logic.py          ✅ 完了（#018まで・変更凍結）
├── exit_logic.py           ✅ 完了（#009以降・変更凍結）
├── plotter.py              ✅ 完了（#020-fix適用済み）
├── backtest.py             ✅ 完了（#018まで・ベースライン保持・変更凍結）
│    PF 5.32 / 勝率 55.0% / MaxDD 14.9 pips / 総損益 +91.6 pips
├── base_scanner.py         ✅ 完了（#015）
├── structure_plotter.py    ✅ 完了（#019）
├── test_1h_coincidence.py  ✅ 完了（#020・修正版v2適用済み）
├── window_scanner.py       ✅ #025完了
│    結果: 15件検出（DB:3 / IHS:3 / ASCENDING:9）
├── volume_alert.py         ⬜ 未着手（Phase D）
├── signals.py              廃止方向
├── data_fetch.py           変更なし
└── regime.py               変更なし

docs/
├── EX_DESIGN_CONFIRMED-2026-3-31.md  ← 本ファイル
├── PLOT_DESIGN_CONFIRMED-2026-3-31.md
└── REX_ARCHITECTURE.html

logs/
├── plots/             ← 5M Swing確認PNG
├── base_scan/         ← 4H+15M基礎スキャン結果
├── structure_plots/   ← 4H+1H構造確認PNG（16枚）
├── 1h_windows/        ← 1H窓 + 5M重ね合わせPNG（8枚・#020-fix修正済み）
├── window_scan_plots/ ← 窓ベーススキャン結果PNG（15枚・#025最新）
└── window_scan_entries.csv  ← エントリー記録CSV（15件・#025最新）
```

---

## 5. Swing検出パラメータ（確定値・2026-03-31時点）

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

| 指標 | #009 | #011 | #018（旧版最新） | #025（新版Phase 1） |
|---|---|---|---|---|
| 総トレード数 | 25件 | 36件 | 20件 | **15件** |
| 全体勝率 | 48.0% | 55.6% | 55.0% | **未計算** |
| PF | 0.98 | 2.86 | **5.32** | **未計算** |
| MaxDD | 106.5 pips | 27.4 pips | **14.9 pips** | **未計算** |
| 総損益 | -2.2 pips | +79.1 pips | **+91.6 pips** | **未計算** |
| モード | LONG+SHORT | LONG限定 | LONG+★★★限定 | LONG+窓ベース |

**#018確定値（★★★のみ・20件）:**
- DB: 9件 / 勝率75.0% / +7.1 pips
- ASCENDING: 10件 / 勝率60.0% / +3.7 pips
- IHS: 1件 / 勝率0.0% / -2.2 pips（サンプル不足・継続監視）

**#025確定値（窓ベース・15件 — エントリー検出のみ・決済未統合）:**
- DB: 3件 / IHS: 3件 / ASCENDING: 9件
- 窓数: 33件 / エントリー検出: 15件
- 決済統合: #026で実施予定

---

## 7. 指示書完了履歴

| # | 内容 | 主要変更 | 状態 |
|---|---|---|---|
| #001〜#008 | Phase A 基盤構築 | swing_detector / entry_logic 基礎 | ✅ |
| #009 | 決済ロジック4段階 | exit_logic.py 刷新 | ✅ |
| #010〜#018 | パラメータ最適化・機能追加 | 各種確定値 | ✅ |
| #019 | 4H+1H構造確認プロット | structure_plotter.py | ✅ |
| #020 | 1H-4H一致検証 + 窓プロット | test_1h_coincidence(v2) | ✅ |
| #020-fix | プロットレンダリングバグ修正 | addplot→scatter | ✅ |
| #021〜#024a | 窓ベース階層スキャン Phase 1 | window_scanner.py | ✅ |
| #025 | 固定ネック原則確定 | neck=sh_vals.iloc[0] / 15件 | ✅ **完了** |
| #026 | 決済シミュレーション統合 | manage_exit()統合 → P&L計算 | 🔴 **次の最優先** |

---

## 8〜11. 完了結果詳細

（#020〜#025の詳細結果は省略 — ADR / NLM に記録済み）

---

## 12. 未解決課題・次のステップ

### 🔴 #026（最優先）— manage_exit() 統合

window_scanner.py に決済シミュレーションを統合。
旧版 backtest.py（PF 5.32）との比較レポート出力が完了条件。

### 🟡 将来課題

- 15M SH 密集フィルター / SHORT 運用再開 / volume_alert.py / Vision AI

---

## 13〜16. 運用ルール

（思考フラグ / Git運用 / プロット設計 / 設計管理 — 変更なし）

思考フラグ: think / think hard / think harder / ultrathink
Git: `claude/[作業内容]-[ID]` ブランチ / Feat / Fix / Tune / Docs
