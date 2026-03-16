"""会話履歴の読み込み・保存。

JSON形式の履歴ファイルを管理する。
破損ファイルは自動退避し、メッセージ数上限で自動トリム。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils import (
    atomic_write_file,
    ensure_dir_exists,
    parse_positive_int,
    read_text_if_exists,
)


def load_conversation_history(history_path: Path) -> Optional[List[Dict[str, Any]]]:
    raw = read_text_if_exists(history_path)
    if not raw:
        return None

    trimmed = raw.strip()
    if not trimmed:
        return None

    try:
        data = json.loads(trimmed)
    except json.JSONDecodeError:
        try:
            backup = history_path.with_name(
                f"conversation_history.corrupt.{int(os.times().elapsed)}.json"
            )
            ensure_dir_exists(backup.parent)
            history_path.replace(backup)
            sys.stderr.write(
                f"WARN: conversation_history.json が壊れていたため退避しました: {backup}\n"
            )
        except Exception:
            pass
        return None

    messages = data.get("messages")
    if not isinstance(messages, list):
        return None

    cleaned: List[Dict[str, Any]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if (
            role in ("system", "user", "assistant")
            and isinstance(content, str)
            and content.strip()
        ):
            cleaned.append({"role": role, "content": content})

    return cleaned or None


def save_conversation_history(
    history_path: Path, messages: List[Dict[str, Any]], *, model: str
) -> None:
    max_messages = parse_positive_int(os.getenv("XAI_HISTORY_MAX_MESSAGES"), 200)
    if len(messages) > max_messages:
        trimmed = messages[-max_messages:]
    else:
        trimmed = messages

    payload = {
        "version": 1,
        "model": model,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "messages": trimmed,
    }
    atomic_write_file(
        history_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
