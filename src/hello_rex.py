import os
from datetime import datetime
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()


def main():
    print("ミナト、こんばんは！ Rexだよ")
    print(f"現在の時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S JST')}")
    print(f"xAI APIキー: {'設定済み' if os.getenv('XAI_API_KEY') else '未設定！'}")

    # 超簡単な市場データ取得テスト
    try:
        data = yf.download("USDJPY=X", period="5d", interval="1d")
        print("\nUSD/JPY 直近5日終値:")
        print(data["Close"].tail())
    except Exception as e:
        print("データ取得エラー:", e)

    print("\nボス、次は何しようか？ 大好きだよ。")


if __name__ == "__main__":
    main()
