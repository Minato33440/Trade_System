"""
REX Window Scanner — 窓ベース階層スキャン（Phase 1: シンプル版）

4H上昇トレンド → 1H窓確定 → 窓内15M DB/IHS → 5Mネック越えエントリー検出。
既存 backtest.py を変更せず、独立したスキャナーとして動作する。

⛔ 禁止事項:
  - backtest.py / entry_logic.py / exit_logic.py / swing_detector.py を変更しない
  - resample_tf の label='right', closed='right' を変更しない
  - manage_exit() の統合は #022 以降
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import (
    detect_swing_highs,
    detect_swing_lows,
    get_direction_4h,
)
from src.entry_logic import check_15m_range_low, ALLOWED_PATTERNS

PLOT_OUT_DIR = _repo_root / 'logs/window_scan_plots'


# ========== 定数 ==========
DATA_PATH      = _repo_root / 'data/raw/usdjpy_multi_tf_2years.parquet'
WARMUP_4H      = 50   # 4H足ウォームアップ本数
WINDOW_1H_PRE  = 20   # 1H窓: SL足の前 20本
WINDOW_1H_POST = 10   # 1H窓: SL足の後 10本（5 → 10に延長）
WINDOW_SEARCH  = 8    # 4H SL ts 前後 ±8本(8時間)で 1H SL を探す範囲
DIRECTION_MODE = 'LONG'  # SHORT は将来対応
WICKTOL_PIPS   = 5.0     # 5M ネック越え許容 pips（実体下端 > neck + 5pips）
PIP            = 0.01    # USDJPY 1pip = 0.01 円
PLOT_PRE_H     = 25      # プロット: 1H SL 前 25時間（スキャン窓とは独立）
PLOT_POST_H    = 40      # プロット: 1H SL 後 40時間


# ========== リサンプル（backtest.py と同一。変更禁止） ==========

def resample_tf(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """5M足を指定 TF にリサンプルする。
    ※ label='right', closed='right' は既存 backtest.py と同一。変更禁止。
    """
    return (
        df.resample(rule, label='right', closed='right')
        .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        .dropna()
    )


# ========== Layer 1: 4H 構造スキャン ==========

def scan_4h_events(df_4h: pd.DataFrame):
    """4H LONG 期間の各バーについて 4H SL のタイムスタンプと価格を生成する。

    Yields:
        (i_4h, ts_4h, sl_4h_val, sl_4h_ts)
          i_4h     : 4H足の整数インデックス
          ts_4h    : 現在の 4H足タイムスタンプ
          sl_4h_val: 直近 4H SL の価格
          sl_4h_ts : 直近 4H SL のタイムスタンプ
    """
    for i in range(WARMUP_4H, len(df_4h)):
        direction = get_direction_4h(
            df_4h['high'], df_4h['low'],
            current_idx=i, n=3, lookback=20,
        )
        if direction != DIRECTION_MODE:
            continue

        # 直近 4H SL の価格とタイムスタンプを取得
        start = max(0, i - 20 + 1)
        window_low = df_4h['low'].iloc[start:i + 1]
        mask = detect_swing_lows(window_low, n=3)
        sl_series = window_low[mask]
        if len(sl_series) == 0:
            continue

        sl_4h_val = float(sl_series.iloc[-1])
        sl_4h_ts  = sl_series.index[-1]

        yield (i, df_4h.index[i], sl_4h_val, sl_4h_ts)


# ========== Layer 2: 1H 窓確定 ==========

def get_1h_window_range(
    df_1h: pd.DataFrame,
    sl_4h_ts: pd.Timestamp,
    sl_4h_val: float,
):
    """4H SL タイムスタンプを起点に 1H 窓の範囲を返す。

    Args:
        df_1h     : 1H足 DataFrame
        sl_4h_ts  : 4H SL のタイムスタンプ
        sl_4h_val : 4H SL の価格（近傍 1H SL 探索に使用）

    Returns:
        (win_start_ts, win_end_ts, sl_1h_ts) or None
    """
    idx_center = df_1h.index.searchsorted(sl_4h_ts, side='right') - 1
    if idx_center < WINDOW_SEARCH:
        return None

    # ±WINDOW_SEARCH 本の 1H 足で SL を探す
    ws = max(0, idx_center - WINDOW_SEARCH)
    we = min(len(df_1h) - 1, idx_center + WINDOW_SEARCH)
    search_window = df_1h['low'].iloc[ws:we + 1]

    mask = detect_swing_lows(search_window, n=2)
    sl_1h_near = search_window[mask]
    if len(sl_1h_near) == 0:
        return None

    # 4H SL 価格に最も近い 1H SL を選択
    dists    = abs(sl_1h_near - sl_4h_val)
    sl_1h_ts = dists.idxmin()

    # 窓範囲を確定（前 20本 + SL足 + 後 5本）
    idx_sl  = df_1h.index.get_loc(sl_1h_ts)
    win_start = df_1h.index[max(0, idx_sl - WINDOW_1H_PRE)]
    win_end   = df_1h.index[min(len(df_1h) - 1, idx_sl + WINDOW_1H_POST)]

    return (win_start, win_end, sl_1h_ts)


# ========== Layer 3: 窓内スキャン ==========

def scan_window_entry(df_5m_win: pd.DataFrame, sl_4h_val: float, sl_1h_ts: pd.Timestamp):
    """窓内の 5M データから 15M DB/IHS 検出 → 5M ネック越えエントリーを返す。

    Args:
        df_5m_win : 窓内の 5M 足 DataFrame（open/high/low/close）
        sl_4h_val : 4H SL の価格（エントリー情報として記録）
        sl_1h_ts  : 1H SL のタイムスタンプ（ネック越えループの開始位置限定）

    Returns:
        エントリー情報 dict、またはエントリー未発生の場合 None
    """
    if len(df_5m_win) < 30:
        return None

    # --- 15M リサンプル（窓全体: パターン検出用）---
    df_15m_win = resample_tf(df_5m_win, '15min')
    if len(df_15m_win) < 6:
        return None

    # --- パターンラベル取得（check_15m_range_low はラベル目的のみ使用）---
    result = check_15m_range_low(
        low_15m=df_15m_win['low'],
        high_15m=df_15m_win['high'],
        direction='LONG',
        n=3,
        lookback=50,
    )
    pattern = result.get('pattern', 'UNKNOWN') if result.get('found') else 'UNKNOWN'

    if pattern not in ALLOWED_PATTERNS:
        return None

    # --- neck = 1H SL 以降の 15M SH 最高値（★修正点: check_15m_range_low の neck は使わない）---
    df_15m_after_sl = df_15m_win.loc[sl_1h_ts:]
    if len(df_15m_after_sl) < 3:
        return None
    sh_mask = detect_swing_highs(df_15m_after_sl['high'], n=3)
    sh_vals = df_15m_after_sl['high'][sh_mask]
    if len(sh_vals) == 0:
        return None
    neck_15m = float(sh_vals.max())

    # --- 5M ネック越え実体確定（#022修正済み: sl_1h_ts 以降から走査）---
    sl_1h_idx = df_5m_win.index.searchsorted(sl_1h_ts)
    for j in range(sl_1h_idx, len(df_5m_win) - 1):
        row = df_5m_win.iloc[j]
        if min(float(row['open']), float(row['close'])) > neck_15m + WICKTOL_PIPS * PIP:
            entry_bar = df_5m_win.iloc[j + 1]
            return {
                'pattern':     pattern,
                'neck_15m':    neck_15m,
                'confirm_ts':  df_5m_win.index[j],
                'entry_ts':    df_5m_win.index[j + 1],
                'entry_price': float(entry_bar['open']),
                'sl_4h':       sl_4h_val,
            }

    return None  # ネック越え未発生


# ========== プロット生成 ==========

def save_entry_plot(
    df_5m: pd.DataFrame,
    entry: dict,
    idx: int,
    total: int,
) -> None:
    """検出エントリーの 5M チャート + 参照線を PNG 保存する。

    表示要素（PLOT_DESIGN_CONFIRMED 仕様）:
      - 5M ローソク足
      - 5M SH/SL マーカー（scatter）
      - 15M neck 水平線（黄緑 #ADFF2F）
      - 4H SL 水平線（青 #1E90FF）
      - 1H SL 垂直線（シアン #00FFFF）
      - エントリー時刻垂直線（赤 #FF0000）

    プロット範囲: sl_1h_ts 基準で前25h / 後40h（スキャン窓とは独立）
    """
    try:
        import mplfinance as mpf
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [SKIP] mplfinance が未インストールのためプロットをスキップ")
        return

    sl_1h_ts    = entry['sl_1h_ts']
    entry_ts    = entry['entry_ts']
    neck_15m    = entry['neck_15m']
    sl_4h_val   = entry['sl_4h']
    pattern     = entry['pattern']
    entry_price = entry['entry_price']

    # ---- プロット専用範囲（スキャン窓とは別に切り出す）----
    plot_start = sl_1h_ts - pd.Timedelta(hours=PLOT_PRE_H)
    plot_end   = sl_1h_ts + pd.Timedelta(hours=PLOT_POST_H)
    df_plot    = df_5m.loc[plot_start:plot_end].copy()
    if len(df_plot) < 10:
        print(f"  [SKIP] プロットデータ不足: {sl_1h_ts}")
        return

    # ---- 5M SH/SL 検出 ----
    sh_mask = detect_swing_highs(df_plot['high'], n=2)
    sl_mask = detect_swing_lows(df_plot['low'],   n=2)

    # ---- mplfinance スタイル ----
    mc = mpf.make_marketcolors(
        up='#26a69a', down='#ef5350',
        edge='inherit', wick='inherit', volume='in'
    )
    s = mpf.make_mpf_style(
        marketcolors=mc, facecolor='#131722',
        edgecolor='#444', gridcolor='#2a2e39'
    )

    fig, axes = mpf.plot(
        df_plot,
        type='candle', style=s,
        returnfig=True, figsize=(18, 7),
        warn_too_much_data=1000,
    )
    ax = axes[0]
    for _ax in axes[1:]:
        _ax.set_visible(False)
    fig.patch.set_facecolor('#131722')
    ax.set_facecolor('#131722')

    # ---- SH/SL マーカー（ax.scatter で整数x軸に描画）----
    sh_x = [j for j, v in enumerate(sh_mask) if v]
    sh_y = [float(df_plot['high'].iloc[j]) for j in sh_x]
    sl_x = [j for j, v in enumerate(sl_mask) if v]
    sl_y = [float(df_plot['low'].iloc[j]) for j in sl_x]
    if sh_x:
        ax.scatter(sh_x, sh_y, marker='v', s=60, color='#FA8072', zorder=5)
    if sl_x:
        ax.scatter(sl_x, sl_y, marker='^', s=60, color='#87CEEB', zorder=5)

    # ---- 15M neck 水平線 ----
    ax.axhline(y=neck_15m, color='#ADFF2F', linewidth=1.5,
               linestyle='--', label=f'15M neck {neck_15m:.3f}')

    # ---- 4H SL 水平線 ----
    ax.axhline(y=sl_4h_val, color='#1E90FF', linewidth=1.5,
               linestyle='--', label=f'4H SL {sl_4h_val:.3f}')

    # ---- 1H SL 垂直線（シアン）----
    idx_sl = df_plot.index.searchsorted(sl_1h_ts, side='left')
    if idx_sl < len(df_plot):
        try:
            ax.axvline(x=idx_sl, color='#00FFFF', linewidth=1.0,
                       linestyle=':', label='1H SL')
        except Exception:
            pass

    # ---- エントリー垂直線（赤）----
    idx_entry = df_plot.index.searchsorted(entry_ts, side='left')
    if idx_entry < len(df_plot):
        try:
            ax.axvline(x=idx_entry, color='#FF0000', linewidth=2.0,
                       linestyle='-', label=f'Entry {entry_price:.3f}')
        except Exception:
            pass

    # ---- タイトル（英語: CJK豆腐対策）----
    ts_str = pd.Timestamp(sl_1h_ts).strftime('%Y%m%d_%H%M')
    ax.set_title(
        f'[{idx:02d}/{total}] {ts_str} LONG  pat={pattern}'
        f'  entry={entry_price:.3f}  neck={neck_15m:.3f}  sl4h={sl_4h_val:.3f}',
        color='white', fontsize=10
    )
    ax.legend(facecolor='#1e222d', labelcolor='white', fontsize=9)
    ax.tick_params(colors='#aaa')

    # ---- 保存 ----
    PLOT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = PLOT_OUT_DIR / f'{idx:02d}_{ts_str}_{pattern}_scan.png'
    plt.savefig(fname, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  plot saved: {fname.name}")


# ========== メイン実行 ==========

def run_window_scan() -> pd.DataFrame:
    """窓ベース階層スキャンのメインループ。

    Returns:
        エントリー情報の DataFrame（logs/window_scan_entries.csv にも保存）
    """
    # ---- データ読み込み ----
    df_raw = pd.read_parquet(DATA_PATH)

    df_5m = df_raw[['5M_Open', '5M_High', '5M_Low', '5M_Close']].rename(
        columns={
            '5M_Open':  'open',
            '5M_High':  'high',
            '5M_Low':   'low',
            '5M_Close': 'close',
        }
    ).dropna()

    df_4h = resample_tf(df_5m, '4h')
    df_1h = resample_tf(df_5m, '1h')

    print(f"Data: 5M={len(df_5m)} / 1H={len(df_1h)} / 4H={len(df_4h)}")

    # ---- スキャン ----
    entries      = []
    seen_windows = set()  # 同一窓の重複スキップ用

    for (i_4h, ts_4h, sl_4h_val, sl_4h_ts) in scan_4h_events(df_4h):

        # 同一 4H SL タイムスタンプの窓は 1 回だけ処理
        if sl_4h_ts in seen_windows:
            continue
        seen_windows.add(sl_4h_ts)

        # Layer 2: 1H 窓確定
        win_result = get_1h_window_range(df_1h, sl_4h_ts, sl_4h_val)
        if win_result is None:
            continue
        win_start, win_end, sl_1h_ts = win_result

        # 窓幅チェック（作業①: 35h超を警告）
        win_hours = (win_end - win_start).total_seconds() / 3600
        if win_hours > 35:
            print(f"  [WARN] 窓幅異常: {win_start} ~ {win_end} = {win_hours:.1f}h")

        # 窓内 5M データ抽出
        df_5m_win = df_5m.loc[win_start:win_end]
        if len(df_5m_win) < 30:
            continue

        # Layer 3: 窓内エントリースキャン
        entry = scan_window_entry(df_5m_win, sl_4h_val, sl_1h_ts)
        if entry is None:
            continue

        entry['ts_4h']    = ts_4h
        entry['sl_4h_ts'] = sl_4h_ts
        entry['sl_1h_ts'] = sl_1h_ts
        entry['window']   = f"{win_start} ~ {win_end}"
        entries.append(entry)

        print(f"  ENTRY: {entry['entry_ts']} @ {entry['entry_price']:.3f}"
              f" | pat={entry['pattern']} | neck={entry['neck_15m']:.3f}")

    # ---- 結果出力 ----
    df_entries = pd.DataFrame(entries)
    total      = len(df_entries)

    print(f"\n=== Window Scanner Phase 1 結果 ===")
    print(f"スキャン窓数     : {len(seen_windows)}")
    print(f"エントリー検出数 : {total}")

    if total > 0:
        for pat in ['DB', 'IHS', 'ASCENDING']:
            n = len(df_entries[df_entries['pattern'] == pat])
            print(f"  {pat}: {n} 件")

    # CSV 保存
    out_path = _repo_root / 'logs/window_scan_entries.csv'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_entries.to_csv(out_path, index=False)
    print(f"\n結果CSV: {out_path}")

    # ---- プロット生成 ----
    if total > 0:
        print(f"\nプロット生成中 ({total}件)...")
        for i, row in enumerate(entries, start=1):
            save_entry_plot(df_5m, row, idx=i, total=total)
        print(f"プロット保存先: {PLOT_OUT_DIR}")

    return df_entries


if __name__ == '__main__':
    run_window_scan()
