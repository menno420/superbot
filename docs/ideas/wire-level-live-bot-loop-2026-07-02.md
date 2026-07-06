# The wire-level live-bot loop — Galaxy Bot dissolves the [needs-live-bot] gate (2026-07-02)

> **Status:** `ideas` — **⚠ CONTRADICTED-IN-PART BY SOURCE (2026-07-06, canonical-plan F-4 / PR
> #1770): do not build as written.** A second *bot* connection cannot drive message commands or
> passive pipelines — discord.py drops bot-authored messages at the library level
> (`ext/commands/bot.py:1413`) and disbot drops them again (`core/runtime/message_pipeline.py:279`
> + per-cog guards) — and slash/component interactions cannot be fabricated (Discord-minted
> tokens). The adopted replacement is the **two-lane fidelity model** in
> [`../planning/rebuild-test-guild-design-2026-07-06.md`](../planning/rebuild-test-guild-design-2026-07-06.md)
> §4 (in-process synthetic gateway + real-HTTP-for-prefix hybrid; human lane for interactions).
> Kept for provenance. Original framing below.
> Session idea (Q-0089, owner-requested harvest). Not approved for
> implementation. **Complements, does not duplicate,**
> [`bot-self-test-walker-2026-06-10.md`](./bot-self-test-walker-2026-06-10.md) — the walker is
> *in-process* synthetic invocation; this is the *out-of-process*, real-Discord loop.

## What Q-0213 changed

Agent containers hold a working **test-bot token** ("Galaxy Bot", verified live this session) plus
full Railway + provider credentials, expressly so the project runs without owner dependency. That
means an agent can, in-session: boot the bot under the test token against a **test guild**, drive
it over the real Discord gateway from a second connection, and read back what it actually posted —
a true black-box loop, no human in it.

## The idea

Build the loop once as a harness: `tools/livebot/` — (1) boot the bot (test token, scratch or
snapshot DB); (2) a driver client sends real messages/interactions in the test guild; (3) capture
embeds/components/DB effects; (4) assert. Two consumers, in order:

1. **Today's repo:** the `[needs-live-bot]` startability tag (repo-sector-map §tags) currently
   parks real work behind "needs a running bot / runtime creds" — this harness makes that gate
   **self-serviceable**: live walks, owner-flagged live bugs, and risky-change verification become
   agent-runnable instead of owner-queued.
2. **The rebuild:** this *is* the Phase-0.5 golden-harness Discord driver (strategy §3, Phase 0.5;
   design spec §6) — building it now against the current bot both unblocks `[needs-live-bot]` work
   and de-risks the rebuild's acceptance oracle before the freeze.

**Caveat honesty:** one thing it cannot do — Discord ignores other bots' messages for command
parsing (`author.bot` guard), so *message-command* invocation still needs the walker's in-process
path or a driver user-account alternative; slash commands, components, and passive pipelines
(logging, moderation events, AI passive answering) are all drivable wire-level. The two harnesses
together cover the surface.

## Route

S1/S3 · pairs with the golden-harness plan (Phase 0.5) and the self-test walker. First slice:
boot + one slash command + one component click asserted end-to-end in a test guild.
