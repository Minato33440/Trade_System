"""Grok (xAI) API 通信モジュール。

chat/completions エンドポイントへのリクエスト送信、
リトライ・タイムアウト制御を担当する。
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests

from src.utils import parse_positive_int


def _get_request_timeout() -> int:
    """環境変数 XAI_REQUEST_TIMEOUT（秒）。未設定なら 180。"""
    return parse_positive_int(os.getenv("XAI_REQUEST_TIMEOUT"), 180)


def _get_max_retries() -> int:
    """環境変数 XAI_MAX_RETRIES。未設定なら 5。"""
    return parse_positive_int(os.getenv("XAI_MAX_RETRIES"), 5)


def call_grok_chat_completions(
    *, api_key: str, model: str, messages: List[Dict[str, str]]
) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"model": model, "messages": messages}
    timeout_sec = _get_request_timeout()
    max_retries = _get_max_retries()
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=timeout_sec)
            try:
                data = resp.json()
            except Exception:
                data = {}

            if not resp.ok:
                detail = json.dumps(data, ensure_ascii=False)
                if 500 <= resp.status_code < 600 and attempt < max_retries - 1:
                    last_error = RuntimeError(
                        f"HTTP {resp.status_code} {resp.reason}: {detail}"
                    )
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise RuntimeError(f"HTTP {resp.status_code} {resp.reason}: {detail}")

            text = (
                data.get("choices")
                and isinstance(data["choices"], list)
                and data["choices"][0].get("message", {}).get("content")
            )
            if not isinstance(text, str):
                raise RuntimeError(
                    f"Unexpected response: {json.dumps(data, ensure_ascii=False)}"
                )
            return text

        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                sys.stderr.write(
                    f"WARN: リクエストが {timeout_sec}秒でタイムアウトしました。"
                    f" {wait}秒後にリトライ ({attempt + 1}/{max_retries})…\n"
                )
                time.sleep(wait)
                continue
            raise RuntimeError(
                f"xAI API が {timeout_sec}秒以内に応答しませんでした（{max_retries}回試行）。"
                " ネットワークまたは api.x.ai の負荷を確認してください。"
            ) from e
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(
                f"通信エラー: {e}. ネットワークを確認してください。"
            ) from e

    if last_error is not None:
        raise last_error
    raise RuntimeError("xAI API 呼び出しに失敗しました。")
