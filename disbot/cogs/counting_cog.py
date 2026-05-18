"""Counting subsystem — Discord plumbing only.

Parsing, game-mode math, and the admin hub view live in:

    cogs/counting/parsing.py     — message → integer
    cogs/counting/game_logic.py  — calculate_expected_count, is_prime
    cogs/counting/_constants.py  — number-word sets + operator tables
    cogs/counting/handler.py     — V/M/A compute_decision + apply_decision (S2.1)
    views/counting/hub_panel.py  — _CountingHubView

This file hosts only commands, the on_message listener glue, the cog
lifecycle, and the staff/owner permission helpers.  The pre-S4.1
back-compat re-export of ``_word_to_num`` was dropped in S5.2 (no
consumers); ``_CountingHubView`` is still imported here because the
listener-glue commands instantiate it directly.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone

import discord
from discord.ext import commands

from cogs.counting import handler
from cogs.counting._stage import COUNTING_STAGE_NAME, CountingStage
from core.runtime import resources, scope_locks, tasks
from core.runtime.interaction_helpers import help_ctx_shim
from utils import db
from views.base import send_panel

# _CountingHubView is instantiated below by the !countingmenu command
# and the help-menu hook.  It also stays importable from this module
# (``from cogs.counting_cog import _CountingHubView``) without an
# explicit __all__ entry — the import name is preserved as a side
# effect, which is fine.
from views.counting import _CountingHubView

logger = logging.getLogger("bot.cogs.counting")


def _scope_id_for_channel(channel_id: str) -> str:
    """Canonical scope_locks scope id for a counting channel."""
    return f"counting:channel:{channel_id}"


class CountingCog(commands.Cog):
    """A cog for managing various counting games with multiple modes."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.logger = logger
        self.lock = asyncio.Lock()
        self.count_data: dict = {}

    async def cog_load(self):
        """Schedule DB state load, register scope_locks teardown hook (S2.1),
        and register the message-pipeline CountingStage (§3.2).
        """
        from core.runtime import message_pipeline

        tasks.spawn("counting:load_when_ready", self._load_when_ready())
        scope_locks.register_guild_teardown_hook(self._drop_scope_locks_for_guild)
        message_pipeline.register(CountingStage(self))

    def _drop_scope_locks_for_guild(self, guild_id: int) -> int:
        """guild_lifecycle teardown hook — drop counting scope_locks for the guild.

        Phase S2.1 / F-2: scope_locks does not know which scope_ids belong
        to which guild; each cog registers its own translation hook.
        We iterate the per-guild channel set in ``self.count_data`` to
        derive the scope_ids and call ``scope_locks.forget`` for each.
        """
        guild_str = str(guild_id)
        channel_dict = self.count_data.get(guild_str, {}).get("channels", {})
        dropped = 0
        for channel_id in list(channel_dict.keys()):
            scope_locks.forget(_scope_id_for_channel(channel_id))
            dropped += 1
        return dropped

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
        await send_panel(ctx, embed=embed, view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the counting hub panel)."""
        view = _CountingHubView(help_ctx_shim(interaction), self)
        embed = await view.build_embed()
        return embed, view

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
            existing_channel = resources.resolve_channel(guild, name=channel_name)
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

    async def _process_counting_message(self, message) -> bool:
        """Validate counts in active channels — V/M/A coordinator (§3.2).

        Called by :class:`CountingStage` from the message pipeline.
        Returns ``True`` if the message was deleted (caller short-circuits
        the pipeline), ``False`` otherwise.

        The pipeline pre-filters bot authors so we don't re-check.
        """
        if not isinstance(message.channel, discord.TextChannel):
            return False

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)

        # Existence check — no lock needed.  If an admin removes the
        # channel mid-flight the mutation is harmless: channel_data is
        # mutated in place but the next save_guild serialises whatever
        # the parent dict holds at that moment.
        channel_data = (
            self.count_data.get(guild_id, {}).get("channels", {}).get(channel_id)
        )
        if channel_data is None:
            return False

        # ---- VALIDATE + MUTATE under per-channel scope_lock ----
        scope_id = _scope_id_for_channel(channel_id)
        async with scope_locks.lock_for(scope_id):
            decision = handler.compute_decision(
                message=message,
                channel_data=channel_data,
                user_id=user_id,
            )
            if decision.state_mutated:
                tasks.spawn(
                    f"counting:save:{guild_id}",
                    self._save_guild(guild_id),
                )

        # ---- APPLY OUTSIDE the lock (Discord I/O) ----
        await handler.apply_decision(decision, message)
        return decision.delete_message

    # --------------------------------------------
    # Cog Unload
    # --------------------------------------------

    def cog_unload(self):
        """Cancel in-flight save / load tasks; unregister the pipeline stage."""
        from core.runtime import message_pipeline

        tasks.cancel_by_prefix("counting:")
        message_pipeline.unregister(COUNTING_STAGE_NAME)


async def setup(bot):
    await bot.add_cog(CountingCog(bot))
