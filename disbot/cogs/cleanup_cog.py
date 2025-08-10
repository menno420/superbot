import re
import discord
from discord.ext import commands
import logging
import asyncio
import json

class Cleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        # Load prohibited words from file and compile regex patterns
        self.prohibited_words_file = '/home/menno/disbot/data/json/prohibited_words.json'
        self.prohibited_words = self.load_prohibited_words()
        self.prohibited_patterns = [
            re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            for word in self.prohibited_words
        ]

        # Command detection regex (messages starting with a command prefix)
        self.command_prefixes = ['?', '!']
        self.command_pattern = re.compile(
            rf'^\s*({"|".join(map(re.escape, self.command_prefixes))})\S+',
            re.IGNORECASE
        )

        # Channels where commands are allowed
        self.whitelisted_channels = [1348795460948590622, 1349693768365903912, 1349851456509055047]  # Replace with your actual channel IDs

    def load_prohibited_words(self):
        try:
            with open(self.prohibited_words_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.info("No prohibited words file found. Starting with an empty list.")
            return []

    def save_prohibited_words(self):
        try:
            with open(self.prohibited_words_file, 'w') as f:
                json.dump(self.prohibited_words, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving prohibited words: {e}")

    async def remove_unwanted_message(self, message):
        """Deletes the message if it is a command in a non‑whitelisted channel or contains prohibited content."""
        if message.author.bot:
            return False

        # If it's a command message and not in a whitelisted channel, delete it.
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
            # If in a whitelisted channel, allow the command to pass through.
            return False

        # For non-command messages, check for prohibited content.
        for pattern in self.prohibited_patterns:
            if pattern.search(message.content):
                try:
                    await message.delete()
                    warning_msg = await message.channel.send(
                        f"A message from {message.author.mention} was deleted because it contained prohibited content."
                    )
                    self.logger.info(f"Deleted message from {message.author}: {message.content}")
                    await warning_msg.delete(delay=10)
                except discord.DiscordException as e:
                    self.logger.error(f"Failed to delete message from {message.author}: {e}")
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only run deletion logic here; do not process commands.
        await self.remove_unwanted_message(message)
        # Note: We intentionally do not call process_commands(message) here
        # so that command processing can be handled by your main script without duplication.

    @commands.command(name='cleanup_history')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def cleanup_history(self, ctx, limit: int = 100, *, keyword: str = None):
        """Cleans up messages containing prohibited content or disallowed commands from the channel history."""
        if limit <= 0:
            await ctx.send("Please provide a positive number of messages to scan.", delete_after=5)
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
                user == ctx.author and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == confirmation_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "✅":
                await ctx.send(
                    f"Starting cleanup for the last {limit} messages"
                    + (f" filtering by `{keyword}`" if keyword else ""),
                    delete_after=5
                )
                async for message in ctx.channel.history(limit=limit):
                    if message.author.bot:
                        continue
                    if keyword and keyword.lower() not in message.content.lower():
                        continue
                    await self.remove_unwanted_message(message)
                await ctx.send("Cleanup completed.", delete_after=5)
                self.logger.info(f"Cleanup completed for the last {limit} messages in {ctx.channel.name}")
            else:
                await ctx.send("Cleanup canceled.", delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send("Cleanup confirmation timed out.", delete_after=5)
        finally:
            await ctx.message.delete()
            await confirmation_msg.delete()

    @commands.command(name='add_prohibited_word')
    @commands.has_permissions(administrator=True)
    async def add_prohibited_word(self, ctx, *, word: str):
        """Adds a word to the prohibited words list."""
        word = word.lower()
        if word in self.prohibited_words:
            await ctx.send(f"The word '{word}' is already in the prohibited list.", delete_after=5)
        else:
            self.prohibited_words.append(word)
            self.prohibited_patterns.append(
                re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            )
            self.save_prohibited_words()
            await ctx.send(f"Added '{word}' to the prohibited words list.", delete_after=5)
            self.logger.info(f"Added prohibited word: {word}")

    @commands.command(name='remove_prohibited_word')
    @commands.has_permissions(administrator=True)
    async def remove_prohibited_word(self, ctx, *, word: str):
        """Removes a word from the prohibited words list."""
        word = word.lower()
        if word in self.prohibited_words:
            self.prohibited_words.remove(word)
            self.prohibited_patterns = [
                re.compile(rf'\b{re.escape(w)}\b', re.IGNORECASE)
                for w in self.prohibited_words
            ]
            self.save_prohibited_words()
            await ctx.send(f"Removed '{word}' from the prohibited words list.", delete_after=5)
            self.logger.info(f"Removed prohibited word: {word}")
        else:
            await ctx.send(f"The word '{word}' is not in the prohibited list.", delete_after=5)

async def setup(bot):
    await bot.add_cog(Cleanup(bot))