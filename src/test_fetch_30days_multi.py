# test_fetch_30days_multi.py - 複数ペアの30日データ取得 & 分析
# FutureWarning対策: float(iloc)ラップ済み。yfinance優先、Polygonキーでフォールバック。
import datetime
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# リポジトリルートを path に追加して src.data_fetch をインポート可能にする
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
load_dotenv(_repo_root / ".env")
from src.data_fetch import fetch_market_data  # noqa: E402

end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

# 対象ペアリスト (yfinanceティッカー) — 8ペア対応
pairs = {
    "USD/JPY": "USDJPY=X",
    "US100": "^NDX",
    "XAU/USD": "GC=F",
    "WTI": "CL=F",
    "US2Y": "^FVX",
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "BTC/USD": "BTC-USD",
}

print(f"取得期間: {start_date} 〜 {end_date} (JST基準)\n")

df_all = pd.DataFrame()
for name, ticker in pairs.items():
    data = fetch_market_data(ticker, start_date, end_date)
    if not data.empty:
        print(f"{name} (30日終値):")
        print(data.tail(10))
        latest = float(data.iloc[-1])
        first = float(data.iloc[0])
        change_30d = (latest - first) / first * 100
        print(f"最新: {latest:.3f} (30日変化: {change_30d:+.2f}%)\n")
        df_all[name] = data
    else:
        print(f"{name}取得失敗\n")

if not df_all.empty:
    df_all = df_all.dropna(how="all")

    # ペアワイズ相関係数
    corr_matrix = df_all.corr()
    print("30日相関係数行列:\n", corr_matrix)

    # 正規化プロット (複数線)
    if HAS_MATPLOTLIB:
        df_norm = (df_all - df_all.min()) / (df_all.max() - df_all.min())
        plt.figure(figsize=(14, 8))
        for col in df_norm.columns:
            plt.plot(df_norm[col], label=col)
        plt.title("8ペア正規化比較 (30日)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.grid(True)
        plt.tight_layout()
        out_dir = _repo_root / "logs" / "png_data"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "multi_pairs_plot_8.png"
        plt.savefig(out_path)
        plt.show()
        print(f"\nプロットを '{out_path}' に保存しました。アプリに貼り付け可能！")
    else:
        print("\n(プロット表示には pip install matplotlib で matplotlib を入れてください)")
else:
    print("全データ取得失敗")
