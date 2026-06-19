from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer
from services import role_automation
from utils import db
from utils.ui_constants import WARNING_COLOR
from views.base import BaseView
from views.navigation import attach_back_button


def _format_preflight(pf: role_automation.PreflightResult) -> str:
    """One-line role-automation health summary from a preflight result.

    Shows the same blockers ``role_automation.apply`` now enforces before
    mutating, so an operator can *see* why automation is failing (missing
    permission / role above the bot / configured role gone) instead of finding
    out only from a degraded health snapshot.
    """
    if not pf.bot_has_manage_roles:
        return "🔴 I'm missing the **Manage Roles** permission."
    problems: list[str] = []
    if pf.hierarchy_blockers:
        problems.append("above my top role: " + ", ".join(pf.hierarchy_blockers))
    if pf.missing_roles:
        problems.append("missing: " + ", ".join(pf.missing_roles))
    if not problems:
        return "🟢 I can manage all configured progression roles."
    return "⚠️ " + "; ".join(problems)


class DiagnosticsPanel(BaseView):
    """Role system diagnostics — counts, exemptions, member cache status."""

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
                custom_id="role:diagnostics:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        guild = self.ctx.guild
        thresholds = await db.get_role_thresholds(guild.id)
        xp_rows = [r for r in thresholds if r.get("level_required") is not None]
        reaction_rows = await db.get_all_reaction_roles(guild.id)
        exemptions = await db.get_role_exemptions(guild.id)

        embed = discord.Embed(title="🔧 Role System Diagnostics", color=WARNING_COLOR)
        embed.add_field(name="Time Thresholds", value=str(len(thresholds)), inline=True)
        embed.add_field(name="XP Thresholds", value=str(len(xp_rows)), inline=True)
        embed.add_field(
            name="Reaction Roles",
            value=str(len(reaction_rows)),
            inline=True,
        )
        if exemptions:
            exempt_lines = []
            for row in exemptions:
                role = resources.resolve_role(guild, role_id=row["role_id"])
                rname = role.name if role else f"id:{row['role_id']}"
                tags = [
                    tag
                    for tag, on in (
                        ("xp", row["exempt_xp"]),
                        ("time", row["exempt_time"]),
                    )
                    if on
                ]
                exempt_lines.append(f"{rname} ({', '.join(tags)})")
            exempt_value = "\n".join(exempt_lines)[:1024]
        else:
            exempt_value = "*(none)*"
        embed.add_field(name="Role Exemptions", value=exempt_value, inline=False)
        embed.add_field(
            name="Members Cached",
            value=str(len([m for m in guild.members if not m.bot])),
            inline=True,
        )
        embed.add_field(
            name="Total Roles",
            value=str(len(guild.roles) - 1),
            inline=True,
        )

        # Live role-automation health: can the bot actually apply the configured
        # time-based progression roles?  This is the operator's window into the
        # "role_automation.apply failed for member" degradation.
        time_objs = tuple(
            role_automation.RoleThreshold(
                role_name=r["role_name"],
                days_required=r["days_required"],
                role_id=r.get("role_id"),
            )
            for r in thresholds
            if not r.get("xp_auto_assign") and r.get("days_required") is not None
        )
        if time_objs:
            ra_value = _format_preflight(
                role_automation.check_preflight(guild, time_objs),
            )
        else:
            ra_value = "*(no time-based roles configured)*"
        embed.add_field(name="Role Automation", value=ra_value, inline=False)
        return embed

    async def _rerender(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(
        label="🔄 Refresh Members",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def refresh_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        await interaction.guild.chunk()
        # Re-render the panel in place so the refreshed "Members Cached" count is
        # visible, then confirm out-of-band (the edit-in-place house pattern).
        await self._rerender()
        await interaction.followup.send("✅ Member list refreshed.", ephemeral=True)

    @discord.ui.button(label="▶️ Run Assignment", style=discord.ButtonStyle.grey, row=0)
    async def run_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        cog = interaction.client.get_cog("RoleCog")  # type: ignore[attr-defined]
        count = await cog._assign_roles(interaction.guild) if cog else 0
        await interaction.followup.send(
            f"✅ Assignment complete — {count} role(s) assigned.",
            ephemeral=True,
        )
