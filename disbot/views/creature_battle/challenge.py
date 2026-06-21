"""Creature PvP challenge accept/decline view (creature-game v1).

Spawned from ``!cbattle <opponent>``. Only the challenged player can interact
(``BaseView`` locked to ``author=opponent``). On **Accept** the battle resolves
immediately — teams auto-build from each player's collection at a normalized
level, so there is no move-picking step — and the outcome embed is posted to the
channel. Mirrors the rps/deathmatch PvP-challenge pattern, minus the wager/escrow
machinery (creature PvP has no stakes in v1).
"""

from __future__ import annotations

import logging

import discord

from services import creature_battle_service
from views.base import BaseView
from views.creature_battle.rematch import CreatureRematchView
from views.creature_battle.render import build_result_embed

logger = logging.getLogger("bot.creature_battle.challenge")

_NO_TEAM_MSG = (
    "🐾 Both fighters need at least one creature to battle — use `!catch` first!"
)


class CreatureBattleChallengeView(BaseView):
    """Accept/decline a creature PvP challenge (interactable only by the opponent)."""

    def __init__(
        self,
        challenger: discord.Member,
        opponent: discord.Member,
        guild_id: int,
    ) -> None:
        # author=opponent → BaseView.interaction_check locks the buttons to the
        # challenged player (only they may accept/decline).
        super().__init__(opponent, timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.guild_id = guild_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="⚔️ Challenge accepted — resolving the battle…",
            view=self,
        )
        recorded = await creature_battle_service.resolve_and_record_pvp(
            self.challenger.id,
            self.opponent.id,
            self.guild_id,
        )
        if recorded is None:
            await interaction.followup.send(_NO_TEAM_MSG)
            self.stop()
            return
        records = {
            recorded.winner_id: recorded.winner_record,
            recorded.loser_id: recorded.loser_record,
        }
        embed = build_result_embed(
            self.challenger,
            self.opponent,
            recorded.result,
            records=records,
            xp_note=recorded.xp_note,
        )
        # Attach a rematch button so either fighter can re-challenge in one tap.
        rematch = CreatureRematchView(self.challenger, self.opponent, self.guild_id)
        rematch.message = await interaction.followup.send(
            embed=embed,
            view=rematch,
            wait=True,
        )
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()
