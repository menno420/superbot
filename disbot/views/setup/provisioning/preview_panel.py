"""Preview panel for the resource-provisioning pipeline — Track 3 PR 7.

Renders the output of
:meth:`services.resource_provisioning.ResourceProvisioningPipeline.preview`
(read-only) and offers two buttons:

* **Apply** — transitions to
  :class:`~views.setup.provisioning.confirm_panel.ConfirmPanelView`
  which actually invokes
  :meth:`ResourceProvisioningPipeline.provision`.
* **Cancel** — closes the panel without side effects.

The view is a pure orchestrator: it constructs no resources, writes
no DB rows, and never calls Discord resource-creation APIs directly.
Every state change flows through the pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services.resource_provisioning import ProvisioningPreview, ProvisioningRequest
from views.base import BaseView

if TYPE_CHECKING:
    from services.resource_provisioning import ResourceProvisioningPipeline

logger = logging.getLogger("bot.views.setup.provisioning.preview_panel")


def build_preview_embed(
    request: ProvisioningRequest,
    preview: ProvisioningPreview,
) -> discord.Embed:
    """Render a :class:`ProvisioningPreview` as a Discord embed.

    The embed is the single source of truth for the panel's "what
    will happen" message; tests assert against it without needing a
    live Discord runtime.
    """
    color = discord.Color.blurple() if preview.allowed else discord.Color.dark_grey()
    title = f"🛠 Provisioning preview — {request.subsystem}.{request.binding_name}"
    description_lines = [
        f"**Action:** `{preview.action}`",
        f"**Mode:** `{request.mode}`",
        f"**Target name:** `{preview.target_name or '—'}`",
        f"**Allowed:** `{preview.allowed}`",
    ]
    if request.custom_name:
        description_lines.append(f"**Custom name:** `{request.custom_name}`")
    if request.category_id is not None:
        description_lines.append(f"**Category id:** `{request.category_id}`")
    if request.permission_template:
        description_lines.append(
            f"**Permission template:** `{request.permission_template}`",
        )

    embed = discord.Embed(
        title=title,
        description="\n".join(description_lines),
        color=color,
    )
    if preview.warnings:
        embed.add_field(
            name="Warnings",
            value="\n".join(f"• {w}" for w in preview.warnings),
            inline=False,
        )
    embed.set_footer(
        text=(
            "Apply confirms via the pipeline (audit + cache + event emit "
            "preserved). Cancel closes without side effects."
        ),
    )
    return embed


class PreviewPanelView(BaseView):
    """Pre-action preview view.

    Public attributes:

    * ``request`` — the :class:`ProvisioningRequest` that drove the
      preview.
    * ``preview`` — the :class:`ProvisioningPreview` returned by the
      pipeline.
    * ``cancelled`` — set to ``True`` when the operator clicks Cancel.
    * ``confirmed`` — set to ``True`` when Apply is clicked (the
      transition to :class:`ConfirmPanelView` happens then).

    Lifecycle:

    1. Caller computes ``preview = await pipeline.preview(guild, request)``.
    2. Caller instantiates this view and renders
       :func:`build_preview_embed` alongside.
    3. Apply → :class:`ConfirmPanelView` is sent in-place via
       :func:`views.navigation.transition_to`.
    4. Cancel → view ends; caller may navigate back.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        request: ProvisioningRequest,
        preview: ProvisioningPreview,
        pipeline: ResourceProvisioningPipeline | None = None,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.request = request
        self.preview = preview
        self.pipeline = pipeline
        self.cancelled: bool = False
        self.confirmed: bool = False

        # Disable Apply if the pipeline already said it can't proceed —
        # the operator sees Cancel as the only valid action.
        if not preview.allowed:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.label == "Apply":
                    child.disabled = True

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.success)
    async def _apply(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button  # disable-on-press handled by transition
        self.confirmed = True
        # Lazy import keeps this module importable without discord
        # being fully resolved in some test setups.
        from views.navigation import transition_to
        from views.setup.provisioning.confirm_panel import (
            ConfirmPanelView,
            build_confirm_embed,
        )

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return

        # Resolve the pipeline now (the test path passes one in;
        # production code instantiates lazily).
        pipeline = self.pipeline
        if pipeline is None:
            from services.resource_provisioning import (
                ResourceProvisioningPipeline,
            )

            pipeline = ResourceProvisioningPipeline()

        confirm_view = ConfirmPanelView(
            self._author,
            request=self.request,
            pipeline=pipeline,
            public=self._public,
            timeout=self.timeout,
        )
        embed = build_confirm_embed(self.request, status="working")
        # ``transition_to`` edits the message in place with the new
        # view + embed.
        await transition_to(interaction, view=confirm_view, embed=embed)
        # Kick off the actual provision call once the new view is on
        # screen; the result is rendered into the same message.
        await confirm_view.run(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def _cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        self.cancelled = True
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="Provisioning cancelled.",
            view=self,
        )
        self.stop()


__all__ = [
    "PreviewPanelView",
    "build_preview_embed",
]
