# rps_cog.py

import discord
from discord.ext import commands, tasks
import asyncio
import random
import logging
import sqlite3
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RPSTournamentCog(commands.Cog, name="Rock-Paper-Scissors Tournament"):
    """Cog for managing Rock-Paper-Scissors tournaments with multiple game modes."""

    def __init__(self, bot):
        self.bot = bot
        self.tournament_active = False
        self.registration_active = False
        self.registration_message = None
        self.registration_emoji = "✅"
        self.registration_timer = 600  # 10 minutes in seconds
        self.reminder_interval = 300   # 5 minutes in seconds
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
            "elemental": ["fire", "water", "grass"]
        }
        self.results = {}
        self.inactivity_limit = 300  # 5 minutes inactivity limit
        self.reminder_task = None
        self.registration_role = None  # Role to mention in reminders
        self.bot_matches = {}
        self.bot_match_channels = set()
        self.settings = {
            "default_mode": "classic",
            "default_best_of": 3
        }
        self.db_connection = sqlite3.connect('rps_tournament.db')
        self.db_cursor = self.db_connection.cursor()
        self.create_tables()
        self.clean_up_task = self.bot.loop.create_task(self.clean_up_expired_matches())

    def create_tables(self):
        """Creates necessary tables in the database."""
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                ties INTEGER DEFAULT 0
            )
        ''')
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER,
                player2_id INTEGER,
                winner_id INTEGER,
                mode TEXT,
                best_of INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_connection.commit()

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
            "grass": ["grass", "leaf", "🌿", "🍃"]
        }

    @commands.command(name="rps_register", aliases=["rpsreg"])
    @commands.has_permissions(administrator=True)
    async def rps_register(self, ctx, role: discord.Role = None):
        """Starts the registration period with a reaction role message."""
        if self.tournament_active:
            await ctx.send("Cannot start registration after the tournament has started.")
            return

        if self.registration_active:
            await ctx.send("Registration is already active.")
            return

        self.registration_active = True
        self.registration_role = role

        # Send the registration message
        embed = discord.Embed(
            title="🎮 Rock-Paper-Scissors Tournament Registration 🎮",
            description=(
                "React with ✅ to sign up for the tournament!\n"
                f"Registration ends in {self.registration_timer // 60} minutes."
            ),
            color=discord.Color.blue()
        )
        if role:
            embed.add_field(name="Attention", value=f"{role.mention}", inline=False)

        self.registration_message = await ctx.send(embed=embed)
        await self.registration_message.add_reaction(self.registration_emoji)

        # Start the registration timer
        self.reminder_task = self.bot.loop.create_task(self.registration_countdown(ctx))

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
            await ctx.send(f"Reminder: {self.registration_role.mention}, registration is still open! React to sign up.")
        else:
            await ctx.send("Reminder: Registration is still open! React to the registration message to sign up.")

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
            reaction = discord.utils.get(registration_message.reactions, emoji=self.registration_emoji)
            if reaction:
                users = await reaction.users().flatten()
                for user in users:
                    if user.bot:
                        continue
                    if user not in self.players:
                        self.players.append(user)
                        self.scores[user] = 0
                        self.add_player_to_db(user)
                await ctx.send(f"{len(self.players)} players have registered for the tournament.")
            else:
                await ctx.send("No participants registered.")
        except Exception as e:
            logger.exception(f"Error ending registration: {e}")
            await ctx.send("An error occurred while ending registration.")

    def add_player_to_db(self, user):
        """Adds a player to the database."""
        try:
            self.db_cursor.execute('''
                INSERT OR IGNORE INTO players (id, name)
                VALUES (?, ?)
            ''', (user.id, user.display_name))
            self.db_connection.commit()
        except Exception as e:
            logger.exception(f"Error adding player to database: {e}")

    @commands.command(name="rps_start", aliases=["rpsbegin"])
    @commands.has_permissions(administrator=True)
    async def rps_start(self, ctx, mode=None, best_of: int = None):
        """Starts the RPS tournament. Usage: !rps_start [mode] [best_of]"""
        if self.tournament_active:
            await ctx.send("Tournament is already active.")
            return

        if self.registration_active:
            await ctx.send("Cannot start the tournament while registration is still active.")
            return

        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}")
            return

        if best_of is None:
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send("Please provide an odd positive integer for the number of rounds.")
            return

        if len(self.players) < 2:
            await ctx.send("Not enough players registered to start the tournament.")
            return

        self.tournament_active = True
        self.game_mode = mode
        self.current_round = self.players.copy()
        random.shuffle(self.current_round)
        await ctx.send(f"Tournament started with game mode: {self.game_mode}, Best of {best_of}")
        await self.start_round(ctx, best_of)

    @commands.command(name="rps_bot")
    async def rps_bot(self, ctx, mode=None, best_of: int = None, *members_or_roles):
        """Starts matches against the bot."""
        if mode is None:
            mode = self.settings["default_mode"]
        if mode not in self.game_modes:
            await ctx.send(f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}")
            return

        if best_of is None:
            best_of = self.settings["default_best_of"]
        if best_of % 2 == 0 or best_of < 1:
            await ctx.send("Please provide an odd positive integer for the number of rounds.")
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
                await ctx.send(f"Failed to create match channel for {player.display_name}.")
                continue

            self.bot_matches[player] = {
                "channel": match_channel.id,
                "wins": 0,
                "bot_wins": 0,
                "best_of": best_of,
                "mode": mode
            }
            self.bot_match_channels.add(match_channel.id)

            await match_channel.send(
                f"{player.mention} vs **Bot**\n"
                f"Game mode: {mode.capitalize()}, Best of {best_of}\n"
                "Please enter your move."
            )

    async def create_bot_match_channel(self, guild, player, ctx):
        """Creates a private channel for a match against the bot."""
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            player: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel_name = f"rps-{player.display_name}-vs-bot"
        category = discord.utils.get(guild.categories, name="RPS Bot Matches")
        if category is None:
            try:
                category = await guild.create_category("RPS Bot Matches")
            except discord.Forbidden:
                await ctx.send("I do not have permission to create categories.")
                return None

        try:
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
            return channel
        except discord.Forbidden:
            await ctx.send("I do not have permission to create text channels.")
            return None
        except Exception as e:
            logger.exception(f"Error creating bot match channel: {e}")
            await ctx.send(f"An error occurred while creating the match channel: {e}")
            return None

    @commands.command(name="rps_matchup")
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
        match_channel = await self.create_match_channel(ctx.guild, player1, player2, ctx)
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
            "mode": self.game_mode
        }
        self.matches[player2] = {
            "opponent": player1,
            "channel": match_channel.id,
            "move": None,
            "wins": 0,
            "opponent_wins": 0,
            "best_of": self.settings["default_best_of"],
            "mode": self.game_mode
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
            match_channel = await self.create_match_channel(ctx.guild, player1, player2, ctx)
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
                "mode": self.game_mode
            }
            self.matches[player2] = {
                "opponent": player1,
                "channel": match_channel.id,
                "move": None,
                "wins": 0,
                "opponent_wins": 0,
                "best_of": best_of,
                "mode": self.game_mode
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
            await ctx.send(f"{player.display_name} advances to the next round by default.")

    async def create_match_channel(self, guild, player1, player2, ctx):
        """Creates a private channel for the match."""
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            player1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            player2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel_name = f"rps-{player1.display_name}-vs-{player2.display_name}"
        category = discord.utils.get(guild.categories, name="RPS Tournaments")
        if category is None:
            try:
                category = await guild.create_category("RPS Tournaments")
            except discord.Forbidden:
                await ctx.send("I do not have permission to create categories.")
                return None

        try:
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
            return channel
        except discord.Forbidden:
            await ctx.send("I do not have permission to create text channels.")
            return None
        except Exception as e:
            logger.exception(f"Error creating match channel: {e}")
            await ctx.send(f"An error occurred while creating the match channel: {e}")
            return None

    @commands.command(name="rps_leaderboard", aliases=["rpslb"])
    async def rps_leaderboard(self, ctx):
        """Displays the current leaderboard."""
        try:
            self.db_cursor.execute('''
                SELECT name, wins, losses, ties FROM players ORDER BY wins DESC
            ''')
            records = self.db_cursor.fetchall()
            if not records:
                await ctx.send("No scores to display.")
                return
            leaderboard = "\n".join(
                f"{idx+1}. {name}: {wins} Wins, {losses} Losses, {ties} Ties"
                for idx, (name, wins, losses, ties) in enumerate(records)
            )
            await ctx.send(f"**Tournament Leaderboard:**\n{leaderboard}")
        except Exception as e:
            logger.exception(f"Error fetching leaderboard: {e}")
            await ctx.send("An error occurred while fetching the leaderboard.")

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

        if user not in self.players:
            self.players.append(user)
            self.scores[user] = 0
            self.add_player_to_db(user)
            await reaction.message.channel.send(f"{user.display_name} has registered for the tournament.")

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
            await message.channel.send(f"{player.mention}, invalid move. Please try again.")
            return

        bot_move = random.choice(self.game_modes[match["mode"]])
        await message.channel.send(f"Bot played: {bot_move.capitalize()}.")

        winner = await self.determine_winner(move, bot_move, match["mode"])
        if winner == 0:
            await message.channel.send("It's a tie!")
            self.update_player_stats(player, 'tie')
        elif winner == 1:
            match["wins"] += 1
            await message.channel.send(f"{player.mention} wins this round!")
            self.update_player_stats(player, 'win')
        else:
            match["bot_wins"] += 1
            await message.channel.send("Bot wins this round!")
            self.update_player_stats(player, 'loss')

        # Check if someone has won the match
        if match["wins"] >= required_wins:
            await message.channel.send(f"{player.mention} wins the match against the bot!")
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
            "classic": {
                "rock": ["scissors"],
                "paper": ["rock"],
                "scissors": ["paper"]
            },
            "lizard_spock": {
                "rock": ["scissors", "lizard"],
                "paper": ["rock", "spock"],
                "scissors": ["paper", "lizard"],
                "lizard": ["spock", "paper"],
                "spock": ["scissors", "rock"]
            },
            "chess": {
                "pawn": ["knight"],
                "knight": ["queen"],
                "queen": ["pawn"]
            },
            "elemental": {
                "fire": ["grass"],
                "water": ["fire"],
                "grass": ["water"]
            }
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
            self.update_player_stats(player1, 'tie')
            self.update_player_stats(player2, 'tie')
            return
        elif winner == 1:
            match1["wins"] += 1
            match2["opponent_wins"] += 1
            winning_player = player1
            losing_player = player2
            self.update_player_stats(player1, 'win')
            self.update_player_stats(player2, 'loss')
        else:
            match2["wins"] += 1
            match1["opponent_wins"] += 1
            winning_player = player2
            losing_player = player1
            self.update_player_stats(player2, 'win')
            self.update_player_stats(player1, 'loss')

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
            await channel.send(f"{player1.mention} wins the match and advances to the next round!")
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
            await channel.send(f"{player2.mention} wins the match and advances to the next round!")
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

    def update_player_stats(self, player, result):
        """Updates player stats in the database."""
        try:
            if result == 'win':
                self.db_cursor.execute('''
                    UPDATE players SET wins = wins + 1 WHERE id = ?
                ''', (player.id,))
            elif result == 'loss':
                self.db_cursor.execute('''
                    UPDATE players SET losses = losses + 1 WHERE id = ?
                ''', (player.id,))
            elif result == 'tie':
                self.db_cursor.execute('''
                    UPDATE players SET ties = ties + 1 WHERE id = ?
                ''', (player.id,))
            self.db_connection.commit()
        except Exception as e:
            logger.exception(f"Error updating player stats: {e}")

    async def schedule_channel_deletion(self, channel):
        """Schedules the deletion of a match channel after a delay."""
        await asyncio.sleep(300)  # Wait for 5 minutes
        try:
            await channel.delete()
        except discord.Forbidden:
            logger.warning(f"Failed to delete channel {channel.name}: insufficient permissions.")
        except Exception as e:
            logger.exception(f"An error occurred while deleting channel {channel.name}: {e}")

    async def check_tournament_progress(self, guild, last_channel):
        """Checks if the tournament is over or starts a new round."""
        if len(self.current_round) == 1:
            winner = self.current_round[0]
            # Try to send the message to the system channel
            if guild.system_channel:
                await guild.system_channel.send(
                    f"🏆 **{winner.display_name}** has won the Rock-Paper-Scissors Tournament! 🏆"
                )
            else:
                # Fallback to the channel where the last match was played
                await last_channel.send(
                    f"🏆 **{winner.display_name}** has won the Rock-Paper-Scissors Tournament! 🏆"
                )
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
        """Deletes all match channels."""
        category = discord.utils.get(guild.categories, name="RPS Tournaments")
        if category:
            for channel in category.channels:
                try:
                    await channel.delete()
                except Exception as e:
                    logger.exception(f"Error deleting match channel {channel.name}: {e}")

    @tasks.loop(minutes=10)
    async def clean_up_expired_matches(self):
        """Periodic task to clean up expired matches."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=30)
        # Implement logic to clean up matches older than cutoff

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

    @commands.command(name="rps_help")
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

    @commands.command(name="rps_settings")
    @commands.has_permissions(administrator=True)
    async def rps_settings(self, ctx, setting: str, value):
        """Updates bot settings."""
        if setting not in self.settings:
            await ctx.send(f"Invalid setting. Available settings: {', '.join(self.settings.keys())}")
            return
        if setting == "default_mode":
            if value not in self.game_modes:
                await ctx.send(f"Invalid game mode. Available modes: {', '.join(self.game_modes.keys())}")
                return
        elif setting == "default_best_of":
            try:
                value = int(value)
                if value % 2 == 0 or value < 1:
                    raise ValueError
            except ValueError:
                await ctx.send("Please provide an odd positive integer for default_best_of.")
                return
        self.settings[setting] = value
        await ctx.send(f"Setting `{setting}` updated to `{value}`.")

    def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        if self.clean_up_task:
            self.clean_up_task.cancel()
        if self.reminder_task and not self.reminder_task.done():
            self.reminder_task.cancel()
        self.db_connection.close()

# Update the setup function according to your discord.py version

# For discord.py version 2.x
async def setup(bot):
    await bot.add_cog(RPSTournamentCog(bot))

# For discord.py version 1.x, comment out the above and uncomment the following:
# def setup(bot):
#     bot.add_cog(RPSTournamentCog(bot))
