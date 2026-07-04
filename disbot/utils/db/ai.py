"""AI Platform DB primitives (M2 — typed policy + decision audit).

The only module that touches the ``ai_guild_policy``,
``ai_channel_policy``, ``ai_category_policy``, ``ai_role_policy``,
``ai_instruction_profile``, and ``ai_decision_audit`` tables.

Reads land here; writes flow through the M2 service-layer mutation
pipelines (``services.ai_policy_mutation`` /
``services.ai_instruction_mutation`` /
``services.ai_decision_audit_service``) which call these write
helpers inside the audited transaction.

The ``audit_log_channel`` binding for the AI subsystem is NOT
stored in any table here — it lives in ``subsystem_bindings``
under the M1 BindingSpec and is the single source of truth.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import pool

logger = logging.getLogger("bot.db.ai")


# ---------------------------------------------------------------------------
# ai_guild_policy
# ---------------------------------------------------------------------------


async def get_guild_policy(guild_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, enabled, natural_language_enabled,
               default_provider, default_model, minimum_level_default,
               cooldown_seconds, fresh_user_mention_allowance,
               guild_instruction_profile_id, orchestration_profile,
               generation, updated_at, updated_by
        FROM ai_guild_policy
        WHERE guild_id = $1
        """,
        guild_id,
    )
    return dict(row) if row else None


async def upsert_guild_policy(
    guild_id: int,
    *,
    enabled: bool,
    natural_language_enabled: bool,
    default_provider: str,
    default_model: str,
    minimum_level_default: int,
    cooldown_seconds: int,
    fresh_user_mention_allowance: int,
    guild_instruction_profile_id: int | None,
    updated_by: int | None,
) -> int:
    """Upsert the per-guild policy row; returns the new ``generation``."""
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_guild_policy (
            guild_id, enabled, natural_language_enabled, default_provider,
            default_model, minimum_level_default, cooldown_seconds,
            fresh_user_mention_allowance, guild_instruction_profile_id,
            generation, updated_at, updated_by
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, 0, NOW(), $10
        )
        ON CONFLICT (guild_id) DO UPDATE SET
            enabled                      = EXCLUDED.enabled,
            natural_language_enabled     = EXCLUDED.natural_language_enabled,
            default_provider             = EXCLUDED.default_provider,
            default_model                = EXCLUDED.default_model,
            minimum_level_default        = EXCLUDED.minimum_level_default,
            cooldown_seconds             = EXCLUDED.cooldown_seconds,
            fresh_user_mention_allowance = EXCLUDED.fresh_user_mention_allowance,
            guild_instruction_profile_id = EXCLUDED.guild_instruction_profile_id,
            generation                   = ai_guild_policy.generation + 1,
            updated_at                   = NOW(),
            updated_by                   = EXCLUDED.updated_by
        RETURNING generation
        """,
        guild_id,
        enabled,
        natural_language_enabled,
        default_provider,
        default_model,
        minimum_level_default,
        cooldown_seconds,
        fresh_user_mention_allowance,
        guild_instruction_profile_id,
        updated_by,
    )
    return int(row["generation"])


async def bump_generation(guild_id: int) -> int:
    """Bump ``ai_guild_policy.generation`` to invalidate caches."""
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_guild_policy (guild_id, generation)
        VALUES ($1, 1)
        ON CONFLICT (guild_id) DO UPDATE SET
            generation = ai_guild_policy.generation + 1,
            updated_at = NOW()
        RETURNING generation
        """,
        guild_id,
    )
    return int(row["generation"])


# ---------------------------------------------------------------------------
# Orchestration-profile column setters (migration 062)
# ---------------------------------------------------------------------------
#
# Each touches ONLY the orchestration_profile column (and updated_at/by),
# leaving the natural-language reply policy on the same row untouched. The
# guild setter bumps generation inline (like upsert_guild_policy); the
# channel/category setters leave the bump to the mutation seam's
# bump_generation call, matching upsert_channel_policy / upsert_category_policy.
# ``orchestration_profile`` is validated against the built-in presets at the
# audited service seam (services.ai_orchestration_mutation), so these write the
# value as-is. NULL clears the override (inherit).


