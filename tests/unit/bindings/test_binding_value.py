"""Phase 2b unit tests — BindingValue dataclass shape + accessor."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime.bindings import BindingValue, get_binding
from core.runtime.subsystem_schema import BindingKind


def test_binding_value_is_frozen():
    """Snapshots are immutable so they can be shared across tasks."""
    bv = BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        bv.target_id = 42  # type: ignore[misc]


def test_binding_value_defaults_to_unresolved():
    bv = BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
    )
    assert bv.target_id is None
    assert bv.status is ResourceStatus.UNRESOLVED
    assert bv.version == 0
    assert bv.last_updated_at is None
    assert bv.is_bound is False


def test_binding_value_is_bound_property():
    bound = BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=42,
        status=ResourceStatus.BOUND,
    )
    missing = BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=42,
        status=ResourceStatus.MISSING,
    )
    no_target = BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=None,
        status=ResourceStatus.BOUND,  # nonsensical but exercises the AND
    )
    assert bound.is_bound is True
    assert missing.is_bound is False
    assert no_target.is_bound is False


@pytest.mark.asyncio
async def test_get_binding_unresolved_on_missing_row():
    with patch(
        "core.runtime.bindings.bindings_db.get_one",
        AsyncMock(return_value=None),
    ):
        bv = await get_binding(1, "xp", "announce_channel")
    assert bv.status is ResourceStatus.UNRESOLVED
    assert bv.target_id is None
    assert bv.version == 0
    assert bv.last_updated_at is None


@pytest.mark.asyncio
async def test_get_binding_uses_expected_kind_when_missing():
    with patch(
        "core.runtime.bindings.bindings_db.get_one",
        AsyncMock(return_value=None),
    ):
        bv = await get_binding(
            1,
            "xp",
            "announce_channel",
            expected_kind=BindingKind.ROLE,
        )
    assert bv.kind is BindingKind.ROLE


@pytest.mark.asyncio
async def test_get_binding_translates_row_to_value():
    now = datetime.now(timezone.utc)
    row = {
        "guild_id": 1,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "channel",
        "target_id": 42,
        "status": "bound",
        "last_validated_at": now,
        "last_updated_at": now,
        "version": 3,
    }
    with patch(
        "core.runtime.bindings.bindings_db.get_one",
        AsyncMock(return_value=row),
    ):
        bv = await get_binding(1, "xp", "announce_channel")
    assert bv.kind is BindingKind.CHANNEL
    assert bv.target_id == 42
    assert bv.status is ResourceStatus.BOUND
    assert bv.version == 3
    assert bv.last_updated_at == now
    assert bv.is_bound is True


@pytest.mark.asyncio
async def test_get_binding_handles_unknown_kind_string_gracefully():
    """A corrupt kind string should not crash get_binding."""
    row = {
        "guild_id": 1,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "spaceship",  # not in enum
        "target_id": 42,
        "status": "bound",
        "last_validated_at": None,
        "last_updated_at": None,
        "version": 1,
    }
    with patch(
        "core.runtime.bindings.bindings_db.get_one",
        AsyncMock(return_value=row),
    ):
        bv = await get_binding(1, "xp", "announce_channel")
    # Falls back to CHANNEL (the default when no expected_kind given).
    assert bv.kind is BindingKind.CHANNEL


@pytest.mark.asyncio
async def test_get_binding_handles_unknown_status_string_gracefully():
    row = {
        "guild_id": 1,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "channel",
        "target_id": 42,
        "status": "haunted",  # not in enum
        "last_validated_at": None,
        "last_updated_at": None,
        "version": 1,
    }
    with patch(
        "core.runtime.bindings.bindings_db.get_one",
        AsyncMock(return_value=row),
    ):
        bv = await get_binding(1, "xp", "announce_channel")
    assert bv.status is ResourceStatus.UNRESOLVED


def test_diagnostics_provider_returns_taxonomy():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("bindings")
    assert set(snap["kinds"]) == {"channel", "role", "category", "thread", "member"}
    # MEMBER kind dispatches to the member resolver, others to "resource"
    assert snap["validator_dispatch"]["member"] == "member"
    assert snap["validator_dispatch"]["channel"] == "resource"
    assert snap["validator_dispatch"]["role"] == "resource"
