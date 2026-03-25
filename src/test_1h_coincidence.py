# REX 指示書 #020 — 作業② 修正版
# test_1h_coincidence.py（時間近傍比較ロジック）
#
# 修正内容:
#   旧版: 4H SL(直近値) vs 1H SL(240本中の絶対最安値) → 構造的ミスマッチ
#   修正版: 4H SL のタイムスタンプ ±8本(8時間)の窓内で
#           最も価格が近い 1H SL を探して比較
#
# ⛔ 禁止事項:
#   - backtest.py / entry_logic.py / exit_logic.py を変更しない
#   - resample_tf の label='right', closed='right' を変更しない

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swing_detector import (
    detect_swing_lows,
    get_direction_4h,
)

DATA_PATH = Path(__file__).parent.parent / "data/raw/usdjpy_multi_tf_2years.parquet"
PIP = 0.01
WARMUP_4H = 50  # 4H足 50本分ウォームアップ
WINDOW_1H = 8  # 4H SL タイムスタンプ前後 ±8本（±8時間）

# ---- データ読み込み ----
df_raw = pd.read_parquet(DATA_PATH)

# 5M 列を抽出・lowercase リネーム
df_5m = df_raw[["5M_Open", "5M_High", "5M_Low", "5M_Close"]].rename(
    columns={"5M_Open": "open", "5M_High": "high", "5M_Low": "low", "5M_Close": "close"}
)


# ---- リサンプル（※ label='right', closed='right' は既存 backtest.py と同一。変更禁止）----
def resample_tf(df, rule):
    return (
        df.resample(rule, label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
    )


df_4h = resample_tf(df_5m, "4h")
df_1h = resample_tf(df_5m, "1h")

print(f"4H: {len(df_4h)}本 / 1H: {len(df_1h)}本")

# ---- スキャン ----
results = []

for i in range(WARMUP_4H, len(df_4h)):
    ts_4h = df_4h.index[i]

    # 4H 方向確認（current_idx=i）
    direction = get_direction_4h(
        df_4h["high"], df_4h["low"], current_idx=i, n=3, lookback=20
    )
    if direction != "LONG":
        continue

    # ---- 4H SL のタイムスタンプと価格を取得 ----
    # get_nearest_swing_low は価格しか返さないので、
    # detect_swing_lows を直接使ってタイムスタンプも取得する
    start_4h = max(0, i - 20 + 1)
    window_4h = df_4h["low"].iloc[start_4h : i + 1]
    mask_4h = detect_swing_lows(window_4h, n=3)
    sl_4h_series = window_4h[mask_4h]

    if len(sl_4h_series) == 0:
        continue

    sl_4h_val = float(sl_4h_series.iloc[-1])  # 直近の4H SL 価格
    sl_4h_ts = sl_4h_series.index[-1]  # 直近の4H SL タイムスタンプ

    # ---- sl_4h_ts の前後 ±WINDOW_1H 本で 1H SL を探す ----
    idx_1h_center = df_1h.index.searchsorted(sl_4h_ts, side="right") - 1
    if idx_1h_center < WINDOW_1H:
        continue

    win_start = max(0, idx_1h_center - WINDOW_1H)
    win_end = min(len(df_1h) - 1, idx_1h_center + WINDOW_1H)
    window_1h = df_1h["low"].iloc[win_start : win_end + 1]

    mask_1h = detect_swing_lows(window_1h, n=2)
    sl_1h_near = window_1h[mask_1h]

    if len(sl_1h_near) == 0:
        results.append(
            {
                "ts_4h": ts_4h,
                "sl_4h_ts": sl_4h_ts,
                "sl_4h": round(sl_4h_val, 3),
                "sl_1h_near": None,
                "sl_1h_ts": None,
                "dist_pips": None,
                "detected": False,
                "match_5p": False,
                "match_10p": False,
                "match_20p": False,
            }
        )
        continue

    # 最も 4H SL の価格に近い 1H SL を選択
    dists = abs(sl_1h_near - sl_4h_val)
    closest_idx = dists.idxmin()
    sl_1h_val = float(sl_1h_near[closest_idx])
    sl_1h_ts = closest_idx

    dist = abs(sl_4h_val - sl_1h_val) / PIP

    results.append(
        {
            "ts_4h": ts_4h,
            "sl_4h_ts": sl_4h_ts,
            "sl_4h": round(sl_4h_val, 3),
            "sl_1h_near": round(sl_1h_val, 3),
            "sl_1h_ts": sl_1h_ts,
            "dist_pips": round(dist, 2),
            "detected": True,
            "match_5p": dist <= 5.0,
            "match_10p": dist <= 10.0,
            "match_20p": dist <= 20.0,
        }
    )

df_result = pd.DataFrame(results)
total = len(df_result)
det = int(df_result["detected"].sum())
not_det = total - det
m5 = int(df_result["match_5p"].sum())
m10 = int(df_result["match_10p"].sum())
m20 = int(df_result["match_20p"].sum())

dist_valid = df_result.dropna(subset=["dist_pips"])["dist_pips"]

print(f"\n=== 1H-4H 一致検証レポート（修正版: 時間近傍比較）===")
print(f"対象サンプル (4H LONG)  : {total} 件")
print(f"1H SL 検出率（±{WINDOW_1H}本窓内）: {det}/{total} = {det/total*100:.1f}%")
print(f"窓内に 1H SL なし       : {not_det} 件")
print(f"")
if len(dist_valid) > 0:
    print(f"--- 4H SL との距離分布 (pips) ---")
    print(f"  mean   : {dist_valid.mean():.1f}")
    print(f"  median : {dist_valid.median():.1f}")
    print(f"  min    : {dist_valid.min():.1f}")
    print(f"  max    : {dist_valid.max():.1f}")
    print(f"")
    print(f"--- 一致率（距離ベース）---")
    print(f"  <= 5pips  : {m5}/{det} = {m5/det*100:.1f}%")
    print(f"  <= 10pips : {m10}/{det} = {m10/det*100:.1f}%")
    print(f"  <= 20pips : {m20}/{det} = {m20/det*100:.1f}%")
else:
    print("※ 検出されたサンプルなし — 窓サイズの拡張を検討")

# ---- CSV保存 ----
out_path = Path(__file__).parent.parent / "logs/test_1h_coincidence.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df_result.to_csv(out_path, index=False)
print(f"\n結果CSV: {out_path}")

# ---- サンプル出力（上位5件・距離が短い順）----
if len(dist_valid) > 0:
    top5 = df_result.dropna(subset=["dist_pips"]).nsmallest(5, "dist_pips")
    print(f"\n--- 距離が近い上位5件 ---")
    for _, row in top5.iterrows():
        print(
            f"  4H SL: {row['sl_4h']} ({row['sl_4h_ts']}) "
            f"| 1H SL: {row['sl_1h_near']} ({row['sl_1h_ts']}) "
            f"| dist: {row['dist_pips']}p"
        )
