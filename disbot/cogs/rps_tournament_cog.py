"""RPS tournament cog — commands + tournament flow (S4.6).

Persistence, recovery, channel helpers, stat helpers, lifecycle tasks,
and bot-match handling have been extracted to ``cogs/rps_tournament/``
submodules.  This file is now the cog itself — commands, the
tournament registration / round flow that holds per-instance state
(``self.players`` / ``self.scores`` / ``self.matches`` /
``self.match_channels`` / ``self.current_round``), and listeners.

Symbols re-exported for back-compat with existing tests:

  RPS_TOURNAMENT_SUBSYSTEM, RPS_TOURNAMENT_VERSION
        — moved to cogs.rps_tournament._persistence (the
          ``inspect.getsource(save_tournament_entry)`` invariant has
          a stable home there).

The ``inspect.getsource(RPSTournamentCog.try_register_player)`` test
was migrated to inspect ``save_tournament_entry`` — see
``tests/unit/cogs/test_rps_tournament_persistence.py`` for the
updated assertion.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import cast

import discord
from discord.ext import commands

from cogs.rps_tournament._bot_matches import (
    channel_is_bot_match,
    handle_bot_match_move,
    run_rps_bot_command,
)
from cogs.rps_tournament._bot_matches import reset_state as _reset_bot_match_state
from cogs.rps_tournament._helpers import (
    add_player_to_db,
    cleanup_orphaned_channels,
    clear_stale_tournament_flag,
    create_match_channel,
    delete_all_match_channels,
    schedule_channel_deletion,
    update_player_stats,
)
from cogs.rps_tournament._persistence import (  # noqa: F401 — re-exported for back-compat with tests
    RPS_TOURNAMENT_SUBSYSTEM,
    RPS_TOURNAMENT_VERSION,
    on_guild_remove_rps,
    recover_rps_pvp_pending,
    recover_rps_tournament,
    save_tournament_entry,
)
from cogs.rps_tournament._quickplay import run_quickrps_command
from cogs.rps_tournament._stage import RPS_STAGE_NAME, RpsTournamentStage
from cogs.rps_tournament.rules import (
    GAME_MODES,
    MOVE_ALIASES,
    determine_winner,
    normalize_move,
)
from core.runtime import tasks
from core.runtime.permission_checks import admin_or_owner
from services import (  # noqa: F401 — game_state_service kept for back-compat patch sites
    economy_service,
    game_state_service,
    game_wager_workflow,
    tournament_state_service,
)
from utils.terminal_guard import SettleOnceMixin
from utils.ui_constants import INFO_COLOR
from views.rps import _RpsRegistrationView
from views.rps._helpers import RPS_PVP_ESCROW_SUBSYSTEM

logger = logging.getLogger("bot")


class RockPaperScissorsCog(
    SettleOnceMixin,
    commands.Cog,
    name="Rock Paper Scissors",
):  # type: ignore[call-arg]
    """Rock Paper Scissors: quick play, PvP, bot matches, tournaments."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.tournament_active = False
        self.registration_active = False
        self.registration_message = None
        self.registration_emoji = "✅"
        self.registration_timer = 600  # 10 minutes in seconds
        self.reminder_interval = 300  # 5 minutes in seconds
        self.players: list[discord.Member] = []
        self.scores: dict[discord.Member, int] = {}
        self.matches: dict[discord.Member, dict] = {}
        self.current_round: list[discord.Member] = []
        self.match_channels: dict[int, list[discord.Member]] = {}
        self.game_mode = "classic"
        # Pure rules tables live in cogs/rps_tournament/rules.py (S4.4).
        # Held as attributes so any historical introspection still works.
        self.move_aliases = MOVE_ALIASES
        self.game_modes = GAME_MODES
        self.inactivity_limit = 300  # 5 minutes inactivity limit
        self.reminder_task = None
        # Role to mention in reminders.
        self.registration_role: discord.Role | None = None
        # Bot-match state lives at module level in
        # ``cogs/rps_tournament/_bot_matches.py``; reset on cog init/
        # unload to preserve the pre-extraction "reload wipes state"
        # semantics.
        _reset_bot_match_state()
        # settings is mixed (str default_mode, int default_best_of) — the
        # union annotation + two casts at the read sites narrow for mypy.
        self.settings: dict[str, str | int] = {
            "default_mode": "classic",
            "default_best_of": 3,
        }
        self.entry_fee = 0
        self.paid_players: set[int] = set()  # players who paid the entry fee

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the RPS hub panel.

        Phase 7 Option A: router-only panel listing Single Round / Tournament
        / Rules. Tournament state stays in this cog; the panel routes to
        the existing typed commands and never duplicates match orchestration.
        """
        from views.games.rps_panel import RPSPanelView, build_rps_overview_embed

        view = RPSPanelView(interaction.user)
        return build_rps_overview_embed(), view

    # ------------------------------------------------------------------
    # Lifecycle + recovery (delegators preserve test invariants)
    # ------------------------------------------------------------------

    async def cog_load(self) -> None:
        from cogs.rps_tournament.schemas import register_schemas
        from core.runtime import message_pipeline

        register_schemas()  # PR 8 — registers RPS_CONFIG_SCHEMA.
        tasks.spawn("rps:clear_stale_flag", clear_stale_tournament_flag(self.bot))
        tasks.spawn("rps:cleanup_orphaned", cleanup_orphaned_channels(self.bot))
        # PR G1 — drop any rps_pvp_pending game_state rows left over
        # from a previous process.
        tasks.spawn("rps:recover_pvp_pending", self._recover_rps_pvp_pending())
        # P0-1 — refund any stranded PvP escrow (stakes debited at accept
        # but the match never settled because the bot bounced).
        tasks.spawn(
            "rps:recover_pvp_escrow",
            game_wager_workflow.recover_escrow(
                RPS_PVP_ESCROW_SUBSYSTEM,
                reason="rps:pvp_escrow_refund",
            ),
        )
        # PR G6 — refund stranded tournament entries.  Same shape as
        # blackjack tournament: entry fees were debited at registration
        # and never paid back if the bot crashed before the final
        # payout in ``check_tournament_progress``.
        tasks.spawn("rps:recover_tournament", self._recover_rps_tournament())
        message_pipeline.register(RpsTournamentStage(self))

    def cog_unload(self):
        """Cancel reminder + all spawned RPS tasks; clear bot-match state."""
        from core.runtime import message_pipeline

        if self.reminder_task and not self.reminder_task.done():
            self.reminder_task.cancel()
        tasks.cancel_by_prefix("rps:")
        _reset_bot_match_state()
        message_pipeline.unregister(RPS_STAGE_NAME)

    async def _recover_rps_pvp_pending(self) -> None:
        """Delegator — see ``cogs.rps_tournament._persistence``."""
        await recover_rps_pvp_pending()

    async def _recover_rps_tournament(self) -> None:
        """Delegator — see ``cogs.rps_tournament._persistence``."""
        await recover_rps_tournament()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        """Wipe rps subsystem rows for a departed guild (delegator)."""
        await on_guild_remove_rps(guild.id)
        # P0-1 — refund stranded PvP escrow for the departing guild.
        await game_wager_workflow.recover_escrow(
            RPS_PVP_ESCROW_SUBSYSTEM,
            reason="rps:pvp_escrow_refund",
            guild_id=guild.id,
        )

    # ------------------------------------------------------------------
    # Tournament registration
    # ------------------------------------------------------------------

    @commands.command(name="rpsregister", aliases=["rpsreg"])
    async def rps_register(
        self,
        ctx,
        role: discord.Role = None,
        entry_fee: int | None = None,
    ):
        """Starts the registration period with a reaction role message.  !rpsregister [@role] [entry_fee]"""
        if self.tournament_active:
            await ctx.send(
                "Cannot start registration after the tournament has started.",
            )
            return

        if self.registration_active:
            await ctx.send("Registration is already active.")
            return

        existing = await tournament_state_service.get_active(ctx.guild.id)
        if existing:
            await ctx.send(
                f"A **{existing}** tournament is already active in this server.",
            )
            return

        # PR 8 — fall back to the guild-configured default entry fee
        # when omitted; operator can pass 0 to override.
        if entry_fee is None:
            from cogs.rps_tournament.schemas import resolve_default_entry_fee

            entry_fee = await resolve_default_entry_fee(ctx.guild.id)
        self.entry_fee = entry_fee

        await tournament_state_service.set_active(ctx.guild.id, "rps")

        self.registration_active = True
        self.registration_role = role

        # Send the registration message
        fee_str = f"**{self.entry_fee}** 🪙" if self.entry_fee else "Free"
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors Tournament Registration 🎮",
            description=(
                "React ✅ or click **Join** to sign up!\n"
                f"Registration ends in {self.registration_timer // 60} minutes."
            ),
            color=INFO_COLOR,
        )
        embed.add_field(name="Entry Fee", value=fee_str, inline=True)
        embed.add_field(
            name="Game Mode",
            value=cast(str, self.settings["default_mode"]).capitalize(),
            inline=True,
        )
        if role:
            embed.add_field(name="Attention", value=f"{role.mention}", inline=False)

        reg_view = _RpsRegistrationView(self)
        reg_msg = await ctx.send(embed=embed, view=reg_view)
        self.registration_message = reg_msg
        await reg_msg.add_reaction(self.registration_emoji)

        # Start the registration timer
        self.reminder_task = tasks.spawn(
            f"rps:countdown:{ctx.guild.id}",
            self.registration_countdown(ctx),
        )

    async def registration_countdown(self, ctx):
        """Handles the registration timer and reminders."""
        try:
            remaining_time = self.registration_timer
            while remaining_time > 0:
                if remaining_time == self.registration_timer // 2:
                    # Send a reminder at half time
                    await self.send_reminder(ctx)
                await asyncio.sleep(5)  # Check every 5 seconds for cancellation
                remaining_time -= 5
            # End of registration period
            await self.end_registration(ctx)
        except asyncio.CancelledError:
            # Handle cancellation if needed
            pass

    async def send_reminder(self, ctx):
        """Sends a reminder message mentioning the specified role."""
        if self.registration_role:
            await ctx.send(
                f"Reminder: {self.registration_role.mention}, registration is still open! React to sign up.",
            )
        else:
            await ctx.send(
                "Reminder: Registration is still open! React to the registration message to sign up.",
            )

    async def end_registration(self, ctx):
        """Ends the registration period and collects the list of participants."""
        self.registration_active = False
        if self.reminder_task and not self.reminder_task.done():
            self.reminder_task.cancel()
            self.reminder_task = None

        if self.registration_message is None:
            # rps_register always sets this — defensive narrow for mypy.
            return

        await ctx.send("Registration period has ended. Collecting participants...")

        # Fetch the users who reacted
        try:
            registration_message = await ctx.fetch_message(self.registration_message.id)
            reaction = discord.utils.get(
                registration_message.reactions,
                emoji=self.registration_emoji,
            )
            if reaction:
                users = [u async for u in reaction.users()]
                for user in users:
                    if not user.bot:
                        await self.try_register_player(user, ctx.guild.id)
                await ctx.send(
                    f"{len(self.players)} players have registered for the tournament.",
                )
            else:
                await ctx.send("No participants registered.")
        except Exception as e:
            logger.exception(f"Error ending registration: {e}")
            await ctx.send("An error occurred while ending registration.")

        if len(self.players) < 2:
            await tournament_state_service.clear_active(ctx.guild.id)

    async def try_register_player(self, user, guild_id: int) -> bool:
        """Check entry fee, deduct if needed, register player. Returns success.

        The persistence call lives in
        ``cogs.rps_tournament._persistence.save_tournament_entry`` — the
        ``inspect.getsource`` test invariant moved with it.
        """
        if user.id in self.paid_players or user in self.players:
            return False  # already registered
        if self.entry_fee > 0:
            # P0-1 — debit the fee and write the recovery row in ONE
            # transaction (the old flow debited, then saved the row in a
            # separate call: a crash between lost the fee with no row to
            # refund from).  channel_id=0 keeps the guild-wide natural
            # key; state={"bet": fee} matches the recovery convention.
            try:
                await game_wager_workflow.enter_tournament(
                    guild_id=guild_id,
                    user_id=user.id,
                    channel_id=0,
                    subsystem=RPS_TOURNAMENT_SUBSYSTEM,
                    version=RPS_TOURNAMENT_VERSION,
                    fee=self.entry_fee,
                    reason="rps:entry_fee",
                )
            except economy_service.InsufficientFundsError:
                return False
            self.paid_players.add(user.id)
        self.players.append(user)
        self.scores[user] = 0
        await add_player_to_db(user, guild_id)
        return True

    # ------------------------------------------------------------------
    # Tournament start + bracket scheduling
    # ------------------------------------------------------------------

    @commands.command(name="rpsstart", aliases=["rpsbegin"])
    @admin_or_owner()
    async def rps_start(self, ctx, mode=None, best_of: int = None):
        """Starts the RPS tournament. Usage: !rps_start [mode] [best_of]"""
        if self.tournament_active:
            await ctx.send("Tournament is already active.")
            return

        if self.registration_active:
            await ctx.send(
                "Cannot start the tournament while registration is still active.",
            )
            return

        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(
                f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}",
            )
            return

        if best_of is None:
            best_of = cast(int, self.settings["default_best_of"])
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send(
                "Please provide an odd positive integer for the number of rounds.",
            )
            return

        if len(self.players) < 2:
            await ctx.send("Not enough players registered to start the tournament.")
            return

        self.tournament_active = True
        self.rearm_settlement()  # new tournament → new payout claim
        self.game_mode = mode
        self.current_round = self.players.copy()
        random.shuffle(self.current_round)
        await ctx.send(
            f"Tournament started with game mode: {self.game_mode}, Best of {best_of}",
        )
        await self.start_round(ctx, best_of)

    @commands.command(name="rpsbot")
    async def rps_bot(self, ctx, mode=None, best_of: int = None, *members_or_roles):
        """Starts matches against the bot.  Delegator — see _bot_matches."""
        await run_rps_bot_command(
            ctx,
            self.settings["default_mode"],
            self.settings["default_best_of"],
            mode,
            best_of,
            members_or_roles,
        )

    @commands.command(name="rpsmatchup")
    @admin_or_owner()
    async def rps_matchup(self, ctx, player1: discord.Member, player2: discord.Member):
        """Manually creates a match between two specific members."""
        if not self.tournament_active:
            await ctx.send("Tournament is not active.")
            return

        if player1 not in self.players or player2 not in self.players:
            await ctx.send("Both players must be registered in the tournament.")
            return

        match_channel = await create_match_channel(
            ctx.guild,
            player1,
            player2,
            ctx,
        )
        if match_channel is None:
            await ctx.send("Failed to create match channel.")
            return

        self.matches[player1] = {
            "opponent": player2,
            "channel": match_channel.id,
            "move": None,
            "wins": 0,
            "opponent_wins": 0,
            "best_of": self.settings["default_best_of"],
            "mode": self.game_mode,
        }
        self.matches[player2] = {
            "opponent": player1,
            "channel": match_channel.id,
            "move": None,
            "wins": 0,
            "opponent_wins": 0,
            "best_of": self.settings["default_best_of"],
            "mode": self.game_mode,
        }
        self.match_channels[match_channel.id] = [player1, player2]

        await match_channel.send(
            f"{player1.mention} vs {player2.mention}\n"
            f"Game mode: {self.game_mode.capitalize()}, Best of {self.settings['default_best_of']}\n"
            "Please enter your move.",
        )

        # Remove players from current_round to prevent duplicate matches
        if player1 in self.current_round:
            self.current_round.remove(player1)
        if player2 in self.current_round:
            self.current_round.remove(player2)

    async def start_round(self, ctx, best_of):
        """Starts a new round in the tournament."""
        await ctx.send("Starting a new round...")
        self.matches.clear()
        self.match_channels.clear()
        round_players = self.current_round.copy()
        self.current_round = []

        while len(round_players) >= 2:
            player1 = round_players.pop()
            player2 = round_players.pop()
            match_channel = await create_match_channel(
                ctx.guild,
                player1,
                player2,
                ctx,
            )
            if match_channel is None:
                await ctx.send("Failed to create match channel.")
                continue
            self.matches[player1] = {
                "opponent": player2,
                "channel": match_channel.id,
                "move": None,
                "wins": 0,
                "opponent_wins": 0,
                "best_of": best_of,
                "mode": self.game_mode,
            }
            self.matches[player2] = {
                "opponent": player1,
                "channel": match_channel.id,
                "move": None,
                "wins": 0,
                "opponent_wins": 0,
                "best_of": best_of,
                "mode": self.game_mode,
            }
            self.match_channels[match_channel.id] = [player1, player2]

            await match_channel.send(
                f"{player1.mention} vs {player2.mention}\n"
                f"Game mode: {self.game_mode.capitalize()}, Best of {best_of}\n"
                "Please enter your move.",
            )

        if round_players:
            # Handle odd player out
            player = round_players.pop()
            self.current_round.append(player)
            await ctx.send(
                f"{player.display_name} advances to the next round by default.",
            )

    # ------------------------------------------------------------------
    # Listeners
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Registers users as they react to the registration message."""
        if user.bot:
            return

        if not self.registration_active or self.registration_message is None:
            return

        if reaction.message.id != self.registration_message.id:
            return

        if str(reaction.emoji) != self.registration_emoji:
            return

        guild_id = reaction.message.guild.id if reaction.message.guild else 0
        ok = await self.try_register_player(user, guild_id)
        if ok:
            await reaction.message.channel.send(
                f"{user.display_name} has registered for the tournament.",
            )

    async def _process_tournament_message(self, message):
        """Capture player moves in tournament match channels.  See _stage.py."""
        channel = message.channel

        # Check for player vs bot matches
        if channel_is_bot_match(channel.id):
            await handle_bot_match_move(message)
            return

        # Check for player vs player matches
        if channel.id not in self.match_channels:
            return

        player = message.author
        if player not in self.match_channels[channel.id]:
            return

        match = self.matches.get(player)
        if not match:
            return

        if match["move"] is not None:
            await channel.send(f"{player.mention}, you have already made your move.")
            return

        move = message.content.lower().strip()
        move = normalize_move(move, match["mode"])
        if move is None:
            await channel.send(f"{player.mention}, invalid move. Please try again.")
            return

        match["move"] = move
        await channel.send(f"{player.mention}, your move has been recorded.")

        opponent = match["opponent"]
        opponent_match = self.matches.get(opponent)
        if opponent_match and opponent_match["move"] is not None:
            # Both players have made their moves
            await self.resolve_match(player, opponent, channel)

    async def resolve_match(self, player1, player2, channel):
        """Determines the match outcome and advances the tournament."""
        match1 = self.matches[player1]
        match2 = self.matches[player2]
        move1 = match1["move"]
        move2 = match2["move"]

        winner = determine_winner(move1, move2, match1["mode"])
        if winner == 0:
            await channel.send("It's a tie! Please both select your moves again.")
            match1["move"] = None
            match2["move"] = None
            update_player_stats(player1, "tie")
            update_player_stats(player2, "tie")
            return
        if winner == 1:
            match1["wins"] += 1
            match2["opponent_wins"] += 1
            winning_player = player1
            update_player_stats(player1, "win")
            update_player_stats(player2, "loss")
        else:
            match2["wins"] += 1
            match1["opponent_wins"] += 1
            winning_player = player2
            update_player_stats(player2, "win")
            update_player_stats(player1, "loss")

        await channel.send(
            f"{winning_player.mention} wins this round!\n"
            f"{player1.display_name} played {move1.capitalize()}.\n"
            f"{player2.display_name} played {move2.capitalize()}.",
        )

        # Check if someone has won the match
        required_wins = (match1["best_of"] // 2) + 1
        if match1["wins"] >= required_wins:
            # Player 1 wins the match
            self.current_round.append(player1)
            await channel.send(
                f"{player1.mention} wins the match and advances to the next round!",
            )
            await schedule_channel_deletion(channel)
            del self.matches[player1]
            del self.matches[player2]
            self.match_channels.pop(channel.id, None)
            # Check if round is over
            if not self.matches:
                await self.check_tournament_progress(channel.guild, channel)
        elif match2["wins"] >= required_wins:
            # Player 2 wins the match
            self.current_round.append(player2)
            await channel.send(
                f"{player2.mention} wins the match and advances to the next round!",
            )
            await schedule_channel_deletion(channel)
            del self.matches[player1]
            del self.matches[player2]
            self.match_channels.pop(channel.id, None)
            # Check if round is over
            if not self.matches:
                await self.check_tournament_progress(channel.guild, channel)
        else:
            # Continue the match
            match1["move"] = None
            match2["move"] = None
            await channel.send("Next round! Please enter your move.")

    async def check_tournament_progress(self, guild, last_channel):
        """Checks if the tournament is over or starts a new round."""
        if len(self.current_round) == 1:
            # Settle-once: racing resolvers both reach here; the FREE-reward
            # leg has no escrow rows, so this claim is its only guard.
            if not self.claim_settlement():
                return
            winner = self.current_round[0]
            # P0-1 — pay the winner the escrowed pot (the sum of the
            # actual entry rows, not a recomputed fee×players) and delete
            # those rows in ONE idempotent transaction.  This replaces
            # the credit-then-separate-clear pair, so a re-run can never
            # double-pay and recovery can never refund an already-settled
            # tournament.
            result = await game_wager_workflow.payout_tournament(
                guild_id=guild.id,
                subsystem=RPS_TOURNAMENT_SUBSYSTEM,
                winner_id=winner.id,
                reason="rps:tournament_win",
                free_reward=100,
                free_reason="rps:tournament_free_reward",
            )
            msg_lines = [f"🏆 **{winner.display_name}** has won the RPS Tournament! 🏆"]
            if result.paid and self.entry_fee > 0:
                msg_lines.append(
                    f"💰 Payout: **{result.amount}** 🪙 "
                    f"(Balance: {result.new_winner_balance} 🪙)",
                )
            elif result.paid:
                msg_lines.append(f"🎁 Free tournament reward: **{result.amount}** 🪙")
            announce = guild.system_channel or last_channel
            await announce.send("\n".join(msg_lines))
            self.tournament_active = False
            await tournament_state_service.clear_active(guild.id)
            self.players.clear()
            self.scores.clear()
            self.matches.clear()
            self.current_round.clear()
            self.match_channels.clear()
            # Clean up any remaining match channels
            await delete_all_match_channels(guild)
        else:
            await self.start_round(last_channel, self.settings["default_best_of"])

    # ------------------------------------------------------------------
    # Error handlers + help/settings + quickplay
    # ------------------------------------------------------------------

    @rps_register.error
    async def rps_register_error(self, ctx, error):
        """Handles errors for rps_register command."""
        await ctx.send(f"An error occurred: {str(error)}")
        logger.exception(f"Error in rps_register command: {error}")

    @rps_start.error
    async def rps_start_error(self, ctx, error):
        """Handles errors for rps_start command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to start the tournament.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
        logger.exception(f"Error in rps_start command: {error}")

    @commands.command(name="rpshelp")
    async def rps_help(self, ctx):
        """Displays help information for RPS tournament commands."""
        help_text = (
            "**Rock Paper Scissors Commands:**\n"
            "`!rps` - Open the RPS panel (quick play, bet match, challenge a player, tournament, rules).\n"
            "`!rpsregister [@role]` - Start tournament registration. Optionally mention a role to notify.\n"
            "`!rpsstart [mode] [best_of]` - Start the tournament (Admin only). Modes: classic, lizard_spock, chess, elemental.\n"
            "`!rpsbot [mode] [best_of] [@members/@roles]` - Play against the bot.\n"
            "`!rpssettings [setting] [value]` - Update RPS settings (Admin only).\n"
            "`!rpshelp` - Show this help message.\n"
            "During tournament/bot matches, type your move in the match channel without any prefix.\n"
            "Valid moves depend on the game mode selected."
        )
        await ctx.send(help_text)

    @commands.command(name="rpssettings")
    @admin_or_owner()
    async def rps_settings(self, ctx, setting: str, value):
        """Updates bot settings."""
        if setting not in self.settings:
            await ctx.send(
                f"Invalid setting. Available settings: {', '.join(self.settings.keys())}",
            )
            return
        if setting == "default_mode":
            if value not in self.game_modes:
                await ctx.send(
                    f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}",
                )
                return
        elif setting == "default_best_of":
            try:
                value = int(value)
                if value % 2 == 0 or value < 1:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    "Please provide an odd positive integer for default_best_of.",
                )
                return
        self.settings[setting] = value
        await ctx.send(f"Setting `{setting}` updated to `{value}`.")

    # ------------------------------------------------------------------
    # Quick-play RPS with coins (button-based, single-player vs bot)
    # ------------------------------------------------------------------

    @commands.command(name="rps")
    async def quickrps(
        self,
        ctx: commands.Context,
        target: discord.Member | None = None,
        bet: int = 0,
    ):
        """Quick RPS.  !rps [bet]  or  !rps @player [bet]"""
        await run_quickrps_command(ctx, target, bet)


# Back-compat alias — PR 3 renamed ``RPSTournamentCog`` to
# ``RockPaperScissorsCog`` but the old name stays importable so any
# out-of-tree imports, test references, or pickled state that
# reference ``cogs.rps_tournament_cog.RPSTournamentCog`` continue to
# resolve to the same class object.
RPSTournamentCog = RockPaperScissorsCog


async def setup(bot):
    await bot.add_cog(RockPaperScissorsCog(bot))
