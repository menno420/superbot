"""Unit tests for services.server_logging — Phase 2 PR-11."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import server_logging
from services.server_logging import (
    _channel_kind_for_action,
    _on_moderation_action_public,
    _root_action,
    auto_create_enabled,
    counters_snapshot,
    ensure_log_channel,
    format_log_embed,
    format_public_log_embed,
    is_enabled,
    log_event,
    maybe_log_public,
    resolve_log_channel,
)


@pytest.fixture(autouse=True)
def _reset_counters():
    server_logging._reset_for_tests()
    yield
    server_logging._reset_for_tests()


def _make_guild(guild_id: int = 99999) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = f"guild-{guild_id}"
    guild.me = MagicMock()
    return guild


def _make_text_channel(channel_id: int = 12345, name: str = "logs") -> MagicMock:
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.mention = f"<#{channel_id}>"
    channel.send = AsyncMock()
    return channel


# ---------------------------------------------------------------------------
# Config accessors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_enabled_reads_setting():
    with patch(
        "services.server_logging.db.get_setting",
        new_callable=AsyncMock,
        return_value="true",
    ) as get_setting:
        assert await is_enabled(123) is True
    get_setting.assert_awaited_once()
    assert get_setting.await_args.args[:2] == (123, "logging_enabled")


@pytest.mark.asyncio
async def test_is_enabled_defaults_to_false_when_unset():
    with patch(
        "services.server_logging.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        assert await is_enabled(123) is False


@pytest.mark.asyncio
async def test_is_enabled_accepts_truthy_literals():
    for val in ("true", "1", "yes", "on", "enabled", "TRUE", "Yes"):
        with patch(
            "services.server_logging.db.get_setting",
            new_callable=AsyncMock,
            return_value=val,
        ):
            assert await is_enabled(123) is True, f"Expected truthy: {val!r}"


@pytest.mark.asyncio
async def test_auto_create_enabled_reads_setting():
    with patch(
        "services.server_logging.db.get_setting",
        new_callable=AsyncMock,
        return_value="true",
    ) as get_setting:
        assert await auto_create_enabled(123) is True
    assert get_setting.await_args.args[:2] == (123, "logging_auto_create_channels")


# ---------------------------------------------------------------------------
# Action → channel routing
# ---------------------------------------------------------------------------


def test_channel_kind_for_action_routes_auto_delete_to_cleanup():
    assert _channel_kind_for_action("auto_delete:cleanup.foo") == "cleanup"


def test_channel_kind_for_action_routes_mod_actions_to_mod():
    # "clearwarnings" (one word) is the canonical token moderation_service emits;
    # "clear_warnings" stays in the loop as a back-compat alias.
    for action in ("warn", "timeout", "kick", "ban", "unban", "clearwarnings", "clear_warnings"):
        assert _channel_kind_for_action(action) == "mod"


def test_root_action_strips_composite_suffix():
    assert _root_action("auto_delete:cleanup.prohibited_words") == "auto_delete"
    assert _root_action("warn") == "warn"


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------


def test_format_log_embed_warn_uses_gold():
    embed = format_log_embed(
        action="warn",
        guild_id=99,
        target_id=42,
        actor_id=7,
        reason="spam",
    )
    assert embed.color == discord.Color.gold()
    assert "warn" in (embed.title or "")
    field_names = [f.name for f in embed.fields]
    assert "Target" in field_names
    assert "Actor" in field_names
    assert "Reason" in field_names


def test_format_log_embed_auto_delete_uses_dark_grey():
    embed = format_log_embed(
        action="auto_delete:cleanup.prohibited_words",
        guild_id=99,
        target_id=42,
        actor_id=None,
        reason="bad word",
    )
    assert embed.color == discord.Color.dark_grey()
    # Action title preserves the composite form so dashboards can
    # tell which rule triggered.
    assert "auto_delete:cleanup.prohibited_words" in (embed.title or "")


def test_format_log_embed_clearwarnings_uses_blurple():
    # Regression guard: moderation_service emits the one-word "clearwarnings"
    # token (server-management PR1), so the style map must recognise it rather
    # than fall through to the generic dark-grey style.
    embed = format_log_embed(
        action="clearwarnings",
        guild_id=99,
        target_id=42,
        actor_id=7,
        reason="reset",
    )
    assert embed.color == discord.Color.blurple()
    assert "🧹" in (embed.title or "")


def test_format_log_embed_unknown_action_uses_generic_style():
    embed = format_log_embed(
        action="future_unknown_action",
        guild_id=99,
        target_id=42,
        actor_id=7,
        reason="reason",
    )
    assert embed.color == discord.Color.dark_grey()


def test_format_log_embed_system_actor_displayed_when_actor_none():
    embed = format_log_embed(
        action="auto_delete:cleanup.x",
        guild_id=1,
        target_id=2,
        actor_id=None,
        reason="r",
    )
    actor_field = next(f for f in embed.fields if f.name == "Actor")
    assert actor_field.value == "system"


def test_format_log_embed_extras_rendered_as_fields():
    embed = format_log_embed(
        action="timeout",
        guild_id=1,
        target_id=2,
        actor_id=3,
        reason="r",
        extras={"until": "2026-12-31T00:00:00+00:00"},
    )
    field_names = [f.name for f in embed.fields]
    assert "until" in field_names


def test_format_log_embed_reason_truncated_at_1000_chars():
    embed = format_log_embed(
        action="warn",
        guild_id=1,
        target_id=2,
        actor_id=3,
        reason="x" * 5000,
    )
    reason_field = next(f for f in embed.fields if f.name == "Reason")
    assert len(reason_field.value) <= 1000


def test_format_log_embed_caps_extras_at_max_fields():
    """A malformed event payload must not push the embed past Discord's
    25-field cap; extras beyond _MAX_EXTRA_FIELDS are replaced with a
    single '... truncated' summary field."""
    big_extras = {f"k{i}": f"v{i}" for i in range(20)}
    embed = format_log_embed(
        action="warn",
        guild_id=1,
        target_id=2,
        actor_id=3,
        reason="r",
        extras=big_extras,
    )
    truncated_fields = [f for f in embed.fields if f.name == "… truncated"]
    assert len(truncated_fields) == 1
    # 4 base fields (Target/Actor/Guild/Reason) + 6 capped extras + 1 truncation note.
    assert len(embed.fields) == 11
    assert "14" in truncated_fields[0].value  # 20 - 6 = 14 dropped


def test_format_log_embed_no_truncation_field_when_under_cap():
    embed = format_log_embed(
        action="warn",
        guild_id=1,
        target_id=2,
        actor_id=3,
        reason="r",
        extras={"until": "2026-12-31T00:00:00+00:00"},
    )
    assert all(f.name != "… truncated" for f in embed.fields)


def test_format_log_embed_extra_value_truncated_at_cap():
    embed = format_log_embed(
        action="warn",
        guild_id=1,
        target_id=2,
        actor_id=3,
        reason="r",
        extras={"context": "z" * 5000},
    )
    ctx_field = next(f for f in embed.fields if f.name == "context")
    assert len(ctx_field.value) <= 500


# ---------------------------------------------------------------------------
# Subject avatar — the mod-log embed matches the passive-event embeds
# ---------------------------------------------------------------------------


def _subject(name: str = "TargetUser", url: str = "https://cdn.example/t.png") -> MagicMock:
    s = MagicMock()
    s.display_name = name
    s.display_avatar = MagicMock()
    s.display_avatar.url = url
    return s


def test_format_log_embed_subject_sets_author_avatar():
    embed = format_log_embed(
        action="ban",
        guild_id=1,
        target_id=7,
        actor_id=2,
        reason="x",
        subject=_subject(),
    )
    assert embed.author.name == "TargetUser"
    assert embed.author.icon_url == "https://cdn.example/t.png"


def test_format_log_embed_without_subject_has_no_author():
    embed = format_log_embed(action="ban", guild_id=1, target_id=7, actor_id=2, reason="x")
    assert embed.author.name is None


def test_format_public_log_embed_subject_sets_author_avatar():
    embed = format_public_log_embed(action="ban", target_id=7, reason="x", subject=_subject())
    assert embed.author.name == "TargetUser"


def test_resolve_subject_user_prefers_guild_member():
    guild = _make_guild()
    member = _subject()
    guild.get_member = MagicMock(return_value=member)
    assert server_logging._resolve_subject_user(guild, 7) is member


def test_resolve_subject_user_falls_back_to_bot_user_cache():
    # A just-banned member is gone from the guild cache but still in the bot's
    # global user cache — so bans/kicks still get a face.
    guild = _make_guild()
    guild.get_member = MagicMock(return_value=None)
    user = _subject()
    fake_bot = MagicMock()
    fake_bot.get_user = MagicMock(return_value=user)
    server_logging._BOT = fake_bot
    try:
        assert server_logging._resolve_subject_user(guild, 7) is user
    finally:
        server_logging._BOT = None


def test_resolve_subject_user_none_when_unresolvable_or_no_id():
    guild = _make_guild()
    guild.get_member = MagicMock(return_value=None)
    server_logging._BOT = None
    assert server_logging._resolve_subject_user(guild, 7) is None
    assert server_logging._resolve_subject_user(guild, None) is None


# ---------------------------------------------------------------------------
# resolve_log_channel
# ---------------------------------------------------------------------------


def _unbound_binding() -> MagicMock:
    """Helper: a get_binding return value with no target set."""
    b = MagicMock()
    b.target_id = None
    return b


@pytest.mark.asyncio
async def test_resolve_log_channel_mod_returns_text_channel():
    guild = _make_guild()
    channel = _make_text_channel(name="mod-log")
    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        result = await resolve_log_channel(guild, "mod")
    assert result is channel


@pytest.mark.asyncio
async def test_resolve_log_channel_cleanup_falls_back_to_mod():
    guild = _make_guild()
    mod_channel = _make_text_channel(name="mod-log")
    calls: list[str] = []

    async def fake_resolve(_guild, key: str):
        calls.append(key)
        if key == "logging_cleanup_channel":
            return None
        if key == "logging_mod_channel":
            return mod_channel
        return None

    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        side_effect=fake_resolve,
    ):
        result = await resolve_log_channel(guild, "cleanup")
    assert result is mod_channel
    # Looked at cleanup first, then mod (both legacy fallbacks since
    # the binding mock returns unbound for both).
    assert calls == ["logging_cleanup_channel", "logging_mod_channel"]


@pytest.mark.asyncio
async def test_resolve_log_channel_returns_none_when_setting_unset():
    guild = _make_guild()
    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await resolve_log_channel(guild, "mod") is None


@pytest.mark.asyncio
async def test_resolve_log_channel_skips_non_text_channel():
    guild = _make_guild()
    voice = MagicMock(spec=discord.VoiceChannel)
    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=voice,
    ):
        assert await resolve_log_channel(guild, "mod") is None


# ---------------------------------------------------------------------------
# Phase 9a — severity / audit route resolution
# ---------------------------------------------------------------------------


def _bound_binding(channel_id: int) -> MagicMock:
    b = MagicMock()
    b.target_id = channel_id
    return b


@pytest.mark.parametrize(
    "kind,binding_name",
    [
        ("debug", "debug_channel"),
        ("info", "info_channel"),
        ("warning", "warning_channel"),
        ("error", "error_channel"),
        ("audit", "audit_channel"),
    ],
    ids=["debug", "info", "warning", "error", "audit"],
)
@pytest.mark.asyncio
async def test_resolve_log_channel_severity_route_returns_own_binding(
    kind: str,
    binding_name: str,
):
    """Each Phase 9a route resolves to its own binding when set."""
    guild = _make_guild()
    own_channel = _make_text_channel(name=f"bot-{kind}-log")
    guild.get_channel = MagicMock(return_value=own_channel)

    seen: list[tuple[str, str]] = []

    async def fake_get_binding(_gid, subsystem, name, expected_kind=None):
        seen.append((subsystem, name))
        if name == binding_name:
            return _bound_binding(channel_id=own_channel.id)
        return _unbound_binding()

    with patch(
        "core.runtime.bindings.get_binding",
        side_effect=fake_get_binding,
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await resolve_log_channel(guild, kind)

    assert result is own_channel
    # The route's own binding was queried first.
    assert seen[0] == ("logging", binding_name)


@pytest.mark.parametrize(
    "kind",
    ["debug", "info", "warning", "error", "audit"],
)
@pytest.mark.asyncio
async def test_resolve_log_channel_severity_route_falls_back_to_mod(kind: str):
    """When the route's own binding is unset, fall through to the mod binding."""
    guild = _make_guild()
    mod_channel = _make_text_channel(name="bot-mod-log")
    guild.get_channel = MagicMock(return_value=mod_channel)

    seen: list[tuple[str, str]] = []

    async def fake_get_binding(_gid, subsystem, name, expected_kind=None):
        seen.append((subsystem, name))
        if name == "mod_channel":
            return _bound_binding(channel_id=mod_channel.id)
        return _unbound_binding()

    with patch(
        "core.runtime.bindings.get_binding",
        side_effect=fake_get_binding,
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await resolve_log_channel(guild, kind)

    assert result is mod_channel
    # The own binding was checked first, then the fallback hit mod.
    binding_names_queried = [name for _, name in seen]
    assert binding_names_queried[0] != "mod_channel"
    assert "mod_channel" in binding_names_queried


@pytest.mark.parametrize(
    "kind",
    ["debug", "info", "warning", "error", "audit"],
)
@pytest.mark.asyncio
async def test_resolve_log_channel_severity_route_returns_none_when_all_unset(
    kind: str,
):
    """No own binding, no mod binding, no legacy → None."""
    guild = _make_guild()
    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await resolve_log_channel(guild, kind) is None


@pytest.mark.asyncio
async def test_resolve_log_channel_unknown_kind_returns_none():
    """Unknown route tokens don't raise — they log a warning and return None."""
    guild = _make_guild()
    with patch(
        "core.runtime.bindings.get_binding",
        new_callable=AsyncMock,
        return_value=_unbound_binding(),
    ), patch(
        "core.runtime.guild_resources.resolve_settings_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await resolve_log_channel(guild, "not_a_real_kind") is None


def test_phase_9a_route_table_is_complete_and_acyclic():
    """Pin the route table shape so a future edit doesn't silently
    drop a route or introduce a fallback cycle.

    The set covers the Phase-9a moderation/severity/audit routes plus the
    server-event-logging v1 routes (events + per-category). Every chain
    terminates at a ``None`` fallback (``mod`` for the severity tier,
    ``events`` for the event tier).
    """
    from services.server_logging import _ROUTE_FALLBACK, _ROUTE_TO_BINDING

    expected = {
        "mod",
        "cleanup",
        "debug",
        "info",
        "warning",
        "error",
        "audit",
        "events",
        "message_log",
        "member_log",
        "role_log",
    }
    assert set(_ROUTE_TO_BINDING) == expected
    assert set(_ROUTE_FALLBACK) == expected
    # Acyclic: walking ``_ROUTE_FALLBACK`` from any starting kind must
    # terminate at a None fallback within at most len(expected) hops.
    for start in expected:
        seen_chain: list[str] = []
        cursor: str | None = start
        for _ in range(len(expected) + 1):
            if cursor is None:
                break
            assert cursor not in seen_chain, (
                f"_ROUTE_FALLBACK has a cycle starting at {start!r}: "
                f"{seen_chain + [cursor]}"
            )
            seen_chain.append(cursor)
            cursor = _ROUTE_FALLBACK[cursor]
        else:
            raise AssertionError(
                f"_ROUTE_FALLBACK chain from {start!r} did not terminate: {seen_chain}"
            )


# ---------------------------------------------------------------------------
# ensure_log_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_log_channel_returns_existing_when_resolved():
    guild = _make_guild()
    channel = _make_text_channel()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ), patch(
        "core.runtime.guild_resources.ensure_channel",
        new_callable=AsyncMock,
    ) as ensure:
        result = await ensure_log_channel(guild, "mod")
    assert result is channel
    ensure.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_log_channel_creates_when_resolve_fails():
    guild = _make_guild()
    created = _make_text_channel(name="bot-mod-log")
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "core.runtime.guild_resources.ensure_channel",
        new_callable=AsyncMock,
        return_value=created,
    ):
        result = await ensure_log_channel(guild, "mod")
    assert result is created
    assert counters_snapshot()["counters"]["created_channel"] == 1


