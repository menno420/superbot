# 2026-07-02 — Memory retention & deletion policy (design session)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual ·
> owner-directed (ultracode brainstorm). Docs + `tools/sim/` only; no `disbot/` code; **no real
> content deleted this session** (one stale claim file removed — its checker surfaced it).
> PR #1643.

**Branch:** `claude/memory-retention-policy-u8espg`

## What I was asked

Owner brainstorm (design, not build): rethink retention vs. deletion for the AI-memory/docs
system — aggressive deletion + hardcoded caps, grounded against the actual repo (Q-0120), the
numbers found empirically by a simulator, folding into the substrate-kit's reserved
context-budget slot. Deliverable: a reviewable proposal an ultracode session can implement.

## What shipped

1. **[`docs/planning/memory-retention-and-context-economy-plan-2026-07-02.md`](../docs/planning/memory-retention-and-context-economy-plan-2026-07-02.md)**
   — the policy (3-tier: live / referenced-terminal / unreferenced-terminal), per-class table
   (session logs delete harvest-gated · plans archive-with-stub · rejected ideas keep · ledger
   tails migrate-then-compress), hard caps + enforcement (checker+actuator, Tier M/J), the
   git-provenance analysis, failure-mode record, 3-PR implementation plan, substrate-kit slot.
   Registered in the plan index (S4) + S4 sector ▶ + companion cross-link on the orientation plan.
2. **`tools/sim/retention_policy_sim.py`** — the retention simulator (house sim-driven-design
   pattern, 4 guardrails honored): corpus growth + read-cost model calibrated on 2026-07-02
   measurements, policy grid search, hard zero-retrieval-loss constraint, sensitivity sweep.
   Headline: keep-everything 92k words/session-equivalent vs ~27.3k under the winning policy
   (−70%); archive≈delete within 0.4% on read cost (sign favors archive) — deletion wins the
   boundedness secondary; bare deletion (no tombstones) is the one infeasible mode.
3. **Evidence base** (5-agent grounding workflow + 3-lens adversarial panel + inline
   measurements): corpus 1.61M words / 55% terminal; grep noise 69.6% terminal; session-log
   afterlife 5.3% (zero date-distant backrefs); historical-plan genuine afterlife 3/41; router
   Q-refs 5,422 working-tree (recorded 9,690 included .git); journal-archive frozen since
   2026-06-08 with zero recorded reads; only 8 non-claim doc deletions in repo history, none
   retention-motivated, none causing a recorded incident.
4. **Groomed** `orientation-doc-linecap-guard` idea → routed into the plan's checker (PR 1 gauge
   class). **Fixed on sight:** stale claim file `claude-funny-franklin-lkqjh9.md` (branch merged;
   `check_stale_claims` red) — the system's one deletion loop working as designed.

## Context delta

- **The measured shape of the problem:** the boot surface is 26,249 words unconditional; the
  discovery surface is where terminal mass taxes sessions (69.6% of grep file-hits). Both soft
  ratchets sit exactly at their caps. Growth is mandated (Q-0089/Q-0102/log) with no mandated
  shrink — linear by construction.
- **Reference topology decides retention:** plans are cited (96% — mostly by prunable ledger
  tails: deletability cascades top-down); session logs aren't (5.3%, all provenance anchors);
  the router's afterlife is real but invisible to citation analysis (Q-0035 invoked 13 days
  post-decision despite zero doc citations) → archive-with-stub stays right for the router.
- **The 2026-06-30 audit (94% of apparent dead weight unsafe to delete) refutes naive deletion
  and specifies the gates**: its refutation classes (broken inbound links, sole-source facts) are
  exactly what the reference gate + harvest step make impossible.
- **Enforcement history:** advisory budgets don't hold (AGENT_ORIENTATION 2× its own cap; Q-0210
  archive 3+ passes overdue); checker+actuator pairs do (recently-shipped trim, stale-claims).
  Hence: every cap ships with its actuator, and destruction is harvest-gated (marker), not
  age-gated — a skipped recon pass stops deletion instead of racing it.

