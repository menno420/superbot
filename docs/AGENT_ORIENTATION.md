# SuperBot — Agent Orientation (Read This First)

> **Status:** `binding` — (reference material, not implementation approval).
> Future Claude / Codex / human contributors should read this page
> before proposing or implementing changes. It is the only file in
> `docs/` that exists to orient a brand-new session; everything else
> is consumed on-demand once you know where to look.
>
> **Scope:** orientation only. This document does not define
> architecture, ownership, or runtime contracts — it tells you which
> existing documents do.

---

## Why this file exists

SuperBot has **over 100 markdown files** in `docs/` (plus 7 ADRs and
`.claude/CLAUDE.md`) — far more than any one session should read. A new agent that opens
the folder and starts reading top-to-bottom will hit roadmap and audit
material before reaching the binding contracts. This file fixes that
by stating, up front:

1. Which docs are **binding** (treat as authoritative).
2. Which docs are **reference inventories** (consult per-task).
3. Which docs are **historical plans** (read for context only — do
   not treat as the current end-state).
4. Which docs are **how-to-work-in-this-repo** material.

> **This route is part of a self-improving system, not just a map.** It exists to
> get you productive fast *so you can spend the saved effort improving the system
> for the next agent* — tighten a route, capture a gotcha, fix a stale pointer.
> When you finish a task and notice the orientation could have pointed you better,
> **improving it is expected work, not scope creep** (you have free rein on docs;
> ask before changing hooks/config). The *why* is `docs/collaboration-model.md`
> § "Why this system exists"; the measurement loop is the session **context delta**
> (`.sessions/README.md`).

If you only read three files before touching code, read:

1. **`docs/architecture.md`** — layering, invariants, decomposition rules.
2. **`docs/ownership.md`** — who owns which tables, services, events.
3. **`docs/runtime_contracts.md`** — lifecycle guarantees + failure modes.

If you are about to add, move, or extract a helper function, also
read **`docs/helper-policy.md`** first.

---

## Reading order by task

> **Working in one area?** Start at its folio — `docs/subsystems/<area>.md`
> (consolidates that area's rules · current state · ideas · next candidates). The
> routes below add the binding/cross-cutting reading needed after the folio.

> **Load context in layers — do not read the whole `docs/` tree by default.**
> The default read path is short on purpose; everything else is consumed on demand.
>
> 1. `.claude/CLAUDE.md` + `docs/collaboration-model.md` — how we work.
> 2. `docs/current-state.md` — what is true right now.
> 3. this file's task route → the **one** relevant `docs/subsystems/<area>.md` folio.
>    **Shortcut:** the generated context pack (`docs/agent/generated/<subsystem>.context.md`)
>    gives you folio + binding docs + source roots + do-not-create warnings + gates
>    + verification commands in one page.  Read the folio for the debug router and
>    next candidates; the pack for everything else.
> 4. binding/deep docs (`architecture` · `ownership` · `runtime_contracts` · ADRs)
>    **only when the task touches them** — not preventively.
> 5. `docs/owner/maintainer-question-router.md` when product/owner intent is unclear.
>
> Everything under `docs/planning/` and `docs/audits/` is **historical context, read
> on demand** — never a top-to-bottom read. **To tell an *active* plan from a shipped/superseded
> one, read [`docs/planning/README.md`](planning/README.md) — the plan index** (active plans by
> sector + a historical inventory). The doc's own `> **Status:**` badge (`plan` = act on it ·
> `historical` = do not) is the per-file signal. When in doubt, source files win over docs.

### Any task