async def set_guild_orchestration_profile(
    guild_id: int,
    *,
    orchestration_profile: str | None,
    updated_by: int | None,
) -> int:
    """Set the guild-default orchestration profile; returns new ``generation``."""
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_guild_policy (guild_id, orchestration_profile,
                                     generation, updated_at, updated_by)
        VALUES ($1, $2, 0, NOW(), $3)
        ON CONFLICT (guild_id) DO UPDATE SET
            orchestration_profile = EXCLUDED.orchestration_profile,
            generation            = ai_guild_policy.generation + 1,
            updated_at            = NOW(),
            updated_by            = EXCLUDED.updated_by
        RETURNING generation
        """,
        guild_id,
        orchestration_profile,
        updated_by,
    )
    return int(row["generation"])


async def set_channel_orchestration_profile(
    guild_id: int,
    channel_id: int,
    *,
    orchestration_profile: str | None,
    updated_by: int | None,
) -> None:
    """Set a channel's orchestration profile (mode defaults to 'inherit' on insert)."""
    await pool.get().execute(
        """
        INSERT INTO ai_channel_policy (guild_id, channel_id, mode,
                                       orchestration_profile, updated_at, updated_by)
        VALUES ($1, $2, 'inherit', $3, NOW(), $4)
        ON CONFLICT (guild_id, channel_id) DO UPDATE SET
            orchestration_profile = EXCLUDED.orchestration_profile,
            updated_at            = NOW(),
            updated_by            = EXCLUDED.updated_by
        """,
        guild_id,
        channel_id,
        orchestration_profile,
        updated_by,
    )


async def set_category_orchestration_profile(
    guild_id: int,
    category_id: int,
    *,
    orchestration_profile: str | None,
    updated_by: int | None,
) -> None:
    """Set a category's orchestration profile (mode defaults to 'inherit' on insert)."""
    await pool.get().execute(
        """
        INSERT INTO ai_category_policy (guild_id, category_id, mode,
                                        orchestration_profile, updated_at, updated_by)
        VALUES ($1, $2, 'inherit', $3, NOW(), $4)
        ON CONFLICT (guild_id, category_id) DO UPDATE SET
            orchestration_profile = EXCLUDED.orchestration_profile,
            updated_at            = NOW(),
            updated_by            = EXCLUDED.updated_by
        """,
        guild_id,
        category_id,
        orchestration_profile,
        updated_by,
    )


# ---------------------------------------------------------------------------
# ai_channel_policy / ai_category_policy
# ---------------------------------------------------------------------------


