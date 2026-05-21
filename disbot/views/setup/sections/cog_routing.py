"""Cog routing section — drafts per-scope per-cog enable/disable overrides.

Stages ``SetupOperation(kind="set_cog_routing", ...)`` drafts.  The
runtime resolver :func:`services.command_routing.is_cog_enabled`
walks ``channel → category → guild → default-true`` so a fresh guild
(no policy rows) gets every cog enabled — routing only restricts.

UX mirrors the cleanup section: operator picks a scope (guild
default / category override / channel override), picks a cog from the
SUBSYSTEMS registry, picks Enable or Disable, and the pick stages a
``set_cog_routing`` op.  Final Review's dispatcher routes the staged
op through :func:`services.command_routing.set_policy` and emits
``audit.action_recorded`` for visibility in the audit channel.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_session
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from utils.subsystem_registry import SUBSYSTEMS
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.cog_routing")

SLUG = "cog_routing"


SCOPE_OPTIONS: list[discord.SelectOption] = [
    discord.SelectOption(
        label="Guild default",
        value="guild",
        description="Enable / disable a cog server-wide.",
        emoji="🌐",
    ),
    discord.SelectOption(
        label="Category override",
        value="category",
        description="Override one category; channels inherit unless overridden.",
        emoji="📁",
    ),
    discord.SelectOption(
        label="Channel override",
        value="channel",
        description="Override one specific channel.",
        emoji="📡",
    ),
]


def _operator_visible_cogs() -> list[str]:
    """Return SUBSYSTEMS keys whose visibility is not internal.

    Capped at Discord's 25-option select limit so the operator-facing
    pick always fits a single select.
    """
    visible = [
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode", "normal") != "internal"
    ]
    visible.sort()
    return visible[:25]


def _cog_options() -> list[discord.SelectOption]:
    """Build Discord SelectOption entries for the visible cogs."""
    options: list[discord.SelectOption] = []
    for name in _operator_visible_cogs():
        meta = SUBSYSTEMS.get(name, {})
        label = meta.get("display_name", name)[:100]
        description = (meta.get("description") or "")[:100] or None
        options.append(
            discord.SelectOption(
                label=label,
                value=name,
                description=description,
                emoji=meta.get("emoji"),
            ),
        )
    return options or [
        discord.SelectOption(label="(no subsystems)", value="_none"),
    ]


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_cog_routing_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧭 Cog routing",
        description=(
            "Enable or disable cogs per scope.  The resolver walks "
            "**channel → category → guild → default-true** — a fresh "
            "server has every cog enabled and routing only restricts.  "
            "Each pick stages a `set_cog_routing` operation; nothing "
            "applies until Final review."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="How to use",
        value=(
            "1. Pick a scope.\n"
            "2. (Category / channel scopes) pick the target.\n"
            "3. Pick the cog.\n"
            "4. Pick Enable or Disable."
        ),
        inline=False,
    )
    embed.set_footer(text="Cogs default to enabled; this section creates exceptions.")
    return embed


# ---------------------------------------------------------------------------
# Enable / Disable selection
# ---------------------------------------------------------------------------


class _EnableDisableSelect(discord.ui.Select):
    """Final step — flips the cog enabled flag and stages the op."""

    def __init__(
        self,
        *,
        scope_kind: str,
        scope_id: int | None,
        scope_name: str,
        cog_name: str,
    ) -> None:
        super().__init__(
            placeholder=f"Enable or disable {cog_name}…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Enable", value="enable", emoji="✅"),
                discord.SelectOption(label="Disable", value="disable", emoji="🚫"),
            ],
        )
        self._scope_kind = scope_kind
        self._scope_id = scope_id
        self._scope_name = scope_name
        self._cog_name = cog_name

    async def callback(self, interaction: discord.Interaction) -> None:
        enabled = self.values[0] == "enable"
        await _stage_cog_routing(
            interaction,
            scope_kind=self._scope_kind,
            scope_id=self._scope_id,
            scope_name=self._scope_name,
            cog_name=self._cog_name,
            enabled=enabled,
        )


class _CogPickSelect(discord.ui.Select):
    """Cog picker — pre-scoped to the operator's earlier pick."""

    def __init__(
        self,
        *,
        scope_kind: str,
        scope_id: int | None,
        scope_name: str,
    ) -> None:
        super().__init__(
            placeholder=f"Pick a cog for {scope_kind} scope…",
            min_values=1,
            max_values=1,
            options=_cog_options(),
        )
        self._scope_kind = scope_kind
        self._scope_id = scope_id
        self._scope_name = scope_name

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = self.values[0]
        if cog == "_none":
            await interaction.response.send_message(
                "No visible subsystems registered.",
                ephemeral=True,
            )
            return
        view = BaseView(interaction.user, public=False, timeout=120)
        view.add_item(
            _EnableDisableSelect(
                scope_kind=self._scope_kind,
                scope_id=self._scope_id,
                scope_name=self._scope_name,
                cog_name=cog,
            ),
        )
        await interaction.response.send_message(
            f"Enable or disable `{cog}` in {self._scope_kind} `{self._scope_name}`?",
            view=view,
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Scope-picker view
# ---------------------------------------------------------------------------


class _CategoryPickSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a category…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=120)
        view.add_item(
            _CogPickSelect(
                scope_kind="category",
                scope_id=picked.id,
                scope_name=picked.name,
            ),
        )
        await interaction.response.send_message(
            f"Pick a cog to override in category **{picked.name}**:",
            view=view,
            ephemeral=True,
        )


