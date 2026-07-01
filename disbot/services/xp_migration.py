"""Bot-to-bot XP migration — batch import orchestration.

Turns a resolved batch of ``(user_id, level)`` records — scraped from another
bot's level-up channel (``utils.xp_migration``) or, in future, pulled from a
direct provider API — into the guild's chat XP, then records the migration and
optionally grants the level roles.

Layering:

* the raise-only per-member write is ``services.xp_service.import_level`` (the
  INV-G seam — XP is never written outside ``xp_service``);
* level roles are planned by the shared ``services.xp_role_sync`` planner (the
  same one the live level-up path uses) and applied through the audited
  ``services.role_automation`` seam;
* the whole import records **one** ``audit.action_recorded`` summary action.

Deliberately quiet: no per-member level-up announcement is posted (a bulk
migration would otherwise flood the announce channel).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import discord

from core.runtime import resources
from services import (
    role_automation,
    role_exemption_service,
    xp_role_sync,
    xp_service,
)
from services.audit_events import emit_audit_action
from utils import xp_migration as xpm
from utils.guild_config_accessors import get_xp_threshold_roles
from utils.xp_migration import ScanPlan

logger = logging.getLogger("bot.xp_migration")

# How many members to preview in a ScanPlan sample.
_SCAN_SAMPLE_LIMIT = 10


async def scan_channel(
    guild: Any,
    channel: Any,
    fmt: xpm.AnnouncerFormat,
    limit: int | None = None,
) -> ScanPlan | None:
    """Read ``channel`` history and build a :class:`ScanPlan` for ``fmt``.

    The shared scan behind both the ``!xpimport`` command and the import
    button.  Only messages authored by a **bot/webhook** are parsed (the
    announcer), so member chatter in the channel can't be mistaken for a
    level-up.  Mentions resolve exactly; a plain-text name is matched against
    the current roster and otherwise recorded as unresolved.  Keeps the
    highest level seen per member.  Returns ``None`` when the channel's
    history is unreadable (the bot lacks Read Message History).
    """
    scanned = 0
    matched = 0
    records: list[tuple[int, int]] = []
    unresolved: dict[str, int] = {}
    try:
        async for msg in channel.history(limit=limit):
            scanned += 1
            if not (msg.author.bot or msg.webhook_id):
                continue
            parsed = xpm.parse_level_message(
                msg.content,
                [u.id for u in msg.mentions],
                fmt=fmt,
            )
            if parsed is None:
                continue
            matched += 1
            if parsed.user_id is not None:
                records.append((parsed.user_id, parsed.level))
            elif parsed.name:
                member = resources.resolve_member_by_name(guild, parsed.name)
                if member is not None:
                    records.append((member.id, parsed.level))
                else:
                    unresolved[parsed.name] = max(
                        unresolved.get(parsed.name, -1),
                        parsed.level,
                    )
    except discord.Forbidden:
        return None

    reduced = xpm.reduce_max_levels(records)
    top = sorted(reduced.items(), key=lambda kv: kv[1], reverse=True)
    sample: list[tuple[str, int]] = []
    for uid, level in top[:_SCAN_SAMPLE_LIMIT]:
        member = resources.resolve_member(guild, uid)
        sample.append((member.display_name if member else f"user {uid}", level))

    return ScanPlan(
        source_key=fmt.key,
        source_label=fmt.label,
        channel_id=channel.id,
        scanned_messages=scanned,
        matched=matched,
        records=tuple(reduced.items()),
        sample=tuple(sample),
        unresolved_names=tuple(sorted(unresolved)),
    )


@dataclass(frozen=True)
class ImportSummary:
    """Aggregate outcome of an :func:`import_levels` batch."""

    total: int
    raised: int
    unchanged: int
    roles_attempted: int
    roles_succeeded: int
    roles_failed: int


async def import_levels(
    guild: Any,
    records: Sequence[tuple[int, int]],
    *,
    source: str,
    actor_id: int | None = None,
    apply_roles: bool = False,
) -> ImportSummary:
    """Import ``(user_id, level)`` *records* into ``guild``'s chat XP.

    Each record is written **raise-only** through
    :func:`services.xp_service.import_level` — an import never lowers a member
    who already earned more here, and re-running the same batch is idempotent.

    When ``apply_roles`` is True, every imported member still present in the
    guild is also granted the level roles they qualify for (shared planner +
    one batched :func:`services.role_automation.apply`); absent members are
    skipped silently (they get their roles on rejoin via the live path).

    Records one summary ``audit.action_recorded`` for the whole import.
    Returns an :class:`ImportSummary`.
    """
    guild_id = int(guild.id)

    raised = 0
    for user_id, level in records:
        outcome = await xp_service.import_level(
            guild_id=guild_id,
            user_id=int(user_id),
            level=int(level),
            source=source,
        )
        if outcome.raised:
            raised += 1
    total = len(records)
    unchanged = total - raised

    roles_attempted = roles_succeeded = roles_failed = 0
    if apply_roles and records:
        roles_attempted, roles_succeeded, roles_failed = await _sync_level_roles(
            guild,
            records,
            source,
        )

    occurred_at = datetime.now(tz=timezone.utc)
    await emit_audit_action(
        mutation_id=f"xp_import:{guild_id}:{occurred_at.timestamp()}",
        subsystem="xp",
        mutation_type="import_levels",
        target=f"guild:{guild_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=(
            f"source={source} total={total} raised={raised} "
            f"roles_succeeded={roles_succeeded}"
        ),
        actor_id=actor_id,
        actor_type="admin" if actor_id is not None else "system",
        occurred_at=occurred_at,
    )

    logger.info(
        "xp_migration.import_levels: guild=%d source=%s total=%d raised=%d "
        "roles(succeeded=%d failed=%d)",
        guild_id,
        source,
        total,
        raised,
        roles_succeeded,
        roles_failed,
    )

    return ImportSummary(
        total=total,
        raised=raised,
        unchanged=unchanged,
        roles_attempted=roles_attempted,
        roles_succeeded=roles_succeeded,
        roles_failed=roles_failed,
    )


async def _sync_level_roles(
    guild: Any,
    records: Sequence[tuple[int, int]],
    source: str,
) -> tuple[int, int, int]:
    """Grant imported members their level roles in one batched apply.

    Reads the guild's threshold list / stack flag / exempt set **once**, plans
    every present member off it (the shared planner), then a single
    :func:`services.role_automation.apply`.  Returns
    ``(attempted, succeeded, failed)``.
    """
    xp_roles = await get_xp_threshold_roles(guild.id)
    if not xp_roles:
        return 0, 0, 0
    exempt = await role_exemption_service.get_exempt_role_ids(guild.id)
    stack = await role_exemption_service.xp_roles_stack(guild.id)

    members_by_id = {m.id: m for m in (getattr(guild, "members", ()) or ())}
    assignments: list = []
    for user_id, level in records:
        member = members_by_id.get(int(user_id))
        if member is None:
            continue  # not in the guild — gets roles on the live path if they rejoin
        assignments.extend(
            xp_role_sync.plan_level_role_assignments(
                guild,
                member,
                int(level),
                stack=stack,
                exempt_xp_ids=exempt.xp,
                xp_roles=xp_roles,
                reason=f"XP migration ({source}): reached level {level}",
            ),
        )
    if not assignments:
        return 0, 0, 0

    result = await role_automation.apply(guild, assignments, actor_type="system")
    return result.attempted, result.succeeded, result.failed
