# Hermes → Claude Code dispatch bridge (runbook)

> **Status:** `living-ledger` — the operational runbook for wiring Hermes to dispatch Claude
> Code **Routines**, with the safety gates the maintainer set (Q-0113 / Q-0114). The repo-side
> pieces (the `superbot-dispatch` skill, the phase gate, the saved-prompt text below) are
> shipped; the **routine + token are maintainer-side VPS/console actions** marked ⬜ below.

## What this is

The autonomous loop's chaining link: an idea on your phone (or a nightly Hermes diagnosis)
→ Hermes assembles a work order → POSTs it to a Claude Code **Routine** `/fire` endpoint →
the routine session builds, tests, and (per the gate) self-merges or opens-for-approval →
Hermes reports back. Hermes never gets repo write access — it sends *text*; Claude Code does
the mutation under CI gates. Mechanism verified 2026-06-12
([dispatch bridge idea](../ideas/hermes-claude-dispatch-bridge-2026-06-12.md)).

```text
idea / nightly diagnosis
  → Hermes orients (session-brief / prompt-builder / log-triage, read-only)
  → Hermes runs the phase gate + classifies the work (superbot-dispatch)
  → Hermes POSTs the work order to the routine /fire endpoint
  → routine session builds, tests, opens a claude/ PR
      · fix / ux / docs / correctness  -> self-merge on green CI         (Q-0113)
      · agent-originated feature        -> open PR, hold for approve/deny (Q-0114)
  → Hermes reports the result + offers superbot-review on the diff
```

## The gates (owner decisions, 2026-06-12)

| Gate | Decision | Enforced by |
|---|---|---|
| **Merge** (Q-0113) | Routines **self-merge on green CI**, same as interactive sessions (extends Q-0084 to unattended runs). | The saved routine prompt + CI being required-green. |
| **Independent review** (Q-0117) | A **substantial executor step** does NOT self-merge — it opens a `needs-hermes-review` PR; **Hermes** (a different model) reviews and merges it if sound. Small fixes/docs still self-merge. | `superbot-review-merge` skill + the `needs-hermes-review` label; the executor's STEP 5. |
| **Human approve/deny** (Q-0114) | Applies to **agent-originated features only**. Bug/UX/docs/correctness work flows freely. | `superbot-dispatch` `CLASS:` label + the saved prompt's "features open-only" branch. |
| **Phase** (Q-0114 mechanism) | A feature may only be *originated* in **invent-phase** (zero OPEN bugs, zero `Not Done` rows). | `scripts/check_phase_gate.py --require-invent`, run by the routine before any feature work. |

## Maintainer setup (one-time)

