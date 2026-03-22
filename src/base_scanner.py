"""base_scanner.py — 4H + 15M 構造スキャナー（#015）。

バックテストに依存せず、4H 方向 + 15M レンジ構造の出現頻度・
パターン分布を調査する。エントリー判定（5M DB 確定）は行わない。

用途:
  - LOOKBACK_4H=100 で広い視野から 4H SH/SL を取得し、
    backtest.py (lookback=20) との乖離を検証する
  - IHS 出現比率が本当に高いかを定量確認する
  - 15M ネック・Fib グレード分布の基礎データ収集

実行:
  python src/base_scanner.py

出力:
  logs/base_scan/base_scan_YYYYMMDD_HHMMSS.csv
  logs/base_scan/plots/*.png  （PLOT_MODE='SAMPLE': ★★★ のみ）
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Windows cp932 端末でも日本語・特殊文字を出力できるよう UTF-8 に強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import (
    _build_direction_5m,
    get_nearest_swing_high,
    get_nearest_swing_low,
    get_nearest_swing_high_1h,
    get_nearest_swing_low_15m,
)
from src.entry_logic import (
    check_15m_range_low,
    MIN_4H_SWING_PIPS,
    NECK_TOLERANCE_PCT,
    PIP_SIZE,
)


# ── 定数 ──────────────────────────────────────────────────────
LOOKBACK_4H           = 100   # 4H SH/SL 検索幅（backtest.py は 20 → より広い視野）
LOOKBACK_15M          = 50    # 15M range_low lookback
N_DIRECTION_LOOKBACK  = 30    # 4H 方向判定の lookback（_build_direction_5m 用）
WARMUP_BARS           = 1728  # 5M ウォームアップ本数（120日相当）
RESCAN_INTERVAL_BARS  = 9     # 同一方向の重複検出防止（45分インターバル）
PLOT_MODE             = 'SAMPLE'  # 'ALL' | 'SAMPLE' | 'NONE'
                                  # SAMPLE: ★★★（fib_grade=2）のみ PNG 出力


# ── データ読み込み ────────────────────────────────────────────

def _load_data(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parquet データを読み込み、各 TF の DataFrame を返す。

    Returns:
        df_5m_raw, df_4h_full, df_15m_full, df_1h_full
    """
    df_path_obj = Path(df_path)
    if not df_path_obj.is_absolute():
        df_path_obj = _repo_root / df_path

    if not df_path_obj.exists():
        raise FileNotFoundError(
            f"データファイルが見つかりません: {df_path_obj}\n"
            f"  → python src/data_fetch.py を先に実行してください"
        )

    df_multi = pd.read_parquet(df_path_obj)

    if not isinstance(df_multi.index, pd.DatetimeIndex):
        df_multi.index = pd.DatetimeIndex(df_multi.index)

    if hasattr(df_multi.index, "tz") and df_multi.index.tz is not None:
        df_multi.index = df_multi.index.tz_convert("Asia/Tokyo")
    else:
        df_multi.index = df_multi.index.tz_localize("UTC").tz_convert("Asia/Tokyo")

    # TF ごとに ffill
    tf_prefixes = ["5M", "15M", "1H", "4H", "D"]
    processed_dfs = []
    for prefix in tf_prefixes:
        cols = [c for c in df_multi.columns if c.startswith(f"{prefix}_")]
        if cols:
            processed_dfs.append(df_multi[cols].copy().ffill())
    df_multi = pd.concat(processed_dfs, axis=1)

    # 5M raw
    df_5m_raw = df_multi[["5M_High", "5M_Low", "5M_Open", "5M_Close"]].rename(
        columns={"5M_High": "High", "5M_Low": "Low",
                 "5M_Open": "Open", "5M_Close": "Close"}
    )

    # 4H full（5M → resample）— backtest.py と同じ方式
    df_4h_full = df_5m_raw.resample("4h").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()

    # 15M full（5M → resample）
    df_15m_full = df_5m_raw.resample("15min").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()

    # 1H full: parquet ネイティブデータ使用（resample 不使用）
    _df_1h_raw = df_multi[["1H_Open", "1H_High", "1H_Low", "1H_Close"]].rename(
        columns={"1H_Open": "Open", "1H_High": "High", "1H_Low": "Low", "1H_Close": "Close"}
    )
    _df_1h_raw.index = _df_1h_raw.index.floor("1h")
    df_1h_full = _df_1h_raw[~_df_1h_raw.index.duplicated(keep="first")].dropna()

    return df_5m_raw, df_4h_full, df_15m_full, df_1h_full


