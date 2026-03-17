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


def detect_swing_highs(high: pd.Series, n: int = 3) -> pd.Series:
    """Swing High を検出する。

    条件: high[i] が前後n本のhighより全て大きい（厳密な不等号）。

    Args:
        high: High価格のSeries
        n:    前後何本で比較するか

    Returns:
        bool Series（TrueがSwing High）

    TFごとの推奨n値:
        4H足 : n=5
        1H足 : n=3
        15M足: n=3
        5M足 : n=2
    """
    # 左側: high[i] > max(high[i-n .. i-1])
    left_max = high.shift(1).rolling(n, min_periods=n).max()
    # 右側: high[i] > max(high[i+1 .. i+n])
    right_max = high.shift(-1).iloc[::-1].rolling(n, min_periods=n).max().iloc[::-1]
    return (high > left_max) & (high > right_max)


def detect_swing_lows(low: pd.Series, n: int = 3) -> pd.Series:
    """Swing Low を検出する。

    条件: low[i] が前後n本のlowより全て小さい（厳密な不等号）。

    Args:
        low: Low価格のSeries
        n:   前後何本で比較するか

    Returns:
        bool Series（TrueがSwing Low）

    TFごとの推奨n値:
        4H足 : n=5
        1H足 : n=3
        15M足: n=3
        5M足 : n=2
    """
    # 左側: low[i] < min(low[i-n .. i-1])
    left_min = low.shift(1).rolling(n, min_periods=n).min()
    # 右側: low[i] < min(low[i+1 .. i+n])
    right_min = low.shift(-1).iloc[::-1].rolling(n, min_periods=n).min().iloc[::-1]
    return (low < left_min) & (low < right_min)


def get_nearest_swing_high(
    high: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> float:
    """current_idx より前のlookback本の範囲で直近SHの価格を返す。

    Args:
        high:        High価格のSeries
        current_idx: 現在のバーの整数位置
        n:           Swing検出の前後本数
        lookback:    何本前まで遡るか

    Returns:
        直近Swing Highの価格。見つからない場合はwindow.max()で代用。
    """
    start = max(0, current_idx - lookback)
    window = high.iloc[start:current_idx]
    if window.empty:
        return float("nan")
    sh_mask = detect_swing_highs(window, n=n)
    sh_prices = window[sh_mask]
    if sh_prices.empty:
        return float(window.max())
    return float(sh_prices.iloc[-1])


def get_nearest_swing_low(
    low: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> float:
    """current_idx より前のlookback本の範囲で直近SLの価格を返す。

    Args:
        low:         Low価格のSeries
        current_idx: 現在のバーの整数位置
        n:           Swing検出の前後本数
        lookback:    何本前まで遡るか

    Returns:
        直近Swing Lowの価格。見つからない場合はwindow.min()で代用。
    """
    start = max(0, current_idx - lookback)
    window = low.iloc[start:current_idx]
    if window.empty:
        return float("nan")
    sl_mask = detect_swing_lows(window, n=n)
    sl_prices = window[sl_mask]
    if sl_prices.empty:
        return float(window.min())
    return float(sl_prices.iloc[-1])


def get_direction_4h(
    high_4h: pd.Series,
    low_4h: pd.Series,
    current_idx: int,
    n: int = 5,
    lookback: int = 20,
) -> str:
    """4H足のダウ理論に基づきトレンド方向を判定する。

    LONG条件 : 直近SH > 前回SH かつ 直近SL > 前回SL（上昇ダウ継続）
    SHORT条件: 直近SH < 前回SH かつ 直近SL < 前回SL（下降ダウ継続）
    それ以外 : 'NONE'

    get_direction_4h() == 'LONG' が継続する限りエントリーを繰り返す
    （4H上昇ダウ継続中に押し目条件が揃うたびにエントリーを繰り返す構造）。

    Args:
        high_4h:     4H足High価格のSeries
        low_4h:      4H足Low価格のSeries
        current_idx: 現在のバーの整数位置
        n:           Swing検出の前後本数（4H推奨: n=5）
        lookback:    何本前まで遡るか

    Returns:
        'LONG' / 'SHORT' / 'NONE'

    TFごとの推奨n値:
        4H足 : n=5
        1H足 : n=3
        15M足: n=3
        5M足 : n=2
    """
    start = max(0, current_idx - lookback)
    high_window = high_4h.iloc[start:current_idx]
    low_window = low_4h.iloc[start:current_idx]

    # SH/SL を2つ確保するのに最低限必要なバー数
    if len(high_window) < n * 2 + 1:
        return "NONE"

    sh_mask = detect_swing_highs(high_window, n=n)
    sl_mask = detect_swing_lows(low_window, n=n)

    sh_prices = high_window[sh_mask]
    sl_prices = low_window[sl_mask]

    # 直近2つのSH/SLが必要（ダウ理論の比較に2点必要）
    if len(sh_prices) < 2 or len(sl_prices) < 2:
        return "NONE"

    latest_sh = float(sh_prices.iloc[-1])
    prev_sh = float(sh_prices.iloc[-2])
    latest_sl = float(sl_prices.iloc[-1])
    prev_sl = float(sl_prices.iloc[-2])

    if latest_sh > prev_sh and latest_sl > prev_sl:
        return "LONG"
    if latest_sh < prev_sh and latest_sl < prev_sl:
        return "SHORT"
    return "NONE"


# ── 動作確認 ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  swing_detector.py 動作確認")
    print("=" * 60)

    np.random.seed(42)
    n_bars = 200

    # 上昇トレンドのサンプルデータ生成
    trend = np.linspace(148.0, 155.0, n_bars)
    noise = np.random.randn(n_bars) * 0.3
    close = pd.Series(trend + noise)
    high = close + np.abs(np.random.randn(n_bars)) * 0.2
    low = close - np.abs(np.random.randn(n_bars)) * 0.2
    high.name = "High"
    low.name = "Low"

    # Swing 検出
    sh = detect_swing_highs(high, n=3)
    sl = detect_swing_lows(low, n=3)

    print(f"\nSwing Highs: {int(sh.sum())} 個")
    print(f"Swing Lows:  {int(sl.sum())} 個")

    # 最初の10件表示
    sh_data = high[sh].reset_index(drop=True)
    sl_data = low[sl].reset_index(drop=True)

    print("\n--- Swing High サンプル（最初の10件） ---")
    print(sh_data.head(10).to_string())

    print("\n--- Swing Low サンプル（最初の10件） ---")
    print(sl_data.head(10).to_string())

    # 直近SH/SL取得
    nearest_sh = get_nearest_swing_high(high, current_idx=150, n=3, lookback=50)
    nearest_sl = get_nearest_swing_low(low, current_idx=150, n=3, lookback=50)
    print(f"\n直近SH (current_idx=150, lookback=50): {nearest_sh:.4f}")
    print(f"直近SL (current_idx=150, lookback=50): {nearest_sl:.4f}")

    # 全バーの方向判定集計
    print("\n--- 全バー方向判定（n=5, lookback=20）---")
    counts: dict[str, int] = {"LONG": 0, "SHORT": 0, "NONE": 0}
    for i in range(20, n_bars):
        d = get_direction_4h(high, low, current_idx=i, n=5, lookback=20)
        counts[d] += 1
    print(f"LONG: {counts['LONG']}, SHORT: {counts['SHORT']}, NONE: {counts['NONE']}")

    # idx=150 単体の方向判定
    direction = get_direction_4h(high, low, current_idx=150, n=5, lookback=20)
    print(f"\n4H方向判定 (current_idx=150): {direction}")

    print("\n[OK] swing_detector.py 正常終了")
