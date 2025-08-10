import discord
from discord.ext import commands
import logging

# Retrieve the existing logger from the main bot script
logger = logging.getLogger('discord_bot.channel_cog')

class ChannelCog(commands.Cog):
    """A cog for managing Discord channels and categories."""

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

    def get_category_or_channel(self, guild, name):
        """Retrieve a category or channel by name."""
        return discord.utils.get(guild.categories, name=name) or discord.utils.get(guild.channels, name=name)

    async def set_permissions(self, target, role, read_messages):
        """Set read permissions for a role in a channel or category."""
        if isinstance(target, discord.CategoryChannel):
            for channel in target.channels:
                await channel.set_permissions(role, read_messages=read_messages)
        elif isinstance(target, (discord.TextChannel, discord.VoiceChannel)):
            await target.set_permissions(role, read_messages=read_messages)

    def format_overwrites(self, overwrites):
        """Format channel permission overwrites into a readable string for embeds."""
        formatted = ""
        for target, perms in overwrites.items():
            if isinstance(target, discord.Role):
                name = target.name
            elif isinstance(target, discord.Member):
                name = target.display_name
            else:
                name = "Unknown"

            allow = ", ".join([perm.replace("_", " ").title() for perm, value in perms if value])
            deny = ", ".join([perm.replace("_", " ").title() for perm, value in perms if not value])

            formatted += f"**{name}**\nAllowed: {allow if allow else 'None'}\nDenied: {deny if deny else 'None'}\n\n"

        return formatted if formatted else "No overwrites."

    # -------------------
    # Commands
    # -------------------

    @commands.command(
        name='set',
        help='Set access for a channel or category. Usage: .set <target> <@role> <True/False>'
    )
    @is_admin_or_owner()
    async def set_access(self, ctx, target: str, role: discord.Role, permission: bool):
        target_channel = self.get_category_or_channel(ctx.guild, target)
        if target_channel:
            await self.set_permissions(target_channel, role, read_messages=permission)
            state = 'opened' if permission else 'closed'
            await ctx.send(f'{target_channel.type.capitalize()} "{target}" {state} for {role.name}!')
        else:
            await ctx.send(f'Channel or Category "{target}" not found.')

    @commands.command(
        name='evt',
        help='Create or delete an event. Usage: .evt <event_name> <create/delete>'
    )
    @is_admin_or_owner()
    async def manage_event(self, ctx, evt: str, action: str):
        category = discord.utils.get(ctx.guild.categories, name="Events")
        if action.lower() == 'create':
            if not category:
                category = await ctx.guild.create_category("Events")
            channel = discord.utils.get(ctx.guild.channels, name=evt)
            if not channel:
                await ctx.guild.create_text_channel(evt, category=category)
                await ctx.send(f'Event "{evt}" created!')
            else:
                await ctx.send(f'Event "{evt}" already exists!')
        elif action.lower() == 'delete':
            channel = discord.utils.get(ctx.guild.channels, name=evt)
            if channel:
                await channel.delete()
                await ctx.send(f'Event "{evt}" deleted!')
            else:
                await ctx.send(f'Event "{evt}" not found.')
        else:
            await ctx.send('Invalid action. Use "create" or "delete".')

    @commands.command(
        name='create',
        help='Create a channel with role access. Usage: .create <channel_name> <@role> <True/False> [category]'
    )
    @is_admin_or_owner()
    async def create_channel_with_role(
        self,
        ctx,
        channel_name: str,
        role: discord.Role,
        permission: bool,
        category_name: str = None
    ):
        existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if existing_channel:
            await ctx.send(f'Channel "{channel_name}" already exists!')
            return

        category = self.get_category_or_channel(ctx.guild, category_name) if category_name else None
        if category_name and not category:
            await ctx.send(f'Category "{category_name}" not found!')
            return

        new_channel = await ctx.guild.create_text_channel(channel_name, category=category)
        await new_channel.set_permissions(role, read_messages=permission)
        state = 'granted' if permission else 'restricted'
        await ctx.send(f'Channel "{channel_name}" created with {state} access for {role.name}!')

    @commands.command(
        name='bulkdelete',
        help='Delete multiple channels. Usage: .bulkdelete <channel_name1> <channel_name2> ... or <word>'
    )
    @is_admin_or_owner()
    async def bulk_delete_channels(self, ctx, *channel_names_or_word: str):
        if not channel_names_or_word:
            await ctx.send("Please provide at least one channel name or a word.")
            return

        deleted = []
        failed = []

        if len(channel_names_or_word) == 1:
            word = channel_names_or_word[0]
            channels_to_delete = [channel for channel in ctx.guild.channels if word in channel.name]
            if not channels_to_delete:
                await ctx.send(f"No channels found containing the word '{word}'.")
                return
        else:
            channels_to_delete = [
                discord.utils.get(ctx.guild.channels, name=name) for name in channel_names_or_word
            ]

        for channel in channels_to_delete:
            if channel:
                try:
                    await channel.delete()
                    deleted.append(channel.name)
                except Exception as e:
                    failed.append(channel.name)
            else:
                failed.append('Not found')

        response = ""
        if deleted:
            response += f'✅ Deleted channels: {", ".join(deleted)}.\n'
        if failed:
            response += f'❌ Failed to delete channels: {", ".join(failed)}.'

        await ctx.send(response)

    @commands.command(
        name='del',
        help='Delete a specific channel. Usage: .del <channel_name>'
    )
    @is_admin_or_owner()
    async def delete_channel(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            await channel.delete()
            await ctx.send(f'Channel "{channel_name}" has been deleted.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='list',
        help='List all categories and channels. Usage: .list'
    )
    @is_admin_or_owner()
    async def list_channels(self, ctx):
        embed = discord.Embed(
            title="Categories and Channels",
            description="Here are all the categories and their channels:",
            color=discord.Color.blue()
        )
        for category in ctx.guild.categories:
            channels = '\n'.join([f" - {channel.name}" for channel in category.channels])
            embed.add_field(
                name=category.name,
                value=channels if channels else "No channels",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(
        name='clone',
        help='Clone a channel. Usage: .clone <existing_channel_name> <new_channel_name>'
    )
    @is_admin_or_owner()
    async def clone_channel(self, ctx, existing_channel_name: str, new_channel_name: str):
        existing_channel = discord.utils.get(ctx.guild.channels, name=existing_channel_name)
        if existing_channel:
            await existing_channel.clone(name=new_channel_name)
            await ctx.send(f'Channel "{existing_channel_name}" cloned as "{new_channel_name}".')
        else:
            await ctx.send(f'Channel "{existing_channel_name}" not found.')

    @commands.command(
        name='move',
        help='Move a channel to a category. Usage: .move <channel_name> <category_name>'
    )
    @is_admin_or_owner()
    async def move_channel(self, ctx, channel_name: str, category_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        category = discord.utils.get(ctx.guild.categories, name=category_name)
        if channel and category:
            await channel.edit(category=category)
            await ctx.send(f'Channel "{channel_name}" moved to category "{category_name}".')
        else:
            await ctx.send(f'Channel or Category not found.')

    @commands.command(
        name='lock',
        help='Lock a channel (restrict send messages for @everyone). Usage: .lock <channel_name>'
    )
    @is_admin_or_owner()
    async def lock_channel(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f'Channel "{channel_name}" has been locked.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='unlock',
        help='Unlock a channel (grant send messages for @everyone). Usage: .unlock <channel_name>'
    )
    @is_admin_or_owner()
    async def unlock_channel(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send(f'Channel "{channel_name}" has been unlocked.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='channelinfo',
        help='Provides detailed information about a specific channel. Usage: .channelinfo <channel_name>'
    )
    @is_admin_or_owner()
    async def channel_info(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            embed = discord.Embed(
                title=f"Channel Information - {channel.name}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Type", value=channel.type.capitalize(), inline=True)
            embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
            embed.add_field(name="Position", value=str(channel.position), inline=True)
            embed.add_field(name="Topic", value=channel.topic if channel.topic else "No topic set.", inline=False)
            embed.add_field(name="Created At", value=channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            embed.add_field(name="Permissions Overwrites", value=self.format_overwrites(channel.overwrites), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='rename',
        help='Rename an existing channel. Usage: .rename <channel_name> <new_name>'
    )
    @is_admin_or_owner()
    async def rename_channel(self, ctx, old_name: str, new_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=old_name)
        if channel:
            await channel.edit(name=new_name)
            await ctx.send(f'Channel "{old_name}" has been renamed to "{new_name}".')
        else:
            await ctx.send(f'Channel "{old_name}" not found.')

    @commands.command(
        name='permissions',
        help='Modify permissions for a role in a channel. Usage: .permissions <channel_name> <@role> <allow/deny>'
    )
    @is_admin_or_owner()
    async def modify_permissions(self, ctx, channel_name: str, role: discord.Role, action: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            if action.lower() == 'allow':
                await channel.set_permissions(role, send_messages=True)
                await ctx.send(f'Send messages permission **allowed** for {role.name} in "{channel_name}".')
            elif action.lower() == 'deny':
                await channel.set_permissions(role, send_messages=False)
                await ctx.send(f'Send messages permission **denied** for {role.name} in "{channel_name}".')
            else:
                await ctx.send('Invalid action. Use "allow" or "deny".')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='bulkcreate',
        help='Create multiple channels at once. Usage: .bulkcreate <channel1> <channel2> ... [category]'
    )
    @is_admin_or_owner()
    async def bulk_create_channels(self, ctx, *args):
        if not args:
            await ctx.send("Please provide at least one channel name.")
            return

        category_name = None
        channel_names = list(args)
        potential_category = self.get_category_or_channel(ctx.guild, args[-1])
        if isinstance(potential_category, discord.CategoryChannel):
            category_name = args[-1]
            channel_names = list(args[:-1])

        category = discord.utils.get(ctx.guild.categories, name=category_name) if category_name else None
        if category_name and not category:
            await ctx.send(f'Category "{category_name}" not found!')
            return

        created = []
        failed = []

        for ch in channel_names:
            existing_channel = discord.utils.get(ctx.guild.channels, name=ch)
            if existing_channel:
                failed.append(f'"{ch}" already exists.')
                continue
            try:
                await ctx.guild.create_text_channel(ch, category=category)
                created.append(ch)
            except Exception as e:
                failed.append(f'"{ch}" failed to create.')

        response = ""
        if created:
            response += f'✅ Created channels: {", ".join(created)}.\n'
        if failed:
            response += f'❌ {", ".join(failed)}'

        await ctx.send(response)

    @commands.command(
        name='archive',
        help='Archive a channel by making it read-only. Usage: .archive <channel_name>'
    )
    @is_admin_or_owner()
    async def archive_channel(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(f'Channel "{channel_name}" has been archived and is now read-only.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

    @commands.command(
        name='unarchive',
        help='Unarchive a channel by allowing it to send messages. Usage: .unarchive <channel_name>'
    )
    @is_admin_or_owner()
    async def unarchive_channel(self, ctx, channel_name: str):
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        if channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send(f'Channel "{channel_name}" has been unarchived and is now writable.')
        else:
            await ctx.send(f'Channel "{channel_name}" not found.')

# -------------------
# Cog Setup
# -------------------

async def setup(bot):
    """Asynchronous setup function to add the ChannelCog to the bot."""
    await bot.add_cog(ChannelCog(bot))
    logger.info("ChannelCog has been successfully loaded and added to the bot.")
