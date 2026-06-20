# 2026-06-20 — BUG note: AI replies to other bots' mentions + Pokétwo demand signal

> **Status:** `in-progress`

## Arc

Follow-up to the Pokétwo/MusicBot feature-mapping plan (#1180, merged). The owner shared a
Discord screenshot showing two things: **(1)** a live bug — SuperBot's AI replied *"Hey! You've
just pinged me…"* to a message that pinged **`@Carl-bot`**, not SuperBot; owner: *"make a note of
this."* **(2)** a product signal — a real user runs **multiple bots** (poketwo + music) because we
lack those features; owner: *"make sure we have a similar/better version of the Pokémon system."*

Docs-only. The AI engagement path is gated/sensitive (Q-0086 wants a runtime walk) and the core
fix has an owner behavior fork, so this **notes** the bug properly rather than speculatively
patching it.

## Plan (what this PR adds)

- `docs/health/bug-book.md` — **BUG-0019** (OPEN): root-caused both mechanisms (`always_reply`
  ambient mode answers messages aimed at other bots + the model hallucinates a "you pinged me"
  greeting because other-user mention tokens aren't stripped; and the `mentioned_in` `@everyone`
  footgun at `natural_language_stage.py:229`). Proposed fix + the one owner behavior decision.
- `docs/planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md` — added the **live demand
  signal** + a one-screen *"what Pokétwo actually does"* reference with our parity map (the owner
  noted he's unsure what poketwo does).

(In-progress; flipped to `complete` as the final step.)
