"""Read-only faucet/sink view over the economy audit ledger.

Every coin movement routed through :mod:`services.economy_service` appends a
signed row to ``economy_audit_log`` (``utils.db.economy.insert_economy_audit``).
This service reads and aggregates those rows into a per-guild **faucet vs.
sink** report — how many coins were minted, how many drained, the net flow,
and the per-reason breakdown over a time window — so an operator can observe
whether the games economy is inflating instead of guessing from static sims.

It adds no writes and no new reasons. Classification is by the **sign of the
summed delta per reason**, not a hardcoded faucet/sink list, so a future
reason is classified automatically and the view never goes stale (the same
self-cleaning principle as the eval drift guard, #879).

Layering (``docs/architecture.md``): a service may import ``utils`` + stdlib
only. It calls the pure ``utils.db.economy`` read fn, returns a typed report
with no Discord types and no ``views`` import. The admin cog renders it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from utils.db import economy as economy_db


class ReasonFlow(NamedTuple):
    """One audit ``reason`` aggregated: its net coin delta + movement count.

    The movement count is named ``movements`` (not ``count``) because
    ``count`` is a reserved method name on ``tuple`` / ``NamedTuple``.
    """

    reason: str
    net: int
    movements: int


class EconomyFlowReport(NamedTuple):
    """Per-guild faucet/sink summary over a time window.

    ``faucets`` / ``sinks`` are sorted by magnitude (largest first).
    ``ratio`` is minted / drained — ``None`` when nothing drained (no
    divide-by-zero); ``net`` is minted minus drained (signed). ``verdict``
    is a coarse one-word read of the balance for the window.
    """

    faucets: list[ReasonFlow]
    sinks: list[ReasonFlow]
    total_minted: int
    total_drained: int
    net: int
    ratio: float | None
    window_label: str
    verdict: str


# Above this minted:drained ratio the economy is minting noticeably faster
# than it drains over the window — a soft inflation signal, not a hard alarm.
_INFLATING_RATIO = 1.5
# Below this the loop is draining faster than it mints (deflation / heavy sink).
_DRAINING_RATIO = 0.67


def _classify(ratio: float | None, total_minted: int, total_drained: int) -> str:
    if total_minted == 0 and total_drained == 0:
        return "no activity"
    if ratio is None:
        # Coins minted, nothing drained at all → pure faucet for the window.
        return "inflating ⚠" if total_minted > 0 else "no activity"
    if ratio >= _INFLATING_RATIO:
        return "inflating ⚠"
    if ratio <= _DRAINING_RATIO:
        return "draining"
    return "balanced"


async def build_flow_report(
    guild_id: int,
    *,
    days: int | None = None,
) -> EconomyFlowReport:
    """Aggregate ``economy_audit_log`` into a faucet/sink report for a guild.

    ``days`` bounds the window to the last *N* days (by audit timestamp);
    ``None`` is the all-time view. Pure read — no writes, no Discord types.
    """
    since: datetime | None = None
    if days is not None and days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        window_label = f"last {days} day{'s' if days != 1 else ''}"
    else:
        window_label = "all time"

    rows = await economy_db.economy_flow_by_reason(guild_id, since=since)
    return _assemble(rows, window_label)


def _assemble(
    rows: list[tuple[str, int, int]],
    window_label: str,
) -> EconomyFlowReport:
    """Pure assembly from raw ``(reason, net, count)`` rows — unit-testable."""
    faucets: list[ReasonFlow] = []
    sinks: list[ReasonFlow] = []
    total_minted = 0
    total_drained = 0  # stored as a positive magnitude

    for reason, net, count in rows:
        if net > 0:
            faucets.append(ReasonFlow(reason, net, count))
            total_minted += net
        elif net < 0:
            sinks.append(ReasonFlow(reason, net, count))
            total_drained += -net
        # net == 0 (a reason that minted and drained equally) is neither a
        # faucet nor a sink for this window — omitted from both tables.

    faucets.sort(key=lambda f: f.net, reverse=True)
    sinks.sort(key=lambda s: s.net)  # most-negative first

    ratio = (total_minted / total_drained) if total_drained > 0 else None
    net = total_minted - total_drained
    verdict = _classify(ratio, total_minted, total_drained)

    return EconomyFlowReport(
        faucets=faucets,
        sinks=sinks,
        total_minted=total_minted,
        total_drained=total_drained,
        net=net,
        ratio=ratio,
        window_label=window_label,
        verdict=verdict,
    )
