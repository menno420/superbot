"""Moderation section — drafts first-class moderation configuration.

Surfaces the moderation behaviour PR10 made configurable
(:mod:`services.moderation_config`) inside the setup wizard.  Each pick
stages a ``SetupOperation(kind="set_setting", subsystem="moderation",
…)`` draft; Final Review's dispatcher routes every staged op through
:class:`services.settings_mutation.SettingsMutationPipeline` (the same
audited, capability-gated path the ``!settings → Moderation`` widget
uses), so this section owns **no** mutation — it only stages writes.

The four knobs surfaced here are the ones that matter most when an
operator first stands up a server:

* **DM on action** (``dm_on_action``) — tell the affected member why.
* **Require a reason** (``require_reason``) — accountability on warn /
  kick / ban.
* **Warn escalation** (``warn_escalation_action``) — what happens when a
  member reaches the warn threshold (timeout / kick / ban / none).
* **Moderator role** (``moderator_role``) — let a role moderate without
  Discord moderation permissions (capability-native, ADR-008).

The full moderation surface (DM template, ban message-purge, timeout
ceiling, post-action cleanup, public log, trusted role, …) stays in
``!settings → Moderation``; the wizard intentionally surfaces only the
high-impact subset so the section stays a four-row picker that works
both as the section card's *Customize* view and as the wizard-native
step-detail view (rows 0–3; row 4 is reserved by ``wizard_nav``).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_session
from services.moderation_config import WARN_ESCALATION_ACTIONS
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.moderation")

SLUG = "moderation"
SUBSYSTEM = "moderation"

# Spec names (``SettingSpec.name``) — NOT the legacy settings_keys.  The
# dispatcher resolves the spec via (subsystem, name); see
# ``cogs/moderation/schemas.py`` and the canonical example in
# ``views/setup/sections/identity.py``.
SETTING_DM_ON_ACTION = "dm_on_action"
SETTING_REQUIRE_REASON = "require_reason"
SETTING_WARN_ESCALATION = "warn_escalation_action"
SETTING_MODERATOR_ROLE = "moderator_role"

_ESCALATION_DESCRIPTIONS: dict[str, str] = {
    "timeout": "Auto-timeout, then reset the count (today's default).",
    "kick": "Kick the member when they hit the warn threshold.",
    "ban": "Ban the member when they hit the warn threshold.",
    "none": "Disable automatic escalation — warnings only accumulate.",
}


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_moderation_embed(
    *,
    dm_on_action: bool | None = None,
    require_reason: bool | None = None,
    warn_escalation_action: str | None = None,
    moderator_role_id: int | None = None,
    guild: discord.Guild | None = None,
) -> discord.Embed:
    """Build the moderation section embed.

    When the optional current-state arguments are supplied the embed
    renders a **Detected** field so the operator sees today's values
    before changing them; with everything ``None`` it renders the
    static explainer used on the section card.
    """
    embed = discord.Embed(
        title="🛡️ Moderation",
        description=(
            "Configure how warns, timeouts, kicks, and bans behave.  Each "
            "pick stages a `set_setting` operation — **Final review** applies "
            "them all through the audited settings pipeline.  Everything else "
            "(DM template, ban message-purge, public log, …) lives in "
            "`!settings → Moderation`."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="What you can set here",
        value=(
            "• **DM on action** — notify the member when they're actioned\n"
            "• **Require a reason** — warn / kick / ban need a reason\n"
            "• **Warn escalation** — what happens at the warn threshold\n"
            "• **Moderator role** — moderate without Discord perms (ADR-008)"
        ),
        inline=False,
    )
    if any(
        v is not None
        for v in (
            dm_on_action,
            require_reason,
            warn_escalation_action,
            moderator_role_id,
        )
    ):
        role_text = "_(none)_"
        if moderator_role_id:
            role = guild.get_role(moderator_role_id) if guild is not None else None
            role_text = role.mention if role is not None else f"`{moderator_role_id}`"
        embed.add_field(
            name="Detected",
            value=(
                f"• DM on action: **{_on_off(dm_on_action)}**\n"
                f"• Require a reason: **{_on_off(require_reason)}**\n"
                f"• Warn escalation: **{warn_escalation_action or 'timeout'}**\n"
                f"• Moderator role: {role_text}"
            ),
            inline=False,
        )
    embed.set_footer(
        text="Recommended: DM on action + require a reason (safe, transparent).",
    )
    return embed


def _on_off(value: bool | None) -> str:
    if value is None:
        return "default"
    return "on" if value else "off"


# ---------------------------------------------------------------------------
# Selects — each pick stages one set_setting op
# ---------------------------------------------------------------------------


class _DmOnActionSelect(discord.ui.Select):
    """Toggle whether the affected member is DM'd on a moderation action."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="DM the member on action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="DM on action: ON",
                    value="true",
                    description="Tell the member why they were actioned.",
                    emoji="✅",
                ),
                discord.SelectOption(
                    label="DM on action: OFF",
                    value="false",
                    description="Don't DM the member (today's default).",
                    emoji="🚫",
                ),
            ],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        enabled = self.values[0] == "true"
        await _stage_setting(
            interaction,
            setting_name=SETTING_DM_ON_ACTION,
            value=enabled,
            label=f"moderation.dm_on_action = {enabled}",
            reason="Operator set DM-on-action via the Moderation setup section",
        )


