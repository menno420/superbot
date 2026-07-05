"""Security service — raid detection + account-age filter (tiers 1+2, Q-0111).

The automated join-screening layer beneath manual moderation. Two APPROVED
tiers; the two DECLINED tiers (alt-detection / VPN blocking) are deliberately
absent — this service makes **no external calls** and stores no PII.

Shape (safety-community family plan): the **pure detection layer** (the
:class:`RaidTracker` sliding window + :func:`account_age_days`) is fully
unit-testable with no Discord I/O; the **orchestration** (:func:`handle_member_join`)
is fail-open (any fault is logged and swallowed so a join always completes) and
routes its one consequential action — a kick — through
:func:`services.moderation_service.kick`, never around it.

* **Tier 1 — raid detection.** Per-guild sliding window of join timestamps. When
  ``>= raid_join_count`` joins land within ``raid_window_seconds`` the service
  raises a **staff alert** (once per lockdown, not per join) and, if a slowmode
  channel is configured, raises that channel's slowmode for ``raid_lockdown_seconds``
  then restores it.
* **Tier 2 — account-age filter.** An account younger than ``age_min_days`` on
  join is acted on per ``age_action``: ``alert`` (staff alert only) or ``kick``
  (reject via ``moderation_service`` + alert).

Module-level detector state (the raid tracker + the active-lockdown set) is
process-local and intentionally not persisted (ADR-002: runtime state is not
restart-safe by design — a restart resets the windows, the conservative choice).
:func:`reset_state` clears it for tests / on a guild leave.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone

import discord

from core.runtime import resources as guild_resources
from services import security_config
from services.channel_lifecycle_service import (
    ChannelLifecycleRequest,
    ChannelLifecycleService,
)

logger = logging.getLogger("bot.services.security")

EVT_RAID_DETECTED = "security.raid_detected"
EVT_ACCOUNT_FLAGGED = "security.account_flagged"

_ALERT_COLOR = discord.Color.red()


# ---------------------------------------------------------------------------
# Tier 1 — raid detection (pure sliding-window counter)
# ---------------------------------------------------------------------------


class RaidTracker:
    """In-memory per-guild sliding-window join counter.

    Mirrors :class:`services.automod_service.SpamTracker` (joins instead of
    messages, keyed by guild only). Process-local; a restart resets windows.
    """

    def __init__(self) -> None:
        self._joins: dict[int, deque[float]] = defaultdict(deque)

    def record_and_count(
        self,
        guild_id: int,
        *,
        window_seconds: float,
        now: float | None = None,
    ) -> int:
        """Record a join at ``now`` and return the join count within the window."""
        ts = time.monotonic() if now is None else now
        bucket = self._joins[guild_id]
        bucket.append(ts)
        cutoff = ts - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        return len(bucket)

    def reset(self, guild_id: int | None = None) -> None:
        """Drop tracked windows — one guild, or all when ``guild_id`` is None."""
        if guild_id is None:
            self._joins.clear()
        else:
            self._joins.pop(guild_id, None)


# Module-level detector state (see module docstring).
_raid_tracker = RaidTracker()
_locked_guilds: set[int] = set()


def reset_state() -> None:
    """Clear all process-local detector state (tests / guild leave)."""
    _raid_tracker.reset()
    _locked_guilds.clear()


# ---------------------------------------------------------------------------
# Tier 2 — account-age (pure)
# ---------------------------------------------------------------------------


def account_age_days(
    member: discord.Member,
    *,
    now: datetime | None = None,
) -> float | None:
    """Days since ``member``'s account was created, or ``None`` if unknown.

    Uses Discord's account-creation timestamp (``created_at``) — a public,
    snowflake-derived value, never any private signal. ``None`` when the member
    object carries no usable timestamp (then the filter conservatively skips).
    """
    created = getattr(member, "created_at", None)
    if not isinstance(created, datetime):
        return None
    reference = now or datetime.now(timezone.utc)
    if created.tzinfo is None:  # defensive — Discord supplies aware datetimes
        created = created.replace(tzinfo=timezone.utc)
    return (reference - created).total_seconds() / 86400.0


def is_young_account(
    member: discord.Member,
    *,
    min_days: int,
    now: datetime | None = None,
) -> bool:
    """True when ``member``'s account is younger than ``min_days``.

    A missing/invalid creation timestamp returns False (fail open — never act on
    an account we can't actually date).
    """
    age = account_age_days(member, now=now)
    return age is not None and age < min_days


# ---------------------------------------------------------------------------
# Verdict (what the orchestration decided — handy for tests + the event payload)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JoinScreeningResult:
    """What :func:`handle_member_join` decided for one join (no I/O)."""

    raid_triggered: bool = False
    raid_join_count: int = 0
    account_flagged: bool = False
    account_age_days: float | None = None
    age_action_taken: str | None = None  # "alert" | "kick" | None


# ---------------------------------------------------------------------------
# Orchestration helpers (fail-safe)
# ---------------------------------------------------------------------------


async def _post_alert(
    guild: discord.Guild,
    channel_id: int | None,
    embed: discord.Embed,
) -> None:
    """Post a staff alert embed to the configured channel — fail-safe."""
    if channel_id is None:
        return
    channel = guild_resources.resolve_channel(guild, channel_id=channel_id)
    if channel is None:
        logger.warning(
            "security: alert channel %s not found in guild %s",
            channel_id,
            guild.id,
        )
        return
    try:
        await channel.send(embed=embed)
    except discord.HTTPException as exc:
        logger.warning("security: failed to post alert: %s", exc)
    except Exception:  # noqa: BLE001 — fail-safe wrapper
        logger.exception("security: unexpected error posting alert")


async def _apply_slowmode(channel: discord.abc.GuildChannel, seconds: int) -> None:
    # Route through the audited ChannelLifecycleService seam (the same one
    # ``!slowmode`` uses) so the raid-lockdown slowmode is audited rather than a
    # bare ``channel.edit()``. Automated raid response → no human actor.
    guild = getattr(channel, "guild", None)
    if guild is None:
        return
    try:
        await ChannelLifecycleService().apply(
            guild,
            ChannelLifecycleRequest(
                operation="set_slowmode",
                channel_ids=(channel.id,),
                slowmode_seconds=seconds,
                reason="Security: raid lockdown",
            ),
            None,  # automated raid response — no human actor
            actor_type="system",
        )
    except Exception:  # noqa: BLE001 — slowmode is best-effort; never crash the join
        logger.exception("security: failed to set slowmode on channel %s", channel.id)


async def _lift_lockdown(
    guild_id: int,
    channel: discord.abc.GuildChannel,
    prior_slowmode: int,
) -> None:
    """Restore a channel's prior slowmode and clear the guild's lockdown flag."""
    try:
        guild = getattr(channel, "guild", None)
        if guild is not None:
            await ChannelLifecycleService().apply(
                guild,
                ChannelLifecycleRequest(
                    operation="set_slowmode",
                    channel_ids=(channel.id,),
                    slowmode_seconds=prior_slowmode,
                    reason="Security: raid lockdown lifted",
                ),
                None,  # automated raid response — no human actor
                actor_type="system",
            )
    except Exception:  # noqa: BLE001 — best-effort restore
        logger.exception(
            "security: failed to restore slowmode on channel %s",
            channel.id,
        )
    finally:
        _locked_guilds.discard(guild_id)


async def _hold_then_lift(
    guild_id: int,
    channel: discord.abc.GuildChannel,
    prior_slowmode: int,
    delay: float,
) -> None:
    try:
        await asyncio.sleep(delay)
    finally:
        await _lift_lockdown(guild_id, channel, prior_slowmode)


async def _clear_lock_after(guild_id: int, delay: float) -> None:
    """Clear a guild's lockdown flag after ``delay`` seconds.

    The alert-only and channel-missing raid paths have no slowmode to restore, so
    nothing else carries the flag clear. Without this the guild would stay in
    ``_locked_guilds`` for the life of the process and a later, *distinct* raid
    would be silently suppressed until a restart. Clearing after the raid window
    lets the dedup expire so a fresh raid re-alerts.
    """
    try:
        await asyncio.sleep(delay)
    finally:
        _locked_guilds.discard(guild_id)


def _raid_alert_embed(
    policy: security_config.SecurityPolicy,
    count: int,
) -> discord.Embed:
    desc = (
        f"**{count} accounts** joined within {policy.raid_window_seconds}s "
        f"(threshold {policy.raid_join_count}/{policy.raid_window_seconds}s)."
    )
    if policy.applies_raid_slowmode:
        desc += (
            f"\nRaised slowmode to **{policy.raid_slowmode_seconds}s** for "
            f"{policy.raid_lockdown_seconds}s (auto-restored)."
        )
    else:
        desc += "\nSuggested action: enable a slow join-gate / raise slowmode."
    return discord.Embed(
        title="🚨 Raid suspected",
        description=desc,
        color=_ALERT_COLOR,
    )


def _age_alert_embed(
    member: discord.Member,
    policy: security_config.SecurityPolicy,
    age_days: float,
    kicked: bool,
) -> discord.Embed:
    action = (
        "**Rejected** (kicked)."
        if kicked
        else "Watching; no action taken (alert-only)."
    )
    return discord.Embed(
        title="⚠️ Young account joined",
        description=(
            f"**{member}** — account age **{age_days:.1f} days** "
            f"(threshold {policy.age_min_days}). {action}"
        ),
        color=discord.Color.orange(),
    )


async def _emit(event: str, **payload: object) -> None:
    from core.events import bus

    try:
        await bus.emit(event, **payload)
    except Exception:  # noqa: BLE001 — advisory event; never fail the handler
        logger.exception("security: %s emit failed", event)


# ---------------------------------------------------------------------------
# Tier handlers
# ---------------------------------------------------------------------------


async def _handle_raid(
    member: discord.Member,
    policy: security_config.SecurityPolicy,
) -> tuple[bool, int]:
    """Record the join and, if a raid is detected, lock down + alert.

    Returns ``(triggered, join_count)``. The lockdown is deduped per guild: while
    a guild is already locked down a fresh trigger only re-counts, it does not
    re-alert or re-apply slowmode.
    """
    guild = member.guild
    count = _raid_tracker.record_and_count(
        guild.id,
        window_seconds=policy.raid_window_seconds,
    )
    if count < policy.raid_join_count:
        return False, count
    if guild.id in _locked_guilds:
        return False, count  # already locked — dedupe the alert/slowmode

    _locked_guilds.add(guild.id)
    lock_clear_scheduled = False
    if policy.applies_raid_slowmode:
        channel = guild_resources.resolve_channel(
            guild,
            channel_id=policy.raid_slowmode_channel_id,
        )
        if channel is not None:
            prior = getattr(channel, "slowmode_delay", 0) or 0
            await _apply_slowmode(channel, policy.raid_slowmode_seconds)
            if policy.raid_lockdown_seconds > 0:
                asyncio.ensure_future(
                    _hold_then_lift(
                        guild.id,
                        channel,
                        prior,
                        float(policy.raid_lockdown_seconds),
                    ),
                )
            else:  # lockdown 0 = apply-and-hold-until-restart; clear the flag now
                _locked_guilds.discard(guild.id)
            lock_clear_scheduled = True
        else:
            logger.warning(
                "security: raid slowmode channel %s not found in guild %s",
                policy.raid_slowmode_channel_id,
                guild.id,
            )
    if not lock_clear_scheduled:
        # Alert-only (the default) or slowmode-channel-missing: nothing above will
        # clear the lockdown flag, so expire the dedup after the raid window — else
        # a later, distinct raid is silently suppressed until restart.
        asyncio.ensure_future(
            _clear_lock_after(guild.id, float(policy.raid_window_seconds)),
        )
    await _post_alert(guild, policy.alert_channel_id, _raid_alert_embed(policy, count))
    await _emit(
        EVT_RAID_DETECTED,
        guild_id=guild.id,
        join_count=count,
        user_id=member.id,
    )
    return True, count


async def _handle_account_age(
    member: discord.Member,
    policy: security_config.SecurityPolicy,
) -> tuple[bool, float | None, str | None]:
    """Flag/reject a too-young account. Returns ``(flagged, age_days, action)``."""
    age = account_age_days(member)
    if age is None or age >= policy.age_min_days:
        return False, age, None

    kicked = False
    if policy.age_action == security_config.ACTION_KICK:
        from services import moderation_service

        try:
            await moderation_service.kick(
                member,
                reason=(
                    f"Security: account age {age:.1f}d < {policy.age_min_days}d "
                    "threshold (auto-reject)"
                ),
                actor_id=None,
            )
            kicked = True
        except Exception:  # noqa: BLE001 — a kick fault must not crash the join
            logger.exception(
                "security: account-age kick failed for member=%s in guild=%s",
                member.id,
                member.guild.id,
            )

    await _post_alert(
        member.guild,
        policy.alert_channel_id,
        _age_alert_embed(member, policy, age, kicked),
    )
    await _emit(
        EVT_ACCOUNT_FLAGGED,
        guild_id=member.guild.id,
        user_id=member.id,
        age_days=round(age, 2),
        action=policy.age_action,
    )
    return True, age, ("kick" if kicked else "alert")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def handle_member_join(member: discord.Member) -> JoinScreeningResult:
    """Screen a joining member through the enabled tiers, per the guild policy.

    Fully fail-safe: a config-read fault or any detector/action error is logged
    and swallowed so the join dispatch always completes. The two tiers are
    independent — an age-filter fault does not skip raid detection and vice
    versa. Returns a :class:`JoinScreeningResult` describing what happened
    (mostly for tests; the cog ignores it).
    """
    guild = getattr(member, "guild", None)
    if guild is None:
        return JoinScreeningResult()
    try:
        policy = await security_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception("security: load_policy failed for guild=%s", guild.id)
        return JoinScreeningResult()

    if not policy.any_tier_enabled:
        return JoinScreeningResult()

    result = JoinScreeningResult()

    if policy.raid_detection_on:
        try:
            triggered, count = await _handle_raid(member, policy)
            result = JoinScreeningResult(
                raid_triggered=triggered,
                raid_join_count=count,
                account_flagged=result.account_flagged,
                account_age_days=result.account_age_days,
                age_action_taken=result.age_action_taken,
            )
        except Exception:  # noqa: BLE001 — raid fault must not skip the age filter
            logger.exception("security: raid handler failed for guild=%s", guild.id)

    if policy.age_filter_on:
        try:
            flagged, age, action = await _handle_account_age(member, policy)
            result = JoinScreeningResult(
                raid_triggered=result.raid_triggered,
                raid_join_count=result.raid_join_count,
                account_flagged=flagged,
                account_age_days=age,
                age_action_taken=action,
            )
        except Exception:  # noqa: BLE001 — age fault must not crash the join
            logger.exception("security: age handler failed for guild=%s", guild.id)

    return result


__all__ = [
    "EVT_ACCOUNT_FLAGGED",
    "EVT_RAID_DETECTED",
    "JoinScreeningResult",
    "RaidTracker",
    "account_age_days",
    "handle_member_join",
    "is_young_account",
    "reset_state",
]
