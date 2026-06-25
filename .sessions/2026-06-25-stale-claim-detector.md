# Session — 2026-06-25 · slice 2 — route claim-GC + badges findings

> **Status:** `complete` — docs/routing slice. Run type: routine · dispatch.

## What this slice is (and the pivot)

Slice 2 of this dispatch run (slice 1 = Essential Setup PR 2, merged #1449). I set out to **build** a
stale-claim detector — the previous-session review (#1449's card) flagged that the 25th reconciliation
pass left a stale claim (`claude-jolly-johnson-rqf8wt.md`, branch merged via #1407). **Investigation
reversed the premise:** `scripts/check_stale_claims.py` **already exists** (built 2026-06-22, `--prune` +
5 tests), works correctly (verified — it catches that exact branch), and the reconciliation routine
prompt (`docs/operations/autonomous-routines.md` L162–163) **already mandates** running it with
`--prune`. So the tool is sound; the stale claim survived because the routine **skipped its own GC
step** across two passes. That's an execution-discipline gap, not a tooling gap — and the durable fix
(automation) is a *workflow proposal*, which CLAUDE.md says I route to the owner, never apply myself.

Also investigated (and dropped) the **extras-menu live status badges** follow-on to PR 2: it needs to
map each extra to a readiness subsystem, but reaction-roles has **no dedicated readiness subsystem**
(per-message data under `role`), and the schema registry is empty in an offline probe — so I can't
verify the mapping without a running bot. Shipping badges that might show wrong status is worse than
none (the repo's "verify against ground truth" rule). Routed, not built.

## What shipped (docs/routing only)

- **Router Q-0206 (DISCUSS)** — automate the claim-GC sweep so a skipped reconciliation step can't
  leave stale claims (the tool exists; only its *invocation* is forgettable).
- **S1 sector** — recorded the extras-badges follow-on (with its running-bot-verification blocker) in
  the PR-2 polish tail, so a future bot-access session can do it correctly.

No runtime code. CI mirror: `check_quality --check-only` + `check_docs --strict`.

## 💡 Session idea (Q-0089)

*A single plain-language "feature status" read model.* Building PR 2, both `build_check_setup_embed` and
(the dropped) extras badges needed the same thing: "is feature X configured, in operator words?" Today
that's an ad-hoc `_CHECK_ESSENTIALS` subsystem→label map plus a `setup_readiness` lookup, re-derived per
surface. A small `services`/`utils` read model — `feature_status(guild) -> {plain_label: on/off}` over
`setup_readiness.collect`, with one canonical subsystem→plain-label table — would let Check-my-setup, the
extras menu badges, the on-join welcome, and any future setup surface share one verified mapping (and is
exactly what would unblock the badges follow-on cleanly). One source of truth for "what's set up."

## ⟲ Previous-slice note (Q-0102 — run-level review in #1449's card)

This slice's own lesson: my slice-1 previous-session review *recommended building* a stale-claim
detector that **already existed** — I proposed a fix without first grepping for it. The discipline
Q-0200 is pushing (grep before defining) generalizes to *review notes too*: before proposing "we should
build X", `grep`/`ls` for X. I caught it here only because slice 2 started by reading the claims README,
which name-dropped the existing script. Cheap habit, real save.

## 📤 Run report (whole dispatch run — slices 1 + 2)

- **Run type:** routine · dispatch
- **What shipped:** **PR #1449** (merged) — Essential Setup PR 2 (extras menu + Check-my-setup); **this
  PR** — docs/routing: router **Q-0206** (DISCUSS, claim-GC automation) + S1 badges follow-on note.
- **⚑ Self-initiated:** none built unprompted (slice 1 = explicit S1 ▶-next plan slice; slice 2 = routing
  findings from slice-1's mandated review + grooming enders — no self-promoted idea→build).
- **⚑ Owner-decisions:** **Q-0206 raised (DISCUSS, needs owner)** — automate the claim-GC sweep.
- **⚑ Owner-manual-steps:** none (merges auto-deploy; no data/seed step — no data file changed).
- **Bug-book:** none fixed (the two open root-fix-backlog items stay gated); none newly opened.
- **Doc audit (Q-0104):** ledger in sync; plan + S1 sector de-staled (slice 1); router + S1 updated
  (slice 2); deleted the stale `claude-jolly-johnson-rqf8wt` claim on sight.
- **Handoff (▶ Next):** S1 = setup-wizard **PR 3** (retire dead spine sections + rework the Advanced
  draft→Final-Review editor, Q-E) — heavier/own-session. The extras-badges follow-on + Q-0206 are
  captured for a future bot-access / owner-decision pickup. Other S1 startables unchanged (Project Moon
  PR 1 · botsite React PR 2).
