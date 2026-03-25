# REX 指示書 #020 — 1H-4H 一致検証 + 26本ウィンドウ プロット（最終修正版）
# 作成: Rex / 承認: Minato / 対象: ClaudeCode
# 作成日: 2026-03-24 / 最終修正: 2026-03-25
# 前提: 指示書 #001〜#019 完了済み

think harder

---

## ⛔ 禁止事項（必ず最初に読むこと）

1. **backtest.py / entry_logic.py / exit_logic.py を一切変更しないこと。**
   → 今回は新関数の「追加」と「検証スクリプト」のみ。
   → `get_nearest_swing_low_1h()` を追加しても、backtest.py の
     `get_nearest_swing_low_15m(lookback=20)` の呼び出しは置き換えない。
   → 置き換えは #021 以降の作業。

2. **`check_15m_range_low()` 等の既存エントリーロジックに触らないこと。**
   → 窓ベースの限定スキャンは #021 以降の設計対象。

3. **`resample_tf()` の定義を変えないこと。**
   → `label='right', closed='right'` は既存 backtest.py と同一。
   → `left` に変更すると 4H 足の境界が 1 本ズレて全データが壊れる。

---

## 作業概要

| # | 対象ファイル               | 内容                                     |
|---|----------------------------|------------------------------------------|
| ① | swing_detector.py          | get_nearest_swing_low_1h() 等 2関数追加  |
| ② | src/test_1h_coincidence.py | 1H SL ≒ 4H SL 一致検証スクリプト 新規   |
| ③ | plotter.py                 | plot_1h_window_5m() 追加 + __main__ 追記 |

**作業順序: ①→②→③ の順に実施。**
②の結果CSV出力・レポート表示まで完了してから③に進むこと。

---

## 作業① swing_detector.py — 2関数追加

既存の `get_nearest_swing_low_15m()` の直後に追加する。
**既存関数は一切変更しない。**

```python
def get_nearest_swing_low_1h(
    low_1h: pd.Series,
    n: int = 2,
    lookback: int = 240,
) -> float | None:
    """
    1H足 lookback=240（約10日分）で直近 Swing Low を返す。
    検出できない場合は None。

    ※ #020 では検証用に追加するのみ。
    ※ backtest.py の support_1h への置き換えは #021 で実施。
    """
    window = low_1h.iloc[-lookback:]
    mask   = detect_swing_lows(window, n=n)
    sl     = window[mask]
    if len(sl) == 0:
        return None
    return float(sl.iloc[-1])


def get_all_swing_lows_1h(
    low_1h: pd.Series,
    n: int = 2,
    lookback: int = 240,
) -> pd.Series:
    """
    1H足 lookback=240 内の全 Swing Low を返す（複数）。
    test_1h_coincidence.py で最安値検索に使用。
    """
    window = low_1h.iloc[-lookback:]
    mask   = detect_swing_lows(window, n=n)
    return window[mask]
```

---

## 作業② src/test_1h_coincidence.py — 一致検証スクリプト 新規作成

### 目的
4H SL（4H足から抽出）と 1H SL 最安値（1H足 lookback=240 内の最深値）の
距離分布を計測し、「両者が一致する」という前提を定量的に確認する。

