"""REX_Trade_System エントリポイント。

使い方:
    python main.py                     # 対話モード
    python main.py --trade             # 8ペア30日データ＋プロット＋レジーム
    python main.py --news              # GMニュース取得
    python main.py --trade --news      # 両方
    python main.py "質問テキスト"       # ワンショットプロンプト
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from configs.rex_chat import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
