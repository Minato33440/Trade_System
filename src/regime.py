"""レジーム判定ロジック。

8ペア30日データからマクロ・レジームを簡易判定し、
ラベル・サマリー・YAMLスナップショットを生成する。
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple


def build_regime_snapshot(
    start_date: date,
    end_date: date,
    snapshots: Dict[str, Dict[str, float]],
) -> Tuple[str, str, str]:
    """
    8ペア30日データからレジームを簡易判定し、概要テキストとYAMLスナップショットを返す。

    Returns:
        (label, summary_text, yaml_text)
    """

    def _get_pair(name: str) -> Tuple[Optional[float], Optional[float]]:
        info = snapshots.get(name) or {}
        return info.get("latest"), info.get("change_30d")

    latest_us100, ch_us100 = _get_pair("US100")
    latest_btc, ch_btc = _get_pair("BTC/USD")
    latest_wti, ch_wti = _get_pair("WTI")
    latest_vix, ch_vix = _get_pair("VIX")
    latest_xau, ch_xau = _get_pair("XAU/USD")
    latest_us2y, ch_us2y = _get_pair("US2Y")
    latest_us10y, ch_us10y = _get_pair("US10Y")

    def _equities_regime() -> str:
        if ch_us100 is None:
            return "unknown"
        if ch_us100 <= -1.5:
            return "down"
        if ch_us100 >= 1.5:
            return "up"
        return "flat"

    def _vol_regime() -> str:
        if ch_vix is None or latest_vix is None:
            return "unknown"
        if latest_vix >= 25 and ch_vix >= 20:
            return "spike"
        if latest_vix <= 15 and ch_vix <= -10:
            return "calm"
        return "normal"

    def _oil_regime() -> str:
        if ch_wti is None:
            return "unknown"
        if ch_wti >= 20:
            return "surge"
        if ch_wti <= -20:
            return "slump"
        return "range"

    def _gold_regime() -> str:
        if ch_xau is None:
            return "unknown"
        if ch_xau >= 2:
            return "bid"
        if ch_xau <= -2:
            return "off"
        return "range"

    def _crypto_regime() -> str:
        if ch_btc is None:
            return "unknown"
        if ch_btc <= -5:
            return "weak"
        if ch_btc >= 5:
            return "strong"
        return "range"

    def _yields_regime() -> str:
        changes = [c for c in (ch_us2y, ch_us10y) if c is not None]
        if not changes:
            return "unknown"
        avg = sum(changes) / len(changes)
        if avg <= -0.5:
            return "falling"
        if avg >= 0.5:
            return "rising"
        return "flat"

    equities = _equities_regime()
    vol = _vol_regime()
    oil = _oil_regime()
    gold = _gold_regime()
    crypto = _crypto_regime()
    yields_regime = _yields_regime()

    if vol == "spike" and oil == "surge":
        label = "Geopolitical Risk-Off + Energy Shock"
    else:
        parts: List[str] = []
        if equities == "down":
            parts.append("Equities Down")
        if vol == "spike":
            parts.append("Volatility Spike")
        if oil == "surge":
            parts.append("Oil Surge")
        if gold == "bid":
            parts.append("Gold Bid")
        if not parts:
            label = "Neutral"
        else:
            label = " / ".join(parts)

    summary = (
        f"label={label}, equities={equities}, volatility={vol}, "
        f"oil={oil}, gold={gold}, crypto={crypto}, yields={yields_regime}"
    )

    # YAMLスナップショット文字列を構築
    order = ["USD/JPY", "US100", "XAU/USD", "WTI", "US2Y", "VIX", "US10Y", "BTC/USD"]
    panel = {
        "risk": ["US100", "BTC/USD"],
        "fear": ["VIX"],
        "inflation": ["WTI", "XAU/USD"],
        "rates": ["US2Y", "US10Y"],
        "liquidity": [],
        "credit": [],
    }

    lines: List[str] = []
    lines.append(f"# {end_date:%Y_%m_%d}_snapshot.yaml")
    lines.append("")
    lines.append("date:")
    lines.append(f"  start: {start_date.isoformat()}")
    lines.append(f"  end: {end_date.isoformat()}")
    lines.append("")
    lines.append("panel:")
    for key, names in panel.items():
        if names:
            joined = ", ".join(names)
            lines.append(f"  {key.capitalize()}: [{joined}]")
    lines.append("")
    lines.append("regime:")
    lines.append(f'  label: "{label}"')
    lines.append(f"  equities: {equities}")
    lines.append(f"  volatility: {vol}")
    lines.append(f"  oil: {oil}")
    lines.append(f"  gold: {gold}")
    lines.append(f"  crypto: {crypto}")
    lines.append(f"  yields: {yields_regime}")
    lines.append("")
    lines.append("snapshot_30d:")
    for name in order:
        info = snapshots.get(name)
        if not info:
            continue
        latest = info.get("latest")
        change = info.get("change_30d")
        if latest is None or change is None:
            continue
        lines.append(f'  "{name}":')
        lines.append(f"    latest: {latest:.3f}")
        lines.append(f"    change_pct: {change:.2f}")

    yaml_text = "\n".join(lines) + "\n"
    return label, summary, yaml_text
