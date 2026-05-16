from __future__ import annotations

import ast
import asyncio
import difflib
import logging
import math
import operator as op
import random
import re
from datetime import datetime, timezone

import discord
from discord.ext import commands

from core.runtime import tasks
from utils import db
from views.base import BaseView


def _word_to_num(text: str) -> int | None:
    """Minimal word-to-number converter (replaces the word2number package)."""
    _ONES = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
    }
    _TENS = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }
    _MAGNITUDES = {
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
        "trillion": 1_000_000_000_000,
    }
    words = text.lower().split()
    if not words:
        return None
    result = 0
    current = 0
    for word in words:
        if word == "and":
            continue
        if word in _ONES:
            current += _ONES[word]
        elif word in _TENS:
            current += _TENS[word]
        elif word == "hundred":
            current = (current or 1) * 100
        elif word in _MAGNITUDES:
            result += (current or 1) * _MAGNITUDES[word]
            current = 0
        else:
            return None
    return result + current


logger = logging.getLogger("CountingCog")


class CountingCog(commands.Cog):
    """A cog for managing various counting games with multiple modes."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.lock = asyncio.Lock()
        self.count_data = {}

        # Precompile regex for performance
        self.number_pattern = re.compile(r"\d+")
        self.word_pattern = re.compile(
            r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
            r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
            r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
            r"eighty|ninety|hundred|thousand|million|billion|trillion|"
            r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
            r"eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
            r"seventeenth|eighteenth|nineteenth|twentieth)\b",
            re.IGNORECASE,
        )

        self.number_words_set = set(
            [
                # Cardinal numbers
                "zero",
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
                "thirteen",
                "fourteen",
                "fifteen",
                "sixteen",
                "seventeen",
                "eighteen",
                "nineteen",
                "twenty",
                "thirty",
                "forty",
                "fifty",
                "sixty",
                "seventy",
                "eighty",
                "ninety",
                "hundred",
                "thousand",
                "million",
                "billion",
                "trillion",
                # Ordinal numbers
                "first",
                "second",
                "third",
                "fourth",
                "fifth",
                "sixth",
                "seventh",
                "eighth",
                "ninth",
                "tenth",
                "eleventh",
                "twelfth",
                "thirteenth",
                "fourteenth",
                "fifteenth",
                "sixteenth",
                "seventeenth",
                "eighteenth",
                "nineteenth",
                "twentieth",
            ],
        )

        self.phrase_number_mapping = {
            "a couple": 2,
            "a few": 3,
            "several": 7,
            "a dozen": 12,
            "half a dozen": 6,
            "a half dozen": 6,
            "a bakers dozen": 13,
            "a score": 20,
            "a gross": 144,
            "a hundred": 100,
            "a thousand": 1000,
            "a million": 1000000,
            "one million": 1000000,
            "a billion": 1000000000,
            "one billion": 1000000000,
        }

        self.ordinal_mapping = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
            "tenth": 10,
            "eleventh": 11,
            "twelfth": 12,
            "thirteenth": 13,
            "fourteenth": 14,
            "fifteenth": 15,
            "sixteenth": 16,
            "seventeenth": 17,
            "eighteenth": 18,
            "nineteenth": 19,
            "twentieth": 20,
        }

        self.roman_numeral_mapping = {
            "I": 1,
            "IV": 4,
            "V": 5,
            "IX": 9,
            "X": 10,
            "XL": 40,
            "L": 50,
            "XC": 90,
            "C": 100,
            "CD": 400,
            "D": 500,
            "CM": 900,
            "M": 1000,
        }

        self.emoji_number_mapping = {
            "0️⃣": "0",
            "1️⃣": "1",
            "2️⃣": "2",
            "3️⃣": "3",
            "4️⃣": "4",
            "5️⃣": "5",
            "6️⃣": "6",
            "7️⃣": "7",
            "8️⃣": "8",
            "9️⃣": "9",
            "🔟": "10",
        }

        # Supported operators for safe evaluation
        self.operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.BitXor: op.pow,  # Allow '^' as exponentiation
            ast.USub: op.neg,
            # Add more operators if needed
        }

        # Operator mapping for replacement
        self.operator_mapping = {
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multipliedby": "*",
            "multiplied": "*",
            "multiply": "*",
            "x": "*",  # Added to handle 'x' as multiplication
            "×": "*",  # Added to handle '×' as multiplication
            "dividedby": "/",
            "divided": "/",
            "divide": "/",
            "over": "/",
            "powerof": "**",
            "tothepowerof": "**",
            "equals": "=",
            "equal": "=",
            "and": "+",  # Sometimes 'and' is used in numbers
        }

    async def cog_load(self):
        """Schedule DB state load for after the bot is connected."""
        tasks.spawn("counting:load_when_ready", self._load_when_ready())

    async def _load_when_ready(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            self.count_data[str(guild.id)] = await db.get_counting_state(guild.id)

    async def _save_guild(self, guild_id_str: str):
        try:
            guild_id = int(guild_id_str)
            await db.set_counting_state(guild_id, self.count_data.get(guild_id_str, {}))
        except Exception:
            pass

    # --------------------------------------------
    # Permission Helpers
    # --------------------------------------------

    async def is_staff_or_owner(self, ctx):
        """Check if the user is staff or the bot owner."""
        if await self.bot.is_owner(ctx.author):
            return True
        # Define staff roles by name
        staff_roles = [
            "Admin",
            "Moderator",
        ]  # Adjust these role names as per your server
        return any(role.name in staff_roles for role in ctx.author.roles)

    # Decorator to check if the user is staff or owner
    def staff_or_owner():  # type: ignore[misc]
        """Decorator to check if the user is staff or owner."""

        async def predicate(ctx):
            cog = ctx.cog
            return await cog.is_staff_or_owner(ctx)

        return commands.check(predicate)

    # --------------------------------------------
    # Commands
    # --------------------------------------------

    @commands.command(name="countingmenu", aliases=["cm"])
    @staff_or_owner()
    async def counting_menu(self, ctx):
        """Open the interactive counting game management panel."""
        view = _CountingHubView(ctx, self)
        embed = await view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @commands.command(name="start_match", aliases=["sm"])
    @staff_or_owner()
    async def start_match(self, ctx, mode: str, *args):
        """Starts a new counting match with the specified mode.
        Available modes: normal, reverse, skip, random, multiples, prime, fibonacci, squares, cubes, factorials, custom
        For 'multiples' mode, specify the multiple (e.g., 3 for multiples of 3).
        For 'custom' mode, provide a sequence of numbers separated by commas.
        """
        guild = ctx.guild
        guild_id = str(guild.id)
        mode = mode.lower()

        # Validate mode
        valid_modes = [
            "normal",
            "reverse",
            "skip",
            "random",
            "multiples",
            "prime",
            "fibonacci",
            "squares",
            "cubes",
            "factorials",
            "custom",
        ]
        if mode not in valid_modes:
            await ctx.send(
                f"Invalid mode. Available modes: {', '.join(valid_modes)}.",
                delete_after=10,
            )
            return

        # Parse additional arguments
        multiple = None
        custom_sequence = None
        if mode == "multiples":
            if not args:
                await ctx.send(
                    "Please specify a multiple for 'multiples' mode.",
                    delete_after=10,
                )
                return
            try:
                multiple = int(args[0])
                if multiple < 1:
                    raise ValueError
            except ValueError:
                await ctx.send("Multiple must be a positive integer.", delete_after=10)
                return
        elif mode == "custom":
            if not args:
                await ctx.send(
                    "Please provide a sequence of numbers for 'custom' mode.",
                    delete_after=10,
                )
                return
            try:
                custom_sequence = [
                    int(num.strip()) for num in " ".join(args).split(",")
                ]
                if not custom_sequence:
                    raise ValueError
            except ValueError:
                await ctx.send(
                    "Invalid sequence. Please provide a comma-separated list of integers.",
                    delete_after=10,
                )
                return

        async with self.lock:
            # Create a channel named after the mode with a timestamp for uniqueness
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
            channel_name = f"{mode}-counting-{timestamp}"
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
            if existing_channel:
                await ctx.send(
                    f"A channel named '{channel_name}' already exists.",
                    delete_after=10,
                )
                return

            try:
                channel = await guild.create_text_channel(channel_name)
                self.logger.info(
                    f"Created channel '{channel_name}' in guild '{guild.name}'.",
                )
            except discord.Forbidden:
                self.logger.error(
                    f"Missing permissions to create channel in guild '{guild.name}'.",
                )
                await ctx.send(
                    "I don't have permission to create channels.",
                    delete_after=10,
                )
                return
            except Exception as e:
                self.logger.error(
                    f"Error creating channel '{channel_name}' in guild '{guild.name}': {e}",
                )
                await ctx.send(
                    "An error occurred while creating the channel.",
                    delete_after=10,
                )
                return

            # Initialize channel data
            channel_id = str(channel.id)
            if guild_id not in self.count_data:
                self.count_data[guild_id] = {}
            self.count_data[guild_id].setdefault("channels", {})
            if channel_id in self.count_data[guild_id]["channels"]:
                await ctx.send(
                    "A counting match is already active in this channel.",
                    delete_after=10,
                )
                return

            # Set up mode-specific configurations
            starting_count = (
                0
                if mode
                in [
                    "normal",
                    "random",
                    "skip",
                    "multiples",
                    "prime",
                    "fibonacci",
                    "squares",
                    "cubes",
                    "factorials",
                    "custom",
                ]
                else 1000
            )
            channel_config = {
                "current_count": starting_count,
                "last_user": None,
                "taking_turns": False,
                "leaderboard": {},
                "mode": mode,
                "step": 1,
                "skip_numbers": [5, 10],
                "random_range": [1, 3],
                "multiple": multiple if mode == "multiples" else None,
                "custom_sequence": custom_sequence if mode == "custom" else None,
                "sequence_index": 0,
                "last_count_time": datetime.now(tz=timezone.utc).timestamp(),
                "reset_on_wrong_count": False,
                # For random mode: pre-roll the first expected value
                "next_expected": (
                    starting_count + random.randint(1, 3) if mode == "random" else None
                ),
            }

            if mode == "prime":
                channel_config["prime_numbers"] = (
                    []
                )  # Optional: Track prime numbers if needed

            self.count_data[guild_id]["channels"][channel_id] = channel_config
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        await ctx.send(
            f"Started a **{mode.capitalize()}** counting match in {channel.mention}!",
            delete_after=10,
        )

    @commands.command(name="end_match", aliases=["em"])
    @staff_or_owner()
    async def end_match(self, ctx, channel: discord.TextChannel):
        """Ends the counting match in the specified channel and deletes the channel."""
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "No active counting match found in the specified channel.",
                    delete_after=10,
                )
                return

            try:
                await channel.delete()
                self.logger.info(
                    f"Deleted channel '{channel.name}' in guild '{ctx.guild.name}'.",
                )
            except discord.Forbidden:
                self.logger.error(
                    f"Missing permissions to delete channel '{channel.name}' in guild '{ctx.guild.name}'.",
                )
                await ctx.send(
                    "I don't have permission to delete that channel.",
                    delete_after=10,
                )
                return
            except Exception as e:
                self.logger.error(
                    f"Error deleting channel '{channel.name}' in guild '{ctx.guild.name}': {e}",
                )
                await ctx.send(
                    "An error occurred while deleting the channel.",
                    delete_after=10,
                )
                return

            # Remove channel data
            del self.count_data[guild_id]["channels"][channel_id]
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        await ctx.send(
            f"Ended and deleted the counting match in {channel.name}.",
            delete_after=10,
        )

    @commands.command(name="reset_count", aliases=["rc"])
    @staff_or_owner()
    async def reset_count(self, ctx, channel: discord.TextChannel = None):
        """Resets the count to the starting value in the specified channel or current channel if none specified."""
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "Counting game is not set up for this channel.",
                    delete_after=10,
                )
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            mode = channel_data.get("mode", "normal")
            start = (
                0
                if mode
                in [
                    "normal",
                    "random",
                    "skip",
                    "multiples",
                    "prime",
                    "fibonacci",
                    "squares",
                    "cubes",
                    "factorials",
                    "custom",
                ]
                else 1000
            )
            channel_data["current_count"] = start
            channel_data["sequence_index"] = 0
            channel_data["last_user"] = None
            channel_data["leaderboard"] = {}
            channel_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
            if mode == "random":
                rand_range = channel_data.get("random_range", [1, 3])
                channel_data["next_expected"] = start + random.randint(*rand_range)
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        await ctx.send(
            f"The count has been reset in {channel.mention}.",
            delete_after=10,
        )

    @commands.command(name="toggle_turns", aliases=["tt"])
    @staff_or_owner()
    async def toggle_turns(self, ctx, channel: discord.TextChannel = None):
        """Toggles the 'taking turns' mode on or off in the specified channel or current channel."""
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "Counting game is not set up for this channel.",
                    delete_after=10,
                )
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            channel_data["taking_turns"] = not channel_data.get("taking_turns", False)
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

            status = "enabled" if channel_data["taking_turns"] else "disabled"
        await ctx.send(
            f"'Taking turns' mode has been {status} in {channel.mention}.",
            delete_after=10,
        )

    @commands.command(name="count_info", aliases=["ci"])
    async def count_info(self, ctx, channel: discord.TextChannel = None):
        """Displays the current count and whether taking turns mode is enabled or disabled in the specified channel or current channel."""
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "Counting game is not set up for this channel.",
                    delete_after=10,
                )
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            current_count = channel_data.get("current_count", 0)
            taking_turns = channel_data.get("taking_turns", False)
            mode = channel_data.get("mode", "normal").capitalize()
            step = channel_data.get("step", 1)
            reset_on_wrong_count = channel_data.get("reset_on_wrong_count", False)

        embed = discord.Embed(title="Counting Info", color=discord.Color.blue())
        embed.add_field(name="Mode", value=mode, inline=False)
        embed.add_field(name="Current Count", value=str(current_count), inline=False)
        embed.add_field(name="Taking Turns Mode", value=str(taking_turns), inline=False)
        embed.add_field(
            name="Reset on Wrong Count",
            value=str(reset_on_wrong_count),
            inline=False,
        )
        embed.add_field(name="Step", value=str(step), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="count_rules", aliases=["cr"])
    async def count_rules(self, ctx):
        """Displays the counting game rules."""
        embed = discord.Embed(title="Counting Game Rules", color=discord.Color.green())
        embed.add_field(
            name="1. Follow the Sequence",
            value="Provide the correct next number based on the game mode.",
            inline=False,
        )
        embed.add_field(
            name="2. Taking Turns",
            value="If enabled, users must take turns before counting again.",
            inline=False,
        )
        embed.add_field(
            name="3. Mode-Specific Rules",
            value="Each counting mode has unique rules (e.g., Fibonacci sequence, squares).",
            inline=False,
        )
        embed.add_field(
            name="4. Respect the Channel",
            value="Use only the designated counting channel for the game.",
            inline=False,
        )
        embed.add_field(
            name="5. Have Fun!",
            value="Enjoy the game and encourage others to participate.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="set_skip_numbers", aliases=["ssn"])
    @staff_or_owner()
    async def set_skip_numbers(
        self,
        ctx,
        channel: discord.TextChannel = None,
        *,
        numbers: str = "",
    ):
        """Sets the skip numbers for the 'skip' mode in the specified or current channel.
        Usage: !set_skip_numbers [channel] <numbers>
        Example: !set_skip_numbers #counting 5,10,15
        """
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "Counting game is not set up for this channel.",
                    delete_after=10,
                )
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            if channel_data.get("mode") != "skip":
                await ctx.send(
                    "Skip numbers can only be set for 'skip' mode.",
                    delete_after=10,
                )
                return

            try:
                skip_numbers = [int(num.strip()) for num in numbers.split(",")]
                channel_data["skip_numbers"] = skip_numbers
                tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))
                await ctx.send(
                    f"Skip numbers updated to: {skip_numbers}",
                    delete_after=10,
                )
            except ValueError:
                await ctx.send(
                    "Invalid input. Please provide a comma-separated list of integers.",
                    delete_after=10,
                )

    @commands.command(name="toggle_reset_on_wrong_count", aliases=["trwc"])
    @staff_or_owner()
    async def toggle_reset_on_wrong_count(
        self,
        ctx,
        channel: discord.TextChannel = None,
    ):
        """Toggles the 'reset on wrong count' feature on or off in the specified channel or current channel.
        Usage: !toggle_reset_on_wrong_count [channel]
        """
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)

        async with self.lock:
            if guild_id not in self.count_data or channel_id not in self.count_data[
                guild_id
            ].get("channels", {}):
                await ctx.send(
                    "Counting game is not set up for this channel.",
                    delete_after=10,
                )
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            channel_data["reset_on_wrong_count"] = not channel_data.get(
                "reset_on_wrong_count",
                False,
            )
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

            status = "enabled" if channel_data["reset_on_wrong_count"] else "disabled"
        await ctx.send(
            f"'Reset on wrong count' has been {status} in {channel.mention}.",
            delete_after=10,
        )

    # --------------------------------------------
    # Event Listeners
    # --------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener to handle counting in active channels."""
        if message.author.bot:
            return  # Ignore bot messages

        if not isinstance(message.channel, discord.TextChannel):
            return  # Ignore messages from DMs or unsupported channel types

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)

        async with self.lock:
            if guild_id not in self.count_data:
                return
            if "channels" not in self.count_data[guild_id]:
                return
            if channel_id not in self.count_data[guild_id]["channels"]:
                return

            channel_data = self.count_data[guild_id]["channels"][channel_id]
            mode = channel_data.get("mode", "normal")
            taking_turns = channel_data.get("taking_turns", False)
            current_count = channel_data.get("current_count", 0)
            last_user = channel_data.get("last_user", None)
            multiple = channel_data.get("multiple", None)
            reset_on_wrong_count = channel_data.get("reset_on_wrong_count", False)

            # Parse the message to extract the count
            parsed_count = self.parse_message(message.content)
            if parsed_count is None:
                # The message isn't recognized as a valid number or expression
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass  # Missing permissions to delete messages
                # Optionally notify the user
                await message.channel.send(
                    f"{message.author.mention}, please send a valid number or mathematical expression.",
                    delete_after=5,
                )
                return

            expected_count = self.calculate_expected_count(
                channel_data,
                current_count,
                mode,
            )

            # Validate the parsed count against expected count
            if parsed_count != expected_count:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass  # Missing permissions to delete messages

                if reset_on_wrong_count:
                    # Reset the count to the starting value
                    if mode in [
                        "normal",
                        "random",
                        "skip",
                        "multiples",
                        "prime",
                        "fibonacci",
                        "squares",
                        "cubes",
                        "factorials",
                        "custom",
                    ]:
                        channel_data["current_count"] = 0
                    else:  # For 'reverse' mode
                        channel_data["current_count"] = 1000
                    channel_data["sequence_index"] = 0
                    channel_data["last_user"] = None
                    channel_data["leaderboard"] = {}
                    channel_data["last_count_time"] = datetime.now(
                        tz=timezone.utc,
                    ).timestamp()
                    tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

                    await message.channel.send(
                        f"{message.author.mention}, incorrect count! The count has been reset.",
                        delete_after=5,
                    )
                else:
                    await message.channel.send(
                        f"{message.author.mention}, incorrect count! The next number should be {expected_count}.",
                        delete_after=5,
                    )
                return

            if taking_turns and user_id == last_user:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass  # Missing permissions to delete messages
                await message.channel.send(
                    f"{message.author.mention}, you cannot count twice in a row!",
                    delete_after=5,
                )
                return

            # Additional mode-specific validations
            if mode == "multiples" and multiple:
                if parsed_count % multiple != 0:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        pass
                    await message.channel.send(
                        f"{message.author.mention}, please count in multiples of {multiple}.",
                        delete_after=5,
                    )
                    return

            if mode == "prime":
                if not self.is_prime(parsed_count):
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        pass
                    await message.channel.send(
                        f"{message.author.mention}, please count prime numbers only.",
                        delete_after=5,
                    )
                    return

            # Update count
            channel_data["current_count"] = parsed_count
            channel_data["last_user"] = user_id
            channel_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
            # Roll next expected value for random mode
            if mode == "random":
                rand_range = channel_data.get("random_range", [1, 3])
                channel_data["next_expected"] = parsed_count + random.randint(
                    *rand_range,
                )
            # Update sequence index for custom sequences
            if mode in ["fibonacci", "squares", "cubes", "factorials", "custom"]:
                channel_data["sequence_index"] += 1
            # Update leaderboard
            leaderboard = channel_data.get("leaderboard", {})
            leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
            channel_data["leaderboard"] = leaderboard
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        # Add reaction to acknowledge correct count
        try:
            await message.add_reaction("✅")
        except discord.Forbidden:
            pass  # Missing permissions to add reactions

    # --------------------------------------------
    # Helper Methods
    # --------------------------------------------

    def parse_message(self, content: str) -> int:
        """Parses the message content to extract the numerical count.
        Returns the integer count if valid, else None.
        """
        content = content.strip().lower()

        # Replace phrases with their numeric equivalents
        for phrase, num in self.phrase_number_mapping.items():
            pattern = r"\b" + re.escape(phrase) + r"\b"
            content = re.sub(pattern, str(num), content)

        # Replace number emotes with their numeric equivalents
        for emote, num_str in self.emoji_number_mapping.items():
            content = content.replace(emote, num_str)

        # **Modify Hyphen Replacement:**
        # Replace hyphens within words (e.g., "twenty-one") with spaces
        # but keep hyphens used as operators intact.
        # This regex replaces hyphens only between letters.
        content = re.sub(r"(?<=[a-zA-Z])-(?=[a-zA-Z])", " ", content)

        # Split concatenated number words
        content = self.split_concatenated_numbers(content)

        # Define all operator symbols, including '×' and 'x'
        operator_symbols = "+-*/^()=.×x"

        # Tokenize the content into numbers, words, and operators
        tokens = re.findall(r"\d+|[^\W\d_]+|[^\w\s]", content, re.UNICODE)

        processed_tokens = []
        number_word_tokens: list[str] = []
        prev_token_type = None

        for token in tokens:
            lower_token = token.lower()

            if lower_token in self.operator_mapping or token in operator_symbols:
                # Process any collected number word tokens
                if number_word_tokens:
                    number_word_str = " ".join(number_word_tokens)
                    number = self.parse_number_word(number_word_str)
                    if number is None:
                        return None
                    processed_tokens.append(str(number))
                    number_word_tokens = []
                    prev_token_type = "number"
                # Append the operator
                if lower_token in self.operator_mapping:
                    processed_tokens.append(self.operator_mapping[lower_token])
                else:
                    processed_tokens.append(token)
                prev_token_type = "operator"
            elif lower_token.isdigit() or token.isdigit():
                # Process any collected number word tokens
                if number_word_tokens:
                    number_word_str = " ".join(number_word_tokens)
                    number = self.parse_number_word(number_word_str)
                    if number is None:
                        return None
                    processed_tokens.append(str(number))
                    number_word_tokens = []
                if prev_token_type == "number":
                    # Insert '+' between adjacent numbers
                    processed_tokens.append("+")
                processed_tokens.append(token)
                prev_token_type = "number"
            elif lower_token in self.number_words_set:
                number_word_tokens.append(lower_token)
                prev_token_type = "number_word"
            else:
                # Try fuzzy matching for misspellings
                close_matches = difflib.get_close_matches(
                    lower_token,
                    self.number_words_set,
                    n=1,
                    cutoff=0.8,
                )
                if close_matches:
                    number_word_tokens.append(close_matches[0])
                    prev_token_type = "number_word"
                else:
                    # Try to parse as a Roman numeral
                    roman_value = self.roman_to_int(lower_token.upper())
                    if roman_value is not None:
                        if prev_token_type == "number":
                            # Insert '+' between adjacent numbers
                            processed_tokens.append("+")
                        processed_tokens.append(str(roman_value))
                        prev_token_type = "number"
                    else:
                        # Unknown token, return None
                        return None

        # Process any remaining number word tokens
        if number_word_tokens:
            number_word_str = " ".join(number_word_tokens)
            number = self.parse_number_word(number_word_str)
            if number is None:
                return None
            processed_tokens.append(str(number))

        # Join the processed tokens into a single expression
        expr = "".join(processed_tokens)

        # Try to evaluate the expression
        result = self.eval_expr(expr)
        if result is not None:
            return int(result)
        return None

    def parse_number_word(self, text: str) -> int:
        """Parses a number word or ordinal into an integer."""
        lower = text.lower()
        if lower in self.ordinal_mapping:
            return self.ordinal_mapping[lower]
        return _word_to_num(lower)

    def split_concatenated_numbers(self, text: str) -> str:
        """Splits concatenated number words in the text by inserting spaces between them."""
        number_words = self.number_words_set

        # Lowercase the text for consistent matching
        text_lower = text.lower()

        # Initialize variables
        result = ""
        i = 0

        while i < len(text_lower):
            match_found = False
            for j in range(len(text_lower), i, -1):
                substr = text_lower[i:j]
                if substr in number_words:
                    # If we find a number word, add it to the result with a space
                    result += substr + " "
                    i = j - 1  # Adjust index to the end of the matched word
                    match_found = True
                    break
            if not match_found:
                # If no number word is found, add the character as is
                result += text_lower[i]
            i += 1

        return result

    def roman_to_int(self, s: str) -> int:
        """Converts a Roman numeral to an integer."""
        roman_map = self.roman_numeral_mapping
        i = 0
        num = 0
        while i < len(s):
            if i + 1 < len(s) and s[i : i + 2] in roman_map:
                num += roman_map[s[i : i + 2]]
                i += 2
            elif s[i] in roman_map:
                num += roman_map[s[i]]
                i += 1
            else:
                return None
        return num

    def eval_expr(self, expr):
        """Safely evaluate an arithmetic expression and return the result.
        Supports basic arithmetic operations.
        """
        try:
            expr = expr.replace(" ", "")
            # Remove any invalid characters
            if not re.match(r"^[0-9+\-*/^().=]+$", expr):
                return None
            # Limit the length of the expression to prevent abuse
            if len(expr) > 50:
                return None
            # Handle equations with '='
            if "=" in expr:
                left_expr, right_expr = expr.split("=", 1)
                left_val = self.safe_eval(left_expr)
                right_val = self.safe_eval(right_expr)
                if left_val == right_val:
                    return right_val  # Return the numeric result
                return None  # Invalid equation
            return self.safe_eval(expr)
        except Exception as e:
            self.logger.error(f"Error evaluating expression '{expr}': {e}")
            return None

    def safe_eval(self, expr):
        """Safely evaluate an arithmetic expression without '=' and return the result."""
        try:
            node = ast.parse(expr, mode="eval").body
            return self.eval_(node)
        except Exception as e:
            self.logger.error(f"Error in safe_eval with expression '{expr}': {e}")
            return None

    def eval_(self, node):
        if isinstance(node, ast.Constant):  # For Python 3.8 and above
            return node.value
        if isinstance(node, ast.Num):  # For Python versions before 3.8
            return node.n
        if isinstance(node, ast.BinOp):  # <left> <operator> <right>
            left = self.eval_(node.left)
            right = self.eval_(node.right)
            operator = self.operators.get(type(node.op))
            if operator is None:
                raise TypeError(f"Unsupported operator: {node.op}")
            return operator(left, right)
        if isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            operand = self.eval_(node.operand)
            operator = self.operators.get(type(node.op))
            if operator is None:
                raise TypeError(f"Unsupported operator: {node.op}")
            return operator(operand)
        raise TypeError(f"Unsupported expression: {node}")

    def calculate_expected_count(
        self,
        channel_data: dict,
        current_count: int,
        mode: str,
    ) -> int:
        """Calculates the expected next count based on the current count and mode."""
        if mode == "reverse":
            expected = current_count - channel_data.get("step", 1)
        elif mode == "skip":
            expected = current_count + channel_data.get("step", 1)
            while expected in channel_data.get("skip_numbers", []):
                expected += channel_data.get("step", 1)
        elif mode == "random":
            # Use the pre-rolled value so it doesn't change between calls
            expected = channel_data.get("next_expected", current_count + 1)
        elif mode == "fibonacci":
            a, b = 0, 1
            for _ in range(channel_data.get("sequence_index", 0) + 1):
                a, b = b, a + b
            expected = a
        elif mode == "squares":
            index = channel_data.get("sequence_index", 0) + 1
            expected = index**2
        elif mode == "cubes":
            index = channel_data.get("sequence_index", 0) + 1
            expected = index**3
        elif mode == "factorials":
            index = channel_data.get("sequence_index", 0) + 1
            expected = math.factorial(index)
        elif mode == "custom":
            sequence = channel_data.get("custom_sequence", [])
            index = channel_data.get("sequence_index", 0)
            expected = sequence[index] if index < len(sequence) else None
        else:  # normal, multiples, prime
            expected = current_count + channel_data.get("step", 1)
        return expected

    def is_prime(self, number: int) -> bool:
        """Check if a number is prime."""
        if number < 2:
            return False
        if number == 2:
            return True
        if number % 2 == 0:
            return False
        return all(number % i != 0 for i in range(3, int(number**0.5) + 1, 2))

    # --------------------------------------------
    # Cog Unload
    # --------------------------------------------

    def cog_unload(self):
        """Handles cleanup when the cog is unloaded."""
        pass