class _ChannelPickSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=120)
        view.add_item(
            _CogPickSelect(
                scope_kind="channel",
                scope_id=picked.id,
                scope_name=picked.name,
            ),
        )
        await interaction.response.send_message(
            f"Pick a cog to override in #{picked.name}:",
            view=view,
            ephemeral=True,
        )


class _ScopeSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a scope…",
            min_values=1,
            max_values=1,
            options=SCOPE_OPTIONS,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        scope = self.values[0]
        if scope == "guild":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(
                _CogPickSelect(
                    scope_kind="guild",
                    scope_id=None,
                    scope_name="guild",
                ),
            )
            await interaction.response.send_message(
                "Pick a cog to set the guild default for:",
                view=view,
                ephemeral=True,
            )
            return
        if scope == "category":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(_CategoryPickSelect())
            await interaction.response.send_message(
                "Pick a category:",
                view=view,
                ephemeral=True,
            )
            return
        if scope == "channel":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(_ChannelPickSelect())
            await interaction.response.send_message(
                "Pick a channel:",
                view=view,
                ephemeral=True,
            )
            return


class CogRoutingSectionView(BaseView):
    """Entry view — hosts the scope-picker dropdown."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_ScopeSelect())


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


async def _stage_cog_routing(
    interaction: discord.Interaction,
    *,
    scope_kind: str,
    scope_id: int | None,
    scope_name: str,
    cog_name: str,
    enabled: bool,
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Cog routing edits require a guild context.",
            ephemeral=True,
        )
        return

    action_word = "enable" if enabled else "disable"
    op = SetupOperation(
        kind="set_cog_routing",
        subsystem="cog_routing",
        target_id=scope_id,
        target_name=scope_name,
        target_kind=scope_kind,
        value=cog_name,
        metadata={
            "source": "manual",
            "confidence": "high",
            "reason": (
                f"Operator chose to {action_word} `{cog_name}` for "
                f"{scope_kind} `{scope_name}`"
            ),
            "risk": "medium",
            "rollback_note": (
                f"Re-stage with the opposite flag, or delete the "
                f"command_routing_policy row for "
                f"({scope_kind}, {scope_id}, {cog_name})"
            ),
            "enabled": "true" if enabled else "false",
        },
    )
    label = (
        f"cog_routing.{scope_kind}({scope_name}).{cog_name} = "
        f"{'enabled' if enabled else 'disabled'}"
    )
    try:
        await setup_draft.append(
            op,
            guild_id=guild.id,
            actor_id=interaction.user.id,
            label=label,
        )
    except Exception:
        logger.exception("cog_routing: setup_draft.append failed")
        await interaction.response.send_message(
            "Could not stage the routing policy — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("cog_routing: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("cog_routing: setup_draft.count failed")
        pending = 0

    await interaction.response.send_message(
        (
            f"✅ Staged for Final review: `{label}`.  "
            f"Pending operations: **{pending}**."
        ),
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry point
# ---------------------------------------------------------------------------


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Cog routing section requires a guild context.",
            ephemeral=True,
        )
        return

    embed = build_cog_routing_embed()
    view = CogRoutingSectionView(interaction.user)
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Cog routing",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🧭",
        order=70,
        op_kinds=frozenset({"set_cog_routing"}),
    ),
)


__all__ = [
    "CogRoutingSectionView",
    "SLUG",
    "build_cog_routing_embed",
    "run",
]
