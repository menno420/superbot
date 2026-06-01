"""BTD6 persistent panel.

The view lives under ``views/btd6/`` (Pattern B) so the cog file
stays small. Importing this module triggers the ``@register``
decorator side-effect on :class:`BTD6PanelView`; the persistent
view registry then resolves the ``btd6`` subsystem when
``on_ready`` restores anchors.

User actions: Ask / Towers / Heroes / Modes / Status. Staff actions
sit behind the **🛠️ Admin** button — opens an ephemeral
:class:`views.btd6.admin_panel.BTD6AdminView` with manual fetch
controls and diagnostics. Natural-language replies are owned by the
AI Platform's central stage — this panel never invokes a provider.
"""

from __future__ import annotations

from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup
from core.runtime.persistent_views import PersistentView, register
from services import btd6_ai_service

_PANEL_COLOR = discord.Color.green()


# ---------------------------------------------------------------------------
# Staff gate (mirrors disbot/views/btd6/strategy_review.py:41-47)
# ---------------------------------------------------------------------------


def _is_staff(member: Any) -> bool:
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(
        getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False),
    )


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
            "Ask BTD6 questions or browse tower / hero / mode / round "
            "info. Staff can open the **🛠️ Admin** panel for manual "
            "data fetches and diagnostics."
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
    """BTD6 Assistant panel.

    All non-modal callbacks open ephemeral sub-views via
    :func:`safe_followup`. The public anchor embed is **never edited**
    on click — this is a UX upgrade from PR 2 (clicking Towers used to
    mutate the panel for everyone in the channel).

    Modal exception: the **Ask** button calls
    ``interaction.response.send_modal`` as the initial response and
    does no service work before that — modals require the response
    slot.

    Back-compat: keeps every legacy ``btd6:*`` custom_id so existing
    panel anchor messages in production keep routing correctly.
    Discord does not re-render existing anchor messages at restart;
    the rendered button row is whatever was posted historically. The
    legacy custom_ids (``btd6:towers`` / ``btd6:heroes`` / ``btd6:modes``)
    redirect to the new ephemeral browsers.
    """

    # back-compat redirect — drop after 2026-Q3
    SUBSYSTEM = "btd6"

    # Row 0 — primary user actions (5 buttons)
    @discord.ui.button(
        label="Ask",
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
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:events",
    )
    async def events_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.live_events_view import open_live_events_browser

        await open_live_events_browser(interaction)

    @discord.ui.button(
        label="Towers",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:towers",
    )
    async def towers_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.tower_browser_view import open_tower_browser

        await open_tower_browser(interaction)

    @discord.ui.button(
        label="Heroes",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:heroes",
    )
    async def heroes_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.hero_browser_view import open_hero_browser

        await open_hero_browser(interaction)

    @discord.ui.button(
        label="Leaderboards",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="btd6:leaderboards",
    )
    async def leaderboards_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.leaderboard_browser_view import open_leaderboard_browser

        await open_leaderboard_browser(interaction)

    # Row 1 — secondary actions + staff
    @discord.ui.button(
        label="🗺️ CT",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:ct",
    )
    async def ct_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Contested Territory browser: active CT events + their relic tiles,
        # with a rendered hex map of the current event when Pillow is present.
        from cogs.btd6._builders import build_ct_browser_embed
        from views.btd6.ct_map_view import build_ct_map_file

        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await build_ct_browser_embed()
        map_file, _ = await build_ct_map_file()
        if map_file is not None:
            embed.set_image(url="attachment://ct_map.png")
        await safe_followup(
            interaction,
            embed=embed,
            file=map_file,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Modes",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="btd6:modes",
    )
    async def modes_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Back-compat redirect: open the modes catalog as an ephemeral.
        # The old behaviour (editing the public panel in place) was a
        # UX anti-pattern; PR 2 switches every drill-down to ephemeral.
        from cogs.btd6._embeds import build_modes_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_followup(
            interaction,
            embed=build_modes_embed(),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Status",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="btd6:status",
    )
    async def status_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from cogs.btd6._embeds import build_status_embed

        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await build_status_embed()
        await safe_followup(interaction, embed=embed, ephemeral=True)

    @discord.ui.button(
        label="🔮 Paragon",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="btd6:paragon",
    )
    async def paragon_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        from views.btd6.paragon_view import open_paragon_calculator

        await open_paragon_calculator(interaction)

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
        if not _is_staff(interaction.user):
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
