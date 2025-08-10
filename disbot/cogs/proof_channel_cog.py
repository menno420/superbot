import discord
from discord.ext import commands
import logging
import asyncio

# Retrieve the logger from the main bot
logger = logging.getLogger('discord_bot.prize_cog')


class ProofChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper: Retrieve the proof channel
    def get_proof_channel(self, guild):
        """Find the #proof channel in the guild."""
        return discord.utils.get(guild.text_channels, name='proof')

    # Helper: Lock the proof channel for everyone except the winner
    async def lock_channel_for_winner(self, proof_channel, winner):
        """Lock the proof channel for everyone except the winner."""
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            winner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        await proof_channel.edit(overwrites=overwrites)
        logger.info(f"Proof channel locked for winner: {winner.display_name}")

    # Helper: Unlock the proof channel after prize claim
    async def unlock_channel_after_claim(self, proof_channel):
        """Unlock the proof channel for everyone (read-only)."""
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        await proof_channel.edit(overwrites=overwrites)
        logger.info("Proof channel unlocked for viewing (read-only).")

    # Command: +prize (grant access to the winner)
    @commands.command(
        name='+prize',
        help="Start a prize claim session. Usage: +prize @winner"
    )
    @commands.has_permissions(manage_channels=True)
    async def start_prize_claim(self, ctx, winner: discord.Member):
        """Start a prize claim session by locking the proof channel for the winner."""
        proof_channel = self.get_proof_channel(ctx.guild)
        if proof_channel:
            await self.lock_channel_for_winner(proof_channel, winner)
            await ctx.send(f"{winner.mention} has been granted access to {proof_channel.mention} to claim their prize!", delete_after=10)
        else:
            await ctx.send("Channel '#proof' not found. Please create one first.", delete_after=10)

    # Command: -prize (revoke access and make the channel read-only)
    @commands.command(
        name='-prize',
        help="End a prize claim session and lock the proof channel. Usage: -prize"
    )
    @commands.has_permissions(manage_channels=True)
    async def end_prize_claim(self, ctx):
        """End the prize claim session and lock the proof channel (read-only for everyone)."""
        proof_channel = self.get_proof_channel(ctx.guild)
        if proof_channel:
            await self.unlock_channel_after_claim(proof_channel)
            await ctx.send(f"{proof_channel.mention} is now visible to everyone (read-only).", delete_after=10)
        else:
            await ctx.send("Channel '#proof' not found. Please create one first.", delete_after=10)

    # Command: prizestatus (check current proof channel status)
    @commands.command(
        name='prizestatus',
        help="Check the current status of the proof channel. Usage: prizestatus"
    )
    @commands.has_permissions(manage_channels=True)
    async def prize_status(self, ctx):
        """Check the current status of the proof channel."""
        proof_channel = self.get_proof_channel(ctx.guild)
        if proof_channel:
            overwrites = proof_channel.overwrites
            permissions = self.format_overwrites(overwrites)
            embed = discord.Embed(
                title=f"Proof Channel Status - {proof_channel.name}",
                description=f"Access and permissions for {proof_channel.mention}:",
                color=discord.Color.green()
            )
            embed.add_field(name="Permissions", value=permissions, inline=False)
            await ctx.send(embed=embed, delete_after=60)
        else:
            await ctx.send("Channel '#proof' not found. Please create one first.", delete_after=10)

    # Command: timedprize (grant temporary access to the winner)
    @commands.command(
        name='timedprize',
        help="Start a timed prize claim session. Usage: timedprize @winner <duration_in_minutes>"
    )
    @commands.has_permissions(manage_channels=True)
    async def start_timed_prize_claim(self, ctx, winner: discord.Member, duration: int):
        """Start a timed prize claim session for the winner."""
        proof_channel = self.get_proof_channel(ctx.guild)
        if proof_channel:
            await self.lock_channel_for_winner(proof_channel, winner)
            await ctx.send(f"{winner.mention} has been granted access to {proof_channel.mention} for {duration} minutes to claim their prize!", delete_after=10)
            
            # Unlock the channel after the duration expires
            await asyncio.sleep(duration * 60)
            await self.unlock_channel_after_claim(proof_channel)
            await ctx.send(f"Time is up! {proof_channel.mention} is now visible to everyone (read-only).", delete_after=10)
        else:
            await ctx.send("Channel '#proof' not found. Please create one first.", delete_after=10)

    # Helper: Format overwrites for display
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


# Cog setup function
async def setup(bot):
    await bot.add_cog(ProofChannelCog(bot))
    logger.info("ProofChannelCog has been successfully loaded and added to the bot.")
