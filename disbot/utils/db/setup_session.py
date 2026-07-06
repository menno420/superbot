"""Setup session — DB primitives (Phase 9e / Track 4 PR 8).

Owns the read/write surface for the ``setup_session`` table created
by migration 031. Higher-level callers (:mod:`services.setup_session`
and the setup-launcher cog in Track 4 PR 9) wrap these primitives;
nothing outside this module + the service issues raw SQL against
``setup_session``.

Status semantics (mirror migration 031 CHECK constraint):

  pending      — guild joined, launcher posted, owner has not started
  in_progress  — owner clicked Start; wizard mid-flow
  complete     — owner finished at least once
  dismissed    — owner deferred / ignored the launcher
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.setup_session")

KNOWN_STATUSES: frozenset[str] = frozenset(
    {"pending", "in_progress", "complete", "dismissed"},
)


async def get(guild_id: int) -> dict[str, Any] | None:
    """Return the row for ``guild_id``, or ``None`` when none exists."""
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, guild_name, owner_id, joined_at, setup_status,
               setup_channel_id, setup_message_id, last_readiness_score,
               current_step, delegated_admins, skipped_sections,
               acknowledged_sections, depth, purpose,
               essential_message_id, essential_step,
               created_at, updated_at
        FROM setup_session
        WHERE guild_id = $1
        """,
        guild_id,
    )
    if row is None:
        return None
    return dict(row)


async def upsert(
    *,
    guild_id: int,
    guild_name: str,
    owner_id: int,
    setup_status: str = "pending",
    setup_channel_id: int | None = None,
    setup_message_id: int | None = None,
) -> None:
    """Insert or update a session row.

    ``joined_at`` is set to NOW() on insert and preserved on update.
    ``setup_status`` only changes via :func:`set_status` /
    :func:`set_step` to keep the lifecycle transitions auditable;
    the upsert path leaves it at its current value when the row
    already exists.
    """
    if setup_status not in KNOWN_STATUSES:
        raise ValueError(
            f"setup_status must be one of {sorted(KNOWN_STATUSES)}, "
            f"got {setup_status!r}",
        )
    await pool.get().execute(
        """
        INSERT INTO setup_session (
            guild_id, guild_name, owner_id, setup_status,
            setup_channel_id, setup_message_id
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (guild_id) DO UPDATE SET
            guild_name       = EXCLUDED.guild_name,
            owner_id         = EXCLUDED.owner_id,
            setup_channel_id = COALESCE(EXCLUDED.setup_channel_id,
                                        setup_session.setup_channel_id),
            setup_message_id = COALESCE(EXCLUDED.setup_message_id,
                                        setup_session.setup_message_id),
            updated_at       = NOW()
        """,
        guild_id,
        guild_name,
        owner_id,
        setup_status,
        setup_channel_id,
        setup_message_id,
    )


async def set_status(guild_id: int, status: str) -> None:
    """Move the row to one of the four documented statuses."""
    if status not in KNOWN_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(KNOWN_STATUSES)}, got {status!r}",
        )
    await pool.get().execute(
        """
        UPDATE setup_session
           SET setup_status = $2,
               updated_at   = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        status,
    )


async def set_step(guild_id: int, step: str | None) -> None:
    """Update the resume token for the wizard's current step."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET current_step = $2,
               updated_at   = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        step,
    )


async def set_readiness_score(guild_id: int, score: int | None) -> None:
    """Cache the latest readiness percentage for drift detection."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET last_readiness_score = $2,
               updated_at           = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        score,
    )


async def add_delegated_admin(guild_id: int, user_id: int) -> None:
    """Append ``user_id`` to ``delegated_admins`` (idempotent)."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET delegated_admins = (
                   SELECT ARRAY(SELECT DISTINCT UNNEST(delegated_admins || $2::BIGINT))
                   FROM setup_session WHERE guild_id = $1
               ),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        user_id,
    )


