from __future__ import annotations

import random

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from services import mining_workflow
from utils import db, equipment
from utils.mining import workshop as mining_workshop
from utils.terminal_guard import SettleOnceMixin

# Base duel constants — the floor every fighter starts from before equipped
# combat gear (utils.equipment.EffectiveStats) tilts it.
BASE_HP = 100
BASE_ATTACK_DAMAGE = 15
BASE_CRIT_DAMAGE = 30


class _Duel:
    def __init__(
        self,
        player1: discord.Member,
        player2: discord.Member,
        *,
        p1_stats: equipment.EffectiveStats | None = None,
        p2_stats: equipment.EffectiveStats | None = None,
    ):
        # Combat stats come from each player's equipped gear (the cross-game
        # EffectiveStats seam).  They default to an all-zero block so a bare
        # fighter — and every existing caller/test that omits them — duels at
        # exactly the historical 100 HP / 15 damage.
        self.player1 = player1
        self.player2 = player2
        self.p1_stats = p1_stats or equipment.EffectiveStats()
        self.p2_stats = p2_stats or equipment.EffectiveStats()
        self.player1_max_hp = BASE_HP + self.p1_stats.max_health
        self.player2_max_hp = BASE_HP + self.p2_stats.max_health
        self.player1_hp = self.player1_max_hp
        self.player2_hp = self.player2_max_hp
        self.turn = player1
        self.is_over = False
        self.defense: dict[int, bool] = {player1.id: False, player2.id: False}

    def _stats_for(self, player_id: int) -> equipment.EffectiveStats:
        return self.p1_stats if player_id == self.player1.id else self.p2_stats

    def attack(self, attacker_id: int, defender_id: int) -> tuple[int, bool]:
        critical = random.random() < 0.1
        base = BASE_CRIT_DAMAGE if critical else BASE_ATTACK_DAMAGE
        damage = base + self._stats_for(attacker_id).damage
        if self.defense.get(defender_id, False):
            damage = damage // 2
            self.defense[defender_id] = False
        # Armor (defender defense) is flat damage reduction, floored at 1 so an
        # attack always lands for *something*.
        damage = max(1, damage - self._stats_for(defender_id).defense)
        if defender_id == self.player1.id:
            self.player1_hp -= damage
        else:
            self.player2_hp -= damage
        return damage, critical

    def defend(self, player_id: int) -> None:
        self.defense[player_id] = True


async def _tick_duel_gear_wear(
    guild_id: int,
    *fighters: discord.Member,
) -> list[str]:
    """Q-0054: a finished PvP duel wears each fighter's weapon + armor once.

    Bot fighters are skipped (bot duels grant nothing, so there is no
    farming vector and nothing to wear).  Returns the fighters' wear notes
    (break / nearly-worn warnings) for the final duel embed.
    """
    notes: list[str] = []
    for member in fighters:
        if getattr(member, "bot", False):
            continue
        equipped = await db.get_equipment(str(member.id), guild_id)
        report = await mining_workflow.wear_tick(
            member.id,
            guild_id,
            action=mining_workshop.ACTION_DUEL,
            depth=0,
            equipped=equipped,
        )
        notes.extend(f"{member.display_name}: {note}" for note in report.notes)
    return notes


