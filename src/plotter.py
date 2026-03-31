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

# ── #024a: プロット範囲定数（スキャン窓とは独立） ────────────────────────────
PLOT_PRE_H  = 25   # 1H SL 前 25時間
PLOT_POST_H = 40   # 1H SL 後 40時間（エントリー〜決済帯をカバー）


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

    # 直近SH: 赤の水平破線（None チェック）
    if sh_price is not None:
        ax.axhline(y=sh_price, color="red", linestyle="--", linewidth=1.2, alpha=0.8, label=f"SH: {sh_price:.3f}")

    # 直近SL: 緑の水平破線（None チェック）
    if sl_price is not None:
        ax.axhline(y=sl_price, color="green", linestyle="--", linewidth=1.2, alpha=0.8, label=f"SL: {sl_price:.3f}")

    # タイトルに方向を表示（None 対応）
    sh_str = f"{sh_price:.3f}" if sh_price is not None else "N/A"
    sl_str = f"{sl_price:.3f}" if sl_price is not None else "N/A"
    ax.set_title(f"USDJPY {tf_label} [{direction}]  SH={sh_str}  SL={sl_str}", fontsize=13)
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


def plot_base_scan(
    df_5m: "pd.DataFrame",
    df_4h: "pd.DataFrame",
    df_15m: "pd.DataFrame",
    event: dict,
    save_path: str,
    left_bars: int = 48,
    right_bars: int = 24,
    dpi: int = 200,
) -> None:
    """base_scanner イベントのチャートを生成・保存する。

    plot_swing_check() のラッパー。イベント dict から引数を展開して呼び出す。

    Args:
        df_5m:     5M OHLC DataFrame
        df_4h:     4H OHLC DataFrame
        df_15m:    15M OHLC DataFrame
        event:     scan_4h_15m_base() が返す 1 件分の dict
        save_path: PNG 保存先パス
        left_bars: チャート中心左側の 5M 足数（デフォルト 48 = 4 時間）
        right_bars: チャート中心右側の 5M 足数（デフォルト 24 = 2 時間）
        dpi:       解像度
    """
    plot_swing_check(
        df_5m=df_5m,
        df_4h=df_4h,
        df_15m=df_15m,
        center_time=event['timestamp'],
        direction=event['direction'],
        save_path=save_path,
        sh_4h=event.get('sh_4h'),
        sl_4h=event.get('sl_4h'),
        left_bars=left_bars,
        right_bars=right_bars,
        dpi=dpi,
    )