class _RequireReasonSelect(discord.ui.Select):
    """Toggle whether warn / kick / ban require a reason."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Require a reason for warn / kick / ban…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Require a reason: ON",
                    value="true",
                    description="Reject warn / kick / ban with no reason.",
                    emoji="✅",
                ),
                discord.SelectOption(
                    label="Require a reason: OFF",
                    value="false",
                    description="Reasons stay optional (today's default).",
                    emoji="🚫",
                ),
            ],
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        enabled = self.values[0] == "true"
        await _stage_setting(
            interaction,
            setting_name=SETTING_REQUIRE_REASON,
            value=enabled,
            label=f"moderation.require_reason = {enabled}",
            reason="Operator set require-reason via the Moderation setup section",
        )


class _WarnEscalationSelect(discord.ui.Select):
    """Pick the terminal action when a member reaches the warn threshold."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Warn escalation action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=action,
                    value=action,
                    description=_ESCALATION_DESCRIPTIONS.get(action, "")[:100],
                )
                for action in WARN_ESCALATION_ACTIONS
            ],
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        action = self.values[0]
        await _stage_setting(
            interaction,
            setting_name=SETTING_WARN_ESCALATION,
            value=action,
            label=f"moderation.warn_escalation_action = {action}",
            reason="Operator set warn escalation via the Moderation setup section",
        )


