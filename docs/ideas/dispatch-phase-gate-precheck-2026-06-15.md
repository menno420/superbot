# Dispatch-side phase-gate pre-check — don't fire agent-feature work orders in fix-phase

> **Status:** `ideas` — proposal, **not** approval. Written by the Claude Code routine that
> received a `CLASS: feature` work order ("Implement Mining Phase 2 — Forge/Vault/Home +
> skill-tree") on 2026-06-15 while the repo was in **fix-phase**. Grounded in what actually
> happened that run (the gate fired, the feature was refused) + the orphan PR #888 a prior
> run left behind. Binding contracts + `docs/current-state.md` win.

## The concrete event this captures

A feature work order arrived via the dispatch fire endpoint. The executor side did the
**right** thing per the routine prompt: ran `scripts/check_phase_gate.py --require-invent`,
got **exit 1 (fix-phase)** — 2 OPEN bugs + 28 `Not Done` readiness rows — and refused to
build, because agent-*originated* features are gated until correctness work clears (Q-0114).
The work was already captured anyway: the turn-key
[`planning/mining-structures-skill-tree-plan-2026-06-14.md`](../planning/mining-structures-skill-tree-plan-2026-06-14.md)
covers Forge/Vault/Home + skill-tree as source-verified PR-sized slices.

So the run shipped **nothing buildable** — by design, correctly. But two things were wasted:

1. **A whole dispatch was burned** on work the dispatcher could have known was out of season.
   The limited daily routine budget (routine-system-improvements Priority 5, "productive once
   started") was spent capturing-and-stopping on an already-captured plan.
2. **A prior run (#888) left an orphan.** That run received the *same* dispatch, **skipped the
   executor phase gate**, and opened a "slice opener" docs PR pretending to tee up build
   work — a thin duplicate plan in the wrong dir (`docs/plans/` vs the repo's `docs/planning/`),
   stuck `in-progress` (born-red), on a non-`claude/*` branch so it could never auto-merge.
   An un-gated feature dispatch is exactly what produces this kind of stuck artifact.

## The proposal — gate at the dispatcher, not only the executor

The phase gate today is an **executor-side self-guard**: each routine runs
`check_phase_gate.py` *after* it has already spent a fire. Move a copy of that check
**upstream into the dispatch step** (Hermes' `superbot-dispatch` skill):

- Before firing a work order classified `CLASS: feature` (agent-originated), run
  `scripts/check_phase_gate.py --phase`. If it returns `fix`, **do not fire that feature** —
  instead either (a) re-route to the standing fix-phase queue (current-state ▶ Next action →
  else an OPEN bug-book item → else backlog grooming, the same ladder the executor falls back
  to), or (b) hold the feature in a "queued until invent-phase" list and fire it automatically
  when the gate next flips to `invent`.
- `CLASS: fix | ux | docs | correctness` always fire (they flow freely in fix-phase) — the
  pre-check only gates `feature`.
- Keep the executor-side gate as the **backstop** (defense-in-depth): the dispatcher can be
  wrong or stale, so the executor still refuses if it somehow receives a gated feature. The
  point is to stop *wasting the fire*, not to remove the safety net.

This is the dispatch-edge complement to routine-system-improvements Priority 3 ("make Hermes
use the dispatch contract it already has") and Priority 5's owner-vs-agent clarity: Hermes
already *classifies* by `CLASS:`; it should also *check season* before firing the one class
that can be out of season.

## Why it's worth having

- **No burned fires on out-of-season features** — the scarce daily budget goes to in-season
  fix/UX/docs/correctness work that actually moves the phase gate toward invent-phase.
- **No more #888-class orphans** — a feature that never fires in fix-phase can't produce a
  stuck "slice opener" PR.
- **Cheap and reuses an existing primitive** — `check_phase_gate.py --phase` already prints
  `fix`/`invent`; the dispatcher just reads one line and branches. No new contract.

## Routing

- Mechanism (add the pre-check to the dispatch skill) is a small Hermes-side change once the
  shape is endorsed; relates to **Q-0137** Thread 1 (Hermes dispatch wiring, owner-undecided)
  and the `routine-dispatch-and-staged-reconciliation` capture. No owner decision is strictly
  required to add a *guard* that only prevents wasted/incorrect fires — but flag it under
  Q-0137 since it touches Hermes' dispatch behavior.
