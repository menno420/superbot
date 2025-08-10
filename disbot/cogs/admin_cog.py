from discord.ext import commands
import discord
import logging
import os
import sys
import importlib
import asyncio

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### Reaction Role System ###
    @commands.command(name='setup_reaction_roles')
    @commands.has_permissions(manage_roles=True)
    async def setup_reaction_roles(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Setup reaction role assignment. Users get a role when reacting with a specific emoji."""
        try:
            message = await ctx.fetch_message(message_id)
            await message.add_reaction(emoji)

            @self.bot.event
            async def on_raw_reaction_add(payload):
                if payload.message_id == message_id and str(payload.emoji) == emoji:
                    guild = self.bot.get_guild(payload.guild_id)
                    role_to_assign = guild.get_role(role.id)
                    member = guild.get_member(payload.user_id)
                    if role_to_assign and member:
                        await member.add_roles(role_to_assign)
                        await ctx.send(f'✅ Assigned {role_to_assign.name} to {member.display_name}.')

            @self.bot.event
            async def on_raw_reaction_remove(payload):
                if payload.message_id == message_id and str(payload.emoji) == emoji:
                    guild = self.bot.get_guild(payload.guild_id)
                    role_to_remove = guild.get_role(role.id)
                    member = guild.get_member(payload.user_id)
                    if role_to_remove and member:
                        await member.remove_roles(role_to_remove)
                        await ctx.send(f'❌ Removed {role_to_remove.name} from {member.display_name}.')
        except Exception as e:
            await ctx.send(f'⚠️ Error setting up reaction roles: {e}')
            logging.error(f'Error setting up reaction roles: {e}')

    ### Polls and Voting ###
    @commands.command(name='create_poll')
    @commands.has_permissions(manage_channels=True)
    async def create_poll(self, ctx, question: str, *options):
        """Create a poll with up to 10 options."""
        if len(options) > 10:
            await ctx.send("⚠️ You can only provide up to 10 options.")
            return

        description = [f"{i}. {option}" for i, option in enumerate(options, 1)]

        embed = discord.Embed(title=question, description="\n".join(description), color=discord.Color.blue())
        poll_message = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_message.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")

    ### Server Statistics ###
    @commands.command(name='server_stats')
    async def server_stats(self, ctx):
        """Display server statistics."""
        guild = ctx.guild
        total_members = guild.member_count
        online_members = sum(member.status != discord.Status.offline for member in guild.members)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)

        embed = discord.Embed(title=f"Server Stats for {guild.name}", color=discord.Color.green())
        embed.add_field(name="Total Members", value=total_members)
        embed.add_field(name="Online Members", value=online_members)
        embed.add_field(name="Text Channels", value=text_channels)
        embed.add_field(name="Voice Channels", value=voice_channels)
        embed.add_field(name="Roles", value=roles)
        await ctx.send(embed=embed)

    ### Dynamic Cog Management ###
    @commands.command(name='cog')
    @commands.is_owner()
    async def manage_cog(self, ctx, action: str, cog_name: str):
        """Load, unload, or reload a specified cog."""
        action = action.lower()
        if action not in ['load', 'unload', 'reload']:
            await ctx.send(f'❌ Invalid action `{action}`. Use `load`, `unload`, or `reload`.')
            return
        try:
            if action == 'load':
                await self.bot.load_extension(f'cogs.{cog_name}')
            elif action == 'unload':
                await self.bot.unload_extension(f'cogs.{cog_name}')
            elif action == 'reload':
                await self.bot.reload_extension(f'cogs.{cog_name}')
            await ctx.send(f'✅ Cog `{cog_name}` has been successfully {action}ed.')
        except Exception as e:
            await ctx.send(f'⚠️ Error {action}ing cog `{cog_name}`: {e}')

    ### Manage All Cogs ###
    @commands.command(name='load_all_cogs')
    @commands.is_owner()
    async def load_all_cogs(self, ctx):
        """Load all cogs."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.load_extension(f'cogs.{filename[:-3]}')
        await ctx.send('✅ All cogs loaded successfully.')

    @commands.command(name='unload_all_cogs')
    @commands.is_owner()
    async def unload_all_cogs(self, ctx):
        """Unload all cogs."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.unload_extension(f'cogs.{filename[:-3]}')
        await ctx.send('✅ All cogs unloaded successfully.')

    @commands.command(name='reload_all_cogs')
    @commands.is_owner()
    async def reload_all_cogs(self, ctx):
        """Reload all cogs."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.reload_extension(f'cogs.{filename[:-3]}')
        await ctx.send('✅ All cogs reloaded successfully.')

    ### Restart Bot (Reload Main Script) ###
    @commands.command(name='reload_main_script')
    @commands.is_owner()
    async def reload_main_script(self, ctx):
        """Restart the bot to reload the main script."""
        await ctx.send('♻️ Restarting bot...')
        logging.info('Restarting bot...')

        await self.bot.close()  # Shut down the bot
        os.execv(sys.executable, [sys.executable] + sys.argv)  # Restart the bot process

    ### Send a startup message only to #bot_spam channel ###
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='bot_spam')
            if channel and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(f'Hello everyone! {self.bot.user.name} is now online and ready to rumble!')
                except Exception as e:
                    logging.error(f'Error sending startup message: {e}')

# Function to load this cog
async def setup(bot):
    await bot.add_cog(AdminCog(bot))