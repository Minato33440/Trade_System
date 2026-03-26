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
    detect_swing_lows,
    get_direction_4h,
)
from src.entry_logic import check_15m_range_low, ALLOWED_PATTERNS


# ========== 定数 ==========
DATA_PATH      = _repo_root / 'data/raw/usdjpy_multi_tf_2years.parquet'
WARMUP_4H      = 50   # 4H足ウォームアップ本数
WINDOW_1H_PRE  = 20   # 1H窓: SL足の前 20本
WINDOW_1H_POST = 5    # 1H窓: SL足の後 5本
WINDOW_SEARCH  = 8    # 4H SL ts 前後 ±8本(8時間)で 1H SL を探す範囲
DIRECTION_MODE = 'LONG'  # SHORT は将来対応


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

def scan_window_entry(df_5m_win: pd.DataFrame, sl_4h_val: float):
    """窓内の 5M データから 15M DB/IHS 検出 → 5M ネック越えエントリーを返す。

    Args:
        df_5m_win : 窓内の 5M 足 DataFrame（open/high/low/close）
        sl_4h_val : 4H SL の価格（エントリー情報として記録）

    Returns:
        エントリー情報 dict、またはエントリー未発生の場合 None
    """
    if len(df_5m_win) < 30:
        return None

    # 窓内 5M → 15M リサンプル
    df_15m_win = resample_tf(df_5m_win, '15min')
    if len(df_15m_win) < 10:
        return None

    # check_15m_range_low() を呼ぶ
    # ⚠️ シグネチャ確認済み: (low_15m, high_15m, direction, n=3, lookback=50) -> dict
    # 戻り値: {'found': bool, 'sl_min': float, 'sl_last': float,
    #          'neck_15m': float, 'pattern': str, 'reason': str}
    result = check_15m_range_low(
        low_15m=df_15m_win['low'],
        high_15m=df_15m_win['high'],
        direction='LONG',
        n=3,
        lookback=50,
    )

    if not result['found']:
        return None

    pattern  = result['pattern']
    neck_15m = result['neck_15m']

    # パターンフィルター（ALLOWED_PATTERNS は entry_logic.py から import）
    if pattern not in ALLOWED_PATTERNS:
        return None

    # 5M ネック越え実体確定を検出
    for j in range(len(df_5m_win) - 1):
        row      = df_5m_win.iloc[j]
        body_low = min(float(row['open']), float(row['close']))

        if body_low > neck_15m:
            # 確定足 = j、執行足 = j+1
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

        # 窓内 5M データ抽出
        df_5m_win = df_5m.loc[win_start:win_end]
        if len(df_5m_win) < 30:
            continue

        # Layer 3: 窓内エントリースキャン
        entry = scan_window_entry(df_5m_win, sl_4h_val)
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

    return df_entries


if __name__ == '__main__':
    run_window_scan()
