# Skill: `superbot-dispatch-resolve`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. The read-side resolver for the
> dispatch contract. Update it when the sector map, the executor model, or `dispatch_menu.py`
> change. Provenance: owner-directed 2026-06-16 (greenlit the Hermes-wiring half of the
> `dispatch-resolution-json-hermes` idea, the read-side of Q-0137 Thread 1).

**Window:** the owner says something vague-but-directive — "work on the bot", "do sector S2 next",
"advance the AI lane"
**Purpose:** Turn a loose "work on X" into a **concrete, correctly-scoped work order routed to the
right runner** — by resolving the live roadmap into the first startable item + its executor, then
either firing the dispatch routine (Claude work), doing it itself (a Hermes read-only op), or
handing the owner a manual step. The missing link between "the dispatch menu exists" and "the
correct worker fires".

**When to use:** whenever the directive names a *sector or lane* rather than a specific task. For a
specific, already-scoped task go straight to `superbot-dispatch`; for a spoken idea that needs
shaping first, use `superbot-prompt-builder`.

---

## Prompt

```
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
```

---

## Notes

- **The read-side of Q-0137 Thread 1.** `dispatch_menu.py` (#882) + the Q-0143 contract made the
  sectors dispatch-*ready* (a human can resolve them by reading a table); `--json` + this skill make
  them dispatch-*resolved* (Hermes resolves them and routes to the right runner). The owner greenlit
  the Hermes-wiring half in-session on 2026-06-16; the broader Thread-1 cron-backstop decision stays
  with the owner.
- **Thin resolver (skill-author rule).** It computes the task + runner and then *delegates* — to
  `superbot-dispatch` (fire), an ops atom (do-it-itself), or the owner (manual step). It must not
  re-implement the dispatch `/fire` body.
- **Why route by executor.** The #880 dispatch test showed the real failure mode is firing a
  repo-editing Claude routine at an S5 token/ops task. Routing on the resolved `executor` prevents
  that — the whole reason `--json` carries the executor field.
- **Provenance + reliability (Q-0105).** Added 2026-06-16, owner-directed. UNVERIFIED until it has
  resolved + routed at least one real directive correctly. Delete or revise if it mis-routes.
