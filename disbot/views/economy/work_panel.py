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
from services import economy_service, xp_service
from utils import db
from utils.cooldowns import check_cooldown, format_remaining
from utils.helpers import post_log_embed
from utils.ui_constants import SUCCESS_COLOR


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

        eco = await db.get_economy(uid, gid)
        on_cd, secs = check_cooldown(eco["last_worked"], _WORK_COOLDOWN)
        if on_cd:
            await interaction.response.send_message(
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
        result_view = _WorkResultView(interaction.user)
        await interaction.response.edit_message(embed=embed, view=result_view)
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

    def __init__(self, user_id: int, guild_id: int, available: list[str]):
        super().__init__(user_id, guild_id, available)

    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.grey, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import — main_panel imports from this module.
        from views.economy.main_panel import EconomyPanelView

        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=EconomyPanelView())
        self.stop()


class _WorkResultView(discord.ui.View):
    """Result screen shown after a successful work transaction.

    Single Back-to-Economy button — replaces the previous pattern of
    disabling every child on ``_WorkSubView`` (which silently disabled
    Back and left the user with no escape).
    """

    def __init__(self, author: discord.Member | discord.User):
        super().__init__(timeout=60)
        self._author = author
        self.message: discord.Message | None = None

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

    @discord.ui.button(
        label="↩ Back to Economy",
        style=discord.ButtonStyle.secondary,
        custom_id="economy:back",
        row=0,
    )
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import — main_panel imports from this module.
        from views.economy.main_panel import EconomyPanelView

        embed = await _build_economy_embed(interaction.user, interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=EconomyPanelView())
        self.stop()
