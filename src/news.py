"""GMニュース取得モジュール。

RSSフィードから投資・地政学関連ニュースを取得・フィルタし、
リンク先の og:description / meta description からサマリーを補完する。
"""
from __future__ import annotations

import re
from typing import Tuple

import feedparser
import requests

from configs.settings import GM_TITLE_KEYWORDS

RSS_SOURCES = [
    "https://news.yahoo.co.jp/rss/topics/money.xml",
    "https://news.yahoo.co.jp/rss/topics/world.xml",
    "https://news.yahoo.co.jp/rss/topics/business.xml",
    "https://www3.nhk.or.jp/news/rss/news_cat0.xml",
]


def get_gm_news(
    keywords: str = "CBDC US economy japan stock europe emerging geopolitics middle east ukraine",
    num_articles: int = 5,
) -> str:
    """GMキーワードニュース取得（投資・市場関連のみ表示）"""
    candidates = []

    for rss_url in RSS_SOURCES:
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                for entry in feed.entries:
                    candidates.append(entry)
                    if len(candidates) >= 80:
                        break
            if len(candidates) >= 80:
                break
        except Exception:
            pass

    filtered = []
    for entry in candidates:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        if any(kw in title for kw in GM_TITLE_KEYWORDS):
            filtered.append(entry)
        if len(filtered) >= num_articles:
            break

    if not filtered:
        return "投資・市場関連のニュースがありません（RSSまたはキーワードを確認）"

    headlines = [_format_entry(e, i + 1) for i, e in enumerate(filtered[:num_articles])]
    return "\n\n".join(headlines)


def _strip_html(text: str) -> str:
    """簡易HTMLタグ除去（RSSサマリー用）"""
    return re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()


def _fetch_summary_from_page(url: str, max_chars: int = 200) -> str:
    """リンク先ページから og:description または meta description を取得"""
    if not url or not url.startswith("http"):
        return ""
    try:
        r = requests.get(
            url,
            timeout=4,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
            },
        )
        r.raise_for_status()
        text = r.text
    except Exception:
        return ""
    m = re.search(
        r'<meta\s[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r'<meta\s[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']',
            text,
            re.I,
        )
    if not m:
        m = re.search(
            r'<meta\s[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            text,
            re.I,
        )
    if not m:
        return ""
    raw = m.group(1).replace("&nbsp;", " ").strip()
    raw = re.sub(r"\s+", " ", raw)
    return (raw[: max_chars - 3] + "...") if len(raw) > max_chars else raw


def _format_entry(entry, num: int = 0, fetch_page_summary: bool = True) -> str:
    """単一エントリをフォーマット（RSSサマリー優先、なければリンク先から取得）"""
    title = entry.get("title", "[タイトルなし]")
    link = entry.get("link", "#")
    raw = entry.get("summary") or entry.get("description") or ""
    if not raw and entry.get("content"):
        raw = entry["content"][0].get("value", "") if entry["content"] else ""
    raw = _strip_html(str(raw).strip())
    if not raw and fetch_page_summary and link.startswith("http"):
        raw = _fetch_summary_from_page(link)
    summary = (raw[:200] + "...") if len(raw) > 200 else (raw or "")

    if summary and (
        summary.startswith("サマリー:") or summary.startswith("サマリー：")
    ):
        summary = summary.split(":", 1)[-1].split("：", 1)[-1].strip()
    label = f"ニュース{num}" if num else "ニュース"
    lines = [f"{label}", f"タイトル: {title}", f"リンク: {link}"]
    if summary:
        lines.append(f"サマリー: {summary}")
    lines.append("---")
    return "\n".join(lines)
