"""Interactive ``!platform`` admin panel.

``_PlatformHubView`` is the ephemeral hub opened by ``!platform`` with
no subcommand. It groups the read-only ``!platform <subcommand>``
families into four category Selects (Runtime/status, Catalogues,
Resources/rollout, Validation), an Overview button that returns
to the category listing, and a Flag manager button that opens the
editable per-guild flag manager. The read-only health family —
``health``/``startup``/``findings`` — is grouped under Runtime/status
(``findings`` shows the default ``open`` status; the typed
``!platform findings <status>`` keeps the status filter). The
``finding`` *lifecycle mutation* is deliberately NOT grouped here: the
four category Selects are strictly read-only, so the only write surface
is the segregated Mutations row. Keep this list honest when extending
(diagnostic completion cert punch #1, 2026-06-30; health readiness map,
P2 sweep 2026-06-12).

Selects update the panel in place via ``safe_defer`` +
``safe_edit``, identical to ``_DiagnosticsHubView`` and
``SettingsHubView`` (canonical panel pattern). All embeds are
produced by the existing builders in
``services.diagnostic_embeds`` so the panel and the typed
commands render byte-identical embeds.

The four category Selects remain strictly read-only. The
"Mutations / managers" row (currently the Flag manager button) is
the single segregated write surface — every click still routes
through the canonical mutation pipeline (e.g.
``services.rollout_mutation.RolloutMutationPipeline`` for flag
state changes). Typed ``!platform <subcommand>`` commands are
preserved and continue to support their existing filter/limit
arguments which the panel does not expose (those remain text-only
power-user paths).
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services.diagnostic_embeds import (
    build_anchors_embed,
    build_bindings_embed,
    build_caches_embed,
    build_consistency_embed,
    build_customization_embed,
    build_findings_embed,
    build_flags_embed,
    build_health_embed,
    build_identity_embed,
    build_lifecycle_embed,
    build_locks_embed,
    build_media_embed,
    build_migrations_embed,
    build_participation_schemas_embed,
    build_provisioning_embed,
    build_resource_requirements_embed,
    build_resources_embed,
    build_runtime_embed,
    build_schemas_embed,
    build_sessions_embed,
    build_settings_registry_embed,
    build_setup_readiness_embed,
    build_slow_embed,
    build_startup_health_embed,
    build_status_embed,
    build_tasks_embed,
    build_views_embed,
)
from views.base import HubView

_RUNTIME_OPTIONS = (
    ("health", "🩺", "Deterministic operational health snapshot (redacted)"),
    ("startup", "🚀", "Settled-startup health report (extension load, gateway, DB)"),
    ("findings", "📋", "Persistent operational-health findings (open, redacted)"),
    ("status", "🛠", "Uptime, cogs, guilds, scheduler, failed subsystems"),
    ("runtime", "🛰", "snapshot_all roll-up across every provider"),
    ("lifecycle", "♻️", "Lifecycle phase, pending requests, recent events"),
    ("caches", "🧠", "F-1 guild_config + governance cache state"),
    ("media", "🎬", "Media (YouTube) cache health + provider outcomes"),
    ("locks", "🔒", "scope_locks snapshot (no filter)"),
    ("tasks", "🔁", "Managed background-task snapshot"),
    ("views", "🖼", "Registered PersistentView classes by subsystem"),
    ("sessions", "🎫", "Active session counts by subsystem"),
    ("slow", "🐢", "Slow-path log entries (latest 10)"),
    ("automation", "🤖", "Scheduler status + per-guild rule management panel"),
)

_CATALOGUES_OPTIONS = (
    ("schemas", "📐", "Registered SubsystemSchema instances"),
    ("settings-registry", "🗂️", "Every declared SettingSpec"),
    ("customization", "🧭", "Customization catalogue across subsystems"),
    ("provisioning", "🧰", "ResourceRequirement × BindingSpec catalogue"),
    ("participation-schemas", "🧑‍🤝‍🧑", "Registered ParticipationSchema instances"),
    ("resource-requirements", "🧱", "Declared ResourceRequirement entries"),
)

_RESOURCES_OPTIONS = (
    ("resources", "🧱", "Resource runtime taxonomy + status histogram"),
    ("bindings", "🔗", "Subsystem bindings taxonomy + per-guild counts"),
    ("flags", "🚩", "Feature flag declarations + effective resolution"),
    ("migrations", "🛠", "Platform migration checkpoints"),
)

_VALIDATION_OPTIONS = (
    ("identity", "🪪", "Identity-contract validator findings"),
    ("consistency", "🛡", "Unified platform readiness diagnostic"),
    ("anchors", "📌", "Panel anchor restoration + active counts"),
    ("setup-readiness", "✅", "Per-guild setup-readiness inventory"),
)


# Mutations / managers — write surfaces, rendered as buttons rather than
# folded into the read-only category Selects. Each entry maps a button
# label to the panel-opening dispatch key handled by ``_open_manager``.
_MUTATION_BUTTONS = (
    ("flag-manager", "🚩 Flag manager", "Open the editable per-guild flag manager"),
)


def build_platform_hub_embed() -> discord.Embed:
    """Build the overview embed that lists every grouped surface."""
    embed = discord.Embed(
        title="🛰 Platform hub",
        description=(
            "Diagnostics + managers. Pick a surface from one of the "
            "category dropdowns below — every entry maps to an "
            "existing `!platform <subcommand>`. The four category "
            "dropdowns are **read-only**; mutation surfaces live under "
            "Mutations / managers."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Runtime / status",
        value="\n".join(
            f"{emoji} `{name}` — {desc}" for name, emoji, desc in _RUNTIME_OPTIONS
        ),
        inline=False,
    )
    embed.add_field(
        name="Catalogues",
        value="\n".join(
            f"{emoji} `{name}` — {desc}" for name, emoji, desc in _CATALOGUES_OPTIONS
        ),
        inline=False,
    )
    embed.add_field(
        name="Resources / rollout",
        value="\n".join(
            f"{emoji} `{name}` — {desc}" for name, emoji, desc in _RESOURCES_OPTIONS
        ),
        inline=False,
    )
    embed.add_field(
        name="Validation",
        value="\n".join(
            f"{emoji} `{name}` — {desc}" for name, emoji, desc in _VALIDATION_OPTIONS
        ),
        inline=False,
    )
    embed.add_field(
        name="Mutations / managers",
        value="\n".join(
            f"{label} — {desc}" for _name, label, desc in _MUTATION_BUTTONS
        ),
        inline=False,
    )
    embed.set_footer(
        text=(
            "Typed `!platform <name>` commands keep working with their "
            "filters/limits (e.g. `!platform locks counting`)."
        ),
    )
    return embed


async def _dispatch(name: str, interaction: discord.Interaction) -> discord.Embed:
    """Map a Select value to its embed builder."""
    bot = interaction.client
    guild = interaction.guild
    if name == "health":
        from services import health_snapshot_service
        from services.health_contracts import HealthSnapshotRequest

        audience = await health_snapshot_service.resolve_audience(bot, interaction.user)
        request = HealthSnapshotRequest(
            purpose="summary",
            audience=audience,
            guild_id=guild.id if guild is not None else None,
        )
        snapshot = await health_snapshot_service.collect_snapshot(request, bot=bot)
        return build_health_embed(snapshot)
    if name == "startup":
        from services import health_snapshot_service
        from services.health_contracts import HealthSnapshotRequest

        audience = await health_snapshot_service.resolve_audience(bot, interaction.user)
        stored = health_snapshot_service.get_last_startup_snapshot()
        if stored is not None:
            snapshot = health_snapshot_service.project_for_audience(stored, audience)
        else:
            snapshot = await health_snapshot_service.collect_snapshot(
                HealthSnapshotRequest(
                    purpose="startup",
                    audience=audience,
                    guild_id=guild.id if guild is not None else None,
                ),
                bot=bot,
            )
        return build_startup_health_embed(snapshot)
    if name == "findings":
        from services import health_findings_service, health_snapshot_service
        from services.health_contracts import HealthAudience

        audience = await health_snapshot_service.resolve_audience(bot, interaction.user)
        is_owner = audience is HealthAudience.PLATFORM_OWNER
        rows = await health_findings_service.list_by_status("open", limit=15)
        counts = await health_findings_service.count_by_status()
        return build_findings_embed(
            rows,
            status="open",
            counts=counts,
            is_owner=is_owner,
        )
    if name == "status":
        return build_status_embed(bot)  # type: ignore[arg-type]
    if name == "runtime":
        return build_runtime_embed()
    if name == "lifecycle":
        return build_lifecycle_embed()
    if name == "caches":
        return build_caches_embed()
    if name == "media":
        return await build_media_embed()
    if name == "locks":
        return build_locks_embed()
    if name == "tasks":
        return build_tasks_embed()
    if name == "views":
        return build_views_embed()
    if name == "slow":
        return build_slow_embed()
    if name == "automation":
        from views.diagnostic.automation_panel import build_automation_embed

        return await build_automation_embed(guild)
    if name == "sessions":
        embed, error = await build_sessions_embed()
        if embed is not None:
            return embed
        return discord.Embed(
            title="🎫 Active sessions",
            description=error or "Unknown error.",
            color=discord.Color.red(),
        )
    if name == "schemas":
        return build_schemas_embed()
    if name == "settings-registry":
        return await build_settings_registry_embed(guild)
    if name == "customization":
        return build_customization_embed()
    if name == "provisioning":
        return build_provisioning_embed()
    if name == "participation-schemas":
        return build_participation_schemas_embed()
    if name == "resource-requirements":
        return build_resource_requirements_embed()
    if name == "resources":
        return await build_resources_embed(guild)
    if name == "bindings":
        return await build_bindings_embed(guild)
    if name == "flags":
        return await build_flags_embed(guild)
    if name == "migrations":
        return await build_migrations_embed(guild)
    if name == "identity":
        return await build_identity_embed(bot)  # type: ignore[arg-type]
    if name == "consistency":
        from services.platform_consistency import collect_report

        report = await collect_report(bot=bot, guild=guild)
        return build_consistency_embed(report)
    if name == "anchors":
        return await build_anchors_embed()
    if name == "setup-readiness":
        guild_id = guild.id if guild is not None else 0
        return await build_setup_readiness_embed(guild_id, guild=guild)
    return discord.Embed(
        title="Unknown surface",
        description=f"`{name}` is not a known platform surface.",
        color=discord.Color.red(),
    )


class _PlatformCategorySelect(discord.ui.Select):
    """A category-scoped Select that dispatches to its builder on pick."""

    def __init__(
        self,
        *,
        placeholder: str,
        options: tuple[tuple[str, str, str], ...],
        custom_id: str,
        row: int,
    ):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=name[:100],
                    value=name,
                    description=desc[:100],
                    emoji=emoji,
                )
                for name, emoji, desc in options
            ],
            custom_id=custom_id,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        embed = await _dispatch(self.values[0], interaction)
        view = self.view
        await safe_edit(interaction, embed=embed, view=view)


class _PlatformHubView(HubView):
    """Read-only platform hub: 4 category Selects + Overview button."""

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)
        self.add_item(
            _PlatformCategorySelect(
                placeholder="Runtime / status…",
                options=_RUNTIME_OPTIONS,
                custom_id="platform_hub.runtime",
                row=0,
            ),
        )
        self.add_item(
            _PlatformCategorySelect(
                placeholder="Catalogues…",
                options=_CATALOGUES_OPTIONS,
                custom_id="platform_hub.catalogues",
                row=1,
            ),
        )
        self.add_item(
            _PlatformCategorySelect(
                placeholder="Resources / rollout…",
                options=_RESOURCES_OPTIONS,
                custom_id="platform_hub.resources",
                row=2,
            ),
        )
        self.add_item(
            _PlatformCategorySelect(
                placeholder="Validation…",
                options=_VALIDATION_OPTIONS,
                custom_id="platform_hub.validation",
                row=3,
            ),
        )

    @discord.ui.button(
        label="↩ Overview",
        style=discord.ButtonStyle.secondary,
        row=4,
        custom_id="platform_hub.overview",
    )
    async def btn_overview(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        await safe_edit(interaction, embed=build_platform_hub_embed(), view=self)

    @discord.ui.button(
        label="🚩 Flag manager",
        style=discord.ButtonStyle.primary,
        row=4,
        custom_id="platform_hub.flag_manager",
    )
    async def btn_flag_manager(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        # Mutation surface: opens the editable per-guild flag manager.
        # Every write inside FlagManagerView still routes through the
        # RolloutMutationPipeline (audit + cache invalidation + event).
        if not await safe_defer(interaction):
            return
        from views.diagnostic.flag_manager import (
            FlagManagerView,
            build_flag_manager_overview_embed,
        )
        from views.navigation import carry_back

        guild_id = interaction.guild.id if interaction.guild else None
        manager = FlagManagerView(self._author, guild_id=guild_id)
        # Carry the externally-attached back (↩ Back to Admin, added by the
        # admin-hub opener) onto the fresh Flag Manager so the grandparent link
        # is not dropped entering it (the same fresh-instance back-loss class as
        # the logging Routes round-trip).
        carry_back(self, manager)
        await safe_edit(
            interaction,
            embed=build_flag_manager_overview_embed(),
            view=manager,
        )


__all__ = [
    "_MUTATION_BUTTONS",
    "_PlatformHubView",
    "build_platform_hub_embed",
]
