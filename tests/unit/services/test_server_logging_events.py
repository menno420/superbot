"""Unit tests for server event logging v1 (Q-0109).

Covers the new passive-event layer added to ``services.server_logging`` +
its config read model ``services.server_logging_config`` + the
``LoggingCog`` listener filters:

* :class:`EventLoggingPolicy` defaults / gating / routing,
* :func:`server_logging_config.load_policy` typed resolution,
* the embed builders (fields + truncation + placeholders),
* :func:`resolve_event_channel` route selection (combined vs per-category),
* the ``log_*`` handlers (disabled-skip / send / missing-channel / counters),
* the cog listeners' cheap structural filters (skip bots / no-op edits /
  non-role member updates).
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import server_logging, server_logging_config
from services.server_logging_config import (
    CATEGORY_MEMBERS,
    CATEGORY_MESSAGES,
    CATEGORY_ROLES,
    EventLoggingPolicy,
)


@pytest.fixture(autouse=True)
def _reset_counters():
    server_logging._reset_for_tests()
    yield
    server_logging._reset_for_tests()


# ---------------------------------------------------------------------------
# Mock factories
# ---------------------------------------------------------------------------


def _guild(guild_id: int = 555) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = f"guild-{guild_id}"
    guild.member_count = 1234
    return guild


def _channel(channel_id: int = 42, name: str = "log") -> MagicMock:
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.mention = f"<#{channel_id}>"
    channel.send = AsyncMock()
    return channel


def _role(role_id: int, name: str = "Role", default: bool = False) -> MagicMock:
    role = MagicMock(spec=discord.Role)
    role.id = role_id
    role.name = name
    role.mention = f"<@&{role_id}>"
    role.is_default = MagicMock(return_value=default)
    return role


def _message(*, content: str = "hi", bot: bool = False) -> MagicMock:
    msg = MagicMock(spec=discord.Message)
    msg.guild = _guild()
    author = MagicMock()
    author.id = 7
    author.bot = bot
    author.display_name = "AuthorName"
    author.display_avatar = MagicMock()
    author.display_avatar.url = "https://cdn.example/author.png"
    msg.author = author
    msg.content = content
    channel = MagicMock(spec=discord.TextChannel)
    channel.mention = "<#99>"
    msg.channel = channel
    msg.attachments = []
    msg.jump_url = "https://discord.com/x"
    return msg


def _member(*, bot: bool = False, roles: list | None = None) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = 11
    member.bot = bot
    member.guild = _guild()
    member.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    member.joined_at = datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)
    member.roles = roles if roles is not None else [_role(1, "@everyone", default=True)]
    member.display_name = "MemberName"
    member.display_avatar = MagicMock()
    member.display_avatar.url = "https://cdn.example/member.png"
    member.__str__ = lambda self: "TestUser"  # type: ignore[assignment]
    return member


# ---------------------------------------------------------------------------
# EventLoggingPolicy
# ---------------------------------------------------------------------------


def test_policy_defaults_all_off():
    pol = EventLoggingPolicy()
    assert pol.enabled is False
    assert not pol.any_category_enabled
    assert pol.routing == "combined"
    assert pol.per_category is False


def test_should_log_requires_master_and_category():
    # Master off → never logs, even with a category on.
    assert not EventLoggingPolicy(messages_enabled=True).should_log(CATEGORY_MESSAGES)
    # Master on but category off → no.
    assert not EventLoggingPolicy(enabled=True).should_log(CATEGORY_MESSAGES)
    # Both on → yes.
    assert EventLoggingPolicy(enabled=True, messages_enabled=True).should_log(
        CATEGORY_MESSAGES,
    )
    # Unknown category → no.
    assert not EventLoggingPolicy(enabled=True).should_log("nonsense")


def test_per_category_property():
    assert EventLoggingPolicy(routing="per_category").per_category is True
    assert EventLoggingPolicy(routing="combined").per_category is False


@pytest.mark.asyncio
async def test_load_policy_composes_typed_values(monkeypatch):
    stored = {
        "enabled": True,
        "messages_enabled": True,
        "event_routing": "per_category",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "logging"
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await server_logging_config.load_policy(guild_id=1)
    assert pol.enabled is True
    assert pol.messages_enabled is True
    assert pol.per_category is True
    # Unset categories fall back to the canonical OFF default.
    assert pol.members_enabled is False
    assert pol.roles_enabled is False


@pytest.mark.asyncio
async def test_load_policy_rejects_unknown_routing(monkeypatch):
    async def fake_resolve(guild_id, subsystem, name, fallback):
        if name == "event_routing":
            return "garbage"
        return fallback

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await server_logging_config.load_policy(guild_id=1)
    assert pol.routing == "combined"  # degraded to the default, not "garbage"


# ---------------------------------------------------------------------------
# Route-table coupling
# ---------------------------------------------------------------------------


def test_category_route_map_in_sync_with_config_categories():
    # v1 (Q-0109) categories each have a dedicated per-category route.
    # v2 (audit-log integration) categories deliberately have NO dedicated
    # route — they resolve to the combined ``events`` channel via
    # ``resolve_event_channel``'s fallback, so they must NOT appear here.
    assert set(server_logging._CATEGORY_TO_ROUTE) == {
        server_logging_config.CATEGORY_MESSAGES,
        server_logging_config.CATEGORY_MEMBERS,
        server_logging_config.CATEGORY_ROLES,
    }
    # No orphan routes: every mapped category is a real config category.
    assert set(server_logging._CATEGORY_TO_ROUTE) <= set(
        server_logging_config.CATEGORIES,
    )


def test_event_routes_are_registered_in_the_route_table():
    for route in ("events", "message_log", "member_log", "role_log"):
        assert route in server_logging._ROUTE_TO_BINDING
        assert route in server_logging._ROUTE_FALLBACK


def test_event_category_routes_fall_back_to_events_not_mod():
    for route in ("message_log", "member_log", "role_log"):
        assert server_logging._ROUTE_FALLBACK[route] == "events"
    # The combined route is terminal — never spills into mod.
    assert server_logging._ROUTE_FALLBACK["events"] is None


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def test_message_delete_embed_shows_author_channel_content():
    embed = server_logging.format_message_delete_embed(_message(content="secret"))
    names = {f.name for f in embed.fields}
    assert {"Author", "Channel", "Content"}.issubset(names)
    content = next(f for f in embed.fields if f.name == "Content")
    assert "secret" in content.value


def test_message_delete_embed_handles_empty_content():
    embed = server_logging.format_message_delete_embed(_message(content=""))
    content = next(f for f in embed.fields if f.name == "Content")
    assert "no text content" in content.value


def test_message_delete_embed_truncates_long_content():
    embed = server_logging.format_message_delete_embed(_message(content="x" * 5000))
    content = next(f for f in embed.fields if f.name == "Content")
    assert len(content.value) <= 1024


def test_message_edit_embed_shows_before_and_after():
    before = _message(content="old")
    after = _message(content="new")
    embed = server_logging.format_message_edit_embed(before, after)
    names = {f.name for f in embed.fields}
    assert {"Before", "After"}.issubset(names)
    assert "old" in next(f for f in embed.fields if f.name == "Before").value
    assert "new" in next(f for f in embed.fields if f.name == "After").value


def test_member_join_embed_shows_count_and_age():
    embed = server_logging.format_member_join_embed(_member())
    names = {f.name for f in embed.fields}
    assert {"Member", "Account created", "Member count"}.issubset(names)


def test_member_leave_embed_lists_non_default_roles():
    staff = _role(2, "Staff")
    member = _member(roles=[_role(1, "@everyone", default=True), staff])
    embed = server_logging.format_member_leave_embed(member)
    roles_field = next(f for f in embed.fields if f.name == "Roles held")
    assert staff.mention in roles_field.value


def test_role_change_embed_shows_added_and_removed():
    added = [_role(3, "Added")]
    removed = [_role(4, "Removed")]
    embed = server_logging.format_role_change_embed(_member(), added, removed)
    names = {f.name for f in embed.fields}
    assert "➕ Added" in names
    assert "➖ Removed" in names


# ---------------------------------------------------------------------------
# Subject avatar in the embed author slot (a face per log entry)
# ---------------------------------------------------------------------------


def test_message_embeds_set_subject_avatar_in_author_slot():
    # The message author's avatar + name ride the embed author slot (the "who"
    # at a glance), while the structured fields are unchanged.
    deleted = server_logging.format_message_delete_embed(_message(content="x"))
    assert deleted.author.name == "AuthorName"
    assert deleted.author.icon_url == "https://cdn.example/author.png"
    edited = server_logging.format_message_edit_embed(_message(), _message())
    assert edited.author.name == "AuthorName"
    assert edited.author.icon_url == "https://cdn.example/author.png"


def test_member_and_role_embeds_set_subject_avatar_in_author_slot():
    for embed in (
        server_logging.format_member_join_embed(_member()),
        server_logging.format_member_leave_embed(_member()),
        server_logging.format_role_change_embed(_member(), [_role(3, "Added")], []),
    ):
        assert embed.author.name == "MemberName"
        assert embed.author.icon_url == "https://cdn.example/member.png"


def test_set_subject_author_is_defensive_on_partial_object():
    # A subject with no display_name / name → no author line, never a raise
    # (keeps the fail-safe handler honest for a partial/odd object).
    class _Bare:
        pass

    embed = discord.Embed()
    server_logging._set_subject_author(embed, _Bare())
    assert embed.author.name is None


# ---------------------------------------------------------------------------
# resolve_event_channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_event_channel_combined_uses_events_route():
    guild = _guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ) as resolve:
        await server_logging.resolve_event_channel(
            guild,
            CATEGORY_MEMBERS,
            per_category=False,
        )
    assert resolve.await_args.args[1] == "events"


@pytest.mark.asyncio
async def test_resolve_event_channel_per_category_uses_category_route():
    guild = _guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ) as resolve:
        await server_logging.resolve_event_channel(
            guild,
            CATEGORY_ROLES,
            per_category=True,
        )
    assert resolve.await_args.args[1] == "role_log"


# ---------------------------------------------------------------------------
# Handlers — gating / send / counters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_skips_when_disabled():
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(),  # all off
    ):
        sent = await server_logging.log_member_join(_member())
    assert sent is False
    assert server_logging.counters_snapshot()["counters"]["event_skipped_disabled"] == 1


@pytest.mark.asyncio
async def test_handler_sends_when_enabled():
    channel = _channel()
    member = _member()
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(enabled=True, members_enabled=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await server_logging.log_member_join(member)
    assert sent is True
    channel.send.assert_awaited_once()
    assert server_logging.counters_snapshot()["counters"]["event_sent"] == 1


@pytest.mark.asyncio
async def test_handler_counts_missing_channel():
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(enabled=True, members_enabled=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "services.server_logging.auto_create_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ):
        sent = await server_logging.log_member_join(_member())
    assert sent is False
    assert server_logging.counters_snapshot()["counters"]["event_missing_channel"] == 1


# ---------------------------------------------------------------------------
# Ignore lists (completion cert punch #1)
# ---------------------------------------------------------------------------


def test_is_ignored_gate():
    pol = EventLoggingPolicy(
        ignored_channel_ids=frozenset({42}),
        ignored_user_ids=frozenset({7}),
    )
    # Channel match.
    assert pol.is_ignored(channel_id=42, user_id=99) is True
    # User match.
    assert pol.is_ignored(channel_id=1, user_id=7) is True
    # Neither → not ignored.
    assert pol.is_ignored(channel_id=1, user_id=2) is False
    # None ids never match (a channel-less member event with no user match).
    assert pol.is_ignored(channel_id=None, user_id=None) is False
    # Empty policy ignores nothing.
    assert EventLoggingPolicy().is_ignored(channel_id=42, user_id=7) is False


@pytest.mark.asyncio
async def test_load_policy_parses_ignore_lists(monkeypatch):
    stored = {
        "ignored_channels": "42, 43 ,bad",  # tolerant: 'bad' dropped
        "ignored_users": "7",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await server_logging_config.load_policy(guild_id=1)
    assert pol.ignored_channel_ids == frozenset({42, 43})
    assert pol.ignored_user_ids == frozenset({7})
    # Unset lists default empty (no exclusion).
    assert EventLoggingPolicy().ignored_channel_ids == frozenset()


@pytest.mark.asyncio
async def test_handler_skips_when_channel_ignored():
    # A deleted message in an ignored channel is not logged even though the
    # messages category is on.
    msg = _message(content="hi")
    msg.channel.id = 42
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(
            enabled=True,
            messages_enabled=True,
            ignored_channel_ids=frozenset({42}),
        ),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=_channel(),
    ) as resolve:
        sent = await server_logging.log_message_delete(msg)
    assert sent is False
    resolve.assert_not_awaited()  # gated out before any channel work
    assert server_logging.counters_snapshot()["counters"]["event_skipped_ignored"] == 1


@pytest.mark.asyncio
async def test_handler_skips_when_user_ignored():
    # A join from an ignored user is not logged even though the members
    # category is on and there is no channel context.
    member = _member()  # id == 11
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(
            enabled=True,
            members_enabled=True,
            ignored_user_ids=frozenset({11}),
        ),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=_channel(),
    ) as resolve:
        sent = await server_logging.log_member_join(member)
    assert sent is False
    resolve.assert_not_awaited()
    assert server_logging.counters_snapshot()["counters"]["event_skipped_ignored"] == 1


@pytest.mark.asyncio
async def test_handler_sends_when_ids_not_ignored():
    # Ignore lists present but the event's ids are not on them → logs normally.
    channel = _channel()
    member = _member()  # id == 11
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(
            enabled=True,
            members_enabled=True,
            ignored_user_ids=frozenset({999}),
        ),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await server_logging.log_member_join(member)
    assert sent is True
    assert server_logging.counters_snapshot()["counters"]["event_skipped_ignored"] == 0


@pytest.mark.asyncio
async def test_role_change_handler_no_diff_short_circuits():
    # Empty add/remove returns before any policy/channel work.
    sent = await server_logging.log_role_change(_member(), [], [])
    assert sent is False


@pytest.mark.asyncio
async def test_handler_is_fail_safe_on_send_error():
    channel = _channel()
    channel.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "boom"))
    with patch(
        "services.server_logging_config.load_policy",
        new_callable=AsyncMock,
        return_value=EventLoggingPolicy(enabled=True, members_enabled=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=channel,
    ):
        sent = await server_logging.log_member_join(_member())
    assert sent is False
    assert server_logging.counters_snapshot()["counters"]["send_error"] == 1


# ---------------------------------------------------------------------------
# Cog listener filters
# ---------------------------------------------------------------------------


def _cog():
    from cogs.logging_cog import LoggingCog

    return LoggingCog(bot=MagicMock())


@pytest.mark.asyncio
async def test_on_message_delete_skips_bot_author():
    cog = _cog()
    with patch(
        "services.server_logging.log_message_delete",
        new_callable=AsyncMock,
    ) as handler:
        await cog.on_message_delete(_message(bot=True))
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_message_edit_skips_noop_content_change():
    cog = _cog()
    before = _message(content="same")
    after = _message(content="same")
    with patch(
        "services.server_logging.log_message_edit",
        new_callable=AsyncMock,
    ) as handler:
        await cog.on_message_edit(before, after)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_message_edit_logs_real_change():
    cog = _cog()
    before = _message(content="old")
    after = _message(content="new")
    with patch(
        "services.server_logging.log_message_edit",
        new_callable=AsyncMock,
    ) as handler:
        await cog.on_message_edit(before, after)
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_member_update_skips_when_no_role_diff():
    cog = _cog()
    roles = [_role(1, "@everyone", default=True), _role(2, "Member")]
    before = _member(roles=roles)
    after = _member(roles=roles)
    with patch(
        "services.server_logging.log_role_change",
        new_callable=AsyncMock,
    ) as handler:
        await cog.on_member_update(before, after)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_member_update_reports_added_role():
    cog = _cog()
    base = _role(1, "@everyone", default=True)
    added = _role(2, "Member")
    before = _member(roles=[base])
    after = _member(roles=[base, added])
    with patch(
        "services.server_logging.log_role_change",
        new_callable=AsyncMock,
    ) as handler:
        await cog.on_member_update(before, after)
    handler.assert_awaited_once()
    args = handler.await_args.args
    # args: (member, added, removed)
    assert added in args[1]
    assert args[2] == []
