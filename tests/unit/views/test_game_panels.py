"""Phase 7 Option A — router-only Blackjack/RPS panel tests.

Pins:

* The panels contain only navigation/embed-swap logic — no game-engine
  imports.
* Each cog's ``build_help_menu_view`` now returns the new panel
  (not an empty View as it did pre-Phase 7).
* Practice / Replay / Best-of variants are not yet present — their
  buttons should NOT exist; a re-introduction must be deliberate.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.games import blackjack_panel, rps_panel


def _author(id_: int = 1) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    member.display_name = "Test"
    return member


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Module-level invariants — no game logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path",
    [
        Path(blackjack_panel.__file__),
        Path(rps_panel.__file__),
    ],
    ids=["blackjack_panel", "rps_panel"],
)
def test_panel_modules_do_not_import_game_engines(module_path: Path):
    """The panels are pure navigation. Importing the blackjack engine,
    economy service, persistence, or tournament state from a panel
    would mean game logic crept in.
    """
    src = module_path.read_text()
    head = src.split("\ndef ", 1)[0]  # module-import section
    forbidden = [
        "blackjack_engine",
        "economy_service",
        "game_state_service",
        "from cogs.blackjack._persistence",
        "from cogs.blackjack._state",
        "from cogs.rps_tournament._persistence",
    ]
    for token in forbidden:
        assert token not in head, (
            f"{module_path.name} imports game-engine token {token!r} at module "
            f"load — Phase 7 Option A keeps panels router-only."
        )


# ---------------------------------------------------------------------------
# Blackjack panel — view shape
# ---------------------------------------------------------------------------


def test_blackjack_overview_embed_lists_modes_and_typed_shortcuts():
    embed = blackjack_panel.build_blackjack_overview_embed()
    title = (embed.title or "")
    assert "Blackjack" in title
    description = (embed.description or "") + "\n".join(
        f.value for f in embed.fields
    ) + (embed.footer.text or "")
    assert "Classic" in description
    assert "Rules" in description
    assert "!blackjack" in description or "!bj" in description


def test_blackjack_panel_buttons_are_classic_rules_overview_only():
    view = blackjack_panel.BlackjackPanelView(_author())
    custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "blackjack_panel:classic",
        "blackjack_panel:rules",
        "blackjack_panel:overview",
    }


def test_blackjack_panel_has_no_practice_or_replay_button_yet():
    """Phase 7b is the place for Practice / Replay. Phase 7a panels
    must not pre-leak those button labels.
    """
    view = blackjack_panel.BlackjackPanelView(_author())
    labels = [
        (c.label or "")
        for c in view.children
        if isinstance(c, discord.ui.Button)
    ]
    for token in ("Practice", "Replay", "Change Mode"):
        assert not any(token in lbl for lbl in labels), (
            f"BlackjackPanelView already exposes {token!r} — Phase 7b "
            "should re-introduce these together with engine support."
        )


@pytest.mark.asyncio
async def test_blackjack_classic_button_renders_classic_embed():
    view = blackjack_panel.BlackjackPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "blackjack_panel:classic"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    assert "Classic" in (embed.title or "")
    rendered = "\n".join(f.value for f in embed.fields)
    assert "!blackjack" in rendered or "!bj" in rendered


@pytest.mark.asyncio
async def test_blackjack_rules_button_renders_rules_embed():
    view = blackjack_panel.BlackjackPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "blackjack_panel:rules"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    assert "Rules" in (embed.title or "")
    rendered = "\n".join(f.value for f in embed.fields)
    assert "Hit" in rendered or "Stand" in rendered


@pytest.mark.asyncio
async def test_blackjack_overview_button_returns_to_overview():
    view = blackjack_panel.BlackjackPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "blackjack_panel:overview"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    # Overview embed names "Modes" as a field; the detail embeds don't.
    field_names = [f.name for f in embed.fields]
    assert "Modes" in field_names


# ---------------------------------------------------------------------------
# RPS panel
# ---------------------------------------------------------------------------


def test_rps_overview_embed_lists_single_tournament_rules():
    embed = rps_panel.build_rps_overview_embed()
    rendered = (embed.description or "") + "\n".join(
        f.value for f in embed.fields
    ) + (embed.footer.text or "")
    assert "Single Round" in rendered
    assert "Tournament" in rendered
    assert "Rules" in rendered
    assert "!rps" in rendered


def test_rps_panel_buttons_are_single_tournament_rules_overview():
    view = rps_panel.RPSPanelView(_author())
    custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "rps_panel:single",
        "rps_panel:tournament",
        "rps_panel:rules",
        "rps_panel:overview",
    }


def test_rps_panel_has_no_replay_or_best_of_button_yet():
    view = rps_panel.RPSPanelView(_author())
    labels = [
        (c.label or "")
        for c in view.children
        if isinstance(c, discord.ui.Button)
    ]
    for token in ("Replay", "Best of"):
        assert not any(token in lbl for lbl in labels)


@pytest.mark.asyncio
async def test_rps_single_button_renders_single_embed():
    view = rps_panel.RPSPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "rps_panel:single"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    assert "Single Round" in (embed.title or "")


@pytest.mark.asyncio
async def test_rps_tournament_button_renders_tournament_embed():
    view = rps_panel.RPSPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "rps_panel:tournament"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    assert "Tournament" in (embed.title or "")
    rendered = "\n".join(f.value for f in embed.fields)
    assert "!rpsregister" in rendered or "!rpsstart" in rendered


@pytest.mark.asyncio
async def test_rps_rules_button_renders_rules_embed():
    view = rps_panel.RPSPanelView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "rps_panel:rules"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    assert "Rules" in (embed.title or "")


# ---------------------------------------------------------------------------
# Cog wiring — build_help_menu_view now returns the panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blackjack_cog_build_help_menu_view_returns_panel():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog(bot=MagicMock())
    interaction = MagicMock()
    interaction.user = _author()
    embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, blackjack_panel.BlackjackPanelView)
    assert "Blackjack" in (embed.title or "")


@pytest.mark.asyncio
async def test_rps_cog_build_help_menu_view_returns_panel():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog(bot=MagicMock())
    interaction = MagicMock()
    interaction.user = _author()
    embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, rps_panel.RPSPanelView)
    assert (
        "Rock-Paper-Scissors" in (embed.title or "")
        or "RPS" in (embed.title or "")
    )
