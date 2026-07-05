"""Stage-2 walk bug #5 — raid-lockdown slowmode goes through the audited seam.

``_apply_slowmode`` / ``_lift_lockdown`` used to call ``channel.edit()`` directly,
bypassing ``ChannelLifecycleService`` (which emits ``channel.lifecycle_changed`` +
the audit companion). They now route through the same ``set_slowmode`` seam
``!slowmode`` uses, as an automated (``actor_type="system"``) write.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import security_service

# ruff: noqa: S101


def _fake_channel(channel_id: int = 777):
    return SimpleNamespace(id=channel_id, guild=SimpleNamespace(id=42))


def _patch_service(monkeypatch):
    apply_mock = AsyncMock(return_value=MagicMock())
    factory = MagicMock(return_value=SimpleNamespace(apply=apply_mock))
    monkeypatch.setattr(security_service, "ChannelLifecycleService", factory)
    return apply_mock


@pytest.mark.asyncio
async def test_apply_slowmode_routes_through_lifecycle_service(monkeypatch):
    apply_mock = _patch_service(monkeypatch)
    ch = _fake_channel()

    await security_service._apply_slowmode(ch, 30)

    apply_mock.assert_awaited_once()
    args, kwargs = apply_mock.await_args
    guild, request, actor = args[0], args[1], args[2]
    assert guild is ch.guild
    assert request.operation == "set_slowmode"
    assert request.channel_ids == (ch.id,)
    assert request.slowmode_seconds == 30
    assert actor is None  # automated raid response — no human actor
    assert kwargs.get("actor_type") == "system"


@pytest.mark.asyncio
async def test_apply_slowmode_no_guild_is_noop(monkeypatch):
    apply_mock = _patch_service(monkeypatch)
    ch = SimpleNamespace(id=1, guild=None)

    await security_service._apply_slowmode(ch, 30)

    apply_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_lift_lockdown_restores_via_service_and_clears_flag(monkeypatch):
    apply_mock = _patch_service(monkeypatch)
    ch = _fake_channel()
    security_service._locked_guilds.add(ch.guild.id)

    await security_service._lift_lockdown(ch.guild.id, ch, prior_slowmode=5)

    apply_mock.assert_awaited_once()
    request = apply_mock.await_args.args[1]
    assert request.operation == "set_slowmode"
    assert request.slowmode_seconds == 5
    # the lockdown flag is cleared in the finally block regardless
    assert ch.guild.id not in security_service._locked_guilds
