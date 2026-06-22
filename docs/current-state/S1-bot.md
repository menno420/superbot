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
  member view, dead-binding self-heal. Only PR 6 (PIL banner cards) + the gated web builder remain
  ([plan](../planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **Creature game** — runtime catch/collection (#1208), level-normalized PvP engine + flow
  (#1213/#1230), leaderboard provider (#1244).
- **Mining grid** — seed-deterministic (x,y,z) grid + dig-moves-you (#1281/#1282).
- **Starboard / Hall-of-Fame** — plan #1254 → PR 1 #1259 → PR 2 #1270.

**▶ Next startable (one of):**
- **Project Moon runtime PR 1** — the `KnowledgeDomain` seam + first ingest
  ([plan](../planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
- **botsite React-SPA migration**
  ([plan](../planning/botsite-react-spa-migration-plan-2026-06-20.md)).

**In flight (don't duplicate):** Starboard PR 2 (#1270) config polish.

**Owner-paced / gated:** reaction-roles PR 6 + web builder · creature PvP balance + art (Q-0187) ·
website rollout · feedback-board PR 1 (owner auth) · AI-ticket build (Q-0183) · Explore-hub PR 2 +
gated layers (Q-0182) · dashboard writes / control-API (security review).
