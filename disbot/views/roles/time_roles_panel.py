from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer
from services import role_automation
from utils import db
from utils.guild_config_accessors import invalidate_xp_threshold_roles
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.paginated_select import PaginatedSelectView
from views.selectors import attach_role_select


def _row_is_stale(guild: discord.Guild, row: dict) -> bool:
    """True if a threshold row's role can no longer be resolved.

    Id-first (PR6 migration 056): a row that stored a ``role_id`` is stale only
    when that id no longer resolves (a rename is fine — the id still resolves).
    Legacy rows (no id) fall back to a name lookup.
    """
    rid = row.get("role_id")
    if rid is not None:
        return resources.resolve_role(guild, role_id=rid) is None
    return resources.resolve_role(guild, name=row["role_name"]) is None


class TimeRolesPanel(BaseView):
    """Days-in-server threshold management panel."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                return parent.build_embed(), parent

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:time:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        embed = discord.Embed(title="⏱️ Time-Based Roles", color=ROLE_COLOR)
        if thresholds:
            lines = []
            stale_any = False
            for r in thresholds:
                stale = _row_is_stale(self.ctx.guild, r)
                stale_any = stale_any or stale
                marker = "⚠️ " if stale else ""
                suffix = "  — *role missing*" if stale else ""
                lines.append(
                    f"{marker}**{r['role_name']}** — {r['days_required']} day(s){suffix}",
                )
            embed.description = "\n".join(lines)
            if stale_any:
                embed.set_footer(
                    text="⚠️ A configured role no longer exists — remove it or "
                    "re-add the current role.",
                )
            else:
                embed.set_footer(text="Roles auto-assigned based on days in server.")
        else:
            embed.description = "No thresholds configured."
            embed.set_footer(text="Roles auto-assigned based on days in server.")
        return embed

    async def _rerender(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="➕ Add / Edit", style=discord.ButtonStyle.green, row=0)
    async def add_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        roles = [r for r in interaction.guild.roles if not r.is_default()]
        if not roles:
            await interaction.response.send_message(
                "No assignable roles in this server.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Pick the role to give a time threshold:",
            view=_TimeRolePickView(self, roles),
            ephemeral=True,
        )

    @discord.ui.button(label="➖ Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        if not thresholds:
            await interaction.response.send_message(
                "No thresholds to remove.",
                ephemeral=True,
            )
            return
        options = [
            discord.SelectOption(
                label=r["role_name"],
                value=r["role_name"],
                description=f"{r['days_required']} day(s)",
            )
            for r in thresholds
        ]
        await interaction.response.send_message(
            "Select a threshold to remove:",
            view=PaginatedSelectView(
                interaction.user,
                options,
                self._remove_threshold,
                placeholder="Choose a threshold to remove…",
            ),
            ephemeral=True,
        )

    async def _remove_threshold(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        role_name = values[0]
        # Audited seam: the field-specific clear (preserves any XP config on the
        # row; drops it only when no automation remains) + audit emit live in
        # role_automation. The cache invalidate also runs there; this local call
        # keeps the panel's invalidator wiring pinned by test_xp_cog_caching.
        await role_automation.clear_time_threshold(
            guild_id=interaction.guild.id,
            role_name=role_name,
            actor_id=interaction.user.id,
        )
        invalidate_xp_threshold_roles(interaction.guild.id)
        await interaction.response.send_message(
            f"✅ Removed **{role_name}** from auto-assignment.",
            ephemeral=True,
        )
        await self._rerender()

    @discord.ui.button(label="🧹 Clear Missing", style=discord.ButtonStyle.grey, row=0)
    async def clear_missing_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Roles are loaded dynamically from the server now (no hardcoded
        # defaults).  A threshold whose role no longer resolves is a phantom row
        # — it can never assign anything and shows as "missing" in diagnostics.
        # Bulk-clear them through the audited seam so the operator does not have
        # to remove each one by hand.
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        stale = [r for r in thresholds if _row_is_stale(self.ctx.guild, r)]
        if not stale:
            await interaction.response.send_message(
                "No missing-role thresholds to clear.",
                ephemeral=True,
            )
            return
        cleared: list[str] = []
        for r in stale:
            await role_automation.clear_time_threshold(
                guild_id=interaction.guild.id,
                role_name=r["role_name"],
                actor_id=interaction.user.id,
            )
            cleared.append(r["role_name"])
        invalidate_xp_threshold_roles(interaction.guild.id)
        if not await safe_defer(interaction, ephemeral=True):
            return
        await self._rerender()
        await interaction.followup.send(
            f"🧹 Cleared {len(cleared)} missing-role threshold(s): "
            f"{', '.join(cleared)}.",
            ephemeral=True,
        )

    @discord.ui.button(label="▶️ Run Now", style=discord.ButtonStyle.blurple, row=1)
    async def run_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        cog = interaction.client.get_cog("RoleCog")  # type: ignore[attr-defined]
        if cog:
            count = await cog._assign_roles(interaction.guild)
            await interaction.followup.send(
                f"✅ Assignment complete — {count} role(s) assigned.",
                ephemeral=True,
            )


class _TimeRolePickView(BaseView):
    """Ephemeral one-shot picker: choose a role, then enter the day threshold."""

    def __init__(self, parent: TimeRolesPanel, roles: list[discord.Role]) -> None:
        super().__init__(parent.ctx.author, timeout=120)
        self.parent = parent
        attach_role_select(self, roles, self._on_select)

    async def _on_select(
        self,
        interaction: discord.Interaction,
        role_id: int,
    ) -> None:
        role = resources.resolve_role(interaction.guild, role_id=role_id)
        if role is None:
            await interaction.response.send_message(
                "That role no longer exists.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(TimeDaysModal(self.parent, role))


class TimeDaysModal(discord.ui.Modal, title="Set Day Threshold"):  # type: ignore[call-arg]
    days = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Days in server required",
        placeholder="0",
        max_length=5,
    )

    def __init__(self, parent: TimeRolesPanel, role: discord.Role) -> None:
        super().__init__()
        self.parent = parent
        self.role = role

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            d = int(self.days.value)
            if d < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Days must be a non-negative integer.",
                ephemeral=True,
            )
            return
        # Selector-sourced: the role exists, so persist its id + name snapshot.
        # Audited seam (P0C): the write + audit emit live in role_automation; the
        # XP-cache invalidation stays here (the time seam does not invalidate it).
        await role_automation.set_time_threshold(
            guild_id=interaction.guild.id,
            role_id=self.role.id,
            role_name=self.role.name,
            days=d,
            actor_id=interaction.user.id,
        )
        invalidate_xp_threshold_roles(interaction.guild.id)
        if not await safe_defer(interaction):
            return
        await self.parent._rerender()
