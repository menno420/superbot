from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime import resources, tasks
from core.runtime.interaction_helpers import help_ctx_shim
from core.runtime.permission_checks import member_has_perms_or_owner, perms_or_owner
from utils.helpers import _parse_member
from utils.ui_constants import ECONOMY_COLOR, SUCCESS_COLOR
from views.base import HubView, send_panel

logger = logging.getLogger("bot.cogs.proof_channel")


class ProofChannelCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        # track timed prize tasks so they can be cancelled if needed
        self._timed_tasks: dict[int, asyncio.Task] = {}

    async def cog_load(self) -> None:
        from cogs.proof_channel.schemas import register_schemas

        register_schemas()  # Settings Phase 2 — declares the channel binding.

    def cog_unload(self):
        """Cancel auto-unlock tasks so a reload doesn't leave winners locked out."""
        tasks.cancel_by_prefix("proof:")
        self._timed_tasks.clear()

    async def get_proof_channel(
        self,
        guild: discord.Guild,
    ) -> discord.TextChannel | None:
        """The guild's proof channel — binding-first (Settings Phase 2).

        A bound ``proof_channel.proof_channel`` wins; the legacy lookup of
        a channel literally named ``proof`` is the fallback lane, so
        existing guilds keep working unbound. A binding read failure
        degrades to the name lookup (one bad row must not kill prize
        commands).
        """
        from core.runtime.bindings import get_binding

        bound_id: int | None = None
        try:
            value = await get_binding(guild.id, "proof_channel", "proof_channel")
            bound_id = value.target_id  # None when the slot was never bound
        except Exception:  # noqa: BLE001 — degrade to the name-based lane
            logger.warning(
                "proof channel: binding read failed for guild %s; "
                "falling back to the name-based lookup",
                guild.id,
                exc_info=True,
            )
        if bound_id is not None:
            channel = guild.get_channel(bound_id)
            if isinstance(channel, discord.TextChannel):
                return channel
            logger.warning(
                "proof channel: bound channel %s missing/non-text in guild %s; "
                "falling back to the name-based lookup",
                bound_id,
                guild.id,
            )
        return resources.resolve_channel(guild, name="proof")  # type: ignore[return-value]

    async def _lock_for_winner(
        self,
        proof_channel: discord.TextChannel,
        winner: discord.Member,
        *,
        actor_id: int | None,
    ) -> None:
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
            ),
            winner: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        await proof_channel.edit(overwrites=overwrites)  # type: ignore[type-var]
        logger.info("Proof channel locked for winner: %s", winner.display_name)
        await _emit_prize_audit(
            proof_channel,
            mutation_type="prize_access_grant",
            new_value=f"winner:{winner.id}",
            actor_id=actor_id,
        )

    async def _unlock(
        self,
        proof_channel: discord.TextChannel,
        *,
        actor_id: int | None,
        actor_type: str = "admin",
    ) -> None:
        overwrites = {
            proof_channel.guild.default_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
            ),
            proof_channel.guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        await proof_channel.edit(overwrites=overwrites)  # type: ignore[type-var]
        logger.info("Proof channel unlocked (read-only).")
        await _emit_prize_audit(
            proof_channel,
            mutation_type="prize_access_revoke",
            new_value="read_only",
            actor_id=actor_id,
            actor_type=actor_type,
        )

    @commands.command(name="+prize")
    @perms_or_owner(manage_channels=True)
    async def start_prize_claim(self, ctx, winner: discord.Member):
        """Grant a winner exclusive access to #proof.  Usage: +prize @winner"""
        ch = await self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send(
                "Channel '#proof' not found. Please create one first.",
                delete_after=10,
            )
            return
        await self._lock_for_winner(ch, winner, actor_id=ctx.author.id)
        await ctx.send(
            f"{winner.mention} has been granted access to {ch.mention}!",
            delete_after=10,
        )

    @commands.command(name="-prize")
    @perms_or_owner(manage_channels=True)
    async def end_prize_claim(self, ctx):
        """End the prize session and make #proof read-only again.  Usage: -prize"""
        ch = await self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return
        # Cancel any pending timed task for this guild
        if task := self._timed_tasks.pop(ctx.guild.id, None):
            task.cancel()
        await self._unlock(ch, actor_id=ctx.author.id)
        await ctx.send(f"{ch.mention} is now read-only for everyone.", delete_after=10)

    @commands.command(name="prizestatus")
    @perms_or_owner(manage_channels=True)
    async def prize_status(self, ctx):
        """Show current #proof channel permissions."""
        ch = await self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return
        formatted = _format_overwrites(ch.overwrites)
        embed = discord.Embed(
            title=f"Proof Channel Status — #{ch.name}",
            description=formatted,
            color=SUCCESS_COLOR,
        )
        await ctx.send(embed=embed, delete_after=60)

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(name="prizemenu")
    @perms_or_owner(manage_channels=True)
    async def prize_menu(self, ctx):
        """Open the interactive prize channel management panel."""
        view = _PrizeManagerView(ctx, self)
        await send_panel(ctx, embed=await view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the prize channel panel)."""
        view = _PrizeManagerView(help_ctx_shim(interaction), self)
        return await view.build_embed(), view

    @commands.command(name="timedprize")
    @perms_or_owner(manage_channels=True)
    async def start_timed_prize_claim(self, ctx, winner: discord.Member, duration: int):
        """Grant timed access to #proof; auto-unlocks after duration minutes.  Usage: timedprize @winner <minutes>"""
        ch = await self.get_proof_channel(ctx.guild)
        if not ch:
            await ctx.send("Channel '#proof' not found.", delete_after=10)
            return

        # Cancel any existing timed task for this guild
        if old_task := self._timed_tasks.pop(ctx.guild.id, None):
            old_task.cancel()

        await self._lock_for_winner(ch, winner, actor_id=ctx.author.id)
        await ctx.send(
            f"{winner.mention} has been granted access to {ch.mention} for **{duration}** minute(s)!",
            delete_after=10,
        )

        async def _auto_unlock():
            await asyncio.sleep(duration * 60)
            try:
                # Timer-driven unlock — system actor (no human at the callback).
                await self._unlock(ch, actor_id=None, actor_type="system")
                await ctx.send(
                    f"Time is up! {ch.mention} is now read-only again.",
                    delete_after=10,
                )
            except Exception:
                pass
            finally:
                self._timed_tasks.pop(ctx.guild.id, None)

        task = tasks.spawn(f"proof:unlock:{ctx.guild.id}", _auto_unlock())
        self._timed_tasks[ctx.guild.id] = task


