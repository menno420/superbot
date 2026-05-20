"""Identity & defaults section — shows server identity and edits one default.

This section is the first non-stage section in the setup wizard.  Unlike
Readiness / Smart Suggestions / Final Review (which are wizard stages),
this section configures actual settings.  It demonstrates the full
section-driven SetupOperation flow end-to-end:

1. The hub button opens an ephemeral panel showing identity facts about
   the guild plus the current value of a writable default.
2. The operator clicks **Edit warn threshold** and submits a modal.
3. The submitted value is packaged as a single
   `SetupOperation(kind="set_setting", subsystem="moderation",
   setting_name="warn_threshold", value=...)` and dispatched through
   `services.setup_operations.apply_operations`.
4. The dispatcher routes to `SettingsMutationPipeline.set_value`, which
   validates, writes, audits, and emits the canonical event.

`moderation.warn_threshold` is a real existing `SettingSpec`; using it
keeps the demo honest while we avoid inventing a new subsystem for one
demo setting.  Future sections (true Identity & Naming, Channel
Bindings, Resource Provisioning) plug into the same registry without
editing the hub.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.identity")

SLUG = "identity"
SETTING_SUBSYSTEM = "moderation"
SETTING_NAME = "warn_threshold"


def _build_identity_embed(
    guild: discord.Guild,
    *,
    current_warn_threshold: int | None,
) -> discord.Embed:
    owner_display = "unknown"
    owner = getattr(guild, "owner", None)
    if owner is not None:
        owner_display = getattr(owner, "display_name", None) or getattr(
            owner,
            "name",
            "unknown",
        )

    embed = discord.Embed(
        title="🪪 Server identity",
        description=(
            "Identity snapshot for this guild.  Edit the default below to "
            "demonstrate the SetupOperation path; new sections plug into "
            "the same registry."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Server", value=guild.name, inline=True)
    embed.add_field(name="Guild ID", value=str(guild.id), inline=True)
    embed.add_field(name="Owner", value=owner_display, inline=True)
    embed.add_field(
        name="Members",
        value=str(getattr(guild, "member_count", "?")),
        inline=True,
    )
    threshold_text = (
        str(current_warn_threshold)
        if current_warn_threshold is not None
        else "(default)"
    )
    embed.add_field(
        name="Warn threshold",
        value=threshold_text,
        inline=True,
    )
    embed.set_footer(text="Edits flow through the SetupOperation dispatcher.")
    return embed


async def _read_current_warn_threshold(guild_id: int) -> int | None:
    """Best-effort read of the current `moderation.warn_threshold`.

    Returns `None` on any failure or missing value — the snapshot is
    informational only and must not block the section's render.
    """
    try:
        from utils import db
        from utils.settings_keys import WARN_THRESHOLD

        raw = await db.get_setting(guild_id, WARN_THRESHOLD)
    except Exception:
        logger.exception("identity section: failed to read warn_threshold")
        return None
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


class _WarnThresholdModal(discord.ui.Modal, title="Edit warn threshold"):
    threshold: discord.ui.TextInput = discord.ui.TextInput(
        label="Warn threshold (positive integer)",
        placeholder="3",
        min_length=1,
        max_length=4,
        required=True,
    )

    def __init__(self, panel: IdentitySectionView) -> None:
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = (self.threshold.value or "").strip()
        try:
            value = int(raw)
        except ValueError:
            await interaction.response.send_message(
                f"⚠️ `{raw}` is not a valid integer.",
                ephemeral=True,
            )
            return
        if value <= 0:
            await interaction.response.send_message(
                "⚠️ Warn threshold must be a positive integer.",
                ephemeral=True,
            )
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Identity edits require a guild context.",
                ephemeral=True,
            )
            return

        from services.setup_operations import SetupOperation, apply_operations

        op = SetupOperation(
            kind="set_setting",
            subsystem=SETTING_SUBSYSTEM,
            setting_name=SETTING_NAME,
            value=value,
        )
        try:
            batch = await apply_operations(
                [op],
                guild=guild,
                actor=interaction.user,
            )
        except Exception:
            logger.exception("identity section: apply_operations failed")
            await interaction.response.send_message(
                "Apply failed — see logs.",
                ephemeral=True,
            )
            return

        if batch.applied:
            try:
                await setup_session.mark_in_progress(guild.id, step=SLUG)
            except Exception:
                logger.exception("identity section: mark_in_progress failed")
            await interaction.response.send_message(
                f"✅ Warn threshold set to **{value}**.",
                ephemeral=True,
            )
            return

        if batch.failed:
            error = batch.failed[0].error or "unknown error"
            await interaction.response.send_message(
                f"❌ Apply failed: {error}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Apply completed without effect.",
            ephemeral=True,
        )


class IdentitySectionView(BaseView):
    """Ephemeral panel: identity snapshot + edit button."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)

    @discord.ui.button(
        label="Edit warn threshold",
        style=discord.ButtonStyle.primary,
    )
    async def _edit_warn_threshold(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await interaction.response.send_modal(_WarnThresholdModal(self))


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Identity requires a guild context.",
            ephemeral=True,
        )
        return

    current = await _read_current_warn_threshold(guild.id)
    embed = _build_identity_embed(guild, current_warn_threshold=current)
    view = IdentitySectionView(interaction.user)
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("identity section: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Identity & defaults",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🪪",
        order=30,
    ),
)


__all__ = [
    "IdentitySectionView",
    "SETTING_NAME",
    "SETTING_SUBSYSTEM",
    "SLUG",
    "run",
]
