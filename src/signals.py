"""signals.py — ミナト流 MTF シグナル生成モジュール。

mtf_minato_short_v2:
  4H/1H/15M/5M マルチタイムフレームの OHLCV DataFrame から
  セッション時間帯ごとにエントリーシグナルを生成する。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ── セッション時間帯フィルタ（JST基準） ─────────────────────
def _session_mask(idx: pd.DatetimeIndex, session: str) -> pd.Series:
    """JST 基準でセッション時間帯の boolean マスクを返す。

    日足データの場合は時間情報が無い（hour=0）ため、
    曜日ベースで代替フィルタを適用する。
    """
    jst_hour = idx.hour
    is_daily = (jst_hour == 0).all()

    if is_daily:
        dow = idx.dayofweek  # 0=月〜4=金
        if session == "tokyo":
            return pd.Series(dow.isin([0, 1, 2, 3, 4]), index=idx)
        if session == "london":
            return pd.Series(dow.isin([0, 1, 2, 3, 4]), index=idx)
        if session == "ny":
            return pd.Series(dow.isin([0, 1, 2, 3, 4]), index=idx)
        return pd.Series(True, index=idx)

    if session == "tokyo":
        return pd.Series((jst_hour >= 9) & (jst_hour < 11), index=idx)
    if session == "london":
        return pd.Series((jst_hour >= 17) & (jst_hour < 19), index=idx)
    if session == "ny":
        return pd.Series((jst_hour >= 22) | (jst_hour < 1), index=idx)
    return pd.Series(True, index=idx)


# ── テクニカル指標ヘルパー ──────────────────────────────────
def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def _rsi(s: pd.Series, period: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """簡易 ADX（Wilder 平滑）。"""
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    return dx.ewm(alpha=1 / period, adjust=False).mean()


def _double_bottom(close: pd.Series, lookback: int = 20, threshold: float = 0.005) -> pd.Series:
    """直近 lookback 本の中で 2番底からの反発を検知。

    rolling min からの反発率が threshold を超え、かつ
    直近値が lookback 期間の中央値を上回っていればシグナル発生。
    """
    rolling_min = close.rolling(lookback, min_periods=5).min()
    rolling_median = close.rolling(lookback, min_periods=5).median()
    rebound_pct = (close - rolling_min) / rolling_min.replace(0, np.nan)
    return (rebound_pct >= threshold) & (close > rolling_median)


def _double_top(close: pd.Series, lookback: int = 20, threshold: float = 0.005) -> pd.Series:
    """直近 lookback 本の中で 2番天井からの落ち込みを検知（ショート用）。

    天井からの落ち込み率が threshold 以上でシグナル。
    （close < rolling_median は外し、下降初期も拾えるように緩和）
    """
    rolling_high = close.rolling(lookback, min_periods=5).max()
    drop_pct = (rolling_high - close) / rolling_high.replace(0, np.nan)
    return (drop_pct >= threshold).fillna(False)


def _fib_throwback(close: pd.Series, lookback: int = 20, max_level: float = 0.618) -> pd.Series:
    """直近安値からの戻りがフィボナッチ max_level 以内か（ショート押し目）。"""
    rolling_high = close.rolling(lookback).max()
    rolling_low = close.rolling(lookback).min()
    fib_range = rolling_high - rolling_low
    throwback_pct = (close - rolling_low) / fib_range.replace(0, np.nan)
    return throwback_pct.fillna(0) <= max_level


def _simple_swing(close: pd.Series, lookback: int = 10, min_range_pct: float = 0.002) -> pd.Series:
    """1Hワントップワンボトム: 明確な高値・安値のスイング構造。"""
    r_high = close.rolling(lookback).max()
    r_low = close.rolling(lookback).min()
    r_range = r_high - r_low
    r_median = close.rolling(lookback).median()
    return (r_range / r_median.replace(0, np.nan) >= min_range_pct).fillna(False)


def _fib_pullback(close: pd.Series, lookback: int = 20, max_level: float = 0.50) -> pd.Series:
    """直近高値からの押し目がフィボナッチ 50% 以内かを判定。"""
    rolling_high = close.rolling(lookback).max()
    rolling_low = close.rolling(lookback).min()
    fib_range = rolling_high - rolling_low
    pullback_depth = (rolling_high - close) / fib_range.replace(0, np.nan)
    return pullback_depth.fillna(1.0) <= max_level


def _volume_spike(volume: pd.Series, window: int = 5, multiplier: float = 2.0) -> pd.Series:
    """前 window 本平均の multiplier 倍以上の出来高スパイク検知。"""
    avg = volume.rolling(window).mean()
    return volume > (avg * multiplier)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """ATR(14) Wilder 平滑。ストップ幅計算用。"""
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


# ── メイン関数 ──────────────────────────────────────────────
def mtf_minato_short_v2(
    df_multi: pd.DataFrame,
    session: str = "all",
    use_daily: bool = False,
    fibo_level: float = 0.618,
    stop_atr_multiplier: float = 1.3,
) -> tuple[pd.Series, pd.Series]:
    """ミナト流 MTF 短期ルール v2 シグナル生成（ロング＋ショート対称）。

    ※この関数は「エントリーシグナルのみ」を返す。ストップ計算は行わない。
      決済ロジック／再エントリー条件／ATR ストップ終値判定は
      `Simple_Backtest.py` 側で実装している。

      - ストップ: Simple_Backtest 内で 5分足 ATR(14)×1.3 + 50pipsキャップ。**バー内高値/安値**で判定（5分足のHigh/Lowでストップに触れたら即損切）。
      - 15分実体下抜け: 前回15分足の**実体安値/高値**（body=min/max(Open,Close)）を終値が下抜け/上抜けしたら確定。
      - 再エントリー: 損切り後 15 分待機 ＋ 15 分ネックライン越えで再エントリー（同一方向最大 1 回）
      - 決済順序（ショート・ロング対称）:
        1. 4H ネックライン到達で半値利確
        2. 半値利確後、1H ローソク 3 本経過＋前回 5 分実体ブレイク or 15 分実体ブレイク
        3. 4H ネックライン越え後、4H ローソク 3 本経過＋前回 15 分実体ブレイク or 1H 実体ブレイク

    Args:
        df_multi: fetch_multi_tf() が返すマージ済み DataFrame。
        session: "tokyo" / "london" / "ny" / "all"
        use_daily: True なら日足トレンド（EMA20/50）でフィルタ。
        fibo_level: 押し目/戻り基準（0.618=Fibo61.8%）。
        stop_atr_multiplier: Simple_Backtest に渡すストップ係数（ATR × multiplier、デフォルト1.3）。

    Returns:
        (entries_long, entries_short) のタプル
    """
    def _col(prefix: str, name: str) -> pd.Series:
        key = f"{prefix}_{name}"
        if key in df_multi.columns:
            return df_multi[key]
        if name in df_multi.columns:
            return df_multi[name]
        return pd.Series(np.nan, index=df_multi.index)

    close_4h = _col("4H", "Close")
    high_4h = _col("4H", "High")
    low_4h = _col("4H", "Low")
    close_d = _col("D", "Close")
    high_d = _col("D", "High")
    low_d = _col("D", "Low")
    close_1h = _col("1H", "Close")
    close_15m = _col("15M", "Close")
    close_5m = _col("5M", "Close")
    vol_15m = _col("15M", "Volume")
    vol_5m = _col("5M", "Volume")

    ema20 = _ema(close_d, 20)
    ema50 = _ema(close_d, 50)
    golden_cross = ema20 > ema50
    death_cross = ema20 < ema50
    adx_val = _adx(high_d, low_d, close_d, 14)
    cond_trend_long = golden_cross | (adx_val > 25) if use_daily else pd.Series(True, index=df_multi.index)
    cond_trend_short = death_cross | (adx_val > 25) if use_daily else pd.Series(True, index=df_multi.index)

    rsi_val = _rsi(close_d, 14)
    cond_rsi_long = (rsi_val >= 40) & (rsi_val <= 60)
    cond_rsi_short = (rsi_val >= 25) & (rsi_val <= 75)  # ショートは緩和（下落相場でRSI低めになりやすい）

    sess_mask = _session_mask(df_multi.index, session)
    vol_spike_15m = _volume_spike(vol_15m, window=5, multiplier=2.0)

    # ── ロング条件 ─────────────────────────────────────────
    cond_4h_dbl_bottom = _double_bottom(close_4h, lookback=20, threshold=0.005)
    cond_fib_long = _fib_pullback(close_4h, lookback=20, max_level=fibo_level)
    cond_1h_pullback = _fib_pullback(close_1h, lookback=10, max_level=fibo_level)
    cond_1h_dbl_bottom = _double_bottom(close_1h, lookback=10, threshold=0.003)
    cond_1h_long = cond_1h_pullback & cond_1h_dbl_bottom
    cond_1h_swing_long = _simple_swing(close_1h, 10, 0.002)
    cond_15m_neck_up = _double_bottom(close_15m, lookback=10, threshold=0.002)
    cond_5m_neck_up = _double_bottom(close_5m, lookback=10, threshold=0.001)
    cond_early_long = vol_spike_15m & cond_5m_neck_up

    main_long = (
        cond_4h_dbl_bottom
        & cond_trend_long
        & cond_fib_long
        & (cond_1h_long | cond_1h_swing_long)
        & cond_15m_neck_up
        & cond_rsi_long
        & sess_mask
    )
    early_long = (
        cond_4h_dbl_bottom
        & cond_trend_long
        & cond_fib_long
        & (cond_1h_long | cond_1h_swing_long)
        & cond_early_long
        & sess_mask
    )
    entries_long = main_long | early_long

    # ── ショート条件（4H2番天井 → 1H戻り → 15Mネックライン下抜け）────────────
    cond_4h_dbl_top = _double_top(close_4h, lookback=20, threshold=0.005)
    cond_fib_short = _fib_throwback(close_4h, lookback=20, max_level=fibo_level)
    cond_1h_throwback = _fib_throwback(close_1h, lookback=10, max_level=fibo_level)
    cond_1h_dbl_top = _double_top(close_1h, lookback=10, threshold=0.003)
    cond_1h_short = cond_1h_throwback & cond_1h_dbl_top
    cond_1h_swing_short = _simple_swing(close_1h, 10, 0.002)
    cond_15m_neck_down = _double_top(close_15m, lookback=10, threshold=0.002)
    cond_5m_neck_down = _double_top(close_5m, lookback=10, threshold=0.001)
    cond_early_short = vol_spike_15m & cond_5m_neck_down

    main_short = (
        cond_4h_dbl_top
        & cond_trend_short
        & cond_fib_short
        & (cond_1h_short | cond_1h_swing_short)
        & cond_15m_neck_down
        & cond_rsi_short
        & sess_mask
    )
    early_short = (
        cond_4h_dbl_top
        & cond_trend_short
        & cond_fib_short
        & (cond_1h_short | cond_1h_swing_short)
        & cond_early_short
        & sess_mask
    )
    entries_short = main_short | early_short

    return entries_long, entries_short
