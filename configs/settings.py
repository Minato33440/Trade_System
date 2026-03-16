"""REX_Trade_System 共通設定（ティッカー定義・定数・パス）。

全モジュールはここから定数を import する。
ティッカーの追加・変更はこのファイルだけで完結させる。
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

# ── プロジェクトルート ────────────────────────────────
ROOT_DIR: Path = Path(__file__).resolve().parents[1]

# ── ティッカー定義 ────────────────────────────────────
# 対話モード（get_market_snapshot）用
CORE_TICKERS: Dict[str, str] = {
    "USD/JPY": "USDJPY=X",
    "EUR/USD": "EURUSD=X",
    "XAU/USD (金)": "GC=F",
    "BTC/USD": "BTC-USD",
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "US2Y": "^FVX",   # 実体は5年債。2年債の直接取得は困難なため代用
    "JP10Y": "^TNX",   # 日本10年債は直接取得困難。US10Yで代用（暫定）
}

FULL_TICKERS: Dict[str, str] = {
    **CORE_TICKERS,
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X",
    "US100 (ナスダック)": "^NDX",
    "SP500": "^GSPC",
    "JP225 (日経)": "^N225",
    "Copper (銅)": "HG=F",
    "WTI": "CL=F",
    "JP2Y": "^FVX",   # 仮置き
}

# --trade 用 8ペア（レジーム判定の入力）
TRADE_PAIRS: Dict[str, str] = {
    "USD/JPY": "USDJPY=X",
    "US100": "^NDX",
    "XAU/USD": "GC=F",
    "WTI": "CL=F",
    "US2Y": "^FVX",
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "BTC/USD": "BTC-USD",
}

# ── GMニュースフィルタ用キーワード ────────────────────
GM_TITLE_KEYWORDS: Tuple[str, ...] = (
    "株",
    "株式",
    "市場",
    "金融",
    "為替",
    "円安",
    "円高",
    "円相場",
    "ドル安",
    "ドル高",
    "ドル円",
    "金利",
    "利上げ",
    "利下げ",
    "米国",
    "日本",
    "中東",
    "イラン",
    "ホルムズ海峡",
    "ウクライナ",
    "ロシア",
    "FRB",
    "日銀",
    "ECB",
    "原油",
    "金価格",
    "地政",
    "BRICS",
    "CBDC",
    "債券",
    "インフレ",
    "景気",
    "GDP",
    "欧州",
    "中国",
    "相場",
    "下落",
    "高騰",
    "利回り",
    "テロ",
    "戦争",
    "制裁",
    "株価",
)

# ── ログ出力先（ROOT_DIR 基準で統一） ─────────────────
LOGS_DIR: Path = ROOT_DIR / "logs"
PNG_DATA_DIR: Path = LOGS_DIR / "png_data"
TEXT_LOG_DIR: Path = LOGS_DIR / "text_log"
