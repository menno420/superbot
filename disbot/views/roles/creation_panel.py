from __future__ import annotations

import logging

import discord
from discord.ext import commands

from services import role_automation
from services.lifecycle import SUCCESS
from services.role_lifecycle_service import RoleLifecycleRequest, RoleLifecycleService
from utils.guild_config_accessors import invalidate_xp_threshold_roles
from views.base import BaseView
from views.roles._helpers import _parse_color

logger = logging.getLogger("bot")


class RoleCreateModal(discord.ui.Modal, title="Create Role"):  # type: ignore[call-arg]
    name = discord.ui.TextInput(label="Role name", max_length=100)  # type: ignore[var-annotated]
    color = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Color (hex, e.g. #3498db)",
        placeholder="#000000",
        required=False,
        max_length=7,
    )
    hoist = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Show separately in member list? (yes/no)",
        placeholder="no",
        required=False,
        max_length=3,
    )
    mentionable = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Mentionable by everyone? (yes/no)",
        placeholder="no",
        required=False,
        max_length=3,
    )

    def __init__(self, ctx: commands.Context) -> None:
        super().__init__()
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction) -> None:
        col = discord.Color.default()
        if self.color.value.strip():
            try:
                col = _parse_color(self.color.value)
            except (ValueError, OverflowError):
                await interaction.response.send_message(
                    "❌ Invalid color — use hex like `#3498db`.",
                    ephemeral=True,
                )
                return

        do_hoist = self.hoist.value.strip().lower() in ("yes", "y", "true", "1")
        do_mention = self.mentionable.value.strip().lower() in ("yes", "y", "true", "1")

        result = await RoleLifecycleService().apply(
            interaction.guild,
            RoleLifecycleRequest(
                operation="create",
                name=self.name.value,
                color=col,
                hoist=do_hoist,
                mentionable=do_mention,
            ),
            interaction.user,
            actor_type="admin",
        )
        if result.outcome != SUCCESS:
            await interaction.response.send_message(
                f"❌ Could not create role: {result.first_error}",
                ephemeral=True,
            )
            return
        role_name = result.steps[0].target_name
        # Capture the freshly-created role id so the XP-automation companion
        # writes through the audited seam id-first (rename-safe), like every
        # other threshold panel — instead of the old name-only write.
        role_id = result.steps[0].target_id
        automation_view = RoleAutomationView(self.ctx, role_name, role_id)
        await interaction.response.send_message(
            f"✅ Created role **{role_name}**.\n"
            "Would you like to configure XP-based auto-assignment for this role?",
            ephemeral=True,
            view=automation_view,
        )
        automation_view.message = await interaction.original_response()


class RoleAutomationView(BaseView):
    """Offered after role creation: configure XP automation or skip."""

    def __init__(
        self,
        ctx: commands.Context,
        role_name: str,
        role_id: int | None = None,
    ) -> None:
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.role_name = role_name
        self.role_id = role_id

    @discord.ui.button(
        label="⚙️ Configure Automation",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def configure_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(
            RoleAutomationModal(self.ctx, self.role_name, self, role_id=self.role_id),
        )

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"✅ Role **{self.role_name}** created. No automation configured.",
            view=self,
        )
        self.stop()


class RoleAutomationModal(
    discord.ui.Modal,
    title="Configure XP Automation",
):  # type: ignore[call-arg]
    level_threshold = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="XP level required (e.g. 5)",
        placeholder="e.g. 5",
        required=True,
        max_length=4,
    )
    auto_assign_enabled = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Enable auto-assign? (yes/no)",
        placeholder="yes",
        required=False,
        max_length=3,
    )

    def __init__(
        self,
        ctx: commands.Context,
        role_name: str,
        parent_view: RoleAutomationView,
        *,
        role_id: int | None = None,
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.role_name = role_name
        self.role_id = role_id
        self._parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            level = int(self.level_threshold.value.strip())
            if level < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Level threshold must be a non-negative integer (e.g. `5`).",
                ephemeral=True,
            )
            return

        raw_auto = self.auto_assign_enabled.value.strip().lower()
        auto_assign = raw_auto not in ("no", "n", "false", "0")

        try:
            # Audited seam (P0C): write + audit emit + XP-cache invalidation all
            # live in role_automation.set_xp_threshold. role_id is the freshly
            # created role's id (threaded from the lifecycle result).
            await role_automation.set_xp_threshold(
                guild_id=interaction.guild.id,
                role_id=self.role_id,
                role_name=self.role_name,
                level=level,
                actor_id=interaction.user.id,
                auto_assign=auto_assign,
            )
        except Exception as exc:
            logger.error("set_xp_threshold failed: %s", exc, exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to save automation config: {exc}",
                ephemeral=True,
            )
            return

        invalidate_xp_threshold_roles(interaction.guild.id)

        for item in self._parent_view.children:
            item.disabled = True
        status = "enabled" if auto_assign else "saved (auto-assign disabled)"
        await interaction.response.edit_message(
            content=(
                f"✅ Role **{self.role_name}** XP automation {status}.\n"
                f"Level threshold: **{level}** | "
                f"Auto-assign: **{'yes' if auto_assign else 'no'}**"
            ),
            view=self._parent_view,
        )
        self._parent_view.stop()