@pytest.mark.asyncio
async def test_ensure_log_channel_counts_permission_error_on_forbidden():
    guild = _make_guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "core.runtime.guild_resources.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.Forbidden(MagicMock(status=403), "no perms"),
    ):
        result = await ensure_log_channel(guild, "mod")
    assert result is None
    assert counters_snapshot()["counters"]["permission_error"] == 1


@pytest.mark.asyncio
async def test_ensure_log_channel_counts_auto_create_error_on_http():
    guild = _make_guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "core.runtime.guild_resources.ensure_channel",
        new_callable=AsyncMock,
        side_effect=discord.HTTPException(MagicMock(status=500), "bad"),
    ):
        result = await ensure_log_channel(guild, "mod")
    assert result is None
    assert counters_snapshot()["counters"]["auto_create_error"] == 1


# ---------------------------------------------------------------------------
# log_event — the main orchestrator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_event_skipped_when_disabled():
    guild = _make_guild()
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ):
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is False
    assert counters_snapshot()["counters"]["skipped_disabled"] == 1


@pytest.mark.asyncio
async def test_log_event_sends_embed_when_configured():
    guild = _make_guild()
    channel = _make_text_channel()
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is True
    channel.send.assert_awaited_once()
    embed = channel.send.await_args.kwargs["embed"]
    assert isinstance(embed, discord.Embed)
    assert counters_snapshot()["counters"]["sent_total"] == 1