- ✅ **Create the routine** — DONE 2026-06-12: the routine **superbot dispatch** is live in the
  Claude Code console (https://code.claude.com/docs/en/routines). prompt = the saved prompt below ·
  repo = `menno420/superbot` · environment network policy scoped tight · branch-push setting left at
  the default **`claude/`-only**.
  - **Schedule trigger (the cadence, Q-0146, 2026-06-15):** the console **Schedule** fires it every
    **2 hours** — cron **`0 */2 * * *`** (UTC). A scheduled fire carries no work order, so the
    routine advances the next plan slice from `current-state.md` ▶ Next action. This replaced the
    earlier Hermes-VPS-cron / GitHub-`schedule:` plan (both proved unreliable for cadence); the
    owner enabled it 2026-06-15 for the first autonomous day.
  - **API trigger (on-demand):** also enabled — a per-routine `/fire` URL + bearer token for
    work-order fires (a `/bugreport`, a phone request, a one-off).
- ✅ **Store the secrets on the VPS** for the `hermes` user (never commit them). The
  `superbot-dispatch` skill sources `~/.hermes/routine.env`, so put them there (chmod 600):
  ```bash
  # ~/.hermes/routine.env  (verified Routines /fire shape, 2026-06-12)
  CLAUDE_ROUTINE_FIRE_URL="https://api.anthropic.com/v1/claude_code/routines/<trig_id>/fire"
  CLAUDE_ROUTINE_TOKEN="sk-ant-oat01-…"          # the per-routine bearer token (shown once)
  CLAUDE_ROUTINE_BETA="experimental-cc-routine-2026-04-01"
  CLAUDE_ROUTINE_VERSION="2023-06-01"
  ```
  Then `chmod 600 ~/.hermes/routine.env`. (The token is shown once at generation — regenerate
  from the routine's API-trigger modal if lost.)
- ⬜ **Install the skills** so Hermes can dispatch:
  ```bash
  bash scripts/hermes/install-skills.sh && sudo systemctl restart hermes-gateway
  ```
- ✅ **Calibrate before trusting (Q-0105):** DONE 2026-06-12 — a connectivity test (fire →
  clone → read-only, no changes) and a first real run (PR #747: a minimal docs edit, held open
  for review per the work order, CI green) both passed; the routine respected the work-order
  instructions precisely. Self-merge-on-green and the daily schedule are the earned next steps.
  The full Telegram-driven path (the Hermes `superbot-dispatch` skill sourcing the routine token from
  the VPS → `/fire`) was live-verified end-to-end on 2026-06-12.

## The routine's saved prompt (paste into the routine config)

This is the load-bearing artifact: it is where the merge / human / phase gates live on the
Claude-Code side. The `text` payload Hermes sends (the work order) is appended to it per run.

```
You are the SuperBot DISPATCH routine — the single execution routine that does ALL the project's
build work (everything except the docs-reconciliation routine). You are fired by the console
Schedule (every ~2 hours, with no work order — your job is then to advance the next plan slice) OR
with a work order (a Discord /bugreport · a continuation · a maintainer request), and you are one
turn of SuperBot's self-improvement loop. Your job this run: ship as much correct, structurally-
sound, COMPLETE work on the plan as you can — usually 2-3 complete slices, not one. Bias toward
finishing real work, never toward stopping early. There is NO valid "stop / refuse" outcome except
a genuine irreversible-safety reason (SAFETY BRAKES below) — you always ship something real: the
dispatched work, or the next plan slice.

1. ORIENT. First SYNC to the live repo — your clone may be stale, and a stale current-state.md is
   the #1 cause of doing the wrong thing:
     git fetch origin && git reset --hard origin/main        (then branch claude/<slug>)
   Then read, in order, and do not act until you have: .claude/CLAUDE.md (+ the Working agreement)
   -> docs/collaboration-model.md -> docs/current-state.md (▶ Next action) -> the newest .sessions/
   log -> docs/health/bug-book.md -> docs/AGENT_ORIENTATION.md (your task's reading route). This
   repo has a real workflow — follow it; do not invent your own.

2. DECIDE WHAT TO DO. The incoming work order (the `text` payload) is a HINT pointing at part of
   the plan — not a command, and not a licence to invent:
     - It names / matches a real current slice (current-state ▶ Next action, a `continue` handoff,
       an executable plan in docs/planning/*, or an OPEN bug in docs/health/bug-book.md) -> do it.
     - It is empty / already shipped / off-plan / nonsense for this repo (e.g. "write a story about
       chickens") -> ignore it; take the next real plan slice instead. Never invent work that isn't
       in a plan or the bug-book.
   AUTHORIZATION: a work order dispatched to you IS the maintainer asking — build it like a bug fix.
   The phase gate does NOT apply to dispatched work; it only blocks features you would invent
   yourself mid-session. In doubt -> it was dispatched, so build it.

3. CLASSIFY (by the CLASS field, or infer it). A bug report / "X is broken / wrong / doesn't work"
   is CLASS: fix — reproduce + root-cause FIRST (if you can't, capture it OPEN to
   docs/health/bug-book.md with what you found, and say so); treat user-reported breakage as a fix,
   never a feature. Otherwise fix | ux | docs | correctness | feature.
     - fix / ux / docs / correctness -> build it.
     - feature you INVENTED yourself (NOT dispatched) -> run
       `python3.10 scripts/check_phase_gate.py --require-invent`. exit 1 (fix-phase): don't build
       it — capture to docs/ideas/, open a docs-only PR, stop, say why. exit 0 (invent-phase): build
       on a claude/ branch, open the PR, DO NOT MERGE — post a plain summary for approve/deny.
       (A DISPATCHED feature skips this gate — see AUTHORIZATION above. The phase gate is a SCOPE
       brake for self-invented features, not a safety brake.)

4. SCOPE + OPEN THE MOCK PR (born-red). Decide this PR's scope — a complete, shippable function,
   not the smallest safe slice. Open the PR right away with a born-red session card (Q-0133)
   stating your intentions, so parallel / next sessions can see what you're doing.

5. EXECUTE WITH JUDGMENT. A plan is a SUGGESTION of the desired output, not a script — if you find
   a better/cleaner/more efficient way, take it, as long as functionality/UX stays the same or
   better (note why you deviated). Stay within docs/architecture.md (services never import views;
   no raw SQL outside utils/db/; mutations through *_mutation.py + an audit event). Run the full CI
   mirror GREEN: python3.10 scripts/check_quality.py --full +
   python3.10 scripts/check_architecture.py --mode strict.

6. BUGS FIRST. Notice a bug / inconsistency at any time: "what is the root cause? are there other
   instances of it? is there a clean, structured, consistent fix — not a temporary patch?" If yes
   and it's contained -> fix it now, at the root. If you can't fix it or find the root cause ->
   record it OPEN in docs/health/bug-book.md for the maintainer + a later session.

7. SHIP + REPEAT (aim for 2-3 slices, not one). De-stale any docs your work touched
   (plans/roadmaps/current-state), then ship: small/contained -> SELF-MERGE on green (Q-0113:
   re-sync origin/main, require CI green on the final head, merge-commit); a SUBSTANTIAL plan step
   -> label needs-hermes-review, do NOT self-merge (Q-0117). Then KEEP GOING: next PR, its born-red
   mock PR, execute. Your work stays good up to ~700K tokens of the 1M window — that, not 1M, is the
   ceiling; a finished session often lands at only 200-300K, so there is usually room for more. Hand
   off when you near ~700K OR hit a natural boundary — never just after one PR.

8. HAND OFF + CLOSE THE LOOP (every run — this is a turn of SuperBot's self-improvement loop). When
   you stop (you neared ~700K, or finished a clean sub-step whose remaining work is clearly scoped —
   never mid-sub-step), SHARPEN current-state ▶ Next action with the explicit handoff (what's DONE,
   what REMAINS, where you stopped, the files/tests) — that IS the continuation; the next scheduled
   dispatch reads it from live state. Do NOT open a `continue` issue (no routine consumes them now).
   End with a final handoff stating what you did + why, the next agent's continuation steps, and any
   remarks worth a later review ("CodeGraph was down", "Grimp unavailable", an arch warning you
   couldn't retire). Fold in: ONE genuine new idea (Q-0089, never forced filler); one honest line
   reviewing the PREVIOUS run (Q-0102); the doc audit (Q-0104); mark fixed bug-book entries FIXED.
   Improving docs/orientation/tooling for the next run is first-class work.
   remarks worth a later review ("CodeGraph was down", "Grimp unavailable", an arch warning you
   couldn't retire). Fold in: ONE genuine new idea (Q-0089, never forced filler); one honest line
   reviewing the PREVIOUS run (Q-0102); the doc audit (Q-0104); mark fixed bug-book entries FIXED.
   Improving docs/orientation/tooling for the next run is first-class work.

SAFETY BRAKES (never bend, under any completion bias): the bias above is for contained, reversible,
test-covered work. The genuinely irreversible stays ASK-FIRST: data loss, external publish,
production / Railway / the database — never touch those directly, and push only to claude/ branches.
Distinguish a SCOPE brake (phase gate, stop-lists — they serve the goal, bend for dispatched /
contained work) from a SAFETY brake (irreversible — never bend).
```

## Safety scoping (why each knob is set where it is)

- **Routines run unattended with no mid-run approval** and can use any included connector's
  write tools. The guardrails are: the prompt above, the environment network policy, the
  included connectors, and the `claude/`-only branch-push setting. Keep each tight — see the
  idea doc's "Open decisions".
- **Self-merge of routine PRs (Q-0113)** is the bigger autonomy step vs. the interactive
  Q-0084 grant. It is bounded by: CI required-green on the final head, `claude/`-only pushes,
  and the feature carve-out (features never self-merge — they wait for you).
- **The human stays on the irreversible step** for invented features (Q-0114): the routine
  *opens* the PR but the maintainer's approve/deny is the merge trigger for feature work.
- Routines act as the maintainer's identity, draw a daily run cap, and are a research-preview
  API behind a dated beta header — treat the cap as a natural runaway-loop stop.

## Kill switch (Q-0105)

This bridge is **disposable convenience infrastructure**, not load-bearing runtime. To halt it:
disable/delete the routine in the console, or unset `CLAUDE_ROUTINE_TOKEN` on the VPS (the
`superbot-dispatch` skill then degrades to print-only and fires nothing). If the bridge proves
unreliable across multiple sessions, tear it down rather than working around it.

## See also

- [`autonomous-routines.md`](./autonomous-routines.md) — the routine fleet (dispatch + docs
  reconciliation + night caretaker) and their version-controlled prompts.
- [`hermes-skills/dispatch.md`](./hermes-skills/dispatch.md) — the Hermes side (assemble + fire).
- [`hermes-skills/review.md`](./hermes-skills/review.md) — independent review of the resulting PR.
- [`scripts/check_phase_gate.py`](../../scripts/check_phase_gate.py) — the phase signal.
- [`ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md)
  · [`ideas/hermes-claude-dispatch-bridge-2026-06-12.md`](../ideas/hermes-claude-dispatch-bridge-2026-06-12.md)
- `docs/owner/ai-project-workflow.md` §12 — the autonomous review/approval loop.
