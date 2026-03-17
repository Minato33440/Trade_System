"""swing_detector.py — ミナト流 Swing High / Low 検出モジュール。

Phase A 最優先実装。
4H / 1H / 15M / 5M 各タイムフレーム対応のスイング検出。

TFごとの推奨 n 値:
  4H 足 : n=5
  1H 足 : n=3
  15M 足: n=3
  5M 足 : n=2
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
) -> float:
    """current_idx より前の直近 Swing High の価格を返す。

    ストップライン・ネックラインの基準価格として使用。

    Args:
        high:        各足のHighのSeries
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数
        lookback:    何本前まで遡るか（4H=20, 1H=50）

    Returns:
        直近 Swing High の価格。見つからない場合は window の max。
    """
    start = max(0, current_idx - lookback)
    window = high.iloc[start:current_idx]
    if len(window) < n * 2 + 1:
        return float(window.max()) if len(window) > 0 else float("nan")

    swings = detect_swing_highs(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) == 0:
        return float(window.max())

    return float(swing_prices.iloc[-1])


def get_nearest_swing_low(
    low: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> float:
    """current_idx より前の直近 Swing Low の価格を返す。

    4H押し目の基準・ネックライン（半値利確ターゲット）として使用。

    Args:
        low:         各足のLowのSeries
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数
        lookback:    何本前まで遡るか

    Returns:
        直近 Swing Low の価格。見つからない場合は window の min。
    """
    start = max(0, current_idx - lookback)
    window = low.iloc[start:current_idx]
    if len(window) < n * 2 + 1:
        return float(window.min()) if len(window) > 0 else float("nan")

    swings = detect_swing_lows(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) == 0:
        return float(window.min())

    return float(swing_prices.iloc[-1])


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
        high_4h:     4H足のHigh Series（本物のOHLCデータ）
        low_4h:      4H足のLow Series（本物のOHLCデータ）
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数（4H推奨: n=5）
        lookback:    何本前まで遡るか（4H推奨: lookback=20）

    Returns:
        'LONG' / 'SHORT' / 'NONE'
    """
    # 直近のSH/SL
    sh_recent = get_nearest_swing_high(high_4h, current_idx, n=n, lookback=lookback)
    sl_recent = get_nearest_swing_low(low_4h, current_idx, n=n, lookback=lookback)

    # 一つ前のSH/SLを探すためにcurrent_idxをずらして再取得
    # 直近SHの位置を特定してその前を探す
    start = max(0, current_idx - lookback)
    window_h = high_4h.iloc[start:current_idx]
    window_l = low_4h.iloc[start:current_idx]

    sh_flags = detect_swing_highs(window_h, n=n)
    sl_flags = detect_swing_lows(window_l, n=n)

    sh_list = window_h[sh_flags].values
    sl_list = window_l[sl_flags].values

    if len(sh_list) < 2 or len(sl_list) < 2:
        return "NONE"

    sh1 = float(sh_list[-2])  # 前回SH
    sh2 = float(sh_list[-1])  # 直近SH
    sl1 = float(sl_list[-2])  # 前回SL
    sl2 = float(sl_list[-1])  # 直近SL

    if sh2 > sh1 and sl2 > sl1:
        return "LONG"   # 高値・安値ともに切り上がり = 上昇ダウ
    elif sh2 < sh1 and sl2 < sl1:
        return "SHORT"  # 高値・安値ともに切り下がり = 下降ダウ
    else:
        return "NONE"   # トレンドレス


def get_direction_from_raw_4h(
    df_5m: pd.DataFrame,
    current_time: pd.Timestamp,
    n: int = 3,
    lookback: int = 20,
) -> str:
    """5M足DataFrameを4H足にresampleしてから方向を判定する。

    df_multi の forward-fill 問題を回避するための実装。
    毎回呼び出す場合はパフォーマンスが悪いため、
    バックテストでは _build_direction_5m() の一括版を使うこと。

    Args:
        df_5m:        5M足のDataFrame（High/Low/Close列を含む）
        current_time: 現在の時刻（この時点より前のデータで判定）
        n:            Swing検出の前後確認本数（4H足でn=3推奨）
        lookback:     何本の4H足を遡るか（20本 ≒ 80時間）

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

    バックテストループ内で毎回resampleするのを避けるため、
    事前に全期間の方向を計算しておく。

    Args:
        df_5m_raw: 5M足のDataFrame（High/Low/Close列を含む）
        n:         Swing検出の前後確認本数
        lookback:  何本の4H足を遡るか

    Returns:
        各5M足タイムスタンプに対する方向（'LONG'/'SHORT'/'NONE'）のSeries
    """
    # 全期間を一括resample
    df_4h_full = df_5m_raw.resample("4h").agg(
        {"High": "max", "Low": "min", "Close": "last"}
    ).dropna()

    # 4H足の全インデックス
    ts_4h = df_4h_full.index

    # 各4H足の方向を事前計算
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

    # 5M足インデックスに対して対応する4H足の方向をマッピング
    direction_5m = pd.Series("NONE", index=df_5m_raw.index, dtype=object)

    # searchsorted で効率的にマッピング
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

    # サンプルデータ生成
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
    print(f"  直近SH: {sh_price:.3f}")
    print(f"  直近SL: {sl_price:.3f}")

    direction = get_direction_4h(high, low, len(high) - 1, n=3, lookback=20)
    print(f"  4H方向: {direction}")

    # 実データでテスト
    data_path = _repo_root / "data" / "raw" / "usdjpy_multi_tf_2years.parquet"
    if data_path.exists():
        print("\n--- 実データテスト ---")
        df = pd.read_parquet(data_path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.DatetimeIndex(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df_5m = df[["5M_High", "5M_Low", "5M_Close"]].ffill()
        df_5m = df_5m.rename(columns={
            "5M_High": "High", "5M_Low": "Low", "5M_Close": "Close"
        })

        print("  4H方向プリコンピュート中（最初の200本のみ）...")
        dir_series = _build_direction_5m(df_5m.iloc[:200], n=3, lookback=10)
        counts = dir_series.value_counts()
        print(f"  方向分布: {counts.to_dict()}")

        sample = dir_series[dir_series != "NONE"].head(5)
        for ts, d in sample.items():
            print(f"    {ts}  →  {d}")
    else:
        print("\n  [INFO] 実データファイルが見つからないためスキップ")

    print("\n✅ swing_detector.py エラーなし")
