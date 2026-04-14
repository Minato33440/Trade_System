"""verify_4h1h_structure.py — 4H/1H 構造整合性検証プロット生成スクリプト。

指示書 #026a-verify に従い、1H足ローソクチャートに4H/1H SH/SLマーカーを
オーバーレイして目視検証用PNGを生成する。

既存ファイルは一切変更しない。

実際に使用するパラメータ（実ファイル確認済み）:
  4H Swing: n=3  （window_scanner.py: scan_4h_events と同値）
  1H Swing: n=2  （window_scanner.py: get_1h_window_range と同値）
  resample_tf: window_scanner.py の関数を使用（label='right', closed='right'）
  カラム名: lowercase（high/low/open/close）
"""
from __future__ import annotations

import sys
from pathlib import Path
from matplotlib.lines import Line2D

import matplotlib
matplotlib.use('Agg')  # GUI なし環境対応
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows
from src.window_scanner import resample_tf  # resample_tf は window_scanner.py にある

# ── データ読み込み ─────────────────────────────────────────────────────────

DATA_PATH = _repo_root / 'data' / 'raw' / 'usdjpy_multi_tf_2years.parquet'

df_raw = pd.read_parquet(DATA_PATH)

# parquet 生列: 5M_Open/High/Low/Close → lowercase にリネーム（window_scanner.py と同一）
df_5m = df_raw[['5M_Open', '5M_High', '5M_Low', '5M_Close']].rename(
    columns={
        '5M_Open':  'open',
        '5M_High':  'high',
        '5M_Low':   'low',
        '5M_Close': 'close',
    }
).dropna()

# リサンプル（label='right', closed='right' 厳守・window_scanner.py と同一）
df_1h = resample_tf(df_5m, '1h')
df_4h = resample_tf(df_5m, '4h')

print(f"Data loaded: 5M={len(df_5m)} / 1H={len(df_1h)} / 4H={len(df_4h)}")

# ── Swing High/Low 検出 ──────────────────────────────────────────────────────

# 4H Swing: n=3（window_scanner.py: scan_4h_events と同値）
# detect_swing_highs は bool Series を返す → [flags] でフィルタして価格取得
sh_4h_flags = detect_swing_highs(df_4h['high'], n=3)
sl_4h_flags = detect_swing_lows(df_4h['low'],   n=3)
sh_4h_vals  = df_4h['high'][sh_4h_flags]   # 4H SH の価格 Series
sl_4h_vals  = df_4h['low'][sl_4h_flags]    # 4H SL の価格 Series

# 1H Swing: n=2（window_scanner.py: get_1h_window_range と同値）
sh_1h_flags = detect_swing_highs(df_1h['high'], n=3)
sl_1h_flags = detect_swing_lows(df_1h['low'],   n=3)
sh_1h_vals  = df_1h['high'][sh_1h_flags]   # 1H SH の価格 Series
sl_1h_vals  = df_1h['low'][sl_1h_flags]    # 1H SL の価格 Series

print(f"4H SH={sh_4h_flags.sum()} / 4H SL={sl_4h_flags.sum()}")
print(f"1H SH={sh_1h_flags.sum()} / 1H SL={sl_1h_flags.sum()}")

# ── プロット生成関数 ──────────────────────────────────────────────────────────

OUT_DIR = _repo_root / 'logs' / 'verify_4h1h'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_x_pos(ts: pd.Timestamp, df_plot: pd.DataFrame):
    """タイムスタンプを df_plot の整数 x 軸位置に変換する。"""
    if ts in df_plot.index:
        return df_plot.index.get_loc(ts)
    # 存在しない場合は searchsorted で最近傍
    pos = df_plot.index.searchsorted(ts)
    return int(pos) if pos < len(df_plot) else None