def plot_swing_check(
    df_5m: "pd.DataFrame",
    df_4h: "pd.DataFrame",
    df_15m: "pd.DataFrame",
    center_time: "pd.Timestamp",
    direction: str,
    save_path: str,
    sh_4h: "float | None" = None,
    sl_4h: "float | None" = None,
    left_bars: int = 48,
    right_bars: int = 24,
    dpi: int = 200,
) -> None:
    """Swing 検出精度確認チャートを生成・保存する（Phase 1 + Fib ライン追加版）。

    【メインパネル】5M OHLC + 上位足構造オーバーレイ
      - 5M ローソク足（mplfinance）
      - 4H Swing High/Low ドット + 水平線
      - 15M Swing High/Low 水平線
      - Fib 61.8% / 50% ライン（sh_4h/sl_4h が非 None の場合のみ）
      - NONE 区間グレー背景

    【サブパネル】小テーブル（Swing パラメータ・direction・NONE 率）

    Args:
        df_5m:       5M OHLC DataFrame（High/Low/Open/Close）
        df_4h:       4H OHLC DataFrame
        df_15m:      15M OHLC DataFrame
        center_time: チャート中心時刻（エントリー確定時刻）
        direction:   'LONG' / 'SHORT'
        save_path:   PNG 保存先パス
        sh_4h:       4H Swing High 価格（None の場合 Fib ライン非表示）
        sl_4h:       4H Swing Low 価格（None の場合 Fib ライン非表示）
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

    # Fib 61.8% / 50% ライン（sh_4h / sl_4h が非 None の場合のみ描画）
    if sh_4h is not None and sl_4h is not None:
        fib_range = sh_4h - sl_4h
        if fib_range > 0:
            fib_618 = sh_4h - fib_range * 0.618
            fib_50  = sh_4h - fib_range * 0.50
            ax_main.axhline(y=fib_618, color='#9B59B6', linewidth=1.0,
                            linestyle='--', alpha=0.8,
                            label=f'Fib 61.8%  {fib_618:.3f}')
            ax_main.axhline(y=fib_50,  color='#9B59B6', linewidth=1.0,
                            linestyle=':',  alpha=0.8,
                            label=f'Fib 50%    {fib_50:.3f}')

    # エントリー時刻のマーカー（縦線）
    try:
        center_x = int(df_view.index.searchsorted(center_time))
        if 0 <= center_x < len(df_view):
            ax_main.axvline(x=center_x, color='#00FF00', linewidth=1.2,
                            linestyle='--', alpha=0.8)
    except Exception:
        pass

    # 凡例（Fib ライン有無に応じて動的追加）
    legend_items = [
        mpatches.Patch(color='#FF8C00', label='4H SH'),
        mpatches.Patch(color='#1E90FF', label='4H SL'),
        mpatches.Patch(color='#FA8072', label='15M SH'),
        mpatches.Patch(color='#87CEEB', label='15M SL'),
        mpatches.Patch(color='#00FF00', label='Entry'),
    ]
    if sh_4h is not None and sl_4h is not None:
        fib_range = sh_4h - sl_4h
        if fib_range > 0:
            legend_items += [
                mpatches.Patch(color='#9B59B6', label=f'Fib 61.8%  {sh_4h - fib_range * 0.618:.3f}'),
                mpatches.Patch(color='#9B59B6', label=f'Fib 50%    {sh_4h - fib_range * 0.50:.3f}'),
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


def plot_4h_1h_structure(
    df_5m        : "pd.DataFrame",
    df_1h        : "pd.DataFrame",
    df_4h        : "pd.DataFrame",
    center_time  : "pd.Timestamp",
    direction    : str,
    sh_4h_list   : "list[tuple]",
    sl_4h_list   : "list[tuple]",
    sh_1h_list   : "list[tuple]",
    sl_1h_list   : "list[tuple]",
    neck_4h      : "float | None",
    neck_break_time: "pd.Timestamp | None",
    save_path    : str,
) -> None:
    """4H + 1H 構造確認プロット。

    「4H Swing High ネック越え」と「1H Swing HighLow トレンド」の重ね合わせを視覚化する。

    表示期間:
      center_time を中心に 左: 10日（5M 2,880本）右: 2日（5M 576本）

    描画要素:
      1. 5M ローソク足（背景）
      2. 4H SH ドット + 水平線（橙 #FF8C00 / 2.5px）
      3. 4H SL ドット + 水平線（青 #1E90FF / 2.5px）
      4. 4H ネックライン（橙 #FF8C00 / 3.0px 太実線）
      5. 4H ネック越え確定足マーカー（橙 ▲ or ▼）
      6. 1H SH ドット + 折れ線（サーモン #FA8072 / 1.5px）
      7. 1H SL ドット + 折れ線（水色 #87CEEB / 1.5px）
      8. 1H トレンド方向テキスト（右上）

    タイトル:
      "YYYY-MM-DD HH:MM LONG | 4H: SH↑SL↑ | 1H: SH↑SL↑ | neck=149.825"

    Args:
        df_5m:           5M OHLC DataFrame（ローソク足表示用）
        df_1h:           1H OHLC DataFrame（将来拡張用）
        df_4h:           4H OHLC DataFrame（将来拡張用）
        center_time:     プロット中心時刻
        direction:       'LONG' or 'SHORT'
        sh_4h_list:      [(timestamp, price), ...] 4H SH 系列
        sl_4h_list:      [(timestamp, price), ...] 4H SL 系列
        sh_1h_list:      [(timestamp, price), ...] 1H SH 系列
        sl_1h_list:      [(timestamp, price), ...] 1H SL 系列
        neck_4h:         4H ネックライン価格
        neck_break_time: ネック越え確定時刻
        save_path:       PNG 保存先パス
    """
    try:
        import mplfinance as mpf
    except ImportError:
        raise RuntimeError(
            "mplfinance が未インストールです。pip install mplfinance を実行してください。"
        )
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        raise RuntimeError("matplotlib が未インストールです")

    # ── 表示範囲 ──
    LEFT_BARS  = 2880   # 10日分（5M 足）
    RIGHT_BARS = 576    # 2日分（5M 足）

    center_loc = df_5m.index.searchsorted(center_time)
    i_start = max(0, center_loc - LEFT_BARS)
    i_end   = min(len(df_5m), center_loc + RIGHT_BARS + 1)
    df_view = df_5m.iloc[i_start:i_end].copy()

    if len(df_view) == 0:
        return

    t_start = df_view.index[0]
    t_end   = df_view.index[-1]

    # ── タイトル用トレンドラベル ──
    def _trend_label(sh_list: list, sl_list: list, d: str) -> str:
        if len(sh_list) < 2 or len(sl_list) < 2:
            return "?"
        if d == "LONG":
            sh_sym = "↑" if sh_list[-1][1] > sh_list[-2][1] else "↓"
            sl_sym = "↑" if sl_list[-1][1] > sl_list[-2][1] else "↓"
        else:
            sh_sym = "↓" if sh_list[-1][1] < sh_list[-2][1] else "↑"
            sl_sym = "↓" if sl_list[-1][1] < sl_list[-2][1] else "↑"
        return f"SH{sh_sym}SL{sl_sym}"

    trend_4h_label = _trend_label(sh_4h_list, sl_4h_list, direction)
    trend_1h_label = _trend_label(sh_1h_list, sl_1h_list, direction)
    neck_str = f"{neck_4h:.3f}" if neck_4h is not None else "N/A"
    title = (
        f"{center_time.strftime('%Y-%m-%d %H:%M')} {direction} | "
        f"4H: {trend_4h_label} | 1H: {trend_1h_label} | neck={neck_str}"
    )

    # ── 1H トレンド整合テキスト（右上）──
    is_1h_ok = False
    if len(sh_1h_list) >= 2 and len(sl_1h_list) >= 2:
        if direction == "LONG":
            is_1h_ok = (sh_1h_list[-1][1] > sh_1h_list[-2][1] and
                        sl_1h_list[-1][1] > sl_1h_list[-2][1])
        else:
            is_1h_ok = (sh_1h_list[-1][1] < sh_1h_list[-2][1] and
                        sl_1h_list[-1][1] < sl_1h_list[-2][1])
    if direction == "LONG":
        trend_text = "1H: HH + HL ✓" if is_1h_ok else "1H: HH + HL ?"
    else:
        trend_text = "1H: LH + LL ✓" if is_1h_ok else "1H: LH + LL ?"

    # ── mplfinance スタイル（既存と統一）──
    mc = mpf.make_marketcolors(up="#26a69a", down="#ef5350",
                               edge="inherit", wick="inherit", volume="in")
    style = mpf.make_mpf_style(
        marketcolors=mc, gridstyle=":", gridcolor="#444444",
        facecolor="#1a1a2e", figcolor="#1a1a2e",
        rc={"axes.labelcolor": "white", "axes.edgecolor": "#555555",
            "xtick.color": "white", "ytick.color": "white", "text.color": "white"},
    )

    fig, axes = mpf.plot(
        df_view,
        type="candle",
        style=style,
        figsize=(16, 9),
        returnfig=True,
        warn_too_much_data=9999,
        title=title,
    )
    ax = axes[0]

    # ── 4H SH: 水平線 + ビュー内ドット ──
    for ts, price in sh_4h_list:
        ax.axhline(y=price, color="#FF8C00", linewidth=2.5, linestyle="-", alpha=0.55)
        if t_start <= ts <= t_end:
            x = max(0, min(int(df_view.index.searchsorted(ts)), len(df_view) - 1))
            ax.scatter([x], [price], marker="v", color="#FF8C00", s=100, zorder=5)

    # ── 4H SL: 水平線 + ビュー内ドット ──
    for ts, price in sl_4h_list:
        ax.axhline(y=price, color="#1E90FF", linewidth=2.5, linestyle="-", alpha=0.55)
        if t_start <= ts <= t_end:
            x = max(0, min(int(df_view.index.searchsorted(ts)), len(df_view) - 1))
            ax.scatter([x], [price], marker="^", color="#1E90FF", s=100, zorder=5)

    # ── 4H ネックライン（太実線）──
    if neck_4h is not None:
        ax.axhline(y=neck_4h, color="#FF8C00", linewidth=3.0,
                   linestyle="-", alpha=0.95, zorder=4)

    # ── 4H ネック越えマーカー ──
    if neck_break_time is not None:
        nbx = int(df_view.index.searchsorted(neck_break_time))
        if 0 <= nbx < len(df_view):
            nb_price = float(df_view["Close"].iloc[nbx])
            marker = "^" if direction == "LONG" else "v"
            ax.scatter([nbx], [nb_price], marker=marker, color="#FF8C00",
                       s=300, zorder=7, edgecolors="white", linewidths=1.5)

    # ── 1H SH: ビュー内を折れ線で接続 ──
    sh_1h_in_view = [(ts, p) for ts, p in sh_1h_list if t_start <= ts <= t_end]
    if sh_1h_in_view:
        sh_x = [max(0, min(int(df_view.index.searchsorted(ts)), len(df_view) - 1))
                for ts, _ in sh_1h_in_view]
        sh_y = [p for _, p in sh_1h_in_view]
        ax.plot(sh_x, sh_y, color="#FA8072", linewidth=1.5,
                marker="o", markersize=5, zorder=4)

    # ── 1H SL: ビュー内を折れ線で接続 ──
    sl_1h_in_view = [(ts, p) for ts, p in sl_1h_list if t_start <= ts <= t_end]
    if sl_1h_in_view:
        sl_x = [max(0, min(int(df_view.index.searchsorted(ts)), len(df_view) - 1))
                for ts, _ in sl_1h_in_view]
        sl_y = [p for _, p in sl_1h_in_view]
        ax.plot(sl_x, sl_y, color="#87CEEB", linewidth=1.5,
                marker="o", markersize=5, zorder=4)

    # ── 1H トレンドテキスト（右上）──
    ax.text(0.99, 0.97, trend_text, transform=ax.transAxes,
            ha="right", va="top", color="white", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="#1a1a2e", alpha=0.8))

    # ── 凡例 ──
    legend_items = [
        mpatches.Patch(color="#FF8C00", label="4H SH / Neck"),
        mpatches.Patch(color="#1E90FF", label="4H SL"),
        mpatches.Patch(color="#FA8072", label="1H SH"),
        mpatches.Patch(color="#87CEEB", label="1H SL"),
    ]
    ax.legend(handles=legend_items, loc="upper left", fontsize=8,
              framealpha=0.3, facecolor="#1a1a2e", labelcolor="white")

    # ── 情報テキスト（下部）──
    n_sh1h_v = len(sh_1h_in_view)
    n_sl1h_v = len(sl_1h_in_view)
    info = (
        f"n(4H)=5  n(1H)=3  |  dir={direction}  |  "
        f"4H SH={len(sh_4h_list)} SL={len(sl_4h_list)}  |  "
        f"1H SH(view)={n_sh1h_v} SL(view)={n_sl1h_v}  |  bars={len(df_view)}"
    )
    fig.text(0.01, 0.01, info, fontsize=8, color="white",
             bbox=dict(boxstyle="round", facecolor="#1a1a2e", alpha=0.7))

    # ── PNG 保存 ──
    save_path_obj = Path(save_path)
    save_path_obj.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path_obj, dpi=150, bbox_inches="tight",
                facecolor="#1a1a2e", edgecolor="none")
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


# ── #020: 1H 押し目ウィンドウ 5M プロット ────────────────────────────────────


def plot_1h_window_5m(
    df_5m: pd.DataFrame,
    df_1h: pd.DataFrame,
    ts_sl_1h: pd.Timestamp,
    sl_4h: float,
    direction: str = 'LONG',
    pre_bars: int = 20,
    post_bars: int = 5,
    save_dir: str = 'logs/1h_windows',
) -> None:
    """
    1H 押し目ウィンドウ（前20本 + SL足 + 後5本 = 26本 ≈ 26時間）の
    5M OHLC + 5M SH/SL + 4H SL水平線 + 1H SL垂直線 を PNG 保存する。
    """
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    from swing_detector import detect_swing_highs, detect_swing_lows

    # ---- #024a: プロット専用範囲を 1H SL 基準の時間幅で切り出す ----
    # （スキャン窓 df_5m_win とは独立した変数）
    plot_start = ts_sl_1h - pd.Timedelta(hours=PLOT_PRE_H)
    plot_end   = ts_sl_1h + pd.Timedelta(hours=PLOT_POST_H)
    df_5m_win  = df_5m.loc[plot_start:plot_end].copy()
    if len(df_5m_win) < 10:
        return

    # ---- 5M SH / SL 検出（窓内限定）----
    sh_mask = detect_swing_highs(df_5m_win['high'], n=2)
    sl_mask = detect_swing_lows(df_5m_win['low'],   n=2)

    # ---- mplfinance スタイル ----
    mc = mpf.make_marketcolors(
        up='#26a69a', down='#ef5350',
        edge='inherit', wick='inherit', volume='in'
    )
    s = mpf.make_mpf_style(
        marketcolors=mc, facecolor='#131722',
        edgecolor='#444', gridcolor='#2a2e39'
    )

    # ---- addplot を使わず candle のみ描画（addplot は空 axes[1] を生成し白帯が出るバグ回避）----
    fig, axes = mpf.plot(
        df_5m_win,
        type='candle',
        style=s,
        returnfig=True,
        figsize=(16, 7),
    )
    ax = axes[0]
    # 余分な axes を非表示（addplot 由来の空パネルが残る場合の保険）
    for _ax in axes[1:]:
        _ax.set_visible(False)
    fig.patch.set_facecolor('#131722')
    ax.set_facecolor('#131722')

    # ---- 5M SH/SL マーカーを ax.scatter で手動描画（整数x軸に直接プロット）----
    sh_x = [j for j, v in enumerate(sh_mask) if v]
    sh_y = [float(df_5m_win['high'].iloc[j]) for j in sh_x]
    sl_x = [j for j, v in enumerate(sl_mask) if v]
    sl_y = [float(df_5m_win['low'].iloc[j]) for j in sl_x]
    if sh_x:
        ax.scatter(sh_x, sh_y, marker='v', s=60, color='#FA8072', zorder=5)
    if sl_x:
        ax.scatter(sl_x, sl_y, marker='^', s=60, color='#87CEEB', zorder=5)

    # ---- 4H SL 水平線 ----
    ax.axhline(y=sl_4h, color='#1E90FF', linewidth=1.5,
               linestyle='--', label=f'4H SL {sl_4h:.3f}')

    # ---- 1H SL 足の垂直線（整数インデックスで描画）----
    idx_in_win = df_5m_win.index.searchsorted(ts_sl_1h, side='left')
    if idx_in_win < len(df_5m_win):
        ax.axvline(x=idx_in_win, color='#ADFF2F',
                   linewidth=1.0, linestyle=':', label='1H SL')

    # ---- タイトル・凡例（英語タイトルに変更: CJK豆腐対策）----
    ts_str = ts_sl_1h.strftime('%Y%m%d_%H%M')
    ax.set_title(
        f'USDJPY 5M [{direction}]  1H SL: {ts_sl_1h}  '
        f'(pre{pre_bars} + SL + post{post_bars})',
        color='white', fontsize=11
    )
    ax.legend(facecolor='#1e222d', labelcolor='white', fontsize=9)
    ax.tick_params(colors='#aaa')

    # ---- 保存 ----
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    fname = save_path / f'{ts_str}_{direction}_1h_window.png'
    plt.savefig(fname, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved: {fname}")


if __name__ == '__main__':
    from swing_detector import (
        detect_swing_lows,
        get_nearest_swing_low,
        get_all_swing_lows_1h,
        get_direction_4h,
    )

    _DATA_PATH = Path(__file__).parent.parent / 'data/raw/usdjpy_multi_tf_2years.parquet'
    _df_raw = pd.read_parquet(_DATA_PATH)

    df_5m = _df_raw[["5M_Open", "5M_High", "5M_Low", "5M_Close"]].rename(
        columns={"5M_Open": "open", "5M_High": "high",
                 "5M_Low": "low", "5M_Close": "close"}
    )

    # ===== #020: 1H-4H 一致イベントの窓プロット =====

    # リサンプル（※ label='right', closed='right' — backtest.py と同一。変更禁止）
    def resample_tf(df, rule):
        return df.resample(rule, label='right', closed='right').agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
        ).dropna()

    df_4h = resample_tf(df_5m, '4h')
    df_1h = resample_tf(df_5m, '1h')

    MATCH_THRESH = 10.0  # pips（10pips以内を一致とみなす）
    MAX_PLOTS    = 20    # 最大プロット件数
    WARMUP       = 50
    WINDOW_1H    = 8     # 4H SL タイムスタンプ前後 ±8本

    plotted = 0
    for i in range(WARMUP, len(df_4h)):
        if plotted >= MAX_PLOTS:
            break
        ts_4h = df_4h.index[i]
        direction = get_direction_4h(
            df_4h['high'], df_4h['low'],
            current_idx=i, n=3, lookback=20
        )
        if direction != 'LONG':
            continue

        # 4H SL タイムスタンプ + 価格を取得
        start_4h = max(0, i - 20 + 1)
        window_4h = df_4h['low'].iloc[start_4h:i + 1]
        mask_4h = detect_swing_lows(window_4h, n=3)
        sl_4h_series = window_4h[mask_4h]
        if len(sl_4h_series) == 0:
            continue
        sl_4h = float(sl_4h_series.iloc[-1])
        sl_4h_ts = sl_4h_series.index[-1]

        # ±WINDOW_1H 本窓内で最近傍 1H SL を探す
        idx_1h_center = df_1h.index.searchsorted(sl_4h_ts, side='right') - 1
        if idx_1h_center < WINDOW_1H:
            continue
        win_s = max(0, idx_1h_center - WINDOW_1H)
        win_e = min(len(df_1h) - 1, idx_1h_center + WINDOW_1H)
        window_1h = df_1h['low'].iloc[win_s:win_e + 1]
        mask_1h = detect_swing_lows(window_1h, n=2)
        sl_1h_near = window_1h[mask_1h]
        if len(sl_1h_near) == 0:
            continue

        dists = abs(sl_1h_near - sl_4h)
        sl_1h_ts  = dists.idxmin()
        sl_1h_val = float(sl_1h_near[sl_1h_ts])
        dist = abs(sl_4h - sl_1h_val) / 0.01

        if dist <= MATCH_THRESH:
            plot_1h_window_5m(
                df_5m=df_5m,
                df_1h=df_1h,
                ts_sl_1h=sl_1h_ts,
                sl_4h=sl_4h,
                direction=direction,
            )
            plotted += 1

    print(f"\n合計 {plotted} 枚 → logs/1h_windows/")