async def list_channel_policies(guild_id: int) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT guild_id, channel_id, mode, min_level, cooldown_seconds,
               instruction_profile_id, orchestration_profile,
               updated_at, updated_by
        FROM ai_channel_policy
        WHERE guild_id = $1
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def get_channel_policy(guild_id: int, channel_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, channel_id, mode, min_level, cooldown_seconds,
               instruction_profile_id, orchestration_profile,
               updated_at, updated_by
        FROM ai_channel_policy
        WHERE guild_id = $1 AND channel_id = $2
        """,
        guild_id,
        channel_id,
    )
    return dict(row) if row else None


async def upsert_channel_policy(
    guild_id: int,
    channel_id: int,
    *,
    mode: str,
    min_level: int | None,
    cooldown_seconds: int | None,
    instruction_profile_id: int | None,
    updated_by: int | None,
    unchanged_fields: set[str] | None = None,
) -> None:
    """Upsert a channel policy row.

    Fields named in ``unchanged_fields`` are omitted from the
    ``EXCLUDED`` SET on conflict — i.e. preserved from the existing
    row. On the INSERT path (no existing row) the parameter values
    are inserted as-is; for sentinel fields the caller should pass
    ``None``. This is the SQL half of the PR-C-pre ``UNCHANGED``
    sentinel pattern.
    """
    unchanged = unchanged_fields or set()
    set_clauses = [
        ("mode", "mode = EXCLUDED.mode"),
        ("min_level", "min_level = EXCLUDED.min_level"),
        ("cooldown_seconds", "cooldown_seconds = EXCLUDED.cooldown_seconds"),
        (
            "instruction_profile_id",
            "instruction_profile_id = EXCLUDED.instruction_profile_id",
        ),
    ]
    active_sets = [clause for name, clause in set_clauses if name not in unchanged]
    active_sets.append("updated_at = NOW()")
    active_sets.append("updated_by = EXCLUDED.updated_by")
    sql = (
        "INSERT INTO ai_channel_policy ("
        "    guild_id, channel_id, mode, min_level, cooldown_seconds,"
        "    instruction_profile_id, updated_at, updated_by"
        ") VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7) "
        "ON CONFLICT (guild_id, channel_id) DO UPDATE SET " + ", ".join(active_sets)
    )
    await pool.get().execute(
        sql,
        guild_id,
        channel_id,
        mode,
        min_level,
        cooldown_seconds,
        instruction_profile_id,
        updated_by,
    )


async def delete_channel_policy(guild_id: int, channel_id: int) -> int:
    result = await pool.get().execute(
        "DELETE FROM ai_channel_policy WHERE guild_id = $1 AND channel_id = $2",
        guild_id,
        channel_id,
    )
    return int(result.split()[-1]) if result else 0


async def list_category_policies(guild_id: int) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT guild_id, category_id, mode, min_level, cooldown_seconds,
               instruction_profile_id, orchestration_profile,
               updated_at, updated_by
        FROM ai_category_policy
        WHERE guild_id = $1
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def get_category_policy(guild_id: int, category_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT guild_id, category_id, mode, min_level, cooldown_seconds,
               instruction_profile_id, orchestration_profile,
               updated_at, updated_by
        FROM ai_category_policy
        WHERE guild_id = $1 AND category_id = $2
        """,
        guild_id,
        category_id,
    )
    return dict(row) if row else None


async def upsert_category_policy(
    guild_id: int,
    category_id: int,
    *,
    mode: str,
    min_level: int | None,
    cooldown_seconds: int | None,
    instruction_profile_id: int | None,
    updated_by: int | None,
    unchanged_fields: set[str] | None = None,
) -> None:
    """Upsert a category policy row; see :func:`upsert_channel_policy`
    for the ``unchanged_fields`` sentinel semantics.
    """
    unchanged = unchanged_fields or set()
    set_clauses = [
        ("mode", "mode = EXCLUDED.mode"),
        ("min_level", "min_level = EXCLUDED.min_level"),
        ("cooldown_seconds", "cooldown_seconds = EXCLUDED.cooldown_seconds"),
        (
            "instruction_profile_id",
            "instruction_profile_id = EXCLUDED.instruction_profile_id",
        ),
    ]
    active_sets = [clause for name, clause in set_clauses if name not in unchanged]
    active_sets.append("updated_at = NOW()")
    active_sets.append("updated_by = EXCLUDED.updated_by")
    sql = (
        "INSERT INTO ai_category_policy ("
        "    guild_id, category_id, mode, min_level, cooldown_seconds,"
        "    instruction_profile_id, updated_at, updated_by"
        ") VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7) "
        "ON CONFLICT (guild_id, category_id) DO UPDATE SET " + ", ".join(active_sets)
    )
    await pool.get().execute(
        sql,
        guild_id,
        category_id,
        mode,
        min_level,
        cooldown_seconds,
        instruction_profile_id,
        updated_by,
    )


# ---------------------------------------------------------------------------
# ai_role_policy
# ---------------------------------------------------------------------------


