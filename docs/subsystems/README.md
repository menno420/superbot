# Subsystems — per-area documentation folios

> **Status:** `reference` (the folio convention) + a living index.
> Source code and `docs/current-state.md` win over anything here.

A **folio** is the single entry point for one part of the bot, so a session working
on that area reads *one* page instead of hunting across `docs/`. A good folio also
lets you spot adjacent work and **self-direct the next session** for that area.

## Folio template (the standard shape)

Each `docs/subsystems/<area>.md` should carry:

1. **What & where** — one-line scope + the key source dirs/files.
2. **Rules & approved structures** — the binding contracts for this area (link;
   don't restate) + any approved patterns.
3. **Current state** — what works / what's degraded *for this area* (links to
   `docs/current-state.md`).
4. **Ideas (not approved)** — link to `docs/ideas/…`.
5. **Next candidates** — ranked, with enough context to self-direct the next session.

**Drift-guard:** a folio's "Current state / Next candidates" is the area's *detail*
home; the global `docs/current-state.md` stays a *thin index* over them. One fact,
one home — vertically too.

## Subsystem index

Until an area has a folio, jump straight to its key docs.

| Subsystem | Folio | Key docs |
|---|---|---|
| AI | ✅ [`ai.md`](./ai.md) | (see folio) |
| Health / diagnostics | _todo_ | `bot-awareness-implementation-plan.md` + health source |
| Server management | _todo_ | `planning/server-management-status-2026-06-05.md` (+ roadmap / impl plan) |
| Settings / bindings / provisioning | _todo_ | `settings-customization-roadmap.md`, `resource-provisioning-overview.md`, `capability-authority.md`, `platform-consistency-ledger.md` |
| BTD6 data / tools | _todo_ | `btd6-*.md` (15+), `decisions/006` |
| Games | _todo_ | `games-actionability-roadmap.md`, `decisions/002` |
| Media / YouTube | _todo_ | `decisions/007`, `server-logging.md` |

> Building out a folio (consolidating an area's docs into the template above, and
> physically moving the area's `docs/*.md` under here when safe — mind doc-test-pinned
> files) is itself a good self-directed **next session**: pick the area you're in.
