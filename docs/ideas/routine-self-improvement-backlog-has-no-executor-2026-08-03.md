# Idea — the reconcile routine's self-improvement backlog has no executor under oracle-freeze

> **Status:** `ideas` — session idea (Q-0089), captured 2026-08-03 (54th Q-0107 reconciliation pass,
> band-#2310). Not approved for implementation. · **Subsystem:** none (agent-workflow / meta).
> Has an owner-decision dimension — flagged on the pass run report.

## The observation

Dedup-checking for this pass's Q-0089 idea, I hit **two already-promoted-but-never-executed**
reconcile-routine improvement plans back to back:

- [`ideas/loop-health-gh-unavailable-fallback-2026-06-19.md`](loop-health-gh-unavailable-fallback-2026-06-19.md)
  → **promoted to a plan 2026-06-20** ([`planning/loop-health-gh-fallback-plan-2026-06-20.md`](../planning/loop-health-gh-fallback-plan-2026-06-20.md)),
  "ungated, one PR". The `check_loop_health.py` SKIP it targets **still fires on this pass** — 1.5 months
  and ~14 passes later — so I did the manual MCP author-read fallback *again* to confirm ROUTINE_PAT.
- [`ideas/reconciliation-cadence-exclude-generated-prs-2026-07-19.md`](reconciliation-cadence-exclude-generated-prs-2026-07-19.md)
  → **collected into [`planning/routine-debt.md`](../planning/routine-debt.md) item 2** (self-mergeable
  `check_*` change). Still uncollected-into-a-PR; the 53rd pass carried the whole `routine-debt.md` batch
  again and added a carry-status escalation because it noticed the collector had no *drain* edge.

The 53rd pass's carry-escalation idea makes the debt's **aging visible**. This idea is the layer under
it: the reason it ages is **there is no executor at all**. Every one of these fixes is a `scripts/*.py`
or workflow change, and:

1. The **docs-only reconcile routine is forbidden from touching `scripts/`** (STRICTLY DOCS-ONLY,
   Q-0107) — so the routine that *generates* these ideas can never ship them.
2. superbot is **frozen as the superbot-next oracle**, so **no dispatch / feature / tooling session
   ever runs here** to pick them up. The dispatch routine that used to drain tooling debt is effectively
   dark on a frozen repo.

Net: the reconcile routine is a **producer with no consumer** for its own self-improvement output. It
faithfully mints ideas → plans → `routine-debt.md` entries every pass, and they accumulate with a
monotonic backlog and zero throughput. `PLAN BACKLOG THIN` (product backlog empty) and this
(self-improvement backlog *full but undrained*) are the two halves of the same freeze artifact.

## The idea

Give the self-improvement backlog an **executor**, one of two shapes (owner picks):

1. **Let the reconcile routine ship its own self-scoped tooling.** Carve a narrow exception to
   DOCS-ONLY: the reconcile routine MAY modify the `check_*`/tooling scripts *that implement its own
   pass* (`check_loop_health.py`, `check_reconciliation_due.py`, `check_current_state_ledger.py`,
   `check_docs.py`) when the change is in `routine-debt.md` and marked self-mergeable — still never
   `disbot/` runtime, migrations, or tests. This makes the producer its own consumer for the exact
   debt it generates.
2. **Schedule a periodic "routine-debt drain" dispatch session on superbot** — a thin recurring
   tooling seat whose only job is to land the self-mergeable `routine-debt.md` items as one
   docs-tooling PR, even while the product is frozen. Keeps DOCS-ONLY intact for the reconcile
   routine; adds a separate draining actor.

Either closes the loop the carry-escalation idea only *measured*.

## Why it's worth having

- **The backlog is real and monotonically growing.** Two dead plans found in one dedup grep is not
  noise — it's the steady state. Every future pass will keep minting ideas the freeze guarantees no
  one executes, which quietly devalues the Q-0089 "one genuine idea per pass" mandate into an unread
  queue.
- **The fixes are cheap and self-contained.** `loop-health` fallback is one `urllib` PR; the
  cadence-exclude is a pattern list. They stay unbuilt only because no actor is allowed+scheduled to
  build them, not because they're hard.
- **It makes the freeze honest.** A frozen *product* is the intent; a frozen *toolchain that keeps
  asking to be improved and can't be* is an accident of the DOCS-ONLY fence meeting the no-dispatch
  reality.

## Reliability / kill-switch

Pure workflow/policy change — no code here. Shape 1 is reversible by re-tightening the DOCS-ONLY fence;
shape 2 by unscheduling the drain seat. If neither is wanted, the honest alternative is to **stop
minting self-improvement ideas on frozen-repo passes** (make Q-0089 skippable under oracle-freeze) so
the backlog stops growing — that decision is itself the owner call this idea surfaces.

→ relates `docs/planning/routine-debt.md` · `docs/operations/autonomous-routines.md` (STEP 2
control-plane + DOCS-ONLY scope) · `loop-health-gh-fallback-plan-2026-06-20.md` ·
`reconciliation-cadence-exclude-generated-prs-2026-07-19.md`.
