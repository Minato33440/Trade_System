202022"""日次GMレポートからキーワード・数値・トレンドブロックをパースする（半自動スクリプト）。

週末更新時に review.md / meta.yaml / distilled 編集用の構造化データを出力する。
入力: 基準日（例: 2026-3-14）または週ID
出力: JSON または Python dict（Rex や手動編集の入力に利用）

使用例:
  python src/daily_report_parser.py --date 2026-3-14
  python src/daily_report_parser.py --date 2026-3-14 --json
  python src/daily_report_parser.py --week-id 2026-3-14_wk11 --json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートを path に追加
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_repo_root))

from configs.settings import LOGS_DIR  # noqa: E402

# 日次レポート配置（logs/gm/daily/YYYY/gm_report/）
DAILY_REPORT_BASE = LOGS_DIR / "gm" / "daily"

# GMキーワード（地政学・イベント検出用）
GM_KEYWORDS = (
    "イラン", "ホルムズ", "地政", "FRB", "日銀", "ECB", "BOJ", "CPI", "GDP",
    "ウクライナ", "ロシア", "中東", "介入", "利上げ", "利下げ", "原油", "金価格",
    "ドル円", "円安", "円高", "BRICS", "CBDC", "全人代", "雇用統計", "FOMC",
    "テロ", "戦争", "制裁", "リスクオフ", "リスクオン",
)

# 主要数値パターン（抽出対象）
VALUE_PATTERNS = [
    (r"S&P500[:\s]*([\d,.]+)", "S&P500"),
    (r"VIX[:\s]*([\d,.]+)", "VIX"),
    (r"WTI[^:]*[:\s]*([\d,.]+)", "WTI"),
    (r"ドル円[^:]*[:\s]*([\d,.]+)", "ドル円"),
    (r"米10年債利回り[:\s]*([\d,.]+)%?", "米10年債"),
    (r"日経平均[^:]*[:\s]*([\d,.]+)", "日経平均"),
    (r"ダウ平均[:\s]*([\d,.]+)", "ダウ平均"),
    (r"ナスダック100[:\s]*([\d,.]+)", "ナスダック100"),
    (r"XAU[/\s]USD[^:]*[:\s]*([\d,.]+)", "XAU/USD"),
]

# トレンドブロック正規表現
TREND_BLOCK_RE = re.compile(
    r"【([^/]+)/中期トレンド判断\(参考\)】\s*\n(.*?)(?=\n【|$)",
    re.DOTALL,
)
CORE_BLOCK_RE = re.compile(r"<コア>\s*\n(.*?)(?=<サテライト|<コア|\n\n|$)", re.DOTALL)
SATELLITE_BLOCK_RE = re.compile(
    r"<サテライト[^>]*>\s*\n(.*?)(?=<コア|\(実際のトレード|【|\n\n\n|$)",
    re.DOTALL,
)
STRATEGY_BLOCK_RE = re.compile(
    r"【([^/]+)のトレード戦略の考え方】\s*\n(.*?)(?=\n【|\n▽|$)",
    re.DOTALL,
)
CALENDAR_RE = re.compile(
    r"▽(\d+)\s*月(\d+)\s*日[〜~]((?:\d+)\s*月)?(\d+)\s*日の?(?:主な経済指標・)?予定\s*\n(.*?)(?=\n【|\n▽|$)",
    re.DOTALL,
)
DATE_LINE_RE = re.compile(r"記載日[：:]\s*(\d{4})[/／](\d{1,2})[/／](\d{1,2})")


def _parse_date_from_line(line: str) -> Optional[date]:
    """記載日行から date をパース。"""
    m = DATE_LINE_RE.search(line)
    if m:
        y, mon, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mon, d)
        except ValueError:
            pass
    return None


def _normalize_filename_to_date(filename: str) -> Optional[date]:
    """ファイル名（2026-3-2 や 2026-03-13）から date を推測。"""
    base = Path(filename).stem
    parts = re.split(r"[-_]", base)
    if len(parts) >= 3:
        try:
            y, mon, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, mon, d)
        except (ValueError, IndexError):
            pass
    m = re.match(r"(\d{4})-?(\d{1,2})-?(\d{1,2})", base)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def _week_range(ref_date: date) -> Tuple[date, date]:
    """ref_date を含む営業週の月曜〜金曜を返す。"""
    # Monday = 0
    delta = ref_date.weekday()
    mon = ref_date - timedelta(days=delta)
    fri = mon + timedelta(days=4)
    return mon, fri


def _list_daily_files_for_week(year: int, mon: date, fri: date) -> List[Path]:
    """対象週の日次レポートファイル一覧を取得。"""
    base = DAILY_REPORT_BASE / str(year) / "gm_report"
    if not base.exists():
        return []
    candidates: List[Tuple[date, Path]] = []
    for p in base.glob("*.txt"):
        d = _normalize_filename_to_date(p.name)
        if d and mon <= d <= fri:
            candidates.append((d, p))
    candidates.sort(key=lambda x: x[0])
    return [p for _, p in candidates]


def _extract_trend_blocks(text: str) -> List[Dict[str, Any]]:
    """【〇〇/中期トレンド判断】ブロックを抽出。"""
    results: List[Dict[str, Any]] = []
    for m in TREND_BLOCK_RE.finditer(text):
        category = m.group(1).strip()
        block = m.group(2).strip()
        core_lines: List[str] = []
        satellite_lines: List[str] = []
        core_m = CORE_BLOCK_RE.search(block)
        if core_m:
            core_lines = [
                ln.strip()
                for ln in core_m.group(1).strip().splitlines()
                if ln.strip() and not ln.strip().startswith("(")
            ]
        sat_m = SATELLITE_BLOCK_RE.search(block)
        if sat_m:
            satellite_lines = [
                ln.strip()
                for ln in sat_m.group(1).strip().splitlines()
                if ln.strip() and not ln.strip().startswith("(")
            ]
        results.append({
            "category": category,
            "core": core_lines,
            "satellite": satellite_lines,
        })
    return results


def _extract_keywords(text: str) -> List[str]:
    """GMキーワードを検出。"""
    found: List[str] = []
    for kw in GM_KEYWORDS:
        if kw in text and kw not in found:
            found.append(kw)
    return found


def _extract_values(text: str) -> Dict[str, str]:
    """主要数値を抽出。"""
    values: Dict[str, str] = {}
    for pat, name in VALUE_PATTERNS:
        m = re.search(pat, text)
        if m:
            values[name] = m.group(1).strip()
    return values


def _extract_strategy_blocks(text: str) -> List[Dict[str, str]]:
    """【〇〇のトレード戦略の考え方】ブロックを抽出。"""
    results: List[Dict[str, str]] = []
    for m in STRATEGY_BLOCK_RE.finditer(text):
        results.append({
            "category": m.group(1).strip(),
            "summary": m.group(2).strip()[:500],
        })
    return results


def _extract_calendar(text: str) -> List[Dict[str, Any]]:
    """▽〇月〇日〜〇日の予定ブロックを抽出（主な経済指標・予定にも対応）。"""
    results: List[Dict[str, Any]] = []
    for m in CALENDAR_RE.finditer(text):
        # group1,2=start_mon,day / group3=optional end_month(e.g. "3月") / group4=end_day / group5=body
        body = m.group(5).strip()
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()][:15]
        end_part = f"{m.group(3) or m.group(1) + '月'}{m.group(4)}日"
        results.append({
            "range": f"{m.group(1)}月{m.group(2)}日〜{end_part}",
            "items": lines,
        })
    return results


def parse_single_report(path: Path) -> Dict[str, Any]:
    """単一の日次レポートをパース。"""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"path": str(path), "error": str(e)}

    report_date: Optional[date] = None
    for line in raw.splitlines()[:5]:
        d = _parse_date_from_line(line)
        if d:
            report_date = d
            break
    if report_date is None:
        report_date = _normalize_filename_to_date(path.name)

    return {
        "path": str(path),
        "date": report_date.isoformat() if report_date else None,
        "trend_blocks": _extract_trend_blocks(raw),
        "keywords": _extract_keywords(raw),
        "values": _extract_values(raw),
        "strategy_blocks": _extract_strategy_blocks(raw),
        "calendar": _extract_calendar(raw),
    }


def parse_week(ref_date: date) -> Dict[str, Any]:
    """対象週の日次レポートをまとめてパース。"""
    mon, fri = _week_range(ref_date)
    files = _list_daily_files_for_week(ref_date.year, mon, fri)
    reports: List[Dict[str, Any]] = []
    all_keywords: List[str] = []
    all_values: Dict[str, List[str]] = {}

    for fp in files:
        r = parse_single_report(fp)
        reports.append(r)
        if "error" not in r:
            for kw in r.get("keywords", []):
                if kw not in all_keywords:
                    all_keywords.append(kw)
            for k, v in r.get("values", {}).items():
                all_values.setdefault(k, []).append(v)

    # 数値は最新日を優先（末尾）
    latest_values: Dict[str, str] = {}
    for k, vals in all_values.items():
        if vals:
            latest_values[k] = vals[-1]

    return {
        "week_start": mon.isoformat(),
        "week_end": fri.isoformat(),
        "files_found": [str(p) for p in files],
        "reports": reports,
        "aggregate": {
            "keywords": all_keywords,
            "latest_values": latest_values,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="日次GMレポートからキーワード・数値・トレンドブロックをパース"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", type=str, help="基準日 (例: 2026-3-14)")
    g.add_argument("--week-id", type=str, help="週ID (例: 2026-3-14_wk11)")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()

    ref_date: Optional[date] = None
    if args.date:
        parts = re.split(r"[-/]", args.date.strip())
        if len(parts) >= 3:
            try:
                ref_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                pass
    elif args.week_id:
        m = re.match(r"(\d{4})-?(\d{1,2})-?(\d{1,2})", args.week_id)
        if m:
            try:
                ref_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass

    if ref_date is None:
        print("ERROR: 日付をパースできませんでした。", file=__import__("sys").stderr)
        return 2

    result = parse_week(ref_date)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"週: {result['week_start']} 〜 {result['week_end']}")
        print(f"対象ファイル: {len(result['files_found'])}件")
        for p in result["files_found"]:
            print(f"  - {Path(p).name}")
        print("\n集約キーワード:", ", ".join(result["aggregate"]["keywords"]) or "(なし)")
        print("\n主要数値（最終日）:", result["aggregate"]["latest_values"] or "(なし)")
        print("\n詳細は --json で出力してください。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