async def list_role_policies(guild_id: int) -> list[dict[str, Any]]:
    rows = await pool.get().fetch(
        """
        SELECT guild_id, role_id, decision, min_level_override,
               bypass_cooldown, created_at, updated_at, updated_by
        FROM ai_role_policy
        WHERE guild_id = $1
        """,
        guild_id,
    )
    return [dict(r) for r in rows]


async def upsert_role_policy(
    guild_id: int,
    role_id: int,
    *,
    decision: str,
    min_level_override: int | None,
    bypass_cooldown: bool,
    updated_by: int | None,
    unchanged_fields: set[str] | None = None,
) -> None:
    """Upsert a role policy row; see :func:`upsert_channel_policy`
    for the ``unchanged_fields`` sentinel semantics.
    """
    unchanged = unchanged_fields or set()
    set_clauses = [
        ("decision", "decision = EXCLUDED.decision"),
        (
            "min_level_override",
            "min_level_override = EXCLUDED.min_level_override",
        ),
        ("bypass_cooldown", "bypass_cooldown = EXCLUDED.bypass_cooldown"),
    ]
    active_sets = [clause for name, clause in set_clauses if name not in unchanged]
    active_sets.append("updated_at = NOW()")
    active_sets.append("updated_by = EXCLUDED.updated_by")
    sql = (
        "INSERT INTO ai_role_policy ("
        "    guild_id, role_id, decision, min_level_override, bypass_cooldown,"
        "    created_at, updated_at, updated_by"
        ") VALUES ($1, $2, $3, $4, $5, NOW(), NOW(), $6) "
        "ON CONFLICT (guild_id, role_id) DO UPDATE SET " + ", ".join(active_sets)
    )
    await pool.get().execute(
        sql,
        guild_id,
        role_id,
        decision,
        min_level_override,
        bypass_cooldown,
        updated_by,
    )


# ---------------------------------------------------------------------------
# ai_instruction_profile
# ---------------------------------------------------------------------------


async def get_instruction_profile(profile_id: int) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT id, guild_id, name, body, scope, feature_key, is_preset,
               created_at, created_by, updated_at
        FROM ai_instruction_profile
        WHERE id = $1
        """,
        profile_id,
    )
    return dict(row) if row else None


async def list_instruction_profiles(
    guild_id: int | None,
    *,
    scope: str | None = None,
) -> list[dict[str, Any]]:
    if scope:
        rows = await pool.get().fetch(
            """
            SELECT id, guild_id, name, body, scope, feature_key, is_preset,
                   created_at, created_by, updated_at
            FROM ai_instruction_profile
            WHERE (guild_id = $1 OR (guild_id IS NULL AND $1 IS NULL))
              AND scope = $2
            ORDER BY name
            """,
            guild_id,
            scope,
        )
    else:
        rows = await pool.get().fetch(
            """
            SELECT id, guild_id, name, body, scope, feature_key, is_preset,
                   created_at, created_by, updated_at
            FROM ai_instruction_profile
            WHERE guild_id IS NOT DISTINCT FROM $1
            ORDER BY scope, name
            """,
            guild_id,
        )
    return [dict(r) for r in rows]


async def list_preset_profiles() -> list[dict[str, Any]]:
    """Built-in presets, sorted alphabetically. Returns all rows with
    ``is_preset = TRUE`` (seeded by migration 044).
    """
    rows = await pool.get().fetch(
        """
        SELECT id, guild_id, name, body, scope, feature_key, is_preset,
               created_at, created_by, updated_at
        FROM ai_instruction_profile
        WHERE is_preset = TRUE
        ORDER BY name
        """,
    )
    return [dict(r) for r in rows]


async def upsert_instruction_profile(
    *,
    guild_id: int | None,
    name: str,
    body: str,
    scope: str,
    feature_key: str | None,
    created_by: int | None,
    is_preset: bool = False,
) -> int:
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_instruction_profile (
            guild_id, name, body, scope, feature_key, is_preset,
            created_at, created_by, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), $7, NOW())
        ON CONFLICT (guild_id, scope, name) DO UPDATE SET
            body        = EXCLUDED.body,
            feature_key = EXCLUDED.feature_key,
            is_preset   = EXCLUDED.is_preset,
            updated_at  = NOW()
        RETURNING id
        """,
        guild_id,
        name,
        body,
        scope,
        feature_key,
        is_preset,
        created_by,
    )
    return int(row["id"])


