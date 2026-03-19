"""entry_logic.py — ミナト流 MTFエントリー条件モジュール。

Phase B → 指示書#007 リファクタ済み。

エントリー条件（2段階フィルター + 指値注文）:
  Step1: 4H Fib61.8% 以内の押し目（Fib50%+ネックライン一致で高優位性★★★）
  Step2: 1H 2番底（LONG）/ 2番天井（SHORT）確認
  Step3 廃止: 15M確定足判定 → 指値注文（calc_limit_price）に置き換え

エントリー執行: 15Mネック + 10pips に指値設置 → 約定でエントリー

設計思想:
  「4H上昇ダウが継続している限り、押し目条件が揃うたびにエントリーを繰り返す」
  Step1+2 成立時に指値価格を算出し、backtest.py 側で約定チェックを行う。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# リポジトリルートをパスに追加（直接実行時 & モジュール import 時の両対応）
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows


# ── 定数 ──────────────────────────────────────────────────────
MAX_REENTRY = 1          # 同一押し目機会での最大再試行回数
LIMIT_OFFSET_PIPS = 10.0 # 指値オフセット（固定）
PIP_SIZE = 0.01          # USDJPYの1pip = 0.01円


# ── Step1: 4H Fib条件 ─────────────────────────────────────────

def check_fib_condition(
    price: float,
    swing_high: float,
    swing_low: float,
    neck_4h: float,
    direction: str,
) -> int:
    """Fibonacci押し目条件を確認する。

    LONGの場合: 高値から安値への押し目深さがFib61.8%以内か
    SHORTの場合: 安値から高値への戻り深さがFib61.8%以内か

    Args:
        price:      現在の価格
        swing_high: 直近Swing High価格（4H）
        swing_low:  直近Swing Low価格（4H）
        neck_4h:    4Hネックライン価格
        direction:  'LONG' / 'SHORT'

    Returns:
        2 = 高優位性（Fib50%付近 かつ 4Hネックライン付近）★★★
        1 = 基本条件（Fib61.8%以内）★★
        0 = 条件外
    """
    fib_range = swing_high - swing_low
    if fib_range <= 0:
        return 0

    if direction == "LONG":
        # 押し目深さ: 高値からの戻り率
        retracement = (swing_high - price) / fib_range
        near_neck = abs(price - neck_4h) < fib_range * 0.03
    elif direction == "SHORT":
        # 戻り深さ: 安値からの反発率
        retracement = (price - swing_low) / fib_range
        near_neck = abs(price - neck_4h) < fib_range * 0.03
    else:
        return 0

    at_fib50 = 0.45 <= retracement <= 0.55    # Fib50%±5%
    at_fib618 = retracement <= 0.65            # Fib61.8%以内

    if at_fib50 and near_neck:
        return 2   # ★★★ 最高優位性（Fib50% + ネックライン一致）
    elif at_fib618:
        return 1   # ★★  基本条件（Fib61.8%以内）
    else:
        return 0   # 条件外


# ── Step2: 1H 2番底 / 2番天井 ────────────────────────────────

def check_double_bottom_1h(
    low_1h: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> bool:
    """LONG用: 1H足での2番底確認。

    直近SL① → 反発上昇 → SL② >= SL① なら成立（安値切り上がり）

    Args:
        low_1h:      1H足のLow Series
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数（1H推奨: n=3）
        lookback:    何本前まで遡るか

    Returns:
        True = 2番底成立、False = 未成立
    """
    start = max(0, current_idx - lookback)
    window = low_1h.iloc[start:current_idx + 1]

    if len(window) < n * 2 + 2:
        return False

    swings = detect_swing_lows(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) < 2:
        return False

    sl1 = float(swing_prices.iloc[-2])  # 前回SL
    sl2 = float(swing_prices.iloc[-1])  # 直近SL

    return sl2 >= sl1  # 安値切り上がり = 2番底成立


def check_double_top_1h(
    high_1h: pd.Series,
    current_idx: int,
    n: int = 3,
    lookback: int = 50,
) -> bool:
    """SHORT用: 1H足での2番天井確認。

    直近SH① → 反落 → SH② <= SH① なら成立（高値切り下がり）

    Args:
        high_1h:     1H足のHigh Series
        current_idx: 現在の足の整数位置
        n:           Swing検出の前後確認本数（1H推奨: n=3）
        lookback:    何本前まで遡るか

    Returns:
        True = 2番天井成立、False = 未成立
    """
    start = max(0, current_idx - lookback)
    window = high_1h.iloc[start:current_idx + 1]

    if len(window) < n * 2 + 2:
        return False

    swings = detect_swing_highs(window, n=n)
    swing_prices = window[swings]

    if len(swing_prices) < 2:
        return False

    sh1 = float(swing_prices.iloc[-2])  # 前回SH
    sh2 = float(swing_prices.iloc[-1])  # 直近SH

    return sh2 <= sh1  # 高値切り下がり = 2番天井成立


# ── Step3廃止: 指値価格算出 & 到達チェック ───────────────────────

def calc_limit_price(
    neck_15m: float,
    direction: str,
    offset_pips: float = LIMIT_OFFSET_PIPS,
) -> float:
    """15Mネックラインから指値価格を算出する。

    LONG : neck_15m + offset_pips * PIP_SIZE
    SHORT: neck_15m - offset_pips * PIP_SIZE

    Args:
        neck_15m    : 15Mネックライン価格（LONGはSwing High、SHORTはSwing Low）
        direction   : 'LONG' or 'SHORT'
        offset_pips : オフセット（デフォルト10pips）
    """
    offset = offset_pips * PIP_SIZE
    if direction == "LONG":
        return neck_15m + offset
    elif direction == "SHORT":
        return neck_15m - offset
    return neck_15m


def check_limit_triggered(
    bar_extreme: float,
    limit_price: float,
    direction: str,
) -> bool:
    """現在バーの高値/安値が指値価格に到達したか判定する。

    LONG : bar_extreme（High）>= limit_price → True
    SHORT: bar_extreme（Low） <= limit_price → True

    Args:
        bar_extreme : LONG=5M足High、SHORT=5M足Low
        limit_price : calc_limit_price() で算出した指値価格
        direction   : 'LONG' or 'SHORT'
    """
    if direction == "LONG":
        return bar_extreme >= limit_price
    elif direction == "SHORT":
        return bar_extreme <= limit_price
    return False


# ── 統合エントリー判定（Step1 + Step2 のみ） ─────────────────────

def evaluate_entry(
    price: float,
    direction: str,
    swing_high_4h: float,
    swing_low_4h: float,
    neck_4h: float,
    low_1h: pd.Series,
    high_1h: pd.Series,
    current_idx_1h: int,
    neck_15m: float,
) -> dict:
    """Step1・Step2を一括評価しセットアップ成立を返す。

    Step3（15M確定足判定）は廃止。
    代わりにbacktest.py 側で calc_limit_price / check_limit_triggered を使い
    指値注文で約定チェックを行う。

    Args:
        price:          現在の価格（5M_Close）
        direction:      'LONG' / 'SHORT'（4H方向）
        swing_high_4h:  4H直近Swing High
        swing_low_4h:   4H直近Swing Low
        neck_4h:        4Hネックライン（LONGはSH、SHORTはSL）
        low_1h:         1H足のLow Series
        high_1h:        1H足のHigh Series
        current_idx_1h: 現在の1H足の整数位置
        neck_15m:       15Mネックライン価格（指値価格算出のため返却）

    Returns:
        {
          'enter'    : bool   # セットアップ条件成立（Step1+2）
          'fib_score': int    # Fib優位性スコア（0/1/2）
          'reason'   : str    # スキップ理由（デバッグ用）
          'neck_15m' : float  # 指値価格算出用（enter=True時に有効）
        }
    """
    if direction not in ("LONG", "SHORT"):
        return {"enter": False, "fib_score": 0, "reason": f"NONE方向スキップ({direction})", "neck_15m": neck_15m}

    # ── Step1: 4H Fib条件 ──
    fib_score = check_fib_condition(
        price, swing_high_4h, swing_low_4h, neck_4h, direction
    )
    if fib_score == 0:
        return {"enter": False, "fib_score": 0, "reason": "Fib条件外", "neck_15m": neck_15m}

    # ── Step2: 1H 2番底 / 2番天井 ──
    if direction == "LONG":
        db_ok = check_double_bottom_1h(low_1h, current_idx_1h)
    else:
        db_ok = check_double_top_1h(high_1h, current_idx_1h)

    if not db_ok:
        return {"enter": False, "fib_score": fib_score, "reason": "1H2番底/天井未形成", "neck_15m": neck_15m}

    # Step1+2 成立 → 指値注文の準備が整った
    return {"enter": True, "fib_score": fib_score, "reason": "OK", "neck_15m": neck_15m}


# ── スクリプト直接実行時のセルフテスト ─────────────────────────

if __name__ == "__main__":
    print("=== entry_logic.py セルフテスト ===")

    # check_fib_condition テスト
    sh = 150.5
    sl = 148.5
    neck = 149.5

    for price, label in [(149.5, "Fib50%+ネック"), (149.2, "Fib61.8%"), (148.8, "Fib外")]:
        score = check_fib_condition(price, sh, sl, neck, "LONG")
        print(f"  LONG Fib score [{label}] price={price}: {score}")

    for price, label in [(149.5, "Fib50%+ネック"), (149.8, "Fib61.8%"), (150.2, "Fib外")]:
        score = check_fib_condition(price, sh, sl, neck, "SHORT")
        print(f"  SHORT Fib score [{label}] price={price}: {score}")

    # check_double_bottom_1h テスト
    np.random.seed(42)
    n_bars = 60
    idx_1h = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    lows = np.array([150.0 - abs(np.sin(i / 5)) * 0.5 for i in range(n_bars)])
    lows[20] = 148.5  # SL1
    lows[40] = 148.7  # SL2 > SL1 → 2番底成立
    low_1h = pd.Series(lows, index=idx_1h)

    db = check_double_bottom_1h(low_1h, len(low_1h) - 1)
    print(f"\n  check_double_bottom_1h: {db}")

    # calc_limit_price テスト
    neck_15m_test = 149.50
    lp_long  = calc_limit_price(neck_15m_test, "LONG")
    lp_short = calc_limit_price(neck_15m_test, "SHORT")
    print(f"\n  calc_limit_price LONG  (neck={neck_15m_test}): {lp_long:.3f}  (+10pips)")
    print(f"  calc_limit_price SHORT (neck={neck_15m_test}): {lp_short:.3f} (-10pips)")

    # check_limit_triggered テスト
    ok_l = check_limit_triggered(149.61, lp_long, "LONG")    # High が到達
    ng_l = check_limit_triggered(149.59, lp_long, "LONG")    # High が未達
    ok_s = check_limit_triggered(149.39, lp_short, "SHORT")  # Low が到達
    ng_s = check_limit_triggered(149.41, lp_short, "SHORT")  # Low が未達
    print(f"\n  check_limit_triggered LONG  (High=149.61 >= {lp_long:.3f}): {ok_l}  ← True期待")
    print(f"  check_limit_triggered LONG  (High=149.59 >= {lp_long:.3f}): {ng_l} ← False期待")
    print(f"  check_limit_triggered SHORT (Low=149.39  <= {lp_short:.3f}): {ok_s}  ← True期待")
    print(f"  check_limit_triggered SHORT (Low=149.41  <= {lp_short:.3f}): {ng_s} ← False期待")

    print(f"\n  定数: MAX_REENTRY={MAX_REENTRY}, LIMIT_OFFSET_PIPS={LIMIT_OFFSET_PIPS}, PIP_SIZE={PIP_SIZE}")
    print("\n[OK] entry_logic.py エラーなし")
