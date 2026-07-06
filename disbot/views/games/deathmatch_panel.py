"""Deathmatch hub panel — PR 6 (playable launcher + bot duels).

PR 6 replaces the empty ``discord.ui.View()`` that ``Deathmatch.
build_help_menu_view`` previously returned with an actionable
launcher: Fight Bot, Challenge Player, Rules. The PvP path reuses
the cog's existing ``_Duel`` / ``_DuelView`` / ``_ChallengeView``;
the new bot-duel path adds ``_BotDuelView`` on top of the same
``_Duel`` state class.

Bot-duel stats rule (plan §13):

* Bot duels **do not** call ``cog.update_leaderboard`` or
  ``db.update_deathmatch``. The result is shown only in the match
  result embed.
* PvP duels keep the existing leaderboard update path unchanged.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from utils import db, equipment
from utils.terminal_guard import SettleOnceMixin
from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.games.common import BackToPanelButton

if TYPE_CHECKING:
    # Type-only — the panel reuses the deathmatch cog's ``_Duel`` state class
    # and the ``Deathmatch`` cog type for annotations. Importing them at module
    # level is the ``views → cogs`` layer-boundary violation (ticket
    # arch-fix-13); the runtime uses (`_Duel`/`_ChallengeView` instantiation,
    # the `actions` helper calls, the `Deathmatch` isinstance check) are done
    # via lazy function-body imports below. Only module-level imports are
    # layer-checked, so this keeps the panel free of a module-level cogs edge
    # while every symbol stays importable from its existing home (the test
    # contract — including the `cogs.deathmatch_cog._tick_duel_gear_wear`
    # string patch — is unchanged).
    from cogs.deathmatch_cog import Deathmatch, _Duel

logger = logging.getLogger("bot.views.games.deathmatch_panel")


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def build_deathmatch_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚔️ Deathmatch",
        description=(
            "Turn-based 1v1 combat with attack and defend actions. "
            "Fight Bot starts an immediate duel vs the bot (results "
            "stay off the PvP leaderboard); Challenge Player opens a "
            "PvP challenge to another member."
        ),
        color=GAME_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


def build_deathmatch_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚔️ Deathmatch — Rules",
        description=(
            "Two combatants start at **100 HP** and take turns "
            "attacking or defending until one falls."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Actions",
        value=(
            "• **⚔️ Attack** — deal **15 damage** (10% chance of "
            "**30 damage** critical).\n"
            "• **🛡️ Defend** — halve incoming damage on the next "
            "enemy attack."
        ),
        inline=False,
    )
    embed.add_field(
        name="Gear",
        value=(
            "Equip combat gear from the mining hub (`!equip iron sword`, "
            "`!equip armor`): a **weapon** adds attack damage, **armor** adds "
            "max HP and flat damage reduction. A small, fair edge — not a "
            "guaranteed win."
        ),
        inline=False,
    )
    embed.add_field(
        name="Leaderboard",
        value=(
            "PvP wins and losses update the deathmatch leaderboard. "
            "**Bot duels do not** — bot wins/losses stay off the "
            "ranking to keep PvP fair."
        ),
        inline=False,
    )
    return embed


def build_bot_duel_embed(
    duel: _Duel,
    player: discord.Member | discord.User,
    bot_user: discord.User | discord.ClientUser,
    last_action: str = "",
) -> discord.Embed:
    desc = (
        f"**{player.display_name}** — "
        f"{max(duel.player1_hp, 0)}/{duel.player1_max_hp} HP\n"
        f"**{bot_user.display_name}** — "
        f"{max(duel.player2_hp, 0)}/{duel.player2_max_hp} HP\n"
    )
    if not duel.is_over:
        whose_turn = (
            player.display_name if duel.turn.id == player.id else bot_user.display_name
        )
        desc += f"\nIt's **{whose_turn}**'s turn!"
    if last_action:
        desc += f"\n\n{last_action}"
    return discord.Embed(
        title="⚔️ Bot Duel In Progress",
        description=desc,
        color=discord.Color.dark_red(),
    )


def build_bot_duel_result_embed(
    duel: _Duel,
    player: discord.Member | discord.User,
    bot_user: discord.User | discord.ClientUser,
    last_action: str,
) -> discord.Embed:
    winner = bot_user if duel.player1_hp <= 0 else player
    return discord.Embed(
        title="⚔️ Bot Duel Ended",
        description=(
            f"{last_action}\n\n"
            f"**{player.display_name}** — "
            f"{max(duel.player1_hp, 0)}/{duel.player1_max_hp} HP\n"
            f"**{bot_user.display_name}** — "
            f"{max(duel.player2_hp, 0)}/{duel.player2_max_hp} HP\n\n"
            f"🏆 **{winner.display_name}** wins!\n"
            "_Bot duels don't update the PvP leaderboard._"
        ),
        color=discord.Color.gold(),
    )


def build_deathmatch_challenge_picker_embed() -> discord.Embed:
    return discord.Embed(
        title="⚔️ Deathmatch — Challenge Player",
        description=(
            "Pick the player you want to challenge. They'll see an "
            "Accept / Decline prompt with 30 seconds to respond."
        ),
        color=GAME_COLOR,
    )


def build_deathmatch_challenge_embed(
    challenger: discord.Member | discord.User,
    opponent: discord.Member | discord.User,
) -> discord.Embed:
    """The Accept/Decline challenge prompt — one builder for every entry
    point (panel opponent-select + the PvP-result rematch), so the copy
    can't drift between them.
    """
    embed = discord.Embed(
        title="⚔️ Deathmatch Challenge",
        description=(
            f"{challenger.mention} has challenged {opponent.mention} to a "
            "duel!\n\nPress **Accept** or **Decline** below."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text="You have 30 seconds to respond.")
    return embed


# ---------------------------------------------------------------------------
# Bot-duel view
# ---------------------------------------------------------------------------


class _BotDuelView(SettleOnceMixin, discord.ui.View):
    """Player-vs-bot duel view (PR 6).

    Reuses the cog's ``_Duel`` state class for HP / attack / defend /
    crit logic. After each player click the bot's turn auto-resolves
    via :func:`pick_bot_action`. **No** leaderboard write happens on
    bot wins/losses (see plan §13 bot-duel stats rule).
    """

    def __init__(
        self,
        player: discord.Member | discord.User,
        bot_user: discord.User | discord.ClientUser,
        *,
        player_stats: equipment.EffectiveStats | None = None,
    ) -> None:
        super().__init__(timeout=120.0)
        # Lazy import — ``_Duel`` lives in the deathmatch cog; importing it in a
        # function body keeps the panel free of a module-level ``views → cogs``
        # edge (only module-level imports are layer-checked).
        from cogs.deathmatch_cog import _Duel

        self.player = player
        self.bot_user = bot_user
        # ``_Duel`` expects two discord.Member arguments; ClientUser
        # duck-types correctly for the .id / .display_name / .mention
        # attributes _Duel reads.  The player brings their equipped combat
        # gear (EffectiveStats); the bot fights bare (default all-zero stats).
        self.duel = _Duel(
            player,  # type: ignore[arg-type]
            bot_user,  # type: ignore[arg-type]
            p1_stats=player_stats or equipment.EffectiveStats(),
        )
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "This duel isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, row=0)
    async def btn_attack(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        damage, critical = self.duel.attack(self.player.id, self.bot_user.id)
        action = f"**{self.player.display_name}** attacks for **{damage} damage**!"
        if critical:
            action += " ⚡ **Critical Hit!**"
        if self.duel.player2_hp <= 0:
            await self._finish(interaction, action)
            return
        await self._bot_turn(interaction, action)

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.blurple, row=0)
    async def btn_defend(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        self.duel.defend(self.player.id)
        action = f"🛡️ **{self.player.display_name}** takes a defensive stance!"
        await self._bot_turn(interaction, action)

    async def _bot_turn(
        self,
        interaction: discord.Interaction,
        player_action: str,
    ) -> None:
        # Lazy import — keeps the bot-AI helper edge out of module scope.
        from cogs.deathmatch.actions import pick_bot_action

        choice = pick_bot_action(self.duel.player2_hp)
        if choice == "attack":
            damage, critical = self.duel.attack(self.bot_user.id, self.player.id)
            bot_action = (
                f"**{self.bot_user.display_name}** attacks for **{damage} damage**!"
            )
            if critical:
                bot_action += " ⚡ **Critical Hit!**"
        else:
            self.duel.defend(self.bot_user.id)
            bot_action = f"🛡️ **{self.bot_user.display_name}** takes a defensive stance!"
        full_action = f"{player_action}\n{bot_action}"
        if self.duel.player1_hp <= 0 or self.duel.player2_hp <= 0:
            await self._finish(interaction, full_action)
            return
        await interaction.response.edit_message(
            embed=build_bot_duel_embed(
                self.duel,
                self.player,
                self.bot_user,
                full_action,
            ),
            view=self,
        )

    async def _finish(
        self,
        interaction: discord.Interaction,
        action_text: str,
    ) -> None:
        # Settle-once: a finishing-blow double-click (or a timeout racing the
        # final move) can re-enter the settlement path; claim it synchronously
        # before any await so the second caller short-circuits.
        if not self.claim_settlement():
            return
        self.duel.is_over = True
        # NOTE: deliberately NO call to ``cog.update_leaderboard`` /
        # ``db.update_deathmatch`` — see plan §13 bot-duel stats rule.
        # Swap to the terminal result view (Play again + standard nav) so the
        # finished duel is never a dead-end (owner directive 2026-06-23).
        await interaction.response.edit_message(
            embed=build_bot_duel_result_embed(
                self.duel,
                self.player,
                self.bot_user,
                action_text,
            ),
            view=_BotDuelResultView(self.player, self.bot_user),
        )
        self.stop()

    async def on_timeout(self) -> None:
        # Shares the settle-once claim with ``_finish`` so a timeout firing just
        # as the duel finishes can't post a second terminal screen.
        if not self.claim_settlement():
            return
        self.duel.is_over = True
        embed = discord.Embed(
            title="⚔️ Bot Duel — Timeout",
            description=(
                f"{self.player.mention} took too long to respond.\n"
                f"🏆 **{self.bot_user.display_name}** wins by default!\n"
                "_Bot duels don't update the PvP leaderboard._"
            ),
            color=discord.Color.orange(),
        )
        if self.message:
            try:
                await self.message.edit(
                    embed=embed,
                    view=_BotDuelResultView(self.player, self.bot_user),
                )
            except Exception as exc:
                logger.debug("bot-duel on_timeout: message.edit failed: %s", exc)


class _BotDuelResultView(HubView):
    """Terminal screen after a bot duel — never a dead-end.

    A ``HubView`` with ``SUBSYSTEM = "deathmatch"`` so
    :func:`views.navigation.attach_standard_nav` auto-attaches **📚 Help** and
    **↩ Games** — the player is one click from the Deathmatch hub and Help.
    The **🔁 Play again** button re-runs the Fight Bot flow (re-fetched gear,
    a fresh :class:`_BotDuelView`), mirroring ``DeathmatchPanelView.btn_fight_bot``.
    """

    SUBSYSTEM = "deathmatch"

    def __init__(
        self,
        player: discord.Member | discord.User,
        bot_user: discord.User | discord.ClientUser,
    ) -> None:
        super().__init__(player)
        self.player = player
        self.bot_user = bot_user

    @discord.ui.button(
        label="🔁 Play again",
        style=discord.ButtonStyle.success,
        custom_id="bot_duel_result:again",
        row=0,
    )
    async def btn_again(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        bot_user = interaction.client.user or self.bot_user
        player_stats = equipment.compute_stats(
            await db.get_equipment(str(interaction.user.id), interaction.guild_id or 0),
        )
        view = _BotDuelView(interaction.user, bot_user, player_stats=player_stats)
        await interaction.response.edit_message(
            embed=build_bot_duel_embed(view.duel, interaction.user, bot_user),
            view=view,
        )
        view.message = interaction.message


class _PvpDuelResultView(HubView):
    """Terminal screen after a human-vs-human duel / resolved challenge —
    never a dead-end.

    A ``HubView`` with ``SUBSYSTEM = "deathmatch"`` so
    :func:`views.navigation.attach_standard_nav` auto-attaches **📚 Help** and
    **↩ Games** (row 4) — neither fighter is ever stranded on a dead embed
    (owner directive 2026-06-23, previously applied only to the bot path via
    :class:`_BotDuelResultView`). The **🔁 Rematch** button re-challenges: the
    clicker challenges the *other* fighter, who re-confirms via the normal
    Accept/Decline prompt (consent preserved). Used by the PvP duel-finish /
    timeout / decline / expire paths in ``cogs.deathmatch_cog``.

    Both duelists may interact (``interaction_check`` allows either id) — a
    duel has two owners, unlike the single-player bot result view.
    """

    SUBSYSTEM = "deathmatch"

    def __init__(
        self,
        cog: Deathmatch,
        player1: discord.Member | discord.User,
        player2: discord.Member | discord.User,
    ) -> None:
        # ``player1`` is the nominal author (BaseView needs one); the override
        # below widens access to both fighters.
        super().__init__(player1)
        self.cog = cog
        self.player1 = player1
        self.player2 = player2

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in (self.player1.id, self.player2.id):
            return True
        await interaction.response.send_message(
            "Only the two duelists can use this.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(
        label="🔁 Rematch",
        style=discord.ButtonStyle.success,
        custom_id="deathmatch_pvp_result:rematch",
        row=0,
    )
    async def btn_rematch(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        # Lazy imports — the rematch reuses the cog's ``_ChallengeView`` and the
        # ``actions`` duel-key/guard helpers; keeping them function-body keeps
        # the panel free of a module-level ``views → cogs`` edge.
        from cogs.deathmatch.actions import has_existing_duel, make_duel_key
        from cogs.deathmatch_cog import _ChallengeView

        # The clicker becomes the new challenger; the other fighter is the
        # opponent (re-confirms via Accept/Decline).
        if interaction.user.id == self.player1.id:
            challenger, opponent = self.player1, self.player2
        else:
            challenger, opponent = self.player2, self.player1
        if not isinstance(challenger, discord.Member) or not isinstance(
            opponent,
            discord.Member,
        ):
            await interaction.response.send_message(
                "A rematch needs both players to be server members.",
                ephemeral=True,
            )
            return
        cog = self.cog
        conflict = has_existing_duel(cog, challenger.id, opponent.id)
        if conflict:
            await interaction.response.send_message(conflict, ephemeral=True)
            return
        duel_key = make_duel_key(challenger.id, opponent.id)
        # ``_ChallengeView`` only reads ``ctx`` to forward into ``_DuelView``,
        # which now takes its ``guild_id`` from the accept interaction — so the
        # panel/rematch path safely passes ctx=None (no longer crashes on
        # resolve; see the deathmatch_cog guild_id thread).
        challenge_view = _ChallengeView(
            cog,
            challenger,
            opponent,
            duel_key,
            None,  # type: ignore[arg-type]
        )
        await interaction.response.edit_message(
            embed=build_deathmatch_challenge_embed(challenger, opponent),
            view=challenge_view,
        )
        challenge_view.message = interaction.message


# ---------------------------------------------------------------------------
# Challenge-picker sub-view
# ---------------------------------------------------------------------------


class _DeathmatchChallengeSelectView(HubView):
    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        self.add_item(_DeathmatchOpponentSelect())
        self.add_item(_make_deathmatch_back_button())


class _DeathmatchOpponentSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose an opponent…",
            min_values=1,
            max_values=1,
            custom_id="deathmatch_panel:opponent_select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # Lazy imports — the PvP-challenge path reuses the deathmatch cog's
        # ``_ChallengeView`` and the ``actions`` validation helpers. Importing
        # them in the function body keeps the panel free of a module-level
        # ``views → cogs`` edge.
        from cogs.deathmatch.actions import (
            can_challenge_human,
            has_existing_duel,
            make_duel_key,
        )
        from cogs.deathmatch_cog import _ChallengeView

        opponent = self.values[0]
        if not isinstance(opponent, discord.Member):
            await interaction.response.send_message(
                "Opponent must be a server member.",
                ephemeral=True,
            )
            return
        challenger = interaction.user
        if not isinstance(challenger, discord.Member):
            await interaction.response.send_message(
                "Challenger must be a server member.",
                ephemeral=True,
            )
            return
        error = can_challenge_human(challenger, opponent)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        cog = _resolve_deathmatch_cog(interaction)
        if cog is None:
            await interaction.response.send_message(
                "Deathmatch cog is not loaded.",
                ephemeral=True,
            )
            return
        duel_key = make_duel_key(challenger.id, opponent.id)
        conflict = has_existing_duel(cog, challenger.id, opponent.id)
        if conflict:
            await interaction.response.send_message(conflict, ephemeral=True)
            return
        # ``_ChallengeView`` requires (cog, challenger, opponent,
        # duel_key, ctx). The cog only reads ``ctx`` to pass it into
        # ``_DuelView``, which stores it but never uses it; safe to
        # pass None from the panel path.
        challenge_view = _ChallengeView(
            cog,
            challenger,
            opponent,
            duel_key,
            None,  # type: ignore[arg-type]
        )
        await interaction.response.edit_message(
            embed=build_deathmatch_challenge_embed(challenger, opponent),
            view=challenge_view,
        )
        challenge_view.message = interaction.message


def _resolve_deathmatch_cog(
    interaction: discord.Interaction,
) -> Deathmatch | None:
    # Lazy imports — the ``Deathmatch`` cog type is needed at runtime for the
    # isinstance narrowing; importing it (and the help-cog resolver) in the
    # function body keeps the panel free of a module-level ``views → cogs`` edge.
    from cogs.deathmatch_cog import Deathmatch
    from cogs.help_cog import _cog_for_subsystem

    cog = _cog_for_subsystem(interaction.client, "deathmatch")  # type: ignore[arg-type]
    if isinstance(cog, Deathmatch):
        return cog
    return None


def _make_deathmatch_back_button() -> BackToPanelButton:
    """Return a fresh "◀ Back to Deathmatch" button for any Deathmatch
    sub-view. Follow-up to PR 7 — Deathmatch now uses the shared
    helper from ``views.games.common`` alongside RPS and Blackjack.
    """
    return BackToPanelButton(
        label="◀ Back to Deathmatch",
        custom_id="deathmatch_panel:back",
        panel_builder=DeathmatchPanelView,
        overview_builder=build_deathmatch_overview_embed,
    )


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------


class DeathmatchPanelView(HubView):
    """Actionable Deathmatch hub (PR 6).

    Three buttons: Fight Bot, Challenge Player, Rules. PR 6 replaces
    the empty ``discord.ui.View()`` that ``Deathmatch.
    build_help_menu_view`` previously returned.
    """

    SUBSYSTEM = "deathmatch"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="🤖 Fight Bot",
        style=discord.ButtonStyle.success,
        custom_id="deathmatch_panel:fight_bot",
        row=0,
    )
    async def btn_fight_bot(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        bot_user = interaction.client.user
        if bot_user is None:
            await interaction.response.send_message(
                "Bot user is not available right now.",
                ephemeral=True,
            )
            return
        player_stats = equipment.compute_stats(
            await db.get_equipment(str(interaction.user.id), interaction.guild_id or 0),
        )
        view = _BotDuelView(interaction.user, bot_user, player_stats=player_stats)
        await interaction.response.edit_message(
            embed=build_bot_duel_embed(view.duel, interaction.user, bot_user),
            view=view,
        )
        view.message = interaction.message

    @discord.ui.button(
        label="👤 Challenge Player",
        style=discord.ButtonStyle.primary,
        custom_id="deathmatch_panel:challenge",
        row=0,
    )
    async def btn_challenge(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_deathmatch_challenge_picker_embed(),
            view=_DeathmatchChallengeSelectView(interaction.user),
        )

    @discord.ui.button(
        label="📖 Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="deathmatch_panel:rules",
        row=0,
    )
    async def btn_rules(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_deathmatch_rules_embed(),
            view=self,
        )


__all__ = [
    "DeathmatchPanelView",
    "build_deathmatch_challenge_embed",
    "build_deathmatch_overview_embed",
    "build_deathmatch_rules_embed",
]
