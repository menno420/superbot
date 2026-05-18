"""Typed guild-resource snapshots.

A :class:`GuildResource` is an *immutable* snapshot of a Discord
primitive at the moment of resolution — its id, name, the kind of
resource it is, and the resource-specific metadata the platform cares
about.  The discord.py guild object remains the source of truth for
live state; these snapshots exist so:

* Diagnostics + audit logs reference resources without retaining a
  live discord.py handle (which would prevent garbage collection of
  stale guild state).
* Phase 4c can compare two snapshots ("the announce channel changed
  category") without re-querying Discord.
* Phase 7's wizard previews can render resources before commit
  without re-resolving on every render.

Snapshots are produced by the discovery layer (:mod:`core.resources.discovery`);
the dataclasses themselves do not import discord.py to keep them
substitutable in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from core.resources.status import ResourceStatus


class ResourceKind(Enum):
    """First-class resource taxonomy used by the platform.

    Mirrors :class:`core.runtime.resource_specs.ResourceKind` from Phase
    1c (which is the declaration-side taxonomy) but is intentionally
    re-declared here because the two layers are independent: a
    :class:`GuildResource` snapshot may correspond to a kind the schema
    doesn't yet declare (e.g. a discovered orphan).

    Members are aligned by ``.value`` with :class:`core.runtime.resource_specs.ResourceKind`
    so conversion is trivial.
    """

    CHANNEL = "channel"
    ROLE = "role"
    CATEGORY = "category"
    THREAD = "thread"


def _now_utc() -> datetime:
    """Return a tz-aware "now" — INV-N forbids bare :func:`datetime.utcnow`."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class GuildResource:
    """Base snapshot for any guild resource.

    Subclasses add resource-specific fields; this base carries the
    universal fields every kind has.

    Fields:

    id:
        Discord snowflake.
    name:
        Display name at snapshot time.  May drift from the live name
        between snapshots.
    kind:
        The resource taxonomy member.  Always matches the concrete
        subclass.
    status:
        Last-known validation status.  ``UNRESOLVED`` for snapshots
        produced without a probe; ``BOUND``/``MISSING``/``INVALID``
        otherwise.
    last_validated_at:
        UTC timestamp of the most recent validation probe.  ``None``
        when the snapshot was constructed without probing.
    metadata:
        Free-form per-kind metadata.  Subclasses set declared fields;
        this map is for opportunistic extras (e.g. computed labels).
    """

    id: int
    name: str
    kind: ResourceKind
    status: ResourceStatus = ResourceStatus.UNRESOLVED
    last_validated_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChannelResource(GuildResource):
    """Snapshot of a Discord channel (text, voice, news, forum)."""

    channel_type: str = "text"  # "text" | "voice" | "news" | "forum" | "stage"
    category_id: int | None = None
    position: int = 0
    nsfw: bool = False
    kind: ResourceKind = ResourceKind.CHANNEL


@dataclass(frozen=True)
class RoleResource(GuildResource):
    """Snapshot of a Discord role.

    ``permissions_bitfield`` is the raw int the discord.py
    :class:`discord.Permissions` object exposes via ``.value``; consumers
    that need named permission flags should reconstruct the Permissions
    object on demand rather than serializing them here.
    """

    color: int = 0
    position: int = 0
    permissions_bitfield: int = 0
    mentionable: bool = False
    hoist: bool = False
    is_managed: bool = False  # True for bot-managed / integration roles
    kind: ResourceKind = ResourceKind.ROLE


@dataclass(frozen=True)
class CategoryResource(GuildResource):
    """Snapshot of a Discord channel category."""

    position: int = 0
    channel_ids: tuple[int, ...] = ()
    kind: ResourceKind = ResourceKind.CATEGORY


@dataclass(frozen=True)
class ThreadResource(GuildResource):
    """Snapshot of a Discord thread."""

    parent_channel_id: int | None = None
    archived: bool = False
    locked: bool = False
    auto_archive_duration: int = 0  # minutes; 0 = unknown
    kind: ResourceKind = ResourceKind.THREAD


__all__ = [
    "CategoryResource",
    "ChannelResource",
    "GuildResource",
    "ResourceKind",
    "RoleResource",
    "ThreadResource",
]