@pytest.mark.asyncio
async def test_log_event_missing_channel_when_auto_create_off():
    guild = _make_guild()
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "services.server_logging.auto_create_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "services.server_logging.ensure_log_channel",
        new_callable=AsyncMock,
    ) as ensure_lc:
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is False
    ensure_lc.assert_not_awaited()
    assert counters_snapshot()["counters"]["missing_channel"] == 1


@pytest.mark.asyncio
async def test_log_event_missing_channel_calls_ensure_when_auto_create_on():
    guild = _make_guild()
    created = _make_text_channel(name="bot-mod-log")
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "services.server_logging.auto_create_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.ensure_log_channel",
        new_callable=AsyncMock,
        return_value=created,
    ) as ensure_lc:
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is True
    ensure_lc.assert_awaited_once()
    created.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_event_swallows_permission_error_on_send():
    guild = _make_guild()
    channel = _make_text_channel()
    channel.send = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(status=403), "no perms"),
    )
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is False
    assert counters_snapshot()["counters"]["permission_error"] == 1


@pytest.mark.asyncio
async def test_log_event_swallows_http_error_on_send():
    guild = _make_guild()
    channel = _make_text_channel()
    channel.send = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(status=500), "boom"),
    )
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is False
    assert counters_snapshot()["counters"]["send_error"] == 1


