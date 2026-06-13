"""Automod detection engine — pure, unit-testable, no Discord I/O.

automod v1 (owner decision Q-0108).  This module decides **whether** a message
trips an automod rule; it does not act.  The acting (delete + warn + audit) is
done by ``cogs.automod.listener`` through :mod:`services.moderation_service`, so
escalation and audit stay one authority (see
``docs/planning/safety-community-family-plan-2026-06-13.md`` §3).

Public surface:

    AutomodVerdict          — (rule, reason) for a tripped rule
    SpamTracker             — per (guild,user,channel) sliding-window counter
    find_invite(content)    — discord invite-link detector
    caps_ratio(content)     — uppercase-letter fraction (0..1)
    exceeds_caps(...)       — caps rule predicate
    mention_count(message)  — user + role (+ @everyone) mention tally
    evaluate(message, policy, *, now, tracker) -> AutomodVerdict | None

The four rule types and their order match the owner-reviewed ``mock_automod_rules``
exhibit: spam burst → invite links → excessive caps → mass mentions.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

# discord.gg/CODE, discord.com/invite/CODE, discordapp.com/invite/CODE.
_INVITE_RE = re.compile(
    r"\b(?:discord\.gg|discord(?:app)?\.com/invite)/\S+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AutomodVerdict:
    """A tripped automod rule.

    ``rule`` is the stable machine id (used for the ``mod_logs`` rule column,
    the ``automod.rule_triggered`` event, and metrics); ``reason`` is the
    human-readable attribution shown in the moderation audit.
    """

    rule: str
    reason: str


# ---------------------------------------------------------------------------
# Spam burst — sliding-window message counter
# ---------------------------------------------------------------------------


class SpamTracker:
    """In-memory per (guild, user, channel) sliding-window message counter.

    State is process-local and intentionally not persisted (ADR-002: game/runtime
    state is not restart-safe by design; a restart simply resets burst windows,
    which is harmless — a fresh window is the conservative choice).
    """

    def __init__(self) -> None:
        self._hits: dict[tuple[int, int, int], deque[float]] = defaultdict(deque)

    def record_and_count(
        self,
        guild_id: int,
        user_id: int,
        channel_id: int,
        *,
        window_seconds: float,
        now: float | None = None,
    ) -> int:
        """Record a message at ``now`` and return the count within the window."""
        ts = time.monotonic() if now is None else now
        key = (guild_id, user_id, channel_id)
        bucket = self._hits[key]
        bucket.append(ts)
        cutoff = ts - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if not bucket:  # pragma: no cover - bucket always holds the just-added ts
            del self._hits[key]
            return 0
        return len(bucket)

    def reset(self) -> None:
        """Drop all tracked windows (used by tests and on a guild leave)."""
        self._hits.clear()


# Module-level default tracker — one per process, shared by the stage.
_DEFAULT_TRACKER = SpamTracker()


def default_tracker() -> SpamTracker:
    """Return the process-wide default :class:`SpamTracker`."""
    return _DEFAULT_TRACKER


# ---------------------------------------------------------------------------
# Pure content detectors
# ---------------------------------------------------------------------------


def find_invite(content: str) -> bool:
    """True when ``content`` contains a Discord invite link."""
    return _INVITE_RE.search(content or "") is not None


def caps_ratio(content: str) -> float:
    """Fraction (0..1) of the *letters* in ``content`` that are uppercase.

    Non-letters (digits, punctuation, emoji, spaces) are ignored so "WOW!!!"
    and "WOW" score identically.  Returns 0.0 when there are no letters.
    """
    upper = 0
    total = 0
    for ch in content or "":
        if ch.isalpha():
            total += 1
            if ch.isupper():
                upper += 1
    if total == 0:
        return 0.0
    return upper / total


def exceeds_caps(content: str, *, percent: int, min_letters: int) -> bool:
    """True when ``content`` is long enough and is >= ``percent`` uppercase."""
    letters = sum(1 for ch in (content or "") if ch.isalpha())
    if letters < min_letters:
        return False
    return caps_ratio(content) * 100 >= percent


def mention_count(message: Any) -> int:
    """Tally distinct user + role mentions on a message.

    ``@everyone``/``@here`` is treated as inherently mass: when present it
    contributes a large sentinel so the mass-mention rule trips on it alone.
    Uses ``getattr`` so the detector works against both ``discord.Message`` and
    lightweight test doubles.
    """
    users = getattr(message, "mentions", None) or []
    roles = getattr(message, "role_mentions", None) or []
    count = len(users) + len(roles)
    if getattr(message, "mention_everyone", False):
        count += 1_000
    return count


# ---------------------------------------------------------------------------
# Orchestrating predicate
# ---------------------------------------------------------------------------


def _is_exempt(message: Any, policy: Any) -> bool:
    """True when the message's channel or author role is on the exempt list."""
    channel_id = getattr(getattr(message, "channel", None), "id", None)
    if channel_id is not None and channel_id in policy.exempt_channel_ids:
        return True
    author = getattr(message, "author", None)
    for role in getattr(author, "roles", None) or []:
        role_id = getattr(role, "id", None)
        if role_id is not None and role_id in policy.exempt_role_ids:
            return True
    return False


def evaluate(
    message: Any,
    policy: Any,
    *,
    now: float | None = None,
    tracker: SpamTracker | None = None,
) -> AutomodVerdict | None:
    """Return the first tripped rule for ``message`` under ``policy``, or None.

    The caller is responsible only for having confirmed ``policy.enabled``.
    Exempt channels/roles short-circuit to None.  The spam window is always
    *recorded* (when the spam rule is on) so a later message still sees the
    burst, even when an earlier message in the burst tripped a different rule.
    """
    if _is_exempt(message, policy):
        return None

    content = getattr(message, "content", "") or ""

    # Spam burst — record first (so the window is accurate) then test.
    if policy.spam_enabled:
        trk = tracker if tracker is not None else _DEFAULT_TRACKER
        guild_id = getattr(getattr(message, "guild", None), "id", 0) or 0
        author_id = getattr(getattr(message, "author", None), "id", 0) or 0
        channel_id = getattr(getattr(message, "channel", None), "id", 0) or 0
        count = trk.record_and_count(
            guild_id,
            author_id,
            channel_id,
            window_seconds=policy.spam_window_seconds,
            now=now,
        )
        if count >= policy.spam_count:
            return AutomodVerdict(
                rule="automod.spam",
                reason=(
                    f"Spam: {count} messages in "
                    f"{policy.spam_window_seconds}s (limit {policy.spam_count})"
                ),
            )

    if policy.invites_enabled and find_invite(content):
        return AutomodVerdict(
            rule="automod.invite_link",
            reason="Posted a Discord invite link",
        )

    if policy.caps_enabled and exceeds_caps(
        content,
        percent=policy.caps_percent,
        min_letters=_caps_min_letters(),
    ):
        return AutomodVerdict(
            rule="automod.caps",
            reason=f"Excessive caps (>= {policy.caps_percent}% uppercase)",
        )

    if policy.mentions_enabled:
        mentions = mention_count(message)
        if mentions >= policy.mentions_count:
            return AutomodVerdict(
                rule="automod.mass_mentions",
                reason=(f"Mass mentions ({mentions}, limit {policy.mentions_count})"),
            )

    return None


def _caps_min_letters() -> int:
    """Indirection so the caps minimum stays one source of truth (config)."""
    from services.automod_config import MIN_CAPS_MESSAGE_LENGTH

    return MIN_CAPS_MESSAGE_LENGTH
