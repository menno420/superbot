"""Access Map + Help Preview — staff-hub subpanels over the P1A projection.

Adaptive Setup **P1C** (consolidated plan Batch 5; Q-0032: staff-hub
subpanels only, **no new command names**): the first UI consumers of
:func:`services.access_projection.project_access_map`. Both panels are
**display-only** — zero writes, no mutation affordances; every row is a
projection over the existing policy owners (§6.2: "it creates no second
permission system").

* **Access Map** — per-feature effective access (allow / deny / unknown)
  for a **simulated audience tier** in the current channel, with a
  per-feature drill-down showing the decision's source chain.
* **Help Preview** — what Help advertises to that audience: advertised /
  shown-as-locked (with the user-safe reason) / hidden, rendered honestly
  per §16.4.

Audience simulation rides the Q-0045 declared-tier path
(``AccessContext.member_tier``, no real member) and must carry the §16.4
limit label: a declared tier cannot model live Discord channel-permission
overrides it was not given.

Authority (ADR-005 / ``docs/capability-authority.md`` §4): like the parent
hub, the panels are **authority-gated, not ownership-gated** — the
administrator floor is re-evaluated live on every interaction, so a
restored/long-lived panel can never outlive the clicker's authority.
"""

from __future__ import annotations

import logging

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services.access_projection import (
    AccessContext,
    AccessDecision,
    project_access_map,
)
from utils.ui_constants import ADMIN_COLOR
from views.base import BaseView, interaction_is_admin

logger = logging.getLogger("bot.views.server_management.access_map")

# §16.4 — every simulated rendering carries this label.
SIMULATION_LIMIT_NOTE = (
    "Simulated audience (declared tier) — cannot model live Discord "
    "channel-permission overrides it was not given."
)

# The §6.3 simulation audiences (sub-owner tiers an operator previews as).
_AUDIENCE_TIERS: tuple[tuple[str, str], ...] = (
    ("user", "Normal member"),
    ("trusted", "Trusted user"),
    ("staff", "Staff"),
    ("moderator", "Moderator"),
    ("administrator", "Administrator"),
)

_STATE_GLYPH = {"allow": "✅", "deny": "❌", "unknown": "❓"}
_FIELD_CAP = 1024


def _simulated_context(
    guild_id: int,
    channel_id: int | None,
    tier: str,
) -> AccessContext:
    """The declared-tier projection input both panels share (Q-0045 path)."""
    return AccessContext(
        guild_id=guild_id,
        channel_id=channel_id,
        member=None,
        member_tier=tier,
        invocation_type="prefix",
    )


def _chunk_field(
    embed: discord.Embed,
    name: str,
    lines: list[str],
) -> None:
    """Add ``lines`` as one or more fields, respecting the 1024-char cap."""
    if not lines:
        return
    chunk: list[str] = []
    size = 0
    part = 1
    for line in lines:
        if size + len(line) + 1 > _FIELD_CAP and chunk:
            embed.add_field(
                name=name if part == 1 else f"{name} (cont.)",
                value="\n".join(chunk),
                inline=False,
            )
            chunk, size, part = [], 0, part + 1
        chunk.append(line)
        size += len(line) + 1
    embed.add_field(
        name=name if part == 1 else f"{name} (cont.)",
        value="\n".join(chunk),
        inline=False,
    )


def _tier_label(tier: str) -> str:
    return next((label for t, label in _AUDIENCE_TIERS if t == tier), tier)


