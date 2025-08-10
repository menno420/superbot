import discord
from discord.ext import commands
import json
import os
from discord.ext.commands import has_permissions, MissingPermissions
import asyncio
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the JSON file for persistence
DATA_FILE = "chain_data.json"

class ChainCog(commands.Cog):
    """Cog for managing message chains and word limits in specified channels."""

    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        """Load chain data from the JSON file."""
        if not os.path.isfile(DATA_FILE):
            logger.info(f"{DATA_FILE} not found. Creating a new one.")
            return {"channels": {}}
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                logger.info("Chain data loaded successfully.")
                return data
            except json.JSONDecodeError:
                logger.error(f"Failed to decode {DATA_FILE}. Initializing empty data.")
                return {"channels": {}}

    def save_data(self):
        """Save chain data to the JSON file."""
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
        logger.info("Chain data saved successfully.")

    @commands.group(name="chain", invoke_without_command=True)
    async def chain(self, ctx):
        """
        Manage message chains and word limits in your server.

        Use subcommands to create, delete, set limits, or list chains.
        """
        # Inform the user to use a subcommand
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

        channel_id_str = str(target_channel.id)

        if channel_id_str in self.data["channels"] and self.data["channels"][channel_id_str].get("word"):
            await ctx.send(f"❌ A chain is already active in {target_channel.mention}.")
            return

        if channel_id_str not in self.data["channels"]:
            self.data["channels"][channel_id_str] = {}

        self.data["channels"][channel_id_str]["word"] = word.lower()
        self.save_data()

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

        channel_id_str = str(target_channel.id)

        if channel_id_str not in self.data["channels"]:
            await ctx.send(f"❌ No active chain found in {target_channel.mention}.")
            return

        del self.data["channels"][channel_id_str]
        self.save_data()

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

        channel_id_str = str(target_channel.id)

        if channel_id_str not in self.data["channels"]:
            self.data["channels"][channel_id_str] = {}

        self.data["channels"][channel_id_str]["limit"] = limit
        self.save_data()

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

        channel_id_str = str(target_channel.id)

        if (
            channel_id_str in self.data["channels"]
            and "limit" in self.data["channels"][channel_id_str]
        ):
            del self.data["channels"][channel_id_str]["limit"]
            # Remove channel entry if empty
            if not self.data["channels"][channel_id_str]:
                del self.data["channels"][channel_id_str]
            self.save_data()
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
        if not self.data["channels"]:
            await ctx.send("ℹ️ There are no active chains or word limits in this server.")
            return

        embed = discord.Embed(title="Active Chains and Word Limits", color=discord.Color.green())

        for channel_id, settings in self.data["channels"].items():
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                word = settings.get("word")
                limit = settings.get("limit")
                description = ""
                if word:
                    description += f"Allowed Word: `{word}`\n"
                if limit:
                    description += f"Word Limit: `{limit}` words\n"
                if not description:
                    description = "No restrictions set."
                embed.add_field(name=channel.name, value=description, inline=False)
            else:
                embed.add_field(
                    name="Unknown Channel", value=f"Channel ID: `{channel_id}`", inline=False
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

        channel_id_str = str(message.channel.id)
        channel_data = self.data["channels"].get(channel_id_str)
        if not channel_data:
            return  # No chain or limit set for this channel

        allowed_word = channel_data.get("word")
        word_limit = channel_data.get("limit")

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
            return  # Message is allowed

        # Delete the message and optionally warn the user
        try:
            await message.delete()
            warning_message = f"{message.author.mention}, your message was deleted."
            if allowed_word and word_limit:
                warning_message += f" Only the word `{allowed_word}` is allowed, and messages must be at most {word_limit} words."
            elif allowed_word:
                warning_message += f" Only the word `{allowed_word}` is allowed in this channel."
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