def plot_verify(start_str: str, end_str: str, save_name: str):
    """
    指定期間の1H足ローソクチャートに4H/1H SH/SLマーカーをオーバーレイして保存。

    Args:
        start_str: 開始日時文字列（例: '2025-01-01'）
        end_str:   終了日時文字列（例: '2025-01-15'）
        save_name: 保存ファイル名（例: '01_20250101_4h1h_verify.png'）
    """
    # 1H足を期間で切り出し
    df_plot_raw = df_1h.loc[start_str:end_str].copy()
    if len(df_plot_raw) == 0:
        print(f"  SKIP: データなし {start_str}〜{end_str}")
        return

    # mplfinance は大文字 OHLC カラムが必須
    df_plot = df_plot_raw.rename(columns={
        'open':  'Open',
        'high':  'High',
        'low':   'Low',
        'close': 'Close',
    })

    # mplfinance でローソク描画（ADR C系厳守）
    s = mpf.make_mpf_style(base_mpf_style='nightclouds')
    fig, axes = mpf.plot(
        df_plot,
        type='candle',
        style=s,
        returnfig=True,        # ADR C-1 必須
        figsize=(22, 9),
        title='',              # タイトルは ax.set_title() で設定
        warn_too_much_data=2000,
    )
    ax = axes[0]

    # タイトル設定（日本語禁止・ADR C-5）
    ax.set_title(
        f'4H/1H Structure Verify  {start_str} ~ {end_str}\n'
        f'4H SH/SL: n=3  |  1H SH/SL: n=3',
        fontsize=11, color='white', pad=10
    )

    # ── 4H / 1H マーカーを ax.scatter() で描画 ──────────────────────
    # addplot は使わない（ADR C-2/C-3）
    # ax.scatter() に x軸の整数インデックスを渡す

    # 期間内の 4H SH/SL / 1H SH/SL を取得（tz 対応: naive/aware 両方）
    try:
        sh_4h_in = sh_4h_vals.loc[start_str:end_str]
        sl_4h_in = sl_4h_vals.loc[start_str:end_str]
        sh_1h_in = sh_1h_vals.loc[start_str:end_str]
        sl_1h_in = sl_1h_vals.loc[start_str:end_str]
    except Exception as e:
        print(f"  WARN: スライスエラー ({e}) — tz ミスマッチの可能性")
        # tz を合わせて再試行
        idx = df_plot_raw.index
        tz  = idx.tzinfo if hasattr(idx, 'tzinfo') else None
        start_ts = pd.Timestamp(start_str, tz=tz)
        end_ts   = pd.Timestamp(end_str,   tz=tz)
        sh_4h_in = sh_4h_vals[(sh_4h_vals.index >= start_ts) & (sh_4h_vals.index <= end_ts)]
        sl_4h_in = sl_4h_vals[(sl_4h_vals.index >= start_ts) & (sl_4h_vals.index <= end_ts)]
        sh_1h_in = sh_1h_vals[(sh_1h_vals.index >= start_ts) & (sh_1h_vals.index <= end_ts)]
        sl_1h_in = sl_1h_vals[(sl_1h_vals.index >= start_ts) & (sl_1h_vals.index <= end_ts)]

    # 4H Swing High（赤・大きめ▼）
    for ts, val in sh_4h_in.items():
        x = get_x_pos(ts, df_plot_raw)
        if x is not None and 0 <= x < len(df_plot_raw):
            ax.scatter(int(x), val * 1.0003, color='#FF4444', marker='v',
                       s=180, zorder=10, label='_nolegend_')

    # 4H Swing Low（青・大きめ▲）
    for ts, val in sl_4h_in.items():
        x = get_x_pos(ts, df_plot_raw)
        if x is not None and 0 <= x < len(df_plot_raw):
            ax.scatter(int(x), val * 0.9997, color='#1E90FF', marker='^',
                       s=180, zorder=10, label='_nolegend_')

    # 1H Swing High（オレンジ・小さめ▼）
    for ts, val in sh_1h_in.items():
        x = get_x_pos(ts, df_plot_raw)
        if x is not None and 0 <= x < len(df_plot_raw):
            ax.scatter(int(x), val * 1.0002, color='#FFA500', marker='v',
                       s=70, zorder=9, label='_nolegend_')

    # 1H Swing Low（シアン・小さめ▲）
    for ts, val in sl_1h_in.items():
        x = get_x_pos(ts, df_plot_raw)
        if x is not None and 0 <= x < len(df_plot_raw):
            ax.scatter(int(x), val * 0.9998, color='#00CED1', marker='^',
                       s=70, zorder=9, label='_nolegend_')

    # 凡例（ダミープロットで作成）
    legend_elements = [
        Line2D([0], [0], marker='v', color='w', markerfacecolor='#FF4444',
               markersize=12, label='4H Swing High'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#1E90FF',
               markersize=12, label='4H Swing Low'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='#FFA500',
               markersize=8,  label='1H Swing High'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#00CED1',
               markersize=8,  label='1H Swing Low'),
    ]
    ax.legend(handles=legend_elements, loc='upper left',
              fontsize=9, framealpha=0.5)

    # 保存
    save_path = OUT_DIR / save_name
    fig.savefig(save_path, dpi=130, bbox_inches='tight',
                facecolor='#0f0f0f')
    plt.close(fig)

    # 期間内の検出数を表示
    print(f"  4H SH={len(sh_4h_in)} / 4H SL={len(sl_4h_in)}"
          f" | 1H SH={len(sh_1h_in)} / 1H SL={len(sl_1h_in)}"
          f"  → Saved: {save_path.name}")

    return len(sh_4h_in), len(sl_4h_in)


# ── メイン実行（5期間）──────────────────────────────────────────────────────

if __name__ == '__main__':
    cases = [
        ('2024-12-25', '2025-01-15', '01_20250101_4h1h_verify.png',
         'Plot06 - 4H SL mismatch check'),
        ('2024-03-20', '2024-04-05', '02_20240325_4h1h_verify.png',
         'Plot01 DB - earliest detection'),
        ('2024-06-10', '2024-06-25', '03_20240617_4h1h_verify.png',
         'Plot02 ASCENDING'),
        ('2025-06-10', '2025-06-25', '04_20250617_4h1h_verify.png',
         'Plot07 DB'),
        ('2025-09-10', '2025-09-25', '05_20250917_4h1h_verify.png',
         'Plot09/10 ASCENDING - consecutive detection'),
    ]

    results = []
    for start, end, fname, note in cases:
        print(f"\n[{note}]  {start} ~ {end}")
        ret = plot_verify(start, end, fname)
        results.append((fname, ret))

    print("\n=== verify_4h1h_structure.py 完了 ===")
    print(f"出力先: logs/verify_4h1h/ ({len(cases)}枚)")

    # 結果報告フォーマット
    print("\n=== #026a-verify 結果報告 ===\n")
    print("生成プロット: 5枚")
    print("実際に使用したパラメータ:")
    print("  4H Swing: n=3 (window_scanner.py: scan_4h_events と同値)")
    print("  1H Swing: n=2 (window_scanner.py: get_1h_window_range と同値)")
    print()
    print("■ 各プロットの4H SH/SL 検出数")
    labels = [
        '01_20250101',
        '02_20240325',
        '03_20240617',
        '04_20250617',
        '05_20250917',
    ]
    for label, (fname, ret) in zip(labels, results):
        if ret is not None:
            sh_n, sl_n = ret
            print(f"{label}: 4H SH={sh_n}本 / 4H SL={sl_n}本  （期間内）")
        else:
            print(f"{label}: SKIP（データなし）")
