"""Preset selector section — drafts a bundle of operations at once.

Consumes :mod:`services.automation_templates`'s ``SERVER_PRESETS``
(minimal / community / gaming / moderation-heavy / economy / custom)
and adapts each preset's ``PresetOperation`` items into
``SetupOperation`` drafts via
:func:`services.setup_operations.preset_operations_to_setup_operations`.

Flow:

1. Operator clicks "Load preset".
2. The embed lists every bundled preset.
3. A select lists each preset's slug + display name.
4. On pick, the section shows a preview embed listing the staged ops
   from the preset (read-only — nothing in the draft yet).
5. On confirm, every adapted ``SetupOperation`` lands in the draft
   with ``metadata.source = f"preset:{slug}"``.
6. Final Review applies the staged ops in the canonical order
   (PR 11).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_session
from services.automation_templates import (
    SERVER_PRESETS,
    get_preset,
    preview_preset,
)
from services.setup_operations import preset_operations_to_setup_operations
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.preset_select")

SLUG = "preset_select"


def _preset_options() -> list[discord.SelectOption]:
    options: list[discord.SelectOption] = []
    for preset in SERVER_PRESETS:
        options.append(
            discord.SelectOption(
                label=preset.display_name[:100],
                value=preset.slug,
                description=preset.description[:100] or None,
            ),
        )
    return options or [
        discord.SelectOption(label="(no presets)", value="_none"),
    ]


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_preset_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎛 Load a preset",
        description=(
            "Pick a preset to stage every operation it ships with in one "
            "go.  Nothing applies — Final review confirms before any "
            "mutation runs.  All preset-staged ops carry "
            "`metadata.source = 'preset:<slug>'` so the Final review "
            "embed can group them."
        ),
        color=discord.Color.blurple(),
    )
    for preset in SERVER_PRESETS:
        embed.add_field(
            name=f"{preset.display_name} (`{preset.slug}`)",
            value=preset.description,
            inline=False,
        )
    embed.set_footer(text="Picking a preset opens a preview before staging.")
    return embed


def build_preview_embed(preset_slug: str) -> discord.Embed:
    preset = get_preset(preset_slug)
    if preset is None:
        return discord.Embed(
            title="🎛 Preset preview",
            description=f"Unknown preset `{preset_slug}`.",
            color=discord.Color.red(),
        )
    preview = preview_preset(preset)
    embed = discord.Embed(
        title=f"🎛 {preset.display_name} · preview",
        description=(
            f"**{preview.operation_count}** operation(s) would be staged.  "
            "Confirm to add them to the draft; nothing applies yet."
        ),
        color=discord.Color.blurple(),
    )
    op_lines = [
        f"• `{op.kind}` — {op.description or '(no description)'}"
        for op in preview.operations[:10]
    ]
    if len(preview.operations) > 10:
        op_lines.append(f"_+{len(preview.operations) - 10} more_")
    embed.add_field(
        name="Operations",
        value="\n".join(op_lines) or "_empty_",
        inline=False,
    )
    if preview.warnings:
        embed.add_field(
            name="Warnings",
            value="\n".join(f"• {w}" for w in preview.warnings),
            inline=False,
        )
    embed.set_footer(text="Confirm below to stage every op in the draft.")
    return embed


# ---------------------------------------------------------------------------
# Confirm view
# ---------------------------------------------------------------------------


class _ConfirmPresetView(BaseView):
    """Confirm-or-cancel staging.  Drafts on confirm."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        preset_slug: str,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.preset_slug = preset_slug

    @discord.ui.button(
        label="Stage every op",
        style=discord.ButtonStyle.success,
        emoji="📥",
    )
    async def _confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await _stage_preset(interaction, self.preset_slug)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def _cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="Preset staging cancelled — draft unchanged.",
            view=self,
        )
        self.stop()


class _PresetPickSelect(discord.ui.Select):
    """Preset picker — opens the preview + confirm view."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a preset…",
            min_values=1,
            max_values=1,
            options=_preset_options(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        slug = self.values[0]
        if slug == "_none":
            await interaction.response.send_message(
                "No presets bundled in services.automation_templates.",
                ephemeral=True,
            )
            return
        embed = build_preview_embed(slug)
        view = _ConfirmPresetView(interaction.user, preset_slug=slug)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


class PresetSectionView(BaseView):
    """Entry view — hosts the preset-picker select."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_PresetPickSelect())


# ---------------------------------------------------------------------------
# Stage every op from a preset
# ---------------------------------------------------------------------------


async def _stage_preset(
    interaction: discord.Interaction,
    preset_slug: str,
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Preset staging requires a guild context.",
            ephemeral=True,
        )
        return

    preset = get_preset(preset_slug)
    if preset is None:
        await interaction.response.send_message(
            f"Unknown preset `{preset_slug}`.",
            ephemeral=True,
        )
        return

    ops = preset_operations_to_setup_operations(
        list(preset.operations),
        preset_slug=preset_slug,
    )

    staged = 0
    failed: list[str] = []
    for op in ops:
        # Build a per-op label.  The preset's PresetOperation.description
        # is already a sentence; we prefix the kind for the embed line.
        label = f"[{preset.display_name}] {op.kind}"
        if op.subsystem:
            label += f" · {op.subsystem}"
        if op.binding_name:
            label += f".{op.binding_name}"
        if op.setting_name:
            label += f".{op.setting_name}"
        if op.value is not None:
            label += f" = {op.value}"
        try:
            await setup_draft.append(
                op,
                guild_id=guild.id,
                actor_id=interaction.user.id,
                label=label,
            )
            staged += 1
        except Exception:
            logger.exception(
                "preset %s: append failed for op kind=%s",
                preset_slug,
                op.kind,
            )
            failed.append(label)

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("preset_select: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("preset_select: setup_draft.count failed")
        pending = 0

    summary_lines = [
        f"✅ Staged **{staged}** operation(s) from preset `{preset_slug}`.",
        f"Pending operations: **{pending}**.",
    ]
    if failed:
        summary_lines.append(f"⚠️ Failed to stage **{len(failed)}** op(s) — see logs.")
    await interaction.response.send_message(
        "\n".join(summary_lines),
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry point
# ---------------------------------------------------------------------------


async def run(interaction: discord.Interaction, hub: "SetupHubView") -> None:
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Preset section requires a guild context.",
            ephemeral=True,
        )
        return

    embed = build_preset_embed()
    view = PresetSectionView(interaction.user)
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Load preset",
        style=discord.ButtonStyle.success,
        run=run,
        emoji="🎛",
        order=25,
    ),
)


__all__ = [
    "PresetSectionView",
    "SLUG",
    "build_preset_embed",
    "build_preview_embed",
    "run",
]