async def delete_instruction_profile(profile_id: int) -> int:
    result = await pool.get().execute(
        "DELETE FROM ai_instruction_profile WHERE id = $1",
        profile_id,
    )
    return int(result.split()[-1]) if result else 0


# ---------------------------------------------------------------------------
# ai_decision_audit
# ---------------------------------------------------------------------------


async def record_decision(
    *,
    guild_id: int,
    channel_id: int,
    category_id: int | None,
    user_id: int,
    message_id: int | None,
    task: str | None,
    route: str | None,
    decision: str,
    reason_code: str,
    policy_snapshot_hash: str | None,
    instruction_profile_ids: list[int] | None,
    provider: str | None,
    model: str | None,
    expires_at: Any | None = None,
) -> int:
    row = await pool.get().fetchrow(
        """
        INSERT INTO ai_decision_audit (
            guild_id, channel_id, category_id, user_id, message_id,
            task, route, decision, reason_code, policy_snapshot_hash,
            instruction_profile_ids, provider, model, created_at, expires_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), $14
        )
        RETURNING id
        """,
        guild_id,
        channel_id,
        category_id,
        user_id,
        message_id,
        task,
        route,
        decision,
        reason_code,
        policy_snapshot_hash,
        instruction_profile_ids,
        provider,
        model,
        expires_at,
    )
    return int(row["id"])


async def query_decisions(
    guild_id: int,
    *,
    channel_id: int | None = None,
    user_id: int | None = None,
    decision: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    sql = (
        "SELECT id, guild_id, channel_id, category_id, user_id, message_id,"
        " task, route, decision, reason_code, policy_snapshot_hash,"
        " instruction_profile_ids, provider, model, created_at "
        "FROM ai_decision_audit WHERE guild_id = $1"
    )
    args: list[Any] = [guild_id]
    if channel_id is not None:
        args.append(channel_id)
        sql += f" AND channel_id = ${len(args)}"
    if user_id is not None:
        args.append(user_id)
        sql += f" AND user_id = ${len(args)}"
    if decision is not None:
        args.append(decision)
        sql += f" AND decision = ${len(args)}"
    args.append(int(limit))
    sql += f" ORDER BY created_at DESC LIMIT ${len(args)}"
    rows = await pool.get().fetch(sql, *args)
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Guild teardown — wired in disbot/guild_lifecycle.py
# ---------------------------------------------------------------------------


async def delete_for_guild(guild_id: int) -> int:
    """Drop every AI-platform row for ``guild_id``.

    Returns the total deleted row count across the AI-platform tables. The
    ``ai_instruction_profile`` rows with ``guild_id IS NULL`` (built-in
    / global profiles) are preserved.
    """
    conn = pool.get()
    total = 0
    for sql in (
        "DELETE FROM ai_decision_audit WHERE guild_id = $1",
        "DELETE FROM ai_review_log WHERE guild_id = $1",
        "DELETE FROM ai_answer_presets WHERE guild_id = $1",
        "DELETE FROM ai_role_policy WHERE guild_id = $1",
        "DELETE FROM ai_category_policy WHERE guild_id = $1",
        "DELETE FROM ai_channel_policy WHERE guild_id = $1",
        "DELETE FROM ai_guild_policy WHERE guild_id = $1",
        "DELETE FROM ai_instruction_profile WHERE guild_id = $1",
    ):
        result = await conn.execute(sql, guild_id)
        if result:
            try:
                total += int(result.split()[-1])
            except (ValueError, IndexError):
                pass
    return total