## 🛠 Friction → guard

No new guard needed this session: the one CI friction (stale-claim red on an unrelated PR) was
the existing `check_stale_claims` guard functioning as designed — caught a missed deletion,
any passing session performs it. The plan itself is this session's guard-work: it converts the
observed drift class (unbounded terminal accretion) into checker+actuator enforcement.

## 💡 Session idea (Q-0089)

[`docs/ideas/context-cost-telemetry-2026-07-02.md`](../docs/ideas/context-cost-telemetry-2026-07-02.md)
— parse session transcripts to measure *real* per-session docs-words-read (boot tax, grep-hit
class split), replacing the retention sim's assumption-grade constants and supplying the
rebuild's §5.2 footprint KPI. Dedup-checked (only transcript idea existing is secret-plumbing).

## ⟲ Previous-session review (Q-0102)

Previous: `2026-07-02-admin-logging-guilds-and-webhook.md` (#1644). Genuinely strong — reading
live Railway state before acting found the surviving notification rule and turned "recreate"
into "repoint" (cheaper, no duplicate rule), and its lessons were routed to durable homes
(idea file + checker line), not just narrated. Its improvement suggestion (live-state reads in
idea captures) is already the right instinct. What this session adds to that pattern: that log
is also a perfect retention specimen — its durable content lives in routed homes, its ⚑ owner
lines live *only* in the log; under the new policy the harvest step would carry those ⚑ lines
into the band's pass record before the log is ever prunable. **System improvement initiated:**
the run-report footer structure (⚑/💡/📊) turns out to be what makes harvesting mechanical —
worth keeping strict.

## 📋 Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_current_state_ledger.py --strict` exit 0 (benign newest-merge
lag only) · new docs reachable (plan index + S4 sector + orientation-plan cross-link + ideas
README) · owner decisions this session: none decided by me — the plan routes every owner call
to the ⚑ lines below rather than deciding them.

## 📤 Run report

- **Did:** grounded the retention brainstorm against the repo (5-agent census/evidence workflow +
  inline measurements), built + ran the retention simulator, stress-tested the draft with a
  3-lens adversarial panel, shipped the implementation-ready plan. · **Outcome:** shipped (plan +
  sim; no content pruned yet by design)
- **Shipped:** PR #1643 — plan doc, `tools/sim/retention_policy_sim.py`, plan-index/S4/idea
  routing, session card. 
- **Run type:** `manual` (owner-directed ultracode brainstorm)
- **⚑ Owner decisions — ANSWERED live via question panel, recorded as Q-0214:** (1) session-log
  posture = **delete + tombstones** (boundedness tiebreak confirmed); (2) owner inbox = **website
  `/updates` feed** (export gains a harvest-table source in PR 2); (3) shrink duty = **checker +
  routine**, no per-session ritual (supersedes orientation-plan Workstream D); (4) rebuilt-repo
  ledger depth = **verdict + short why**. Still open for the implementing session: the journal
  deeper-cut (8,349 → ~4,000 words; owner-gated overflow decision) and the 2026-06-30 audit's **7
  confirmed-delete files** go-ahead (owner reviews with PR 2).
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** groomed `orientation-doc-linecap-guard` into the plan; stale-claim
  fix-on-sight; the `context-cost-telemetry` idea file. (All docs-lane, reversible.)
- **↪ Next:** hand the plan to an implementation session (PR 1 → 2 → 3); orientation plan B0–B3
  remains independently overdue and compounds this plan's win.

## 📊 Telemetry

- Pointed to but didn't need: nothing notable — the task-specific route (orientation plan →
  fresh-rebuild §5.2 → sim-driven-design doc) was exactly right.
- Needed but not pointed to: the *live* consumers of `.sessions/` (Hermes dispatch-skill grep,
  dashboard export, router backtick `Home:` citations) — discovered only by adversarial sweep;
  nothing in the orientation route names the machine consumers of memory files. The plan's
  reference-pass + consumer inventory fixes this class.
