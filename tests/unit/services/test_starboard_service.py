"""Tests for services.starboard_service (idea B1 / PR 1 + PR 2).

Config writes audit (subsystem ``starboard``); the high-volume star path
(``handle_star_change``) decides post/edit/delete/none against authoritative DB
state and is **not** audited. CI-safe with no DB (the ``utils.db.starboard``
layer is mocked). PR 2 adds the self-star policy + ignore-channel gate.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest

from services import starboard_service as svc


def _settings(
    *, channel_id=100, threshold=3, emoji="⭐", enabled=True, self_star=False
) -> dict:
    return {
        "guild_id": 1,
        "channel_id": channel_id,
        "threshold": threshold,
        "emoji": emoji,
        "enabled": enabled,
        "self_star": self_star,
    }


@contextmanager
def _no_ignores():
    """Patch the ignore-channel read to an empty set (the common-path default)."""
    with patch.object(
        svc.db, "list_ignore_channels", new=AsyncMock(return_value=set())
    ):
        yield


# ---------------------------------------------------------------------------
# Config writes (audited)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_configure_persists_and_audits():
    with (
        patch.object(svc.db, "get_settings", new=AsyncMock(return_value=None)),
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
    set_mock.assert_awaited_once_with(
        1, 200, threshold=5, emoji="⭐", enabled=True, self_star=False
    )
    kw = audit.await_args.kwargs
    assert kw["subsystem"] == "starboard"
    assert kw["mutation_type"] == "configure_starboard"
    assert kw["guild_id"] == 1
    assert kw["actor_id"] == 99


@pytest.mark.asyncio
async def test_configure_preserves_existing_self_star():
    """Re-pointing the channel must not reset the self-star toggle."""
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(self_star=True)),
        ),
        patch.object(svc.db, "set_settings", new=AsyncMock()) as set_mock,
        patch("services.audit_events.emit_audit_action", new=AsyncMock()),
    ):
        await svc.configure(guild_id=1, channel_id=200, threshold=5, actor_id=9)
    assert set_mock.await_args.kwargs["self_star"] is True


@pytest.mark.asyncio
async def test_configure_clamps_threshold_to_at_least_one():
    with (
        patch.object(svc.db, "get_settings", new=AsyncMock(return_value=None)),
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
async def test_set_self_star_persists_and_audits():
    with (
        patch.object(svc.db, "set_self_star", new=AsyncMock()) as set_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        await svc.set_self_star(guild_id=1, self_star=True, actor_id=9)
    set_mock.assert_awaited_once_with(1, True)
    kw = audit.await_args.kwargs
    assert kw["mutation_type"] == "set_starboard_self_star"
    assert kw["new_value"] == "self_star=True"


@pytest.mark.asyncio
async def test_add_and_remove_ignore_channel_audit():
    with (
        patch.object(svc.db, "add_ignore_channel", new=AsyncMock()) as add_mock,
        patch.object(svc.db, "remove_ignore_channel", new=AsyncMock()) as rm_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit,
    ):
        await svc.add_ignore_channel(guild_id=1, channel_id=42, actor_id=9)
        assert (
            audit.await_args.kwargs["mutation_type"] == "add_starboard_ignore_channel"
        )
        await svc.remove_ignore_channel(guild_id=1, channel_id=42, actor_id=9)
        assert (
            audit.await_args.kwargs["mutation_type"]
            == "remove_starboard_ignore_channel"
        )
    add_mock.assert_awaited_once_with(1, 42)
    rm_mock.assert_awaited_once_with(1, 42)


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
async def test_handle_none_for_an_ignored_channel():
    with (
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(channel_id=100)),
        ),
        patch.object(svc.db, "list_ignore_channels", new=AsyncMock(return_value={5})),
        patch.object(svc.db, "get_entry", new=AsyncMock()) as get_entry,
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,  # on the ignore list
            source_message_id=7,
            star_count=10,
        )
    assert out.action == svc.NONE
    get_entry.assert_not_awaited()  # gated before the entry read


@pytest.mark.asyncio
async def test_handle_post_when_threshold_crossed_first_time():
    with (
        _no_ignores(),
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
async def test_self_star_excluded_keeps_below_threshold():
    """3 stars but one is the author's own → effective 2 < threshold 3 → NONE."""
    with (
        _no_ignores(),
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(threshold=3, self_star=False)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=None)),
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=3,
            author_starred=True,
        )
    assert out.action == svc.NONE
    assert out.star_count == 2  # the displayed count excludes the self-star


@pytest.mark.asyncio
async def test_self_star_counted_when_enabled():
    """Same 3 stars, but self_star is on → effective 3 ≥ 3 → POST."""
    with (
        _no_ignores(),
        patch.object(
            svc.db,
            "get_settings",
            new=AsyncMock(return_value=_settings(threshold=3, self_star=True)),
        ),
        patch.object(svc.db, "get_entry", new=AsyncMock(return_value=None)),
        patch.object(svc.db, "upsert_entry", new=AsyncMock()),
    ):
        out = await svc.handle_star_change(
            guild_id=1,
            source_channel_id=5,
            source_message_id=7,
            star_count=3,
            author_starred=True,
        )
    assert out.action == svc.POST
    assert out.star_count == 3


@pytest.mark.asyncio
async def test_handle_edit_when_already_posted():
    entry = {"starboard_message_id": 555, "star_count": 4}
    with (
        _no_ignores(),
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
        _no_ignores(),
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
        _no_ignores(),
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
