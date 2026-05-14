from __future__ import annotations
import discord
from discord.ext import commands
import logging
from utils.channels import safe_channel_name, get_or_create_category

logger = logging.getLogger("bot")

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
                      help="Open the interactive channel creator UI.")
    @is_admin_or_owner()
    async def channel_creator(self, ctx):
        """Opens a button/dropdown panel for creating a channel."""
        view = _ChannelCreatorView(ctx)
        embed = discord.Embed(
            title="📋 Channel Creator",
            description=(
                "Use the menus below to pick a name and category for the new channel.\n"
                "You can also type a custom name via the **Custom Name** button."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Selected name",     value="*(none)*", inline=True)
        embed.add_field(name="Selected category", value="*(none)*", inline=True)
        msg = await ctx.send(embed=embed, view=view)
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

    @commands.command(name="list", help="List all categories and channels.")
    @is_admin_or_owner()
    async def list_channels(self, ctx):
        embed = discord.Embed(title="Categories and Channels", color=discord.Color.blue())
        for category in ctx.guild.categories:
            channels = "\n".join(f" - {ch.name}" for ch in category.channels)
            embed.add_field(name=category.name, value=channels or "No channels", inline=False)
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


# -------------------
# Channel Creator UI
# -------------------

class _ChannelCreatorView(discord.ui.View):
    """Interactive channel creation panel with dropdown name/category pickers."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=120)
        self.ctx          = ctx
        self.chosen_name: str | None  = None
        self.chosen_cat:  str | None  = None
        self.message: discord.Message | None = None

        # Build category select: existing ones first, then presets not yet in guild
        existing_cats = [c.name for c in ctx.guild.categories]
        cat_options = [discord.SelectOption(label=c, description="Existing category")
                       for c in existing_cats[:15]]  # cap to avoid Discord limit
        for p in _CATEGORY_PRESETS:
            if p not in existing_cats and len(cat_options) < 24:
                cat_options.append(discord.SelectOption(label=p, description="New category"))
        if not cat_options:
            cat_options = [discord.SelectOption(label=p) for p in _CATEGORY_PRESETS]

        self.name_select = _NameSelect(_NAME_PRESETS, self)
        self.cat_select  = _CategorySelect(cat_options, self)
        self.add_item(self.name_select)
        self.add_item(self.cat_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This panel isn't for you.", ephemeral=True)
            return False
        return True

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("ChannelCreatorView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 Channel Creator",
            description=(
                "Use the menus below to pick a name and category.\n"
                "Click **Custom Name** to type your own name."
            ),
            color=discord.Color.blurple(),
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

    @discord.ui.button(label="Custom Name", style=discord.ButtonStyle.grey, emoji="✏️", row=2)
    async def custom_name_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_CustomNameModal(self))

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.green, emoji="✅", row=2)
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not self.chosen_name:
            await interaction.response.send_message(
                "Please select or enter a channel name first.", ephemeral=True)
            return

        # Defer immediately — Discord requires acknowledgement within 3 seconds.
        # ephemeral=True keeps the follow-up visible only to the invoker.
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
            description=f"{ch.mention} created" + (f" in **{self.chosen_cat}**" if self.chosen_cat else "") + suffix,
            color=discord.Color.green(),
        )
        # Update the panel embed; if it fails (e.g. message deleted) still confirm via followup
        try:
            await self.message.edit(embed=embed, view=self)
        except Exception:
            await interaction.followup.send(
                f"✅ Channel {ch.mention} created!" + (f" in **{self.chosen_cat}**" if self.chosen_cat else ""),
                ephemeral=True,
            )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌", row=2)
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=self)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(content="Timed out.", view=self)
        except Exception:
            pass


class _NameSelect(discord.ui.Select):
    def __init__(self, presets: list[str], view: _ChannelCreatorView):
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
                embed=self._parent._build_embed(), view=self._parent)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()


class _CategorySelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], view: _ChannelCreatorView):
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
                embed=self._parent._build_embed(), view=self._parent)
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer()


class _CustomNameModal(discord.ui.Modal, title="Custom Channel Name"):
    channel_name = discord.ui.TextInput(
        label="Channel name",
        placeholder="e.g. my-channel",
        max_length=100,
    )

    def __init__(self, view: _ChannelCreatorView):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        name = self.channel_name.value.strip().lower().replace(" ", "-")
        self._view.chosen_name = name
        await interaction.response.defer()
        if self._view.message:
            await self._view.message.edit(
                embed=self._view._build_embed(), view=self._view)


# -------------------
# Cog Setup
# -------------------

async def setup(bot):
    await bot.add_cog(ChannelCog(bot))
    logger.info("ChannelCog loaded.")
