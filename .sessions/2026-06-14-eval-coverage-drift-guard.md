# Session: eval-coverage drift guard (Q-0089 idea → build)

> **Status:** `in-progress`

**Branch:** `claude/wizardly-edison-xw34kb` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** AI hardening / invariant (follow-up to #878)

## What I'm about to do (born-red declaration)
Implement the session idea the owner approved from #878: a **CI eval-coverage drift guard**. A tiny
invariant that fails when a canonical AI tool (`services.ai_tools.all_tool_specs`) or an `AITask`
enters the surface but **no** golden/smoke eval case references it — so the now-versioned eval
matrix can't silently fall behind the surface it's meant to prove ("enforce, don't exhort", the same
principle as the doc-freshness gates).

**Design:** a self-cleaning **ratchet**, not an absolute mandate (only 8/34 tools, 2/16 tasks are
covered today). Partition: `catalogue == referenced ∪ acknowledged`. The acknowledged set is the
explicit, reviewable **pick-list of the current gap**; the guard fails on (a) a new
unreferenced+unacknowledged tool/task, (b) a stale ack whose tool/task no longer exists, and (c) an
ack entry that is now *also* referenced (forces the ledger to shrink as coverage grows).

## Coordination
Bot tests only (`tests/evals/`). No `disbot/` runtime change. Follow-up to the just-merged #878.

_(filled in at session close: shipped / verified / idea / review / doc audit)_
