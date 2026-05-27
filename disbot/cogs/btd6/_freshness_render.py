"""Freshness rendering helpers for BTD6 embeds.

Single source of truth for the bucket emoji + warning copy used across
BTD6 embeds. Consolidates three duplicate dicts that previously lived
in ``cogs/btd6/_embeds.py:_BUCKET_EMOJI``,
``cogs/btd6/_builders.py:_BUCKET_BADGE``, and
``cogs/btd6/_builders.py:_FRESHNESS_BADGE``.

Pure functions; no I/O. Stale-data and never-fetched copy is locked
by the plan — do not change without updating the corresponding tests.
"""

from __future__ import annotations

from typing import Literal

import discord

from services.btd6_source_registry import FreshnessBucket

# ---------------------------------------------------------------------------
# Bucket badges (single source of truth)
# ---------------------------------------------------------------------------

# Emoji-only — used in the status embed's "Live facts" block and the
# panel's "Currently active" block.
BUCKET_EMOJI: dict[FreshnessBucket, str] = {
    "fresh": "🟢",
    "aging": "🟡",
    "stale": "🔴",
    "never": "⚪",
}

# Emoji + label — used in source-health and leaderboard footers.
BUCKET_BADGE: dict[FreshnessBucket, str] = {
    "fresh": "🟢 fresh",
    "aging": "🟡 aging",
    "stale": "🔴 stale",
    "never": "⚪ never",
}


# ---------------------------------------------------------------------------
# Locked copy
# ---------------------------------------------------------------------------

STALE_WARNING = (
    "⚠️ This data may be outdated. Last successful update was over "
    "24 hours ago. Showing the latest stored data."
)
NEVER_FETCHED_COPY = "This source has not been fetched yet, so no data is available."


EmptyStateReason = Literal["never_fetched", "no_active"]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_freshness_warning(state: FreshnessBucket) -> str | None:
    """Return the warning copy for a stale/never state, else ``None``.

    Only ``stale`` and ``never`` surface a user warning. ``aging`` is an
    operator-only signal — surfaced via the per-source badge but not as
    a user-facing warning in this PR.
    """
    if state == "stale":
        return STALE_WARNING
    if state == "never":
        return NEVER_FETCHED_COPY
    return None


def render_empty_state(
    context_type: str,
    reason: EmptyStateReason,
) -> discord.Embed:
    """Render the empty-state embed.

    ``reason="never_fetched"`` → source has never been fetched.
    ``reason="no_active"`` → source is fresh but has no active events
    of this kind right now.
    """
    if reason == "never_fetched":
        description = NEVER_FETCHED_COPY
    else:
        description = f"No active {context_type} right now."
    return discord.Embed(
        title=f"🐵 BTD6 — {context_type}",
        description=description,
        color=discord.Color.greyple(),
    )


__all__ = [
    "BUCKET_BADGE",
    "BUCKET_EMOJI",
    "NEVER_FETCHED_COPY",
    "STALE_WARNING",
    "EmptyStateReason",
    "render_empty_state",
    "render_freshness_warning",
]