class _ModeratorRoleSelect(discord.ui.RoleSelect):
    """Pick the role that may moderate without Discord moderation perms.

    Stored as the numeric role id (string) under ``moderator_role`` —
    governance's tier resolver grants the ``moderator`` tier to that
    role's members (ADR-008).  Native ``RoleSelect`` avoids the 25-option
    cap and renders every guild role.
    """

    def __init__(self) -> None:
        super().__init__(
            placeholder="Moderator role (optional — grants moderation access)…",
            min_values=1,
            max_values=1,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        role = self.values[0]
        await _stage_setting(
            interaction,
            setting_name=SETTING_MODERATOR_ROLE,
            value=str(role.id),
            label=f"moderation.moderator_role = @{role.name}",
            reason="Operator set the moderator role via the Moderation setup section",
            risk="medium",
        )


class ModerationSectionView(BaseView):
    """Detail view — four single-purpose pickers (rows 0–3).

    Used both as the section card's *Customize* target and as the
    wizard-native step-detail view, so it stays within rows 0–3 (row 4
    is reserved by ``views.setup.wizard_nav.render_step_detail`` for the
    injected "↩ Back to step" button).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_DmOnActionSelect())
        self.add_item(_RequireReasonSelect())
        self.add_item(_WarnEscalationSelect())
        self.add_item(_ModeratorRoleSelect())


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


async def _stage_setting(
    interaction: discord.Interaction,
    *,
    setting_name: str,
    value: object,
    label: str,
    reason: str,
    risk: str = "low",
) -> None:
    """Stage one moderation ``set_setting`` op into the guild's draft."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Moderation edits require a guild context.",
            ephemeral=True,
        )
        return

    op = SetupOperation(
        kind="set_setting",
        subsystem=SUBSYSTEM,
        setting_name=setting_name,
        value=value,
        metadata={
            "source": "manual",
            "confidence": "high",
            "reason": reason,
            "risk": risk,
            "rollback_note": (
                f"Re-stage a different value or change `{setting_name}` in "
                "`!settings → Moderation`."
            ),
        },
    )
    try:
        await setup_draft.append(
            op,
            guild_id=guild.id,
            actor_id=interaction.user.id,
            label=label,
            section_slug=SLUG,
        )
    except Exception:
        logger.exception("moderation: setup_draft.append failed")
        await interaction.response.send_message(
            "Could not stage the moderation setting — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("moderation: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("moderation: setup_draft.count failed")
        pending = 0

    await interaction.response.send_message(
        f"✅ Staged for Final review: `{label}`.  Pending operations: **{pending}**.",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _read_current_state(
    guild: discord.Guild,
) -> tuple[bool | None, bool | None, str | None, int | None]:
    """Best-effort read of the four surfaced moderation values.

    Returns ``(dm_on_action, require_reason, warn_escalation_action,
    moderator_role_id)``.  Any failure degrades to ``None`` — the
    snapshot is informational and must never block the render.
    """
    dm_on = require_reason = None
    escalation = None
    moderator_role_id = None
    try:
        from services.moderation_config import load_policy

        policy = await load_policy(guild.id)
        dm_on = policy.dm_on_action
        require_reason = policy.require_reason
        escalation = policy.warn_escalation_action
    except Exception:
        logger.exception("moderation: load_policy failed")
    try:
        from utils import db
        from utils.settings_keys import MODERATOR_TIER_ROLE_ID

        raw = await db.get_setting(guild.id, MODERATOR_TIER_ROLE_ID)
        if raw not in (None, ""):
            moderator_role_id = int(raw)
    except Exception:
        logger.exception("moderation: moderator-role read failed")
    return dm_on, require_reason, escalation, moderator_role_id


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the detailed moderation picker (the card's Customize target)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Moderation section requires a guild context.",
            ephemeral=True,
        )
        return

    dm_on, require_reason, escalation, role_id = await _read_current_state(guild)
    embed = build_moderation_embed(
        dm_on_action=dm_on,
        require_reason=require_reason,
        warn_escalation_action=escalation,
        moderator_role_id=role_id,
        guild=guild,
    )
    view = ModerationSectionView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def _recommended_moderation_ops(
    guild: discord.Guild,
) -> list[SetupOperation]:
    """Safe moderation baseline: DM on action + require a reason.

    Both are transparency / accountability wins and behaviour-preserving
    otherwise (warn escalation stays at its existing default).  Returns
    two ``set_setting`` ops.
    """
    del guild
    common = {
        "source": "setup_ux:recommended",
        "confidence": "high",
        "risk": "low",
    }
    return [
        SetupOperation(
            kind="set_setting",
            subsystem=SUBSYSTEM,
            setting_name=SETTING_DM_ON_ACTION,
            value=True,
            metadata={**common, "reason": "Notify members why they were actioned"},
        ),
        SetupOperation(
            kind="set_setting",
            subsystem=SUBSYSTEM,
            setting_name=SETTING_REQUIRE_REASON,
            value=True,
            metadata={**common, "reason": "Require a reason for warn / kick / ban"},
        ),
    ]


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Moderation section entry — shows the section card."""
    from views.setup.section_card import show

    detected = (
        "Moderation behaviour (DM-on-action, required reason, warn escalation, "
        "moderator role) stays at its current values until you change it. "
        "Apply Recommended enables DM-on-action + require-a-reason; Customize "
        "tunes each knob."
    )
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: object = None,
    draft_rows: object = None,
) -> discord.Embed:
    """Wizard-native detail embed for the moderation step."""
    del session, draft_rows
    dm_on, require_reason, escalation, role_id = await _read_current_state(guild)
    return build_moderation_embed(
        dm_on_action=dm_on,
        require_reason=require_reason,
        warn_escalation_action=escalation,
        moderator_role_id=role_id,
        guild=guild,
    )


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: object = None,
) -> ModerationSectionView:
    """Wizard-native detail view for the moderation step."""
    del section, guild, session
    return ModerationSectionView(author)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Moderation",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🛡️",
        order=65,
        # ``set_setting`` is shared with other sections (identity, …) so
        # leaving op_kinds empty keeps cross-section badge pollution out;
        # progress is attributed by ``section_slug`` provenance (passed to
        # ``setup_draft.append`` above and set by the recommended path).
        op_kinds=frozenset(),
        description_if_skipped=(
            "Moderation keeps its current behaviour — no DM on action, reasons "
            "optional, warns escalate to a timeout at the threshold, and only "
            "Discord-permission holders can moderate. Configure later in "
            "`!settings → Moderation`."
        ),
        depths=frozenset({"standard", "advanced"}),
        recommended_ops_builder=_recommended_moderation_ops,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "ModerationSectionView",
    "SLUG",
    "SUBSYSTEM",
    "build_moderation_embed",
    "run",
]