async def remove_delegated_admin(guild_id: int, user_id: int) -> None:
    """Drop ``user_id`` from ``delegated_admins``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET delegated_admins = ARRAY_REMOVE(delegated_admins, $2::BIGINT),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        user_id,
    )


async def clear(guild_id: int) -> None:
    """Delete the row entirely. Used by ``guild_lifecycle.teardown``."""
    await pool.get().execute(
        "DELETE FROM setup_session WHERE guild_id = $1",
        guild_id,
    )


async def add_skipped_section(guild_id: int, slug: str) -> None:
    """Append ``slug`` to ``skipped_sections`` (idempotent set semantics)."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET skipped_sections = (
                   SELECT ARRAY(SELECT DISTINCT UNNEST(skipped_sections || $2::TEXT))
                   FROM setup_session WHERE guild_id = $1
               ),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        slug,
    )


async def remove_skipped_section(guild_id: int, slug: str) -> None:
    """Drop ``slug`` from ``skipped_sections``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET skipped_sections = ARRAY_REMOVE(skipped_sections, $2::TEXT),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        slug,
    )


async def clear_skipped_sections(guild_id: int) -> None:
    """Empty the skipped-section set for ``guild_id``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET skipped_sections = '{}',
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
    )


async def add_acknowledged_section(guild_id: int, slug: str) -> None:
    """Append ``slug`` to ``acknowledged_sections`` (idempotent set semantics).

    Phase 2 added this for metadata-only / link-only sections (Purpose,
    AI link-only) that emit zero draft operations.  The hub's
    progress read model surfaces acknowledged slugs as APPLIED.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET acknowledged_sections = (
                   SELECT ARRAY(SELECT DISTINCT UNNEST(acknowledged_sections || $2::TEXT))
                   FROM setup_session WHERE guild_id = $1
               ),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        slug,
    )


async def remove_acknowledged_section(guild_id: int, slug: str) -> None:
    """Drop ``slug`` from ``acknowledged_sections``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET acknowledged_sections = ARRAY_REMOVE(acknowledged_sections, $2::TEXT),
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        slug,
    )


async def clear_acknowledged_sections(guild_id: int) -> None:
    """Empty the acknowledged-section set for ``guild_id``."""
    await pool.get().execute(
        """
        UPDATE setup_session
           SET acknowledged_sections = '{}',
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
    )


async def set_setup_channel_id(guild_id: int, channel_id: int | None) -> None:
    """Persist (or clear) the workspace's setup channel id.

    The setup wizard creates ``#superbot-setup`` and remembers its id
    on ``setup_session.setup_channel_id``; Phase 8's guarded cleanup
    service calls this with ``channel_id=None`` after a successful
    ``delete_setup_channel`` so a future ``/setup`` re-creates the
    channel cleanly rather than reusing the now-stale id.

    A dedicated setter is required because :func:`upsert` COALESCEs
    its ``setup_channel_id`` argument with the existing value, so
    the upsert path cannot clear a stale id.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET setup_channel_id = $2,
               updated_at       = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        channel_id,
    )


async def set_setup_message_id(guild_id: int, message_id: int | None) -> None:
    """Persist (or clear) the workspace wizard's anchor message id.

    The setup wizard posts a single message in the private setup channel
    and re-edits it across the session lifetime; ``message_id`` is the
    Discord snowflake of that anchor.  Passing ``None`` clears the
    pointer (e.g. when the launcher cog's resume sweep can't refetch
    the message and chooses to repost on the next ``/setup``).

    A dedicated setter is required because :func:`upsert` COALESCEs
    its ``setup_message_id`` argument with the existing value, so the
    upsert path cannot clear a stale id.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET setup_message_id = $2,
               updated_at       = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        message_id,
    )


async def set_essential_anchor(
    guild_id: int,
    message_id: int | None,
    step: int | None,
) -> None:
    """Record (or clear) the Essential Setup flow's message id + step.

    The plain-language Essential Setup spine posts a single message in the
    private setup channel and re-edits it across the flow; ``message_id`` is
    that anchor's Discord snowflake and ``step`` is the 0-based step index.
    Together they let the on-ready resume sweep revive the message in place
    after a restart (migration 099).  Passing both ``None`` clears the anchor
    when the flow completes.

    Distinct from ``setup_message_id`` / ``current_step`` (the launcher +
    advanced wizard anchors), which point at a different coexisting message.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET essential_message_id = $2,
               essential_step       = $3,
               updated_at           = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        message_id,
        step,
    )


