# 2026-06-18 — Consistency linter rule 4: select-option truncation

> **Status:** `complete`

## What & why
Added **rule 4 (`select_option_truncation`)** to `scripts/check_consistency.py` — the
UX/interaction-pattern linter (Q-0170). A Discord select caps at **25 options**, so a
*front* slice `options[:25]` / `roles[:25]` / `text_channels[:25]` **silently drops**
every entry past the cap instead of paginating — the exact **#1040** bug (the cog-routing
picker dropped `moderation`/`role`/`settings`/… once the registry grew past 25).

This rule was **surfaced by a real bug + the previous session's explicit session-idea**
("turn registry-built-select limit-drift into a CI signal at the source"), i.e. a genuine
review-surfaced mechanical-consistency shape — exactly what the linter plan reserves rule
4+ for, not invented filler.

## Change
- `scripts/check_consistency.py`:
  - `rule_select_option_truncation` — scopes to `views/` files that construct ≥1
    `discord.SelectOption`; flags a `Subscript` slice with lower `None`/`0`, **integer
    constant upper ≤ 25**, no step. Helpers `_builds_select_options`,
    `_is_front_truncation`, const `_SELECT_OPTION_LIMIT = 25`.
  - Registered in `RULES`; module docstring updated.
  - **Windowed pagination** (`x[start:start+N]`, variable bounds — the correct #1040 fix
    in `_CogPickView`) and **string-length** slices (`label[:100]`, N > 25) are correctly
    NOT flagged.
- `architecture_rules/consistency_exceptions.yml` — added the `select_option_truncation`
  allowlist section (empty; warn-only triage in follow-up).
- `tests/unit/scripts/test_check_consistency.py` — +6 tests: positive (front-truncated
  options) + windowed / string-limit / non-select / cogs-scope / allowlist negatives.
- De-staled the [linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md)
  (rule 4 row + PR-4 shipped note) and current-state ▶ Next action.

**First-run count: 53** — the #1040 silent-drop is a *widespread* class, not an isolated
bug (shared `selectors/`, roles/channels panels, mining market, btd6 browsers, settings
enum-editor). A small subclass are genuine top-N *display* truncations (e.g. a preview
`operations[:10]`, an error-message `valid_towers[:8]`) to allowlist during triage; the
rest are real selects to paginate.

`check_quality --full` green (10635 passed, 38 skipped); `check_architecture --mode strict`
0 errors. Pure tooling + tests; no `disbot/` runtime change.

## ⚑ Self-initiated
Yes — promoted the previous session's logged session-idea (#1040) into consistency-linter
**rule 4** and built it without a dispatch/owner ask (Q-0172 idea→build gate). Contained,
reversible, warn-only read-only tooling. Owner can review/revert via this PR.

## 💡 Session idea
**A `severity: error`-on-regression ratchet for warn-only linter rules.** Right now a rule
graduates to `error` wholesale only once the *whole* tree is clean. But for rules with a
long-lived warn backlog (edit_in_place=45, select_option_truncation=53), a *new* violation
hides in the noise for sessions. Idea: a committed per-rule baseline count (like the arch
checker's known-violations ratchet) so `check_consistency --mode strict` fails when a rule's
count **rises above its baseline** — catching new drift immediately while the backlog is
triaged down, the same way the architecture checker already ratchets `views→cogs`.

## ⟲ Previous-session review
The previous session (#1040, cog-routing pagination) did the right thing: while reviewing
the `needs-hermes-review` queue it caught a *latent* cross-PR bug (the registry crossing
Discord's 25-option cap), fixed it at the root with real pagination, AND logged a precise
session-idea to turn the class into a CI signal — which this session built. That's the
self-auditing loop working as designed. One thing it could have done: the bug it found
(`[:25]` silent truncation) was visibly *not unique* to cog-routing — a 30-second grep
(`rg '\[:25\]' disbot/views`) would have shown the ~7 other `[:25]` select sites, so the
"is this a class?" instinct could have fired one session earlier. **Workflow improvement:**
the session-idea ratchet above (baseline-count regression guard) closes the gap between
"a rule exists" and "a new violation is caught now" — turning each of these warn-only rules
into a live guard instead of a static report that needs a human to diff.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1044 (consistency rule 4 — select-option truncation)
- **Result:** shipped; CI mirror green; auto-merge armed (small/contained → self-merge on green, Q-0113).
- **⚑ Self-initiated:** rule 4 (promoted the #1040 session-idea → build, Q-0172).
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none

## Doc audit (Q-0104)
- Recently-shipped ledger: #1044 not added (correct — merged-PRs-only; benign newest-merge
  lag, the next session/recon adds it once merged). Reconciliation marker stays #1020.
- Plan + current-state ▶ Next action de-staled to rule 4. No new owner decisions to route.
- bug-book: no new entry (this is prevention tooling for the already-FIXED #1040 class;
  #1040 is on `main`, not a bug-book OPEN).
