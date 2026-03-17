"""exit_logic.py — ミナト流3段階決済ロジック（Phase C実装）。

python src/exit_logic.py でセルフテスト実行可能。

決済フロー:
  【段階1: 4Hネック未到達】 5Mダウ崩れ → 全量決済
  【段階2: 4Hネック到達】   半値決済 + 残り50%ストップを建値に移動
  【段階3: 4Hネック越え後】 15Mダウ崩れ → 残り全量決済
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def check_5m_dow_break(
    high_5m: pd.Series,
    low_5m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    direction: str,
    n: int = 2,
) -> bool:
    """5M足のSwing押し戻しラインを5M実体が越えたか判定する。
    （確定足判定 = 実体がラインを越えた足）

    LONG の場合：
      Low系列でSwing Lowを検出
      body_high = min(open, close) がSwingLowを下回る → True（ダウ崩れ）

    SHORT の場合：
      High系列でSwing Highを検出
      body_low = max(open, close) がSwingHighを上回る → True（ダウ崩れ）

    戻り値: True = 崩れ確定（次の5M始値で決済執行）
    """
    from src.swing_detector import get_nearest_swing_low, get_nearest_swing_high

    current_idx = len(close_5m) - 1
    latest_close = float(close_5m.iloc[-1])
    latest_open = float(open_5m.iloc[-1])
    body_low = min(latest_open, latest_close)
    body_high = max(latest_open, latest_close)

    if direction == "LONG":
        swing_low = get_nearest_swing_low(
            low_5m, current_idx, n=n, lookback=20   # Low系列を使う
        )
        return body_high < swing_low  # 実体全体がSwingLow下 = 崩れ確定

    elif direction == "SHORT":
        swing_high = get_nearest_swing_high(
            high_5m, current_idx, n=n, lookback=20  # High系列を使う
        )
        return body_low > swing_high  # 実体全体がSwingHigh上 = 崩れ確定

    return False


def check_15m_dow_break(
    high_15m: pd.Series,
    low_15m: pd.Series,
    close_15m: pd.Series,
    open_15m: pd.Series,
    direction: str,
    n: int = 3,
) -> bool:
    """15M足のSwing押し戻しラインを15M実体が越えたか判定する。
    4Hネックライン越え後の最終決済用。

    check_5m_dow_break と同じ修正済みロジック。TFが15Mになる点のみ異なる。
    """
    from src.swing_detector import get_nearest_swing_low, get_nearest_swing_high

    current_idx = len(close_15m) - 1
    latest_close = float(close_15m.iloc[-1])
    latest_open = float(open_15m.iloc[-1])
    body_low = min(latest_open, latest_close)
    body_high = max(latest_open, latest_close)

    if direction == "LONG":
        swing_low = get_nearest_swing_low(
            low_15m, current_idx, n=n, lookback=30   # Low系列を使う
        )
        return body_high < swing_low

    elif direction == "SHORT":
        swing_high = get_nearest_swing_high(
            high_15m, current_idx, n=n, lookback=30  # High系列を使う
        )
        return body_low > swing_high

    return False


def manage_exit(
    entry_price: float,
    direction: str,
    high_5m: pd.Series,
    low_5m: pd.Series,
    close_5m: pd.Series,
    open_5m: pd.Series,
    high_15m: pd.Series,
    low_15m: pd.Series,
    close_15m: pd.Series,
    open_15m: pd.Series,
    neck_4h: float,
    position_size: float = 1.0,
) -> dict:
    """ミナト流3段階決済を管理する。

    決済フロー:
      【段階1: 4Hネック未到達】
        5Mダウ崩れ → 全量決済（利確・損切 共通）

      【段階2: 4Hネック到達】
        半値決済（50%クローズ）
        残り50%のストップを建値に移動（ノーリスク化）

      【段階3: 4Hネック越え後】
        15Mダウ崩れ → 残り全量決済

    戻り値:
      {
        'action'        : 'hold' / 'exit_half' / 'exit_all'
        'exit_price_bar': bool  # 次の足の始値で執行するか
        'reason'        : str   # 決済理由
        'remaining_size': float # 残りポジションサイズ
      }
    """
    current_price = float(close_5m.iloc[-1])

    # 4Hネック到達チェック
    if direction == "LONG":
        at_neck_4h = current_price >= neck_4h
    else:
        at_neck_4h = current_price <= neck_4h

    # 段階1: 4Hネック未到達 → 5Mダウ崩れで全決済
    if not at_neck_4h:
        if check_5m_dow_break(high_5m, low_5m, close_5m, open_5m, direction):
            return {
                "action": "exit_all",
                "exit_price_bar": True,
                "reason": "5Mダウ崩れ（4Hネック未到達）",
                "remaining_size": 0.0,
            }
        return {
            "action": "hold",
            "exit_price_bar": False,
            "reason": "保有継続",
            "remaining_size": position_size,
        }

    # 段階2: 4Hネック到達 → 半値決済
    if position_size == 1.0:
        return {
            "action": "exit_half",
            "exit_price_bar": True,
            "reason": "4Hネックライン到達・半値決済",
            "remaining_size": 0.5,
        }

    # 段階3: 4Hネック越え・残り50%保有中 → 15Mダウ崩れで全決済
    if position_size == 0.5:
        if check_15m_dow_break(high_15m, low_15m, close_15m, open_15m, direction):
            return {
                "action": "exit_all",
                "exit_price_bar": True,
                "reason": "15Mダウ崩れ（4Hネック越え後・最終決済）",
                "remaining_size": 0.0,
            }
        return {
            "action": "hold",
            "exit_price_bar": False,
            "reason": "4Hネック越え・15Mダウ崩れ待ち",
            "remaining_size": 0.5,
        }

    return {
        "action": "hold",
        "exit_price_bar": False,
        "reason": "保有継続",
        "remaining_size": position_size,
    }


# ── セルフテスト ────────────────────────────────────────────────

if __name__ == "__main__":
    import numpy as np

    print("=== exit_logic.py セルフテスト ===")

    np.random.seed(42)
    n = 50
    idx_5m = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC")
    idx_15m = pd.date_range("2024-01-01", periods=n // 3 + 1, freq="15min", tz="UTC")

    price_5m = 150.0 + np.cumsum(np.random.randn(n) * 0.02)
    high_5m = pd.Series(price_5m + 0.05, index=idx_5m)
    low_5m = pd.Series(price_5m - 0.05, index=idx_5m)
    close_5m = pd.Series(price_5m, index=idx_5m)
    open_5m = pd.Series(price_5m - 0.01, index=idx_5m)

    price_15m = 150.0 + np.cumsum(np.random.randn(len(idx_15m)) * 0.05)
    high_15m = pd.Series(price_15m + 0.10, index=idx_15m)
    low_15m = pd.Series(price_15m - 0.10, index=idx_15m)
    close_15m = pd.Series(price_15m, index=idx_15m)
    open_15m = pd.Series(price_15m - 0.01, index=idx_15m)

    # --- check_5m_dow_break テスト ---
    result_5m = check_5m_dow_break(high_5m, low_5m, close_5m, open_5m, "LONG")
    print(f"  check_5m_dow_break (LONG): {result_5m}")

    result_5m_s = check_5m_dow_break(high_5m, low_5m, close_5m, open_5m, "SHORT")
    print(f"  check_5m_dow_break (SHORT): {result_5m_s}")

    # --- check_15m_dow_break テスト ---
    result_15m = check_15m_dow_break(high_15m, low_15m, close_15m, open_15m, "LONG")
    print(f"  check_15m_dow_break (LONG): {result_15m}")

    # --- manage_exit テスト（段階1: ネック未到達） ---
    neck_4h = 152.0  # 現在価格(~150)より高い → 未到達
    r = manage_exit(
        entry_price=149.0,
        direction="LONG",
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        open_5m=open_5m,
        high_15m=high_15m,
        low_15m=low_15m,
        close_15m=close_15m,
        open_15m=open_15m,
        neck_4h=neck_4h,
        position_size=1.0,
    )
    print(f"\n  manage_exit 段階1(ネック未到達): action={r['action']}, reason={r['reason']}")

    # --- manage_exit テスト（段階2: ネック到達） ---
    neck_4h_low = 148.0  # 現在価格(~150)より低い → 到達済み
    r2 = manage_exit(
        entry_price=149.0,
        direction="LONG",
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        open_5m=open_5m,
        high_15m=high_15m,
        low_15m=low_15m,
        close_15m=close_15m,
        open_15m=open_15m,
        neck_4h=neck_4h_low,
        position_size=1.0,
    )
    print(f"  manage_exit 段階2(ネック到達): action={r2['action']}, reason={r2['reason']}")

    # --- manage_exit テスト（段階3: 残り50%保有中） ---
    r3 = manage_exit(
        entry_price=149.0,
        direction="LONG",
        high_5m=high_5m,
        low_5m=low_5m,
        close_5m=close_5m,
        open_5m=open_5m,
        high_15m=high_15m,
        low_15m=low_15m,
        close_15m=close_15m,
        open_15m=open_15m,
        neck_4h=neck_4h_low,
        position_size=0.5,
    )
    print(f"  manage_exit 段階3(残り50%): action={r3['action']}, reason={r3['reason']}")

    print("\n[OK] exit_logic.py エラーなし")
