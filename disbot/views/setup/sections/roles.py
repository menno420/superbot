"""Roles section — drafts time- and XP-based auto-role thresholds.

Lets an operator wire up automatic role progression during setup: pick
a role, then say "members reach it after N days in the server" (time
tier) or "at XP level N" (XP tier).  Each submission stages a
``SetupOperation(kind="set_role_threshold", subsystem="roles", …)``
draft; Final Review's dispatcher routes it through the audited
``services.role_automation.set_{time,xp}_threshold`` seam (a service,
not a raw DB write), which captures the role id so a later rename does
not orphan the tier (PR6 id-groundwork).

The section configures thresholds for **existing** roles — role
*creation* stays owned by resource provisioning / the role lifecycle
service (the wizard never opens a second resource-creation path).  The
fuller per-tier management (clearing tiers, stale-role diagnostics,
seed defaults) lives in the role-automation panels (``!roles``); the
wizard surfaces only the "set one tier" path so the detail view stays
two rows (usable as both the section-card *Customize* view and the
wizard-native step-detail view; row 4 is reserved by ``wizard_nav``).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_session
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.roles")

SLUG = "roles"
SUBSYSTEM = "roles"

# Threshold sub-kinds — carried on ``SetupOperation.setting_name`` and
# read by the dispatcher's ``_apply_set_role_threshold`` arm.
KIND_TIME = "time"
KIND_XP = "xp"

_MAX_DAYS = 3650  # ~10 years — a generous sanity ceiling
_MAX_LEVEL = 1000


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_roles_embed(*, current_summary: str | None = None) -> discord.Embed:
    """Build the roles section embed.

    ``current_summary`` (when supplied) renders a **Detected** field
    listing today's configured tiers; ``None`` renders the static
    explainer used on the section card.
    """
    embed = discord.Embed(
        title="🎖️ Auto roles (time & XP)",
        description=(
            "Automatically grant a role when a member has been in the server "
            "long enough (**time tier**) or reaches an **XP level** (XP tier). "
            "Pick a role below, then enter the threshold — each submission "
            "stages a `set_role_threshold` operation that **Final review** "
            "applies through the audited role-automation seam."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="How it works",
        value=(
            "• **Time tier** — granted after N days in the server\n"
            "• **XP tier** — granted at XP level N (auto-assigned)\n"
            "• Configure each tier for an **existing** role; create roles "
            "first in Discord or via the role manager."
        ),
        inline=False,
    )
    if current_summary is not None:
        embed.add_field(
            name="Detected",
            value=current_summary or "_(no auto-role tiers configured yet)_",
            inline=False,
        )
    embed.set_footer(
        text="Final Review applies all staged tiers · clear/edit tiers in !roles.",
    )
    return embed


# ---------------------------------------------------------------------------
# Threshold modals
# ---------------------------------------------------------------------------


class _TimeDaysModal(discord.ui.Modal, title="Set time tier (days)"):
    days: discord.ui.TextInput = discord.ui.TextInput(
        label="Days in server before the role is granted",
        placeholder="7",
        min_length=1,
        max_length=4,
        required=True,
    )

    def __init__(self, *, role_id: int, role_name: str) -> None:
        super().__init__()
        self._role_id = role_id
        self._role_name = role_name

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = _parse_positive_int((self.days.value or "").strip(), _MAX_DAYS)
        if value is None:
            await interaction.response.send_message(
                f"⚠️ Enter a whole number of days between 1 and {_MAX_DAYS}.",
                ephemeral=True,
            )
            return
        await _stage_threshold(
            interaction,
            kind=KIND_TIME,
            role_id=self._role_id,
            role_name=self._role_name,
            value=value,
            label=f"role tier: @{self._role_name} after {value}d",
        )


class _XpLevelModal(discord.ui.Modal, title="Set XP tier (level)"):
    level: discord.ui.TextInput = discord.ui.TextInput(
        label="XP level at which the role is granted",
        placeholder="10",
        min_length=1,
        max_length=4,
        required=True,
    )

    def __init__(self, *, role_id: int, role_name: str) -> None:
        super().__init__()
        self._role_id = role_id
        self._role_name = role_name

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = _parse_positive_int((self.level.value or "").strip(), _MAX_LEVEL)
        if value is None:
            await interaction.response.send_message(
                f"⚠️ Enter a whole number level between 1 and {_MAX_LEVEL}.",
                ephemeral=True,
            )
            return
        await _stage_threshold(
            interaction,
            kind=KIND_XP,
            role_id=self._role_id,
            role_name=self._role_name,
            value=value,
            label=f"role tier: @{self._role_name} at XP level {value}",
        )


def _parse_positive_int(raw: str, ceiling: int) -> int | None:
    """Return a positive int within ``[1, ceiling]`` or ``None``."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    if value < 1 or value > ceiling:
        return None
    return value


# ---------------------------------------------------------------------------
# Role pickers — each opens the matching threshold modal
# ---------------------------------------------------------------------------


