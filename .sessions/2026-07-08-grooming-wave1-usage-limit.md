# 2026-07-08 — Grooming wave-1 lane C: usage-limit-aware routines → plan

> **Status:** `complete`
> **Branch:** `claude/grooming-wave1-usage-limit-plan` · **PR:** #1845
> **Lane:** C (grooming-only) of the owner's 3-lane campaign wave (A = server-management
> subsystem audit, B = supersede-checker execution). Docs-only; forward-only git.

## What happened

**Grooming (the main task, Q-0015 lane):** structured
[`docs/ideas/usage-limit-aware-routines-2026-07-07.md`](../docs/ideas/usage-limit-aware-routines-2026-07-07.md)
from `ideas` → **`plan`**:
- New plan: [`docs/planning/usage-limit-aware-routines-plan-2026-07-08.md`](../docs/planning/usage-limit-aware-routines-plan-2026-07-08.md)
  — 2 PRs (PR 1: the `limit-deferred` + `send_later` re-arm clause into every saved routine
  prompt + the orchestration failure-class rule; PR 2: a stdlib deferral counter feeding the
  Q-0248/Q-0249 spend dataset). Ungated; kit portability flagged as a follow-up that rides a
  kit release.
- Homed per `check_plan_homing`: roadmap S5 standing lane (**Next** bullet) + the
  `docs/planning/README.md` S5 table row; idea file carries the PROMOTED banner; ideas README
  index entry updated. No idea was executed — routing/structure only.

**Anti-collision record (required deliverable):** at orientation (≈11:15 UTC) lanes A/B had
zero visible claims/branches/PRs — claims only travel via pushed branches/open PRs, so a
simultaneous-start wave has a blind window (that observation became this session's Q-0089
idea). Re-checks after my claim push resolved them:
- **Lane A** (`claude/audit-server-management-2026-07-08`): audit-only, server-management
  subsystem → I groomed nothing in server-management.
- **Lane B** (`claude/wave1-lane-b-supersede-checker`): executing
  `supersede-banner-integrity-checker-2026-07-06` → I left that idea **and its checker-family
  neighbors** (`reconcile-band-anchor-guard-2026-07-06`,
  `warn-first-checker-authoring-kit-2026-07-06`) untouched; my ideas-README edits sit ~17
  lines from lane B's index entry (separate hunks, git-mergeable), and I did not touch
  `docs/current-state.md`, which lane B claims.
- My groomed idea (S5 agent-workflow, `Subsystem: none`-adjacent) was chosen precisely
  because it can't overlap a bot-subsystem audit or lane B's checker build.

## 💡 Session idea (Q-0089)

[`docs/ideas/claim-remote-visibility-scan-2026-07-08.md`](../docs/ideas/claim-remote-visibility-scan-2026-07-08.md)
— born from the blind window above: `check_lane_overlap.py` reads only the *local* claims dir
(`scripts/check_lane_overlap.py:47`), so a sibling's claim on an un-merged branch is invisible
to the tool. Add a `--remote` mode scanning recent `origin/claude/*` refs for claim files not
on main (+ a "re-scan once right after your own claim push" protocol line). Worth having
because the owner now runs deliberate multi-lane waves and the pre-PR window is exactly where
the #1221 duplicate-work class lives. Dedup-checked (bug-book-claimed-signal ·
ci-cost-and-duplicate-work-prevention · ultracode-worker-pr-scope-guard — all different
surfaces).

## ⟲ Previous-session review (Q-0102)

The EAP permission-probe session (#1830) did the right epistemic move: it converted the
eval-journal's *relayed* permission-boundary claims into 11 first-hand probe tests with
verbatim classifier messages — closing its own predecessor's second-hand-evidence gap. What it
could have done better: its "⚑ Owner action" line asks the owner to delete the stranded
`test/permprobe-0708` scratch branch, but the report already knew the durable fix ("do not
create disposable remote refs in auto mode") — the caveat lives only inside that report.
**Workflow improvement:** that rule belongs in the auto-mode capability table the session
itself proposed for `docs/AGENT_ORIENTATION.md` (its own 💡 idea) — the improvement is to
*execute* that orientation-table idea rather than let two sessions in a row carry the fact in
prose; it is exactly the kind of one-table docs change a grooming or dispatch session can ship.

## Q-0104 doc audit

- `python3.10 scripts/check_current_state_ledger.py --strict` — green; only benign
  newest-merge lag (10 PRs newer than marker #1830, the sanctioned exception; recon is the
  routine's job, Q-0124 — this manual session does not run the pass).
- `python3.10 scripts/check_docs.py --strict` — all checks passed (710 docs; new plan + idea
  reachable via the roadmap / planning-index / ideas-README links added this session).
- `python3.10 scripts/check_plan_homing.py` flagged one piece of visible drift: the
  just-merged (#1843) `per-repo-settings-state-ledger-2026-07-08.md` plan was **unhomed** (no
  planning-index row, no roadmap link). Fixed on sight per Q-0166 (docs-only, inside this
  lane's already-claimed files): S5 row in `docs/planning/README.md` + a roadmap S5 **Next**
  bullet. Checker clean after the fix.
- Nothing from this session lives only in chat: the plan, the promotion banners, the new idea,
  and this card are the durable homes.

## 📤 Run report

- **Did:** grooming-only lane C — promoted `usage-limit-aware-routines` (ideas → plan, homed
  in roadmap S5 + planning index), added the claim-remote-visibility-scan idea, recorded the
  anti-collision narration · **Outcome:** shipped
- **Shipped:** PR #1845 (docs-only)
- **Run type:** `manual` (owner-directed campaign wave, lane C)
- **⚑ Owner decisions needed:** none — the promoted plan is ungated and reversible.
- **⚑ Self-initiated:** the idea→plan promotion itself (Q-0172 lane, flagged here); choice of
  which idea to groom was mine (rationale: most current — the routine fleet is multiplying and
  the kit-lab loop's standing routine should be born limit-aware).
- **↪ Next:** any session can build the plan's PR 1 (docs-only, ungated); the
  claim-remote-visibility idea is a natural small dispatch slice.

## 📊 Telemetry

| Metric | Value |
|---|---|
| Ideas groomed (moved down lifecycle) | 1 (`usage-limit-aware-routines`: ideas → plan) |
| New ideas contributed | 1 (`claim-remote-visibility-scan`) |
| Files touched | 8 (all docs/ · .sessions/ · claims/) |
| Collisions avoided | 2 (lane A server-management area · lane B supersede-checker idea + neighbors) |
| Drift fixed | 1 (unhomed #1843 settings-ledger plan → homed in planning index + roadmap) |
