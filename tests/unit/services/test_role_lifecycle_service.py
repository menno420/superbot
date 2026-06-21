"""Tests for services.role_lifecycle_service (server-management PR5)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.events_catalogue import KNOWN_EVENTS
from services.lifecycle import (
    BLOCKED,
    COMPENSATABLE,
    DECLINED,
    DISCORD_FAILED,
    IRREVERSIBLE,
    REVERSIBLE,
    SUCCESS,
)
from services.role_lifecycle_service import (
    EVT_ROLE_LIFECYCLE,
    RoleLifecycleRequest,
    RoleLifecycleService,
)


def _role(rid, name="Members", *, position=1, managed=False, fail=None):
    role = MagicMock()
    role.id = rid
    role.name = name
    role.position = position
    role.managed = managed
    role.is_default = lambda: False
    role.edit = AsyncMock(side_effect=fail)
    role.delete = AsyncMock(side_effect=fail)
    return role


def _guild(roles=None, *, manage_roles=True, bot_top_position=100, guild_id=1, created=None):
    rolemap = {r.id: r for r in (roles or [])}
    guild = MagicMock()
    guild.id = guild_id
    guild.me = SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_roles=manage_roles),
        top_role=SimpleNamespace(position=bot_top_position),
    )
    guild.get_role.side_effect = lambda rid: rolemap.get(rid)
    guild.create_role = AsyncMock(return_value=created or _role(999, "new-role"))
    return guild


def _actor(uid=42):
    return SimpleNamespace(id=uid)


@pytest.fixture(autouse=True)
def _no_side_effects():
    with (
        patch(
            "services.lifecycle.contracts.emit_lifecycle_audit",
            new_callable=AsyncMock,
            return_value=True,
        ) as audit,
        patch("core.events.bus.emit", new_callable=AsyncMock) as event,
    ):
        yield SimpleNamespace(audit=audit, event=event)


@pytest.fixture
def svc():
    return RoleLifecycleService()


def test_event_is_catalogued():
    assert EVT_ROLE_LIFECYCLE in KNOWN_EVENTS


@pytest.mark.asyncio
async def test_create_calls_create_role_and_succeeds(svc):
    guild = _guild(created=_role(999, "Recruit"))
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="create", name="Recruit", color=discord.Color(0x1)),
        _actor(),
    )
    guild.create_role.assert_awaited_once()
    assert result.outcome == SUCCESS
    assert result.reversibility == COMPENSATABLE
    assert result.steps[0].target_id == 999
    assert result.steps[0].target_name == "Recruit"


@pytest.mark.asyncio
async def test_create_passes_gradient_colours_when_set(svc):
    guild = _guild(created=_role(999, "Sunset"))
    await svc.apply(
        guild,
        RoleLifecycleRequest(
            operation="create",
            name="Sunset",
            color=discord.Color(0x1),
            secondary_color=discord.Color(0x2),
            tertiary_color=discord.Color(0x3),
        ),
        _actor(),
    )
    kwargs = guild.create_role.await_args.kwargs
    assert kwargs["secondary_color"] == discord.Color(0x2)
    assert kwargs["tertiary_color"] == discord.Color(0x3)


@pytest.mark.asyncio
async def test_create_omits_gradient_colours_when_absent(svc):
    guild = _guild(created=_role(999, "Plain"))
    await svc.apply(
        guild,
        RoleLifecycleRequest(operation="create", name="Plain", color=discord.Color(0x1)),
        _actor(),
    )
    kwargs = guild.create_role.await_args.kwargs
    assert "secondary_color" not in kwargs
    assert "tertiary_color" not in kwargs


@pytest.mark.asyncio
async def test_edit_calls_role_edit_with_changed_fields(svc):
    role = _role(10, "Old")
    guild = _guild([role])
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(
            operation="edit",
            role_id=10,
            name="New",
            color=discord.Color(0xABCDEF),
        ),
        _actor(),
    )
    role.edit.assert_awaited_once()
    kwargs = role.edit.await_args.kwargs
    assert kwargs["name"] == "New"
    assert kwargs["color"] == discord.Color(0xABCDEF)
    assert result.outcome == SUCCESS
    assert result.reversibility == REVERSIBLE


@pytest.mark.asyncio
async def test_delete_requires_confirmation(svc):
    role = _role(10)
    guild = _guild([role])
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="delete", role_id=10),
        _actor(),
        confirmed=False,
    )
    assert result.outcome == DECLINED
    assert result.reversibility == IRREVERSIBLE
    role.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_confirmed_succeeds(svc):
    role = _role(10, "ToGo")
    guild = _guild([role])
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="delete", role_id=10),
        _actor(),
        confirmed=True,
    )
    role.delete.assert_awaited_once()
    assert result.outcome == SUCCESS


@pytest.mark.asyncio
async def test_blocked_when_bot_cannot_manage(svc):
    role = _role(10)
    guild = _guild([role], manage_roles=False)
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="delete", role_id=10),
        _actor(),
        confirmed=True,
    )
    assert result.outcome == BLOCKED
    role.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_blocked_when_role_above_bot(svc):
    # Role STRICTLY above the bot's top role → role_feasibility ABOVE_BOT.
    # (Equal positions are not automatically "above" — Discord breaks position
    # ties by id — so use a strictly-higher position; see the role-hierarchy
    # (position, id) tiebreak in utils.role_feasibility.)
    role = _role(10, "Admins", position=100)
    guild = _guild([role], bot_top_position=50)
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="edit", role_id=10, name="x"),
        _actor(),
    )
    assert result.outcome == BLOCKED
    assert "highest role" in result.first_error
    role.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_role_blocks(svc):
    guild = _guild([])  # id 10 absent
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="delete", role_id=10),
        _actor(),
        confirmed=True,
    )
    assert result.outcome == BLOCKED
    assert result.first_error == "role not found"


@pytest.mark.asyncio
async def test_discord_failure_becomes_failed_step(svc):
    role = _role(10, "Boom", fail=discord.Forbidden(MagicMock(), "nope"))
    guild = _guild([role])
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="edit", role_id=10, name="x"),
        _actor(),
    )
    assert result.outcome == DISCORD_FAILED
    assert result.failed and result.failed[0].error == "missing permission"


@pytest.mark.asyncio
async def test_emits_audit_and_event_with_shared_mutation_id(svc, _no_side_effects):
    role = _role(10, "Old")
    guild = _guild([role])
    result = await svc.apply(
        guild,
        RoleLifecycleRequest(operation="edit", role_id=10, name="New"),
        _actor(),
    )
    _no_side_effects.audit.assert_awaited_once()
    _no_side_effects.event.assert_awaited_once()
    assert _no_side_effects.audit.await_args.kwargs["mutation_id"] == result.mutation_id
    assert _no_side_effects.event.await_args.kwargs["mutation_id"] == result.mutation_id
    assert _no_side_effects.event.await_args.args[0] == EVT_ROLE_LIFECYCLE


@pytest.mark.asyncio
async def test_preview_is_side_effect_free(svc):
    role = _role(10, "ToGo")
    guild = _guild([role])
    preview = await svc.preview(
        guild,
        RoleLifecycleRequest(operation="delete", role_id=10),
    )
    assert preview.allowed is True
    assert preview.reversibility == IRREVERSIBLE
    assert any("irreversible" in w for w in preview.warnings)
    role.delete.assert_not_awaited()
    role.edit.assert_not_awaited()
