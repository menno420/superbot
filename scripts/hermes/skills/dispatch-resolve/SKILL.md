---
name: superbot-dispatch-resolve
description: "Turn a loose \"work on X\" into a **concrete, correctly-scoped work order routed to the right runner** — by resolving the live roadmap into the first startable item + its executor, then either firing the dispatch routine (Claude work), doing it itself (a Hermes read-only op), or handing the owner a manual step. The missing link between \"the dispatch menu exists\" and \"the correct worker fires\"."
version: 1.0.0
author: "SuperBot agents"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Automation, SuperBot, Dispatch]
    related_skills: [superbot-dispatch, superbot-prompt-builder]
---

<!-- GENERATED — DO NOT EDIT. Source of truth: docs/operations/hermes-skills/dispatch-resolve.md. Regenerate with scripts/hermes/build_skills.py. -->

You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot. Read-only here;
the only action is firing the dispatch routine via the superbot-dispatch skill (or handing the owner
a step). GOAL: resolve a vague "work on SX / the bot / lane Y" into a concrete task + the right runner.

1. SYNC: git -C /home/hermes/repos/superbot fetch origin main && \
         git -C /home/hermes/repos/superbot checkout -B main origin/main

2. RESOLVE the sector(s). If the owner named a sector (S1..S5), pass it; else resolve all and pick:
   cd /home/hermes/repos/superbot && python3 scripts/dispatch_menu.py --json [SX]
   Each record is: {sector, name, executor, state, startable_item, source}. The states:
     - startable                → a ▶ item in Now, run by Claude-in-repo
     - now_blocked_fallthrough  → Now had no ▶; the item is from Next (still Claude-in-repo)
     - maintainer_or_hermes     → there is a startable item but the executor is NOT Claude-in-repo
     - starving                 → no ▶ item anywhere in that sector
   (S1..S4 are normally Claude-in-repo; S5 Operations is the executor outlier — often Hermes/maintainer.)

3. ROUTE by the resolved executor/state — do NOT fire a repo-editing agent at a non-Claude task:
   - startable / now_blocked_fallthrough (executor Claude-in-repo):
       Confirm the item against docs/current-state.md ▶ Next action + the sector's plan (the JSON is
       a pointer; live state wins). Then hand off to the superbot-dispatch skill with a work order
       built from `startable_item` (CLASS inferred: fix/ux/docs/correctness/feature). Dispatch fires
       the routine; it builds/tests/PRs under the CI gates.
   - maintainer_or_hermes, executor Hermes-VPS:
       This is a read-only operations task (e.g. log-triage). DO IT YOURSELF with the matching skill;
       do not fire a Claude routine.
   - maintainer_or_hermes, executor maintainer (👤):
       Reply to the owner with the concrete manual step. Do not fire any agent.
   - starving:
       No startable item — tell the owner the sector is blocked/empty and suggest a planning pass
       (a `reconcile` issue or a plan-first slice), rather than inventing work. Never fabricate a task.

4. REPORT: the sector, the resolved item, the executor, and what you DID (fired #PR via dispatch /
   did it myself / handed the owner a step / flagged starving). One verdict line.

RULES:
- The roadmap JSON is a HINT; verify against live current-state before firing (Q-0142: pick by
  description, not a stale PR number). When the menu and live state disagree, live state wins.
- A dispatched work order is the owner asking → the routine builds it (the phase gate is only for
  features the routine would INVENT itself). But only resolve+fire off an OWNER directive — never
  off your own initiative.
- Never push code yourself; dispatch does the mutation under CI. Keep the safety split intact.
