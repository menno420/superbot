# Session — Hermes model/provider record (capture the live findings)

> **Status:** `complete`

## What I did

Continuation of the long Hermes investigation (#913/#914/#915 merged + applied live). The single
biggest driver of Hermes' behaviour — its model/provider — was documented nowhere in the repo, and a
pile of verified facts from this session lived only in chat. Captured them in the ops docs.

## What shipped (docs-only)

- `hermes-control-plane.md` — new **"Model / provider"** subsection: the free default is Nous
  Research's own inference endpoint (`stepfun/step-3.7-flash:free` via `inference-api.nousresearch.com`,
  verified from `hermes config`); 2026-06-15 switched to `openai/gpt-5.4-mini` on the owner's own
  OpenAI key (`/model` confirms `Provider: openai-api`; **live-reply verification still pending**); the
  own-key switch commands; the **stale `/model` picker** gotcha (offers only `gpt-4o-mini` — a
  downgrade, not what runs); and the independence-vs-reliability rationale (Q-0117).
- `hermes-terminal-cheatsheet.md` — added the switch-model / own-key commands + the stale-picker note.
- `hermes-token-efficiency-investigation-2026-06-15.md` — "Live outcome" note: the lever was model
  *capability*, not window.
- **Verified:** `check_docs --strict` ✓. The model facts (free default, provider switch, picker
  gotcha, own-key mechanism) are all verified from the owner's terminal/Telegram output; only
  gpt-5.4-mini's end-to-end *reply* is pending (marked as such in the doc).

## Handoff / next

- **Owner:** send Hermes a real task to confirm gpt-5.4-mini actually answers (the `/status` showed
  `Agent Running: No`). If it errors, fall back to `gpt-4o-mini` (picker), `gpt-5.5`, or a Claude key
  — all one command (cheatsheet). Then this record's "pending" line can be ticked.
- Don't tap `gpt-4o-mini` in the `/model` picker expecting an upgrade — it's stale.

## 💡 Session idea (Q-0089)

**Per-role model for Hermes.** Hermes plays several roles (orient / dispatch / **review**). The cheap
`gpt-5.4-mini` is fine for orient/dispatch, but the **review-merge gate** (Q-0117) is the role that
most needs to be sharp — it's the independent check on Claude's big steps. Hermes' cron supports
per-job `model` overrides, so the review skill could pin a stronger model (gpt-5.5, or a different
mind) while the default stays cheap. Best independence × reliability per €. Dedup-checked
`docs/ideas/` — none.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-15-hermes-sync-hardening.md` (#915). It responsively hardened the sync right after
the diverged-clone bit the owner live — good reflexes. **System improvement this run surfaced:** the
#1 driver of Hermes' behaviour (its *model*) was invisible to every repo-side doc and `check_*` until
the owner happened to mention it mid-session — the Control-plane state table tracks secrets/deploys
but never "what model is Hermes on." This PR homes it in the control-plane doc; a future pass could
add a "model" row to that table so it can't silently drift.

## 📋 Doc audit (Q-0104)

`check_docs --strict` green; all three edited docs reachable. The model decision (chat-only until now
— exactly the Q-0104 drift class) is now durably homed in `hermes-control-plane.md` + cheatsheet +
investigation pointer. No new owner Q-block: the model choice is a reversible ops config in its proper
home (the control-plane record), not a binding policy. The one open item is a **runtime** check
(gpt-5.4-mini live reply), flagged in the doc — not a docs gap. Ledger unaffected (docs-only).