class _TimeRoleSelect(discord.ui.RoleSelect):
    """Pick the role to grant on a time-in-server tier."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Time tier: pick a role to grant after N days…",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        role = self.values[0]
        await interaction.response.send_modal(
            _TimeDaysModal(role_id=role.id, role_name=role.name),
        )


class _XpRoleSelect(discord.ui.RoleSelect):
    """Pick the role to grant at an XP level."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="XP tier: pick a role to grant at a level…",
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        role = self.values[0]
        await interaction.response.send_modal(
            _XpLevelModal(role_id=role.id, role_name=role.name),
        )


class RolesSectionView(BaseView):
    """Detail view — a time-tier role picker and an XP-tier role picker.

    Used both as the section card's *Customize* target and the
    wizard-native step-detail view, so it stays within rows 0–3 (row 4
    is reserved by ``views.setup.wizard_nav.render_step_detail``).
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_TimeRoleSelect())
        self.add_item(_XpRoleSelect())


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


async def _stage_threshold(
    interaction: discord.Interaction,
    *,
    kind: str,
    role_id: int,
    role_name: str,
    value: int,
    label: str,
) -> None:
    """Stage one ``set_role_threshold`` op into the guild's draft."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Role-tier edits require a guild context.",
            ephemeral=True,
        )
        return

    unit = "days in server" if kind == KIND_TIME else "XP level"
    op = SetupOperation(
        kind="set_role_threshold",
        subsystem=SUBSYSTEM,
        setting_name=kind,
        # The draft's replace-on-conflict slot key is
        # (op_kind, subsystem, setting_name, binding_name) — it does NOT
        # include target_id.  Without a per-role discriminator, staging a
        # time tier for role A then role B would collide on
        # (set_role_threshold, roles, "time", '') and the second would
        # overwrite the first.  Encode the role id into binding_name so each
        # role's tier is its own slot (re-editing the *same* role's same-kind
        # tier still replaces, which is correct).  The dispatcher reads
        # setting_name/target_id, never binding_name, so this is slot-only.
        binding_name=f"tier:{role_id}",
        target_id=role_id,
        target_name=role_name,
        target_kind="role",
        value=value,
        metadata={
            "source": "manual",
            "confidence": "high",
            "reason": f"Operator set @{role_name} to {value} {unit}",
            "risk": "medium",
            "rollback_note": (
                f"Clear this tier for @{role_name} in `!roles`, or re-stage a "
                "different value."
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
        logger.exception("roles: setup_draft.append failed")
        await interaction.response.send_message(
            "Could not stage the role tier — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("roles: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("roles: setup_draft.count failed")
        pending = 0

    await interaction.response.send_message(
        f"✅ Staged for Final review: `{label}`.  Pending operations: **{pending}**.",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _read_current_summary(guild: discord.Guild) -> str | None:
    """Best-effort one-line summary of configured auto-role tiers.

    Returns ``None`` on failure (the snapshot is informational and must
    never block the render).
    """
    try:
        from utils.db import roles as roles_db

        rows = await roles_db.get_role_thresholds(guild.id)
    except Exception:
        logger.exception("roles: get_role_thresholds failed")
        return None

    lines: list[str] = []
    for row in rows:
        name = row.get("display_name") or row.get("role_name") or "?"
        days = row.get("days_required") or 0
        level = row.get("level_required")
        if days:
            lines.append(f"• @{name} — after **{days}d**")
        if level is not None and row.get("xp_auto_assign"):
            lines.append(f"• @{name} — at **XP level {level}**")
    if not lines:
        return ""
    return "\n".join(lines[:10])


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the detailed roles picker (the card's Customize target)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Roles section requires a guild context.",
            ephemeral=True,
        )
        return

    summary = await _read_current_summary(guild)
    embed = build_roles_embed(current_summary=summary)
    view = RolesSectionView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Roles section entry — shows the section card.

    No auto-recommended path: which role maps to which threshold is
    server-specific, so there is no safe default to stage.  Operators
    configure each tier via Customize.
    """
    from views.setup.section_card import show

    detected = (
        "Time / XP auto-role tiers stay at their current values until you "
        "change them. Click Customize to grant a role after N days in the "
        "server or at an XP level; manage existing tiers in `!roles`."
    )
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
        recommended_ops_builder=None,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: object = None,
    draft_rows: object = None,
) -> discord.Embed:
    """Wizard-native detail embed for the roles step."""
    del session, draft_rows
    summary = await _read_current_summary(guild)
    return build_roles_embed(current_summary=summary)


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: object = None,
) -> RolesSectionView:
    """Wizard-native detail view for the roles step."""
    del section, guild, session
    return RolesSectionView(author)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Auto roles (time & XP)",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🎖️",
        order=55,
        # ``set_role_threshold`` is roles-specific, so it is safe to declare
        # for accurate per-section progress badges (unlike the shared
        # ``set_setting``).
        op_kinds=frozenset({"set_role_threshold"}),
        description_if_skipped=(
            "No automatic role progression is configured — members keep "
            "whatever roles they have. You can set time / XP tiers later in "
            "`!roles` without re-running the wizard."
        ),
        depths=frozenset({"standard", "advanced"}),
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "RolesSectionView",
    "SLUG",
    "SUBSYSTEM",
    "build_roles_embed",
    "run",
]
