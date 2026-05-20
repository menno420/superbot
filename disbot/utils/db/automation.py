"""Automation — DB primitives (Phase 9g / Track 6 PR 15).

Owns the read/write surface for ``automation_rules`` and
``automation_runs``. Higher-level callers (the
:class:`AutomationMutationPipeline` in Track 6 PR 16, the executor
in Track 6 PR 17, the scheduler in Track 6 PR 18) wrap these
primitives.

Status semantics for ``automation_runs`` (mirror migration 033
CHECK): ``queued`` / ``running`` / ``success`` / ``failure`` /
``skipped``.

All write primitives serialise ``trigger_config`` / ``action_config``
/ ``result_summary`` via :func:`json.dumps` because asyncpg's JSONB
codec is not always installed. The DB stores TEXT-encoded JSONB and
the read primitives decode it on the way back out.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.automation")

KNOWN_RUN_STATUSES: frozenset[str] = frozenset(
    {"queued", "running", "success", "failure", "skipped"},
)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _encode(value: Any | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str)


def _decode(value: Any | None) -> Any | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# ---------------------------------------------------------------------------
# automation_rules — CRUD
# ---------------------------------------------------------------------------


async def get_rule(rule_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, guild_id, name, enabled, trigger_kind, trigger_config,
               action_kind, action_config, schedule, timezone,
               last_run_at, next_run_at, failure_count, last_error,
               created_by, created_at, updated_at
        FROM automation_rules
        WHERE id = $1
        """,
        rule_id,
    )
    if row is None:
        return None
    out = dict(row)
    out["trigger_config"] = _decode(out.get("trigger_config")) or {}
    out["action_config"] = _decode(out.get("action_config")) or {}
    return out


async def get_rule_by_name(guild_id: int, name: str) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, guild_id, name, enabled, trigger_kind, trigger_config,
               action_kind, action_config, schedule, timezone,
               last_run_at, next_run_at, failure_count, last_error,
               created_by, created_at, updated_at
        FROM automation_rules
        WHERE guild_id = $1 AND name = $2
        """,
        guild_id,
        name,
    )
    if row is None:
        return None
    out = dict(row)
    out["trigger_config"] = _decode(out.get("trigger_config")) or {}
    out["action_config"] = _decode(out.get("action_config")) or {}
    return out


async def list_rules_for_guild(guild_id: int) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT id, guild_id, name, enabled, trigger_kind, trigger_config,
               action_kind, action_config, schedule, timezone,
               last_run_at, next_run_at, failure_count, last_error,
               created_by, created_at, updated_at
        FROM automation_rules
        WHERE guild_id = $1
        ORDER BY name
        """,
        guild_id,
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        rec["trigger_config"] = _decode(rec.get("trigger_config")) or {}
        rec["action_config"] = _decode(rec.get("action_config")) or {}
        out.append(rec)
    return out


async def insert_rule(
    *,
    guild_id: int,
    name: str,
    trigger_kind: str,
    action_kind: str,
    trigger_config: dict[str, Any] | None = None,
    action_config: dict[str, Any] | None = None,
    schedule: str | None = None,
    timezone: str = "UTC",
    created_by: int | None = None,
) -> int:
    """Insert a new disabled rule. Returns the new row's ``id``."""
    row = await pool.get().fetchrow(
        """
        INSERT INTO automation_rules (
            guild_id, name, trigger_kind, trigger_config,
            action_kind, action_config, schedule, timezone, created_by
        )
        VALUES ($1, $2, $3, $4::JSONB, $5, $6::JSONB, $7, $8, $9)
        RETURNING id
        """,
        guild_id,
        name,
        trigger_kind,
        _encode(trigger_config or {}),
        action_kind,
        _encode(action_config or {}),
        schedule,
        timezone,
        created_by,
    )
    if row is None:
        raise RuntimeError(
            "automation.insert_rule: RETURNING returned no row.",
        )
    return int(row["id"])


async def set_enabled(rule_id: int, enabled: bool) -> None:
    await pool.get().execute(
        """
        UPDATE automation_rules
           SET enabled    = $2,
               updated_at = NOW()
         WHERE id = $1
        """,
        rule_id,
        enabled,
    )


