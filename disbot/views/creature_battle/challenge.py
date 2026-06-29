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
from utils.terminal_guard import SettleOnceMixin
from views.base import BaseView
from views.creature_battle.rematch import CreatureRematchView
from views.creature_battle.render import build_result_embed

logger = logging.getLogger("bot.creature_battle.challenge")

_NO_TEAM_MSG = (
    "🐾 Both fighters need at least one creature to battle — use `!catch` first!"
)


class CreatureBattleChallengeView(SettleOnceMixin, BaseView):
    """Accept/decline a creature PvP challenge (interactable only by the opponent).

    The accept/decline buttons settle the challenge (resolve + record a battle, or
    close it). :class:`SettleOnceMixin` gives that transition one atomic claim so a
    double-click on Accept — or an Accept racing a Decline — can't resolve and record
    the battle twice (completion cert #5; the deathmatch settle-once lineage).
    """

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
        # Set once accept/decline answers the challenge so a late on_timeout (the
        # BUG-0013 race) can't overwrite a resolved challenge with the expiry copy.
        self._resolved = False

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Claim the settling transition before any await so a double-click (or an
        # Accept racing a Decline) can't resolve + record the battle twice.
        if not self.claim_settlement():
            return
        self._resolved = True
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
        if not self.claim_settlement():
            return
        self._resolved = True
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()

    async def on_timeout(self) -> None:
        """Close an unanswered challenge with an explicit expiry notice.

        accept/decline call ``self.stop()`` (which cancels the timeout), so this
        fires only when the challenge was never answered — the silent-timeout gap
        the deathmatch BUG-0013 fix closed for its own challenge view. The
        ``_resolved`` guard covers the rare race where a click lands as the timeout
        is already firing (don't overwrite a resolved challenge).
        """
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self._resolved or self.message is None:
            return
        try:
            await self.message.edit(
                content=(
                    f"⌛ {self.opponent.display_name} didn't respond — the creature "
                    f"challenge from {self.challenger.display_name} expired."
                ),
                view=self,
            )
        except Exception as exc:
            logger.debug(
                "CreatureBattleChallengeView.on_timeout: message.edit failed: %s",
                exc,
            )
