"""Phase 2a unit tests — discovery enumeration + validation primitives."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import discord
import pytest

from core.resources import discovery
from core.resources.status import ResourceStatus
from core.resources.types import (
    CategoryResource,
    ChannelResource,
    ResourceKind,
    RoleResource,
    ThreadResource,
)

# ---------------------------------------------------------------------------
# Discord mock helpers — produce objects that pass isinstance(spec=...) checks
# ---------------------------------------------------------------------------


def _mk_text_channel(channel_id: int, name: str, *, category=None):
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.name = name
    ch.category_id = category.id if category else None
    ch.category = category
    ch.position = 0
    ch.nsfw = False
    ch.is_news = lambda: False
    return ch


def _mk_voice_channel(channel_id: int, name: str, *, category=None):
    ch = MagicMock(spec=discord.VoiceChannel)
    ch.id = channel_id
    ch.name = name
    ch.category_id = category.id if category else None
    ch.category = category
    ch.position = 0
    ch.nsfw = False
    return ch


def _mk_category(category_id: int, name: str, *, channels=()):
    cat = MagicMock(spec=discord.CategoryChannel)
    cat.id = category_id
    cat.name = name
    cat.position = 0
    cat.category_id = None
    cat.category = None
    cat.nsfw = False
    cat.channels = list(channels)
    return cat


def _mk_role(
    role_id: int,
    name: str,
    *,
    is_default=False,
    managed=False,
    is_assignable=None,
):
    """Mock a :class:`discord.Role` for snapshot tests.

    Phase 2a hardening split ``is_managed`` (intrinsic) from
    ``is_assignable`` (contextual).  Callers can supply either
    independently; default behavior is "managed roles aren't assignable;
    non-managed roles are" which matches the historical conflated
    semantics for existing tests.
    """
    role = MagicMock(spec=discord.Role)
    role.id = role_id
    role.name = name
    role.color = MagicMock(value=0)
    role.position = 0
    role.permissions = MagicMock(value=0)
    role.mentionable = False
    role.hoist = False
    role.managed = managed
    role.is_default = MagicMock(return_value=is_default)
    effective_assignable = (
        is_assignable if is_assignable is not None else not managed
    )
    role.is_assignable = MagicMock(return_value=effective_assignable)
    return role


def _mk_thread(thread_id: int, name: str, *, parent_id=None, archived=False):
    thread = MagicMock(spec=discord.Thread)
    thread.id = thread_id
    thread.name = name
    thread.parent_id = parent_id
    thread.archived = archived
    thread.locked = False
    thread.auto_archive_duration = 1440
    return thread


def _mk_guild(
    *,
    channels=(),
    categories=(),
    roles=(),
    threads=(),
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    guild.channels = list(channels) + list(categories)
    guild.categories = list(categories)
    guild.roles = list(roles)
    guild.threads = list(threads)

    by_id = {x.id: x for x in guild.channels}
    guild.get_channel = lambda cid: by_id.get(cid)
    roles_by_id = {r.id: r for r in guild.roles}
    guild.get_role = lambda rid: roles_by_id.get(rid)
    threads_by_id = {t.id: t for t in guild.threads}
    guild.get_thread = lambda tid: threads_by_id.get(tid)
    return guild


# ---------------------------------------------------------------------------
# Snapshot factories
# ---------------------------------------------------------------------------


def test_channel_to_snapshot_text():
    ch = _mk_text_channel(42, "general")
    snap = discovery.channel_to_snapshot(ch)
    assert isinstance(snap, ChannelResource)
    assert snap.id == 42
    assert snap.name == "general"
    assert snap.channel_type == "text"


def test_channel_to_snapshot_voice():
    ch = _mk_voice_channel(42, "Lounge")
    snap = discovery.channel_to_snapshot(ch)
    assert snap.channel_type == "voice"


def test_role_to_snapshot():
    role = _mk_role(42, "Moderator")
    snap = discovery.role_to_snapshot(role)
    assert isinstance(snap, RoleResource)
    assert snap.id == 42
    assert snap.name == "Moderator"
    assert snap.kind is ResourceKind.ROLE


def test_role_to_snapshot_managed_and_assignable_split():
    """Phase 2a hardening: snapshot factory must populate both fields
    from their respective discord.py attributes, not conflate them."""
    integration = _mk_role(1, "Bot", managed=True, is_assignable=False)
    hierarchy_blocked = _mk_role(2, "Above", managed=False, is_assignable=False)
    normal = _mk_role(3, "Member", managed=False, is_assignable=True)

    snap_integration = discovery.role_to_snapshot(integration)
    snap_blocked = discovery.role_to_snapshot(hierarchy_blocked)
    snap_normal = discovery.role_to_snapshot(normal)

    assert snap_integration.is_managed is True
    assert snap_integration.is_assignable is False

    # Hierarchy-blocked: NOT managed (Discord doesn't mark it so) but
    # NOT assignable by the bot.  The conflated semantics from before
    # P2a hardening incorrectly reported is_managed=True for this case.
    assert snap_blocked.is_managed is False
    assert snap_blocked.is_assignable is False

    assert snap_normal.is_managed is False
    assert snap_normal.is_assignable is True


def test_category_to_snapshot():
    ch_a = _mk_text_channel(1, "a")
    ch_b = _mk_text_channel(2, "b")
    cat = _mk_category(99, "Staff", channels=(ch_a, ch_b))
    snap = discovery.category_to_snapshot(cat)
    assert isinstance(snap, CategoryResource)
    assert snap.channel_ids == (1, 2)


def test_thread_to_snapshot():
    thread = _mk_thread(42, "post-mortem", parent_id=99)
    snap = discovery.thread_to_snapshot(thread)
    assert isinstance(snap, ThreadResource)
    assert snap.parent_channel_id == 99


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------


def test_list_channels_excludes_categories():
    text = _mk_text_channel(1, "general")
    cat = _mk_category(99, "Staff")
    guild = _mk_guild(channels=[text], categories=[cat])
    result = discovery.list_channels(guild)
    assert len(result) == 1
    assert result[0].id == 1


def test_list_roles_excludes_everyone():
    everyone = _mk_role(0, "@everyone", is_default=True)
    mod = _mk_role(42, "Moderator")
    guild = _mk_guild(roles=[everyone, mod])
    result = discovery.list_roles(guild)
    assert len(result) == 1
    assert result[0].id == 42


def test_list_resources_dispatches_by_kind():
    text = _mk_text_channel(1, "general")
    cat = _mk_category(99, "Staff", channels=(text,))
    role = _mk_role(42, "Mod")
    thread = _mk_thread(7, "t")
    guild = _mk_guild(
        channels=[text],
        categories=[cat],
        roles=[role],
        threads=[thread],
    )

    assert len(discovery.list_resources(guild, ResourceKind.CHANNEL)) == 1
    assert len(discovery.list_resources(guild, ResourceKind.CATEGORY)) == 1
    assert len(discovery.list_resources(guild, ResourceKind.ROLE)) == 1
    assert len(discovery.list_resources(guild, ResourceKind.THREAD)) == 1


def test_list_resources_filter_applies_after_snapshot():
    a = _mk_text_channel(1, "general")
    b = _mk_text_channel(2, "spam")
    guild = _mk_guild(channels=[a, b])
    result = discovery.list_resources(
        guild,
        ResourceKind.CHANNEL,
        filter_fn=lambda r: r.name.startswith("g"),
    )
    assert [r.id for r in result] == [1]


# ---------------------------------------------------------------------------
# Single resource resolution
# ---------------------------------------------------------------------------


def test_resolve_channel_present():
    ch = _mk_text_channel(42, "general")
    guild = _mk_guild(channels=[ch])
    result = discovery.resolve_resource(guild, ResourceKind.CHANNEL, 42)
    assert isinstance(result, ChannelResource)
    assert result.id == 42


def test_resolve_channel_missing():
    guild = _mk_guild(channels=[])
    result = discovery.resolve_resource(guild, ResourceKind.CHANNEL, 42)
    assert result is None


def test_resolve_channel_id_is_actually_category():
    """Channel ID lookup on a category returns None (wrong kind)."""
    cat = _mk_category(42, "Staff")
    guild = _mk_guild(categories=[cat])
    result = discovery.resolve_resource(guild, ResourceKind.CHANNEL, 42)
    assert result is None


def test_resolve_role_present_and_missing():
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    found = discovery.resolve_resource(guild, ResourceKind.ROLE, 42)
    assert isinstance(found, RoleResource)
    assert discovery.resolve_resource(guild, ResourceKind.ROLE, 99) is None


def test_resolve_category_only_returns_actual_category():
    text = _mk_text_channel(1, "general")
    cat = _mk_category(99, "Staff", channels=(text,))
    guild = _mk_guild(channels=[text], categories=[cat])
    # Category ID returns CategoryResource
    assert isinstance(
        discovery.resolve_resource(guild, ResourceKind.CATEGORY, 99),
        CategoryResource,
    )
    # Channel ID returns None when caller asked for category
    assert discovery.resolve_resource(guild, ResourceKind.CATEGORY, 1) is None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_resource_bound():
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
    ) as mock_upsert:
        mock_upsert.return_value = None
        status = await discovery.validate_resource(
            guild,
            ResourceKind.ROLE,
            42,
        )
    assert status is ResourceStatus.BOUND
    mock_upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_resource_missing():
    guild = _mk_guild()
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
    ) as mock_upsert:
        mock_upsert.return_value = None
        status = await discovery.validate_resource(
            guild,
            ResourceKind.ROLE,
            42,
        )
    assert status is ResourceStatus.MISSING


@pytest.mark.asyncio
async def test_validate_resource_invalid_wrong_kind():
    cat = _mk_category(42, "Staff")
    guild = _mk_guild(categories=[cat])
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
    ) as mock_upsert:
        mock_upsert.return_value = None
        status = await discovery.validate_resource(
            guild,
            ResourceKind.CHANNEL,
            42,
        )
    assert status is ResourceStatus.INVALID


@pytest.mark.asyncio
async def test_validate_resource_archived_thread_invalid():
    thread = _mk_thread(42, "t", archived=True)
    guild = _mk_guild(threads=[thread])
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
    ) as mock_upsert:
        mock_upsert.return_value = None
        status = await discovery.validate_resource(
            guild,
            ResourceKind.THREAD,
            42,
        )
    assert status is ResourceStatus.INVALID


@pytest.mark.asyncio
async def test_validate_resource_persist_false_skips_cache_write():
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
    ) as mock_upsert:
        mock_upsert.return_value = None
        await discovery.validate_resource(
            guild,
            ResourceKind.ROLE,
            42,
            persist=False,
        )
    mock_upsert.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_resources_batch():
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    with patch(
        "core.resources.discovery.resource_cache.upsert_statuses",
    ) as mock_batch:
        mock_batch.return_value = 2
        result = await discovery.validate_resources(
            guild,
            [(ResourceKind.ROLE, 42), (ResourceKind.ROLE, 99)],
        )
    assert result[(ResourceKind.ROLE, 42)] is ResourceStatus.BOUND
    assert result[(ResourceKind.ROLE, 99)] is ResourceStatus.MISSING
    mock_batch.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_resource_cache_failure_swallowed():
    """Cache write failures must not propagate; status is still returned."""
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    with patch(
        "core.resources.discovery.resource_cache.upsert_status",
        side_effect=RuntimeError("db down"),
    ):
        status = await discovery.validate_resource(
            guild,
            ResourceKind.ROLE,
            42,
        )
    assert status is ResourceStatus.BOUND


@pytest.mark.asyncio
async def test_validate_resource_permissions_is_phase_4_5_stub():
    """Phase 2a ships the signature; Phase 4.5 fills in the implementation.

    The hook MUST raise NotImplementedError rather than silently return
    BOUND — Phase 2b's bindings could otherwise treat a missing
    implementation as a green light to skip permission gating.
    """
    guild = _mk_guild()
    with pytest.raises(NotImplementedError, match="Phase 4.5"):
        await discovery.validate_resource_permissions(
            guild,
            ResourceKind.CHANNEL,
            42,
            "moderation.warn.apply",
        )


# ---------------------------------------------------------------------------
# Name lookup
# ---------------------------------------------------------------------------


def test_find_role_by_name_case_insensitive():
    role = _mk_role(42, "Moderator")
    everyone = _mk_role(0, "@everyone", is_default=True)
    guild = _mk_guild(roles=[everyone, role])
    assert discovery.find_role_by_name(guild, "moderator") is role
    assert discovery.find_role_by_name(guild, "MODERATOR") is role
    assert discovery.find_role_by_name(guild, "missing") is None
