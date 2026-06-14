# Session: map the roadmaps/plans onto the 5 planning sectors (dispatch targets)

> **Status:** `in-progress`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** owner-directed workflow substrate (docs-only)

## What this session is about to do (HOLD — born-red card, Q-0133)
Continue the 5-sector work. The **top layer** (`docs/repo-sector-map.md`, #859) already names the
sectors; this session makes them **live, dispatchable queues** by organising the roadmap under them.

Goal (owner, this session): make each sector a clean **dispatch target** so Hermes can run simple
dispatches — "send a worker to sector S2 to continue the BTD6 plan execution" / "one worker to plan
the AI-Memory sector, another an hour later to execute it." A worker names a sector + an action and
reads that sector's live queue to know what to do. (Hermes/routine *wiring* = Q-0137 Thread 1, still
owner-undecided — structured *for* it here, **not built**.)

### Planned (docs-only — no `disbot/`)
1. **Restructure `docs/roadmap.md` by sector** — S1–S5 top level; the 9 existing areas nest under
   their sector (most → S1; BTD6 → S2; the agent-ecosystem area splits across S3/S4/S5). Add a
   per-sector at-a-glance (Now/Next) — the dispatch-facing summary. **Row text preserved; only the
   grouping changes** (pure reorganisation + populating S4/S5 from existing items).
2. **Populate S4 + S5** (the under-planned sectors) from work already filed under "agent ecosystem"
   so every sector has a non-empty Now/Next (Q-0137 deep-clean terminal condition).
3. **Dispatch surface per sector** in `repo-sector-map.md` — id · what *plan* / *execute·continue*
   mean · live-queue pointer. Lean; points at Q-0137 Thread 1 for the Hermes wiring.
4. **Reconcile taxonomies** — S1–S5 (planning) ⇄ A1–A5 (review) cross-pointers in `roadmap.md` and
   `repo-review-map.md`.
5. Close-out: re-point `current-state.md` ▶, re-badge the handoff brief done, session enders + audit.

### ⚠️ Parallel-session note (a bot session is running concurrently)
This PR is **docs-only** — zero `disbot/`, tests, migrations, or runtime. Watch-items for the bot
session when it merges:
- **`docs/roadmap.md`** — I restructure the *whole* file by sector. Row **content is preserved**; if
  the bot session edits a horizon row, UNION-resolve by re-placing its edited row under the matching
  sector header (S1 for all bot areas, S2 for BTD6). Cleanest: land this docs-only PR first (fast CI)
  and rebase the bot PR onto it.
- **`docs/current-state.md`** — I touch only the ▶ Next-action pointer + `Last updated` stamp. Keep
  the bot lane's own bullet + Recently-shipped; UNION-resolve.
- **`docs/owner/active-work.md`** — both append a claim; UNION.
- No collision on any bot code.