@pytest.mark.asyncio
async def test_log_event_swallows_unexpected_exception_on_send():
    guild = _make_guild()
    channel = _make_text_channel()
    channel.send = AsyncMock(side_effect=RuntimeError("anything"))
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await log_event(
            guild,
            action="warn",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is False
    assert counters_snapshot()["counters"]["send_error"] == 1


@pytest.mark.asyncio
async def test_log_event_renders_unknown_action_safely():
    guild = _make_guild()
    channel = _make_text_channel()
    with patch(
        "services.server_logging.is_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await log_event(
            guild,
            action="some_future_action",
            target_id=1,
            actor_id=2,
            reason="r",
        )
    assert sent is True
    channel.send.assert_awaited_once()
    embed = channel.send.await_args.kwargs["embed"]
    assert embed.color == discord.Color.dark_grey()


# ---------------------------------------------------------------------------
# Subscriber path — _on_moderation_action
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_skipped_when_bot_unset():
    server_logging._BOT = None
    await server_logging._on_moderation_action(
        guild_id=1,
        target_id=2,
        actor_id=3,
        action="warn",
        reason="r",
    )
    assert counters_snapshot()["counters"]["skipped_no_guild"] == 1


@pytest.mark.asyncio
async def test_subscriber_skipped_when_guild_not_cached():
    fake_bot = MagicMock()
    fake_bot.get_guild = MagicMock(return_value=None)
    server_logging._BOT = fake_bot
    await server_logging._on_moderation_action(
        guild_id=999,
        target_id=2,
        actor_id=3,
        action="warn",
        reason="r",
    )
    assert counters_snapshot()["counters"]["skipped_no_guild"] == 1


@pytest.mark.asyncio
async def test_subscriber_delegates_to_log_event():
    fake_bot = MagicMock()
    guild = _make_guild()
    fake_bot.get_guild = MagicMock(return_value=guild)
    server_logging._BOT = fake_bot

    with patch(
        "services.server_logging.log_event",
        new_callable=AsyncMock,
    ) as log_event_mock:
        await server_logging._on_moderation_action(
            guild_id=guild.id,
            target_id=42,
            actor_id=7,
            action="warn",
            reason="spam",
        )

    log_event_mock.assert_awaited_once()
    kwargs = log_event_mock.await_args.kwargs
    assert kwargs["action"] == "warn"
    assert kwargs["target_id"] == 42
    assert kwargs["actor_id"] == 7
    assert kwargs["reason"] == "spam"


@pytest.mark.asyncio
async def test_subscriber_passes_extras_through():
    fake_bot = MagicMock()
    guild = _make_guild()
    fake_bot.get_guild = MagicMock(return_value=guild)
    server_logging._BOT = fake_bot

    with patch(
        "services.server_logging.log_event",
        new_callable=AsyncMock,
    ) as log_event_mock:
        await server_logging._on_moderation_action(
            guild_id=guild.id,
            target_id=42,
            actor_id=7,
            action="timeout",
            reason="cooldown",
            until="2026-12-31T00:00:00+00:00",
        )

    extras = log_event_mock.await_args.kwargs["extras"]
    assert extras == {"until": "2026-12-31T00:00:00+00:00"}


@pytest.mark.asyncio
async def test_subscriber_counts_unexpected_exception():
    fake_bot = MagicMock()
    fake_bot.get_guild = MagicMock(side_effect=RuntimeError("kaboom"))
    server_logging._BOT = fake_bot
    await server_logging._on_moderation_action(
        guild_id=1,
        target_id=2,
        actor_id=3,
        action="warn",
        reason="r",
    )
    assert counters_snapshot()["counters"]["subscriber_errors"] == 1


# ---------------------------------------------------------------------------
# setup() — bus subscription
# ---------------------------------------------------------------------------


def test_setup_registers_bus_handler_idempotently():
    from core.events import bus

    # Capture handler count before & after.  setup() may have been
    # called by the module import via fixture autouse=False; we test
    # the idempotency invariant from a known-zero state.  Two handlers
    # are registered on EVT_MOD_ACTION: the staff log + the public mirror
    # (server-management PR10); a second setup() must not re-register either.
    bus._handlers.get(server_logging.EVT_MOD_ACTION, []).clear()
    server_logging._SUBSCRIBED = False
    server_logging.setup(MagicMock())
    server_logging.setup(MagicMock())  # second call must not re-register
    handlers = bus._handlers.get(server_logging.EVT_MOD_ACTION, [])
    assert len(handlers) == 2


def test_setup_captures_bot_reference():
    server_logging._SUBSCRIBED = False
    server_logging._BOT = None
    fake_bot = MagicMock()
    server_logging.setup(fake_bot)
    assert server_logging._BOT is fake_bot


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


def test_counters_snapshot_has_stable_shape():
    snap = counters_snapshot()
    assert "counters" in snap
    assert "subscribed_events" in snap
    counters = snap["counters"]
    expected_keys = {
        "sent_total",
        "skipped_disabled",
        "skipped_no_guild",
        "missing_channel",
        "created_channel",
        "permission_error",
        "send_error",
        "auto_create_error",
        "subscriber_errors",
    }
    assert expected_keys <= set(counters)
    for v in counters.values():
        assert isinstance(v, int)
    # Phase 9c.1 added the audit subscriber alongside the moderation
    # subscriber. The list is part of the public snapshot shape — pin
    # both members but keep order-insensitive matching so a future
    # addition (debug/info/warning/error in 9c.3/9c.4) doesn't break
    # this guard.
    assert set(snap["subscribed_events"]) == {
        "moderation.action_taken",
        "audit.action_recorded",
    }


def test_diagnostics_service_registers_server_logging_provider():
    from services import diagnostics_service

    # The module-level _register_diagnostics() call runs at import.
    snap = diagnostics_service.snapshot("server_logging")
    assert "counters" in snap


def test_counters_snapshot_returns_copy_not_live_dict():
    snap = counters_snapshot()
    snap["counters"]["sent_total"] = 999_999
    again = counters_snapshot()
    assert again["counters"]["sent_total"] != 999_999


# ---------------------------------------------------------------------------
# Event catalogue check
# ---------------------------------------------------------------------------


def test_subscribed_event_is_catalogued():
    from core.events_catalogue import KNOWN_EVENTS

    assert server_logging.EVT_MOD_ACTION in KNOWN_EVENTS


# ---------------------------------------------------------------------------
# No top-level core.runtime imports (cycle safety)
# ---------------------------------------------------------------------------


def test_module_source_has_no_top_level_cycle_imports():
    """Server-logging service must keep core.runtime imports inside
    function bodies so loading the service module during startup
    never re-enters a partially-loaded core.runtime.  utils.db is
    safe at module scope (mirrors moderation_service pattern)."""
    src = Path(server_logging.__file__).read_text()
    # Naive top-of-file scan — anything inside a def/class is fine.
    head = src.split("\n\nasync def", 1)[0].split("\n\ndef ", 1)[0]
    forbidden = ("from core.runtime", "from utils.subsystem_registry")
    for token in forbidden:
        assert token not in head, (
            f"Top-level import of {token!r} would re-enter the "
            f"partially-loaded core.runtime during startup; move it "
            f"inside the function that needs it."
        )


# ---------------------------------------------------------------------------
# Optional public moderation log (server-management PR10) — separate
# subscriber, moderator-name redacted, gated by the moderation policy.
# ---------------------------------------------------------------------------


def test_public_embed_redacts_the_moderator():
    """The public embed shows the member + reason but never the acting mod."""
    embed = format_public_log_embed(action="ban", target_id=42, reason="raiding")
    field_names = [f.name for f in embed.fields]
    assert "Member" in field_names
    assert "Reason" in field_names
    # The acting moderator must NOT appear anywhere on the public surface.
    assert "Actor" not in field_names
    assert all("<@" not in f.value or "42" in f.value for f in embed.fields)
    assert "🔨" in embed.title and "ban" in embed.title


def test_public_embed_omits_reason_when_empty():
    embed = format_public_log_embed(action="kick", target_id=7, reason="")
    assert [f.name for f in embed.fields] == ["Member"]


def _public_policy(actions: str, channel_id: int):
    from services.moderation_config import ModerationPolicy

    return ModerationPolicy(
        public_log_actions=actions,
        public_log_channel=str(channel_id) if channel_id else "",
    )


@pytest.mark.asyncio
async def test_maybe_log_public_sends_when_configured():
    guild = _make_guild()
    channel = _make_text_channel(channel_id=555)
    guild.get_channel = MagicMock(return_value=channel)
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
        return_value=_public_policy("removals", 555),
    ):
        sent = await maybe_log_public(guild, action="ban", target_id=9, reason="x")
    assert sent is True
    channel.send.assert_awaited_once()
    assert counters_snapshot()["counters"]["mod_public_sent"] == 1


