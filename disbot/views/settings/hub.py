"""SettingsHubView — top-level navigation for ``!settings``.

Hub-and-spoke navigation:

* Header embed shows global counters (registered subsystems, declared
  settings, declared bindings, declared resource requirements,
  customization findings).
* A Discord ``Select`` lists the **actionable** settings groups
  (settings audit §6 inclusion rule, Lane 7): subsystems declaring an
  editable scalar, a binding, a provisionable resource, or a registered
  domain-config panel — computed by
  :func:`services.customization_catalogue.actionable_settings_groups`.
  Router-only / internal / empty subsystems never appear, and groups
  beyond Discord's 25-option cap are reached through page-nav buttons
  instead of being silently truncated. Picking a subsystem replaces the
  panel with a :class:`~views.settings.subsystem_view.SubsystemSettingsView`,
  which hosts the scalar edit + reset widgets.
* Four buttons open diagnostic sub-panels:
  Needs setup / Invalid settings / Missing bindings / Recent changes.

The hub itself is navigation-only — it never mutates state.  Write
behaviour lives one level down in the subsystem drill-down's edit/reset
widgets (see the read-only invariant allowlist in
``tests/unit/invariants/test_settings_cog_read_only.py``); domain
config (cleanup, command access, …) stays with its own canonical
panel/services — the hub only *routes* there.

The hub depends on three S0–S4 catalogues:

* :mod:`core.runtime.settings_registry` (S1) for declared settings
* :mod:`services.customization_catalogue` (S2) for the actionable-group
  discovery rule + help/panel cross-discoverability findings
* :mod:`core.runtime.subsystem_schema` for declared bindings and
  resource requirements

Each is read-only; the hub never mutates them. Build the hub with
:meth:`SettingsHubView.create` where a guild id is available — it
pre-reads per-guild availability (cog routing) so gated groups carry a
"routed off" marker while staying reachable (an admin may configure a
feature before enabling it; every edit callback still re-checks
authority at execution time).
"""

from __future__ import annotations

import logging

import discord

from utils.subsystem_registry import SUBSYSTEMS
from views.base import HubView

logger = logging.getLogger("bot.views.settings.hub")


_DISCORD_SELECT_OPTION_LIMIT = 25

# Availability marker rendered in front of a gated group's description.
_UNAVAILABLE_PREFIX = "⛔"


