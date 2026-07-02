# Idea — a single "START HERE" index for the fresh-rebuild doc-set

> **Status:** `ideas` — captured 2026-07-02 (Q-0089, thirty-second reconciliation pass).
> Lane: S3 (AI-Memory / the rebuild) + S4 (docs orientation). Size: small (one index doc + README
> row + roadmap link). `ready`-adjacent — pure orientation, no runtime code.

## The gap (grounded in this pass)

Reconciling band #1621–#1650 surfaced that the **fresh-rebuild initiative** — now the owner's top-focus
S3 lane — has accreted **nine planning docs in `docs/planning/`** with no single ordered entry point:

- `fresh-rebuild-strategy-2026-07-02.md` — verified baseline + plan-of-plans
- `rebuild-design-spec-2026-07-02.md` — the Fable 5 Phase-2 design spec
- `rebuild-parallel-execution-plan-2026-07-02.md` — the schedule (kernel / fan-out / gates / cutover)
- `rebuild-linchpin-validation-2026-07-02.md` — the commit-gate evidence package (§F)
- `memory-retention-and-context-economy-plan-2026-07-02.md` — the retention engine (Q-0214)
- `rebuild-ultracode-handoff-2026-07-02.md` — the launch prompt (§B start-gate, §F commit-gate)
- `portable-substrate-kit-extraction-2026-06-13.md` + `portable-agent-substrate-revision-2026-06-13.md`
  — the substrate-kit lineage the K0 gate builds on

A K0 executor (the queued Fable 5 ultracode session) starting cold must reconstruct the *map* — which
doc is the spec, which is the schedule, which gate comes first, which are superseded lineage — from nine
scattered files. The handoff §5 is the closest thing to a map, but the doc-set proliferated *after* it
was written, so it no longer enumerates the full set. This is exactly the drift the one-fact-one-home
rule exists to prevent, but for a reading *path* rather than a fact.

## The change

Add one short **`docs/planning/rebuild/README.md`** (or a "Rebuild doc-set" subsection in
`docs/planning/README.md`) that orders the set into a single reading path, each row carrying its **role**
and **gate-state**:

| Read | Doc | Role | Gate |
|---|---|---|---|
| 1 | fresh-rebuild-strategy | verified baseline + plan-of-plans | — |
| 2 | rebuild-design-spec | the architecture to build | 👤 owner design-approval |
| 3 | rebuild-parallel-execution-plan | the schedule | — |
| 4 | rebuild-ultracode-handoff §B | **start-gate** — finalise the memory system first | ▶ buildable |
| 5 | memory-retention-and-context-economy-plan | the retention engine | ▶ buildable (Q-0214) |
| 6 | rebuild-linchpin-validation | **commit-gate** evidence | ✅ evidence in (#1639) |

Plus a one-line "superseded lineage: `portable-substrate-kit-*` — read for history, not for the build."

## Why it's worth having

- The rebuild is the **top-focus lane**; the highest-leverage orientation doc in the repo right now is
  the one that lets its executor start correctly with no re-derivation.
- It is the two-gates model (start-gate §B vs commit-gate §F) made *findable* — the exact distinction the
  band-#1650 execution-plan session had to surface by hand.
- Cheap, reversible, and it keeps drifting as the rebuild adds docs — so pair it with the existing plan-
  homing convention so a new `rebuild-*` doc must be added to the index (the guard that keeps it fresh).

## Route

S3/S4. Executor: Claude-in-repo (docs-only). Promote directly (decided lane, small) or fold into the
next reconciliation pass's improve-the-system step.