async def set_essential_step(guild_id: int, step: int | None) -> None:
    """Update only the Essential Setup flow's step index.

    Called as the operator moves through the flow so a restart resumes at the
    right step.  Leaves ``essential_message_id`` untouched.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET essential_step = $2,
               updated_at     = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        step,
    )


async def clear_essential_anchor(guild_id: int) -> None:
    """Clear the Essential Setup anchor (message id + step → NULL).

    Used when the flow completes (reaches the summary) or its message can no
    longer be fetched, so the resume sweep stops trying to revive it.
    """
    await pool.get().execute(
        """
        UPDATE setup_session
           SET essential_message_id = NULL,
               essential_step        = NULL,
               updated_at            = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
    )


KNOWN_DEPTHS: frozenset[str] = frozenset({"quick", "standard", "advanced"})

#: Allowed values for ``setup_session.purpose``.  Validated at the Python
#: layer (migration 047 has no DB CHECK) so new options can land without
#: a follow-up migration.  Sections that read ``session.purpose`` should
#: treat unknown / NULL values as "unspecified".
KNOWN_PURPOSES: frozenset[str] = frozenset(
    {
        "community",
        "gaming_btd6",
        "support",
        "moderation",
        "ai_helper",
        "testing_private",
        "mixed",
    },
)


async def set_purpose(guild_id: int, purpose: str | None) -> None:
    """Persist (or clear) the operator's ``purpose`` choice.

    Phase 4 of the setup wizard.  Accepts any value in
    :data:`KNOWN_PURPOSES` or ``None`` (clears the pick).  Other
    values raise ``ValueError``.
    """
    if purpose is not None and purpose not in KNOWN_PURPOSES:
        raise ValueError(
            f"purpose must be one of {sorted(KNOWN_PURPOSES)} or None, got {purpose!r}",
        )
    await pool.get().execute(
        """
        UPDATE setup_session
           SET purpose    = $2,
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        purpose,
    )


async def set_depth(guild_id: int, depth: str | None) -> None:
    """Persist the operator's depth choice (or ``None`` to unset).

    Accepts ``"quick"``, ``"standard"``, ``"advanced"``, or ``None``;
    other values raise ``ValueError``. The CHECK constraint in
    migration 038 enforces the same set at the DB layer.
    """
    if depth is not None and depth not in KNOWN_DEPTHS:
        raise ValueError(
            f"depth must be one of {sorted(KNOWN_DEPTHS)} or None, got {depth!r}",
        )
    await pool.get().execute(
        """
        UPDATE setup_session
           SET depth = $2,
               updated_at = NOW()
         WHERE guild_id = $1
        """,
        guild_id,
        depth,
    )


__all__ = [
    "KNOWN_DEPTHS",
    "KNOWN_PURPOSES",
    "KNOWN_STATUSES",
    "add_acknowledged_section",
    "add_delegated_admin",
    "add_skipped_section",
    "clear",
    "clear_acknowledged_sections",
    "clear_essential_anchor",
    "clear_skipped_sections",
    "get",
    "remove_acknowledged_section",
    "remove_delegated_admin",
    "remove_skipped_section",
    "set_depth",
    "set_essential_anchor",
    "set_essential_step",
    "set_purpose",
    "set_readiness_score",
    "set_setup_channel_id",
    "set_setup_message_id",
    "set_status",
    "set_step",
    "upsert",
]
