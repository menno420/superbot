# 2026-07-08 — Grooming: PR #1846 follow-ons (Wave-2, coordinator-dispatched)

> **Status:** `complete`
> **Run type:** grooming-only, docs-only · Branch `claude/groom-pr1846-followons` · PR **#1854**.

**Intent:** docs-only grooming pass routing the four follow-on items surfaced by merged
PR #1846 (supersede-banner integrity checker) into their correct documentation homes per
the `docs/ideas/README.md` lifecycle. No code/checker changes.

## Routing decisions (one-line rationale each)

| Item | Home | State | Rationale |
|---|---|---|---|
| **A** `--strict` promotion | [`docs/ideas/supersede-banner-integrity-checker-2026-07-06.md`](../docs/ideas/supersede-banner-integrity-checker-2026-07-06.md) § Follow-ups | tracked note, trigger: *~5 sessions/passes of clean warn output (Q-0105 proving period)* | Future-conditional on the idea's own artifact → its lifecycle home, not a new file. |
| **B** culprit-attribution for live-tree tests | [`docs/ideas/live-tree-test-culprit-attribution-2026-07-08.md`](../docs/ideas/live-tree-test-culprit-attribution-2026-07-08.md) + README index entry | new idea file | Genuinely new (dedup-grepped ideas + roadmap: no hit); promotes the #1846 card's deliberately card-only Q-0089 flag into the backlog where grooming can find it. |
| **C** how did #1843 "merge red"? | [`docs/operations/ci-what-runs-where.md`](../docs/operations/ci-what-runs-where.md) §2b, dated note | inline answer (cheap — one check-runs API call + git log) | It merged **green-by-skip**: docs-only fast path skipped pytest (12 s green run on head `faaa29f`), so the live-tree homing test never ran on the PR that introduced the unhomed plan; the CI-coverage map is where that gap class is catalogued. |
| **D** extend checker to `.sessions/` + mid-doc banners | same § Follow-ups as A | tracked note, trigger: *warn-period output shows real drift in `.sessions/` or mid-doc banners* | Same artifact, same future-conditional shape as A; checker header explicitly scopes these out today, so extension must be evidence-driven. |

**Item C full answer (also in the ci-what-runs-where note):** PR #1843's required
`code-quality` check ran green in 12 seconds (11:06:56→11:07:08Z) on head `faaa29f` because the
workflow's docs-only fast path skips ruff/mypy/pytest; `check_docs --strict` (which does run on
docs-only PRs) checks reachability/badges, not plan homing. #1843 added
`docs/planning/per-repo-settings-state-ledger-2026-07-08.md` without a routing-doc link, so
`test_live_repo_plans_are_all_homed` — a live-tree test validating the checked-out tree, not
the diff — failed on every subsequent full-CI branch until parallel sessions homed the plan
(#1845 `75a495a`, #1846-lane `58a2e24`, dedup `0dc13f6`). Not a stale-base race, not a red
merge: the required check passed legitimately under its fast path; the test it would have
failed was skipped by design on exactly the PR class that introduces this drift.

## ⚑ Self-initiated

Coordinator-dispatched grooming (Wave-2, PR #1846 follow-ons) — the four routings above are the
dispatched scope; no un-dispatched promotions. The one judgment call: answering item C inline
(it was cheap) instead of filing a router Q-block.

## Backlog grooming (Q-0015)

This session **is** a grooming pass: it moved one implemented idea's follow-ups into tracked
trigger-conditioned notes (A/D), promoted one card-only Q-0089 flag into a real backlog idea
file (B), and closed one open question inline (C).

## 💡 Session idea (Q-0089)

**Warn-first proving-period evidence trail.** Item A's promotion trigger ("~5 sessions of clean
warn output") is currently uncheckable — nothing records how many times a Q-0105 warn-first
checker has run clean, so promotion/deletion decisions rest on vibes and archaeology. Idea: the
session-close skill (or `check_docs`' soft-check summary) writes one greppable line per
warn-first checker into the session card (`warn-checker: check_supersede_integrity=0 findings`),
so "N clean sessions" is answerable with one grep over `.sessions/`. Dedup-checked:
`warn-first-checker-authoring-kit-2026-07-06` scaffolds *new* checkers,
`sim-assumption-telemetry-loop-2026-06-22` is the same self-verifying instinct for sims — neither
tracks proving-period outcomes. Card-flag capture (small, protocol-level); worth an idea file if
a second consumer appears.

## ⟲ Previous-session review (Q-0102)

Reviewed: the Wave-1 lane B session (PR #1846). Genuinely strong — it verified its checker's
detection was non-vacuous against ground truth (Q-0120 discipline: 6 banners + 5 rows detected,
0 findings), fixed the #1843 homing drift on sight (Q-0166), and yielded cleanly to the parallel
#1848 homing fix instead of duplicating the index row. One miss / concrete workflow improvement:
its Q-0089 idea was deliberately left as a **card-only flag** ("campaign rails route follow-ons
to Wave-2 grooming") — which worked only because a coordinator actually dispatched this Wave-2
pass. A card-only 💡 flag is invisible to `groom-ideas` (which browses `docs/ideas/`), so an
undispatched follow-on would rot. Improvement: campaign rails should have EXECUTE lanes still
write the one-paragraph idea *file* (cheap, ~2 min) and let grooming enrich it later — or
`groom-ideas` should also grep recent `.sessions/` cards for 💡 flags that lack a matching idea
file.

## Docs audit (Q-0104)

- `python3.10 scripts/check_current_state_ledger.py --strict` — see verification below.
- `python3.10 scripts/check_docs.py --strict` — see verification below.
- New idea file reachable via the README index; follow-ups live on the idea's own artifact;
  item C's answer is in the CI-coverage map with a link back to the new idea. Nothing
  chat-only left unhomed.

## Verification

- `python3.10 scripts/check_current_state_ledger.py --strict` ✓ (exit 0; 19 PRs newer than
  marker #1830 = benign newest-merge lag, next reconciliation pass records them)
- `python3.10 scripts/check_docs.py --strict` ✓ (all checks passed; new idea file reachable)
- `python3.10 scripts/check_supersede_integrity.py` ✓ (web intact after the follow-ups edit)
- `python3.10 scripts/check_plan_homing.py` ✓ (81/81 homed — item C's drift confirmed fixed)
- No visible docs drift found beyond what this session was dispatched to route (Q-0166 sweep:
  the ledger lag above is the allowed benign class).
