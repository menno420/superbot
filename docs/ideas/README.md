# docs/ideas — the idea backlog & lifecycle

> **Status:** `ideas`. **Nothing here is approved for implementation.** These are
> capture docs so ideas live in the repo instead of in chat. Source code, the
> binding contracts, and `docs/current-state.md` always win over anything here.
>
> **This folder is a conveyor, not a graveyard.** The maintainer drops ideas in *any
> order, any time*; agents capture them, route each to a reasonable home, and keep the
> backlog moving so **every idea eventually becomes _implemented_ or _discussed_** (or
> explicitly _rejected_). Grooming this backlog is also the standing **secondary task** —
> what an agent does with leftover capacity once its main work + PR are done (see §
> "Backlog grooming").

## What lives here

Pure brainstorm backlogs — capture without commitment. Each file should carry an
`ideas` badge in its header and state what it is *not* (not a plan, not approval). **Once a
capture reaches its lifecycle outcome (§5) by being _implemented_, it is re-badged `historical`
during grooming** (it stays listed here, annotated ✅) so the active backlog reflects only live ideas.

Current broad captures:

- [`routine-activity-visibility-2026-06-14.md`](./routine-activity-visibility-2026-06-14.md) —
  **workflow / UX (2026-06-14, owner-observed):** routine *run* sessions are hidden from the
  Recents tab (intentional upstream behavior; open FR
  [anthropics/claude-code#54517](https://github.com/anthropics/claude-code/issues/54517)), so there
  is no at-a-glance "is a session active?" signal. Can't change the app UI — the DIY fit is a
  **Discord webhook ping** from each routine on start/finish (ask-gated: needs a channel + webhook).
- [`scheduled-maintenance-registry-2026-06-14.md`](./scheduled-maintenance-registry-2026-06-14.md) —
  **tooling / arch (2026-06-14, P0-2 media-retention session):** a central
  `register_maintenance(name, interval, coro, owner)` registry + one runner cog, to retire the
  "mint a whole cog per `tasks.loop`" tax (counters / spotlight / role / the new
  `media_maintenance_cog`) and give periodic work the observability it currently lacks (last-run /
  result / next-run / error per job — also feeds the P0-2 media-diagnostics follow-up). Surfaced
  by this session minting a zero-command cog just to host one purge loop. Medium; slice
  registry-first then migrate loop cogs one PR at a time.
- [`readiness-map-claim-vs-source-guard-2026-06-14.md`](./readiness-map-claim-vs-source-guard-2026-06-14.md) —
  **tooling (2026-06-14, P0-4 PR 2 session):** a guard that fails when a readiness-map /
  ownership row's **routing claim** ("routes through X", "uses the Y lane", "Done") contradicts
  the cited source file (reusing the channel invariants' forbidden-call sets). Surfaced by a real
  drift this session caught — `create_panel.py` was marked "uses the provisioning lane" while the
  source called `guild.create_text_channel` directly. Lifts the per-PR `test_no_direct_*`
  invariants up to the docs that describe them. Small/safe grooming-lane candidate.
- [`ledger-checker-print-pr-subjects-2026-06-14.md`](./ledger-checker-print-pr-subjects-2026-06-14.md) —
  **tooling (2026-06-14, band-#820 reconciliation pass):** have
  `check_current_state_ledger.py` print each **missing PR's merge-commit subject** next to its
  number (it already walks `git log`), collapsing the reconciler's manual `git log --grep` loop
  and reducing mis-attributed ledger entries. Runtime-lane (`scripts/`), so out of scope for a
  docs-only self-merge pass. Small/safe grooming-lane candidate.
- [`cogs-layer-view-residence-guard-2026-06-14.md`](./cogs-layer-view-residence-guard-2026-06-14.md) —
  **tooling / arch invariant (2026-06-14):** a guard flagging `discord.ui.View`/`Modal`
  subclasses **defined under `cogs/`** — invisible to the baseview ratchet (which only scans
  `views/`). Surfaced when the `!list` paginator was found mislayered in `channel_cog.py`
  only by tripping the cog-size ceiling. Warn → ratchet. Small/safe grooming-lane candidate.
- [`effective-check-constraint-test-helper-2026-06-14.md`](./effective-check-constraint-test-helper-2026-06-14.md) —
  **tooling (2026-06-14, PR #817):** a shared `effective_check_constraint(table, column)` test
  helper that derives the *current* SQL `CHECK (col IN …)` set by scanning all migrations in
  order, so the bespoke per-table **alignment tests never need manual repointing** when a
  constraint is widened in a later migration (059→op_kind, 069→actor_type each hand-rolled it).
  Small/safe grooming-lane candidate.
- [`ux-lab-interface-gallery-2026-06-12.md`](./ux-lab-interface-gallery-2026-06-12.md) —
  **owner-commissioned design (2026-06-12):** the **UX Lab** — a zero-write, admin-gated
  gallery cog (`!uxlab`) exhibiting every Discord interaction/layout pattern the pinned
  library supports (buttons · all 5 selects · modals incl. Label-wrapped selects · embed
  card archetypes · **Components V2** layouts (verified: 40-child/4 000-char budget on
  discord.py 2.7.1) · PIL cards), plus a **platform-limit probe bench** and clickable
  **mockups of the approved Q-0108–Q-0112 features**. Each exhibit carries registry
  metadata (`pattern_id`, status, limits) that graduates into `docs/ux/pattern-library.md`
  — the bot's design vocabulary. **State: IMPLEMENTED same day** (owner-steered):
  PRs **#758 / #760 / #762**, 2026-06-12 — the design
  ([plan](../planning/ux-lab-interface-gallery-plan-2026-06-12.md), now `historical`)
  shipped end-to-end; the durable artifact is
  [`../ux/pattern-library.md`](../ux/pattern-library.md) (Q-0116 records the call).
- [`server-safety-and-automod-2026-06-12.md`](./server-safety-and-automod-2026-06-12.md) —
  **owner-uploaded research (2026-06-12):** four moderation-safety modules SuperBot
  lacks vs. competitors (Carl-bot, Dyno, YAGPDB, Koya, Double Counter):
  **automod rules engine** (spam/link/caps/mention filtering with per-rule escalation) ·
  **server logging service** (message edits/deletes, join/leave, role changes) ·
  **image moderation** (OpenAI omni-moderation free endpoint vs. API4AI vs. Hive 50+
  categories) · **security service** (raid detection, account-age filter, alt detection,
  VPN blocking — tiered by privacy risk). **Decisions ANSWERED 2026-06-12
  (Q-0108/Q-0109/Q-0111, PR #740):** automod (all 4 rule types) + OpenAI-only image
  moderation + logging v1 + security tiers 1+2 **approved, plan-first** (routed to the
  roadmap's safety/community lane); security tiers 3+4 + paid image tiers declined.
- [`community-platform-features-2026-06-12.md`](./community-platform-features-2026-06-12.md) —
  **owner-uploaded research (2026-06-12):** five community-management features from
  ProBot, Koya, YAGPDB, Sesh, and Statbot:
  **welcome service** (PIL avatar-composited welcome cards, join DM, auto-role, goodbye) ·
  **social feed notifications** (YouTube-first per Q-0041, then Twitch/RSS/Reddit, with
  optional LLM video summarization) ·
  **event scheduler** (simple RSVP tier first; NL parsing gated on AI cost) ·
  **custom commands** (TagScript-safe, DB-stored, admin-only creation) ·
  **dynamic server counters** (statdock channel-renaming, quick-win candidate).
  **Decisions ANSWERED 2026-06-12 (Q-0110/Q-0112, PR #740):** welcome = embed-first,
  PIL cards phase 2; event scheduler = NL parsing from day one (Q-0082-metered) —
  both **approved, plan-first** (routed to the roadmap's safety/community lane).
- [`repo-manageability-2026-06-12.md`](./repo-manageability-2026-06-12.md) — ✅ **EXECUTED →
  `historical`** (2026-06-13 reconciliation): #1/#2/#3/#5 shipped (`scripts/{review_scope,_review_units,
  readiness_scoreboard,check_doc_freshness}.py` + the `current-state.md` trim/ratchet), #4 resolved via
  Q-0101. Originally (owner-asked 2026-06-12) five workflow-substrate manageability ideas.
- [`voice-mode-planning-capture-2026-06-11.md`](./voice-mode-planning-capture-2026-06-11.md) —
  **voice-mode brainstorm (2026-06-11):** UX and product ideas from a casual spoken planning
  session via ChatGPT. Covers setup wizard clarity, centralized settings navigation, help-menu
  modernization, crafting filters, craft-and-equip shortcut, deeper mining/chopping progression,
  world/exploration hub concept, idle/pets/co-op/NPC ideas, and routing notes per candidate.
  Strongest near-term candidates: crafting UX polish + AI settings clarity.
- [`ci-cost-and-duplicate-work-prevention-2026-06-14.md`](./ci-cost-and-duplicate-work-prevention-2026-06-14.md) —
  **owner-asked (2026-06-14, Q-0126):** `code-quality.yml` is the repo's dominant CI cost
  (940 runs / 2,396 min/month). **(a) CI efficiency — SHIPPED (PR #814):** concurrency
  cancellation of superseded PR runs + pip/mypy caching. `pytest -n auto` was tried (3× faster)
  but **reverted** — CI proved the suite isn't parallel-safe (non-deterministic state pollution).
  **(b) duplicate-work prevention — DECIDED & implemented:** claim ledger (`docs/owner/active-work.md`)
  + push-batching. **Live remaining idea:** make the suite parallel-safe → re-enable xdist (the
  ~3× unlock).

> **Standing intake note (Q-0089, 2026-06-10):** every session now *generates*
> one new `💡 Session idea` at END (owner directive — consistent generation
> beats occasional brilliance). Substantial ones land here as files; small ones
> live in their session log's 💡 flag. The grooming pass then moves them.

- **`scripts/command_surface_dump.py`** *(Q-0089 session idea, 2026-06-12 — **EXECUTED
  same session as grooming pass**)* — offline AST-based command-surface dump: reads
  all cog files without a live bot and emits every prefix/slash/group command by
  subsystem. `--diff-checklist` flags commands in source with no checklist entry (found
  120 gaps on first run — expected, as the checklist covers hub-level entries not individual
  commands). 8 tests. Makes `docs/audits/untested-surface-checklist.md` machine-verifiable
  going forward.

- [`wager-flow-map-2026-06-12.md`](./wager-flow-map-2026-06-12.md) —
  **session idea (2026-06-12, Q-0089, from the P0-1 wager-safety session #748):** a
  read-only offline `scripts/wager_flow_map.py` that traces every game's money path
  (accept→escrow→settle/refund, entry→payout) from the new `game_wager_workflow` call
  sites + `*_escrow` subsystems — the human-readable companion to the
  `test_game_wager_write_boundary` fence, with a `--check` drift mode (every escrow
  subsystem must have a matching settle + recovery). Quick-win, read-only tooling lane;
  build it next time an economy path is touched. Not auto-promoted.
- [`review-unit-tagging-2026-06-12.md`](./review-unit-tagging-2026-06-12.md) — ✅ **EXECUTED →
  `historical`** (2026-06-13 reconciliation): shipped as `scripts/review_scope.py` +
  `scripts/_review_units.py` + the `context_map.py` "Review unit" line. Originally a 2026-06-12
  Q-0089 session idea to make the repo-review partition a toolchain signal.
- [`portable-agent-memory-package-2026-06-12.md`](./portable-agent-memory-package-2026-06-12.md) —
  **maintainer vision (2026-06-12, voice):** extract this repo's consistent-memory +
  self-improving-workflow substrate into a standalone **open-source package** (à la CodeGraph)
  — the externalization of the "real artifact" CLAUDE.md already names. Carries a **priority
  reorientation**: lead with memory/workflow-substrate improvements so sessions auto-execute
  bot work. Core hard problem = mechanism-vs-content separation; sequencing = harden in-repo
  first (no approval needed), extract later. → **GRADUATED 2026-06-13 to an approved executable
  plan:** [`../planning/portable-substrate-kit-extraction-2026-06-13.md`](../planning/portable-substrate-kit-extraction-2026-06-13.md)
  (10 review rounds + owner approval; entry point PR 1a).
- [`autonomous-improvement-loop-vision-2026-06-12.md`](./autonomous-improvement-loop-vision-2026-06-12.md) —
  **maintainer vision (2026-06-12, voice):** the north-star — agents continuously improve
  the bot, chain session→session autonomously (idea → revised plan → implement), gate
  agent-*generated* features behind correctness (bugs/UX first), and use **Hermes as the
  independent reviewer** (a non-Claude "different mind" that critiques plans + implementations,
  explains features to the maintainer, and routes his approve/deny verdict). Maps each claim
  to existing scaffolding (`ai-project-workflow.md` §10/§11, the idea lifecycle); the loop is
  ~3 seams short. Decomposes into reviewable steps (dispatch bridge → reviewer seam → phase
  gate) → **discuss lane**.
- [`hermes-claude-dispatch-bridge-2026-06-12.md`](./hermes-claude-dispatch-bridge-2026-06-12.md) —
  **session idea (2026-06-12, Q-0089):** let Hermes *trigger* a Claude Code-on-the-web
  session from Telegram (not just prepare the prompt), closing the autonomous loop —
  phone idea → Hermes orients + dispatches → Claude Code builds/tests/PRs/self-merges →
  Hermes reports back. Preserves the safety split (Hermes read-only; Claude Code mutates
  under CI gates). Needs web-trigger API research → **discuss lane** (router Q-block).
- [`claude-code-plugins-evaluation-2026-06-12.md`](./claude-code-plugins-evaluation-2026-06-12.md) —
  **owner-asked (2026-06-12):** "any good Claude (Code) plugins useful for us?" —
  ecosystem survey (official + community marketplaces, spot-verified), filtered
  against our existing hooks/skills/CodeGraph stack. Verdict: most categories
  duplicate or fight our bespoke workflow; shortlist = **Context7** (live
  version-pinned library docs, strongest), read-only **Postgres MCP**, trial-only
  `pyright-lsp`. Supply-chain posture + pinning rules included. Adoption =
  executable-config change → routed to **Q-0096** (discuss lane).
- [`ai-panel-inplace-navigation-2026-06-11.md`](./ai-panel-inplace-navigation-2026-06-11.md) —
  **owner-requested (2026-06-11 live session):** the AI settings/panel family
  spawns a new ephemeral message per navigation click, scatters config across seven subpanels + a flat scalar editor (second owner ask: centralize), and extends raw
  `discord.ui.View` behind a blanket `views/ai/` yaml exemption (ratchet-invisible
  debt). Migrate it to the rest-of-bot in-place HubView pattern (V-02 navigation
  doctrine); source-confirmed diagnosis + scope sketch in the file.
- [`gap-analysis-2026-06-11.md`](./gap-analysis-2026-06-11.md) — six
  dedup-verified blind spots from the owner's "what's still missing?" probe:
  cross-server character identity (**Q-0091**, the public-era architectural
  question) · per-user data export/erasure (V-15's mirror) · owner alerting /
  dead-man's switch · session telemetry (quantify the self-improvement loop) ·
  AI spend metering (the Q-0082 instrument) · toolchain rot watch (live
  example: the Node-20 actions deprecation, forced 2026-06-16).
- [`bot-self-test-walker-2026-06-10.md`](./bot-self-test-walker-2026-06-10.md) —
  owner idea (brainstorm round 3): **the bot tests itself** — an owner-gated
  in-process walker that synthetically invokes every ledger-listed command
  (EventBus as witness, governance audience simulation, scratch test guild)
  + an AI eval mode running scripted prompts through the real pipeline
  (Q-0086 keys). Pairs with the commissioned untested-surface testing
  checklist; candidate probe set for the workflow-§10 Stage 1 caretaker.
  **→ Routed Later (structure-or-defer, 2026-06-13):** clear direction but bigger; pairs with
  P1-1 AI eval matrix and wants its own plan before building (roadmap → agent-ecosystem / Later).
- [`hermes-bug-triage-flow-2026-06-13.md`](./hermes-bug-triage-flow-2026-06-13.md) —
  **owner-directed (design captured, build next):** route `/bugreport` *through Hermes*
  (spam/genuine triage → reproduce + reword + fetch logs → save a curated `bug` issue +
  Discord summary) → nightly executor batch-fixes. Replaces the current direct instant-fire.
  **→ Routed Next (2026-06-13, roadmap agent-ecosystem lane); gated on Q-0121** — Hermes's
  second sanctioned write (`gh issue create`) needs an owner decision (the Q-0117 pattern).
- [`backup-integrity-check-2026-06-13.md`](./backup-integrity-check-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the backup-posture session):** add a dump
  integrity step to `backup-db.yml` — verify the dump contains ≥ threshold `CREATE TABLE`
  statements before uploading, catching the silent empty-dump failure class (pg_dump exits 0
  on permission errors). Turns the backup posture from "uploads something" to "uploads a
  verifiable schema snapshot." Small one-step addition; quick-win ops lane.
  ✅ **EXECUTED → `historical` (2026-06-13):** the `CREATE TABLE`-count gate shipped in `backup-db.yml`.
- [`safety-community-operator-landing-2026-06-13.md`](./safety-community-operator-landing-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the welcome+counters slot-6 session):** a read-only
  operator landing (`!safety` / Settings supergroup) aggregating the lane's scattered
  subsystems (automod · logging · welcome · counters · image-mod · security) with each
  master-flag state + a jump to its `!settings` group. Closes the operator-discoverability
  cost of going hub-less; composes from the existing schema registry (zero new state).
  Sequence after the lane's remaining slices land.
- [`readiness-maps-cite-regen-command-2026-06-13.md`](./readiness-maps-cite-regen-command-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the P0-3 settings pointer-lane session):**
  `production-readiness/*` maps embed frozen inventory counts that rot the moment a feature
  lands (the settings map was 1 day old and already wrong — 36/13 claimed vs 65/17 real).
  Convention (soft `check_docs` rule): a map stating a count must cite its regen command
  (`scripts/settings_lane_matrix.py`, `command_surface_dump.py`) beside it. Source-wins
  applied to the doc class most prone to drift.
- [`live-decade-queue-pointer-invariant-2026-06-13.md`](./live-decade-queue-pointer-invariant-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the third Q-0107 reconciliation pass):** a small
  invariant (extend `check_docs.py`) asserting the "one live queue" rule on disk — exactly one
  non-`historical` `reconciliation-pass-*.md`, and the current-state ▶ + roadmap pointers both
  resolve to it. Turns a convention every pass must remember into a CI guard; motivated by the
  three pointers this pass hand-verified. Workflow lane; quick-win when capacity allows.
- [`ledger-checker-range-scope-2026-06-13.md`](./ledger-checker-range-scope-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the fourth/band-#800 Q-0107 reconciliation pass):**
  scope `check_current_state_ledger.py`'s `#AAA–#BBB` range-expansion to the `## Recently
  shipped` section only, so a forward-looking planning range in the `▶ Next action` pointer
  can't silently mask a whole merged band from the ledger guard (the false-green this pass
  found + fixed by convention; ~14 PRs were hidden). The structural complement to the pointer
  invariant above. Workflow lane; small (logic + one test), high-leverage for the autonomous
  loop. Routed Next.
- [`executable-verification-over-prose-verified-2026-06-12.md`](./executable-verification-over-prose-verified-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** make evidence status machine-checkable — turn prose
  "verified" checklist items into executable checks/CI tests, or label them explicitly manual with a
  trace ID; treat any item without a verification rule as implicitly unverified. Prevents
  rot-by-narrative. Workflow lane.
- [`lane-scoped-session-state-2026-06-12.md`](./lane-scoped-session-state-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** cut the parallel-session merge tax by making
  in-flight session state lane-scoped by default (per-lane sub-files under `.sessions/` + `docs/ideas/`,
  scoped Q-router prefixes), aggregated on demand — prevention rather than after-the-fact UNION/renumber
  cleanup. Workflow lane; partially embodied by the existing per-`.sessions/`-file + ledger-discipline rules.
- [`single-canonical-execution-pointer-2026-06-12.md`](./single-canonical-execution-pointer-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** enforce that exactly one doc is canonical for "what do I
  execute next," and a superseding plan must repoint the old one in the same commit. **Overlaps
  [`live-decade-queue-pointer-invariant-2026-06-13.md`](./live-decade-queue-pointer-invariant-2026-06-13.md)**
  (the later, more specific form) — grooming to reconcile the two into one invariant.
- [`setup-wizard-onboarding-planner-spec.md`](./setup-wizard-onboarding-planner-spec.md) —
  **preserved target-scope spec (from closed issue #232, owner 2026-05-21):** the full
  guided server-onboarding planner — scan → propose plan → presets → `SetupOperation` drafts →
  Final Review, with confidence/conflict-detection/completeness-scoring/post-setup-summary. Much
  is now the active setup-platform lane; this preserves the original vision + the open-tail
  enhancements. Settings/setup lane.
- [`rps-tournament-service-refactor.md`](./rps-tournament-service-refactor.md) —
  **preserved refactor spec (from closed issue #229, owner 2026-05-20):** move RPS tournament
  orchestration/state out of `rps_tournament_cog.py` into an `RpsTournamentService` (5-step
  decomposition; the money seam already audited via `game_wager_workflow`). Games lane; medium-high
  before new tournament features.
- [`superbot-vision-2026-06-10.md`](./superbot-vision-2026-06-10.md) — the
  maintainer's written **product vision statement** (2-minute setup, panel
  navigation doctrine, 4-button help home, per-user preferences, RPG
  difficulty/survival/energy design, story pets, AI-as-panel-orchestrator) +
  the agent's creative response (AG-01…AG-15), dedup-mapped against every
  existing capture/plan/decision, with flagged tensions (T-1…T-5) and a routing
  ledger. **Newest owner-voice capture — read alongside the 2026-06-08 one.**
- [`fun-and-ease-brainstorm-2026-06-09.md`](./fun-and-ease-brainstorm-2026-06-09.md) —
  24 dedup-verified new ideas for "more fun + easier to use" (social/competition layer,
  ambient delight, member UX), each grep-checked against docs *and* source before
  capture. Owner cluster picks recorded (Q-0053): **pets & companions** (structured →
  [`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md)),
  context-menu actions, persistent reminders.
- [`cog-improvement-audit-2026-06-08.md`](./cog-improvement-audit-2026-06-08.md) —
  cog-by-cog improvement audit from a 36-question interactive session (2026-06-08).
  Covers all 35 existing cogs; includes a priority-ranked routing table. Top finding:
  setup wizard is P0 (half its steps do nothing); AI cog settings and RPS tournament
  decoupling are next.
- [`owner-vision-ideas-2026-06-08.md`](./owner-vision-ideas-2026-06-08.md) —
  20-question interactive session with the maintainer (2026-06-08); covers games
  (poker, idle), economy (marketplace, streaks), AI (dungeon master, NL, events),
  social (guilds, achievements, profiles), integrations (Twitch, YouTube, Spotify,
  Steam), and UX priorities. Includes a routing summary table. **Start here for
  the most up-to-date owner preferences.**
- [`future-product-direction-2026-06-07.md`](./future-product-direction-2026-06-07.md) —
  source-aware future product direction across polish, extensions, reusable systems,
  and long-term expansions; capture-only, not a roadmap.
- [`settings-presets-and-ai-template-advisor.md`](./settings-presets-and-ai-template-advisor.md) —
  the **Q-0070 presets-everywhere posture** (decided — routed to settings-audit
  Phase 4) + the **AI template/preset advisor** idea (modular prompt designs/styles
  as AI-cog settings so the AI can suggest the right template per task; captured
  only, gated).
- [`ai-extra-tool-capability-ideas.md`](./ai-extra-tool-capability-ideas.md) — AI
  extra-tool capability backlog (capture only, not approved work).
- [`mining_exploration_brainstorm.md`](./mining_exploration_brainstorm.md) — design-intent
  for the mining subsystem, referenced by `disbot/cogs/mining/exploration.py`.

Related idea-shaped docs that live elsewhere **by design**:

- `docs/planning/superbot-ideas-lab-2026-06-05.md` — brainstorm backlog, **but** its
  §2 (operating decisions) and §6 (rejection ledger) are **binding** "do-not-propose"
  — so it stays in `planning/`, not here.

## The idea lifecycle

```text
(1) INTAKE      maintainer drops an idea, any time, any order
      ↓         → capture it in docs/ideas/<topic>.md (state: raw → captured)
(2) MAP         name the owning subsystem, rough size, rough risk
      ↓
(3) ROUTE       send it to ONE reasonable home:
      ├─ small + safe + in an active lane → quick-win (execute now or next session)
      ├─ clear direction, bigger          → structured plan in docs/planning/ + a
      │                                      horizon on docs/roadmap.md (Now/Next/Later/Someday)
      └─ excessive / ambiguous / product  → DISCUSS FIRST: a Q-block in
                                             docs/owner/maintainer-question-router.md
(4) GROOM       leftover-capacity work: pull one routable idea forward (see below)
      ↓
(5) OUTCOME     every idea ends as exactly one of:
                implemented · on the roadmap at a horizon · in discussion (router) · rejected
```

**Routing rule — never auto-promote.** An idea is *captured and routed*, not promoted to
active work, unless the maintainer says so or it exposes a blocker / safety / architecture
conflict (`.claude/CLAUDE.md` Working agreement; `docs/collaboration-model.md`). Routing
just gives every idea a **state** and a **next destination** so none sits at `raw`.

**"Discuss if excessive."** If an idea is large, ambiguous, or a product-vision call,
the right route is a router Q-block — not silent promotion and not silent drop. The
maintainer's answer then sends it back onto this lifecycle (roadmap horizon, plan, or the
rejection ledger).

## Promotion gates (idea → implementation plan)

An idea may graduate to an implementation plan only after **all** of:

1. **Ownership** — the owning service / cog / pipeline is identified (`docs/ownership.md`).
2. **Reuse check** — existing service/helper/abstraction reuse is confirmed; no
   duplicate systems (`docs/helper-policy.md`).
3. **Risk review** — privacy, security/permissions, cost, and moderation risk reviewed.
4. **Mechanics** — migration / cache / test / rollback needs are listed.
5. **Promotion** — `docs/current-state.md` marks it an active candidate (and/or it lands
   on `docs/roadmap.md` at a horizon).

> **Idea-state vocabulary maps here.** The shared idea-states used across the AI projects
> (`raw → captured → … → shipped`, see
> [`../owner/ai-project-workflow.md`](../owner/ai-project-workflow.md) §5) are just words
> for an idea's position on *this* lifecycle plus the question-router question-lifecycle.
> This README owns the `captured → ready-for-planning → shipped` gates; the workflow doc
> references them — it does **not** define a parallel tracker.

## Backlog grooming (the standing secondary task)

So an agent **always has a next thing to do** — and so the backlog actually drains — every
session ends with a grooming pass once the main task + PR are done and capacity remains:

1. **Browse** `docs/ideas/` (and any new ideas the maintainer dropped this session).
2. **Pick one** routable idea and move it *one step* down the lifecycle:
   - **Execute it now** if it is small, safe, reversible, and in an already-decided lane
     (this is real work, not scope creep — `docs/collaboration-model.md` act-vs-ask).
   - **Structure it into a plan** for the next agent (`docs/planning/…`) + place it on
     `docs/roadmap.md` at a horizon, if the direction is clear but the work is bigger.
   - **Open a discussion** (router Q-block) if it is excessive / ambiguous / a product call.
3. **Record** the move: update the idea's state, and note the grooming in the `.sessions/`
   log so the next agent sees the backlog is live.

A **periodic sweep** (the `.session-journal.md` REVIEW cadence) confirms no idea is stuck
at `raw`/`captured` with no destination — that is the no-orphan guarantee, made checkable.

## Routed planning pass — 2026-06-08

The current cross-source lifecycle outcomes are recorded in
[`../planning/idea-roadmap-inventory-2026-06-08.md`](../planning/idea-roadmap-inventory-2026-06-08.md).
That ledger groups ideas by canonical subsystem/platform seam and links the resulting roadmap drafts; it does not approve implementation or replace the preserved capture docs above.
