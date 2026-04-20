from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Tuple


CSV_HEADERS = [
    "opened_at",
    "closed_at",
    "symbol",
    "direction",
    "size",
    "entry_price",
    "exit_price",
    "pnl_pct",
    "pnl_amount",
    "tag",
    "notes",
]


@dataclass
class Trade:
    opened_at: datetime
    closed_at: datetime
    symbol: str
    direction: str
    size: float
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_amount: float
    tag: str
    notes: str

    @property
    def is_win(self) -> bool:
        return self.pnl_pct > 0


def _parse_datetime(s: str) -> datetime:
    """
    Parse datetime string.

    Accepts:
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM
    """
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {s!r}")


def _ensure_csv_exists(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def append_trade(csv_path: Path, trade: Trade) -> None:
    _ensure_csv_exists(csv_path)
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                trade.opened_at.strftime("%Y-%m-%d %H:%M"),
                trade.closed_at.strftime("%Y-%m-%d %H:%M"),
                trade.symbol,
                trade.direction,
                f"{trade.size:.4f}",
                f"{trade.entry_price:.6f}",
                f"{trade.exit_price:.6f}",
                f"{trade.pnl_pct:.4f}",
                f"{trade.pnl_amount:.4f}",
                trade.tag,
                trade.notes.replace("\n", " ").strip(),
            ]
        )


def _load_trades(csv_path: Path) -> List[Trade]:
    if not csv_path.exists():
        return []
    trades: List[Trade] = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                opened_at = _parse_datetime(row["opened_at"])
                closed_at = _parse_datetime(row["closed_at"])
                symbol = (row.get("symbol") or "").strip()
                direction = (row.get("direction") or "").strip().lower()
                size = float(row.get("size") or 0.0)
                entry_price = float(row.get("entry_price") or 0.0)
                exit_price = float(row.get("exit_price") or 0.0)
                pnl_pct_str = row.get("pnl_pct") or ""
                pnl_amount_str = row.get("pnl_amount") or ""
                tag = (row.get("tag") or "").strip()
                notes = (row.get("notes") or "").strip()
                if pnl_pct_str:
                    pnl_pct = float(pnl_pct_str)
                else:
                    if direction == "long":
                        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0.0
                    elif direction == "short":
                        pnl_pct = (entry_price - exit_price) / entry_price * 100 if entry_price else 0.0
                    else:
                        pnl_pct = 0.0
                pnl_amount = float(pnl_amount_str) if pnl_amount_str else 0.0
                trades.append(
                    Trade(
                        opened_at=opened_at,
                        closed_at=closed_at,
                        symbol=symbol,
                        direction=direction,
                        size=size,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        pnl_pct=pnl_pct,
                        pnl_amount=pnl_amount,
                        tag=tag,
                        notes=notes,
                    )
                )
            except Exception:
                continue
    return trades


def _filter_trades_by_date(
    trades: List[Trade],
    start_date: Optional[date],
    end_date: Optional[date],
) -> List[Trade]:
    if start_date is None and end_date is None:
        return trades
    result: List[Trade] = []
    for t in trades:
        d = t.opened_at.date()
        if start_date is not None and d < start_date:
            continue
        if end_date is not None and d > end_date:
            continue
        result.append(t)
    return result


def _compute_summary(trades: List[Trade]) -> Tuple[int, int, int, float]:
    total = len(trades)
    wins = sum(1 for t in trades if t.is_win)
    losses = total - wins
    pnl_sum = sum(t.pnl_pct for t in trades)
    return total, wins, losses, pnl_sum


