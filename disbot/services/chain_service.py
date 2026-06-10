"""Chain game — canonical mutation owner for ``chain_channels`` (RS07).

Before this seam, ``cogs/chain_cog.py`` owned the chain config mutations
in-cog: the four typed commands and the four panel modals each ran their
own existence checks and called the ``utils.db.games.chain`` writers
directly (the last named service-boundary hole from the 2026-06-10
runtime/services map — FIND-RS07). This module is the Batch 3 pattern
(:mod:`services.command_routing`) applied to chain: the service reads the
old row, validates, performs the write, emits the ``audit.action_recorded``
companion with the real previous value, and returns a typed
:class:`ChainMutationResult`. Callers render messages from the result;
they must not call the ``utils.db.games.chain`` writers directly (fenced
by ``tests/unit/invariants/test_chain_write_boundary.py``).

Two write lanes live here:

* **Config** (``create_chain`` / ``delete_chain`` / ``set_word_limit``) —
  admin-initiated, audited, direct-lane per ``docs/ownership.md``
  § "Direct vs. draft mutation lanes".
* **Game state** (:func:`record_chain_progress`) — the per-message
  ``chain_count`` increment from the message pipeline. Deliberately
  **not** audited (hot path, no operator intent), but routed through the
  service so ``chain_channels`` has exactly one writing module.

Reads (``get_chain_channel`` / ``get_all_chain_channels``) stay direct via
``utils.db`` — panels and embeds compose them freely (read lane).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from services.audit_events import emit_audit_action
from utils.db.games import chain as db

logger = logging.getLogger("bot.services.chain")

ChainMutationStatus = Literal[
    "applied",
    "already_exists",
    "not_found",
    "no_change",
    "invalid",
]


@dataclass(frozen=True)
class ChainMutationResult:
    """Outcome of a chain config write.

    ``status`` other than ``"applied"`` means **no write happened** (and no
    audit row was emitted): the existence/validation checks that used to be
    duplicated across the typed commands and the panel modals live here now.
    ``mutation_id`` / ``audit_emitted`` are only meaningful when applied.
    """

    status: ChainMutationStatus
    guild_id: int | None
    channel_id: int
    action: str
    old_value: str | None = None
    new_value: str | None = None
    mutation_id: str | None = None
    audit_emitted: bool = False

    @property
    def applied(self) -> bool:
        return self.status == "applied"


def _describe_row(row: dict | None) -> str | None:
    """Compact audit string for an existing chain row (no user content
    beyond the configured word, which the operator set themselves).
    """
    if not row:
        return None
    parts: list[str] = []
    if row.get("word"):
        parts.append(f"word={row['word']}")
    if row.get("word_limit"):
        parts.append(f"limit={row['word_limit']}")
    return " ".join(parts) or "(empty row)"


async def _emit(
    *,
    mutation_type: str,
    guild_id: int | None,
    channel_id: int,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
) -> tuple[str, bool]:
    mutation_id = str(uuid.uuid4())
    audit_emitted = await emit_audit_action(
        mutation_id=mutation_id,
        subsystem="chain",
        mutation_type=mutation_type,
        target=f"channel:{channel_id}",
        scope="channel",
        guild_id=guild_id,
        prev_value=prev_value,
        new_value=new_value,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=datetime.now(tz=timezone.utc),
    )
    return mutation_id, audit_emitted


async def create_chain(
    *,
    guild_id: int | None,
    channel_id: int,
    word: str,
    actor_id: int | None,
    actor_type: str = "user",
) -> ChainMutationResult:
    """Create (or claim) the chain for ``channel_id`` — the canonical write.

    Normalizes the word (``strip().lower()`` — the typed command and the
    modal used to normalize differently), rejects an empty word, refuses a
    channel that already has an active chain word, and **preserves an
    existing word limit** (the old direct upsert silently reset a
    limit-only row's ``word_limit`` to 0 when a chain was created on top
    of it — pinned by ``test_create_chain_preserves_existing_limit``).
    """
    normalized = word.strip().lower()
    if not normalized:
        return ChainMutationResult(
            status="invalid",
            guild_id=guild_id,
            channel_id=channel_id,
            action="create_chain",
        )
    existing = await db.get_chain_channel(channel_id)
    if existing and existing.get("word"):
        return ChainMutationResult(
            status="already_exists",
            guild_id=guild_id,
            channel_id=channel_id,
            action="create_chain",
            old_value=_describe_row(existing),
        )
    await db.set_chain_channel(
        channel_id,
        guild_id,
        normalized,
        limit=(existing or {}).get("word_limit") or 0,
    )
    mutation_id, audit_emitted = await _emit(
        mutation_type="create_chain",
        guild_id=guild_id,
        channel_id=channel_id,
        prev_value=_describe_row(existing),
        new_value=f"word={normalized}",
        actor_id=actor_id,
        actor_type=actor_type,
    )
    return ChainMutationResult(
        status="applied",
        guild_id=guild_id,
        channel_id=channel_id,
        action="create_chain",
        old_value=_describe_row(existing),
        new_value=normalized,
        mutation_id=mutation_id,
        audit_emitted=audit_emitted,
    )


async def delete_chain(
    *,
    guild_id: int | None,
    channel_id: int,
    actor_id: int | None,
    actor_type: str = "user",
) -> ChainMutationResult:
    """Delete the chain row for ``channel_id`` (word **and** limit)."""
    existing = await db.get_chain_channel(channel_id)
    if not existing:
        return ChainMutationResult(
            status="not_found",
            guild_id=guild_id,
            channel_id=channel_id,
            action="delete_chain",
        )
    await db.delete_chain_channel(channel_id)
    mutation_id, audit_emitted = await _emit(
        mutation_type="delete_chain",
        guild_id=guild_id,
        channel_id=channel_id,
        prev_value=_describe_row(existing),
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
    )
    return ChainMutationResult(
        status="applied",
        guild_id=guild_id,
        channel_id=channel_id,
        action="delete_chain",
        old_value=_describe_row(existing),
        mutation_id=mutation_id,
        audit_emitted=audit_emitted,
    )


async def set_word_limit(
    *,
    guild_id: int | None,
    channel_id: int,
    limit: int,
    actor_id: int | None,
    actor_type: str = "user",
) -> ChainMutationResult:
    """Set (``limit > 0``) or remove (``limit == 0``) the word limit.

    Requires an existing chain row (matching both legacy surfaces) and
    skips the write + audit when the effective limit would not change.
    """
    if limit < 0:
        return ChainMutationResult(
            status="invalid",
            guild_id=guild_id,
            channel_id=channel_id,
            action="set_chain_limit",
        )
    existing = await db.get_chain_channel(channel_id)
    if not existing:
        return ChainMutationResult(
            status="not_found",
            guild_id=guild_id,
            channel_id=channel_id,
            action="set_chain_limit",
        )
    old_limit = existing.get("word_limit") or 0
    if old_limit == limit:
        return ChainMutationResult(
            status="no_change",
            guild_id=guild_id,
            channel_id=channel_id,
            action="set_chain_limit",
            old_value=str(old_limit),
            new_value=str(limit),
        )
    await db.set_chain_limit(channel_id, limit)
    mutation_id, audit_emitted = await _emit(
        mutation_type="set_chain_limit",
        guild_id=guild_id,
        channel_id=channel_id,
        prev_value=str(old_limit),
        new_value=str(limit),
        actor_id=actor_id,
        actor_type=actor_type,
    )
    return ChainMutationResult(
        status="applied",
        guild_id=guild_id,
        channel_id=channel_id,
        action="set_chain_limit",
        old_value=str(old_limit),
        new_value=str(limit),
        mutation_id=mutation_id,
        audit_emitted=audit_emitted,
    )


async def record_chain_progress(channel_id: int) -> int:
    """Increment the channel's ``chain_count`` — per-message game state.

    Called by the chain message-pipeline stage for every allowed message.
    Not audited (no operator intent, hot path); lives here so the service
    is the sole ``chain_channels`` writer.
    """
    return await db.increment_chain_count(channel_id)


__all__ = [
    "ChainMutationResult",
    "ChainMutationStatus",
    "create_chain",
    "delete_chain",
    "record_chain_progress",
    "set_word_limit",
]
