"""Pin the shape of the unified ``/btd6`` command tree (owner request, 2026-06-24).

The five separate BTD6 command groups (``btd6`` / ``btd6ref`` / ``btd6ops`` /
``btd6strat`` / ``btd6events``) were collapsed into one ``/btd6`` (and ``!btd6``)
tree in the **"Flattest"** layout: everyday lookups sit flat, the bigger buckets
nest one level (``strat`` / ``ops`` / ``events``). This locks that shape so a
later edit can't silently re-split it or push it past Discord's 25-per-group cap.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _unified

_FLAT_LOOKUPS = {
    "income",
    "rbe",
    "round",
    "tower",
    "hero",
    "relic",
    "ct",
    "ask",
    "estimate",
    "status",
    "diagnostics",
    "test-intent",
}
_SUBGROUPS = {"strat", "ops", "events"}

_STRAT = {
    "browse",
    "mine",
    "strategy",
    "strategy-audit",
    "submit",
    "pending",
    "strategies",
    "why-no-response",
}
_OPS = {
    "readiness",
    "runs",
    "source_enable",
    "source_disable",
    "seed-data",
    "announcechannel",
}
_EVENTS = {
    "live",
    "event",
    "leaderboard",
    "sources",
    "source-health",
    "latest-data",
    "refresh-source",
    "grounding",
}


def test_root_is_one_btd6_group() -> None:
    assert isinstance(_unified.btd6_app, app_commands.Group)
    assert _unified.btd6_app.name == "btd6"
    assert isinstance(_unified.btd6_prefix, commands.Group)
    assert _unified.btd6_prefix.name == "btd6"


def test_slash_top_level_is_flat_lookups_plus_subgroups() -> None:
    top = {c.name for c in _unified.btd6_app.commands}
    assert top == _FLAT_LOOKUPS | _SUBGROUPS
    # Discord caps a single slash group at 25 children — the whole point of the
    # Flattest layout is that 33 actions fit by nesting the three big buckets.
    assert len(top) <= 25


def test_subgroups_are_groups_within_cap() -> None:
    by_name = {c.name: c for c in _unified.btd6_app.commands}
    for name in _SUBGROUPS:
        sub = by_name[name]
        assert isinstance(sub, app_commands.Group)
        assert len(list(sub.commands)) <= 25


def test_flat_lookups_are_leaves_not_groups() -> None:
    by_name = {c.name: c for c in _unified.btd6_app.commands}
    for name in _FLAT_LOOKUPS:
        assert isinstance(by_name[name], app_commands.Command)


def test_subgroup_leaves_match_expected() -> None:
    by_name = {c.name: c for c in _unified.btd6_app.commands}
    assert {c.name for c in by_name["strat"].commands} == _STRAT
    assert {c.name for c in by_name["ops"].commands} == _OPS
    assert {c.name for c in by_name["events"].commands} == _EVENTS


def test_prefix_mirrors_slash_plus_ctteam() -> None:
    slash_top = {c.name for c in _unified.btd6_app.commands}
    prefix_top = {c.name for c in _unified.btd6_prefix.commands}
    # ctteam is prefix-only (pasting a long bracket URL suits the prefix surface).
    assert prefix_top == slash_top | {"ctteam"}


def test_register_is_idempotent() -> None:
    bot = MagicMock()
    bot.tree.get_command = MagicMock(return_value=None)
    bot.get_command = MagicMock(return_value=None)

    _unified.register(bot)
    bot.tree.add_command.assert_called_once_with(_unified.btd6_app)
    bot.add_command.assert_called_once_with(_unified.btd6_prefix)

    # Second call when the commands already exist must NOT double-register.
    bot.tree.get_command = MagicMock(return_value=_unified.btd6_app)
    bot.get_command = MagicMock(return_value=_unified.btd6_prefix)
    bot.tree.add_command.reset_mock()
    bot.add_command.reset_mock()

    _unified.register(bot)
    bot.tree.add_command.assert_not_called()
    bot.add_command.assert_not_called()
