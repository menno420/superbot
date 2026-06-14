# Dispatch resolution — `dispatch_menu.py --json` wired into the Hermes dispatch skill

> **Status:** `ideas` — **not approved, not a plan.** Capture so it isn't lost. The Hermes-wiring half
> is gated on **Q-0137 Thread 1** (the owner's open dispatch decision); the `--json` half is a safe
> read-only quick-win. Source, the binding contracts, and `docs/current-state.md` win over this.

**Captured:** 2026-06-14 (from the sector-tooling session, PR #882 — the Q-0089 session idea, owner
invited the capture). **Owning area:** S3 AI-Memory / S5 Operations (the dispatch mechanism).

## The gap
`scripts/dispatch_menu.py` (#882) already *computes* the answer to "what would a worker dispatched to
sector SX pick up?" — per sector: the first **▶ startable** item, the **executor**, and whether the
sector is blocked. But it emits **human-readable text only**. The owner's goal — *"ask Hermes to
dispatch S2"* and have it resolve to a concrete work order — needs that resolution **machine-readable**
so Hermes can consume it, not just a person reading a table.

## Proposal (two halves)
1. **`dispatch_menu.py --json [SECTOR]`** (safe quick-win, repo-side, read-only). Emit the same
   resolution as JSON, one object per sector:
   ```json
   {"sector": "S2", "name": "BTD6", "executor": "Claude-in-repo",
    "state": "now_blocked_fallthrough", "startable_item": "P1-1 BTD6 eval cases",
    "source": "Next"}
   ```
   States: `startable` · `now_blocked_fallthrough` (→ Next) · `starving` (no ▶ anywhere) ·
   `maintainer_or_hermes` (executor isn't Claude-in-repo). Small: extend the existing parse + a test.
2. **Wire it into the Hermes `superbot-dispatch` skill** (gated on Q-0137 Thread 1). On *"dispatch
   SX,"* Hermes runs `dispatch_menu.py --json SX` and **routes by the resolved executor**:
   - `Claude-in-repo` → compose the `/fire` work order from `startable_item` (the existing dispatch
     bridge);
   - `Hermes-VPS` → Hermes does it itself (read-only ops, e.g. log-triage);
   - `maintainer` → reply to the owner with the manual step, don't fire an agent.
   This is the routing the #880 dispatch test showed is needed (don't fire a repo-editing agent at an
   S5 token task).

## Why it matters
It closes the **read-side of Q-0137 Thread 1**: the Q-0143 contract (`sector + action + executor`) and
`dispatch_menu` make the sectors dispatch-*ready*; this makes them dispatch-*resolved* — the owner names
a sector, the system computes the concrete task **and** the right runner. It's the missing link between
"the menu exists" and "Hermes fires the correct worker."

## Connections
- Builds on: `scripts/dispatch_menu.py` (#882), the dispatch contract **Q-0143**, the per-sector
  startability/executor tags (`docs/repo-sector-map.md`).
- Gated on / part of: **Q-0137 Thread 1** (Hermes-dispatch + cron backstop — owner-undecided).
- Composes with: [`hermes-claude-dispatch-bridge-2026-06-12.md`](./hermes-claude-dispatch-bridge-2026-06-12.md)
  (the `/fire` mechanism) and [`routine-dispatch-and-staged-reconciliation-2026-06-14.md`](./routine-dispatch-and-staged-reconciliation-2026-06-14.md).

## Sizing / risk
- `--json` half: **small**, read-only, repo-side — could ship in a grooming slice without the Thread-1
  decision (it just exposes existing output in another format).
- Hermes-skill half: a docs/skill change re-pasted onto the VPS; waits on Q-0137 Thread 1 because it
  defines *how Hermes dispatches*. No repo mutation from Hermes (preserves the safety split).

## Routing
→ **DISCUSS lane under Q-0137 Thread 1** for the Hermes-wiring half (it's part of the dispatch-mechanism
decision the owner owns). The `--json` half is a **quick-win** an executor can ship when it next touches
the sector tooling — not auto-promoted.