def _build_header_embed() -> discord.Embed:
    """Build the hub header embed with global counters."""
    from core.runtime.settings_registry import get_cached_registry
    from core.runtime.subsystem_schema import all_schemas
    from services.customization_catalogue import (
        actionable_settings_groups,
        get_cached_catalogue,
    )

    schemas = all_schemas()
    registry = get_cached_registry()
    catalogue = get_cached_catalogue()
    groups = actionable_settings_groups()

    bindings_total = sum(len(s.bindings) for s in schemas.values())
    resources_total = sum(len(s.resource_requirements) for s in schemas.values())
    settings_total = len(registry.entries) if registry is not None else 0
    findings_total = catalogue.findings.total if catalogue is not None else 0

    embed = discord.Embed(
        title="⚙️ Settings Manager",
        description=(
            "Browse platform settings, bindings, resource requirements, "
            "and recent audit history.  The dropdown lists every group "
            "with something configurable (scalar edit + reset live on the "
            "group's page); use the buttons for cross-cutting diagnostics."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Inventory",
        value=(
            f"`groups`: {len(groups)}  ·  "
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


def _page_count(total: int) -> int:
    return max(1, -(-total // _DISCORD_SELECT_OPTION_LIMIT))


def _option_description(group, availability: dict[str, str]) -> str | None:
    """Group description with the availability marker in front when gated."""
    label = availability.get(group.subsystem)
    base = group.description
    if label:
        base = (
            f"{_UNAVAILABLE_PREFIX} {label} · {base}"
            if base
            else f"{_UNAVAILABLE_PREFIX} {label}"
        )
    return base[:100] or None


class _SubsystemSelect(discord.ui.Select):
    """Drop-down listing one page of actionable settings groups."""

    def __init__(
        self,
        groups: tuple,
        availability: dict[str, str],
        page: int,
    ):
        pages = _page_count(len(groups))
        start = page * _DISCORD_SELECT_OPTION_LIMIT
        select_options: list[discord.SelectOption] = []
        for group in groups[start : start + _DISCORD_SELECT_OPTION_LIMIT]:
            select_options.append(
                discord.SelectOption(
                    label=group.display_name[:100],
                    value=group.subsystem,
                    description=_option_description(group, availability),
                    emoji=group.emoji,
                ),
            )
        placeholder = "Open a settings group…"
        if pages > 1:
            placeholder = f"Open a settings group… (page {page + 1}/{pages})"
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=select_options
            or [discord.SelectOption(label="(no settings groups)", value="_none")],
            custom_id="settings_hub.subsystem_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        name = self.values[0]
        if name == "_none":
            await interaction.response.send_message(
                "No settings groups registered.",
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


class _GroupPageButton(discord.ui.Button):
    """Page-nav for >25 groups — replaces the old silent first-25 truncation.

    Rebuilds the hub at the target page with the same author + availability
    (no re-read needed; both ride the view instance).
    """

    def __init__(self, *, delta: int, page: int, pages: int) -> None:
        prev = delta < 0
        super().__init__(
            label="◀ Prev groups" if prev else "More groups ▶",
            style=discord.ButtonStyle.secondary,
            custom_id="settings_hub.page_prev" if prev else "settings_hub.page_next",
            disabled=(page + delta) < 0 or (page + delta) >= pages,
            row=3,
        )
        self._delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        current = self.view
        view = SettingsHubView(
            interaction.user,
            availability=current._availability,
            page=current._page + self._delta,
        )
        await interaction.response.edit_message(view=view)


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


class _OpenCommandAccess(discord.ui.Button):
    """Open the per-guild command-access (allowed-channels) panel.

    The panel mutates state, but the ``!settings`` group is already
    gated by ``@commands.has_permissions(administrator=True)`` so
    reaching this button implies admin.  The view itself re-checks
    Administrator / Manage Guild on every callback as a defence in
    depth.
    """

    def __init__(self):
        super().__init__(
            label="Command access",
            style=discord.ButtonStyle.secondary,
            emoji="🚪",
            custom_id="settings_hub.command_access",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.edit_command_access import (
            CommandAccessView,
            build_command_access_embed,
        )

        view = CommandAccessView(interaction.user)
        embed = await build_command_access_embed(interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)


class SettingsHubView(HubView):
    """Top-level navigation for the Settings Manager (S5).

    The plain constructor builds the hub without per-guild availability
    labels (back-compat for callers with no guild context); prefer
    :meth:`create`, which pre-reads them.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        availability: dict[str, str] | None = None,
        page: int = 0,
    ):
        super().__init__(author)
        from services.customization_catalogue import actionable_settings_groups

        groups = actionable_settings_groups()
        pages = _page_count(len(groups))
        self._availability = availability or {}
        self._page = max(0, min(page, pages - 1))
        self.add_item(_SubsystemSelect(groups, self._availability, self._page))
        self.add_item(_OpenNeedsSetup())
        self.add_item(_OpenInvalid())
        self.add_item(_OpenMissingBindings())
        self.add_item(_OpenAudit())
        self.add_item(_OpenCommandAccess())
        if pages > 1:
            self.add_item(_GroupPageButton(delta=-1, page=self._page, pages=pages))
            self.add_item(_GroupPageButton(delta=1, page=self._page, pages=pages))

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int | None,
    ) -> SettingsHubView:
        """Build the hub with actor-aware availability labels for ``guild_id``.

        Availability is supplementary by contract (a failed/absent read
        renders the same hub without labels), so this never raises for
        availability reasons and ``guild_id=None`` degrades cleanly.
        """
        availability: dict[str, str] = {}
        if guild_id is not None:
            from services.customization_catalogue import (
                actionable_settings_groups,
                group_availability,
            )

            names = [g.subsystem for g in actionable_settings_groups()]
            availability = await group_availability(guild_id, names)
        return cls(author, availability=availability)

    @staticmethod
    def build_embed() -> discord.Embed:
        """Static helper used by the cog + tests."""
        return _build_header_embed()


__all__ = ["SettingsHubView"]
