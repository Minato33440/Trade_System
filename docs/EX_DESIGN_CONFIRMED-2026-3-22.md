# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-03-22
# 保存先: REX_Trade_System/docs/EX_DESIGN_CONFIRMED-2026-3-22.md

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

## 3. ミナト流MTF短期売買ルール（確定定義・2026-03-22版）

### 3-1. 戦略の本質

「4H上昇ダウが継続している限り、
 押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

---

### 3-2. エントリー条件（3段階フィルター — #018確定版）

前提:
- get_direction_4h() == 'LONG'（DIRECTION_MODE = 'LONG'、SHORT一時停止）
- 4H Swing幅 >= MIN_4H_SWING_PIPS（20pips）
- ALLOWED_GRADES = ['★★★']（#018追加）

**Step1: 4H押し目確認（Fib条件 + 1H neck + Support_1h）**
```
優位性★★★: fib_pct <= 0.55
            かつ 1H neck から ±20pips 以内（NECK_TOLERANCE_PIPS=20.0）
            かつ sl_last >= support_1h（15M SL割れなし）

優位性★★ : fib_pct <= 0.65（★★★条件を満たさない場合）
            ※ ALLOWED_GRADES=['★★★'] により現在フィルター除外中

条件外    : 上記以外 → スキップ
```

**neck_4h 定義（#016確定）:**
```
neck_4h = 直近 1H Swing High（get_nearest_swing_high_1h, n=2, lookback=20）
          旧設計: 4H SH をそのまま使用（★★★が数学的に成立不能だったバグ）
```

**Support_1h 定義（#016確定・暫定）:**
```
support_1h = 直近 15M Swing Low（get_nearest_swing_low_15m, n=3, lookback=20）
             → 将来: 1H Swing Low（lookback=240）に変更予定
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

SL3上限保護コード（DBパターン保護）:
  MIN_RANGE = 5.0 * PIP_SIZE
  sl3_max = max(sl_min + 2.0*(sl2-sl_min), sl_min + MIN_RANGE)

ALLOWED_PATTERNS = ['DB', 'ASCENDING', 'IHS']
LOOKBACK_15M_RANGE = 50（#014確定）
```

**Step3: 5M DBネックライン実体確定**
```
5M の min(open,close)（実体下端）が neck_15m を上抜け確定した足
かつ 5M DB ネック価格 <= 15M Swing High（構造フィルター）
かつ 5M SL2 >= 15M_SL - WICKTOL_PIPS * PIP_SIZE（下ヒゲ許容）

WICKTOL_PIPS = 5.0（#013確定）

執行: 確定足の次の5M足の始値でエントリー（指値方式は廃止）
```

---

### 3-3. 確定足・執行足の定義（全ロジック共通）

「確定足」= 実体（min/max(open,close)）がラインを越えた足
「執行足」= 確定足の次の足の始値で執行

---

### 3-4. 決済ロジック（4段階 — #009以降確定版）

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

### 3-5. 再エントリー仕様

- 同一押し目機会での再試行: 最大1回（MAX_REENTRY = 1）
- 4H上昇ダウが崩れたらカウントリセット → 戦略完全リセット
- 15M ダウ intact（1H・4H継続）なら → ①に戻り再エントリー

---

### 3-6. 撤退条件（⑪）

4Hサポートラインを15M足実体が下抜け確定 → 戦略撤退
ただし15M終値がサポート上に戻れば継続（下ヒゲの場合）

---

### 3-7. Long/Short分岐仕様

DIRECTION_MODE = 'LONG'（SHORT一時停止中 — #012確定）
将来: SHORT復活後はリスクリワード比較によりロット縮小幅を決定

LONG: Swing Low → 押し目買い / ボラ小 / 損切幅 小
SHORT: Swing High → 戻り売り / ボラ大 / 損切幅 広め（将来縮小）

---

## 4. ファイル構成（確定版・2026-03-22時点）

