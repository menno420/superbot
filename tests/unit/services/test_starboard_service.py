"""Tests for services.starboard_service (idea B1 / PR 1).

Config writes audit (subsystem ``starboard``); the high-volume star path
(``handle_star_change``) decides post/edit/delete/none against authoritative DB
state and is **not** audited. CI-safe with no DB (the ``utils.db.starboard``
layer is mocked).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import starboard_service as svc


def _settings(*, channel_id=100, threshold=3, emoji="⭐", enabled=True) -> dict:
    return {
        "guild_id": 1,
        "channel_id": channel_id,
        "threshold": threshold,
        "emoji": emoji,
        "enabled": enabled,
    }


# ---------------------------------------------------------------------------
# Config writes (audited)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_configure_persists_and_audits():
    with (
        patch.object(svc.db, "set_settings", new=AsyncMock()) as set_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        stored = await svc.configure(
            guild_id=1,
            channel_id=200,
            threshold=5,
            actor_id=99,
        )
    assert stored == 5
    set_mock.assert_awaited_once_with(1, 200, threshold=5, emoji="⭐", enabled=True)
    kw = audit.await_args.kwargs
    assert kw["subsystem"] == "starboard"
    assert kw["mutation_type"] == "configure_starboard"
    assert kw["guild_id"] == 1
    assert kw["actor_id"] == 99


@pytest.mark.asyncio
async def test_configure_clamps_threshold_to_at_least_one():
    with (
        patch.object(svc.db, "set_settings", new=AsyncMock()) as set_mock,
        patch("services.audit_events.emit_audit_action", new=AsyncMock()),
    ):
        stored = await svc.configure(guild_id=1, channel_id=2, threshold=0, actor_id=9)
    assert stored == 1
    assert set_mock.await_args.kwargs["threshold"] == 1


@pytest.mark.asyncio
async def test_disable_flips_enabled_and_audits():
    with (
        patch.object(svc.db, "set_enabled", new=AsyncMock()) as set_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        await svc.disable(guild_id=1, actor_id=9)
    set_mock.assert_awaited_once_with(1, False)
    assert audit.await_args.kwargs["mutation_type"] == "disable_starboard"


@pytest.mark.asyncio
async def test_trigger_emoji_gates_on_enabled():
    with patch.object(svc.db, "get_settings", new=AsyncMock(return_value=None)):
        assert await svc.trigger_emoji(1) is None
    with patch.object(
        svc.db,
        "get_settings",
        new=AsyncMock(return_value=_settings(enabled=False)),
    ):
        assert await svc.trigger_emoji(1) is None
    with patch.object(
        svc.db,
        "get_settings",
        new=AsyncMock(return_value=_settings(emoji="✨")),
    ):
        assert await svc.trigger_emoji(1) == "✨"


# ---------------------------------------------------------------------------
# Star path — post / edit / delete / none (not audited)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_none_when_unconfigured():
    with patch.object(svc.db, "get_settings", new=AsyncMock(return_value=None)):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=10,
        )
    assert out.action == svc.NONE


@pytest.mark.asyncio
async def test_handle_none_for_the_starboard_channel_itself():
    with patch.object(
        svc.db,
        "get_settings",
        new=AsyncMock(return_value=_settings(channel_id=100)),
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=100,  # reacting in the hall-of-fame channel
            source_message_id=7,
            star_count=10,
        )
    assert out.action == svc.NONE


@pytest.mark.asyncio
async def test_handle_post_when_threshold_crossed_first_time():
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(channel_id=100, threshold=3)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=None)),
        patch.object(svc.db, "upsert_entry", new=AsyncMock()) as upsert,
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=3,
        )
    assert out.action == svc.POST
    assert out.channel_id == 100
    assert out.starboard_message_id is None
    upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_edit_when_already_posted():
    entry = {"starboard_message_id": 555, "star_count": 4}
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(threshold=3)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=entry)),
        patch.object(svc.db, "upsert_entry", new=AsyncMock()),
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=6,
        )
    assert out.action == svc.EDIT
    assert out.starboard_message_id == 555


@pytest.mark.asyncio
async def test_handle_delete_when_dropped_below_threshold():
    entry = {"starboard_message_id": 555, "star_count": 3}
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(threshold=3)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=entry)),
        patch.object(svc.db, "delete_entry", new=AsyncMock()) as delete,
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=2,
        )
    assert out.action == svc.DELETE
    assert out.starboard_message_id == 555
    delete.assert_awaited_once_with(1, 7)


@pytest.mark.asyncio
async def test_handle_none_below_threshold_and_never_posted():
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(threshold=5)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=None)),
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=2,
        )
    assert out.action == svc.NONE


@pytest.mark.asyncio
async def test_record_post_persists_message_id():
    with patch.object(svc.db, "upsert_entry", new=AsyncMock()) as upsert:
        await svc.record_post(1, 7, starboard_message_id=555, star_count=3)
    upsert.assert_awaited_once_with(
        1,
        7,
        star_count=3,
        starboard_message_id=555,
    )