class _DuelView(SettleOnceMixin, discord.ui.View):
    def __init__(
        self,
        cog: Deathmatch,
        duel: _Duel,
        duel_key: tuple,
        ctx: commands.Context,
        *,
        timeout: float = 60.0,
        guild_id: int | None = None,
    ):
        # PR 8 — ``timeout`` is now a keyword arg; defaults to the
        # historical 60s value when called without the setting-aware
        # path (e.g. from tests). Callers reading the guild setting
        # pass the configured value explicitly.
        super().__init__(timeout=timeout)
        self.cog = cog
        self.duel = duel
        self.duel_key = duel_key
        self.ctx = ctx
        # The originating guild for the leaderboard / gear-wear writes. The
        # panel-initiated PvP path constructs this view with ``ctx=None`` (it
        # only has an interaction), so reading ``ctx.guild.id`` on resolve used
        # to raise ``AttributeError`` mid-duel — callers now pass ``guild_id``
        # explicitly. The ctx fallback preserves the command path + existing
        # tests that build a ``_DuelView`` with a real ``ctx`` and no guild_id.
        if guild_id is None:
            guild_id = ctx.guild.id if ctx and getattr(ctx, "guild", None) else 0
        self.guild_id = guild_id
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.duel.turn:
            await interaction.response.send_message(
                "It's not your turn!",
                ephemeral=True,
            )
            return False
        return True

    def build_embed(self, last_action: str = "") -> discord.Embed:
        duel = self.duel
        desc = (
            f"**{duel.player1.display_name}** — "
            f"{max(duel.player1_hp, 0)}/{duel.player1_max_hp} HP\n"
            f"**{duel.player2.display_name}** — "
            f"{max(duel.player2_hp, 0)}/{duel.player2_max_hp} HP\n\n"
            f"It's **{duel.turn.display_name}**'s turn!"
        )
        if last_action:
            desc += f"\n\n{last_action}"
        return discord.Embed(
            title="⚔️ Deathmatch In Progress",
            description=desc,
            color=discord.Color.dark_red(),
        )

    async def on_timeout(self) -> None:
        duel = self.duel
        # Shares the settle-once claim with ``_resolve`` so a timeout firing
        # just as the finishing blow lands can't write a second W/L + gear-wear
        # settlement (the Gate-V Arm-D live-confirmed double-write).
        if not self.claim_settlement():
            return
        opponent = duel.player2 if duel.turn == duel.player1 else duel.player1
        duel.is_over = True
        self.cog.active_duels.pop(self.duel_key, None)
        await self.cog.update_leaderboard(
            winner_id=opponent.id,
            loser_id=duel.turn.id,
            guild_id=self.guild_id,
        )
        wear_notes = await _tick_duel_gear_wear(
            self.guild_id,
            duel.player1,
            duel.player2,
        )
        description = (
            f"{duel.turn.mention} took too long to respond.\n"
            f"🏆 {opponent.mention} wins by default!"
        )
        if wear_notes:
            description += "\n\n" + "\n".join(wear_notes)
        embed = discord.Embed(
            title="⚔️ Deathmatch — Timeout",
            description=description,
            color=discord.Color.orange(),
        )
        if self.message:
            try:
                # Swap to the terminal result view (Help + Games nav + Rematch)
                # so a timed-out PvP duel is never a dead-end (owner directive
                # 2026-06-23, previously applied only to the bot path).
                from views.games.deathmatch_panel import _PvpDuelResultView

                await self.message.edit(
                    embed=embed,
                    view=_PvpDuelResultView(self.cog, duel.player1, duel.player2),
                )
            except Exception:
                pass

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, row=0)
    async def btn_attack(self, interaction: discord.Interaction, _: discord.ui.Button):
        duel = self.duel
        current = duel.turn
        opponent = duel.player2 if current == duel.player1 else duel.player1
        damage, critical = duel.attack(current.id, opponent.id)
        result = f"**{current.display_name}** attacks for **{damage} damage**!"
        if critical:
            result += " ⚡ **Critical Hit!**"
        await self._resolve(interaction, result)

    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.blurple, row=0)
    async def btn_defend(self, interaction: discord.Interaction, _: discord.ui.Button):
        duel = self.duel
        current = duel.turn
        duel.defend(current.id)
        await self._resolve(
            interaction,
            f"🛡️ **{current.display_name}** takes a defensive stance!",
        )

    async def _resolve(
        self,
        interaction: discord.Interaction,
        action_text: str,
    ) -> None:
        duel = self.duel
        current = duel.turn
        opponent = duel.player2 if current == duel.player1 else duel.player1
        duel.turn = opponent

        winner = loser = None
        if duel.player1_hp <= 0:
            winner, loser = duel.player2, duel.player1
        elif duel.player2_hp <= 0:
            winner, loser = duel.player1, duel.player2

        if winner:
            # Settle-once: claim inside the winner branch (a non-finishing
            # move must not consume the claim), before any await, so a
            # finishing-blow double-click or a racing timeout short-circuits.
            if not self.claim_settlement():
                return
            duel.is_over = True
            self.cog.active_duels.pop(self.duel_key, None)
            await self.cog.update_leaderboard(
                winner_id=winner.id,
                loser_id=loser.id,
                guild_id=self.guild_id,
            )
            wear_notes = await _tick_duel_gear_wear(
                self.guild_id,
                duel.player1,
                duel.player2,
            )
            description = (
                f"{action_text}\n\n"
                f"**{duel.player1.display_name}** — "
                f"{max(duel.player1_hp, 0)}/{duel.player1_max_hp} HP\n"
                f"**{duel.player2.display_name}** — "
                f"{max(duel.player2_hp, 0)}/{duel.player2_max_hp} HP\n\n"
                f"🏆 {winner.mention} wins!"
            )
            if wear_notes:
                description += "\n\n" + "\n".join(wear_notes)
            embed = discord.Embed(
                title="⚔️ Deathmatch Ended",
                description=description,
                color=discord.Color.gold(),
            )
            # Swap to the terminal result view (Help + Games nav + Rematch) so a
            # finished PvP duel is never a dead-end (owner directive 2026-06-23,
            # previously applied only to the bot path via _BotDuelResultView).
            from views.games.deathmatch_panel import _PvpDuelResultView

            await interaction.response.edit_message(
                embed=embed,
                view=_PvpDuelResultView(self.cog, duel.player1, duel.player2),
            )
        else:
            await interaction.response.edit_message(
                embed=self.build_embed(action_text),
                view=self,
            )


