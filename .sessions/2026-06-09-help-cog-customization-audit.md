# Session journal — Help cog customization audit — 2026-06-09

## Summary

Completed a documentation-only, source-verified mapping of SuperBot's Help, mother-hub,
navigation, governance visibility, access projection, settings/customization, setup, and command-panel systems. Added a phased target architecture and routed five owner decisions. No runtime behavior was changed.

## Files read

- Workflow/architecture: `docs/owner/agent-workflow-spec.md`, `docs/owner/ai-project-workflow.md`, `docs/collaboration-model.md`, `.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`, `docs/current-state.md`, `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `docs/roadmap.md`.
- Help/hub/setup docs: `docs/help-command-surface-map.md`, both hub-roadmap docs, setup-platform roadmap/command map/presets, adaptive setup/access plan, UI adoption audit, repo navigation map, and relevant subsystem folios.
- Core source: Help cog/route, subsystem/hub registries, navigation, governance resolver/writes, access projection, command surface/access/routing, customization catalogue, settings registry/resolution/mutation/accessors, setup change plan/draft/operations, configuration, visibility panel, Access Explorer, and representative hub/panel files.
- Tests: all `tests/unit/help/*` plus relevant hub registry, access projection, customization/settings, navigation, visibility, setup, and docs tests.

## Files changed

- `docs/planning/help-cog-customization-audit-2026-06-09.md` — new durable audit/roadmap.
- `docs/owner/maintainer-question-router.md` — Q-0055 through Q-0059.
- `docs/roadmap.md` — Later/decisions-first route to the plan.
- `docs/subsystems/settings-bindings-provisioning.md` — folio link to the plan.
- `.sessions/2026-06-09-help-cog-customization-audit.md` — this journal.

## Important findings

- Help Home filters hubs by tier only, not by resolved governance visibility or access projection.
- Advanced consumes governance visibility but excludes all `parent_hub` children.
- Typed/direct hub, subsystem, and command routes resolve without checking the target against the resolved visible set.
- Generic command embeds filter static command visibility but do not evaluate whether the audience can execute a command; dedicated panels own independent static composition.
- Governance, command access, routing, and access projection already own policy/read models that a future Help Projection should compose rather than duplicate.
- A read-only catalogue plus audited guild presentation overlay is the cleanest long-term architecture; governance remains true visibility owner.
- Existing binding Help inventory has count drift; Community Spotlight registration is already decided but belongs to the Q-0025 scaffold lane.

## Context-delta

### needed-not-pointed

- `disbot/utils/subsystem_registry.py` — actual canonical subsystem metadata/parent relationships.
- `disbot/cogs/help/route.py` — canonical shared route/open behavior.
- `disbot/core/runtime/command_surface_ledger.py` — static hidden-from-help policy.
- `disbot/services/command_routing.py` and `disbot/core/runtime/command_access.py` — effective-access axes Help does not consume.
- `disbot/governance/writes.py` — canonical audited scoped visibility mutation.
- `disbot/config.py` and `community_spotlight_cog.py` — loaded-vs-registered drift.

### pointed-not-needed

- No requested route was wholly unnecessary. Several large setup/preset docs were read for ownership and integration constraints but did not determine current Help rendering behavior.

### discovered-by-hand

- Home's use of `member_tier` discards the resolved subsystem set.
- Direct routes do not enforce target visibility.
- “Advanced / All Commands” excludes parent-hub children despite its broad label.
- Single-command Help does not apply the static hidden-from-help classification.
- The existing Help map's count wording is stale relative to source.

## Verification performed

- Verified requested paths and discovered source/tests exist.
- Enumerated `HUBS` and `SUBSYSTEMS` from live source.
- Manually verified source claims.
- Attempted live PR verification; unavailable because `gh` is not installed and no remote is configured.
- Attempted `python3.10 scripts/context_map.py`; unavailable through the shim. Python 3.10.20 lacked PyYAML. Repository-default Python 3.12 produced a Help context map.
- `python scripts/check_docs.py` passed.
- `pytest -q tests/unit/help tests/unit/utils/test_hub_registry.py tests/unit/services/test_access_projection.py tests/unit/services/test_customization_catalogue.py tests/unit/services/test_settings_resolution.py tests/unit/services/test_settings_mutation_pipeline.py tests/unit/views/test_navigation.py tests/unit/views/test_visibility_panel_multi.py tests/unit/docs/test_help_surface_map_doc.py tests/unit/docs/test_subsystem_folios_doc.py` passed: 348 tests. The first attempt exposed a missing environment dependency (`pytest-asyncio`); after installing the pinned dev dependency, the same command passed.
- `python scripts/check_architecture.py --mode strict` passed with 0 errors and 86 known warnings.
- `git diff --check` passed.

## Recommended next step

Route Q-0055–Q-0059 to owner Decisions, then use Opus planning/revision to define the Phase 1 Help Catalogue and Phase 2 Help Projection contract while coordinating with Adaptive Setup/Access P1B/P1C. A separate bounded documentation/test PR can reconcile the existing Help surface map before runtime implementation.
