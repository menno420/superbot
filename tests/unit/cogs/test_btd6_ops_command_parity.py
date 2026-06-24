"""Backward-compat pin for the hidden ``!btd6ops`` prefix-alias group.

The BTD6 ops slash surface moved to the unified ``/btd6 ops …`` tree
(:mod:`cogs.btd6._unified`, owner request 2026-06-24); the ops cog keeps
``!btd6ops`` as a *hidden* prefix alias so existing operator muscle-memory still
works. This locks that the alias still exposes its full leaf set, is hidden, and
declares no slash of its own (parity for the unified surface is covered by
``test_btd6_command_parity.py``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from discord import app_commands
from discord.ext import commands

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


def test_alias_group_is_hidden() -> None:
    cog = _cog()
    group = next(
        c
        for c in cog.walk_commands()
        if isinstance(c, commands.Group) and c.parent is None
    )
    assert group.name == "btd6ops"
    assert group.hidden is True


def test_cog_declares_no_slash_commands() -> None:
    cog = _cog()
    slash = [
        c for c in cog.walk_app_commands() if isinstance(c, app_commands.Command)
    ]
    assert slash == []
