from discord.ext import commands
import discord
import asyncio

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### Clear Command to Delete Messages (with limit) ###
    @commands.command(name='clear', aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Clears a specified number of messages (default is 5, maximum is 100)."""
        if amount <= 0:
            await ctx.send("Please specify a number greater than 0.", delete_after=5)
            return
        if amount > 100:
            await ctx.send("You can only clear up to 100 messages at a time.", delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=amount)
        confirmation_message = await ctx.send(f'Cleared {len(deleted)} messages.')
        await confirmation_message.delete(delay=5)

    ### Server Info Command ###
    @commands.command(name='serverinfo')
    async def serverinfo(self, ctx):
        """Displays detailed information about the server."""
        guild = ctx.guild
        embed = discord.Embed(title=f"{guild.name} Info", description="Server Information", color=discord.Color.blue())
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
        embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    ### User Info Command ###
    @commands.command(name='userinfo')
    async def userinfo(self, ctx, member: discord.Member = None):
        """Displays detailed information about a user."""
        member = member or ctx.author
        status = str(member.status).capitalize()  # Online, Offline, etc.
        activity = member.activity.name if member.activity else "None"  # Current activity if available
        embed = discord.Embed(title=f"User Info - {member}", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Discriminator", value=f"#{member.discriminator}", inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Activity", value=activity, inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    ### Reminder Command with Minute.Second Countdown ###
    @commands.command(name='remind')
    async def remind(self, ctx, time: int, *, message: str):
        """
        Sends an initial reminder with a countdown and a final reminder at the end.

        Parameters:
        - time: Delay in minutes before the second reminder.
        - message: Content of the reminder.
        """
        if time <= 0:
            await ctx.send("Please specify a time greater than 0 minutes.")
            return

        # Send the initial reminder with a unique start message
        initial_message = await ctx.send(f"⏳ Reminder set for {time} minutes: {message}")

        # Countdown loop in minutes and seconds format
        total_seconds = time * 60
        while total_seconds > 0:
            minutes, seconds = divmod(total_seconds, 60)
            await asyncio.sleep(1)
            total_seconds -= 1
            await initial_message.edit(content=f"⏳ Reminder in progress ({minutes:02}:{seconds:02} remaining): {message}")

        # Final reminder with a different message
        await ctx.send(f"⏰ Time's up! Reminder: {message}")

    ### Create Server Invite Command ###
    @commands.command(name='invite')
    @commands.has_permissions(create_instant_invite=True)
    async def invite(self, ctx):
        """Generates a server invite link."""
        invite = await ctx.channel.create_invite(max_uses=1, unique=True)
        await ctx.send(f"Here is your invite link (valid for 1 use): {invite.url}")

    ### Avatar Command ###
    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Displays a user's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    ### Poll Command ###
    @commands.command(name='poll')
    async def poll(self, ctx, question: str, *options):
        """Create a simple poll with options."""
        if len(options) < 2:
            await ctx.send("You need at least two options for a poll.")
            return
        if len(options) > 10:
            await ctx.send("You can only provide up to 10 options.")
            return

        embed = discord.Embed(title=f"Poll: {question}", description="\n".join(f"{i+1}. {option}" for i, option in enumerate(options)), color=discord.Color.blue())
        poll_message = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_message.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")

# Function required to load this cog
async def setup(bot):
    await bot.add_cog(UtilityCog(bot))