# ── メインスキャン ────────────────────────────────────────────

def scan_4h_15m_base(
    df_5m_raw: pd.DataFrame,
    df_4h_full: pd.DataFrame,
    df_15m_full: pd.DataFrame,
    df_1h_full: pd.DataFrame,
) -> list[dict]:
    """4H 方向 + 15M レンジ構造イベントを全期間スキャンする。

    エントリー判定（5M DB）は行わない。
    4H SH/SL の存在と 15M レンジ構造の有無のみを確認する。

    Returns:
        events: list of dict
            {
              'timestamp'    : pd.Timestamp,
              'direction'    : 'LONG' | 'SHORT',
              'pattern'      : 'DB' | 'IHS' | 'ASCENDING' | ...,
              'neck_15m'     : float,
              'sh_4h'        : float,
              'sl_4h'        : float,
              'neck_1h'      : float | None,  # 1H SH（neck_4h として使用）
              'support_1h'   : float | None,  # 15M SL（サポートライン）
              'zone_valid'   : bool,           # neck_1h > support_1h
              'above_support': bool,           # sl_last >= support_1h
              'fib_grade'    : int,   # 0 / 1 (★★) / 2 (★★★) — #016 新判定
              'fib_618'      : float,
              'fib_50'       : float,
              'bar_idx'      : int,
            }
    """
    print("  [INFO] 4H 方向プリコンピュート中...")
    t0 = time.time()
    direction_series = _build_direction_5m(
        df_5m_raw, n=3, lookback=N_DIRECTION_LOOKBACK
    )
    dir_counts = direction_series.value_counts()
    print(
        f"  [INFO] 完了 ({time.time()-t0:.1f}s)  "
        f"LONG={dir_counts.get('LONG', 0)}  "
        f"SHORT={dir_counts.get('SHORT', 0)}  "
        f"NONE={dir_counts.get('NONE', 0)}"
    )

    ts_4h  = df_4h_full.index.values
    ts_15m = df_15m_full.index.values
    ts_1h  = df_1h_full.index.values
    ts_5m  = df_5m_raw.index.values

    n_bars = len(df_5m_raw)
    warmup = WARMUP_BARS

    # RESCAN 制御（方向別に最後の検出バーを保持）
    last_event_bar: dict[str, int] = {"LONG": -9999, "SHORT": -9999}

    events: list[dict] = []

    skip_none       = 0
    skip_4h_none    = 0
    skip_4h_min     = 0
    skip_rescan     = 0
    skip_15m        = 0
    skip_1h_none    = 0
    skip_sup_none   = 0
    skip_zone       = 0

    print(f"  [INFO] {n_bars} 本スキャン開始（warm-up {warmup} 本スキップ）...")

    for i in range(warmup, n_bars):
        direction = direction_series.iloc[i]

        if direction == "NONE":
            skip_none += 1
            continue

        # RESCAN インターバル（同一方向の重複検出防止）
        if i - last_event_bar[direction] < RESCAN_INTERVAL_BARS:
            skip_rescan += 1
            continue

        # 各 TF のインデックス算出
        idx_4h  = int(np.searchsorted(ts_4h,  ts_5m[i], side="right")) - 1
        idx_15m = int(np.searchsorted(ts_15m, ts_5m[i], side="right")) - 1
        idx_1h  = int(np.searchsorted(ts_1h,  ts_5m[i], side="right")) - 1

        if idx_4h < 10 or idx_15m < 6 or idx_1h < 5:
            continue

        # 4H SH/SL 取得（LOOKBACK_4H=100）
        sh_4h = get_nearest_swing_high(
            df_4h_full["High"], idx_4h, n=3, lookback=LOOKBACK_4H
        )
        sl_4h = get_nearest_swing_low(
            df_4h_full["Low"], idx_4h, n=3, lookback=LOOKBACK_4H
        )

        if sh_4h is None or sl_4h is None:
            skip_4h_none += 1
            continue

        # 4H Swing 幅ガード
        swing_width_pips = (sh_4h - sl_4h) / PIP_SIZE
        if swing_width_pips < MIN_4H_SWING_PIPS:
            skip_4h_min += 1
            continue

        # 1H neck 取得（#016: neck_4h として使用）
        neck_1h = get_nearest_swing_high_1h(
            df_1h_full["High"].iloc[:idx_1h + 1], n=2, lookback=20
        )
        if neck_1h is None:
            skip_1h_none += 1
            continue

        # 15M レンジ構造チェック
        low_15m_w  = df_15m_full["Low"].iloc[:idx_15m + 1]
        high_15m_w = df_15m_full["High"].iloc[:idx_15m + 1]

        range_result = check_15m_range_low(
            low_15m_w, high_15m_w, direction, lookback=LOOKBACK_15M
        )

        if not range_result['found']:
            skip_15m += 1
            continue

        # Support_1h 取得（15M SL の独立取得）
        support_1h = get_nearest_swing_low_15m(
            low_15m_w, n=3, lookback=20
        )
        if support_1h is None:
            skip_sup_none += 1
            continue

        # ゾーン整合性
        zone_valid    = neck_1h > support_1h
        above_support = float(range_result['sl_last']) >= support_1h

        if not zone_valid:
            skip_zone += 1
            continue

        # Fib グレード計算（#016 新判定）
        fib_range     = sh_4h - sl_4h
        current_price = float(df_5m_raw["Close"].iloc[i])

        if direction == "LONG":
            fib_pct = (sh_4h - current_price) / fib_range
            fib_618 = sh_4h - fib_range * 0.618
            fib_50  = sh_4h - fib_range * 0.50
        else:
            fib_pct = (current_price - sl_4h) / fib_range
            fib_618 = sl_4h + fib_range * 0.618
            fib_50  = sl_4h + fib_range * 0.50

        neck_lower   = neck_1h * (1.0 - NECK_TOLERANCE_PCT)
        neck_upper   = neck_1h * (1.0 + NECK_TOLERANCE_PCT)
        is_near_neck = neck_lower <= current_price <= neck_upper

        if fib_pct <= 0.55 and is_near_neck and above_support:
            fib_grade = 2
        elif fib_pct <= 0.65:
            fib_grade = 1
        else:
            fib_grade = 0

        events.append({
            'timestamp'    : df_5m_raw.index[i],
            'direction'    : direction,
            'pattern'      : range_result['pattern'],
            'neck_15m'     : round(float(range_result['neck_15m']), 3),
            'sh_4h'        : round(sh_4h, 3),
            'sl_4h'        : round(sl_4h, 3),
            'neck_1h'      : round(neck_1h, 3),
            'support_1h'   : round(support_1h, 3),
            'zone_valid'   : zone_valid,
            'above_support': above_support,
            'fib_grade'    : fib_grade,
            'fib_618'      : round(fib_618, 3),
            'fib_50'       : round(fib_50, 3),
            'bar_idx'      : i,
        })

        last_event_bar[direction] = i

    print(f"  [INFO] スキャン完了: {len(events)} 件検出")
    print(
        f"         スキップ内訳: NONE方向={skip_none:,}, "
        f"4H_None={skip_4h_none}, 4H幅不足={skip_4h_min}, "
        f"RESCAN={skip_rescan:,}, 15M未成立={skip_15m:,}, "
        f"1H_neck_None={skip_1h_none}, sup_None={skip_sup_none}, zone無効={skip_zone}"
    )

    return events