| Order | Doc | Why |
|---|---|---|
| 1 | `docs/collaboration-model.md` | **How we work** (binding, all agents): the goal comes first; session prompts are guidance not orders; approved plan = execute; act-vs-ask; bugs first. Read this before treating any prompt as a command. |
| 2 | `.claude/CLAUDE.md` | Working agreement + session workflow, CI parity rules, CodeGraph quick-reference, architecture invariants. Auto-loaded every session. |
| 3 | `docs/current-state.md` | **What is true right now**: stability baseline, in-flight work, recently shipped, gates, off-limits. A dated snapshot — source & merged PRs win; verify in-flight PRs against live GitHub. |
| 4 | `docs/codegraph-usage.md` | Full trust matrix behind the short CLAUDE.md rules. Skim once, refer back when CodeGraph surprises you. |
| 5 | `docs/AGENT_ORIENTATION.md` (this file) | What to read next, based on what you are doing. |
| 6 | `docs/repo-navigation-map.md` | Where things live in the tree. Use as a folder-to-purpose lookup. |
| 6b | [`docs/repo-sector-map.md`](repo-sector-map.md) | **The 3-tap navigation top layer** — the 5 planning sectors (Bot · BTD6 · AI-Memory system · Documentation system · Operations), each linking down to its subsystems (folios) and cogs/ideas. Planning lens; pairs with the review-scoping `repo-review-map.md`. |
| 7 | `docs/repo-review-map.md` (when scoping a review/refactor) | The review/refactor partition: for a given change, what is the smallest self-contained unit (subsystem slice vs. shared platform layer vs. data/tooling/docs domain). |
| 7b | [`docs/ultracode/`](ultracode/README.md) (when scoping a **parallel** refactor / fleet run) | The parallel-safety partition: which units a fleet can build at once without colliding, the shared-held surfaces + touch policy, the collision matrix, and the worker-scope template. Operationalizes row 7 for an Ultracode fleet. |
| 8 | `docs/owner/maintainer-question-router.md` (when needed) | Unresolved maintainer-facing questions and preserved owner intent. Unanswered questions are not approval. |

> **Dependabot PRs are yours on sight (Q-0256).** The session-start open-PR overlap scan
> (CLAUDE.md, Q-0126) is where you'll see them: an open `dependabot/*` PR has **no merge
> actor** (the auto-merge-enabler only arms `claude/*`), so the *first session that sees one
> reviews it and merges it* — majors get a real breaking-change assessment first
> (fix-then-merge if contained, else write a dedicated-session work item). Full rule:
> `docs/operations/repo-settings-state.md` § Dependabot PR policy.

### Adding a new subsystem / cog

1. `docs/architecture.md` § "Where to add a new subsystem" + § "Subsystem decomposition" + § "PersistentView placement".
2. `docs/ownership.md` § "Subsystem ownership" + § "Dependency direction".
3. `docs/runtime_contracts.md` § 1 ("Subsystem identity contract") + § 3 ("PersistentView contract") + § 7 ("Managed task lifecycle").
4. `docs/building-roadmap/command-integration-standard.md` — required panel / Help / settings wiring.
5. `docs/building-roadmap/mother-hub-map.md` — where the new subsystem fits in the hub tree.
6. `docs/helper-policy.md` — where to put any new helpers you write along the way.

### Editing an existing cog

1. `docs/repo-navigation-map.md` — find the cog's package, view package, service, DB module.
2. `docs/ownership.md` — confirm which service/pipeline mutations must go through.
3. `docs/help-command-surface-map.md` — confirm the cog's Help route and hub.
4. `docs/runtime_contracts.md` § 6 (interaction lifecycle) + § 7 (managed tasks).
5. Source files (always authoritative when in doubt).

### Touching shared runtime / `core/runtime/*`

1. `docs/architecture.md` § "Ownership boundary" + § "Single-process assumption" + § "State classification".
2. `docs/runtime_contracts.md` (all sections).
3. `docs/health/platform-consistency-ledger.md` § 1 (domain contract ledger).
4. `docs/decisions/001-no-redis-backed-state.md` — before adding any "we should cache this in Redis" plan.

### Touching governance / mutation pipelines

1. `docs/ownership.md` § "Service ownership" + § "Direct DB writes — explicit blocklist".
2. `docs/architecture.md` § "Runtime invariants (CI-enforced)" — INV-E, INV-F, INV-G are AST-checked.
3. `docs/runtime_contracts.md` § 9 (mutation contract checklist).
4. `docs/capability-authority.md` — how a settings/binding/provisioning mutation is authorized (capability resolver + operator kill-switches + the panel-callback re-check rule).

