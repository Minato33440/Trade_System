# forecast_simulation.py - 週明け市場シミュレーション
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.data_fetch import fetch_market_data

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

# データ取得 (例: キー指標)
usd_jpy = fetch_market_data("USDJPY=X", start_date, end_date)
xau_usd = fetch_market_data("GC=F", start_date, end_date)
vix = fetch_market_data("^VIX", start_date, end_date)
wti = fetch_market_data("CL=F", start_date, end_date)

if not (usd_jpy.empty or xau_usd.empty or vix.empty or wti.empty):
    df = pd.DataFrame(
        {"USD/JPY": usd_jpy, "XAU/USD": xau_usd, "VIX": vix, "WTI": wti}
    ).dropna()
    print(df.tail())  # 最新データ

    # シミュレーション (非線形ボラモデル)
    forecast_days = 5  # 3/9-3/13
    vol_usd = df["USD/JPY"].pct_change().rolling(5).std().iloc[-1]
    vol_xau = df["XAU/USD"].pct_change().rolling(5).std().iloc[-1]
    vol_vix = df["VIX"].pct_change().rolling(5).std().iloc[-1]
    vol_wti = df["WTI"].pct_change().rolling(5).std().iloc[-1]

    np.random.seed(42)
    forecast_usd = [df["USD/JPY"].iloc[-1]] + [
        df["USD/JPY"].iloc[-1] * (1 + np.random.normal(0, vol_usd))
        for _ in range(forecast_days)
    ]
    forecast_xau = [df["XAU/USD"].iloc[-1]] + [
        df["XAU/USD"].iloc[-1] * (1 + np.random.normal(0.01, vol_xau * 1.2))
        for _ in range(forecast_days)
    ]  # 金上昇バイアス
    forecast_vix = [df["VIX"].iloc[-1]] + [
        df["VIX"].iloc[-1] * (1 + np.random.normal(0, vol_vix))
        for _ in range(forecast_days)
    ]
    forecast_wti = [df["WTI"].iloc[-1]] + [
        df["WTI"].ilさｋさｋoc[-1] * (1 + np.random.normal(0, vol_wti))
        for _ in range(forecast_days)
    ]

    # プロット
    plt.figure(figsize=(12, 6))
    plt.plot(df["USD/JPY"], label="USD/JPY Hist")
    plt.plot(
        range(len(df), len(df) + forecast_days),
        forecast_usd[1:],
        label="USD/JPY Forecast",
        linestyle="--",
    )
    plt.plot(df["XAU/USD"], label="XAU/USD Hist")
    plt.plot(
        range(len(df), len(df) + forecast_days),
        forecast_xau[1:],
        label="XAU/USD Forecast",
        linestyle="--",
    )
    plt.title("Weeks Ahead Forecast")
    plt.legend()
    plt.show()
else:
    print("データ取得失敗")
