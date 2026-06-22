from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_defer
from services.lifecycle import SUCCESS
from services.role_lifecycle_service import RoleLifecycleRequest, RoleLifecycleService
from utils.role_feasibility import manageable_roles
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.roles._helpers import _parse_color
from views.selectors import attach_multi_role_select, attach_role_select


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
        # Render each role as a mention so Discord shows it in the role's own
        # colour (matching the reaction-role panel) — mentions in an embed never
        # ping. Falls back to the plain name for the rare role that can't mention.
        lines = [
            f"{getattr(role, 'mention', None) or f'**{role.name}**'} — "
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

    async def _rerender(self) -> None:
        if self.message:
            await self.message.edit(embed=await self.build_embed(), view=self)

    def _editable_roles(self, interaction: discord.Interaction) -> list[discord.Role]:
        """Roles the bot AND the acting member can manage (edit/delete targets).

        Filters out @everyone, integration-managed roles, and anything at/above
        the bot's or the actor's top role — the same partition the lifecycle
        service enforces, so the picker only offers roles the action can succeed
        on.
        """
        manageable, _excluded = manageable_roles(
            interaction.guild.roles,
            bot_member=interaction.guild.me,
            actor=interaction.user,
        )
        return manageable

    @discord.ui.button(label="📝 Create", style=discord.ButtonStyle.green, row=0)
    async def create_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.roles.creation_panel import RoleCreatePanel

        panel = RoleCreatePanel(self.ctx)
        await interaction.response.send_message(
            embed=panel.build_embed(),
            view=panel,
            ephemeral=True,
        )

    @discord.ui.button(label="✏️ Edit Role", style=discord.ButtonStyle.blurple, row=0)
    async def edit_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        roles = self._editable_roles(interaction)
        if not roles:
            await interaction.response.send_message(
                "No roles you can edit (all are above me/you, managed, or @everyone).",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Pick a role to edit:",
            view=_EditRolePickView(self, roles),
            ephemeral=True,
        )

    @discord.ui.button(label="🗑️ Delete Role", style=discord.ButtonStyle.red, row=0)
    async def delete_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        roles = self._editable_roles(interaction)
        if not roles:
            await interaction.response.send_message(
                "No deletable roles available.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Select one or more roles to delete, then press **🗑️ Delete Selected**:",
            view=_DeleteRolesView(self, roles),
            ephemeral=True,
        )


class _EditRolePickView(BaseView):
    """Ephemeral picker: choose the role to edit, then open the edit modal."""

    def __init__(self, parent: ManagementPanel, roles: list[discord.Role]) -> None:
        super().__init__(parent._author, timeout=120)
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
        await interaction.response.send_modal(EditRoleModal(self.parent, role))


class EditRoleModal(discord.ui.Modal, title="Edit Role"):  # type: ignore[call-arg]
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

    def __init__(self, parent: ManagementPanel, role: discord.Role) -> None:
        super().__init__()
        self.parent = parent
        self.role = role
        # The role is already chosen (no "find by name" field): show which one
        # in the modal title so the operator has confirmation.
        self.title = f"Edit Role: {role.name}"[:45]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Resolve id-first so a rename between picking and submitting is caught.
        role = resources.resolve_role(interaction.guild, role_id=self.role.id)
        if role is None:
            await interaction.response.send_message(
                f"❌ Role **{self.role.name}** no longer exists.",
                ephemeral=True,
            )
            return

        new_name = self.new_name.value.strip() or None
        new_color = None
        if self.new_color.value.strip():
            try:
                new_color = _parse_color(self.new_color.value)
            except (ValueError, OverflowError):
                await interaction.response.send_message(
                    "❌ Invalid color — use hex like `#ff0000`.",
                    ephemeral=True,
                )
                return

        if new_name is None and new_color is None:
            await interaction.response.send_message(
                "Nothing to change — provide a new name or color.",
                ephemeral=True,
            )
            return

        # Manageability (bot perms + hierarchy) is enforced by the service.
        result = await RoleLifecycleService().apply(
            interaction.guild,
            RoleLifecycleRequest(
                operation="edit",
                role_id=role.id,
                name=new_name,
                color=new_color,
            ),
            interaction.user,
            actor_type="admin",
        )
        if result.outcome != SUCCESS:
            await interaction.response.send_message(
                f"❌ Could not edit role: {result.first_error}",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction):
            return
        await self.parent._rerender()


class _DeleteRolesView(BaseView):
    """Ephemeral multi-select of deletable roles → a confirmation step.

    Replaces the old single-select-deletes-immediately flow: an operator picks
    one or more roles, then presses **Delete Selected** to reach an explicit
    confirmation before anything is removed.
    """

    def __init__(self, parent: ManagementPanel, roles: list[discord.Role]) -> None:
        super().__init__(parent._author, timeout=120)
        self.parent = parent
        self._roles_by_id = {r.id: r for r in roles}
        self.selected_ids: list[int] = []
        attach_multi_role_select(
            self,
            roles,
            self._on_pick,
            placeholder="Select roles to delete…",
            min_values=0,
            select_row=0,
            nav_row=1,
        )

    async def _on_pick(
        self,
        interaction: discord.Interaction,
        role_ids: list[int],
    ) -> None:
        self.selected_ids = role_ids
        # Just record the selection; the Delete-Selected button drives the
        # confirmation. Ack without changing the message.
        await safe_defer(interaction)

    @discord.ui.button(
        label="🗑️ Delete Selected",
        style=discord.ButtonStyle.red,
        row=2,
    )
    async def confirm_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        names = [
            self._roles_by_id[i].name
            for i in self.selected_ids
            if i in self._roles_by_id
        ]
        if not names:
            await interaction.response.send_message(
                "Pick at least one role first.",
                ephemeral=True,
            )
            return
        listing = "\n".join(f"• {n}" for n in names)
        await interaction.response.edit_message(
            content=(
                f"⚠️ Delete these **{len(names)}** role(s)? This cannot be undone.\n"
                f"{listing}"
            ),
            view=_ConfirmDeleteView(self.parent, list(self.selected_ids)),
        )


class _ConfirmDeleteView(BaseView):
    """Final confirm/cancel for a batched role delete."""

    def __init__(self, parent: ManagementPanel, role_ids: list[int]) -> None:
        super().__init__(parent._author, timeout=60)
        self.parent = parent
        self.role_ids = role_ids

    @discord.ui.button(
        label="✅ Confirm delete",
        style=discord.ButtonStyle.red,
        row=0,
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        deleted: list[str] = []
        failed: list[str] = []
        for rid in self.role_ids:
            role = resources.resolve_role(interaction.guild, role_id=rid)
            if role is None:
                continue
            name = role.name
            result = await RoleLifecycleService().apply(
                interaction.guild,
                RoleLifecycleRequest(operation="delete", role_id=role.id),
                interaction.user,
                confirmed=True,
                actor_type="admin",
            )
            if result.outcome == SUCCESS:
                deleted.append(name)
            else:
                failed.append(f"{name} ({result.first_error})")
        parts: list[str] = []
        if deleted:
            parts.append(f"🗑️ Deleted {len(deleted)}: {', '.join(deleted)}.")
        if failed:
            parts.append(f"❌ Failed {len(failed)}: {'; '.join(failed)}.")
        await interaction.followup.send(
            " ".join(parts) or "Nothing deleted.",
            ephemeral=True,
        )
        await self.parent._rerender()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            content="Cancelled — no roles deleted.",
            view=None,
        )
        self.stop()
