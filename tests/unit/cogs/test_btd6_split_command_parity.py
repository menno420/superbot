"""Per-cog leaf-set pins for the split BTD6 command surface.

Locks *which* commands live on each sibling cog carved out of ``btd6_cog``,
so a command can't silently move to the wrong cog or disappear, and that each
cog's prefix and slash leaves stay in parity. Mirrors
``test_btd6_ops_command_parity.py`` for the reference / events / strategy
cogs. The mother cog's residual surface + cross-cog twin/backbone parity are
covered by ``test_btd6_cog.py`` and ``test_btd6_command_parity.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from discord import app_commands
from discord.ext import commands

from cogs.btd6_events_cog import BTD6EventsCog
from cogs.btd6_reference_cog import BTD6ReferenceCog
from cogs.btd6_strategy_cog import BTD6StrategyCog

_EXPECTED: dict[type[commands.Cog], set[str]] = {
    BTD6ReferenceCog: {"tower", "hero", "round", "relic", "ct"},
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


def _prefix_leaves(cog: commands.Cog) -> set[str]:
    return {c.name for c in cog.walk_commands() if not isinstance(c, commands.Group)}


def _slash_leaves(cog: commands.Cog) -> set[str]:
    return {
        c.name
        for c in cog.walk_app_commands()
        if isinstance(c, app_commands.Command)
    }


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_prefix_leaves_match_expected(cls: type[commands.Cog]) -> None:
    assert _prefix_leaves(cls(bot=MagicMock())) == _EXPECTED[cls]


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_slash_leaves_match_expected(cls: type[commands.Cog]) -> None:
    assert _slash_leaves(cls(bot=MagicMock())) == _EXPECTED[cls]


@pytest.mark.parametrize("cls", list(_EXPECTED))
def test_prefix_and_slash_in_parity(cls: type[commands.Cog]) -> None:
    cog = cls(bot=MagicMock())
    assert _prefix_leaves(cog) == _slash_leaves(cog)
