"""Tests for services.channel_lifecycle_service (server-management PR4)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.events_catalogue import KNOWN_EVENTS
from services.channel_lifecycle_service import (
    EVT_CHANNEL_LIFECYCLE,
    ChannelLifecycleRequest,
    ChannelLifecycleService,
)
from services.lifecycle import (
    BLOCKED,
    COMPENSATABLE,
    DECLINED,
    IRREVERSIBLE,
    PARTIAL,
    REVERSIBLE,
    SUCCESS,
)


def _channel(cid, name="general", *, fail=None):
    ch = MagicMock()
    ch.id = cid
    ch.name = name
    ch.edit = AsyncMock(side_effect=fail)
    ch.delete = AsyncMock(side_effect=fail)
    ch.move = AsyncMock(side_effect=fail)
    ch.set_permissions = AsyncMock(side_effect=fail)
    ch.clone = AsyncMock(side_effect=fail)
    return ch


def _guild(channels=None, *, manage_channels=True, guild_id=1, roles=None):
    chans = {c.id: c for c in (channels or [])}
    role_map = dict(roles or {})
    guild = MagicMock()
    guild.id = guild_id
    guild.me = SimpleNamespace(
        guild_permissions=SimpleNamespace(manage_channels=manage_channels),
    )
    guild.get_channel.side_effect = lambda cid: chans.get(cid)
    guild.get_role.side_effect = lambda rid: role_map.get(rid)
    guild.get_member.side_effect = lambda mid: role_map.get(mid)
    return guild


def _actor(uid=99):
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
    return ChannelLifecycleService()


def test_event_is_catalogued():
    assert EVT_CHANNEL_LIFECYCLE in KNOWN_EVENTS


@pytest.mark.asyncio
async def test_rename_calls_edit_and_succeeds(svc):
    ch = _channel(10, "old")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="rename", channel_ids=(10,), new_name="new"),
        _actor(),
    )
    ch.edit.assert_awaited_once_with(name="new", reason=None)
    assert result.outcome == SUCCESS
    assert result.reversibility == REVERSIBLE


@pytest.mark.asyncio
async def test_move_calls_edit_with_resolved_category(svc):
    ch = _channel(10, "general")
    guild = _guild([ch])
    category = MagicMock()
    with patch(
        "core.runtime.guild_resources.resolve_category",
        return_value=category,
    ):
        result = await svc.apply(
            guild,
            ChannelLifecycleRequest(
                operation="move",
                channel_ids=(10,),
                category_id=55,
            ),
            _actor(),
        )
    ch.edit.assert_awaited_once_with(category=category, reason=None)
    assert result.outcome == SUCCESS
    assert result.reversibility == COMPENSATABLE


@pytest.mark.asyncio
async def test_reorder_top_calls_move_beginning(svc):
    ch = _channel(10, "general")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="reorder", channel_ids=(10,), position="top"),
        _actor(),
    )
    ch.move.assert_awaited_once_with(beginning=True, reason=None)
    assert result.outcome == SUCCESS
    assert result.reversibility == COMPENSATABLE


@pytest.mark.asyncio
async def test_reorder_defaults_to_bottom(svc):
    ch = _channel(10, "general")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="reorder", channel_ids=(10,)),
        _actor(),
    )
    ch.move.assert_awaited_once_with(end=True, reason=None)
    assert result.outcome == SUCCESS


@pytest.mark.asyncio
async def test_delete_requires_confirmation(svc):
    ch = _channel(10)
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="delete", channel_ids=(10,)),
        _actor(),
        confirmed=False,
    )
    assert result.outcome == DECLINED
    assert result.reversibility == IRREVERSIBLE
    ch.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_confirmed_succeeds(svc):
    ch = _channel(10, "to-go")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="delete", channel_ids=(10,)),
        _actor(),
        confirmed=True,
    )
    ch.delete.assert_awaited_once()
    assert result.outcome == SUCCESS


@pytest.mark.asyncio
async def test_blocked_when_bot_cannot_manage(svc):
    ch = _channel(10)
    guild = _guild([ch], manage_channels=False)
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="delete", channel_ids=(10,)),
        _actor(),
        confirmed=True,
    )
    assert result.outcome == BLOCKED
    ch.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_delete_partial_failure(svc):
    ok = _channel(1, "ok")
    bad = _channel(2, "bad", fail=discord.Forbidden(MagicMock(), "no perms"))
    guild = _guild([ok, bad])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="delete", channel_ids=(1, 2)),
        _actor(),
        confirmed=True,
    )
    assert result.outcome == PARTIAL
    assert [s.target_id for s in result.applied] == [1]
    assert [s.target_id for s in result.failed] == [2]


@pytest.mark.asyncio
async def test_missing_channel_becomes_failed_step(svc):
    guild = _guild([])  # id 10 not present
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="rename", channel_ids=(10,), new_name="x"),
        _actor(),
    )
    assert result.failed and result.failed[0].error == "channel not found"


@pytest.mark.asyncio
async def test_emits_audit_and_event_with_shared_mutation_id(svc, _no_side_effects):
    ch = _channel(10, "general")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(operation="rename", channel_ids=(10,), new_name="new"),
        _actor(),
    )
    _no_side_effects.audit.assert_awaited_once()
    _no_side_effects.event.assert_awaited_once()
    assert _no_side_effects.audit.await_args.kwargs["mutation_id"] == result.mutation_id
    assert _no_side_effects.event.await_args.kwargs["mutation_id"] == result.mutation_id
    assert _no_side_effects.event.await_args.args[0] == EVT_CHANNEL_LIFECYCLE


@pytest.mark.asyncio
async def test_set_overwrite_calls_set_permissions_for_role(svc):
    ch = _channel(10, "general")
    role = SimpleNamespace(id=77, name="@everyone")
    guild = _guild([ch], roles={77: role})
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(
            operation="set_overwrite",
            channel_ids=(10,),
            overwrite_target_id=77,
            overwrite_target_type="role",
            overwrites={"send_messages": False},
        ),
        _actor(),
    )
    ch.set_permissions.assert_awaited_once_with(
        role,
        reason=None,
        send_messages=False,
    )
    assert result.outcome == SUCCESS
    assert result.reversibility == REVERSIBLE


@pytest.mark.asyncio
async def test_set_overwrite_does_not_require_confirmation(svc):
    """An overwrite is reversible, so it must apply without confirmed=True."""
    ch = _channel(10, "general")
    role = SimpleNamespace(id=77, name="@everyone")
    guild = _guild([ch], roles={77: role})
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(
            operation="set_overwrite",
            channel_ids=(10,),
            overwrite_target_id=77,
            overwrites={"read_messages": True},
        ),
        _actor(),
        confirmed=False,
    )
    assert result.outcome == SUCCESS
    ch.set_permissions.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_overwrite_missing_target_is_failed_step(svc):
    ch = _channel(10, "general")
    guild = _guild([ch], roles={})  # role 77 absent
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(
            operation="set_overwrite",
            channel_ids=(10,),
            overwrite_target_id=77,
            overwrites={"send_messages": False},
        ),
        _actor(),
    )
    ch.set_permissions.assert_not_awaited()
    assert result.failed and "not found" in result.failed[0].error


@pytest.mark.asyncio
async def test_clone_calls_clone_and_is_compensatable(svc):
    ch = _channel(10, "general")
    guild = _guild([ch])
    result = await svc.apply(
        guild,
        ChannelLifecycleRequest(
            operation="clone",
            channel_ids=(10,),
            clone_name="general-copy",
        ),
        _actor(),
    )
    ch.clone.assert_awaited_once_with(name="general-copy", reason=None)
    assert result.outcome == SUCCESS
    assert result.reversibility == COMPENSATABLE


@pytest.mark.asyncio
async def test_preview_is_side_effect_free(svc):
    ch = _channel(10, "general")
    guild = _guild([ch])
    preview = await svc.preview(
        guild,
        ChannelLifecycleRequest(operation="delete", channel_ids=(10,)),
    )
    assert preview.allowed is True
    assert preview.reversibility == IRREVERSIBLE
    assert any("irreversible" in w for w in preview.warnings)
    ch.delete.assert_not_awaited()
    ch.edit.assert_not_awaited()
