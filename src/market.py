"""市場データ取得・スナップショット生成モジュール。

yfinance によるリアルタイム/ヒストリカルデータ取得、
フォーマット出力を担当する。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from configs.settings import CORE_TICKERS, FULL_TICKERS, TRADE_PAIRS
from src.data_fetch import fetch_market_data


def get_market_snapshot(full_mode: bool = False) -> Dict[str, Dict[str, Any]]:
    """対話モード用: 直近5日のスナップショットを取得。"""
    tickers = FULL_TICKERS if full_mode else CORE_TICKERS
    snapshot: Dict[str, Dict[str, Any]] = {}
    for name, symbol in tickers.items():
        try:
            data = yf.download(symbol, period="5d", progress=False)

            if data.empty:
                snapshot[name] = {"error": "データ空 (yfinanceから空DF返却)"}
                continue

            close_series = data["Close"]
            if close_series.empty:
                snapshot[name] = {"error": "Close列が空"}
                continue

            latest = float(close_series.iloc[-1])
            prev = float(close_series.iloc[-2]) if len(close_series) >= 2 else None
            change_pct = ((latest - prev) / prev * 100) if prev is not None else 0.0
            snapshot[name] = {
                "latest": round(latest, 4 if "/" in name or "VIX" in name else 2),
                "change_pct": round(change_pct, 2),
            }
        except Exception as e:
            snapshot[name] = {"error": str(e)}
    return snapshot


def get_current_market_snapshot(
    tickers: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """チャット内で市場データをフェッチ（yfinance優先、Polygonフォールバック）。"""
    if tickers is None:
        tickers = ["USDJPY=X", "GC=F"]
    end_d = date.today()
    start_d = end_d - timedelta(days=7)
    snapshot: Dict[str, Dict[str, Any]] = {}
    for ticker in tickers:
        data = fetch_market_data(ticker, start_d, end_d)
        if data is not None and not data.empty:
            latest = float(data.iloc[-1])
            change = (
                (float(data.iloc[-1]) - float(data.iloc[-2]))
                / float(data.iloc[-2])
                * 100
                if len(data) >= 2
                else 0.0
            )
            snapshot[ticker] = {
                "latest": round(latest, 4 if "=X" in ticker or "=F" in ticker else 2),
                "change_pct": round(change, 2),
            }
        else:
            snapshot[ticker] = {"error": "Data fetch failed"}
    return snapshot


def format_snapshot(snapshot: Dict[str, Dict[str, Any]]) -> str:
    """スナップショットをテキスト表示用にフォーマット。"""
    lines = ["トレードモード起動！ 最新市場スナップショット（yfinanceより）:"]
    lines.append(f"現在時刻: {datetime.now().strftime('%Y/%m/%d %H:%M JST')}")
    lines.append("")

    groups = {
        "為替": [k for k in snapshot if ("/" in k and "JPY" in k) or "USD" in k],
        "指数": [k for k in snapshot if "US100" in k or "SP500" in k or "JP225" in k],
        "商品・暗号": [
            k
            for k in snapshot
            if "XAU" in k or "BTC" in k or "Copper" in k or "WTI" in k
        ],
        "金利・ボラ": [k for k in snapshot if "Y" in k or "VIX" in k],
    }

    for group_name, keys in groups.items():
        if any(k in snapshot for k in keys):
            lines.append(f"【{group_name}】")
            for key in keys:
                if key in snapshot:
                    info = snapshot[key]
                    if "error" in info:
                        lines.append(
                            f"{key}: 取得失敗 → {info['error'][:100]}..."
                        )
                    else:
                        lines.append(
                            f"{key}: {info['latest']} (前日比 {info['change_pct']:+.2f}%)"
                        )
            lines.append("")

    lines.append("ボス、この状況で何が気になる？ シフトの予兆？ ポジション考えようか？")
    return "\n".join(lines)


def fetch_trade_data(
    days: int = 30,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]], str]:
    """
    --trade 用: TRADE_PAIRS の30日データを取得し、
    DataFrame・ペアスナップショット・テキストサマリーを返す。
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    df_all = pd.DataFrame()
    pair_snapshots: Dict[str, Dict[str, float]] = {}
    output_lines = [
        f"取得期間: {start_date} 〜 {end_date} (JST基準)",
        "",
    ]

    for name, ticker in TRADE_PAIRS.items():
        data = fetch_market_data(ticker, start_date, end_date)
        if not data.empty:
            latest = float(data.iloc[-1])
            first = float(data.iloc[0])
            change_30d = (latest - first) / first * 100
            output_lines.append(
                f"{name}: 最新 {latest:.3f} (30日変化: {change_30d:+.2f}%)"
            )
            df_all[name] = data
            pair_snapshots[name] = {
                "latest": latest,
                "change_30d": change_30d,
            }
        else:
            output_lines.append(f"{name}: データ取得失敗")

    return df_all, pair_snapshots, "\n".join(output_lines)
