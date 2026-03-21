# REX AI Trade System — 設計確定文書
# 作成: Rex / 最終更新: 2026-03-20
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

## 3. ミナト流MTF短期売買ルール（確定定義・2026-03-20版）

### 3-1. 戦略の本質

「4H上昇ダウが継続している限り、
 押し目条件が揃うたびにエントリーを繰り返す構造」

エリオット波数カウントは不要・実装しない。
「初動3波狙い」は裁量表現であり、コード上は使わない。

---

### 3-2. エントリー条件（新3段階フィルター — #009以降確定版）

前提: get_direction_4h() == 'LONG' または 'SHORT'
     かつ 4H Swing幅 >= MIN_4H_SWING_PIPS（20pips）← #010追加

**Step1: 4H押し目確認（Fib条件）**
```
優位性★★★: Fib50%付近（45〜55%） かつ 4Hネックライン付近（±3%以内）
優位性★★ : Fib61.8%以内（65%以下）
条件外    : 上記以外 → スキップ
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
```

**Step3: 5M DBネックライン実体確定**
```
5M の min(open,close)（実体下端）が neck_15m を上抜け確定した足
かつ 5M DB ネック価格 <= 15M Swing High（構造フィルター）
かつ 5M SL2 >= 15M_SL - WICKTOL_PIPS * PIP_SIZE（下ヒゲ許容）

WICKTOL_PIPS = 0.0（初期値・許容なし）
テスト順: 0.0 → 5.0 → 10.0

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

初期はLong・Shortともに同ロット（データ取り優先）
将来: リスクリワード比較後にShortのロット縮小幅を決定

LONG: Swing Low → 押し目買い / ボラ小 / 損切幅 小
SHORT: Swing High → 戻り売り / ボラ大 / 損切幅 広め（将来縮小）

---

## 4. ファイル構成（確定版・2026-03-20時点）

```
src/
├── swing_detector.py  ✅ 完了（Phase A）
│    detect_swing_highs/lows
│    get_nearest_swing_high/low
│    get_direction_4h
│    get_direction_from_raw_4h
│    _build_direction_5m（パフォーマンス最適化版）
│
├── entry_logic.py     ✅ 完了（#011実装待ち）
│    check_fib_condition（Fib61.8% / 50%+ネック 2段階）
│    check_15m_range_low()   ← #011: 統合レンジロジック（DB/IHS/ASCENDING）
│    check_5m_double_bottom()（WICKTOL_PIPS対応）
│    evaluate_entry（3段階統合・MIN_4H_SWING_PICSガード付き）
│    MAX_REENTRY = 1 / MIN_4H_SWING_PIPS = 20.0 / WICKTOL_PIPS = 0.0
│
│    ※ 廃止済み: check_double_bottom_1h / check_double_top_1h
│    ※ 廃止済み: calc_limit_price / check_limit_triggered
│    ※ 廃止済み: check_5m_swing_confirmed / MIN_SWING_BARS
│
├── exit_logic.py      ✅ 完了（#009以降）
│    check_5m_dow_break（Low/High系列 修正済み）
│    check_15m_dow_break（Low/High系列 修正済み）
│    check_4h_neck_1h_confirmed（1H実体確定判定）
│    manage_exit（4段階決済統合・neck_1h / exit_phase 引数追加）
│
├── plotter.py         ✅ Phase1完了（#009）
│    plot_swing_check()   ← Swing検出精度確認チャート
│    （既存8ペアチャート機能は変更なし）
│
├── backtest.py        ✅ 大幅修正完了
│    ポジション管理: neck_1h / exit_phase / entry_pattern 追加
│    デバッグ出力: a〜i 全項目
│
├── volume_alert.py    未着手（Phase D）
├── signals.py         廃止方向
├── data_fetch.py      変更なし
└── regime.py          変更なし
```

---

## 5. Swing検出パラメータ（確定値）

| TF | n（前後確認本数） | lookback |
|---|---|---|
| 4H足 | 2 | 30 |
| 15M足（レンジロジック） | 3 | 40 |
| 15M足（ダウ崩れ判定） | 3 | 30 |
| 5M足 | 2 | 20 |

NONE比率: 修正後42.1%（目標50%以下クリア済み）

---

## 6. 現在のバックテスト結果（#009完了時点 / #011実装前）

| 指標 | #005 | #007 | #009 |
|---|---|---|---|
| 総トレード数 | 111件 | 36件 | 25件 |
| 全体勝率 | 29.7% | 36.1% | 48.0% |
| PF | 0.60 | 0.70 | 0.98 |
| MaxDD | 581 pips | 330 pips | 106.5 pips |
| 総損益 | -520 pips | -144 pips | -2.2 pips |

---

## 7. 46枚プロット評価の知見（2026-03-20）

| 評価項目 | 結果 | 対処 |
|---|---|---|
| OK判定 | 19枚 (41.3%) | — |
| A=NARROW（4H幅 < 15pips） | 10枚 | #010で対処済み |
| B=SKIP（5M DBスキップ） | 0枚 | ロジック正常動作確認 |
| C=TOP（天井エントリー） | 11枚 | #010/#011で改善期待 |
| C=LATE（遅れエントリー） | 12枚 | #011統合ロジックで改善期待 |
| 複合問題（NARROW+TOP） | 10枚 | #010で6枚排除見込み |

**主要知見:**
- 15M DBネックは46枚全件で概ね正常抽出
- 5M DBはボラ依存でスキップ発生 → 将来ATRベースのn値動的変更で対処
- 4H Swing幅ガード（MIN_4H_SWING_PIPS=20）が根本修正の核心

---

## 8. 未解決課題・進行中作業

### 🔴 指示書 #011（think hard）— ClaudeCodeへ未渡し（最優先）
`entry_logic.py`:
- `check_15m_double_bottom()` を `check_15m_range_low()` に置き換え
- `MIN_4H_SWING_PIPS = 20.0` ガード追加

`backtest.py`:
- デバッグ出力 f/g/h/i 追加（パターン別勝率が核心）

**ClaudeCodeへの補足（口頭必須）:**
SL3上限計算の保護コード: `sl3_max = max(..., sl_min + MIN_RANGE)`
MIN_RANGE = 5pips を必ず追加すること。

### 🟡 #012候補（#011結果確認後）
- ボラティリティ係数（ATRベースのn値動的変更）
  ATR低(<3pips)→n=3 / ATR中(3〜7)→n=2 / ATR高(>7)→n=1

### 🟡 Phase D — 未着手
- volume_alert.py: 出来高急増検知 + LINE通知

### 🟡 将来課題
- Shortロットの縮小幅決定（リスクリワード比較後）
- Vision AI によるプロット自動チェック（Phase 3）
- リアルタイム用「仮確定モード」実装

---

## 9. 思考フラグ運用ルール（ClaudeCode向け）

| フラグ | 使うタイミング |
|---|---|
| think | 単純な修正・パラメータ変更 |
| think hard | 複数ファイル修正・バグ修正 |
| think harder | 設計判断が必要な実装 |
| ultrathink | アーキテクチャ全体変更・最適化 |

指示書 #011: think hard を冒頭に記載済み

---

## 10. Git運用

作業ブランチ命名: claude/[作業内容]-[ID]
masterへのmerge: テスト確認後

コミットメッセージ規則:
```
Phase A: "Phase A: ..."
バグ修正: "Fix: ..."
パラメータ調整: "Tune: ..."
新機能: "Feat: ..."
```

---

## 11. プロット設計（参照先）

詳細は `REX_Trade_System/docs/REX_PLOT_DESIGN_CONFIRMED.md` を参照。

概要:
- Phase 1完了: mplfinance OHLC + 4H/15M Swing + NONE区間グレー背景
- 保存先: `logs/plots/YYYYMMDD_HHMM_{LONG|SHORT}_swing.png`
- Phase 2以降: Fib・DBネック・エントリー決済マーカー追加予定