class _PrizeWinnerModal(discord.ui.Modal, title="Grant Prize Access"):  # type: ignore[call-arg]
    winner_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Winner (mention, ID, or name)",
        max_length=100,
    )

    def __init__(self, cog: ProofChannelCog, timed: bool = False):
        super().__init__()
        self.cog = cog
        self.timed = timed

    async def on_submit(self, interaction: discord.Interaction):
        if not await _reject_without_manage_channels(interaction):
            return
        member = _parse_member(interaction.guild, self.winner_input.value)
        if not member:
            await interaction.response.send_message(
                "❌ Member not found.",
                ephemeral=True,
            )
            return
        ch = await self.cog.get_proof_channel(interaction.guild)
        if not ch:
            await interaction.response.send_message(
                "Channel '#proof' not found.",
                ephemeral=True,
            )
            return
        if self.timed:
            await interaction.response.send_modal(_TimedPrizeModal(self.cog, member))
        else:
            await self.cog._lock_for_winner(ch, member, actor_id=interaction.user.id)
            await interaction.response.send_message(
                f"✅ {member.mention} has been granted access to {ch.mention}!",
                ephemeral=True,
            )


class _TimedPrizeModal(discord.ui.Modal, title="Timed Prize Access"):  # type: ignore[call-arg]
    duration_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Duration (minutes)",
        placeholder="e.g. 10",
        max_length=5,
    )

    def __init__(self, cog: ProofChannelCog, winner: discord.Member):
        super().__init__()
        self.cog = cog
        self.winner = winner

    async def on_submit(self, interaction: discord.Interaction):
        if not await _reject_without_manage_channels(interaction):
            return
        if not self.duration_input.value.isdigit():
            await interaction.response.send_message(
                "❌ Duration must be a whole number of minutes.",
                ephemeral=True,
            )
            return
        duration = int(self.duration_input.value)
        ch = await self.cog.get_proof_channel(interaction.guild)
        if not ch:
            await interaction.response.send_message(
                "Channel '#proof' not found.",
                ephemeral=True,
            )
            return

        if old_task := self.cog._timed_tasks.pop(interaction.guild_id, None):
            old_task.cancel()

        await self.cog._lock_for_winner(ch, self.winner, actor_id=interaction.user.id)

        async def _auto_unlock():
            await asyncio.sleep(duration * 60)
            try:
                # Timer-driven unlock — system actor (no human at the callback).
                await self.cog._unlock(ch, actor_id=None, actor_type="system")
            except Exception:
                pass
            finally:
                self.cog._timed_tasks.pop(interaction.guild_id, None)

        self.cog._timed_tasks[interaction.guild_id] = tasks.spawn(
            f"proof:unlock:{interaction.guild_id}",
            _auto_unlock(),
        )
        await interaction.response.send_message(
            f"✅ {self.winner.mention} has access to {ch.mention} for **{duration}** minute(s).",
            ephemeral=True,
        )


