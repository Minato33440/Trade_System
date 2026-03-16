# src/data_fetch.py
# Rex作成: GMトレード用データフェッチモジュール。
# yfinance優先、失敗時Polygonフォールバック。週末・非線形シンクロニシティ検知を考慮したロバスト設計。

from __future__ import annotations

import os
import time
from datetime import date, datetime, timedelta
from typing import Optional
from pathlib import Path

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

# プロジェクトルート
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"

# APIキー読み込み
POLYGON_API_KEY: Optional[str] = (
    os.getenv("POLYGON_API_KEY") or os.getenv("Polygon_API_KEY")
)

# Polygon用ティッカー変換（yfinance → Polygon表記）
def _yf_to_polygon_ticker(yf_ticker: str) -> str:
    """yfinanceティッカーをPolygon用に変換。未対応はそのまま返す。"""
    s = yf_ticker.strip().upper()
    if s.endswith("=X"):  # 通貨ペア
        return "C:" + s.replace("=X", "")
    if s == "GC=F":
        return "C:XAUUSD"
    if s in ("CL=F", "WTI"):
        return "C:WTICO"
    if s == "BTC-USD":
        return "X:BTCUSD"
    if s.startswith("^"):
        return s  # 指数はPolygonで別体系のためそのまま試す
    return s


def _parse_timeframe(tf: str) -> tuple[int, str]:
    """
    "5min", "15min", "1h", "4h", "1d" などをPolygonの (multiplier, timespan) に変換。
    例: "5min" -> (5, "minute"), "1h" -> (1, "hour"), "1d" -> (1, "day")
    """
    tf = tf.lower().strip()
    if "min" in tf:
        return int(tf.replace("min", "")), "minute"
    elif "h" in tf:
        return int(tf.replace("h", "")), "hour"
    elif "d" in tf:
        return int(tf.replace("d", "")), "day"
    else:
        # デフォルトは1分足
        return 1, "minute"


def fetch_polygon_aggs(ticker, start, end, multiplier=1, timespan="minute"):
    """
    Polygonからaggsを取得（月ごと分割でレート制限回避）。
    無料版: 5 req/min制限 → 12秒間隔で安全に取得。
    """
    if not POLYGON_API_KEY:
        print("Polygon API key not found in .env", flush=True)
        return pd.DataFrame()
    
    try:
        from polygon import RESTClient
    except ImportError:
        print("polygon-api-client not installed. Run: pip install polygon-api-client", flush=True)
        return pd.DataFrame()
    
    client = RESTClient(api_key=POLYGON_API_KEY)
    data = []
    current_start = start
    
    while current_start < end:
        current_end = min(current_start + timedelta(days=90), end)  # 3ヶ月ごとに分割
        try:
            print(f"  Fetching {ticker} {timespan} {current_start.date()} ~ {current_end.date()}...", flush=True)
            aggs = client.get_aggs(
                ticker,
                multiplier,
                timespan,
                current_start.strftime("%Y-%m-%d"),
                current_end.strftime("%Y-%m-%d"),
                limit=50000
            )
            if aggs:
                rows = []
                for agg in aggs:
                    rows.append({
                        'timestamp': pd.Timestamp(agg.timestamp, unit='ms', tz='UTC'),
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close,
                        'volume': agg.volume,
                    })
                if rows:
                    df_chunk = pd.DataFrame(rows).set_index('timestamp')
                    data.append(df_chunk)
                    print(f"    → {len(df_chunk)} bars", flush=True)
            time.sleep(12)  # レートリミット5req/min対策（12秒待機）
        except Exception as e:
            print(f"  Polygon error for {current_start}~{current_end}: {e}", flush=True)
        current_start = current_end
    
    if data:
        return pd.concat(data).sort_index()
    return pd.DataFrame()


