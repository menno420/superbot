"""SuperBot must advertise its own capabilities (and games) when introducing itself.

Live behaviour (owner screenshot, 2026-06-20): asked "@SuperBot introduce
yourself", the bot produced a generic "server management + BTD6 support" blurb
and never mentioned the games it runs, the economy, or progression. The static
persona only framed scope around BTD6 + server management, and an introduction
matched no command-catalog trigger, so nothing taught the model the breadth of
what the bot actually offers.

The instruction stack now carries an always-present capability overview that
tells the model how to introduce itself and lists the real feature areas —
including the available games. These tests pin that overview (and its presence
in every assembled system prompt) so the regression can't silently return.
"""

from __future__ import annotations

import pytest

from services import ai_instruction_service as instr


def test_capabilities_overview_describes_how_to_introduce_itself():
    overview = instr._CAPABILITIES_OVERVIEW
    lowered = overview.lower()
    # The clause must fire on introduction / overview phrasings.
    assert "introduce yourself" in lowered
    assert "what you can do" in lowered
    # And steer toward a brief, grouped overview rather than a command dump.
    assert "concise" in lowered
    assert "!help" in overview


def test_capabilities_overview_lists_the_available_games():
    """The owner asked specifically for "which games are available" — the
    overview must name the real games the bot runs."""
    overview = instr._CAPABILITIES_OVERVIEW
    for game in ("Blackjack", "Rock Paper Scissors", "Deathmatch", "Mining", "Fishing"):
        assert game in overview, game


def test_capabilities_overview_covers_the_main_feature_areas():
    overview = instr._CAPABILITIES_OVERVIEW
    lowered = overview.lower()
    # General assistant + BTD6 expertise.
    assert "general-purpose assistant" in lowered
    assert "bloons td 6" in lowered
    # Economy / progression.
    assert "coin economy" in lowered
    assert "leaderboards" in lowered
    # Server management.
    assert "server management" in lowered


def test_capabilities_overview_keeps_btd6_overview_grounding_safe():
    """An introduction is a GENERAL_NL_ANSWER turn, and naming "Bloons TD 6"
    makes the BTD6 faithfulness guard run over the reply. The overview must
    tell the model to keep its BTD6 mention general (no ungrounded tower / hero
    / paragon names or numbers) so a friendly intro is never floored to the
    no-data refusal."""
    overview = instr._CAPABILITIES_OVERVIEW
    lowered = overview.lower()
    assert "do not name specific towers, heroes, or paragons" in lowered
    assert "never invent commands or features" in lowered


@pytest.mark.asyncio
async def test_assembled_system_prompt_carries_capabilities_overview():
    """Every turn's system prompt (built by assemble) carries the overview —
    assemble always includes it in the system layer, with no DB or guild
    profile required."""
    stack = await instr.assemble(
        guild_id=1,
        user_message="introduce yourself",
        profile_ids=(),
    )
    sys_prompt = stack.render_system_prompt()
    assert "The main things you can do on this server" in sys_prompt
    assert "Blackjack" in sys_prompt
    assert "general-purpose assistant" in sys_prompt
