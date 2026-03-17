"""entry_logic.py — ミナト流 3段階MTFエントリー条件モジュール。

Phase B 実装。

エントリー条件（3段階フィルター）:
  Step1: 4H Fib61.8% 以内の押し目（Fib50%+ネックライン一致で高優位性★★★）
  Step2: 1H 2番底（LONG）/ 2番天井（SHORT）確認
  Step3: 15M ネックラインを 5M 実体で越えた確定足判定

エントリー執行: 確定足の次の5M足の始値でエントリー

設計思想:
  「4H上昇ダウが継続している限り、押し目条件が揃うたびにエントリーを繰り返す」
  エリオット波数カウントは一切不要。
  get_direction_4h() == 'LONG' が継続する限りループし続けるのが正しい動作。
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
MAX_REENTRY = 1  # 同一押し目機会での最大再試行回数（将来の変更用）


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


# ── Step3: 15M ネックライン越え（5M 実体確定足）────────────────

def check_15m_neckline_break(
    close_5m: pd.Series,
    open_5m: pd.Series,
    neck_15m: float,
    direction: str,
) -> bool:
    """15Mネックラインを5M実体が越えたかどうかを確認する（確定足判定）。

    確定足の定義:
      LONG : 5M実体のlow（min(open,close)）がneck_15mを上回っている
             → 実体全体がネック上 = 確定越え
      SHORT: 5M実体のhigh（max(open,close)）がneck_15mを下回っている
             → 実体全体がネック下 = 確定割れ

    Args:
        close_5m:  5M足のClose Series（直近数本）
        open_5m:   5M足のOpen Series（直近数本）
        neck_15m:  15Mネックライン価格
        direction: 'LONG' / 'SHORT'

    Returns:
        True = 確定越え、False = 未越え
    """
    if len(close_5m) == 0 or len(open_5m) == 0:
        return False

    latest_close = float(close_5m.iloc[-1])
    latest_open = float(open_5m.iloc[-1])

    body_low = min(latest_open, latest_close)
    body_high = max(latest_open, latest_close)

    if direction == "LONG":
        return body_low > neck_15m   # 実体全体がネック上
    elif direction == "SHORT":
        return body_high < neck_15m  # 実体全体がネック下
    return False


# ── 統合エントリー判定 ────────────────────────────────────────

def evaluate_entry(
    price: float,
    direction: str,
    swing_high_4h: float,
    swing_low_4h: float,
    neck_4h: float,
    low_1h: pd.Series,
    high_1h: pd.Series,
    current_idx_1h: int,
    close_5m: pd.Series,
    open_5m: pd.Series,
    neck_15m: float,
) -> dict:
    """3段階エントリー条件を一括評価する。

    Args:
        price:          現在の価格（5M_Close）
        direction:      'LONG' / 'SHORT'（4H方向）
        swing_high_4h:  4H直近Swing High
        swing_low_4h:   4H直近Swing Low
        neck_4h:        4Hネックライン（LONGはSH、SHORTはSL）
        low_1h:         1H足のLow Series
        high_1h:        1H足のHigh Series
        current_idx_1h: 現在の1H足の整数位置
        close_5m:       5M足のClose Series（直近数本）
        open_5m:        5M足のOpen Series（直近数本）
        neck_15m:       15Mネックライン価格

    Returns:
        {
          'enter'    : bool   # エントリー可否
          'fib_score': int    # Fib優位性スコア（0/1/2）
          'reason'   : str    # スキップ理由（デバッグ用）
        }
    """
    if direction not in ("LONG", "SHORT"):
        return {"enter": False, "fib_score": 0, "reason": f"NONE方向スキップ({direction})"}

    # ── Step1: 4H Fib条件 ──
    fib_score = check_fib_condition(
        price, swing_high_4h, swing_low_4h, neck_4h, direction
    )
    if fib_score == 0:
        return {"enter": False, "fib_score": 0, "reason": "Fib条件外"}

    # ── Step2: 1H 2番底 / 2番天井 ──
    if direction == "LONG":
        db_ok = check_double_bottom_1h(low_1h, current_idx_1h)
    else:
        db_ok = check_double_top_1h(high_1h, current_idx_1h)

    if not db_ok:
        return {"enter": False, "fib_score": fib_score, "reason": "1H2番底/天井未形成"}

    # ── Step3: 15M ネック越え（5M実体確定） ──
    neck_ok = check_15m_neckline_break(close_5m, open_5m, neck_15m, direction)
    if not neck_ok:
        return {"enter": False, "fib_score": fib_score, "reason": "15Mネック未越え"}

    return {"enter": True, "fib_score": fib_score, "reason": "OK"}


# ── スクリプト直接実行時のセルフテスト ─────────────────────────

if __name__ == "__main__":
    print("=== entry_logic.py セルフテスト ===")

    # check_fib_condition テスト
    # LONG: 高値150.5, 安値148.5 → レンジ2.0
    #   現在価格: Fib50%=149.5, Fib61.8%=149.26
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
    # 2番底パターン: 下落 → 反発 → 再下落（前回安値より高め）→ 反発
    lows = np.array([150.0 - abs(np.sin(i / 5)) * 0.5 for i in range(n_bars)])
    lows[20] = 148.5  # SL1
    lows[40] = 148.7  # SL2 > SL1 → 2番底成立
    low_1h = pd.Series(lows, index=idx_1h)

    db = check_double_bottom_1h(low_1h, len(low_1h) - 1)
    print(f"\n  check_double_bottom_1h: {db}")

    # check_15m_neckline_break テスト
    close_5m = pd.Series([149.0, 149.2, 149.5])
    open_5m = pd.Series([148.9, 149.1, 149.3])
    neck_15m = 149.25

    ok_long = check_15m_neckline_break(close_5m, open_5m, neck_15m, "LONG")
    ok_short = check_15m_neckline_break(close_5m, open_5m, neck_15m, "SHORT")
    print(f"\n  15Mネック越え LONG(neck={neck_15m}, body_low={min(149.3, 149.5):.3f}): {ok_long}")
    print(f"  15Mネック越え SHORT(neck={neck_15m}, body_high={max(149.3, 149.5):.3f}): {ok_short}")

    print(f"\n  MAX_REENTRY 定数: {MAX_REENTRY}")
    print("\n✅ entry_logic.py エラーなし")
