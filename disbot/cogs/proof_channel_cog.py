from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

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
        # guard so the boot reconcile sweep runs at most once per process
        # (on_ready can fire repeatedly on gateway reconnects).
        self._reconciled = False

    async def cog_load(self) -> None:
        from cogs.proof_channel.schemas import register_schemas

        register_schemas()  # Settings Phase 2 — declares the channel binding.
        # Hot cog-reload while the bot is already connected: on_ready will not
        # fire again, so recover persisted timed locks here. On a cold boot
        # is_ready() is False and the on_ready listener handles it.
        if self.bot.is_ready():
            await self._reconcile_locks()

    def cog_unload(self):
        """Cancel auto-unlock tasks so a reload doesn't leave winners locked out."""
        tasks.cancel_by_prefix("proof:")
        self._timed_tasks.clear()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Recover timed prize locks whose in-memory unlock timer was lost to a
        # restart (Stage-2 walk bug #8). Guarded to run once per process.
        if self._reconciled:
            return
        self._reconciled = True
        await self._reconcile_locks()

    async def _persist_timed_lock(
        self,
        guild_id: int,
        channel_id: int,
        winner_id: int,
        duration_minutes: int,
    ) -> None:
        """Record a timed lock's unlock deadline for restart recovery (bug #8).

        Best-effort: a persistence failure must never block granting the prize,
        it only forfeits restart recovery for this one lock (the in-memory timer
        still runs), so it is logged and swallowed.
        """
        unlock_at = datetime.now(tz=timezone.utc) + timedelta(minutes=duration_minutes)
        try:
            from utils.db import proof_channel_locks

            await proof_channel_locks.upsert_lock(
                guild_id=guild_id,
                channel_id=channel_id,
                winner_id=winner_id,
                unlock_at=unlock_at,
            )
        except Exception:  # noqa: BLE001 — persistence is best-effort
            logger.exception(
                "proof: failed to persist timed lock for guild=%s channel=%s",
                guild_id,
                channel_id,
            )

    def _schedule_unlock(
        self,
        channel: discord.TextChannel,
        guild_id: int,
        delay_seconds: float,
        *,
        notify: discord.abc.Messageable | None = None,
    ) -> asyncio.Task:
        """Spawn (and register) the timer that auto-unlocks *channel* after
        *delay_seconds*. Shared by the timed prize commands and the boot
        reconcile sweep so the auto-unlock body lives in one place.
        """

        async def _auto_unlock() -> None:
            try:
                await asyncio.sleep(delay_seconds)
                # Timer-driven unlock — system actor (no human at the callback).
                await self._unlock(channel, actor_id=None, actor_type="system")
                if notify is not None:
                    try:
                        await notify.send(
                            f"Time is up! {channel.mention} is now read-only again.",
                            delete_after=10,
                        )
                    except Exception:  # noqa: BLE001 — notify is best-effort
                        pass
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — never let a timer crash the loop
                logger.exception(
                    "proof: timed auto-unlock failed for guild %s",
                    guild_id,
                )
            finally:
                self._timed_tasks.pop(guild_id, None)

        task = tasks.spawn(f"proof:unlock:{guild_id}", _auto_unlock())
        self._timed_tasks[guild_id] = task
        return task

    async def _reconcile_locks(self) -> None:
        """Boot-time recovery for persisted timed prize locks.

        For each persisted lock: if the channel/guild is gone, drop the stale
        row; if the deadline already passed, unlock now (which also clears the
        row); otherwise reschedule the in-memory timer for the remaining time.
        One bad row must never abort the whole sweep.
        """
        from utils.db import proof_channel_locks

        try:
            rows = await proof_channel_locks.all_locks()
        except Exception:  # noqa: BLE001 — no persisted locks is not fatal
            logger.exception("proof: failed to read persisted locks for reconcile")
            return
        now = datetime.now(tz=timezone.utc)
        for row in rows:
            guild_id = row["guild_id"]
            channel_id = row["channel_id"]
            try:
                guild = self.bot.get_guild(guild_id)
                channel = guild.get_channel(channel_id) if guild else None
                if not isinstance(channel, discord.TextChannel):
                    # Guild/channel gone — the row is stale bookkeeping.
                    await proof_channel_locks.delete_lock(guild_id, channel_id)
                    continue
                if row["unlock_at"] <= now:
                    # Deadline already passed while we were down — unlock now
                    # (``_unlock`` clears the persisted row).
                    await self._unlock(channel, actor_id=None, actor_type="system")
                else:
                    remaining = (row["unlock_at"] - now).total_seconds()
                    self._schedule_unlock(channel, guild_id, remaining)
            except Exception:  # noqa: BLE001 — isolate one bad row from the sweep
                logger.exception(
                    "proof: failed to reconcile lock for guild=%s channel=%s",
                    guild_id,
                    channel_id,
                )

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
        # Clear any persisted timed-lock row now that the channel is unlocked —
        # the single chokepoint that covers -prize, the panel end button, both
        # auto-unlocks, and the reconcile sweep. Best-effort: a DB blip must
        # never block the permission change (mirrors the best-effort audit).
        try:
            from utils.db import proof_channel_locks

            await proof_channel_locks.delete_lock(
                proof_channel.guild.id,
                proof_channel.id,
            )
        except Exception:  # noqa: BLE001 — persistence cleanup is best-effort
            logger.exception(
                "proof: failed to clear persisted lock for channel %s",
                proof_channel.id,
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

        # Persist the unlock deadline so a restart can recover it (bug #8).
        await self._persist_timed_lock(ctx.guild.id, ch.id, winner.id, duration)
        self._schedule_unlock(ch, ctx.guild.id, duration * 60, notify=ctx.channel)


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

        # Persist the unlock deadline so a restart can recover it (bug #8).
        await self.cog._persist_timed_lock(
            interaction.guild_id,
            ch.id,
            self.winner.id,
            duration,
        )
        self.cog._schedule_unlock(ch, interaction.guild_id, duration * 60)
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
