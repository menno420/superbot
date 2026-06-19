# Session — extend consistency linter (select-option truncation) to `disbot/cogs/`

> **Status:** `complete`

**Lane B4 (ultracode fleet).** PR #1133.

## What & why
`scripts/check_consistency.py` rule 4 (`select_option_truncation`) was `views/`-scoped, a
real cog-layer blind spot — **BUG-0017** (the Cog Manager dropdown silently dropped 22/46
cogs via `options[:25]`) lived in exactly that gap. This is the plan's anticipated follow-up:
the rule-4 row ended *"extend rule 4 to `disbot/cogs/` … if a cog-level select truncation
ever surfaces"* — BUG-0017 was that surfaced case.

## Change
- **Rule 4 now scans both `views/` and `cogs/`.** The `SelectOption` module-gate is kept for
  both, so a leaderboard `[:10]` in a non-select cog stays OUT (only a file that actually
  constructs a `discord.SelectOption` is scanned).
- **Cog coverage is WARN-ONLY** via a new `Finding.force_warning` flag. `run_checks` keeps a
  `force_warning` finding at `warning` even though the rule is graduated to `error` for
  `views/` — so the not-yet-soaked cog scope can't fail CI before it graduates separately
  (the step-3 graduation discipline). The `views/` scope stays error-enforced, unchanged.
- `_all_files()` widened to include `disbot/cogs/`; the views-only rules
  (`edit_in_place`/`back_button`/`panel_base_class`) self-restrict via their own
  `rel.startswith("views/")` guard, so they still skip cogs.
- **`panel_base_class` for cogs: evaluated, NOT extended.** Cogs are `commands.Cog`
  subclasses, so the rule doesn't apply to the cogs themselves. A few cog *modules* define
  helper `discord.ui.View` subclasses (`cogs/logging/select_view.py`,
  `cogs/logging/provision_view.py`, `cogs/deathmatch_cog.py`, `cogs/settings_cog.py`) — a
  separate, larger triage surface, out of scope for this warn-only extension. Deliberately
  not extended (forced filler ≠ work); noted in the plan.

## First-run cog-scope finding count: **2** (net new genuine truncations: **0**)
Both are `top_xp[:3]` / `top_coins[:3]` in `cogs/community_spotlight_cog.py::_build_main_embed`
— top-3 leaderboard **embed** fields, not selects (the file's real `_GameSelect` builds from
the fixed `_GAMES` list, no slice). Allowlisted by `::qualname` so the file's select stays
checked. BUG-0017's Cog Manager dropdown is already windowed (#1120, `attach_windowed_select`)
so it produces zero findings — the rule is now its regression guard.

## Tests
Flipped the old cogs-scope **negative** (`test_trunc_only_scans_views`) into positives:
`test_trunc_flags_front_slice_in_cog_select` (a cog select front-truncation IS flagged),
`test_trunc_cog_finding_is_warn_only` (force_warning → stays `warning` through `run_checks`),
`test_trunc_cog_without_select_is_out_of_scope` (module-gate keeps a bare `[:10]` cog out),
`test_trunc_cog_allowlist_suppresses_by_qualname`, plus `test_all_files_includes_both_views_and_cogs`
and `test_views_only_rules_skip_cogs`. 42 tests pass.

## Verification
- `python3.10 scripts/check_consistency.py --mode strict` — exit 0 (cog coverage warn-only).
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors.
- `python3.10 scripts/check_quality.py --full` — green.

## ⚑ Self-initiated
None beyond the routed B4 lane — this is the plan's named follow-up for BUG-0017.

## 💡 Session idea
The linter graduates a *rule* as a whole, but this PR shows a rule can have **multiple scopes
at different maturities** (views graduated, cogs warm-up). Extend the `--graduation` tracker to
report **per-scope** soak state (e.g. `select_option_truncation [views: GRADUATED] [cogs:
NOT READY — 0 findings, soaking]`), driven by a small per-scope severity map on the `Rule`
instead of the single `force_warning` finding flag. That makes "is the cog scope ready to flip
to error?" a one-hop answer the same way `--graduation` already does for whole rules, and
generalizes cleanly to any future scope extension (e.g. adding `services/` to a rule).

## ⟲ Previous-session review
The `2026-06-18-cog-routing-pagination` session fixed the *views*-side #1040 truncation
(setup cog-routing select) and, tellingly, proposed exactly this idea as its session idea —
*"a lightweight invariant test that asserts every operator-facing select built from a registry
either paginates or stays ≤25, so the next subsystem that crosses a Discord limit fails loudly
at the source."* This PR is the cog-layer realization of that idea via the linter (a static
regression guard rather than a runtime test). What that session could have done better: it
flagged the *cumulative cross-PR drift* class but left the cog layer (where BUG-0017 then
surfaced) uncovered — closing the symmetric blind spot in the same pass would have pre-empted
BUG-0017. Workflow improvement surfaced: when a fix closes a limit-drift gap in one layer,
check the mirror layer (cogs ↔ views) in the same session — the linter's per-scope coverage is
now the durable mechanism for that.

## 📄 Doc audit
Plan doc (`docs/planning/repo-consistency-linter-plan-2026-06-17.md`) updated with the cog-scope
extension (shipped + count + panel_base_class N/A decision). No new owner decision (routed lane,
no CLAUDE.md/router change). Living-ledger / `active-work.md` are orchestrator-owned (not touched
this lane, per B4 hard rule).
