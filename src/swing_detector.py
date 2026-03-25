"""swing_detector.py — Swing High/Low 検出エンジン。

TFごとの推奨n値:
    4H足 : n=5
    1H足 : n=3
    15M足: n=3
    5M足 : n=2

python src/swing_detector.py で動作確認可能。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ── 基本スイング検出 ───────────────────────────────────────────

def detect_swing_highs(high: pd.Series, n: int = 3) -> pd.Series:
    """Swing High（局所的な高値ピーク）を検出する。

    足[i]のHighが前後n本のHighより全て大きければ Swing High 確定。

    Args:
        high: 各足のHighのSeries（4H/1H/15M/5M どれでもOK）
        n:    左右に何本確認するか
              推奨: 4H=5, 1H=3, 15M=3, 5M=2

    Returns:
        True/False の bool Series（Trueの足がSwing High）
    """
    arr = high.values.astype(float)
    result = np.zeros(len(arr), dtype=bool)

    for i in range(n, len(arr) - n):
        if np.isnan(arr[i]):
            continue
        left_ok = all(arr[i] > arr[i - j] for j in range(1, n + 1))
        right_ok = all(arr[i] > arr[i + j] for j in range(1, n + 1))
        if left_ok and right_ok:
            result[i] = True

    return pd.Series(result, index=high.index)


def detect_swing_lows(low: pd.Series, n: int = 3) -> pd.Series:
    """Swing Low（局所的な安値の谷）を検出する。

    足[i]のLowが前後n本のLowより全て小さければ Swing Low 確定。

    Args:
        low: 各足のLowのSeries
        n:   左右に何本確認するか
             推奨: 4H=5, 1H=3, 15M=3, 5M=2

    Returns:
        True/False の bool Series（Trueの足がSwing Low）
    """
    arr = low.values.astype(float)
    result = np.zeros(len(arr), dtype=bool)

    for i in range(n, len(arr) - n):
        if np.isnan(arr[i]):
            continue
        left_ok = all(arr[i] < arr[i - j] for j in range(1, n + 1))
        right_ok = all(arr[i] < arr[i + j] for j in range(1, n + 1))
        if left_ok and right_ok:
            result[i] = True

    return pd.Series(result, index=low.index)


# ── 直近スイング価格取得 ──────────────────────────────────────

def get_nearest_swing_high(
    high: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> float | None:
    """current_idx より前の直近 Swing High の価格を返す。

    Args:
        high:        各足のHighのSeries
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数
        lookback:    何本前まで遡るか（4H=20, 1H=50）

    Returns:
        直近 Swing High の価格。見つからない場合は None（フォールバックなし）。
    """
    start = max(0, current_idx - lookback)
    window = high.iloc[start:current_idx]
    if len(window) < n * 2 + 1:
        return None

    swings = detect_swing_highs(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) == 0:
        return None

    return float(swing_prices.iloc[-1])


def get_nearest_swing_low(
    low: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> float | None:
    """current_idx より前の直近 Swing Low の価格を返す。

    Args:
        low:         各足のLowのSeries
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数
        lookback:    何本前まで遡るか

    Returns:
        直近 Swing Low の価格。見つからない場合は None（フォールバックなし）。
    """
    start = max(0, current_idx - lookback)
    window = low.iloc[start:current_idx]
    if len(window) < n * 2 + 1:
        return None

    swings = detect_swing_lows(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) == 0:
        return None

    return float(swing_prices.iloc[-1])


# ── 1H/15M 直近スイング取得 ────────────────────────────────────

def get_nearest_swing_high_1h(
    high_1h: pd.Series,
    n: int = 2,
    lookback: int = 20,
) -> "float | None":
    """1H足データから直近の Swing High を返す。

    neck_4h（押し目ゾーンの上限）として使用。

    Args:
        high_1h  : 1H足の High 系列
        n        : 前後確認本数（デフォルト2）
        lookback : 検索範囲（デフォルト20本 = 約20時間）

    Returns:
        直近 Swing High の価格。見つからない場合は None。
    """
    window = high_1h.iloc[-lookback:]
    if len(window) < n * 2 + 1:
        return None

    mask = detect_swing_highs(window, n=n)
    sh   = window[mask]

    if len(sh) == 0:
        return None

    return float(sh.iloc[-1])


def get_nearest_swing_low_15m(
    low_15m: pd.Series,
    n: int = 3,
    lookback: int = 20,
) -> "float | None":
    """15M足データから直近の Swing Low を返す。

    Support_1h（押し目ゾーンの下限）として使用。
    check_15m_range_low() の sl_min とは独立して取得する。
    sl_min は構造検出用（頭の最深値）。
    この関数は「現在のサポートライン」取得用。

    Args:
        low_15m  : 15M足の Low 系列
        n        : 前後確認本数（デフォルト3、#014確定値）
        lookback : 検索範囲（デフォルト20本 = 約5時間）

    Returns:
        直近 Swing Low の価格。見つからない場合は None。
    """
    window = low_15m.iloc[-lookback:]
    if len(window) < n * 2 + 1:
        return None

    mask = detect_swing_lows(window, n=n)
    sl   = window[mask]

    if len(sl) == 0:
        return None

    return float(sl.iloc[-1])


def get_nearest_swing_low_1h(
    low_1h: pd.Series,
    n: int = 2,
    lookback: int = 240,
) -> "float | None":
    """1H足 lookback=240（約10日分）で直近 Swing Low を返す。

    support_1h の正式版（#021 で backtest.py への置き換えを実施）。
    #020 では検証用追加のみ。backtest.py の get_nearest_swing_low_15m()
    呼び出しは変更しない。

    Args:
        low_1h   : 1H足の Low 系列
        n        : 前後確認本数（デフォルト2）
        lookback : 検索範囲（デフォルト240本 ≈ 10日分）

    Returns:
        直近 Swing Low の価格。見つからない場合は None。
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
    """1H足 lookback=240 内の全 Swing Low を返す（複数）。

    test_1h_coincidence.py で 4H SL との最安値一致確認に使用。

    Args:
        low_1h   : 1H足の Low 系列
        n        : 前後確認本数（デフォルト2）
        lookback : 検索範囲（デフォルト240本 ≈ 10日分）

    Returns:
        Swing Low の価格 Series（空の場合は空 Series）。
    """
    window = low_1h.iloc[-lookback:]
    mask   = detect_swing_lows(window, n=n)
    return window[mask]


