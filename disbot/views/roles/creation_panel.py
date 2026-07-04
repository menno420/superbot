from __future__ import annotations

import inspect
import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from core.runtime.permission_checks import member_has_perms_or_owner
from services import role_automation
from services.lifecycle import SUCCESS
from services.role_lifecycle_service import RoleLifecycleRequest, RoleLifecycleService
from utils.guild_config_accessors import invalidate_xp_threshold_roles
from utils.ui_constants import ROLE_COLOR
from views.base import BaseView
from views.navigation import attach_back_button
from views.roles._helpers import _COLOR_OPTIONS, ROLE_PRESETS, _parse_color

logger = logging.getLogger("bot")


class _PresetNameSelect(discord.ui.Select):
    """Quick-pick a preset role *name* (the creation-menu-only ``ROLE_PRESETS``)."""

    def __init__(self, panel: RoleCreatePanel) -> None:
        self._panel = panel
        super().__init__(
            placeholder="Pick a preset name…",
            row=0,
            options=[
                discord.SelectOption(
                    label=p.name,
                    value=p.name,
                    description=(p.description or None),
                )
                for p in ROLE_PRESETS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._panel._on_name_preset(interaction, self.values[0])


class _PresetColorSelect(discord.ui.Select):
    """Quick-pick a preset colour (the shared ``_COLOR_OPTIONS`` palette)."""

    def __init__(self, panel: RoleCreatePanel) -> None:
        self._panel = panel
        super().__init__(
            placeholder="Pick a colour…",
            row=1,
            options=[
                discord.SelectOption(label=label, value=hex_value)
                for label, hex_value in _COLOR_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._panel._on_color_preset(interaction, self.values[0])


class RoleCreatePanel(BaseView):
    """The role *creation menu*: pick a preset name + colour, or go custom.

    Presets (``ROLE_PRESETS`` names + ``_COLOR_OPTIONS`` colours) are surfaced
    **only here** — never in diagnostics, automation, or any other panel
    (owner constraint).  "✏️ Custom…" opens the full free-text modal; "✅ Create"
    creates the staged role through the audited
    :class:`~services.role_lifecycle_service.RoleLifecycleService` and then offers
    the same XP-automation follow-up as the modal path.
    """

    def __init__(self, ctx: commands.Context, parent: BaseView | None = None) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.parent = parent
        self.pending_name: str | None = None
        self.pending_color: discord.Color = discord.Color.default()
        self.pending_color_label: str = "*(default)*"
        self.pending_hoist: bool = False
        self.pending_mentionable: bool = False
        # An explicit colour pick wins over a preset's default colour.
        self._color_explicit = False
        self.add_item(_PresetNameSelect(self))
        self.add_item(_PresetColorSelect(self))

        if parent is not None:

            async def _build_parent(
                _interaction: discord.Interaction,
            ) -> tuple[discord.Embed, discord.ui.View]:
                # The parent's build_embed may be sync (RoleHubView) or async
                # (ManagementPanel) — await it only when it returns a coroutine.
                built = parent.build_embed()
                embed = await built if inspect.isawaitable(built) else built
                return embed, parent

            attach_back_button(
                self,
                label="↩ Back",
                custom_id="role:create:back",
                parent_builder=_build_parent,
                row=3,
            )

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title="📝 Create a Role",
            description=(
                "Pick a **name** and a **colour** below, then press **✅ Create** — "
                "or press **✏️ Custom…** to type your own.\n"
                "Need several at once? **📦 Role Packs** bulk-creates a whole "
                "category (gaming, staff, pronouns, …) in one step.\n\n"
                f"**Name:** {self.pending_name or '*(none yet)*'}\n"
                f"**Colour:** {self.pending_color_label}\n"
                f"**Shown separately:** {'yes' if self.pending_hoist else 'no'}"
            ),
            color=ROLE_COLOR,
        )

    async def _rerender(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_name_preset(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        preset = next((p for p in ROLE_PRESETS if p.name == name), None)
        if preset is None:  # pragma: no cover - select can only emit known values
            await safe_defer(interaction)
            return
        self.pending_name = preset.name
        self.pending_hoist = preset.hoist
        if not self._color_explicit:
            try:
                self.pending_color = _parse_color(preset.color)
                self.pending_color_label = preset.color
            except (ValueError, OverflowError):  # pragma: no cover - constant data
                pass
        await self._rerender(interaction)

    async def _on_color_preset(
        self,
        interaction: discord.Interaction,
        hex_value: str,
    ) -> None:
        try:
            self.pending_color = _parse_color(hex_value)
            self.pending_color_label = hex_value
            self._color_explicit = True
        except (ValueError, OverflowError):  # pragma: no cover - constant data
            pass
        await self._rerender(interaction)

    @discord.ui.button(label="✏️ Custom…", style=discord.ButtonStyle.secondary, row=2)
    async def custom_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(RoleCreateModal(self.ctx))

    @discord.ui.button(
        label="📦 Role Packs",
        style=discord.ButtonStyle.secondary,
        row=3,
    )
    async def packs_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not member_has_perms_or_owner(interaction.user, manage_roles=True):
            await interaction.response.send_message(
                "❌ You need **Manage Roles** permission.",
                ephemeral=True,
            )
            return
        from views.roles._role_pack_flow import RolePackView

        view = RolePackView(interaction.user, interaction.guild)
        await interaction.response.send_message(
            content=(
                "📦 **Bulk-create roles.** Pick a category and multiselect its "
                "roles, or **✏️ Custom (bulk)** to type your own names with an "
                "optional preset colour — existing same-named roles are reused:"
            ),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(label="✅ Create", style=discord.ButtonStyle.green, row=2)
    async def create_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not self.pending_name:
            await interaction.response.send_message(
                "Pick a preset name first, or use **✏️ Custom…** to type your own.",
                ephemeral=True,
            )
            return
        result = await RoleLifecycleService().apply(
            interaction.guild,
            RoleLifecycleRequest(
                operation="create",
                name=self.pending_name,
                color=self.pending_color,
                hoist=self.pending_hoist,
                mentionable=self.pending_mentionable,
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
        role_id = result.steps[0].target_id
        automation_view = RoleAutomationView(self.ctx, role_name, role_id)
        await interaction.response.edit_message(
            content=(
                f"✅ Created role **{role_name}**.\n"
                "Would you like to configure XP-based auto-assignment for this role?"
            ),
            embed=None,
            view=automation_view,
        )
        automation_view.message = interaction.message
        self.stop()


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
