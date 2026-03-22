"""structure_plotter.py — 4H+1H 構造確認プロット生成スクリプト（#019）。

目的:
  4H ネック越え確定イベントを全件スキャンし
  LONG / SHORT それぞれの「4H+1H 構造確認プロット」を
  自動生成・保存する。

  15M / 5M ロジックは一切使わない。
  上位足構造の視覚確認専用。

実行方法:
  python src/structure_plotter.py

出力:
  logs/structure_plots/YYYYMMDD_HHMM_{LONG|SHORT}_4H1H_structure.png
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Windows cp932 端末でも日本語・特殊文字を出力できるよう UTF-8 に強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.base_scanner import _load_data
from src.swing_detector import (
    detect_swing_highs,
    detect_swing_lows,
    get_direction_4h,
    get_nearest_swing_high,
    get_nearest_swing_low,
)
from src.plotter import plot_4h_1h_structure


# ── 定数 ──────────────────────────────────────────────────────
N_4H_SWING            = 5     # 4H Swing 検出 n値（推奨値）
N_1H_SWING            = 3     # 1H Swing 検出 n値（推奨値）
LOOKBACK_4H_SWING     = 100   # 4H Swing 検索幅（#015確定値）
LOOKBACK_1H_SWING     = 240   # 1H Swing 検索幅（10日分 = 240本）
WARMUP_BARS           = 1728  # 5M ウォームアップ（#012確定値）
MIN_EVENT_INTERVAL_1H = 24    # 同一方向イベントの最小間隔（1H bars = 24時間）
NECK_BREAK_CONFIRM    = True  # 確定足（close基準）でネック越え判定

OUTPUT_DIR = "logs/structure_plots/"


# ── スキャン ──────────────────────────────────────────────────

def scan_4h_neck_breaks(
    df_1h_full: pd.DataFrame,
    df_4h_full: pd.DataFrame,
) -> list[dict]:
    """4H ネック越え確定イベントを全件スキャンする。

    検出条件（LONG）:
      ① get_direction_4h() == 'LONG'（4H上昇ダウ確認）
      ② 直前 1H Close <= neck_4h（ネック未越え）
      ③ 現在 1H Close >  neck_4h（ネック越え確定）
      ④ 1H SH 切り上がり: sh_1h[-1] > sh_1h[-2]（HH）
      ⑤ 1H SL 切り上がり: sl_1h[-1] > sl_1h[-2]（HL）

    SHORT は上記の対称（4H SL 下抜け + 1H LH+LL）。

    Returns:
        イベントリスト:
          [{
            'time'       : pd.Timestamp,
            'direction'  : 'LONG' or 'SHORT',
            'neck_4h'    : float,
            'sh_4h_list' : list[tuple],
            'sl_4h_list' : list[tuple],
            'sh_1h_list' : list[tuple],
            'sl_1h_list' : list[tuple],
            '4h_trend_ok': bool,
            '1h_trend_ok': bool,
          }, ...]
    """
    ts_4h = df_4h_full.index.values
    ts_1h = df_1h_full.index.values
    n_1h  = len(df_1h_full)

    # ウォームアップ: 5M 1728本 → 1H 144本
    warmup_1h = WARMUP_BARS // 12

    last_event_idx: dict[str, int] = {"LONG": -9999, "SHORT": -9999}
    events: list[dict] = []

    skip_none      = 0
    skip_no_neck   = 0
    skip_no_break  = 0
    skip_1h_trend  = 0
    skip_interval  = 0
    skip_no_swing  = 0

    print(f"  [INFO] 1H スキャン開始: {n_1h} 本（ウォームアップ {warmup_1h} 本スキップ）...")

    for i in range(warmup_1h, n_1h):
        ts_now = ts_1h[i]

        # 対応する 4H インデックス
        idx_4h = int(np.searchsorted(ts_4h, ts_now, side="right")) - 1
        if idx_4h < N_4H_SWING * 2 + 2:
            continue

        # ── ① 4H 方向判定 ──
        direction = get_direction_4h(
            df_4h_full["High"], df_4h_full["Low"],
            current_idx=idx_4h, n=N_4H_SWING, lookback=LOOKBACK_4H_SWING,
        )
        if direction == "NONE":
            skip_none += 1
            continue

        # ── 4H ネック（最安打確認前に計算: 高コスト処理を最小化）──
        if direction == "LONG":
            neck_4h = get_nearest_swing_high(
                df_4h_full["High"], idx_4h, n=N_4H_SWING, lookback=LOOKBACK_4H_SWING,
            )
        else:
            neck_4h = get_nearest_swing_low(
                df_4h_full["Low"], idx_4h, n=N_4H_SWING, lookback=LOOKBACK_4H_SWING,
            )

        if neck_4h is None:
            skip_no_neck += 1
            continue

        # ── ②③ 1H Close ネック越え判定 ──
        close_curr = float(df_1h_full["Close"].iloc[i])
        close_prev = float(df_1h_full["Close"].iloc[i - 1])

        if direction == "LONG":
            neck_break = (close_prev <= neck_4h) and (close_curr > neck_4h)
        else:
            neck_break = (close_prev >= neck_4h) and (close_curr < neck_4h)

        if not neck_break:
            skip_no_break += 1
            continue

        # ── イベント間隔チェック ──
        if i - last_event_idx[direction] < MIN_EVENT_INTERVAL_1H:
            skip_interval += 1
            continue

        # ── 4H Swing リスト収集（プロット用）──
        w4_start = max(0, idx_4h - LOOKBACK_4H_SWING)
        win_4h_h = df_4h_full["High"].iloc[w4_start:idx_4h + 1]
        win_4h_l = df_4h_full["Low"].iloc[w4_start:idx_4h + 1]

        sh_4h_flags  = detect_swing_highs(win_4h_h, n=N_4H_SWING)
        sl_4h_flags  = detect_swing_lows(win_4h_l,  n=N_4H_SWING)
        sh_4h_series = win_4h_h[sh_4h_flags]
        sl_4h_series = win_4h_l[sl_4h_flags]

        if len(sh_4h_series) < 2 or len(sl_4h_series) < 2:
            skip_no_swing += 1
            continue

        sh_4h_list = [(ts, float(p)) for ts, p in sh_4h_series.items()]
        sl_4h_list = [(ts, float(p)) for ts, p in sl_4h_series.items()]

        # ── 1H Swing リスト収集（プロット + トレンド判定用）──
        w1_start = max(0, i - LOOKBACK_1H_SWING)
        win_1h_h = df_1h_full["High"].iloc[w1_start:i + 1]
        win_1h_l = df_1h_full["Low"].iloc[w1_start:i + 1]

        sh_1h_flags  = detect_swing_highs(win_1h_h, n=N_1H_SWING)
        sl_1h_flags  = detect_swing_lows(win_1h_l,  n=N_1H_SWING)
        sh_1h_series = win_1h_h[sh_1h_flags]
        sl_1h_series = win_1h_l[sl_1h_flags]

        sh_1h_list = [(ts, float(p)) for ts, p in sh_1h_series.items()]
        sl_1h_list = [(ts, float(p)) for ts, p in sl_1h_series.items()]

        # ── ④⑤ 1H トレンド整合 ──
        trend_1h_ok = False
        if len(sh_1h_list) >= 2 and len(sl_1h_list) >= 2:
            if direction == "LONG":
                trend_1h_ok = (
                    sh_1h_list[-1][1] > sh_1h_list[-2][1] and
                    sl_1h_list[-1][1] > sl_1h_list[-2][1]
                )
            else:
                trend_1h_ok = (
                    sh_1h_list[-1][1] < sh_1h_list[-2][1] and
                    sl_1h_list[-1][1] < sl_1h_list[-2][1]
                )

        if not trend_1h_ok:
            skip_1h_trend += 1
            continue

        # ── イベント記録 ──
        events.append({
            "time"        : df_1h_full.index[i],
            "direction"   : direction,
            "neck_4h"     : round(neck_4h, 3),
            "sh_4h_list"  : sh_4h_list,
            "sl_4h_list"  : sl_4h_list,
            "sh_1h_list"  : sh_1h_list,
            "sl_1h_list"  : sl_1h_list,
            "4h_trend_ok" : True,          # direction != NONE = 4H trend 確認済み
            "1h_trend_ok" : trend_1h_ok,
        })
        last_event_idx[direction] = i

    print(f"  [INFO] スキャン完了: {len(events)} 件検出")
    print(
        f"         スキップ: NONE方向={skip_none:,}, "
        f"ネック未取得={skip_no_neck}, ネック越え不成立={skip_no_break:,}, "
        f"1H Trend不整合={skip_1h_trend}, インターバル={skip_interval:,}, "
        f"4H Swing不足={skip_no_swing}"
    )
    return events


# ── メイン実行 ────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  structure_plotter.py — 4H+1H 構造確認プロット (#019)")
    print(f"  N_4H={N_4H_SWING}  N_1H={N_1H_SWING}")
    print(f"  LOOKBACK_4H={LOOKBACK_4H_SWING}  LOOKBACK_1H={LOOKBACK_1H_SWING}")
    print(f"  MIN_INTERVAL={MIN_EVENT_INTERVAL_1H}h  OUTPUT={OUTPUT_DIR}")
    print("=" * 60)

    t_start = time.time()

    # [1] データ読み込み
    print("\n[1] データ読み込み...")
    df_5m_raw, df_4h_full, _, df_1h_full = _load_data()
    print(
        f"    5M: {len(df_5m_raw):,} 本  "
        f"4H: {len(df_4h_full):,} 本  "
        f"1H: {len(df_1h_full):,} 本(native)"
    )
    print(f"    期間: {df_5m_raw.index[0]}  〜  {df_5m_raw.index[-1]}")

    # [2] スキャン
    print("\n[2] 4H ネック越えスキャン...")
    events = scan_4h_neck_breaks(df_1h_full, df_4h_full)

    if not events:
        print("    イベント: 0 件（条件成立なし）")
        print(f"\n[完了] 経過時間: {time.time() - t_start:.1f}s")
        print("=" * 60)
        return

    # [3] サマリー
    print("\n[3] 結果サマリー")
    long_events  = [e for e in events if e["direction"] == "LONG"]
    short_events = [e for e in events if e["direction"] == "SHORT"]
    print(f"    総件数: {len(events):4d}   LONG: {len(long_events):4d}   SHORT: {len(short_events):4d}")
    print(f"    4H trend OK: {sum(e['4h_trend_ok'] for e in events):4d} / {len(events)}")
    print(f"    1H trend OK: {sum(e['1h_trend_ok'] for e in events):4d} / {len(events)}")

    # [4] プロット生成
    print("\n[4] プロット生成...")
    out_dir = _repo_root / OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    long_count  = 0
    short_count = 0
    err_count   = 0

    for ev in events:
        ts_str    = ev["time"].strftime("%Y%m%d_%H%M")
        fname     = f"{ts_str}_{ev['direction']}_4H1H_structure.png"
        save_path = str(out_dir / fname)

        try:
            plot_4h_1h_structure(
                df_5m           = df_5m_raw,
                df_1h           = df_1h_full,
                df_4h           = df_4h_full,
                center_time     = ev["time"],
                direction       = ev["direction"],
                sh_4h_list      = ev["sh_4h_list"],
                sl_4h_list      = ev["sl_4h_list"],
                sh_1h_list      = ev["sh_1h_list"],
                sl_1h_list      = ev["sl_1h_list"],
                neck_4h         = ev["neck_4h"],
                neck_break_time = ev["time"],
                save_path       = save_path,
            )
            if ev["direction"] == "LONG":
                long_count += 1
            else:
                short_count += 1
        except Exception as ex:
            print(f"  [WARN] {fname}: {ex}")
            err_count += 1

    # [5] 最終レポート
    print(f"\n[完了]")
    print(f"    LONG  プロット生成: {long_count} 件")
    print(f"    SHORT プロット生成: {short_count} 件")
    if err_count:
        print(f"    エラー: {err_count} 件")
    print(f"    保存先: {out_dir}")
    print(f"    経過時間: {time.time() - t_start:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
