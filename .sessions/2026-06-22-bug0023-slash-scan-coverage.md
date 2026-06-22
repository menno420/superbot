# 2026-06-22 — BUG-0023 root fix: scanner discovers `app_commands.Group` attribute slash commands

> **Status:** `complete` — Dispatch routine (no work order). Empty-fire run; bugs-first picked the
> top offline-fixable bug-book item: **BUG-0023 slash under-coverage**. Self-initiated (Q-0172).
> PR #1272, auto-merge armed on green.

> **Run type:** `routine · dispatch`

## What I'm about to do

BUG-0023's one real gap — *"static scan finds **25** slash, the live tree has **71** → the website
under-documents slash commands"* — was hypothesised in the bug book as *"dynamically-registered app
commands / context menus the AST cannot see."* **That hypothesis is wrong.** Investigated this run:

- 0 context menus, 0 `tree.add_command`, 0 hybrids in the codebase.
- The gap is **`app_commands.Group` declared as a class *attribute*** (`ai_app_group =
  app_commands.Group(name="ai", …)`) with subcommands decorated `@ai_app_group.command(…)`, in 6 cogs
  (ai · btd6 · btd6_events · btd6_ops · btd6_reference · btd6_strategy).
- `scan_commands._find_groups` only detects groups declared as **decorated methods**
  (`@app_commands.group`), so it misses these groups **and every subcommand under them**.
- Exact reconciliation: **25 standalone + 40 subcommands + 6 groups = 71** = the live tree count. All
  46 missing commands are **statically discoverable** — no runtime-aware counting needed.

This run: teach `scan_commands.py` to detect attribute-assigned `app_commands.Group` (and
`HybridGroup`) groups so their subcommands are scanned and the groups counted, regenerate the
dashboard/site data, and close BUG-0023's slash under-coverage at the root with a regression test.

## Files (planned)

- `scripts/scan_commands.py` — detect `X = app_commands.Group(...)` class-attr groups → register the
  group + scan its `@X.command` subcommands (inherit `slash`/`both`); emit the synthesized group record.
- `tests/unit/scripts/test_scan_commands.py` — a sample cog with an attribute-assigned slash group +
  subcommands; assert the group and its subcommands are scanned (fails against the pre-fix behaviour).
- regenerate `dashboard/data/dashboard.json` · `botsite/data/site.json` · `botsite/site/data.js`.
- `docs/health/bug-book.md` — mark BUG-0023 slash under-coverage FIXED (root) with the reconciliation.

## What shipped

- **`scripts/scan_commands.py`** — `_find_attr_groups(class_node)` detects class-attribute group
  assignments (`X = app_commands.Group(...)` / `HybridGroup`) → maps the variable name to
  `(command name, type, brief)`. `_scan_class` merges these into the `groups` map (so `@X.command`
  subcommands resolve their parent + slash/both type exactly like method-group subcommands already did)
  and emits a synthesized `is_group` record per attr-group. Added `_GROUP_CONSTRUCTORS`. The scanner's
  `by_type["slash"]` went **25 → 71** (matches the live `bot.tree.walk_commands()` count); total
  commands 322 → 368 (+40 subcommands +6 groups).
- **`tests/unit/scripts/test_scan_commands.py`** — `test_attribute_assigned_app_command_group_is_scanned`
  (a sample cog whose attribute slash group + subcommand are now scanned — fails against the pre-fix
  decorator-only behaviour) + `test_attribute_app_group_subcommands_counted_in_real_repo` (real-repo
  slash total reconciles to the bot tree, `>= 70`).
- **Regenerated** `dashboard/data/dashboard.json` · `botsite/data/site.json` · `botsite/site/data.js`
  (commands 322 → 368) so the website command explorer now documents the 46 previously-missing slash
  commands. `check_dashboard_data` self-consistent (counts derived from array lengths); committed-vs-fresh
  + data.js-sync tests green.
- **`docs/health/bug-book.md`** — BUG-0023 slash under-coverage marked **FIXED (root)**; corrected the
  wrong "dynamically-registered / can't see statically" hypothesis with the real cause + the
  25+40+6=71 reconciliation; status line updated.

## Findings / decisions