```
src/
├── swing_detector.py  ✅ 完了
│    detect_swing_highs/lows
│    get_nearest_swing_high/low
│    get_nearest_swing_high_1h（#016追加: neck_4h取得用）
│    get_nearest_swing_low_15m（#016追加: support_1h取得用）
│    get_direction_4h
│    get_direction_from_raw_4h
│    _build_direction_5m（パフォーマンス最適化版）
│
├── entry_logic.py     ✅ 完了（#018まで）
│    check_fib_condition
│    check_15m_range_low()   ← #011: 統合レンジロジック（DB/IHS/ASCENDING）
│    check_5m_double_bottom()（WICKTOL_PIPS対応）
│    evaluate_entry（3段階統合 + 1H neck/support + grade filter）
│    MAX_REENTRY = 1
│    MIN_4H_SWING_PIPS = 20.0
│    WICKTOL_PIPS = 5.0（#013確定）
│    NECK_TOLERANCE_PIPS = 20.0（#017確定: 旧 PCT=0.03 を廃止）
│    ALLOWED_GRADES = ['★★★']（#018確定）
│    ALLOWED_PATTERNS = ['DB', 'ASCENDING', 'IHS']
│    LOOKBACK_15M_RANGE = 50（#014確定）
│
│    ※ 廃止済み: NECK_TOLERANCE_PCT
│    ※ 廃止済み: check_double_bottom_1h / check_double_top_1h
│    ※ 廃止済み: calc_limit_price / check_limit_triggered
│
├── exit_logic.py      ✅ 完了（#009以降）
│    check_5m_dow_break（Low/High系列 修正済み）
│    check_15m_dow_break（Low/High系列 修正済み）
│    check_4h_neck_1h_confirmed（1H実体確定判定）
│    manage_exit（4段階決済統合・neck_1h / exit_phase 引数追加）
│
├── plotter.py         ✅ 完了（#019追加）
│    save_normalized_plot()
│    save_swing_debug_plot()
│    plot_base_scan()（#015追加）
│    plot_swing_check()（Phase1完了・#009）
│    plot_4h_1h_structure()（#019追加: 4H+1H構造確認プロット）
│
├── backtest.py        ✅ 完了（#018まで）
│    ポジション管理: neck_1h / exit_phase / entry_pattern / grade 追加
│    デバッグ出力: a〜n 全項目（#018で m/n 追加）
│    WARMUP_BARS = 1728（#012確定）
│
├── base_scanner.py    ✅ 完了（#015: 4H+15M基礎スキャナー）
│    scan_4h_15m_base()
│    save_base_scan_csv()
│    出力: logs/base_scan/
│
├── structure_plotter.py  ✅ 完了（#019: 4H+1H構造確認プロット）
│    scan_4h_neck_breaks()（N_4H=5, N_1H=3）
│    main(): 全件スキャン → PNG生成
│    出力: logs/structure_plots/
│
├── volume_alert.py    未着手（Phase D）
├── signals.py         廃止方向
├── data_fetch.py      変更なし
└── regime.py          変更なし
```

---

## 5. Swing検出パラメータ（確定値・2026-03-22時点）

| 用途 | TF | n | lookback |
|---|---|---|---|
| 4H方向判定（backtest） | 4H | 3 | 20 |
| 4H方向判定（structure_plotter） | 4H | 5 | 100 |
| 4H SH/SL取得（backtest） | 4H | 3 | 20 |
| 4H SH/SL取得（base_scanner） | 4H | 3 | 100 |
| 1H neck_4h取得 | 1H | 2 | 20 |
| 15M support_1h取得 | 15M | 3 | 20 |
| 15M レンジロジック | 15M | 3 | 50 |
| 5M DB確定 | 5M | 2 | 20 |

NONE比率: 修正後42.1%（目標50%以下クリア済み）

---

## 6. バックテスト結果推移（確定値）

| 指標 | #009 | #011 | #018（最新） |
|---|---|---|---|
| 総トレード数 | 25件 | 36件 | 20件 |
| 全体勝率 | 48.0% | 55.6% | 55.0% |
| PF | 0.98 | 2.86 | **5.32** |
| MaxDD | 106.5 pips | 27.4 pips | **14.9 pips** |
| 総損益 | -2.2 pips | +79.1 pips | **+91.6 pips** |
| モード | LONG+SHORT | LONG限定 | LONG+★★★限定 |

**#018確定値（★★★のみ・20件）:**
- DB: 9件 / 勝率75.0% / +7.1 pips
- ASCENDING: 10件 / 勝率60.0% / +3.7 pips
- IHS: 1件 / 勝率0.0% / -2.2 pips（サンプル不足）
- ★★ 除外: 552件（グレードフィルター適用数）

