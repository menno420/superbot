"""Help category index view (decomposed from help_cog).

:class:`HelpCategoryView` is the persistent view ``!help`` opens — the
mother-hub category index. Selecting a hub swaps the message in place to
that hub's panel (via :func:`cogs.help.route.open_route`) with a
"↩ Back to Help" button appended.

The legacy paginated "All Commands / Advanced" browser (``HelpPanelView``)
was removed once every subsystem was homed into a hub — it only re-listed
the hub hosts, redundant with this index (owner decision, 2026-06-22, PR
#1294). Every feature is reachable through its hub in ≤2 clicks.

Cycle discipline: imports of ``cogs.help_cog`` helpers
(``_resolve_projection`` / ``_attach_back_to_help_button``) are
**function-local and late-bound** — the same pattern ``cogs.help.route``
uses — so the import graph stays acyclic and test monkeypatches on the
``help_cog`` module keep biting.
"""

from __future__ import annotations

import logging

import discord

from cogs.help.route import HelpOpener
from cogs.help.route import open_route as _open_route
from cogs.help.route import resolve_route as _resolve_route
from core.runtime.persistent_views import PersistentView, register
from services.governance_service import GovernanceContext
from services.help_projection import HelpProjection

logger = logging.getLogger("bot")


@register
class HelpCategoryView(PersistentView):
    """Top-level Help — mother-hub category index (S3).

    The surface ``!help`` opens. The dropdown shows one option per visible
    mother hub; selecting one swaps the view in place to that hub's panel.

    Stateless aside from ``_projection`` cached at construction time so the
    dropdown options match the user's effective access (HLP-2: hub tier
    floor **and** host-subsystem governance visibility — the same seam every
    other Help path consumes). The select callback re-resolves visibility
    before opening a hub so a user who lost a tier between Help renders gets
    the current state, not the stale snapshot.

    ``member_tier`` (without a projection) falls back to the static
    registry-defaults projection — persistent-view restore symmetry and
    tests only; live callers pass ``projection``.
    """

    SUBSYSTEM = "help"
    PANEL_ID = "help:categories"

    def __init__(
        self,
        member_tier: str | None = None,
        *,
        projection: HelpProjection | None = None,
    ) -> None:
        super().__init__()
        self._projection = projection or HelpProjection.registry_defaults(
            member_tier or "user",
        )
        self._rebuild_items()

    def _rebuild_items(self) -> None:
        self.clear_items()
        options: list[discord.SelectOption] = []
        for hub in self._projection.visible_hubs():
            options.append(
                discord.SelectOption(
                    label=hub.display_name[:100],
                    value=hub.key,
                    description=hub.purpose[:100],
                    emoji=hub.emoji or None,
                ),
            )
        select = discord.ui.Select(  # type: ignore[var-annotated]
            custom_id="help_categories:select",
            placeholder="Pick a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        select.callback = self._on_select  # type: ignore[method-assign]
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        # Late-bound to cogs.help_cog (the canonical patch seam for tests).
        from cogs.help_cog import _attach_back_to_help_button, _resolve_projection

        value = interaction.data["values"][0]  # type: ignore[typeddict-item]

        # Re-resolve governance at click time so the user's current
        # visibility/tier drives the next view, not the snapshot from
        # when the category panel was first rendered.
        gctx = GovernanceContext.from_interaction(interaction)
        projection = await _resolve_projection(gctx)

        opener = HelpOpener.from_interaction(interaction)
        route = _resolve_route(value, bot=opener.client)

        if route.kind == "unknown":
            await interaction.response.send_message(
                "That category is no longer available.",
                ephemeral=True,
            )
            return

        embed, sub_view = await _open_route(
            route,
            opener,
            projection=projection,
        )

        if sub_view is None:
            # Embed-only fallback (e.g. hub builder failed) — surface as
            # an ephemeral so the category panel stays intact.
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
            return

        # Attach Back-to-Help on every interactive surface opened from
        # the category index so the user has a one-click return.
        _attach_back_to_help_button(sub_view)
        await interaction.response.edit_message(embed=embed, view=sub_view)


__all__ = [
    "HelpCategoryView",
]
