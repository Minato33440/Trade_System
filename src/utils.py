"""共通ユーティリティ関数。

ファイル操作・型変換など、複数モジュールで使う汎用ヘルパー。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


def ensure_dir_exists(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text_if_exists(path: Path) -> Optional[str]:
    try:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def parse_positive_int(value: Any, fallback: int) -> int:
    try:
        n = int(str(value))
    except Exception:
        return fallback
    return n if n > 0 else fallback


def atomic_write_file(path: Path, content: str) -> None:
    ensure_dir_exists(path.parent)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{int(os.times().elapsed)}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