def fetch_market_data(
    ticker: str,
    start_date: date,
    end_date: date,
    multiplier: int = 1,
    timespan: str = "day",
) -> pd.Series:
    """
    yfinance優先でデータ取得。失敗/空ならPolygonにフォールバック（キー設定時のみ）。
    週末はヒストリカルデータで対応。

    :param ticker: yfinanceティッカー (e.g. 'USDJPY=X', 'GC=F')
    :param start_date: 開始日
    :param end_date: 終了日
    :param multiplier: Polygon用
    :param timespan: Polygon用 (e.g. 'day')
    :return: 終値の pd.Series（失敗時は空のSeries）
    """
    # yfinance試行
    try:
        data = yf.download(
            ticker, start=start_date, end=end_date, progress=False
        )
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            raise ValueError(f"yfinance returned empty data for {ticker}")
        close = data["Close"] if isinstance(data, pd.DataFrame) else data
        if hasattr(close, "empty") and close.empty:
            raise ValueError(f"yfinance Close empty for {ticker}")
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()
        return close.copy() if isinstance(close, pd.Series) else pd.Series(close)
    except Exception as e:
        print(f"yfinance failed for {ticker}: {e}. Falling back to Polygon.")

    # Polygonフォールバック（キーがある場合のみ）
    if not POLYGON_API_KEY:
        print("POLYGON_API_KEY / Polygon_API_KEY not set. Skipping Polygon.")
        return pd.Series()

    try:
        from polygon import RESTClient

        client = RESTClient(POLYGON_API_KEY)
        polygon_ticker = _yf_to_polygon_ticker(ticker)
        from_str = start_date.strftime("%Y-%m-%d")
        to_str = end_date.strftime("%Y-%m-%d")

        aggs = client.get_aggs(
            polygon_ticker, multiplier, timespan, from_str, to_str
        )
        rows = []
        for agg in aggs:
            rows.append(
                {
                    "date": pd.Timestamp(agg.timestamp, unit="ms"),
                    "close": agg.close,
                }
            )
        if not rows:
            raise ValueError(f"Polygon returned no data for {polygon_ticker}")
        df = pd.DataFrame(rows).set_index("date").sort_index()
        return df["close"]
    except ImportError:
        print("polygon package not installed. Install with: pip install polygon-api-client")
        return pd.Series()
    except Exception as poly_e:
        print(f"Polygon failed: {poly_e}")
        return pd.Series()


