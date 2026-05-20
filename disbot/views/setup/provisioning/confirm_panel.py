"""Confirm panel for the resource-provisioning pipeline — Track 3 PR 7.

Renders the outcome of
:meth:`services.resource_provisioning.ResourceProvisioningPipeline.provision`.
Unlike the preview panel, this view actually triggers the pipeline
call — but only when its :meth:`run` method is awaited (which the
preview panel does on the operator's Apply click). Bare instantiation
performs no side effects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import discord

from services.resource_provisioning import ProvisioningRequest
from views.base import BaseView

if TYPE_CHECKING:
    from services.resource_provisioning import (
        ProvisioningResult,
        ResourceProvisioningPipeline,
    )

logger = logging.getLogger("bot.views.setup.provisioning.confirm_panel")


_OUTCOME_COLORS = {
    "success": discord.Color.green(),
    "binding_failed": discord.Color.gold(),
    "blocked": discord.Color.red(),
    "working": discord.Color.blurple(),
    "errored": discord.Color.red(),
}


def build_confirm_embed(
    request: ProvisioningRequest,
    *,
    status: str,
    result: Any = None,
    error: str | None = None,
) -> discord.Embed:
    """Render the confirm panel in one of four states.

    Status values:

    * ``"working"`` — pipeline call in flight.
    * ``"success"`` / ``"binding_failed"`` / ``"blocked"`` — pipeline
      returned a :class:`ProvisioningResult`; embed renders its
      fields.
    * ``"errored"`` — the pipeline raised; ``error`` carries the
      exception text.
    """
    color = _OUTCOME_COLORS.get(status, discord.Color.dark_grey())
    title = (
        f"🛠 Provisioning · {request.subsystem}.{request.binding_name} · {status}"
    )
    description_lines = [
        f"**Mode:** `{request.mode}`",
    ]
    if request.custom_name:
        description_lines.append(f"**Custom name:** `{request.custom_name}`")
    embed = discord.Embed(
        title=title,
        description="\n".join(description_lines),
        color=color,
    )

    if status == "working":
        embed.add_field(
            name="Status",
            value="⏳ Running provisioning pipeline…",
            inline=False,
        )
        return embed

    if status == "errored" and error:
        embed.add_field(name="Error", value=f"`{error}`", inline=False)
        return embed

    if result is None:
        embed.add_field(
            name="No result",
            value="The pipeline did not return a result.",
            inline=False,
        )
        return embed

    embed.add_field(
        name="Outcome",
        value=f"`{result.outcome}`",
        inline=True,
    )
    embed.add_field(
        name="Created",
        value=f"`{result.created}`",
        inline=True,
    )
    embed.add_field(
        name="Resource id",
        value=f"`{result.resource_id}`",
        inline=True,
    )
    embed.add_field(
        name="Binding written",
        value=f"`{result.binding_written}`",
        inline=True,
    )
    embed.add_field(
        name="Mutation id",
        value=f"`{result.mutation_id}`",
        inline=False,
    )
    if result.audit_id is not None:
        embed.add_field(
            name="Audit row id",
            value=f"`{result.audit_id}`",
            inline=True,
        )
    return embed


class ConfirmPanelView(BaseView):
    """Final-step view that owns the pipeline call.

    The view is constructed in the ``"working"`` state. The caller
    (typically :class:`PreviewPanelView`) calls :meth:`run` once on
    the interaction; this method awaits
    ``pipeline.provision(..., confirmed=True)`` and edits the message
    to reflect the outcome.

    No buttons are exposed in v1 — the operator already confirmed via
    the preview Apply click. A future iteration may add a "Re-run" or
    "Back to preview" button.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        request: ProvisioningRequest,
        pipeline: ResourceProvisioningPipeline,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.request = request
        self.pipeline = pipeline
        self.result: ProvisioningResult | None = None
        self.error: str | None = None

    async def run(self, interaction: discord.Interaction) -> None:
        """Invoke the pipeline and edit the message with the outcome.

        Failure-safe: any pipeline exception is logged and surfaced
        in the embed as ``status="errored"``. The view never
        re-raises into the interaction handler.
        """
        guild = interaction.guild
        if guild is None:
            self.error = "Provisioning requires a guild context."
            embed = build_confirm_embed(
                self.request,
                status="errored",
                error=self.error,
            )
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )
            return

        try:
            actor = interaction.user
            self.result = await self.pipeline.provision(
                guild,
                self.request,
                actor,
                confirmed=True,
            )
            status = self.result.outcome
            embed = build_confirm_embed(
                self.request,
                status=status,
                result=self.result,
            )
        except Exception as exc:
            logger.exception(
                "ConfirmPanelView.run: pipeline.provision raised for "
                "subsystem=%s binding=%s",
                self.request.subsystem,
                self.request.binding_name,
            )
            self.error = f"{type(exc).__name__}: {exc}"
            embed = build_confirm_embed(
                self.request,
                status="errored",
                error=self.error,
            )

        try:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )
        except discord.HTTPException:
            logger.warning(
                "ConfirmPanelView.run: followup.edit_message failed; "
                "the outcome embed was not delivered.",
            )


__all__ = [
    "ConfirmPanelView",
    "build_confirm_embed",
]