# ── 4H方向判定 ────────────────────────────────────────────────

def get_direction_4h(
    high_4h: pd.Series,
    low_4h: pd.Series,
    current_idx: int,
    n: int = 5,
    lookback: int = 20,
) -> str:
    """4H実足のSwing構造から方向（上昇ダウ/下降ダウ）を判定する。

    LONG条件:  直近SH > 前回SH かつ 直近SL > 前回SL（上昇ダウ継続）
    SHORT条件: 直近SH < 前回SH かつ 直近SL < 前回SL（下降ダウ継続）

    Args:
        high_4h:     4H足のHigh Series
        low_4h:      4H足のLow Series
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数（4H推奨: n=5）
        lookback:    何本前まで遡るか（4H推奨: lookback=20）

    Returns:
        'LONG' / 'SHORT' / 'NONE'
    """
    start = max(0, current_idx - lookback)
    window_h = high_4h.iloc[start:current_idx]
    window_l = low_4h.iloc[start:current_idx]

    sh_flags = detect_swing_highs(window_h, n=n)
    sl_flags = detect_swing_lows(window_l, n=n)

    sh_list = window_h[sh_flags].values
    sl_list = window_l[sl_flags].values

    if len(sh_list) < 2 or len(sl_list) < 2:
        return "NONE"

    sh1 = float(sh_list[-2])
    sh2 = float(sh_list[-1])
    sl1 = float(sl_list[-2])
    sl2 = float(sl_list[-1])

    if sh2 > sh1 and sl2 > sl1:
        return "LONG"
    elif sh2 < sh1 and sl2 < sl1:
        return "SHORT"
    else:
        return "NONE"


