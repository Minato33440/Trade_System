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