class _ChallengeView(discord.ui.View):
    def __init__(
        self,
        cog: Deathmatch,
        challenger: discord.Member,
        opponent: discord.Member,
        duel_key: tuple,
        ctx: commands.Context,
    ):
        super().__init__(timeout=30.0)
        self.cog = cog
        self.challenger = challenger
        self.opponent = opponent
        self.duel_key = duel_key
        self.ctx = ctx
        self.message: discord.Message | None = None
        # Set once the challenge is accepted or declined. accept/decline also
        # call self.stop() (which cancels the timeout), but this flag guards the
        # race where on_timeout() was already firing — so a stale 30s challenge
        # timer can never overwrite the live (or finished) duel message with an
        # "expired" notice.
        self._resolved = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.opponent:
            await interaction.response.send_message(
                "This challenge is not for you!",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        # The challenge was already accepted/declined — the duel now owns the
        # message, so the expired-challenge notice must not clobber it.
        if self._resolved:
            return
        embed = discord.Embed(
            title="⚔️ Challenge Expired",
            description=f"{self.opponent.mention} did not respond in time.",
            color=discord.Color.greyple(),
        )
        if self.message:
            try:
                # Not a dead-end — offer Help + Games nav and a 🔁 Rematch
                # (re-challenge) instead of a dead embed.
                from views.games.deathmatch_panel import _PvpDuelResultView

                await self.message.edit(
                    embed=embed,
                    view=_PvpDuelResultView(self.cog, self.challenger, self.opponent),
                )
            except Exception:
                pass

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def btn_accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        self._resolved = True
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        # Both fighters bring their equipped combat gear (guild-scoped) into the
        # duel via the shared EffectiveStats seam.
        gid = interaction.guild_id or 0
        duel = _Duel(
            self.challenger,
            self.opponent,
            p1_stats=equipment.compute_stats(
                await db.get_equipment(str(self.challenger.id), gid),
            ),
            p2_stats=equipment.compute_stats(
                await db.get_equipment(str(self.opponent.id), gid),
            ),
        )
        self.cog.active_duels[self.duel_key] = duel
        # PR 8 — read the per-guild turn timeout setting. Falls back to
        # the historical 60s default when unset or unparseable (the
        # resolver coerces + validates and degrades invalid rows to the
        # SettingSpec default).
        from services.settings_resolution import resolve_value

        turn_timeout = float(
            await resolve_value(
                interaction.guild_id or 0,
                "deathmatch",
                "turn_timeout",
                60,
            ),
        )
        duel_view = _DuelView(
            self.cog,
            duel,
            self.duel_key,
            self.ctx,
            timeout=turn_timeout,
            # Thread the originating guild explicitly: the panel-initiated PvP
            # path builds this challenge with ctx=None, so the duel must take
            # its guild from the accept interaction rather than ``ctx.guild``
            # (which would AttributeError on resolve).
            guild_id=gid,
        )
        await interaction.response.edit_message(
            embed=duel_view.build_embed(),
            view=duel_view,
        )
        duel_view.message = await interaction.original_response()
        # Cancel this challenge view's 30s timeout — the duel owns the message
        # lifecycle now (and _DuelView has its own turn timeout). Without this
        # the stale challenge timer fires mid/post-match and overwrites the duel
        # with "Challenge Expired".
        self.stop()

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def btn_decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        self._resolved = True
        embed = discord.Embed(
            title="⚔️ Challenge Declined",
            description=f"{self.opponent.mention} declined the duel.",
            color=discord.Color.greyple(),
        )
        # Not a dead-end — swap to the result view (Help + Games nav + a
        # 🔁 Rematch the challenger can use to re-issue the challenge).
        from views.games.deathmatch_panel import _PvpDuelResultView

        await interaction.response.edit_message(
            embed=embed,
            view=_PvpDuelResultView(self.cog, self.challenger, self.opponent),
        )
        # Challenge resolved — stop the view so its timeout can't later fire and
        # replace this "Declined" notice with an "Expired" one.
        self.stop()


class Deathmatch(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.active_duels: dict[tuple, _Duel] = {}

    async def cog_load(self) -> None:
        """PR 8 — register the Deathmatch settings schema so
        ``!platform setup-readiness`` can surface its configuration
        state.
        """
        from cogs.deathmatch.schemas import register_schemas

        register_schemas()

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Deathmatch panel.

        PR 6 replaced the previous empty ``discord.ui.View()`` with
        :class:`DeathmatchPanelView` so the panel is actionable from
        Help/Games (Fight Bot / Challenge Player / Rules buttons).
        """
        from views.games.deathmatch_panel import (
            DeathmatchPanelView,
            build_deathmatch_overview_embed,
        )

        view = DeathmatchPanelView(interaction.user)
        return build_deathmatch_overview_embed(), view

    @commands.command(
        name="dm_challenge",
        aliases=["deathmatch", "challenge", "dm"],
        # Fluency spellings, deliberately advertised — not legacy.
        extras={"alias_classification": "power_user_shortcut"},
    )
    @cooldown(1, 30, BucketType.user)
    async def challenge(self, ctx: commands.Context, opponent: discord.Member):
        """Challenge another user to a deathmatch duel."""
        if opponent == ctx.author:
            await ctx.send("You cannot challenge yourself!")
            return
        if opponent.bot:
            await ctx.send("You cannot challenge a bot!")
            return

        duel_key = tuple(sorted([ctx.author.id, opponent.id]))
        if duel_key in self.active_duels:
            await ctx.send(
                "A duel between you and the opponent is already in progress.",
            )
            return
        for existing_key in self.active_duels:
            if ctx.author.id in existing_key or opponent.id in existing_key:
                await ctx.send("Either you or the opponent is already in a duel.")
                return

        embed = discord.Embed(
            title="⚔️ Deathmatch Challenge",
            description=(
                f"{ctx.author.mention} has challenged {opponent.mention} to a duel!\n\n"
                "Press **Accept** or **Decline** below."
            ),
            color=discord.Color.red(),
        )
        embed.set_footer(text="You have 30 seconds to respond.")
        view = _ChallengeView(self, ctx.author, opponent, duel_key, ctx)  # type: ignore[arg-type]
        view.message = await ctx.send(embed=embed, view=view)

    async def update_leaderboard(
        self,
        winner_id: int,
        loser_id: int,
        guild_id: int = 0,
    ) -> None:
        await db.update_deathmatch(winner_id, loser_id, guild_id)

    @challenge.error
    async def challenge_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"You're on cooldown! Please try again in {int(error.retry_after)} seconds.",
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Couldn't find the user. Please mention a valid member.")
        else:
            await ctx.send("An error occurred while processing the command.")
            raise error

    @commands.command(name="dm_help", aliases=["deathmatch_help"])
    async def dm_help(self, ctx: commands.Context):
        """Display help information for Deathmatch commands."""
        embed = discord.Embed(
            title="Deathmatch Help",
            description=(
                "**Commands:**\n"
                "`!deathmatch @User` — Challenge a user to a duel.\n"
                "`!leaderboard deathmatch` — View the top duelists.\n\n"
                "**During a Duel:**\n"
                "Use the **⚔️ Attack** and **🛡️ Defend** buttons in the duel message."
            ),
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Deathmatch(bot))
