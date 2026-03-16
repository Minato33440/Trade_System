# mtf_minato_short_v2 完全解説＆ショート0件→29件 修正経緯

updated: 2026-03-11 (JST)

---

## 1. mtf_minato_short_v2 の全体構造（完全出力相当）

```
戻り値: (entries_long, entries_short) タプル

【ロング条件】4H2番底目 → 1H戻り → 15Mネックライン上抜け
  cond_4h_dbl_bottom = _double_bottom(close_4h, 20, 0.005)
  cond_fib_long = _fib_pullback(close_4h, 20, fibo_level)
  cond_1h_long = _fib_pullback(1H) & _double_bottom(1H)
  cond_1h_swing_long = _simple_swing(close_1h, 10, 0.002)
  cond_15m_neck_up = _double_bottom(15M)  # ネックライン上抜け
  cond_5m_neck_up = _double_bottom(5M)
  main_long = 4H底 & trend_long & fib & (1H_long | 1H_swing) & 15M上 & RSI40-60 & session
  early_long = 上記大枠 & vol_spike & 5M上 & session
  entries_long = main_long | early_long

【ショート条件】4H2番天井目 → 1H戻り → 15Mネックライン下抜け
  cond_4h_dbl_top = _double_top(close_4h, 20, 0.005)
  cond_fib_short = _fib_throwback(close_4h, 20, fibo_level)
  cond_1h_short = _fib_throwback(1H) & _double_top(1H)
  cond_1h_swing_short = _simple_swing(close_1h, 10, 0.002)
  cond_15m_neck_down = _double_top(15M)  # ネックライン下抜け
  cond_5m_neck_down = _double_top(5M)
  main_short = 4H天井 & trend_short & fib & (1H_short | 1H_swing) & 15M下 & RSI25-75 & session
  early_short = 上記大枠 & vol_spike & 5M下 & session
  entries_short = main_short | early_short
```

---

## 2. 各ヘルパーの定義と呼び出し

| 関数 | 定義 | ロング | ショート |
|------|------|--------|----------|
| `_double_bottom` | rolling_min からの反発率 ≥ threshold & close > rolling_median | ✓ 4H,1H,15M,5M | - |
| `_double_top` | 天井からの落ち込み率 ≥ threshold（median条件は緩和済み） | - | ✓ 4H,1H,15M,5M |
| `_fib_pullback` | 高値からの押し目深さ ≤ max_level | ✓ 4H,1H | - |
| `_fib_throwback` | 安値からの戻り率 ≤ max_level（ショート押し目） | - | ✓ 4H,1H |
| `_simple_swing` | レンジ幅/中央値 ≥ min_range_pct | ✓ 1H | ✓ 1H |

---

## 3. ショートが0件だった原因（コードから推測・3つ以上）

1. **ショートロジックが実装されていなかった（決定的）**
   - `_double_top`, `_fib_throwback` は定義のみで `mtf_minato_short_v2` 内で未使用だった
   - 戻り値が単一 `sig`（ロングのみ）のため、Simple_Backtest で `entries_short = 全False` になっていた

2. **戻り値が (entries_long, entries_short) でなく単一 Series**
   - Simple_Backtest はタプルを期待しており、単一 Series の場合ショートを 0 として扱っていた

3. **`_double_top` の `close < rolling_median` が厳しすぎた**
   - 天井形成直後の下降初期では close がまだ median より上になりやすく、条件を満たさない
   - → 緩和: median 条件を削除し、天井からの落ち込み率のみで検知するよう変更

4. **RSI 40〜60 がショートに不向き**
   - 下落相場では RSI が 40 未満になりやすい
   - → 緩和: ショート側の RSI を 25〜75 に拡張

5. **AND 条件が多数つながっており、1つでも失敗すると全体 False**
   - 4H・1H・15M の各条件が全て成立する必要があった

---

## 4. 適用した修正（最小限）

1. **ショートロジック追加** … 4H2番天井 → 1H戻り → 15Mネックライン下抜けを実装
2. **戻り値を `(entries_long, entries_short)` に変更**
3. **`_double_top` の median 条件削除** … 落ち込み率のみで検知
4. **RSI ショート緩和** … 25〜75 に拡張
5. **use_daily=False のとき `cond_trend_short = True`** … デフォルトではトレンド制約なし

---

## 5. 修正後の実行結果（2026-03-11）

```
総シグナル数: 47 (ロング: 18 / ショート: 29)
先行エントリー(1.5倍): 14 (29.8%)
再エントリー: 34 回 / 成功: 29 (85.3%)
```

ショートは **0件 → 29件** に改善。ロングよりショートの方が多いのは、当該期間の相場（下落・調整）にショートパターンが多かったためと考えられる。
