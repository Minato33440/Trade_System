"""backtest.py — USDJPY MTF v2 バックテスト（Phase B完結版）。

python src/backtest.py で実行。

変更履歴:
  Phase A: swing_detector.py 追加・Long/Short分岐骨格
  Phase A補足: 4H実足Swing検出（resampled 4H）によるNONE問題修正
  Phase B: entry_logic.py 追加・3段階エントリー条件実装
  Phase B完結(指示書#003):
    - signals.py シグナル依存を廃止（コメントアウトで残存）
    - 全5Mバー走査（_scan_all_bars_for_entry）に移行
    - Long/Short 両方向 同ロット数で実装（データ取り優先）
    - MAX_REENTRY = 1 の再エントリー管理変数追加

設計思想:
  「4H上昇ダウが継続している限り、押し目条件が揃うたびにエントリーを繰り返す」
  エリオット波数カウントは不要。
  Long/Short 両方向同ロット（将来のロット調整は TODO コメントで明示）。
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
from src.entry_logic import MAX_REENTRY, evaluate_entry

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
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """全5Mバーを走査して evaluate_entry() が True になるバーを探す。

    signals.py のシグナルに依存せず、4H方向が確定している全バーで
    3段階エントリー条件をチェックする。

    Args:
        df_multi:         前処理済みのMulti-TF DataFrame（ffill済み）
        df_5m_raw:        5M足の生DataFrame（High/Low/Open/Close列を含む）
                          ※4H/1H/15Mへのresampleに使用
        direction_series: _build_direction_5m() でプリコンピュート済みの方向Series

    Returns:
        (entries_long, entries_short, skip_reason_series)
        entries_long/short: bool Series（True のバーの次の始値でエントリー）
        skip_reason_series: str Series（スキップ理由のデバッグ情報）
    """
    entries_long = pd.Series(False, index=df_multi.index)
    entries_short = pd.Series(False, index=df_multi.index)
    skip_reasons = pd.Series("", index=df_multi.index, dtype=object)

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
    warmup = 100  # 先頭100本はウォームアップ

    # 再エントリー管理（同一押し目機会）
    reentry_count_long = 0
    reentry_count_short = 0
    last_sl_long = float("nan")   # 最後に参照したSL（押し目機会の識別）
    last_sh_short = float("nan")  # 最後に参照したSH（戻り機会の識別）

    print(f"  [INFO] {n_bars}本のバーをスキャン中...")

    for i in range(warmup, n_bars - 1):
        ts = ts_5m[i]
        direction = direction_series.iloc[i]

        if direction == "NONE":
            skip_reasons.iloc[i] = "NONE方向"
            continue

        # ── searchsorted でインデックスを取得 ──
        idx_4h = int(np.searchsorted(ts_4h, ts, side="right")) - 1
        idx_1h = int(np.searchsorted(ts_1h, ts, side="right")) - 1
        idx_15m = int(np.searchsorted(ts_15m, ts, side="right")) - 1

        if idx_4h < 10 or idx_1h < 6 or idx_15m < 6:
            skip_reasons.iloc[i] = "データ不足"
            continue

        # ── 4H Swing値を取得 ──
        sh_4h = get_nearest_swing_high(df_4h_full["High"], idx_4h, n=3, lookback=20)
        sl_4h = get_nearest_swing_low(df_4h_full["Low"], idx_4h, n=3, lookback=20)

        # ── 再エントリー管理：同一押し目機会の識別 ──
        if direction == "LONG":
            if not np.isnan(last_sl_long) and abs(sl_4h - last_sl_long) > (sh_4h - sl_4h) * 0.05:
                # 新しいSwing Low → 押し目機会リセット
                reentry_count_long = 0
                last_sl_long = sl_4h
            elif np.isnan(last_sl_long):
                last_sl_long = sl_4h
            if reentry_count_long > MAX_REENTRY:
                skip_reasons.iloc[i] = "再エントリー上限"
                continue
        else:  # SHORT
            if not np.isnan(last_sh_short) and abs(sh_4h - last_sh_short) > (sh_4h - sl_4h) * 0.05:
                reentry_count_short = 0
                last_sh_short = sh_4h
            elif np.isnan(last_sh_short):
                last_sh_short = sh_4h
            if reentry_count_short > MAX_REENTRY:
                skip_reasons.iloc[i] = "再エントリー上限"
                continue

        # ── 4Hネックライン（LONGはSH、SHORTはSL） ──
        neck_4h = sh_4h if direction == "LONG" else sl_4h

        # ── 1H Swing ──
        low_1h = df_1h_full["Low"].iloc[: idx_1h + 1]
        high_1h = df_1h_full["High"].iloc[: idx_1h + 1]

        # ── 15Mネックライン ──
        neck_15m_sh = get_nearest_swing_high(df_15m_full["High"], idx_15m, n=3, lookback=30)
        neck_15m_sl = get_nearest_swing_low(df_15m_full["Low"], idx_15m, n=3, lookback=30)
        neck_15m = neck_15m_sh if direction == "LONG" else neck_15m_sl

        # ── 5M直近2本（確定足判定用） ──
        close_5m_w = df_multi["5M_Close"].iloc[max(0, i - 2): i + 1]
        open_5m_w = df_multi["5M_Open"].iloc[max(0, i - 2): i + 1]

        current_price = float(df_multi["5M_Close"].iloc[i])

        # ── evaluate_entry で3段階チェック ──
        result = evaluate_entry(
            price=current_price,
            direction=direction,
            swing_high_4h=sh_4h,
            swing_low_4h=sl_4h,
            neck_4h=neck_4h,
            low_1h=low_1h,
            high_1h=high_1h,
            current_idx_1h=len(low_1h) - 1,
            close_5m=close_5m_w,
            open_5m=open_5m_w,
            neck_15m=neck_15m,
        )

        skip_reasons.iloc[i] = result["reason"]

        if result["enter"]:
            if direction == "LONG":
                entries_long.iloc[i + 1] = True   # 次の5M始値でエントリー
                reentry_count_long += 1
            else:
                entries_short.iloc[i + 1] = True
                reentry_count_short += 1

    return entries_long, entries_short, skip_reasons


# ── シンプルバックテスト（方向対応版） ────────────────────────────
def _simple_backtest_directional(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    entries_long: pd.Series,
    entries_short: pd.Series,
    commission: float = 0.0005,
    slippage: float = 0.0002,
    stop_atr_mult: float = 1.3,
    hold_bars: int = 48,        # デフォルト: 4時間足3本 ≒ 5M 144本（仮）
) -> Dict[str, Any]:
    """Long/Short 両方向対応のシンプルバックテスト。

    エントリー: entries_long/short が True の足の Open（次足始値）
    ストップ:   ATR(14) × stop_atr_mult + 最大50pipsキャップ
    決済:       固定バー数保持（将来的にexit_logic.pyで高度化）
    """
    from src.signals import _atr as calc_atr_signal  # ATR計算流用

    atr = calc_atr_signal(high, low, close, period=14)

    close_arr = close.values.astype(float)
    high_arr = high.values.astype(float)
    low_arr = low.values.astype(float)
    atr_arr = atr.values.astype(float)
    entries_long_arr = entries_long.values.astype(bool)
    entries_short_arr = entries_short.values.astype(bool)

    trades: List[Dict[str, Any]] = []
    in_pos = False
    entry_idx = 0
    entry_price = 0.0
    direction = ""
    stop_price = 0.0

    for i in range(len(close_arr)):
        if in_pos:
            # ── ストップ判定（バー内High/Lowで判断） ──
            atr_val = atr_arr[entry_idx] if not np.isnan(atr_arr[entry_idx]) else 0.01
            stop_dist = min(atr_val * stop_atr_mult, 0.50)  # 最大50pipsキャップ（USDJPY）

            if direction == "LONG":
                stop_price = entry_price - stop_dist
                hit_stop = low_arr[i] <= stop_price
                hit_target = (i - entry_idx) >= hold_bars
                exit_price = (
                    stop_price * (1 - slippage)
                    if hit_stop
                    else close_arr[i] * (1 - slippage)
                )
                pnl_per_unit = exit_price - entry_price
            else:  # SHORT
                stop_price = entry_price + stop_dist
                hit_stop = high_arr[i] >= stop_price
                hit_target = (i - entry_idx) >= hold_bars
                exit_price = (
                    stop_price * (1 + slippage)
                    if hit_stop
                    else close_arr[i] * (1 + slippage)
                )
                pnl_per_unit = entry_price - exit_price

            if hit_stop or hit_target:
                pnl_pips = pnl_per_unit * 100  # 円→pips換算（USDJPY）
                trades.append({
                    "entry_bar": entry_idx,
                    "exit_bar": i,
                    "direction": direction,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl_pips": pnl_pips,
                    "exit_reason": "STOP" if hit_stop else "HOLD_BARS",
                    "hold_bars": i - entry_idx,
                })
                in_pos = False

        if not in_pos:
            if entries_long_arr[i]:
                entry_price = close_arr[i] * (1 + slippage)
                entry_idx = i
                direction = "LONG"
                in_pos = True
            elif entries_short_arr[i]:
                entry_price = close_arr[i] * (1 - slippage)
                entry_idx = i
                direction = "SHORT"
                in_pos = True

    # 未決済ポジションを最終バーで決済
    if in_pos:
        if direction == "LONG":
            exit_price = close_arr[-1] * (1 - slippage)
            pnl_pips = (exit_price - entry_price) * 100
        else:
            exit_price = close_arr[-1] * (1 + slippage)
            pnl_pips = (entry_price - exit_price) * 100
        trades.append({
            "entry_bar": entry_idx,
            "exit_bar": len(close_arr) - 1,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pips": pnl_pips,
            "exit_reason": "FINAL_BAR",
            "hold_bars": len(close_arr) - 1 - entry_idx,
        })

    if not trades:
        return {
            "total_trades": 0, "long_trades": 0, "short_trades": 0,
            "win_rate": 0.0, "profit_factor": 0.0,
            "max_drawdown_pips": 0.0, "avg_hold_bars": 0,
            "total_pnl_pips": 0.0,
            "long_win_rate": 0.0, "short_win_rate": 0.0,
        }

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
    print("  REX MTF バックテスト — Phase B完結版（entry_logic統合）")
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
    direction_series = _build_direction_5m(df_5m_raw, n=3, lookback=20)
    dir_counts = direction_series.value_counts()
    print(f"  方向分布: LONG={dir_counts.get('LONG', 0)}, SHORT={dir_counts.get('SHORT', 0)}, NONE={dir_counts.get('NONE', 0)}")

    # ── 全バースキャン ──
    print("\n[STEP 3] エントリースキャン（全5Mバー評価）...")
    entries_long, entries_short, skip_reasons = _scan_all_bars_for_entry(
        df_multi, df_5m_raw, direction_series
    )

    n_long = int(entries_long.sum())
    n_short = int(entries_short.sum())
    print(f"  エントリー候補: LONG={n_long}件, SHORT={n_short}件")

    # スキップ理由の内訳
    reason_counts = skip_reasons[skip_reasons != ""].value_counts()
    print("\n  スキップ理由の内訳:")
    for reason, count in reason_counts.items():
        print(f"    {reason}: {count}件")

    if n_long == 0 and n_short == 0:
        print("\n  [WARNING] エントリーが0件です。パラメータを確認してください。")
        return

    # ── バックテスト実行 ──
    print("\n[STEP 4] バックテスト実行...")
    close = df_multi["5M_Close"]
    high = df_multi["5M_High"]
    low = df_multi["5M_Low"]

    res = _simple_backtest_directional(close, high, low, entries_long, entries_short)

    elapsed = time.time() - t0

    # ── 結果出力 ──
    print("\n" + "=" * 70)
    print("  バックテスト結果サマリ")
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
        print(f"\n  → [OK] PF {pf:.2f} — 1.5以上！長期的にプラス期待")
    else:
        print(f"\n  → [NG] PF {pf:.2f} — 低い。リスクリワード改善が必要")

    max_dd = res["max_drawdown_pips"]
    if max_dd > 100.0:
        print(f"\n  → [警告] MaxDD {max_dd:.1f}pips超え！リスク管理を見直してください")
    else:
        print(f"\n  → [OK] MaxDD {max_dd:.1f}pips — リスク管理良好")

    print("\n" + "=" * 70)
    print("  [次のステップ]")
    print("  Phase C: exit_logic.py — 5M/15Mダウ崩れ段階決済実装")
    print("  Phase D: volume_alert.py — 出来高急増シグナル通知")
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
