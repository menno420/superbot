"""Phase 2b unit tests — validate_binding_target dispatch.

Verifies the design decision documented in
``docs/phase_2b_bindings_plan.md``: resource kinds use
:func:`core.resources.discovery.validate_resource`; member kind uses
:func:`core.runtime.guild_resources.resolve_member`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime.bindings import validate_binding_target
from core.runtime.subsystem_schema import BindingKind


@pytest.mark.asyncio
async def test_member_kind_dispatches_to_member_resolver():
    guild = MagicMock()
    sentinel_member = object()
    with patch(
        "core.runtime.bindings.guild_resources.resolve_member",
        return_value=sentinel_member,
    ) as mock_resolve, patch(
        "core.runtime.bindings.discovery.validate_resource",
        AsyncMock(return_value=ResourceStatus.BOUND),
    ) as mock_validate:
        status = await validate_binding_target(guild, BindingKind.MEMBER, 42)
    assert status is ResourceStatus.BOUND
    mock_resolve.assert_called_once_with(guild, 42)
    mock_validate.assert_not_called()


@pytest.mark.asyncio
async def test_member_kind_missing_returns_missing():
    guild = MagicMock()
    with patch(
        "core.runtime.bindings.guild_resources.resolve_member",
        return_value=None,
    ):
        status = await validate_binding_target(guild, BindingKind.MEMBER, 42)
    assert status is ResourceStatus.MISSING


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind",
    [
        BindingKind.CHANNEL,
        BindingKind.ROLE,
        BindingKind.CATEGORY,
        BindingKind.THREAD,
    ],
)
async def test_resource_kinds_dispatch_to_discovery(kind):
    guild = MagicMock()
    guild.id = 1
    with patch(
        "core.runtime.bindings.discovery.validate_resource",
        AsyncMock(return_value=ResourceStatus.BOUND),
    ) as mock_validate, patch(
        "core.runtime.bindings.guild_resources.resolve_member",
    ) as mock_resolve:
        status = await validate_binding_target(guild, kind, 42)
    assert status is ResourceStatus.BOUND
    # Ensure persist=False is used — Phase 2b bindings track their own
    # status, the resource cache should not be poisoned by binding probes.
    assert mock_validate.await_args.kwargs == {"persist": False}
    mock_resolve.assert_not_called()


@pytest.mark.asyncio
async def test_resource_kind_missing_returns_missing():
    guild = MagicMock()
    with patch(
        "core.runtime.bindings.discovery.validate_resource",
        AsyncMock(return_value=ResourceStatus.MISSING),
    ):
        status = await validate_binding_target(guild, BindingKind.CHANNEL, 42)
    assert status is ResourceStatus.MISSING


@pytest.mark.asyncio
async def test_resource_kind_invalid_returns_invalid():
    """Wrong-type ID (e.g. channel kind, category id) propagates INVALID."""
    guild = MagicMock()
    with patch(
        "core.runtime.bindings.discovery.validate_resource",
        AsyncMock(return_value=ResourceStatus.INVALID),
    ):
        status = await validate_binding_target(guild, BindingKind.CHANNEL, 42)
    assert status is ResourceStatus.INVALID
