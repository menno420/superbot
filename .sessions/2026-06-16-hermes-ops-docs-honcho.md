# Session — Hermes ops docs: lean-filter how-to · Honcho eval · open-steps findability

> **Status:** `complete`

Owner-requested follow-ups from the live Hermes setup/calibration session. Docs/ideas only.

## What shipped

1. **Lean-filter technique documented** (`hermes-terminal-cheatsheet.md`, new "Lean a config of empty
   placeholders" section). The owner asked to keep this reusable: the `grep -E '^[A-Z_0-9]+=.+'`
   filter strips blank `NAME=` placeholders from a flat env file while preserving every set value
   (incl. a custom `OPENAI_BASE_URL` the model depends on) — locally, secrets never leaving the box.
   With the back-up + name-only review steps, and the "don't hand-trim CLI-managed `config.yaml`"
   caveat. (Came out of leaning the owner's `~/.hermes/.env`, which had ~15 empty tool placeholders.)
2. **Honcho evaluated → captured as an idea** (`docs/ideas/honcho-memory-evaluation-2026-06-16.md` +
   README index). Verdict: **not for the Hermes control plane** (its memory is deliberately a sticky
   note; the repo is the real memory), but a possible **Someday** option for the bot's per-user AI
   personalization (V-04, gated on Q-0082). Routed via the new `intake` skill's idea lane (dogfood).
3. **Open-steps findability** (`hermes-control-plane.md` § Still open): pulled the **read-only Railway
   token** (log-triage gate) up into the open-steps list where it belongs (was buried in the
   capability note), and corrected the now-stale "Discord integration (later)" item — the **gateway
   is live** (owner chats with Hermes on Discord); only auto-*posting* summaries remains optional.

`check_docs --strict` green.

## 💡 Session idea (Q-0089)

A `scripts/hermes/lean_env.py` (or a one-liner alias) that wraps the env lean-filter with a built-in
**safety allow-list** — it refuses to write the new file if a required key (`OPENAI_API_KEY` /
`OPENAI_BASE_URL` / the gateway tokens) didn't survive the filter, so a custom-provider var can never
be silently dropped. Turns the "review before mv" manual step into a guard. Small, stdlib, disposable.

## ⟲ Previous-session review (Q-0102)

The intake skill (#928, prior PR this session) immediately earned its keep: the Honcho input was
routed through its exact "idea → evaluate → capture, don't promote" lane here. What it proves: the
front-door router and the idea/bug homes compose — a real inbound ("is Honcho worth it?") flowed
cleanly to a captured, classified idea file instead of a chat message that evaporates.
