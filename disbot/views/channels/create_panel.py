"""Channel-creation sub-panel + its supporting category / modal widgets.

A ``_CreateSubView`` opens from the main hub's "Create Channel" button.
The view holds a multi-select **name** picker (preset names) plus any
free-form names added through ``_CustomNameModal``, and a single
**category** selection.  Pressing "Create Channel" creates *every* chosen
name under that one category in a single pass (audit P1-10 — the
create-side sibling of the restrict/delete/visibility multi-select
panels), then summarises the per-channel outcome.

``_CategorySelect`` stays single-select on purpose: a batch of channels
shares one category.  ``_CustomNameModal`` appends to the chosen set
rather than replacing it, so custom and preset names compose.
"""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from core.runtime.panel_recovery import restore_parent_or_send_fresh
from services.channel_lifecycle_service import ChannelLifecycleService
from services.lifecycle import BLOCKED
from utils.ui_constants import ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR
from views.base import BaseView
from views.channels._helpers import _CATEGORY_PRESETS, _NAME_PRESETS
from views.navigation import attach_back_button
from views.selectors import MultiSelect

logger = logging.getLogger("bot")


class _CreateSubView(BaseView):
    """Channel-creation sub-panel: multi-name picker + single category."""

    def __init__(
        self,
        ctx: commands.Context,
        *,
        manager_message: discord.Message | None,
    ):
        super().__init__(ctx.author, timeout=120)
        self.ctx = ctx
        self.manager_message = manager_message
        # Two name sources composed into ``all_names``: preset multi-select
        # + free-form modal entries.
        self.selected_presets: list[str] = []
        self.custom_names: list[str] = []
        self.chosen_cat: str | None = None

        # Category options: existing guild categories first, then presets
        existing_cats = [c.name for c in ctx.guild.categories]
        cat_options = [
            discord.SelectOption(label=c, description="Existing category")
            for c in existing_cats[:15]
        ]
        for p in _CATEGORY_PRESETS:
            if p not in existing_cats and len(cat_options) < 24:
                cat_options.append(
                    discord.SelectOption(label=p, description="New category"),
                )
        if not cat_options:
            cat_options = [discord.SelectOption(label=p) for p in _CATEGORY_PRESETS]

        # Name picker is the shared multi-select primitive.  ``min_values=0``
        # so an admin can rely solely on custom names; "Create" validates
        # that the composed set is non-empty.
        self.name_select = MultiSelect(
            [discord.SelectOption(label=p, value=p) for p in _NAME_PRESETS],
            self._on_names_selected,
            placeholder="Pick one or more channel names…",
            min_values=0,
            row=0,
        )
        self.cat_select = _CategorySelect(cat_options, self)
        self.add_item(self.name_select)
        self.add_item(self.cat_select)

        async def _build_parent(
            _interaction: discord.Interaction,
        ) -> tuple[discord.Embed, discord.ui.View]:
            from views.channels.main_panel import _ChannelManagerView

            manager = _ChannelManagerView(self.ctx)
            manager.message = self.manager_message
            return manager.build_embed(), manager

        attach_back_button(
            self,
            label="↩️ Back",
            custom_id="channels:create:back",
            parent_builder=_build_parent,
            row=2,
        )

    @property
    def all_names(self) -> list[str]:
        """Preset + custom names, de-duplicated, order preserved."""
        ordered: dict[str, None] = {}
        for name in [*self.selected_presets, *self.custom_names]:
            ordered[name] = None
        return list(ordered)

    async def _on_names_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        self.selected_presets = values
        try:
            await interaction.response.edit_message(
                embed=self.build_embed(),
                view=self,
            )
        except discord.HTTPException:
            await safe_defer(interaction)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        logger.error("CreateSubView error on %s: %s", item, error, exc_info=True)
        msg = f"❌ {type(error).__name__}: {error}"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="➕ Create Channel",
            description=(
                "Pick one or more names and a category, then press "
                "**Create Channel**.\n"
                "Click **Custom Name** to add your own name to the set."
            ),
            color=SUCCESS_COLOR,
        )
        names = self.all_names
        embed.add_field(
            name=f"Selected name{'s' if len(names) != 1 else ''}",
            value=(", ".join(f"`{n}`" for n in names) if names else "*(none)*"),
            inline=False,
        )
        embed.add_field(
            name="Selected category",
            value=f"`{self.chosen_cat}`" if self.chosen_cat else "*(none)*",
            inline=True,
        )
        return embed

    @discord.ui.button(
        label="Custom Name",
        style=discord.ButtonStyle.grey,
        emoji="✏️",
        row=2,
    )
    async def custom_name_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_CustomNameModal(self))

    @discord.ui.button(
        label="Create Channel",
        style=discord.ButtonStyle.green,
        emoji="✅",
        row=2,
    )
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        names = self.all_names
        if not names:
            await interaction.response.send_message(
                "Please select or enter at least one channel name first.",
                ephemeral=True,
            )
            return

        if not await safe_defer(interaction, ephemeral=True):
            return

        guild = interaction.guild

        # Channel + category creation route through the audited lifecycle seam
        # (P0-4 PR 2, Q-0100). A category failure blocks the whole batch — every
        # channel would otherwise land in the wrong place.
        result = await ChannelLifecycleService().create_channels(
            guild,
            names,
            interaction.user,
            category_name=self.chosen_cat or None,
            actor_type="admin",
        )
        if result.outcome == BLOCKED:
            await interaction.followup.send(f"❌ {result.first_error}", ephemeral=True)
            return

        created: list[str] = []
        renamed: list[str] = []
        forbidden: list[str] = []
        failed: list[str] = []
        for step in result.steps:
            if step.ok:
                ch = guild.get_channel(step.target_id)
                mention = ch.mention if ch is not None else step.target_name
                created.append(mention)
                if ch is not None and ch.name != step.target_name:
                    renamed.append(f"`{step.target_name}` → {mention}")
            elif step.error == "missing permission":
                forbidden.append(step.target_name)
            else:
                logger.warning(
                    "Channel create failed | name=%r err=%s",
                    step.target_name,
                    step.error,
                )
                failed.append(step.target_name)

        result_embed = self._build_result_embed(
            created=created,
            renamed=renamed,
            forbidden=forbidden,
            failed=failed,
        )

        for item in self.children:
            item.disabled = True

        # Result embed lives on the same parent message; recovery utility
        # falls back to sending a fresh message if the parent is gone.
        success_anchor = await restore_parent_or_send_fresh(
            parent_message=self.manager_message,
            channel=interaction.channel,
            embed=result_embed,
            view=self,
        )
        if success_anchor is None:
            await interaction.followup.send(embed=result_embed, ephemeral=True)

        self.stop()

        # Brief visual pause before restoring the manager panel
        await asyncio.sleep(2)
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        # Track whichever message currently hosts our success embed —
        # could be the original parent or the fresh fallback.
        restore_target = success_anchor or self.manager_message
        restored = await restore_parent_or_send_fresh(
            parent_message=restore_target,
            channel=interaction.channel,
            embed=manager.build_embed(),
            view=manager,
        )
        if restored is not None:
            manager.message = restored

    def _build_result_embed(
        self,
        *,
        created: list[str],
        renamed: list[str],
        forbidden: list[str],
        failed: list[str],
    ) -> discord.Embed:
        if not created:
            title, color = "❌ Creation Failed", ERROR_COLOR
        elif forbidden or failed:
            title, color = "➕ Creation Results", WARNING_COLOR
        else:
            title, color = "✅ Channels Created", SUCCESS_COLOR
        embed = discord.Embed(title=title, color=color)
        if created:
            in_cat = f" in **{self.chosen_cat}**" if self.chosen_cat else ""
            embed.add_field(
                name=f"✅ Created{in_cat}",
                value=", ".join(created),
                inline=False,
            )
        if renamed:
            embed.add_field(
                name="✏️ Renamed (name was taken / sanitised)",
                value="\n".join(renamed),
                inline=False,
            )
        if forbidden:
            embed.add_field(
                name="🚫 Permission denied",
                value=", ".join(f"`{n}`" for n in forbidden),
                inline=False,
            )
        if failed:
            embed.add_field(
                name="⚠️ Failed",
                value=", ".join(f"`{n}`" for n in failed),
                inline=False,
            )
        embed.set_footer(text="Returning to the management panel…")
        return embed

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌", row=2)
    async def cancel_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.channels.main_panel import _ChannelManagerView

        manager = _ChannelManagerView(self.ctx)
        manager.message = self.manager_message
        await interaction.response.edit_message(
            embed=manager.build_embed(),
            view=manager,
        )
        self.stop()


