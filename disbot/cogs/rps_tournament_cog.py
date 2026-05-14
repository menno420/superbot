from __future__ import annotations

import asyncio
import logging
import os
import random

import discord
from discord.ext import commands
from utils import db as global_db
from utils.channels import (
    cleanup_category,
    create_private_channel,
    get_or_create_category,
)
from utils.tournaments import TournamentRegistration

logger = logging.getLogger("bot")

_FREE_WIN = 30  # coins for free-play win


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

    @commands.command(name="rpsregister", aliases=["rpsreg"])
    @commands.has_permissions(administrator=True)
    async def rps_register(self, ctx, role: discord.Role = None, entry_fee: int = 0):
        """Starts the registration period with a reaction role message.  !rpsregister [@role] [entry_fee]"""
        self.entry_fee = max(0, entry_fee)
        if self.tournament_active:
            await ctx.send(
                "Cannot start registration after the tournament has started."
            )
            return

        if self.registration_active:
            await ctx.send("Registration is already active.")
            return

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
            color=discord.Color.blue(),
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
        self.reminder_task = asyncio.create_task(self.registration_countdown(ctx))

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
                f"Reminder: {self.registration_role.mention}, registration is still open! React to sign up."
            )
        else:
            await ctx.send(
                "Reminder: Registration is still open! React to the registration message to sign up."
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
                registration_message.reactions, emoji=self.registration_emoji
            )
            if reaction:
                users = [u async for u in reaction.users()]
                for user in users:
                    if not user.bot:
                        await self.try_register_player(user, ctx.guild.id)
                await ctx.send(
                    f"{len(self.players)} players have registered for the tournament."
                )
            else:
                await ctx.send("No participants registered.")
        except Exception as e:
            logger.exception(f"Error ending registration: {e}")
            await ctx.send("An error occurred while ending registration.")

    async def add_player_to_db(self, user) -> None:
        """Ensures the player exists in the async RPS stats table."""
        try:
            await global_db.rps_ensure_player(user.id, user.display_name)
        except Exception as e:
            logger.exception("Error adding RPS player to database: %s", e)

    async def try_register_player(self, user, guild_id: int) -> bool:
        """Check entry fee, deduct if needed, register player. Returns success."""
        if user.id in self.paid_players or user in self.players:
            return False  # already registered
        if self.entry_fee > 0:
            bal = await global_db.get_coins(user.id, guild_id)
            if bal < self.entry_fee:
                return False
            await global_db.add_coins(user.id, guild_id, -self.entry_fee)
            self.paid_players.add(user.id)
        self.players.append(user)
        self.scores[user] = 0
        await self.add_player_to_db(user)
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
                "Cannot start the tournament while registration is still active."
            )
            return

        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(
                f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}"
            )
            return

        if best_of is None:
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send(
                "Please provide an odd positive integer for the number of rounds."
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
            f"Tournament started with game mode: {self.game_mode}, Best of {best_of}"
        )
        await self.start_round(ctx, best_of)

    @commands.command(name="rpsbot")
    async def rps_bot(self, ctx, mode=None, best_of: int = None, *members_or_roles):
        """Starts matches against the bot."""
        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(
                f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}"
            )
            return

        if best_of is None:
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send(
                "Please provide an odd positive integer for the number of rounds."
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
                    f"Failed to create match channel for {player.display_name}."
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
                "Please enter your move."
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
            ctx.guild, player1, player2, ctx
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
            "Please enter your move."
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
                ctx.guild, player1, player2, ctx
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
                "Please enter your move."
            )

        if round_players:
            # Handle odd player out
            player = round_players.pop()
            self.current_round.append(player)
            await ctx.send(
                f"{player.display_name} advances to the next round by default."
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
                f"{user.display_name} has registered for the tournament."
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
                f"{player.mention}, invalid move. Please try again."
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
                f"{player.mention} wins the match against the bot!"
            )
            await self.schedule_channel_deletion(message.channel)
            del self.bot_matches[player]
            self.bot_match_channels.discard(message.channel.id)
            return  # Prevent further execution
        elif match["bot_wins"] >= required_wins:
            await message.channel.send("Bot wins the match!")
            await self.schedule_channel_deletion(message.channel)
            del self.bot_matches[player]
            self.bot_match_channels.discard(message.channel.id)
            return  # Prevent further execution
        else:
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
        else:
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
        elif winner == 1:
            match1["wins"] += 1
            match2["opponent_wins"] += 1
            winning_player = player1
            losing_player = player2
            self.update_player_stats(player1, "win")
            self.update_player_stats(player2, "loss")
        else:
            match2["wins"] += 1
            match1["opponent_wins"] += 1
            winning_player = player2
            losing_player = player1
            self.update_player_stats(player2, "win")
            self.update_player_stats(player1, "loss")

        await channel.send(
            f"{winning_player.mention} wins this round!\n"
            f"{player1.display_name} played {move1.capitalize()}.\n"
            f"{player2.display_name} played {move2.capitalize()}."
        )

        # Check if someone has won the match
        required_wins = (match1["best_of"] // 2) + 1
        if match1["wins"] >= required_wins:
            # Player 1 wins the match
            self.current_round.append(player1)
            await channel.send(
                f"{player1.mention} wins the match and advances to the next round!"
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
                f"{player2.mention} wins the match and advances to the next round!"
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
        """Schedule an async stats update without blocking the event loop."""
        asyncio.create_task(self._async_update_stat(player.id, result))

    async def _async_update_stat(self, user_id: int, result: str) -> None:
        try:
            await global_db.rps_update_stat(user_id, result)
        except Exception as e:
            logger.exception("Error updating RPS player stats: %s", e)

    async def schedule_channel_deletion(self, channel):
        """Schedules the deletion of a match channel after a delay."""
        await asyncio.sleep(300)  # Wait for 5 minutes
        try:
            await channel.delete()
        except discord.Forbidden:
            logger.warning(
                f"Failed to delete channel {channel.name}: insufficient permissions."
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while deleting channel {channel.name}: {e}"
            )

    async def check_tournament_progress(self, guild, last_channel):
        """Checks if the tournament is over or starts a new round."""
        if len(self.current_round) == 1:
            winner = self.current_round[0]
            pot = self.entry_fee * len(self.paid_players)
            msg_lines = [f"🏆 **{winner.display_name}** has won the RPS Tournament! 🏆"]
            if pot:
                new_bal = await global_db.add_coins(winner.id, guild.id, pot)
                msg_lines.append(f"💰 Payout: **{pot}** 🪙 (Balance: {new_bal} 🪙)")
            elif self.entry_fee == 0:
                reward = 100
                new_bal = await global_db.add_coins(winner.id, guild.id, reward)
                msg_lines.append(f"🎁 Free tournament reward: **{reward}** 🪙")
            announce = guild.system_channel or last_channel
            await announce.send("\n".join(msg_lines))
            self.tournament_active = False
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
                f"Invalid setting. Available settings: {', '.join(self.settings.keys())}"
            )
            return
        if setting == "default_mode":
            if value not in self.game_modes:
                await ctx.send(
                    f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}"
                )
                return
        elif setting == "default_best_of":
            try:
                value = int(value)
                if value % 2 == 0 or value < 1:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    "Please provide an odd positive integer for default_best_of."
                )
                return
        self.settings[setting] = value
        await ctx.send(f"Setting `{setting}` updated to `{value}`.")

    async def cog_load(self):
        asyncio.create_task(self._cleanup_orphaned_channels())

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
                            "This channel will be deleted in 5 minutes."
                        )
                    except Exception:
                        pass
                await asyncio.sleep(300)
                await cleanup_category(cat)

    def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        if self.reminder_task and not self.reminder_task.done():
            self.reminder_task.cancel()

    # ------------------------------------------------------------------
    # Quick-play RPS with coins (button-based, single-player vs bot)
    # ------------------------------------------------------------------

    @commands.command(name="rps")
    async def quickrps(
        self, ctx: commands.Context, target: discord.Member | None = None, bet: int = 0
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
            view = _RpsPvpChallengeView(ctx.author, target, ctx.guild.id, bet)
            embed = discord.Embed(
                title="✂️ RPS Challenge!",
                description=(
                    f"{ctx.author.mention} challenges {target.mention} to Rock-Paper-Scissors "
                    f"({bet_str}).\n{target.mention}, do you accept?"
                ),
                color=discord.Color.blurple(),
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
        view = _RpsView(ctx.author, ctx.guild.id, bet)
        bet_str = f"**{bet}** 🪙" if bet else f"Free play (win = +{_FREE_WIN} 🪙)"
        embed = discord.Embed(
            title="✂️ Rock · Paper · Scissors",
            description=f"Bet: {bet_str}\nChoose your move!",
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


# ---------------------------------------------------------------------------
# Quick-play RPS View
# ---------------------------------------------------------------------------

_RPS_WINS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
_RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}


class _RpsView(discord.ui.View):
    def __init__(self, user: discord.Member, guild_id: int, bet: int):
        super().__init__(timeout=60)
        self.user = user
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This game isn't yours.", ephemeral=True
            )
            return False
        return True

    async def _play(self, interaction: discord.Interaction, player_move: str):
        for item in self.children:
            item.disabled = True

        bot_move = random.choice(["rock", "paper", "scissors"])
        pe, be = _RPS_EMOJI[player_move], _RPS_EMOJI[bot_move]

        if player_move == bot_move:
            result = "🤝 Tie!"
            coin_delta = 0
            color = discord.Color.blurple()
        elif _RPS_WINS[player_move] == bot_move:
            payout = self.bet if self.bet else _FREE_WIN
            result = f"🎉 You win! +{payout} 🪙"
            coin_delta = payout
            color = discord.Color.green()
        else:
            loss = -self.bet if self.bet else 0
            result = f"😞 Bot wins. {loss} 🪙" if self.bet else "😞 Bot wins."
            coin_delta = loss
            color = discord.Color.red()

        new_bal = await global_db.add_coins(self.user.id, self.guild_id, coin_delta)
        embed = discord.Embed(
            title="✂️ Rock · Paper · Scissors",
            description=(
                f"You: **{player_move}** {pe}  vs  Bot: **{bot_move}** {be}\n\n"
                f"{result}\n"
                f"Balance: **{new_bal}** 🪙"
            ),
            color=color,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.grey)
    async def rock(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.grey)
    async def paper(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.grey)
    async def scissors(self, i: discord.Interaction, _: discord.ui.Button):
        await self._play(i, "scissors")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Game timed out.", view=self)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# RPS Registration View (button-based join)
# ---------------------------------------------------------------------------


class _RpsRegistrationView(discord.ui.View):
    def __init__(self, cog: RPSTournamentCog):
        super().__init__(timeout=None)  # lives until tournament starts
        self.cog = cog

    @discord.ui.button(
        label="Join Tournament", style=discord.ButtonStyle.green, emoji="✅"
    )
    async def join_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        cog = self.cog
        if not cog.registration_active:
            await interaction.response.send_message(
                "Registration is no longer open.", ephemeral=True
            )
            return
        guild_id = interaction.guild_id or 0
        ok = await cog.try_register_player(interaction.user, guild_id)
        if ok:
            await interaction.response.send_message(
                f"✅ Registered! ({len(cog.players)} player(s) so far)", ephemeral=True
            )
        else:
            bal = await global_db.get_coins(interaction.user.id, guild_id)
            if cog.entry_fee > 0 and bal < cog.entry_fee:
                await interaction.response.send_message(
                    f"❌ Need **{cog.entry_fee}** 🪙 to enter (you have {bal}).",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "You're already registered!", ephemeral=True
                )


# ---------------------------------------------------------------------------
# RPS PvP Challenge
# ---------------------------------------------------------------------------

_rps_pvp_pending: dict[frozenset, dict] = (
    {}
)  # {p1,p2} → {choices, guild_id, bet, channel_id}


class _RpsPvpChallengeView(discord.ui.View):
    def __init__(
        self,
        challenger: discord.Member,
        opponent: discord.Member,
        guild_id: int,
        bet: int,
    ):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.guild_id = guild_id
        self.bet = bet
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message(
                "This challenge isn't for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="✅ Challenge accepted — both players, choose your move!",
            view=self,
        )
        key = frozenset({self.challenger.id, self.opponent.id})
        _rps_pvp_pending[key] = {
            "choices": {},
            "guild_id": self.guild_id,
            "bet": self.bet,
            "channel_id": interaction.channel_id,
        }
        # Send ephemeral choose-views to both players
        ch = interaction.channel
        play_view = _RpsPvpPlayView(
            self.challenger, self.opponent, self.guild_id, self.bet, ch
        )
        await ch.send(
            f"{self.challenger.mention} {self.opponent.mention} — click below to pick your move (only you can see your choice):",
            view=play_view,
        )
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"❌ {self.opponent.display_name} declined the challenge.",
            view=self,
        )
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="⏰ Challenge timed out.", view=self)
        except Exception:
            pass