class _CountingHubView(BaseView):
    """Admin hub for managing the counting game in the current channel."""

    def __init__(self, ctx: commands.Context, cog: CountingCog):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.cog = cog

    def _channel_data(self) -> dict | None:
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        return self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)

    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🔢 Counting Manager", color=discord.Color.blue())
        ch_data = self._channel_data()
        if ch_data:
            mode = ch_data.get("mode", "normal").capitalize()
            current = ch_data.get("current_count", 0)
            turns = ch_data.get("taking_turns", False)
            reset_wrong = ch_data.get("reset_on_wrong_count", False)
            embed.description = f"Managing {self.ctx.channel.mention}"  # type: ignore[union-attr]
            embed.add_field(name="Mode", value=mode, inline=True)
            embed.add_field(name="Current Count", value=str(current), inline=True)
            embed.add_field(
                name="Taking Turns",
                value="✅" if turns else "❌",
                inline=True,
            )
            embed.add_field(
                name="Reset on Wrong",
                value="✅" if reset_wrong else "❌",
                inline=True,
            )
        else:
            gid = str(self.ctx.guild.id)
            active_ids = list(
                self.cog.count_data.get(gid, {}).get("channels", {}).keys(),
            )
            active_mentions = []
            for cid in active_ids:
                ch = self.ctx.guild.get_channel(int(cid))
                if ch:
                    active_mentions.append(ch.mention)
            embed.description = (
                f"{self.ctx.channel.mention} is not an active counting channel.\n\n"  # type: ignore[union-attr]
                "Start a new match with `!start_match <mode>`."
            )
            if active_mentions:
                embed.add_field(
                    name="Active Counting Channels",
                    value="\n".join(active_mentions),
                    inline=False,
                )
        embed.set_footer(text="Buttons below operate on the current channel.")
        return embed

    @discord.ui.button(
        label="🔄 Toggle Turns",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_toggle_turns(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            ch_data["taking_turns"] = not ch_data.get("taking_turns", False)
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(
        label="♻️ Toggle Reset",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_toggle_reset(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            ch_data["reset_on_wrong_count"] = not ch_data.get(
                "reset_on_wrong_count",
                False,
            )
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(label="🔁 Reset Count", style=discord.ButtonStyle.danger, row=0)
    async def btn_reset_count(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        gid = str(self.ctx.guild.id)
        cid = str(self.ctx.channel.id)
        async with self.cog.lock:
            ch_data = self.cog.count_data.get(gid, {}).get("channels", {}).get(cid)
            if not ch_data:
                await interaction.response.send_message(
                    "This channel is not an active counting channel.",
                    ephemeral=True,
                )
                return
            mode = ch_data.get("mode", "normal")
            start = 1000 if mode == "reverse" else 0
            ch_data["current_count"] = start
            ch_data["sequence_index"] = 0
            ch_data["last_user"] = None
            ch_data["leaderboard"] = {}
            ch_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
            if mode == "random":
                rand_range = ch_data.get("random_range", [1, 3])
                ch_data["next_expected"] = start + random.randint(*rand_range)
            tasks.spawn(f"counting:save:{gid}", self.cog._save_guild(gid))
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )


async def setup(bot):
    await bot.add_cog(CountingCog(bot))
    logger.info("CountingCog has been successfully loaded and added to the bot.")
