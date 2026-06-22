"""Karma service — the only path through which karma totals mutate.

Peer reputation (thanks/upvote): members grant each other karma.  Mirrors
:mod:`services.economy_service` / :mod:`services.xp_service` — the service
is the single authority, so every grant goes through one place that:

1. Enforces the data-level rules: a member cannot grant karma to
   themselves, the amount must be positive, and the giver must be within
   both the per-(giver -> receiver) cooldown and the per-giver daily cap.
2. Writes the recipient's running total atomically (``db.credit_karma``)
   and bumps the giver's lifetime ``given_count``.
3. Appends an immutable row to ``karma_audit_log`` — the same row that
   backs the anti-abuse reads (no separate cooldown table).
4. Emits the catalogued ``EVT_KARMA_GRANTED`` event so subscribers
   (panel refresh, future analytics) react without touching the DB.

Bot-target / self checks that need Discord objects (is the recipient a
bot?) live in the **cog** before calling :func:`give`; the service owns
the data-level rules (self-id, cooldown, cap) so they hold for every
caller.  ``db.credit_karma`` / ``db.insert_karma_audit`` are kept callable
directly only for the DB layer and unit tests — INV-K forbids any other
caller.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.events import bus
from services.karma_config import KarmaPolicy, load_policy
from utils import db

logger = logging.getLogger("bot.karma_service")

# Event name — also listed in core/events_catalogue.KNOWN_EVENTS.
EVT_KARMA_GRANTED = "karma.granted"


class KarmaError(RuntimeError):
    """Base class for karma grant rejections (caller-facing, expected)."""


class SelfKarmaError(KarmaError):
    """Raised when a member tries to grant karma to themselves."""


class KarmaDisabledError(KarmaError):
    """Raised when karma is disabled for the guild."""


class KarmaCooldownError(KarmaError):
    """Raised when the giver already thanked this recipient recently.

    ``retry_after`` is the whole seconds remaining on the cooldown.
    """

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"karma cooldown active, retry in {retry_after}s")


class KarmaDailyCapError(KarmaError):
    """Raised when the giver has hit their per-day grant cap."""

    def __init__(self, cap: int) -> None:
        self.cap = cap
        super().__init__(f"daily karma cap of {cap} reached")


@dataclass(frozen=True)
class KarmaGrant:
    """Result of a karma grant."""

    to_user: int
    new_total: int
    delta: int
    source: str


@dataclass(frozen=True)
class KarmaRecord:
    """Typed read-only view of a member's karma standing."""

    points: int
    received_count: int
    given_count: int
    rank: int | None


async def get_record(guild_id: int, user_id: int) -> KarmaRecord:
    """Return the karma standing for *user_id* (zeros when no row exists)."""
    row = await db.get_karma(user_id, guild_id)
    points = int(row.get("karma_points", 0) or 0)
    rank = await db.karma_rank(user_id, guild_id) if points > 0 else None
    return KarmaRecord(
        points=points,
        received_count=int(row.get("received_count", 0) or 0),
        given_count=int(row.get("given_count", 0) or 0),
        rank=rank,
    )


async def give(
    guild_id: int,
    *,
    from_user: int,
    to_user: int,
    amount: int = 1,
    source: str,
    reason: str | None = None,
    now: datetime | None = None,
    policy: KarmaPolicy | None = None,
) -> KarmaGrant:
    """Grant *amount* karma from *from_user* to *to_user*; return the result.

    *amount* must be > 0 (positive-only by design — there is no downvote).
    Enforces, in order: karma enabled, no self-grant, the per-(giver ->
    receiver) cooldown, and the per-giver daily cap.  Raises the matching
    :class:`KarmaError` subclass (caller renders a friendly message) when a
    rule blocks the grant — nothing is written in that case.

    Args:
        guild_id: discord guild.
        from_user: the granter.
        to_user: the recipient.
        amount: karma to grant (default 1, must be > 0).
        source: short label ("command", "reaction") for the audit row +
            event payload.
        reason: optional free-text reason supplied by the granter.
        now: injectable "current time" (UTC) for deterministic tests;
            defaults to :func:`datetime.now`.
        policy: injectable resolved :class:`KarmaPolicy`; loaded for the
            guild when omitted.
    """
    if amount <= 0:
        msg = f"karma amount must be positive, got {amount}"
        raise ValueError(msg)
    if from_user == to_user:
        raise SelfKarmaError("a member cannot grant karma to themselves")

    effective_policy = policy if policy is not None else await load_policy(guild_id)
    if not effective_policy.enabled:
        raise KarmaDisabledError("karma is disabled for this guild")

    current = now if now is not None else datetime.now(tz=timezone.utc)

    # Per-(giver -> receiver) cooldown.
    cooldown = effective_policy.cooldown_seconds
    if cooldown > 0:
        window_start = current - timedelta(seconds=cooldown)
        recent = await db.recent_grant_count(
            guild_id,
            from_user,
            to_user,
            window_start,
        )
        if recent > 0:
            raise KarmaCooldownError(cooldown)

    # Per-giver daily cap (rolling 24h).
    day_start = current - timedelta(days=1)
    given_today = await db.grants_given_since(guild_id, from_user, day_start)
    if given_today >= effective_policy.daily_cap:
        raise KarmaDailyCapError(effective_policy.daily_cap)

    new_total = await db.credit_karma(to_user, guild_id, amount)
    await db.increment_given(from_user, guild_id)
    await db.insert_karma_audit(
        guild_id,
        from_user,
        to_user,
        amount,
        source,
        reason,
    )
    await bus.emit(
        EVT_KARMA_GRANTED,
        guild_id=guild_id,
        from_user=from_user,
        to_user=to_user,
        delta=amount,
        new_total=new_total,
        source=source,
    )
    return KarmaGrant(
        to_user=to_user,
        new_total=new_total,
        delta=amount,
        source=source,
    )
