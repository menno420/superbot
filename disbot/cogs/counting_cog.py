"""Counting subsystem — Discord plumbing only.

Parsing, game-mode math, and the admin hub view live in:

    cogs/counting/parsing.py     — message → integer
    cogs/counting/game_logic.py  — calculate_expected_count, is_prime
    cogs/counting/_constants.py  — number-word sets + operator tables
    views/counting/hub_panel.py  — _CountingHubView

This file hosts only commands, the on_message listener, the cog
lifecycle, and the staff/owner permission helpers.  Tests that reach
in for ``_word_to_num`` or ``_CountingHubView`` continue to resolve
via the back-compat re-exports at the bottom of this module.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from cogs.counting import game_logic, parsing
from cogs.counting._constants import word_to_num as _word_to_num  # noqa: F401
from core.runtime import tasks
from utils import db

# Re-export the hub view so legacy ``from cogs.counting_cog import
# _CountingHubView`` imports keep resolving.
from views.counting import _CountingHubView  # noqa: F401

logger = logging.getLogger("CountingCog")


class CountingCog(commands.Cog):
    """A cog for managing various counting games with multiple modes."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.lock = asyncio.Lock()
        self.count_data: dict = {}

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
        staff_roles = ["Admin", "Moderator"]
        return any(role.name in staff_roles for role in ctx.author.roles)

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

        Available modes: normal, reverse, skip, random, multiples, prime,
        fibonacci, squares, cubes, factorials, custom.
        For 'multiples' specify the multiple (e.g., 3 for multiples of 3).
        For 'custom' provide a sequence of numbers separated by commas.
        """
        guild = ctx.guild
        guild_id = str(guild.id)
        mode = mode.lower()

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
                "next_expected": (
                    starting_count + random.randint(1, 3) if mode == "random" else None
                ),
            }

            if mode == "prime":
                channel_config["prime_numbers"] = []

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
                    f"Missing permissions to delete channel '{channel.name}'.",
                )
                await ctx.send(
                    "I don't have permission to delete that channel.",
                    delete_after=10,
                )
                return
            except Exception as e:
                self.logger.error(
                    f"Error deleting channel '{channel.name}': {e}",
                )
                await ctx.send(
                    "An error occurred while deleting the channel.",
                    delete_after=10,
                )
                return

            del self.count_data[guild_id]["channels"][channel_id]
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        await ctx.send(
            f"Ended and deleted the counting match in {channel.name}.",
            delete_after=10,
        )

    @commands.command(name="reset_count", aliases=["rc"])
    @staff_or_owner()
    async def reset_count(self, ctx, channel: discord.TextChannel = None):
        """Resets the count to the starting value."""
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
        """Toggles the 'taking turns' mode."""
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
        """Displays the current count and configuration."""
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
        """Sets the skip numbers for 'skip' mode."""
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
        """Toggles the 'reset on wrong count' feature."""
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
        """Validate counts in active channels."""
        if message.author.bot:
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

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

            parsed_count = parsing.parse_message(message.content)
            if parsed_count is None:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                await message.channel.send(
                    f"{message.author.mention}, please send a valid number or mathematical expression.",
                    delete_after=5,
                )
                return

            expected_count = game_logic.calculate_expected_count(
                channel_data,
                current_count,
                mode,
            )

            if parsed_count != expected_count:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass

                if reset_on_wrong_count:
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
                    else:  # reverse mode
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
                    pass
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
                if not game_logic.is_prime(parsed_count):
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        pass
                    await message.channel.send(
                        f"{message.author.mention}, please count prime numbers only.",
                        delete_after=5,
                    )
                    return

            channel_data["current_count"] = parsed_count
            channel_data["last_user"] = user_id
            channel_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
            if mode == "random":
                rand_range = channel_data.get("random_range", [1, 3])
                channel_data["next_expected"] = parsed_count + random.randint(
                    *rand_range,
                )
            if mode in ["fibonacci", "squares", "cubes", "factorials", "custom"]:
                channel_data["sequence_index"] += 1
            leaderboard = channel_data.get("leaderboard", {})
            leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
            channel_data["leaderboard"] = leaderboard
            tasks.spawn(f"counting:save:{guild_id}", self._save_guild(guild_id))

        try:
            await message.add_reaction("✅")
        except discord.Forbidden:
            pass

    # --------------------------------------------
    # Cog Unload
    # --------------------------------------------

    def cog_unload(self):
        """Cancel in-flight save / load tasks so a reload doesn't leak them."""
        tasks.cancel_by_prefix("counting:")


async def setup(bot):
    await bot.add_cog(CountingCog(bot))
