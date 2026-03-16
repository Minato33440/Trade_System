"""Simple_Backtest.py — 強化版MTF v2 シグナル分析。

・再エントリー: 損切後15分待機 ＋ 15分ネックライン越え（同一方向最大1回）
・ストップ: 5分足ATR(14)×1.3 + 50pipsキャップ。**バー内高値/安値**で判定（終値のみでなく各5分足のHigh/Lowでストップに触れたら即損切）。
・決済: 4Hネックライン半値利確 → 残り半分は「前回15分足**実体安値/高値**（終値でなくbody）を実体下抜け/上抜け確定」まで待つ。
・累積損益（1Lot円）表示

【v3 修正内容】
バグ1 (_prev_body 根本修正):
  close_15m / open_15m は 5M インデックスに ffill されているため、
  旧コードの j-1 は「前回15M足」でなく「同じ15M期間内の前5Mバー」を参照していた。
  → 実体安値 bl_15 が現在バーとほぼ同値になり、c < bl_15 がほぼ発動しなかった。
  修正: _precompute_prev_body_series() で15M/1Hバー境界を事前検出し、
        各5Mバーに「前回TFバーの実体low/high」を展開した Series を作成。
        _simulate_trade 内で直接 iloc 参照に変更。

バグ2 (reentry_used_since_stop リセット漏れ):
  再エントリー後に新たな損切りが発生しても reentry_used_since_stop が True のままで
  次の再エントリーが永久に不可になっていた。
  修正: 損切り発生時に reentry_used_since_stop[direction] = False でリセット。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.signals import mtf_minato_short_v2


def _calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def load_data(df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet") -> pd.DataFrame:
    df_path_obj = Path(df_path)
    if not df_path_obj.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        df_path_obj = project_root / df_path

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


def _safe_atr_val(atr_series, t) -> float:
    """ATR をスカラーで安全に取得。"""
    if atr_series is None or t not in atr_series.index:
        return float("nan")
    v = atr_series.loc[t]
    if isinstance(v, pd.Series):
        return float(v.iloc[0]) if len(v) > 0 else float("nan")
    return float(v) if pd.notna(v) else float("nan")


def _precompute_prev_body_series(
    open_ser: "pd.Series | None",
    close_ser: "pd.Series | None",
    tf_name: str = "?",
    debug: bool = False,
) -> "tuple[pd.Series | None, pd.Series | None]":
    """5M インデックスの上位TF Open/Close から「前回バー実体低値/高値」を各5Mバーに展開。

    【解決するバグ】
    close_15m / open_15m は df_multi の 5M インデックスに ffill されているため、
    旧 _prev_body() の j-1 は「前回15M足」でなく「同じ15M期間内の前5Mバー」を返していた。
    同じ15M期間内では Open も Close も同値なため bl_15 ≈ 現在値となり、
    c < bl_15 がほぼ発動しなかった。

    【修正方針】
    Open 値が変化する行 = 新しいTFバーの開始 と判定し、
    各 5M バーに「1つ前の完成したTFバーの body_low / body_high」を事前展開する。

    Returns:
        (prev_bl_series, prev_bh_series): 各5Mバーに対応する前回TFバー実体低値・高値
        前回バーが存在しない行は NaN。
    """
    if open_ser is None or close_ser is None:
        return None, None

    open_vals = open_ser.values.astype(float)
    close_vals = close_ser.values.astype(float)
    n = len(open_vals)

    # TFバー境界検出: Open 値が変化する行 = 新しいバーの開始
    is_new_bar = np.zeros(n, dtype=bool)
    is_new_bar[0] = True
    for i in range(1, n):
        prev_o = open_vals[i - 1]
        curr_o = open_vals[i]
        if np.isnan(prev_o) and not np.isnan(curr_o):
            is_new_bar[i] = True
        elif not np.isnan(curr_o) and not np.isnan(prev_o) and curr_o != prev_o:
            is_new_bar[i] = True

    bar_starts = np.where(is_new_bar)[0]
    n_bars = len(bar_starts)

    prev_bl_arr = np.full(n, np.nan)
    prev_bh_arr = np.full(n, np.nan)

    if debug:
        print(f"\n[_precompute_prev_body] TF={tf_name}: 検出バー数={n_bars}, 全5Mバー数={n}")
        print(f"  最初の5バー境界インデックス: {bar_starts[:5].tolist()}")

    for k in range(1, n_bars):
        curr_start = bar_starts[k]        # 現在バー開始位置
        prev_start = bar_starts[k - 1]    # 前回バー開始位置
        prev_end   = curr_start - 1        # 前回バー終了位置

        prev_o = open_vals[prev_start]
        prev_c = close_vals[prev_end]
        if np.isnan(prev_o) or np.isnan(prev_c):
            continue

        prev_bl = min(prev_o, prev_c)
        prev_bh = max(prev_o, prev_c)

        # 現在バーの全5M行に前回バー実体をセット
        next_start = bar_starts[k + 1] if k + 1 < n_bars else n
        prev_bl_arr[curr_start:next_start] = prev_bl
        prev_bh_arr[curr_start:next_start] = prev_bh

    if debug:
        valid_count = int(np.sum(~np.isnan(prev_bl_arr)))
        print(f"  前回実体が取得できた5Mバー数: {valid_count} / {n} ({valid_count/n*100:.1f}%)")
        first_valid = next((i for i in range(n) if not np.isnan(prev_bl_arr[i])), None)
        if first_valid is not None:
            ts_str = str(open_ser.index[first_valid])
            print(f"  最初の有効行 idx={first_valid} ts={ts_str}: "
                  f"prev_bl={prev_bl_arr[first_valid]:.5f}, prev_bh={prev_bh_arr[first_valid]:.5f}")

    return (
        pd.Series(prev_bl_arr, index=open_ser.index),
        pd.Series(prev_bh_arr, index=open_ser.index),
    )


def _precompute_4h_swing(
    open_4h: "pd.Series | None",
    high_4h: "pd.Series | None",
    low_4h:  "pd.Series | None",
    n_bars: int = 5,
    debug: bool = False,
) -> "tuple[pd.Series | None, pd.Series | None, np.ndarray, np.ndarray, np.ndarray]":
    """5M インデックスの 4H Open/High/Low から「直近 n_bars 本の本物の4Hバー」の
    スイング高値(max of High) / スイング安値(min of Low) を各5Mバーに事前展開する。

    Returns:
        (swing_high_series, swing_low_series, bar_starts, bar_highs, bar_lows)
        bar_* は方向性ネックライン計算 (_get_directional_neckline) で使用する。
    """
    _empty = (None, None, np.array([]), np.array([]), np.array([]))
    if open_4h is None or high_4h is None or low_4h is None:
        return _empty

    open_vals = open_4h.values.astype(float)
    high_vals = high_4h.values.astype(float)
    low_vals  = low_4h.values.astype(float)
    n = len(open_vals)

    # 4Hバー境界検出: Open 値が変化する行 = 新しい4Hバーの開始
    is_new_bar = np.zeros(n, dtype=bool)
    is_new_bar[0] = True
    for i in range(1, n):
        prev_o = open_vals[i - 1]
        curr_o = open_vals[i]
        if np.isnan(prev_o) and not np.isnan(curr_o):
            is_new_bar[i] = True
        elif not np.isnan(curr_o) and not np.isnan(prev_o) and curr_o != prev_o:
            is_new_bar[i] = True

    bar_starts = np.where(is_new_bar)[0]
    n_4h_bars  = len(bar_starts)

    swing_high_arr = np.full(n, np.nan)
    swing_low_arr  = np.full(n, np.nan)

    if debug:
        print(f"\n[_precompute_4h_swing] n_bars={n_bars}: 検出4Hバー数={n_4h_bars}, 全5Mバー数={n}")
        print(f"  最初の5境界インデックス: {bar_starts[:5].tolist()}")

    # 各4Hバーの High/Low を確定（前回バーの High = prev_start〜prev_end の max）
    # 4H High/Low は ffill されているので、バー内では同値 → バーの終端値を使う
    bar_highs = np.full(n_4h_bars, np.nan)
    bar_lows  = np.full(n_4h_bars, np.nan)
    for k in range(n_4h_bars):
        start = bar_starts[k]
        end   = bar_starts[k + 1] - 1 if k + 1 < n_4h_bars else n - 1
        # バー内最大High / 最小Lowを取得（ffillされているので全て同値のはずだが念のため）
        h_slice = high_vals[start:end + 1]
        l_slice = low_vals[start:end + 1]
        valid_h = h_slice[~np.isnan(h_slice)]
        valid_l = l_slice[~np.isnan(l_slice)]
        if len(valid_h) > 0:
            bar_highs[k] = valid_h.max()
        if len(valid_l) > 0:
            bar_lows[k]  = valid_l.min()

    # 各5Mバーに「直近 n_bars 本の完成済み4Hバー」のスイング高値/安値を展開
    for k in range(1, n_4h_bars):
        curr_start = bar_starts[k]
        # 直近 n_bars 本の完成済みバー = k-n_bars 〜 k-1
        look_from  = max(0, k - n_bars)
        window_h   = bar_highs[look_from:k]
        window_l   = bar_lows[look_from:k]
        valid_h    = window_h[~np.isnan(window_h)]
        valid_l    = window_l[~np.isnan(window_l)]
        if len(valid_h) == 0 or len(valid_l) == 0:
            continue
        sw_high = valid_h.max()
        sw_low  = valid_l.min()

        # 現在の4Hバー全体（次の4Hバー開始まで）に展開
        next_start = bar_starts[k + 1] if k + 1 < n_4h_bars else n
        swing_high_arr[curr_start:next_start] = sw_high
        swing_low_arr[curr_start:next_start]  = sw_low

    if debug:
        valid_count = int(np.sum(~np.isnan(swing_high_arr)))
        print(f"  スイング値が取得できた5Mバー数: {valid_count} / {n} ({valid_count/n*100:.1f}%)")
        # エントリー#3付近(2024-09-09)の確認用サンプル
        idx_sample = next((i for i in range(n) if not np.isnan(swing_high_arr[i])), None)
        if idx_sample is not None:
            ts_str = str(open_4h.index[idx_sample])
            print(f"  最初の有効行 idx={idx_sample} ts={ts_str}: "
                  f"sw_high={swing_high_arr[idx_sample]:.3f}, sw_low={swing_low_arr[idx_sample]:.3f}")

    return (
        pd.Series(swing_high_arr, index=open_4h.index),
        pd.Series(swing_low_arr,  index=open_4h.index),
        bar_starts,
        bar_highs,
        bar_lows,
    )


def _get_directional_neckline(
    bar_starts: np.ndarray,
    bar_highs: np.ndarray,
    bar_lows: np.ndarray,
    idx: int,
    direction: str,
    price: float,
    atr_val: float,
    n_bars: int = 20,
    min_dist: float = 0.0,
    debug: bool = False,
) -> "tuple[float, float]":
    """方向性ネックライン: 最小距離フィルタ付きで4H高値/安値を返す（v8）。

    LONG:  entryより上、かつ min_dist 以上離れた直近4H高値の中で最も近いもの
    SHORT: entryより下、かつ min_dist 以上離れた直近4H安値の中で最も近いもの
    fallback: ATR × 2.5

    Args:
        min_dist: エントリーからの最小距離（price単位）。stop_dist * 2.0 推奨。

    Returns:
        (entry_4h_high, entry_4h_low) - _simulate_trade に渡す形式
    """
    fallback_high = price + max(atr_val * 2.5, min_dist)
    fallback_low  = price - max(atr_val * 2.5, min_dist)

    if len(bar_starts) == 0:
        return fallback_high, fallback_low

    # idxが属する4Hバーのインデックスを二分探索で特定
    k_cur = int(np.searchsorted(bar_starts, idx, side="right")) - 1
    k_cur = max(0, k_cur)

    # 直近 n_bars 本の完成済みバー（現在バーは未完成なので除外）
    look_from = max(0, k_cur - n_bars)
    look_to   = k_cur  # exclusive

    if look_to <= look_from:
        return fallback_high, fallback_low

    window_h = bar_highs[look_from:look_to]
    window_l = bar_lows[look_from:look_to]

    if debug:
        min_dist_pips = min_dist * 100
        print(f"  [neck_dbg] MIN_NECK_DIST={min_dist_pips:.1f}pips  "
              f"window={look_to - look_from}本(idx{look_from}〜{look_to-1})")

    if direction == "L":
        # entryより上、かつ min_dist 以上離れた高値のうち最も近い（最小の）もの
        mask = (window_h > price) & ((window_h - price) >= min_dist) & ~np.isnan(window_h)
        all_above = window_h[(window_h > price) & ~np.isnan(window_h)]
        filtered  = window_h[mask]
        if debug:
            all_above_sorted = sorted(float(v) for v in all_above)
            print(f"  [neck_dbg LONG] entry上の候補全件({len(all_above_sorted)}件): "
                  + ", ".join(f"{v:.3f}({(v-price)*100:.1f}p)" for v in all_above_sorted[:10]))
            filt_sorted = sorted(float(v) for v in filtered)
            print(f"  [neck_dbg LONG] MIN_DIST通過({len(filt_sorted)}件): "
                  + ", ".join(f"{v:.3f}({(v-price)*100:.1f}p)" for v in filt_sorted[:10]))
        neck_high = float(filtered.min()) if len(filtered) > 0 else fallback_high
        neck_low  = fallback_low
        if debug:
            src = "候補採用" if len(filtered) > 0 else "fallback(ATR*2.5)"
            print(f"  [neck_dbg LONG] => entry_4h_high={neck_high:.3f} "
                  f"({(neck_high-price)*100:.1f}pips) [{src}]")
    else:
        # entryより下、かつ min_dist 以上離れた安値のうち最も近い（最大の）もの
        mask = (window_l < price) & ((price - window_l) >= min_dist) & ~np.isnan(window_l)
        all_below = window_l[(window_l < price) & ~np.isnan(window_l)]
        filtered  = window_l[mask]
        if debug:
            all_below_sorted = sorted((float(v) for v in all_below), reverse=True)
            print(f"  [neck_dbg SHORT] entry下の候補全件({len(all_below_sorted)}件): "
                  + ", ".join(f"{v:.3f}({(price-v)*100:.1f}p)" for v in all_below_sorted[:10]))
            filt_sorted = sorted((float(v) for v in filtered), reverse=True)
            print(f"  [neck_dbg SHORT] MIN_DIST通過({len(filt_sorted)}件): "
                  + ", ".join(f"{v:.3f}({(price-v)*100:.1f}p)" for v in filt_sorted[:10]))
        neck_low  = float(filtered.max()) if len(filtered) > 0 else fallback_low
        neck_high = fallback_high
        if debug:
            src = "候補採用" if len(filtered) > 0 else "fallback(ATR*2.5)"
            print(f"  [neck_dbg SHORT] => entry_4h_low={neck_low:.3f} "
                  f"({(price-neck_low)*100:.1f}pips) [{src}]")

    return neck_high, neck_low


def _simulate_trade(
    direction: str,
    idx: int,
    price: float,
    entry_4h_high: float,
    entry_4h_low: float,
    atr_val: float,
    close_5m: pd.Series,
    low_5m: "pd.Series | None",
    high_5m: "pd.Series | None",
    open_5m: "pd.Series | None",
    prev_bl_15_s: "pd.Series | None",   # 事前計算済み: 各5Mバーの前回15M実体低値
    prev_bh_15_s: "pd.Series | None",   # 事前計算済み: 各5Mバーの前回15M実体高値
    prev_bl_1h_s: "pd.Series | None",   # 事前計算済み: 各5Mバーの前回1H実体低値
    prev_bh_1h_s: "pd.Series | None",   # 事前計算済み: 各5Mバーの前回1H実体高値
    max_bars: int = 96,
    stop_mult: float = 1.3,
    debug_log: "Optional[List[str]]" = None,
    trade_id: int = 0,
    debug_body_n: int = 0,   # 半値利確後 N バーのみ詳細デバッグ出力（0=無効）
    sim_extra: "Optional[Dict[str, Any]]" = None,  # 追加情報（elapsed_k等）を返す用
) -> "Tuple[str, bool, float, float | None]":
    """1トレードをバー順にシミュレート（v3: precomputed 15M/1H 実体使用）。

    決済順序:
      1. ストップ: 5分足バー内安値/高値でストップに触れたら即損切
      2. 4Hネックライン到達で半値利確（残り半分継続）
      3. 半値利確後: 前回15M実体突破 → 即決済（急落/急騰対策）
      4. 半値利確後: 前回1H実体突破 → 即決済
      5. 1H3本(36バー)経過後: 前回5M実体突破 → 決済
      6. 4H3本(144バー)経過後: 前回15M実体突破でも決済（phase2）

    Returns:
        (exit_type, took_half, exit_price, half_price)
        exit_type: stopped | phase1_5m | phase1_15m | phase2_15m | phase2_1h | timeout
    """
    stop_dist = atr_val * stop_mult
    took_half = False
    half_price: "float | None" = None
    n = len(close_5m)

    # デバッグ集計
    dbg_bars_after_half = 0
    dbg_bars_with_bl15 = 0
    dbg_bars_c_triggered_bl15 = 0
    dbg_last_bl15: "float | None" = None
    dbg_last_c: "float | None" = None

    half_bar_k: "int | None" = None

    for k in range(1, min(max_bars, n - idx)):
        i = idx + k
        if i >= n:
            break

        lo = float(low_5m.iloc[i])  if low_5m  is not None and i < len(low_5m)  else float(close_5m.iloc[i])
        hi = float(high_5m.iloc[i]) if high_5m is not None and i < len(high_5m) else float(close_5m.iloc[i])
        c  = float(close_5m.iloc[i])

        # ── 1) ストップ（最優先: バー内High/Lowで判定） ──────────────────────
        if direction == "L":
            if lo <= price - stop_dist:
                if sim_extra is not None:
                    sim_extra["elapsed_k"] = k
                return "stopped", took_half, price - stop_dist, half_price
        else:
            if hi >= price + stop_dist:
                if sim_extra is not None:
                    sim_extra["elapsed_k"] = k
                return "stopped", took_half, price + stop_dist, half_price

        # ── 2) 4Hネックライン到達 → 半値利確 ────────────────────────────────
        if not took_half:
            if direction == "L" and hi >= entry_4h_high:
                took_half = True
                half_price = c
                half_bar_k = k
            elif direction == "S" and lo <= entry_4h_low:
                took_half = True
                half_price = c
                half_bar_k = k

        # 半値利確前はスキップ
        if not took_half or half_bar_k is None:
            continue

        # ── 前回バー実体取得（precomputed series から iloc 直接参照） ─────────
        def _safe_iloc(ser: "pd.Series | None", pos: int) -> "float | None":
            if ser is None or pos >= len(ser):
                return None
            v = ser.iloc[pos]
            return float(v) if pd.notna(v) else None

        bl_15 = _safe_iloc(prev_bl_15_s, i)
        bh_15 = _safe_iloc(prev_bh_15_s, i)
        bl_1h = _safe_iloc(prev_bl_1h_s, i)
        bh_1h = _safe_iloc(prev_bh_1h_s, i)

        # 前回5M実体
        prev_bl_5 = prev_bh_5 = None
        if open_5m is not None and i >= 1:
            prev_bl_5 = min(float(open_5m.iloc[i - 1]), float(close_5m.iloc[i - 1]))
            prev_bh_5 = max(float(open_5m.iloc[i - 1]), float(close_5m.iloc[i - 1]))

        # ── デバッグ出力（最初の N バーのみ） ────────────────────────────────
        if debug_body_n > 0 and dbg_bars_after_half < debug_body_n:
            ts = close_5m.index[i]
            print(
                f"  [body_dbg trade={trade_id} k={k} dir={direction}] "
                f"ts={ts} c={c:.5f} | "
                f"bl_15={bl_15} bh_15={bh_15} | "
                f"bl_1h={bl_1h} bh_1h={bh_1h}"
            )

        dbg_bars_after_half += 1
        if direction == "L" and bl_15 is not None:
            dbg_bars_with_bl15 += 1
            dbg_last_bl15 = bl_15
            dbg_last_c = c
            if c < bl_15:
                dbg_bars_c_triggered_bl15 += 1
        elif direction == "S" and bh_15 is not None:
            dbg_bars_with_bl15 += 1
            dbg_last_bl15 = bh_15
            dbg_last_c = c
            if c > bh_15:
                dbg_bars_c_triggered_bl15 += 1

        # ── 3a) 前回15M実体突破 → 即決済（急落/急騰対策） ───────────────────
        if direction == "L":
            if bl_15 is not None and c < bl_15:
                return "phase1_15m", took_half, c, half_price
        else:
            if bh_15 is not None and c > bh_15:
                return "phase1_15m", took_half, c, half_price

        # ── 3b) 前回1H実体突破 → 即決済 ──────────────────────────────────────
        if direction == "L":
            if bl_1h is not None and c < bl_1h:
                return "phase2_1h", took_half, c, half_price
        else:
            if bh_1h is not None and c > bh_1h:
                return "phase2_1h", took_half, c, half_price

        # ── 4) 前回5M実体突破（v9: 半値利確後1H=12本の時間ゲートを復活） ─────
        # v5で撤廃した時間ゲートをphase1_5mのみ復活。
        # 理由: ゲートなしだと半値利確直後に5M実体(小)で即決済 → 15M実体が発動する前に終了
        #       15M実体決済0件/5M決済9件 → net -86K の主因。
        # 1H(12本)待機後は15M実体(3a)より先に発動しないため15Mと競合しない。
        PHASE1_5M_GATE = 12  # 1H = 5Mバー12本
        if half_bar_k is not None and k - half_bar_k >= PHASE1_5M_GATE:
            if direction == "L":
                if prev_bl_5 is not None and c < prev_bl_5:
                    return "phase1_5m", took_half, c, half_price
            else:
                if prev_bh_5 is not None and c > prev_bh_5:
                    return "phase1_5m", took_half, c, half_price

        # ── 5) 前回15M実体突破 phase2（v5: 4H3本経過の時間ゲート撤廃） ────────
        # phase1_15m(3a) が先に発動するため、ここは「3a をすり抜けたバーの追加保険」
        # 具体的には: bl_15 が NaN だったバーで c が新しい bl_15 を突破した場合など
        if direction == "L":
            if bl_15 is not None and c < bl_15:
                return "phase2_15m", took_half, c, half_price
        else:
            if bh_15 is not None and c > bh_15:
                return "phase2_15m", took_half, c, half_price

    # タイムアウト
    last_c = float(close_5m.iloc[min(idx + max_bars - 1, n - 1)]) if n > idx else price
    if debug_log is not None and took_half:
        debug_log.append(
            f"  [15m未発動] 半値利確後バー数={dbg_bars_after_half}, "
            f"前回15M実体ありバー数={dbg_bars_with_bl15}, 終値が実体突破バー数={dbg_bars_c_triggered_bl15}"
            + (
                f", 直近bl_15={dbg_last_bl15:.4f} c={dbg_last_c:.4f}"
                if dbg_last_bl15 is not None
                else ", bl_15=NaN多（境界未検出の可能性）"
            )
        )
    return "timeout", took_half, last_c, half_price


def _analyze_enhanced(
    df_multi: pd.DataFrame,
    entries_long: pd.Series,
    entries_short: pd.Series,
    stop_atr_multiplier: float = 1.3,
    use_5m_atr: bool = True,
    stop_cap_pips: "float | None" = 50.0,
    debug_print_first_n: int = 3,
    debug_15m_reason: bool = True,
    debug_reentry_reason: bool = True,
    debug_body_n: int = 5,   # 半値利確後 N バーのみ詳細body デバッグ（最初の3トレードのみ）
) -> "Dict[str, Any]":
    """強化版分析 v3: precomputed 15M/1H 実体 + reentry_used_since_stop リセット修正。"""
    times_long  = entries_long[entries_long].index
    times_short = entries_short[entries_short].index
    long_count  = len(times_long)
    short_count = len(times_short)
    total = long_count + short_count

    # ── 出来高スパイク ────────────────────────────────────────────────────────
    vol_5m   = df_multi.get("5M_Volume", pd.Series(0.0, index=df_multi.index))
    avg_vol_5 = vol_5m.rolling(5).mean()
    early_15x = early_18x = 0
    for t in list(times_long) + list(times_short):
        try:
            if t in vol_5m.index and t in avg_vol_5.index:
                cv, av = vol_5m.loc[t], avg_vol_5.loc[t]
                if pd.notna(cv) and pd.notna(av) and av > 0:
                    if cv > av * 1.5: early_15x += 1
                    if cv > av * 1.8: early_18x += 1
        except Exception:
            pass

    # ── 各TF Series 取得 ──────────────────────────────────────────────────────
    close_5m = df_multi.get("5M_Close")
    open_5m  = df_multi.get("5M_Open")

    low_5m = next((df_multi[k] for k in ("5M_Low", "5M_low", "5min_low") if k in df_multi.columns), None)
    high_5m= next((df_multi[k] for k in ("5M_High","5M_high","5min_high") if k in df_multi.columns), None)
    if low_5m  is None: low_5m  = close_5m
    if high_5m is None: high_5m = close_5m

    open_15m  = df_multi.get("15M_Open")
    close_15m = df_multi.get("15M_Close")
    high_15m  = next((df_multi[k] for k in ("15M_High","15M_high") if k in df_multi.columns), close_15m)
    low_15m   = next((df_multi[k] for k in ("15M_Low", "15M_low")  if k in df_multi.columns), close_15m)

    open_1h  = df_multi.get("1H_Open")
    close_1h = df_multi.get("1H_Close")

    open_4h  = df_multi.get("4H_Open")
    high_4h  = df_multi.get("4H_High")
    low_4h   = df_multi.get("4H_Low")

    atr_5m  = _calc_atr(high_5m, low_5m, close_5m, 14) if all(x is not None for x in [close_5m, high_5m, low_5m]) else None
    atr_15m = _calc_atr(high_15m, low_15m, close_15m, 14) if all(x is not None for x in [close_15m, high_15m, low_15m]) else None

    # ── 事前計算: 前回TFバー実体 (15M/1H) ───────────────────────────────────
    print("\n[v3] 前回15M実体を事前計算中...")
    prev_bl_15_s, prev_bh_15_s = _precompute_prev_body_series(open_15m, close_15m, "15M", debug=True)
    print("[v3] 前回1H実体を事前計算中...")
    prev_bl_1h_s, prev_bh_1h_s = _precompute_prev_body_series(open_1h,  close_1h,  "1H",  debug=True)

    # ── 事前計算: 4Hスイング高値/安値（v6修正の核心） ──────────────────────
    # 旧コードは high_4h.iloc[idx-N:idx].max() で「5Mバー N本のffillコピー」を参照→誤り
    # 新コード: 4Hバー境界を検出し「直近N本の完成済み4Hバー」のmax/minを展開
    print("[v7] 4Hスイング高値/安値を事前計算中...")
    NECK_4H_BARS = 20   # 直近20本の完成済み4Hバー（約80時間）
    _, _, bar4h_starts, bar4h_highs, bar4h_lows = _precompute_4h_swing(
        open_4h, high_4h, low_4h, n_bars=NECK_4H_BARS, debug=True
    )

    # ── 集計変数 ──────────────────────────────────────────────────────────────
    exit_half = exit_phase1_5m = exit_phase1_15m = exit_phase2_15m = exit_phase2_1h = exit_timeout = stopped = 0
    re_entry_count = re_entry_success = 0
    cumulative_profit_yen = cumulative_loss_yen = 0.0
    half_tp_pips_sum = half_tp_count = 0
    final_tp_pips_sum = final_tp_count = 0
    total_tp_pips_sum = total_tp_trade_count = 0
    stop_pips_sum = stop_count = 0
    # MaxDD計算用
    running_equity_yen = 0.0
    equity_peak_yen    = 0.0
    max_dd_yen         = 0.0

    REENTRY_WAIT_BARS = 2    # 10分（v5: 15分→10分 = 5Mバー2本）
    REENTRY_MAX_BARS  = 144  # 12時間以内（v5: 96→144 に拡大）
    DEDUP_SKIP_BARS   = 3    # 同一方向15分以内の重複シグナルを除去

    all_signals: "List[Tuple[str, pd.Timestamp]]" = (
        [("L", t) for t in times_long] + [("S", t) for t in times_short]
    )
    all_signals.sort(key=lambda x: x[1])

    # ── 重複シグナル除去（同一方向 DEDUP_SKIP_BARS 以内 → 最新1つだけ残す）──
    # 同じ押し目/戻りで連続シグナルが出た場合、直近（最新）エントリーを採用する。
    # 実装: 前から後ろをスキャンし、直後に同方向シグナルが DEDUP_SKIP_BARS 以内に
    #       存在する場合は「古い方」をスキップして新しい方を採用（最新優先）。
    def _get_bar_idx(ts: pd.Timestamp) -> int:
        if close_5m is None or ts not in close_5m.index:
            return -1
        _l = close_5m.index.get_loc(ts)
        return int(_l) if isinstance(_l, (int, __import__("numpy").integer)) else int(_l.start)

    _signal_bar_idxs = [_get_bar_idx(t) for _, t in all_signals]

    keep_mask = [True] * len(all_signals)
    skipped_dup_by_dir: "Dict[str, int]" = {"L": 0, "S": 0}
    for _i in range(len(all_signals)):
        if not keep_mask[_i]:
            continue
        dir_i = all_signals[_i][0]
        idx_i = _signal_bar_idxs[_i]
        if idx_i < 0:
            continue
        for _j in range(_i + 1, len(all_signals)):
            idx_j = _signal_bar_idxs[_j]
            if idx_j < 0:
                continue
            gap_ij = idx_j - idx_i
            if gap_ij > DEDUP_SKIP_BARS:
                break
            if all_signals[_j][0] == dir_i and 0 <= gap_ij <= DEDUP_SKIP_BARS:
                # 古い方（_i）をスキップして新しい方（_j）を採用
                keep_mask[_i] = False
                skipped_dup_by_dir[dir_i] += 1
                break

    filtered_signals = [(d, t) for keep, (d, t) in zip(keep_mask, all_signals) if keep]
    skipped_dup_total = len(all_signals) - len(filtered_signals)
    print(f"\n[v4] 重複シグナル除去: {skipped_dup_total}件スキップ "
          f"(L={skipped_dup_by_dir['L']} / S={skipped_dup_by_dir['S']}) "
          f"→ 残り {len(filtered_signals)} 件")

    prev_entry_idx_by_dir: "Dict[str, int]"          = {"L": -99, "S": -99}
    last_exit_type_by_dir: "Dict[str, str | None]"   = {"L": None, "S": None}
    reentry_used_since_stop: "Dict[str, bool]"       = {"L": False, "S": False}

    def _safe_atr(ser, ts):
        if ser is None or ts not in ser.index:
            return None
        v = ser.loc[ts]
        try:
            return float(v.iloc[0]) if isinstance(v, pd.Series) else float(v)
        except (TypeError, ValueError):
            return None

    atr_series_for_stop = atr_5m if use_5m_atr else atr_15m
    atr_tf_name = "5M" if use_5m_atr else "15M"

    trade_counter = 0
    trade_trace_log: "List[Dict[str, Any]]" = []
    duplicate_warnings: "List[str]" = []
    debug_15m_log: "List[str]" = []
    reentry_detail_log: "List[str]" = []   # 再エントリー発動詳細ログ
    reentry_fail_reasons: "Dict[str, int]" = {
        "prev_not_stopped": 0, "gap_too_small": 0,
        "gap_too_large": 0, "reentry_already_used": 0,
    }
    stopped_detail_log: "List[Dict[str, Any]]" = []   # 損切詳細（E案）

    for direction, t in filtered_signals:
        if close_5m is None or t not in close_5m.index:
            continue
        _loc = close_5m.index.get_loc(t)
        idx   = int(_loc) if isinstance(_loc, (int, __import__("numpy").integer)) else int(_loc.start)
        price = float(close_5m.iloc[idx])

        # ── ATR計算（ネックラインfallbackに先立って実行） ────────────────────
        atr_val     = _safe_atr(atr_series_for_stop, t)
        atr_5m_val  = _safe_atr(atr_5m, t)
        atr_15m_val = _safe_atr(atr_15m, t)

        if atr_val is None or atr_val <= 0:
            atr_val = price * 0.005  # fallback ≈ 50pips

        # ── G案: ATRフィルタ（異常ボラはエントリーしない） ────────────────────
        ATR_SKIP_PIPS = 30.0
        atr_5m_pips = (atr_5m_val or 0.0) * 100
        if atr_5m_pips > ATR_SKIP_PIPS:
            print(f"  [ATRフィルタ] dir={direction} ts={t} "
                  f"ATR_5M={atr_5m_pips:.1f}pips > {ATR_SKIP_PIPS}pips -> skip")
            prev_entry_idx_by_dir[direction] = idx   # 位置だけ更新しておく
            continue

        stop_dist_raw = atr_val * stop_atr_multiplier
        if stop_cap_pips is not None and stop_cap_pips > 0:
            cap_price = stop_cap_pips * 0.01
            stop_dist = min(stop_dist_raw, cap_price)
        else:
            stop_dist = stop_dist_raw

        # ── ネックライン: 方向性 + 最小距離フィルタ（v8） ──────────────────────
        # MIN_NECK_DIST = stop_dist * 2.0: ストップの2倍以上離れたネックのみ採用
        # → R:R = 0.21:1 の逆ザヤを解消するための最低ライン確保
        MIN_NECK_DIST = stop_dist * 2.0
        neck_debug = (trade_counter < debug_print_first_n)
        entry_4h_high, entry_4h_low = _get_directional_neckline(
            bar4h_starts, bar4h_highs, bar4h_lows,
            idx, direction, price, atr_val,
            n_bars=NECK_4H_BARS,
            min_dist=MIN_NECK_DIST,
            debug=neck_debug,
        )

        # ネックライン詳細ログ（最初の N 件のみ）
        if trade_counter < debug_print_first_n:
            print(f"\n[ネックライン v8 #{trade_counter+1}] dir={direction} ts={t} entry={price:.3f}")
            print(f"  MIN_NECK_DIST={MIN_NECK_DIST*100:.1f}pips (stop_dist*2.0)")
            print(f"  方向性ネック(直近{NECK_4H_BARS}本): high={entry_4h_high:.3f} / low={entry_4h_low:.3f}")
            dist_h = (entry_4h_high - price) * 100
            dist_l = (price - entry_4h_low)  * 100
            print(f"  採用ネックライン距離: 上={dist_h:.1f}pips / 下={dist_l:.1f}pips")
            atr_pips   = atr_val * 100
            stop_level = price - stop_dist if direction == "L" else price + stop_dist
            print(f"[ストップ計算 #{trade_counter+1}] direction={direction} entry={price:.3f} ts={t}")
            print(f"  ATR基準: **{atr_tf_name}** ATR(14) = {atr_val:.5f} ({atr_pips:.1f} pips)")
            if atr_5m_val:  print(f"  参考: 5M  ATR(14) = {atr_5m_val:.5f} ({atr_5m_val*100:.1f} pips)")
            if atr_15m_val: print(f"  参考: 15M ATR(14) = {atr_15m_val:.5f} ({atr_15m_val*100:.1f} pips)")
            print(f"  stop_dist = {stop_dist:.5f} ({stop_dist*100:.1f} pips)"
                  + (" [キャップ適用]" if stop_cap_pips and stop_dist < stop_dist_raw else ""))
            print(f"  最終 stop_level = {stop_level:.3f}")
        trade_counter += 1

        # 重複エントリー検出
        gap_from_prev = idx - prev_entry_idx_by_dir[direction]
        if 0 < gap_from_prev <= 3 and prev_entry_idx_by_dir[direction] >= 0:
            duplicate_warnings.append(
                f"  trade_id={len(trade_trace_log)} dir={direction} ts={t}: 前回から{gap_from_prev}本（重複疑い）"
            )

        atr_val_for_sim = stop_dist / stop_atr_multiplier if stop_atr_multiplier != 0 else atr_val

        # 再エントリー判定
        prev_was_stopped = last_exit_type_by_dir[direction] == "stopped"
        is_reentry_candidate = (
            prev_was_stopped
            and not reentry_used_since_stop[direction]
            and REENTRY_WAIT_BARS <= gap_from_prev <= REENTRY_MAX_BARS
        )
        if debug_reentry_reason and prev_was_stopped and not is_reentry_candidate:
            if reentry_used_since_stop[direction]:
                reentry_fail_reasons["reentry_already_used"] += 1
            elif gap_from_prev < REENTRY_WAIT_BARS:
                reentry_fail_reasons["gap_too_small"] += 1
            elif gap_from_prev > REENTRY_MAX_BARS:
                reentry_fail_reasons["gap_too_large"] += 1
        if is_reentry_candidate:
            re_entry_count += 1
            reentry_detail_log.append(
                f"  re-entry: trade_id={len(trade_trace_log)} dir={direction} "
                f"ts={t} entry={price:.3f} gap={gap_from_prev}本({gap_from_prev*5}分後)"
            )

        # トレードシミュレーション（v3: precomputed 実体使用）
        sim_debug: "List[str]" = [] if debug_15m_reason else []
        body_dbg = debug_body_n if trade_counter <= debug_print_first_n else 0
        sim_extra: "Dict[str, Any]" = {}

        exit_type, took_half, exit_price, half_price = _simulate_trade(
            direction, idx, price, entry_4h_high, entry_4h_low,
            atr_val_for_sim,
            close_5m, low_5m, high_5m, open_5m,
            prev_bl_15_s, prev_bh_15_s,
            prev_bl_1h_s, prev_bh_1h_s,
            max_bars=96,
            stop_mult=stop_atr_multiplier,
            debug_log=sim_debug,
            trade_id=len(trade_trace_log),
            debug_body_n=body_dbg,
            sim_extra=sim_extra,
        )
        if sim_debug:
            debug_15m_log.append(f"trade_id={len(trade_trace_log)} dir={direction} exit={exit_type}:")
            debug_15m_log.extend(sim_debug)

        trade_trace_log.append({
            "trade_id": len(trade_trace_log),
            "direction": direction,
            "entry_ts": t,
            "entry_idx": idx,
            "exit_type": exit_type,
            "took_half": took_half,
            "gap_from_prev": gap_from_prev,
        })

        # 損益計算（1Lot = 10万通貨、USDJPY 1pip = 0.01 → 1pip = 1000円）
        half_pips  = 0.0
        final_pips = 0.0
        if took_half and half_price is not None:
            half_pips = (half_price - price) * 100 if direction == "L" else (price - half_price) * 100
            if half_pips > 0:
                half_tp_pips_sum += half_pips
                half_tp_count    += 1

        final_pips = (exit_price - price) * 100 if direction == "L" else (price - exit_price) * 100
        if final_pips > 0:
            final_tp_pips_sum += final_pips
            final_tp_count    += 1

        if exit_type == "stopped":
            stop_pips_sum += abs(final_pips)
            stop_count    += 1
            neck_dist = (entry_4h_high - price) * 100 if direction == "L" else (price - entry_4h_low) * 100
            atr_5m_pips = (atr_5m_val or 0.0) * 100
            stopped_detail_log.append({
                "trade_id": len(trade_trace_log),
                "direction": direction,
                "ts": t,
                "entry": price,
                "stop_price": exit_price,
                "stop_pips": abs(final_pips),
                "atr_5m_pips": atr_5m_pips,
                "atr_15m_pips": (atr_15m_val or 0.0) * 100,
                "neck_dist_pips": neck_dist,
                "took_half": took_half,
                "elapsed_k": sim_extra.get("elapsed_k", -1),
                "capped": (stop_cap_pips is not None and abs(final_pips) >= stop_cap_pips - 0.1),
            })

        size_half  = 0.5 if (took_half and half_price is not None) else 0.0
        size_final = 0.5 if (took_half and half_price is not None) else 1.0
        yen_pnl = (half_pips * size_half + final_pips * size_final) * 1000
        if yen_pnl > 0:
            cumulative_profit_yen += yen_pnl
        else:
            cumulative_loss_yen   += yen_pnl

        # MaxDD計算（トレード完了ごとに更新）
        running_equity_yen += yen_pnl
        if running_equity_yen > equity_peak_yen:
            equity_peak_yen = running_equity_yen
        dd = equity_peak_yen - running_equity_yen
        if dd > max_dd_yen:
            max_dd_yen = dd

        # 決済種別カウント
        if exit_type == "stopped":
            stopped += 1
        elif exit_type == "phase1_5m":
            exit_phase1_5m += 1
            if took_half: exit_half += 1
        elif exit_type == "phase1_15m":
            exit_phase1_15m += 1
            if took_half: exit_half += 1
        elif exit_type == "phase2_15m":
            exit_phase2_15m += 1
            if took_half: exit_half += 1
        elif exit_type == "phase2_1h":
            exit_phase2_1h += 1
            if took_half: exit_half += 1
        elif exit_type == "timeout":
            exit_timeout += 1

        trade_total_pips = half_pips * size_half + final_pips * size_final
        if trade_total_pips > 0:
            total_tp_pips_sum    += trade_total_pips
            total_tp_trade_count += 1

        # 再エントリー結果
        if is_reentry_candidate:
            outcome = "成功" if exit_type != "stopped" else "損切"
            reentry_detail_log.append(
                f"    → 結果: {exit_type} ({outcome}) took_half={took_half}"
            )
            if exit_type != "stopped":
                re_entry_success += 1
            reentry_used_since_stop[direction] = True

        prev_entry_idx_by_dir[direction] = idx
        last_exit_type_by_dir[direction] = exit_type

        # ── v3 バグ修正: 損切り発生時に reentry_used_since_stop をリセット ──
        # 旧コードではリセット漏れにより、再エントリー後に新たな損切りが発生しても
        # reentry_used_since_stop = True のままで次の再エントリーが永久に不可だった。
        if exit_type == "stopped":
            reentry_used_since_stop[direction] = False

    survival_rate  = (total - stopped) / total * 100 if total > 0 else 0.0
    avg_half_tp    = half_tp_pips_sum  / half_tp_count    if half_tp_count    > 0 else 0.0
    avg_final_tp   = final_tp_pips_sum / final_tp_count   if final_tp_count   > 0 else 0.0
    avg_total_tp   = total_tp_pips_sum / total_tp_trade_count if total_tp_trade_count > 0 else 0.0
    avg_stop_pips  = stop_pips_sum     / stop_count        if stop_count       > 0 else 0.0
    exit_15m_body  = exit_phase1_15m + exit_phase2_15m
    exit_other     = exit_phase1_5m  + exit_phase2_1h + exit_timeout

    return {
        "total": total, "long": long_count, "short": short_count,
        "early_15x": early_15x, "early_18x": early_18x,
        "exit_half": exit_half,
        "exit_phase1_5m": exit_phase1_5m, "exit_phase1_15m": exit_phase1_15m,
        "exit_phase2_15m": exit_phase2_15m, "exit_phase2_1h": exit_phase2_1h,
        "exit_15m_body": exit_15m_body, "exit_other": exit_other,
        "exit_timeout": exit_timeout,
        "stopped": stopped, "survival_rate": survival_rate,
        "re_entry_count": re_entry_count, "re_entry_success": re_entry_success,
        "cumulative_profit_yen": cumulative_profit_yen,
        "cumulative_loss_yen":   cumulative_loss_yen,
        "net_pnl_yen": cumulative_profit_yen + cumulative_loss_yen,
        "max_dd_yen": max_dd_yen,
        "avg_half_tp_pips": avg_half_tp, "avg_final_tp_pips": avg_final_tp,
        "avg_total_tp_pips": avg_total_tp, "avg_stop_pips": avg_stop_pips,
        "skipped_dup_total": skipped_dup_total,
        "skipped_dup_by_dir": skipped_dup_by_dir,
        "trade_trace_log": trade_trace_log,
        "duplicate_warnings": duplicate_warnings,
        "debug_15m_log": debug_15m_log,
        "reentry_detail_log": reentry_detail_log,
        "reentry_fail_reasons": reentry_fail_reasons,
        "stopped_detail_log": stopped_detail_log,
    }


def _analyze_conventional(df_multi: pd.DataFrame, entries_long: pd.Series) -> "Dict[str, Any]":
    """従来版: ロングのみ・旧決済（%閾値）。"""
    times  = entries_long[entries_long].index
    total  = len(times)
    close_5m = df_multi.get("5M_Close")
    quick, mid, long_ex = 0, 0, 0
    if close_5m is not None and total > 0:
        for t in times:
            try:
                idx   = close_5m.index.get_loc(t)
                price = close_5m.iloc[idx]
                end_idx = min(idx + 10, len(close_5m) - 1)
                rng = close_5m.iloc[idx:end_idx + 1]
                if len(rng) > 1:
                    mv = max(
                        abs(rng.max() - price) / price * 100,
                        abs(rng.min() - price) / price * 100,
                    )
                    if mv < 0.1:   quick   += 1
                    elif mv < 0.3: mid     += 1
                    else:          long_ex += 1
            except Exception:
                quick += 1
    return {
        "total": total, "long": total, "short": 0,
        "exit_5m_down": quick, "exit_4h_mid": mid, "exit_15m_down": long_ex,
    }


def run_all_patterns() -> None:
    print("[INFO] データ読み込み中…")
    df_multi = load_data()
    print(f"[INFO] データ形状: {df_multi.shape}")
    print(f"[INFO] カラム: {list(df_multi.columns)}")

    out = mtf_minato_short_v2(df_multi, session="all")
    if isinstance(out, tuple) and len(out) == 2:
        entries_long, entries_short = out
    else:
        entries_long  = out if isinstance(out, pd.Series) else pd.Series(False, index=df_multi.index)
        entries_short = pd.Series(False, index=df_multi.index)

    enhanced = _analyze_enhanced(
        df_multi, entries_long, entries_short,
        stop_atr_multiplier=1.3,
        use_5m_atr=True,
        stop_cap_pips=50.0,
        debug_print_first_n=3,
        debug_15m_reason=True,
        debug_reentry_reason=True,
        debug_body_n=5,
    )
    conventional = _analyze_conventional(df_multi, entries_long)

    print("\n" + "=" * 70)
    print("  強化版 v5（時間ゲート撤廃 + REENTRY12H + 待機10分 + MaxDD）")
    print("=" * 70)
    e = enhanced
    dup_by = e.get("skipped_dup_by_dir", {"L": 0, "S": 0})
    print(f"  重複スキップ: 計{e.get('skipped_dup_total', 0)}件 (L={dup_by['L']} / S={dup_by['S']})")
    print(f"  総シグナル数: {e['total']} (ロング: {e['long']} / ショート: {e['short']})")
    if e["total"] > 0:
        print(f"  先行エントリー(1.5倍): {e['early_15x']} ({e['early_15x']/e['total']*100:.1f}%)")
        print(f"  先行エントリー(1.8倍): {e['early_18x']} ({e['early_18x']/e['total']*100:.1f}%)")
    print(f"  ストップ損切件数: {e['stopped']} / 生存率: {e['survival_rate']:.1f}%")
    print(f"  決済内訳:")
    print(f"    半値利確あり:       {e['exit_half']}")
    print(f"    15M実体下抜け:      {e['exit_15m_body']} (phase1={e['exit_phase1_15m']} / phase2={e['exit_phase2_15m']})")
    print(f"    1H実体下抜け:       {e['exit_phase2_1h']}")
    print(f"    5M実体(1H3本後):    {e['exit_phase1_5m']}")
    print(f"    タイムアウト:       {e['exit_timeout']}")
    reentry_pct = (f" ({e['re_entry_success']/e['re_entry_count']*100:.1f}%成功)"
                   if e['re_entry_count'] > 0 else "")
    print(f"  再エントリー回数: {e['re_entry_count']} / 成功: {e['re_entry_success']}{reentry_pct}")
    print(f"  累積損益(1Lot円): 利益={e['cumulative_profit_yen']:,.0f} / 損失={e['cumulative_loss_yen']:,.0f} / ネット={e['net_pnl_yen']:,.0f}")
    net = e['net_pnl_yen']
    max_dd = e.get('max_dd_yen', 0)
    dd_pct = (max_dd / (net + max_dd) * 100) if (net + max_dd) > 0 else 0
    print(f"  MaxDD(1Lot円):   {max_dd:,.0f}  ({dd_pct:.1f}% of peak equity)")
    print(f"  平均利確Pips: 半値={e['avg_half_tp_pips']:.1f} / 最終={e['avg_final_tp_pips']:.1f} / 全体={e['avg_total_tp_pips']:.1f}")
    print(f"  平均損切Pips: {e['avg_stop_pips']:.1f}")

    # 15M実体下抜けデバッグ
    if e["exit_15m_body"] == 0 and e["total"] > 0:
        print("\n  【15M実体下抜け = 0件】デバッグ情報:")
        for line in e.get("debug_15m_log", [])[:20]:
            print("   ", line)
        if not e.get("debug_15m_log"):
            print("    (半値利確トレードが0件、またはタイムアウト前に全決済)")
    else:
        print(f"\n  [OK] 15M実体下抜け発動: {e['exit_15m_body']}件")

    # 再エントリー詳細ログ
    rr = e.get("reentry_fail_reasons", {})
    detail = e.get("reentry_detail_log", [])
    if e["re_entry_count"] > 0:
        print(f"\n  【再エントリー発動詳細】:")
        for line in detail:
            print(line)
    else:
        print(f"\n  【再エントリー = 0回】失敗内訳:")
        print(f"    gap_too_small (8時間未満の15分未満): {rr.get('gap_too_small', 0)}")
        print(f"    gap_too_large (8時間超):             {rr.get('gap_too_large', 0)}")
        print(f"    reentry_already_used:                {rr.get('reentry_already_used', 0)}")
        if rr.get("gap_too_large", 0) > 0:
            print(f"  → gap_too_large が残存: REENTRY_MAX_BARS=96本(8時間)でも不足の可能性")

    # ── 損切詳細ログ（E案） ────────────────────────────────────────────────
    sdl = e.get("stopped_detail_log", [])
    if sdl:
        print(f"\n  【損切トレード詳細 全{len(sdl)}件】")
        atr_high_count   = sum(1 for s in sdl if s["atr_5m_pips"] > 30)
        stop_l_count     = sum(1 for s in sdl if s["direction"] == "L")
        stop_s_count     = sum(1 for s in sdl if s["direction"] == "S")
        preneck_count    = sum(1 for s in sdl if not s["took_half"])
        for s in sdl:
            cap_mark = "[CAP]" if s["capped"] else ""
            half_mark = "(半値後)" if s["took_half"] else "(ネック未到達)"
            elapsed_str = f"{s['elapsed_k']}本" if s['elapsed_k'] >= 0 else "?"
            print(
                f"  [損切 #{s['trade_id']}] dir={s['direction']} ts={s['ts']}\n"
                f"    entry={s['entry']:.3f}  stop={s['stop_price']:.3f}  "
                f"損切={s['stop_pips']:.1f}pips {cap_mark}\n"
                f"    ATR_5M={s['atr_5m_pips']:.1f}pips  ATR_15M={s['atr_15m_pips']:.1f}pips"
                + ("  ← 異常値" if s["atr_5m_pips"] > 30 else "") + "\n"
                f"    ネックライン距離={s['neck_dist_pips']:.1f}pips  "
                f"経過={elapsed_str}  {half_mark}"
            )
        print(f"\n  【損切サマリー】")
        print(f"    ATR_5M > 30pips のトレード: {atr_high_count}件")
        print(f"    損切 L/S 内訳: L={stop_l_count} / S={stop_s_count}")
        print(f"    ネック到達前に損切: {preneck_count}件 / 半値後に損切: {len(sdl)-preneck_count}件")

    # 従来版比較
    print("\n" + "=" * 70)
    print("  従来版（ロングのみ・旧決済）")
    print("=" * 70)
    c = conventional
    print(f"  総シグナル数: {c['total']}")
    print(f"  決済: 5分ダウ崩れ={c['exit_5m_down']} / 4H半値={c['exit_4h_mid']} / 15分ダウ崩れ={c['exit_15m_down']}")

    # Markdown 比較表
    print("\n" + "=" * 70)
    print("  比較テーブル (v3 → v4)")
    print("=" * 70)
    inc = ((e["total"] / c["total"] - 1) * 100) if c["total"] > 0 else 0
    print(f"""
