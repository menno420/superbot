# Session — consistency-linter: embedded windowed-select helper + bounded-catalog triage

> **Status:** `in-progress`

## Origin

Scheduled dispatch fire, no work order → advance the live ▶ Next action: the
consistency-linter `select_option_truncation` slice. The previous slices (#1042–#1048)
built the linter + rules 1–4 and migrated the *standalone* ephemeral pickers onto
`views/paginated_select.py` `PaginatedSelectView`. The remaining **28** candidates are
all **embedded in multi-control views**, which the standalone `PaginatedSelectView`
does not drop into — the handoff named this "a design step first … treat it as a small
plan, not a mechanical swap."

## What I'm about to do (PR 1)

1. **Design step — the embedded windowed-select helper.** Refactor
   `views/paginated_select.py` to share ONE windowing core: a `SelectWindow`
   controller that manages a *band* of items (a windowed `Select` + ◀/▶ nav) within
   **any host view**, removing only its own items on a page flip so it composes with a
   view that carries other controls. `PaginatedSelectView` becomes a thin wrapper that
   owns a `SelectWindow`; a new `attach_windowed_select(view, options, on_select, …)`
   exposes the embedded path. Full tests (incl. the embedded-with-other-controls case).
2. **Bounded-catalog triage.** Allowlist the candidates whose option source is a
   **fixed in-repo catalog / game-data roster / concurrent-events feed** that cannot
   realistically exceed 25 (the btd6 tower roster + live-events feed; the curated mining
   taxonomy market/recipe/workshop/gear selects) — same standard as the existing
   `consistency_exceptions.yml` btd6-catalog entries. These are not the #1040 bug.
3. **Dogfood** the helper on a genuinely-dynamic embedded select: `access_map`
   `_FeatureDetailSelect` (access-map features can exceed 25).

Leaves the shared `views/selectors/` primitives migration (the API-ripple set) +
the remaining guild-scaled embedded panels (channels move/visibility/create,
settings subsystem_view, setup channels, access/explorer) for follow-up PRs — see the
handoff at close.

## Done

(filled at close)
