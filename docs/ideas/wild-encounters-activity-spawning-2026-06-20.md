# Wild Encounters — activity-based spawning (2026-06-20)

> **✅ OWNER DECISION (Q-0186, 2026-06-28, question panel):** this is the Pokétwo **Lane A** the owner
> chose to **build first** (highest engagement leverage; feeds the Collection / Quest / Shiny lanes).
> Spawn defaults + anti-spam guardrails (per-channel opt-in, rate-limit, no auto-catch, earned-only per
> Q-0039, stranger-grade per Q-0080) ride this doc's defaults; a runtime session builds it in small PRs.
> Canonical: router Q-0186.

> **Status:** `ideas`. **Not a plan, not approval.** Capture doc. Source + binding contracts +
> `docs/current-state.md` win. **Subsystem:** games.
>
> Origin: the owner's Pokétwo/JMusicBot research report (2026-06-20). The report's strongest,
> most-repeated Pokétwo lesson — *spawns linked to chat activity drive conversation and
> community* — is the **one mechanic with no analog anywhere in the repo** (fishing and mining
> are both manual command-only; there is no passive, message-triggered event). Promoted into a
> PR-sized spec in [`planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md`](../planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md)
> § "Lane A".

## The idea

A new **Encounters** subsystem: non-bot messages in an opted-in channel accrue a debounced
activity counter; at a configurable threshold the bot spawns a **wild encounter** (embed +
**Claim** button) in that channel. The first valid claimer (capability re-checked at callback
time, stranger-grade Q-0080) receives a reward **routed through existing seams** — a
fishing/mining item, coins via `economy_service`, and `game_xp` for a new `GAME_ENCOUNTERS`.

It is deliberately **not** a Pokémon clone: there's no creature roster to license, no battles, no
new currency. It's a thin engagement engine that **reuses** the economy/XP/inventory/world-hub
seams and **docks** into the federated Explore hub (`world_registry`).

## Why it's worth having

- **Engagement leverage:** passive spawns reward genuine conversation (the report's core lesson),
  unlike every current game which only fires on an explicit command.
- **Net-new, ungated, anti-P2W:** no existing analog to duplicate; rewards are free and earned by
  activity (no conflict with Q-0039); read/claim is stranger-grade.
- **Feeds the other lanes:** the items/variants it drops are exactly what a future
  collection-filter (Lane B), shiny/variant layer (Lane D), quest engine (Lane C), and eventually
  the gated marketplace would operate on.

## Open design questions (route to Q-0186, don't decide unprompted)

1. **Default threshold + debounce** (the report's "~24 messages" — config-driven, off by default).
2. **Reward pool** — fishing/mining items vs. coins vs. a dedicated encounter catalogue.
3. **Claim shape** — first-click vs. "name the catch" guess (folds in the report's hint mechanic).
4. **Anti-abuse** — per-claimer cooldown, one live spawn per channel, channel allow-list,
   no-auto-catch (the report's own anti-spam rule).

## Anti-patterns

- ❌ A parallel "catching game" — catching already lives in fishing/mining/pets; this is a
  *spawn+claim* engine, not a second collection game.
- ❌ A new currency or buyable boost (Q-0039).
- ❌ Unbounded spawns / DM spam — off by default, per-channel opt-in, rate-limited.

→ relates [feature-mapping plan](../planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md)
· [explore-hub plan](../planning/explore-hub-federated-world-plan-2026-06-19.md) ·
[fishing plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md) · Q-0186 · Q-0039
(no P2W) · Q-0080 (stranger-grade) · Q-0071 (atomic workflow).
