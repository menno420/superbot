"""Identity & defaults section — shows server identity and stages one default.

This section is the first non-stage section in the setup wizard.  Unlike
Readiness / Smart Suggestions / Final Review (which are wizard stages),
this section configures an actual setting — but in the draft-first
model: the modal submission **stages** a SetupOperation in the
per-guild draft via :mod:`services.setup_draft`, and Final Review is
the only path that applies the staged ops.

Flow:

1. The hub button opens an ephemeral panel showing identity facts about
   the guild plus the current value of a writable default.
2. The operator clicks **Edit warn threshold** and submits a modal.
3. The submitted value is packaged as a single
   ``SetupOperation(kind="set_setting", subsystem="moderation",
   setting_name="warn_threshold", value=...)`` and appended to the
   guild's draft via :func:`services.setup_draft.append` with
   canonical metadata (source=manual, confidence=high, risk=low).
4. The operator sees a "Staged for Final review" confirmation; nothing
   has applied to the database yet.
5. The hub embed will reflect ``Pending operations: N`` when re-opened.

`moderation.warn_threshold` is a real existing `SettingSpec`; using it
keeps the demo honest while we avoid inventing a new subsystem for one
demo setting.  Subsequent sections (channels, roles, presets, etc.)
follow the same draft-append pattern.
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
    embed.set_footer(
        text="Edits stage in the setup draft — Final Review applies them.",
    )
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

        from services import setup_draft
        from services.setup_operations import SetupOperation

        op = SetupOperation(
            kind="set_setting",
            subsystem=SETTING_SUBSYSTEM,
            setting_name=SETTING_NAME,
            value=value,
        )
        label = f"{SETTING_SUBSYSTEM}.{SETTING_NAME} = {value}"
        try:
            await setup_draft.append(
                op,
                guild_id=guild.id,
                actor_id=interaction.user.id,
                label=label,
                metadata={
                    "source": "manual",
                    "confidence": "high",
                    "reason": "Operator entered value via Identity section",
                    "risk": "low",
                },
            )
        except Exception:
            logger.exception("identity section: setup_draft.append failed")
            await interaction.response.send_message(
                "Could not stage the change — see logs.",
                ephemeral=True,
            )
            return

        try:
            await setup_session.mark_in_progress(guild.id, step=SLUG)
        except Exception:
            logger.exception("identity section: mark_in_progress failed")

        try:
            pending = await setup_draft.count(guild.id)
        except Exception:
            logger.exception("identity section: setup_draft.count failed")
            pending = 0

        await interaction.response.send_message(
            (
                f"✅ Staged for Final review: **warn threshold = {value}**.  "
                f"Pending operations: **{pending}**."
            ),
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
# Identity stages `set_setting` ops but `set_setting` is shared with
# many other surfaces (settings cog, automation, etc.). Leaving
# op_kinds empty here keeps the channels/cleanup/cog_routing badges
# from polluting the identity row; tighter scoping comes in PR 3 once
# section cards declare a per-section subsystem filter.


__all__ = [
    "IdentitySectionView",
    "SETTING_NAME",
    "SETTING_SUBSYSTEM",
    "SLUG",
    "run",
]
