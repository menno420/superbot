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
from core.runtime.permission_checks import member_has_perms_or_owner
from services.channel_lifecycle_service import (
    MAX_SLOWMODE_SECONDS,
    ChannelLifecycleRequest,
    ChannelLifecycleService,
)
from services.lifecycle import SUCCESS
from utils.ui_constants import INFO_COLOR, WARNING_COLOR
from views.base import send_panel

# Re-exports for test backward-compat and any external consumers that
# imported these names directly from cogs.channel_cog.
from views.channels import (  # noqa: F401 — backward-compat re-exports
    _CATEGORY_PRESETS,
    _NAME_PRESETS,
    _build_channel_options,
    _ChannelManagerView,
    _ChannelSelect,
    _CreateSubView,
    _CustomNameModal,
    _DeleteConfirmView,
    _DeleteSubView,
    _RestrictSubView,
    _SubsystemToggleView,
    _VisibilitySubView,
)

# !list pagination moved to views/channels/list_panel.py (P0-4); re-exported
# here so callers/tests importing them from cogs.channel_cog keep working.
from views.channels.list_panel import (  # noqa: F401 — backward-compat re-exports
    _CHANNELS_PER_PAGE_CATEGORIES,
    _MAX_FIELD_VALUE,
    _build_channel_list_pages,
    _ChannelListPaginatorView,
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
                member_has_perms_or_owner(ctx.author, administrator=True)
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

    @staticmethod
    def _overwrite_channel_ids(target) -> tuple[int, ...]:
        """Channel ids an overwrite applies to: a category fans out to its
        text/voice children, a single channel is itself.
        """
        if isinstance(target, discord.CategoryChannel):
            return tuple(ch.id for ch in target.channels)
        if isinstance(target, (discord.TextChannel, discord.VoiceChannel)):
            return (target.id,)
        return ()

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

    @staticmethod
    def _channel_result_error(result) -> str:
        """First human-readable error from a ChannelLifecycleService result."""
        for step in result.failed:
            if step.error:
                return step.error
        return "operation could not be completed"

    async def _apply_overwrite(
        self,
        ctx,
        channel_ids: tuple[int, ...],
        target_id: int,
        overwrites: dict[str, bool | None],
        *,
        success: str,
        fail_label: str,
    ) -> None:
        """Route permission overwrite(s) through the audited
        ChannelLifecycleService (P0-4, Q-0100) and report the typed outcome.
        """
        if not channel_ids:
            await ctx.send(f"{fail_label}: no channels to update.")
            return
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="set_overwrite",
                channel_ids=channel_ids,
                overwrite_target_id=target_id,
                overwrite_target_type="role",
                overwrites=overwrites,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(success)
        else:
            await ctx.send(f"❌ {fail_label}: {self._channel_result_error(result)}")

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
        if not target_channel:
            await ctx.send(f'Channel or Category "{target}" not found.')
            return
        state = "opened" if permission else "closed"
        await self._apply_overwrite(
            ctx,
            self._overwrite_channel_ids(target_channel),
            role.id,
            {"read_messages": permission},
            success=(
                f'{target_channel.type} "{target_channel.name}" {state} '
                f"for {role.name}!"
            ),
            fail_label=f'Could not update "{target_channel.name}"',
        )

    @commands.command(
        name="evt",
        help="Create or delete an event channel. Usage: !evt <name|id> <create/delete>",
    )
    @is_admin_or_owner()
    async def manage_event(self, ctx, evt: str, action: str):
        if action.lower() == "create":
            result = await ChannelLifecycleService().create_channels(
                ctx.guild,
                [evt],
                ctx.author,
                category_name="Events",
                actor_type="admin",
            )
            if result.outcome == SUCCESS:
                created = ctx.guild.get_channel(result.applied[0].target_id)
                name = created.name if created else evt
                await ctx.send(f'Event channel "{name}" created!')
            else:
                await ctx.send(
                    f"❌ Could not create event channel: "
                    f"{self._channel_result_error(result)}",
                )
        elif action.lower() == "delete":
            channel = self._resolve_channel(ctx.guild, evt)
            if not channel:
                await ctx.send(f'Event "{evt}" not found.')
                return
            name = channel.name
            result = await ChannelLifecycleService().apply(
                ctx.guild,
                ChannelLifecycleRequest(operation="delete", channel_ids=(channel.id,)),
                ctx.author,
                confirmed=True,
                actor_type="admin",
            )
            if result.outcome == SUCCESS:
                await ctx.send(f'Event "{name}" deleted!')
            else:
                await ctx.send(
                    f'❌ Could not delete "{name}": {self._channel_result_error(result)}',
                )
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
        category = None
        if category_name:
            category = self._resolve_category(ctx.guild, category_name)
            if not category:
                await ctx.send(f'Category "{category_name}" not found!')
                return

        # Channel creation routes through the audited lifecycle seam (P0-4 PR 2,
        # Q-0100); the follow-up permission overwrite routes through it too.
        result = await ChannelLifecycleService().create_channels(
            ctx.guild,
            [channel_name],
            ctx.author,
            category_id=category.id if category else None,
            actor_type="admin",
        )
        if result.outcome != SUCCESS:
            await ctx.send(
                f'❌ Could not create channel "{channel_name}": '
                f"{self._channel_result_error(result)}",
            )
            return
        new_channel = ctx.guild.get_channel(result.applied[0].target_id)
        safe_name = new_channel.name if new_channel else channel_name
        state = "granted" if permission else "restricted"
        suffix = f' (renamed to "{safe_name}")' if safe_name != channel_name else ""
        await self._apply_overwrite(
            ctx,
            (new_channel.id,),
            role.id,
            {"read_messages": permission},
            success=(
                f'Channel "{safe_name}" created with {state} access '
                f"for {role.name}!{suffix}"
            ),
            fail_label=f'Channel "{safe_name}" created, but access setup failed',
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

        resolved = [ch for ch in channels_to_delete if ch]
        not_found = len(channels_to_delete) - len(resolved)
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="delete",
                channel_ids=tuple(ch.id for ch in resolved),
            ),
            ctx.author,
            confirmed=True,
            actor_type="admin",
        )
        deleted = [s.target_name for s in result.applied]
        failed = [s.target_name or "?" for s in result.failed]
        failed += ["Not found"] * not_found

        response = ""
        if deleted:
            response += f"✅ Deleted: {', '.join(deleted)}.\n"
        if failed:
            response += f"❌ Failed: {', '.join(failed)}."
        await ctx.send(response)

    @commands.command(
        name="del",
        help="Delete a specific channel. Usage: !del <name|id>",
    )
    @is_admin_or_owner()
    async def delete_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            await ctx.send(f'Channel "{channel_name}" not found.')
            return
        name = channel.name
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(operation="delete", channel_ids=(channel.id,)),
            ctx.author,
            confirmed=True,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f'Channel "{name}" deleted.')
        else:
            await ctx.send(
                f'❌ Could not delete "{name}": {self._channel_result_error(result)}',
            )

    @commands.command(
        name="list",
        help="List all categories and channels, including uncategorized.",
    )
    @is_admin_or_owner()
    async def list_channels(self, ctx):
        """PR F: paginated to dodge Discord's 25-field and 6000-char caps.

        Previously this command added one embed field per category and
        one for uncategorized channels. A guild with ~25 categories
        or a few category-with-many-channels combinations could push
        the embed over the field cap (silent failure) or the 6000-char
        total-embed cap (HTTPException). Now the categories are split
        into pages and each field value is truncated to 1024 characters
        (Discord's per-field cap).
        """
        pages = _build_channel_list_pages(ctx.guild)
        if not pages:
            await ctx.send(
                embed=discord.Embed(
                    title="Categories and Channels",
                    description="No channels found.",
                    color=INFO_COLOR,
                ),
            )
            return
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        view = _ChannelListPaginatorView(ctx.author, pages)
        view.message = await ctx.send(embed=pages[0], view=view)

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
        if not existing:
            await ctx.send(f'"{existing_channel_name}" not found.')
            return
        name = existing.name
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="clone",
                channel_ids=(existing.id,),
                clone_name=new_channel_name,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f'"{name}" cloned as "{new_channel_name}".')
        else:
            await ctx.send(
                f'❌ Could not clone "{name}": {self._channel_result_error(result)}',
            )

    @commands.command(
        name="move",
        help="Move a channel to a category. Usage: !move <channel name|id> <category name|id>",
    )
    @is_admin_or_owner()
    async def move_channel(self, ctx, channel_name: str, category_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        category = self._resolve_category(ctx.guild, category_name)
        if not (channel and category):
            await ctx.send("Channel or Category not found.")
            return
        name = channel.name
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="move",
                channel_ids=(channel.id,),
                category_id=category.id,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f'"{name}" moved to "{category.name}".')
        else:
            await ctx.send(
                f'❌ Could not move "{name}": {self._channel_result_error(result)}',
            )

    @commands.command(name="lock", help="Lock a channel. Usage: !lock <name|id>")
    @is_admin_or_owner()
    async def lock_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            await ctx.send(f'"{channel_name}" not found.')
            return
        await self._apply_overwrite(
            ctx,
            (channel.id,),
            ctx.guild.default_role.id,
            {"send_messages": False},
            success=f'"{channel.name}" locked.',
            fail_label=f'Could not lock "{channel.name}"',
        )

    @commands.command(name="unlock", help="Unlock a channel. Usage: !unlock <name|id>")
    @is_admin_or_owner()
    async def unlock_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            await ctx.send(f'"{channel_name}" not found.')
            return
        await self._apply_overwrite(
            ctx,
            (channel.id,),
            ctx.guild.default_role.id,
            {"send_messages": True},
            success=f'"{channel.name}" unlocked.',
            fail_label=f'Could not unlock "{channel.name}"',
        )

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
        if not channel:
            await ctx.send(f'"{old_name}" not found.')
            return
        old = channel.name
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="rename",
                channel_ids=(channel.id,),
                new_name=new_name,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            await ctx.send(f'"{old}" renamed to "{new_name}".')
        else:
            await ctx.send(
                f'❌ Could not rename "{old}": {self._channel_result_error(result)}',
            )

    @commands.command(
        name="slowmode",
        aliases=["slow"],
        help=(
            "Set a channel's slowmode. Usage: !slowmode <name|id> <seconds> "
            "(0 disables; max 21600 = 6h)"
        ),
    )
    @is_admin_or_owner()
    async def set_slowmode(self, ctx, channel_name: str, seconds: int):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            await ctx.send(f'"{channel_name}" not found.')
            return
        if seconds < 0:
            await ctx.send("Slowmode must be 0 or more seconds.")
            return
        if seconds > MAX_SLOWMODE_SECONDS:
            await ctx.send(
                f"Slowmode caps at {MAX_SLOWMODE_SECONDS} seconds (6 hours).",
            )
            return
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="set_slowmode",
                channel_ids=(channel.id,),
                slowmode_seconds=seconds,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            if seconds == 0:
                await ctx.send(f'Slowmode disabled in "{channel.name}".')
            else:
                await ctx.send(f'Slowmode set to **{seconds}s** in "{channel.name}".')
        else:
            await ctx.send(
                f'❌ Could not set slowmode in "{channel.name}": '
                f"{self._channel_result_error(result)}",
            )

    @commands.command(
        name="topic",
        aliases=["settopic"],
        help="Set a channel's topic. Usage: !topic <name|id> <text> (omit text to clear)",
    )
    @is_admin_or_owner()
    async def set_topic(self, ctx, channel_name: str, *, text: str = ""):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if not channel:
            await ctx.send(f'"{channel_name}" not found.')
            return
        result = await ChannelLifecycleService().apply(
            ctx.guild,
            ChannelLifecycleRequest(
                operation="set_topic",
                channel_ids=(channel.id,),
                topic=text,
            ),
            ctx.author,
            actor_type="admin",
        )
        if result.outcome == SUCCESS:
            if text.strip():
                await ctx.send(f'Topic updated for "{channel.name}".')
            else:
                await ctx.send(f'Topic cleared for "{channel.name}".')
        else:
            await ctx.send(
                f'❌ Could not update topic for "{channel.name}": '
                f"{self._channel_result_error(result)}",
            )

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
        if not channel:
            await ctx.send(f'"{channel_name}" not found.')
            return
        act = action.lower()
        if act not in ("allow", "deny"):
            await ctx.send('Invalid action. Use "allow" or "deny".')
            return
        allow = act == "allow"
        word = "allowed" if allow else "denied"
        await self._apply_overwrite(
            ctx,
            (channel.id,),
            role.id,
            {"send_messages": allow},
            success=f'Send messages **{word}** for {role.name} in "{channel.name}".',
            fail_label=f'Could not update permissions in "{channel.name}"',
        )

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
        if not channel_names:
            await ctx.send("Please provide at least one channel name.")
            return

        result = await ChannelLifecycleService().create_channels(
            ctx.guild,
            channel_names,
            ctx.author,
            category_id=category.id if category else None,
            actor_type="admin",
        )
        created, failed = [], []
        for step in result.steps:
            if step.ok:
                made = ctx.guild.get_channel(step.target_id)
                actual = made.name if made else step.target_name
                suffix = f" (as {actual})" if actual != step.target_name else ""
                created.append(f"{step.target_name}{suffix}")
            else:
                failed.append(step.target_name)

        response = ""
        if created:
            response += f"✅ Created: {', '.join(created)}.\n"
        if failed:
            response += f"❌ Failed: {', '.join(failed)}."
        await ctx.send(response)


async def setup(bot):
    await bot.add_cog(ChannelCog(bot))
    logger.info("ChannelCog loaded.")
