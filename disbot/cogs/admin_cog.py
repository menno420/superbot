from __future__ import annotations
from discord.ext import commands
import discord
import logging
import os
import re
import sys
import ast
import asyncio

COGS_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(os.path.dirname(COGS_DIR), "bot.pid")


def _normalize(name: str) -> str:
    """Strip underscores/spaces, lowercase, remove trailing 'cog'."""
    return re.sub(r'[\s_]+', '', name.lower()).removesuffix('cog')


def _find_module(name: str) -> str | None:
    """Return the full module path (e.g. 'cogs.admin_cog') for a fuzzy cog name."""
    target = _normalize(name)
    for fname in sorted(os.listdir(COGS_DIR)):
        if fname.endswith('_cog.py') and not fname.startswith('__'):
            if _normalize(fname[:-3]) == target:
                return f'cogs.{fname[:-3]}'
    return None


def _all_cog_modules() -> list[str]:
    """Return module paths for every *_cog.py file."""
    return [
        f'cogs.{f[:-3]}'
        for f in sorted(os.listdir(COGS_DIR))
        if f.endswith('_cog.py') and not f.startswith('__')
    ]


def _syntax_ok(fname: str) -> bool:
    """Return True if the file parses without syntax errors."""
    try:
        with open(os.path.join(COGS_DIR, fname), 'r', encoding='utf-8') as fh:
            ast.parse(fh.read(), fname)
        return True
    except SyntaxError:
        return False


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Reaction Role System
    # ------------------------------------------------------------------
    @commands.command(name='setup_reaction_roles', aliases=['reaktionsrollen'])
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

    # ------------------------------------------------------------------
    # Polls
    # ------------------------------------------------------------------
    @commands.command(name='create_poll', aliases=['erstelle_umfrage'])
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

    # ------------------------------------------------------------------
    # Server Statistics
    # ------------------------------------------------------------------
    @commands.command(name='server_stats')
    async def server_stats(self, ctx):
        """Display server statistics."""
        guild = ctx.guild
        embed = discord.Embed(title=f"Server Stats for {guild.name}", color=discord.Color.green())
        embed.add_field(name="Total Members", value=guild.member_count)
        embed.add_field(name="Online Members", value=sum(m.status != discord.Status.offline for m in guild.members))
        embed.add_field(name="Text Channels", value=len(guild.text_channels))
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------
    # Cog Management
    # ------------------------------------------------------------------
    @commands.command(name='cog')
    @commands.is_owner()
    async def manage_cog(self, ctx, action: str, cog_name: str):
        """Load, unload, or reload a cog by name (underscores and _cog suffix optional)."""
        action = action.lower()
        if action not in ('load', 'unload', 'reload'):
            await ctx.send(f'❌ Invalid action `{action}`. Use `load`, `unload`, or `reload`.')
            return
        module = _find_module(cog_name)
        if not module:
            await ctx.send(f'❌ No cog found matching `{cog_name}`.')
            return
        try:
            if action == 'load':
                await self.bot.load_extension(module)
            elif action == 'unload':
                await self.bot.unload_extension(module)
            elif action == 'reload':
                await self.bot.reload_extension(module)
            await ctx.send(f'✅ `{module}` {action}ed.')
        except Exception as e:
            await ctx.send(f'⚠️ Error {action}ing `{module}`: {e}')

    @commands.command(name='cog_list')
    @commands.has_permissions(administrator=True)
    async def cog_list(self, ctx):
        """List all cog files with load status and syntax check."""
        loaded = set(self.bot.extensions.keys())
        lines = []
        for fname in sorted(os.listdir(COGS_DIR)):
            if not fname.endswith('_cog.py') or fname.startswith('__'):
                continue
            module = f'cogs.{fname[:-3]}'
            load_icon = '✅' if module in loaded else '❌'
            syntax_icon = '🟢' if _syntax_ok(fname) else '🔴 SYNTAX ERROR'
            lines.append(f'{load_icon} {syntax_icon}  `{fname[:-3]}`')
        embed = discord.Embed(
            title='Cog List',
            description='\n'.join(lines) or 'No cogs found.',
            color=discord.Color.blue(),
        )
        embed.set_footer(text='✅ Loaded  ❌ Unloaded  🟢 Syntax OK  🔴 Syntax Error')
        await ctx.send(embed=embed)

    @commands.command(name='load_all_cogs')
    @commands.is_owner()
    async def load_all_cogs(self, ctx):
        """Load all unloaded cogs, skipping already-loaded ones."""
        loaded_now, skipped, failed = [], [], []
        for module in _all_cog_modules():
            if module in self.bot.extensions:
                skipped.append(module.split('.')[1])
                continue
            try:
                await self.bot.load_extension(module)
                loaded_now.append(module.split('.')[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if loaded_now:
            parts.append(f'✅ Loaded: {", ".join(f"`{n}`" for n in loaded_now)}')
        if skipped:
            parts.append(f'⏭️ Already loaded: {", ".join(f"`{n}`" for n in skipped)}')
        if failed:
            parts.append('❌ Failed:\n' + '\n'.join(failed))
        await ctx.send('\n'.join(parts) or '✅ Nothing to load.')

    @commands.command(name='unload_all_cogs')
    @commands.is_owner()
    async def unload_all_cogs(self, ctx):
        """Unload all loaded cogs except this one."""
        unloaded, skipped, failed = [], [], []
        for module in _all_cog_modules():
            if module == 'cogs.admin_cog':
                skipped.append('admin_cog (self)')
                continue
            if module not in self.bot.extensions:
                skipped.append(module.split('.')[1])
                continue
            try:
                await self.bot.unload_extension(module)
                unloaded.append(module.split('.')[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if unloaded:
            parts.append(f'🔴 Unloaded: {", ".join(f"`{n}`" for n in unloaded)}')
        if skipped:
            parts.append(f'⏭️ Skipped: {", ".join(f"`{n}`" for n in skipped)}')
        if failed:
            parts.append('❌ Failed:\n' + '\n'.join(failed))
        await ctx.send('\n'.join(parts) or '✅ Nothing to unload.')

    @commands.command(name='reload_all_cogs')
    @commands.is_owner()
    async def reload_all_cogs(self, ctx):
        """Reload all currently loaded cogs."""
        reloaded, failed = [], []
        for module in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(module)
                reloaded.append(module.split('.')[1])
            except Exception as e:
                failed.append(f'`{module.split(".")[1]}`: {e}')
        parts = []
        if reloaded:
            parts.append(f'🔄 Reloaded: {", ".join(f"`{n}`" for n in reloaded)}')
        if failed:
            parts.append('❌ Failed:\n' + '\n'.join(failed))
        await ctx.send('\n'.join(parts) or '✅ Nothing to reload.')

    # ------------------------------------------------------------------
    # Restart
    # ------------------------------------------------------------------
    @commands.command(name='reload_main_script')
    @commands.is_owner()
    async def reload_main_script(self, ctx):
        """Restart the bot process."""
        await ctx.send('♻️ Restarting bot...')
        logging.info('Restarting bot...')
        # Remove PID file so the new process doesn't think another instance is running
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # ------------------------------------------------------------------
    # Webhook log level
    # ------------------------------------------------------------------
    @commands.command(name='loglevel')
    @commands.has_permissions(administrator=True)
    async def set_log_level(self, ctx, level: str):
        """Change the webhook log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)."""
        handler = getattr(self.bot, '_webhook_handler', None)
        if not handler:
            await ctx.send('❌ No webhook handler is configured.')
            return
        level_int = getattr(logging, level.upper(), None)
        if not isinstance(level_int, int):
            await ctx.send(f'❌ Unknown level `{level}`. Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL')
            return
        handler.setLevel(level_int)
        await ctx.send(f'✅ Webhook log level set to `{level.upper()}`.')

    # ------------------------------------------------------------------
    # Startup message
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='bot_spam')
            if channel and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(f'Hello everyone! {self.bot.user.name} is now online and ready to rumble!')
                except Exception as e:
                    logging.error(f'Error sending startup message: {e}')


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
