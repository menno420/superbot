# Session: capture — routine dispatch, staged deep-clean reconciliation, planning sectors

> **Status:** `complete`

**Branch:** `claude/modest-ptolemy-2xipoh` · **PR:** #857 · **Date:** 2026-06-14 · **Type:** owner design discussion — capture + opinion (manual)

## What this session did
Owner dropped a substantial design direction in chat across several messages; I delivered my opinion
in chat and captured the whole thing durably so it can't be lost. **No runtime/code change** — this
is intake + routing of owner intent.

### Captured + routed
- **`docs/ideas/routine-dispatch-and-staged-reconciliation-2026-06-14.md`** — full owner direction
  (3 threads) + agent opinion, marked provisional (`ideas`, discussion in progress).
- **Router Q-0137** (DISCUSS lane) — the open owner decisions distilled, linked to the idea doc.
- **`docs/ideas/README.md`** — indexed (reachability + discoverability).
- **`docs/owner/active-work.md`** — cleared the stale #856 watchlist claim (Q-0126 drift I'd left in
  Active claims after that PR merged) → moved to Recently cleared; added this session's claim.

### The three threads + my position (short form; full in the idea doc)
1. **Dispatch:** endorse Hermes-dispatch — but the concrete change is just moving the **night
   executor** off GitHub's flaky `schedule:` cron onto the always-on Hermes VPS (general dispatch is
   already `/fire`). **Keep reconciliation independent — it's the watchdog** (runs `check_loop_health`);
   add a GitHub-cron **backstop** so a Hermes outage = "late" not "stopped."
2. **Staged deep-clean:** strong agree; separate *mechanical* (checker-generated punch-list) from
   *judgment* (roadmap/planning); make it a **resumable staged program** with a **terminal condition**
   (every sector has live Now/Next, zero rotting PRs/branches, ledger+docs green, control-plane verified).
3. **Sectors:** key reframe — **planning taxonomy ≠ review taxonomy**. Proposed S1 Bot · S2 BTD6
   (standing, spans A1+A2) · S3 Agent substrate (memory+docs-system+governance+tooling+loop) ·
   **S4 Operations/control-plane (the forgotten one — no home for non-file operational health)** ·
   (S5 substrate-as-product, future). In-bot AI = a slice within S1, per owner.

### Withdrawn this session
- A proposed **pre-merge-conflict hook** — owner withdrew it ("might not even be necessary") after a
  *parallel session* (#855) demonstrably self-handled the exact case: detected `mergeable_state:
  dirty`, merged `origin/main`, UNION-resolved `active-work.md` per the journal rule, re-ran CI. The
  orientation docs already drive that behaviour, so a hook is redundant. Not built.

## 💡 Session idea (Q-0089)
**A `scripts/check_open_pr_branch_health.py` sweep** — list open PRs with their mergeable/CI state +
stale `claude/*` branches whose PR already merged, emitting a disposition punch-list. It's the
mechanical half of the Thread-2 deep-clean (and would have caught the stale-claim drift class). Small,
read-only, GitHub-MCP-or-`gh`-driven; quick-win once the deep-clean shape is approved. Dedup-checked:
the existing `check_loop_health` covers the control-plane table, not PR/branch disposition — no overlap.

## ⟲ Previous-session review (Q-0102)
Reviewing **#856 (external-systems watchlist):** good — shipped clean, reachable, cross-linked. **What
it missed:** it left its `active-work.md` claim in **Active claims** after merging (I cleared it this
session) — the exact Q-0126 drift the ledger exists to prevent, caused by writing the claim in an early
commit and never moving it at close. **System improvement:** the `/session-close` skill (or the Stop
hook) should *assert* "your branch's claim is in Recently cleared, not Active" before a session ends —
turn the close-out ledger move from a remembered step into a checked one. (Sibling to this session's
Q-0089 PR/branch-health sweep.)

## Doc audit (Q-0104)
`check_docs --strict` ✓ (new idea doc reachable via README; Q-0137 + idea cross-link resolve) ·
`check_current_state_ledger --strict` ✓ · no code touched (no arch/quality run needed). New owner
*discussion* recorded as Q-0137 (DISCUSS, not a decision — nothing to enact yet). **Grooming (Q-0015):**
this session's main work *was* idea intake + routing (Threads 1–3 each given a state + destination);
backlog left live with the new PR/branch-health idea captured.
