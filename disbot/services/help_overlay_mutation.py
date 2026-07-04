"""Audited writes for the guild Help overlay (HLP-3).

Single chokepoint for the ``help_overlay`` table (migration 064). Mirrors
:mod:`services.ai_orchestration_mutation`: authority check → value
validation → DB write → cache invalidation → audit emit → typed result.
Future editors (the audit Phase 5 settings/setup UI) write through here,
never directly.

Contract (audit §9 + owner decisions):

* **Presentation only** (Q-0055/HLP-4): the overlay can hide/rename/
  re-describe entries *in Help*; it never touches command access, routing,
  or governance, and nothing in any admission path reads it.
* **Stable keys validated at write time** against the Help catalogue —
  an unknown hub/subsystem key is rejected (orphans can only *become*
  orphans later, via registry changes; the read side preserves + reports
  them rather than crashing).
* **Store only deviations**: a row whose override fields all become
  ``None`` is deleted, so "no rows" stays the byte-identical default.
* Every write invalidates the per-guild overlay cache and emits
  ``audit.action_recorded`` via :func:`services.audit_events.emit_audit_action`.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("bot.services.help_overlay_mutation")

_SUBSYSTEM = "help"

# Sentinel distinguishing "leave this field as it is" from "reset to inherit
# (None)" in partial edits.
UNSET: Any = object()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class HelpOverlayMutationError(Exception):
    """Base class for rejected Help-overlay writes."""


class UnauthorizedHelpOverlayMutationError(HelpOverlayMutationError):
    """Actor lacked the administrator tier."""


class InvalidHelpOverlayValueError(HelpOverlayMutationError):
    """Entity or field value rejected by the mutation contract."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HelpOverlayMutationResult:
    mutation_id: str
    guild_id: int
    entity_kind: str | None  # None for the full-guild reset
    entity_key: str | None
    prev: dict[str, Any] | None  # override fields before the write
    new: dict[str, Any] | None  # override fields after (None = row removed)
    audit_emitted: bool


# ---------------------------------------------------------------------------
# Authority + value checks
# ---------------------------------------------------------------------------


def _check_admin(actor: Any) -> int | None:
    """Return ``actor.id`` if administrator-tier (or platform owner); raise otherwise."""
    if actor is None:
        raise UnauthorizedHelpOverlayMutationError("actor is required")
    # Platform-owner override: the configured bot owner administers config in any
    # guild, even without Discord admin there (single source: config).
    from config import is_platform_owner

    actor_id = getattr(actor, "id", None)
    if is_platform_owner(actor_id):
        return actor_id
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedHelpOverlayMutationError(
            "help overlay mutations require administrator permission",
        )
    return actor_id


def _check_entity(entity_kind: str, entity_key: str) -> None:
    """Reject unknown kinds/keys — stable keys are validated at write time."""
    from services.help_catalogue import build_help_catalogue
    from services.help_overlay import VALID_ENTITY_KINDS

    if entity_kind not in VALID_ENTITY_KINDS:
        raise InvalidHelpOverlayValueError(
            f"entity_kind must be one of {sorted(VALID_ENTITY_KINDS)}, "
            f"got {entity_kind!r}",
        )
    catalogue = build_help_catalogue()
    known = (
        catalogue.hub(entity_key)
        if entity_kind == "hub"
        else catalogue.subsystem(entity_key)
    )
    if known is None:
        raise InvalidHelpOverlayValueError(
            f"unknown {entity_kind} key {entity_key!r} — overlay rows must "
            "reference a current Help-catalogue entity",
        )


