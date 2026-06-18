# Idea — a "⚑ Product lanes gated" balance flag (companion to PLAN-BACKLOG-THIN)

> **Status:** `ideas`. **Not a plan, not approval.** Capture from the band-#1050 Q-0107
> reconciliation pass (2026-06-18, issue #1051). Source + binding contracts win.

**Session idea (2026-06-18, Q-0089, from the band-#1050 reconciliation pass).**

**The observation.** For ~6 consecutive bands the *planned product slots* (S1 bot / S2 BTD6) have
been mostly gated (owner / creds / `needs-hermes-review` / data) and the *buffer* (S3/S4/S5
workflow + tooling) has become the band. The band-#1050 pass §3 named this as a **standing
structural condition**, not band noise, and gave the owner the lever (merge a `needs-hermes-review`
PR, decide a Q-0175 fishing question, or greenlight a dashboard write surface).

**The gap.** The Q-0164 `⚠️ PLAN BACKLOG THIN` flag measures **raw depth** (is there *enough*
buildable work?). It says nothing about **balance** (is the buildable work all on one side?). So a
band can be "deep and healthy" by the THIN check while every *product* lane is gated — the exact
state we're in — and the only thing that surfaces it is a human writing a §3 paragraph by hand each
pass. That makes the owner-side lever easy to miss between passes.

**The idea.** A tiny stdlib reporter — `scripts/check_lane_balance.py` (Q-0105 disposable tooling) —
that reads the live ▶ Next-action queue / the latest band pass doc, classifies each buildable slice
by sector (product = S1/S2 vs. workflow/tooling = S3/S4/S5), and emits a **warn-only**
`⚑ Product lanes gated (N bands)` line when **zero** S1/S2 slots are ungated. Surfaced on the
run-report footer (next to the THIN flag) and optionally in `current-state.md ▶ Next action`, so the
owner sees "the next band ships tooling, not features — unblock one of these to rebalance" *every*
pass, automatically, instead of relying on a human noticing. Pairs naturally with the proposed
`check_plan_backlog.py` (the THIN automation) — same input, complementary axis.

**Why it's worth having.** It makes the band-#1050 §6 improvement *self-firing*: the
product-vs-tooling balance becomes a measured signal, not a per-pass judgment call, and the owner
learns *early and consistently* that the lever is in their hands. It is the balance-axis sibling of
the depth-axis THIN flag.

→ relates `scripts/check_reconciliation_due.py` · the Q-0164 THIN flag · the
[agent-tooling-automation-shortlist](agent-tooling-automation-shortlist-2026-06-17.md)
(`check_plan_backlog.py`) · `docs/roadmap.md` sector queues.