async def build_access_map_embed(
    guild_id: int,
    channel_id: int | None,
    tier: str,
) -> tuple[discord.Embed, tuple[AccessDecision, ...]]:
    """Render the per-feature effective-access table for ``tier``."""
    decisions = await project_access_map(
        _simulated_context(guild_id, channel_id, tier),
    )
    embed = discord.Embed(
        title="🔓 Access Map",
        description=(
            f"Effective feature access for a **{_tier_label(tier)}** in this "
            "channel — a read-only projection over the live policy owners "
            "(command access · routing · governance · help)."
        ),
        color=ADMIN_COLOR,
    )
    allowed = [d.feature for d in decisions if d.effective == "allow"]
    unknown = [d.feature for d in decisions if d.effective == "unknown"]
    denied_lines = []
    for d in decisions:
        if d.effective != "deny":
            continue
        axis = d.deciding_axis.value if d.deciding_axis else "?"
        reason = d.reason.safe_text if d.reason else "denied"
        denied_lines.append(f"❌ **{d.feature}** — {reason} *(axis: {axis})*")

    if allowed:
        _chunk_field(embed, f"✅ Allowed ({len(allowed)})", ["· ".join(allowed)])
    _chunk_field(embed, f"❌ Denied ({len(denied_lines)})", denied_lines)
    if unknown:
        _chunk_field(embed, f"❓ Unresolved ({len(unknown)})", ["· ".join(unknown)])
    embed.add_field(name="Simulation limits", value=SIMULATION_LIMIT_NOTE, inline=False)
    embed.set_footer(text="Read-only · pick a feature below for the full source chain")
    return embed, decisions


async def build_help_preview_embed(
    guild_id: int,
    channel_id: int | None,
    tier: str,
) -> discord.Embed:
    """Render what Help advertises to a simulated ``tier`` audience (§6.3).

    Buckets per §16.4's honest rendering: **advertised** (help shows it and
    the audience may use it), **shown as locked** (help shows it but an axis
    denies — with the user-safe reason only), **hidden** (help does not show
    it to this audience).
    """
    decisions = await project_access_map(
        _simulated_context(guild_id, channel_id, tier),
    )
    advertised: list[str] = []
    locked_lines: list[str] = []
    hidden: list[str] = []
    for d in decisions:
        help_axis = next(
            (o for o in d.source_chain if o.axis.value == "help"),
            None,
        )
        help_shown = help_axis is not None and help_axis.state == "shown"
        if not help_shown:
            hidden.append(d.feature)
        elif d.effective == "deny":
            reason = d.reason.safe_text if d.reason else "locked"
            locked_lines.append(f"🔒 **{d.feature}** — {reason}")
        else:
            advertised.append(d.feature)

    embed = discord.Embed(
        title="👁 Help Preview",
        description=(
            f"What Help advertises to a **{_tier_label(tier)}** in this "
            "channel. Display-only — the live Help command stays the renderer "
            "of record."
        ),
        color=ADMIN_COLOR,
    )
    if advertised:
        _chunk_field(
            embed,
            f"📣 Advertised ({len(advertised)})",
            ["· ".join(advertised)],
        )
    _chunk_field(embed, f"🔒 Shown as locked ({len(locked_lines)})", locked_lines)
    if hidden:
        _chunk_field(embed, f"🙈 Hidden ({len(hidden)})", ["· ".join(hidden)])
    embed.add_field(name="Simulation limits", value=SIMULATION_LIMIT_NOTE, inline=False)
    embed.set_footer(text="Read-only preview · simulated audience")
    return embed