| 項目 | 従来版 | 強化版v4 |
|------|--------|----------|
| 元シグナル数 | {c['total']} | (重複除去前) |
| 重複スキップ | - | {e.get('skipped_dup_total', 0)}件 |
| 採用シグナル数 | {c['total']} | {e['total']} ({inc:+.1f}%) |
| ロング/ショート | {c['long']}/0 | {e['long']}/{e['short']} |
| ストップ損切 | - | {e['stopped']}件 |
| 生存率 | - | {e['survival_rate']:.1f}% |
| 15M実体下抜け | - | {e['exit_15m_body']}件 |
| 1H実体下抜け | - | {e['exit_phase2_1h']}件 |
| 5M実体(1H3本後) | - | {e['exit_phase1_5m']}件 |
| タイムアウト | - | {e['exit_timeout']}件 |
| 再エントリー | - | {e['re_entry_count']}回 ← v5: 12H/待機10分 |
| 平均損切Pips | - | {e['avg_stop_pips']:.1f} |
| 平均利確Pips(全体) | - | {e['avg_total_tp_pips']:.1f} |
| 累積利益(1Lot円) | - | {e['cumulative_profit_yen']:,.0f} |
| 累積損失(1Lot円) | - | {e['cumulative_loss_yen']:,.0f} |
| ネット損益(1Lot円) | - | {e['net_pnl_yen']:,.0f} |
| MaxDD(1Lot円) | - | {e.get('max_dd_yen',0):,.0f} |
| 15M実体(time gate撤廃) | - | {e['exit_15m_body']}件 ← v5変化点 |
| phase2発動 | - | {e['exit_phase2_15m']}件 |
| 比較テーブル | v4→v5 | 待機10分/12H/ゲート撤廃 |
""")
    print("=" * 70)
    print("  分析完了 (v5)")
    print("=" * 70)
    print("\n保存して python src/Simple_Backtest.py で実行！")
    print("再エントリー回数（詳細含む）、phase2件数、生存率、ネット損益、MaxDD、平均利確Pipsを教えてね。")


if __name__ == "__main__":
    run_all_patterns()
