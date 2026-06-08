# SuperBot — Implementation Roadmap

> **Status:** `living-ledger` — the one cross-area "what's planned, for which area, in
> what order" index. **Last updated:** 2026-06-07.
>
> **What this is:** a thin router over the detailed plans. Each row is a one-line
> description + a link to the **authoritative plan** and the area **folio** — it restates
> nothing. The plan and the folio win over this page.
>
> **What this is *not*:** a schedule. Horizons are **relative sequencing, not dates** — the
> maintainer works associatively ([`owner/maintainer-working-profile.md`](owner/maintainer-working-profile.md))
> and idea-order ≠ implementation-order. A "gate" is what must clear before an item is
> ready, not a deadline.
>
> **Initial cut — evolving, not locked.** New plans get slotted into their area below as
> they land (see [Adding a plan](#adding-a-plan)); horizons will re-sequence as plans
> arrive and gates clear. Treat the ordering as a current best-guess, not a commitment.

## How to read

- **Now** = active lane / owed verification · **Next** = queued and ready (no blocking
  gate) · **Later** = wants a decision or a gate to clear first · **Someday** = captured
  ideas, not approved.
- **Gate** = the concrete thing that must clear first (a decision, a dependency, a
  stability bar). An item doesn't move up until its gate clears.
- **Authority:** `docs/current-state.md` owns *what is true now*; the **folios** own
  per-area detail; the **trackers/plans** own scope. This page only sequences them.
- **Ideas flow in here.** A captured idea (`docs/ideas/`) is routed onto a horizon below
  once it has a clear direction; until then it sits in **Someday** or in discussion (the
  question router). The intake → route → groom mechanism is
  [`ideas/README.md`](ideas/README.md) — promoting a backlog idea to a horizon is standing
  grooming work, not scope creep.

## At a glance

| Horizon | Items |
|---|---|
| **Now** | Server-management **PR13 AI** template layer (deterministic slice shipped 2026-06-08; PR10–PR12 shipped) · health/diagnostics production live-tests (owed) · [docs restructure (Q-0010)](planning/docs-restructure-brief-2026-06-08.md) |
| **Next** | Server-Management Hub (PR14) · deferred governance setup section · Discord-native interface completion · settings consistency coverage |
| **Later** | AI expansion (gated) · BTD6 extraction (ADR-006) · media channel-summary (privacy review) · games deferred follow-ups |
| **Someday** | The ideas backlog — not approved (see [§Someday](#someday--ideas-not-approved--capture-only)) |

---

## By area

### 🛡️ Server management — **Now** (active lane)

Folio: [server-management](subsystems/server-management.md) · **authoritative sequence:**
[status tracker](planning/server-management-status-2026-06-05.md)

- **Now** — **PR13 AI** template layer. (PR13's **deterministic** role-templates slice
  shipped 2026-06-08; PR10 moderation config, PR11 moderation + roles setup sections, and
  PR12 setup diagnostics & repair all shipped; PR11's governance setup section is deferred —
  owner decision Q-0008.)
- **Next** — the unified **Server Management Hub** (PR14, last;
  [plan](planning/server-management-pr14-hub-plan.md)) → the deferred governance setup section
  (capability overrides + command-access, Q-0011).
- Plans (context, not sequence): [roadmap](planning/server-management-roadmap-2026-06-05.md)
  (target architecture) · [implementation-plan](planning/server-management-implementation-plan-2026-06-05.md)
  (PR scope; PR1–9 shipped).

### ⚙️ Settings / bindings / provisioning — **Next**

Folio: [settings-bindings-provisioning](subsystems/settings-bindings-provisioning.md)

- **Next** — **setup-wizard finalization** ([plan](setup-platform/setup_wizard_finalization_plan.md), active):
  finish the shipped scan/draft/review/provisioning flow.
- **Next** — settings coverage: pick a *verified* inconsistency from the
  [consistency ledger](health/platform-consistency-ledger.md); the three-lane model is
  [settings-customization-roadmap](setup-platform/settings-customization-roadmap.md).
- **Later** — [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md): one source-grounded orchestration roadmap; Phase 0 identity/read-model foundations and owner questions precede product mutation.
- **Later** — [setup-platform roadmap](setup-platform/roadmap_setup_platform.md) is the *aspirational*
  8-phase vision; the shipped wizard is a pragmatic subset. Direction, not queue.

### 🖥️ Building / interface (Discord-native UI) — **Next**

- **Next** — **interface completion**: the live sequence is
  [mother-hub-map](building-roadmap/mother-hub-map.md) (S1–S13).
  [interface-completion-roadmap](building-roadmap/interface-completion-roadmap.md) is the
  arc; [loose-ends-audit](planning/loose-ends-audit-roadmap.md) is the source audit (its L1–L6
  sequence is superseded by mother-hub).
- **Later** — [command-expansion-backlog](building-roadmap/command-expansion-backlog.md)
  and [admin-powers config-coverage](building-roadmap/admin-powers-config-coverage.md):
  backlogs — cross-check source before pulling one.
- Standards (read when building, not roadmap items):
  [command-integration](building-roadmap/command-integration-standard.md) ·
  [hub-ui](building-roadmap/hub-ui-standard.md) ·
  [config-input](building-roadmap/config-input-standard.md).

### 🩺 Health / diagnostics — **Now** (verification owed)

Folio: [health-diagnostics](subsystems/health-diagnostics.md)

- **Now** — all bot-awareness phases (PR1–6) shipped; what's owed is **maintainer
  production live-tests**: owner receives `diagnostics_health_snapshot` (a non-owner does
  not), plus grouped-findings / recurrence rendering. The sandbox can't do this (no AI key).
- **Maintenance** — no unshipped phase pending; a new write-capable diagnostics flow needs
  a fresh approved plan. Execution authority:
  [bot-awareness-implementation-plan](health/bot-awareness-implementation-plan.md).

### 🤖 AI — **Later** (fully gated)

Folio: [ai](subsystems/ai.md) · **Gate:** AI expansion is gated on *all* of bot-wide
stability + provider/provenance + caching/source-health + behavior-config correctness
(`docs/current-state.md`), **plus a dedicated decision** for any action capability.

> **AI sequencing lives in the dedicated AI roadmap:**
> [`planning/ai-roadmap-2026-06-07.md`](planning/ai-roadmap-2026-06-07.md) (Phase 0–11,
> source-verified, planning-only) — the **AI-area authority**; the plans below are the
> inputs it consolidates. **First Opus AI target (AR-10, 2026-06-07): lock the orchestration
> foundation** before any net-new tools; audience posture is **tiered** (AR-08) and AI stays
> **explanation-only** (AR-09). Decisions: [`owner/maintainer-question-router.md`](owner/maintainer-question-router.md) §18.

- **Later (do first when unblocked)** — approve the **orchestration foundation**
  ([ai-complex-request-tool-orchestration-plan](ai/ai-complex-request-tool-orchestration-plan.md))
  *before* any net-new tools.
- **Later** — [ai-tool-capability-roadmap](ai/ai-tool-capability-roadmap.md) sequences the
  backlog onto that foundation · [ai-readiness-plan](ai/ai-readiness-plan.md) M2 (typed policy
  tables + central NL stage) · [provider-switch + grounding fix](ai/ai-provider-and-grounding-fix-plan.md).
  Map: [ai-service-integration-map](ai/ai-service-integration-map.md).

### 🎈 BTD6 data / tools — **Later** (gated on ADR-006)

Folio: [btd6](subsystems/btd6.md) · index: [docs/btd6/](btd6/README.md) · **Gate:** the
**ADR-006** provenance schema must be implemented before extraction resumes.

- **Later** — restart extraction only after the provenance schema, source-registry owner
  matrix, safe migrations, and observable cache/source-health are in place. Status:
  [decode-status](btd6/btd6-gamedata-decode-status.md).
- **Next (needs sign-off)** — scheduled "fetch-everything-on-update" data refresh: the manual
  command chain + regenerable [coverage map](btd6/btd6-dump-coverage-map.md) exist; committing
  the GitHub Actions automation is a maintainer call. Plan:
  [data-refresh-pipeline](btd6/btd6-data-refresh-pipeline-plan.md).

### 🎮 Games — **Later / maintenance**

Folio: [games](subsystems/games.md) · **Boundary:** ADR-002 (game state not restart-safe —
accepted, not a target).

- **Later** — bounded deferred actionability follow-ups (inventory architecture,
  leaderboards, bot-duel stats, shared back-button adoption) from the completed
  [actionability roadmap](archive/games-actionability-roadmap.md). Low priority; pick one bounded
  slice.
- **Next (ready, ungated)** — **wire `!explore` to the shipped depth/loadout engine.** The
  pure `cogs/mining/exploration.py` engine is already shipped + unit-tested; the swap reuses
  `resolve_to_legacy_tuple()` (the exact tuple `!explore` already consumes), so it's a bounded
  one-command behaviour change. Plan:
  [mining: wire exploration](planning/mining-wire-exploration-plan.md). Promoted from the
  [mining brainstorm](ideas/mining_exploration_brainstorm.md) §5 via the idea lifecycle
  (Q-0015 grooming, 2026-06-08); awaiting maintainer go to build.

### 📺 Media / YouTube — **Later** (needs an approved plan)

Folio: [media-youtube](subsystems/media-youtube.md) · **Gate:** ADR-007 + a
privacy/provenance/moderation review before any public surface.

- **Later** — a channel-summary / content-status feature would need a bounded read-only
  first slice and an explicit privacy/security review. No public media command ships today.

---

## Someday / ideas (NOT approved — capture only)

> These are **not** queued work — captured so the picture is complete. Promoting one
> requires the gates in [`ideas/README.md`](ideas/README.md). Do not treat anything here as
> a priority.

- [future-product-direction](ideas/future-product-direction-2026-06-07.md) — source-aware
  future product direction (polish, extensions, reusable systems, long-term).
- [ai-extra-tool-capability-ideas](ideas/ai-extra-tool-capability-ideas.md) — AI capability
  backlog (web / vision / file / KB / connectors / scheduler).
- [mining-exploration-brainstorm](ideas/mining_exploration_brainstorm.md) — mining design intent.
  *(§5 step 1 promoted 2026-06-08 to a [plan](planning/mining-wire-exploration-plan.md) + the
  Games lane; the rest stays captured.)*
- [superbot-ideas-lab](planning/superbot-ideas-lab-2026-06-05.md) — broad brainstorm; its
  §2 (operating decisions) + §6 (rejection ledger) are **binding do-not-propose**.

---

## Adding a plan

When a new plan doc lands (e.g. a fresh Codex/Opus planning doc):

1. Add a **one-line row under its area** above — description + link to the plan + a
   horizon + a gate (or "—" if none). If it doesn't fit an existing area, add it under the
   closest one and note that the folio assignment is pending.
2. A new plan is **not auto-prioritized** — idea-order ≠ implementation-order. Default it
   to *Later* (or *Next* only if the maintainer says it's ready and nothing gates it).
3. Link the plan from its area **folio** too, so it's reachable both ways (the
   `scripts/check_docs.py` reachability gate enforces this).

This page is the *index*; the new plan doc stays the authority for its own scope.

## Maintenance

When work ships: update the area **folio** + `docs/current-state.md`, move the item's
horizon here (or drop it), and re-badge a finished plan `historical`. When a **gate**
clears (a decision lands, a dependency ships), promote the gated item from *Later* to
*Next*. The reachability gate (`scripts/check_docs.py`) keeps every plan linked here
findable.
