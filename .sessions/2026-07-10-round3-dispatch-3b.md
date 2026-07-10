# Session — round-3 dispatch part 3b: Q-0265 continuous mode (live copilot)

> **Status:** `in-progress`
> **Run type:** owner-directed · same chat as part 3 (PR #1955, merged) — fresh card/branch
> per the never-reuse-a-merged-card rule.
> **Model/time:** fable-5 · 2026-07-10 ~21:2xZ →

## What is about to happen

The owner caught both new seats idling between wakes ("I thought you were supposed to
keep working indefinitely, with the routine as a failsafe") — diagnosis confirmed: the
founding packages' inherited "ONE bounded slice per wake / no excessive work" doctrine
did instruct exactly that. Owner ruling: **ALL SIX core seats go continuous** (work loop
slice-after-slice, self-re-arm send_later chain as the continuation trigger, standing
cron demoted to dead-man failsafe, queue-based backpressure replaces the time throttle,
Q-0089 honesty guard retained). Shipping: router **Q-0265** + package rewrites (forge,
simulator — unbooted) + amendment banners (idea-engine, builder, manager/runbook §2 —
live seats get the owner-pasted amendment block) + the paste block in the part-4 brief.
