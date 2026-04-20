"""mtf_minato_short_v2 の完全 print 出力＆条件診断スクリプト。

実行: python src/print_signals_analysis.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.signals import mtf_minato_short_v2


def main() -> None:
    print("=" * 70)
    print("  mtf_minato_short_v2 関数の完全ソース")
    print("=" * 70)
    print(inspect.getsource(mtf_minato_short_v2))
    print("=" * 70)
    print("  診断完了（詳細は docs/SIGNALS_SHORT_ANALYSIS.md 参照）")
    print("=" * 70)


if __name__ == "__main__":
    main()
