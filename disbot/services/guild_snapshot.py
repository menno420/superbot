"""Guild metadata snapshot — Phase 9f / Track 5 PR 11.

Collects an opt-in, privacy-vetted view of a guild's structure that
both the deterministic and AI advisors consume. The snapshot is a
frozen dataclass with explicit fields — no ``**extra``, no
``__dict__`` shoveling — so a future schema change is a code change,
not an accidental data exposure.

Privacy contract
----------------
**Included by default** (anything operator-visible in the Discord UI):

* Guild id + name + owner id.
* Channel + category + role metadata: id, name, type, position,
  topic (channels only), parent category, manageable flag.
* Per-channel bot-permission summary (a compact view-only string —
  no member-by-member ACL matrix).
* The bot's existing settings + bindings snapshots (already in
  service catalogues).
* The output of :func:`services.resource_health.inspect` so the
  advisor can ground recommendations against actual health.

**Excluded by default** (operator can later opt in per
``setup.snapshot_scope = "extended"``, but Track 5 ships OFF):

* Message content.
* Member list / member count per channel.
* Invites.
* Per-channel permission-overwrite matrix (the raw bitmask grid).

Tests pin both lists via the documented field-name conventions: a
test enumerates ``dataclasses.asdict(snapshot)`` and rejects any
key that smells like a member, invite, message, or overwrite
field.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any

from services.resource_health import (
    ResourceHealthFinding,
)
from services.resource_health import inspect as inspect_resource_health

if TYPE_CHECKING:
    import discord

logger = logging.getLogger("bot.services.guild_snapshot")


@dataclass(frozen=True)
class ChannelMeta:
    """View-only channel metadata."""

    id: int
    name: str
    type: str
    topic: str | None
    parent_category: str | None
    position: int
    bot_can_view: bool
    bot_can_send: bool
    bot_can_embed: bool


@dataclass(frozen=True)
class CategoryMeta:
    """View-only category metadata."""

    id: int
    name: str
    position: int
    bot_can_manage: bool


@dataclass(frozen=True)
class RoleMeta:
    """View-only role metadata."""

    id: int
    name: str
    position: int
    bot_can_manage: bool


@dataclass(frozen=True)
class GuildSnapshot:
    """Metadata-only snapshot of a guild's structure.

    All fields are documented; the field set is closed (no dynamic
    attributes) so a future privacy widening is a deliberate edit,
    not an accident.
    """

    guild_id: int
    guild_name: str
    owner_id: int
    channels: tuple[ChannelMeta, ...] = ()
    categories: tuple[CategoryMeta, ...] = ()
    roles: tuple[RoleMeta, ...] = ()
    settings_snapshot: dict[str, Any] = field(default_factory=dict)
    bindings_snapshot: dict[str, Any] = field(default_factory=dict)
    readiness_findings: tuple[ResourceHealthFinding, ...] = ()


# Documented "should never appear in a snapshot" field-name tokens.
# Tests assert these against the keys of ``dataclasses.asdict(snapshot)``.
EXCLUDED_FIELD_TOKENS: frozenset[str] = frozenset(
    {
        "message_content",
        "messages",
        "members",
        "member_count",
        "member_list",
        "invites",
        "permission_overwrites",
        "overwrites_matrix",
        "raw_permissions",
    },
)


# ---------------------------------------------------------------------------
# Collect
# ---------------------------------------------------------------------------


async def collect(guild: discord.Guild) -> GuildSnapshot:
    """Build the snapshot for ``guild``.

    Pure read; no DB writes, no Discord create calls. The
    readiness inspection may raise (DB down, etc.); failure is
    swallowed and ``readiness_findings`` is left empty so the
    advisor still has something to work with.
    """
    me = guild.me

    channels = _collect_channels(guild, me)
    categories = _collect_categories(guild, me)
    roles = _collect_roles(guild, me)
    settings_snapshot = _collect_settings_snapshot()
    bindings_snapshot = _collect_bindings_snapshot()

    findings: tuple[ResourceHealthFinding, ...] = ()
    try:
        findings = await inspect_resource_health(guild)
    except Exception:
        logger.exception(
            "guild_snapshot.collect: resource_health.inspect failed for "
            "guild=%d; snapshot continues with empty readiness_findings.",
            guild.id,
        )

    return GuildSnapshot(
        guild_id=guild.id,
        guild_name=guild.name,
        owner_id=guild.owner_id or 0,
        channels=channels,
        categories=categories,
        roles=roles,
        settings_snapshot=settings_snapshot,
        bindings_snapshot=bindings_snapshot,
        readiness_findings=findings,
    )


# ---------------------------------------------------------------------------
# Per-collection helpers
# ---------------------------------------------------------------------------


def _collect_channels(guild: Any, me: Any) -> tuple[ChannelMeta, ...]:
    import discord  # local — keep the module importable without discord

    out: list[ChannelMeta] = []
    text_channels = list(getattr(guild, "text_channels", ()) or ())
    voice_channels = list(getattr(guild, "voice_channels", ()) or ())
    stage_channels = list(getattr(guild, "stage_channels", ()) or ())

    def _add_text_like(channels, kind_label):
        for ch in channels:
            perms = ch.permissions_for(me) if me is not None else None
            parent = getattr(ch, "category", None)
            out.append(
                ChannelMeta(
                    id=ch.id,
                    name=ch.name,
                    type=kind_label,
                    topic=getattr(ch, "topic", None),
                    parent_category=parent.name if parent is not None else None,
                    position=getattr(ch, "position", 0),
                    bot_can_view=(
                        bool(getattr(perms, "view_channel", False))
                        if perms is not None
                        else False
                    ),
                    bot_can_send=(
                        bool(getattr(perms, "send_messages", False))
                        if perms is not None
                        else False
                    ),
                    bot_can_embed=(
                        bool(getattr(perms, "embed_links", False))
                        if perms is not None
                        else False
                    ),
                ),
            )

    _add_text_like(text_channels, "text")
    _add_text_like(voice_channels, "voice")
    _add_text_like(stage_channels, "stage")

    del discord  # keep mypy happy without an unused-import warning
    return tuple(out)


def _collect_categories(guild: Any, me: Any) -> tuple[CategoryMeta, ...]:
    out: list[CategoryMeta] = []
    for cat in getattr(guild, "categories", ()) or ():
        perms = cat.permissions_for(me) if me is not None else None
        out.append(
            CategoryMeta(
                id=cat.id,
                name=cat.name,
                position=getattr(cat, "position", 0),
                bot_can_manage=(
                    bool(getattr(perms, "manage_channels", False))
                    if perms is not None
                    else False
                ),
            ),
        )
    return tuple(out)


def _collect_roles(guild: Any, me: Any) -> tuple[RoleMeta, ...]:
    out: list[RoleMeta] = []
    bot_top_position = (
        getattr(getattr(me, "top_role", None), "position", 0) if me is not None else 0
    )
    bot_can_manage_roles = (
        bool(getattr(getattr(me, "guild_permissions", None), "manage_roles", False))
        if me is not None
        else False
    )
    for role in getattr(guild, "roles", ()) or ():
        position = getattr(role, "position", 0)
        manageable = bool(
            bot_can_manage_roles and position < bot_top_position,
        )
        out.append(
            RoleMeta(
                id=role.id,
                name=role.name,
                position=position,
                bot_can_manage=manageable,
            ),
        )
    return tuple(out)


def _collect_settings_snapshot() -> dict[str, Any]:
    """Return a flat ``{subsystem.name: default_value}`` snapshot.

    Uses :func:`core.runtime.subsystem_schema.all_schemas` so the
    advisor knows what settings exist without us shipping a
    parallel catalogue. Defaults only — per-guild values are not
    surfaced through the snapshot to keep it metadata-only.
    """
    try:
        from core.runtime.subsystem_schema import all_schemas
    except Exception:
        logger.exception(
            "guild_snapshot: subsystem_schema unavailable; settings_snapshot empty.",
        )
        return {}
    out: dict[str, Any] = {}
    for subsystem, schema in (all_schemas() or {}).items():
        for spec in schema.settings:
            out[f"{subsystem}.{spec.name}"] = spec.default
    return out


def _collect_bindings_snapshot() -> dict[str, Any]:
    """Return a flat ``{subsystem.name: {kind, required, hint}}`` snapshot.

    Names + kinds only — binding TARGETS (channel/role ids) are out
    of scope for the snapshot; the per-guild target state lives in
    the readiness findings.
    """
    try:
        from core.runtime.subsystem_schema import all_schemas
    except Exception:
        logger.exception(
            "guild_snapshot: subsystem_schema unavailable; bindings_snapshot empty.",
        )
        return {}
    out: dict[str, Any] = {}
    for subsystem, schema in (all_schemas() or {}).items():
        for binding in schema.bindings:
            out[f"{subsystem}.{binding.name}"] = {
                "kind": binding.kind.value,
                "required": binding.required,
                "hint": binding.hint,
            }
    return out


# ---------------------------------------------------------------------------
# Static introspection helper used by tests
# ---------------------------------------------------------------------------


def documented_field_names() -> tuple[str, ...]:
    """Return every field name declared on :class:`GuildSnapshot`.

    Tests pin the set so adding a new field requires updating the
    privacy test list at the same time.
    """
    return tuple(f.name for f in fields(GuildSnapshot))


__all__ = [
    "EXCLUDED_FIELD_TOKENS",
    "CategoryMeta",
    "ChannelMeta",
    "GuildSnapshot",
    "RoleMeta",
    "collect",
    "documented_field_names",
]