def _check_text(field_name: str, value: str | None, max_len: int) -> str | None:
    """Bound-check an optional text override (``None`` = reset to inherit)."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        raise InvalidHelpOverlayValueError(
            f"{field_name} must be non-empty (use None to reset to default)",
        )
    if len(text) > max_len:
        raise InvalidHelpOverlayValueError(
            f"{field_name} exceeds {max_len} characters ({len(text)})",
        )
    return text


def _fields(row: Any) -> dict[str, Any]:
    return {
        "display_hidden": row.display_hidden,
        "display_name": row.display_name,
        "description": row.description,
    }


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def set_overlay_fields(
    guild_id: int,
    entity_kind: str,
    entity_key: str,
    *,
    actor: Any,
    display_hidden: bool | None = UNSET,
    display_name: str | None = UNSET,
    description: str | None = UNSET,
) -> HelpOverlayMutationResult:
    """Set / reset override fields for one Help entity (partial edit).

    Pass a value to override, ``None`` to reset that field to inherit, or
    omit (``UNSET``) to leave it untouched. A row whose fields all become
    ``None`` is deleted (absence = default).
    """
    from services import help_overlay as read_model
    from services.help_overlay import (
        MAX_DESCRIPTION_LEN,
        MAX_DISPLAY_NAME_LEN,
        HelpOverlayRow,
    )
    from utils.db import help_overlay as db

    actor_id = _check_admin(actor)
    _check_entity(entity_kind, entity_key)
    if display_hidden is not UNSET and display_hidden is not None:
        if not isinstance(display_hidden, bool):
            raise InvalidHelpOverlayValueError("display_hidden must be a bool or None")
    if display_name is not UNSET:
        display_name = _check_text("display_name", display_name, MAX_DISPLAY_NAME_LEN)
    if description is not UNSET:
        description = _check_text("description", description, MAX_DESCRIPTION_LEN)

    current = await db.get_row(guild_id, entity_kind, entity_key)
    prev_row = HelpOverlayRow(
        entity_kind=entity_kind,
        entity_key=entity_key,
        display_hidden=current["display_hidden"] if current else None,
        display_name=current["display_name"] if current else None,
        description=current["description"] if current else None,
    )
    merged = HelpOverlayRow(
        entity_kind=entity_kind,
        entity_key=entity_key,
        display_hidden=(
            prev_row.display_hidden if display_hidden is UNSET else display_hidden
        ),
        display_name=(prev_row.display_name if display_name is UNSET else display_name),
        description=(prev_row.description if description is UNSET else description),
    )

    if merged.is_noop:
        await db.delete_row(guild_id, entity_kind, entity_key)
        new_fields: dict[str, Any] | None = None
    else:
        await db.upsert_row(
            guild_id,
            entity_kind,
            entity_key,
            display_hidden=merged.display_hidden,
            display_name=merged.display_name,
            description=merged.description,
            updated_by=actor_id,
        )
        new_fields = _fields(merged)

    read_model.invalidate_help_overlay_cache(guild_id)
    mutation_id = uuid.uuid4().hex
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        guild_id=guild_id,
        target=f"{entity_kind}:{entity_key}",
        prev_value=repr(_fields(prev_row)) if current else None,
        new_value=repr(new_fields) if new_fields is not None else None,
        actor_id=actor_id,
    )
    return HelpOverlayMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        entity_kind=entity_kind,
        entity_key=entity_key,
        prev=_fields(prev_row) if current else None,
        new=new_fields,
        audit_emitted=audit_emitted,
    )


async def set_home_message(
    guild_id: int,
    *,
    actor: Any,
    title: str | None = UNSET,
    body: str | None = UNSET,
    color: int | None = UNSET,
) -> HelpOverlayMutationResult:
    """Set / reset the Q-0059 Help-Home message (partial edit).

    Same contract as :func:`set_overlay_fields`: pass a value to
    override, ``None`` to reset that field to the default, or omit
    (``UNSET``) to leave it untouched. A row whose fields all become
    ``None`` is deleted — absence renders the byte-identical default
    Home. Bounds are enforced here (migration 067's CHECKs are the
    backstop): title ≤ 256, body ≤ 2000, color in Discord's 24-bit space.
    """
    from services import help_overlay as read_model
    from services.help_overlay import (
        MAX_HOME_BODY_LEN,
        MAX_HOME_COLOR,
        MAX_HOME_TITLE_LEN,
        HomeMessage,
    )
    from utils.db import help_overlay as db

    actor_id = _check_admin(actor)
    if title is not UNSET:
        title = _check_text("home_title", title, MAX_HOME_TITLE_LEN)
    if body is not UNSET:
        body = _check_text("home_body", body, MAX_HOME_BODY_LEN)
    if color is not UNSET and color is not None:
        if not isinstance(color, int) or isinstance(color, bool):
            raise InvalidHelpOverlayValueError("home_color must be an int or None")
        if not 0 <= color <= MAX_HOME_COLOR:
            raise InvalidHelpOverlayValueError(
                f"home_color must be within 0..{MAX_HOME_COLOR:#x}, got {color:#x}",
            )

    current = await db.get_home_row(guild_id)
    prev = HomeMessage(
        title=current["home_title"] if current else None,
        body=current["home_body"] if current else None,
        color=current["home_color"] if current else None,
    )
    merged = HomeMessage(
        title=prev.title if title is UNSET else title,
        body=prev.body if body is UNSET else body,
        color=prev.color if color is UNSET else color,
    )

    def _as_fields(msg: HomeMessage) -> dict[str, Any]:
        return {"title": msg.title, "body": msg.body, "color": msg.color}

    if merged.is_noop:
        await db.delete_home_row(guild_id)
        new_fields: dict[str, Any] | None = None
    else:
        await db.upsert_home_row(
            guild_id,
            home_title=merged.title,
            home_body=merged.body,
            home_color=merged.color,
            updated_by=actor_id,
        )
        new_fields = _as_fields(merged)

    read_model.invalidate_help_overlay_cache(guild_id)
    mutation_id = uuid.uuid4().hex
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        guild_id=guild_id,
        target="home:home",
        prev_value=repr(_as_fields(prev)) if current else None,
        new_value=repr(new_fields) if new_fields is not None else None,
        actor_id=actor_id,
    )
    return HelpOverlayMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        entity_kind="home",
        entity_key="home",
        prev=_as_fields(prev) if current else None,
        new=new_fields,
        audit_emitted=audit_emitted,
    )


async def reset_guild_overlay(
    guild_id: int,
    *,
    actor: Any,
) -> HelpOverlayMutationResult:
    """Full reset: delete every overlay row for the guild (audited)."""
    from services import help_overlay as read_model
    from utils.db import help_overlay as db

    actor_id = _check_admin(actor)
    removed = await db.delete_guild_rows(guild_id)
    read_model.invalidate_help_overlay_cache(guild_id)
    mutation_id = uuid.uuid4().hex
    audit_emitted = await _emit_audit(
        mutation_id=mutation_id,
        guild_id=guild_id,
        target="guild:*",
        prev_value=f"{removed} override row(s)",
        new_value=None,
        actor_id=actor_id,
    )
    return HelpOverlayMutationResult(
        mutation_id=mutation_id,
        guild_id=guild_id,
        entity_kind=None,
        entity_key=None,
        prev={"rows_removed": removed},
        new=None,
        audit_emitted=audit_emitted,
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


async def _emit_audit(
    *,
    mutation_id: str,
    guild_id: int,
    target: str,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
) -> bool:
    """Best-effort ``audit.action_recorded`` emit; never breaks the write."""
    try:
        from services.audit_events import emit_audit_action

        return await emit_audit_action(
            mutation_id=mutation_id,
            subsystem=_SUBSYSTEM,
            mutation_type="help_overlay_update",
            target=target,
            scope="guild",
            guild_id=guild_id,
            prev_value=prev_value,
            new_value=new_value,
            actor_id=actor_id,
            actor_type="user",
            occurred_at=datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001 — audit must not drag the write down
        logger.warning("help_overlay_mutation: audit emit failed: %s", exc)
        return False


__all__ = [
    "UNSET",
    "HelpOverlayMutationError",
    "HelpOverlayMutationResult",
    "InvalidHelpOverlayValueError",
    "UnauthorizedHelpOverlayMutationError",
    "reset_guild_overlay",
    "set_home_message",
    "set_overlay_fields",
]
