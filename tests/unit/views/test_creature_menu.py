"""Creatures menu — the interactive hub panel (completion cert #1/#2, Q-0209).

Pins that the Creatures panel reached via the Help hub / ``!creatures`` is a real
buttoned surface: Catch runs an encounter in place, Dex opens the element-filterable
browser, Challenge opens the opponent picker, Ladder renders the win ladder, and the
shared embed builders can't drift from the typed commands. Discord I/O + DB mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.creatures import CREATURES
from views.creature import (
    CreatureChallengeSelectView,
    CreatureDexView,
    CreatureMenuView,
    build_battletop_embed,
    build_catch_result_embed,
    build_dex_embed,
    build_menu_embed,
    build_record_embed,
)
from views.creature.embeds import ELEMENTS
from views.creature.menu import _ElementFilterSelect, _OpponentSelect

_MENU_MOD = "views.creature.menu"


def _author(user_id: int = 1) -> MagicMock:
    author = MagicMock()
    author.id = user_id
    author.display_name = "Anya"
    return author


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = _author(user_id)
    interaction.guild = MagicMock()
    interaction.message = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _click(view, name: str, interaction: MagicMock):
    return getattr(type(view), name)(view, interaction, MagicMock())


def _menu() -> CreatureMenuView:
    return CreatureMenuView(_author(), guild_id=99)


def _catch_result(*, creature=None, caught=False, is_new=False, xp_note=None):
    return SimpleNamespace(
        creature=creature,
        caught=caught,
        is_new=is_new,
        xp_note=xp_note,
    )


def _creature():
    return SimpleNamespace(
        name="Emberfox",
        emoji="🔥",
        rarity="Rare",
        element="Fire",
    )


# ---------------------------------------------------------------------------
# Embeds (shared builders — one source of truth)
# ---------------------------------------------------------------------------


def test_menu_embed_advertises_the_actions():
    text = build_menu_embed().description
    assert "Catch" in text and "Dex" in text and "Challenge" in text
    assert "Ladder" in text


def test_menu_embed_shows_progress_numbers():
    embed = build_menu_embed(caught_unique=3, level=4)
    field = embed.fields[0].value
    assert "3/" in field and "level **4**" in field


def test_catch_result_embed_caught_new_entry():
    embed = build_catch_result_embed(
        "Anya",
        _catch_result(creature=_creature(), caught=True, is_new=True, xp_note="+5 XP"),
    )
    body = embed.description
    assert "Emberfox" in body and "New dex entry" in body and "+5 XP" in body


def test_catch_result_embed_flee():
    embed = build_catch_result_embed(
        "Anya",
        _catch_result(creature=_creature(), caught=False),
    )
    assert "escaped" in embed.description


def test_catch_result_embed_quiet_wilds_when_no_creature():
    embed = build_catch_result_embed("Anya", _catch_result(creature=None))
    assert "quiet" in embed.description


def test_dex_embed_counts_only_known_creatures():
    known = CREATURES[0].name
    log = {known: 2, "Legacymon": 99}  # the legacy row must not count
    embed = build_dex_embed("Anya", log, level=3)
    assert f"1/{len(CREATURES)}" in embed.description
    assert "**2** total catches" in embed.description


def test_dex_embed_element_filter_scopes_to_one_element():
    element = ELEMENTS[0]
    embed = build_dex_embed("Anya", {}, level=1, element=element)
    assert f"filtered to **{element}**" in embed.description
    # Only the filtered element is rendered as a field group.
    assert {f.name for f in embed.fields} == {element}


def test_battletop_empty_invites_a_challenge():
    embed = build_battletop_embed([], lambda uid: f"U{uid}")
    assert "No battles won yet" in embed.description


def test_battletop_ranks_with_medals_and_winrate():
    embed = build_battletop_embed([(7, 3, 1)], lambda uid: "Bo")
    assert "🥇" in embed.description and "75%" in embed.description


def test_record_embed_winrate():
    embed = build_record_embed("Bo", wins=1, losses=3)
    assert "25%" in embed.description


# ---------------------------------------------------------------------------
# Menu buttons
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_catch_button_runs_an_encounter_and_keeps_the_menu():
    view = _menu()
    interaction = _interaction()
    with patch(f"{_MENU_MOD}.creature_workflow") as wf:
        wf.catch = AsyncMock(
            return_value=_catch_result(creature=_creature(), caught=True),
        )
        await _click(view, "catch_btn", interaction)
    wf.catch.assert_awaited_once_with(1, 99)
    _, kwargs = interaction.response.edit_message.await_args
    assert kwargs["view"] is view  # menu stays so you can catch again


@pytest.mark.asyncio
async def test_dex_button_opens_the_browser():
    view = _menu()
    interaction = _interaction()
    with patch(f"{_MENU_MOD}.load_progress", AsyncMock(return_value=(0, 1, {}))):
        await _click(view, "dex_btn", interaction)
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], CreatureDexView)


@pytest.mark.asyncio
async def test_challenge_button_opens_the_opponent_picker():
    view = _menu()
    interaction = _interaction()
    await _click(view, "challenge_btn", interaction)
    _, kwargs = interaction.response.edit_message.await_args
    assert isinstance(kwargs["view"], CreatureChallengeSelectView)


@pytest.mark.asyncio
async def test_ladder_button_renders_and_keeps_the_menu():
    view = _menu()
    interaction = _interaction()
    with patch(f"{_MENU_MOD}.db") as db:
        db.top_battlers = AsyncMock(return_value=[(7, 2, 0)])
        await _click(view, "ladder_btn", interaction)
    _, kwargs = interaction.response.edit_message.await_args
    assert kwargs["view"] is view


@pytest.mark.asyncio
async def test_rules_button_is_ephemeral():
    view = _menu()
    interaction = _interaction()
    await _click(view, "rules_btn", interaction)
    _, kwargs = interaction.response.send_message.await_args
    assert kwargs["ephemeral"] is True


# ---------------------------------------------------------------------------
# Dex filter + opponent select
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_element_filter_callback_re_renders_filtered():
    dex = CreatureDexView(_author(), guild_id=99)
    select = next(c for c in dex.children if isinstance(c, _ElementFilterSelect))
    select._values = [ELEMENTS[0]]  # discord.py stores chosen values here
    interaction = _interaction()
    with patch(f"{_MENU_MOD}.load_progress", AsyncMock(return_value=(0, 1, {}))):
        await select.callback(interaction)
    _, kwargs = interaction.response.edit_message.await_args
    assert f"filtered to **{ELEMENTS[0]}**" in kwargs["embed"].description


@pytest.mark.asyncio
async def test_opponent_select_rejects_a_bot():
    sel_view = CreatureChallengeSelectView(_author(), guild_id=99)
    select = next(c for c in sel_view.children if isinstance(c, _OpponentSelect))
    bot_member = MagicMock(spec=__import__("discord").Member)
    bot_member.id = 2
    bot_member.bot = True
    select._values = [bot_member]
    interaction = _interaction()
    await select.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    _, kwargs = interaction.response.send_message.await_args
    assert kwargs["ephemeral"] is True
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_opponent_select_opens_the_challenge():
    import discord

    sel_view = CreatureChallengeSelectView(_author(1), guild_id=99)
    select = next(c for c in sel_view.children if isinstance(c, _OpponentSelect))
    opponent = MagicMock(spec=discord.Member)
    opponent.id = 2
    opponent.bot = False
    opponent.mention = "<@2>"
    challenger = MagicMock(spec=discord.Member)
    challenger.id = 1
    challenger.mention = "<@1>"
    select._values = [opponent]
    interaction = _interaction()
    interaction.user = challenger
    await select.callback(interaction)
    _, kwargs = interaction.response.edit_message.await_args
    from views.creature_battle import CreatureBattleChallengeView

    assert isinstance(kwargs["view"], CreatureBattleChallengeView)