### Touching health / diagnostics

1. `docs/subsystems/health-diagnostics.md` — canonical area entry point and verification gaps.
2. `docs/health/bot-awareness-implementation-plan.md` — shipped programme status and execution authority.
3. `docs/health/platform-consistency-ledger.md` — cross-subsystem consistency/readiness state.
4. `docs/smoke-test-checklist.md` — doc-test-pinned runtime smoke expectations.

### Touching server management

1. `docs/subsystems/server-management.md` — canonical area entry point.
2. `docs/planning/server-management-status-2026-06-05.md` — authoritative shipped/remaining tracker; trust its body over older ordering.
3. `docs/setup-platform/resource-provisioning-overview.md` — resource-creation ownership and confirmation rules.
4. `docs/capability-authority.md` — operator authority and callback re-check rules.

### Touching BTD6 data / tools

1. `docs/subsystems/btd6.md` — canonical area entry point and extraction/expansion gates.
2. `docs/decisions/006-btd6-data-provenance-ownership.md` — binding provenance and owner-per-fact-type decision.
3. `docs/current-state.md` — global BTD6/AI expansion gate.

### Touching games

1. `docs/subsystems/games.md` — canonical area entry point and accepted boundaries.
2. `docs/decisions/002-game-state-not-restart-safe.md` — binding restart-safety decision.
3. `docs/archive/games-actionability-roadmap.md` — shipped actionability baseline and deferred context.

### Marking a feature "complete" (completion certification)

1. `docs/planning/feature-completion/README.md` — the system: the *feature-completeness* axis (distinct
   from the `production-readiness` *risk* axis), the per-feature unit model, the `▢ → ◐ → ✔` state
   machine, the soft completion-first policy, and the completion ledger of every S1 unit (Q-0209).
2. `docs/planning/feature-completion/rubric-game.md` / `rubric-server-function.md` — the two
   Definition-of-Complete checklists to score a unit against.
3. `docs/planning/feature-completion/units/blackjack.md` — the worked pilot certificate.
4. `python3.10 scripts/completion_scoreboard.py` — the generated certified-% scoreboard.

### Touching media / YouTube

1. `docs/subsystems/media-youtube.md` — canonical area entry point and verification/risk gates.
2. `docs/decisions/007-media-youtube-ownership.md` — binding shared-media ownership decision.
3. `docs/server-logging.md` — logging/audit routing and fail-safe expectations.

### Touching the public site (`botsite/`) / design-system / Claude Design

0. `docs/owner/website-explained.md` — **plain-language orientation** (Jinja vs. SPA, the
   `site.json` → `data.js` data pipeline, and the Claude Design loop). Read this first if the
   web/design vocabulary is unfamiliar.
1. `design-system/README.md` — **the contract for the Claude Design workflow**: the
   React/Tailwind component library that mirrors `botsite/`, how Claude Design reads it (the
   **GitHub connector** — primary — or `/design-sync`), the hybrid design→port→preview loop,
   and how to preview without redeploying.
2. `botsite/` — the live public site. The front-end is now the **Claude-Design SPA**
   (`botsite/site/`, served at `/`) whose data layer is generated from `site.json`
   (`botsite/site_data.py` → live `/data.js` + committed fallback). The earlier server-rendered
   Jinja2 templates (`botsite/templates/`) remain wired as a fallback. (Note: the design-system
   README still frames the loop as "port into Jinja" — reconcile when convenient.)
3. `.github/workflows/design-system-ci.yml` / `botsite-ci.yml` — the JS / site CI legs.

### Touching settings / bindings / resource provisioning

1. `docs/subsystems/settings-bindings-provisioning.md` — canonical area entry point.
2. `docs/setup-platform/settings-customization-roadmap.md` — the three lanes (settings / binding / provisioning) and which pipeline owns which.
3. `docs/setup-platform/resource-provisioning-overview.md` — the RPM lane.
4. `docs/health/platform-consistency-ledger.md` § 1 — current state of each domain.
5. `docs/building-roadmap/config-input-standard.md` — UI rules for setting widgets.
6. `docs/capability-authority.md` — authorization (capability resolver), the two operator kill-switches, and the panel-callback re-check rule.

