"""backtest.py - USDJPY MTF v2 バックテスト（指示書#007 指値エントリー + 二段階SL版）。

python src/backtest.py で実行。

変更履歴:
  Phase A: swing_detector.py 追加・Long/Short分岐骨格
  Phase B: entry_logic.py 追加・3段階エントリー条件実装
  Phase C: exit_logic.py 追加・3段階決済ロジック
  指示書#007: 指値エントリー + 二段階SL（swing_confirmed切替）

設計思想:
  Step1+2成立 → 15Mネック+10pips に指値設置 → 約定でエントリー
  swing_confirmed前: 15Mダウ崩れ早期損切
  swing_confirmed後: 5Mダウ崩れ（押し安値トレール）
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# リポジトリルートを path に追加
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# ── 既存シグナルモジュール（signals.py依存はコメントアウトで残存）──
# from src.signals import mtf_minato_short_v2  # Phase B完結で廃止

# ── 新モジュール ──────────────────────────────────────────────
from src.swing_detector import (
    _build_direction_5m,
    get_nearest_swing_high,
    get_nearest_swing_low,
)
from src.entry_logic import MAX_REENTRY, evaluate_entry, calc_limit_price, check_limit_triggered
from src.exit_logic import manage_exit, check_5m_swing_confirmed

# ── VectorBT があれば使う ────────────────────────────────────
try:
    import vectorbt as vbt
    HAS_VBT = True
except ImportError:
    HAS_VBT = False


# ── 定数 ──────────────────────────────────────────────────────
# TODO: ショートのロット縮小幅はデータ取り後のリスクリワード比較で決定
LONG_LOT_MULTIPLIER = 1.0   # ロングLot倍率
SHORT_LOT_MULTIPLIER = 1.0  # ショートLot倍率（初期はLONGと同じ）


# ── データ読み込みヘルパー ─────────────────────────────────────
def _load_and_preprocess(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
) -> pd.DataFrame:
    """Parquetデータを読み込み、UTC→JST変換・ffill前処理を行う。"""
    df_path_obj = Path(df_path)
    if not df_path_obj.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        df_path_obj = project_root / df_path

    if not df_path_obj.exists():
        raise FileNotFoundError(
            f"データファイルが見つかりません: {df_path_obj}\n"
            f"  → REX_Trade_Systemディレクトリで python src/data_fetch.py を先に実行してください"
        )

    df_multi = pd.read_parquet(df_path_obj)

    if not isinstance(df_multi.index, pd.DatetimeIndex):
        df_multi.index = pd.DatetimeIndex(df_multi.index)

    if hasattr(df_multi.index, "tz") and df_multi.index.tz is not None:
        df_multi.index = df_multi.index.tz_convert("Asia/Tokyo")
    else:
        df_multi.index = df_multi.index.tz_localize("UTC").tz_convert("Asia/Tokyo")

    tf_prefixes = ["5M", "15M", "1H", "4H", "D"]
    processed_dfs = []
    for prefix in tf_prefixes:
        cols = [c for c in df_multi.columns if c.startswith(f"{prefix}_")]
        if cols:
            processed_dfs.append(df_multi[cols].copy().ffill())

    return pd.concat(processed_dfs, axis=1)


# ── 全バースキャン：新エントリーロジック ─────────────────────────
def _scan_all_bars_for_entry(
    df_multi: pd.DataFrame,
    df_5m_raw: pd.DataFrame,
    direction_series: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """全5Mバーを走査して Step1+2 が成立するセットアップバーを探す。

    Step3（15M確定足）は廃止。指値注文は _simple_backtest_directional() で管理。

    Returns:
        (setups_long, setups_short, skip_reasons,
         neck_4h_long, neck_4h_short, neck_15m_long, neck_15m_short)
    """
    setups_long = pd.Series(False, index=df_multi.index)
    setups_short = pd.Series(False, index=df_multi.index)
    skip_reasons = pd.Series("", index=df_multi.index, dtype=object)
    neck_4h_long = pd.Series(float("nan"), index=df_multi.index, dtype=float)
    neck_4h_short = pd.Series(float("nan"), index=df_multi.index, dtype=float)
    neck_15m_long = pd.Series(float("nan"), index=df_multi.index, dtype=float)
    neck_15m_short = pd.Series(float("nan"), index=df_multi.index, dtype=float)

    # ── 全期間を一括resample（パフォーマンス最適化） ──
    print("  [INFO] 4H/1H/15M resample中（一括プリコンピュート）...")
    df_4h_full = df_5m_raw.resample("4h").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    df_1h_full = df_5m_raw.resample("1h").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    df_15m_full = df_5m_raw.resample("15min").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    print(f"    4H: {len(df_4h_full)}本, 1H: {len(df_1h_full)}本, 15M: {len(df_15m_full)}本")

    ts_4h = df_4h_full.index.values
    ts_1h = df_1h_full.index.values
    ts_15m = df_15m_full.index.values
    ts_5m = df_multi.index.values

    n_bars = len(df_multi)
    warmup = 100

    reentry_count_long = 0
    reentry_count_short = 0
    last_sl_long = float("nan")
    last_sh_short = float("nan")

    print(f"  [INFO] {n_bars}本のバーをスキャン中...")

    for i in range(warmup, n_bars - 1):
        ts = ts_5m[i]
        direction = direction_series.iloc[i]

        if direction == "NONE":
            skip_reasons.iloc[i] = "NONE方向"
            continue

        idx_4h = int(np.searchsorted(ts_4h, ts, side="right")) - 1
        idx_1h = int(np.searchsorted(ts_1h, ts, side="right")) - 1
        idx_15m = int(np.searchsorted(ts_15m, ts, side="right")) - 1

        if idx_4h < 10 or idx_1h < 6 or idx_15m < 6:
            skip_reasons.iloc[i] = "データ不足"
            continue

        sh_4h = get_nearest_swing_high(df_4h_full["High"], idx_4h, n=3, lookback=20)
        sl_4h = get_nearest_swing_low(df_4h_full["Low"], idx_4h, n=3, lookback=20)

        if direction == "LONG":
            if not np.isnan(last_sl_long) and abs(sl_4h - last_sl_long) > (sh_4h - sl_4h) * 0.05:
                reentry_count_long = 0
                last_sl_long = sl_4h
            elif np.isnan(last_sl_long):
                last_sl_long = sl_4h
            if reentry_count_long > MAX_REENTRY:
                skip_reasons.iloc[i] = "再エントリー上限"
                continue
        else:
            if not np.isnan(last_sh_short) and abs(sh_4h - last_sh_short) > (sh_4h - sl_4h) * 0.05:
                reentry_count_short = 0
                last_sh_short = sh_4h
            elif np.isnan(last_sh_short):
                last_sh_short = sh_4h
            if reentry_count_short > MAX_REENTRY:
                skip_reasons.iloc[i] = "再エントリー上限"
                continue

        neck_4h = sh_4h if direction == "LONG" else sl_4h

        low_1h = df_1h_full["Low"].iloc[: idx_1h + 1]
        high_1h = df_1h_full["High"].iloc[: idx_1h + 1]

        neck_15m_sh = get_nearest_swing_high(df_15m_full["High"], idx_15m, n=3, lookback=30)
        neck_15m_sl = get_nearest_swing_low(df_15m_full["Low"], idx_15m, n=3, lookback=30)
        neck_15m = neck_15m_sh if direction == "LONG" else neck_15m_sl

        current_price = float(df_multi["5M_Close"].iloc[i])

        # Step1+2 チェック（Step3廃止・指値注文に移行）
        result = evaluate_entry(
            price=current_price,
            direction=direction,
            swing_high_4h=sh_4h,
            swing_low_4h=sl_4h,
            neck_4h=neck_4h,
            low_1h=low_1h,
            high_1h=high_1h,
            current_idx_1h=len(low_1h) - 1,
            neck_15m=neck_15m,
        )

        skip_reasons.iloc[i] = result["reason"]

        if result["enter"]:
            if direction == "LONG":
                setups_long.iloc[i] = True
                neck_4h_long.iloc[i] = neck_4h
                neck_15m_long.iloc[i] = neck_15m
                reentry_count_long += 1
            else:
                setups_short.iloc[i] = True
                neck_4h_short.iloc[i] = neck_4h
                neck_15m_short.iloc[i] = neck_15m
                reentry_count_short += 1

    return setups_long, setups_short, skip_reasons, neck_4h_long, neck_4h_short, neck_15m_long, neck_15m_short


# ── ミナト流3段階決済バックテスト（Phase C） ────────────────────
def _simple_backtest_directional(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    open_5m: pd.Series,
    setups_long: pd.Series,
    setups_short: pd.Series,
    neck_4h_long: pd.Series,
    neck_4h_short: pd.Series,
    neck_15m_long: pd.Series,
    neck_15m_short: pd.Series,
    df_15m_full: pd.DataFrame,
    direction_series: pd.Series,
    commission: float = 0.0005,
    slippage: float = 0.0002,
) -> Dict[str, Any]:
    """Long/Short 両方向対応のバックテスト（指示書#007 指値エントリー + 二段階SL版）。

    エントリー: セットアップ成立 → 指値設置 → 約定でエントリー
    決済:
      フェーズ1（swing_confirmed=False）: 15Mダウ崩れ早期損切
      フェーズ2（swing_confirmed=True）:  5Mダウ崩れ（押し安値トレール）
      4Hネック到達: 半値決済 + 残り50%保有
      残り50%: 15Mダウ崩れで最終決済
    """
    setups_long_arr = setups_long.values.astype(bool)
    setups_short_arr = setups_short.values.astype(bool)
    neck_4h_long_arr = neck_4h_long.values.astype(float)
    neck_4h_short_arr = neck_4h_short.values.astype(float)
    neck_15m_long_arr = neck_15m_long.values.astype(float)
    neck_15m_short_arr = neck_15m_short.values.astype(float)

    ts_5m = close.index.values
    ts_15m = df_15m_full.index.values

    trades: List[Dict[str, Any]] = []
    exit_events: List[str] = []

    # ── ポジション状態 ──
    in_pos = False
    entry_idx = 0
    entry_price = 0.0
    direction = ""
    neck_4h = 0.0
    position_size = 0.0
    position_pnl = 0.0
    swing_confirmed = False
    current_trade_swing = False  # このトレードで一度でもswing確定したか

    # ── 指値状態 ──
    limit_pending = False
    limit_price = 0.0
    limit_direction = ""
    limit_neck_4h = 0.0
    limit_neck_15m = 0.0

    # ── デバッグカウンタ ──
    limit_cancel_count = 0
    phase1_stop_count = 0
    phase2_stop_count = 0
    swing_confirmed_count = 0
    reset_count = 0

    for i in range(len(close)):
        current_price = float(close.iloc[i])
        current_high = float(high.iloc[i])
        current_low = float(low.iloc[i])
        dir_4h = direction_series.iloc[i] if i < len(direction_series) else "NONE"

        if in_pos:
            # ── 4Hダウ崩れ → 強制決済・戦略リセット ──
            if dir_4h != direction and dir_4h != "NONE":
                ep = current_price * (1 - slippage) if direction == "LONG" else current_price * (1 + slippage)
                partial_pnl = (ep - entry_price) * position_size * 100 if direction == "LONG" \
                              else (entry_price - ep) * position_size * 100
                position_pnl += partial_pnl
                exit_events.append("4H_direction_reset")
                trades.append({
                    "entry_bar": entry_idx, "exit_bar": i, "direction": direction,
                    "entry_price": entry_price, "exit_price": ep,
                    "pnl_pips": position_pnl, "exit_reason": "4H_direction_reset",
                    "hold_bars": i - entry_idx, "swing_confirmed": current_trade_swing,
                })
                in_pos = False
                swing_confirmed = False
                current_trade_swing = False
                position_size = 0.0
                reset_count += 1
                # 指値状態もリセット（continue後の下部で新指値は設定しない）
                limit_pending = False
                continue

            # ── swing_confirmed 更新 ──
            if not swing_confirmed:
                win_high = high.iloc[entry_idx: i + 1]
                win_low = low.iloc[entry_idx: i + 1]
                if check_5m_swing_confirmed(win_high, win_low, direction, n=2):
                    swing_confirmed = True
                    if not current_trade_swing:
                        current_trade_swing = True
                        swing_confirmed_count += 1

            # ── 決済ウィンドウ構築 ──
            win_start = max(0, i - 50)
            high_5m_w = high.iloc[win_start: i + 1]
            low_5m_w = low.iloc[win_start: i + 1]
            close_5m_w = close.iloc[win_start: i + 1]
            open_5m_w = open_5m.iloc[win_start: i + 1]

            idx_15m = int(np.searchsorted(ts_15m, ts_5m[i], side="right")) - 1
            if idx_15m < 0:
                idx_15m = 0
            win_start_15m = max(0, idx_15m - 50)
            high_15m_w = df_15m_full["High"].iloc[win_start_15m: idx_15m + 1]
            low_15m_w = df_15m_full["Low"].iloc[win_start_15m: idx_15m + 1]
            close_15m_w = df_15m_full["Close"].iloc[win_start_15m: idx_15m + 1]
            open_15m_w = df_15m_full["Open"].iloc[win_start_15m: idx_15m + 1]

            result = manage_exit(
                entry_price=entry_price, direction=direction,
                high_5m=high_5m_w, low_5m=low_5m_w,
                close_5m=close_5m_w, open_5m=open_5m_w,
                high_15m=high_15m_w, low_15m=low_15m_w,
                close_15m=close_15m_w, open_15m=open_15m_w,
                neck_4h=neck_4h, position_size=position_size,
                swing_confirmed=swing_confirmed,
            )

            if result["action"] == "exit_half":
                ep = current_price * (1 - slippage) if direction == "LONG" else current_price * (1 + slippage)
                partial_pnl = (ep - entry_price) * 0.5 * 100 if direction == "LONG" \
                              else (entry_price - ep) * 0.5 * 100
                position_pnl += partial_pnl
                position_size = 0.5
                exit_events.append(result["reason"])

            elif result["action"] == "exit_all":
                reason = result["reason"]
                ep = current_price * (1 - slippage) if direction == "LONG" else current_price * (1 + slippage)
                partial_pnl = (ep - entry_price) * position_size * 100 if direction == "LONG" \
                              else (entry_price - ep) * position_size * 100
                position_pnl += partial_pnl
                exit_events.append(reason)
                if reason == "early_stop_15m":
                    phase1_stop_count += 1
                elif reason == "5m_dow_break":
                    phase2_stop_count += 1
                trades.append({
                    "entry_bar": entry_idx, "exit_bar": i, "direction": direction,
                    "entry_price": entry_price, "exit_price": ep,
                    "pnl_pips": position_pnl, "exit_reason": reason,
                    "hold_bars": i - entry_idx, "swing_confirmed": current_trade_swing,
                })
                in_pos = False
                swing_confirmed = False
                current_trade_swing = False
                position_size = 0.0

        elif limit_pending:
            # ── 4Hダウ崩れ → 指値キャンセル ──
            if dir_4h != limit_direction and dir_4h != "NONE":
                limit_pending = False
                limit_cancel_count += 1

            # ── ネックライン再割れ → 指値キャンセル ──
            elif (limit_direction == "LONG" and current_price < limit_neck_15m) or \
                 (limit_direction == "SHORT" and current_price > limit_neck_15m):
                limit_pending = False
                limit_cancel_count += 1

            # ── 指値到達 → エントリー ──
            elif check_limit_triggered(
                current_high if limit_direction == "LONG" else current_low,
                limit_price, limit_direction
            ):
                entry_price = limit_price * (1 + slippage) if limit_direction == "LONG" \
                             else limit_price * (1 - slippage)
                entry_idx = i
                direction = limit_direction
                neck_4h = limit_neck_4h
                position_size = 1.0
                position_pnl = 0.0
                swing_confirmed = False
                current_trade_swing = False
                in_pos = True
                limit_pending = False

        if not in_pos and not limit_pending:
            if setups_long_arr[i] and not np.isnan(neck_4h_long_arr[i]) and not np.isnan(neck_15m_long_arr[i]):
                limit_direction = "LONG"
                limit_neck_15m = float(neck_15m_long_arr[i])
                limit_price = calc_limit_price(limit_neck_15m, "LONG")
                limit_neck_4h = float(neck_4h_long_arr[i])
                limit_pending = True
            elif setups_short_arr[i] and not np.isnan(neck_4h_short_arr[i]) and not np.isnan(neck_15m_short_arr[i]):
                limit_direction = "SHORT"
                limit_neck_15m = float(neck_15m_short_arr[i])
                limit_price = calc_limit_price(limit_neck_15m, "SHORT")
                limit_neck_4h = float(neck_4h_short_arr[i])
                limit_pending = True

    # 未決済ポジションを最終バーで強制決済
    if in_pos:
        current_price = float(close.iloc[-1])
        ep = current_price * (1 - slippage) if direction == "LONG" else current_price * (1 + slippage)
        partial_pnl = (ep - entry_price) * position_size * 100 if direction == "LONG" \
                      else (entry_price - ep) * position_size * 100
        position_pnl += partial_pnl
        trades.append({
            "entry_bar": entry_idx, "exit_bar": len(close) - 1, "direction": direction,
            "entry_price": entry_price, "exit_price": ep,
            "pnl_pips": position_pnl, "exit_reason": "FINAL_BAR",
            "hold_bars": len(close) - 1 - entry_idx, "swing_confirmed": current_trade_swing,
        })

    _empty = {
        "total_trades": 0, "long_trades": 0, "short_trades": 0,
        "win_rate": 0.0, "profit_factor": 0.0,
        "max_drawdown_pips": 0.0, "avg_hold_bars": 0, "total_pnl_pips": 0.0,
        "long_win_rate": 0.0, "short_win_rate": 0.0, "exit_reason_counts": {},
        "long_avg_pnl": 0.0, "short_avg_pnl": 0.0,
        "neck_reach_count": 0, "neck_reach_rate": 0.0,
        "limit_cancel_count": limit_cancel_count,
        "phase1_stop_count": phase1_stop_count, "phase2_stop_count": phase2_stop_count,
        "swing_confirmed_count": swing_confirmed_count, "reset_count": reset_count,
    }
    if not trades:
        return _empty

    from collections import Counter
    reason_counts = dict(Counter(exit_events))

    df_t = pd.DataFrame(trades)
    df_long = df_t[df_t["direction"] == "LONG"]
    df_short = df_t[df_t["direction"] == "SHORT"]

    wins = df_t[df_t["pnl_pips"] > 0]
    losses = df_t[df_t["pnl_pips"] <= 0]
    gross_profit = float(wins["pnl_pips"].sum()) if len(wins) else 0.0
    gross_loss = float(losses["pnl_pips"].sum()) if len(losses) else 0.0
    pf = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf")

    cum_pnl = df_t["pnl_pips"].cumsum()
    running_max = cum_pnl.cummax()
    max_dd = float((running_max - cum_pnl).max()) if len(cum_pnl) else 0.0

    def _wr(df):
        if len(df) == 0:
            return 0.0
        return float((df["pnl_pips"] > 0).sum() / len(df) * 100)

    long_avg_pnl = round(float(df_long["pnl_pips"].mean()), 2) if len(df_long) else 0.0
    short_avg_pnl = round(float(df_short["pnl_pips"].mean()), 2) if len(df_short) else 0.0
    neck_reach_count = reason_counts.get("4Hネックライン到達・半値決済", 0)
    neck_reach_rate = round(neck_reach_count / max(len(trades), 1) * 100, 1)

    return {
        "total_trades": len(trades),
        "long_trades": len(df_long),
        "short_trades": len(df_short),
        "win_rate": round(float(len(wins) / len(trades) * 100), 2),
        "long_win_rate": round(_wr(df_long), 2),
        "short_win_rate": round(_wr(df_short), 2),
        "profit_factor": round(pf, 2),
        "max_drawdown_pips": round(max_dd, 2),
        "avg_hold_bars": round(float(df_t["hold_bars"].mean()), 1),
        "total_pnl_pips": round(float(df_t["pnl_pips"].sum()), 2),
        "exit_reason_counts": reason_counts,
        "long_avg_pnl": long_avg_pnl,
        "short_avg_pnl": short_avg_pnl,
        "neck_reach_count": neck_reach_count,
        "neck_reach_rate": neck_reach_rate,
        # デバッグ統計 a/b/c/d
        "limit_cancel_count": limit_cancel_count,
        "phase1_stop_count": phase1_stop_count,
        "phase2_stop_count": phase2_stop_count,
        "swing_confirmed_count": swing_confirmed_count,
        "reset_count": reset_count,
    }


# ── メインバックテスト関数（Phase B完結版） ───────────────────────
def run_rex_mtf_backtest(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
    lot_size: float = 1.0,
) -> None:
    """ミナト流MTF v2 バックテスト（Phase B完結・entry_logic統合版）。

    signals.py 依存を廃止し、全5Mバーを走査してエントリー条件を評価する。
    Long/Short 両方向を同ロットサイズで実装（データ取り優先フェーズ）。
    """
    t0 = time.time()

    print("=" * 70)
    print("  REX MTF バックテスト - #007 指値エントリー + 二段階SL版")
    print("=" * 70)
    print(f"データ: {df_path}")
    print(f"Lotサイズ: {lot_size} | Long倍率: {LONG_LOT_MULTIPLIER} | Short倍率: {SHORT_LOT_MULTIPLIER}")
    print("  ※ Short倍率は初期データ取り優先のためLongと同値。")
    print("     リスクリワード比較後にShort縮小幅を決定予定。")
    print("=" * 70)

    # ── データ読み込み ──
    print("\n[STEP 1] データ読み込み + 前処理...")
    df_multi = _load_and_preprocess(df_path)
    print(f"  完了: {df_multi.shape}, 期間={df_multi.index.min()} ~ {df_multi.index.max()}")

    # ── 5M生DataFrame（Open列が必要） ──
    # df_multi は ffill 済みなので5M列を生として使う（5M足はほぼ欠損なし）
    df_5m_raw = df_multi[["5M_High", "5M_Low", "5M_Open", "5M_Close"]].rename(
        columns={
            "5M_High": "High", "5M_Low": "Low",
            "5M_Open": "Open", "5M_Close": "Close",
        }
    )
    # JSTインデックスのままresampleするためtz情報を保持

    # ── 4H方向プリコンピュート ──
    print("\n[STEP 2] 4H方向プリコンピュート（_build_direction_5m）...")
    direction_series = _build_direction_5m(df_5m_raw, n=2, lookback=30)
    dir_counts = direction_series.value_counts()
    none_ratio = dir_counts.get('NONE', 0) / max(len(direction_series), 1) * 100
    print(f"  方向分布: LONG={dir_counts.get('LONG', 0)}, SHORT={dir_counts.get('SHORT', 0)}, NONE={dir_counts.get('NONE', 0)}")
    print(f"  NONE比率: {none_ratio:.1f}%")

    # ── 全バースキャン ──
    print("\n[STEP 3] セットアップスキャン（全5Mバー評価）...")
    setups_long, setups_short, skip_reasons, neck_4h_long, neck_4h_short, neck_15m_long, neck_15m_short = (
        _scan_all_bars_for_entry(df_multi, df_5m_raw, direction_series)
    )

    n_long = int(setups_long.sum())
    n_short = int(setups_short.sum())
    print(f"  セットアップ候補: LONG={n_long}件, SHORT={n_short}件")

    # スキップ理由の内訳
    skip_reason_counts = skip_reasons[skip_reasons != ""].value_counts()
    print("\n  スキップ理由の内訳:")
    for reason, count in skip_reason_counts.items():
        print(f"    {reason}: {count}件")

    if n_long == 0 and n_short == 0:
        print("\n  [WARNING] エントリーが0件です。パラメータを確認してください。")
        return

    # ── 15M足（決済ロジック用） ──
    print("\n[STEP 4] 15M足プリコンピュート（決済ロジック用）...")
    df_15m_for_exit = df_5m_raw.resample("15min").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    print(f"  15M: {len(df_15m_for_exit)}本")

    # ── バックテスト実行 ──
    print("\n[STEP 5] バックテスト実行（ミナト流3段階決済）...")
    close = df_multi["5M_Close"]
    high = df_multi["5M_High"]
    low = df_multi["5M_Low"]
    open_5m = df_multi["5M_Open"]

    res = _simple_backtest_directional(
        close, high, low, open_5m,
        setups_long, setups_short,
        neck_4h_long, neck_4h_short,
        neck_15m_long, neck_15m_short,
        df_15m_for_exit,
        direction_series,
    )

    elapsed = time.time() - t0

    # ── 結果出力 ──
    print("\n" + "=" * 70)
    print("  REX MTF バックテスト結果サマリ（#007: 指値エントリー + 二段階SL版）")
    print("=" * 70)
    print(f"\n  総トレード数:         {res['total_trades']}")
    print(f"  うちLong:             {res['long_trades']}")
    print(f"  うちShort:            {res['short_trades']}")
    print(f"\n  全体勝率:             {res['win_rate']:.2f}%")
    print(f"  Long勝率:             {res['long_win_rate']:.2f}%")
    print(f"  Short勝率:            {res['short_win_rate']:.2f}%")
    print(f"\n  Profit Factor:        {res['profit_factor']}")
    print(f"  最大DD (pips):        {res['max_drawdown_pips']:.2f}")
    print(f"  総損益 (pips):        {res['total_pnl_pips']:.2f}")
    print(f"  平均保有バー数:       {res['avg_hold_bars']}")

    print("\n  決済理由の内訳:")
    for reason, count in res.get("exit_reason_counts", {}).items():
        print(f"    {reason}: {count}件")

    print("\n" + "=" * 70)
    print("  デバッグ統計 a/b/c/d")
    print("=" * 70)
    print(f"\n  [a] 指値未約定キャンセル件数: {res['limit_cancel_count']}件")
    print(f"\n  [b] SLフェーズ別損切件数:")
    print(f"      フェーズ1（15M早期損切）: {res['phase1_stop_count']}件")
    print(f"      フェーズ2（5Mダウ崩れ）:  {res['phase2_stop_count']}件")
    sc_rate = round(res['swing_confirmed_count'] / max(res['total_trades'], 1) * 100, 1)
    print(f"\n  [c] swing_confirmed到達率:")
    print(f"      {res['total_trades']}件中{res['swing_confirmed_count']}件 = {sc_rate:.1f}%")
    print(f"\n  [d] 4Hダウ崩れ戦略リセット件数: {res['reset_count']}件")
    print(f"\n  LONG/SHORT別 平均値幅:")
    print(f"      Long  平均: {res['long_avg_pnl']:+.2f} pips")
    print(f"      Short 平均: {res['short_avg_pnl']:+.2f} pips")
    print(f"\n  4Hネック到達率:")
    print(f"      {res['total_trades']}件中{res['neck_reach_count']}件到達 = {res['neck_reach_rate']:.1f}%")

    print(f"\n  実行時間:             {elapsed:.1f}秒")

    # 総合評価
    print("\n" + "=" * 70)
    print("  総合評価")
    print("=" * 70)

    avg_pnl = res["total_pnl_pips"] / max(res["total_trades"], 1)
    print(f"\n  期待値(pips/trade):   {avg_pnl:.2f}")
    if avg_pnl >= 5.0:
        print("  → [OK] 期待値+5pips以上！裁量で狙う価値あり")
    else:
        print("  → [NG] 期待値が低い。ルール見直し推奨")

    pf = res["profit_factor"]
    if pf >= 1.5:
        print(f"\n  → [OK] PF {pf:.2f} - 1.5以上！長期的にプラス期待")
    else:
        print(f"\n  → [NG] PF {pf:.2f} - 低い。リスクリワード改善が必要")

    max_dd = res["max_drawdown_pips"]
    if max_dd > 100.0:
        print(f"\n  → [警告] MaxDD {max_dd:.1f}pips超え！リスク管理を見直してください")
    else:
        print(f"\n  → [OK] MaxDD {max_dd:.1f}pips - リスク管理良好")

    print("\n" + "=" * 70)
    print("  [次のステップ]")
    print("  Phase D: volume_alert.py - 出来高急増シグナル通知")
    print("=" * 70)
    print("\nボス、結果見てLong/Short別の勝率・MaxDDを確認してね！")


# ── 旧バックテスト（後方互換で残存、signals.py依存） ──────────────
def run_usdjpy_mtf_v2(
    ticker: str = "USDJPY=X",
    years: int = 5,
) -> None:
    """[DEPRECATED] 旧バックテスト。signals.py依存版。互換性のため残存。"""
    print("[WARNING] run_usdjpy_mtf_v2 は旧バージョンです。")
    print("  run_rex_mtf_backtest() を使用してください。")


def run_usdjpy_mtf_v2_advanced(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
    lot_size: float = 1.0,
    risk_percent: float = 0.5,
) -> None:
    """[DEPRECATED] 旧Advanced版。互換性のため残存。"""
    print("[WARNING] run_usdjpy_mtf_v2_advanced は旧バージョンです。")
    print("  run_rex_mtf_backtest() を使用してください。")
    run_rex_mtf_backtest(df_path=df_path, lot_size=lot_size)


if __name__ == "__main__":
    run_rex_mtf_backtest(
        df_path="data/raw/usdjpy_multi_tf_2years.parquet",
        lot_size=1.0,
    )
