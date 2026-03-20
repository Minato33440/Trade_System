"""exit_logic.py — ミナト流決済ロジックモジュール（#009 新ロジック）。

決済フェーズ構造:
  pre_1h  : エントリー直後〜1H ネック未到達
              SL = 15M ダウ崩れ（5M 実体確定の次足始値）
              5M Swing High 確定後は 5M ダウ崩れに自動移行
  pre_4h  : 1H ネック到達後〜4H ネック未確定
              半値決済済み・建値 SL 化
              SL = 5M ダウ崩れ
  post_4h : 4H ネック + 1H 実体確定後
              SL = 15M ダウ崩れ（最終段階）
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows


def check_4h_neck_1h_confirmed(
    close_1h: pd.Series,
    neck_4h: float,
    direction: str,
) -> bool:
    """1H 足の実体（Close）が 4H Swing High/Low を突破した足かを判定する。

    LONG : close_1h.iloc[-1] > neck_4h → True
    SHORT: close_1h.iloc[-1] < neck_4h → True

    実装上の注意:
      1H Close の確定 = 5M ループ内で minute==0 の足が開始した瞬間（前の 1H 確定）
      backtest では 5M ループ内で 1H Close を参照すれば自動的に正しいタイミングになる
    """
    if len(close_1h) == 0:
        return False
    latest = float(close_1h.iloc[-1])
    if direction == 'LONG':
        return latest > neck_4h
    elif direction == 'SHORT':
        return latest < neck_4h
    return False


def _get_recent_swing_low(low_series: pd.Series, n: int = 2, lookback: int = 20) -> float:
    """直近 Swing Low を取得する。見つからなければ window の min を返す。"""
    window = low_series.iloc[-lookback:]
    if len(window) < n * 2 + 1:
        return float(window.min()) if len(window) > 0 else float('nan')
    flags = detect_swing_lows(window, n=n)
    prices = window[flags]
    if len(prices) == 0:
        return float(window.min())
    return float(prices.iloc[-1])


def _get_recent_swing_high(high_series: pd.Series, n: int = 2, lookback: int = 20) -> float:
    """直近 Swing High を取得する。見つからなければ window の max を返す。"""
    window = high_series.iloc[-lookback:]
    if len(window) < n * 2 + 1:
        return float(window.max()) if len(window) > 0 else float('nan')
    flags = detect_swing_highs(window, n=n)
    prices = window[flags]
    if len(prices) == 0:
        return float(window.max())
    return float(prices.iloc[-1])


def manage_exit(
    position: dict,
    bar_5m_idx: int,
    df_5m: pd.DataFrame,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
) -> dict:
    """フェーズ別決済判定を行う。

    Args:
        position: 現在のポジション状態 dict（下記参照）
        bar_5m_idx: df_5m における現在バーの整数インデックス
        df_5m: 5M OHLC DataFrame（High/Low/Open/Close）
        df_15m: 15M OHLC DataFrame
        df_1h: 1H OHLC DataFrame

    position dict の必須キー:
        direction      : 'LONG' / 'SHORT'
        entry_price    : float
        neck_1h        : float  エントリー時の 1H Swing High（LONG）/ Low（SHORT）
        neck_4h        : float  4H ネックライン
        exit_phase     : 'pre_1h' / 'pre_4h' / 'post_4h'
        half_exited    : bool
        swing_confirmed_5m : bool  5M Swing High 確定フラグ（pre_1h 内で使用）

    Returns:
        {
          'action'     : 'hold' / 'exit_all' / 'exit_half',
          'reason'     : str,
          'new_phase'  : str,   action が hold / exit_half のときの遷移後フェーズ
          'new_swing_confirmed': bool,
        }
    """
    direction = position['direction']
    entry_price = position['entry_price']
    neck_1h = position['neck_1h']
    neck_4h = position['neck_4h']
    phase = position['exit_phase']
    half_exited = position['half_exited']
    swing_confirmed = position['swing_confirmed_5m']

    current_high = float(df_5m['High'].iloc[bar_5m_idx])
    current_low  = float(df_5m['Low'].iloc[bar_5m_idx])
    current_close = float(df_5m['Close'].iloc[bar_5m_idx])

    result = {
        'action': 'hold',
        'reason': '',
        'new_phase': phase,
        'new_swing_confirmed': swing_confirmed,
    }

    # ── 1H ネック到達 → 半値決済 + pre_4h 移行 ──────────────────
    if not half_exited:
        if direction == 'LONG' and current_high >= neck_1h:
            result['action'] = 'exit_half'
            result['reason'] = '1H_neck_reached'
            result['new_phase'] = 'pre_4h'
            return result
        elif direction == 'SHORT' and current_low <= neck_1h:
            result['action'] = 'exit_half'
            result['reason'] = '1H_neck_reached'
            result['new_phase'] = 'pre_4h'
            return result

    # ── 4H ネック + 1H 実体確定 → post_4h 移行 ──────────────────
    if phase == 'pre_4h':
        ts = df_5m.index[bar_5m_idx]
        if hasattr(ts, 'minute') and ts.minute == 0:
            # 毎時 00 分足 = 直前の 1H 確定
            idx_1h = int(df_1h.index.searchsorted(ts, side='right')) - 1
            if idx_1h >= 0:
                close_1h_w = df_1h['Close'].iloc[:idx_1h + 1]
                if check_4h_neck_1h_confirmed(close_1h_w, neck_4h, direction):
                    result['new_phase'] = 'post_4h'
                    # フェーズ移行のみ、この足では決済しない

    # ── フェーズ別 SL 判定 ────────────────────────────────────────
    if phase in ('pre_1h', 'post_4h'):
        # 15M ダウ崩れ判定
        idx_15m = int(df_15m.index.searchsorted(df_5m.index[bar_5m_idx], side='right')) - 1
        if idx_15m >= 2:
            if direction == 'LONG':
                sl_15m = _get_recent_swing_low(df_15m['Low'].iloc[:idx_15m], n=2, lookback=20)
                if current_close < sl_15m:
                    result['action'] = 'exit_all'
                    result['reason'] = f'15M_dow_break(SL={sl_15m:.3f})'
                    return result
            else:
                sh_15m = _get_recent_swing_high(df_15m['High'].iloc[:idx_15m], n=2, lookback=20)
                if current_close > sh_15m:
                    result['action'] = 'exit_all'
                    result['reason'] = f'15M_dow_break(SH={sh_15m:.3f})'
                    return result

        # pre_1h: 5M Swing 確定後は 5M ダウ崩れに切替
        if phase == 'pre_1h' and not swing_confirmed:
            # 5M Swing High 確定チェック（エントリー後の足のみ）
            entry_bar = position.get('entry_bar', 0)
            post_entry_high = df_5m['High'].iloc[entry_bar:bar_5m_idx + 1]
            if len(post_entry_high) >= 5:
                sh_flags = detect_swing_highs(post_entry_high, n=2)
                if sh_flags.any():
                    result['new_swing_confirmed'] = True
                    swing_confirmed = True

    if phase == 'pre_4h' or (phase == 'pre_1h' and swing_confirmed):
        # 5M ダウ崩れ判定
        lookback_5m = min(bar_5m_idx, 30)
        if direction == 'LONG':
            sl_5m = _get_recent_swing_low(
                df_5m['Low'].iloc[max(0, bar_5m_idx - lookback_5m):bar_5m_idx],
                n=2, lookback=20
            )
            # 建値より高い場合のみトレールとして機能（pre_4h では建値保護）
            if phase == 'pre_4h':
                sl_5m = max(sl_5m, entry_price)
            if current_low < sl_5m:
                result['action'] = 'exit_all'
                result['reason'] = f'5M_dow_break(SL={sl_5m:.3f})'
                return result
        else:
            sh_5m = _get_recent_swing_high(
                df_5m['High'].iloc[max(0, bar_5m_idx - lookback_5m):bar_5m_idx],
                n=2, lookback=20
            )
            if phase == 'pre_4h':
                sh_5m = min(sh_5m, entry_price)
            if current_high > sh_5m:
                result['action'] = 'exit_all'
                result['reason'] = f'5M_dow_break(SH={sh_5m:.3f})'
                return result

    return result
