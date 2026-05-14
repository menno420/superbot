import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions, has_permissions
from utils import db

logger = logging.getLogger(__name__)


class ChainCog(commands.Cog):
    """Cog for managing message chains and word limits in specified channels."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="chain", invoke_without_command=True)
    async def chain(self, ctx):
        """
        Manage message chains and word limits in your server.

        Use subcommands to create, delete, set limits, or list chains.
        """
        await ctx.send(
            "❓ Please specify a subcommand. Use `?chain create`, `?chain delete`, `?chain setlimit`, `?chain removelimit`, or `?chain list`."
        )

    @chain.command(name="create")
    @has_permissions(administrator=True)
    async def create_chain(
        self,
        ctx,
        channel: Optional[discord.TextChannel] = None,
        *,
        word: str = None,
    ):
        """
        Create a chain in a specified channel or the current channel if none is provided.

        Only the specified word will be allowed in that channel. All other messages will be deleted.

        **Usage:** `?chain create [channel] <word>`
        """
        if word is None:
            await ctx.send(
                "❌ Please specify the word to enforce in the chain.\n**Usage:** `?chain create [channel] <word>`"
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
            f"✅ Chain created in {target_channel.mention}. Only the word `{word}` is allowed in this channel."
        )

    @create_chain.error
    async def create_chain_error(self, ctx, error):
        """Handle errors for the create_chain command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel."
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in create_chain command: {error}")

    @chain.command(name="delete")
    @has_permissions(administrator=True)
    async def delete_chain(self, ctx, channel: discord.TextChannel = None):
        """
        Delete a chain from a specified channel or the current channel if none is provided.

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
                "❌ Invalid channel specified. Please mention a valid text channel."
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in delete_chain command: {error}")

    @chain.command(name="setlimit")
    @has_permissions(administrator=True)
    async def set_limit(
        self, ctx, channel: discord.TextChannel = None, limit: int = None
    ):
        """
        Set a word limit in a specified channel or the current channel if none is provided.

        **Usage:** `?chain setlimit [channel] <number>`
        """
        if limit is None or limit <= 0:
            await ctx.send(
                "❌ Please specify a valid word limit greater than 0.\n**Usage:** `?chain setlimit [channel] <number>`"
            )
            return

        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if not existing:
            await ctx.send(
                f"❌ No active chain found in {target_channel.mention}. Create one first with `?chain create`."
            )
            return

        await db.set_chain_limit(channel_id, limit)

        await ctx.send(
            f"✅ Word limit of {limit} has been set in {target_channel.mention}."
        )

    @set_limit.error
    async def set_limit_error(self, ctx, error):
        """Handle errors for the set_limit command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid input. Please mention a valid channel and specify a numerical limit."
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in set_limit command: {error}")

    @chain.command(name="removelimit")
    @has_permissions(administrator=True)
    async def remove_limit(self, ctx, channel: discord.TextChannel = None):
        """
        Remove the word limit from a specified channel or the current channel if none is provided.

        **Usage:** `?chain removelimit [channel]`
        """
        target_channel = channel or ctx.channel
        channel_id = target_channel.id

        existing = await db.get_chain_channel(channel_id)
        if existing and existing.get("word_limit"):
            await db.set_chain_limit(channel_id, 0)
            await ctx.send(
                f"✅ Word limit has been removed from {target_channel.mention}."
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
                "❌ Invalid channel specified. Please mention a valid text channel."
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in remove_limit command: {error}")

    @chain.command(name="list")
    async def list_chains(self, ctx):
        """
        List all active chains and word limits in the server.

        **Usage:** `?chain list`
        """
        channels = await db.get_all_chain_channels(ctx.guild.id)

        if not channels:
            await ctx.send(
                "ℹ️ There are no active chains or word limits in this server."
            )
            return

        embed = discord.Embed(
            title="Active Chains and Word Limits", color=discord.Color.green()
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
                f"Missing permissions to delete messages in {message.channel}."
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to delete message in {message.channel}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Event handler when the cog is ready."""
        logger.info(f"{self.__class__.__name__} is ready and operational.")


# Asynchronous setup for discord.py 2.x
async def setup(bot):
    await bot.add_cog(ChainCog(bot))
    logger.info("ChainCog has been loaded.")
