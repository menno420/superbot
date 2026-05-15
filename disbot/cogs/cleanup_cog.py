from __future__ import annotations

import asyncio
import logging
import re

import config as _config
import discord
from discord.ext import commands
from utils import db
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView


class Cleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        # Per-guild caches: guild_id → (words, patterns)
        self._word_cache: dict[int, list[str]] = {}
        self._pattern_cache: dict[int, list] = {}

        self.command_prefixes = ["?", "!"]
        self.command_pattern = re.compile(
            rf'^\s*({"|".join(map(re.escape, self.command_prefixes))})\S+',
            re.IGNORECASE,
        )

        self.whitelisted_channels = _config.CLEANUP_WHITELIST_CHANNELS

    async def _load_guild(self, guild_id: int) -> None:
        words = await db.get_prohibited_words(guild_id)
        self._word_cache[guild_id] = words
        self._pattern_cache[guild_id] = [
            re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in words
        ]

    async def _get_patterns(self, guild_id: int) -> list:
        if guild_id not in self._pattern_cache:
            await self._load_guild(guild_id)
        return self._pattern_cache[guild_id]

    async def remove_unwanted_message(self, message):
        """Deletes the message if it is a command in a non-whitelisted channel or contains prohibited content."""
        if message.author.bot:
            return False

        if self.command_pattern.match(message.content):
            if message.channel.id not in self.whitelisted_channels:
                try:
                    await message.delete()
                    self.logger.info(
                        f"Deleted command message from {message.author} in non-whitelisted channel: {message.content}"
                    )
                except discord.DiscordException as e:
                    self.logger.error(f"Failed to delete command message: {e}")
                return True
            return False

        guild_id = message.guild.id if message.guild else 0
        for pattern in await self._get_patterns(guild_id):
            if pattern.search(message.content):
                try:
                    await message.delete()
                    warning_msg = await message.channel.send(
                        f"A message from {message.author.mention} was deleted because it contained prohibited content."
                    )
                    self.logger.info(
                        f"Deleted message from {message.author}: {message.content}"
                    )
                    await warning_msg.delete(delay=10)
                except discord.DiscordException as e:
                    self.logger.error(
                        f"Failed to delete message from {message.author}: {e}"
                    )
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.remove_unwanted_message(message)

    @commands.command(name="cleanuphistory")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def cleanup_history(self, ctx, limit: int = 100, *, keyword: str = None):
        """Cleans up messages containing prohibited content or disallowed commands from the channel history."""
        if limit <= 0:
            await ctx.send(
                "Please provide a positive number of messages to scan.", delete_after=5
            )
            return

        confirmation_msg = await ctx.send(
            f"Are you sure you want to clean up the last {limit} messages"
            + (f" filtering by `{keyword}`" if keyword else "")
            + "? React with ✅ to confirm or ❌ to cancel."
        )
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == confirmation_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=check
            )
            if str(reaction.emoji) == "✅":
                await ctx.send(
                    f"Starting cleanup for the last {limit} messages"
                    + (f" filtering by `{keyword}`" if keyword else ""),
                    delete_after=5,
                )
                async for message in ctx.channel.history(limit=limit):
                    if message.author.bot:
                        continue
                    if keyword and keyword.lower() not in message.content.lower():
                        continue
                    await self.remove_unwanted_message(message)
                await ctx.send("Cleanup completed.", delete_after=5)
                self.logger.info(
                    f"Cleanup completed for the last {limit} messages in {ctx.channel.name}"
                )
            else:
                await ctx.send("Cleanup canceled.", delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send("Cleanup confirmation timed out.", delete_after=5)
        finally:
            await ctx.message.delete()
            await confirmation_msg.delete()

    @commands.group(name="word", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def word_cmd(self, ctx):
        """Manage prohibited words. Subcommands: add, remove, list."""
        guild_id = ctx.guild.id
        if guild_id not in self._word_cache:
            await self._load_guild(guild_id)
        words = self._word_cache[guild_id]
        if words:
            word_list = ", ".join(f"`{w}`" for w in sorted(words))
            await ctx.send(f"Prohibited words: {word_list}", delete_after=15)
        else:
            await ctx.send("No prohibited words are currently set.", delete_after=10)

    @word_cmd.command(name="add")
    @commands.has_permissions(administrator=True)
    async def word_add(self, ctx, *, word: str):
        """Adds a word to the prohibited words list."""
        word = word.lower()
        added = await db.add_prohibited_word(ctx.guild.id, word)
        if added:
            await self._load_guild(ctx.guild.id)
            await ctx.send(
                f"Added '{word}' to the prohibited words list.", delete_after=5
            )
            self.logger.info(f"Added prohibited word: {word}")
        else:
            await ctx.send(
                f"The word '{word}' is already in the prohibited list.", delete_after=5
            )

    @word_cmd.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def word_remove(self, ctx, *, word: str):
        """Removes a word from the prohibited words list."""
        word = word.lower()
        removed = await db.remove_prohibited_word(ctx.guild.id, word)
        if removed:
            await self._load_guild(ctx.guild.id)
            await ctx.send(
                f"Removed '{word}' from the prohibited words list.", delete_after=5
            )
            self.logger.info(f"Removed prohibited word: {word}")
        else:
            await ctx.send(
                f"The word '{word}' is not in the prohibited list.", delete_after=5
            )

    @word_cmd.command(name="list")
    @commands.has_permissions(administrator=True)
    async def word_list(self, ctx):
        """Shows all prohibited words."""
        guild_id = ctx.guild.id
        if guild_id not in self._word_cache:
            await self._load_guild(guild_id)
        words = self._word_cache[guild_id]
        if words:
            word_list = ", ".join(f"`{w}`" for w in sorted(words))
            await ctx.send(f"Prohibited words: {word_list}", delete_after=15)
        else:
            await ctx.send("No prohibited words are currently set.", delete_after=10)

    @commands.command(name="wordmenu")
    @commands.has_permissions(administrator=True)
    async def word_menu(self, ctx):
        """Open the interactive prohibited words management panel."""
        if ctx.guild.id not in self._word_cache:
            await self._load_guild(ctx.guild.id)
        view = _WordMenuView(ctx, self)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


class _AddWordModal(discord.ui.Modal, title="Add Prohibited Word"):  # type: ignore[call-arg]
    word_input = discord.ui.TextInput(label="Word to prohibit", max_length=100)

    def __init__(self, cog: "Cleanup"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        word = self.word_input.value.lower().strip()
        added = await db.add_prohibited_word(interaction.guild_id, word)
        if added:
            await self.cog._load_guild(interaction.guild_id)
            await interaction.response.send_message(
                f"✅ Added `{word}` to the prohibited list.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ `{word}` is already in the prohibited list.", ephemeral=True
            )


class _RemoveWordModal(discord.ui.Modal, title="Remove Prohibited Word"):  # type: ignore[call-arg]
    word_input = discord.ui.TextInput(label="Word to remove", max_length=100)

    def __init__(self, cog: "Cleanup"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        word = self.word_input.value.lower().strip()
        removed = await db.remove_prohibited_word(interaction.guild_id, word)
        if removed:
            await self.cog._load_guild(interaction.guild_id)
            await interaction.response.send_message(
                f"✅ Removed `{word}` from the prohibited list.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ `{word}` was not in the prohibited list.", ephemeral=True
            )


class _WordMenuView(BaseView):
    """Interactive prohibited-words management panel."""

    def __init__(self, ctx: commands.Context, cog: "Cleanup"):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        words = self.cog._word_cache.get(self.ctx.guild.id, [])
        embed = discord.Embed(title="🔤 Prohibited Words Manager", color=ADMIN_COLOR)
        if words:
            embed.add_field(
                name="Current Words",
                value=", ".join(f"`{w}`" for w in sorted(words))[:1000],
                inline=False,
            )
        else:
            embed.description = "No prohibited words are currently set."
        embed.set_footer(text="Use buttons below to manage prohibited words.")
        return embed

    @discord.ui.button(label="➕ Add Word", style=discord.ButtonStyle.green, row=0)
    async def btn_add(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_AddWordModal(self.cog))

    @discord.ui.button(label="➖ Remove Word", style=discord.ButtonStyle.danger, row=0)
    async def btn_remove(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_RemoveWordModal(self.cog))

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.cog._load_guild(self.ctx.guild.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(
        label="🔍 Scan History", style=discord.ButtonStyle.blurple, row=1
    )
    async def btn_scan(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_ScanHistoryModal(self.cog))


class _ScanHistoryModal(discord.ui.Modal, title="Scan Channel History"):  # type: ignore[call-arg]
    limit = discord.ui.TextInput(
        label="Messages to scan (1–500)",
        placeholder="100",
        default="100",
        max_length=3,
    )
    keyword = discord.ui.TextInput(
        label="Keyword filter (optional)",
        placeholder="Leave blank to scan all messages",
        required=False,
        max_length=100,
    )

    def __init__(self, cog: "Cleanup"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ You need **Manage Messages** permission to scan history.",
                ephemeral=True,
            )
            return

        try:
            scan_limit = int(self.limit.value.strip())
            if not 1 <= scan_limit <= 500:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Limit must be a number between 1 and 500.", ephemeral=True
            )
            return

        kw = self.keyword.value.strip().lower() if self.keyword.value.strip() else None

        await interaction.response.defer(ephemeral=True)

        scanned = 0
        deleted = 0
        async for message in interaction.channel.history(limit=scan_limit):
            if message.author.bot:
                continue
            if kw and kw not in message.content.lower():
                continue
            scanned += 1
            if await self.cog.remove_unwanted_message(message):
                deleted += 1

        filter_note = f" (filtered by `{kw}`)" if kw else ""
        await interaction.followup.send(
            f"✅ Scanned **{scanned}** messages{filter_note}. Deleted **{deleted}**.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Cleanup(bot))