### 完全なスクリプト
```python
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swing_detector import (
    get_nearest_swing_low,
    get_all_swing_lows_1h,
    get_direction_4h,
)

DATA_PATH = Path(__file__).parent.parent / 'data/raw/usdjpy_multi_tf_2years.parquet'
PIP = 0.01
WARMUP_4H = 50   # 4H足 50本分ウォームアップ（約8日）

# ---- データ読み込み ----
df_5m = pd.read_parquet(DATA_PATH)

# ---- リサンプル（※ label='right', closed='right' は既存 backtest.py と同一。変更禁止）----
def resample_tf(df, rule):
    return df.resample(rule, label='right', closed='right').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
    ).dropna()

df_4h = resample_tf(df_5m, '4h')
df_1h = resample_tf(df_5m, '1h')

print(f"4H: {len(df_4h)}本 / 1H: {len(df_1h)}本")

# ---- スキャン ----
results = []

for i in range(WARMUP_4H, len(df_4h)):
    ts_4h = df_4h.index[i]

    # 4H 方向確認
    direction = get_direction_4h(
        df_4h['high'].iloc[:i+1],
        df_4h['low'].iloc[:i+1],
        n=3, lookback=20
    )
    if direction != 'LONG':
        continue

    # 4H SL 取得
    sl_4h = get_nearest_swing_low(
        df_4h['low'].iloc[:i+1], n=3, lookback=20
    )
    if sl_4h is None:
        continue

    # 対応する 1H インデックスを取得（ts_4h 以前の最新 1H 足）
    idx_1h = df_1h.index.searchsorted(ts_4h, side='right') - 1
    if idx_1h < 240:
        continue

    # 1H lookback=240 内の全 Swing Low を取得
    all_sl_1h = get_all_swing_lows_1h(
        df_1h['low'].iloc[:idx_1h+1], n=2, lookback=240
    )

    if len(all_sl_1h) == 0:
        results.append({
            'ts_4h': ts_4h,
            'sl_4h': round(sl_4h, 3),
            'sl_1h_deepest': None,
            'sl_1h_deepest_ts': None,
            'dist_pips': None,
            'detected': False,
            'match_5p': False,
            'match_10p': False,
            'match_20p': False,
        })
        continue

    # 1H SL 最安値（最深値）を特定
    sl_1h_deepest_ts  = all_sl_1h.idxmin()
    sl_1h_deepest_val = float(all_sl_1h.min())

    dist = abs(sl_4h - sl_1h_deepest_val) / PIP

    results.append({
        'ts_4h':            ts_4h,
        'sl_4h':            round(sl_4h, 3),
        'sl_1h_deepest':    round(sl_1h_deepest_val, 3),
        'sl_1h_deepest_ts': sl_1h_deepest_ts,
        'dist_pips':        round(dist, 2),
        'detected':         True,
        'match_5p':         dist <= 5.0,
        'match_10p':        dist <= 10.0,
        'match_20p':        dist <= 20.0,
    })

df_result = pd.DataFrame(results)
total     = len(df_result)
det       = df_result['detected'].sum()
m5        = df_result['match_5p'].sum()
m10       = df_result['match_10p'].sum()
m20       = df_result['match_20p'].sum()

dist_valid = df_result.dropna(subset=['dist_pips'])['dist_pips']

print(f"\n=== 1H-4H 一致検証レポート ===")
print(f"対象サンプル (4H LONG) : {total} 件")
print(f"1H SL 検出率           : {det}/{total} = {det/total*100:.1f}%")
print(f"")
print(f"--- 4H SL との距離分布 ---")
print(f"  mean   : {dist_valid.mean():.1f} pips")
print(f"  median : {dist_valid.median():.1f} pips")
print(f"  min    : {dist_valid.min():.1f} pips")
print(f"  max    : {dist_valid.max():.1f} pips")
print(f"")
print(f"--- 一致率（距離ベース）---")
print(f"  <= 5pips  : {m5}/{det} = {m5/det*100:.1f}%")
print(f"  <= 10pips : {m10}/{det} = {m10/det*100:.1f}%")
print(f"  <= 20pips : {m20}/{det} = {m20/det*100:.1f}%")

out_path = Path(__file__).parent.parent / 'logs/test_1h_coincidence.csv'
out_path.parent.mkdir(parents=True, exist_ok=True)
df_result.to_csv(out_path, index=False)
print(f"\n結果CSV: {out_path}")
```

---

## 作業③ plotter.py — plot_1h_window_5m() + __main__ 追加

### 関数本体

