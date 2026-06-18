# Session — consistency-linter: embedded windowed-select helper + bounded-catalog triage

> **Status:** `complete`

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

## Done (PR #1050)

1. **The embedded windowed-select helper (design step).** Refactored
   `views/paginated_select.py` to share **one** windowing core: a `SelectWindow` controller
   that manages a *band* of items (a windowed `Select` + ◀/▶ nav) inside **any host view**,
   removing only its own items on a page flip so it composes with a multi-control panel.
   `PaginatedSelectView` is now a thin wrapper that owns a `SelectWindow` (constructor +
   `page_count` unchanged — the 4 migrated callers from #1047/#1048 are untouched). New
   `attach_windowed_select(view, options, on_select, *, select_row, nav_row, …)` is the
   embedded path. `_WindowSelect`/`_PageButton` now hold a `window` ref instead of relying on
   `isinstance(view, PaginatedSelectView)`, so they work in any host.
2. **Bounded-catalog triage → 28 candidates down to 15.** Allowlisted **12** candidates backed
   by a fixed in-repo catalog / game-data roster (btd6 tower roster + the two live-events feed
   selects; the curated mining taxonomy market `_Category/_Type/_Buy`, recipe
   `_Category/_Type/_Variant`, workshop repair/craft, gear `_ItemSelect`) with per-callback
   reasons in `consistency_exceptions.yml` — same standard as the existing btd6-catalog entries;
   these are not the #1040 bug.
3. **Dogfood.** Migrated `access_map`'s feature drill-down (`_FeatureDetailSelect` →
   `_attach_feature_detail_select`) onto the helper — a genuinely-dynamic select (access-map
   features can exceed 25); the drill-down stays an ephemeral (a real new detail message). Pinned
   the tier select to `row=0` so the new explicit select/nav rows don't collide.

- Tests: `test_paginated_select.py` extended (embedded-with-host-controls: coexistence, page-flip
  preserves siblings, single-page no-nav, dispatch, in-place edit) + new
  `tests/unit/views/server_management/test_access_map_feature_select.py` (pagination without
  dropping, drill-down ephemeral, unknown-feature safety) + updated the two cog-routing tests and
  the one `test_access_map_view` drill-down test for the refactor.
