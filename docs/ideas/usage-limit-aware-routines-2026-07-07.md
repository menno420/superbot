# Usage-limit-aware routines and orchestrations

> **Status:** `ideas` — session idea (2026-07-07, Q-0089, kit-lab founding-plan session PR #1804).
> **Subsystem:** agent workflow / routine fleet (S5) · kit-lab loop (the founding plan §6).
> **PROMOTED → plan (2026-07-08, grooming wave-1 lane C, PR #1845):**
> [`../planning/usage-limit-aware-routines-plan-2026-07-08.md`](../planning/usage-limit-aware-routines-plan-2026-07-08.md)
> — 2-PR structure (conventions PR · counter PR), ungated. This capture stays for provenance;
> the plan is the buildable spec.

## The observed failure

This session's 4-agent adversarial-review workflow died mid-flight when the account hit the
5-hour usage limit: all four lanes returned the opaque error `You've hit your session limit ·
resets 5:40pm (UTC)` and the workflow completed "successfully" with an **empty result set**.
Nothing distinguishes "limit-exhausted, retry after HH:MM" from a real agent failure unless the
coordinator parses the error string; a scheduled routine (dispatch, docs-reconciliation, the
future kit-lab loop) firing into an exhausted window would burn its run the same way — the
owner just sees a silent no-op or an abandoned partial run.

## The idea

1. **Routine-prompt clause** (cheap, dispatch + reconciliation + lab-loop prompts): "if your
   work dies with a usage-limit error, do not error out or write a failure report — schedule a
   self check-in (`send_later`) at the stated reset time + 2 min, note `limit-deferred` on the
   run report, and resume there."
2. **Orchestration-side detection** (the workflow pattern): coordinators treat the
   limit-error string as a distinct failure class — re-arm instead of diagnosing, and never
   count limit-killed lanes as evidence lanes ran clean (this session did exactly this by hand;
   the lesson should be mechanical).
3. **Fleet telemetry hook:** a `limit-deferred` counter in the run-report footer feeds the
   Q-0248/Q-0249 dataset — exhausted windows are spend-planning data the ~2-month observation
   window wants.

## Why it's worth having

The whole program is moving to *more* scheduled autonomy (the kit-lab loop, the trading repo's
routines). Limit collisions get more likely as routines multiply, and today each one silently
wastes a firing. One prompt clause + one error-class rule converts them from silent losses into
scheduled retries. Dedup-checked: `executor-chain-trigger-via-workflow-2026-06-15.md` covers
run *caps*, not limit-window *recovery* — distinct concern.
