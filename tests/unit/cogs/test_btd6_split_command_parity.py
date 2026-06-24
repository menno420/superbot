"""Backward-compat pins for the hidden BTD6 prefix-alias groups.

The BTD6 command surface was unified under one ``/btd6`` tree
(:mod:`cogs.btd6._unified`, owner request 2026-06-24): the old per-cog SLASH
groups were removed, but each sibling cog keeps its original PREFIX group as a
*hidden* alias so existing ``!btd6ref …`` / ``!btd6events …`` / ``!btd6strat …``
muscle-memory still works. This locks that:

* each alias group still exposes its full leaf set (no command silently lost in
  the move), and
* the group is ``hidden`` (not advertised in ``!help`` — the canonical surface
  is ``!btd6 <action>``).

The unified surface's own prefix↔slash parity is covered by
``test_btd6_command_parity.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from discord.ext import commands

from cogs.btd6_events_cog import BTD6EventsCog
from cogs.btd6_reference_cog import BTD6ReferenceCog
from cogs.btd6_strategy_cog import BTD6StrategyCog

_EXPECTED: dict[type[commands.Cog], set[str]] = {
    BTD6ReferenceCog: {"tower", "hero", "round", "relic", "ct", "income", "rbe"},
    BTD6EventsCog: {
        "live",
        "event",
        "leaderboard",
        "sources",
        "source-health",
        "latest-data",
        "refresh-source",
        "grounding",
    },
    BTD6StrategyCog: {
        "browse",
        "mine",
        "strategy",
        "strategy-audit",
        "submit",
        "pending",
        "strategies",
        "why-no-response",
    },
}

# The top-level (hidden) alias group each cog registers.
_ALIAS_GROUP: dict[type[commands.Cog], str] = {
    BTD6ReferenceCog: "btd6ref",
    BTD6EventsCog: "btd6events",
    BTD6StrategyCog: "btd6strat",
}


def _prefix_leaves(cog: commands.Cog) -> set[str]:
    return {c.name for c in cog.walk_commands() if not isinstance(c, commands.Group)}


def _top_group(cog: commands.Cog) -> commands.Group:
    return next(
        c
        for c in cog.walk_commands()
        if isinstance(c, commands.Group) and c.parent is None
    )


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_hidden_alias_prefix_leaves_match_expected(cls: type[commands.Cog]) -> None:
    assert _prefix_leaves(cls(bot=MagicMock())) == _EXPECTED[cls]


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_alias_group_is_hidden(cls: type[commands.Cog]) -> None:
    group = _top_group(cls(bot=MagicMock()))
    assert group.name == _ALIAS_GROUP[cls]
    assert group.hidden is True


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_cog_declares_no_slash_commands(cls: type[commands.Cog]) -> None:
    """The slash surface moved to the unified tree — the alias cogs are prefix-only."""
    from discord import app_commands

    cog = cls(bot=MagicMock())
    slash = [
        c for c in cog.walk_app_commands() if isinstance(c, app_commands.Command)
    ]
    assert slash == []
