"""Unit tests for server event logging v2 — Discord audit-log integration.

Covers the layer added to close the "Dyno catches things we don't" gap:

* the ``_AUDIT_ACTION_META`` map (drift guard: every category is real; the
  headline actions are categorised as expected),
* :func:`server_logging.log_audit_entry` — categorisation, master/category
  gating, the actor-**or**-target ignore list, uncategorised-action skip, and
  the ``member_role_update`` special-case (role embed with actor),
* :func:`server_logging.format_audit_log_embed` — actor/target/reason/diff
  rendering + ``member_update`` verb refinement,
* :func:`server_logging.log_voice_state` — join/leave/move classification,
  same-channel skip, gating,
* :func:`server_logging.log_uncached_message_delete` — gating + embed,
* the ``LoggingCog`` v2 listeners (raw-delete defers to the cached path; voice
  skips bots).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import server_logging, server_logging_config
from services.server_logging_config import CATEGORIES, EventLoggingPolicy


@pytest.fixture(autouse=True)
def _reset_counters():
    server_logging._reset_for_tests()
    yield
    server_logging._reset_for_tests()


# ---------------------------------------------------------------------------
# Fakes — a minimal AuditLogEntry / VoiceState shaped like discord.py's
# ---------------------------------------------------------------------------


class _FakeDiff:
    """An ``AuditLogDiff`` stand-in: iterable of (attr, value) + attr access."""

    def __init__(self, **kw):
        self._d = dict(kw)

    def __iter__(self):
        return iter(self._d.items())

    def __getattr__(self, name):
        return self._d.get(name)


class _FakeChanges:
    def __init__(self, before=None, after=None):
        self.before = _FakeDiff(**(before or {}))
        self.after = _FakeDiff(**(after or {}))


def _actor(uid: int = 111, name: str = "Mod") -> MagicMock:
    u = MagicMock(spec=discord.Member)
    u.id = uid
    u.name = name
    u.display_name = name
    u.mention = f"<@{uid}>"
    u.display_avatar = MagicMock(url="http://cdn/av.png")
    return u


def _guild(gid: int = 555) -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = gid
    return g


def _audit_entry(
    action_name: str,
    *,
    user=None,
    target=None,
    reason=None,
    before=None,
    after=None,
    extra=None,
    guild=None,
) -> MagicMock:
    entry = MagicMock()
    entry.action = MagicMock()
    entry.action.name = action_name
    entry.user = user if user is not None else _actor()
    entry.target = target
    entry.reason = reason
    entry.changes = _FakeChanges(before=before, after=after)
    entry.extra = extra
    entry.guild = guild if guild is not None else _guild()
    entry.created_at = None
    return entry


def _policy(**flags) -> EventLoggingPolicy:
    base = {"enabled": True}
    base.update(flags)
    return EventLoggingPolicy(**base)


# ---------------------------------------------------------------------------
# _AUDIT_ACTION_META drift guard
# ---------------------------------------------------------------------------


def test_audit_action_meta_categories_are_all_real():
    valid = set(CATEGORIES)
    for name, (category, icon, verb) in server_logging._AUDIT_ACTION_META.items():
        assert category in valid, f"{name!r} → unknown category {category!r}"
        assert icon and verb


def test_audit_category_colors_are_all_real_categories():
    valid = set(CATEGORIES)
    for category in server_logging._AUDIT_CATEGORY_COLOR:
        assert category in valid


def test_headline_actions_are_categorised_as_expected():
    meta = server_logging._AUDIT_ACTION_META
    assert meta["ban"][0] == server_logging_config.CATEGORY_MODERATION
    assert meta["kick"][0] == server_logging_config.CATEGORY_MODERATION
    assert meta["member_role_update"][0] == server_logging_config.CATEGORY_ROLES
    assert meta["channel_create"][0] == server_logging_config.CATEGORY_CHANNELS
    assert meta["role_create"][0] == server_logging_config.CATEGORY_SERVER
    assert meta["invite_create"][0] == server_logging_config.CATEGORY_SERVER
    # Single message_delete is owned by the passive path — never the audit map.
    assert "message_delete" not in meta
    assert meta["message_bulk_delete"][0] == server_logging_config.CATEGORY_MESSAGES


# ---------------------------------------------------------------------------
# log_audit_entry — gating / categorisation / ignore
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_entry_posts_when_category_enabled():
    entry = _audit_entry("ban", target=_actor(999, "Victim"), reason="spam")
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(moderation_enabled=True)),
        ),
        patch.object(
            server_logging,
            "_post_event_embed",
            AsyncMock(return_value=True),
        ) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is True
    post.assert_awaited_once()
    # posted under the moderation category
    assert post.await_args.args[1] == server_logging_config.CATEGORY_MODERATION


@pytest.mark.asyncio
async def test_audit_entry_skipped_when_category_disabled():
    entry = _audit_entry("ban", target=_actor(999))
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(moderation_enabled=False)),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    post.assert_not_awaited()
    assert server_logging._COUNTERS["event_skipped_disabled"] == 1


@pytest.mark.asyncio
async def test_audit_entry_skipped_when_master_off():
    entry = _audit_entry("ban", target=_actor(999))
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(enabled=False, moderation_enabled=True)),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    post.assert_not_awaited()


@pytest.mark.asyncio
async def test_uncategorised_action_is_not_logged():
    # message_delete is deliberately unmapped (passive path owns it).
    entry = _audit_entry("message_delete", target=_actor(999))
    with (
        patch.object(server_logging_config, "load_policy", AsyncMock()) as load,
        patch.object(
            server_logging,
            "_post_event_embed",
            AsyncMock(),
        ) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    load.assert_not_awaited()  # short-circuits before any DB read
    post.assert_not_awaited()


@pytest.mark.asyncio
async def test_audit_entry_ignored_by_actor_id():
    entry = _audit_entry("ban", user=_actor(111), target=_actor(999))
    policy = _policy(moderation_enabled=True, ignored_user_ids=frozenset({111}))
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=policy),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    post.assert_not_awaited()
    assert server_logging._COUNTERS["event_skipped_ignored"] == 1


@pytest.mark.asyncio
async def test_audit_entry_ignored_by_target_id():
    entry = _audit_entry("ban", user=_actor(111), target=_actor(999))
    policy = _policy(moderation_enabled=True, ignored_user_ids=frozenset({999}))
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=policy),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    post.assert_not_awaited()


@pytest.mark.asyncio
async def test_audit_entry_never_raises_into_gateway():
    entry = _audit_entry("ban", target=_actor(999))
    with patch.object(
        server_logging_config,
        "load_policy",
        AsyncMock(side_effect=RuntimeError("boom")),
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is False
    assert server_logging._COUNTERS["subscriber_errors"] == 1


@pytest.mark.asyncio
async def test_member_role_update_uses_role_embed_with_actor():
    role = MagicMock(spec=discord.Role)
    role.mention = "<@&42>"
    role.id = 42
    role.name = "Member"
    member = _actor(999, "Grantee")
    entry = _audit_entry(
        "member_role_update",
        user=_actor(111, "Admin"),
        target=member,
        after={"roles": [role]},
    )
    captured = {}

    async def _capture(guild, category, *, per_category, embed):
        captured["category"] = category
        captured["embed"] = embed
        return True

    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(roles_enabled=True)),
        ),
        patch.object(server_logging, "_post_event_embed", _capture),
    ):
        result = await server_logging.log_audit_entry(entry)
    assert result is True
    assert captured["category"] == server_logging_config.CATEGORY_ROLES
    # The role embed names the actor (the phase-2 gap this closes).
    field_values = " ".join(f.value for f in captured["embed"].fields)
    assert "<@111>" in field_values
    assert "<@&42>" in field_values


# ---------------------------------------------------------------------------
# format_audit_log_embed
# ---------------------------------------------------------------------------


def test_format_audit_embed_shows_actor_target_reason_and_diff():
    entry = _audit_entry(
        "channel_update",
        user=_actor(111, "Admin"),
        target=MagicMock(mention="<#7>", id=7, name="general"),
        reason="rename",
        before={"name": "old"},
        after={"name": "new"},
    )
    embed = server_logging.format_audit_log_embed(
        entry,
        icon="📝",
        verb="Channel updated",
        category="channels",
    )
    names = [f.name for f in embed.fields]
    joined = " ".join(f"{f.name}={f.value}" for f in embed.fields)
    assert "Actor" in names
    assert "Target" in names
    assert "Reason" in names
    assert "old → new" in joined


def test_member_update_verb_refined_for_timeout():
    entry = _audit_entry(
        "member_update",
        target=_actor(999),
        before={"timed_out_until": None},
        after={"timed_out_until": "2026-01-01T00:00:00Z"},
    )
    embed = server_logging.format_audit_log_embed(
        entry,
        icon="⏳",
        verb="Member updated",
        category="moderation",
    )
    assert "timeout" in embed.title.lower()


def test_member_update_verb_refined_for_nick():
    entry = _audit_entry(
        "member_update",
        target=_actor(999),
        before={"nick": "old"},
        after={"nick": "new"},
    )
    embed = server_logging.format_audit_log_embed(
        entry,
        icon="⏳",
        verb="Member updated",
        category="moderation",
    )
    assert "nickname" in embed.title.lower()


def test_format_audit_embed_bulk_delete_shows_count():
    extra = MagicMock()
    extra.count = 25
    entry = _audit_entry(
        "message_bulk_delete",
        target=MagicMock(mention="<#7>", id=7, name="general"),
        extra=extra,
    )
    embed = server_logging.format_audit_log_embed(
        entry,
        icon="🧨",
        verb="Messages bulk-deleted",
        category="messages",
    )
    assert any(f.name == "Count" and f.value == "25" for f in embed.fields)


# ---------------------------------------------------------------------------
# log_voice_state
# ---------------------------------------------------------------------------


def _voice_state(channel):
    vs = MagicMock(spec=discord.VoiceState)
    vs.channel = channel
    return vs


def _vchannel(cid: int):
    ch = MagicMock()
    ch.id = cid
    ch.mention = f"<#{cid}>"
    return ch


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("before_ch", "after_ch", "expect_kind"),
    [
        (None, _vchannel(1), "joined"),
        (_vchannel(1), None, "left"),
        (_vchannel(1), _vchannel(2), "moved"),
    ],
)
async def test_voice_transitions_classified_and_logged(
    before_ch, after_ch, expect_kind
):
    member = _actor(999, "Speaker")
    member.guild = _guild()
    captured = {}

    async def _capture(guild, category, *, per_category, embed):
        captured["category"] = category
        captured["embed"] = embed
        return True

    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(voice_enabled=True)),
        ),
        patch.object(server_logging, "_post_event_embed", _capture),
    ):
        result = await server_logging.log_voice_state(
            member,
            _voice_state(before_ch),
            _voice_state(after_ch),
        )
    assert result is True
    assert captured["category"] == server_logging_config.CATEGORY_VOICE
    assert expect_kind in captured["embed"].title.lower()


@pytest.mark.asyncio
async def test_voice_same_channel_state_change_is_skipped():
    member = _actor(999)
    member.guild = _guild()
    ch = _vchannel(1)
    with patch.object(server_logging, "_post_event_embed", AsyncMock()) as post:
        result = await server_logging.log_voice_state(
            member,
            _voice_state(ch),
            _voice_state(ch),
        )
    assert result is False
    post.assert_not_awaited()


@pytest.mark.asyncio
async def test_voice_skipped_when_category_disabled():
    member = _actor(999)
    member.guild = _guild()
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(voice_enabled=False)),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_voice_state(
            member,
            _voice_state(None),
            _voice_state(_vchannel(1)),
        )
    assert result is False
    post.assert_not_awaited()


# ---------------------------------------------------------------------------
# log_uncached_message_delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uncached_delete_logs_event_with_unavailable_content():
    guild = _guild()
    captured = {}

    async def _capture(g, category, *, per_category, embed):
        captured["embed"] = embed
        return True

    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(messages_enabled=True)),
        ),
        patch.object(server_logging, "_post_event_embed", _capture),
    ):
        result = await server_logging.log_uncached_message_delete(guild, 7, 123456)
    assert result is True
    joined = " ".join(f"{f.name}={f.value}" for f in captured["embed"].fields)
    assert "<#7>" in joined
    assert "123456" in joined
    assert "unavailable" in joined.lower()


@pytest.mark.asyncio
async def test_uncached_delete_skipped_when_messages_disabled():
    with (
        patch.object(
            server_logging_config,
            "load_policy",
            AsyncMock(return_value=_policy(messages_enabled=False)),
        ),
        patch.object(server_logging, "_post_event_embed", AsyncMock()) as post,
    ):
        result = await server_logging.log_uncached_message_delete(_guild(), 7, 1)
    assert result is False
    post.assert_not_awaited()


# ---------------------------------------------------------------------------
# LoggingCog v2 listeners
# ---------------------------------------------------------------------------


def _cog():
    from cogs.logging_cog import LoggingCog

    bot = MagicMock()
    return LoggingCog(bot)


@pytest.mark.asyncio
async def test_on_audit_log_entry_create_delegates():
    cog = _cog()
    entry = _audit_entry("ban")
    with patch(
        "services.server_logging.log_audit_entry",
        AsyncMock(),
    ) as handler:
        await cog.on_audit_log_entry_create(entry)
    handler.assert_awaited_once_with(entry)


@pytest.mark.asyncio
async def test_on_raw_message_delete_defers_to_cached_path():
    cog = _cog()
    payload = MagicMock()
    payload.guild_id = 555
    payload.cached_message = MagicMock()  # cached → on_message_delete owns it
    with patch(
        "services.server_logging.log_uncached_message_delete",
        AsyncMock(),
    ) as handler:
        await cog.on_raw_message_delete(payload)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_raw_message_delete_handles_uncached():
    cog = _cog()
    cog.bot.get_guild = MagicMock(return_value=_guild())
    payload = MagicMock()
    payload.guild_id = 555
    payload.cached_message = None  # uncached → the raw path logs it
    payload.channel_id = 7
    payload.message_id = 42
    with patch(
        "services.server_logging.log_uncached_message_delete",
        AsyncMock(),
    ) as handler:
        await cog.on_raw_message_delete(payload)
    handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_voice_state_update_skips_bots():
    cog = _cog()
    member = _actor(999)
    member.bot = True
    with patch(
        "services.server_logging.log_voice_state",
        AsyncMock(),
    ) as handler:
        await cog.on_voice_state_update(
            member, _voice_state(None), _voice_state(_vchannel(1))
        )
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_voice_state_update_logs_non_bot():
    cog = _cog()
    member = _actor(999)
    member.bot = False
    with patch(
        "services.server_logging.log_voice_state",
        AsyncMock(),
    ) as handler:
        await cog.on_voice_state_update(
            member, _voice_state(None), _voice_state(_vchannel(1))
        )
    handler.assert_awaited_once()
