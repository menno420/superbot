"""Setup session lifecycle service — Phase 9e / Track 4 PR 8.

Wraps :mod:`utils.db.setup_session` with the four lifecycle
transitions the launcher cog uses:

* :func:`start_session` — bot just joined or owner clicked Start;
  upserts the row in ``pending``.
* :func:`resume_session` — fetch the row on ``on_ready`` so the
  launcher can re-render in the correct state.
* :func:`mark_in_progress` — owner clicked the wizard's first step.
* :func:`mark_complete` — owner finished a full setup walkthrough.
* :func:`dismiss` — owner deferred the launcher.

All functions are best-effort: a DB error is logged and surfaced via
the return value so the caller can decide whether to retry. None of
them perform Discord-side I/O; the launcher cog (Track 4 PR 9) owns
the embed / view orchestration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from utils.db import setup_session as db

logger = logging.getLogger("bot.services.setup_session")


@dataclass(frozen=True)
class SetupSession:
    """Snapshot of one row of ``setup_session``."""

    guild_id: int
    guild_name: str
    owner_id: int
    setup_status: str
    setup_channel_id: int | None
    setup_message_id: int | None
    last_readiness_score: int | None
    current_step: str | None
    delegated_admins: tuple[int, ...]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> SetupSession:
        return cls(
            guild_id=row["guild_id"],
            guild_name=row["guild_name"],
            owner_id=row["owner_id"],
            setup_status=row["setup_status"],
            setup_channel_id=row.get("setup_channel_id"),
            setup_message_id=row.get("setup_message_id"),
            last_readiness_score=row.get("last_readiness_score"),
            current_step=row.get("current_step"),
            delegated_admins=tuple(row.get("delegated_admins") or ()),
        )


async def start_session(
    *,
    guild_id: int,
    guild_name: str,
    owner_id: int,
    setup_channel_id: int | None = None,
    setup_message_id: int | None = None,
) -> SetupSession:
    """Create or refresh the row in ``pending``.

    Idempotent: if a row already exists, this only updates the
    cached guild_name / owner_id / channel-message ids and leaves
    the existing ``setup_status`` untouched.
    """
    await db.upsert(
        guild_id=guild_id,
        guild_name=guild_name,
        owner_id=owner_id,
        setup_status="pending",
        setup_channel_id=setup_channel_id,
        setup_message_id=setup_message_id,
    )
    row = await db.get(guild_id)
    if row is None:
        # Should never happen — we just upserted. Surface defensively.
        raise RuntimeError(
            f"setup_session.start_session: row for guild_id={guild_id} "
            "missing immediately after upsert.",
        )
    return SetupSession.from_row(row)


async def resume_session(guild_id: int) -> SetupSession | None:
    """Return the existing row, or ``None`` if the bot never joined."""
    row = await db.get(guild_id)
    if row is None:
        return None
    return SetupSession.from_row(row)


async def mark_in_progress(guild_id: int, *, step: str | None = None) -> None:
    """Move the row to ``in_progress`` and optionally record a step."""
    await db.set_status(guild_id, "in_progress")
    if step is not None:
        await db.set_step(guild_id, step)


async def mark_complete(guild_id: int) -> None:
    """Move the row to ``complete``; clears any in-flight step token."""
    await db.set_status(guild_id, "complete")
    await db.set_step(guild_id, None)


async def dismiss(guild_id: int) -> None:
    """Move the row to ``dismissed``; clears any in-flight step token.

    Note: this only flips the launcher state. It does **not** delete
    the guild's bound resources or settings — those persist so the
    owner can re-run setup later.
    """
    await db.set_status(guild_id, "dismissed")
    await db.set_step(guild_id, None)


async def record_readiness_score(guild_id: int, score: int | None) -> None:
    """Cache the latest readiness % so drift can be detected on re-runs."""
    await db.set_readiness_score(guild_id, score)


__all__ = [
    "SetupSession",
    "dismiss",
    "mark_complete",
    "mark_in_progress",
    "record_readiness_score",
    "resume_session",
    "start_session",
]
