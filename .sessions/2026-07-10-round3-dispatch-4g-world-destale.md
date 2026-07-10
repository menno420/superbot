# Session — round-3 dispatch, part 4g: world-package de-stale (check-in sweep findings)

> **Status:** `in-progress`
> **Run type:** self check-in sweep (22:42Z wakeup) → fix-on-sight (Q-0166) · same live
> dispatch chat (parts 4/4b/4c/4d/4e/4f merged)
> **Model/time:** fable-5 · 2026-07-10 ~22:4xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1968).

## What is about to happen

The check-in sweep read superbot-games @ HEAD `4493292` + the manager's conformed
mapping (fm PR #46) + the live `projects/` registry, and found part-4f's world brief
stale on arrival: the unified control bus ALREADY exists with manager ORDERs 001
(P0 CI collection-scope fix, 73/121 tests) + 002 (P1 self-arm, pre-Q-0265 hourly) in
it, and the kit is ALREADY v1.7.0 (games PR #22, 20:22Z — the "v1.2.0" I read was
heartbeat drift, exactly as the registry meta warns). De-stale §0/§2 of the world
package; hand the owner the corrected §2 block + the manager ingest relay in chat.