class _RpsPvpPlayView(discord.ui.View):
    """Visible to the channel; each player clicks to get their ephemeral move picker."""

    def __init__(
        self,
        p1: discord.Member,
        p2: discord.Member,
        guild_id: int,
        bet: int,
        channel: discord.TextChannel,
    ):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.guild_id = guild_id
        self.bet = bet
        self.channel = channel
        self.choices: dict[int, str] = {}
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message(
                "You're not part of this match.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Pick your move", style=discord.ButtonStyle.blurple, emoji="✂️"
    )
    async def pick(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id in self.choices:
            await interaction.response.send_message(
                "You already picked!", ephemeral=True
            )
            return
        picker_view = _RpsMovePickerView(interaction.user.id, self)
        await interaction.response.send_message(
            "Choose your move — only you can see this:",
            view=picker_view,
            ephemeral=True,
        )

    async def record_choice(self, user_id: int, move: str):
        self.choices[user_id] = move
        if len(self.choices) == 2:
            await self._resolve()

    async def _resolve(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass
        self.stop()

        m1 = self.choices.get(self.p1.id, "forfeit")
        m2 = self.choices.get(self.p2.id, "forfeit")

        def _wins(a, b):
            return {"rock": "scissors", "scissors": "paper", "paper": "rock"}.get(
                a
            ) == b

        e = {"rock": "🪨", "paper": "📄", "scissors": "✂️", "forfeit": "❌"}

        if m1 == "forfeit" and m2 == "forfeit":
            result, coin_delta, winner_id = "🤝 Both forfeited.", 0, None
        elif m1 == "forfeit":
            result, coin_delta, winner_id = (
                f"{self.p2.mention} wins (opponent forfeited)!",
                self.bet,
                self.p2.id,
            )
        elif m2 == "forfeit":
            result, coin_delta, winner_id = (
                f"{self.p1.mention} wins (opponent forfeited)!",
                self.bet,
                self.p1.id,
            )
        elif m1 == m2:
            result, coin_delta, winner_id = "🤝 Tie! No coins exchanged.", 0, None
        elif _wins(m1, m2):
            result, coin_delta, winner_id = (
                f"🎉 {self.p1.mention} wins!",
                self.bet,
                self.p1.id,
            )
        else:
            result, coin_delta, winner_id = (
                f"🎉 {self.p2.mention} wins!",
                self.bet,
                self.p2.id,
            )

        if coin_delta and winner_id:
            loser_id = self.p2.id if winner_id == self.p1.id else self.p1.id
            payout = coin_delta if coin_delta else _FREE_WIN
            await global_db.add_coins(winner_id, self.guild_id, payout)
            await global_db.add_coins(loser_id, self.guild_id, -payout)

        embed = discord.Embed(
            title="✂️ RPS PvP Result",
            description=(
                f"{self.p1.mention}: **{m1}** {e.get(m1, '')}\n"
                f"{self.p2.mention}: **{m2}** {e.get(m2, '')}\n\n"
                f"{result}"
            ),
            color=discord.Color.green() if winner_id else discord.Color.blurple(),
        )
        await self.channel.send(embed=embed)

    async def on_timeout(self):
        # Anyone who didn't choose forfeits
        for pid in (self.p1.id, self.p2.id):
            if pid not in self.choices:
                self.choices[pid] = "forfeit"
        if len(self.choices) == 2:
            await self._resolve()


class _RpsMovePickerView(discord.ui.View):
    """Ephemeral view for picking a move in PvP."""

    def __init__(self, user_id: int, parent: _RpsPvpPlayView):
        super().__init__(timeout=55)
        self.user_id = user_id
        self.parent = parent

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.grey)
    async def rock(self, i: discord.Interaction, _):
        await self._pick(i, "rock")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.grey)
    async def paper(self, i: discord.Interaction, _):
        await self._pick(i, "paper")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.grey)
    async def scissors(self, i: discord.Interaction, _):
        await self._pick(i, "scissors")

    async def _pick(self, interaction: discord.Interaction, move: str):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"You chose **{move}** — waiting for opponent…", view=self
        )
        self.stop()
        await self.parent.record_choice(self.user_id, move)


async def setup(bot):
    await bot.add_cog(RPSTournamentCog(bot))


# For discord.py version 1.x, comment out the above and uncomment the following:
# def setup(bot):
#     bot.add_cog(RPSTournamentCog(bot))