# ── CSV 保存 ──────────────────────────────────────────────────

def save_base_scan_csv(
    events: list[dict],
    output_dir: str = "logs/base_scan",
) -> Path:
    """スキャン結果を CSV に保存する。

    統計サマリーをファイル末尾に # コメント行として追記する。

    Returns:
        保存先 Path
    """
    out_dir = _repo_root / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_str   = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"base_scan_{ts_str}.csv"

    fieldnames = [
        'timestamp', 'direction', 'pattern', 'neck_15m',
        'sh_4h', 'sl_4h', 'neck_1h', 'support_1h',
        'zone_valid', 'above_support', 'fib_grade', 'fib_618', 'fib_50',
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(events)

        # ── サマリーコメント ──
        if events:
            df_ev = pd.DataFrame(events)
            total = len(df_ev)

            f.write(f"\n# === SUMMARY ===\n")
            f.write(f"# 総件数: {total}\n")
            f.write(f"# LOOKBACK_4H={LOOKBACK_4H}  LOOKBACK_15M={LOOKBACK_15M}\n")
            f.write(f"# WARMUP_BARS={WARMUP_BARS}  RESCAN_INTERVAL={RESCAN_INTERVAL_BARS}\n")

            f.write(f"# --- 方向別 ---\n")
            for d in ['LONG', 'SHORT']:
                n = int((df_ev['direction'] == d).sum())
                f.write(f"# {d}: {n} 件 ({n/total*100:.1f}%)\n")

            f.write(f"# --- パターン別 ---\n")
            for pat, cnt in df_ev['pattern'].value_counts().items():
                f.write(f"# {pat:12s}: {int(cnt):4d} 件 ({cnt/total*100:.1f}%)\n")

            f.write(f"# --- Fib グレード別 ---\n")
            for grade, cnt in df_ev['fib_grade'].value_counts().sort_index().items():
                star = '★★★' if grade == 2 else ('★★' if grade == 1 else '未達')
                f.write(
                    f"# grade={grade} ({star}): {int(cnt):4d} 件 ({cnt/total*100:.1f}%)\n"
                )

            # IHS/LONG 比率（設計検証の重点指標）
            long_ev = df_ev[df_ev['direction'] == 'LONG']
            if len(long_ev) > 0:
                ihs_cnt = int((long_ev['pattern'] == 'IHS').sum())
                f.write(
                    f"# IHS/LONG比率: {ihs_cnt}/{len(long_ev)} "
                    f"({ihs_cnt/len(long_ev)*100:.1f}%)\n"
                )

            # zone_valid / above_support 通過率
            zv_cnt  = int(df_ev['zone_valid'].sum())
            as_cnt  = int(df_ev['above_support'].sum())
            f.write(f"# --- ゾーン整合性 ---\n")
            f.write(f"# zone_valid=True   : {zv_cnt:4d} 件 ({zv_cnt/total*100:.1f}%)\n")
            f.write(f"# above_support=True: {as_cnt:4d} 件 ({as_cnt/total*100:.1f}%)\n")

    print(f"  [CSV] 保存完了: {csv_path}")
    return csv_path


# ── プロット生成 ──────────────────────────────────────────────

def _plot_events(
    events: list[dict],
    df_5m_raw: pd.DataFrame,
    df_4h_full: pd.DataFrame,
    df_15m_full: pd.DataFrame,
    plot_dir: Path,
) -> int:
    """PLOT_MODE に従ってイベントチャートを生成する。

    PLOT_MODE='ALL'    : 全イベントを PNG 出力
    PLOT_MODE='SAMPLE' : ★★★（fib_grade=2）のみ PNG 出力
    PLOT_MODE='NONE'   : PNG 出力なし

    Returns:
        生成した PNG 枚数
    """
    if PLOT_MODE == 'NONE':
        print("  [PLOT] PLOT_MODE='NONE': スキップ")
        return 0

    if PLOT_MODE == 'SAMPLE':
        target = [e for e in events if e['fib_grade'] == 2]
    else:
        target = events

    if not target:
        grade_note = " (★★★=0件)" if PLOT_MODE == 'SAMPLE' else ""
        print(f"  [PLOT] PLOT_MODE='{PLOT_MODE}': 対象イベントなし{grade_note}")
        return 0

    from src.plotter import plot_base_scan

    plot_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for e in target:
        fname = (
            f"{e['timestamp'].strftime('%Y%m%d_%H%M')}"
            f"_{e['direction']}_{e['pattern']}_g{e['fib_grade']}.png"
        )
        save_path = str(plot_dir / fname)
        try:
            plot_base_scan(
                df_5m=df_5m_raw,
                df_4h=df_4h_full,
                df_15m=df_15m_full,
                event=e,
                save_path=save_path,
            )
            count += 1
        except Exception as ex:
            print(f"  [PLOT] {fname} 生成失敗: {ex}")

    print(f"  [PLOT] {count} 枚保存完了 → {plot_dir}")
    return count


# ── メイン実行 ────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  base_scanner.py — 4H + 15M 構造スキャン (#015)")
    print(f"  LOOKBACK_4H={LOOKBACK_4H}  LOOKBACK_15M={LOOKBACK_15M}")
    print(f"  WARMUP_BARS={WARMUP_BARS}  RESCAN_INTERVAL={RESCAN_INTERVAL_BARS}")
    print(f"  PLOT_MODE='{PLOT_MODE}'")
    print("=" * 60)

    t_start = time.time()

    # [1] データ読み込み
    print("\n[1] データ読み込み...")
    df_5m_raw, df_4h_full, df_15m_full, df_1h_full = _load_data()
    print(
        f"    5M: {len(df_5m_raw):,} 本  "
        f"4H: {len(df_4h_full):,} 本  "
        f"15M: {len(df_15m_full):,} 本  "
        f"1H: {len(df_1h_full):,} 本(native)"
    )
    print(f"    期間: {df_5m_raw.index[0]}  〜  {df_5m_raw.index[-1]}")

    # [2] スキャン
    print("\n[2] スキャン実行...")
    events = scan_4h_15m_base(df_5m_raw, df_4h_full, df_15m_full, df_1h_full)

    # [3] 結果サマリー表示
    print("\n[3] 結果サマリー")
    if not events:
        print("    イベント: 0 件（条件成立なし）")
    else:
        df_ev = pd.DataFrame(events)
        total = len(df_ev)
        print(f"    総イベント数: {total:,} 件")

        print("\n    ── 方向別 ──")
        for d in ['LONG', 'SHORT']:
            n = int((df_ev['direction'] == d).sum())
            print(f"    {d:6s}: {n:4d} 件 ({n/total*100:.1f}%)")

        print("\n    ── パターン別 ──")
        for pat, cnt in df_ev['pattern'].value_counts().items():
            print(f"    {pat:12s}: {int(cnt):4d} 件 ({cnt/total*100:.1f}%)")

        print("\n    ── Fib グレード別 ──")
        for grade, cnt in df_ev['fib_grade'].value_counts().sort_index().items():
            star = '★★★' if grade == 2 else ('★★' if grade == 1 else '未達(0)')
            print(f"    grade={grade} ({star}): {int(cnt):4d} 件 ({cnt/total*100:.1f}%)")

        # IHS/LONG 比率（設計検証の重点指標）
        long_ev = df_ev[df_ev['direction'] == 'LONG']
        if len(long_ev) > 0:
            ihs_cnt = int((long_ev['pattern'] == 'IHS').sum())
            print(
                f"\n    IHS/LONG比率: {ihs_cnt}/{len(long_ev)} "
                f"= {ihs_cnt/len(long_ev)*100:.1f}%"
            )

        print("\n    ── ゾーン整合性（#016） ──")
        zv_cnt = int(df_ev['zone_valid'].sum())
        as_cnt = int(df_ev['above_support'].sum())
        print(f"    zone_valid=True   : {zv_cnt:4d} 件 ({zv_cnt/total*100:.1f}%)")
        print(f"    above_support=True: {as_cnt:4d} 件 ({as_cnt/total*100:.1f}%)")

    # [4] CSV 保存
    print("\n[4] CSV 保存...")
    if events:
        save_base_scan_csv(events)
    else:
        print("    イベントなし: CSV スキップ")

    # [5] プロット生成
    print("\n[5] プロット生成...")
    if events:
        plot_dir = _repo_root / "logs" / "base_scan" / "plots"
        _plot_events(events, df_5m_raw, df_4h_full, df_15m_full, plot_dir)
    else:
        print("    イベントなし: プロットスキップ")

    print(f"\n[完了] 経過時間: {time.time()-t_start:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
