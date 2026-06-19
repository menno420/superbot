# 2026-06-19 — Dispatch: BUG-0016 + BUG-0017 (two bugs-first fixes)

> **Status:** `complete`

## Arc

Scheduled dispatch, no work order → advance the next plan slice. The website two-site
split's buildable wave is shipped (foundation #1109 + back-half #1112…#1118); the remaining
website slices are owner-paced rollout / security-review-gated. So **bugs first** (CLAUDE.md):
worked the bug book + a code-inspection sweep of the named "extend rule 4 to cogs" candidate,
which surfaced a second real bug.

## Shipped (PR #1120)

**BUG-0016 — stale reconciliation-trigger cadence copy (FIXED).**
- `.github/workflows/reconciliation-trigger.yml`: issue body "A multiple-of-20 PR band was
  crossed" → "A 30-PR band was crossed" (Q-0134 raised the cadence 20 → 30); "plans the next
  ~9 PRs" → "plans the next full band (depth ≥ the cadence, Q-0164)". Header comment updated to
  the full 10 → 20 → 30 history + a note that `check_reconciliation_due.py` (`STEP = 30`) owns
  the firing boundary so the copy must track it.
- Firing logic was never wrong (it keys off the script, already 30) — copy-only fix, no
  regression guard needed (the script's own tests cover the boundary). Marked FIXED in bug book.

**BUG-0017 — Cog Manager dropdown silently dropped 22 of 46 cogs (FIXED — found this run).**
- `disbot/cogs/admin/cog_manager.py`: the interactive Cog Manager select did
  `options=options[:25]`, but there are **46** `*_cog.py`; the 22 cogs sorting past the 25th
  were **unreachable** from the panel (owner had to use the `!cog` prefix escape hatch). The
  #1040 select-option-truncation class, living in the **cog layer** — which the consistency
  linter's `select_option_truncation` rule doesn't scan (it's `views/`-scoped), so the existing
  guard never saw it.
- Root fix: replaced the bespoke `_CogManagerSelect` + `options[:25]` with the project's
  `views.paginated_select.attach_windowed_select` (◀/▶ paging; `select_row=0`, `nav_row=3` leave
  the action row, refresh row, and the opener's row-4 Back button clear). Option-building moved
  to module-level `_build_cog_options(loaded)`.
- Stays-fixed guards (same PR): `test_cog_manager_view_windows_more_than_25_cogs_no_silent_drop`
  (page capped at 25 **and** ◀/▶ nav present when >25 cogs — fails against the old behaviour) +
  `test_cog_select_callback_stashes_selection_and_rerenders`. Marked FIXED (BUG-0017) in bug book.

Verification: `check_quality.py --full` green (10860 passed, 44 skipped) · `check_architecture
--mode strict` 0 errors · `check_docs --strict` clean.

## 📤 Run report

- **Did:** fixed BUG-0016 (stale reconciliation-trigger cadence copy) + BUG-0017 (Cog Manager
  dropdown silent `options[:25]` truncation → windowed). · **Outcome:** shipped
- **Shipped:** #1120
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (both are bug-book / inspection bug fixes — bugs-first lane, not
  a self-promoted feature)
- **↪ Next:** the routed follow-up — extend the consistency linter's `select_option_truncation`
  (and likely `panel_base_class`) rules to scan `disbot/cogs/` so a future cog-layer truncation
  is caught in CI, not by inspection (BUG-0017 was that blind spot). Otherwise resume the
  current-state queue (website rollout is owner-paced; consistency-linter AI-nav PR 1 is
  `needs-hermes-review`).

## 💡 Session idea (Q-0089)

**A repo-wide "platform-cap truncation" audit, layer-agnostic.** BUG-0017 slipped through because
the silent-truncation guard is `views/`-scoped, but the same `[:N]` silent-drop class applies to
*every* Discord platform cap, anywhere in the tree: select options (25), embed fields (25), embed
total (6000), message content (2000), action rows (5), buttons-per-view (25). Idea: a small stdlib
AST audit (`scripts/check_platform_cap_truncation.py`) that flags any `[:N]` slice where `N`
matches a known platform cap and feeds the matching Discord constructor — across `disbot/` whole,
not one layer. It's broader than "extend rule 4 to cogs" (which only covers selects in cogs) and
would have caught BUG-0017 regardless of layer. Warn-only/disposable per Q-0105; graduate the
high-signal caps once proven. *Genuine, distinct from the routed selects-only follow-up.*

## ⟲ Previous-session review (Q-0102)

The band-#1110 reconciliation pass (2026-06-19) did the right thing by **capturing BUG-0016 in the
bug book rather than leaving it as chat-only drift** — and scoping it precisely (exact file, exact
lines, the exact string change, and explicitly noting "not docs-only → out of scope for this pass,
a dispatch routine can land it"). That precision is *why* this dispatch run fixed it in minutes
instead of re-deriving it. Good handoff hygiene.

**Workflow improvement it surfaces:** a bug-book `OPEN` entry that a docs-only pass deliberately
defers has **no automatic nudge** into the next dispatch run — it relies on the dispatch agent
reading `docs/health/bug-book.md` (which the routine prompt does say to do, but it's easy to skim
past for a "no work order → advance the plan" run). Concretely: the SessionStart banner already
prints a `Ledger:` drift warning; it could similarly print an `OPEN bugs: N (oldest BUG-XXXX)`
line so a dispatch fire is steered toward bugs-first by the banner, not only by discipline. Cheap,
and it closes the "captured-but-unpicked-up bug" gap. (Routed as a candidate, not built this run —
it touches `scripts/claude_session_start.sh`, executable config the agent doesn't self-edit on its
own initiative per Q-0106; flag for owner / a directed session.)

## 📊 Telemetry

| Metric | Value |
|---|---|
| Bugs fixed | 2 (BUG-0016 copy, BUG-0017 cog-select truncation) |
| New regression tests | 2 (cog-manager windowing + select callback) |
| CI-red rounds | 2 (born-red session gate, by design) |
| Full mirror | green (10860 passed) |
| New ideas contributed | 1 (platform-cap truncation audit) |
| Ideas groomed | 0 |
