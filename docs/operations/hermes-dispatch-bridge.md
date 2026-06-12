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

## The three gates (owner decisions, 2026-06-12)

| Gate | Decision | Enforced by |
|---|---|---|
| **Merge** (Q-0113) | Routines **self-merge on green CI**, same as interactive sessions (extends Q-0084 to unattended runs). | The saved routine prompt + CI being required-green. |
| **Human approve/deny** (Q-0114) | Applies to **agent-originated features only**. Bug/UX/docs/correctness work flows freely. | `superbot-dispatch` `CLASS:` label + the saved prompt's "features open-only" branch. |
| **Phase** (Q-0114 mechanism) | A feature may only be *originated* in **invent-phase** (zero OPEN bugs, zero `Not Done` rows). | `scripts/check_phase_gate.py --require-invent`, run by the routine before any feature work. |

## Maintainer setup (one-time)

- ✅ **Create the routine** — DONE 2026-06-12: the routine **superbot autonomous dispatch**
  is live in the Claude Code console (https://code.claude.com/docs/en/routines) with the API
  trigger enabled. prompt = the saved prompt below · repo = `menno420/superbot` · environment
  network policy scoped tight · branch-push setting left at the default **`claude/`-only** ·
  API trigger enabled (you get a per-routine `/fire` URL + bearer token).
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
You are a Claude Code routine continuing the SuperBot project autonomously.

ORIENT FIRST: read .claude/CLAUDE.md, docs/current-state.md, the newest .sessions/ log, and
docs/AGENT_ORIENTATION.md for your task's reading route. The incoming work order (the `text`
payload) is your task. If it is empty, read the standing handoff (current-state ▶ Next action
/ roadmap session queue) and take the recommended next ~2 bounded tasks instead.

CLASSIFY the work order by its CLASS field (fix | ux | docs | correctness | feature):

- fix / ux / docs / correctness  -> build it, write/extend tests, run the full CI mirror
  (python3.10 scripts/check_quality.py --full + scripts/check_architecture.py --mode strict),
  open a PR, and SELF-MERGE on green CI (Q-0084 / Q-0113): re-sync origin/main first,
  UNION-resolve conflicts, require CI green on the final head, merge-commit method.

- feature (agent-originated)  -> FIRST run `python3.10 scripts/check_phase_gate.py --require-invent`.
    · exit 1 (fix-phase): DO NOT build the feature. Capture it as a docs/ideas/ file instead,
      open a docs-only PR with the capture, and stop. Say why (correctness work remains).
    · exit 0 (invent-phase): build it on a claude/ branch, test it, open a PR, and DO NOT
      MERGE. Post a plain-language summary (what it does, what to test, the one risk) for the
      maintainer's approve/deny. Leave the PR open for him.

ALWAYS: stay within docs/architecture.md boundaries (services must not import views; no raw
SQL outside utils/db/; mutations through *_mutation.py with an audit event). Respect the
bounded-session protocol (workflow §10): ~2 substantial tasks max, then hand off. Push only to
claude/ branches. Never touch production, Railway, or the database directly.

CLOSE THE LOOP before you end (this is a turn of SuperBot's self-improvement loop, not just a
task): leave current-state ▶ Next action sharpened so the next run continues cleanly; contribute
ONE genuine new idea (Q-0089) to docs/ideas/ if you have one worth having (never forced filler);
and note one honest line on the PREVIOUS run/session (Q-0102). Trigger a positive improvement
wherever one honestly exists — improving docs/orientation/tooling for the next run is first-class.
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
