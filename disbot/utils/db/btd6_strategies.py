"""Sole DB module for ``btd6_strategies`` + ``btd6_strategy_audit`` (M4).

Reads land here; writes route through
:mod:`services.btd6_strategy_mutation` so every state transition
produces an audit row in the same transaction.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.btd6_strategies")


_BASE_COLUMNS = (
    "id, origin_guild_id, current_guild_id, visibility, approval_status,"
    " approved_by, approved_by_id, approval_provider, approval_model,"
    " title, summary, map, mode, difficulty, hero, towers, upgrade_paths,"
    " round_range, steps, common_failures, source_links, submitted_by,"
    " submitter_display_snapshot, submitter_identity_state, origin_metadata,"
    " created_at, updated_at, version"
)


async def insert_strategy(
    *,
    origin_guild_id: int,
    current_guild_id: int | None,
    visibility: str,
    approval_status: str,
    title: str,
    summary: str,
    map: str | None,
    mode: str | None,
    difficulty: str | None,
    hero: str | None,
    towers: list[Any],
    upgrade_paths: list[Any],
    round_range: dict[str, Any] | None,
    steps: list[Any],
    common_failures: list[Any],
    source_links: list[Any],
    submitted_by: int | None,
    submitter_display_snapshot: str | None,
    origin_metadata: dict[str, Any],
) -> int:
    row = await pool.get().fetchrow(
        f"""
        INSERT INTO btd6_strategies (
            origin_guild_id, current_guild_id, visibility, approval_status,
            title, summary, map, mode, difficulty, hero, towers,
            upgrade_paths, round_range, steps, common_failures, source_links,
            submitted_by, submitter_display_snapshot, origin_metadata,
            created_at, updated_at, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11::jsonb, $12::jsonb, $13::jsonb, $14::jsonb, $15::jsonb,
            $16::jsonb, $17, $18, $19::jsonb, NOW(), NOW(), 1
        )
        RETURNING id
        """,
        origin_guild_id, current_guild_id, visibility, approval_status,
        title, summary, map, mode, difficulty, hero,
        json.dumps(towers), json.dumps(upgrade_paths),
        json.dumps(round_range) if round_range is not None else None,
        json.dumps(steps), json.dumps(common_failures),
        json.dumps(source_links), submitted_by, submitter_display_snapshot,
        json.dumps(origin_metadata),
    )
    return int(row["id"])


async def get_strategy(strategy_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        f"SELECT {_BASE_COLUMNS} FROM btd6_strategies WHERE id = $1",
        strategy_id,
    )
    return _row_to_dict(row)


async def search_strategies(
    *,
    guild_id: int | None = None,
    visibility: str | None = None,
    approval_status: str | None = None,
    map: str | None = None,
    mode: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    sql = f"SELECT {_BASE_COLUMNS} FROM btd6_strategies"
    args: list[Any] = []
    clauses: list[str] = []
    if guild_id is not None:
        args.append(guild_id)
        clauses.append(
            "(origin_guild_id = $%d OR current_guild_id = $%d)" % (len(args), len(args)),
        )
    if visibility is not None:
        args.append(visibility)
        clauses.append(f"visibility = ${len(args)}")
    if approval_status is not None:
        args.append(approval_status)
        clauses.append(f"approval_status = ${len(args)}")
    if map is not None:
        args.append(map)
        clauses.append(f"map = ${len(args)}")
    if mode is not None:
        args.append(mode)
        clauses.append(f"mode = ${len(args)}")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    args.append(int(limit))
    sql += f" ORDER BY updated_at DESC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [_row_to_dict(r) for r in rows]


async def update_strategy_state(
    strategy_id: int,
    *,
    approval_status: str | None = None,
    visibility: str | None = None,
    approved_by: str | None = None,
    approved_by_id: int | None = None,
    approval_provider: str | None = None,
    approval_model: str | None = None,
    current_guild_id: int | None = None,
    bump_version: bool = False,
) -> None:
    """Apply a partial state update.

    Uses a single fixed SQL statement with COALESCE on every column
    so the dynamic-SQL invariant
    (``tests/unit/invariants/test_no_dynamic_sql.py``) stays happy.
    Pass ``None`` to leave a column untouched. ``current_guild_id``
    is the one exception: it accepts an explicit NULL via the
    ``_clear_current_guild`` flag in the row payload (used by the
    retention path).
    """
    bump = 1 if bump_version else 0
    await pool.get().execute(
        """
        UPDATE btd6_strategies SET
            approval_status   = COALESCE($2, approval_status),
            visibility        = COALESCE($3, visibility),
            approved_by       = COALESCE($4, approved_by),
            approved_by_id    = COALESCE($5, approved_by_id),
            approval_provider = COALESCE($6, approval_provider),
            approval_model    = COALESCE($7, approval_model),
            current_guild_id  = COALESCE($8, current_guild_id),
            version           = version + $9,
            updated_at        = NOW()
        WHERE id = $1
        """,
        strategy_id,
        approval_status,
        visibility,
        approved_by,
        approved_by_id,
        approval_provider,
        approval_model,
        current_guild_id,
        bump,
    )


async def clear_current_guild(strategy_id: int) -> None:
    """Explicitly set ``current_guild_id`` to NULL (retention path)."""
    await pool.get().execute(
        """
        UPDATE btd6_strategies
        SET current_guild_id = NULL, updated_at = NOW()
        WHERE id = $1
        """,
        strategy_id,
    )


async def anonymize_submitter(
    strategy_id: int,
    *,
    new_state: str,
) -> None:
    await pool.get().execute(
        """
        UPDATE btd6_strategies
        SET submitted_by = NULL,
            submitter_display_snapshot = NULL,
            submitter_identity_state = $2,
            updated_at = NOW()
        WHERE id = $1
        """,
        strategy_id, new_state,
    )


async def record_strategy_audit(
    strategy_id: int,
    *,
    actor_kind: str,
    actor_id: int | None,
    action: str,
    detail: dict[str, Any] | None = None,
) -> int:
    row = await pool.get().fetchrow(
        """
        INSERT INTO btd6_strategy_audit (
            strategy_id, actor_kind, actor_id, action, detail, created_at
        ) VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
        RETURNING id
        """,
        strategy_id, actor_kind, actor_id, action,
        json.dumps(detail or {}),
    )
    return int(row["id"])


async def list_strategy_audit(
    strategy_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT id, strategy_id, actor_kind, actor_id, action, detail, created_at
        FROM btd6_strategy_audit
        WHERE strategy_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        strategy_id, int(limit),
    )
    return [dict(r) for r in rows]


async def delete_guild_local_for_guild(guild_id: int) -> int:
    """Drop ``visibility='guild'`` rows for ``guild_id``.

    Published rows survive guild leave by accepted decision; the
    mutation service handles the ``current_guild_id`` reset
    separately so the audit row records the transition.
    """
    result = await pool.get().execute(
        """
        DELETE FROM btd6_strategies
        WHERE current_guild_id = $1
          AND visibility = 'guild'
        """,
        guild_id,
    )
    return int(result.split()[-1]) if result else 0


async def detach_published_from_guild(guild_id: int) -> int:
    """Set ``current_guild_id`` to NULL on published rows for the
    departed guild; preserves ``origin_guild_id`` for attribution."""
    result = await pool.get().execute(
        """
        UPDATE btd6_strategies
        SET current_guild_id = NULL,
            updated_at = NOW()
        WHERE current_guild_id = $1
          AND visibility = 'published'
        """,
        guild_id,
    )
    return int(result.split()[-1]) if result else 0


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in (
        "towers", "upgrade_paths", "steps", "common_failures",
        "source_links", "origin_metadata",
    ):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except (TypeError, ValueError):
                data[key] = []
    if "round_range" in data and isinstance(data["round_range"], str):
        try:
            data["round_range"] = json.loads(data["round_range"])
        except (TypeError, ValueError):
            data["round_range"] = None
    return data
