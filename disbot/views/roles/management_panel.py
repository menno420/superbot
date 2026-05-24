from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.roles._helpers import _find_role_normalized, _parse_color


class ManagementPanel(BaseView):
    """View, edit, and delete server roles."""

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
                custom_id="role:management:back",
                parent_builder=_build_parent,
                row=1,
            )

    async def build_embed(self) -> discord.Embed:
        guild = self.ctx.guild
        lines = [
            f"**{role.name}** — "
            f"{sum(1 for m in guild.members if role in m.roles)} members"
            for role in reversed(guild.roles)
            if role != guild.default_role
        ]
        description = "\n".join(lines) or "No roles found."
        if len(description) > 3800:
            description = description[:3790] + "\n…"
        embed = discord.Embed(
            title="🗂️ Role Management",
            description=description,
            color=ROLE_COLOR,
        )
        embed.set_footer(text="Create · Edit · Delete roles using the buttons below.")
        return embed

    @discord.ui.button(label="📝 Create", style=discord.ButtonStyle.green, row=0)
    async def create_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.roles.creation_panel import RoleCreateModal

        await interaction.response.send_modal(RoleCreateModal(self.ctx))

    @discord.ui.button(label="✏️ Edit Role", style=discord.ButtonStyle.blurple, row=0)
    async def edit_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(EditRoleModal(self))

    @discord.ui.button(label="🗑️ Delete Role", style=discord.ButtonStyle.red, row=0)
    async def delete_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        guild = interaction.guild
        roles = [
            r for r in guild.roles if r != guild.default_role and r < guild.me.top_role
        ]
        if not roles:
            await interaction.response.send_message(
                "No deletable roles available.",
                ephemeral=True,
            )
            return
        view = _DeleteRoleView(self, roles)
        await interaction.response.send_message(
            "Select a role to delete:",
            view=view,
            ephemeral=True,
        )


class EditRoleModal(discord.ui.Modal, title="Edit Role"):  # type: ignore[call-arg]
    role_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Current role name (to find it)",
        max_length=100,
    )
    new_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="New name (blank = keep)",
        max_length=100,
        required=False,
    )
    new_color = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="New color hex e.g. #ff0000 (blank = keep)",
        max_length=7,
        required=False,
    )

    def __init__(self, parent: ManagementPanel) -> None:
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        role = _find_role_normalized(interaction.guild, self.role_name.value.strip())
        if not role:
            await interaction.response.send_message(
                f"❌ Role **{self.role_name.value}** not found.",
                ephemeral=True,
            )
            return
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ That role is above my top role — I can't edit it.",
                ephemeral=True,
            )
            return

        kwargs: dict = {}
        if self.new_name.value.strip():
            kwargs["name"] = self.new_name.value.strip()
        if self.new_color.value.strip():
            try:
                kwargs["color"] = _parse_color(self.new_color.value)
            except (ValueError, OverflowError):
                await interaction.response.send_message(
                    "❌ Invalid color — use hex like `#ff0000`.",
                    ephemeral=True,
                )
                return

        if not kwargs:
            await interaction.response.send_message(
                "Nothing to change — provide a new name or color.",
                ephemeral=True,
            )
            return

        try:
            await role.edit(**kwargs)
            if not await safe_defer(interaction):
                return
            if self.parent.message:
                await self.parent.message.edit(
                    embed=await self.parent.build_embed(),
                    view=self.parent,
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to edit that role.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)


class _DeleteRoleSelect(discord.ui.Select):
    def __init__(self, parent: ManagementPanel, roles: list[discord.Role]) -> None:
        self.parent = parent  # type: ignore[misc]
        options = [
            discord.SelectOption(label=r.name[:100], value=str(r.id)) for r in roles
        ][:25]
        super().__init__(placeholder="Choose a role to delete…", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        role = resources.resolve_role(interaction.guild, role_id=self.values[0])
        if not role:
            await interaction.response.send_message(
                "❌ Role no longer exists.",
                ephemeral=True,
            )
            return
        name = role.name
        try:
            await role.delete()
            await interaction.response.send_message(
                f"🗑️ Deleted role **{name}**.",
                ephemeral=True,
            )
            if self.parent.message:  # type: ignore[attr-defined]
                await self.parent.message.edit(  # type: ignore[attr-defined]
                    embed=await self.parent.build_embed(),  # type: ignore[attr-defined]
                    view=self.parent,  # type: ignore[attr-defined]
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to delete that role.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)


class _DeleteRoleView(discord.ui.View):
    def __init__(self, parent: ManagementPanel, roles: list[discord.Role]) -> None:
        super().__init__(timeout=60)
        self.add_item(_DeleteRoleSelect(parent, roles))
