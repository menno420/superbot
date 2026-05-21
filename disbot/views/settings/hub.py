"""SettingsHubView — top-level navigation for ``!settings``.

Hub-and-spoke navigation:

* Header embed shows global counters (registered subsystems, declared
  settings, declared bindings, declared resource requirements,
  customization findings).
* A Discord ``Select`` lists every subsystem whose schema is
  registered, sorted by ``ui_priority``.  Picking a subsystem
  replaces the panel with a :class:`~views.settings.subsystem_view.SubsystemSettingsView`,
  which hosts the scalar edit + reset widgets.
* Four buttons open diagnostic sub-panels:
  Needs setup / Invalid settings / Missing bindings / Recent changes.

The hub itself is navigation-only — it never mutates state.  Write
behaviour lives one level down in the subsystem drill-down's edit/reset
widgets (see the read-only invariant allowlist in
``tests/unit/invariants/test_settings_cog_read_only.py``).

The hub depends on three S0–S4 catalogues:

* :mod:`core.runtime.settings_registry` (S1) for declared settings
* :mod:`services.customization_catalogue` (S2) for help/panel
  cross-discoverability findings
* :mod:`core.runtime.subsystem_schema` for declared bindings and
  resource requirements

Each is read-only and already cached at startup; the hub never
mutates them.
"""

from __future__ import annotations

import logging

import discord

from utils.subsystem_registry import SUBSYSTEMS
from views.base import HubView

logger = logging.getLogger("bot.views.settings.hub")


_DISCORD_SELECT_OPTION_LIMIT = 25


def _candidate_subsystems() -> list[tuple[str, dict]]:
    """Return subsystems sorted by ``ui_priority`` then name.

    Includes every subsystem with a registered schema *or* declared
    capabilities; excludes ``visibility_mode='internal'`` entries
    because they should not surface in operator-facing UI.
    """
    from core.runtime.subsystem_schema import all_schemas

    schemas = all_schemas()
    out: list[tuple[str, dict]] = []
    for name, meta in SUBSYSTEMS.items():
        if meta.get("visibility_mode", "normal") == "internal":
            continue
        # Show every subsystem.  Even those without a schema are
        # surfaced so the operator sees the gap explicitly; the
        # subsystem page renders an empty-state message.
        out.append((name, meta))
    # Sort: subsystems with schemas first, then by ui_priority ascending,
    # then alphabetically by display_name.
    out.sort(
        key=lambda kv: (
            kv[0] not in schemas,
            kv[1].get("ui_priority", 99),
            kv[1].get("display_name", kv[0]),
        ),
    )
    return out


def _build_header_embed() -> discord.Embed:
    """Build the hub header embed with global counters."""
    from core.runtime.settings_registry import get_cached_registry
    from core.runtime.subsystem_schema import all_schemas
    from services.customization_catalogue import get_cached_catalogue

    schemas = all_schemas()
    registry = get_cached_registry()
    catalogue = get_cached_catalogue()

    bindings_total = sum(len(s.bindings) for s in schemas.values())
    resources_total = sum(len(s.resource_requirements) for s in schemas.values())
    settings_total = len(registry.entries) if registry is not None else 0
    findings_total = catalogue.findings.total if catalogue is not None else 0

    embed = discord.Embed(
        title="⚙️ Settings Manager",
        description=(
            "Browse platform settings, bindings, resource requirements, "
            "and recent audit history.  Use the dropdown to drill into a "
            "subsystem (scalar edit + reset live on the subsystem page); "
            "use the buttons for cross-cutting diagnostics."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Inventory",
        value=(
            f"`subsystems`: {len(SUBSYSTEMS)}  ·  "
            f"`schemas`: {len(schemas)}\n"
            f"`settings`: {settings_total}  ·  "
            f"`bindings`: {bindings_total}  ·  "
            f"`resources`: {resources_total}"
        ),
        inline=False,
    )
    embed.add_field(
        name="Customization findings",
        value=(
            f"`total`: {findings_total}"
            if catalogue is not None
            else "*catalogue not built yet*"
        ),
        inline=False,
    )
    embed.set_footer(
        text=(
            "Tip: `!platform customization` and `!platform settings-registry` "
            "expose the underlying catalogues."
        ),
    )
    return embed


class _SubsystemSelect(discord.ui.Select):
    """Drop-down listing every subsystem.  Picking one swaps the panel."""

    def __init__(self, options: list[tuple[str, dict]]):
        select_options: list[discord.SelectOption] = []
        for name, meta in options[:_DISCORD_SELECT_OPTION_LIMIT]:
            select_options.append(
                discord.SelectOption(
                    label=meta.get("display_name", name)[:100],
                    value=name,
                    description=str(meta.get("description", ""))[:100] or None,
                    emoji=meta.get("emoji") or None,
                ),
            )
        super().__init__(
            placeholder="Open a subsystem…",
            min_values=1,
            max_values=1,
            options=select_options
            or [discord.SelectOption(label="(no subsystems)", value="_none")],
            custom_id="settings_hub.subsystem_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        name = self.values[0]
        if name == "_none":
            await interaction.response.send_message(
                "No subsystems registered.",
                ephemeral=True,
            )
            return
        # Defer the heavy import until selection so the hub stays cheap
        # to build.
        from views.settings.subsystem_view import (
            SubsystemSettingsView,
            build_subsystem_embed,
        )

        view = SubsystemSettingsView(interaction.user, name)
        embed = await build_subsystem_embed(interaction, name)
        await interaction.response.edit_message(embed=embed, view=view)


class _OpenNeedsSetup(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Needs setup",
            style=discord.ButtonStyle.secondary,
            emoji="📋",
            custom_id="settings_hub.needs_setup",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.needs_setup import NeedsSetupView, build_needs_setup_embed

        view = NeedsSetupView(interaction.user)
        embed = await build_needs_setup_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=view)


class _OpenInvalid(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Invalid settings",
            style=discord.ButtonStyle.secondary,
            emoji="⚠️",
            custom_id="settings_hub.invalid",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.invalid_settings import (
            InvalidSettingsView,
            build_invalid_embed,
        )

        view = InvalidSettingsView(interaction.user)
        embed = await build_invalid_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=view)


class _OpenMissingBindings(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Missing bindings",
            style=discord.ButtonStyle.secondary,
            emoji="🔗",
            custom_id="settings_hub.missing_bindings",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.missing_bindings import (
            MissingBindingsView,
            build_missing_bindings_embed,
        )

        view = MissingBindingsView(interaction.user)
        embed = await build_missing_bindings_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=view)


class _OpenAudit(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Recent changes",
            style=discord.ButtonStyle.secondary,
            emoji="🕒",
            custom_id="settings_hub.audit",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.audit_view import (
            RecentChangesView,
            build_audit_embed,
        )

        view = RecentChangesView(interaction.user)
        embed = await build_audit_embed(interaction)
        await interaction.response.edit_message(embed=embed, view=view)


class SettingsHubView(HubView):
    """Top-level navigation for the Settings Manager (S5)."""

    def __init__(self, author: discord.Member | discord.User):
        super().__init__(author)
        self.add_item(_SubsystemSelect(_candidate_subsystems()))
        self.add_item(_OpenNeedsSetup())
        self.add_item(_OpenInvalid())
        self.add_item(_OpenMissingBindings())
        self.add_item(_OpenAudit())

    @staticmethod
    def build_embed() -> discord.Embed:
        """Static helper used by the cog + tests."""
        return _build_header_embed()


__all__ = ["SettingsHubView"]
