# 2026-06-21 — Carl-bot reaction-roles research + overhaul plan

> **Status:** `complete` — docs-only research + planning deliverable. Carl-bot reaction-role
> mechanics + broader feature gap researched; a build-ready 3-PR overhaul/parity plan written.
> No runtime code. Self-merge on green (Q-0113 — docs-only, additive).

> **Run type:** `manual`

## Arc

Owner asked: *"Find out how Carl-bot does its reaction roles, as well as any other functions
we're missing, then create a plan on how we should implement this and possibly improve on it."*

Research + planning task (deliverable is a plan, not an implementation). Researched Carl-bot from
its official docs + the `carlbot-docs` source; mapped our current role subsystem from source (via
an Explore agent + direct reads); dedup-checked the backlog; wrote the plan; cross-referenced the
broader gaps to their existing idea captures.

## What shipped (docs only)

- `docs/planning/reaction-roles-overhaul-plan-2026-06-21.md` — the plan: Carl-bot mechanics, our
  code-grounded current state, the 3-PR arc (audited seam → button/dropdown role menus → modes +
  interactive panel), how we beat Carl, the full Carl feature-gap matrix, and 3 owner design Qs.
- `docs/ideas/channel-deployed-component-menu-primitive-2026-06-21.md` — the Q-0089 session idea
  (a shared deploy-a-persistent-component-message primitive that role menus / starboard / polls share).
- Index/homing wiring: `docs/planning/README.md` (S1 row), `docs/subsystems/server-management.md`
  (Plans pointer), `docs/ideas/README.md` (idea entry).

## Findings (the research, condensed)

- **Carl-bot reaction roles are emoji-reaction-first.** Modes `normal/unique/verify/drop/reversed/
  binding/temp`; per-message `limit` + `maxroles` + role black/whitelist; multi-message `link`;
  20 RR/message, ~250 total; `temp` (timed) is **Patreon-only**. Buttons/dropdowns are a secondary
  surface — its core is reactions, which is precisely the weakness to improve on.
- **We already have basic emoji reaction-roles** (`reaction_roles` table, raw listeners, 3 prefix
  commands, read-only panel) — but they're the project's clearest documented architectural debt:
  **direct DB writes (no audit seam)**, no modes/limits, read-only management UI. This is already
  flagged in `general-feature-layer-analysis` + `ui-view-adoption-audit`, and "self-role menu" is
  already on the command-expansion backlog. The plan **consolidates** that, it doesn't invent.
- **Most broader Carl gaps are already captured as ideas** — starboard (`fun-and-ease` §B1), custom
  commands (`community-platform-features` §4, Someday), suggestion box (`superbot-vision` AG-15),
  feeds (roadmap Later). Cross-referenced, not duplicated.
- **Automod already exists** (`automod_cog`: spam/invites/caps/mentions) — so content-moderation is
  *not* a Carl gap (only word/link/attachment-spam sub-filters are missing). Avoided mis-listing it.

## Decisions made alone (ratify if wrong)

- **Deliver a plan, not an implementation.** The ask said "create a plan"; role menus are a
  UX-heavy feature the owner-designer will want to visualize, so plan-first (not "smallest safe
  slice", but the right altitude). PR 1 (audited seam) is pure debt-paydown and safe to build
  immediately whenever greenlit.
- **Lead with native buttons/dropdowns** as the headline (vs. extending the emoji surface) — the
  modern component model is strictly nicer than Carl's reaction legacy.
- **New `role_menus`/`role_menu_options` tables** (migration 078) rather than overloading
  `reaction_roles` — keeps the emoji surface untouched in PR 1.

## ⟲ Previous-session review (Q-0102)

Reviewed `2026-06-21-creature-game-catch-collection.md` (#1208 — creature catch+collection v1).
**Did well:** textbook discipline — mirrored the fishing subsystem exactly (pure domain → audited
workflow → CRUD → hub-less cog), one-transaction write with emit-after-commit (Q-0071), fail-safe
catalog load, known-catalog allow-list on the leaderboard (carrying the fishing reconciliation
lesson forward). A clean, low-risk additive slice.
**Could improve / system observation:** creatures shipped **hub-less "exactly like fishing"** — but
the federated **Explore-hub** plan is now active, so that's *two* subsystems (fishing + creatures)
the hub will later have to retrofit. **Workflow improvement:** when a known-incoming plan (Explore
hub) will absorb a new subsystem, let the subsystem **declare its future world-hub membership at
creation** (a `subsystem_registry` field / folio note) instead of being retrofitted later — cheap
now, avoids a "wire N hub-less cogs into the hub" sweep when the hub lands. (Captured here; promote
to an idea file if a third hub-less game subsystem ships before the Explore hub does.)

## Context delta (self-improvement loop)

- **Needed but not pointed to:** the *current* reaction-role architecture debt (direct DB writes,
  read-only panel) is the crux of this task but lives only in two dated audit docs
  (`general-feature-layer-analysis`, `ui-view-adoption-audit`) — not surfaced from the role folio or
  current-state. A reader planning role work wouldn't be routed to it. → the server-management folio
  now links the overhaul plan, which names the debt; a folio "known debt" line would help more.
- **Pointed to but didn't need:** the large `current-state.md` ▶ Next callout (40K tokens) — none of
  it touched roles; the task-specific reads (folio + role source) carried the work. Confirms the
  "load context in layers, don't read the whole tree" guidance.
- **Discovered by hand:** that **automod already exists** (`automod_cog`) — the repo-navigation cheat
  sheet doesn't list an `automod` row (it predates the Q-0108 automod cog), so a quick grep was the
  only way to avoid mis-listing it as a Carl gap. → nav-map subsystem cheat sheet is mildly stale
  (missing automod / image_moderation / security / creature / fishing rows vs. the live cog glob).
- **Decisions made alone:** see above (deliver-a-plan; buttons-first; new tables).
- **Genuine weak point:** the plan's migration/table shape (§4 PR 1) is a *recommendation* designed
  from the schema, not yet validated against the persistent-view runtime — the building session
  should confirm the `role_menus.message_id`-nullable-until-posted flow against
  `core/runtime/persistent_views.py` before locking the schema.

## 📤 Run report

- **Did:** researched Carl-bot reaction roles + the broader feature gap and wrote a build-ready 3-PR overhaul/parity plan · **Outcome:** shipped (plan)
- **Shipped:** #1215 — reaction-roles Carl-bot parity + role-menu overhaul plan (docs-only)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** 3 design calls in the plan §9 — default surface (dropdown vs button), whether to audit per-member toggles, and whether to build free temp-roles. None block PR 1.
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** the Q-0089 idea [`channel-deployed-component-menu-primitive`](../docs/ideas/channel-deployed-component-menu-primitive-2026-06-21.md) (capture only, not built); the *plan itself* was the directly-requested deliverable, not self-initiated
- **↪ Next:** greenlight reaction-roles **PR 1** (audited `reaction_role_service` + migration 078) — pure debt-paydown, safe to build immediately; or answer the §9 design Qs to unblock PRs 2–3

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (1 pending auto-merge: #1215) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (Q-0089: channel-deployed component-menu primitive) |
| Ideas groomed | 0 (research/plan session — routed 4 existing captures into the plan matrix) |