### Touching tests / docs / smoke

1. `docs/smoke-test-checklist.md` — what must be smoked before a runtime-relevant PR ships. Pinned to `ReadinessSnapshot` by `tests/unit/docs/test_smoke_test_checklist.py`.
2. `tests/unit/docs/` — every doc-pinning test. Adding or removing a doc that has a pinning test means the test changes too.

### Touching command access (prefix + slash admission)

1. `disbot/core/runtime/command_access.py` — the resolver
   (`resolve_command_access`), adapters (`from_prefix_ctx` /
   `from_interaction`), and the bootstrap allowlist.  Both the
   prefix global check and `bot.tree.interaction_check` delegate
   here.
2. `disbot/services/command_access_service.py` — the canonical write
   path (`set_mode`, `replace_allowed_channels`, the `set_policy`
   composite).  Every operator-facing mutation must route through
   this module so cache invalidation + audit emission stay in step.
3. `disbot/cogs/bootstrap_access_cog.py` — installs both gates
   (prefix `_channel_guard` and `tree.interaction_check`).  Loads
   first in `config.INITIAL_EXTENSIONS`.
4. `disbot/views/settings/edit_command_access.py` + the
   `Command access` button on `views/settings/hub.py` — the
   operator UI surface.
5. `disbot/migrations/050_guild_command_access.sql` (schema) +
   `051_command_access_main_server_backfill.sql` (data) — the
   policy storage and the main-server backfill.  Add to
   migration 050's CHECK constraint before adding a new
   `AccessMode` literal.

### Editing the agent context system (docs/agent/, tools/agent_context/)

1. `docs/agent/README.md` — how the system works, what to put in the manifest, and what it does not replace.
2. `docs/agent/index.yml` — the curated manifest; **edit this, not the generated packs**.
3. `tools/agent_context/build_pack.py` — generates `docs/agent/generated/*.context.md`.
4. `tools/agent_context/validate_pack.py` — validates index paths and generated packs.
5. `tests/unit/docs/test_agent_context_index.py` — CI gate; regenerate + commit packs after index changes.

After editing the index, always run:
```bash
python3.10 tools/agent_context/build_pack.py
python3.10 tools/agent_context/validate_pack.py
python3.10 -m pytest tests/unit/docs/test_agent_context_index.py -v
```

### Working on the multi-agent pipeline / generating session prompts

1. `docs/owner/agent-workflow-spec.md` — **start here**: Analysis, Decisions, Revision,
   and Prompt Forge stage specs; prompt anatomy; cross-cutting rules.
2. `docs/owner/ai-project-workflow.md` — pipeline overview, per-stage role table,
   handoff templates, and idea-state vocabulary.
3. `docs/owner/maintainer-question-router.md` — preserved owner intent; Q-block template
   for routing unclear intent.
4. `docs/collaboration-model.md` — binding contracts every executor agent must follow
   (plan→execute lifecycle, act-vs-ask, bugs-first).

### Touching AI / setup advisor

1. `docs/subsystems/ai.md` — canonical area entry point and expansion gates.
2. `docs/ai-config-ownership.md` — binding contract for the AI cog's
   read model, projection rules, mutation seam, and UI surface
   pinning. Read this before any AI-cog change.
3. `docs/ai/ai-readiness-plan.md` — the inert scaffold + planned layer.
4. `docs/ai/ai-service-integration-map.md` — current setup advisor integration shape.
5. `disbot/core/runtime/ai/README.md` — package-level intent.

---

## Document classification

The taxonomy below is the only reliable way to tell "what does the
project still care about?" from "what was the plan a year ago?". When
in doubt, treat the source files as authoritative over any doc.

### Status badges (put one in each doc's header)

So a doc's authority is self-declaring (no inferring from filename/date),
each major doc should carry a one-line badge in its header. Use one of:

