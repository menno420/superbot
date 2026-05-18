"""Resource enumeration + validation primitives.

Builds typed :class:`~core.resources.types.GuildResource` snapshots from
a live discord.py guild object, and validates resource existence /
accessibility against the live guild state, persisting the resulting
status to :mod:`utils.db.resource_cache`.

The functions in this module are the *single point of contact* between
the platform's resource taxonomy and discord.py's primitives.  Phase 2c
selectors, Phase 4c diagnostics, Phase 7 wizard previews, and Phase 7.5
provisioning all consume the snapshots produced here.

Public surface:

* :func:`list_resources` — enumerate all resources of a given kind in
  a guild (snapshotted, not validated).
* :func:`resolve_resource` — look up a single resource by ID.
* :func:`validate_resource` — compute the live :class:`ResourceStatus`
  for a snapshot and persist it.
* :func:`find_role_by_name` — case + space-insensitive role lookup
  (absorbed from ``views/selectors/_resource_helpers.py``).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

import discord

from core.resources.status import ResourceStatus
from core.resources.types import (
    CategoryResource,
    ChannelResource,
    GuildResource,
    ResourceKind,
    RoleResource,
    ThreadResource,
)
from utils.db import resource_cache
from utils.helpers import normalize_name

logger = logging.getLogger("bot.resources.discovery")


# ---------------------------------------------------------------------------
# Snapshot factories — discord.py object → typed dataclass
# ---------------------------------------------------------------------------


def _channel_type_name(channel: discord.abc.GuildChannel) -> str:
    """Return the canonical channel-type string for a discord channel."""
    if isinstance(channel, discord.TextChannel):
        # News channels are TextChannel with .is_news() True.
        if getattr(channel, "is_news", lambda: False)():
            return "news"
        return "text"
    if isinstance(channel, discord.VoiceChannel):
        return "voice"
    if isinstance(channel, discord.ForumChannel):
        return "forum"
    if isinstance(channel, discord.StageChannel):
        return "stage"
    if isinstance(channel, discord.CategoryChannel):
        return "category"
    return channel.__class__.__name__.lower()


def channel_to_snapshot(channel: discord.abc.GuildChannel) -> ChannelResource:
    """Build a :class:`ChannelResource` snapshot of ``channel``."""
    return ChannelResource(
        id=channel.id,
        name=channel.name,
        kind=ResourceKind.CHANNEL,
        channel_type=_channel_type_name(channel),
        category_id=channel.category_id,
        position=channel.position,
        nsfw=getattr(channel, "nsfw", False),
    )


def role_to_snapshot(role: discord.Role) -> RoleResource:
    """Build a :class:`RoleResource` snapshot of ``role``."""
    return RoleResource(
        id=role.id,
        name=role.name,
        kind=ResourceKind.ROLE,
        color=role.color.value,
        position=role.position,
        permissions_bitfield=role.permissions.value,
        mentionable=role.mentionable,
        hoist=role.hoist,
        is_managed=role.is_assignable() is False or role.managed,
    )


def category_to_snapshot(category: discord.CategoryChannel) -> CategoryResource:
    """Build a :class:`CategoryResource` snapshot of ``category``."""
    return CategoryResource(
        id=category.id,
        name=category.name,
        kind=ResourceKind.CATEGORY,
        position=category.position,
        channel_ids=tuple(ch.id for ch in category.channels),
    )


def thread_to_snapshot(thread: discord.Thread) -> ThreadResource:
    """Build a :class:`ThreadResource` snapshot of ``thread``."""
    return ThreadResource(
        id=thread.id,
        name=thread.name,
        kind=ResourceKind.THREAD,
        parent_channel_id=thread.parent_id,
        archived=thread.archived,
        locked=thread.locked,
        auto_archive_duration=thread.auto_archive_duration or 0,
    )


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


def list_channels(guild: discord.Guild) -> list[ChannelResource]:
    """Return snapshots of every non-category channel in ``guild``."""
    return [
        channel_to_snapshot(ch)
        for ch in guild.channels
        if not isinstance(ch, discord.CategoryChannel)
    ]


def list_roles(guild: discord.Guild) -> list[RoleResource]:
    """Return snapshots of every role in ``guild`` except ``@everyone``."""
    return [role_to_snapshot(r) for r in guild.roles if not r.is_default()]


def list_categories(guild: discord.Guild) -> list[CategoryResource]:
    """Return snapshots of every category in ``guild``."""
    return [category_to_snapshot(c) for c in guild.categories]


def list_threads(guild: discord.Guild) -> list[ThreadResource]:
    """Return snapshots of every active thread in ``guild``."""
    return [thread_to_snapshot(t) for t in guild.threads]


def list_resources(
    guild: discord.Guild,
    kind: ResourceKind,
    *,
    filter_fn: Callable[[GuildResource], bool] | None = None,
) -> list[GuildResource]:
    """Enumerate resources of ``kind`` from ``guild``.

    Dispatches to the kind-specific lister.  Applies ``filter_fn`` (if
    given) after snapshotting so filters operate on the typed snapshot
    rather than the discord.py object.
    """
    if kind is ResourceKind.CHANNEL:
        results: list[GuildResource] = list(list_channels(guild))
    elif kind is ResourceKind.ROLE:
        results = list(list_roles(guild))
    elif kind is ResourceKind.CATEGORY:
        results = list(list_categories(guild))
    elif kind is ResourceKind.THREAD:
        results = list(list_threads(guild))
    else:  # pragma: no cover — enum is exhaustive
        msg = f"unsupported resource kind: {kind!r}"
        raise ValueError(msg)
    if filter_fn is not None:
        return [r for r in results if filter_fn(r)]
    return results


# ---------------------------------------------------------------------------
# Resolution — single resource by ID
# ---------------------------------------------------------------------------


def resolve_resource(
    guild: discord.Guild,
    kind: ResourceKind,
    resource_id: int,
) -> GuildResource | None:
    """Return a snapshot of the resource with ``resource_id``, or ``None``.

    The lookup uses discord.py's cached lookups (``guild.get_channel``,
    ``guild.get_role``, ``guild.get_thread``) — sync, no I/O.  Returns
    ``None`` if the resource is not present in the cache (which is
    usually equivalent to "does not exist", though startup races can
    briefly produce false negatives).
    """
    if kind is ResourceKind.CHANNEL:
        channel = guild.get_channel(resource_id)
        if isinstance(channel, discord.CategoryChannel):
            # Category IDs collide with the channel ID-space; reject the
            # caller's mis-typed lookup explicitly.
            return None
        if channel is None:
            return None
        return channel_to_snapshot(channel)
    if kind is ResourceKind.ROLE:
        role = guild.get_role(resource_id)
        return None if role is None else role_to_snapshot(role)
    if kind is ResourceKind.CATEGORY:
        category = guild.get_channel(resource_id)
        if not isinstance(category, discord.CategoryChannel):
            return None
        return category_to_snapshot(category)
    if kind is ResourceKind.THREAD:
        thread = guild.get_thread(resource_id)
        return None if thread is None else thread_to_snapshot(thread)
    return None


# ---------------------------------------------------------------------------
# Validation — live probe + cache write
# ---------------------------------------------------------------------------


def _compute_status(
    guild: discord.Guild,
    kind: ResourceKind,
    resource_id: int,
) -> ResourceStatus:
    """Pure status computation; no DB writes.

    Returns :class:`ResourceStatus.BOUND` if the resource exists and is
    the right type, :class:`ResourceStatus.MISSING` if it does not
    exist, :class:`ResourceStatus.INVALID` if it exists but with the
    wrong type (e.g. caller asked for CHANNEL, ID points at a category).
    """
    if kind is ResourceKind.CHANNEL:
        candidate = guild.get_channel(resource_id)
        if candidate is None:
            return ResourceStatus.MISSING
        if isinstance(candidate, discord.CategoryChannel):
            return ResourceStatus.INVALID
        return ResourceStatus.BOUND
    if kind is ResourceKind.ROLE:
        return (
            ResourceStatus.BOUND
            if guild.get_role(resource_id) is not None
            else ResourceStatus.MISSING
        )
    if kind is ResourceKind.CATEGORY:
        candidate = guild.get_channel(resource_id)
        if candidate is None:
            return ResourceStatus.MISSING
        return (
            ResourceStatus.BOUND
            if isinstance(candidate, discord.CategoryChannel)
            else ResourceStatus.INVALID
        )
    if kind is ResourceKind.THREAD:
        thread = guild.get_thread(resource_id)
        if thread is None:
            return ResourceStatus.MISSING
        if thread.archived or thread.locked:
            return ResourceStatus.INVALID
        return ResourceStatus.BOUND
    return ResourceStatus.UNRESOLVED


async def validate_resource(
    guild: discord.Guild,
    kind: ResourceKind,
    resource_id: int,
    *,
    persist: bool = True,
) -> ResourceStatus:
    """Compute the live status for a resource and (optionally) persist it.

    ``persist=False`` is for read-only diagnostics that should not write
    the cache (e.g. dry-run completeness checks).  Default is to upsert
    the row so subsequent ``get_status`` calls see the fresh value.
    """
    status = _compute_status(guild, kind, resource_id)
    if persist:
        try:
            await resource_cache.upsert_status(
                guild.id,
                kind.value,
                resource_id,
                status.value,
            )
        except Exception as exc:
            # Cache write failure must not propagate to the caller — the
            # status is still valid; the only loss is that subsequent
            # reads will be stale.
            logger.warning(
                "validate_resource: cache upsert failed for "
                "guild=%d kind=%s resource_id=%d (%s); "
                "returning computed status anyway.",
                guild.id,
                kind.value,
                resource_id,
                exc,
            )
    return status


async def validate_resources(
    guild: discord.Guild,
    pairs: Iterable[tuple[ResourceKind, int]],
) -> dict[tuple[ResourceKind, int], ResourceStatus]:
    """Batch validate.  Returns a ``(kind, id) -> status`` mapping.

    Uses a single transactional executemany for the cache write so
    sweeps from Phase 4c diagnostics do not bombard the DB.
    """
    materialised = list(pairs)
    if not materialised:
        return {}
    results: dict[tuple[ResourceKind, int], ResourceStatus] = {}
    rows_to_write: list[tuple[int, str, int, str]] = []
    for kind, resource_id in materialised:
        status = _compute_status(guild, kind, resource_id)
        results[(kind, resource_id)] = status
        rows_to_write.append((guild.id, kind.value, resource_id, status.value))
    try:
        await resource_cache.upsert_statuses(rows_to_write)
    except Exception as exc:
        logger.warning(
            "validate_resources: batch cache upsert failed for guild=%d (%s); "
            "returning computed statuses anyway.",
            guild.id,
            exc,
        )
    return results


# ---------------------------------------------------------------------------
# Name-based lookup helpers — absorbed from views/selectors/_resource_helpers
# ---------------------------------------------------------------------------


def find_role_by_name(guild: discord.Guild, name: str) -> discord.Role | None:
    """Case + space-insensitive role lookup.

    Mirrors the legacy ``_find_role_normalized`` helper.  Returns the
    raw :class:`discord.Role` (not a snapshot) since most callers need
    to invoke methods on it; wrap with :func:`role_to_snapshot` if a
    snapshot is needed.
    """
    key = normalize_name(name)
    return discord.utils.find(
        lambda r: normalize_name(r.name) == key,
        guild.roles,
    )


__all__ = [
    "category_to_snapshot",
    "channel_to_snapshot",
    "find_role_by_name",
    "list_categories",
    "list_channels",
    "list_resources",
    "list_roles",
    "list_threads",
    "resolve_resource",
    "role_to_snapshot",
    "thread_to_snapshot",
    "validate_resource",
    "validate_resources",
]
