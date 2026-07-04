"""Phase 9c.1 — server_logging audit subscriber tests.

Covers:

* ``audit.action_recorded`` is in ``KNOWN_EVENTS``.
* ``server_logging.setup(bot)`` registers a subscriber for it.
* The subscriber respects ``is_enabled`` (skips when logging is OFF).
* The subscriber skips global-scope mutations (``guild_id=None``).
* The subscriber resolves the route via
  ``resolve_log_channel(guild, "audit")`` — falling back to the mod
  channel through the Phase 9a fallback chain.
* The subscriber bumps the ``audit_sent`` counter on success.
* The subscriber catches every exception and bumps
  ``subscriber_errors`` rather than crashing.
* ``format_audit_embed`` renders the expected fields.
* The Phase 9c.1 ``audit_sent`` counter bucket exists in
  ``counters_snapshot()``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import server_logging
from services.server_logging import (
    EVT_AUDIT_ACTION_RECORDED,
    _on_audit_action,
    counters_snapshot,
    format_audit_embed,
    log_audit_event,
)


def _guild(guild_id: int = 42) -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    return g


def _channel(name: str = "bot-audit-log") -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.name = name
    ch.send = AsyncMock()
    return ch


@pytest.fixture(autouse=True)
def _reset_counters():
    """Reset counters before each test so per-test bucket asserts work."""
    server_logging._reset_for_tests()
    yield
    server_logging._reset_for_tests()


# ---------------------------------------------------------------------------
# Catalogue + subscription
# ---------------------------------------------------------------------------


def test_audit_topic_is_in_known_events():
    from core.events_catalogue import KNOWN_EVENTS

    assert "audit.action_recorded" in KNOWN_EVENTS


def test_counters_snapshot_includes_audit_sent_bucket():
    snap = counters_snapshot()
    assert "audit_sent" in snap["counters"]
    assert snap["counters"]["audit_sent"] == 0
    assert "audit.action_recorded" in snap["subscribed_events"]


def test_subscriber_signature_accepts_full_payload():
    """The handler must accept the canonical payload + extra fields
    (via ``**_extras``) without raising TypeError. A future publisher
    that adds new keys to the payload should not break this subscriber."""
    import inspect

    sig = inspect.signature(_on_audit_action)
    params = sig.parameters
    for required in (
        "mutation_id",
        "subsystem",
        "mutation_type",
        "target",
        "scope",
        "guild_id",
        "prev_value",
        "new_value",
        "actor_id",
        "actor_type",
        "occurred_at",
    ):
        assert required in params
    # **_extras catches arbitrary future additions.
    assert any(p.kind == p.VAR_KEYWORD for p in params.values())


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------


def test_format_audit_embed_renders_expected_fields():
    embed = format_audit_embed(
        mutation_id="abc-123",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:settings.manager_cog.enabled",
        scope="guild",
        guild_id=42,
        prev_value="off",
        new_value="on",
        actor_id=99,
        actor_type="platform_owner",
        occurred_at="2026-05-19T12:00:00+00:00",
    )
    field_names = [f.name for f in embed.fields]
    for required in (
        "Target",
        "Actor",
        "Actor type",
        "Previous",
        "New",
        "Mutation ID",
    ):
        assert required in field_names
    rendered = "\n".join(f.value for f in embed.fields)
    assert "abc-123" in rendered
    assert "off" in rendered
    assert "on" in rendered
    assert "<@99>" in rendered  # actor mention
    assert "set_flag_state" in (embed.title or "")


def test_format_audit_embed_subject_sets_actor_avatar():
    # The audit embed's face is the *actor* (who made the change), matching the
    # face-per-entry look of every other log embed.
    subject = MagicMock()
    subject.display_name = "ActorUser"
    subject.display_avatar = MagicMock()
    subject.display_avatar.url = "https://cdn.example/a.png"
    embed = format_audit_embed(
        mutation_id="abc-123",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:x",
        scope="guild",
        guild_id=42,
        prev_value="off",
        new_value="on",
        actor_id=99,
        actor_type="platform_owner",
        occurred_at="2026-05-19T12:00:00+00:00",
        subject=subject,
    )
    assert embed.author.name == "ActorUser"
    assert embed.author.icon_url == "https://cdn.example/a.png"


def test_format_audit_embed_without_subject_has_no_author():
    embed = format_audit_embed(
        mutation_id="x",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:x",
        scope="guild",
        guild_id=42,
        prev_value="off",
        new_value="on",
        actor_id=None,
        actor_type="system",
        occurred_at="2026-05-19T12:00:00+00:00",
    )
    assert embed.author.name is None


def test_format_audit_embed_handles_cleared_value():
    embed = format_audit_embed(
        mutation_id="x",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:x",
        scope="guild",
        guild_id=42,
        prev_value="on",
        new_value=None,
        actor_id=99,
        actor_type="platform_owner",
        occurred_at="2026-05-19T12:00:00+00:00",
    )
    new_field = next(f for f in embed.fields if f.name == "New")
    assert "cleared" in new_field.value


def test_format_audit_embed_handles_system_actor():
    embed = format_audit_embed(
        mutation_id="x",
        subsystem="logging",
        mutation_type="set_flag_state",
        target="flag:x",
        scope="global",
        guild_id=None,
        prev_value=None,
        new_value="canary",
        actor_id=None,
        actor_type="system",
        occurred_at="2026-05-19T12:00:00+00:00",
    )
    actor_field = next(f for f in embed.fields if f.name == "Actor")
    # No actor_id → falls back to actor_type display.
    assert "system" in actor_field.value


# ---------------------------------------------------------------------------
# Subscriber routing
# ---------------------------------------------------------------------------


_PAYLOAD = {
    "mutation_id": "abc-123",
    "subsystem": "logging",
    "mutation_type": "set_flag_state",
    "target": "flag:settings.manager_cog.enabled",
    "scope": "guild",
    "guild_id": 42,
    "prev_value": "off",
    "new_value": "on",
    "actor_id": 99,
    "actor_type": "platform_owner",
    "occurred_at": "2026-05-19T12:00:00+00:00",
}


@pytest.mark.asyncio
async def test_subscriber_skips_when_logging_disabled():
    bot = MagicMock()
    bot.get_guild.return_value = _guild()
    with patch.object(server_logging, "_BOT", bot), patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=False),
    ):
        await _on_audit_action(**_PAYLOAD)
    snap = counters_snapshot()
    assert snap["counters"]["skipped_disabled"] == 1
    assert snap["counters"]["audit_sent"] == 0


@pytest.mark.asyncio
async def test_subscriber_skips_global_scope_mutations():
    """Global-scope mutations have no guild to route into."""
    bot = MagicMock()
    bot.get_guild.return_value = _guild()
    payload = dict(_PAYLOAD, guild_id=None, scope="global")
    with patch.object(server_logging, "_BOT", bot):
        await _on_audit_action(**payload)
    snap = counters_snapshot()
    assert snap["counters"]["skipped_no_guild"] == 1
    assert snap["counters"]["audit_sent"] == 0


@pytest.mark.asyncio
async def test_subscriber_skips_when_guild_not_resolvable():
    bot = MagicMock()
    bot.get_guild.return_value = None  # guild not in bot's cache
    with patch.object(server_logging, "_BOT", bot):
        await _on_audit_action(**_PAYLOAD)
    snap = counters_snapshot()
    assert snap["counters"]["skipped_no_guild"] == 1


@pytest.mark.asyncio
async def test_subscriber_routes_through_audit_channel():
    """The subscriber must call ``resolve_log_channel(guild, "audit")``,
    not "mod" or any other route. This pins the routing contract.
    """
    bot = MagicMock()
    guild = _guild()
    bot.get_guild.return_value = guild
    channel = _channel(name="bot-audit-log")

    seen_kinds: list[str] = []

    async def fake_resolve(_guild, kind):
        seen_kinds.append(kind)
        return channel

    with patch.object(server_logging, "_BOT", bot), patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        side_effect=fake_resolve,
    ):
        await _on_audit_action(**_PAYLOAD)

    assert seen_kinds == ["audit"]
    channel.send.assert_awaited_once()
    snap = counters_snapshot()
    assert snap["counters"]["audit_sent"] == 1


@pytest.mark.asyncio
async def test_subscriber_counts_missing_channel():
    bot = MagicMock()
    bot.get_guild.return_value = _guild()
    with patch.object(server_logging, "_BOT", bot), patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        AsyncMock(return_value=None),
    ), patch(
        "services.server_logging.auto_create_enabled",
        AsyncMock(return_value=False),
    ):
        await _on_audit_action(**_PAYLOAD)
    snap = counters_snapshot()
    assert snap["counters"]["missing_channel"] == 1
    assert snap["counters"]["audit_sent"] == 0


@pytest.mark.asyncio
async def test_subscriber_falls_back_to_mod_channel_when_audit_unset():
    """Phase 9a route table: ``audit`` falls back to ``mod`` when
    ``logging.audit_channel`` is unset. The subscriber must not bypass
    the route table — it always asks for kind="audit" and trusts
    ``resolve_log_channel`` to do the fallback chain."""
    bot = MagicMock()
    guild = _guild()
    bot.get_guild.return_value = guild
    mod_channel = _channel(name="bot-mod-log")

    seen_kinds: list[str] = []

    async def fake_resolve(_guild, kind):
        # Mimic the real route table: kind="audit" resolves to the
        # mod channel when audit_channel is unset.
        seen_kinds.append(kind)
        return mod_channel

    with (
        patch.object(server_logging, "_BOT", bot),
        patch(
            "services.server_logging.is_enabled",
            AsyncMock(return_value=True),
        ),
        patch(
            "services.server_logging.resolve_log_channel",
            side_effect=fake_resolve,
        ),
    ):
        await _on_audit_action(**_PAYLOAD)

    # The subscriber asks for "audit" exactly once and does not retry
    # with "mod" on its own — the route table owns the fallback.
    assert seen_kinds == ["audit"]
    mod_channel.send.assert_awaited_once()
    snap = counters_snapshot()
    assert snap["counters"]["audit_sent"] >= 1


@pytest.mark.asyncio
async def test_subscriber_counts_send_error_on_http_exception():
    """``discord.HTTPException`` (Discord rate limits, 5xx, etc.) on
    ``channel.send`` bumps ``send_error`` and is swallowed."""
    bot = MagicMock()
    guild = _guild()
    bot.get_guild.return_value = guild
    channel = _channel()
    channel.send = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(status=503), "service down"),
    )

    with (
        patch.object(server_logging, "_BOT", bot),
        patch(
            "services.server_logging.is_enabled",
            AsyncMock(return_value=True),
        ),
        patch(
            "services.server_logging.resolve_log_channel",
            AsyncMock(return_value=channel),
        ),
    ):
        # Must not raise.
        await _on_audit_action(**_PAYLOAD)

    snap = counters_snapshot()
    assert snap["counters"]["send_error"] >= 1
    assert snap["counters"]["audit_sent"] == 0


@pytest.mark.asyncio
async def test_subscriber_counts_send_error_on_unexpected_exception():
    """A non-Discord ``Exception`` on ``channel.send`` (e.g. network
    timeout from an aiohttp transport bug) is still caught and
    counted under ``send_error``."""
    bot = MagicMock()
    guild = _guild()
    bot.get_guild.return_value = guild
    channel = _channel()
    channel.send = AsyncMock(side_effect=RuntimeError("transport reset"))

    with (
        patch.object(server_logging, "_BOT", bot),
        patch(
            "services.server_logging.is_enabled",
            AsyncMock(return_value=True),
        ),
        patch(
            "services.server_logging.resolve_log_channel",
            AsyncMock(return_value=channel),
        ),
    ):
        # Must not raise — the fail-safe wrapper covers BLE001.
        await _on_audit_action(**_PAYLOAD)

    snap = counters_snapshot()
    assert snap["counters"]["send_error"] >= 1
    assert snap["counters"]["audit_sent"] == 0


@pytest.mark.asyncio
async def test_subscriber_counts_permission_error():
    bot = MagicMock()
    guild = _guild()
    bot.get_guild.return_value = guild
    channel = _channel()
    channel.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "nope"))

    with patch.object(server_logging, "_BOT", bot), patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        AsyncMock(return_value=channel),
    ):
        await _on_audit_action(**_PAYLOAD)
    snap = counters_snapshot()
    assert snap["counters"]["permission_error"] == 1


@pytest.mark.asyncio
async def test_subscriber_catches_unexpected_exception():
    """The handler must not raise into the event bus."""

    async def boom(*_a, **_k):
        raise RuntimeError("unexpected")

    # The bot lookup itself raising is the cleanest way to force an
    # exception inside the subscriber body.
    bad_bot = MagicMock()
    bad_bot.get_guild = MagicMock(side_effect=RuntimeError("unexpected"))
    with patch.object(server_logging, "_BOT", bad_bot):
        # The subscriber must not propagate the exception.
        await _on_audit_action(**_PAYLOAD)
    snap = counters_snapshot()
    assert snap["counters"]["subscriber_errors"] == 1


@pytest.mark.asyncio
async def test_subscriber_accepts_unknown_payload_fields():
    """A future publisher may add keys. The subscriber must accept
    them via ``**_extras`` and ignore them."""
    bot = MagicMock()
    bot.get_guild.return_value = _guild()
    channel = _channel()
    payload_with_extras = dict(
        _PAYLOAD,
        future_field_1="ignored",
        future_field_2=42,
    )
    with patch.object(server_logging, "_BOT", bot), patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        AsyncMock(return_value=channel),
    ):
        await _on_audit_action(**payload_with_extras)
    # No crash, audit was sent normally.
    snap = counters_snapshot()
    assert snap["counters"]["audit_sent"] == 1


# ---------------------------------------------------------------------------
# log_audit_event direct entry point (for non-bus consumers)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_log_audit_event_returns_true_on_success():
    guild = _guild()
    channel = _channel()
    with patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=True),
    ), patch(
        "services.server_logging.resolve_log_channel",
        AsyncMock(return_value=channel),
    ):
        result = await log_audit_event(guild, **_PAYLOAD)
    assert result is True
    snap = counters_snapshot()
    assert snap["counters"]["audit_sent"] == 1


@pytest.mark.asyncio
async def test_log_audit_event_returns_false_when_disabled():
    guild = _guild()
    with patch(
        "services.server_logging.is_enabled",
        AsyncMock(return_value=False),
    ):
        result = await log_audit_event(guild, **_PAYLOAD)
    assert result is False


# ---------------------------------------------------------------------------
# setup() registers the new subscriber
# ---------------------------------------------------------------------------


def test_setup_registers_audit_subscriber():
    """``setup(bot)`` must register a handler for
    ``audit.action_recorded`` (in addition to the existing
    moderation handler). The bus registration is global so we
    inspect ``server_logging._SUBSCRIBED`` + the subscribed_events
    snapshot.
    """
    bot = MagicMock()
    # The setup function is idempotent; calling it multiple times in
    # tests is safe.
    server_logging.setup(bot)
    snap = counters_snapshot()
    assert EVT_AUDIT_ACTION_RECORDED in snap["subscribed_events"]
