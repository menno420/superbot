# Session — 2026-06-24 · capture owner idea: bot-migration assistant

> **Status:** `complete` — docs-only idea capture. Single push, born-red → ready.

**Trigger:** owner chat request — *"can the bot recognize other bots, find out which things they offer,
suggest steps to replicate their functions, and delete the old bots once setup is complete?"* I
researched feasibility against live source (two `Explore` agents over setup + moderation/member seams),
answered in chat, and the owner chose **capture as an idea doc** over plan/build.

## What changed

- **New idea** [`docs/ideas/bot-migration-assistant-2026-06-24.md`](../docs/ideas/bot-migration-assistant-2026-06-24.md)
  — the detect → map → replicate → retire flow, grounded in the real seams it would dock into and honest
  about the one hard Discord constraint (no API to introspect another bot's commands → curated
  app-id-keyed catalog + observable signals, never live command reads). Subsystem: setup.
- **README index entry** added at the top of the broad-captures list, cross-linked to the V-14
  feature-mining lineage (this is the *live-in-server engine* on top of that *hand-harvest* lane).
- `check_docs --strict` green (new doc reachable via the index).

## Feasibility verdict (recorded so a planning session starts from reality)

- **Jobs 1/3/4 (detect / replicate / retire) are easy** — `member.bot` detection + `intents.members`
  already on; the setup advisor → draft → Final Review pipeline already stages audited reversible
  `SetupOperation`s; `moderation_service.kick()` already audited + hierarchy-gated.
- **Job 2 (discover what a bot offers) is the crux** — Discord exposes no cross-application command
  introspection. The realistic design is a curated catalog keyed by application id + observable signals
  (roles/channels/webhooks/integrations), with an honest "unknown bot → operator picks" fallback.
- It is a **feature-layer extension, not an architecture change** (new setup section + advisor +
  snapshot extension + catalog).

## 💡 Session idea (Q-0089)

**Shared competitor catalog as one source of truth.** The V-14 teardown (`competitive-teardown`,
`competitive-positioning-north-star`) harvests rival features into prose docs by hand; this new idea
needs a *machine-readable* app-id → competitor-features → SuperBot-subsystem map. Rather than letting
those drift apart, a future planning session should make **one structured catalog** (e.g.
`docs/data/competitor-bots.yml` or a service constant) that *both* the teardown docs and the migration
advisor consume — the same "one source, two consumers" discipline the repo already applies to the
subsystem registry and dashboard export. Captured inline in the idea doc's open-questions §; worth its
own idea file if the migration idea is promoted. Genuine — it prevents a real drift class before it
starts.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: the **twenty-fourth Q-0107 reconciliation pass (band-#1410)**. Did well: tight,
born-complete docs PR with every automated check (`check_docs`, `check_current_state_ledger`,
`check_loop_health`) explicitly run and its result recorded — exemplary ground-truth discipline, and it
correctly *carried forward* the band-#1380 plan queue rather than re-deriving it. One genuine miss it
flagged itself: it fired ~50 min after the prior pass on a 4-merge band (cadence jitter), and its own
session idea proposes the fix — good self-audit. **System improvement this surfaces:** idea capture has
*no* equivalent of the reconciliation routine's automated checklist — there is no checker that a new
`docs/ideas/*.md` carries the now-conventional header block (`Status:`, `Subsystem:`, lineage links). A
tiny warn-first `check_idea_header.py` (the proven 3-file disposable-tool shape, Q-0105) would keep idea
captures uniform the way `check_session_gate` keeps session cards uniform. Noting here, not building —
out of this session's scope.

## 📋 Doc audit (Q-0104)

Is anything from this session not in its durable home? No. The idea + its feasibility verdict live in the
idea doc; the index entry makes it reachable; no owner *decision* was made (the owner chose a workflow
step — capture — not a product/architecture ruling), so no router Q-block is owed. `check_docs --strict`
green. No `current-state.md` ledger change (no merged runtime PR).

## Context delta

- **Surprise:** the codebase *already* has nearly every building block this feature needs — the only
  genuinely new primitives are the curated catalog and a bot-only snapshot read. The feasibility risk is
  entirely in Job 2's Discord-API limit, not in SuperBot's architecture.
- **For next session:** if this idea is promoted, start from the "shared catalog, two consumers" decision
  above and Phase 1 (detect & report, read-only) — it ships value with zero risk.

## ⚑ Self-initiated: none — owner-directed capture (the owner explicitly chose "capture as an idea doc").
