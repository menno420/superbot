from __future__ import annotations
import discord
from discord.ext import commands
import logging
from utils.channels import safe_channel_name, get_or_create_category
from utils.helpers import CogMenuView

logger = logging.getLogger("bot")

_CHANNEL_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("channelmenu",    "!channelmenu",                              "Show this channel command menu."),
    ("list",           "!list",                                     "List all categories and channels, including uncategorized."),
    ("create",         "!create <name> <@role> <True/False> [cat]", "Create a channel with role access."),
    ("channelcreator", "!channelcreator",                           "Open the interactive channel management panel."),
    ("del",            "!del <name|id>",                            "Delete a specific channel."),
    ("move",           "!move <channel> <category>",                "Move a channel into a category."),
    ("lock",           "!lock <name|id>",                           "Lock a channel (no send messages)."),
    ("unlock",         "!unlock <name|id>",                         "Unlock a previously locked channel."),
    ("archive",        "!archive <name|id>",                        "Make a channel read-only."),
    ("rename",         "!rename <old> <new>",                       "Rename a channel."),
    ("channelinfo",    "!channelinfo <name|id>",                    "Show detailed info about a channel."),
    ("clone",          "!clone <name|id> <new_name>",               "Clone a channel with a new name."),
]

# Keyword presets shown in the dropdown menus
_NAME_PRESETS = [
    "general", "gaming", "announcements", "events",
    "tournament", "support", "bot-commands", "vc-lounge",
]
_CATEGORY_PRESETS = [
    "Gaming", "Community", "Events", "Tournaments", "Staff",
]


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
            return ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id
        return commands.check(predicate)

    def _resolve_channel(self, guild: discord.Guild, query: str):
        """Find a channel by name, mention (<#ID>), or numeric ID."""
        if query.startswith('<#') and query.endswith('>'):
            query = query[2:-1]
        if query.isdigit():
            ch = guild.get_channel(int(query))
            if ch:
                return ch
        return discord.utils.get(guild.channels, name=query)

    def _resolve_category(self, guild: discord.Guild, query: str):
        """Find a category by name, mention, or numeric ID."""
        if query.startswith('<#') and query.endswith('>'):
            query = query[2:-1]
        if query.isdigit():
            ch = guild.get_channel(int(query))
            if isinstance(ch, discord.CategoryChannel):
                return ch
        return discord.utils.get(guild.categories, name=query)

    def get_category_or_channel(self, guild, query):
        return self._resolve_category(guild, query) or self._resolve_channel(guild, query)

    async def set_permissions(self, target, role, read_messages):
        if isinstance(target, discord.CategoryChannel):
            for channel in target.channels:
                await channel.set_permissions(role, read_messages=read_messages)
        elif isinstance(target, (discord.TextChannel, discord.VoiceChannel)):
            await target.set_permissions(role, read_messages=read_messages)

    def format_overwrites(self, overwrites):
        formatted = ""
        for target, perms in overwrites.items():
            name = (target.name if isinstance(target, discord.Role)
                    else target.display_name if isinstance(target, discord.Member)
                    else "Unknown")
            allow = ", ".join([p.replace("_", " ").title() for p, v in iter(perms) if v is True])
            deny  = ", ".join([p.replace("_", " ").title() for p, v in iter(perms) if v is False])
            formatted += f"**{name}**\nAllowed: {allow or 'None'}\nDenied: {deny or 'None'}\n\n"
        return formatted or "No overwrites."

    # -------------------
    # Commands
    # -------------------

    @commands.command(name="channelmenu", help="Show the channel command quick-reference menu.")
    @is_admin_or_owner()
    async def channel_menu(self, ctx):
        """Show a quick-reference menu for all channel commands."""
        view = CogMenuView(ctx, "📋 Channel Commands", _CHANNEL_MENU_COMMANDS)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="set", help="Set access for a channel/category. Usage: !set <name|id> <@role> <True/False>")
    @is_admin_or_owner()
    async def set_access(self, ctx, target: str, role: discord.Role, permission: bool):
        target_channel = self.get_category_or_channel(ctx.guild, target)
        if target_channel:
            await self.set_permissions(target_channel, role, read_messages=permission)
            state = "opened" if permission else "closed"
            await ctx.send(f'{target_channel.type} "{target_channel.name}" {state} for {role.name}!')
        else:
            await ctx.send(f'Channel or Category "{target}" not found.')

    @commands.command(name="evt", help="Create or delete an event channel. Usage: !evt <name|id> <create/delete>")
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

    @commands.command(name="create", help="Create a channel with role access. Usage: !create <name> <@role> <True/False> [category]")
    @is_admin_or_owner()
    async def create_channel_with_role(self, ctx, channel_name: str, role: discord.Role,
                                       permission: bool, category_name: str = None):
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
        await ctx.send(f'Channel "{safe_name}" created with {state} access for {role.name}!{suffix}')

    @commands.command(name="channelcreator", aliases=["ccreate"],
                      help="Open the comprehensive channel management panel.")
    @is_admin_or_owner()
    async def channel_creator(self, ctx):
        """Opens the comprehensive channel management panel."""
        view = _ChannelManagerView(ctx)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="bulkdelete", help="Delete multiple channels. Usage: !bulkdelete <name|id> [name|id...] or <keyword>")
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
                channels_to_delete = [ch for ch in ctx.guild.channels if word in ch.name]
                if not channels_to_delete:
                    await ctx.send(f"No channels found matching '{word}'.")
                    return
        else:
            channels_to_delete = [self._resolve_channel(ctx.guild, n)
                                   for n in channel_names_or_word]

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
        if deleted: response += f'✅ Deleted: {", ".join(deleted)}.\n'
        if failed:  response += f'❌ Failed: {", ".join(failed)}.'
        await ctx.send(response)

    @commands.command(name="del", help="Delete a specific channel. Usage: !del <name|id>")
    @is_admin_or_owner()
    async def delete_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.delete()
            await ctx.send(f'Channel "{channel.name}" deleted.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(name="list", help="List all categories and channels, including uncategorized.")
    @is_admin_or_owner()
    async def list_channels(self, ctx):
        embed = discord.Embed(title="Categories and Channels", color=discord.Color.blue())
        for category in ctx.guild.categories:
            channels = "\n".join(f" - {ch.name}" for ch in category.channels)
            embed.add_field(name=category.name, value=channels or "No channels", inline=False)
        uncategorized = [ch for ch in ctx.guild.channels if ch.category is None and not isinstance(ch, discord.CategoryChannel)]
        if uncategorized:
            names = "\n".join(f" - {ch.name}" for ch in sorted(uncategorized, key=lambda c: c.position))
            embed.add_field(name="— Uncategorized —", value=names, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="clone", help="Clone a channel. Usage: !clone <name|id> <new_name>")
    @is_admin_or_owner()
    async def clone_channel(self, ctx, existing_channel_name: str, new_channel_name: str):
        existing = self._resolve_channel(ctx.guild, existing_channel_name)
        if existing:
            await existing.clone(name=new_channel_name)
            await ctx.send(f'"{existing.name}" cloned as "{new_channel_name}".')
        else:
            await ctx.send(f'"{existing_channel_name}" not found.')

    @commands.command(name="move", help="Move a channel to a category. Usage: !move <channel name|id> <category name|id>")
    @is_admin_or_owner()
    async def move_channel(self, ctx, channel_name: str, category_name: str):
        channel  = self._resolve_channel(ctx.guild, channel_name)
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

    @commands.command(name="channelinfo", help="Channel details. Usage: !channelinfo <name|id>")
    @is_admin_or_owner()
    async def channel_info(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            embed = discord.Embed(title=f"Channel Info — {channel.name}", color=discord.Color.orange())
            embed.add_field(name="Type",      value=str(channel.type),                    inline=True)
            embed.add_field(name="Category",  value=channel.category.name if channel.category else "None", inline=True)
            embed.add_field(name="Position",  value=str(channel.position),                inline=True)
            embed.add_field(name="Topic",     value=getattr(channel, "topic", None) or "No topic set.", inline=False)
            embed.add_field(name="Created",   value=channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            embed.add_field(name="ID",        value=str(channel.id),                      inline=True)
            embed.add_field(name="Overwrites", value=self.format_overwrites(channel.overwrites), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(name="rename", help="Rename a channel. Usage: !rename <old name|id> <new_name>")
    @is_admin_or_owner()
    async def rename_channel(self, ctx, old_name: str, new_name: str):
        channel = self._resolve_channel(ctx.guild, old_name)
        if channel:
            old = channel.name
            await channel.edit(name=new_name)
            await ctx.send(f'"{old}" renamed to "{new_name}".')
        else:
            await ctx.send(f'"{old_name}" not found.')

    @commands.command(name="permissions", help="Modify channel permissions. Usage: !permissions <name|id> <@role> <allow/deny>")
    @is_admin_or_owner()
    async def modify_permissions(self, ctx, channel_name: str, role: discord.Role, action: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            if action.lower() == "allow":
                await channel.set_permissions(role, send_messages=True)
                await ctx.send(f'Send messages **allowed** for {role.name} in "{channel.name}".')
            elif action.lower() == "deny":
                await channel.set_permissions(role, send_messages=False)
                await ctx.send(f'Send messages **denied** for {role.name} in "{channel.name}".')
            else:
                await ctx.send('Invalid action. Use "allow" or "deny".')
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(name="bulkcreate", help="Create multiple channels. Usage: !bulkcreate <ch1> [ch2...] [category]")
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
        if created: response += f'✅ Created: {", ".join(created)}.\n'
        if failed:  response += f'❌ Failed: {", ".join(failed)}.'
        await ctx.send(response)

    @commands.command(name="archive", help="Make a channel read-only. Usage: !archive <name|id>")
    @is_admin_or_owner()
    async def archive_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f'"{channel.name}" archived (read-only).')
        else:
            await ctx.send(f'"{channel_name}" not found.')

    @commands.command(name="unarchive", help="Restore send permissions for a channel. Usage: !unarchive <name|id>")
    @is_admin_or_owner()
    async def unarchive_channel(self, ctx, channel_name: str):
        channel = self._resolve_channel(ctx.guild, channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send(f'"{channel.name}" unarchived.')
        else:
            await ctx.send(f'"{channel_name}" not found.')


# =====================================================================
# Shared helpers
# =====================================================================

def _build_channel_options(guild: discord.Guild) -> list[discord.SelectOption]:
    """Return up to 25 SelectOptions for all text + voice channels, sorted by name."""
    channels = sorted(
        [ch for ch in guild.channels
         if isinstance(ch, (discord.TextChannel, discord.VoiceChannel))],
        key=lambda c: c.name,
    )
    options = []
    for ch in channels[:25]:
        emoji = "🔊" if isinstance(ch, discord.VoiceChannel) else "#"
        cat_label = ch.category.name if ch.category else "No category"
        options.append(discord.SelectOption(
            label=ch.name[:100],
            value=str(ch.id),
            description=f"{cat_label}"[:100],
            emoji=emoji,
        ))
    return options


# =====================================================================
# Top-level manager panel
# =====================================================================

class _ChannelManagerView(discord.ui.View):
    """Top-level channel management panel with three action modes."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message: discord.Message | None = None

    # ------------------------------------------------------------------
    # Auth guard
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("ChannelManagerView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Embed
    # ------------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🛠️ Channel Management Panel",
            description=(
                "Select an action below to manage your server's channels.\n\n"
                "**➕ Create Channel** — interactive channel creator\n"
                "**🗑️ Delete Channel** — select and delete a channel\n"
                "**🔒 Manage Restrictions** — lock, unlock, archive, or unarchive"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Only the command author can interact with this panel.")
        return embed

    # ------------------------------------------------------------------
    # Buttons (row 0)
    # ------------------------------------------------------------------

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.green,
                       emoji="➕", row=0)
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        sub = _CreateSubView(self.ctx, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.red,
                       emoji="🗑️", row=0)
    async def delete_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        options = _build_channel_options(interaction.guild)
        if not options:
            await interaction.response.send_message(
                "No text or voice channels found on this server.", ephemeral=True)
            return
        sub = _DeleteSubView(self.ctx, options=options, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    @discord.ui.button(label="Manage Restrictions", style=discord.ButtonStyle.blurple,
                       emoji="🔒", row=0)
    async def restrict_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        options = _build_channel_options(interaction.guild)
        if not options:
            await interaction.response.send_message(
                "No text or voice channels found on this server.", ephemeral=True)
            return
        sub = _RestrictSubView(self.ctx, options=options, manager_message=self.message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Panel timed out.", view=self)
        except Exception:
            pass


# =====================================================================
# Create sub-panel  (same logic as the old _ChannelCreatorView)
# =====================================================================

class _CreateSubView(discord.ui.View):
    """Channel-creation sub-panel — mirrors the old _ChannelCreatorView."""

    def __init__(self, ctx: commands.Context, *, manager_message: discord.Message | None):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.chosen_name: str | None = None
        self.chosen_cat:  str | None = None

        # Category options: existing guild categories first, then presets
        existing_cats = [c.name for c in ctx.guild.categories]
        cat_options = [
            discord.SelectOption(label=c, description="Existing category")
            for c in existing_cats[:15]
        ]
        for p in _CATEGORY_PRESETS:
            if p not in existing_cats and len(cat_options) < 24:
                cat_options.append(discord.SelectOption(label=p, description="New category"))
        if not cat_options:
            cat_options = [discord.SelectOption(label=p) for p in _CATEGORY_PRESETS]

        self.name_select = _NameSelect(_NAME_PRESETS, self)
        self.cat_select  = _CategorySelect(cat_options, self)
        self.add_item(self.name_select)
        self.add_item(self.cat_select)

    # ------------------------------------------------------------------
    # Auth guard
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("CreateSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Embed
    # ------------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="➕ Create Channel",
            description=(
                "Use the menus below to pick a name and category.\n"
                "Click **Custom Name** to type your own name."
            ),
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Selected name",
            value=f"`{self.chosen_name}`" if self.chosen_name else "*(none)*",
            inline=True,
        )
        embed.add_field(
            name="Selected category",
            value=f"`{self.chosen_cat}`" if self.chosen_cat else "*(none)*",
            inline=True,
        )
        return embed

    # ------------------------------------------------------------------
    # Buttons (row 2)
    # ------------------------------------------------------------------

    @discord.ui.button(label="Custom Name", style=discord.ButtonStyle.grey, emoji="✏️", row=2)
    async def custom_name_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_CustomNameModal(self))

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.green, emoji="✅", row=2)
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.chosen_name:
            await interaction.response.send_message(
                "Please select or enter a channel name first.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        safe  = await safe_channel_name(guild, self.chosen_name)
        category = None
        if self.chosen_cat:
            try:
                category = await get_or_create_category(guild, self.chosen_cat)
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I don't have permission to create categories.", ephemeral=True)
                return
            except discord.HTTPException as exc:
                await interaction.followup.send(
                    f"❌ Failed to create category: {exc}", ephemeral=True)
                return

        try:
            ch = await guild.create_text_channel(safe, category=category)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create channels.", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"❌ Failed to create channel: {exc}", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        suffix = f' (renamed from "{self.chosen_name}")' if safe != self.chosen_name else ""
        embed = discord.Embed(
            title="✅ Channel Created",
            description=(
                f"{ch.mention} created"
                + (f" in **{self.chosen_cat}**" if self.chosen_cat else "")
                + suffix
                + "\n\nReturning to the management panel…"
            ),
            color=discord.Color.green(),
        )
        try:
            await self.manager_message.edit(embed=embed, view=self)
        except Exception:
            await interaction.followup.send(
                f"✅ Channel {ch.mention} created!"
                + (f" in **{self.chosen_cat}**" if self.chosen_cat else ""),
                ephemeral=True,
            )

        self.stop()

        # After a brief visual pause, restore the manager panel
        import asyncio
        await asyncio.sleep(2)
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        try:
            await self.manager_message.edit(embed=manager.build_embed(), view=manager)
        except Exception:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌", row=2)
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(embed=manager.build_embed(), view=manager)
        self.stop()

    @discord.ui.button(label="↩️ Back", style=discord.ButtonStyle.grey, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(embed=manager.build_embed(), view=manager)
        self.stop()

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.manager_message.edit(content="Panel timed out.", view=self)
        except Exception:
            pass


# =====================================================================
# Delete sub-panel
# =====================================================================

class _DeleteSubView(discord.ui.View):
    """Channel-deletion sub-panel with a select menu and confirmation flow."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        options: list[discord.SelectOption],
        manager_message: discord.Message | None,
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_id: int | None = None
        self.selected_channel_name: str | None = None

        self.channel_select = _ChannelSelect(options, self, placeholder="Select a channel to delete…")
        self.add_item(self.channel_select)

    # ------------------------------------------------------------------
    # Auth guard
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("DeleteSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Embed
    # ------------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🗑️ Delete Channel",
            description="Select the channel you want to delete, then press **Delete Selected**.",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="Selected channel",
            value=f"`{self.selected_channel_name}`" if self.selected_channel_name else "*(none)*",
            inline=False,
        )
        return embed

    def _confirm_embed(self) -> discord.Embed:
        return discord.Embed(
            title="⚠️ Confirm Deletion",
            description=(
                f"Are you sure you want to delete **`{self.selected_channel_name}`**?\n"
                "**This action cannot be undone.**"
            ),
            color=discord.Color.dark_red(),
        )

    # ------------------------------------------------------------------
    # Buttons (row 1)
    # ------------------------------------------------------------------

    @discord.ui.button(label="Delete Selected", style=discord.ButtonStyle.red, emoji="🗑️", row=1)
    async def delete_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.selected_channel_id:
            await interaction.response.send_message(
                "Please select a channel first.", ephemeral=True)
            return
        confirm_view = _DeleteConfirmView(
            self.ctx,
            channel_id=self.selected_channel_id,
            channel_name=self.selected_channel_name,
            manager_message=self.manager_message,
        )
        await interaction.response.edit_message(embed=self._confirm_embed(), view=confirm_view)
        self.stop()

    @discord.ui.button(label="↩️ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(embed=manager.build_embed(), view=manager)
        self.stop()

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.manager_message.edit(content="Panel timed out.", view=self)
        except Exception:
            pass


class _DeleteConfirmView(discord.ui.View):
    """Confirmation step before actually deleting a channel."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        channel_id: int,
        channel_name: str,
        manager_message: discord.Message | None,
    ):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.manager_message = manager_message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("DeleteConfirmView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.red, emoji="🗑️", row=0)
    async def confirm_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel is None:
            result_embed = discord.Embed(
                title="❌ Channel Not Found",
                description=f"Channel `{self.channel_name}` could not be found — it may have already been deleted.",
                color=discord.Color.orange(),
            )
        else:
            try:
                await channel.delete()
                result_embed = discord.Embed(
                    title="✅ Channel Deleted",
                    description=f"`{self.channel_name}` has been deleted.",
                    color=discord.Color.green(),
                )
            except discord.Forbidden:
                result_embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="I don't have permission to delete that channel.",
                    color=discord.Color.red(),
                )
            except discord.HTTPException as exc:
                result_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to delete channel: {exc}",
                    color=discord.Color.red(),
                )

        for item in self.children:
            item.disabled = True
        result_embed.set_footer(text="Returning to the management panel…")
        await interaction.response.edit_message(embed=result_embed, view=self)
        self.stop()

        import asyncio
        await asyncio.sleep(2)
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        try:
            await self.manager_message.edit(embed=manager.build_embed(), view=manager)
        except Exception:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, emoji="❌", row=0)
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Go back to the delete sub-panel
        options = _build_channel_options(interaction.guild)
        sub = _DeleteSubView(self.ctx, options=options, manager_message=self.manager_message)
        await interaction.response.edit_message(embed=sub.build_embed(), view=sub)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.manager_message.edit(content="Panel timed out.", view=self)
        except Exception:
            pass


# =====================================================================
# Restrict sub-panel
# =====================================================================

class _RestrictSubView(discord.ui.View):
    """Restriction management: pick a channel, then choose lock/unlock/archive/unarchive."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        options: list[discord.SelectOption],
        manager_message: discord.Message | None,
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        self.selected_channel_id: int | None = None
        self.selected_channel_name: str | None = None

        self.channel_select = _ChannelSelect(options, self, placeholder="Select a channel to manage…")
        self.add_item(self.channel_select)

    # ------------------------------------------------------------------
    # Auth guard
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    _run_checks = interaction_check

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("RestrictSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Embed
    # ------------------------------------------------------------------

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔒 Manage Restrictions",
            description=(
                "Select a channel, then choose a restriction action.\n\n"
                "**🔒 Lock** — disable send messages for @everyone\n"
                "**🔓 Unlock** — restore send messages for @everyone\n"
                "**📁 Archive** — make the channel read-only\n"
                "**📂 Unarchive** — restore send messages (same as unlock)"
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Selected channel",
            value=f"`{self.selected_channel_name}`" if self.selected_channel_name else "*(none)*",
            inline=False,
        )
        return embed

    # ------------------------------------------------------------------
    # Action buttons (row 1) — shown only after a channel is selected
    # ------------------------------------------------------------------

    async def _apply_restriction(
        self,
        interaction: discord.Interaction,
        *,
        send_messages: bool,
        action_label: str,
        past_tense: str,
        embed_color: discord.Color,
    ) -> None:
        if not self.selected_channel_id:
            await interaction.response.send_message(
                "Please select a channel first.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(self.selected_channel_id)
        if channel is None:
            await interaction.response.send_message(
                f"Channel `{self.selected_channel_name}` not found.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=send_messages)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to change that channel's permissions.", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"❌ Failed to update permissions: {exc}", ephemeral=True)
            return

        result_embed = discord.Embed(
            title=f"{action_label} Applied",
            description=f"`{self.selected_channel_name}` has been {past_tense}.",
            color=embed_color,
        )
        result_embed.set_footer(text="Returning to the management panel…")

        for item in self.children:
            item.disabled = True

        try:
            await self.manager_message.edit(embed=result_embed, view=self)
        except Exception:
            pass
        self.stop()

        import asyncio
        await asyncio.sleep(2)
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        try:
            await self.manager_message.edit(embed=manager.build_embed(), view=manager)
        except Exception:
            pass

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, emoji="🔒", row=1)
    async def lock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=False,
            action_label="🔒 Lock",
            past_tense="locked (send messages disabled for @everyone)",
            embed_color=discord.Color.red(),
        )

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, emoji="🔓", row=1)
    async def unlock_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=True,
            action_label="🔓 Unlock",
            past_tense="unlocked (send messages restored for @everyone)",
            embed_color=discord.Color.green(),
        )

    @discord.ui.button(label="Archive", style=discord.ButtonStyle.grey, emoji="📁", row=1)
    async def archive_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=False,
            action_label="📁 Archive",
            past_tense="archived (read-only)",
            embed_color=discord.Color.greyple(),
        )

    @discord.ui.button(label="Unarchive", style=discord.ButtonStyle.grey, emoji="📂", row=1)
    async def unarchive_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._apply_restriction(
            interaction,
            send_messages=True,
            action_label="📂 Unarchive",
            past_tense="unarchived (send messages restored for @everyone)",
            embed_color=discord.Color.green(),
        )

    @discord.ui.button(label="↩️ Back", style=discord.ButtonStyle.grey, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(embed=manager.build_embed(), view=manager)
        self.stop()

    # ------------------------------------------------------------------
    # Timeout
    # ------------------------------------------------------------------

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.manager_message.edit(content="Panel timed out.", view=self)
        except Exception:
            pass


# =====================================================================
# Shared Select components
# =====================================================================

class _ChannelSelect(discord.ui.Select):
    """Generic channel select used by Delete and Restrict sub-panels."""

    def __init__(self, options: list[discord.SelectOption], parent_view, *, placeholder: str):
        super().__init__(
            placeholder=placeholder,
            min_values=1, max_values=1,
            options=options,
            row=0,
        )
        self._parent = parent_view

    async def callback(self, interaction: discord.Interaction):
        self._parent.selected_channel_id = int(self.values[0])
        # Resolve the display name from the options list
        chosen_opt = next((o for o in self.options if o.value == self.values[0]), None)
        self._parent.selected_channel_name = chosen_opt.label if chosen_opt else self.values[0]
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(), view=self._parent)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()


class _NameSelect(discord.ui.Select):
    """Name preset picker used by _CreateSubView."""

    def __init__(self, presets: list[str], view):
        options = [discord.SelectOption(label=p, value=p) for p in presets]
        super().__init__(
            placeholder="Pick a channel name…",
            min_values=1, max_values=1,
            options=options,
            row=0,
        )
        self._parent = view

    async def callback(self, interaction: discord.Interaction):
        self._parent.chosen_name = self.values[0]
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(), view=self._parent)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()


class _CategorySelect(discord.ui.Select):
    """Category picker used by _CreateSubView."""

    def __init__(self, options: list[discord.SelectOption], view):
        super().__init__(
            placeholder="Pick a category…",
            min_values=1, max_values=1,
            options=options,
            row=1,
        )
        self._parent = view

    async def callback(self, interaction: discord.Interaction):
        self._parent.chosen_cat = self.values[0]
        try:
            await interaction.response.edit_message(
                embed=self._parent.build_embed(), view=self._parent)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()


class _CustomNameModal(discord.ui.Modal, title="Custom Channel Name"):
    channel_name = discord.ui.TextInput(
        label="Channel name",
        placeholder="e.g. my-channel",
        max_length=100,
    )

    def __init__(self, view: _CreateSubView):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        name = self.channel_name.value.strip().lower().replace(" ", "-")
        self._view.chosen_name = name
        await interaction.response.defer()
        if self._view.manager_message:
            await self._view.manager_message.edit(
                embed=self._view.build_embed(), view=self._view)


# =====================================================================
# Cog Setup
# =====================================================================

async def setup(bot):
    await bot.add_cog(ChannelCog(bot))
    logger.info("ChannelCog loaded.")
