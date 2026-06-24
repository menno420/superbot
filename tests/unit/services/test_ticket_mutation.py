"""ticket_mutation — the audited open path's gate, delegation, and emissions.

Pins: an ineligible request opens nothing; a successful open delegates channel
creation to the lifecycle seam, inserts the row, and emits ``ticket.opened`` +
an audit companion after commit; claim refuses an already-claimed ticket.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import ticket_mutation as tm
from services import ticket_service as ts
from services.lifecycle import contracts as lc


def _cfg(**over):
    base = dict(
        guild_id=1,
        enabled=True,
        staff_role_id=99,
        category_id=None,
        log_channel_id=None,
        panel_channel_id=None,
        panel_message_id=None,
        max_open_per_user=1,
        ping_staff_on_open=True,
    )
    base.update(over)
    return ts.TicketConfig(**base)


def _guild():
    g = MagicMock()
    g.id = 1
    g.get_channel.return_value = MagicMock(name="created_channel")  # not a TextChannel
    return g


def _member(uid=2, name="bob"):
    m = MagicMock()
    m.id = uid
    m.display_name = name
    return m


@pytest.mark.asyncio
async def test_open_refused_when_ineligible(monkeypatch):
    monkeypatch.setattr(
        tm.ticket_service,
        "check_open_eligibility",
        AsyncMock(return_value=ts.OpenEligibility(False, ts.REASON_LIMIT_REACHED, 1, 1)),
    )
    create = AsyncMock()
    monkeypatch.setattr(
        tm, "ChannelLifecycleService", MagicMock(return_value=MagicMock(create_channels=create))
    )
    db_create = AsyncMock()
    monkeypatch.setattr(tm.db, "ticket_create", db_create)

    result = await tm.open_ticket(_guild(), _member(), "help me")

    assert not result.success
    assert result.reason == ts.REASON_LIMIT_REACHED
    create.assert_not_awaited()
    db_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_success_delegates_creates_row_and_emits(monkeypatch):
    monkeypatch.setattr(
        tm.ticket_service,
        "check_open_eligibility",
        AsyncMock(return_value=ts.OpenEligibility(True, ts.REASON_OK, 0, 1)),
    )
    monkeypatch.setattr(tm.ticket_service, "get_config", AsyncMock(return_value=_cfg()))

    lifecycle_result = lc.LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="create",
        outcome=lc.SUCCESS,
        reversibility=lc.COMPENSATABLE,
        steps=(lc.StepResult(target_id=555, target_name="ticket-bob", ok=True),),
    )
    create = AsyncMock(return_value=lifecycle_result)
    monkeypatch.setattr(
        tm, "ChannelLifecycleService", MagicMock(return_value=MagicMock(create_channels=create))
    )

    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="conn")

    monkeypatch.setattr(tm.db, "transaction", _txn)
    monkeypatch.setattr(tm.db, "ticket_create", AsyncMock(return_value=7))

    emitted: list[tuple] = []

    async def _emit(event, **payload):
        emitted.append((event, payload))

    monkeypatch.setattr(tm.bus, "emit", _emit)
    audit = AsyncMock(return_value=True)
    monkeypatch.setattr(tm, "emit_audit_action", audit)

    result = await tm.open_ticket(_guild(), _member(), "  need   help  ", source="ai")

    assert result.success
    assert result.ticket_id == 7
    assert result.channel_id == 555
    assert "<#555>" in result.message
    create.assert_awaited_once()
    audit.assert_awaited_once()
    assert any(e == "ticket.opened" for e, _ in emitted)
    # subject is whitespace-normalised
    _, payload = next(p for p in emitted if p[0] == "ticket.opened")
    assert payload["subject"] == "need help"
    assert payload["source"] == "ai"


@pytest.mark.asyncio
async def test_open_failure_when_channel_creation_blocked(monkeypatch):
    monkeypatch.setattr(
        tm.ticket_service,
        "check_open_eligibility",
        AsyncMock(return_value=ts.OpenEligibility(True, ts.REASON_OK, 0, 1)),
    )
    monkeypatch.setattr(tm.ticket_service, "get_config", AsyncMock(return_value=_cfg()))
    blocked = lc.LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="create",
        outcome=lc.BLOCKED,
        reversibility=lc.COMPENSATABLE,
        steps=(),
    )
    monkeypatch.setattr(
        tm,
        "ChannelLifecycleService",
        MagicMock(return_value=MagicMock(create_channels=AsyncMock(return_value=blocked))),
    )
    db_create = AsyncMock()
    monkeypatch.setattr(tm.db, "ticket_create", db_create)

    result = await tm.open_ticket(_guild(), _member(), "help")
    assert not result.success
    assert result.reason == "channel_failed"
    db_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_claim_rejects_already_claimed():
    out = await tm.claim_ticket(
        {"id": 1, "guild_id": 1, "status": "open", "claimed_by": 42}, _member(uid=7)
    )
    assert not out.success
    assert "claimed" in out.message.lower()


@pytest.mark.asyncio
async def test_claim_rejects_closed_ticket():
    out = await tm.claim_ticket(
        {"id": 1, "guild_id": 1, "status": "closed", "claimed_by": None}, _member(uid=7)
    )
    assert not out.success


# --------------------------------------------------------------------------- #
# create_log_channel — the auto-create-log-channel setup button's service seam
# --------------------------------------------------------------------------- #


def _autocreate_guild(channel):
    g = MagicMock()
    g.id = 1
    g.default_role = MagicMock(name="everyone")
    g.me = MagicMock(name="me")
    g.get_channel.return_value = channel
    return g


def _lifecycle(outcome, *, target_id=4242):
    return lc.LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="create",
        outcome=outcome,
        reversibility=lc.COMPENSATABLE,
        steps=(
            lc.StepResult(target_id=target_id, target_name="ticket-transcripts", ok=True),
        )
        if outcome == lc.SUCCESS
        else (),
    )


@pytest.mark.asyncio
async def test_create_log_channel_creates_via_seam_locks_down_sets_config(monkeypatch):
    import discord

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 4242
    channel.mention = "#ticket-transcripts"
    channel.edit = AsyncMock()
    guild = _autocreate_guild(channel)

    create = AsyncMock(return_value=_lifecycle(lc.SUCCESS))
    monkeypatch.setattr(
        tm,
        "ChannelLifecycleService",
        MagicMock(return_value=MagicMock(create_channels=create)),
    )
    monkeypatch.setattr(
        tm.guild_resources, "resolve_role", lambda *a, **k: MagicMock(name="staff")
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(tm, "update_config", update_mock)

    result = await tm.create_log_channel(guild, 7, staff_role_id=99)

    assert result.success is True
    assert result.channel_id == 4242
    # Created through the audited lifecycle seam, not a raw guild.create_*.
    create.assert_awaited_once()
    # Locked down staff-only: @everyone denied view.
    channel.edit.assert_awaited_once()
    overwrites = channel.edit.await_args.kwargs["overwrites"]
    assert guild.default_role in overwrites
    # Config updated through the audited update_config seam.
    update_mock.assert_awaited_once_with(1, 7, log_channel_id=4242)


@pytest.mark.asyncio
async def test_create_log_channel_handles_creation_blocked(monkeypatch):
    guild = _autocreate_guild(None)
    create = AsyncMock(return_value=_lifecycle(lc.BLOCKED))
    monkeypatch.setattr(
        tm,
        "ChannelLifecycleService",
        MagicMock(return_value=MagicMock(create_channels=create)),
    )
    update_mock = AsyncMock()
    monkeypatch.setattr(tm, "update_config", update_mock)

    result = await tm.create_log_channel(guild, 7, staff_role_id=None)

    assert result.success is False
    assert "Manage Channels" in result.message
    update_mock.assert_not_awaited()
