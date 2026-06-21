"""Starboard config writes (audited) + the star-change decision (idea B1).

Mirrors :mod:`services.reaction_role_service`: operator **config** mutations
(``configure`` / ``disable``) emit ``audit.action_recorded``; the high-volume
member **star** path (``handle_star_change``) is not audited. The decision —
post a new starboard message, edit the count, delete it, or do nothing — is made
here against the authoritative DB state; the *Discord I/O* (sending/editing the
message) stays in the cog, because services do not send messages.

Cycle discipline mirrors the rest of ``services``: cross-package ``services.*``
imports are function-local; top-level imports are stdlib + ``utils`` only.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from utils.db import starboard as db

logger = logging.getLogger("bot.services.starboard")

# Action codes for StarboardOutcome — what the cog should do with Discord.
POST = "post"
EDIT = "edit"
DELETE = "delete"
NONE = "none"


@dataclass(frozen=True)
class StarboardOutcome:
    """What the cog must do after a star change (the DB is already updated)."""

    action: str  # POST | EDIT | DELETE | NONE
    channel_id: int | None  # the hall-of-fame channel (POST/EDIT/DELETE targets)
    starboard_message_id: int | None  # existing post (EDIT/DELETE)
    star_count: int


# ---------------------------------------------------------------------------
# Config writes (audited)
# ---------------------------------------------------------------------------


async def configure(
    *,
    guild_id: int,
    channel_id: int,
    threshold: int,
    emoji: str = "⭐",
    actor_id: int | None,
) -> int:
    """Set the hall-of-fame channel + threshold (audited). Returns the threshold."""
    threshold = max(1, int(threshold))
    await db.set_settings(
        guild_id,
        channel_id,
        threshold=threshold,
        emoji=emoji or "⭐",
        enabled=True,
    )
    await _emit(
        guild_id,
        mutation_type="configure_starboard",
        new_value=f"channel={channel_id},threshold={threshold},emoji={emoji}",
        actor_id=actor_id,
    )
    return threshold


async def disable(*, guild_id: int, actor_id: int | None) -> None:
    """Turn the starboard off for a guild (audited); config is preserved."""
    await db.set_enabled(guild_id, False)
    await _emit(
        guild_id,
        mutation_type="disable_starboard",
        new_value="disabled",
        actor_id=actor_id,
    )


async def get_settings(guild_id: int) -> dict | None:
    """Read the guild's starboard config (the cog/command read)."""
    return await db.get_settings(guild_id)


async def trigger_emoji(guild_id: int) -> str | None:
    """The configured trigger emoji, or ``None`` when unconfigured/disabled.

    The listener's fast-path gate — mirrors ``reaction_roles_enabled``: a cheap
    read that lets the cog ignore the vast majority of reactions immediately.
    """
    settings = await db.get_settings(guild_id)
    if settings is None or not settings["enabled"]:
        return None
    return settings["emoji"]


# ---------------------------------------------------------------------------
# Member star path (NOT audited — high-volume)
# ---------------------------------------------------------------------------


async def handle_star_change(
    *,
    guild_id: int,
    source_channel_id: int,
    source_message_id: int,
    star_count: int,
) -> StarboardOutcome:
    """Decide post/edit/delete for a star count change; update the DB count.

    Re-reads authoritative config + entry state (never trusts a delta — robust
    against missed events / restarts, like the role-menu re-read). The caller
    passes the *live* star count (recounted from the message) and performs the
    Discord I/O the returned outcome describes; on a POST it then calls
    :func:`record_post` with the new message id.
    """
    settings = await db.get_settings(guild_id)
    if settings is None or not settings["enabled"]:
        return StarboardOutcome(NONE, None, None, star_count)
    channel_id = int(settings["channel_id"])
    # Never starboard the starboard channel itself.
    if source_channel_id == channel_id:
        return StarboardOutcome(NONE, channel_id, None, star_count)

    threshold = int(settings["threshold"])
    entry = await db.get_entry(guild_id, source_message_id)
    sb_msg = (
        int(entry["starboard_message_id"])
        if entry and entry["starboard_message_id"]
        else None
    )
    meets = star_count >= threshold

    if meets and sb_msg is None:
        # Crossed the threshold for the first time → cog posts, then record_post.
        await db.upsert_entry(
            guild_id,
            source_message_id,
            star_count=star_count,
            starboard_message_id=None,
        )
        return StarboardOutcome(POST, channel_id, None, star_count)
    if meets and sb_msg is not None:
        await db.upsert_entry(
            guild_id,
            source_message_id,
            star_count=star_count,
            starboard_message_id=sb_msg,
        )
        return StarboardOutcome(EDIT, channel_id, sb_msg, star_count)
    if not meets and sb_msg is not None:
        await db.delete_entry(guild_id, source_message_id)
        return StarboardOutcome(DELETE, channel_id, sb_msg, star_count)
    return StarboardOutcome(NONE, channel_id, sb_msg, star_count)


async def record_post(
    guild_id: int,
    source_message_id: int,
    *,
    starboard_message_id: int,
    star_count: int,
) -> None:
    """Persist the posted starboard message id (cog calls this after sending)."""
    await db.upsert_entry(
        guild_id,
        source_message_id,
        star_count=star_count,
        starboard_message_id=starboard_message_id,
    )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


async def _emit(
    guild_id: int,
    *,
    mutation_type: str,
    new_value: str | None,
    actor_id: int | None,
) -> None:
    """Emit ``audit.action_recorded`` for a starboard config mutation."""
    from services.audit_events import emit_audit_action

    await emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="starboard",
        mutation_type=mutation_type,
        target=f"guild:{guild_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=new_value,
        actor_id=actor_id,
        actor_type="admin",
        occurred_at=datetime.now(tz=timezone.utc),
    )


__all__ = [
    "DELETE",
    "EDIT",
    "NONE",
    "POST",
    "StarboardOutcome",
    "configure",
    "disable",
    "get_settings",
    "handle_star_change",
    "record_post",
    "trigger_emoji",
]
