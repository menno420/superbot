# 2026-06-08 — Adaptive setup/access/profile/routine source map

## Arc

- Verified binding workflow/current-state/roadmap/owner decisions, relevant subsystem folios/plans/ideas, live merged PR #584/#585 state, and that no PRs were open.
- Mapped setup drafts/Final Review, command access, cog routing, governance/help, diagnostics, server-management managers, settings panels, and automation infrastructure.
- Created the one comprehensive planning document required by Q-0017, routed six genuinely blocking follow-up decisions, and linked the plan from the roadmap and settings/bindings/provisioning folio.

## Result

- Canonical plan: [`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`](../docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md).
- Near-term destination: Q-0026 identity repair, then an Opus access/read-model contract session before new mutation surfaces.
- No runtime code or schema changed.

## Findings / gates

- Existing panels share UI bases and many canonical services, but not one edit rule: setup sections use drafts/Final Review; focused settings and runtime managers write directly; role thresholds and portions of channel management are notable normalization risks before automation.
- `context_map.py` initially could not run because the selected Python 3.10 environment lacked PyYAML; after installing PyYAML, maps completed for setup operations, command routing, automation executor, and setup diagnostics.
- Q-0028–Q-0033 now own unresolved catalogue, quiet-mode ownership, snapshots, risk classification, UI naming, and account-link privacy decisions.

## Verification

- `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py` — passed.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_architecture.py --mode strict` — 0 errors, 87 known warnings.
- GitHub API — PR #584/#585 merged; no open PRs.

## Context delta

- **Needed but not pointed to:** the manager-panel write-path comparison required direct source inspection across `views/roles/`, `views/channels/`, `views/cleanup/`, and settings editors; no single current inventory fully captures their direct-vs-draft behavior.
- **Pointed to but didn't need:** no broad stability audit or live bot boot was needed for this docs-only planning session, consistent with the accepted #535 baseline.
- **Discovered by hand:** the strongest future unification boundary is not a universal panel base; it is a shared read/explanation model plus explicit direct-vs-draft mutation lanes.
