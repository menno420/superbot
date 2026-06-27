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

from datetime import date, datetime, timedelta, timezone
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


class DayFlow(NamedTuple):
    """One calendar day (UTC) of coin flow: minted / drained / net + movements.

    ``net`` is ``minted - drained`` (signed). ``drained`` is a positive
    magnitude (coins removed), mirroring :class:`EconomyFlowReport`.
    """

    day: date
    minted: int
    drained: int
    net: int
    movements: int


class EconomyFlowTimeseries(NamedTuple):
    """Per-day faucet/sink trend over a window — the time-series sibling.

    ``days`` is oldest-first so it reads left-to-right. The totals/ratio/verdict
    mirror :class:`EconomyFlowReport` (the whole-window aggregate), and
    ``trend`` is a coarse read of whether net coin flow is rising (minting
    pulling ahead of draining over the window), falling, or steady — the signal
    a single aggregate can't show.
    """

    days: list[DayFlow]
    total_minted: int
    total_drained: int
    net: int
    ratio: float | None
    window_label: str
    verdict: str
    trend: str


# Below this fraction of the window's net-flow magnitude a half-over-half change
# is noise, not a trend — keeps a flat economy from reading as "rising/falling".
_TREND_EPS = 0.15


def _trend(daily_nets: list[int]) -> str:
    """Coarse direction of net coin flow: rising / falling / steady / n/a.

    Compares the mean daily net of the window's first half against its second
    half. A move smaller than :data:`_TREND_EPS` of the window's magnitude is
    "steady" (noise-tolerant); fewer than two days is "n/a".
    """
    if len(daily_nets) < 2:
        return "n/a"
    mid = len(daily_nets) // 2
    first = daily_nets[:mid] or daily_nets[:1]
    second = daily_nets[mid:]
    first_mean = sum(first) / len(first)
    second_mean = sum(second) / len(second)
    delta = second_mean - first_mean
    scale = max(abs(first_mean), abs(second_mean), 1.0)
    if delta > _TREND_EPS * scale:
        return "rising ⬆"
    if delta < -_TREND_EPS * scale:
        return "falling ⬇"
    return "steady ➡"


async def build_flow_timeseries(
    guild_id: int,
    *,
    days: int | None = None,
) -> EconomyFlowTimeseries:
    """Aggregate ``economy_audit_log`` into a per-day faucet/sink trend.

    ``days`` bounds the window to the last *N* days (by audit timestamp);
    ``None`` is the all-time view. Pure read — no writes, no Discord types.
    """
    since: datetime | None = None
    if days is not None and days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        window_label = f"last {days} day{'s' if days != 1 else ''}"
    else:
        window_label = "all time"

    rows = await economy_db.economy_flow_daily(guild_id, since=since)
    return _assemble_timeseries(rows, window_label)


def _assemble_timeseries(
    rows: list[tuple[date, int, int, int, int]],
    window_label: str,
) -> EconomyFlowTimeseries:
    """Pure assembly from raw ``(day, minted, drained, net, count)`` rows."""
    day_flows = [
        DayFlow(day, minted, drained, net, count)
        for day, minted, drained, net, count in rows
    ]
    total_minted = sum(d.minted for d in day_flows)
    total_drained = sum(d.drained for d in day_flows)
    net = total_minted - total_drained
    ratio = (total_minted / total_drained) if total_drained > 0 else None
    verdict = _classify(ratio, total_minted, total_drained)
    trend = _trend([d.net for d in day_flows])

    return EconomyFlowTimeseries(
        days=day_flows,
        total_minted=total_minted,
        total_drained=total_drained,
        net=net,
        ratio=ratio,
        window_label=window_label,
        verdict=verdict,
        trend=trend,
    )


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