- **The bug-book hypothesis was wrong, and that itself is the lesson (Q-0120 instinct).** The entry
  guessed "context menus / dynamic registration the AST cannot see" and scoped the fix to a
  *runtime-aware* session. A 10-minute investigation (grep for context_menu / tree.add_command /
  hybrids → all zero; grep for `app_commands.Group(` → 6 hits) showed the entire gap is **statically
  discoverable**. A scoping note based on an unverified root-cause guess can defer a cheap fix
  indefinitely — verify the cause before trusting the scope.
- **Synthesize the group record (not just the subcommands).** The live `walk_commands()` counts the
  group object itself plus each leaf; emitting an `is_group` record for the attr-group makes the
  scanner's count reconcile exactly to 71 and matches how decorated-method groups already render.
- **Decision made alone — this is the slash-under-coverage (#3) root fix only.** BUG-0023's count
  *display* reconciliation (#1/#2, the `prefix · slash` breakdown on the site) stays folded into the
  React-migration PR 1, unchanged.

## 💡 Session idea

**A `scan_commands.py` ↔ live-tree reconciliation check (CI guard, Q-0105-disposable).** This bug
existed because nothing compared the static scan's slash total to the bot's live `tree.walk_commands()`
count — they silently diverged by 46. A tiny check that asserts the scanner's `by_type` reconciles to a
*recorded* live-tree snapshot (refreshed when the bot boots, the way the command-surface ledger already
captures a live snapshot) would catch the *next* AST-blind-spot class automatically — a new slash
group-declaration idiom the scanner doesn't yet recognise would fail the guard instead of quietly
under-documenting the website. (Dedup-checked: `test_manifest_drift.py` demotes the scanner vs the
runtime manifest spine but doesn't assert the slash *count* reconciles; this is the count-level guard.)

## ⟲ Previous-session review (Q-0102)

The previous dispatch run (Starboard PR 2 #1270 + `band_pr_status --themes` #1271) was strong — two
complete slices, both self-initiated and flagged, with a clean Q-0089 idea that mechanizes the
reconciliation routine. **Where it could improve:** its own card noted the `ruff --fix tests/` foot-gun
(339 files mutated, recovered) and filed a "`--changed-only` guard" idea — but the fix it reached for
already largely exists (`check_quality.py` default mode auto-fixes within CI's exact scope, *excluding*
`tests/`); the real gap is only "scope to my changed files," a narrow add. The lesson worth promoting:
**reach for `check_quality.py` (interpreter- and scope-pinned), never a bare `ruff --fix <path>`** — the
journal already says this, so the durable fix is habit, not new tooling. **System improvement
(initiated):** the session-idea above (a static-scan ↔ live-tree count reconciliation guard) is the
kind of cheap invariant that turns "an agent eventually notices the divergence" into "CI catches it" —
the same detector→guard shape the bug-book rewards.

## 📤 Run report

- **Did:** BUG-0023 slash under-coverage root fix (scanner discovers attribute-assigned
  `app_commands.Group` slash commands) · **Outcome:** shipped (PR #1272, self-merge on green)
- **Shipped:** #1272 — BUG-0023 slash-scan coverage root fix
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merged = deployed (the scanner/data change is build-time; no runtime
  data step). The site only reflects the 46 newly-documented commands at its next data export/deploy,
  which is automatic.
- **⚑ Self-initiated:** yes — empty-fire dispatch, no work order; bugs-first picked the top
  offline-fixable bug-book item (Q-0172). Contained, reversible, test-covered; flagged for owner review.
- **↪ Next:** BUG-0023's remaining piece is the count-*display* reconciliation (#1/#2 — show the bot's
  `prefix · slash` breakdown on the site), folded into the botsite React-migration **PR 1**. Other
  ungated lanes untouched: Project Moon runtime PR 1 (`needs-hermes-review`, needs network ingestion),
  creature leaderboards UI (gated on Explore-hub Q-0182), procedures→skills Batch 2
  (`needs-hermes-review`). Open bug-book root-fix backlog stays BUG-0019 #1 (owner decision) + BUG-0009
  newest-towers (data-gated) — both still gated, not offline-startable.

## ⟳ Doc audit (Q-0104)

`check_current_state_ledger --strict` + `check_docs --strict` green; bug-book BUG-0023 entry de-staled
to FIXED (root) with the corrected root cause. current-state Recently-shipped is deliberately **not**
touched (merged-PRs-only convention; #1272 isn't merged yet — the next reconciliation pass records it,
benign newest-merge lag). No new owner decisions (nothing for the router). The regenerated data
artifacts keep `check_dashboard_data` self-consistent.
