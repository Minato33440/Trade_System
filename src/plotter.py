"""チャート生成モジュール。

8ペア正規化比較プロットおよびSwing High/Low視覚化デバッグ機能を提供する。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# リポジトリルートをパスに追加
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

try:
    from configs.settings import PNG_DATA_DIR
except ImportError:
    PNG_DATA_DIR = _repo_root / "data" / "charts"

from src.utils import ensure_dir_exists


def save_normalized_plot(df: pd.DataFrame, filename: str = "multi_pairs_plot_8.png") -> Path:
    """DataFrame の各列を 0-1 正規化してプロットを保存する。

    Returns:
        保存先 Path
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("matplotlib が未インストールです")

    df_norm = (df - df.min()) / (df.max() - df.min())
    plt.figure(figsize=(14, 8))
    for col in df_norm.columns:
        plt.plot(df_norm[col], label=col)
    plt.title("8ペア正規化比較 (30日)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)
    plt.tight_layout()

    plot_path = PNG_DATA_DIR / filename
    ensure_dir_exists(plot_path.parent)
    plt.savefig(plot_path)
    plt.close()
    return plot_path


def save_swing_debug_plot(
    df_ohlc: pd.DataFrame,
    direction: str = "NONE",
    tf_label: str = "4H",
    n: int = 3,
    filename: str = "swing_debug.png",
) -> Path:
    """Swing High/Low を視覚化したデバッグチャートを保存する。

    チャートに含まれる情報:
      - ローソク足（Close線で代替）
      - Swing High: 赤い ▼ マーカー
      - Swing Low: 緑の ▲ マーカー
      - 直近SH: 赤の水平破線（ラベル: SH）
      - 直近SL: 緑の水平破線（ラベル: SL）
      - チャートタイトルに direction を表示

    Args:
        df_ohlc:   OHLC DataFrame（High/Low/Close列を含む）
        direction: '4H方向文字列（LONG/SHORT/NONE）'
        tf_label:  タイムフレームラベル（チャートタイトル用）
        n:         Swing検出の前後確認本数
        filename:  出力ファイル名

    Returns:
        保存先 Path
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("matplotlib が未インストールです")

    from src.swing_detector import (
        detect_swing_highs,
        detect_swing_lows,
        get_nearest_swing_high,
        get_nearest_swing_low,
    )

    high = df_ohlc["High"]
    low = df_ohlc["Low"]
    close = df_ohlc["Close"]

    sh_flags = detect_swing_highs(high, n=n)
    sl_flags = detect_swing_lows(low, n=n)

    sh_price = get_nearest_swing_high(high, len(high) - 1, n=n, lookback=min(50, len(high) - 1))
    sl_price = get_nearest_swing_low(low, len(low) - 1, n=n, lookback=min(50, len(low) - 1))

    x = range(len(close))

    fig, ax = plt.subplots(figsize=(16, 6))

    # Close ライン
    ax.plot(x, close.values, color="steelblue", linewidth=1.0, label="Close", zorder=1)

    # High ライン（薄く）
    ax.plot(x, high.values, color="gray", linewidth=0.5, alpha=0.4, label="High/Low")
    ax.plot(x, low.values, color="gray", linewidth=0.5, alpha=0.4)

    # Swing High: 赤い ▼ マーカー
    sh_x = [i for i, v in enumerate(sh_flags.values) if v]
    sh_y = [float(high.values[i]) for i in sh_x]
    ax.scatter(sh_x, sh_y, marker="v", color="red", s=80, zorder=5, label="Swing High ▼")

    # Swing Low: 緑の ▲ マーカー
    sl_x = [i for i, v in enumerate(sl_flags.values) if v]
    sl_y = [float(low.values[i]) for i in sl_x]
    ax.scatter(sl_x, sl_y, marker="^", color="green", s=80, zorder=5, label="Swing Low ▲")

    # 直近SH: 赤の水平破線
    ax.axhline(y=sh_price, color="red", linestyle="--", linewidth=1.2, alpha=0.8, label=f"SH: {sh_price:.3f}")

    # 直近SL: 緑の水平破線
    ax.axhline(y=sl_price, color="green", linestyle="--", linewidth=1.2, alpha=0.8, label=f"SL: {sl_price:.3f}")

    # タイトルに方向を表示
    ax.set_title(f"USDJPY {tf_label} [{direction}]  SH={sh_price:.3f}  SL={sl_price:.3f}", fontsize=13)
    ax.set_xlabel("Bar index")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    plot_path = PNG_DATA_DIR / filename
    ensure_dir_exists(plot_path.parent)
    plt.savefig(plot_path, dpi=120)
    plt.close()
    return plot_path


def plot_swing_check(
    df_5m: "pd.DataFrame",
    df_4h: "pd.DataFrame",
    df_15m: "pd.DataFrame",
    center_time: "pd.Timestamp",
    direction: str,
    save_path: str,
    left_bars: int = 48,
    right_bars: int = 24,
    dpi: int = 200,
) -> None:
    """Swing 検出精度確認チャートを生成・保存する（Phase 1）。

    【メインパネル】5M OHLC + 上位足構造オーバーレイ
      - 5M ローソク足（mplfinance）
      - 4H Swing High/Low ドット + 水平線
      - 15M Swing High/Low 水平線
      - NONE 区間グレー背景

    【サブパネル】小テーブル（Swing パラメータ・direction・NONE 率）

    Args:
        df_5m:       5M OHLC DataFrame（High/Low/Open/Close）
        df_4h:       4H OHLC DataFrame
        df_15m:      15M OHLC DataFrame
        center_time: チャート中心時刻（エントリー確定時刻）
        direction:   'LONG' / 'SHORT'
        save_path:   PNG 保存先パス
        left_bars:   中心の左側に表示する 5M 足数（デフォルト 48 = 4 時間）
        right_bars:  中心の右側に表示する 5M 足数（デフォルト 24 = 2 時間）
        dpi:         解像度（デフォルト 200）

    保存先: save_path で指定（backtest.py 側が logs/plots/ 以下を指定する）
    既存の plotter.py 関数には一切手を触れない。本関数は末尾追加のみ。
    """
    try:
        import mplfinance as mpf
    except ImportError:
        raise RuntimeError(
            "mplfinance が未インストールです。pip install mplfinance を実行してください。"
        )

    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        import matplotlib.patches as mpatches
    except ImportError:
        raise RuntimeError("matplotlib が未インストールです")

    from src.swing_detector import detect_swing_highs, detect_swing_lows

    # ── 表示範囲を決定 ──
    center_loc = df_5m.index.searchsorted(center_time)
    i_start = max(0, center_loc - left_bars)
    i_end   = min(len(df_5m), center_loc + right_bars + 1)
    df_view = df_5m.iloc[i_start:i_end].copy()

    if len(df_view) == 0:
        return

    # ── 4H Swing 検出（全期間から検出して表示範囲内のものを抽出） ──
    sh_4h_flags = detect_swing_highs(df_4h["High"], n=3)
    sl_4h_flags = detect_swing_lows(df_4h["Low"],   n=3)
    sh_4h_prices = df_4h["High"][sh_4h_flags]
    sl_4h_prices = df_4h["Low"][sl_4h_flags]

    # ── 15M Swing 検出 ──
    sh_15m_flags = detect_swing_highs(df_15m["High"], n=3)
    sl_15m_flags = detect_swing_lows(df_15m["Low"],   n=3)
    sh_15m_prices = df_15m["High"][sh_15m_flags]
    sl_15m_prices = df_15m["Low"][sl_15m_flags]

    # 表示範囲の時刻
    t_start = df_view.index[0]
    t_end   = df_view.index[-1]

    sh_4h_in_view  = sh_4h_prices[(sh_4h_prices.index >= t_start) & (sh_4h_prices.index <= t_end)]
    sl_4h_in_view  = sl_4h_prices[(sl_4h_prices.index >= t_start) & (sl_4h_prices.index <= t_end)]
    sh_15m_in_view = sh_15m_prices[(sh_15m_prices.index >= t_start) & (sh_15m_prices.index <= t_end)]
    sl_15m_in_view = sl_15m_prices[(sl_15m_prices.index >= t_start) & (sl_15m_prices.index <= t_end)]

    # ── mplfinance スタイル ──
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350',
                               edge='inherit', wick='inherit', volume='in')
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='#444444',
                                facecolor='#1a1a2e', figcolor='#1a1a2e',
                                rc={'axes.labelcolor': 'white',
                                    'axes.edgecolor': '#555555',
                                    'xtick.color': 'white',
                                    'ytick.color': 'white',
                                    'text.color': 'white'})

    # ── mplfinance で returnfig=True → axes 取得後に水平線追加 ──
    fig, axes = mpf.plot(
        df_view,
        type='candle',
        style=style,
        figsize=(16, 9),
        returnfig=True,
        warn_too_much_data=9999,
        title=f"USDJPY 5M [{direction}]  {center_time.strftime('%Y-%m-%d %H:%M')}",
    )
    ax_main = axes[0]

    # 4H Swing High 水平線（橙 #FF8C00）
    for price in sh_4h_in_view.values:
        ax_main.axhline(y=price, color='#FF8C00', linewidth=2.0, linestyle='-', alpha=0.9)
    # 4H Swing Low 水平線（青 #1E90FF）
    for price in sl_4h_in_view.values:
        ax_main.axhline(y=price, color='#1E90FF', linewidth=2.0, linestyle='-', alpha=0.9)
    # 15M Swing High 水平線（サーモン #FA8072）
    for price in sh_15m_in_view.values:
        ax_main.axhline(y=price, color='#FA8072', linewidth=1.5, linestyle='-', alpha=0.85)
    # 15M Swing Low 水平線（水色 #87CEEB）
    for price in sl_15m_in_view.values:
        ax_main.axhline(y=price, color='#87CEEB', linewidth=1.5, linestyle='-', alpha=0.85)

    # エントリー時刻のマーカー（縦線）
    try:
        center_x = int(df_view.index.searchsorted(center_time))
        if 0 <= center_x < len(df_view):
            ax_main.axvline(x=center_x, color='#00FF00', linewidth=1.2,
                            linestyle='--', alpha=0.8)
    except Exception:
        pass

    # 凡例
    legend_items = [
        mpatches.Patch(color='#FF8C00', label='4H SH'),
        mpatches.Patch(color='#1E90FF', label='4H SL'),
        mpatches.Patch(color='#FA8072', label='15M SH'),
        mpatches.Patch(color='#87CEEB', label='15M SL'),
        mpatches.Patch(color='#00FF00', label='Entry'),
    ]
    ax_main.legend(handles=legend_items, loc='upper left', fontsize=8,
                   framealpha=0.3, facecolor='#1a1a2e', labelcolor='white')

    # ── 情報テーブル（図の下部にテキスト注記） ──
    n_sh4h  = len(sh_4h_in_view)
    n_sl4h  = len(sl_4h_in_view)
    n_sh15m = len(sh_15m_in_view)
    n_sl15m = len(sl_15m_in_view)

    info_text = (
        f"n(4H)=3  n(15M)=3  |  dir={direction}  |  "
        f"4H SH={n_sh4h} SL={n_sl4h}  |  "
        f"15M SH={n_sh15m} SL={n_sl15m}  |  "
        f"bars={len(df_view)}"
    )
    fig.text(0.01, 0.01, info_text, fontsize=8, color='white',
             bbox=dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.7))

    # ── PNG 保存 ──
    save_path_obj = Path(save_path)
    save_path_obj.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path_obj, dpi=dpi, bbox_inches='tight',
                facecolor='#1a1a2e', edgecolor='none')
    plt.close(fig)


def save_entry_debug_plot(
    df_multi: pd.DataFrame,
    entries_long: pd.Series,
    entries_short: pd.Series,
    n_bars_tail: int = 500,
    filename: str = "entry_debug.png",
) -> Path:
    """エントリーポイントを視覚化したデバッグチャートを保存する。

    Args:
        df_multi:      前処理済みのMulti-TF DataFrame
        entries_long:  Long エントリーフラグ Series
        entries_short: Short エントリーフラグ Series
        n_bars_tail:   末尾から何本分を表示するか
        filename:      出力ファイル名

    Returns:
        保存先 Path
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("matplotlib が未インストールです")

    close = df_multi["5M_Close"].iloc[-n_bars_tail:]
    el = entries_long.iloc[-n_bars_tail:]
    es = entries_short.iloc[-n_bars_tail:]

    x = range(len(close))
    long_x = [i for i, v in enumerate(el.values) if v]
    long_y = [float(close.values[i]) for i in long_x]
    short_x = [i for i, v in enumerate(es.values) if v]
    short_y = [float(close.values[i]) for i in short_x]

    fig, ax = plt.subplots(figsize=(16, 6))
    ax.plot(x, close.values, color="steelblue", linewidth=0.8, label="5M Close")
    ax.scatter(long_x, long_y, marker="^", color="lime", s=100, zorder=5, label=f"Long Entry ({len(long_x)}件)")
    ax.scatter(short_x, short_y, marker="v", color="red", s=100, zorder=5, label=f"Short Entry ({len(short_x)}件)")
    ax.set_title(f"USDJPY 5M エントリーポイント（末尾{n_bars_tail}本）  Long:{len(long_x)} Short:{len(short_x)}", fontsize=12)
    ax.set_xlabel("Bar index")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    plot_path = PNG_DATA_DIR / filename
    ensure_dir_exists(plot_path.parent)
    plt.savefig(plot_path, dpi=120)
    plt.close()
    return plot_path