- **`binding`** — authoritative contract; changing it is an architecture change.
- **`living-ledger`** — current status, updated as work lands (carry a date).
- **`reference`** — a standard / how-to; stable.
- **`plan`** — a planned end-state; cross-check source before implementing.
- **`historical`** — superseded; kept for context. Start at `docs/current-state.md`.
- **`audit`** — a dated review/analysis snapshot; findings reflect that date only.
- **`owner-guidance`** — maintainer-facing intent/question routing (e.g. `docs/owner/`).
- **`ideas`** — brainstorm; not approved for implementation.
- **`archive`** — retired content kept only for history; do not act on it.

Write the badge as the **first** `> **Status:** \`badge\` — <role>` line under the
H1. When you touch a doc whose status is declared in an older free-form way
(`Status: …`, a "Superseded" banner), normalize it to this token opportunistically.
When a doc still has no badge, the classification lists below are authoritative.

### Binding (treat as authoritative)

These define the platform contract. Changing them is an architecture
change — open an issue or a separate doc-only PR before implementing
something that conflicts with them.

- `docs/collaboration-model.md` (how every agent works together; read first)
- `.claude/CLAUDE.md`
- `docs/architecture.md`
- `docs/ownership.md`
- `docs/runtime_contracts.md`
- `docs/codegraph-usage.md`
- `docs/AGENT_ORIENTATION.md` (this file)
- `docs/repo-navigation-map.md`
- `docs/helper-policy.md`
- `docs/decisions/*.md` (ADRs — immutable once landed)
- `docs/server-logging.md` (shipped feature reference)
- `docs/smoke-test-checklist.md` (pinned to code by doc-test)
- `docs/help-command-surface-map.md` (pinned to code by doc-test)
- `docs/ai-config-ownership.md` (pinned to code by doc-test)

### Living inventories / status ledgers

Updated as work lands. Always check the date / referenced PRs at the
top before trusting the contents.

- `docs/current-state.md` — the cross-cutting "what is true right now?"
  router (read 2nd, after CLAUDE.md): stability baseline, in-flight work,
  gates, off-limits. Source code and merged PRs win over it.
- `docs/roadmap.md` — the cross-area **plan index**: by area, with Now / Next / Later /
  Someday horizons + gates, linking each authoritative plan + folio. Where to look for
  which plans apply to which part of the code. Evolving; sequencing is relative, not dated.
- `docs/health/platform-consistency-ledger.md` — contract/reference shape with stale
  Phase-2 implementation-status cells; verify every cell against source + the relevant
  folio/tracker before treating it as work.
