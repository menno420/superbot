from __future__ import annotations

import asyncio
import logging
import random

import discord
from discord.ext import commands

from core.runtime import tasks
from services import economy_service
from utils import db as global_db
from utils.channels import cleanup_category, create_private_channel
from utils.settings_keys import ACTIVE_TOURNAMENT
from utils.ui_constants import GAME_COLOR, INFO_COLOR

# Views + shared constants moved to views/rps/ during D4 — re-exported
# below for backward compatibility with any external import of these
# private names.
from views.rps import (  # noqa: F401 — re-exported for back-compat
    _FREE_WIN,
    _RPS_EMOJI,
    _RPS_WINS,
    _rps_pvp_pending,
    _RpsMovePickerView,
    _RpsPvpChallengeView,
    _RpsPvpPlayView,
    _RpsRegistrationView,
    _RpsView,
)

logger = logging.getLogger("bot")


class RPSTournamentCog(commands.Cog, name="Rock-Paper-Scissors Tournament"):  # type: ignore[call-arg]
    """Cog for managing Rock-Paper-Scissors tournaments with multiple game modes."""

    def __init__(self, bot):
        self.bot = bot
        self.tournament_active = False
        self.registration_active = False
        self.registration_message = None
        self.registration_emoji = "✅"
        self.registration_timer = 600  # 10 minutes in seconds
        self.reminder_interval = 300  # 5 minutes in seconds
        self.players = []
        self.scores = {}
        self.matches = {}
        self.current_round = []
        self.match_channels = {}
        self.game_mode = "classic"
        self.move_aliases = self.create_move_aliases()
        self.game_modes = {
            "classic": ["rock", "paper", "scissors"],
            "lizard_spock": ["rock", "paper", "scissors", "lizard", "spock"],
            "chess": ["pawn", "knight", "queen"],
            "elemental": ["fire", "water", "grass"],
        }
        self.results = {}
        self.inactivity_limit = 300  # 5 minutes inactivity limit
        self.reminder_task = None
        self.registration_role = None  # Role to mention in reminders
        self.bot_matches = {}
        self.bot_match_channels = set()
        self.settings = {"default_mode": "classic", "default_best_of": 3}
        self.entry_fee = 0
        self.paid_players: set[int] = set()  # players who paid the entry fee

    def create_move_aliases(self):
        """Creates a dictionary of move aliases for all game modes."""
        return {
            "rock": ["rock", "stone", "pebble", "boulder", "🪨", "🤜", "✊"],
            "paper": ["paper", "sheet", "page", "📄", "📰", "✋"],
            "scissors": ["scissors", "shears", "✂️", "✌️"],
            "lizard": ["lizard", "🦎"],
            "spock": ["spock", "🖖"],
            "pawn": ["pawn", "♟️"],
            "knight": ["knight", "horse", "♞"],
            "queen": ["queen", "♛"],
            "fire": ["fire", "flame", "🔥"],
            "water": ["water", "💧", "🌊"],
            "grass": ["grass", "leaf", "🌿", "🍃"],
        }

    async def cog_load(self) -> None:
        tasks.spawn("rps:clear_stale_flag", self._clear_stale_tournament_flag())
        tasks.spawn("rps:cleanup_orphaned", self._cleanup_orphaned_channels())

    async def _clear_stale_tournament_flag(self) -> None:
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            flag = await global_db.get_setting(guild.id, ACTIVE_TOURNAMENT, "")
            if flag == "rps":
                await global_db.set_setting(guild.id, ACTIVE_TOURNAMENT, "")

    @commands.command(name="rpsregister", aliases=["rpsreg"])
    async def rps_register(self, ctx, role: discord.Role = None, entry_fee: int = 0):
        """Starts the registration period with a reaction role message.  !rpsregister [@role] [entry_fee]"""
        if self.tournament_active:
            await ctx.send(
                "Cannot start registration after the tournament has started.",
            )
            return

        if self.registration_active:
            await ctx.send("Registration is already active.")
            return

        existing = await global_db.get_setting(ctx.guild.id, ACTIVE_TOURNAMENT, "")
        if existing:
            await ctx.send(
                f"A **{existing}** tournament is already active in this server.",
            )
            return

        await global_db.set_setting(ctx.guild.id, ACTIVE_TOURNAMENT, "rps")

        self.registration_active = True
        self.registration_role = role

        # Send the registration message
        fee_str = f"**{self.entry_fee}** 🪙" if self.entry_fee else "Free"
        embed = discord.Embed(
            title="🎮 Rock-Paper-Scissors Tournament Registration 🎮",
            description=(
                "React ✅ or click **Join** to sign up!\n"
                f"Registration ends in {self.registration_timer // 60} minutes."
            ),
            color=INFO_COLOR,
        )
        embed.add_field(name="Entry Fee", value=fee_str, inline=True)
        embed.add_field(
            name="Game Mode",
            value=self.settings["default_mode"].capitalize(),
            inline=True,
        )
        if role:
            embed.add_field(name="Attention", value=f"{role.mention}", inline=False)

        reg_view = _RpsRegistrationView(self)
        self.registration_message = await ctx.send(embed=embed, view=reg_view)
        await self.registration_message.add_reaction(self.registration_emoji)

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
            await global_db.set_setting(ctx.guild.id, ACTIVE_TOURNAMENT, "")

    async def add_player_to_db(self, user, guild_id: int) -> None:
        """Ensures the player exists in the async RPS stats table.

        PR R1: ``guild_id`` is now required.  rps_players' PK is
        (user_id, guild_id) since migration 005; defaulting to 0 made
        every guild's stats collide at the same row.
        """
        try:
            await global_db.rps_ensure_player(user.id, guild_id, user.display_name)
        except Exception as e:
            logger.exception("Error adding RPS player to database: %s", e)

    async def try_register_player(self, user, guild_id: int) -> bool:
        """Check entry fee, deduct if needed, register player. Returns success."""
        if user.id in self.paid_players or user in self.players:
            return False  # already registered
        if self.entry_fee > 0:
            try:
                await economy_service.debit(
                    guild_id,
                    user.id,
                    self.entry_fee,
                    reason="rps:entry_fee",
                    actor_id=user.id,
                )
            except economy_service.InsufficientFundsError:
                return False
            self.paid_players.add(user.id)
        self.players.append(user)
        self.scores[user] = 0
        await self.add_player_to_db(user, guild_id)
        return True

    @commands.command(name="rpsstart", aliases=["rpsbegin"])
    @commands.has_permissions(administrator=True)
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
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send(
                "Please provide an odd positive integer for the number of rounds.",
            )
            return

        if len(self.players) < 2:
            await ctx.send("Not enough players registered to start the tournament.")
            return

        self.tournament_active = True
        self.game_mode = mode
        self.current_round = self.players.copy()
        random.shuffle(self.current_round)
        await ctx.send(
            f"Tournament started with game mode: {self.game_mode}, Best of {best_of}",
        )
        await self.start_round(ctx, best_of)

    @commands.command(name="rpsbot")
    async def rps_bot(self, ctx, mode=None, best_of: int = None, *members_or_roles):
        """Starts matches against the bot."""
        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(
                f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}",
            )
            return

        if best_of is None:
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send(
                "Please provide an odd positive integer for the number of rounds.",
            )
            return

        players = []
        if members_or_roles:
            for item in members_or_roles:
                member = None
                if isinstance(item, discord.Member):
                    member = item
                elif isinstance(item, str):
                    # Try to get member by ID or mention
                    member = ctx.guild.get_member_named(item)
                elif isinstance(item, discord.Role):
                    players.extend(item.members)
                    continue
                if member:
                    players.append(member)
        else:
            players.append(ctx.author)

        for player in players:
            match_channel = await self.create_bot_match_channel(ctx.guild, player, ctx)
            if match_channel is None:
                await ctx.send(
                    f"Failed to create match channel for {player.display_name}.",
                )
                continue

            self.bot_matches[player] = {
                "channel": match_channel.id,
                "wins": 0,
                "bot_wins": 0,
                "best_of": best_of,
                "mode": mode,
            }
            self.bot_match_channels.add(match_channel.id)

            await match_channel.send(
                f"{player.mention} vs **Bot**\n"
                f"Game mode: {mode.capitalize()}, Best of {best_of}\n"
                "Please enter your move.",
            )

    async def create_bot_match_channel(self, guild, player, ctx):
        """Creates a private channel for a match against the bot."""
        try:
            return await create_private_channel(
                guild,
                f"rps-{player.display_name}-vs-bot",
                [player],
                "RPS Bot Matches",
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to create channels.")
            return None
        except Exception as e:
            logger.exception(f"Error creating bot match channel: {e}")
            await ctx.send(f"An error occurred while creating the match channel: {e}")
            return None

    @commands.command(name="rpsmatchup")
    @commands.has_permissions(administrator=True)
    async def rps_matchup(self, ctx, player1: discord.Member, player2: discord.Member):
        """Manually creates a match between two specific members."""
        if not self.tournament_active:
            await ctx.send("Tournament is not active.")
            return

        if player1 not in self.players or player2 not in self.players:
            await ctx.send("Both players must be registered in the tournament.")
            return

        # Create a match between the two players
        match_channel = await self.create_match_channel(
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
            match_channel = await self.create_match_channel(
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

    async def create_match_channel(self, guild, player1, player2, ctx):
        """Creates a private channel for the match."""
        try:
            return await create_private_channel(
                guild,
                f"rps-{player1.display_name}-vs-{player2.display_name}",
                [player1, player2],
                "RPS Tournaments",
            )
        except discord.Forbidden:
            await ctx.send("I do not have permission to create channels.")
            return None
        except Exception as e:
            logger.exception(f"Error creating match channel: {e}")
            await ctx.send(f"An error occurred while creating the match channel: {e}")
            return None

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Registers users as they react to the registration message."""
        if user.bot:
            return

        if not self.registration_active:
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

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listens for moves in match channels."""
        if message.author.bot:
            return

        channel = message.channel

        # Check for player vs bot matches
        if channel.id in self.bot_match_channels:
            await self.handle_bot_match_move(message)
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
        move = await self.normalize_move(move, match["mode"])
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

    async def handle_bot_match_move(self, message):
        """Handles moves in player vs bot matches."""
        player = message.author
        match = self.bot_matches.get(player)
        if not match:
            return

        # Check if the match is already over
        required_wins = (match["best_of"] // 2) + 1
        if match["wins"] >= required_wins or match["bot_wins"] >= required_wins:
            # Match is over; inform the player and return
            await message.channel.send("The match is already over.")
            return

        move = message.content.lower().strip()
        move = await self.normalize_move(move, match["mode"])
        if move is None:
            await message.channel.send(
                f"{player.mention}, invalid move. Please try again.",
            )
            return

        bot_move = random.choice(self.game_modes[match["mode"]])
        await message.channel.send(f"Bot played: {bot_move.capitalize()}.")

        winner = await self.determine_winner(move, bot_move, match["mode"])
        if winner == 0:
            await message.channel.send("It's a tie!")
            self.update_player_stats(player, "tie")
        elif winner == 1:
            match["wins"] += 1
            await message.channel.send(f"{player.mention} wins this round!")
            self.update_player_stats(player, "win")
        else:
            match["bot_wins"] += 1
            await message.channel.send("Bot wins this round!")
            self.update_player_stats(player, "loss")

        # Check if someone has won the match
        if match["wins"] >= required_wins:
            await message.channel.send(
                f"{player.mention} wins the match against the bot!",
            )
            await self.schedule_channel_deletion(message.channel)
            del self.bot_matches[player]
            self.bot_match_channels.discard(message.channel.id)
            return  # Prevent further execution
        if match["bot_wins"] >= required_wins:
            await message.channel.send("Bot wins the match!")
            await self.schedule_channel_deletion(message.channel)
            del self.bot_matches[player]
            self.bot_match_channels.discard(message.channel.id)
            return  # Prevent further execution
        await message.channel.send("Please enter your next move.")

    async def normalize_move(self, input_move, mode=None):
        """Converts input to a valid move."""
        if not mode:
            mode = self.game_mode
        for move, aliases in self.move_aliases.items():
            if input_move in aliases:
                if move in self.game_modes[mode]:
                    return move
        return None

    async def determine_winner(self, move1, move2, mode=None):
        """Determines the winner based on the game mode."""
        if not mode:
            mode = self.game_mode
        if move1 == move2:
            return 0  # Tie

        # Define win conditions for each game mode
        win_conditions = {
            "classic": {"rock": ["scissors"], "paper": ["rock"], "scissors": ["paper"]},
            "lizard_spock": {
                "rock": ["scissors", "lizard"],
                "paper": ["rock", "spock"],
                "scissors": ["paper", "lizard"],
                "lizard": ["spock", "paper"],
                "spock": ["scissors", "rock"],
            },
            "chess": {"pawn": ["knight"], "knight": ["queen"], "queen": ["pawn"]},
            "elemental": {"fire": ["grass"], "water": ["fire"], "grass": ["water"]},
        }

        if move2 in win_conditions[mode][move1]:
            return 1  # Player 1 wins
        return 2  # Player 2 wins

    async def resolve_match(self, player1, player2, channel):
        """Determines the match outcome and advances the tournament."""
        match1 = self.matches[player1]
        match2 = self.matches[player2]
        move1 = match1["move"]
        move2 = match2["move"]

        winner = await self.determine_winner(move1, move2, match1["mode"])
        if winner == 0:
            await channel.send("It's a tie! Please both select your moves again.")
            match1["move"] = None
            match2["move"] = None
            self.update_player_stats(player1, "tie")
            self.update_player_stats(player2, "tie")
            return
        if winner == 1:
            match1["wins"] += 1
            match2["opponent_wins"] += 1
            winning_player = player1
            self.update_player_stats(player1, "win")
            self.update_player_stats(player2, "loss")
        else:
            match2["wins"] += 1
            match1["opponent_wins"] += 1
            winning_player = player2
            self.update_player_stats(player2, "win")
            self.update_player_stats(player1, "loss")

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
            await self.schedule_channel_deletion(channel)
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
            await self.schedule_channel_deletion(channel)
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

    def update_player_stats(self, player, result: str) -> None:
        """Schedule an async stats update without blocking the event loop.

        PR R1: derives ``guild_id`` from ``player.guild`` and passes it
        through so ``rps_update_stat`` writes to the correct guild row.
        Players passed in here always come from a guild context (bot
        matches and tournament matches both originate in guild channels)
        so ``player.guild`` is non-None.
        """
        guild = getattr(player, "guild", None)
        if guild is None:
            logger.warning(
                "update_player_stats: player=%s has no guild context; "
                "skipping stat update",
                player.id,
            )
            return
        tasks.spawn(
            f"rps:stat:{player.id}",
            self._async_update_stat(player.id, guild.id, result),
        )

    async def _async_update_stat(
        self,
        user_id: int,
        guild_id: int,
        result: str,
    ) -> None:
        try:
            await global_db.rps_update_stat(user_id, guild_id, result)
        except Exception as e:
            logger.exception("Error updating RPS player stats: %s", e)

    async def schedule_channel_deletion(self, channel):
        """Schedules the deletion of a match channel after a delay."""
        await asyncio.sleep(300)  # Wait for 5 minutes
        try:
            await channel.delete()
        except discord.Forbidden:
            logger.warning(
                f"Failed to delete channel {channel.name}: insufficient permissions.",
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while deleting channel {channel.name}: {e}",
            )

    async def check_tournament_progress(self, guild, last_channel):
        """Checks if the tournament is over or starts a new round."""
        if len(self.current_round) == 1:
            winner = self.current_round[0]
            pot = self.entry_fee * len(self.paid_players)
            msg_lines = [f"🏆 **{winner.display_name}** has won the RPS Tournament! 🏆"]
            if pot:
                new_bal = await economy_service.credit(
                    guild.id,
                    winner.id,
                    pot,
                    reason="rps:tournament_win",
                )
                msg_lines.append(f"💰 Payout: **{pot}** 🪙 (Balance: {new_bal} 🪙)")
            elif self.entry_fee == 0:
                reward = 100
                new_bal = await economy_service.credit(
                    guild.id,
                    winner.id,
                    reward,
                    reason="rps:tournament_free_reward",
                )
                msg_lines.append(f"🎁 Free tournament reward: **{reward}** 🪙")
            announce = guild.system_channel or last_channel
            await announce.send("\n".join(msg_lines))
            self.tournament_active = False
            await global_db.set_setting(guild.id, ACTIVE_TOURNAMENT, "")
            self.players.clear()
            self.scores.clear()
            self.matches.clear()
            self.current_round.clear()
            self.match_channels.clear()
            # Clean up any remaining match channels
            await self.delete_all_match_channels(guild)
        else:
            await self.start_round(last_channel, self.settings["default_best_of"])

    async def delete_all_match_channels(self, guild):
        """Deletes all RPS tournament match channels and their category."""
        category = discord.utils.get(guild.categories, name="RPS Tournaments")
        if category:
            await cleanup_category(category)

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
            "**Rock-Paper-Scissors Tournament Commands:**\n"
            "`!rps_register [@role]` - Starts registration. Optionally mention a role to notify.\n"
            "`!rps_start [mode] [best_of]` - Start the tournament (Admin only). Modes: classic, lizard_spock, chess, elemental.\n"
            "`!rps_bot [mode] [best_of] [@members/@roles]` - Play against the bot.\n"
            "`!rps_leaderboard` - Show the current leaderboard.\n"
            "`!rps_settings [setting] [value]` - Update bot settings (Admin only).\n"
            "`!rps_help` - Show this help message.\n"
            "During matches, simply type your move in the match channel without any prefix.\n"
            "Valid moves depend on the game mode selected."
        )
        await ctx.send(help_text)

    @commands.command(name="rpssettings")
    @commands.has_permissions(administrator=True)
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

    async def _cleanup_orphaned_channels(self):
        """On startup, clean up any leftover RPS tournament/bot-match channels."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for cat_name in ("RPS Tournaments", "RPS Bot Matches"):
                cat = discord.utils.get(guild.categories, name=cat_name)
                if not cat or not cat.channels:
                    continue
                for ch in cat.channels:
                    try:
                        await ch.send(
                            "⚠️ The bot restarted and this match was interrupted. "
                            "This channel will be deleted in 5 minutes.",
                        )
                    except Exception:
                        pass
                await asyncio.sleep(300)
                await cleanup_category(cat)

    def cog_unload(self):
        """Cancel reminder + all spawned RPS tasks so a reload doesn't leak them."""
        if self.reminder_task and not self.reminder_task.done():
            self.reminder_task.cancel()
        tasks.cancel_by_prefix("rps:")

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
        if bet < 0:
            await ctx.send("Bet must be 0 or a positive number.", delete_after=5)
            return

        # PvP challenge
        if target and target != ctx.author:
            if target.bot:
                await ctx.send("You can't challenge a bot to PvP.", delete_after=5)
                return
            if bet > 0:
                bal = await global_db.get_coins(ctx.author.id, ctx.guild.id)
                if bet > bal:
                    await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=8)
                    return
            bet_str = f"**{bet}** 🪙" if bet else "free play"
            view = _RpsPvpChallengeView(ctx.author, target, ctx.guild.id, bet)  # type: ignore[arg-type]
            embed = discord.Embed(
                title="✂️ RPS Challenge!",
                description=(
                    f"{ctx.author.mention} challenges {target.mention} to Rock-Paper-Scissors "
                    f"({bet_str}).\n{target.mention}, do you accept?"
                ),
                color=GAME_COLOR,
            )
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # vs bot
        if bet > 0:
            bal = await global_db.get_coins(ctx.author.id, ctx.guild.id)
            if bet > bal:
                await ctx.send(f"❌ You only have **{bal}** 🪙.", delete_after=10)
                return
        view = _RpsView(ctx.author, ctx.guild.id, bet)  # type: ignore[assignment, arg-type]
        bet_str = f"**{bet}** 🪙" if bet else f"Free play (win = +{_FREE_WIN} 🪙)"
        embed = discord.Embed(
            title="✂️ Rock · Paper · Scissors",
            description=f"Bet: {bet_str}\nChoose your move!",
            color=GAME_COLOR,
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(RPSTournamentCog(bot))