async def update_schedule_state(
    rule_id: int,
    *,
    next_run_at: Any | None,
    last_run_at: Any | None = None,
) -> None:
    """Set the scheduler's bookkeeping fields after computing the next
    fire time.
    """
    await pool.get().execute(
        """
        UPDATE automation_rules
           SET next_run_at = $2,
               last_run_at = COALESCE($3, last_run_at),
               updated_at  = NOW()
         WHERE id = $1
        """,
        rule_id,
        next_run_at,
        last_run_at,
    )


async def record_failure(rule_id: int, error: str) -> int:
    """Increment ``failure_count`` and store ``error``. Returns the new
    ``failure_count`` so the caller can act on the auto-disable
    threshold.
    """
    row = await pool.get().fetchrow(
        """
        UPDATE automation_rules
           SET failure_count = failure_count + 1,
               last_error    = $2,
               updated_at    = NOW()
         WHERE id = $1
        RETURNING failure_count
        """,
        rule_id,
        error[:1024],
    )
    if row is None:
        return 0
    return int(row["failure_count"])


async def reset_failure_count(rule_id: int) -> None:
    """Called by the executor after a successful run."""
    await pool.get().execute(
        """
        UPDATE automation_rules
           SET failure_count = 0,
               last_error    = NULL,
               updated_at    = NOW()
         WHERE id = $1
        """,
        rule_id,
    )


async def delete_rule(rule_id: int) -> None:
    """Cascades into ``automation_runs`` via the FK."""
    await pool.get().execute(
        "DELETE FROM automation_rules WHERE id = $1",
        rule_id,
    )


async def delete_rules_for_guild(guild_id: int) -> int:
    """Used by ``guild_lifecycle.teardown``. Returns the number of
    rules deleted.
    """
    result = await pool.get().execute(
        "DELETE FROM automation_rules WHERE guild_id = $1",
        guild_id,
    )
    return _parse_delete_count(result)


# ---------------------------------------------------------------------------
# automation_runs — append-only
# ---------------------------------------------------------------------------


async def claim_run(
    *,
    rule_id: int,
    guild_id: int,
    idempotency_key: str,
    dry_run: bool = False,
) -> int | None:
    """Insert a new run row in ``queued`` status. Returns the new
    row's ``id``, or ``None`` if the idempotency key is already
    taken (i.e. another scheduler beat us to it).
    """
    try:
        row = await pool.get().fetchrow(
            """
            INSERT INTO automation_runs (
                rule_id, guild_id, status, dry_run, idempotency_key
            )
            VALUES ($1, $2, 'queued', $3, $4)
            RETURNING id
            """,
            rule_id,
            guild_id,
            dry_run,
            idempotency_key,
        )
    except Exception:
        logger.exception(
            "automation.claim_run: insert failed for rule_id=%d; "
            "treating as already-claimed.",
            rule_id,
        )
        return None
    if row is None:
        return None
    return int(row["id"])


async def mark_running(run_id: int) -> None:
    await pool.get().execute(
        """
        UPDATE automation_runs
           SET status = 'running'
         WHERE id = $1
        """,
        run_id,
    )


async def finish_run(
    *,
    run_id: int,
    status: str,
    result_summary: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    if status not in KNOWN_RUN_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(KNOWN_RUN_STATUSES)}, got {status!r}",
        )
    await pool.get().execute(
        """
        UPDATE automation_runs
           SET status         = $2,
               finished_at    = NOW(),
               result_summary = COALESCE($3::JSONB, result_summary),
               error          = $4
         WHERE id = $1
        """,
        run_id,
        status,
        _encode(result_summary) if result_summary is not None else None,
        error,
    )


async def list_runs_for_rule(
    rule_id: int,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT id, rule_id, guild_id, status, dry_run, idempotency_key,
               started_at, finished_at, result_summary, error
        FROM automation_runs
        WHERE rule_id = $1
        ORDER BY started_at DESC
        LIMIT $2
        """,
        rule_id,
        limit,
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        rec["result_summary"] = _decode(rec.get("result_summary")) or {}
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_delete_count(result: str | None) -> int:
    if not result:
        return 0
    parts = result.split()
    if len(parts) < 2 or parts[0] != "DELETE":
        return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0


__all__ = [
    "KNOWN_RUN_STATUSES",
    "claim_run",
    "delete_rule",
    "delete_rules_for_guild",
    "finish_run",
    "get_rule",
    "get_rule_by_name",
    "insert_rule",
    "list_rules_for_guild",
    "list_runs_for_rule",
    "mark_running",
    "record_failure",
    "reset_failure_count",
    "set_enabled",
    "update_schedule_state",
]