- `check_quality.py --full` GREEN (10659 passed, +1 net new file's cases; mypy + check_docs clean)
  · `check_architecture --mode strict` exit 0 · `check_consistency` `select_option_truncation`
  28→15, 27 linter unit tests pass.

## Handoff → next dispatch

**The embedded-windowing helper exists — the remaining 15 `select_option_truncation` candidates
are now small per-view swaps, not a design problem.** Two clean follow-up PRs:

1. **The shared `views/selectors/` primitives (the API-ripple set).** `role`/`channel`/`multi`/
   `multi_role`/`subsystem` are `discord.ui.Select` subclasses added via `view.add_item(...)`;
   windowing them means converting each to an `attach_*_select(view, …)` helper (built on
   `attach_windowed_select`) + updating their ~8 consumers (channels delete/visibility/create/
   restrict/move panels; roles xp/time/exemptions panels). Do it as **one focused PR** so the API
   change lands atomically. This retires `selectors/{role,channel,multi,multi_role,subsystem}` (6)
   and fixes real >25 bugs in subsystem (~35 entries) + guild role/channel pickers everywhere.
2. **The per-panel embedded selects.** `channels/move_panel`·`visibility_panel`·`create_panel`,
   `settings/subsystem_view` edit/reset selects, `setup/sections/channels`, `access/explorer`,
   `diagnostic/automation_panel` — each a small swap to `attach_windowed_select` with the host's
   own `select_row`/`nav_row` (mind the 5-row budget; see `access_map._attach_feature_detail_select`
   for the pattern). Some (e.g. the channels panels) truncate at the *source* (`text_channels[:25]`)
   before building options — fix the source slice too.

After those, the rule can graduate (b): once `select_option_truncation` runs quiet on a clean tree
across a few sessions, flip it to error + wire into `code-quality.yml`. Per the per-fire discipline:
**sync `origin/main` first.**

## 💡 Session idea (Q-0089)

**An `attach_*_select` convergence for `views/selectors/`.** This session surfaced that the shared
`views/selectors/` primitives are `Select` *subclasses* (added via `add_item`), which structurally
*cannot* paginate (pagination needs sibling nav items the subclass can't add to its own host). The
durable fix is to converge the whole `selectors/` package onto the `attach_*(view, …)` shape now
that `attach_windowed_select` exists — every shared picker becomes paginated-by-default, and a new
caller can't reintroduce the `[:25]` truncation because the primitive no longer exposes a
truncating constructor. Worth a small `docs/ideas/` entry (filed as the follow-up PR 1 above, which
is the first concrete instance). Not forced filler — it's the structural root the 15 remaining
findings share.

## ⟲ Previous-session review (Q-0102)

Previous run was #1048 (standalone ephemeral pickers → `PaginatedSelectView`). *Did well:* it left a
genuinely precise handoff — it named the exact remaining candidate set, correctly diagnosed *why*
`PaginatedSelectView` doesn't drop into them ("standalone, not embedded"), and explicitly flagged
"design step first, not a mechanical swap." That framing let this run start building the right thing
in minutes instead of re-discovering the constraint. *Could improve / system note:* #1048's handoff
said "either a new windowed-embedded helper **or** per-view nav" but didn't note the **row-budget**
constraint (Discord's 5 action-rows; an embedded select + nav can exhaust a panel that already has
4 button rows — the exemptions panel is the worst case). That's the one thing this run had to
re-derive. **System improvement surfaced:** when a handoff names a "design step," it should also name
the *binding constraint* the design must satisfy (here: the 5-row budget), so the next run doesn't
re-find it. Cheap, durable — it's the same "verify against the real constraint, not just the plan"
instinct the collaboration model already values; no doc change needed beyond doing it in handoffs
(this run's handoff does — it calls out `select_row`/`nav_row` + the 5-row budget).

## 📋 Doc audit (Q-0104)

current-state ▶ Next-action re-pointed (helper built; the 15-remaining migration named as the next
slice across two follow-up PRs) + a #1050 Recently-shipped ledger line. Recorded **#1049** on sight
(newest-merge lag, Q-0166). Plan doc (`repo-consistency-linter-plan-2026-06-17.md`) updated with the
#1050 helper + triage. No new owner decision this run. `check_current_state_ledger --strict` should
now be clean for #1049/#1050. The standing reconciliation-band marker (#1020) is the
reconciliation routine's lane; the next cadence pass fires at #1050 (Q-0107) — this PR *is* #1050 but
is a normal dispatch build, not the docs-only reconciliation pass (that routine auto-fires).

## 📤 Run report

- **Did:** built the embedded windowed-select helper (`attach_windowed_select` + shared
  `SelectWindow`) — the design step the #1048 handoff named — and triaged the 28
  `select_option_truncation` candidates → 15 (dogfooded on `access_map`, allowlisted 12 fixed-catalog
  selects). · **Outcome:** shipped
- **Shipped:** #1050 — embedded windowed-select helper + bounded-catalog allowlist triage; dogfood
  on access_map feature drill-down.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (dispatched lane — the live ▶ Next-action consistency-linter slice)
- **↪ Next:** migrate the 15 remaining genuinely-dynamic embedded selects onto
  `attach_windowed_select` — PR 1 = the shared `views/selectors/` primitives (API-ripple set: convert
  to `attach_*` helpers + update ~8 consumers, one focused PR); PR 2 = the per-panel selects (channels
  move/visibility/create, settings subsystem_view, setup channels, access/explorer, diagnostic
  automation). Then graduate the rule to error + wire into `code-quality.yml`.

