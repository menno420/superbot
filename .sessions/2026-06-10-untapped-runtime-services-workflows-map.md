# 2026-06-10 — Untapped runtime / services / workflows map

## Arc

Mapped the source-level runtime, service, helper, workflow, mutation, audit, cache, and ownership seams behind the already-completed platform user/admin surface reports. Created a mapping-only audit and did not edit runtime source, tests, shared ledgers, current-state, roadmap, folios, or the owner-question router.

## Shipped

- `docs/planning/untapped-runtime-services-workflows-map-2026-06-10.md`
- This session record.

## Highest-value findings

- Economy shop purchase debits and grants inventory in separate commits from a view.
- Mining workflows directly coordinate multi-table/domain mutations from cogs/views.
- Cog-routing audit ownership leaks into setup dispatcher.
- Binding cache invalidation remains a no-op.
- Event publish-result booleans do not reflect subscriber failures/timeouts.
- Role-threshold clears bypass the audited setter seam.

## Gates / limits

- No open PRs existed at mapping time; no findings are provisional.
- Adaptive availability projection remains blocked by P1C.
- AI structural expansion remains gated; only naming/layer observations were recorded.
- `gh` and CodeGraph CLI were unavailable; GitHub API + `scripts/context_map.py` AST fallback + manual source verification were used.
- Parallel Codex Agent 2 is mapping docs/tests/plans/verification gaps; this session maps runtime/services/workflows only.

## Context delta

- **Needed but not pointed to:** the direct-write invariant scan sets themselves were essential for finding asymmetric coverage (notably role-threshold clears), but the route points mainly to binding ownership docs rather than invariant scope.
- **Pointed to but didn't need:** most detailed BTD6 decode-tail docs were not needed after source/boundary checks showed no ungated bypass worth mapping; only status/coverage context paid off.
- **Discovered by hand:** `BindingMutationPipeline._invalidate_cache` is still a no-op; cog-routing audit emission belongs to setup dispatcher rather than the routing owner; EventBus handler failures cannot influence `event_emitted` results.
- **Decisions made alone:** ranked economy purchase as the smallest high-value mutation-hardening slice and recommended mining workshop as the first mining workflow boundary; these are recommendations, not product decisions.
- **Flagged for maintainer:** cross-domain transaction ownership (coins + inventory/mining) requires a deliberate owner choice before implementation.
- **Most helpful future tooling change:** a repository script that enumerates cogs/views calling `utils.db` mutation primitives and compares them with ownership/invariant allowlists would make this audit repeatable.

## Verification

- Bare `python3.10` commands could not select the inactive pyenv shim; they were re-run with `PYENV_VERSION=3.10.20`.
- Python 3.10 strict docs reports only the expected orphan for the new mapping doc; linking it would require editing shared docs outside this lane.
- Python 3.10 full quality passed black/isort/ruff/mypy, then failed strict docs on that orphan and pytest collection because the isolated environment lacks `discord`/`asyncpg`.
- Python 3.10 architecture check lacks `yaml`; the Python 3.12 substitute passed with 0 errors / 86 tracked warnings.
- See §11 of the mapping document for the exact mapping commands and results.