**注意: mplfinance は `returnfig=True` パターンで使うこと。
 `plt.subplots()` で ax を先に作って `mpf.plot(ax=ax)` に渡すパターンは使わない。
 既存の `plot_swing_check()` と同じパターンに統一する。**

```python
def plot_1h_window_5m(
    df_5m: pd.DataFrame,
    df_1h: pd.DataFrame,
    ts_sl_1h: pd.Timestamp,
    sl_4h: float,
    direction: str = 'LONG',
    pre_bars: int = 20,
    post_bars: int = 5,
    save_dir: str = 'logs/1h_windows',
) -> None:
    """
    1H 押し目ウィンドウ（前20本 + SL足 + 後5本 = 26本 ≈ 26時間）の
    5M OHLC + 5M SH/SL + 4H SL水平線 + 1H SL垂直線 を PNG 保存する。
    """
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    from pathlib import Path
    from swing_detector import detect_swing_highs, detect_swing_lows

    # ---- 1H ウィンドウ範囲を確定 ----
    idx_sl       = df_1h.index.get_loc(ts_sl_1h)
    win_start_1h = df_1h.index[max(0, idx_sl - pre_bars)]
    win_end_1h   = df_1h.index[min(len(df_1h) - 1, idx_sl + post_bars)]

    # ---- 5M 範囲を抽出 ----
    df_5m_win = df_5m.loc[win_start_1h:win_end_1h].copy()
    if len(df_5m_win) < 10:
        return

    # ---- 5M SH / SL 検出（窓内限定）----
    sh_mask = detect_swing_highs(df_5m_win['high'], n=2)
    sl_mask = detect_swing_lows(df_5m_win['low'],   n=2)
    sh_vals = df_5m_win['high'].where(sh_mask)
    sl_vals = df_5m_win['low'].where(sl_mask)

    # ---- mplfinance スタイル ----
    mc = mpf.make_marketcolors(
        up='#26a69a', down='#ef5350',
        edge='inherit', wick='inherit', volume='in'
    )
    s = mpf.make_mpf_style(
        marketcolors=mc, facecolor='#131722',
        edgecolor='#444', gridcolor='#2a2e39'
    )

    # ---- addplot（※ ax= 引数は渡さない。mplfinance の仕様。） ----
    apds = [
        mpf.make_addplot(sh_vals, type='scatter', marker='v',
                         markersize=60, color='#FA8072'),
        mpf.make_addplot(sl_vals, type='scatter', marker='^',
                         markersize=60, color='#87CEEB'),
    ]

    # ---- returnfig=True で fig/axes を取得（正しいパターン） ----
    fig, axes = mpf.plot(
        df_5m_win,
        type='candle',
        style=s,
        addplot=apds,
        returnfig=True,
        figsize=(16, 7),
    )
    ax = axes[0]
    fig.patch.set_facecolor('#131722')
    ax.set_facecolor('#131722')

    # ---- 4H SL 水平線 ----
    ax.axhline(y=sl_4h, color='#1E90FF', linewidth=1.5,
               linestyle='--', label=f'4H SL {sl_4h:.3f}')

    # ---- 1H SL 足の垂直線 ----
    # 注意: mplfinance の returnfig=True モードでは x軸が整数インデックスに
    #       なる場合がある。Timestamp 渡しで垂直線が表示されない場合は
    #       整数インデックス渡しに切り替えること。
    idx_in_win = df_5m_win.index.searchsorted(ts_sl_1h, side='left')
    if idx_in_win < len(df_5m_win):
        # まず Timestamp で試す
        ts_for_vline = df_5m_win.index[idx_in_win]
        try:
            ax.axvline(x=ts_for_vline, color='#ADFF2F',
                       linewidth=1.0, linestyle=':', label='1H SL')
        except Exception:
            # Timestamp が効かない場合は整数インデックスで描画
            ax.axvline(x=idx_in_win, color='#ADFF2F',
                       linewidth=1.0, linestyle=':', label='1H SL')

    # ---- タイトル・凡例 ----
    ts_str = ts_sl_1h.strftime('%Y%m%d_%H%M')
    ax.set_title(
        f'USDJPY 5M [{direction}]  1H SL: {ts_sl_1h}  '
        f'(前{pre_bars}本 + SL足 + 後{post_bars}本)',
        color='white', fontsize=11
    )
    ax.legend(facecolor='#1e222d', labelcolor='white', fontsize=9)
    ax.tick_params(colors='#aaa')

    # ---- 保存 ----
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    fname = save_path / f'{ts_str}_{direction}_1h_window.png'
    plt.savefig(fname, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved: {fname}")
```

