"""BTD6 persistent panel.

The view lives under ``views/btd6/`` (Pattern B) so the cog file
stays small. Importing this module triggers the ``@register``
decorator side-effect on :class:`BTD6PanelView`; the persistent
view registry then resolves the ``btd6`` subsystem when
``on_ready`` restores anchors.

Menu Layout B (category hub, owner-picked 2026-07-01 via
``tools/btd6/menu_layout_simulator.html``; design study in
``docs/btd6/btd6-menu-layout-design-2026-07-01.md``): eight labelled
subdivisions instead of the old 13-button wall. **Ask** opens a modal;
every other button opens an ephemeral sub-panel
(:mod:`views.btd6.hub_panels`) for that subdivision — so every function
is 1–2 clicks away. Staff actions sit behind **🛠️ Admin**. Natural-language
replies are owned by the AI Platform's central stage — this panel never
invokes a provider.
"""

from __future__ import annotations

from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup
from core.runtime.persistent_views import PersistentView, register
from services import btd6_ai_service
from utils.discord_permissions import is_staff_member

_PANEL_COLOR = discord.Color.green()


# ---------------------------------------------------------------------------
# Ask modal
# ---------------------------------------------------------------------------


class BTD6AskModal(discord.ui.Modal, title="Ask BTD6 Assistant"):
    """Modal that takes a free-form BTD6 question and renders a deterministic answer."""

    question: discord.ui.TextInput = discord.ui.TextInput(
        label="Your question",
        placeholder="e.g. how do I survive round 63?",
        max_length=300,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from cogs.btd6._embeds import response_to_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        response = await btd6_ai_service.answer_question(str(self.question.value))
        await safe_followup(
            interaction,
            embed=response_to_embed(response),
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Panel embed
# ---------------------------------------------------------------------------


def _format_currently_active_from_vm(
    vm_active: tuple[Any, ...],
) -> str:
    """One line per kind in useful-first order; '—' for missing kinds.

    Each line now leads with a per-kind freshness badge (PR 1):
    ``🟢/🟡/🔴/⚪`` reflects how stale the latest fact for that kind is.
    Missing kinds render ``⚪`` (never fetched).
    """
    from cogs.btd6._freshness_render import BUCKET_EMOJI
    from utils.btd6.event_window import format_ends_relative

    lines: list[str] = []
    for active in vm_active:
        badge = BUCKET_EMOJI.get(active.freshness.state, "⚪")
        if active.name is None:
            lines.append(
                f"{badge} {active.emoji} `{active.short_kind:<8}` —",
            )
            continue
        ends = format_ends_relative(active.end_ms)
        name_str = str(active.name)[:60]
        suffix = f" {ends}" if ends else ""
        lines.append(
            f"{badge} {active.emoji} `{active.short_kind:<8}` `{name_str}`{suffix}",
        )
    return "\n".join(lines)


async def build_btd6_panel_embed() -> discord.Embed:
    """BTD6 panel embed.

    Two information blocks:

    * Reference (seed) — data/game version + entity counts; what the
      deterministic resolver answers from.
    * Currently active — the latest race/boss/CT/odyssey/event by name
      from ``btd6_facts``, prefixed with a per-kind freshness badge so
      operators see at a glance which sources have gone stale.

    PR 1: now built from :class:`HubViewModel`. The badge is the only
    user-visible change vs. the previous panel embed.
    """
    from services.btd6_view_model_service import build_hub_view_model

    vm = await build_hub_view_model()

    embed = discord.Embed(
        title="🐵 BTD6 Assistant",
        description=(
            "Ask BTD6 questions or browse tower / hero / round / event "
            "info by category. Staff can open the **🛠️ Admin** panel for "
            "manual data fetches and diagnostics."
        ),
        color=_PANEL_COLOR,
    )
    embed.add_field(
        name="📚 Reference (seed)",
        value=(
            f"Data version: `{vm.data_version}` · "
            f"Game version: `{vm.game_version}`\n"
            f"{vm.tower_count} towers • "
            f"{vm.hero_count} heroes • "
            f"{vm.map_count} maps • "
            f"{vm.mode_count} modes • "
            f"{vm.round_count} rounds"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎯 Currently active",
        value=_format_currently_active_from_vm(vm.active_events),
        inline=False,
    )
    embed.set_footer(
        text=(
            "!btd6 ask <q> · !btd6 tower <n> · !btd6 round <N> · "
            "!btd6 leaderboard <race|boss> · !btd6 status"
        ),
    )
    from utils.btd6.context_footer import append_context_footer

    append_context_footer(embed, vm.context.context_id)
    return embed


# ---------------------------------------------------------------------------
# Persistent view
# ---------------------------------------------------------------------------


@register
class BTD6PanelView(PersistentView):
    """BTD6 Assistant panel — Layout B (category hub).

    Eight subdivision buttons; **Ask** opens a modal, the rest open an
    ephemeral :class:`views.btd6.hub_panels.BTD6CategoryView` sub-panel via
    :func:`safe_followup`. The public anchor embed is **never edited** on
    click, so a click never mutates the shared panel for the whole channel.

    Modal exception: the **Ask** button calls
    ``interaction.response.send_modal`` as the initial response and does no
    service work before that — modals require the response slot.

    Back-compat: the reused ``btd6:*`` custom_ids (``ask`` / ``events`` /
    ``maps`` / ``strategy`` / ``status`` / ``admin``) keep existing production
    anchors routing. The Layout-A leaf ids that were folded into sub-panels
    (``towers`` / ``heroes`` / ``leaderboards`` / ``ct`` / ``modes`` /
    ``paragon``) are dropped from the top level — an old anchor still showing
    those buttons needs a one-time re-post (``!btd6menu``), which happens
    naturally when the new panel is posted.
    """

    SUBSYSTEM = "btd6"

    # Row 0 — Ask (modal) + the highest-traffic browse categories.
    @discord.ui.button(
        label="Ask",
        emoji="🧠",
        style=discord.ButtonStyle.success,
        row=0,
        custom_id="btd6:ask",
    )
    async def ask_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Modal exception: send_modal must be the initial response.
        # Do NOT call safe_defer here.
        await interaction.response.send_modal(BTD6AskModal())

    @discord.ui.button(
        label="Live Events",
        emoji="🎯",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:events",
    )
    async def events_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "events")

    @discord.ui.button(
        label="Units",
        emoji="🗼",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:units",
    )
    async def units_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "units")

    @discord.ui.button(
        label="Rounds",
        emoji="🎲",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:rounds",
    )
    async def rounds_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "rounds")

    # Row 1 — reference categories + staff.
    @discord.ui.button(
        label="Maps & Modes",
        emoji="🗺️",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:maps",
    )
    async def maps_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "maps")

    @discord.ui.button(
        label="Strategy",
        emoji="📋",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:strategy",
    )
    async def strategy_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "strategy")

    @discord.ui.button(
        label="Status",
        emoji="📊",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:status",
    )
    async def status_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from views.btd6.hub_panels import open_category

        await open_category(interaction, "status")

    @discord.ui.button(
        label="🛠️ Admin",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:admin",
    )
    async def admin_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not is_staff_member(interaction.user):
            await interaction.response.send_message(
                "❌ The Admin panel requires `manage_guild` or administrator.",
                ephemeral=True,
            )
            return
        from views.btd6.admin_panel import BTD6AdminView, build_admin_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        view = await BTD6AdminView.create(interaction.user.id)
        embed = await build_admin_embed()
        await safe_followup(
            interaction,
            embed=embed,
            view=view,
            ephemeral=True,
        )
