"""Prefix/slash parity for the BTD6 ops cog.

The shared parity pin (``test_btd6_command_parity.py``) is hardcoded to
``btd6_cog.py``, so the ops cog needs its own sibling check: every prefix
subcommand of ``!btd6ops`` must have a matching ``/btd6ops`` slash subcommand
and vice versa.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from discord import app_commands

from cogs.btd6_ops_cog import BTD6OpsCog

_EXPECTED = {
    "readiness",
    "runs",
    "source_enable",
    "source_disable",
    "seed-data",
    "announcechannel",
}


def _cog() -> BTD6OpsCog:
    return BTD6OpsCog(bot=MagicMock())


def test_prefix_subcommands_match_expected() -> None:
    cog = _cog()
    leaves = {c.name for c in cog.walk_commands() if c.parent is not None}
    assert leaves == _EXPECTED


def test_slash_subcommands_match_expected() -> None:
    cog = _cog()
    leaves = {
        c.name
        for c in cog.walk_app_commands()
        if isinstance(c, app_commands.Command)
    }
    assert leaves == _EXPECTED


def test_prefix_and_slash_surfaces_are_in_parity() -> None:
    cog = _cog()
    prefix_leaves = {c.name for c in cog.walk_commands() if c.parent is not None}
    slash_leaves = {
        c.name
        for c in cog.walk_app_commands()
        if isinstance(c, app_commands.Command)
    }
    assert prefix_leaves == slash_leaves
