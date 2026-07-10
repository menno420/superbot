# Purpose-specific test-bot fleet (2026-07-10)

> **Status:** `ideas` — owner-raised 2026-07-10 (round-3 dispatch, live). **Subsystem:** none
> (agent workflow / fleet testing infrastructure). **Gate:** deferred by the owner — explicitly
> "later"; capture only.

## The idea (owner's words, expanded per Q-0254)

For now the fleet reuses the ONE existing test bot for superbot-next live-drive. Later:
a small fleet of purpose-specific test bot identities — e.g. one dedicated to **testing
game functions** (games lanes + band-6 + Game Lab builds), possibly others per domain
(moderation-testing, load/soak). Each is its own Discord application: own token (separate
blast radius), own command namespace, own least-privilege guild placement — so parallel
test lanes never collide on one identity and a burned token never costs more than its
own domain.

## Dedup

Grepped docs/ideas/ (`test bot`, `sacrificial`, `bot identity`): nothing covers test-bot
identity provisioning; the Builder founding package §0.4 records the current reuse
decision.
