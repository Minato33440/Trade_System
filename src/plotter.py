"""チャート生成モジュール。

8ペア正規化比較プロットの生成・保存を担当する。
"""
from __future__ import annotations

from pathlib import Path

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