class _PrizeManagerView(HubView):
    """Interactive prize channel management panel."""

    def __init__(self, ctx: commands.Context, cog: ProofChannelCog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    async def build_embed(self) -> discord.Embed:
        ch = await self.cog.get_proof_channel(self.ctx.guild)
        embed = discord.Embed(
            title="🏆 Prize Channel Manager",
            color=ECONOMY_COLOR,
        )
        if ch:
            embed.description = f"Managing {ch.mention}"
            formatted = _format_overwrites(ch.overwrites)
            embed.add_field(
                name="Current Permissions",
                value=formatted[:1000] or "Default",
                inline=False,
            )
        else:
            embed.description = "⚠️ No `#proof` channel found. Create one first."
        embed.set_footer(text="Use buttons below to manage prize access.")
        return embed

    @discord.ui.button(label="🏆 Grant Access", style=discord.ButtonStyle.green, row=0)
    async def btn_grant(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await _reject_without_manage_channels(interaction):
            return
        await interaction.response.send_modal(_PrizeWinnerModal(self.cog, timed=False))

    @discord.ui.button(
        label="⏱️ Timed Access",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_timed(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await _reject_without_manage_channels(interaction):
            return
        await interaction.response.send_modal(_PrizeWinnerModal(self.cog, timed=True))

    @discord.ui.button(label="🔒 End Session", style=discord.ButtonStyle.danger, row=0)
    async def btn_end(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await _reject_without_manage_channels(interaction):
            return
        ch = await self.cog.get_proof_channel(interaction.guild)
        if not ch:
            await interaction.response.send_message(
                "Channel '#proof' not found.",
                ephemeral=True,
            )
            return
        if task := self.cog._timed_tasks.pop(interaction.guild_id, None):
            task.cancel()
        await self.cog._unlock(ch, actor_id=interaction.user.id)
        embed = await self.build_embed()
        embed.description = f"✅ {ch.mention} is now read-only for everyone."
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="🔄 Refresh Status",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )


def _actor_has_manage_channels(interaction: discord.Interaction) -> bool:
    """True when the interacting member holds Manage Channels.

    Defensive: a missing member / permissions object degrades to ``False``
    (deny), never raises.
    """
    return member_has_perms_or_owner(
        getattr(interaction, "user", None),
        manage_channels=True,
    )


async def _reject_without_manage_channels(interaction: discord.Interaction) -> bool:
    """Re-check authority at the callback; ``False`` (already replied) if denied.

    Opening the prize panel does not authorize later button/modal callbacks
    (discord-views rule), so every mutation entry point re-verifies the actor
    still holds ``manage_channels`` before acting.
    """
    if _actor_has_manage_channels(interaction):
        return True
    await interaction.response.send_message(
        "❌ You need **Manage Channels** permission to manage prize access.",
        ephemeral=True,
    )
    return False


async def _emit_prize_audit(
    proof_channel: discord.TextChannel,
    *,
    mutation_type: str,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str = "admin",
) -> None:
    """Audit a prize-access permission change (Q-0209 proof-channel punch #2).

    The lock/unlock is an ephemeral permission-overwrite change rather than a
    DB mutation, so it has no ``*_mutation.py`` seam — but other access
    surfaces audit, so a prize session must leave a trail too. Best-effort:
    an audit-bus failure never blocks the access change.
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    from services.audit_events import emit_audit_action

    guild = proof_channel.guild
    try:
        await emit_audit_action(
            mutation_id=str(uuid4()),
            subsystem="proof_channel",
            mutation_type=mutation_type,
            target=f"channel:{proof_channel.id}",
            scope="guild",
            guild_id=guild.id if guild else None,
            prev_value=None,
            new_value=new_value,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=datetime.now(tz=timezone.utc),
        )
    except Exception:  # noqa: BLE001 — audit is best-effort; never block access
        logger.exception(
            "proof channel: audit emit failed for %s (channel %s); "
            "the permission change is authoritative either way.",
            mutation_type,
            proof_channel.id,
        )


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
            f"**{name}**\nAllowed: {allow or 'None'}\nDenied: {deny or 'None'}",
        )
    return "\n\n".join(lines) or "No overwrites."


async def setup(bot):
    await bot.add_cog(ProofChannelCog(bot))
    logger.info("ProofChannelCog loaded.")
