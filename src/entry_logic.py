"""entry_logic.py — ミナト流エントリー条件モジュール（#011 統合レンジロジック）。

エントリー条件（3段階フィルター）:
  Step1: 4H Fib61.8% 以内の押し目 + 4H Swing 幅ガード（MIN_4H_SWING_PIPS）
  Step2: 15M 統合レンジロジック（DB / IHS / ASCENDING）
  Step3: 5M DB ネックライン実体確定（下ヒゲ許容 WICKTOL_PIPS）

エントリー執行: 確定足の次の5M足の始値でエントリー

変更履歴:
  #009: 1H DB 廃止 → 15M DB + 5M DB に全面置き換え
        指値エントリー廃止 → 確定足方式に戻す
        WICKTOL_PIPS 追加（下ヒゲ許容幅）
  #011: check_15m_double_bottom() → check_15m_range_low() に置き換え
        DB / IHS / ASCENDING を統合検出
        4H Swing 幅ガード（MIN_4H_SWING_PIPS = 20pips）追加
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
MAX_REENTRY       = 1       # 同一押し目機会での最大再試行回数
WICKTOL_PIPS      = 0.0    # 15M 前回安値からの 5M 2番底許容幅（下ヒゲ対策）
                            # 初期値: 0.0（許容なし）/ テスト順: 0.0 → 5.0 → 10.0
PIP_SIZE          = 0.01   # USDJPY の 1pip = 0.01 円
MIN_4H_SWING_PIPS = 20.0   # 4H Swing 最小幅（pips）
                            # これ未満は Fib 計算が無意味になる（Fib フィルタ機能不全）
DIRECTION_MODE    = 'LONG' # 'LONG' | 'SHORT' | 'BOTH'
                            # #012 では 'LONG' 固定


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


# ── Step2: 15M 統合レンジロジック ─────────────────────────────

def check_15m_range_low(
    low_15m: pd.Series,
    high_15m: pd.Series,
    direction: str,
    n: int = 3,
    lookback: int = 40,
) -> dict:
    """統合レンジロジック — ダブルボトム・逆三尊・安値切り上げを統合検出。

    LONG 成立条件:
      ① SL_last >= SL_min
           最終安値（右肩）が最深値（頭）を下回らない

      ② SL_last <= SL_min + 2.0 * (SL2 - SL_min)  ← 等距離ルール
           右肩の上限 = SL_min から SL2 の2倍の値幅まで
           DBパターン（SL2 ≈ SL_min）では MIN_RANGE=5pips の下限保護あり
           → sl3_max = max(sl_min + 2*(sl2-sl_min), sl_min + 5pips)

      ③ SL_min 以降に 15M Swing High が存在する
           ネックライン形成確認

    ネックライン定義:
      SL_min（最深値）のインデックス以降の 15M Swing High の最高値

    SHORT は High 系列で対称に実装。

    戻り値:
      {
        'found'    : True / False,
        'sl_min'   : float,   LONG=最深安値 / SHORT=最高値（呼び出し側で直接参照禁止）
        'sl_last'  : float,   LONG=最終安値(SL2) / SHORT=最終高値(SH2)
        'neck_15m' : float,   ネックライン価格（LONG/SHORT 共通キーで使用可）
        'pattern'  : str,     'DB'/'IHS'/'ASCENDING'（LONG）/ 'DT'/'HNS'/'DESCENDING'（SHORT）
        'reason'   : str,     found=False の時の理由
      }
    """
    MIN_RANGE = 5.0 * PIP_SIZE   # DBパターン保護: sl3_max / sh3_min に最低5pipsの余裕を確保

    _nan = float('nan')

    if direction == 'LONG':
        window_low  = low_15m.iloc[-lookback:]
        window_high = high_15m.iloc[-lookback:]

        sl_mask   = detect_swing_lows(window_low, n=n)
        sl_prices = window_low[sl_mask]

        if len(sl_prices) < 2:
            return {'found': False, 'sl_min': _nan, 'sl_last': _nan,
                    'neck_15m': _nan, 'pattern': '', 'reason': '15M SL 不足（2本未満）'}

        sl_min  = float(sl_prices.min())
        sl2     = float(sl_prices.iloc[-2])
        sl_last = float(sl_prices.iloc[-1])

        # 条件①: 最終安値 >= 最深値
        if sl_last < sl_min:
            return {'found': False, 'sl_min': sl_min, 'sl_last': sl_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SL_last < SL_min（最深値割れ）'}

        # 条件②: 右肩の上限チェック（DBパターン保護: sl2=sl_min でも5pips余裕を確保）
        sl3_max = max(sl_min + 2.0 * (sl2 - sl_min), sl_min + MIN_RANGE)
        if sl_last > sl3_max:
            return {'found': False, 'sl_min': sl_min, 'sl_last': sl_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SL3 上限超過（等距離ルール違反）'}

        # 条件③: ネックライン取得（SL_min 以降の 15M SH 最高値）
        sl_min_idx      = sl_prices.idxmin()
        neck_candidates = window_high[window_high.index > sl_min_idx]
        sh_mask         = detect_swing_highs(neck_candidates, n=n)
        sh_prices       = neck_candidates[sh_mask]

        if len(sh_prices) == 0:
            return {'found': False, 'sl_min': sl_min, 'sl_last': sl_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SL_min 以降に 15M SH なし'}

        neck_15m = float(sh_prices.max())

        # パターン分類（デバッグ・統計用）
        threshold = 0.03 * abs(sl2 - sl_min)
        if abs(sl_last - sl2) <= threshold:
            pattern = 'DB'
        elif sl_last <= sl2:
            pattern = 'IHS'
        else:
            pattern = 'ASCENDING'

        return {
            'found'    : True,
            'sl_min'   : sl_min,
            'sl_last'  : sl_last,
            'neck_15m' : neck_15m,
            'pattern'  : pattern,
            'reason'   : 'OK',
        }

    elif direction == 'SHORT':
        window_high = high_15m.iloc[-lookback:]
        window_low  = low_15m.iloc[-lookback:]

        sh_mask   = detect_swing_highs(window_high, n=n)
        sh_prices = window_high[sh_mask]

        if len(sh_prices) < 2:
            return {'found': False, 'sl_min': _nan, 'sl_last': _nan,
                    'neck_15m': _nan, 'pattern': '', 'reason': '15M SH 不足（2本未満）'}

        sh_max  = float(sh_prices.max())
        sh2     = float(sh_prices.iloc[-2])
        sh_last = float(sh_prices.iloc[-1])

        # 条件①: 最終高値 <= 最高値
        if sh_last > sh_max:
            return {'found': False, 'sl_min': sh_max, 'sl_last': sh_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SH_last > SH_max（最高値超え）'}

        # 条件②: 右肩の下限チェック（DTパターン保護: sh2=sh_max でも5pips余裕を確保）
        sh3_min = min(sh_max - 2.0 * (sh_max - sh2), sh_max - MIN_RANGE)
        if sh_last < sh3_min:
            return {'found': False, 'sl_min': sh_max, 'sl_last': sh_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SH3 下限超過（等距離ルール違反）'}

        # 条件③: ネックライン取得（SH_max 以降の 15M SL 最安値）
        sh_max_idx      = sh_prices.idxmax()
        neck_candidates = window_low[window_low.index > sh_max_idx]
        sl_mask         = detect_swing_lows(neck_candidates, n=n)
        sl_prices       = neck_candidates[sl_mask]

        if len(sl_prices) == 0:
            return {'found': False, 'sl_min': sh_max, 'sl_last': sh_last,
                    'neck_15m': _nan, 'pattern': '', 'reason': 'SH_max 以降に 15M SL なし'}

        neck_15m = float(sl_prices.min())

        # パターン分類
        threshold = 0.03 * abs(sh2 - sh_max)
        if abs(sh_last - sh2) <= threshold:
            pattern = 'DT'
        elif sh_last >= sh2:
            pattern = 'HNS'
        else:
            pattern = 'DESCENDING'

        return {
            'found'    : True,
            'sl_min'   : sh_max,
            'sl_last'  : sh_last,
            'neck_15m' : neck_15m,
            'pattern'  : pattern,
            'reason'   : 'OK',
        }

    return {'found': False, 'sl_min': _nan, 'sl_last': _nan,
            'neck_15m': _nan, 'pattern': '', 'reason': 'direction 不明'}


# ── Step3: 5M ダブルボトム確定 ────────────────────────────────

def check_5m_double_bottom(
    low_5m: pd.Series,
    high_5m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    direction: str,
    neck_15m: float,
    swing_ref_15m: float,          # LONG: 15M SL_last（最終安値基準）/ SHORT: 15M SH_last（最終高値基準）
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
    swing_high_4h: "float | None",
    swing_low_4h: "float | None",
    neck_4h: float,
    low_15m: pd.Series,
    high_15m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    low_5m: pd.Series,
    high_5m: pd.Series,
) -> dict:
    """3段階エントリー条件を一括評価する（#012 DIRECTION_MODE + None チェック版）。

    Step-1: 方向フィルター（DIRECTION_MODE）
    Step0a: 4H Swing None チェック（フォールバック修正後の安全網）
    Step0b: 4H Swing 幅ガード（MIN_4H_SWING_PIPS 未満はスキップ）
    Step1: 4H Fib61.8% 以内
    Step2: 15M 統合レンジロジック（DB / IHS / ASCENDING）
    Step3: 5M DB ネックライン実体確定

    Returns:
      {
        'enter'           : bool,
        'fib_score'       : int,
        'reason'          : str,
        'neck_15m'        : float,  Step2 で取得したネック（Step3・plotter 用）
        'sl2_15m'         : float,  Step2 の sl_last（swing_ref_15m として Step3 に渡す）
        'db_15m_found'    : bool,   Step2 通過フラグ（デバッグカウント用）
        'wicktol_invalid' : bool,   Step3 で WICKTOL 超過で弾かれたフラグ
        'pattern'         : str,    'DB'/'IHS'/'ASCENDING'/'DT'/'HNS'/'DESCENDING'
        'swing_guard_skip': bool,   4H Swing 幅不足スキップフラグ（デバッグ g 用）
        'sl3_over_skip'   : bool,   SL3/SH3 等距離ルール超過スキップフラグ（デバッグ h 用）
        'swing_none_skip' : bool,   4H Swing 未検出（None）スキップフラグ（デバッグ g 用）
      }
    """
    base = {
        'enter': False, 'fib_score': 0, 'reason': '',
        'neck_15m': 0.0, 'sl2_15m': 0.0,
        'db_15m_found': False, 'wicktol_invalid': False,
        'pattern': '', 'swing_guard_skip': False, 'sl3_over_skip': False,
        'swing_none_skip': False,
    }

    if direction not in ("LONG", "SHORT"):
        base['reason'] = f"NONE方向スキップ({direction})"
        return base

    # ── Step-1: 方向フィルター（DIRECTION_MODE） ──
    if DIRECTION_MODE != 'BOTH' and direction != DIRECTION_MODE:
        base['reason'] = f'DIRECTION_MODE={DIRECTION_MODE} によりスキップ'
        return base

    # ── Step0a: 4H Swing None チェック（安全網） ──
    if swing_high_4h is None or swing_low_4h is None:
        base['swing_none_skip'] = True
        base['reason'] = '4H Swing 未検出（None）'
        return base

    # ── Step0b: 4H Swing 幅ガード ──
    fib_range = swing_high_4h - swing_low_4h
    if fib_range < MIN_4H_SWING_PIPS * PIP_SIZE:
        base['swing_guard_skip'] = True
        base['reason'] = f'4H Swing 幅不足 ({fib_range / PIP_SIZE:.1f} pips < {MIN_4H_SWING_PIPS})'
        return base

    # ── Step1: 4H Fib 条件 ──
    fib_score = check_fib_condition(price, swing_high_4h, swing_low_4h, neck_4h, direction)
    base['fib_score'] = fib_score
    if fib_score == 0:
        base['reason'] = "Fib条件外"
        return base

    # ── Step2: 15M 統合レンジロジック ──
    range_result = check_15m_range_low(low_15m, high_15m, direction)
    if not range_result['found']:
        if '超過' in range_result.get('reason', ''):
            base['sl3_over_skip'] = True
        base['reason'] = f"15M レンジ未形成: {range_result['reason']}"
        return base

    base['db_15m_found'] = True
    base['neck_15m']     = range_result['neck_15m']
    base['sl2_15m']      = range_result['sl_last']
    base['pattern']      = range_result['pattern']

    # ── Step3: 5M DB ネックライン実体確定 ──
    db_5m = check_5m_double_bottom(
        low_5m=low_5m,
        high_5m=high_5m,
        close_5m=close_5m,
        open_5m=open_5m,
        direction=direction,
        neck_15m=range_result['neck_15m'],
        swing_ref_15m=range_result['sl_last'],
    )

    if not db_5m['confirmed']:
        reason = db_5m['reason']
        if '下回った' in reason or '上回った' in reason:
            base['wicktol_invalid'] = True
        base['reason'] = f"5M DB未確定: {reason}"
        return base

    base['enter'] = True
    base['reason'] = "OK"
    return base


# ── スクリプト直接実行時のセルフテスト ─────────────────────────

if __name__ == "__main__":
    print("=== entry_logic.py セルフテスト (#011) ===")

    # check_fib_condition
    sh, sl, neck = 150.5, 148.5, 149.5
    for price, label in [(149.5, "Fib50%+ネック"), (149.2, "Fib61.8%"), (148.8, "Fib外")]:
        score = check_fib_condition(price, sh, sl, neck, "LONG")
        print(f"  LONG Fib [{label}] price={price}: {score}")

    # check_15m_range_low — 4スイングASCENDINGテスト
    # 構造: SL at bars 8,20,38,48 / SH (neck) at bar 30
    idx_15m = pd.date_range("2024-01-01", periods=60, freq="15min", tz="UTC")
    lows_15m  = np.full(60, 150.0)
    highs_15m = np.full(60, 151.0)
    # SL 構造 (n=2 判定のため各スイングは5本幅で設定)
    lows_15m[6:11]   = [150.0, 149.5, 149.2, 149.5, 150.0]   # SL@8: 149.2
    lows_15m[18:23]  = [149.0, 149.3, 148.5, 149.3, 149.0]   # SL@20: 148.5 (sl_min)
    highs_15m[28:33] = [151.0, 151.3, 151.8, 151.3, 151.0]   # SH@30: 151.8 (neck)
    lows_15m[36:41]  = [149.2, 149.5, 148.9, 149.5, 149.2]   # SL@38: 148.9 (sl2)
    lows_15m[46:51]  = [149.4, 149.6, 149.1, 149.6, 149.4]   # SL@48: 149.1 (sl_last)

    low_15m_s  = pd.Series(lows_15m, index=idx_15m)
    high_15m_s = pd.Series(highs_15m, index=idx_15m)

    r = check_15m_range_low(low_15m_s, high_15m_s, 'LONG', n=2, lookback=60)
    print(f"\n  check_15m_range_low (LONG/ASCENDING): {r}")

    # DBパターンテスト — MIN_RANGE 保護確認
    lows_db  = np.full(30, 150.0)
    highs_db = np.full(30, 151.0)
    lows_db[6:11]   = [150.0, 149.7, 148.5, 149.7, 150.0]   # SL1@8: 148.5
    highs_db[13:18] = [151.0, 151.4, 151.8, 151.4, 151.0]   # SH@15: 151.8 (neck)
    lows_db[21:26]  = [149.7, 149.5, 148.5, 149.5, 149.7]   # SL2@23: 148.5 (DB = sl_min)
    idx_db = pd.date_range("2024-01-01", periods=30, freq="15min", tz="UTC")

    r_db = check_15m_range_low(
        pd.Series(lows_db, index=idx_db),
        pd.Series(highs_db, index=idx_db),
        'LONG', n=2, lookback=30,
    )
    print(f"  check_15m_range_low (LONG/DB):        {r_db}")

    # check_5m_double_bottom
    idx_5m = pd.date_range("2024-01-01", periods=30, freq="5min", tz="UTC")
    lows_5m  = np.full(30, 149.5)
    highs_5m = np.full(30, 150.5)
    opens_5m  = np.full(30, 149.8)
    closes_5m = np.full(30, 150.2)
    lows_5m[10] = 148.8
    lows_5m[20] = 148.9
    closes_5m[-1] = 151.9
    opens_5m[-1]  = 151.85

    db5 = check_5m_double_bottom(
        pd.Series(lows_5m, index=idx_5m),
        pd.Series(highs_5m, index=idx_5m),
        pd.Series(closes_5m, index=idx_5m),
        pd.Series(opens_5m, index=idx_5m),
        direction='LONG',
        neck_15m=151.8,
        swing_ref_15m=148.5,
        wicktol_pips=0.0,
        n=2,
    )
    print(f"  check_5m_double_bottom: {db5}")

    print(f"\n  WICKTOL_PIPS:      {WICKTOL_PIPS}")
    print(f"  PIP_SIZE:          {PIP_SIZE}")
    print(f"  MAX_REENTRY:       {MAX_REENTRY}")
    print(f"  MIN_4H_SWING_PIPS: {MIN_4H_SWING_PIPS}")
    print("\n[OK] entry_logic.py (#011) エラーなし")
