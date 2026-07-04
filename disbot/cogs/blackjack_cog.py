"""Blackjack cog — commands, listeners, lifecycle, recovery (S4.5).

The pre-extraction layout had every state class, persistence helper,
view class, and orchestration function inline (1700+ LOC).  S4.5
relocates:

  * data classes + module dicts + constants → cogs/blackjack/_state.py
  * save/clear helpers                       → cogs/blackjack/_persistence.py
  * 4 view classes + embed builders + PvP/tournament orchestration
                                            → views/blackjack/

This file is now the cog itself — commands, listeners, cog_load /
cog_unload recovery, and the on_guild_remove cleanup hook —  plus the
``_launch_tournament`` helper that the !bjstart / autostart paths
share.

Back-compat re-exports at the bottom of the file preserve every
``from cogs.blackjack_cog import X`` test path.  Test patches that
target ``cogs.blackjack_cog.game_state_service.X`` need to be moved to
``cogs.blackjack._persistence.game_state_service.X`` (see the test
files updated in this PR — patching tracks where the function looks
up the symbol, not where the symbol is re-exported).
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from cogs.blackjack._persistence import (  # noqa: F401 — re-exported
    _clear_pvp_match,
    _clear_solo_game,
    _clear_tournament_entry,
    _is_solo_game,
    _pvp_canonical_user_id,
    _save_game_state,
    _save_pvp_match,
    _save_solo_game,
    _save_tournament_entry,
    _serialize_pvp_hand,
)

# Re-exports for test back-compat (see docstring).  Underscore-prefixed
# imports are flagged by ruff so we collect them via __all__ below
# instead of relying on F401 noqa pragmas.
from cogs.blackjack._state import (  # noqa: F401 — re-exported
    BLACKJACK_PVP_ESCROW_SUBSYSTEM,
    BLACKJACK_PVP_SUBSYSTEM,
    BLACKJACK_PVP_VERSION,
    BLACKJACK_SOLO_SUBSYSTEM,
    BLACKJACK_SOLO_VERSION,
    BLACKJACK_TOURNAMENT_SUBSYSTEM,
    BLACKJACK_TOURNAMENT_VERSION,
    FREE_WIN_COINS,
    TOURN_BET_PER_ROUND,
    TOURN_START_CHIPS,
    _active,
    _BjTournament,
    _Game,
    _pvp,
    _PvPState,
    _tournaments,
    _TournPlayerState,
)
from core.runtime import resources, tasks
from core.runtime.permission_checks import admin_or_owner
from services import (
    economy_service,
    game_state_service,
    game_wager_workflow,
    tournament_state_service,
)
from services.blackjack_engine import is_blackjack as _is_blackjack
from utils import db
from utils.channels import cleanup_category, create_private_channel
from utils.ui_constants import ECONOMY_COLOR, SUCCESS_COLOR
from views.blackjack import (  # noqa: F401 — re-exported
    BlackjackView,
    _ChallengeView,
    _check_tourn_done,
    _game_embed,
    _resolve_pvp,
    _start_pvp,
    _start_tourn_round,
    _tourn_embed,
    _TournBlackjackView,
    _TournRegistrationView,
    _update_tourn_embed,
)

logger = logging.getLogger("bot")


class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Blackjack hub panel.

        Phase 7 Option A: router-only panel that lists Classic and Rules.
        Game-engine code paths are untouched; Practice/Replay are deferred
        to Phase 7b once the engine-side design is settled.
        """
        from views.games.blackjack_panel import (
            BlackjackPanelView,
            build_blackjack_overview_embed,
        )

        view = BlackjackPanelView(interaction.user)
        return build_blackjack_overview_embed(), view

    # ------------------------------------------------------------------
    # Lifecycle + recovery
    # ------------------------------------------------------------------

    async def cog_load(self):
        from cogs.blackjack.schemas import register_schemas

        register_schemas()  # PR 8 — registers BLACKJACK_CONFIG_SCHEMA.
        tasks.spawn("blackjack:cleanup_orphaned", self._cleanup_orphaned_tournaments())
        # PR G2/G3 — drop blackjack solo + PvP game_state rows left
        # over from a previous process.  Live views cannot be
        # re-attached.  No coins are refunded — both modes settle at
        # resolve and never pre-debit, so the user simply keeps their
        # balance and starts a new game.
        tasks.spawn("blackjack:recover_solo", self._recover_blackjack_solo())
        tasks.spawn("blackjack:recover_pvp", self._recover_blackjack_pvp())
        # P0-1 — refund any stranded PvP escrow (stakes debited at accept
        # but the match never settled because the bot bounced).
        tasks.spawn(
            "blackjack:recover_pvp_escrow",
            game_wager_workflow.recover_escrow(
                BLACKJACK_PVP_ESCROW_SUBSYSTEM,
                reason="blackjack:pvp_escrow_refund",
            ),
        )
        # PR G5 — tournament recovery DOES refund.  Entry fees were
        # debited at launch; if the bot crashed before _check_tourn_done
        # paid out the pot, those coins are still in limbo.  Refund
        # each player and clear the row.
        tasks.spawn(
            "blackjack:recover_tournament",
            self._recover_blackjack_tournament(),
        )

    def cog_unload(self):
        """Cancel cleanup + tournament-timer tasks so a reload doesn't leak them."""
        tasks.cancel_by_prefix("blackjack:")

    async def _recover_blackjack_solo(self) -> None:
        try:
            rows = await game_state_service.list_active_for_subsystem(
                BLACKJACK_SOLO_SUBSYSTEM,
            )
        except Exception as exc:
            logger.warning("blackjack_solo recovery skipped: %s", exc)
            return
        if not rows:
            return
        cleared = 0
        for row in rows:
            try:
                version = row.get("version")
                if version != BLACKJACK_SOLO_VERSION:
                    logger.info(
                        "blackjack_solo recovery: dropping version-mismatch "
                        "row id=%s (saved=%s, current=%s)",
                        row["id"],
                        version,
                        BLACKJACK_SOLO_VERSION,
                    )
                await game_state_service.clear_by_id(row["id"])
                cleared += 1
            except Exception as exc:
                logger.warning(
                    "blackjack_solo recovery: clear failed for id=%s: %s",
                    row.get("id"),
                    exc,
                )
        if cleared:
            logger.info(
                "blackjack_solo recovery: cleared %d stranded hand(s)",
                cleared,
            )

    async def _recover_blackjack_pvp(self) -> None:
        try:
            rows = await game_state_service.list_active_for_subsystem(
                BLACKJACK_PVP_SUBSYSTEM,
            )
        except Exception as exc:
            logger.warning("blackjack_pvp recovery skipped: %s", exc)
            return
        if not rows:
            return
        cleared = 0
        for row in rows:
            try:
                version = row.get("version")
                if version != BLACKJACK_PVP_VERSION:
                    logger.info(
                        "blackjack_pvp recovery: dropping version-mismatch "
                        "row id=%s (saved=%s, current=%s)",
                        row["id"],
                        version,
                        BLACKJACK_PVP_VERSION,
                    )
                await game_state_service.clear_by_id(row["id"])
                cleared += 1
            except Exception as exc:
                logger.warning(
                    "blackjack_pvp recovery: clear failed for id=%s: %s",
                    row.get("id"),
                    exc,
                )
        if cleared:
            logger.info(
                "blackjack_pvp recovery: cleared %d stranded match(es)",
                cleared,
            )

    async def _recover_blackjack_tournament(self) -> None:
        """Refund every stranded tournament entry then clear the row.

        Unlike the solo/PvP recovery paths, this one MUST refund:
        entry fees were debited at launch and never paid back if the
        bot crashed before _check_tourn_done.  The refund reason
        string is filterable in economy_audit_log for incident
        forensics.
        """
        try:
            rows = await game_state_service.list_active_for_subsystem(
                BLACKJACK_TOURNAMENT_SUBSYSTEM,
            )
        except Exception as exc:
            logger.warning("blackjack_tournament recovery skipped: %s", exc)
            return
        if not rows:
            return
        refunded = 0
        cleared = 0
        for row in rows:
            try:
                version = row.get("version")
                if version != BLACKJACK_TOURNAMENT_VERSION:
                    logger.info(
                        "blackjack_tournament recovery: version-mismatch row "
                        "id=%s (saved=%s, current=%s) — refunding the entry "
                        "fee before dropping",
                        row["id"],
                        version,
                        BLACKJACK_TOURNAMENT_VERSION,
                    )
                # The entry fee was debited at launch and is owed regardless
                # of the state-schema version: a VERSION bump on the
                # merge=deploy restart must NOT forfeit live tournament fees
                # (the previous code cleared version-mismatch rows without
                # refunding).  `bet` is a stable top-level int in state, so
                # refund it whenever present, then clear the row either way.
                state = row.get("state") or {}
                bet = state.get("bet")
                if isinstance(bet, int) and bet > 0:
                    try:
                        await economy_service.refund(
                            guild_id=row["guild_id"],
                            user_id=row["user_id"],
                            amount=bet,
                            reason="blackjack_tournament:restart_refund",
                        )
                        refunded += 1
                    except Exception as exc:
                        logger.warning(
                            "blackjack_tournament refund failed for "
                            "user=%d guild=%d: %s",
                            row.get("user_id"),
                            row.get("guild_id"),
                            exc,
                        )
                await game_state_service.clear_by_id(row["id"])
                cleared += 1
            except Exception as exc:
                logger.warning(
                    "blackjack_tournament recovery: row id=%s failed: %s",
                    row.get("id"),
                    exc,
                )
        if cleared or refunded:
            logger.info(
                "blackjack_tournament recovery: cleared %d row(s), "
                "issued %d refund(s)",
                cleared,
                refunded,
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        """PR G2/G3/G5 — wipe blackjack rows for a departed guild.

        Tournament rows additionally trigger a refund — guild removal
        before tournament resolution is equivalent to a crash from the
        player's perspective.
        """
        # Tournament path: refund + clear (entries were pre-debited).
        try:
            rows = await game_state_service.list_active_for_subsystem(
                BLACKJACK_TOURNAMENT_SUBSYSTEM,
                guild_id=guild.id,
            )
            for row in rows:
                state = row.get("state") or {}
                bet = state.get("bet")
                if isinstance(bet, int) and bet > 0:
                    try:
                        await economy_service.refund(
                            guild_id=row["guild_id"],
                            user_id=row["user_id"],
                            amount=bet,
                            reason="blackjack_tournament:guild_remove_refund",
                        )
                    except Exception as exc:
                        logger.warning(
                            "blackjack_tournament on_guild_remove "
                            "refund failed for user=%d: %s",
                            row.get("user_id"),
                            exc,
                        )
                try:
                    await game_state_service.clear_by_id(row["id"])
                except Exception as exc:
                    logger.warning(
                        "blackjack_tournament on_guild_remove clear "
                        "failed for id=%s: %s",
                        row.get("id"),
                        exc,
                    )
        except Exception as exc:
            logger.warning(
                "blackjack_tournament on_guild_remove failed for guild=%d: %s",
                guild.id,
                exc,
            )

        # Solo + PvP paths: clear without refund (no pre-debit).
        for subsystem in (BLACKJACK_SOLO_SUBSYSTEM, BLACKJACK_PVP_SUBSYSTEM):
            try:
                rows = await game_state_service.list_active_for_subsystem(
                    subsystem,
                    guild_id=guild.id,
                )
                for row in rows:
                    try:
                        await game_state_service.clear_by_id(row["id"])
                    except Exception as exc:
                        logger.warning(
                            "%s on_guild_remove: clear id=%s failed: %s",
                            subsystem,
                            row.get("id"),
                            exc,
                        )
            except Exception as exc:
                logger.warning(
                    "%s on_guild_remove failed for guild=%d: %s",
                    subsystem,
                    guild.id,
                    exc,
                )

        # P0-1 — refund stranded PvP escrow for the departing guild.
        await game_wager_workflow.recover_escrow(
            BLACKJACK_PVP_ESCROW_SUBSYSTEM,
            reason="blackjack:pvp_escrow_refund",
            guild_id=guild.id,
        )

    async def _cleanup_orphaned_tournaments(self):
        """On startup, find leftover BJ Tournament categories and notify players."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            flag = await tournament_state_service.get_active(guild.id)
            if flag == "blackjack":
                await tournament_state_service.clear_active(guild.id)
            cat = resources.resolve_channel(
                guild,
                name="BJ Tournament",
                kind="category",
            )
            if not cat or not cat.channels:
                continue
            for ch in cat.channels:
                # Match channels are TextChannel; other types in the
                # category union can't receive a "tournament interrupted"
                # notice.
                if not isinstance(ch, discord.TextChannel):
                    continue
                try:
                    await ch.send(
                        "⚠️ The bot restarted and this tournament was interrupted. "
                        "This channel will be deleted in 5 minutes. "
                        "Use `!bjtournament` to start a new one.",
                    )
                except Exception:
                    pass
            await asyncio.sleep(300)
            await cleanup_category(cat)

    # ---- reaction-based tournament registration ----
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "✅":
            return
        tourn = _tournaments.get(payload.guild_id)
        if not tourn or tourn.started or not tourn.reg_message:
            return
        if payload.message_id != tourn.reg_message.id:
            return
        uid = payload.user_id
        guild = self.bot.get_guild(payload.guild_id)
        if guild:
            member = resources.resolve_member(guild, uid)
            if member and member.bot:
                return
        ok, _ = await tourn.try_join(uid)
        if ok:
            await _update_tourn_embed(tourn)

    # ---- commands ----

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(
        self,
        ctx: commands.Context,
        target: discord.Member | None = None,
        bet: int = 0,
    ):
        """Play blackjack.  !bj [bet]  or  !bj @player [bet]"""
        if bet < 0:
            await ctx.send("Bet must be 0 or a positive number.", delete_after=5)
            return

        # PvP mode
        if target and target != ctx.author:
            if target.bot:
                await ctx.send("You can't challenge a bot to PvP.", delete_after=5)
                return
            key = frozenset({ctx.author.id, target.id})
            if key in _pvp:
                await ctx.send(
                    "There's already a PvP game between these players.",
                    delete_after=8,
                )
                return
            if bet > 0:
                bal = await db.get_coins(ctx.author.id, ctx.guild.id)
                if bet > bal:
                    await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                    return
            bet_str = f"**{bet}** 🪙" if bet else "free play"
            view = _ChallengeView(ctx.author, target, ctx.guild.id, bet)  # type: ignore[arg-type]
            embed = discord.Embed(
                title="🃏 Blackjack Challenge!",
                description=(
                    f"{ctx.author.mention} challenges {target.mention} to Blackjack "
                    f"({bet_str}).\n{target.mention}, do you accept?"
                ),
                color=SUCCESS_COLOR,
            )
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # Solo vs bot
        key = (ctx.author.id, ctx.guild.id)  # type: ignore[assignment]
        if key in _active:
            await ctx.send("You already have a game running!", delete_after=8)
            return
        if bet > 0:
            bal = await db.get_coins(ctx.author.id, ctx.guild.id)
            if bet > bal:
                await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                return

        game = _Game(ctx.author.id, ctx.guild.id, bet, channel_id=ctx.channel.id)
        _active[key] = game  # type: ignore[index]

        if _is_blackjack(game.player):
            payout = int(bet * 1.5) if bet else FREE_WIN_COINS
            new_bal = await economy_service.credit(
                ctx.guild.id,
                ctx.author.id,
                payout,
                reason="blackjack:natural_blackjack",
                actor_id=ctx.author.id,
            )
            embed = _game_embed(game, reveal=True)
            embed.color = ECONOMY_COLOR
            embed.add_field(
                name="🎉 Blackjack!",
                value=f"+{payout} 🪙  |  Balance: **{new_bal}** 🪙",
                inline=False,
            )
            _active.pop(key)  # type: ignore[call-overload]
            await ctx.send(embed=embed)
            return

        view = BlackjackView(game)  # type: ignore[assignment]
        msg = await ctx.send(embed=_game_embed(game), view=view)
        view.message = msg
        # PR G2 — initial save once the view is live.  If the bot
        # crashes between deal and any further action, ``cog_load``
        # will see this row and clear it.
        await _save_game_state(game)

    @commands.command(name="bjtournament", aliases=["bjtourn"])
    @admin_or_owner()
    async def bjtournament(
        self,
        ctx: commands.Context,
        entry_fee: int | None = None,
        rounds: int = 5,
        duration_mins: int = 5,
    ):
        """Start a Blackjack tournament.  !bjtournament [entry_fee] [rounds] [mins]"""
        if _tournaments.get(ctx.guild.id):
            await ctx.send("A tournament is already running.", delete_after=8)
            return
        existing = await tournament_state_service.get_active(ctx.guild.id)
        if existing:
            await ctx.send(
                f"A **{existing}** tournament is already active in this server.",
                delete_after=8,
            )
            return
        # PR 8 — fall back to the guild-configured default entry fee
        # when the operator did not supply one explicitly.
        if entry_fee is None:
            from services.settings_resolution import resolve_value

            entry_fee = await resolve_value(
                ctx.guild.id,
                "blackjack",
                "default_entry_fee",
                0,
            )
        if entry_fee < 0 or rounds < 1 or duration_mins < 1:
            await ctx.send("Invalid parameters.", delete_after=5)
            return

        tourn = _BjTournament(
            ctx.author.id,
            ctx.guild.id,
            ctx.channel.id,
            entry_fee,
            rounds,
            duration_mins,
        )
        _tournaments[ctx.guild.id] = tourn
        await tournament_state_service.set_active(ctx.guild.id, "blackjack")

        view = _TournRegistrationView(tourn)
        msg = await ctx.send(embed=_tourn_embed(tourn), view=view)
        await msg.add_reaction("✅")
        tourn.reg_message = msg

        async def _auto_start():
            await asyncio.sleep(duration_mins * 60)
            if not tourn.started and tourn.guild_id in _tournaments:
                await _launch_tournament(tourn, ctx.guild, ctx.bot)

        tourn.timer_task = tasks.spawn(
            f"blackjack:autostart:{tourn.guild_id}",
            _auto_start(),
        )

    @commands.command(name="bjstart")
    @admin_or_owner()
    async def bjstart(self, ctx: commands.Context):
        """Manually start a pending Blackjack tournament early."""
        tourn = _tournaments.get(ctx.guild.id)
        if not tourn or tourn.started:
            await ctx.send("No pending tournament.", delete_after=5)
            return
        if tourn.timer_task:
            tourn.timer_task.cancel()
        await _launch_tournament(tourn, ctx.guild, self.bot)

    @commands.command(name="bjstatus")
    async def bjstatus(self, ctx: commands.Context):
        """Show the current tournament status."""
        tourn = _tournaments.get(ctx.guild.id)
        if not tourn:
            await ctx.send("No active tournament.", delete_after=5)
            return
        await ctx.send(embed=_tourn_embed(tourn))


async def _launch_tournament(
    tourn: _BjTournament,
    guild: discord.Guild,
    bot: commands.Bot,
):
    if tourn.started:
        return
    tourn.started = True

    announce = bot.get_channel(tourn.announce_id)
    if not tourn.players:
        if announce:
            await announce.send("❌ Tournament cancelled — no players registered.")  # type: ignore[union-attr]
        _tournaments.pop(tourn.guild_id, None)
        await tournament_state_service.clear_active(tourn.guild_id)
        return

    # P0-1 — debit each entry fee and write its recovery row in ONE
    # transaction per player (the old flow batch-debited via
    # ``deduct_fees`` then saved each row separately at channel-creation
    # time: a crash in the window lost the fee with no row to refund).
    # channel_id=0 keeps the guild-wide natural key; the per-round
    # private channel is bookkeeping, not money.
    if tourn.entry_fee:
        paid: set[int] = set()
        for uid in list(tourn.players):
            try:
                await game_wager_workflow.enter_tournament(
                    guild_id=tourn.guild_id,
                    user_id=uid,
                    channel_id=0,
                    subsystem=BLACKJACK_TOURNAMENT_SUBSYSTEM,
                    version=BLACKJACK_TOURNAMENT_VERSION,
                    fee=tourn.entry_fee,
                    reason="tournament:entry_fee",
                    extra_state={"rounds": tourn.rounds},
                )
                paid.add(uid)
            except economy_service.InsufficientFundsError:
                continue
        tourn.players = paid

    if not tourn.players:
        if announce:
            await announce.send(  # type: ignore[union-attr]
                "❌ Tournament cancelled — no players could afford the entry fee.",
            )
        _tournaments.pop(tourn.guild_id, None)
        await tournament_state_service.clear_active(tourn.guild_id)
        return

    if announce:
        await announce.send(  # type: ignore[union-attr]
            f"🃏 **Blackjack Tournament starting** with {len(tourn.players)} player(s)! "
            "Check your private channel.",
        )

    # Create private channels via shared utility
    for uid in tourn.players:
        member = resources.resolve_member(guild, uid)
        if not member:
            tourn.results[uid] = 0
            continue
        try:
            ch = await create_private_channel(
                guild,
                f"bj-{member.display_name}",
                [member],
                "BJ Tournament",
            )
            if tourn.category is None:
                tourn.category = ch.category
            ps = _TournPlayerState(
                uid,
                tourn.guild_id,
                tourn.rounds,
                channel_id=ch.id,
            )
            # The paid-entry recovery row was written atomically with the
            # fee debit in ``enter_tournament`` above (P0-1), keyed at
            # channel_id=0 — no separate save here.
            await ch.send(
                f"Welcome, {member.mention}! You have **{tourn.rounds}** rounds "
                f"and start with **{TOURN_START_CHIPS}** chips. Good luck! 🃏",
            )
            await _start_tourn_round(ps, ch, tourn, bot)
        except discord.Forbidden:
            if announce:
                await announce.send("❌ I don't have permission to create channels.")  # type: ignore[union-attr]
            _tournaments.pop(tourn.guild_id, None)
            await tournament_state_service.clear_active(tourn.guild_id)
            return
        except Exception as e:
            logger.error("Failed to create tournament channel: %s", e)
            tourn.results[uid] = 0

    await _check_tourn_done(tourn, bot)


async def setup(bot: commands.Bot):
    await bot.add_cog(BlackjackCog(bot))
    logger.info("BlackjackCog loaded.")
