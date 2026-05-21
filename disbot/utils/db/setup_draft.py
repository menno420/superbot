"""Setup draft operations — DB primitives (Setup Wizard).

Owns the read/write surface for the ``setup_draft_operations`` table
created by migration 035.  Higher-level callers (:mod:`services.setup_draft`)
wrap these primitives; nothing outside this module + the service issues
raw SQL against the table.

Contract:

* Inserts are upserts on the slot key
  ``(guild_id, op_kind, subsystem, COALESCE(setting_name, ''),
  COALESCE(binding_name, ''))`` — a second draft for the same slot
  supersedes the first within a session.  ``seq`` is bumped to the
  new MAX+1 so the replaced row sorts at the back of the operator's
  draft list (it is logically a new edit, not the old one).
* Reads are ordered by ``seq`` ascending so callers reconstruct the
  operator's edit history in order.
* ``clear`` removes every row for a guild — invoked by Final Review
  on successful apply and by ``setup_session.mark_complete`` /
  ``dismiss``.

All writes occur in a single SQL statement; the upsert uses
PostgreSQL's ``ON CONFLICT`` on the partial UNIQUE index so the
SELECT-MAX-then-INSERT race window is closed at the DB layer.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.setup_draft")


_KNOWN_OP_KINDS: frozenset[str] = frozenset(
    {
        "bind_channel",
        "bind_role",
        "bind_category",
        "bind_thread",
        "bind_member",
        "clear_binding",
        "set_setting",
        "create_channel",
        "create_role",
        "create_category",
        "add_automation_rule",
        "enable_automation_rule",
        "disable_automation_rule",
        # Per-feature op kinds staged by Setup Wizard sections.
        # Routed by services.setup_operations._apply_set_cleanup_policy
        # and _apply_set_cog_routing respectively.
        "set_cleanup_policy",
        "set_cog_routing",
    },
)


async def insert(
    *,
    guild_id: int,
    session_started_at: datetime,
    op_kind: str,
    subsystem: str,
    binding_name: str | None,
    setting_name: str | None,
    target_id: int | None,
    target_name: str | None,
    target_kind: str | None,
    value_raw: str | None,
    resource_mode: str | None,
    resource_name: str | None,
    existing_id: int | None,
    automation_rule_id: int | None,
    automation_rule_name: str | None,
    trigger_kind: str | None,
    action_kind: str | None,
    trigger_config: dict[str, Any] | None,
    action_config: dict[str, Any] | None,
    schedule: str | None,
    timezone: str | None,
    actor_id: int | None,
    label: str,
    metadata: dict[str, Any] | None,
) -> int:
    """Insert or replace a draft op row; return the resulting ``seq``.

    Slot key (``guild_id``, ``op_kind``, ``subsystem``, ``setting_name``,
    ``binding_name``) is unique per guild.  When a row already exists
    for the slot, the existing row is replaced with the new content
    and assigned a fresh ``seq`` (current MAX+1 within the guild) so
    the operator-visible order reflects the latest edit.

    The CHECK on ``op_kind`` is also enforced at the SQL layer, but
    we validate here for an earlier failure with a friendlier traceback.
    """
    if op_kind not in _KNOWN_OP_KINDS:
        raise ValueError(
            f"op_kind must be one of {sorted(_KNOWN_OP_KINDS)}, got {op_kind!r}",
        )
    if not subsystem:
        raise ValueError("subsystem must be non-empty")
    if not label:
        raise ValueError("label must be non-empty")

    trigger_json = json.dumps(trigger_config) if trigger_config is not None else None
    action_json = json.dumps(action_config) if action_config is not None else None
    metadata_json = json.dumps(metadata) if metadata is not None else None

    # We allocate seq inside the upsert: COALESCE(MAX(seq), 0) + 1
    # within the same guild.  The unique index ensures only one row
    # per slot survives.
    row = await pool.get().fetchrow(
        """
        INSERT INTO setup_draft_operations (
            guild_id, session_started_at, seq, op_kind, subsystem,
            binding_name, setting_name, target_id, target_name, target_kind,
            value_raw, resource_mode, resource_name, existing_id,
            automation_rule_id, automation_rule_name, trigger_kind, action_kind,
            trigger_config_json, action_config_json, schedule, timezone,
            actor_id, label, metadata_json
        )
        VALUES (
            $1, $2,
            (SELECT COALESCE(MAX(seq), 0) + 1
               FROM setup_draft_operations
              WHERE guild_id = $1),
            $3, $4,
            $5, $6, $7, $8, $9,
            $10, $11, $12, $13,
            $14, $15, $16, $17,
            $18::JSONB, $19::JSONB, $20, $21,
            $22, $23, $24::JSONB
        )
        ON CONFLICT (
            guild_id, op_kind, subsystem,
            COALESCE(setting_name, ''),
            COALESCE(binding_name, '')
        ) DO UPDATE SET
            session_started_at   = EXCLUDED.session_started_at,
            seq                  = (SELECT COALESCE(MAX(seq), 0) + 1
                                      FROM setup_draft_operations
                                     WHERE guild_id = EXCLUDED.guild_id),
            target_id            = EXCLUDED.target_id,
            target_name          = EXCLUDED.target_name,
            target_kind          = EXCLUDED.target_kind,
            value_raw            = EXCLUDED.value_raw,
            resource_mode        = EXCLUDED.resource_mode,
            resource_name        = EXCLUDED.resource_name,
            existing_id          = EXCLUDED.existing_id,
            automation_rule_id   = EXCLUDED.automation_rule_id,
            automation_rule_name = EXCLUDED.automation_rule_name,
            trigger_kind         = EXCLUDED.trigger_kind,
            action_kind          = EXCLUDED.action_kind,
            trigger_config_json  = EXCLUDED.trigger_config_json,
            action_config_json   = EXCLUDED.action_config_json,
            schedule             = EXCLUDED.schedule,
            timezone             = EXCLUDED.timezone,
            actor_id             = EXCLUDED.actor_id,
            label                = EXCLUDED.label,
            metadata_json        = EXCLUDED.metadata_json,
            created_at           = NOW()
        RETURNING seq
        """,
        guild_id,
        session_started_at,
        op_kind,
        subsystem,
        binding_name,
        setting_name,
        target_id,
        target_name,
        target_kind,
        value_raw,
        resource_mode,
        resource_name,
        existing_id,
        automation_rule_id,
        automation_rule_name,
        trigger_kind,
        action_kind,
        trigger_json,
        action_json,
        schedule,
        timezone,
        actor_id,
        label,
        metadata_json,
    )
    return int(row["seq"])


async def list_rows(guild_id: int) -> list[dict[str, Any]]:
    """Return every draft row for ``guild_id`` ordered by ``seq`` asc."""
    rows = await pool.get().fetch(
        """
        SELECT id, guild_id, session_started_at, seq, op_kind, subsystem,
               binding_name, setting_name, target_id, target_name, target_kind,
               value_raw, resource_mode, resource_name, existing_id,
               automation_rule_id, automation_rule_name, trigger_kind,
               action_kind, trigger_config_json, action_config_json,
               schedule, timezone, actor_id, label, metadata_json, created_at
          FROM setup_draft_operations
         WHERE guild_id = $1
         ORDER BY seq ASC
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def clear(guild_id: int) -> int:
    """Delete every draft row for ``guild_id``; return the row count.

    Invoked by Final Review on successful apply and by
    ``setup_session.mark_complete`` / ``dismiss``.  No-op when the
    guild has no drafts.
    """
    row = await pool.get().fetchrow(
        """
        WITH deleted AS (
            DELETE FROM setup_draft_operations
             WHERE guild_id = $1
             RETURNING 1
        )
        SELECT COUNT(*) AS n FROM deleted
        """,
        guild_id,
    )
    return int(row["n"]) if row else 0


async def count(guild_id: int) -> int:
    """Return the number of drafts pending for ``guild_id``."""
    row = await pool.get().fetchrow(
        "SELECT COUNT(*) AS n FROM setup_draft_operations WHERE guild_id = $1",
        guild_id,
    )
    return int(row["n"]) if row else 0


__all__ = [
    "clear",
    "count",
    "insert",
    "list_rows",
]
