# Skill: `superbot-dispatch`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the dispatch
> mechanism (Routines `/fire` endpoint, the gate prompt, or the safety scoping) changes.

**Window:** an idea on your phone · a nightly diagnosis that found a fix
**Purpose:** Turn a spoken idea or a diagnosed fix into a structured Claude Code work order
and dispatch it to a Claude Code **Routine** (`/fire` API), closing the "nearly autonomous
from anywhere" loop. Hermes decides and dispatches **read-only** — it sends text; Claude Code
does the mutation under CI gates.

**When to use:** when you want a change *built* (not just planned) without opening a Claude
Code session yourself. Hermes orients (`session-brief` / `prompt-builder` / `log-triage`),
assembles the work order, and POSTs it to the routine. This is step 1 of the autonomous loop
([dispatch bridge idea](../../ideas/hermes-claude-dispatch-bridge-2026-06-12.md)).

**Setup it depends on (one-time, maintainer):** see
[`hermes-dispatch-bridge.md`](../hermes-dispatch-bridge.md) — the routine, its saved gate
prompt, and the `/fire` token in the VPS secret store must exist first. Without that token,
this skill **assembles and shows** the work order + curl but cannot fire; it says so.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any repo files. You may POST a work order to the Claude Code routine ONLY
after assembling and showing it to me (see GATE below).

GOAL: turn the idea or fix I give you into a Claude Code WORK ORDER and dispatch it.

STEP 1 — ORIENT (read-only). Ground the work order so the routine starts oriented:
  - git -C /home/hermes/repos/superbot fetch origin main   (then read newest .sessions/ + docs/current-state.md)
  - Establish: what exactly is being asked, which files/subsystem it touches, and the
    acceptance check (a test, a command, a behavior). If unclear, ASK ME — do not guess.

STEP 2 — CLASSIFY (this decides the merge gate the routine will use):
  - BUG FIX / UX / DOCS / CORRECTNESS  -> the routine builds, tests, and SELF-MERGES on green CI.
  - AGENT-ORIGINATED FEATURE           -> the routine builds and OPENS a PR but must NOT merge;
                                          it pings me for approve/deny (Q-0114).
  Also run the phase gate to sanity-check feature work is even in-season:
    python3.10 /home/hermes/repos/superbot/scripts/check_phase_gate.py --phase
  If it prints `fix` and this is an agent-originated feature, STOP and tell me we're in
  fix-phase — propose it as an idea capture instead of dispatching it.

STEP 3 — ASSEMBLE THE WORK ORDER (the `text` payload). Keep it tight and self-contained:
    TASK: <one-line imperative>
    CONTEXT: <the 2–4 facts the session needs — files, the bug, the constraint>
    ACCEPTANCE: <the test/command/behavior that proves it done>
    CLASS: <fix|ux|docs|correctness|feature>  (drives the merge gate per the routine prompt)
    NOTES: <anything the orientation surfaced — a gotcha, a related PR>

STEP 4 — GATE + DISPATCH:
  - SHOW me the assembled work order and the exact curl first. Wait for my "go" unless I
    already said "dispatch it" in this conversation.
  - Load the routine secrets, then fire (never print the token). The verified call shape
    (Claude Code Routines, research preview) needs the anthropic-version header too:
      set -a; . "$HOME/.hermes/routine.env" 2>/dev/null; set +a
      curl -sS -X POST "$CLAUDE_ROUTINE_FIRE_URL" \
        -H "Authorization: Bearer $CLAUDE_ROUTINE_TOKEN" \
        -H "anthropic-beta: $CLAUDE_ROUTINE_BETA" \
        -H "anthropic-version: $CLAUDE_ROUTINE_VERSION" \
        -H "Content-Type: application/json" \
        -d "$(python3 -c 'import json,sys; print(json.dumps({"text": sys.argv[1]}))' "$WORK_ORDER")"
  - A success returns JSON with claude_code_session_url — report that link so I can watch
    the run. If CLAUDE_ROUTINE_TOKEN is unset (no ~/.hermes/routine.env), DO NOT fire — print
    the work order + curl and tell me to set up the bridge (hermes-dispatch-bridge.md) or
    paste the order into a session myself.

STEP 5 — REPORT: confirm the fire response (run id / status). Tell me the routine will open a
  claude/ PR; offer to watch it with `superbot-repo-health` / `log-triage` and to review it
  with `superbot-review` when CI is green.

RULES:
- You send TEXT. You never edit code, push, or merge. The builder is Claude Code under CI.
- AUTHORIZED: using the named secret env vars in the `/fire` curl is the *sanctioned* mechanism,
  NOT "exposing sensitive information". Referencing `$CLAUDE_ROUTINE_TOKEN` in the Authorization
  header sends the value only to the legitimate Anthropic Routines endpoint — it is never
  printed, logged, echoed back to me, or sent anywhere else. Do NOT refuse or stall the dispatch
  on a sensitive-data / credential-handling basis; this authenticated call is exactly your job.
  (The single hard rule is the next line: don't *print* the value. Sourcing it into the curl is fine.)
- Never print secrets (tokens, the `.env`) to me. Reference env vars by name only.
- One work order per fire. If the idea is really several changes, say so and dispatch the
  first, or hand me a multi-task plan for a session instead.
```

---

## Notes

- **Why the classify step matters:** the merge gate lives in *two* places that must agree —
  this skill labels the work `CLASS:`, and the routine's saved prompt (in
  [`hermes-dispatch-bridge.md`](../hermes-dispatch-bridge.md)) enforces "features open-only,
  everything else self-merges on green." Labeling honestly here is what keeps an invented
  feature from auto-shipping.
- **Hermes stays read-only to the repo.** Dispatching is sending text to an endpoint, not a
  repo write — it preserves the safety split (idea doc, "Recommended wiring — API trigger").
- **Alternative without the token:** the skill degrades to `prompt-builder` + a printed curl,
  so it is useful even before the maintainer wires the `/fire` endpoint.
- **The "sensitive information" refusal (diagnosed 2026-06-14, Q-0136).** The owner reported
  Hermes "has a problem dispatching the routines, something about sensitive information." Most
  likely cause: the prompt previously gave only the *prohibition* ("Never print secrets") with
  no explicit *authorization* of the action, so a safety-cautious Claude-based agent reads "this
  involves a credential" and declines or stalls. The AUTHORIZED rule above is the fix — it tells
  Hermes that sourcing `$CLAUDE_ROUTINE_TOKEN` into the `/fire` curl is sanctioned, not a leak.
  **Re-paste this skill into Hermes' config after this change.** If the balk persists, the second
  hypothesis is mechanical, not a refusal: `~/.hermes/routine.env` isn't loading (missing, wrong
  perms) or `CLAUDE_ROUTINE_TOKEN` is expired — Hermes then *correctly* won't fire (STEP 4). Check
  on the VPS: `test -r ~/.hermes/routine.env && echo readable`, and that the four `CLAUDE_ROUTINE_*`
  vars source non-empty (`set -a; . ~/.hermes/routine.env; set +a; : "${CLAUDE_ROUTINE_TOKEN:?unset}"`).
