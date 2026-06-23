# S1 — Bot product · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S1 · Folios:
> [server-management](../subsystems/server-management.md) ·
> [games](../subsystems/games.md) ·
> [settings-bindings-provisioning](../subsystems/settings-bindings-provisioning.md).

**Recently shipped (this sector):**
- **Reaction-roles arc — Carl-bot-mature** (#1234/#1237/#1242/#1243/#1245/#1246/#1248/#1250):
  multi-emote-per-message, channel/message pickers, role + gradient presets, free temp-roles
  member view, dead-binding self-heal. **PR 6 (PIL banner cards) shipped (#1279);** only the gated web
  builder (Surface A) remains
  ([plan](../planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **Creature game** — runtime catch/collection (#1208), level-normalized PvP engine + flow
  (#1213/#1230), leaderboard provider (#1244).
- **Mining grid** — seed-deterministic (x,y,z) grid + dig-moves-you (#1281/#1282).
- **Starboard / Hall-of-Fame** — plan #1254 → PR 1 #1259 → PR 2 #1270.
- **Fishing minigame** — cast/reel loop + rod ladder + energy (#1296–#1304, incl. the generous
  sell-value rebalance 1–7 → 1–21 in #1304); **Bait layer** — coin-bought consumable with **both**
  economy knobs: rarity (#1329) + the **bite-speed** half (#1337) on the same
  `CastStart`/cast-view seam, plus speed/combo baits. **Bait crafting** — turn small caught
  fish into bait packs (`fishing_workflow.craft_bait`, the `🪱 Bait` Craft select + `!craftbait`),
  closing `catch → craft → bait → bigger catch` (#1338). **⛵ Boat/deepwater venue** (#1340, this
  PR) — a persisted shore↔deepwater toggle (`!sail` + the menu button, migration 094
  `fishing_venue`); deepwater holds 11 **boat-only species** (uncatchable from shore) and runs a
  **tougher minigame** (6–12 s bites · 22% base escape) so the rod escape-resist knob finally pays
  off — additive (the original 21 shore fish unchanged), the literal §5 shore-cap rebalance left as
  an owner balance call.
- **Casino — multiplayer poker** (PR #1333) — a new Games-hub child for **group** card games with
  **per-player auto-updating ephemeral** hands; v1 = Texas Hold'em (play-chips). Pure `utils/cards/`
  + `utils/poker/` (eval + engine w/ side pots, fully tested) + the `views/casino/` ephemeral
  broadcast table. [design](../planning/casino-poker-design-2026-06-22.md).

**▶ Next startable (one of):**
- **Fishing follow-ups** (turn-key, on the bait/venue seam) — *(bait speed knob ✅ #1337, sell-value
  re-tune ✅ #1304, bait-crafting ✅ #1338, and the **⛵ boat/deepwater venue** ✅ PR #1340 — shore↔
  deepwater toggle + boat-only species + tougher deep minigame — are all done)* — remaining:
  the literal §5 **shore-cap-at-12 rebalance** (owner balance call, flagged in #1340) ·
  **weather/time-of-day modifier** · **trophy records per species**
  ([plan](../planning/fishing-minigame-design-2026-06-22.md) §"Other ideas" +
  [open-world expansion](../planning/fishing-open-world-expansion-plan-2026-06-18.md) Phase 2+: the
  boat-as-structure / travel-timer / destinations layer).
- **Project Moon runtime PR 1** — the `KnowledgeDomain` seam + first ingest
  ([plan](../planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
- **botsite React-SPA migration PR 2** — serve the built React app from `botsite/` + cutover
  (PR 1 foundation shipped; [plan](../planning/botsite-react-spa-migration-plan-2026-06-20.md)).

**In flight (don't duplicate):** Starboard PR 2 (#1270) config polish · botsite React-SPA
migration **PR 1** (#1305 — runnable data-fed React app + `/site-data.json`; foundation).

**Owner-paced / gated:** reaction-roles web builder (Surface A; PR 6 shipped #1279) · creature PvP balance + art (Q-0187) ·
website rollout ·
[feedback-board PR 1](../planning/feedback-board-generalization-plan-2026-06-19.md) (owner auth) ·
AI-ticket build (Q-0183) · Explore-hub PR 2 + gated layers (Q-0182) · dashboard writes / control-API
(security review).
