"""
#021 window_scan_entries.csv の 13件を精査プロット

表示要素:
  - 5M ローソク足（窓内）
  - 4H SL 水平線（青破線）
  - 15M neck 水平線（黄緑破線）  ← window_scanner 検出値
  - 1H SL 垂直線（青緑点線）
  - エントリー足 垂直線（赤実線）
  - タイトル: パターン / エントリー価格 / sl_4h
保存先: logs/window_scan_plots/
"""
from __future__ import annotations

import sys
from pathlib import Path

import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows

# ---- データ読み込み ----
DATA_PATH = _repo_root / 'data/raw/usdjpy_multi_tf_2years.parquet'
CSV_PATH  = _repo_root / 'logs/window_scan_entries.csv'
OUT_DIR   = _repo_root / 'logs/window_scan_plots'
OUT_DIR.mkdir(parents=True, exist_ok=True)

df_raw = pd.read_parquet(DATA_PATH)
df_5m = df_raw[['5M_Open', '5M_High', '5M_Low', '5M_Close']].rename(
    columns={'5M_Open': 'open', '5M_High': 'high',
             '5M_Low': 'low', '5M_Close': 'close'}
).dropna()


def resample_tf(df, rule):
    return (
        df.resample(rule, label='right', closed='right')
        .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        .dropna()
    )


df_1h = resample_tf(df_5m, '1h')

# ---- mplfinance スタイル ----
mc = mpf.make_marketcolors(
    up='#26a69a', down='#ef5350',
    edge='inherit', wick='inherit', volume='in'
)
s = mpf.make_mpf_style(
    marketcolors=mc, facecolor='#131722',
    edgecolor='#444', gridcolor='#2a2e39'
)

# ---- CSV 読み込み ----
df_csv = pd.read_csv(CSV_PATH, parse_dates=[
    'confirm_ts', 'entry_ts', 'ts_4h', 'sl_4h_ts', 'sl_1h_ts'
])

print(f"Total entries: {len(df_csv)}")

for idx, row in df_csv.iterrows():
    sl_1h_ts   = pd.Timestamp(row['sl_1h_ts'])
    sl_4h      = float(row['sl_4h'])
    neck_15m   = float(row['neck_15m'])
    entry_ts   = pd.Timestamp(row['entry_ts'])
    entry_price= float(row['entry_price'])
    pattern    = row['pattern']

    # 窓範囲（1H 前20 + SL + 後5）
    idx_sl_1h = df_1h.index.searchsorted(sl_1h_ts, side='right') - 1
    win_start  = df_1h.index[max(0, idx_sl_1h - 20)]
    win_end    = df_1h.index[min(len(df_1h) - 1, idx_sl_1h + 5)]

    df_5m_win  = df_5m.loc[win_start:win_end].copy()
    if len(df_5m_win) < 10:
        print(f"  skip {sl_1h_ts}: bars too few")
        continue

    # SH/SL マーカー
    sh_mask = detect_swing_highs(df_5m_win['high'], n=2)
    sl_mask = detect_swing_lows(df_5m_win['low'],   n=2)

    fig, axes = mpf.plot(
        df_5m_win, type='candle', style=s,
        returnfig=True, figsize=(16, 7),
    )
    ax = axes[0]
    for _ax in axes[1:]:
        _ax.set_visible(False)
    fig.patch.set_facecolor('#131722')
    ax.set_facecolor('#131722')

    # SH/SL scatter（整数インデックス）
    sh_x = [j for j, v in enumerate(sh_mask) if v]
    sh_y = [float(df_5m_win['high'].iloc[j]) for j in sh_x]
    sl_x = [j for j, v in enumerate(sl_mask) if v]
    sl_y = [float(df_5m_win['low'].iloc[j]) for j in sl_x]
    if sh_x:
        ax.scatter(sh_x, sh_y, marker='v', s=60, color='#FA8072', zorder=5)
    if sl_x:
        ax.scatter(sl_x, sl_y, marker='^', s=60, color='#87CEEB', zorder=5)

    # 4H SL 水平線（青破線）
    ax.axhline(y=sl_4h, color='#1E90FF', linewidth=1.5,
               linestyle='--', label=f'4H SL {sl_4h:.3f}')

    # 15M neck 水平線（黄緑破線）
    ax.axhline(y=neck_15m, color='#ADFF2F', linewidth=1.5,
               linestyle='--', label=f'15M neck {neck_15m:.3f}')

    # 1H SL 垂直線（シアン点線）
    idx_1h_in_win = df_5m_win.index.searchsorted(sl_1h_ts, side='left')
    if idx_1h_in_win < len(df_5m_win):
        ax.axvline(x=idx_1h_in_win, color='#00CED1',
                   linewidth=1.0, linestyle=':', label='1H SL')

    # エントリー足 垂直線（赤実線）
    idx_entry_in_win = df_5m_win.index.searchsorted(entry_ts, side='left')
    if idx_entry_in_win < len(df_5m_win):
        ax.axvline(x=idx_entry_in_win, color='#FF4444',
                   linewidth=1.5, linestyle='-', label=f'Entry {entry_price:.3f}')

    # タイトル
    ts_str = sl_1h_ts.strftime('%Y%m%d_%H%M')
    ax.set_title(
        f'[{idx + 1:02d}/{len(df_csv)}] {ts_str} LONG  '
        f'pat={pattern}  entry={entry_price:.3f}  '
        f'neck={neck_15m:.3f}  sl4h={sl_4h:.3f}',
        color='white', fontsize=10
    )
    ax.legend(facecolor='#1e222d', labelcolor='white', fontsize=9)
    ax.tick_params(colors='#aaa')

    fname = OUT_DIR / f'{idx + 1:02d}_{ts_str}_{pattern}_scan.png'
    plt.savefig(fname, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved: {fname.name}")

print(f"\nDone. {len(df_csv)} plots -> {OUT_DIR}")
