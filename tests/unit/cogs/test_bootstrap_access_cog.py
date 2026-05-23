"""Behavior tests for ``cogs.bootstrap_access_cog``.

These pin the runtime wiring that PR #220 introduced:

* ``setup(bot)`` removes the legacy ``_channel_guard`` registered by
  ``bot1.py`` and installs the fresh-guild-aware guard in its place.
* The new guard preserves the historical contract:
    - inside ``config.ALLOWED_CHANNELS`` → allow;
    - ``!force`` → allow regardless of channel;
    - guild operators on bootstrap commands → allow even outside
      ``ALLOWED_CHANNELS``;
    - everyone else outside ``ALLOWED_CHANNELS`` → deny.
* The legacy ``_shutting_down`` flag is still honored when its source
  module is reachable through the captured legacy guard.
* The cog's ``on_command_error`` listener surfaces ``MissingPermissions``
  for bootstrap commands invoked outside allowed channels (so guild
  operators see why a command was refused after the channel guard let it
  through to the permission check).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

import config
from cogs.bootstrap_access_cog import (
    BootstrapAccessCog,
    _find_channel_guard_checks,
    setup,
)


def _legacy_channel_guard_factory(shutting_down: bool = False):
    """Build a stand-in for the ``bot1._channel_guard`` global check."""

    async def _channel_guard(ctx):  # noqa: ARG001 — name-shape matters
        return not shutting_down

    _channel_guard.__globals__["_shutting_down"] = shutting_down
    return _channel_guard


def _make_bot_with_legacy_guard(shutting_down: bool = False):
    """Mimic the state ``bot1.py`` leaves the bot in before cog load."""
    bot = MagicMock(spec=commands.Bot)
    legacy = _legacy_channel_guard_factory(shutting_down=shutting_down)
    bot._checks = [legacy]
    removed: list = []

    def _remove(check):
        bot._checks.remove(check)
        removed.append(check)

    added: list = []

    def _add(check):
        bot._checks.append(check)
        added.append(check)

    bot.remove_check = MagicMock(side_effect=_remove)
    bot.add_check = MagicMock(side_effect=_add)
    bot.add_cog = AsyncMock()
    bot._removed_checks = removed
    bot._added_checks = added
    return bot, legacy


def _ctx(
    *,
    channel_id: int,
    guild: object | None = None,
    command_name: str = "help",
    qualified_name: str | None = None,
    aliases: tuple[str, ...] = (),
    invoked_with: str | None = None,
    author_id: int = 10,
    owner_id: int = 10,
    administrator: bool = False,
    manage_guild: bool = False,
):
    if guild is None:
        guild = SimpleNamespace(owner_id=owner_id)
    author = SimpleNamespace(
        id=author_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=manage_guild,
        ),
    )
    command = SimpleNamespace(
        name=command_name,
        qualified_name=qualified_name or command_name,
        aliases=aliases,
    )
    send = AsyncMock()
    bot = SimpleNamespace(is_owner=AsyncMock(return_value=False))
    return SimpleNamespace(
        guild=guild,
        channel=SimpleNamespace(id=channel_id),
        author=author,
        command=command,
        invoked_with=invoked_with or command_name,
        bot=bot,
        send=send,
    )


# ---------------------------------------------------------------------------
# setup() — replacement contract
# ---------------------------------------------------------------------------


async def test_setup_removes_legacy_channel_guard_and_installs_replacement():
    bot, legacy = _make_bot_with_legacy_guard()

    await setup(bot)

    assert legacy in bot._removed_checks, "setup() must remove the legacy guard"
    assert legacy not in bot._checks, "legacy guard must not remain registered"
    assert len(bot._added_checks) == 1, "setup() must install exactly one new check"
    new_guard = bot._added_checks[0]
    assert new_guard.__func__ is BootstrapAccessCog._channel_guard
    bot.add_cog.assert_awaited_once()
    installed_cog = bot.add_cog.await_args.args[0]
    assert isinstance(installed_cog, BootstrapAccessCog)
    # The cog instance that owns the new check must be the same cog
    # registered on the bot so listeners and check share state.
    assert new_guard.__self__ is installed_cog


async def test_setup_is_idempotent_when_no_legacy_guard_present():
    bot = MagicMock(spec=commands.Bot)
    bot._checks = []
    bot.remove_check = MagicMock(side_effect=bot._checks.remove)
    bot.add_check = MagicMock(side_effect=bot._checks.append)
    bot.add_cog = AsyncMock()

    await setup(bot)

    bot.remove_check.assert_not_called()
    assert len(bot._checks) == 1
    assert bot._checks[0].__func__ is BootstrapAccessCog._channel_guard


def test_find_channel_guard_checks_matches_by_name():
    legacy = _legacy_channel_guard_factory()
    unrelated = AsyncMock()
    unrelated.__name__ = "_other_check"
    bot = SimpleNamespace(_checks=[unrelated, legacy])

    found = _find_channel_guard_checks(bot)

    assert found == [legacy]


# ---------------------------------------------------------------------------
# _channel_guard — behavior preservation
# ---------------------------------------------------------------------------


async def test_channel_guard_allows_inside_allowed_channels(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", {12345})
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=12345, command_name="daily")

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_allows_force_outside_allowed_channels(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="force")

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_allows_guild_owner_for_bootstrap_command(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="setup", author_id=42, owner_id=42)

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_denies_normal_command_outside_allowed_channels(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="daily", author_id=42, owner_id=42)

    assert await cog._channel_guard(ctx) is False


async def test_channel_guard_denies_dm_context(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", {12345})
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=12345, guild=None, command_name="help")
    ctx.guild = None

    assert await cog._channel_guard(ctx) is False


async def test_channel_guard_blocks_when_lifecycle_is_shutting_down(monkeypatch):
    """LP-2: command admission consults
    :func:`core.runtime.lifecycle.can_accept_commands` (no longer the
    legacy ``_shutting_down`` attribute on the previous guard).
    """
    from core.runtime import lifecycle

    monkeypatch.setattr(config, "ALLOWED_CHANNELS", {12345})
    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("test")
    try:
        cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
        ctx = _ctx(channel_id=12345, command_name="help")

        assert await cog._channel_guard(ctx) is False
    finally:
        lifecycle.reset_for_tests()


# ---------------------------------------------------------------------------
# on_command_error — bootstrap-only feedback
# ---------------------------------------------------------------------------


async def test_on_command_error_replies_for_missing_permissions_on_bootstrap(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="settings")
    error = commands.MissingPermissions(["manage_guild"])

    await cog.on_command_error(ctx, error)

    ctx.send.assert_awaited()


async def test_on_command_error_silent_for_non_bootstrap_command(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="daily")
    error = commands.MissingPermissions(["manage_guild"])

    await cog.on_command_error(ctx, error)

    ctx.send.assert_not_called()


async def test_on_command_error_silent_inside_allowed_channels(monkeypatch):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", {12345})
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=12345, command_name="settings")
    error = commands.MissingPermissions(["manage_guild"])

    await cog.on_command_error(ctx, error)

    ctx.send.assert_not_called()


@pytest.mark.parametrize(
    ("error_factory", "expected_substring"),
    [
        (lambda: commands.BotMissingPermissions(["send_messages"]), "missing permissions"),
        (
            lambda: commands.MissingRequiredArgument(
                SimpleNamespace(name="user", displayed_name="user"),
            ),
            "Missing argument",
        ),
        (lambda: commands.BadArgument("nope"), "Bad argument"),
        (lambda: commands.CommandOnCooldown(SimpleNamespace(), 1.0, type=None), "cooldown"),
    ],
)
async def test_on_command_error_handles_each_known_error(
    monkeypatch,
    error_factory,
    expected_substring,
):
    monkeypatch.setattr(config, "ALLOWED_CHANNELS", set())
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="diagnostics")

    await cog.on_command_error(ctx, error_factory())

    ctx.send.assert_awaited()
    message = ctx.send.await_args.args[0]
    assert expected_substring.lower() in message.lower()
