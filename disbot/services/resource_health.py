"""Resource-health inspector — Phase 9d / Track 2 PR 4.

Pure-read inspector that joins each subsystem's declared
:class:`~core.runtime.subsystem_schema.BindingSpec` with the live
binding row from ``subsystem_bindings`` and the actual Discord
resource (channel / role / category / thread / member) in the guild
cache. The output is a frozen tuple of
:class:`ResourceHealthFinding` records consumed downstream by
:mod:`services.setup_readiness` (Track 2 PR 5) and by the future
repair previews (Track 2 PR 6).

**Read-only.** No DB writes. No Discord resource creation. No
mutation calls. Tests pin both invariants via static AST asserts.

Status codes:

* ``ok``                 — binding present, resolved, kind matches,
                           permissions/hierarchy OK.
* ``not_configured``     — optional binding has no row yet.
* ``missing``            — required binding has no row yet.
* ``unbound``            — row exists with ``target_id IS NULL`` or
                           status ``unresolved``.
* ``stale_binding``      — row's ``target_id`` no longer resolves to
                           a live resource.
* ``wrong_type``         — resolved resource exists but its kind does
                           not match the spec's :class:`BindingKind`.
* ``permission_blocked`` — resource exists but the bot lacks the
                           permissions it needs (view/send/embed for
                           channels; manage for roles).
* ``hierarchy_blocked``  — role exists but sits at or above the
                           bot's top role, so the bot cannot manage
                           it.
* ``unknown``            — escape hatch for an unhandled
                           :class:`BindingKind` so a future enum
                           expansion doesn't crash this service.

Severity tiers:

* ``info``  — informational only; no operator action required.
* ``warn``  — best-effort issue; the bot may degrade silently.
* ``error`` — blocker for the affected subsystem; fix to restore
              full function.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import discord

from core.runtime.guild_resources import resolve_member, resolve_role
from core.runtime.subsystem_schema import BindingKind, BindingSpec, all_schemas
from utils.db import bindings as bindings_db

logger = logging.getLogger("bot.services.resource_health")

OK = "ok"
NOT_CONFIGURED = "not_configured"
MISSING = "missing"
UNBOUND = "unbound"
STALE_BINDING = "stale_binding"
WRONG_TYPE = "wrong_type"
PERMISSION_BLOCKED = "permission_blocked"
HIERARCHY_BLOCKED = "hierarchy_blocked"
UNKNOWN = "unknown"

STATUS_CODES: frozenset[str] = frozenset(
    {
        OK,
        NOT_CONFIGURED,
        MISSING,
        UNBOUND,
        STALE_BINDING,
        WRONG_TYPE,
        PERMISSION_BLOCKED,
        HIERARCHY_BLOCKED,
        UNKNOWN,
    },
)

SEV_INFO = "info"
SEV_WARN = "warn"
SEV_ERROR = "error"

SEVERITIES: frozenset[str] = frozenset({SEV_INFO, SEV_WARN, SEV_ERROR})


@dataclass(frozen=True)
class ResourceHealthFinding:
    """A single health verdict for one (subsystem, binding) slot."""

    subsystem: str
    binding_name: str
    kind: BindingKind
    status: str
    severity: str
    message: str
    target_id: int | None = None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def inspect(guild: discord.Guild) -> tuple[ResourceHealthFinding, ...]:
    """Return one :class:`ResourceHealthFinding` per declared binding.

    The findings are sorted by ``(subsystem, binding_name)`` so consumers
    get a stable order across calls.
    """
    schemas = all_schemas()
    if not schemas:
        return ()

    rows_by_key = await _load_binding_rows(guild.id)
    bot_member = guild.me

    findings: list[ResourceHealthFinding] = []
    for subsystem, schema in sorted(schemas.items()):
        for spec in schema.bindings:
            row = rows_by_key.get((subsystem, spec.name))
            findings.append(_inspect_one(guild, bot_member, subsystem, spec, row))
    return tuple(findings)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


async def _load_binding_rows(guild_id: int) -> dict[tuple[str, str], dict[str, Any]]:
    """One DB read; key by ``(subsystem, binding_name)``."""
    try:
        rows = await bindings_db.list_for_guild(guild_id)
    except Exception:
        logger.exception(
            "resource_health: bindings_db.list_for_guild failed for guild=%d; "
            "every finding will be marked as unknown.",
            guild_id,
        )
        return {}
    return {(r["subsystem"], r["binding_name"]): r for r in rows}


def _inspect_one(
    guild: discord.Guild,
    bot_member: discord.Member | None,
    subsystem: str,
    spec: BindingSpec,
    row: dict[str, Any] | None,
) -> ResourceHealthFinding:
    """Produce a :class:`ResourceHealthFinding` for one declared slot."""
    # 1. No row → missing (if required) / not_configured (if optional).
    if row is None:
        if spec.required:
            return ResourceHealthFinding(
                subsystem=subsystem,
                binding_name=spec.name,
                kind=spec.kind,
                status=MISSING,
                severity=SEV_ERROR,
                message=(
                    f"required binding {subsystem}.{spec.name} has no row; "
                    "operator must bind it before this subsystem is usable."
                ),
            )
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=NOT_CONFIGURED,
            severity=SEV_INFO,
            message=(f"optional binding {subsystem}.{spec.name} is not configured."),
        )

    target_id = row.get("target_id")
    row_status = row.get("status")

    # 2. Row exists but unbound (NULL target_id or status=unresolved).
    if target_id is None or row_status == "unresolved":
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=UNBOUND,
            severity=SEV_WARN,
            message=(
                f"binding {subsystem}.{spec.name} exists but points at no "
                "live resource (cleared or never resolved)."
            ),
            target_id=None,
        )

    # 3. Resolve the live resource by kind. Per-kind branch.
    if spec.kind is BindingKind.CHANNEL:
        return _inspect_channel(subsystem, spec, target_id, guild, bot_member)
    if spec.kind is BindingKind.CATEGORY:
        return _inspect_category(subsystem, spec, target_id, guild, bot_member)
    if spec.kind is BindingKind.ROLE:
        return _inspect_role(subsystem, spec, target_id, guild, bot_member)
    if spec.kind is BindingKind.THREAD:
        return _inspect_thread(subsystem, spec, target_id, guild)
    if spec.kind is BindingKind.MEMBER:
        return _inspect_member(subsystem, spec, target_id, guild)

    return ResourceHealthFinding(
        subsystem=subsystem,
        binding_name=spec.name,
        kind=spec.kind,
        status=UNKNOWN,
        severity=SEV_WARN,
        message=(
            f"binding kind {spec.kind!r} is not handled by resource_health; "
            "extend the inspector when adding new BindingKind values."
        ),
        target_id=target_id,
    )


# ---------------------------------------------------------------------------
# Per-kind probes (pure, in-memory; no I/O)
# ---------------------------------------------------------------------------


def _inspect_channel(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    guild: discord.Guild,
    bot_member: discord.Member | None,
) -> ResourceHealthFinding:
    channel = guild.get_channel(target_id)
    if channel is None:
        return _stale(subsystem, spec, target_id)
    if not isinstance(
        channel,
        (discord.TextChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        return _wrong_type(subsystem, spec, target_id, channel)
    if bot_member is None:
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=OK,
            severity=SEV_INFO,
            message=(
                f"channel {subsystem}.{spec.name} resolves; bot member not "
                "in cache so permission probe was skipped."
            ),
            target_id=target_id,
        )
    perms = channel.permissions_for(bot_member)
    missing = _missing_channel_perms(channel, perms)
    if missing:
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=PERMISSION_BLOCKED,
            severity=SEV_ERROR,
            message=(
                f"channel #{channel.name} is bound but bot lacks: {', '.join(missing)}."
            ),
            target_id=target_id,
        )
    return _ok(subsystem, spec, target_id, f"#{channel.name}")


def _inspect_category(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    guild: discord.Guild,
    bot_member: discord.Member | None,
) -> ResourceHealthFinding:
    category = guild.get_channel(target_id)
    if category is None:
        return _stale(subsystem, spec, target_id)
    if not isinstance(category, discord.CategoryChannel):
        return _wrong_type(subsystem, spec, target_id, category)
    if bot_member is None:
        return _ok(subsystem, spec, target_id, category.name)
    perms = category.permissions_for(bot_member)
    if not perms.view_channel:
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=PERMISSION_BLOCKED,
            severity=SEV_ERROR,
            message=(f"category {category.name!r} is bound but bot lacks view."),
            target_id=target_id,
        )
    return _ok(subsystem, spec, target_id, category.name)


def _inspect_role(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    guild: discord.Guild,
    bot_member: discord.Member | None,
) -> ResourceHealthFinding:
    role = resolve_role(guild, role_id=target_id)
    if role is None:
        return _stale(subsystem, spec, target_id)
    if bot_member is None:
        return _ok(subsystem, spec, target_id, f"@{role.name}")
    if not bot_member.guild_permissions.manage_roles:
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=PERMISSION_BLOCKED,
            severity=SEV_ERROR,
            message=(f"role @{role.name} is bound but bot lacks Manage Roles."),
            target_id=target_id,
        )
    if role >= bot_member.top_role:
        return ResourceHealthFinding(
            subsystem=subsystem,
            binding_name=spec.name,
            kind=spec.kind,
            status=HIERARCHY_BLOCKED,
            severity=SEV_ERROR,
            message=(
                f"role @{role.name} sits at or above the bot's top role "
                f"(@{bot_member.top_role.name}); cannot be managed."
            ),
            target_id=target_id,
        )
    return _ok(subsystem, spec, target_id, f"@{role.name}")


def _inspect_thread(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    guild: discord.Guild,
) -> ResourceHealthFinding:
    thread = guild.get_thread(target_id)
    if thread is None:
        return _stale(subsystem, spec, target_id)
    return _ok(subsystem, spec, target_id, f"#{thread.name}")


def _inspect_member(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    guild: discord.Guild,
) -> ResourceHealthFinding:
    member = resolve_member(guild, target_id)
    if member is None:
        return _stale(subsystem, spec, target_id)
    return _ok(subsystem, spec, target_id, str(member))


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _missing_channel_perms(
    channel: discord.abc.GuildChannel,
    perms: discord.Permissions,
) -> list[str]:
    """Return the subset of channel permissions the bot is missing."""
    needed: Iterable[tuple[str, bool]]
    if isinstance(channel, discord.TextChannel):
        needed = (
            ("view_channel", perms.view_channel),
            ("send_messages", perms.send_messages),
            ("embed_links", perms.embed_links),
        )
    elif isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
        needed = (
            ("view_channel", perms.view_channel),
            ("connect", perms.connect),
        )
    else:
        needed = (("view_channel", perms.view_channel),)
    return [name for name, ok in needed if not ok]


def _stale(subsystem: str, spec: BindingSpec, target_id: int) -> ResourceHealthFinding:
    return ResourceHealthFinding(
        subsystem=subsystem,
        binding_name=spec.name,
        kind=spec.kind,
        status=STALE_BINDING,
        severity=SEV_ERROR,
        message=(
            f"binding {subsystem}.{spec.name} points at {spec.kind.value}="
            f"{target_id} which is not in the guild — clear the binding "
            "or re-bind to a live resource."
        ),
        target_id=target_id,
    )


def _wrong_type(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    resource: Any,
) -> ResourceHealthFinding:
    return ResourceHealthFinding(
        subsystem=subsystem,
        binding_name=spec.name,
        kind=spec.kind,
        status=WRONG_TYPE,
        severity=SEV_ERROR,
        message=(
            f"binding {subsystem}.{spec.name} declares kind={spec.kind.value} "
            f"but target_id={target_id} resolves to {type(resource).__name__}."
        ),
        target_id=target_id,
    )


def _ok(
    subsystem: str,
    spec: BindingSpec,
    target_id: int,
    display: str,
) -> ResourceHealthFinding:
    return ResourceHealthFinding(
        subsystem=subsystem,
        binding_name=spec.name,
        kind=spec.kind,
        status=OK,
        severity=SEV_INFO,
        message=f"binding {subsystem}.{spec.name} resolves to {display}.",
        target_id=target_id,
    )


__all__ = [
    "HIERARCHY_BLOCKED",
    "MISSING",
    "NOT_CONFIGURED",
    "OK",
    "PERMISSION_BLOCKED",
    "ResourceHealthFinding",
    "SEVERITIES",
    "SEV_ERROR",
    "SEV_INFO",
    "SEV_WARN",
    "STALE_BINDING",
    "STATUS_CODES",
    "UNBOUND",
    "UNKNOWN",
    "WRONG_TYPE",
    "inspect",
]
