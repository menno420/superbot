# Idea — plan the decade queue *lead* from the prior band's dominant thread, not from the static priority list

> **Status:** `ideas` — captured by the band-#900 Q-0107 reconciliation pass (2026-06-15) as its
> Q-0089 forward idea. One-line why: **four consecutive bands had their headline work happen in the
> "buffer / steered" slot — the queue keeps mis-planning where the real work goes.**

## The observation (from four scorecards)

Bands #820 → #840 → #870 → #900 all ended the same way: the planned top slots (P1-1 full matrix,
substrate-kit, security tiers) carried, and **slot 10 — "buffer / steered"** — became the band's
actual headline:

- #820/#840 band: Railway agent-access arc
- #870 band: Hermes control-plane / autonomous-loop operationalization arc
- #900 band: mining structures product burst (#884/#891/#897) + routine-consolidation/sector-dispatch arc

Each pass wrote a plausible priority-ordered queue, then reality routed most of the effort into the
buffer. The plan wasn't *wrong* about value — it was wrong about **where the next band's energy
would actually go**, because it derived the queue from the standing priority list (P0→P1→safety…)
rather than from the **momentum signal** the previous one or two scorecards already contain.

## The idea

When building a decade queue, **read the previous 1–2 band scorecards first and lead the new queue
with the thread that actually consumed those bands' buffers** — as a *named, top-tier* slot (slot 2
or 3), not as "buffer / steered" at slot 10. The buffer slot then becomes genuinely residual
("anything not the active thread"), and the queue stops systematically under-counting the work that
predictably dominates.

Concretely, the planning step gains one rule:

> **Lead-with-momentum:** before ordering the queue, identify the thread that filled the buffer in
> the prior band(s). If the same thread filled the buffer **≥2 bands running**, promote it to a
> named top-tier slot in the new queue (it is not buffer — it is the band's likely spine). Only then
> append the standing-priority slots beneath it.

This is the complement to two existing ideas — it doesn't *detect* carries
([`reconciliation-slot-carry-tracker`](reconciliation-slot-carry-tracker-2026-06-14.md)) or
*demote* an owner-blocked slot (the band-#900 §6 rule); it **promotes** the recurring buffer thread
so the queue's *lead* reflects reality. The band-#900 pass already did a manual version of this
(mining structures → slot 2; Railway log-triage → reserved slot 4) — this idea is to make that the
*standing planning step*, not a one-off judgment call.

## Why it's worth having

A decade queue whose top slots never execute looks like a plan that doesn't work, even when the
system ships plenty (the band-#870 §6 worry). Leading with the actual momentum thread makes the
queue **predictive instead of aspirational** — the next autonomous session picks slot 2 and it's
the work that was always going to happen anyway, so the plan and reality converge.

## Size / route

Small, docs/process-only. It is a one-paragraph addition to the reconciliation routine prompt's
planning step + a note in the next pass doc's §4 preamble. No code. Promote it into the routine
prompt at the next reconciliation pass if a fifth band repeats the buffer-becomes-band pattern.