@pytest.mark.asyncio
async def test_maybe_log_public_skips_action_not_selected():
    guild = _make_guild()
    channel = _make_text_channel()
    guild.get_channel = MagicMock(return_value=channel)
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
        return_value=_public_policy("bans", 555),  # bans only
    ):
        sent = await maybe_log_public(guild, action="kick", target_id=9, reason="x")
    assert sent is False
    channel.send.assert_not_awaited()
    assert counters_snapshot()["counters"]["mod_public_skipped"] == 1


@pytest.mark.asyncio
async def test_maybe_log_public_skips_when_channel_unresolvable():
    guild = _make_guild()
    guild.get_channel = MagicMock(return_value=None)  # stale / unset id
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
        return_value=_public_policy("all", 555),
    ):
        sent = await maybe_log_public(guild, action="warn", target_id=9, reason="x")
    assert sent is False
    assert counters_snapshot()["counters"]["mod_public_skipped"] == 1


@pytest.mark.asyncio
async def test_maybe_log_public_forbidden_is_counted_not_raised():
    guild = _make_guild()
    channel = _make_text_channel()
    channel.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perms"))
    guild.get_channel = MagicMock(return_value=channel)
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
        return_value=_public_policy("all", 555),
    ):
        sent = await maybe_log_public(guild, action="ban", target_id=9, reason="x")
    assert sent is False
    assert counters_snapshot()["counters"]["send_error"] == 1


@pytest.mark.asyncio
async def test_public_subscriber_skips_non_disciplinary_without_config_read():
    """unban / clearwarnings / sweeps never reach the policy read."""
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
    ) as load_policy:
        for action in ("unban", "clearwarnings", "post_action_cleanup", "auto_delete:x"):
            await _on_moderation_action_public(
                guild_id=1, target_id=2, action=action, reason="x", actor_id=3,
            )
    load_policy.assert_not_awaited()
