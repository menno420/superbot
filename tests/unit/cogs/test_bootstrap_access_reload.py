"""Reload-safety tests for ``cogs.bootstrap_access_cog``.

Pins:

* ``cog_unload`` removes the channel guard from the bot's check list
  so a subsequent ``setup()`` doesn't end up with two checks
  installed.
* ``setup()`` is defensively idempotent: when a previous
  BootstrapAccessCog left its guard installed (no clean unload), the
  remnant is cleaned up before the new check is installed, leaving
  exactly one ``_channel_guard`` registered.
* The cleanup distinguishes bootstrap-owned remnants from legacy
  ``bot1._channel_guard`` instances: only the latter is preserved as
  the cog's ``self._legacy_guard`` reference (which carries the
  ``_shutting_down`` flag).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from cogs.bootstrap_access_cog import (
    BootstrapAccessCog,
    _check_is_owned_by_bootstrap_cog,
    _find_channel_guard_checks,
    setup,
)


def _legacy_guard_fn():
    async def _channel_guard(ctx):  # noqa: ARG001
        return True
    _channel_guard.__globals__["_shutting_down"] = False
    return _channel_guard


def _make_bot(*initial_checks):
    bot = MagicMock(spec=commands.Bot)
    bot._checks = list(initial_checks)

    def _remove(check):
        if check in bot._checks:
            bot._checks.remove(check)

    def _add(check):
        bot._checks.append(check)

    bot.remove_check = MagicMock(side_effect=_remove)
    bot.add_check = MagicMock(side_effect=_add)
    bot.add_cog = AsyncMock()
    return bot


# ---------------------------------------------------------------------------
# _check_is_owned_by_bootstrap_cog
# ---------------------------------------------------------------------------


def test_check_owned_by_bootstrap_cog_detects_bound_method():
    bot = _make_bot()
    cog = BootstrapAccessCog(bot)
    assert _check_is_owned_by_bootstrap_cog(cog._channel_guard) is True


def test_check_owned_by_bootstrap_cog_rejects_function():
    legacy = _legacy_guard_fn()
    assert _check_is_owned_by_bootstrap_cog(legacy) is False


# ---------------------------------------------------------------------------
# cog_unload
# ---------------------------------------------------------------------------


def test_cog_unload_removes_channel_guard():
    bot = _make_bot()
    cog = BootstrapAccessCog(bot)
    bot._checks.append(cog._channel_guard)
    cog.cog_unload()
    assert cog._channel_guard not in bot._checks
    bot.remove_check.assert_called_once_with(cog._channel_guard)


def test_cog_unload_tolerates_remove_check_failure():
    """A bot whose remove_check raises (e.g. shutdown race) must not
    propagate the exception — production reload paths must stay
    resilient.
    """
    bot = _make_bot()
    bot.remove_check = MagicMock(side_effect=RuntimeError("bot already shutting down"))
    cog = BootstrapAccessCog(bot)
    # Should not raise.
    cog.cog_unload()


# ---------------------------------------------------------------------------
# setup() — first load (no remnants)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_load_installs_exactly_one_check_when_no_legacy_present():
    bot = _make_bot()
    await setup(bot)
    channel_guards = _find_channel_guard_checks(bot)
    assert len(channel_guards) == 1
    # The installed check belongs to a BootstrapAccessCog.
    assert _check_is_owned_by_bootstrap_cog(channel_guards[0]) is True


@pytest.mark.asyncio
async def test_first_load_removes_legacy_guard_from_bot_checks():
    """LP-2: the legacy ``bot1._channel_guard`` is removed at load time.
    The cog no longer captures a reference to it; the shutdown signal
    is owned by ``core.runtime.lifecycle`` instead.
    """
    legacy = _legacy_guard_fn()
    bot = _make_bot(legacy)
    await setup(bot)

    cog_arg = bot.add_cog.await_args.args[0]
    assert isinstance(cog_arg, BootstrapAccessCog)
    # Legacy guard is gone; only the new bootstrap check is registered.
    assert legacy not in bot._checks
    assert _find_channel_guard_checks(bot)[0] is not legacy


# ---------------------------------------------------------------------------
# setup() — reload (bootstrap remnant present)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reload_cleans_bootstrap_remnant_before_installing_new_check():
    """A previous load left its check installed; the second load
    removes the remnant + the legacy guard (if any) and installs
    exactly one new check.
    """
    bot = _make_bot()
    # Simulate a previous load that didn't unload cleanly.
    prev_cog = BootstrapAccessCog(bot)
    bot._checks.append(prev_cog._channel_guard)

    await setup(bot)

    channel_guards = _find_channel_guard_checks(bot)
    assert len(channel_guards) == 1
    # The surviving check is the NEW one — not the remnant.
    assert channel_guards[0] is not prev_cog._channel_guard
    # And the remnant was removed.
    assert prev_cog._channel_guard not in bot._checks


@pytest.mark.asyncio
async def test_reload_with_remnant_and_legacy_keeps_only_new_check():
    """Both a bootstrap remnant AND a legacy guard present (worst case);
    setup cleans both and installs exactly one check (LP-2: no
    legacy-guard reference is captured any more — lifecycle owns the
    shutdown signal).
    """
    bot = _make_bot()
    prev_cog = BootstrapAccessCog(bot)
    legacy = _legacy_guard_fn()
    bot._checks.append(legacy)
    bot._checks.append(prev_cog._channel_guard)

    await setup(bot)

    channel_guards = _find_channel_guard_checks(bot)
    assert len(channel_guards) == 1
    assert channel_guards[0] is not prev_cog._channel_guard
    assert channel_guards[0] is not legacy
    assert legacy not in bot._checks
    assert prev_cog._channel_guard not in bot._checks


@pytest.mark.asyncio
async def test_reload_removes_remnant_when_no_legacy_present():
    """LP-2: with only a bootstrap remnant in place, setup() still
    removes the remnant and installs exactly one new check.
    """
    bot = _make_bot()
    prev_cog = BootstrapAccessCog(bot)
    bot._checks.append(prev_cog._channel_guard)

    await setup(bot)

    channel_guards = _find_channel_guard_checks(bot)
    assert len(channel_guards) == 1
    assert prev_cog._channel_guard not in bot._checks


# ---------------------------------------------------------------------------
# unload → reload round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unload_then_reload_keeps_exactly_one_check():
    """Mimic a clean reload: first load, then unload, then load again.
    Across the round-trip exactly one ``_channel_guard`` is registered.
    """
    bot = _make_bot()
    await setup(bot)
    cog = bot.add_cog.await_args.args[0]
    cog.cog_unload()
    assert _find_channel_guard_checks(bot) == []

    bot.add_cog = AsyncMock()
    await setup(bot)
    assert len(_find_channel_guard_checks(bot)) == 1
