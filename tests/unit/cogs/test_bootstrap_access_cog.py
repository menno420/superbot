"""Behavior tests for ``cogs.bootstrap_access_cog`` (post-PR-4).

These pin the runtime wiring around the central command-access guard:

* ``setup(bot)`` removes any leftover legacy / bootstrap-remnant
  ``_channel_guard`` and installs the cog's bound-method check exactly
  once.  This is the load-order invariant: the cog is loaded first in
  ``config.INITIAL_EXTENSIONS`` so the gate is in place before any
  other cog registers a command.
* The guard delegates to
  :func:`core.runtime.command_access.resolve_command_access`.  Tests
  mock the typed-accessor policy load so each scenario controls the
  effective per-guild mode without touching real DB or cache.
* ``!force`` is still admitted inline (admin escape hatch — the
  per-command ``@has_permissions(administrator=True)`` on the
  ``force`` definition is what makes the override admin-only).
* Denial with feedback posts the resolver-supplied message before
  returning ``False`` so the CheckFailure doesn't look like a silent
  crash to the operator (the regression PR-4 was written to fix).
* Lifecycle-drain denial is silent (no feedback in the payload —
  feedback would race the connection close).

The pre-PR-4 ``on_command_error`` listener is deleted; ``bot1.py``'s
error handler now surfaces user-facing replies in every channel, so
the listener's bootstrap-specific surface was redundant.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from cogs.bootstrap_access_cog import (
    BootstrapAccessCog,
    _find_channel_guard_checks,
    setup,
)
from utils.guild_config_accessors import CommandAccessPolicySnapshot


def _legacy_channel_guard_factory(shutting_down: bool = False):
    """Build a stand-in for the pre-PR-4 ``bot1._channel_guard`` global check.

    The legacy guard is gone from ``bot1.py`` post-PR-4, but
    ``setup()`` still sweeps any leftover check named
    ``_channel_guard`` so a hot-reload from an older codebase settles
    to a single check.  These factories let the cleanup tests exercise
    that branch.
    """

    async def _channel_guard(ctx):  # noqa: ARG001 — name-shape matters
        return not shutting_down

    return _channel_guard


def _make_bot_with_legacy_guard(shutting_down: bool = False):
    """Mimic the state a pre-PR-4 ``bot1.py`` would leave the bot in."""
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
    channel_id: int = 100,
    guild_id: int | None = 10,
    command_name: str = "blackjack",
    qualified_name: str | None = None,
    aliases: tuple[str, ...] = (),
    invoked_with: str | None = None,
    author_id: int = 10,
    owner_id: int = 10,
    administrator: bool = False,
    manage_guild: bool = False,
    is_bot_owner: bool = False,
):
    guild = (
        SimpleNamespace(id=guild_id, owner_id=owner_id)
        if guild_id is not None
        else None
    )
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
    bot = SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner))
    return SimpleNamespace(
        guild=guild,
        channel=SimpleNamespace(id=channel_id),
        author=author,
        command=command,
        invoked_with=invoked_with or command_name,
        bot=bot,
        send=send,
    )


def _patch_policy(monkeypatch, mode: str | None, *allowed_channels: int) -> None:
    """Stub the resolver's typed-accessor read so the policy lookup is
    controlled by the test rather than the real cache + DB.

    ``mode=None`` simulates an unconfigured guild (no policy row);
    pass a mode literal + channel IDs to simulate ``selected_channels``
    or other configured states.
    """
    snapshot = CommandAccessPolicySnapshot(
        mode=mode,
        allowed_channels=frozenset(allowed_channels),
    )
    monkeypatch.setattr(
        "utils.guild_config_accessors.get_command_access_policy",
        AsyncMock(return_value=snapshot),
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
# _channel_guard — admits via the resolver
# ---------------------------------------------------------------------------


async def test_channel_guard_admits_under_default_all_channels(monkeypatch):
    """Unconfigured guild → resolver returns ``allowed=True`` under the
    ``all_channels`` default, so a non-operator's normal command runs
    anywhere.  This is the fresh-guild fix: ``!bj`` works without any
    setup having been completed.
    """
    _patch_policy(monkeypatch, mode=None)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="blackjack")

    assert await cog._channel_guard(ctx) is True
    ctx.send.assert_not_called()


async def test_channel_guard_admits_inside_selected_channel(monkeypatch):
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=12345, command_name="blackjack")

    assert await cog._channel_guard(ctx) is True
    ctx.send.assert_not_called()


async def test_channel_guard_admits_force_under_restrictive_policy(monkeypatch):
    """``!force`` bypasses the resolver — preserves the legacy admin
    override semantics.  The per-command
    ``@has_permissions(administrator=True)`` decorator on ``force``
    is what makes the override admin-only; the cog only short-circuits
    so the override is reachable outside allowed channels.
    """
    _patch_policy(monkeypatch, "selected_channels")  # empty allowlist
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="force")

    assert await cog._channel_guard(ctx) is True
    ctx.send.assert_not_called()


# ---------------------------------------------------------------------------
# _channel_guard — bootstrap bypass preserved
# ---------------------------------------------------------------------------


async def test_channel_guard_allows_guild_owner_for_bootstrap_command(monkeypatch):
    """Bootstrap bypass: owner can run ``!setup`` under any policy, in
    any channel.  Resolver's BOOTSTRAP_BYPASS branch fires before the
    policy lookup.
    """
    _patch_policy(monkeypatch, "disabled_except_bootstrap")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="setup", author_id=42, owner_id=42)

    assert await cog._channel_guard(ctx) is True
    ctx.send.assert_not_called()


async def test_channel_guard_allows_administrator_for_bootstrap_command(monkeypatch):
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(
        channel_id=999,
        command_name="setup",
        author_id=99,
        owner_id=42,
        administrator=True,
    )

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_allows_manage_guild_for_bootstrap_command(monkeypatch):
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(
        channel_id=999,
        command_name="setup",
        author_id=99,
        owner_id=42,
        manage_guild=True,
    )

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_allows_bot_owner_for_bootstrap_command(monkeypatch):
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(
        channel_id=999,
        command_name="setup",
        author_id=99,
        owner_id=42,
        is_bot_owner=True,
    )

    assert await cog._channel_guard(ctx) is True


async def test_channel_guard_denies_non_operator_for_bootstrap_command(monkeypatch):
    """Bootstrap bypass requires operator/owner privilege.  A regular
    user running ``!setup`` outside allowed channels under
    ``selected_channels`` mode falls through to the channel check and
    is denied with feedback.
    """
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="setup", author_id=99, owner_id=42)

    assert await cog._channel_guard(ctx) is False


# ---------------------------------------------------------------------------
# _channel_guard — denial + feedback
# ---------------------------------------------------------------------------


async def test_channel_guard_denies_normal_command_outside_selected_channels(
    monkeypatch,
):
    """The core fresh-guild bug in reverse: in a guild that has
    deliberately configured ``selected_channels``, normal commands
    outside the allowlist must be denied — but with visible feedback,
    not the legacy silent CheckFailure.
    """
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="blackjack", author_id=42, owner_id=42)

    assert await cog._channel_guard(ctx) is False
    ctx.send.assert_awaited_once()
    message, kwargs = ctx.send.await_args.args[0], ctx.send.await_args.kwargs
    # Feedback must point operators at the recovery path.
    assert "channel" in message.lower() or "settings" in message.lower()
    # delete_after keeps the channel tidy under repeated denials.
    assert kwargs.get("delete_after") == 10


async def test_channel_guard_denies_normal_command_under_disabled_mode(monkeypatch):
    _patch_policy(monkeypatch, "disabled_except_bootstrap")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="blackjack", author_id=42, owner_id=42)

    assert await cog._channel_guard(ctx) is False
    ctx.send.assert_awaited_once()
    message = ctx.send.await_args.args[0]
    assert "!setup" in message or "settings" in message.lower()


async def test_channel_guard_tolerates_send_failure(monkeypatch):
    """If ``ctx.send`` raises (channel deleted mid-denial, missing
    permissions, etc.) the guard must still return False instead of
    propagating the exception up into the discord.py check chain.
    """
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(channel_id=999, command_name="blackjack")
    ctx.send = AsyncMock(side_effect=RuntimeError("send failed"))

    assert await cog._channel_guard(ctx) is False


async def test_channel_guard_denies_dm_context_silently(monkeypatch):
    """DM invocations: resolver returns ``allowed=False, feedback=None``
    so the guard denies without sending — DMs that opt into
    DM-friendly commands handle their own routing.
    """
    _patch_policy(monkeypatch, None)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    ctx = _ctx(guild_id=None, command_name="help")

    assert await cog._channel_guard(ctx) is False
    ctx.send.assert_not_called()


async def test_channel_guard_blocks_when_lifecycle_is_shutting_down(monkeypatch):
    """LP-2: command admission consults
    :func:`core.runtime.lifecycle.can_accept_commands` (the resolver
    runs the lifecycle check first; the channel-guard chain inherits
    this without needing its own duplicate check).

    No feedback under lifecycle drain — message would race the
    connection close.
    """
    from core.runtime import lifecycle

    _patch_policy(monkeypatch, None)
    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("test")
    try:
        cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
        ctx = _ctx(channel_id=12345, command_name="help")

        assert await cog._channel_guard(ctx) is False
        ctx.send.assert_not_called()
    finally:
        lifecycle.reset_for_tests()
