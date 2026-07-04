"""The ``!platform`` command group, extracted onto a cog mixin.

``DiagnosticCog`` is the Discord-facing surface for the whole ``!platform``
admin group — ~30 thin ``@platform_grp.command`` wrappers, each delegating to
an embed builder in :mod:`cogs.diagnostic._platform_embeds`.  That surface
pushed ``diagnostic_cog.py`` to the 800-LOC cog ceiling
(``tests/unit/invariants/test_cog_size.py``), so the command registrations
live here on :class:`PlatformCommandsMixin` while the command *identity* stays
on ``DiagnosticCog`` (the ``diagnostic`` subsystem).

This is the same "Discord surface = the cog; the weight lives in
``cogs/<sub>/``" convention F-3 already established for the embed builders.
discord.py's ``CogMeta`` collects commands across the cog's MRO, so a non-Cog
mixin base contributing the group + subcommands resolves exactly as if they
were defined inline — the ``!platform <sub>`` surface and group registration
are byte-for-byte unchanged.  Helper modules under ``cogs/<sub>/`` are not
subject to the 800-LOC ceiling (only top-level ``*_cog.py`` files are), so the
``!platform`` lane can grow again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from cogs.diagnostic._platform_embeds import (
    build_anchors_embed,
    build_bindings_embed,
    build_caches_embed,
    build_consistency_pages,
    build_customization_embed,
    build_findings_pages,
    build_flags_embed,
    build_health_embed,
    build_identity_embed,
    build_lifecycle_embed,
    build_locks_embed,
    build_migrations_embed,
    build_participation_schemas_embed,
    build_provisioning_embed,
    build_resource_requirements_embed,
    build_resources_embed,
    build_runtime_embed,
    build_schemas_embed,
    build_sessions_embed,
    build_setting_detail_embed,
    build_settings_registry_embed,
    build_slow_embed,
    build_startup_health_embed,
    build_status_embed,
    build_tasks_embed,
    build_views_embed,
)
from core.runtime.permission_checks import admin_or_owner
from views.base import send_panel
from views.diagnostic import _PlatformHubView, build_platform_hub_embed


async def _send_paginated(ctx, pages: list[discord.Embed]) -> None:
    """Send a list of embed pages, attaching the prev/next paginator when >1.

    A single page is sent as a plain embed (no view) so the common case is
    byte-identical to the pre-pagination behaviour; multi-page output gets a
    ``_PaginatorView`` so dense findings/consistency reports stay fully
    reachable (diagnostic cert punch #2).
    """
    if not pages:  # defensive — builders always return at least one page
        return
    if len(pages) == 1:
        await ctx.send(embed=pages[0])
        return
    # Local import: keep the module-load import surface lean and mirror the
    # diagnostic-cog paginator-send pattern.
    from views.diagnostic.paginator import _PaginatorView

    view = _PaginatorView(pages, ctx.author)
    view.message = await ctx.send(embed=pages[0], view=view)


if TYPE_CHECKING:
    # Under type-checking the mixin is a ``Cog`` so the ``@commands.group`` /
    # ``@platform_grp.command`` decorators see a valid ``CogT`` (the group is
    # only ever mixed into ``DiagnosticCog``, a real Cog). At runtime the base
    # is ``object`` — discord.py's ``CogMeta`` collects the commands across the
    # final cog's MRO, so no Cog base is needed here.
    _MixinBase = commands.Cog
else:
    _MixinBase = object


class PlatformCommandsMixin(_MixinBase):
    """The ``!platform`` runtime-introspection group (R1 from the hardening plan).

    Surfaces anchor restoration state, identity-contract findings, and basic
    runtime statistics so operators can investigate without SSH access.  Mixed
    into :class:`~cogs.diagnostic_cog.DiagnosticCog`; ``self.bot`` is supplied
    by the cog, so every command here reads it exactly as before.
    """

    # Supplied by ``DiagnosticCog.__init__`` — declared here so the commands
    # below type-check their ``self.bot`` reads.
    bot: commands.Bot

    # ────────────────────────────────────────────────────────────────
    # !platform — runtime introspection (R1 from the hardening plan)
    # ────────────────────────────────────────────────────────────────

    @commands.group(name="platform", invoke_without_command=True)
    @admin_or_owner()
    async def platform_grp(self, ctx):
        """Runtime introspection group.

        With no subcommand the interactive ``_PlatformHubView`` opens —
        every existing typed ``!platform <subcommand>`` is preserved and
        continues to work exactly as before.

        Existing surfaces (read-only):
            status · anchors · identity · runtime · caches ·
            locks [prefix] · tasks · views · sessions [subsystem] ·
            slow [limit] · schemas · settings-registry · customization ·
            provisioning · participation-schemas · resource-requirements ·
            resources · bindings · flags · migrations · consistency
        """
        view = _PlatformHubView(ctx.author)
        await send_panel(ctx, embed=build_platform_hub_embed(), view=view)

    @platform_grp.command(name="status")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_status(self, ctx):
        """High-level platform status: uptime, cogs, governance, scheduler."""
        await ctx.send(embed=build_status_embed(self.bot))

    @platform_grp.command(name="setup-readiness", aliases=["readiness", "ready"])  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_setup_readiness(self, ctx):
        """Per-guild setup-readiness inventory (PR H).

        Walks ``core.runtime.subsystem_schema.all_schemas`` and joins
        each subsystem's declared bindings + settings against this
        guild's stored values to compute how much of the configurable
        surface has been populated.

        Read-only — does not mutate anything. The output is the
        substrate for a future setup wizard; for now operators use it
        to spot subsystems that need attention.
        """
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(ctx.guild.id, guild=ctx.guild)
        await ctx.send(embed=embed)

    @platform_grp.command(name="anchors")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_anchors(self, ctx):
        """Show last restoration outcome and active anchor counts per subsystem."""
        await ctx.send(embed=await build_anchors_embed())

    @platform_grp.command(name="identity")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_identity(self, ctx, mode: str = ""):
        """Run the identity-contract validator and show findings.

        Usage:
            !platform identity          run validator, show findings
            !platform identity --fix    also remediate auto_healable
                                        findings (fatal-tier are never
                                        auto-fixed; cog reload required).
        """
        await ctx.send(embed=await build_identity_embed(self.bot, mode))

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase S2.5 / O-1: diagnostics_service-backed commands
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="runtime")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_runtime(self, ctx):
        """High-level runtime snapshot: every registered diagnostic provider."""
        await ctx.send(embed=build_runtime_embed())

    @platform_grp.command(name="health")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_health(self, ctx):
        """Deterministic operational health snapshot (admin-gated, redacted).

        Aggregates runtime / gateway / database / consistency / startup /
        tasks / diagnostics / AI subsystem health into one bounded view.
        Works with AI disabled; the bot owner sees the full cross-process
        projection, other admins a guild-local redacted one.
        """
        from services import health_snapshot_service
        from services.health_contracts import HealthSnapshotRequest

        audience = await health_snapshot_service.resolve_audience(self.bot, ctx.author)
        request = HealthSnapshotRequest(
            purpose="summary",
            audience=audience,
            guild_id=ctx.guild.id if ctx.guild is not None else None,
        )
        snapshot = await health_snapshot_service.collect_snapshot(request, bot=self.bot)
        await ctx.send(embed=build_health_embed(snapshot))

    @platform_grp.command(name="startup")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_startup(self, ctx):
        """Settled-startup health report (extension load, gateway, DB, …).

        Shows the one-shot snapshot captured after the bot reached a stable
        post-ready state (re-projected to the caller's audience). Falls back
        to a fresh collection if the settled snapshot is not available yet.
        """
        from services import health_snapshot_service
        from services.health_contracts import HealthSnapshotRequest

        audience = await health_snapshot_service.resolve_audience(self.bot, ctx.author)
        stored = health_snapshot_service.get_last_startup_snapshot()
        if stored is not None:
            snapshot = health_snapshot_service.project_for_audience(stored, audience)
        else:
            snapshot = await health_snapshot_service.collect_snapshot(
                HealthSnapshotRequest(
                    purpose="startup",
                    audience=audience,
                    guild_id=ctx.guild.id if ctx.guild is not None else None,
                ),
                bot=self.bot,
            )
        await ctx.send(embed=build_startup_health_embed(snapshot))

    @platform_grp.command(name="findings")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_findings(self, ctx, status: str = "open"):
        """Persistent operational-health findings (open / resolved / ignored / all).

        Unlike `!platform health` (a live in-memory snapshot), these survive
        restarts: each row's occurrence count accumulates across boots so a
        recurring problem is visible over time. Read-only and admin-gated;
        owner-only detail (file/provider hints) is shown only to the bot owner.
        """
        from services import health_findings_service, health_snapshot_service
        from services.health_contracts import HealthAudience

        wanted = status.lower().strip()
        if wanted not in ("open", "resolved", "ignored", "all"):
            wanted = "open"
        audience = await health_snapshot_service.resolve_audience(self.bot, ctx.author)
        is_owner = audience is HealthAudience.PLATFORM_OWNER
        rows = await health_findings_service.list_by_status(
            None if wanted == "all" else wanted,
            limit=60,
        )
        counts = await health_findings_service.count_by_status()
        await _send_paginated(
            ctx,
            build_findings_pages(
                rows,
                status=wanted,
                counts=counts,
                is_owner=is_owner,
            ),
        )

    @platform_grp.command(name="finding")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_finding(self, ctx, action: str, *, fingerprint: str):
        """Transition a persistent finding: `resolve` / `ignore` / `reopen` <fingerprint>.

        The operator-managed lifecycle (Q-0097) for the rows shown by
        `!platform findings`. Resolving/ignoring lets retention eventually prune
        a row (open findings are retained forever); `reopen` returns it to open.
        Copy the fingerprint from a finding (e.g. `diagnostics.provider_failed:ai`).
        The transition routes through the sole writer `health_findings_service`
        and is recorded on the canonical audit seam. Admin-gated.
        """
        from services import health_findings_service

        action_to_status = {
            "resolve": "resolved",
            "resolved": "resolved",
            "ignore": "ignored",
            "ignored": "ignored",
            "reopen": "open",
            "open": "open",
        }
        target_status = action_to_status.get(action.lower().strip())
        if target_status is None:
            await ctx.send(
                "❓ Unknown action. Use `resolve`, `ignore`, or `reopen` "
                "followed by the finding fingerprint.",
            )
            return

        fp = fingerprint.strip()
        result = await health_findings_service.set_status(
            fp,
            target_status,
            actor_id=ctx.author.id,
        )
        if result.outcome == "not_found":
            await ctx.send(
                f"⚠️ No finding with fingerprint `{fp}` "
                "(see `!platform findings all`).",
            )
        elif result.outcome == "unchanged":
            await ctx.send(f"ℹ️ `{fp}` is already `{target_status}` — no change.")
        else:
            await ctx.send(
                f"✅ `{fp}`: `{result.previous_status}` → `{target_status}`.",
            )

    @platform_grp.command(name="lifecycle")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_lifecycle(self, ctx):
        """Lifecycle state: phase, pending request, recent events."""
        await ctx.send(embed=build_lifecycle_embed())

    @platform_grp.command(name="caches")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_caches(self, ctx):
        """Cache state: F-1 guild_config + governance.cache."""
        await ctx.send(embed=build_caches_embed())

    @platform_grp.command(name="media")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_media(self, ctx):
        """Content-free media (YouTube) diagnostics.

        Credential presence, provider-request outcome counters, cache
        size/age/expiry counts, and the last physical-purge outcome — counts
        and categories only, never any provider content (P0-2 / Q-0099).
        """
        from cogs.diagnostic._platform_embeds import build_media_embed

        await ctx.send(embed=await build_media_embed())

    @platform_grp.command(name="economy", aliases=["coinflow"])  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_economy(self, ctx, days: int | None = None):
        """Faucet/sink coin-economy view (`!platform economy [days]`): minted
        vs. drained, net, ratio + verdict, per reason. Window N days or omit
        for all-time. Read-only, content-free (counts/totals, no per-user data).
        """
        from cogs.diagnostic._platform_embeds import build_economy_flow_embed

        await ctx.send(embed=await build_economy_flow_embed(ctx.guild.id, days=days))

    @platform_grp.command(name="economytrend", aliases=["coinflowtrend"])  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_economy_trend(self, ctx, days: int | None = None):
        """Per-day coin-flow trend (`!platform economytrend [days]`): the daily
        minted/drained/net series + a net sparkline + a rising/falling read, so
        you can see whether the economy is inflating *over time*, not just at one
        snapshot. Window N days or omit for all-time. Read-only, content-free.
        """
        from cogs.diagnostic._platform_embeds import build_economy_trend_embed

        await ctx.send(embed=await build_economy_trend_embed(ctx.guild.id, days=days))

    @platform_grp.command(name="locks")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_locks(self, ctx, prefix: str = ""):
        """scope_locks snapshot; pass a prefix to filter (e.g. `counting`)."""
        await ctx.send(embed=build_locks_embed(prefix))

    @platform_grp.command(name="tasks")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_tasks(self, ctx):
        """Managed background-task snapshot (core.runtime.tasks)."""
        await ctx.send(embed=build_tasks_embed())

    @platform_grp.command(name="views")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_views(self, ctx):
        """Registered PersistentView classes (by subsystem)."""
        await ctx.send(embed=build_views_embed())

    @platform_grp.command(name="slow")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_slow(self, ctx, limit: int = 10):
        """Show the most recent slow-path entries (S3.2 ring buffer)."""
        await ctx.send(embed=build_slow_embed(limit))

    @platform_grp.command(name="automation")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_automation(self, ctx):
        """Open the automation management + diagnostics panel.

        Renders the ``automation_scheduler`` snapshot alongside the
        per-guild rule list and lets administrators enable / disable /
        delete individual rules through the audited
        :class:`AutomationMutationPipeline`.
        """
        from views.diagnostic.automation_panel import open_panel

        embed, view = await open_panel(ctx)
        await send_panel(ctx, embed=embed, view=view)

    @platform_grp.command(name="sessions")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_sessions(self, ctx, subsystem: str = ""):
        """Active session counts (DB-backed); optionally filtered by subsystem."""
        embed, error = await build_sessions_embed(subsystem)
        if error is not None:
            await ctx.send(error, delete_after=15)
            return
        await ctx.send(embed=embed)

    # ────────────────────────────────────────────────────────────────
    # !platform — Phase 1: schema / participation / resource registries
    # ────────────────────────────────────────────────────────────────

    @platform_grp.command(name="schemas")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_schemas(self, ctx):
        """Registered SubsystemSchema instances (Phase 1a)."""
        await ctx.send(embed=build_schemas_embed())

    @platform_grp.command(name="settings-registry")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_settings_registry(self, ctx):
        """Declared SettingSpec catalogue + this guild's current values (S1)."""
        await ctx.send(embed=await build_settings_registry_embed(ctx.guild))

    @platform_grp.command(name="setting")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_setting(self, ctx, subsystem: str, name: str):
        """Explain one scalar setting for this guild.

        Shows the resolved value, its provenance (default vs legacy_kv),
        the declared default, validity, the raw stored string, and any
        resolver diagnostics — the "why is this value?" answer that
        feature flags already have via ``!platform flag``.
        """
        await ctx.send(
            embed=await build_setting_detail_embed(ctx.guild, subsystem, name),
        )

    @platform_grp.command(name="customization")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_customization(self, ctx):
        """Customization catalogue across subsystems (S2)."""
        await ctx.send(embed=build_customization_embed())

    @platform_grp.command(name="provisioning")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_provisioning(self, ctx):
        """Cross-linked ResourceRequirement × BindingSpec catalogue (S2.5)."""
        await ctx.send(embed=build_provisioning_embed())

    @platform_grp.command(name="participation-schemas")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_participation_schemas(self, ctx):
        """Registered ParticipationSchema instances (Phase 1b)."""
        await ctx.send(embed=build_participation_schemas_embed())

    @platform_grp.command(name="resource-requirements")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_resource_requirements(self, ctx):
        """Declared ResourceRequirement entries across subsystems (Phase 1c)."""
        await ctx.send(embed=build_resource_requirements_embed())

    @platform_grp.command(name="bindings")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_bindings(self, ctx):
        """Subsystem bindings (Phase 2b) — taxonomy + per-guild histograms."""
        await ctx.send(embed=await build_bindings_embed(ctx.guild))

    @platform_grp.command(name="resources")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_resources(self, ctx):
        """Resource runtime (Phase 2a) — taxonomy + cached status histogram."""
        await ctx.send(embed=await build_resources_embed(ctx.guild))

    @platform_grp.command(name="flags")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_flags(self, ctx):
        """Feature flags: declarations + Phase 2d evaluator state per flag."""
        await ctx.send(embed=await build_flags_embed(ctx.guild))

    @platform_grp.command(name="flag")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_flag_manager(self, ctx):
        """Open the editable per-guild flag manager (Phase 6.5a).

        Every mutation routes through
        :class:`services.rollout_mutation.RolloutMutationPipeline`
        (validates, writes audit, invalidates cache, emits event).
        """
        from views.base import send_panel
        from views.diagnostic.flag_manager import (
            FlagManagerView,
            build_flag_manager_overview_embed,
        )

        guild_id = ctx.guild.id if ctx.guild else None
        view = FlagManagerView(ctx.author, guild_id=guild_id)
        await send_panel(
            ctx,
            embed=build_flag_manager_overview_embed(),
            view=view,
        )

    @platform_grp.command(name="migrations")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_migrations(self, ctx):
        """Platform migration checkpoints (Phase 2 PR-5) — status + summary."""
        await ctx.send(embed=await build_migrations_embed(ctx.guild))

    @platform_grp.command(name="consistency")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_consistency(self, ctx):
        """Unified platform readiness diagnostic — read-only (Phase 2 PR-10)."""
        from services.platform_consistency import collect_report

        report = await collect_report(bot=self.bot, guild=ctx.guild)
        await _send_paginated(ctx, build_consistency_pages(report))

    @platform_grp.command(name="backfill")  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_backfill(self, ctx, action: str = "") -> None:
        """Dry-run (default) or `apply` the legacy-pointer → binding backfill."""
        from cogs.diagnostic._backfill import handle_platform_backfill

        await handle_platform_backfill(ctx, action)

    @platform_grp.command(  # type: ignore[arg-type]
        name="command-access",
        aliases=["commandaccess"],
    )
    @admin_or_owner()
    async def platform_command_access(
        self,
        ctx,
        channel: discord.TextChannel | None = None,
    ):
        """Show the live command-access decision for a channel.

        Defaults to the invoking channel.  Output covers every input
        the resolver consumed to make its decision so operators can
        see at a glance why ``!bj`` (or ``/blackjack``) succeeded or
        denied here — closes the "command vanished" debugging loop
        the command-access onboarding fix was written to eliminate.
        """
        from cogs.diagnostic._platform_embeds import (
            build_command_access_diagnostic_embed,
        )

        target = channel or ctx.channel
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
        await ctx.send(embed=embed)

    @platform_grp.command(name="access", aliases=["whyhere"])  # type: ignore[arg-type]
    @admin_or_owner()
    async def platform_access(
        self,
        ctx,
        target: discord.TextChannel | discord.Thread | None = None,
    ):
        """Explain which subsystems you can use in a channel/thread (IL-1).

        Resolves the governance snapshot for the selected location (thread-aware,
        validates RC-2) and lists visible/denied subsystems + where each decision
        resolved from.  Read-only.
        """
        from cogs.diagnostic._platform_embeds import (
            build_access_explainer_embed,
            governance_context_for,
        )
        from governance.snapshot import build_governance_snapshot

        where = target or ctx.channel
        gctx = governance_context_for(ctx, where)
        snapshot = await build_governance_snapshot(gctx)
        await ctx.send(embed=build_access_explainer_embed(where.mention, snapshot))

    @platform_grp.command(  # type: ignore[arg-type]
        name="cleanup-preview",
        aliases=["cleanuppreview", "cleanup-policy"],
    )
    @admin_or_owner()
    async def platform_cleanup_preview(
        self,
        ctx,
        target: discord.TextChannel | discord.Thread | None = None,
    ):
        """Dry-run preview of the cleanup policy resolved for a location (IL-2).

        Reuses the read-only resolver; shows the resolved policy + which scope
        types a cleanup write accepts.  Makes no changes.
        """
        from cogs.diagnostic._platform_embeds import (
            build_cleanup_preview_embed,
            governance_context_for,
        )
        from governance.cleanup import resolve_cleanup_policy
        from governance.scopes import VALID_CLEANUP_SCOPE_TYPES

        where = target or ctx.channel
        gctx = governance_context_for(ctx, where)
        policy = await resolve_cleanup_policy(gctx)
        await ctx.send(
            embed=build_cleanup_preview_embed(
                where.mention,
                policy,
                is_thread=isinstance(where, discord.Thread),
                valid_cleanup_scopes=VALID_CLEANUP_SCOPE_TYPES,
            ),
        )

    @platform_grp.command(  # type: ignore[arg-type]
        name="counting-health",
        aliases=["countinghealth"],
    )
    @admin_or_owner()
    async def platform_counting_health(self, ctx):
        """Surface counting persistence health from task_outcome_total (IL-3).

        Reads the existing managed-task metric (RC-15) — not a new monitor.
        """
        from cogs.diagnostic._platform_embeds import (
            build_counting_health_embed,
            read_counting_save_outcomes,
        )

        guild_id = ctx.guild.id
        await ctx.send(
            embed=build_counting_health_embed(
                guild_id,
                read_counting_save_outcomes(guild_id),
                read_counting_save_outcomes(),
            ),
        )