### plotter.py の `if __name__ == '__main__'` ブロックに追加

既存の `__main__` ブロックの末尾に以下を追記する。
（既存のプロット処理は残す。消さない。）

```python
    # ===== #020: 1H-4H 一致イベントの窓プロット =====
    from swing_detector import get_all_swing_lows_1h

    # リサンプル（※ label='right', closed='right' — backtest.py と同一。変更禁止）
    def resample_tf(df, rule):
        return df.resample(rule, label='right', closed='right').agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
        ).dropna()

    df_4h = resample_tf(df_5m, '4h')
    df_1h = resample_tf(df_5m, '1h')

    MATCH_THRESH = 10.0  # pips（10pips以内を一致とみなす）
    MAX_PLOTS    = 20    # 最大プロット件数
    WARMUP       = 50

    plotted = 0
    for i in range(WARMUP, len(df_4h)):
        if plotted >= MAX_PLOTS:
            break
        ts_4h = df_4h.index[i]
        direction = get_direction_4h(
            df_4h['high'].iloc[:i+1], df_4h['low'].iloc[:i+1],
            n=3, lookback=20
        )
        if direction != 'LONG':
            continue
        sl_4h = get_nearest_swing_low(
            df_4h['low'].iloc[:i+1], n=3, lookback=20
        )
        if sl_4h is None:
            continue
        idx_1h = df_1h.index.searchsorted(ts_4h, side='right') - 1
        if idx_1h < 240:
            continue
        all_sl_1h = get_all_swing_lows_1h(
            df_1h['low'].iloc[:idx_1h+1], n=2, lookback=240
        )
        if len(all_sl_1h) == 0:
            continue
        sl_1h_ts  = all_sl_1h.idxmin()
        sl_1h_val = float(all_sl_1h.min())
        dist = abs(sl_4h - sl_1h_val) / 0.01

        if dist <= MATCH_THRESH:
            plot_1h_window_5m(
                df_5m=df_5m,
                df_1h=df_1h,
                ts_sl_1h=sl_1h_ts,
                sl_4h=sl_4h,
                direction=direction,
            )
            plotted += 1

    print(f"\n合計 {plotted} 枚 → logs/1h_windows/")
```

---

## 完了条件

- [ ] `get_nearest_swing_low_1h()` / `get_all_swing_lows_1h()` が swing_detector.py に追加されている
- [ ] **backtest.py / entry_logic.py / exit_logic.py が一切変更されていない**（git diff で確認）
- [ ] `python src/test_1h_coincidence.py` が実行できる
- [ ] `logs/test_1h_coincidence.csv` が生成されている
- [ ] `python src/plotter.py` が実行できる（TypeError なし）
- [ ] `logs/1h_windows/` に PNG が最大 20 枚保存されている
- [ ] `git commit -m "Feat: #020 1H-4H coincidence test + window plot"`

---

## 完了後の報告フォーマット

以下をそのまま Rex に貼り付けること:

```
=== #020 結果報告 ===
対象サンプル (4H LONG) :
1H SL 検出率           :    %
4H SL との距離
  mean / median :
一致率
  <=5pips  :    %
  <=10pips :    %
  <=20pips :    %
PNG 生成枚数 :
```
