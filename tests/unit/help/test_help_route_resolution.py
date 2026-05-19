"""Unit tests for :func:`cogs.help_cog._resolve_route` — the single
resolver shared by typed ``!help <name>`` and the Help dropdown.

The resolver normalizes the input name and returns one of five route
kinds: ``hub``, ``subsystem``, ``advanced``, ``command``, ``unknown``.
Typed Help and the dropdown both call this so the same name produces
the same destination regardless of entry point.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cogs import help_cog


def _bot(command_names: tuple[str, ...] = ()) -> MagicMock:
    bot = MagicMock()

    def _get_command(name: str):
        if name in command_names:
            cmd = MagicMock()
            cmd.name = name
            return cmd
        return None

    bot.get_command = _get_command
    return bot


# ---------------------------------------------------------------------------
# Advanced aliases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["advanced", "all", "commands", "all commands", "Advanced", "ALL"],
)
def test_advanced_aliases_resolve_to_advanced(name):
    route = help_cog._resolve_route(name, bot=_bot())
    assert route.kind == "advanced"


# ---------------------------------------------------------------------------
# Hub aliases — every committed hub
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected_hub"),
    [
        ("games", "games"),
        ("economy", "economy"),
        ("moderation", "moderation"),
        ("mod", "moderation"),
        ("community", "community"),
        ("utility", "utility"),
        ("admin", "admin"),
        ("settings", "settings"),
        ("platform", "diagnostic"),
        ("diagnostic", "diagnostic"),
        # Case-insensitive
        ("Games", "games"),
        ("PLATFORM", "diagnostic"),
        # Entry-command match (without leading !)
        ("adminmenu", "admin"),
        ("modmenu", "moderation"),
        ("utilitymenu", "utility"),
        ("economymenu", "economy"),
    ],
)
def test_hub_aliases_resolve_to_hub(name, expected_hub):
    route = help_cog._resolve_route(name, bot=_bot())
    assert route.kind == "hub", f"{name!r} did not resolve as hub"
    assert route.target == expected_hub


# ---------------------------------------------------------------------------
# Diagnostics subsystem aliases — must NOT route to Platform hub
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["diagnostics", "diag", "Diagnostics", "DIAG"])
def test_diagnostics_aliases_resolve_to_diagnostic_subsystem(name):
    """The subsystem alias overrides run before the hub match so plural
    "diagnostics" and short "diag" stay on the Diagnostics Hub via the
    generic ``build_help_menu_view`` hook (the singular "diagnostic" and
    "platform" continue to open the Platform Hub).
    """
    route = help_cog._resolve_route(name, bot=_bot())
    assert route.kind == "subsystem"
    assert route.target == "diagnostic"


# ---------------------------------------------------------------------------
# Subsystem keys with build_help_menu_view → subsystem route
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "blackjack",
        "mining",
        "inventory",
        "leaderboard",
        "cleanup",
        "logging",
        "channel",
        "proof_channel",
        "xp",
        "rps_tournament",
        "deathmatch",
        "counting",
        "chain",
    ],
)
def test_subsystem_keys_resolve_to_subsystem(name):
    route = help_cog._resolve_route(name, bot=_bot())
    assert route.kind == "subsystem"
    assert route.target == name


def test_role_subsystem_resolves_to_role():
    route = help_cog._resolve_route("role", bot=_bot())
    assert route.kind == "subsystem"
    assert route.target == "role"


# ---------------------------------------------------------------------------
# Command name route
# ---------------------------------------------------------------------------


def test_command_name_resolves_to_command():
    """When no hub/subsystem matches but the name is a real command,
    resolve to the command route (single-command help embed).
    """
    bot = _bot(command_names=("daily",))
    route = help_cog._resolve_route("daily", bot=bot)
    # ``daily`` is not a hub key or subsystem key today — it's a command
    # owned by the economy cog. The resolver should fall through to the
    # command branch.
    assert route.kind == "command"
    assert route.target == "daily"


# ---------------------------------------------------------------------------
# Unknown fallback
# ---------------------------------------------------------------------------


def test_unknown_name_resolves_to_unknown():
    route = help_cog._resolve_route("not-a-real-thing", bot=_bot())
    assert route.kind == "unknown"


def test_empty_name_resolves_to_unknown():
    route = help_cog._resolve_route("", bot=_bot())
    assert route.kind == "unknown"
