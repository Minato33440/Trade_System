"""チャート生成モジュール。

8ペア正規化比較プロットの生成・保存を担当する。
Swing High/Low の視覚化デバッグ機能も含む。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from configs.settings import PNG_DATA_DIR
from src.utils import ensure_dir_exists


def save_normalized_plot(df: pd.DataFrame, filename: str = "multi_pairs_plot_8.png") -> Path:
    """
    DataFrame の各列を 0-1 正規化してプロットを保存する。

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


def save_swing_plot(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    direction: str = "NONE",
    pair: str = "USDJPY",
    tf: str = "4H",
    filename: Optional[str] = None,
) -> Path:
    """Swing High/Low を視覚化してデバッグ用PNGを保存する。

    - Swing High を赤い ▼ マーカーでプロット
    - Swing Low  を緑の ▲ マーカーでプロット
    - 直近SH を赤の水平破線で表示（ラベル: SH）
    - 直近SL を緑の水平破線で表示（ラベル: SL）
    - チャートタイトルに direction を表示（例: "USDJPY 4H [LONG]"）

    Args:
        close:     Close価格のSeries
        high:      High価格のSeries
        low:       Low価格のSeries
        direction: 'LONG' / 'SHORT' / 'NONE'
        pair:      通貨ペア名（タイトル表示用）
        tf:        時間足（タイトル表示用）
        filename:  保存ファイル名（Noneの場合は自動生成）

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

    # Swing 検出
    n = 5 if tf in ("4H", "4h") else 3
    sh_mask = detect_swing_highs(high, n=n)
    sl_mask = detect_swing_lows(low, n=n)

    # 直近SH/SL（最終バー直前）
    last_idx = len(high) - 1
    nearest_sh = get_nearest_swing_high(high, current_idx=last_idx, n=n, lookback=50)
    nearest_sl = get_nearest_swing_low(low, current_idx=last_idx, n=n, lookback=50)

    fig, ax = plt.subplots(figsize=(16, 7))

    # Close ライン
    ax.plot(close.values, color="steelblue", linewidth=1.0, label="Close", zorder=2)

    # Swing High マーカー（赤 ▼）
    sh_indices = [i for i, v in enumerate(sh_mask.values) if v]
    if sh_indices:
        ax.scatter(
            sh_indices,
            high.values[sh_indices],
            marker="v",
            color="red",
            s=60,
            label="Swing High",
            zorder=3,
        )

    # Swing Low マーカー（緑 ▲）
    sl_indices = [i for i, v in enumerate(sl_mask.values) if v]
    if sl_indices:
        ax.scatter(
            sl_indices,
            low.values[sl_indices],
            marker="^",
            color="green",
            s=60,
            label="Swing Low",
            zorder=3,
        )

    # 直近SH 水平破線（赤）
    if not pd.isna(nearest_sh):
        ax.axhline(
            y=nearest_sh,
            color="red",
            linestyle="--",
            linewidth=1.2,
            alpha=0.8,
            label=f"SH: {nearest_sh:.3f}",
        )

    # 直近SL 水平破線（緑）
    if not pd.isna(nearest_sl):
        ax.axhline(
            y=nearest_sl,
            color="green",
            linestyle="--",
            linewidth=1.2,
            alpha=0.8,
            label=f"SL: {nearest_sl:.3f}",
        )

    title = f"{pair} {tf} [{direction}]"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Bar")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.4)
    plt.tight_layout()

    if filename is None:
        filename = f"swing_{pair}_{tf}_{direction}.png"

    plot_path = PNG_DATA_DIR / filename
    ensure_dir_exists(plot_path.parent)
    plt.savefig(plot_path, dpi=100)
    plt.close()
    print(f"[plotter] Swing chart saved: {plot_path}")
    return plot_path
