# Session — count-citation guard (soft check_docs rule)

> **Status:** `complete` — work done, PR #964, auto-merge on green.
> **Date:** 2026-06-16 · **Branch:** `claude/hopeful-meitner-772pv8` · **PR:** #964

## What I did

The owner-picked follow-on (#3 of the architecture-review thread): the **count-citation guard** — closes
the drift loop the three #957 fixes opened (bare hand-maintained inventory counts in binding docs).

1. **`scripts/check_docs.py`** — a **soft** check (`inventory_count_flags` / `print_inventory_count_report`,
   never changes exit code, like the census ratchets): flags a bare `N migrations/workflows/extensions/
   cogs/subsystems` in a **binding** doc unless it cites a regen command (`scripts/*.py`), is marked
   `generated`, or carries `<!-- count-ok -->`. Pinned-to-code docs exempt (their doc-tests guard counts).
2. **`tests/unit/scripts/test_check_docs.py`** — 6 logic tests; deliberately **no** repo zero-pinning
   test → keeps the guard genuinely soft (no FP hard-gate on a future legit count).
3. Idea docs updated: architecture-atlas #3 → shipped; `readiness-maps-cite-regen-command` → mechanism
   partially shipped (remaining: widen scope to `production-readiness/*`).

Design rationale: calibration grep showed the count pattern is widespread + often stale across non-binding
docs — a hard gate would red CI on dozens of pre-existing instances, against the repo's anti-FP-gate
culture. Soft + binding-scoped + pinned-exempt = clean zero-flag baseline now, useful nudge on any new
count. (The idea itself called for "a soft check_docs rule.")

## Verification
`check_quality --full` green (**10045 passed**, 37 skipped) · `check_docs --strict` clean ·
`inventory_count_flags()` on the live repo → `[]` (clean baseline).

## Session enders

**Grooming (Q-0015).** Executed idea #3 of the architecture-review thread (count guard) — moved it
routed→shipped in the capture doc, and advanced `readiness-maps-cite-regen-command` from captured →
*mechanism partially shipped* (the regex + cite/escape-hatch detection now exists; only the scope-widen
to `production-readiness/*` remains). The atlas thread is now fully executed (#957/#958/#960/#964).

**💡 Session idea (Q-0089).** **Surface `check_docs` soft warnings in the SessionStart banner.** This
session shipped a *soft* guard, and #960 shipped an atlas whose body isn't committed — both share a
weakness: a soft/generated signal only helps if someone *sees* it, and today you only see it by running
`check_docs` by hand. The SessionStart hook already surfaces arch / recon / ledger state; add a one-line
"check_docs soft: N top-level over budget · M inventory-count flags · K recently-shipped over budget" so
the soft ratchets are *proactively* visible (their whole design is to nudge, which requires visibility).
Dedup-checked: the banner shows arch/recon/ledger, not check_docs soft warnings; new. Small (one hook
line + a `check_docs --soft-summary` mode).

**⟲ Previous-session review (Q-0102).** #960 (the atlas) was a clean thin composer with honest scoping.
One genuine observation, reinforced by this session: #960 chose *body-not-committed* (invisible unless
run) and this session chose *soft warning* (invisible unless run) — independently reasonable, but the
pair reveals a systemic gap: **the repo keeps adding read-only signals that nobody is prompted to look
at.** That's exactly what the Q-0089 idea above addresses (surface them at SessionStart). Good call this
session keeping the count guard in `check_docs` (doc-hygiene domain) rather than folding it into the
atlas `--check` (code-structure domain) — the seams stayed clean.

**Doc audit (Q-0104).** Outputs homed: the `check_docs` change + tests, both idea docs updated to
shipped/partially-shipped, card. `check_docs --strict` green. Pre-existing, **out of scope**: the
`check_current_state_ledger` lag — owned by the #960-boundary reconciliation routine (Q-0124), which is
due/firing now.
