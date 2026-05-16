from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions, has_permissions

from utils import db
from views.base import BaseView

logger = logging.getLogger(__name__)


class ChainCog(commands.Cog):
    """Cog for managing message chains and word limits in specified channels."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="chain", invoke_without_command=True)
    async def chain(self, ctx):
        """Manage message chains and word limits in your server.

        Use subcommands to create, delete, set limits, or list chains.
        """
        await ctx.send(
            "❓ Please specify a subcommand. Use `?chain create`, `?chain delete`, `?chain setlimit`, `?chain removelimit`, or `?chain list`.",
        )

    @chain.command(name="create")  # type: ignore[arg-type]
    @has_permissions(administrator=True)
    async def create_chain(
        self,
        ctx,
        channel: discord.TextChannel | None = None,
        *,
        word: str = None,
    ):
        """Create a chain in a specified channel or the current channel if none is provided.

        Only the specified word will be allowed in that channel. All other messages will be deleted.

        **Usage:** `?chain create [channel] <word>`
        """
        if word is None:
            await ctx.send(
                "❌ Please specify the word to enforce in the chain.\n**Usage:** `?chain create [channel] <word>`",
            )
            return

        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if existing and existing.get("word"):
            await ctx.send(f"❌ A chain is already active in {target_channel.mention}.")
            return

        await db.set_chain_channel(channel_id, ctx.guild.id, word.lower())

        await ctx.send(
            f"✅ Chain created in {target_channel.mention}. Only the word `{word}` is allowed in this channel.",
        )

    @create_chain.error
    async def create_chain_error(self, ctx, error):
        """Handle errors for the create_chain command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in create_chain command: {error}")

    @chain.command(name="delete")  # type: ignore[arg-type]
    @has_permissions(administrator=True)
    async def delete_chain(self, ctx, channel: discord.TextChannel = None):
        """Delete a chain from a specified channel or the current channel if none is provided.

        **Usage:** `?chain delete [channel]`
        """
        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if not existing:
            await ctx.send(f"❌ No active chain found in {target_channel.mention}.")
            return

        await db.delete_chain_channel(channel_id)

        await ctx.send(f"✅ Chain deleted from {target_channel.mention}.")

    @delete_chain.error
    async def delete_chain_error(self, ctx, error):
        """Handle errors for the delete_chain command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in delete_chain command: {error}")

    @chain.command(name="setlimit")  # type: ignore[arg-type]
    @has_permissions(administrator=True)
    async def set_limit(
        self,
        ctx,
        channel: discord.TextChannel = None,
        limit: int = None,
    ):
        """Set a word limit in a specified channel or the current channel if none is provided.

        **Usage:** `?chain setlimit [channel] <number>`
        """
        if limit is None or limit <= 0:
            await ctx.send(
                "❌ Please specify a valid word limit greater than 0.\n**Usage:** `?chain setlimit [channel] <number>`",
            )
            return

        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if not existing:
            await ctx.send(
                f"❌ No active chain found in {target_channel.mention}. Create one first with `?chain create`.",
            )
            return

        await db.set_chain_limit(channel_id, limit)

        await ctx.send(
            f"✅ Word limit of {limit} has been set in {target_channel.mention}.",
        )

    @set_limit.error
    async def set_limit_error(self, ctx, error):
        """Handle errors for the set_limit command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid input. Please mention a valid channel and specify a numerical limit.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in set_limit command: {error}")

    @chain.command(name="removelimit")  # type: ignore[arg-type]
    @has_permissions(administrator=True)
    async def remove_limit(self, ctx, channel: discord.TextChannel = None):
        """Remove the word limit from a specified channel or the current channel if none is provided.

        **Usage:** `?chain removelimit [channel]`
        """
        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if existing and existing.get("word_limit"):
            await db.set_chain_limit(channel_id, 0)
            await ctx.send(
                f"✅ Word limit has been removed from {target_channel.mention}.",
            )
        else:
            await ctx.send(f"ℹ️ No word limit is set in {target_channel.mention}.")

    @remove_limit.error
    async def remove_limit_error(self, ctx, error):
        """Handle errors for the remove_limit command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in remove_limit command: {error}")

    @commands.command(name="chainmenu")
    @has_permissions(administrator=True)
    async def chain_menu(self, ctx):
        """Open the interactive chain management panel."""
        view = _ChainMenuView(ctx, self)
        embed = await view.build_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @chain.command(name="list")  # type: ignore[arg-type]
    async def list_chains(self, ctx):
        """List all active chains and word limits in the server.

        **Usage:** `?chain list`
        """
        channels = await db.get_all_chain_channels(ctx.guild.id)

        if not channels:
            await ctx.send(
                "ℹ️ There are no active chains or word limits in this server.",
            )
            return

        embed = discord.Embed(
            title="Active Chains and Word Limits",
            color=discord.Color.green(),
        )

        for entry in channels:
            channel = self.bot.get_channel(entry["channel_id"])
            word = entry.get("word")
            limit = entry.get("word_limit")
            description = ""
            if word:
                description += f"Allowed Word: `{word}`\n"
            if limit:
                description += f"Word Limit: `{limit}` words\n"
            if not description:
                description = "No restrictions set."
            if channel:
                embed.add_field(name=channel.name, value=description, inline=False)
            else:
                embed.add_field(
                    name="Unknown Channel",
                    value=f"Channel ID: `{entry['channel_id']}`\n{description}",
                    inline=False,
                )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener to enforce chain rules and word limits in specified channels."""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the message is invoking a command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Don't process command messages

        channel_data = await db.get_chain_channel(message.channel.id)
        if not channel_data:
            return  # No chain or limit set for this channel

        allowed_word = channel_data.get("word")
        word_limit = channel_data.get("word_limit")

        # Initialize a flag to determine if message should be deleted
        delete_message = False

        # Check for allowed word
        if allowed_word:
            if message.content.strip().lower() != allowed_word.lower():
                delete_message = True

        # Check for word limit
        if word_limit:
            word_count = len(message.content.strip().split())
            if word_count > word_limit:
                delete_message = True

        if not delete_message:
            await db.increment_chain_count(message.channel.id)
            return  # Message is allowed

        # Delete the message and optionally warn the user
        try:
            await message.delete()
            warning_message = f"{message.author.mention}, your message was deleted."
            if allowed_word and word_limit:
                warning_message += f" Only the word `{allowed_word}` is allowed, and messages must be at most {word_limit} words."
            elif allowed_word:
                warning_message += (
                    f" Only the word `{allowed_word}` is allowed in this channel."
                )
            elif word_limit:
                warning_message += f" Messages must be at most {word_limit} words."
            warning = await message.channel.send(warning_message)
            # Delete the warning after 5 seconds
            await asyncio.sleep(5)
            await warning.delete()
        except discord.Forbidden:
            logger.warning(
                f"Missing permissions to delete messages in {message.channel}.",
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to delete message in {message.channel}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Event handler when the cog is ready."""
        logger.info(f"{self.__class__.__name__} is ready and operational.")


def _resolve_channel(
    interaction: discord.Interaction,
    raw: str,
) -> discord.TextChannel | None:
    raw = raw.strip()
    if not raw:
        return interaction.channel  # type: ignore[return-value]
    stripped = raw.strip("<#>")
    try:
        return interaction.guild.get_channel(int(stripped))  # type: ignore[return-value]
    except ValueError:
        return discord.utils.get(interaction.guild.text_channels, name=raw)


class _CreateChainModal(discord.ui.Modal, title="Create Chain"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )
    word_input = discord.ui.TextInput(label="Allowed word", max_length=100)  # type: ignore[var-annotated]

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        word = self.word_input.value.lower().strip()
        existing = await db.get_chain_channel(channel.id)
        if existing and existing.get("word"):
            await interaction.response.send_message(
                f"❌ A chain is already active in {channel.mention}.",
                ephemeral=True,
            )
            return
        await db.set_chain_channel(channel.id, interaction.guild_id, word)
        await interaction.response.send_message(
            f"✅ Chain created in {channel.mention}. Only `{word}` is allowed.",
            ephemeral=True,
        )


class _DeleteChainModal(discord.ui.Modal, title="Delete Chain"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        existing = await db.get_chain_channel(channel.id)
        if not existing:
            await interaction.response.send_message(
                f"❌ No active chain found in {channel.mention}.",
                ephemeral=True,
            )
            return
        await db.delete_chain_channel(channel.id)
        await interaction.response.send_message(
            f"✅ Chain deleted from {channel.mention}.",
            ephemeral=True,
        )


class _SetLimitModal(discord.ui.Modal, title="Set Word Limit"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )
    limit_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Word limit (0 = remove limit)",
        max_length=10,
    )

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        if not self.limit_input.value.strip().isdigit():
            await interaction.response.send_message(
                "❌ Limit must be a non-negative integer.",
                ephemeral=True,
            )
            return
        limit = int(self.limit_input.value.strip())
        existing = await db.get_chain_channel(channel.id)
        if not existing:
            await interaction.response.send_message(
                f"❌ No active chain in {channel.mention}. Create one first.",
                ephemeral=True,
            )
            return
        await db.set_chain_limit(channel.id, limit)
        if limit == 0:
            await interaction.response.send_message(
                f"✅ Word limit removed from {channel.mention}.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"✅ Word limit set to {limit} words in {channel.mention}.",
                ephemeral=True,
            )


class _ChainMenuView(BaseView):
    """Interactive chain channel management panel."""

    def __init__(self, ctx: commands.Context, cog: ChainCog):
        super().__init__(ctx.author, timeout=180)
        self.ctx = ctx
        self.cog = cog

    async def build_embed(self) -> discord.Embed:
        channels = await db.get_all_chain_channels(self.ctx.guild.id)
        embed = discord.Embed(title="⛓️ Chain Manager", color=discord.Color.blue())
        if not channels:
            embed.description = "No active chains in this server."
        else:
            lines = []
            for entry in channels:
                ch = self.cog.bot.get_channel(entry["channel_id"])
                name = ch.mention if ch else f"<#{entry['channel_id']}>"
                parts = []
                if entry.get("word"):
                    parts.append(f"word: `{entry['word']}`")
                if entry.get("word_limit"):
                    parts.append(f"limit: `{entry['word_limit']}`")
                lines.append(f"{name} — {', '.join(parts) or 'no restrictions'}")
            embed.description = "\n".join(lines)
        embed.set_footer(text="Use buttons below to manage chains.")
        return embed

    @discord.ui.button(label="➕ Create Chain", style=discord.ButtonStyle.green, row=0)
    async def btn_create(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_CreateChainModal(self.cog))

    @discord.ui.button(label="🗑️ Delete Chain", style=discord.ButtonStyle.danger, row=0)
    async def btn_delete(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_DeleteChainModal(self.cog))

    @discord.ui.button(label="📏 Set Limit", style=discord.ButtonStyle.blurple, row=0)
    async def btn_setlimit(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_SetLimitModal(self.cog))

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )


# Asynchronous setup for discord.py 2.x
async def setup(bot):
    await bot.add_cog(ChainCog(bot))
    logger.info("ChainCog has been loaded.")