---

## 7. 指示書完了履歴

| # | 内容 | 主要変更 |
|---|---|---|
| #001〜#008 | Phase A 基盤構築 | swing_detector / entry_logic 基礎 |
| #009 | 決済ロジック4段階 | exit_logic.py 刷新 |
| #010 | MIN_4H_SWING_PIPS | 4H幅ガード20pips |
| #011 | 15M統合レンジロジック | DB/IHS/ASCENDING 統合 |
| #012 | LONG限定 + フォールバック修正 | DIRECTION_MODE='LONG' / None返却 |
| #013 | IHSフラグ除外 + WICKTOL修正 | WICKTOL_PIPS=5.0 |
| #014 | IHS復活 + lookback拡張 | LOOKBACK_15M_RANGE=50 |
| #015 | 4H+15M基礎スキャナー | base_scanner.py 新規 |
| #016 | 1Hロジック導入 | neck_4h=1H SH / support_1h=15M SL |
| #017 | ネック許容 pips基準修正 | NECK_TOLERANCE_PIPS=20.0 |
| #018 | ★★★限定 + クロス集計 | ALLOWED_GRADES / debug m/n |
| #019 | 4H+1H構造確認プロット | plot_4h_1h_structure() / structure_plotter.py |

---

## 8. base_scanner 主要知見（#015結果）

- 総イベント: 1,938件
- IHS = LONG全体の52.8%（最多パターン）
- ★★★ = 0件（#017修正前: neck_4h=sh_4h設計バグにより数学的に成立不能）
- ★★★ 発生条件: Fib50%付近 かつ 1H neck ±20pips 以内（#017修正後に正常動作）

---

## 9. #019 structure_plotter 結果（2026-03-22実行）

- 総イベント: 16件（LONG: 13件 / SHORT: 3件）
- スキャン条件: N_4H=5 / N_1H=3 / LOOKBACK_4H=100 / LOOKBACK_1H=240
- 1H trend OK: 16/16（全件整合）
- スキップ: NONE方向=3,002 / ネック越え不成立=4,153 / 1H Trend不整合=15
- 保存先: logs/structure_plots/（16 PNG）

---

## 10. 未解決課題・次のステップ

### 🔴 #020（最優先）— 4H+1H構造 目視確認 → 階層スキャン本格実装

#019 で生成したプロット（logs/structure_plots/）を目視確認し、
4H+1H 構造が正しく抽出できていると判断したら、
以下の階層スキャンへ進む。

**Support_1h の正式変更（#019確認後）:**
```
現行: 15M Swing Low（lookback=20、暫定）
正式: 1H Swing Low（lookback=240）
```

**structure_scanner.py 本格実装（予定）:**
```
Phase1: 1H足10日分 → 4H構造 + 1H SL特定
Phase2: 1H-bottom前後 ±5時間窓を抽出
Phase3: 窓内で 15M/5M 条件をスキャン
```

### 🟡 将来課題
- Shortロットの縮小幅決定（リスクリワード比較後）
- Vision AI によるプロット自動チェック（Phase 3）
- volume_alert.py: 出来高急増検知 + LINE通知

---

## 11. 思考フラグ運用ルール（ClaudeCode向け）

| フラグ | 使うタイミング |
|---|---|
| think | 単純な修正・パラメータ変更 |
| think hard | 複数ファイル修正・バグ修正 |
| think harder | 設計判断が必要な実装 |
| ultrathink | アーキテクチャ全体変更・最適化 |

---

## 12. Git運用

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

## 13. プロット設計（参照先）

詳細は `REX_Trade_System/docs/REX_PLOT_DESIGN_CONFIRMED.md` を参照。

概要:
- Phase 1完了: mplfinance OHLC + 4H/15M Swing + NONE区間グレー背景
- plot_4h_1h_structure(): 4H+1H 構造確認（#019追加）
  左10日 / 右2日 / 5M ローソク + 4H SH/SL + 4H neck + 1H SH/SL折れ線
- 保存先: logs/structure_plots/YYYYMMDD_HHMM_{LONG|SHORT}_4H1H_structure.png
