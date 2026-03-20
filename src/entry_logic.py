"""entry_logic.py — ミナト流エントリー条件モジュール（#009 新ロジック）。

エントリー条件（3段階フィルター）:
  Step1: 4H Fib61.8% 以内の押し目（Fib50%+ネックライン一致で高優位性★★★）
  Step2: 15M ダブルボトム（LONG）/ ダブルトップ（SHORT）確認
  Step3: 5M DB ネックライン実体確定（下ヒゲ許容 WICKTOL_PIPS）

エントリー執行: 確定足の次の5M足の始値でエントリー

変更履歴:
  #009: 1H DB 廃止 → 15M DB + 5M DB に全面置き換え
        指値エントリー廃止 → 確定足方式に戻す
        WICKTOL_PIPS 追加（下ヒゲ許容幅）
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


# ── 定数 ──────────────────────────────────────────────────────
MAX_REENTRY = 1       # 同一押し目機会での最大再試行回数
WICKTOL_PIPS = 0.0   # 15M 前回安値からの 5M 2番底許容幅（下ヒゲ対策）
                     # 初期値: 0.0（許容なし）/ テスト順: 0.0 → 5.0 → 10.0
PIP_SIZE = 0.01      # USDJPY の 1pip = 0.01 円


# ── Step1: 4H Fib 条件 ────────────────────────────────────────

def check_fib_condition(
    price: float,
    swing_high: float,
    swing_low: float,
    neck_4h: float,
    direction: str,
) -> int:
    """Fibonacci 押し目条件を確認する。

    Returns:
        2 = 高優位性（Fib50%付近 かつ 4Hネックライン付近）★★★
        1 = 基本条件（Fib61.8%以内）★★
        0 = 条件外
    """
    fib_range = swing_high - swing_low
    if fib_range <= 0:
        return 0

    if direction == "LONG":
        retracement = (swing_high - price) / fib_range
        near_neck = abs(price - neck_4h) < fib_range * 0.03
    elif direction == "SHORT":
        retracement = (price - swing_low) / fib_range
        near_neck = abs(price - neck_4h) < fib_range * 0.03
    else:
        return 0

    at_fib50 = 0.45 <= retracement <= 0.55
    at_fib618 = retracement <= 0.65

    if at_fib50 and near_neck:
        return 2
    elif at_fib618:
        return 1
    else:
        return 0


# ── Step2: 15M ダブルボトム / ダブルトップ ─────────────────────

def check_15m_double_bottom(
    low_15m: pd.Series,
    high_15m: pd.Series,
    direction: str,
    n: int = 3,
    lookback: int = 30,
) -> dict:
    """15M ダブルボトム（LONG）/ ダブルトップ（SHORT）を検出する。

    LONG の成立条件:
      ① 直近 15M Swing Low を SL1 として取得
      ② SL1 より後に 15M Swing High（= DB ネックライン）が存在
      ③ さらに後に SL2 が形成され SL2 >= SL1（安値切り上がり）

    SHORT は High 系列で対称に判定。

    Returns:
      {
        'found'    : True / False,
        'sl1'      : float,  # 1番底価格（SHORT では 1番天井）
        'sl2'      : float,  # 2番底価格（SHORT では 2番天井）
        'neck_15m' : float,  # DB ネックライン価格
      }
    """
    window_low  = low_15m.iloc[-lookback:]
    window_high = high_15m.iloc[-lookback:]

    _none = {'found': False, 'sl1': None, 'sl2': None, 'neck_15m': None}

    if direction == 'LONG':
        sl_mask = detect_swing_lows(window_low, n=n)
        sh_mask = detect_swing_highs(window_high, n=n)
        sl_prices = window_low[sl_mask]
        sh_prices = window_high[sh_mask]

        if len(sl_prices) < 2 or len(sh_prices) < 1:
            return _none

        sl1 = sl_prices.iloc[-2]
        sl2 = sl_prices.iloc[-1]

        if sl2 < sl1:
            return _none

        sl1_idx = sl_prices.index[-2]
        sl2_idx = sl_prices.index[-1]
        neck_candidates = sh_prices[
            (sh_prices.index > sl1_idx) & (sh_prices.index < sl2_idx)
        ]
        if len(neck_candidates) == 0:
            return _none

        neck_15m = float(neck_candidates.max())
        return {'found': True, 'sl1': float(sl1), 'sl2': float(sl2), 'neck_15m': neck_15m}

    elif direction == 'SHORT':
        sh_mask = detect_swing_highs(window_high, n=n)
        sl_mask = detect_swing_lows(window_low, n=n)
        sh_prices = window_high[sh_mask]
        sl_prices = window_low[sl_mask]

        if len(sh_prices) < 2 or len(sl_prices) < 1:
            return _none

        sh1 = sh_prices.iloc[-2]
        sh2 = sh_prices.iloc[-1]

        if sh2 > sh1:
            return _none

        sh1_idx = sh_prices.index[-2]
        sh2_idx = sh_prices.index[-1]
        neck_candidates = sl_prices[
            (sl_prices.index > sh1_idx) & (sl_prices.index < sh2_idx)
        ]
        if len(neck_candidates) == 0:
            return _none

        neck_15m = float(neck_candidates.min())
        return {'found': True, 'sl1': float(sh1), 'sl2': float(sh2), 'neck_15m': neck_15m}

    return _none


# ── Step3: 5M ダブルボトム確定 ────────────────────────────────

def check_5m_double_bottom(
    low_5m: pd.Series,
    high_5m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    direction: str,
    neck_15m: float,
    swing_ref_15m: float,          # LONG: 15M SL2（2番底基準）/ SHORT: 15M SH2（2番天井基準）
    wicktol_pips: float = WICKTOL_PIPS,
    n: int = 2,
    lookback: int = 20,
) -> dict:
    """5M ダブルボトムの成立 + ネックライン実体上抜け確定を判定する。

    LONG の成立条件:
      ① 5M DB の 2番底安値が 15M 前回 Swing Low の -wicktol_pips 以内
         （5M_SL2 >= swing_ref_15m - wicktol_pips * PIP_SIZE）
      ② 5M DB ネック（neck_15m）を 5M 実体下端（min(open,close)）が上抜け確定

    SHORT は対称に判定。

    Returns:
      {
        'confirmed' : True / False,
        'reason'    : str,  # 否定時の理由（デバッグ用）
      }
    """
    window_low  = low_5m.iloc[-lookback:]
    window_high = high_5m.iloc[-lookback:]
    latest_open  = float(open_5m.iloc[-1])
    latest_close = float(close_5m.iloc[-1])
    tolerance = wicktol_pips * PIP_SIZE

    if direction == 'LONG':
        body_low = min(latest_open, latest_close)

        sl_mask = detect_swing_lows(window_low, n=n)
        sl_prices = window_low[sl_mask]

        if len(sl_prices) < 2:
            return {'confirmed': False, 'reason': '5M SL 不足'}

        sl2 = float(sl_prices.iloc[-1])

        # 条件①: 下ヒゲ許容チェック
        if sl2 < (swing_ref_15m - tolerance):
            return {'confirmed': False, 'reason': f'5M SL2({sl2:.3f}) が 15M SL -{wicktol_pips}pips({swing_ref_15m - tolerance:.3f}) を下回った'}

        # 条件②: 実体上抜け確定
        if body_low > neck_15m:
            return {'confirmed': True, 'reason': 'OK'}
        else:
            return {'confirmed': False, 'reason': f'実体下端({body_low:.3f}) がネック({neck_15m:.3f})未越え'}

    elif direction == 'SHORT':
        body_high = max(latest_open, latest_close)

        sh_mask = detect_swing_highs(window_high, n=n)
        sh_prices = window_high[sh_mask]

        if len(sh_prices) < 2:
            return {'confirmed': False, 'reason': '5M SH 不足'}

        sh2 = float(sh_prices.iloc[-1])

        if sh2 > (swing_ref_15m + tolerance):
            return {'confirmed': False, 'reason': f'5M SH2({sh2:.3f}) が 15M SH +{wicktol_pips}pips({swing_ref_15m + tolerance:.3f}) を上回った'}

        if body_high < neck_15m:
            return {'confirmed': True, 'reason': 'OK'}
        else:
            return {'confirmed': False, 'reason': f'実体上端({body_high:.3f}) がネック({neck_15m:.3f})未割れ'}

    return {'confirmed': False, 'reason': 'direction 不明'}


# ── 統合エントリー判定 ────────────────────────────────────────

def evaluate_entry(
    price: float,
    direction: str,
    swing_high_4h: float,
    swing_low_4h: float,
    neck_4h: float,
    low_15m: pd.Series,
    high_15m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    low_5m: pd.Series,
    high_5m: pd.Series,
) -> dict:
    """3段階エントリー条件を一括評価する（#009 新ロジック）。

    Step1: 4H Fib61.8% 以内
    Step2: 15M ダブルボトム / ダブルトップ検出
    Step3: 5M DB ネックライン実体確定

    Returns:
      {
        'enter'    : bool,
        'fib_score': int,
        'reason'   : str,
        'neck_15m' : float,  # Step2 で取得した DB ネック（Step3・plotter 用）
        'sl2_15m'  : float,  # Step2 の 2番底（swing_ref_15m として Step3 に渡す）
        'db_15m_found': bool,  # Step2 通過フラグ（デバッグカウント用）
        'wicktol_invalid': bool,  # Step3 で WICKTOL 超過で弾かれたフラグ
      }
    """
    base = {
        'enter': False, 'fib_score': 0, 'reason': '',
        'neck_15m': 0.0, 'sl2_15m': 0.0,
        'db_15m_found': False, 'wicktol_invalid': False,
    }

    if direction not in ("LONG", "SHORT"):
        base['reason'] = f"NONE方向スキップ({direction})"
        return base

    # ── Step1: 4H Fib 条件 ──
    fib_score = check_fib_condition(price, swing_high_4h, swing_low_4h, neck_4h, direction)
    base['fib_score'] = fib_score
    if fib_score == 0:
        base['reason'] = "Fib条件外"
        return base

    # ── Step2: 15M ダブルボトム / ダブルトップ ──
    db_15m = check_15m_double_bottom(low_15m, high_15m, direction)
    if not db_15m['found']:
        base['reason'] = "15M DB未形成"
        return base

    base['db_15m_found'] = True
    base['neck_15m'] = db_15m['neck_15m']
    base['sl2_15m'] = db_15m['sl2']

    # ── Step3: 5M DB ネックライン実体確定 ──
    db_5m = check_5m_double_bottom(
        low_5m=low_5m,
        high_5m=high_5m,
        close_5m=close_5m,
        open_5m=open_5m,
        direction=direction,
        neck_15m=db_15m['neck_15m'],
        swing_ref_15m=db_15m['sl2'],
    )

    if not db_5m['confirmed']:
        reason = db_5m['reason']
        if 'WICKTOL' in reason or '下回った' in reason or '上回った' in reason:
            base['wicktol_invalid'] = True
        base['reason'] = f"5M DB未確定: {reason}"
        return base

    base['enter'] = True
    base['reason'] = "OK"
    return base


# ── スクリプト直接実行時のセルフテスト ─────────────────────────

if __name__ == "__main__":
    print("=== entry_logic.py セルフテスト (#009) ===")

    # check_fib_condition
    sh, sl, neck = 150.5, 148.5, 149.5
    for price, label in [(149.5, "Fib50%+ネック"), (149.2, "Fib61.8%"), (148.8, "Fib外")]:
        score = check_fib_condition(price, sh, sl, neck, "LONG")
        print(f"  LONG Fib [{label}] price={price}: {score}")

    # check_15m_double_bottom — 合成データ
    idx_15m = pd.date_range("2024-01-01", periods=60, freq="15min", tz="UTC")
    lows_15m  = np.full(60, 150.0)
    highs_15m = np.full(60, 151.0)
    # SL1 at bar 15, SH (neck) at bar 30, SL2 at bar 45 (> SL1)
    lows_15m[14] = 149.0
    lows_15m[15] = 148.5   # SL1
    lows_15m[16] = 149.0
    highs_15m[29] = 151.5  # neck
    highs_15m[30] = 151.8  # SH
    highs_15m[31] = 151.5
    lows_15m[44] = 149.2
    lows_15m[45] = 148.7   # SL2 > SL1 → DB 成立
    lows_15m[46] = 149.2

    low_15m_s  = pd.Series(lows_15m, index=idx_15m)
    high_15m_s = pd.Series(highs_15m, index=idx_15m)

    db = check_15m_double_bottom(low_15m_s, high_15m_s, 'LONG', n=2, lookback=60)
    print(f"\n  check_15m_double_bottom: {db}")

    # check_5m_double_bottom
    idx_5m = pd.date_range("2024-01-01", periods=30, freq="5min", tz="UTC")
    lows_5m  = np.full(30, 149.5)
    highs_5m = np.full(30, 150.5)
    opens_5m  = np.full(30, 149.8)
    closes_5m = np.full(30, 150.2)
    lows_5m[10] = 148.8    # SL1
    lows_5m[20] = 148.9    # SL2 > SL1
    closes_5m[-1] = 151.9  # 実体がネック(151.8)を上回る
    opens_5m[-1]  = 151.85

    db5 = check_5m_double_bottom(
        pd.Series(lows_5m, index=idx_5m),
        pd.Series(highs_5m, index=idx_5m),
        pd.Series(closes_5m, index=idx_5m),
        pd.Series(opens_5m, index=idx_5m),
        direction='LONG',
        neck_15m=151.8,
        swing_ref_15m=148.7,
        wicktol_pips=0.0,
        n=2,
    )
    print(f"  check_5m_double_bottom: {db5}")

    print(f"\n  WICKTOL_PIPS: {WICKTOL_PIPS}")
    print(f"  PIP_SIZE:     {PIP_SIZE}")
    print(f"  MAX_REENTRY:  {MAX_REENTRY}")
    print("\n[OK] entry_logic.py (#009) エラーなし")
