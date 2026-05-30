"""Role-automation exemptions panel — Settings UI for per-role exemptions.

Lets an operator pick one or more server roles and mark them exempt from
the XP and/or time-based role automation independently, and flip the two
"stack vs. single" tier toggles. Reads/writes route through
:mod:`services.role_exemption_service` (audited + cache-invalidated); the
stacking toggles flip through the canonical settings toggle helper.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from utils import db
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button


class _ExemptRoleSelect(discord.ui.RoleSelect):
    """Multi-role picker — stores the selection on the parent panel."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Select role(s) to configure…",
            min_values=0,
            max_values=25,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, RoleExemptionsPanel):
            return
        view.selected_role_ids = [role.id for role in self.values]
        await interaction.response.edit_message(
            embed=await view.build_embed(),
            view=view,
        )


class RoleExemptionsPanel(BaseView):
    """Per-role automation exemptions + the two tier-stacking toggles."""

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent
        self.selected_role_ids: list[int] = []
        self.add_item(_ExemptRoleSelect())

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                return parent.build_embed(), parent

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:exemptions:back",
                parent_builder=_build_parent,
                row=4,
            )

    async def build_embed(self) -> discord.Embed:
        from services.settings_resolution import resolve_value

        guild = self.ctx.guild
        rows = await db.get_role_exemptions(guild.id)
        time_stack = bool(
            await resolve_value(guild.id, "role", "time_roles_stack", False),
        )
        xp_stack = bool(await resolve_value(guild.id, "role", "xp_roles_stack", True))

        embed = discord.Embed(
            title="🚫 Role Automation Exemptions",
            description=(
                "Pick role(s) from the dropdown, then mark them exempt from "
                "the XP and/or time-based role automation. Members holding an "
                "XP-exempt role earn no level roles; members holding a "
                "time-exempt role get no tenure (days-in-server) roles."
            ),
            color=ROLE_COLOR,
        )

        if rows:
            lines = []
            for row in rows:
                role = resources.resolve_role(guild, role_id=row["role_id"])
                rname = role.mention if role else f"`id:{row['role_id']}`"
                tags = [
                    tag
                    for tag, on in (
                        ("XP", row["exempt_xp"]),
                        ("Time", row["exempt_time"]),
                    )
                    if on
                ]
                lines.append(f"{rname} — exempt: {', '.join(tags)}")
            value = "\n".join(lines)[:1024]
        else:
            value = "*(none)*"
        embed.add_field(name="Current exemptions", value=value, inline=False)

        if self.selected_role_ids:
            parts = []
            for rid in self.selected_role_ids:
                role = resources.resolve_role(guild, role_id=rid)
                parts.append(role.mention if role else f"id:{rid}")
            selected = ", ".join(parts)
        else:
            selected = "*(none — pick from the dropdown first)*"
        embed.add_field(name="Selected", value=selected[:1024], inline=False)

        embed.add_field(
            name="Tier stacking",
            value=(
                f"Time roles: **{'stack (keep all)' if time_stack else 'single (replace)'}**\n"
                f"XP roles: **{'stack (keep all)' if xp_stack else 'single (replace)'}**"
            ),
            inline=False,
        )
        return embed

    async def _apply(
        self,
        interaction: discord.Interaction,
        *,
        field: str,
        value: bool,
    ) -> None:
        if not self.selected_role_ids:
            await interaction.response.send_message(
                "Pick one or more roles from the dropdown first.",
                ephemeral=True,
            )
            return

        from services import role_exemption_service

        guild = self.ctx.guild
        rows = await db.get_role_exemptions(guild.id)
        current = {
            int(r["role_id"]): (bool(r["exempt_xp"]), bool(r["exempt_time"]))
            for r in rows
        }
        for role_id in self.selected_role_ids:
            exempt_xp, exempt_time = current.get(role_id, (False, False))
            if field == "xp":
                exempt_xp = value
            else:
                exempt_time = value
            await role_exemption_service.set_exemption(
                guild.id,
                role_id,
                exempt_xp=exempt_xp,
                exempt_time=exempt_time,
                actor_id=interaction.user.id,
            )
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )

    @discord.ui.button(label="Exempt XP", style=discord.ButtonStyle.danger, row=1)
    async def exempt_xp_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._apply(interaction, field="xp", value=True)

    @discord.ui.button(label="Allow XP", style=discord.ButtonStyle.secondary, row=1)
    async def allow_xp_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._apply(interaction, field="xp", value=False)

    @discord.ui.button(label="Exempt Time", style=discord.ButtonStyle.danger, row=2)
    async def exempt_time_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._apply(interaction, field="time", value=True)

    @discord.ui.button(label="Allow Time", style=discord.ButtonStyle.secondary, row=2)
    async def allow_time_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._apply(interaction, field="time", value=False)

    async def _toggle_stack(
        self,
        interaction: discord.Interaction,
        setting_name: str,
    ) -> None:
        from views.settings.edit_boolean import toggle_setting

        await toggle_setting(interaction, "role", setting_name)
        # toggle_setting consumes the interaction response (ephemeral
        # confirmation); refresh the panel message directly so the
        # displayed stacking state stays in sync.
        try:
            await interaction.message.edit(embed=await self.build_embed(), view=self)
        except discord.HTTPException:
            pass

    @discord.ui.button(
        label="Toggle time stacking",
        style=discord.ButtonStyle.blurple,
        row=3,
    )
    async def toggle_time_stack_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._toggle_stack(interaction, "time_roles_stack")

    @discord.ui.button(
        label="Toggle XP stacking",
        style=discord.ButtonStyle.blurple,
        row=3,
    )
    async def toggle_xp_stack_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await self._toggle_stack(interaction, "xp_roles_stack")
