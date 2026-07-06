"""Access-policy explorer — read-only governance surface (Phase 6).

A diagnostic view that lets an operator see *why* a given member can
or cannot access a given subsystem in a given scope. The view is
strictly read-only — it composes existing governance reads:

* :func:`governance.resolve_subsystem_state` — produces a
  :class:`SubsystemEffectiveState` with the full ``ResolutionTrace``
  that the resolver already computes for diagnostics.
* :data:`utils.subsystem_registry.SUBSYSTEMS` — static metadata
  (tier requirement, visibility_mode, parent_hub).

No write surface. No new governance helper is introduced — the
existing ``resolve_subsystem_state`` already powers ``/why``-style
diagnostics, so this view is a UI on top of it.

Tier filtering
--------------

The subsystem select only lists subsystems the invoker can already see
(via ``governance.get_visible_subsystems``). An admin cannot use this
explorer to discover policies for subsystems they're not authorised to
view — that's the same airtight rule the rest of governance enforces.

Scope selection
---------------

A scope select narrows the explanation surface:

* **Channel** — full context (member, channel, category, guild)
* **Category** — same as Channel but without the channel-scope override
* **Guild** — guild-only context

For each scope, a synthetic :class:`GovernanceContext` is built and
passed through ``resolve_subsystem_state``. The decision chain falls
through scopes in priority order, so switching scope mainly affects
which override (if any) appears as the matched scope.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted
from utils.ui_constants import ADMIN_COLOR, UTILITY_COLOR
from views.base import HubView
from views.paginated_select import attach_windowed_select

logger = logging.getLogger("bot.views.access.explorer")


_SCOPE_LABELS = {
    "channel": "Channel (current)",
    "category": "Category (current)",
    "guild": "Guild (server-wide)",
}


def _resolve_default_subsystem_options(
    visible_subsystems: set[str],
) -> list[discord.SelectOption]:
    """Build select options for every subsystem the invoker can see.

    The full set can exceed Discord's 25-option select cap, so the caller
    *windows* these options (◀/▶ nav) rather than front-truncating — every
    visible subsystem stays selectable (the #1040 class).
    """
    options: list[discord.SelectOption] = []
    for name, meta in all_subsystems_sorted():
        if name not in visible_subsystems:
            continue
        options.append(
            discord.SelectOption(
                label=(meta.get("display_name") or name)[:100],
                value=name,
                description=(meta.get("description") or "")[:100] or None,
                emoji=meta.get("emoji") or None,
            ),
        )
    return options


async def _build_context_for_scope(
    interaction: discord.Interaction,
    scope: str,
):
    """Build a :class:`GovernanceContext` tuned to *scope*.

    Imported locally so the module loads without the heavy governance
    package at import time.
    """
    from governance.models import GovernanceContext

    base = GovernanceContext.from_interaction(interaction)
    if scope == "guild":
        return GovernanceContext(
            guild_id=base.guild_id,
            channel_id=None,
            category_id=None,
            thread_id=None,
            member=base.member,
            role_ids=set(base.role_ids),
        )
    if scope == "category":
        return GovernanceContext(
            guild_id=base.guild_id,
            channel_id=None,
            category_id=base.category_id,
            thread_id=None,
            member=base.member,
            role_ids=set(base.role_ids),
        )
    # Default — channel scope (full context)
    return base


def build_explorer_overview_embed(
    invoker: discord.Member | discord.User,
) -> discord.Embed:
    embed = discord.Embed(
        title="🔍 Access Policy Explorer",
        description=(
            "Read-only diagnostic for effective governance policy. "
            "Pick a subsystem and a scope, then press **Explain Access** "
            "to see the decision chain."
        ),
        color=UTILITY_COLOR,
    )
    invoker_name = getattr(invoker, "display_name", None) or str(invoker)
    embed.set_footer(
        text=(
            f"Invoker: {invoker_name}. Only the invoker can interact with this panel."
        ),
    )
    embed.add_field(
        name="Subsystem",
        value="_Pick from the first dropdown._",
        inline=True,
    )
    embed.add_field(
        name="Scope",
        value="_Pick from the second dropdown._",
        inline=True,
    )
    return embed


def build_explanation_embed(
    *,
    invoker: discord.Member | discord.User,
    subsystem: str,
    scope: str,
    effective: Any,
) -> discord.Embed:
    """Render an effective-state result as a decision-chain embed."""
    meta = SUBSYSTEMS.get(subsystem) or {}
    color = meta.get("color", ADMIN_COLOR.value)
    title = f"{meta.get('emoji', '🔍')} {meta.get('display_name', subsystem)}"
    state = getattr(effective.state, "value", str(effective.state))
    vis_source = getattr(
        effective.visibility_source,
        "value",
        str(effective.visibility_source),
    )
    trace = effective.trace
    checked_scopes = ", ".join(trace.checked_scopes) if trace.checked_scopes else "—"
    matched = (
        getattr(trace.matched_scope, "value", str(trace.matched_scope))
        if trace.matched_scope is not None
        else "—"
    )
    dependency_blocks = (
        ", ".join(effective.dependency_blocks) if effective.dependency_blocks else "—"
    )

    embed = discord.Embed(
        title=title,
        description=(
            f"**State:** `{state}`\n"
            f"**Effective for:** {invoker.mention} @ scope `{scope}`"
        ),
        color=color,
    )
    embed.add_field(
        name="Required tier",
        value=meta.get("visibility_tier", "—"),
        inline=True,
    )
    embed.add_field(
        name="Visibility mode",
        value=meta.get("visibility_mode", "—"),
        inline=True,
    )
    embed.add_field(
        name="parent_hub",
        value=meta.get("parent_hub") or "—",
        inline=True,
    )
    embed.add_field(
        name="Decision source",
        value=f"`{vis_source}`",
        inline=True,
    )
    embed.add_field(
        name="Matched scope",
        value=f"`{matched}`",
        inline=True,
    )
    embed.add_field(
        name="Dependency blocks",
        value=dependency_blocks,
        inline=True,
    )
    embed.add_field(
        name="Scopes inspected",
        value=checked_scopes,
        inline=False,
    )
    embed.set_footer(
        text="Diagnostic only — does not mutate governance state.",
    )
    return embed


def _attach_subsystem_select(
    view: AccessExplorerView,
    options: list[discord.SelectOption],
) -> None:
    """Attach the windowed subsystem picker to ``view``.

    The visible-subsystem set can exceed Discord's 25-option cap, so the
    options are *windowed* (◀/▶ nav) rather than front-truncated — every
    visible subsystem stays selectable (the #1040 class).
    """

    async def _on_pick(interaction: discord.Interaction, values: list[str]) -> None:
        if not values:
            return
        view.selected_subsystem = values[0]
        await interaction.response.edit_message(
            embed=view.build_overview_embed(),
            view=view,
        )

    attach_windowed_select(
        view,
        options,
        _on_pick,
        placeholder="Choose a subsystem…",
        select_row=0,
        nav_row=3,
    )


class _ScopeSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label=_SCOPE_LABELS["channel"],
                value="channel",
                description="The channel this command was invoked in.",
                default=True,
            ),
            discord.SelectOption(
                label=_SCOPE_LABELS["category"],
                value="category",
                description="The category that contains the channel.",
            ),
            discord.SelectOption(
                label=_SCOPE_LABELS["guild"],
                value="guild",
                description="Guild-level — no channel/category override.",
            ),
        ]
        super().__init__(
            placeholder="Choose a scope…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="access:select_scope",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccessExplorerView):
            return
        view.selected_scope = self.values[0]
        await interaction.response.edit_message(
            embed=view.build_overview_embed(),
            view=view,
        )


class AccessExplorerView(HubView):
    """Read-only access-policy explorer."""

    SUBSYSTEM = "settings"

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        visible_subsystems: set[str],
    ) -> None:
        super().__init__(author)
        self._visible_subsystems = set(visible_subsystems)
        self.selected_subsystem: str | None = None
        self.selected_scope: str = "channel"
        options = _resolve_default_subsystem_options(self._visible_subsystems)
        _attach_subsystem_select(self, options)
        self.add_item(_ScopeSelect())

    def build_overview_embed(self) -> discord.Embed:
        embed = build_explorer_overview_embed(self._author)
        subsystem_field = next(f for f in embed.fields if f.name == "Subsystem")
        scope_field = next(f for f in embed.fields if f.name == "Scope")
        embed.set_field_at(
            embed.fields.index(subsystem_field),
            name="Subsystem",
            value=self.selected_subsystem or "_Not selected._",
            inline=True,
        )
        embed.set_field_at(
            embed.fields.index(scope_field),
            name="Scope",
            value=_SCOPE_LABELS.get(self.selected_scope, self.selected_scope),
            inline=True,
        )
        return embed

    @discord.ui.button(
        label="🔬 Explain Access",
        style=discord.ButtonStyle.blurple,
        custom_id="access:explain",
        row=2,
    )
    async def btn_explain(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not self.selected_subsystem or self.selected_subsystem == "__none__":
            await interaction.response.send_message(
                "Pick a subsystem from the first dropdown before explaining.",
                ephemeral=True,
            )
            return
        # Confirm the invoker can still see the selected subsystem —
        # governance may have changed mid-session.
        if self.selected_subsystem not in self._visible_subsystems:
            await interaction.response.send_message(
                "That subsystem is no longer visible to you.",
                ephemeral=True,
            )
            return

        # Local imports keep this module import-safe.
        from governance import resolve_subsystem_state

        ctx = await _build_context_for_scope(interaction, self.selected_scope)
        try:
            effective = await resolve_subsystem_state(ctx, self.selected_subsystem)
        except Exception as exc:  # noqa: BLE001 — diagnostic must not crash
            logger.warning(
                "Access explorer: resolve_subsystem_state failed "
                "(subsystem=%r, scope=%r): %s",
                self.selected_subsystem,
                self.selected_scope,
                exc,
                exc_info=True,
            )
            await interaction.response.send_message(
                "Governance resolution failed — check bot logs.",
                ephemeral=True,
            )
            return

        embed = build_explanation_embed(
            invoker=self._author,
            subsystem=self.selected_subsystem,
            scope=self.selected_scope,
            effective=effective,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="🔄 Reset",
        style=discord.ButtonStyle.secondary,
        custom_id="access:reset",
        row=2,
    )
    async def btn_reset(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        self.selected_subsystem = None
        self.selected_scope = "channel"
        await interaction.response.edit_message(
            embed=self.build_overview_embed(),
            view=self,
        )
