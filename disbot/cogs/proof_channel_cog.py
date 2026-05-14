from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger("discord_bot.prize_cog")


class ProofChannelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # track timed prize tasks so they can be cancelled if needed
        self._timed_tasks: dict[int, asyncio.Task] = {}

    def get_proof_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        return discord.utils.get(guild.text_channels, name="proof")

    async def _lock_for_winner(
        self, proof_channel: discord.TextChannel, winner: discord.Member
    ) -> None:
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            winner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        await proof_channel.edit(overwrites=overwrites)
        logger.info("Proof channel locked for winner: %s", winner.display_name)

    async def _unlock(self, proof_channel: discord.TextChannel) -> None:
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=False
            ),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        await proof_channel.edit(overwrites=overwrites)
        logger.info("Proof channel unlocked (read-only).")

    @commands.command(name="+prize")
    @commands.has_permissions(manage_channels=True)
    async def start_prize_claim(self, ctx, winner: discord.Member):
        """Grant a winner exclusive access to #proof.  Usage: +prize @winner"""
        ch = self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send(
                "Channel '#proof' not found. Please create one first.", delete_after=10
            )
            return
        await self._lock_for_winner(ch, winner)
        await ctx.send(
            f"{winner.mention} has been granted access to {ch.mention}!",
            delete_after=10,
        )

    @commands.command(name="-prize")
    @commands.has_permissions(manage_channels=True)
    async def end_prize_claim(self, ctx):
        """End the prize session and make #proof read-only again.  Usage: -prize"""
        ch = self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return
        # Cancel any pending timed task for this guild
        if task := self._timed_tasks.pop(ctx.guild.id, None):
            task.cancel()
        await self._unlock(ch)
        await ctx.send(f"{ch.mention} is now read-only for everyone.", delete_after=10)

    @commands.command(name="prizestatus")
    @commands.has_permissions(manage_channels=True)
    async def prize_status(self, ctx):
        """Show current #proof channel permissions."""
        ch = self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return
        formatted = _format_overwrites(ch.overwrites)
        embed = discord.Embed(
            title=f"Proof Channel Status — #{ch.name}",
            description=formatted,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, delete_after=60)

    @commands.command(name="timedprize")
    @commands.has_permissions(manage_channels=True)
    async def start_timed_prize_claim(self, ctx, winner: discord.Member, duration: int):
        """Grant timed access to #proof; auto-unlocks after duration minutes.  Usage: timedprize @winner <minutes>"""
        ch = self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return

        # Cancel any existing timed task for this guild
        if old_task := self._timed_tasks.pop(ctx.guild.id, None):
            old_task.cancel()

        await self._lock_for_winner(ch, winner)
        await ctx.send(
            f"{winner.mention} has been granted access to {ch.mention} for **{duration}** minute(s)!",
            delete_after=10,
        )

        async def _auto_unlock():
            await asyncio.sleep(duration * 60)
            try:
                await self._unlock(ch)
                await ctx.send(
                    f"Time is up! {ch.mention} is now read-only again.", delete_after=10
                )
            except Exception:
                pass
            finally:
                self._timed_tasks.pop(ctx.guild.id, None)

        task = asyncio.create_task(_auto_unlock())
        self._timed_tasks[ctx.guild.id] = task


def _format_overwrites(overwrites: dict) -> str:
    lines = []
    for target, perms in overwrites.items():
        name = (
            target.name
            if isinstance(target, discord.Role)
            else getattr(target, "display_name", "Unknown")
        )
        allow = ", ".join(
            p.replace("_", " ").title() for p, v in iter(perms) if v is True
        )
        deny = ", ".join(
            p.replace("_", " ").title() for p, v in iter(perms) if v is False
        )
        lines.append(
            f"**{name}**\nAllowed: {allow or 'None'}\nDenied: {deny or 'None'}"
        )
    return "\n\n".join(lines) or "No overwrites."


async def setup(bot):
    await bot.add_cog(ProofChannelCog(bot))
    logger.info("ProofChannelCog loaded.")
