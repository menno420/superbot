"""Phase 2a unit tests — GuildResource snapshot dataclass shape."""

from __future__ import annotations

from datetime import datetime, timezone

from core.resources.status import ResourceStatus
from core.resources.types import (
    CategoryResource,
    ChannelResource,
    GuildResource,
    ResourceKind,
    RoleResource,
    ThreadResource,
)


def test_resource_kind_alignment_with_p1c():
    """ResourceKind.value strings match Phase 1c's resource_specs.ResourceKind.

    Both layers refer to the same Discord resource taxonomy; the
    snapshot kind values must align with the declaration kind values
    so conversion is trivial.
    """
    from core.runtime.resource_specs import ResourceKind as DeclKind

    snap_values = {k.value for k in ResourceKind}
    decl_values = {k.value for k in DeclKind}
    # Every snapshot kind has a matching declaration kind.  (The
    # reverse direction is not required because snapshots may exist
    # for kinds the schema doesn't yet declare, e.g. discovered
    # orphans.)
    assert snap_values <= decl_values, (
        f"snapshot kinds {snap_values - decl_values} missing from "
        f"declaration enum"
    )


def test_guild_resource_is_frozen():
    """Snapshots are immutable so they can be safely shared across tasks."""
    snap = GuildResource(id=1, name="x", kind=ResourceKind.CHANNEL)
    try:
        snap.name = "mutated"  # type: ignore[misc]
    except Exception:
        return  # FrozenInstanceError or AttributeError both acceptable
    msg = "GuildResource should be frozen"
    raise AssertionError(msg)


def test_channel_resource_carries_channel_fields():
    snap = ChannelResource(
        id=42,
        name="general",
        kind=ResourceKind.CHANNEL,
        channel_type="text",
        category_id=99,
        position=0,
        nsfw=False,
    )
    assert snap.channel_type == "text"
    assert snap.category_id == 99
    assert snap.position == 0
    assert snap.nsfw is False
    assert snap.kind is ResourceKind.CHANNEL


def test_role_resource_carries_role_fields():
    snap = RoleResource(
        id=42,
        name="Moderator",
        kind=ResourceKind.ROLE,
        color=0xFF0000,
        position=5,
        permissions_bitfield=8,
        mentionable=True,
        hoist=True,
    )
    assert snap.color == 0xFF0000
    assert snap.permissions_bitfield == 8
    assert snap.mentionable is True
    assert snap.kind is ResourceKind.ROLE
    # Phase 2a hardening: managed vs assignable are independent.
    assert snap.is_managed is False  # default
    assert snap.is_assignable is True  # default


def test_role_resource_managed_and_assignable_are_independent():
    """An integration-managed role is managed but not assignable; a
    hierarchy-blocked role is assignable=False yet managed=False.  The
    two fields encode different facts and must vary independently."""
    integration = RoleResource(
        id=1,
        name="Bot",
        kind=ResourceKind.ROLE,
        is_managed=True,
        is_assignable=False,
    )
    hierarchy_blocked = RoleResource(
        id=2,
        name="Above the bot",
        kind=ResourceKind.ROLE,
        is_managed=False,
        is_assignable=False,
    )
    normal = RoleResource(
        id=3,
        name="Member",
        kind=ResourceKind.ROLE,
        is_managed=False,
        is_assignable=True,
    )
    assert integration.is_managed and not integration.is_assignable
    assert not hierarchy_blocked.is_managed and not hierarchy_blocked.is_assignable
    assert not normal.is_managed and normal.is_assignable


def test_category_resource_carries_category_fields():
    snap = CategoryResource(
        id=42,
        name="Staff",
        kind=ResourceKind.CATEGORY,
        position=0,
        channel_ids=(1, 2, 3),
    )
    assert snap.channel_ids == (1, 2, 3)
    assert snap.kind is ResourceKind.CATEGORY


def test_thread_resource_carries_thread_fields():
    snap = ThreadResource(
        id=42,
        name="post-mortem",
        kind=ResourceKind.THREAD,
        parent_channel_id=99,
        archived=False,
        locked=False,
        auto_archive_duration=1440,
    )
    assert snap.parent_channel_id == 99
    assert snap.auto_archive_duration == 1440
    assert snap.kind is ResourceKind.THREAD


def test_resource_default_status_is_unresolved():
    """Snapshots default to UNRESOLVED until a validation probe runs."""
    snap = GuildResource(id=1, name="x", kind=ResourceKind.CHANNEL)
    assert snap.status is ResourceStatus.UNRESOLVED
    assert snap.last_validated_at is None


def test_resource_carries_validation_timestamp():
    now = datetime.now(timezone.utc)
    snap = GuildResource(
        id=1,
        name="x",
        kind=ResourceKind.CHANNEL,
        status=ResourceStatus.BOUND,
        last_validated_at=now,
    )
    assert snap.last_validated_at == now
    assert snap.status is ResourceStatus.BOUND
