"""Channel-management subsystem — thin command dispatcher.

Panel views live under :mod:`views.channels`.  This cog hosts only the
prefix commands and helpers that operate directly on the Discord
guild; everything UI-related delegates to the views package.

Compatibility:
- ``cogs.channel_cog._SubsystemToggleView`` and friends remain importable
  via re-export below so existing tests (``test_view_error_handling.py``)
  continue to work without change.
- ``SUBSYSTEM`` identity string and every persisted custom_id are
  unchanged (the visibility panel still uses ``toggle_<subsystem>``).
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import help_ctx_shim
from utils.channels import get_or_create_category, safe_channel_name
from utils.ui_constants import INFO_COLOR, WARNING_COLOR
from views.base import send_panel

# Re-exports for test backward-compat and any external consumers that
# imported these names directly from cogs.channel_cog.
from views.channels import (  # noqa: F401 — backward-compat re-exports
    _CATEGORY_PRESETS,
    _NAME_PRESETS,
    _build_channel_options,
    _CategorySelect,
    _ChannelManagerView,
    _ChannelSelect,
    _ChannelSelectForVisibility,
    _CreateSubView,
    _CustomNameModal,
    _DeleteConfirmView,
    _DeleteSubView,
    _NameSelect,
    _RestrictSubView,
    _SubsystemToggleView,
    _VisibilitySubView,
)

logger = logging.getLogger("bot")


class ChannelCog(commands.Cog):
    """Cog for managing Discord channels and categories."""

    def __init__(self, bot):
        self.bot = bot

    # -------------------
    # Helper Functions
    # -------------------

    @staticmethod
    def is_admin_or_owner():
        """Check if the user is an administrator or the server owner."""

        async def predicate(ctx):
            return (
                ctx.author.guild_permissions.administrator
                or ctx.author.id == ctx.guild.owner_id
            )

        return commands.check(predicate)

    def _resolve_channel(self, guild: discord.Guild, query: str):
        """Find a channel by name, mention (<#ID>), or numeric ID."""
        if query.startswith("<#") and query.endswith(">"):
            query = query[2:-1]
        if query.isdigit():
            ch = resources.resolve_channel(guild, channel_id=query)
            if ch:
                return ch
        return resources.resolve_channel(guild, name=query, kind="any")

    def _resolve_category(self, guild: discord.Guild, query: str):
        """Find a category by name, mention, or numeric ID."""
        if query.startswith("<#") and query.endswith(">"):
            query = query[2:-1]
        if query.isdigit():
            ch = resources.resolve_channel(guild, channel_id=query)
            if isinstance(ch, discord.CategoryChannel):
                return ch
        return resources.resolve_channel(guild, name=query, kind="category")

    def get_category_or_channel(self, guild, query):
        return self._resolve_category(guild, query) or self._resolve_channel(
            guild,
            query,
        )

    async def set_permissions(self, target, role, read_messages):
        if isinstance(target, discord.CategoryChannel):
            for channel in target.channels:
                await channel.set_permissions(role, read_messages=read_messages)
        elif isinstance(target, (discord.TextChannel, discord.VoiceChannel)):
            await target.set_permissions(role, read_messages=read_messages)

    def format_overwrites(self, overwrites):
        formatted = ""
        for target, perms in overwrites.items():
            name = (
                target.name
                if isinstance(target, discord.Role)
                else (
                    target.display_name
                    if isinstance(target, discord.Member)
                    else "Unknown"
                )
            )
            allow = ", ".join(
                [p.replace("_", " ").title() for p, v in iter(perms) if v is True],
            )
            deny = ", ".join(
                [p.replace("_", " ").title() for p, v in iter(perms) if v is False],
            )
            formatted += (
                f"**{name}**\nAllowed: {allow or 'None'}\nDenied: {deny or 'None'}\n\n"
            )
        return formatted or "No overwrites."

    # -------------------
    # Commands
    # -------------------

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(
        name="channelmenu",
        help="Open the interactive channel management panel.",
    )
    @is_admin_or_owner()
    async def channel_menu(self, ctx):
        """Open the interactive channel management panel."""
        view = _ChannelManagerView(ctx)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the channel manager panel)."""
        view = _ChannelManagerView(help_ctx_shim(interaction))
        return view.build_embed(), view

    @commands.command(
        name="set",
        help="Set access for a channel/category. Usage: !set <name|id> <@role> <True/False>",
    )
    @is_admin_or_owner()
    async def set_access(self, ctx, target: str, role: discord.Role, permission: bool):
        target_channel = self.get_category_or_channel(ctx.guild, target)
        if target_channel:
            await self.set_permissions(target_channel, role, read_messages=permission)
            state = "opened" if permission else "closed"
            await ctx.send(
                f'{target_channel.type} "{target_channel.name}" {state} for {role.name}!',
            )
        else:
            await ctx.send(f'Channel or Category "{target}" not found.')

    @commands.command(
        name="evt",
        help="Create or delete an event channel. Usage: !evt <name|id> <create/delete>",
    )
    @is_admin_or_owner()
    async def manage_event(self, ctx, evt: str, action: str):
        if action.lower() == "create":
            category = await get_or_create_category(ctx.guild, "Events")
            name = await safe_channel_name(ctx.guild, evt)
            await ctx.guild.create_text_channel(name, category=category)
            await ctx.send(f'Event channel "{name}" created!')
        elif action.lower() == "delete":
            channel = self._resolve_channel(ctx.guild, evt)
            if channel:
                await channel.delete()
                await ctx.send(f'Event "{channel.name}" deleted!')
            else:
                await ctx.send(f'Event "{evt}" not found.')
        else:
            await ctx.send('Invalid action. Use "create" or "delete".')

    @commands.command(
        name="create",
        help="Create a channel with role access. Usage: !create <name> <@role> <True/False> [category]",
    )
    @is_admin_or_owner()
    async def create_channel_with_role(
        self,
        ctx,
        channel_name: str,
        role: discord.Role,
        permission: bool,
        category_name: str = None,
    ):
        safe_name = await safe_channel_name(ctx.guild, channel_name)
        category = None
        if category_name:
            category = self._resolve_category(ctx.guild, category_name)
            if not category:
                await ctx.send(f'Category "{category_name}" not found!')
                return

        new_channel = await ctx.guild.create_text_channel(safe_name, category=category)
        await new_channel.set_permissions(role, read_messages=permission)
        state = "granted" if permission else "restricted"
        suffix = f' (renamed to "{safe_name}")' if safe_name != channel_name else ""
        await ctx.send(
            f'Channel "{safe_name}" created with {state} access for {role.name}!{suffix}',
        )

    @commands.command(
        name="bulkdelete",
        help="Delete multiple channels. Usage: !bulkdelete <name|id> [name|id...] or <keyword>",
    )
    @is_admin_or_owner()
    async def bulk_delete_channels(self, ctx, *channel_names_or_word: str):
        if not channel_names_or_word:
            await ctx.send("Please provide at least one channel name, ID, or keyword.")
            return

        if len(channel_names_or_word) == 1:
            word = channel_names_or_word[0]
            # Single arg: try exact ID/name match first, then keyword search
            exact = self._resolve_channel(ctx.guild, word)
            if exact:
                channels_to_delete = [exact]
            else:
                channels_to_delete = [
                    ch for ch in ctx.guild.channels if word in ch.name
                ]
                if not channels_to_delete:
                    await ctx.send(f"No channels found matching '{word}'.")
                    return
        else:
            channels_to_delete = [
                self._resolve_channel(ctx.guild, n) for n in channel_names_or_word
            ]

        deleted, failed = [], []
        for channel in channels_to_delete:
            if channel:
                try:
                    await channel.delete()
                    deleted.append(channel.name)
                except Exception:
                    failed.append(channel.name)
            else:
                failed.append("Not found")

        response = ""
        if deleted:
            response += f'✅ Deleted: {", ".join(deleted)}.\n'
        if failed:
            response += f'❌ Failed: {", ".join(failed)}.'
        await ctx.send(response)

    @commands.command(
        name="del",
        help="Delete a specific channel. Usage: !del <name|id>",
    )
    @is_admin_or_owner()
    async def delete_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.delete()
            await ctx.send(f'Channel "{channel.name}" deleted.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name="list",
        help="List all categories and channels, including uncategorized.",
    )
    @is_admin_or_owner()
    async def list_channels(self, ctx):
        embed = discord.Embed(title="Categories and Channels", color=INFO_COLOR)
        for category in ctx.guild.categories:
            channels = "\n".join(f" - {ch.name}" for ch in category.channels)
            embed.add_field(
                name=category.name,
                value=channels or "No channels",
                inline=False,
            )
        uncategorized = [
            ch
            for ch in ctx.guild.channels
            if ch.category is None and not isinstance(ch, discord.CategoryChannel)
        ]
        if uncategorized:
            names = "\n".join(
                f" - {ch.name}"
                for ch in sorted(uncategorized, key=lambda c: c.position)
            )
            embed.add_field(name="— Uncategorized —", value=names, inline=False)
        await ctx.send(embed=embed)

    @commands.command(
        name="clone",
        help="Clone a channel. Usage: !clone <name|id> <new_name>",
    )
    @is_admin_or_owner()
    async def clone_channel(
        self,
        ctx,
        existing_channel_name: str,
        new_channel_name: str,
    ):
        existing = self._resolve_channel(ctx.guild, existing_channel_name)
        if existing:
            await existing.clone(name=new_channel_name)
            await ctx.send(f'"{existing.name}" cloned as "{new_channel_name}".')
        else:
            await ctx.send(f'"{existing_channel_name}" not found.')

    @commands.command(
        name="move",
        help="Move a channel to a category. Usage: !move <channel name|id> <category name|id>",
    )
    @is_admin_or_owner()
    async def move_channel(self, ctx, channel_name: str, category_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        category = self._resolve_category(ctx.guild, category_name)
        if channel and category:
            await channel.edit(category=category)
            await ctx.send(f'"{channel.name}" moved to "{category.name}".')
        else:
            await ctx.send("Channel or Category not found.")

    @commands.command(name="lock", help="Lock a channel. Usage: !lock <name|id>")
    @is_admin_or_owner()
    async def lock_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f'"{channel.name}" locked.')
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(name="unlock", help="Unlock a channel. Usage: !unlock <name|id>")
    @is_admin_or_owner()
    async def unlock_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send(f'"{channel.name}" unlocked.')
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(
        name="channelinfo",
        help="Channel details. Usage: !channelinfo <name|id>",
    )
    @is_admin_or_owner()
    async def channel_info(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            embed = discord.Embed(
                title=f"Channel Info — {channel.name}",
                color=WARNING_COLOR,
            )
            embed.add_field(name="Type", value=str(channel.type), inline=True)
            embed.add_field(
                name="Category",
                value=channel.category.name if channel.category else "None",
                inline=True,
            )
            embed.add_field(name="Position", value=str(channel.position), inline=True)
            embed.add_field(
                name="Topic",
                value=getattr(channel, "topic", None) or "No topic set.",
                inline=False,
            )
            embed.add_field(
                name="Created",
                value=channel.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=True,
            )
            embed.add_field(name="ID", value=str(channel.id), inline=True)
            embed.add_field(
                name="Overwrites",
                value=self.format_overwrites(channel.overwrites),
                inline=False,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(
        name="rename",
        help="Rename a channel. Usage: !rename <old name|id> <new_name>",
    )
    @is_admin_or_owner()
    async def rename_channel(self, ctx, old_name: str, new_name: str):
        channel = self._resolve_channel(ctx.guild, old_name)
        if channel:
            old = channel.name
            await channel.edit(name=new_name)
            await ctx.send(f'"{old}" renamed to "{new_name}".')
        else:
            await ctx.send(f'"{old_name}" not found.')

    @commands.command(
        name="permissions",
        help="Modify channel permissions. Usage: !permissions <name|id> <@role> <allow/deny>",
    )
    @is_admin_or_owner()
    async def modify_permissions(
        self,
        ctx,
        channel_name: str,
        role: discord.Role,
        action: str,
    ):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            if action.lower() == "allow":
                await channel.set_permissions(role, send_messages=True)
                await ctx.send(
                    f'Send messages **allowed** for {role.name} in "{channel.name}".',
                )
            elif action.lower() == "deny":
                await channel.set_permissions(role, send_messages=False)
                await ctx.send(
                    f'Send messages **denied** for {role.name} in "{channel.name}".',
                )
            else:
                await ctx.send('Invalid action. Use "allow" or "deny".')
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(
        name="bulkcreate",
        help="Create multiple channels. Usage: !bulkcreate <ch1> [ch2...] [category]",
    )
    @is_admin_or_owner()
    async def bulk_create_channels(self, ctx, *args):
        if not args:
            await ctx.send("Please provide at least one channel name.")
            return

        channel_names = list(args)
        category = None
        potential = self.get_category_or_channel(ctx.guild, args[-1])
        if isinstance(potential, discord.CategoryChannel):
            category = potential
            channel_names = list(args[:-1])

        created, failed = [], []
        for ch in channel_names:
            safe = await safe_channel_name(ctx.guild, ch)
            try:
                await ctx.guild.create_text_channel(safe, category=category)
                suffix = f" (as {safe})" if safe != ch else ""
                created.append(f"{ch}{suffix}")
            except Exception:
                failed.append(ch)

        response = ""
        if created:
            response += f'✅ Created: {", ".join(created)}.\n'
        if failed:
            response += f'❌ Failed: {", ".join(failed)}.'
        await ctx.send(response)


async def setup(bot):
    await bot.add_cog(ChannelCog(bot))
    logger.info("ChannelCog loaded.")
