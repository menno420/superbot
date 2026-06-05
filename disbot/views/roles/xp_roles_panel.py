from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer, safe_followup
from utils import db
from utils.guild_config_accessors import invalidate_xp_threshold_roles
from utils.ui_constants import ECONOMY_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.roles.time_roles_panel import _row_is_stale
from views.selectors import RoleSelector

logger = logging.getLogger("bot")


class XpRolesPanel(BaseView):
    """XP level-based role automation panel."""

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
                custom_id="role:xp:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        all_rows = await db.get_role_thresholds(self.ctx.guild.id)
        xp_rows = [r for r in all_rows if r.get("level_required") is not None]
        embed = discord.Embed(title="⚡ XP Role Automation", color=ECONOMY_COLOR)
        if xp_rows:
            lines = []
            stale_any = False
            for r in sorted(xp_rows, key=lambda x: x["level_required"]):
                stale = _row_is_stale(self.ctx.guild, r)
                stale_any = stale_any or stale
                if stale:
                    lines.append(
                        f"⚠️ Level **{r['level_required']}** → **{r['role_name']}** "
                        "— *role missing*",
                    )
                    continue
                status = "✅" if r.get("xp_auto_assign") else "⏸️"
                lines.append(
                    f"{status} Level **{r['level_required']}** → **{r['role_name']}**",
                )
            embed.description = "\n".join(lines)
            embed.set_footer(
                text=(
                    "⚠️ a configured role no longer exists — remove or re-add it"
                    if stale_any
                    else "✅ auto-assign active  ⏸️ configured but paused"
                ),
            )
        else:
            embed.description = (
                "No XP threshold roles configured.\n"
                "Use **➕ Add / Edit** to assign a role at a specific XP level."
            )
            embed.set_footer(text="✅ auto-assign active  ⏸️ configured but paused")
        return embed

    async def _refresh(self) -> None:
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
            "Pick the role to assign at an XP level:",
            view=_XpRolePickView(self, roles),
            ephemeral=True,
        )

    @discord.ui.button(label="➖ Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        all_rows = await db.get_role_thresholds(self.ctx.guild.id)
        xp_rows = [r for r in all_rows if r.get("level_required") is not None]
        if not xp_rows:
            await interaction.response.send_message(
                "No XP threshold roles to remove.",
                ephemeral=True,
            )
            return
        view = _XpRemoveView(self, xp_rows)
        await interaction.response.send_message(
            "Select an XP threshold role to remove:",
            view=view,
            ephemeral=True,
        )


class _XpRolePickView(BaseView):
    """Ephemeral one-shot picker: choose a role, then enter the XP level."""

    def __init__(self, parent: XpRolesPanel, roles: list[discord.Role]) -> None:
        super().__init__(parent.ctx.author, timeout=120)
        self.parent = parent
        self.add_item(RoleSelector(roles, self._on_select))

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
        await interaction.response.send_modal(XpLevelModal(self.parent, role))


class XpLevelModal(discord.ui.Modal, title="Set XP Threshold"):  # type: ignore[call-arg]
    level = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="XP Level required",
        placeholder="e.g. 5",
        max_length=4,
    )
    auto_assign = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Enable auto-assign? (yes/no)",
        placeholder="yes",
        required=False,
        max_length=3,
    )

    def __init__(self, parent: XpRolesPanel, role: discord.Role) -> None:
        super().__init__()
        self.parent = parent
        self.role = role

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            lvl = int(self.level.value.strip())
            if lvl < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Level must be a non-negative integer.",
                ephemeral=True,
            )
            return

        raw_auto = self.auto_assign.value.strip().lower()
        enabled = raw_auto not in ("no", "n", "false", "0")

        try:
            # Selector-sourced: the role exists, so persist its id + name snapshot.
            await db.set_role_xp_threshold(
                interaction.guild.id,
                self.role.name,
                lvl,
                enabled,
                role_id=self.role.id,
                display_name=self.role.name,
            )
        except Exception as exc:
            logger.error("XP threshold save failed: %s", exc, exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to save: {exc}",
                ephemeral=True,
            )
            return

        invalidate_xp_threshold_roles(interaction.guild.id)
        if not await safe_defer(interaction):
            return
        await self.parent._refresh()


class _XpRemoveSelect(discord.ui.Select):
    def __init__(self, parent: XpRolesPanel, rows: list[dict]) -> None:
        self.parent = parent  # type: ignore[misc]
        options = [
            discord.SelectOption(
                label=r["role_name"],
                value=r["role_name"],
                description=f"Level {r['level_required']}",
            )
            for r in rows
        ][:25]
        super().__init__(
            placeholder="Choose an XP threshold to remove…",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        # Field-specific: clears only the XP tier, preserves any days_required on
        # the same row, and drops the row entirely when no time tier remains.
        await db.clear_role_xp_threshold(interaction.guild.id, self.values[0])
        invalidate_xp_threshold_roles(interaction.guild.id)
        await safe_followup(
            interaction,
            f"✅ Removed XP threshold for **{self.values[0]}**.",
            ephemeral=True,
        )
        await self.parent._refresh()  # type: ignore[attr-defined]


class _XpRemoveView(discord.ui.View):
    def __init__(self, parent: XpRolesPanel, rows: list[dict]) -> None:
        super().__init__(timeout=60)
        self.add_item(_XpRemoveSelect(parent, rows))
