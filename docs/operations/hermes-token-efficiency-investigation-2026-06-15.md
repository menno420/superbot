# Hermes token-efficiency — investigation + fix plan (tomorrow's focus)

> **Status:** `plan` — owner-prioritized for the next session (2026-06-15, captured fresh from the
> live failure). Investigation-first: confirm the pipeline, then pick a fix. Not yet approved to build.
> Home: the Hermes control plane ([`hermes-control-plane.md`](hermes-control-plane.md)).

## The smoking gun (observed live 2026-06-14/15)

Hermes `/status` after only a handful of small messages:

```
Cumulative API tokens (re-sent each call): 2,207,496
Agent Running: No
```

**2.2M cumulative tokens ≈ 8–9× the stated ~256K working window**, that fast. The label is the tell:
*"re-sent each call."* Hermes runs as **one long-lived, accumulating gateway session** — every turn
re-injects the full system prompt (`soul.md`) **+ the entire conversation history + every prior tool
output**. So per-turn **input** grows ~linearly and the cumulative grows ~**O(N²)**.

## Root cause (hypothesis — one cause, all the symptoms)

By the 3rd–4th tool call, the repo state Hermes read early (the plan, the folio, what it had already
verified) is **pushed out of the effective working window**, and it falls back to pattern-matching the
**always-present injected system prompt** instead of the repo facts it read ten tool calls ago.

Every symptom Hermes self-diagnosed is **downstream of that one cause**:
- *Invented scope instead of reading the repo* — dispatched "Phase 2 mining" without opening
  `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md` (the canonical plan, on `main`).
- *Didn't use the subsystem folio* (`docs/subsystems/games.md`).
- *Fired twice without re-grounding* — re-fired vague instead of stopping to read.
- *Context collapse by the 3rd–4th tool call* — lost the thread, repeated/reinvented.

Concrete result tonight: Hermes opened a docs-only re-declaration (**#888**, closed as churn) that
re-stated the existing plan, put it in the wrong dir, and targeted the **owner-blocked** V-16 slice.

## Investigate first (answer before changing anything)

Consolidates the owner's + Hermes's own questions:
1. **Where does per-turn context come from?** Is `soul.md` injected *whole* every turn, **on top of**
   the accumulated history — or is something else bounding what stays loaded?
2. **Working cutoff vs. the counter.** The 2.2M is *cumulative re-sent*, not the live window — what is
   the *actual* working-context cutoff per call, and at which turn does the early repo-read fall out?
3. **Session memory vs. working context.** Is there a difference between `.sessions/` logs (durable
   memory) and what actually stays in the model's working context across tool calls? (Yes in
   principle — confirm it in Hermes's pipeline.)
4. **Can history be capped/summarized/flushed?** Is there a seam to cap or summarize history before
   re-injection, or to **flush context between bounded tasks**?

Where to look (VPS-side, owner has access): the Hermes gateway code that builds each API call's
`messages` array; `soul.md`; [`hermes-control-plane.md`](hermes-control-plane.md) ·
[`hermes-dispatch-bridge.md`](hermes-dispatch-bridge.md) ·
[`hermes-operating-prompt.md`](hermes-operating-prompt.md) · the `hermes-skills/`.

## Candidate fixes (levers, cheapest-impact first)

1. **Stateless, bounded dispatch (the big one).** Each Hermes work order should run in a **fresh
   context** — *read the work order → open the canonical plan/folio → execute → end* — **not** appended
   to a growing session. This is the §10 bounded-session protocol (already used for Claude sessions)
   applied to Hermes; it kills the O(N²) growth at the root and forces re-grounding by construction.
2. **History cap / sliding window / running summary** before re-injection — keep the last *K* turns +
   a compact summary, never the full transcript.
3. **`soul.md` injection strategy** — inject once / cache it (prompt-cache), or trim it; stop re-sending
   the whole thing every turn on top of growing history.
4. **Force re-grounding at dispatch start** — the dispatch skill's **step 1** must *open* the canonical
   plan (`docs/planning/…`) + folio (`docs/subsystems/…`), never act from the injected prompt's memory.
   (A prompt fix, but only *durable* once the context actually retains the read — i.e. after #1/#2.)
5. **Explicit flush between tasks** — reset context between bounded work orders.

## Success criteria

- **Per-dispatch input tokens roughly constant (O(1))** regardless of how many turns/tool calls a
  dispatch takes — not growing toward the window.
- A dispatch **reliably reads the canonical plan/folio and acts on repo state**, not the injected prompt.

## Note — the in-repo Claude sessions don't hit this (and why)

These Claude Code sessions re-send history each call too (it's how the harness works), **but** the
harness **summarizes/manages** the context window, and each session **re-orients from disk** every
resume (`git fetch` + read `current-state` / the plan / the folio). The fix for Hermes is to give it the
*same* discipline: **bounded, re-grounding dispatches** instead of one ever-growing session. That is the
deeper reason #1 above is the right primary lever.
