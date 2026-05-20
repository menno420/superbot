"""PR 3 — Rock Paper Scissors display rename + alias pins.

The canonical subsystem key remains ``rps_tournament`` (no second
active SUBSYSTEMS entry is added — see §13 acceptance checklist of
the operating-contract plan). What changes:

* Display name: ``"RPS Tournament"`` → ``"Rock Paper Scissors"``.
* Help aliases: ``rps``, ``rock paper scissors``, and ``rps_tournament``
  all resolve to the same subsystem panel.
* Class rename: ``RPSTournamentCog`` → ``RockPaperScissorsCog`` with a
  back-compat alias keeping the old name importable.
* User-facing labels in the panel embed + tournament UI use the new
  spelling.

What does **not** change:

* The ``"rps_tournament"`` key in :data:`SUBSYSTEMS`.
* Tournament state ``kind="rps"`` in
  :mod:`services.tournament_state_service`.
* The leaderboard / rank-provider name ``"rps"``.
* Existing prefix commands (``!rps``, ``!rpsregister``, ``!rpsstart``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from discord.ext import commands

from cogs.help.route import resolve_route
from utils.subsystem_registry import SUBSYSTEMS
from views.games.hub import discover_game_children


def _bot_without_rps_command() -> MagicMock:
    """A bot mock whose ``get_command`` returns ``None`` so a
    fallthrough into the command branch would short-circuit on an
    explicit None and not mask the override / SUBSYSTEMS-loop match.
    """
    bot = MagicMock(spec=commands.Bot)
    bot.get_command = MagicMock(return_value=None)
    return bot


# ---------------------------------------------------------------------------
# Registry — display name + no duplicate active entry
# ---------------------------------------------------------------------------


def test_rps_subsystem_display_name_is_rock_paper_scissors():
    assert SUBSYSTEMS["rps_tournament"]["display_name"] == "Rock Paper Scissors"


def test_no_second_active_rps_subsystem_entry():
    """The canonical key stays ``rps_tournament``. A second active entry
    keyed ``rps`` would duplicate Games-hub children, readiness rows,
    settings schema entries, and rank-provider registrations — see the
    operating-contract plan §13 acceptance checklist.
    """
    assert "rps" not in SUBSYSTEMS, (
        "A second active SUBSYSTEMS entry keyed 'rps' would create "
        "duplicate Games-hub children / readiness rows. Canonical key "
        "for this sweep is 'rps_tournament' — see plan §13."
    )


def test_rps_appears_exactly_once_in_games_hub():
    children = discover_game_children()
    rps_entries = [
        (name, meta)
        for name, meta in children
        if "rps" in name.lower()
        or "rock paper" in (meta.get("display_name") or "").lower()
    ]
    assert len(rps_entries) == 1, (
        f"Games hub must show exactly one RPS entry; found "
        f"{[name for name, _ in rps_entries]}. Plan §13 forbids "
        "duplicate visible RPS surfaces."
    )
    name, meta = rps_entries[0]
    assert name == "rps_tournament"
    assert meta["display_name"] == "Rock Paper Scissors"


# ---------------------------------------------------------------------------
# Help route resolution — three aliases, one target
# ---------------------------------------------------------------------------


def test_help_resolves_rps_to_rps_tournament_subsystem():
    """``!help rps`` must open the Rock Paper Scissors panel rather
    than the single-command help for ``!rps``. The
    SUBSYSTEM_ALIAS_OVERRIDES branch handles this; without the
    override the resolver would fall through to ``bot.get_command
    ("rps")`` which returns the ``!rps`` command.
    """
    bot = _bot_without_rps_command()
    route = resolve_route("rps", bot=bot)
    assert route.kind == "subsystem"
    assert route.target == "rps_tournament"


def test_help_resolves_rock_paper_scissors_to_rps_tournament_subsystem():
    bot = _bot_without_rps_command()
    route = resolve_route("rock paper scissors", bot=bot)
    assert route.kind == "subsystem"
    assert route.target == "rps_tournament"


def test_help_resolves_rps_tournament_to_rps_tournament_subsystem():
    """Legacy name keeps working — back-compat for operators who type
    the old display name.
    """
    bot = _bot_without_rps_command()
    route = resolve_route("rps_tournament", bot=bot)
    assert route.kind == "subsystem"
    assert route.target == "rps_tournament"


def test_help_resolution_is_case_insensitive():
    bot = _bot_without_rps_command()
    for variant in ("RPS", "Rps", "Rock Paper Scissors", "ROCK PAPER SCISSORS"):
        route = resolve_route(variant, bot=bot)
        assert route.kind == "subsystem", f"variant {variant!r}: {route!r}"
        assert route.target == "rps_tournament", (
            f"variant {variant!r}: {route!r}"
        )


def test_all_three_rps_aliases_resolve_to_same_target():
    """Symmetry pin: every alias must produce the same routed target so
    the user-visible panel is identical regardless of how they typed
    it.
    """
    bot = _bot_without_rps_command()
    targets = {
        resolve_route(name, bot=bot).target
        for name in ("rps", "rock paper scissors", "rps_tournament")
    }
    assert targets == {"rps_tournament"}


# ---------------------------------------------------------------------------
# Class rename + back-compat alias
# ---------------------------------------------------------------------------


def test_rock_paper_scissors_cog_class_exists():
    from cogs.rps_tournament_cog import RockPaperScissorsCog

    assert RockPaperScissorsCog is not None


def test_legacy_rps_tournament_cog_alias_still_importable():
    """Back-compat: old imports continue to resolve to the renamed
    class without code changes anywhere else.
    """
    from cogs.rps_tournament_cog import RockPaperScissorsCog, RPSTournamentCog

    assert RPSTournamentCog is RockPaperScissorsCog


def test_cog_name_attribute_uses_rock_paper_scissors_display():
    """discord.py's ``commands.Cog`` ``name=`` attribute drives the cog
    registry key (``bot.cogs[...]``) and the help-page section header.
    PR 3 updates it from "Rock-Paper-Scissors Tournament" to "Rock
    Paper Scissors".
    """
    from cogs.rps_tournament_cog import RockPaperScissorsCog

    # ``commands.Cog`` stores the name attribute on the class via the
    # ``name=`` kwarg in its metaclass; check via the underscored attr
    # discord.py uses internally.
    name_attr = getattr(RockPaperScissorsCog, "__cog_name__", None)
    assert name_attr == "Rock Paper Scissors", (
        f"Cog name attribute is {name_attr!r}; expected 'Rock Paper "
        "Scissors'."
    )


# ---------------------------------------------------------------------------
# Out-of-scope state stays untouched
# ---------------------------------------------------------------------------


def test_tournament_state_kind_value_rps_still_valid():
    """The tournament-state service uses ``kind="rps"`` (short form,
    not ``"rps_tournament"``). PR 3 must not change this; the
    canonical-key migration is deferred per plan §12.
    """
    from services.tournament_state_service import _VALID_KINDS

    assert "rps" in _VALID_KINDS


def test_rank_provider_rps_name_unchanged():
    """The leaderboard / rank provider uses ``name = "rps"``. PR 3 must
    not change it; rank-provider aliases are deferred state.
    """
    from services.rank_providers import RpsProvider

    assert RpsProvider.name == "rps"
