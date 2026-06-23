"""Game-result continuation pins (never-stranded follow-up to PR #1382).

PR #1382 gave every *panel* a Help + Back-to-hub control. The game-RESULT
screens (terminal ``discord.ui.View`` game-state views) were left out and
dead-ended with all buttons disabled. These tests pin that the terminal views
now carry a game-specific "… again" button AND the universal standard nav
(``nav:help`` + ``nav:hub:games``) so the player is never stranded.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from views.fishing.cast_view import _FishingDoneView  # noqa: E402
from views.games.deathmatch_panel import (  # noqa: E402
    _BotDuelResultView,
    _BotDuelView,
)


def _ids(view: discord.ui.View) -> set[str]:
    return {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if getattr(c, "custom_id", None)
    }


def _player(id_: int = 100) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_, display_name="Player", mention=f"<@{id_}>", bot=False
    )


def _bot_user(id_: int = 999) -> SimpleNamespace:
    return SimpleNamespace(id=id_, display_name="Bot", mention=f"<@{id_}>", bot=True)


def test_bot_duel_result_view_offers_play_again_and_standard_nav():
    view = _BotDuelResultView(_player(), _bot_user())
    assert _ids(view) == {"bot_duel_result:again", "nav:help", "nav:hub:games"}


def test_fishing_done_view_offers_cast_again_and_standard_nav():
    view = _FishingDoneView(_player(), guild_id=42)
    assert _ids(view) == {"fishing_done:cast_again", "nav:help", "nav:hub:games"}


@pytest.mark.asyncio
async def test_bot_duel_finish_swaps_to_a_continuation_view_not_a_dead_end():
    """``_BotDuelView._finish`` must render the result on a continuation view
    (Play again + nav), never the old all-disabled ``self``.
    """
    duel = _BotDuelView(_player(), _bot_user())
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()

    await duel._finish(interaction, "Final blow!")

    interaction.response.edit_message.assert_awaited_once()
    swapped = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(swapped, _BotDuelResultView)
    assert {"nav:help", "nav:hub:games", "bot_duel_result:again"} <= _ids(swapped)