- `docs/health/bot-awareness-implementation-plan.md` — the bot-awareness / health-diagnostics
  programme. **Execution authority** for that work + live delivery status (**all 6 PRs
  shipped — PR1–PR3 in #537, PR4–PR6 in #541; D1 resolved**). Read
  this before touching `services/health_snapshot_service.py`,
  `services/health_contracts.py`, or the `!platform health` / `!platform startup`
  surfaces. The Codex map `docs/health/bot-awareness-diagnostics-plan.md` is context only.
- `docs/setup-platform/settings-customization-command-map.md`
- `docs/setup-platform/operator-settings-presets.md`
- `docs/planning/server-management-status-2026-06-05.md` — live status tracker for
  the server-management initiative. Authoritative on *what is done* + the remaining
  queue; **trust the tracker's "Shipped" / "Remaining queue" sections over any summary
  here** — don't restate its PR numbers (they drift). Start here before the roadmap/plan.
- `docs/archive/games-actionability-roadmap.md` (status: complete — historical now)
- `docs/audits/helper-debt-inventory.md` (snapshot — companion to `helper-policy.md`)
- `docs/audits/mutation_boundary_audit.md` — mutation boundary audit results.
  Run against the codebase post-hardening session (2026-05-24).

### Standards / reference guides

- `docs/owner/README.md` + `docs/owner/maintainer-question-router.md` — owner-facing
  question/intent routing; not a roadmap, plan, or approval source.
- `docs/owner/maintainer-working-profile.md` (`owner-guidance`) — the maintainer's
  working style and idea-flow shape (the *person*).
- `docs/owner/ai-project-workflow.md` (`reference`) — the multi-agent pipeline: per-project
  roles, handoff templates, idea-state vocabulary, and failure modes (the *process*).

Read once when relevant. They describe how to do something, not what
has already been done.

- `docs/building-roadmap/command-integration-standard.md`
- `docs/building-roadmap/hub-ui-standard.md`
- `docs/building-roadmap/config-input-standard.md`
- `docs/building-roadmap/mother-hub-map.md`
- `docs/setup-platform/settings-customization-roadmap.md`
- `docs/setup-platform/resource-provisioning-overview.md`
- `docs/architecture/service_ownership.md` — enriched "at a glance" ownership lookup.
  Quick-reference companion to `docs/ownership.md`; `ownership.md` is authoritative
  when the two disagree.
- `docs/context-map-tooling.md` — how to use `scripts/context_map.py` (file-impact context
  before editing a `disbot/` file: importers, blast radius, related docs/tests, risk).
- [`docs/architecture/repo-atlas.md`](architecture/repo-atlas.md) — how to use `scripts/atlas.py`,
  the repo-wide companion to this file: a generated, provenance-stamped index composing
  `context_map` / `_review_units` / `extension_crosswalk` (layer · review-unit · role · tests across
  the whole repo). Generated on demand, body not committed (Q-0151a).
- `docs/repo-review-map.md` — the review/refactor partition of the repo: the coarse
  top-level domains (Axis A) and, inside the bot, the unit of independent review
  (Axis B = the vertical subsystem slice vs. the shared platform layers). Read when
  scoping what a given change's self-contained review unit is. Companion to the
  navigation map (paths), architecture (layers), and ownership (tables).
- [`docs/research/external-systems-watchlist.md`](research/external-systems-watchlist.md) —
  external AI-agent / memory / autonomous-SWE systems (and human-org practice) worth learning
  from, each with the one transferable lesson + our adoption status. Re-checked on the grooming
  cadence; the place to look when asking "what is the field doing that we should steal?"

### Plans / roadmaps (read for context only)

These describe **planned** end-states. They do **not** describe what
exists today. Do not implement against them as if they were specs —
cross-check the source and the consistency ledger first.

- `docs/setup-platform/roadmap_setup_platform.md`
- `docs/planning/loose-ends-audit-roadmap.md`
- `docs/archive/phase_2b_bindings_plan.md`
- `docs/building-roadmap/interface-completion-roadmap.md`
- `docs/building-roadmap/command-expansion-backlog.md`
- `docs/building-roadmap/admin-powers-config-coverage.md`
- `docs/ai/ai-readiness-plan.md`
- `docs/ai/ai-readiness-pr-notes.md`
- `docs/ai/ai-service-integration-map.md`
- `docs/planning/server-management-roadmap-2026-06-05.md` — target architecture +
  maintainer decisions. **PR ordering superseded after #523** — read the status
  tracker / implementation plan for sequence.
- `docs/planning/server-management-implementation-plan-2026-06-05.md` — per-PR scope
  detail (PR1→PR14 — **all shipped through PR14/#584 except the gated PR13 AI
  layer**; the status tracker is authoritative). Pair with the status tracker.
- `docs/planning/superbot-ideas-lab-2026-06-05.md` — brainstorm backlog
  (advisory, **except** its §2 "operating decisions" and §6 "rejection ledger",
  which are binding "do-not-propose"). Read before proposing new
  UX/diagnostics/feature ideas so you don't re-litigate settled rejections.

### Historical snapshots (context only)

- `docs/archive/phase-2-completion-readiness.md` — old Phase-2 punch list; retained for
  blocker/migration history, not current next-work status.
- `docs/archive/` (see [`docs/archive/README.md`](archive/README.md)) — retired dated
  snapshots (the 2026-06 planning/audit burst, early cartography); superseded, do not act
  on them. Start from `docs/current-state.md` instead.
- Any remaining raw dated audits under `docs/planning/` / `docs/audits/`; obey their
  banners and start from `docs/current-state.md` instead.

### Ideas / brainstorms (not approved)

Capture, not commitment. Refine into a plan before implementing.

- `docs/ideas/` — pure idea backlogs (e.g. AI extra-tool capabilities). See
  `docs/ideas/README.md` for the promotion path + criteria.
- `docs/planning/superbot-ideas-lab-2026-06-05.md` — brainstorm backlog whose §2
  (operating decisions) + §6 (rejection ledger) are **binding**.

### Subsystem-specific scaffold notes

- `disbot/core/runtime/ai/README.md`

---

## "Read first" mandate for agents

Before proposing or implementing any non-trivial change:

1. Open this file (`docs/AGENT_ORIENTATION.md`) and follow the
   "Reading order by task" section that matches your work.
2. Open the relevant binding doc(s) before editing the corresponding
   code. Do not synthesize the contract from memory or from a roadmap.
3. If you are about to put a function somewhere "general" (in
   `utils/`, in `services/`, in `views/base.py`), open
   `docs/helper-policy.md` first.
4. If CodeGraph and a source file disagree, the **source file wins**
   (`.claude/CLAUDE.md` § "Read first — agent orientation"). Re-read
   the actual file you are about to edit.
5. **At the end of every session, create a PR** — do not wait to be
   asked. Plans span 2–3 PRs max (foundation first, implementation
   second). Plan approval means full execution in one session — do not
   stop for confirmation or wait for merges between PRs.
6. **Treat the session prompt as guidance, not orders, and use your own
   judgment** (`docs/collaboration-model.md`). Act on contained, reversible,
   verifiable changes — including a root-cause fix you find mid-task; ask only
   when something is irreversible, large/cross-cutting, or the goal itself is
   ambiguous. Aim for a positive, noticeable result every session.
7. **Before substantive work, state back the fuller picture you built from the
   ask** — inline, not as a blocking question — including the broader specs it
   implied but didn't say (`.claude/CLAUDE.md` § Working agreement, Q-0254).
   The maintainer builds ideas in fragments by design, sometimes starting from
   uncertain feasibility; this both catches a misreading before work happens
   and gives him new material (incl. the possibility space, when relevant) to
   react to — reasoning toward the most advanced capability the simplest,
   most efficient implementation can reach. During brainstorming, surface the
   one guiding question you can't derive yourself (rare, only when it matters
   and is actionable); escalate a big/vague idea to a delegated research pass
   or its own session rather than answering from memory alone. **Portable
   kit doctrine now** (graduated repo [menno420/substrate-kit](https://github.com/menno420/substrate-kit)
   `src/engine/templates/`; superbot's pin: `substrate.config.json`, #1879), not just local.

This is not a courtesy — repeated rediscovery is the main reason
SuperBot accumulates duplicate helpers and orphan plans. The minutes
spent reading these docs pay back at PR review.

---

## What this document does **not** cover

- Architecture. That is `docs/architecture.md`.
- Ownership. That is `docs/ownership.md`.
- Runtime guarantees. That is `docs/runtime_contracts.md`.
- Helper rules. That is `docs/helper-policy.md`.
- Where things live. That is `docs/repo-navigation-map.md`.
- CodeGraph caveats. That is `.claude/CLAUDE.md` and
  `docs/codegraph-usage.md`.

If you have to choose between this file and any of the above for a
given question, the specific doc wins.

---

## Updating this file

This file is **orientation**, not architecture. Update it when:

- A new binding doc lands → add it to the classification list.
- An existing doc graduates from "plan" to "binding" → move it.
- A binding doc is renamed or split → fix the path.
- A new common task pattern emerges that needs its own reading order
  → add a row to "Reading order by task".

Do **not** update it for:

- Phase progress (use `docs/archive/phase-2-completion-readiness.md` or
  the consistency ledger).
- Specific PR notes (those belong in the PR description).
- Long-form architecture rationale (those belong in
  `docs/architecture.md` or an ADR).

Keep this file short. If it grows past ~250 lines it has become a
duplicate architecture doc and the additions belong elsewhere.
