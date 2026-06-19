# Idea: per-user AI memory for the bot (Honcho) — remember Discord users across conversations

> **Status:** `ideas` — **bot / AI-lane idea** (owner-flagged "would be cool to have for our bot",
> 2026-06-16; wants to look into it **soon**). It first surfaced while evaluating Honcho for the
> *Hermes* control plane — not a fit there (footnote below) — but it **is** the right shape for the
> **bot's** per-user AI memory. Vision anchor: **V-04** (per-user preferences); gated on the AI spend
> ceiling (Q-0082).
> **Subsystem:** ai — in-bot AI per-user memory.

## The idea — give SuperBot's AI real memory of individual users

Today the bot's AI answers each request cold. **Per-user memory** would let it *remember a Discord
user across conversations* — their preferences, past questions, running context — and personalize
instead of starting from scratch every time. This is the V-04 "per-user preferences" vision item made
real for the AI surface.

## What Honcho is (the tool that fits)

Honcho (Plastic Labs, open-source) is an agent **memory / social-cognition layer**: it models each
participant as a "peer" and **extracts conclusions** from conversations (not just stores raw chunks),
exposing a `honcho_context` *representation document* — a compact summary of insights about a user —
to inject into the prompt without re-reading history. Strong long-memory benchmarks (LongMem-S ~90%,
LoCoMo, BEAM) at a **median ~5% of the context budget**.

**Why it beats the naive approach:** dumping full chat history into a big context window actually
*degrades* accuracy (Plastic Labs' benchmark: full-haystack context drops Haiku 4.5 ~27 pts vs an
oracle). Honcho gives the useful *conclusions* at a fraction of the size — better memory, less context,
lower cost. The cost angle matters because the AI lane runs under a hard spend ceiling (Q-0082).

## What to look into (when this is picked up)

- **Scope + privacy:** which AI surfaces get memory (general AI cog? BTD6 Q&A? all?), per-user vs
  per-guild, opt-in, what's stored, retention/forget — ties to the bot's existing P0-2
  data-minimization discipline.
- **Cost:** Honcho's per-call/representation cost vs the Q-0082 ceiling; self-host vs hosted.
- **Integration:** the AI cog's prompt-build seam is where a `honcho_context` doc would inject; needs
  a `HONCHO_API_KEY` + provider wiring. (Caveat: Hermes cron blocks external memory providers, upstream
  #9763 — but the *bot's* AI cog isn't cron, so that's a Hermes-only limit, not a bot one.)
- **Alternatives:** Honcho is one of several (Mem0, Supermemory, …) — compare before committing.

## Footnote — why NOT for Hermes (the control plane)

First evaluated for Hermes and rejected: Hermes' memory is deliberately a sticky note (owner prefs +
infra facts; the *repo* is its real memory), so a per-user modelling layer is overkill there. The
conclusion stands — Honcho is a **bot** idea, not a Hermes one.

## Disposition

- **Bot / AI lane:** owner wants to look into this **soon** → promote to a `docs/planning/` plan
  (scope · privacy · cost vs Q-0082 · integration seam) when the AI lane has capacity. V-04 is the
  anchor.
- **Hermes:** no action (keep the built-in `MEMORY.md` / `USER.md`).

Sources: [honcho.dev](https://honcho.dev/) · [plastic-labs/honcho](https://github.com/plastic-labs/honcho) ·
the Hermes memory-providers doc.