class _AudienceTierSelect(discord.ui.Select):
    """Switch the simulated audience tier; the panel re-renders in place."""

    def __init__(self, current_tier: str) -> None:
        super().__init__(
            placeholder="Simulate audience…",
            options=[
                discord.SelectOption(
                    label=label,
                    value=tier,
                    default=tier == current_tier,
                )
                for tier, label in _AUDIENCE_TIERS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _AccessPanelBase = self.view  # type: ignore[assignment]
        await view.rerender(interaction, tier=self.values[0])


class _FeatureDetailSelect(discord.ui.Select):
    """Drill into one feature's full decision source chain (ephemeral)."""

    def __init__(self, decisions: tuple[AccessDecision, ...]) -> None:
        options = [
            discord.SelectOption(
                label=f"{_STATE_GLYPH.get(d.effective, '·')} {d.feature}"[:100],
                value=d.feature,
            )
            for d in decisions[:25]  # Discord's option cap; map shows the rest
        ]
        super().__init__(
            placeholder="Inspect a feature's source chain…",
            options=options
            or [
                discord.SelectOption(label="(no features)", value="-"),
            ],
        )
        self._by_feature = {d.feature: d for d in decisions}

    async def callback(self, interaction: discord.Interaction) -> None:
        decision = self._by_feature.get(self.values[0])
        if decision is None:
            await interaction.response.send_message(
                "That feature is not in the current projection.",
                ephemeral=True,
            )
            return
        lines = [
            f"`{o.axis.value}` → **{o.state}**" + (f" — {o.detail}" if o.detail else "")
            for o in decision.source_chain
        ]
        embed = discord.Embed(
            title=f"Source chain — {decision.feature}",
            description="\n".join(lines)[:4000],
            color=ADMIN_COLOR,
        )
        if decision.reason is not None:
            embed.add_field(
                name="User-safe reason",
                value=decision.reason.safe_text,
                inline=False,
            )
        if decision.remediation:
            embed.add_field(
                name="Remediation",
                value=decision.remediation,
                inline=False,
            )
        embed.set_footer(text=SIMULATION_LIMIT_NOTE)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _AccessPanelBase(BaseView):
    """Shared shell: authority gate + tier switching + in-place rerender.

    ``public=True`` disables BaseView's ownership lock on purpose — the
    panel lives on the shared hub message; the gate below is **authority**
    (administrator floor, re-checked live on every interaction), the
    ModPanelView / ServerManagementHubView pattern.
    """

    def __init__(self, author: discord.abc.User, *, tier: str = "user") -> None:
        super().__init__(author, public=True)
        self.tier = tier

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction_is_admin(interaction):
            return True
        await interaction.response.send_message(
            "❌ You need **Administrator** permission to use this panel.",
            ephemeral=True,
        )
        return False

    async def rerender(
        self,
        interaction: discord.Interaction,
        *,
        tier: str,
    ) -> None:  # pragma: no cover - overridden by both panels
        raise NotImplementedError


class AccessMapView(_AccessPanelBase):
    """The read-only Access Map subpanel (P1C)."""

    def __init__(
        self,
        author: discord.abc.User,
        decisions: tuple[AccessDecision, ...],
        *,
        tier: str = "user",
    ) -> None:
        super().__init__(author, tier=tier)
        self.add_item(_AudienceTierSelect(tier))
        self.add_item(_FeatureDetailSelect(decisions))

    async def rerender(
        self,
        interaction: discord.Interaction,
        *,
        tier: str,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This panel is only available inside a server.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction):
            return
        embed, decisions = await build_access_map_embed(
            interaction.guild.id,
            getattr(interaction.channel, "id", None),
            tier,
        )
        view = AccessMapView(interaction.user, decisions, tier=tier)
        _copy_back_button(self, view)
        await safe_edit(interaction, embed=embed, view=view)


class HelpPreviewView(_AccessPanelBase):
    """The read-only Help Preview subpanel (P1C)."""

    def __init__(self, author: discord.abc.User, *, tier: str = "user") -> None:
        super().__init__(author, tier=tier)
        self.add_item(_AudienceTierSelect(tier))

    async def rerender(
        self,
        interaction: discord.Interaction,
        *,
        tier: str,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This panel is only available inside a server.",
                ephemeral=True,
            )
            return
        if not await safe_defer(interaction):
            return
        embed = await build_help_preview_embed(
            interaction.guild.id,
            getattr(interaction.channel, "id", None),
            tier,
        )
        view = HelpPreviewView(interaction.user, tier=tier)
        _copy_back_button(self, view)
        await safe_edit(interaction, embed=embed, view=view)


def _copy_back_button(old: discord.ui.View, new: discord.ui.View) -> None:
    """Carry the hub's attached back button across a tier re-render."""
    for item in old.children:
        custom_id = getattr(item, "custom_id", None)
        if custom_id == "server_management:back":
            new.add_item(item)
            return


__all__ = [
    "SIMULATION_LIMIT_NOTE",
    "AccessMapView",
    "HelpPreviewView",
    "build_access_map_embed",
    "build_help_preview_embed",
]