def get_direction_from_raw_4h(
    df_5m: pd.DataFrame,
    current_time: pd.Timestamp,
    n: int = 3,
    lookback: int = 20,
) -> str:
    """5M足DataFrameを4H足にresampleしてから方向を判定する。

    バックテストでは _build_direction_5m() の一括版を使うこと。

    Args:
        df_5m:        5M足のDataFrame（High/Low/Close列を含む）
        current_time: 現在の時刻
        n:            Swing検出の前後確認本数
        lookback:     何本の4H足を遡るか

    Returns:
        'LONG' / 'SHORT' / 'NONE'
    """
    df_past = df_5m[df_5m.index < current_time]
    df_4h = df_past.resample("4h").agg(
        {"High": "max", "Low": "min", "Close": "last"}
    ).dropna()

    if len(df_4h) < lookback + n * 2:
        return "NONE"

    idx = len(df_4h) - 1
    return get_direction_4h(
        df_4h["High"], df_4h["Low"],
        current_idx=idx, n=n, lookback=lookback,
    )


def _build_direction_5m(
    df_5m_raw: pd.DataFrame,
    n: int = 3,
    lookback: int = 20,
) -> pd.Series:
    """全5Mバーの4H方向を一括プリコンピュートする（高速版）。

    Args:
        df_5m_raw: 5M足のDataFrame（High/Low/Close列を含む）
        n:         Swing検出の前後確認本数
        lookback:  何本の4H足を遡るか

    Returns:
        各5M足タイムスタンプに対する方向（'LONG'/'SHORT'/'NONE'）のSeries
    """
    df_4h_full = df_5m_raw.resample("4h").agg(
        {"High": "max", "Low": "min", "Close": "last"}
    ).dropna()

    ts_4h = df_4h_full.index

    dir_4h = {}
    for i in range(len(ts_4h)):
        if i < lookback + n * 2:
            dir_4h[ts_4h[i]] = "NONE"
            continue
        d = get_direction_4h(
            df_4h_full["High"], df_4h_full["Low"],
            current_idx=i, n=n, lookback=lookback,
        )
        dir_4h[ts_4h[i]] = d

    direction_5m = pd.Series("NONE", index=df_5m_raw.index, dtype=object)

    ts_4h_arr = ts_4h.values
    ts_5m_arr = df_5m_raw.index.values

    for i, ts in enumerate(ts_5m_arr):
        pos = np.searchsorted(ts_4h_arr, ts, side="right") - 1
        if pos < 0:
            continue
        direction_5m.iloc[i] = dir_4h.get(ts_4h[pos], "NONE")

    return direction_5m


# ── スクリプト直接実行時のセルフテスト ─────────────────────────

if __name__ == "__main__":
    import sys
    from pathlib import Path

    _repo_root = Path(__file__).resolve().parents[1]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

    print("=== swing_detector.py セルフテスト ===")

    np.random.seed(42)
    n_bars = 100
    price = 150.0 + np.cumsum(np.random.randn(n_bars) * 0.05)
    idx = pd.date_range("2024-01-01", periods=n_bars, freq="4h", tz="UTC")

    high = pd.Series(price + np.random.rand(n_bars) * 0.2, index=idx)
    low = pd.Series(price - np.random.rand(n_bars) * 0.2, index=idx)

    sh = detect_swing_highs(high, n=3)
    sl = detect_swing_lows(low, n=3)

    print(f"  Swing High 検出数: {sh.sum()}")
    print(f"  Swing Low  検出数: {sl.sum()}")

    sh_price = get_nearest_swing_high(high, len(high) - 1, n=3, lookback=50)
    sl_price = get_nearest_swing_low(low, len(low) - 1, n=3, lookback=50)
    print(f"  直近SH: {sh_price:.3f}" if sh_price is not None else "  直近SH: None（未検出）")
    print(f"  直近SL: {sl_price:.3f}" if sl_price is not None else "  直近SL: None（未検出）")

    direction = get_direction_4h(high, low, len(high) - 1, n=3, lookback=20)
    print(f"  4H方向: {direction}")

    print("\n✅ swing_detector.py エラーなし")