class _CategorySelect(discord.ui.Select):
    """Category picker used by _CreateSubView (single — one per batch)."""

    def __init__(self, options: list[discord.SelectOption], view):
        super().__init__(
            placeholder="Pick a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )
        # NB: must NOT be ``self._parent``.  discord.py 2.7+ owns
        # ``Item._parent`` for check propagation — ``View`` dispatch calls
        # ``item._parent._run_checks(interaction)``.  Shadowing it with the
        # parent *view* made dispatch call ``View._run_checks`` (which does
        # not exist) and crashed every select callback with AttributeError.
        self._owner_view = view

    async def callback(self, interaction: discord.Interaction):
        self._owner_view.chosen_cat = self.values[0]  # type: ignore[attr-defined]
        try:
            await interaction.response.edit_message(
                embed=self._owner_view.build_embed(),  # type: ignore[attr-defined]
                view=self._owner_view,  # type: ignore[attr-defined, arg-type]
            )
        except discord.HTTPException:
            await safe_defer(interaction)


class _CustomNameModal(discord.ui.Modal, title="Custom Channel Name"):  # type: ignore[call-arg]
    channel_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel name",
        placeholder="e.g. my-channel",
        max_length=100,
    )

    def __init__(self, view: _CreateSubView):
        super().__init__()
        self._view = view

    async def on_submit(self, interaction: discord.Interaction):
        name = self.channel_name.value.strip().lower().replace(" ", "-")
        # Append to the set (compose with presets) rather than replace, and
        # avoid duplicates if the same custom name is entered twice.
        if name and name not in self._view.custom_names:
            self._view.custom_names.append(name)
        if not await safe_defer(interaction):
            return
        if self._view.manager_message:
            # Use the recovery helper so a deleted parent doesn't leave
            # the user with an updated name set they can't see.
            await restore_parent_or_send_fresh(
                parent_message=self._view.manager_message,
                channel=interaction.channel,
                embed=self._view.build_embed(),
                view=self._view,
            )
