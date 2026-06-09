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

## Part 2 — Gate-lifting interview (same session, after #621 merged)

The maintainer asked for all unresolved questions via AskUserQuestion, plain-language,
with one recommended option each — goal: lift every gate blocking plan revision/execution.
**16 questions over 4 rounds; every recommendation accepted.**

Decisions (verbatim in router; new entries §22):
- **Q-0045** audience sim → governance tier-input path (P1B/P1C **unblocked**)
- **Q-0044** Spotlight → register via the Q-0025 scaffold as a community-hub child;
  `!hub`/`!server` aliases **dropped same session** (code)
- **Q-0046** orchestration P4 MVP → one vertical slice (round-cash family + 1 contract)
- **Q-0047** answerability P3 → all three read-only tools, gate lifted
- **Q-0048** gate posture → **standing lift for read-only deterministic AI tools**;
  writes/external/UI stay per-exposure
- **Q-0049** BTD6 refresh → manual-dispatch Actions workflow approved
- **Q-0036** denial copy → Claude drafts, maintainer reviews in PR
- **Q-0028–Q-0031** → catalogue committed · availability owns quiet mode · snapshots
  compound+high-risk · risk policy approved as written
- **Q-0032/Q-0033** → staff-hub subpanels only, no new command names · account links deferred
- **Q-0050** mining lights permanent (owner-confirmed §6.8 P2)
- **Q-0051** vision batch (Q-0038–Q-0042) → draft-answer session queued

Routed into: router (9 entries → Answered + §22 with Q-0046–Q-0051 + handling notes on
Q-0038–Q-0042), adaptive plan (§14/§15/§16.8), both AI plans, roadmap (at-a-glance + AI
gate + BTD6 sign-off), current-state (gates re-postured + lanes unblocked), help-map
banner, nav map, mining brainstorm §6.8, btd6 refresh plan banner.

### Context delta (part 2)
- The interview pattern worked: 4 rounds × 4 single-select questions with one
  recommended option each — the maintainer accepted all 16 recommendations, which
  suggests batching open router questions into recommendation-led interviews is an
  efficient periodic ritual (vs. letting Opens accumulate).
- **Next sessions, in decided order:** (1) Q-0025 scaffold → register Spotlight;
  (2) P1B remainder (tier-input path + drafted denial copy); (3) orchestration P4 MVP
  slice; (4) answerability P3 trio; (5) BTD6 manual-dispatch workflow; (6) the Q-0051
  vision draft-answer session.

## Part 3 — Workflow close-out

Maintainer confirmed the trust/alignment read on the interview ("I went with your
recommendations mostly because I actually agree … that's the exact proof that my memory
system is working") and **approved draft-PR-at-first-push** (it used to work that way and
silently lapsed) → codified as **Q-0052**: CLAUDE.md SESSION_WORKFLOW (edited with
explicit chat approval per Q-0035), journal Quick reference + END step 1, multi-lane plan
§2. The check_docs "(this session)"-marker gate stays a **proposal** (executable config).
Also shipped this part: the multi-lane execution plan itself + 3 earned journal rules.
Next session = the autonomous multi-lane test; prompt can be one line.
