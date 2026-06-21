"""Creature PvP rematch view (creature-game v1).

Attached to the battle-outcome embed so either fighter can fire a fresh challenge
without re-typing ``!cbattle @x`` — the continuous-laddering affordance, mirroring
the rps ``🔁 Play again`` button. The button re-issues a brand-new
:class:`views.creature_battle.challenge.CreatureBattleChallengeView` (the clicker
becomes the challenger, the other fighter the opponent, who Accepts/Declines as
usual), so there is **no new battle logic** — the next battle reuses the existing
challenge flow and the audited result-recording path.

Specialized lifecycle: unlike a standard single-author ``BaseView``, the rematch
button is interactable by **either** participant. The check below allows the two
fighters and no one else; ``BaseView(public=False)`` would lock it to one author,
``public=True`` would open it to the whole channel — neither is right here.
"""

from __future__ import annotations

import logging

import discord

from views.base import BaseView

logger = logging.getLogger("bot.creature_battle.rematch")


class CreatureRematchView(BaseView):
    """A single 🔄 Rematch button either fighter may press to re-challenge."""

    def __init__(
        self,
        player_a: discord.Member,
        player_b: discord.Member,
        guild_id: int,
    ) -> None:
        # author=player_a satisfies BaseView; interaction_check below widens the
        # allowed clickers to both fighters (specialized two-participant lifecycle).
        super().__init__(player_a, timeout=120)
        self.player_a = player_a
        self.player_b = player_b
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in (self.player_a.id, self.player_b.id):
            return True
        await interaction.response.send_message(
            "Only the two fighters can start a rematch — challenge with `!cbattle` "
            "to play your own.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Rematch", style=discord.ButtonStyle.primary, emoji="🔄")
    async def rematch(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        # The clicker re-challenges; the other fighter becomes the opponent who
        # must Accept/Decline (the existing challenge flow IS the agreement step).
        challenger = (
            self.player_a if interaction.user.id == self.player_a.id else self.player_b
        )
        opponent = self.player_b if challenger.id == self.player_a.id else self.player_a

        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

        # Late import: challenge.py attaches this view to the outcome message, so a
        # module-level import here would create a cycle.
        from views.creature_battle.challenge import CreatureBattleChallengeView

        view = CreatureBattleChallengeView(challenger, opponent, self.guild_id)
        view.message = await interaction.followup.send(
            f"{opponent.mention} — {challenger.mention} wants a rematch! "
            "Teams are level-normalized; your collection and type matchups decide it.",
            view=view,
            wait=True,
        )
