from __future__ import annotations

import logging

import discord
from discord.ext import commands
from utils import db
from views.base import BaseView
from views.roles._helpers import _parse_color

logger = logging.getLogger("bot")


class RoleCreateModal(discord.ui.Modal, title="Create Role"):  # type: ignore[call-arg]
    name = discord.ui.TextInput(label="Role name", max_length=100)
    color = discord.ui.TextInput(
        label="Color (hex, e.g. #3498db)",
        placeholder="#000000",
        required=False,
        max_length=7,
    )
    hoist = discord.ui.TextInput(
        label="Show separately in member list? (yes/no)",
        placeholder="no",
        required=False,
        max_length=3,
    )
    mentionable = discord.ui.TextInput(
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
                    "❌ Invalid color — use hex like `#3498db`.", ephemeral=True
                )
                return

        do_hoist = self.hoist.value.strip().lower() in ("yes", "y", "true", "1")
        do_mention = self.mentionable.value.strip().lower() in ("yes", "y", "true", "1")

        try:
            role = await interaction.guild.create_role(
                name=self.name.value,
                color=col,
                hoist=do_hoist,
                mentionable=do_mention,
            )
            automation_view = RoleAutomationView(self.ctx, role.name)
            await interaction.response.send_message(
                f"✅ Created role **{role.name}**.\n"
                "Would you like to configure XP-based auto-assignment for this role?",
                ephemeral=True,
                view=automation_view,
            )
            automation_view.message = await interaction.original_response()
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create roles.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)


class RoleAutomationView(BaseView):
    """Offered after role creation: configure XP automation or skip."""

    def __init__(self, ctx: commands.Context, role_name: str) -> None:
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.role_name = role_name

    @discord.ui.button(
        label="⚙️ Configure Automation", style=discord.ButtonStyle.blurple, row=0
    )
    async def configure_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(
            RoleAutomationModal(self.ctx, self.role_name, self)
        )

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"✅ Role **{self.role_name}** created. No automation configured.",
            view=self,
        )
        self.stop()


class RoleAutomationModal(
    discord.ui.Modal, title="Configure XP Automation"
):  # type: ignore[call-arg]
    level_threshold = discord.ui.TextInput(
        label="XP level required (e.g. 5)",
        placeholder="e.g. 5",
        required=True,
        max_length=4,
    )
    auto_assign_enabled = discord.ui.TextInput(
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
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.role_name = role_name
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
            await db.set_role_xp_threshold(
                interaction.guild.id, self.role_name, level, auto_assign
            )
        except Exception as exc:
            logger.error("set_role_xp_threshold failed: %s", exc, exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to save automation config: {exc}", ephemeral=True
            )
            return

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
