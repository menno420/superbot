# Idea: Honcho external memory — evaluated; not for Hermes (maybe the bot's AI someday)

> **Status:** `ideas` — captured + evaluated 2026-06-16 (owner asked "is Honcho worth looking into?", seen in
> the Hermes env as `HONCHO_API_KEY` → `honcho_context`). Verdict: **not a fit for the Hermes control
> plane**; a possible future option for the **bot's** per-user AI memory. Routed here per the `intake`
> skill (idea → capture + classify, don't promote).

## What Honcho is

Honcho (Plastic Labs, open-source) is an agent **memory / social-cognition layer**: it models each
participant as a "peer" and **extracts conclusions** from conversations/events (not just chunks to
match later), exposing a `honcho_context` *representation document* with insights about a peer in a
session — quick to inject into a prompt without an extra LLM round-trip. Strong long-memory benchmarks
(LongMem-S ~90%, LoCoMo, BEAM) at a **median ~5% of the context budget**. Hermes ships it as one of
its ~8 external memory providers.

## Why it's NOT for Hermes (the control plane)

- Hermes' memory need is deliberately **tiny** — owner prefs + infra stickies + one behavioural rule
  (just cleaned to `MEMORY.md` / `USER.md`). SOUL.md's own rule: *"direct memory is a sticky note; the
  real memory is the repo"* (`current-state.md`, `.sessions/`, the docs). A user-modelling layer is
  overkill for an agent whose whole job is reading a thoroughly-documented repo.
- It adds an external dependency + API key + latency/cost to model **one owner** (and a few allowed
  users) — exactly the kind of unused integration the 2026-06-16 lean-base pass was *removing*.
- Hermes cron runs `skip_memory=True`, and upstream issue #9763 blocks external memory providers in
  the cron path anyway — so it would not help the routine/dispatch loop.

## Where it COULD fit (future — the BOT, not Hermes)

If SuperBot's **AI cog** ever wants genuine **per-user memory / personalization** (remembering a
Discord user's preferences and history across conversations — the V-04 "per-user preferences" vision
item), Honcho-style conclusion-extraction memory is the right *shape*: far better than dumping history
into the prompt (Plastic Labs' own benchmark shows a full-haystack context drops Haiku 4.5 ~27 pts vs
an oracle). That's an **AI-lane product decision**, gated on the AI spend ceiling (Q-0082), not a
Hermes setup step.

## Disposition

- **Hermes:** no action — keep the built-in `MEMORY.md` / `USER.md`.
- **Bot AI memory:** parked as a **Someday** option for the AI lane; revisit only if/when per-user
  personalization is prioritized.

Sources: [honcho.dev](https://honcho.dev/) · [plastic-labs/honcho](https://github.com/plastic-labs/honcho) ·
the Hermes memory-providers doc.