def _format_markdown_summary(
    trades: List[Trade],
    period_label: str,
) -> str:
    total, wins, losses, pnl_sum = _compute_summary(trades)
    win_rate = (wins / total * 100) if total else 0.0

    lines: List[str] = []
    lines.append(f"# Trade Results – {period_label}")
    lines.append("")
    lines.append("## 概要")
    lines.append(f"- 期間: {period_label}")
    lines.append(f"- トレード回数: {total}")
    lines.append(f"- 勝ち: {wins} / 負け: {losses}")
    lines.append(f"- 勝率: {win_rate:.1f}%")
    lines.append(f"- 合計PnL (pnl_pct合計): {pnl_sum:+.2f}%")
    lines.append("")

    lines.append("## トレード一覧")
    lines.append("")
    lines.append(
        "| opened_at | closed_at | symbol | dir | size | entry | exit | pnl_% | tag | notes |"
    )
    lines.append(
        "|-----------|-----------|--------|-----|------|-------|------|-------|-----|-------|"
    )
    for t in trades:
        lines.append(
            "| {opened} | {closed} | {symbol} | {dir} | {size:.2f} | {entry:.4f} | {exit:.4f} | {pnl:+.2f} | {tag} | {notes} |".format(
                opened=t.opened_at.strftime("%Y-%m-%d %H:%M"),
                closed=t.closed_at.strftime("%Y-%m-%d %H:%M"),
                symbol=t.symbol,
                dir=t.direction,
                size=t.size,
                entry=t.entry_price,
                exit=t.exit_price,
                pnl=t.pnl_pct,
                tag=t.tag,
                notes=t.notes.replace("|", "/"),
            )
        )

    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "data" / "private_trades.csv"

    parser = argparse.ArgumentParser(
        description="Track private trades (append & summarize)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Add a single trade to private_trades.csv")
    add_p.add_argument("--opened-at", required=True, help="YYYY-MM-DD or YYYY-MM-DD HH:MM")
    add_p.add_argument("--closed-at", required=True, help="YYYY-MM-DD or YYYY-MM-DD HH:MM")
    add_p.add_argument("--symbol", required=True, help="Symbol, e.g., USDJPY, WTI, BTCUSD")
    add_p.add_argument("--direction", required=True, choices=["long", "short"])
    add_p.add_argument("--size", type=float, required=True, help="Position size (lot or risk %)")
    add_p.add_argument("--entry", type=float, required=True, help="Entry price")
    add_p.add_argument("--exit", type=float, required=True, help="Exit price")
    add_p.add_argument("--pnl-pct", type=float, default=None, help="PnL in percent (optional)")
    add_p.add_argument("--pnl-amount", type=float, default=0.0, help="PnL amount (optional)")
    add_p.add_argument("--tag", default="", help="Strategy tag, e.g., trend, mean_rev, event")
    add_p.add_argument("--notes", default="", help="Free-form notes")

    sum_p = subparsers.add_parser(
        "summary",
        help="Print markdown summary for a date range (for review.md / trade_results.md).",
    )
    sum_p.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD, inclusive, based on opened_at).",
    )
    sum_p.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD, inclusive, based on opened_at).",
    )

    args = parser.parse_args()

    if args.command == "add":
        opened_at = _parse_datetime(args.opened_at)
        closed_at = _parse_datetime(args.closed_at)
        direction = args.direction.lower()
        entry_price = float(args.entry)
        exit_price = float(args.exit)

        if args.pnl_pct is not None:
            pnl_pct = float(args.pnl_pct)
        else:
            if direction == "long":
                pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0.0
            else:
                pnl_pct = (entry_price - exit_price) / entry_price * 100 if entry_price else 0.0

        trade = Trade(
            opened_at=opened_at,
            closed_at=closed_at,
            symbol=args.symbol.strip(),
            direction=direction,
            size=float(args.size),
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_pct=pnl_pct,
            pnl_amount=float(args.pnl_amount),
            tag=args.tag.strip(),
            notes=args.notes.strip(),
        )
        append_trade(csv_path, trade)
        print(f"Appended trade for {trade.symbol} at {trade.opened_at} -> {csv_path}")
        return 0

    if args.command == "summary":
        start_d = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_d = datetime.strptime(args.end, "%Y-%m-%d").date()
        if end_d < start_d:
            raise SystemExit("end must be >= start")

        trades = _load_trades(csv_path)
        trades = _filter_trades_by_date(trades, start_d, end_d)
        period_label = f"{start_d.isoformat()}〜{end_d.isoformat()}"
        md = _format_markdown_summary(trades, period_label)
        print(md)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

