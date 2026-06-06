"""Ephemeral work sub-panel (Job Center).

``_WorkView`` is the bare select widget; ``_WorkSubView`` extends it
with a Back button that returns to the persistent ``EconomyPanelView``.
``_JobSelect`` is the dropdown — its callback performs the actual
work transaction.

After a successful work transaction the dropdown view is replaced with
a fresh :class:`_WorkResultView` that exposes an enabled
"↩ Back to Economy" button. The previous behaviour — disabling every
child of ``_WorkSubView`` and re-rendering it — created a dead-end
result screen because the Back button was disabled along with the
dropdown.
"""

from __future__ import annotations

import time

import discord

from cogs.economy._helpers import _WORK_COOLDOWN, JOBS, _build_economy_embed, _job_pay
from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from services import economy_service, xp_service
from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import post_log_embed
from utils.ui_constants import SUCCESS_COLOR
from views.navigation import BackTarget, attach_back_button, chain_back


class _WorkView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int, available: list[str]):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_id = guild_id
        self.message: discord.Message | None = None
        self.add_item(_JobSelect(user_id, guild_id, available, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This job menu isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class _JobSelect(discord.ui.Select):
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        available: list[str],
        view: _WorkView,
    ):
        self._user_id = user_id
        self._guild_id = guild_id
        self._work_view = view
        options = []
        for name in available:
            j = JOBS[name]
            options.append(
                discord.SelectOption(
                    label=f"{j['emoji']} {name.replace('_', ' ').title()}",
                    value=name,
                    description=f"Base pay: {j['pay']} 🪙  |  +{j['xp']} XP  |  Tier {j['tier']}",
                ),
            )
        super().__init__(
            placeholder="Choose a job to work…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        job_name = self.values[0]
        uid, gid = self._user_id, self._guild_id
        now = int(time.time())

        # Defer before any I/O: this handler does 4 DB ops + 2 service
        # calls (credit, award) + a webhook post before the final edit.
        # The cumulative work blows past the 3s interaction-token window
        # on a normal day.
        if not await safe_defer(interaction):
            return

        eco = await db.get_economy(uid, gid)
        on_cd, secs = check_cooldown(eco["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await safe_followup(
                interaction,
                f"⏰ Still on cooldown! {format_remaining(secs)} left.",
                ephemeral=True,
            )
            return

        times = await db.get_job_times(uid, gid, job_name)
        pay = _job_pay(job_name, times)
        job = JOBS[job_name]
        xp_gain = job["xp"]

        new_times = await db.increment_job(uid, gid, job_name)
        new_bal = await economy_service.credit(
            gid,
            uid,
            pay,
            reason=f"work:{job_name}",
            actor_id=uid,
        )
        xp_result = await xp_service.award(
            guild_id=gid,
            user_id=uid,
            amount=xp_gain,
            source=f"work:{job_name}",
            now=now,
        )
        new_lv = xp_result.new_level
        lvup = xp_result.leveled_up
        await db.set_last_worked(uid, gid, now)

        bonus_pct = min(times, 100)
        embed = discord.Embed(
            title=f"{job['emoji']} Work Complete — {job_name.replace('_', ' ').title()}",
            description=job["desc"],
            color=SUCCESS_COLOR,
        )
        embed.add_field(name="Earned", value=f"**+{pay}** 🪙", inline=True)
        embed.add_field(name="XP gained", value=f"**+{xp_gain}** XP", inline=True)
        embed.add_field(name="Balance", value=f"**{new_bal}** 🪙", inline=True)
        embed.add_field(
            name="Job mastery",
            value=f"{new_times}× worked (+{bonus_pct}% pay)",
            inline=True,
        )
        embed.add_field(
            name="Level",
            value=f"**{new_lv}**{'  🎉 Level up!' if lvup else ''}",
            inline=True,
        )
        embed.set_footer(text="Come back in 1 hour to work again!")

        # Replace the dropdown view with a fresh result view so the
        # ↩ Back to Economy button stays enabled. The previous flow
        # disabled every child on ``_work_view`` (including Back),
        # leaving the user on a dead-end result screen.
        result_view = _WorkResultView(
            interaction.user,
            back_target=getattr(self._work_view, "_back_target", None),
        )
        await safe_edit(interaction, embed=embed, view=result_view)
        result_view.message = interaction.message
        self._work_view.stop()

        log_embed = discord.Embed(
            title="💼 Work Completed",
            description=(
                f"{interaction.user.mention} worked as "
                f"**{job['emoji']} {job_name.replace('_', ' ').title()}**\n"
                f"Earned **+{pay}** 🪙 and **+{xp_gain}** XP"
                + ("  🎉 *Level up!*" if lvup else "")
            ),
            color=SUCCESS_COLOR,
        )
        await post_log_embed(interaction.client, gid, log_embed)


class _WorkSubView(_WorkView):
    """Work sub-panel with a Back button to return to the economy hub."""

    def __init__(
        self,
        user_id: int,
        guild_id: int,
        available: list[str],
        back_target: BackTarget | None = None,
    ):
        super().__init__(user_id, guild_id, available)
        # AB2: propagate the hub's back chain (e.g. back-to-Help when opened via
        # !economymenu) so "↩ Back" rebuilds Economy with the chain re-attached.
        self._back_target = back_target

        async def _build_parent(
            interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            # Late import — main_panel imports from this module.
            from views.economy.main_panel import EconomyPanelView

            embed = await _build_economy_embed(interaction.user, interaction.guild_id)
            return embed, EconomyPanelView()

        attach_back_button(
            self,
            label="↩ Back",
            custom_id="economy:work:back",
            parent_builder=chain_back(_build_parent, back_target),
            row=1,
        )


class _WorkResultView(discord.ui.View):
    """Result screen shown after a successful work transaction.

    Single Back-to-Economy button — replaces the previous pattern of
    disabling every child on ``_WorkSubView`` (which silently disabled
    Back and left the user with no escape).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        back_target: BackTarget | None = None,
    ):
        super().__init__(timeout=60)
        self._author = author
        self.message: discord.Message | None = None
        self._back_target = back_target

        async def _build_parent(
            interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            # Late import — main_panel imports from this module.
            from views.economy.main_panel import EconomyPanelView

            embed = await _build_economy_embed(interaction.user, interaction.guild_id)
            return embed, EconomyPanelView()

        attach_back_button(
            self,
            label="↩ Back to Economy",
            custom_id="economy:back",
            parent_builder=chain_back(_build_parent, back_target),
            row=0,
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._author.id:
            await interaction.response.send_message(
                "This result screen isn't for you.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass
