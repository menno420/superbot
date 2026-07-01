"""XP service — the single authority for XP awards and level-up events.

Mirrors :mod:`services.economy_service`: the service is the only path
through which production code should grant XP, so every grant goes
through one place that emits the catalogued ``EVT_XP_AWARDED`` and
(when applicable) ``EVT_LEVEL_UP`` events.

Subscribers — panel-refresh, future analytics, possible XP-audit log —
react to these events instead of polling the DB.

Public API
----------
- ``award(guild_id, user_id, amount, *, source, now=None)``
  Atomic XP increment via the existing ``db.add_xp`` upsert + level
  recalculation.  Returns ``XpAward`` (new_xp, new_level, leveled_up).
  Emits ``EVT_XP_AWARDED`` always and ``EVT_LEVEL_UP`` on level boundary
  crossings.

The existing ``db.add_xp`` remains the implementation primitive — the
service wraps it.  ``db.add_xp`` is kept callable directly only for
unit tests and the legacy on_message path in xp_cog; new code should
go through this module.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from core.events import bus
from services.audit_events import emit_audit_action
from utils import db

logger = logging.getLogger("bot.xp_service")

EVT_XP_AWARDED = "xp.awarded"
EVT_LEVEL_UP = "xp.level_up"
EVT_XP_RESET = "xp.reset"


@dataclass(frozen=True)
class XpAward:
    """Result of an XP grant."""

    new_xp: int
    new_level: int
    leveled_up: bool
    delta: int
    source: str


@dataclass(frozen=True)
class XpImport:
    """Result of a single bot-to-bot level import."""

    final_xp: int
    final_level: int
    raised: bool
    source: str


@dataclass(frozen=True)
class UserXPRecord:
    """Typed read-only view of an XP row for permission/level checks."""

    xp: int
    level: int
    messages: int


async def get_user_record(
    guild_id: int,
    user_id: int,
) -> UserXPRecord | None:
    """Return the typed XP record for ``user_id`` in ``guild_id``.

    ``utils.db.xp.get_xp`` synthesises an all-zeros dict when no row
    exists; ``add_xp`` always inserts ``messages=1`` on first grant, so
    ``messages == 0`` distinguishes the synthesised sentinel from any
    real row. Returns ``None`` for that sentinel so callers can branch
    on "no row yet" without inspecting fields.
    """
    row = await db.get_xp(user_id, guild_id)
    messages = int(row.get("messages", 0) or 0)
    xp = int(row.get("xp", 0) or 0)
    level = int(row.get("level", 0) or 0)
    if messages == 0 and xp == 0 and level == 0:
        return None
    return UserXPRecord(xp=xp, level=level, messages=messages)


async def award(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    source: str,
    now: int | None = None,
) -> XpAward:
    """Grant *amount* XP to *user_id* in *guild_id* and emit events.

    Args:
        guild_id: discord guild.
        user_id: target member.
        amount: XP to grant.  Must be > 0.
        source: short label for the grant ("message", "work:carpenter",
            "daily", …).  Surfaces in the event payload and aids
            downstream attribution.
        now: optional Unix timestamp for the cooldown column.  Defaults
            to ``int(time.time())``.

    Returns:
        :class:`XpAward` describing the post-award state.

    Raises:
        ValueError: if ``amount <= 0``.
    """
    if amount <= 0:
        msg = f"award amount must be positive, got {amount}"
        raise ValueError(msg)
    ts = now if now is not None else int(time.time())
    new_xp, new_level, leveled_up = await db.add_xp(user_id, guild_id, amount, ts)

    await bus.emit(
        EVT_XP_AWARDED,
        guild_id=guild_id,
        user_id=user_id,
        delta=amount,
        new_xp=new_xp,
        new_level=new_level,
        source=source,
    )
    if leveled_up:
        await bus.emit(
            EVT_LEVEL_UP,
            guild_id=guild_id,
            user_id=user_id,
            new_level=new_level,
            source=source,
        )

    return XpAward(
        new_xp=new_xp,
        new_level=new_level,
        leveled_up=leveled_up,
        delta=amount,
        source=source,
    )


async def import_level(
    guild_id: int,
    user_id: int,
    level: int,
    *,
    source: str,
    now: int | None = None,
) -> XpImport:
    """Set *user_id*'s XP to the migration target for *level* (raise-only).

    The single seam for bot-to-bot XP migration.  Converts a scraped/exported
    *level* into the concrete XP total that reaches it
    (:func:`db.total_xp_for_level`) and writes it via the raise-only
    ``db.set_imported_xp`` primitive, so an import never lowers a member who
    already earned more here and re-running the same import is idempotent.

    Deliberately emits **no** events: unlike :func:`award` it does not fire
    ``EVT_LEVEL_UP`` (a bulk migration must not spam the level-up announce
    channel), and it skips ``EVT_XP_AWARDED`` because an absolute set has no
    meaningful per-message ``delta``.  The batch caller
    (:mod:`services.xp_migration`) records one summary audit action for the
    whole import and optionally syncs level roles.

    Args:
        guild_id: discord guild.
        user_id: target member.
        level: the level the member reached under the other bot.  Must be >= 0.
        source: short label for the import ("import:arcane", ...).
        now: optional Unix timestamp for the ``last_xp`` column on first
            insert.  Defaults to ``int(time.time())``.

    Returns:
        :class:`XpImport` describing the post-import state.

    Raises:
        ValueError: if ``level < 0``.
    """
    if level < 0:
        msg = f"import level must be >= 0, got {level}"
        raise ValueError(msg)
    ts = now if now is not None else int(time.time())
    target_xp = db.total_xp_for_level(level)
    final_xp, final_level, raised = await db.set_imported_xp(
        user_id,
        guild_id,
        target_xp,
        level,
        ts,
    )
    return XpImport(
        final_xp=final_xp,
        final_level=final_level,
        raised=raised,
        source=source,
    )


async def reset(
    guild_id: int,
    user_id: int,
    *,
    source: str,
    actor_id: int | None = None,
    actor_type: str = "system",
) -> None:
    """Clear all XP for *user_id* in *guild_id* and emit ``EVT_XP_RESET``.

    Args:
        guild_id: discord guild.
        user_id: target member whose XP row is removed.
        source: short label for the reset ("admin:resetxp",
            "admin:modal_reset", ...).  Surfaces in the event payload
            so subscribers can attribute the action.
        actor_id: optional ID of the admin who triggered the reset.
        actor_type: capability-resolver actor token for the shared audit
            event ("admin" for operator-initiated resets, "system" for
            scripted/automated purges).

    Emits ``EVT_XP_RESET`` after the row is deleted so panel-refresh and
    level-role subscribers can react, then publishes the generic
    ``audit.action_recorded`` event via :func:`emit_audit_action` so an
    XP wipe — a sensitive, operator-initiated mutation — reaches the
    shared audit stream that feeds server logging (it previously did
    not).
    """
    await db.delete_xp(user_id, guild_id)
    await bus.emit(
        EVT_XP_RESET,
        guild_id=guild_id,
        user_id=user_id,
        actor_id=actor_id,
        source=source,
    )
    occurred_at = datetime.now(tz=timezone.utc)
    await emit_audit_action(
        mutation_id=f"xp_reset:{guild_id}:{user_id}:{occurred_at.timestamp()}",
        subsystem="xp",
        mutation_type="reset_xp",
        target=f"member:{user_id}",
        scope="guild",
        guild_id=guild_id,
        prev_value=None,
        new_value=None,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=occurred_at,
    )
