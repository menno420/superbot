# 2026-06-09 — Full repo review + docs reconciliation + spotlight hardening

## Arc

Maintainer asked for a thorough capability-demonstrating review: errors/inconsistencies,
docs-structure + navigability assessment, plan-executability assessment (refining while
working), output as both a repo document and a chat summary, outdated docs updated on
sight. Deliverable: [`docs/audits/repo-review-2026-06-09.md`](../docs/audits/repo-review-2026-06-09.md)
+ a wide reconciliation pass + a contained code fix.

## Shipped

- **The audit doc** — verification snapshot (CI mirror 8352 passed / arch 0 errors /
  docs checks green), 9 fixed inconsistencies, 2 routed owner questions, docs-structure
  verdict, 4-lane plan-readiness table, prioritized recommendations R1–R6.
- **Community Spotlight hardening** (the side-lane #613/#614/#615/#617 feature): the
  only raw-SQL-in-a-cog in the repo moved onto the canonical owner
  (`utils/db/xp.py get_guild_xp_totals` + re-export), `member_count=None` format crash
  fixed, first 6 tests added. Integration depth + greedy `!hub`/`!server` aliases routed
  as **Q-0044** (registration = the Q-0025 scaffold's natural first consumer); bannered
  in `help-command-surface-map.md` §3.
- **current-state.md reconciled**: 10 stale "Reconcile PR #" markers resolved against
  live GitHub (#619 / #610 / #609 / #594 / #592), the unrecorded Community Spotlight
  lane added, the reconciled Q-0026 debt block retired, and the two ~3,000-char
  single-line header paragraphs (▶ Next action / Last updated) restructured into
  readable bullets (doc-test pins sections, not formatting — verified before editing).
- **roadmap.md re-horizoned**: AI "Later (fully gated)" → "Now (active lane;
  per-exposure gate lifts)"; games "Later/maintenance" → "Now (mining Wave 1)";
  at-a-glance table now mirrors current-state's three lanes; the stale
  "wire `!explore` awaiting go" bullet folded into the shipped list (#606).
- **Plan/contract syncs**: ownership.md role-threshold cell → audited seam (#592);
  orchestration plan + answerability roadmap + wire-exploration plan PR #s reconciled;
  adaptive plan §15.3 re-synced (P1B partial-shipped reality) and §16.8 item 3
  promoted to **Q-0045** (audience simulation — blocks `help_advertises_locked` + P1C).
- **Journal runbook corrections**: "latest migration 057" → 062 (with a
  check-disk-not-this-number phrasing), "~7470 tests" → ~8.3k.

## Verification

- `python3.10 scripts/check_quality.py --full` → green (8358 passed, 16 skipped after
  the 6 new tests). `check_architecture --mode strict` → 0 errors. `check_docs.py` →
  pass (the new audit doc is reachable via current-state).
- New tests: `tests/unit/db/test_xp_totals.py` (3) +
  `tests/unit/cogs/test_community_spotlight_cog.py` (3).

## Context delta

- **Needed but not pointed to:** nothing for orientation itself — the prescribed read
  path carried the whole session (worth saying explicitly: the system worked as
  designed for a cold-start agent on a meta task).
- **Discovered by hand:** the **side-lane blind spot** — a feature merged outside the
  session workflow (#613/#614) bypassed *three* nets at once: the integration standard
  (no registry entry), the doc-test net (pins only registered surfaces), and
  current-state recording. The audit doc names this as a class, not a one-off.
- **Discovered by hand:** `Edit` replace_all of a line-tail sentence with `""` can
  consume the trailing newline and merge bullets — re-split with a regex and **verify
  line structure after bulk doc edits** (`grep -c '^- '` before/after).
- **Pointed to but didn't need:** CodeGraph symbol tools — for a docs-vs-source review,
  `context_map.py` + grep + the doc-tests were the right altitude; the graph stats
  (cycles, coupling) fed exactly one audit table row.
- **Process note:** two background Explore scouts (docs-staleness sweep + plan-readiness
  assessment) parallelized the review well, but one scout claim was wrong
  (claimed #615 renamed `community_cog.py`; actually both cogs exist) — the
  "verify cross-agent output against source" rule earned its keep again.
- **Unresolved for next session:** reconcile this PR's # into current-state (the R3
  recommendation — draft-PR-first or a freshness gate — would end this recurring step);
  Q-0044/Q-0045 await answers; #620 (test-only) was open at session end.