def fetch_multi_tf(
    ticker: str = "USDJPY=X",
    years: int = 2,
    timeframe_list: list[str] = None,
    use_polygon: bool = True,
) -> pd.DataFrame:
    """
    Polygon無料版優先で直近years年分のmulti-timeframeデータを取得。
    保存: data/raw/usdjpy_multi_tf_{years}years.parquet
    失敗時はyfinanceフォールバック（ただし短期足は60日制限あり）。
    
    列名は signals.py 互換のプレフィックスに変換:
    - "5min" -> "5M_"
    - "15min" -> "15M_"
    - "1h" -> "1H_"
    - "4h" -> "4H_"
    - "1d" -> "D_"
    
    :param ticker: yfinanceティッカー（例: "USDJPY=X"）
    :param years: 取得年数（無料は最大2年）
    :param timeframe_list: 取得する時間枠リスト（例: ["5min", "15min", "1h", "4h"]）
    :param use_polygon: True なら Polygon 優先、False なら yfinance のみ
    :return: フラットな列名の DataFrame (e.g., "5M_open", "1H_close")
    """
    if timeframe_list is None:
        timeframe_list = ["5min", "15min", "1h", "4h", "1d"]
    
    # data/raw/ ディレクトリ作成
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    end = datetime.now()
    start = end - timedelta(days=365 * years)
    
    all_dfs = {}
    success = False
    
    # Polygon優先（キーありかつuse_polygon=Trueの場合）
    if use_polygon and POLYGON_API_KEY:
        polygon_ticker = _yf_to_polygon_ticker(ticker)
        print(f"Polygon無料版で取得開始: {polygon_ticker} {years}年分", flush=True)
        
        for tf in timeframe_list:
            try:
                multiplier, timespan = _parse_timeframe(tf)
                print(f"\n[{tf}] Polygon取得中...", flush=True)
                df = fetch_polygon_aggs(polygon_ticker, start, end, multiplier=multiplier, timespan=timespan)
                if not df.empty:
                    all_dfs[tf] = df
                    success = True
                    print(f"  {tf} 取得成功: {len(df)} 本", flush=True)
                else:
                    print(f"  {tf} Polygon失敗: 0本", flush=True)
            except Exception as e:
                print(f"  {tf} Polygon失敗: {e}", flush=True)
    
    # Polygon失敗 or 空 → yfinanceフォールバック
    if not success or not all_dfs:
        print("\nPolygon失敗 → yfinanceフォールバック使用", flush=True)
        yf_ticker = ticker
        for tf in timeframe_list:
            interval_map = {"5min": "5m", "15min": "15m", "1h": "1h", "4h": "4h", "1d": "1d", "day": "1d"}
            interval = interval_map.get(tf, "1d")
            try:
                print(f"[{tf}] yfinance取得中...", flush=True)
                df = yf.download(yf_ticker, start=start, end=end, interval=interval, progress=False)
                if not df.empty:
                    # 列名の正規化
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                    })
                    all_dfs[tf] = df
                    print(f"  yfinance {tf} 取得成功: {len(df)} 本", flush=True)
            except Exception as e:
                print(f"  yfinance {tf} 失敗: {e}", flush=True)
    
    # 4H フォールバック: 取得失敗時は 1h から resample で生成
    if "4h" not in all_dfs and "1h" in all_dfs:
        print("\n[INFO] 4h取得失敗 → 1hからresampleで生成", flush=True)
        df_1h = all_dfs["1h"]
        df_4h = df_1h.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        if not df_4h.empty:
            all_dfs["4h"] = df_4h
            print(f"  4h生成成功: {len(df_4h)} 本", flush=True)
    
    if all_dfs:
        # 列名を統一（open -> Open, close -> Close など）
        for tf in all_dfs:
            df = all_dfs[tf]
            if 'open' in df.columns:
                df.columns = [c.capitalize() for c in df.columns]
                all_dfs[tf] = df
        
        # timeframe名を signals.py 互換に変換
        tf_map = {
            "5min": "5M",
            "15min": "15M",
            "1h": "1H",
            "4h": "4H",
            "1d": "D"
        }
        renamed_dfs = {}
        for tf_key, df in all_dfs.items():
            new_key = tf_map.get(tf_key, tf_key.upper())
            renamed_dfs[new_key] = df
        
        # 全時間枠の index を結合（outer join）
        all_indices = pd.DatetimeIndex([])
        for df in renamed_dfs.values():
            all_indices = all_indices.union(df.index)
        all_indices = all_indices.sort_values()
        
        # 各tf を結合し、列名プレフィックスを付与
        combined = pd.DataFrame(index=all_indices)
        for tf_prefix, df in renamed_dfs.items():
            # 各列にプレフィックスを付与
            df_prefixed = df.copy()
            df_prefixed.columns = [f"{tf_prefix}_{col}" for col in df.columns]
            # outer join
            combined = combined.join(df_prefixed, how='outer')
        
        # 保存
        base_name = ticker.replace("=X", "").replace(":", "").lower()
        save_path = RAW_DATA_DIR / f"{base_name}_multi_tf_{years}years.parquet"
        combined.to_parquet(save_path)
        print(f"\n[OK] 保存完了: {save_path}", flush=True)
        print(f"     Shape: {combined.shape}", flush=True)
        print(f"     列: {list(combined.columns)[:10]}...", flush=True)
        return combined
    else:
        print("\n[FAILED] 全ソース失敗。データ取得できませんでした。", flush=True)
        return pd.DataFrame()


# テスト実行
if __name__ == "__main__":
    import sys
    print("=" * 60, flush=True)
    print("Polygon無料版テスト: 直近2年 5min/15min/1h/4h/1d データ取得", flush=True)
    print("=" * 60, flush=True)
    print("WARNING: レート制限により取得に時間がかかります（約6〜8分）", flush=True)
    print("-" * 60, flush=True)
    
    df_multi = fetch_multi_tf(
        ticker="USDJPY=X",
        years=2,
        timeframe_list=["5min", "15min", "1h", "4h", "1d"],
        use_polygon=True
    )
    if not df_multi.empty:
        print("\n[SUCCESS] データサンプル:", flush=True)
        print("  5M_Close最後の3行:", df_multi['5M_Close'].tail(3).values if '5M_Close' in df_multi.columns else 'N/A', flush=True)
        print("  15M_Close最後の3行:", df_multi['15M_Close'].tail(3).values if '15M_Close' in df_multi.columns else 'N/A', flush=True)
        print("  1H_Close最後の3行:", df_multi['1H_Close'].tail(3).values if '1H_Close' in df_multi.columns else 'N/A', flush=True)
        print("  4H_Close最後の3行:", df_multi['4H_Close'].tail(3).values if '4H_Close' in df_multi.columns else 'N/A', flush=True)
        print("  D_Close最後の3行:", df_multi['D_Close'].tail(3).values if 'D_Close' in df_multi.columns else 'N/A', flush=True)
    else:
        print("\n[FAILED] データ取得失敗", flush=True)
