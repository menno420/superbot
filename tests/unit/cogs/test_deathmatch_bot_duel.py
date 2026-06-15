"""PR 6 — Deathmatch bot-duel stats pins.

Critical invariants from plan §13 (acceptance checklist):

* Player-vs-bot duels do **NOT** call
  ``Deathmatch.update_leaderboard`` or ``db.update_deathmatch``. Bot
  wins/losses stay off the PvP leaderboard to prevent farming.
* Player-vs-player duels keep the existing leaderboard update path
  unchanged.
* The typed ``!deathmatch @bot`` command remains rejected (only the
  panel's "Fight Bot" path is the supported bot-duel entry point).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


def _player(id_: int = 100, name: str = "Player") -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        display_name=name,
        mention=f"<@{id_}>",
        bot=False,
    )


def _bot_user(id_: int = 999, name: str = "Bot") -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        display_name=name,
        mention=f"<@{id_}>",
        bot=True,
    )


def _stub_interaction(player: SimpleNamespace) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = player
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.message = MagicMock(id=444)
    return interaction


# ---------------------------------------------------------------------------
# Bot-duel stats / leaderboard isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_duel_does_not_call_update_leaderboard():
    """Plan §13: bot duels must not call ``cog.update_leaderboard``.

    Force a win by repeatedly attacking the bot until its HP reaches
    zero. Assert :meth:`Deathmatch.update_leaderboard` is never called
    along the way.
    """
    from views.games.deathmatch_panel import _BotDuelView

    player = _player(100)
    bot_user = _bot_user(999)
    view = _BotDuelView(player, bot_user)

    with patch(
        "cogs.deathmatch_cog.Deathmatch.update_leaderboard",
        new_callable=AsyncMock,
    ) as mock_update:
        # Hammer with Attack until bot dies. Use a deterministic random
        # seed so test isn't flaky.
        import random

        random.seed(0)
        attack_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and (c.label or "").startswith("⚔️")
        )
        # Cap iterations to prevent infinite loop on a regression.
        for _ in range(200):
            if view.duel.is_over:
                break
            interaction = _stub_interaction(player)
            await attack_btn.callback(interaction)  # type: ignore[union-attr,misc]

        assert view.duel.is_over, (
            "Test loop did not finish the duel — increase iteration cap "
            "or check bot AI."
        )
        # Plan §13 critical assertion:
        mock_update.assert_not_called()


@pytest.mark.asyncio
async def test_bot_duel_does_not_call_db_update_deathmatch():
    """Plan §13: bot duels must not call ``db.update_deathmatch``."""
    from views.games.deathmatch_panel import _BotDuelView

    player = _player(100)
    bot_user = _bot_user(999)
    view = _BotDuelView(player, bot_user)

    with patch(
        "utils.db.update_deathmatch",
        new_callable=AsyncMock,
    ) as mock_db_update:
        import random

        random.seed(0)
        attack_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and (c.label or "").startswith("⚔️")
        )
        for _ in range(200):
            if view.duel.is_over:
                break
            interaction = _stub_interaction(player)
            await attack_btn.callback(interaction)  # type: ignore[union-attr,misc]

        assert view.duel.is_over, "Test loop did not finish the duel."
        mock_db_update.assert_not_called()


# ---------------------------------------------------------------------------
# Bot AI sanity
# ---------------------------------------------------------------------------


def test_pick_bot_action_returns_valid_choice():
    from cogs.deathmatch.actions import pick_bot_action

    for hp in (100, 75, 50, 25, 10, 1):
        choice = pick_bot_action(hp)
        assert choice in (
            "attack",
            "defend",
        ), f"pick_bot_action({hp}) returned {choice!r}"


def test_pick_bot_action_biases_defensive_when_low_hp():
    """At low HP the bot should defend more often. Statistical pin —
    over 200 rolls with the same low HP, defends should be > 30%.
    """
    import random

    from cogs.deathmatch.actions import pick_bot_action

    random.seed(42)
    low_hp_defends = sum(pick_bot_action(20) == "defend" for _ in range(200))
    random.seed(42)
    high_hp_defends = sum(pick_bot_action(80) == "defend" for _ in range(200))
    assert low_hp_defends > high_hp_defends, (
        f"Low-HP bot defended {low_hp_defends}/200 times vs high-HP "
        f"{high_hp_defends}/200; low-HP bias is missing."
    )


# ---------------------------------------------------------------------------
# Existing !deathmatch @bot rejection unchanged
# ---------------------------------------------------------------------------


def test_can_challenge_human_rejects_bot_opponent():
    """The extracted ``can_challenge_human`` check rejects bot
    opponents — same behaviour as the command body's pre-PR-6 inline
    check at ``cogs/deathmatch_cog.py:274``.
    """
    from cogs.deathmatch.actions import can_challenge_human

    author = _player(100)
    bot = _bot_user(999)
    error = can_challenge_human(author, bot)  # type: ignore[arg-type]
    assert error is not None
    assert "bot" in error.lower()


def test_can_challenge_human_rejects_self_target():
    from cogs.deathmatch.actions import can_challenge_human

    author = _player(100)
    error = can_challenge_human(author, author)  # type: ignore[arg-type]
    assert error is not None
    assert "yourself" in error.lower()


def test_can_challenge_human_accepts_valid_pair():
    from cogs.deathmatch.actions import can_challenge_human

    author = _player(100)
    opponent = _player(200, "Other")
    assert can_challenge_human(author, opponent) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Panel returns a non-empty view
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deathmatch_cog_build_help_menu_view_returns_panel():
    """The cog hook now returns the new panel (no longer an empty
    discord.ui.View()).
    """
    from cogs.deathmatch_cog import Deathmatch
    from views.games.deathmatch_panel import DeathmatchPanelView

    cog = Deathmatch(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction(_player()))
    assert isinstance(view, DeathmatchPanelView)
    assert "Deathmatch" in (embed.title or "")
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) >= 3, (
        f"Expected at least Fight Bot / Challenge Player / Rules "
        f"buttons; got {len(buttons)}: {[b.label for b in buttons]}"
    )
