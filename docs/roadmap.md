# SuperBot — Implementation Roadmap

> **Status:** `living-ledger` — the one cross-area "what's planned, for which area, in
> what order" index. **Last updated:** 2026-06-10.
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
| **Now** | The three active lanes (`docs/current-state.md` ▶ Next action is authoritative): **mining character platform** Wave 1 (Workshop + durability + live overview shipped #624; **next slice — Q-0072 answered 2026-06-10: the workshop-workflow service boundary first**, then structures / game-XP) · **Adaptive Setup/Access** Phase 1 (**P1B complete** — remainder shipped #632; **P1C next**, Q-0032) · **AI tooling** (orchestration **P4 MVP shipped #634**; **answerability P3 shipped #639** — the three self-awareness tools, Q-0047; read-only deterministic tools have a standing lift, Q-0048) |
| **Next** | The **[consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md)** (2026-06-10 — reconciles mapping PRs **#646**/**#647** + carries the 06-09 queue): **Batches 1–3 executed 2026-06-10** (#650 truth/clarity · #651 surface-classification invariant · #652 service boundaries, RS07 slice still open — verify merges) → **Batch 4** Settings **Phase 2** declaration coverage (Q-0064 BTD6 rows ride along) → **Batch 5** Adaptive **P1C** → **Batch 6** Help **projection seam** (Q-0055–Q-0059 overlay follows) · health/diagnostics production live-tests (owed) |
| **Later** | **Batch 7** mutation hardening (economy purchase → mining workflow convergence; **Q-0071/Q-0072 answered 2026-06-10** — workflow-service-owned transactions, workshop boundary first) · BTD6 post-cutover decode backlog (the Q-0066 `--all` cutover itself **shipped 2026-06-10, PR #649** — see the BTD6 section) · server-management **PR13 AI generation layer** + deferred governance setup (gated — Q-0008/Q-0011) · broad AI expansion beyond the active lanes (gated) · media channel-summary (privacy review) · games deferred follow-ups |
| **Someday** | The ideas backlog — not approved (see [§Someday](#someday--ideas-not-approved--capture-only)) |

---

## By area

### 🛡️ Server management — **structurally complete** (gated tail only)

Folio: [server-management](subsystems/server-management.md) · **authoritative sequence:**
[status tracker](planning/server-management-status-2026-06-05.md)

- **Shipped through PR14** *(routing corrected 2026-06-10 — this page queued the hub
  long after it merged)*: the unified **Server Management Hub** merged **2026-06-08 via
  #584** ([plan](planning/server-management-pr14-hub-plan.md), executed/`historical`);
  PR10 moderation config (all six slices), PR11 moderation + roles setup sections,
  PR12 setup diagnostics & repair, and PR13's **deterministic** role-templates slice
  all shipped before it.
- **Later (gated)** — the **PR13 AI generation layer** ("Generate with AI" role
  templates; AI per-exposure gate) → the deferred **governance** setup section
  (capability overrides + command-access — owner decisions Q-0008/Q-0011).
- Plans (context, not sequence): [roadmap](planning/server-management-roadmap-2026-06-05.md)
  (target architecture) · [implementation-plan](planning/server-management-implementation-plan-2026-06-05.md)
  (PR scope; shipped through PR14 — the tracker is authoritative).

### ⚙️ Settings / bindings / provisioning — **Next**

Folio: [settings-bindings-provisioning](subsystems/settings-bindings-provisioning.md)

- **Next** — **setup-wizard finalization** ([plan](setup-platform/setup_wizard_finalization_plan.md), active):
  finish the shipped scan/draft/review/provisioning flow.
- **Next** — settings coverage: pick a *verified* inconsistency from the
  [consistency ledger](health/platform-consistency-ledger.md); the three-lane model is
  [settings-customization-roadmap](setup-platform/settings-customization-roadmap.md).
- **Shipped 2026-06-09 (#640, scoreboard Lane 7)** — **settings audit Phases 0+1**:
  actionable-groups-only hub (`actionable_settings_groups()`, 11 live groups) +
  paginated >25-option reachability + per-guild routing availability markers.
  Sequencing home: [settings audit §11](planning/settings-cog-centralization-audit-2026-06-09.md).
- **Next** — settings audit **Phase 2** (declaration/coverage map: real domain-panel
  registrations replacing the Phase 1 `DOMAIN_CONFIG_SUBSYSTEMS` seam; **Q-0064**
  BTD6 announcement-channel binding + CT guided flow) — **Batch 4 of the
  [consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md)** —
  then **Phase 3** duplicate-path convergence (**Q-0063** converge-gradually — router §27).
- **Now (Phase 1 active)** — [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md):
  P0 + P1A + P1B shipped (#588/#589/#591/#592/#632); **P1C next** (staff-hub
  subpanels, Q-0032 — Batch 5 of the consolidated plan). *(Horizon corrected
  2026-06-10: this row said "Later" while the at-a-glance table said P1C "Next".)*
- **Later** — [setup-platform roadmap](setup-platform/roadmap_setup_platform.md) is the *aspirational*
  8-phase vision; the shipped wizard is a pragmatic subset. Direction, not queue.

### 🖥️ Building / interface (Discord-native UI) — **Next**

- **Complete (2026-06-10)** — the **platform-surface mapping campaign**: the
  [mapping standard](planning/platform-surface-mapping-standard-2026-06-09.md) (#641),
  Agent A's [user-surface map](planning/platform-mapping-a-user-surface.md) (#643),
  Agent B's [admin-surface map](planning/platform-mapping-b-admin-surface.md) (#644),
  and the two follow-on **untapped maps** —
  [runtime/services/workflows](planning/untapped-runtime-services-workflows-map-2026-06-10.md)
  (#646) · [docs/tests/verification](planning/untapped-docs-tests-verification-map-2026-06-10.md)
  (#647) — all merged; findings verified + reconciled 2026-06-10.
- **Next** — **implement the verified mapping batches**: the one active queue is the
  [consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md)
  (Batch 1 low-risk runtime truth/clarity — executed in #650, verify merged — +
  Batch 2 surface-classification invariant first).
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

### 🤖 AI — **Now** (active lane; per-exposure gate lifts)

Folio: [ai](subsystems/ai.md) · **Gate (re-postured 2026-06-09, Q-0048):** **read-only,
deterministic tools carry a standing lift** (no per-case ask; audience-tiered, no writes /
external calls); anything that **writes, costs money, calls external services, or adds UI**
still needs a per-exposure lift (precedents: `btd6_round_cash` #612, `ai:tools` UI #619).
Broad expansion stays gated on *all* of bot-wide stability + provider/provenance +
caching/source-health + behavior-config correctness (`docs/current-state.md`), **plus a
dedicated decision** for any action capability.

> **AI sequencing lives in the dedicated AI roadmap:**
> [`planning/ai-roadmap-2026-06-07.md`](planning/ai-roadmap-2026-06-07.md) (Phase 0–11,
> source-verified, planning-only) — the **AI-area authority**; the plans below are the
> inputs it consolidates. **First Opus AI target (AR-10, 2026-06-07): lock the orchestration
> foundation** before any net-new tools; audience posture is **tiered** (AR-08) and AI stays
> **explanation-only** (AR-09). Decisions: [`owner/maintainer-question-router.md`](owner/maintainer-question-router.md) §18.

- **Now (active lane)** — the **orchestration foundation**
  ([ai-complex-request-tool-orchestration-plan](ai/ai-complex-request-tool-orchestration-plan.md))
  **Phases 1–4 MVP shipped** (#612 catalogue+selector, #618 tool-choice+budgets, #619 typed
  policy + the gate-lifted `ai:tools` operator UI, **#634 the Phase 4 MVP slice** — the
  round-cash plan→execute→verify workflow + the first typed answer-with-evidence contract,
  profile-gated, default byte-identical; model loop awaits the maintainer's prod check).
  **Next:** the remaining §7 workflow families + the §12.1 durable audit trace follow the
  proven template.
- **Now (active lane)** — [AI Cog Completion + BTD6 Answerability](planning/ai-btd6-answerability-roadmap-2026-06-09.md):
  **Phase 1A/1B shipped** (#612 — `btd6_round_cash`, gate lifted per-tool), **Phase 2
  shipped** (#616 — the read-only introspection read model), and **Phase 3 shipped**
  (**#639**, 2026-06-09, Q-0047 — execution-plan Lane 4): all three read-only
  self-awareness tools in one slice (`get_ai_tool_catalog` · `get_ai_policy_explanation` ·
  `btd6_answerability`), audience-tiered at construction; model loop awaits the
  maintainer's prod check. **Next:** Phase 4 (AI settings UI) and Phase 5 (generated
  answerability dashboard) stay gated — Phase 4 behind the settings foundation, both
  behind their per-exposure asks.
- **Later** — [ai-tool-capability-roadmap](ai/ai-tool-capability-roadmap.md) sequences the
  backlog onto that foundation · [ai-readiness-plan](ai/ai-readiness-plan.md) M2 (typed policy
  tables + central NL stage) · [provider-switch + grounding fix](ai/ai-provider-and-grounding-fix-plan.md).
  Map: [ai-service-integration-map](ai/ai-service-integration-map.md).

### 🎈 BTD6 data / tools — **Now** (THE CUTOVER IS DONE — post-cutover decode backlog)

Folio: [btd6](subsystems/btd6.md) · index: [docs/btd6/](btd6/README.md) · ADR-006
provenance schema is implemented.

- **Shipped (2026-06-10 — PR #649, merged, the Q-0066 dedicated cutover
  session)** — **every committed stats file is game-native v55.1**: 25 towers +
  17 heroes + 13 paragons via `parse_gamedata.py --all` through the new cutover
  merge layer (curated names preserved + set-level name guard); Q-0067
  (Farm/Village full tiers + decoded income auras) and Q-0068 (per-tier beast
  names) executed in the same pass; source labels now read "BTD6 game data".
- **Post-cutover verification + carry-forward decode pass (2026-06-10 — PR
  #655)** — dump fidelity re-proven (byte-identical regeneration, rounds
  parity 140/140), all 2,022 menu embeds + the AI tool battery green; fixed:
  mode-rules dark data (now on both surfaces), the `!btd6 diagnostics` 400,
  the version-stamp-rot class (everything reports 55.1), the container-path
  leak. Then **every #649 carry-forward decoded** (`_CUTOVER_CARRYFORWARD`
  empty; audit **91 CLEAN / 0 DELTA / 0 SUSPECT**) — druid + paragon thorn
  rings, engineer typed-sentry rosters, sub Energizer/paragon support, bucc
  sellback + Flagship dedup, striker auras (+ dump fills committed holes),
  Magus phoenix.
  **Next:** decode-status ⭐ item 2 (banana economy), the buff/zone tail, the
  #655 answerability-gap items (5–6) — plus the maintainer's live spot-check
  of the new surfaces.
- **Earlier (#638, merged 2026-06-10)** — ABR rounds + income sets ingested
  game-natively (roundset-aware `btd6_round_composition`/`btd6_round_cash`);
  subtower mechanisms 7/7; buffs 15/38 confirmed.
- **Built (Q-0049 — #633, merged 2026-06-09)** — the
  "fetch-everything-on-update" data refresh is a committed **manual-dispatch GitHub
  Actions workflow** (`workflow_dispatch` only, no schedule): one-click refresh after a
  game update, no unattended fetches, output is a reviewable PR (never a push to main).
  Remaining: the first real dispatch from the Actions tab. Plan + how-to-run:
  [data-refresh-pipeline](btd6/btd6-data-refresh-pipeline-plan.md).

### 🎮 Games — **Now** (mining character platform active lane)

Folio: [games](subsystems/games.md) · **Boundary:** ADR-002 (game state not restart-safe —
accepted, not a target).

- **Now (active lane)** — the **mining character platform** (Wave 1, from the
  [mining brainstorm](ideas/mining_exploration_brainstorm.md) §7 vision). Shipped: explore
  wiring + equipment seam (#606, incl. the
  [wire-exploration plan](planning/mining-wire-exploration-plan.md)), "The Descent"
  persistent depth (#607), combat gear → deathmatch via the shared `utils/equipment.py`
  stat seam (#608), the sell-ore/buy-gear market economy loop (#609), and the read-only
  Character overview (#610), and the audited **Workshop + durability** keystone with
  the **mother-panel live overview** (#624, merged 2026-06-09 — brainstorm §7.5/§6.3;
  migration 063, tuning = Q-0054). **Next slice — Q-0072 answered (2026-06-10): the
  workshop-workflow service boundary first** (mapping FIND-RS02 — hardens the
  densest mutation path before more mining writes land); functional **structures**
  (§7.5 sinks) and Wave 2's **game-XP service** (§7.4) follow on the safer base.
  The owner-approved **duels-tick-weapon/armor-wear** slice (Q-0054) stays queued
  alongside.
- **Later** — bounded deferred actionability follow-ups (inventory architecture,
  leaderboards, bot-duel stats, shared back-button adoption) from the completed
  [actionability roadmap](archive/games-actionability-roadmap.md). Low priority; pick one bounded
  slice.
- **Later** — [**Pet companions**](planning/pets-companions-plan-2026-06-09.md): nameable
  pets from exploration drops + a care-loop coin/ore sink + tiny non-P2W perks; the
  owner's ⭐ pick from the 2026-06-09 fun/ease brainstorm (Q-0053). Gate: Wave-1
  keystone slices (Workshop + durability) + balance review + owner promotion.

### 📺 Media / YouTube — **Later** (needs an approved plan)

Folio: [media-youtube](subsystems/media-youtube.md) · **Gate:** ADR-007 + a
privacy/provenance/moderation review before any public surface.

- **Later** — a channel-summary / content-status feature would need a bounded read-only
  first slice and an explicit privacy/security review. No public media command ships today.

---

## Product-growth roadmap drafts — **Later / Someday** (not approved)

- **Later** — [social/community/progression](planning/social-community-progression-roadmap-2026-06-08.md): guilds, achievements, profiles, leaderboards, and notifications; gate: privacy/new-owner decision (Q-0038 answered 2026-06-09: server-scoped clans).
- **Later** — [economy/marketplace/rewards](planning/economy-marketplace-rewards-roadmap-2026-06-08.md): trade, rewards, sinks, onboarding, and crafting; gate: economy-health review + chance-reward review (Q-0039 answered 2026-06-09: donation = cosmetic-only, no bot-side billing).
- **Later** — [games/mining/idle growth](planning/games-mining-idle-roadmap-2026-06-08.md): poker, blackjack follow-ups, mining depth/co-op/idle; gate: ADR-002 + balance/ownership review.
- **Later (fully gated)** — [AI product-extension routing](ai/ai-product-extension-routing-2026-06-08.md): DM/events/NL/tool ideas routed under the authoritative AI roadmap; gate: all AI readiness/orchestration/action decisions (Q-0040 answered 2026-06-09: bounded-menu DM posture; building still needs its plan + per-exposure lift).
- **Later (gated)** — [BTD6 product-extension routing](btd6/btd6-product-extension-routing-2026-06-08.md): rules/trivia, challenges, runs, leaderboards; gate: ADR-006/provenance/source-health.
- **Existing plans** — [server-management/setup/access/routine extension routing](planning/server-management-extension-routing-2026-06-08.md): announcements, anti-spam, availability, explanations, analytics; gate: authoritative trackers and privacy/AI decisions.
- **Someday / Later** — [integrations/media/voice/website](planning/integrations-media-voice-website-roadmap-2026-06-08.md): provider alerts, activity, voice, and web projection; gate: privacy/security/moderation review (Q-0041/Q-0042 answered 2026-06-09: YouTube-first posture; staged Someday website).
- **Later** — [UX/discoverability/mobile-first](planning/ux-discoverability-mobile-roadmap-2026-06-08.md): help, changelog, copy, and mobile conformance through existing UI standards; gate: authoritative interface sequencing and copy/release-manifest decisions.
- **Later (decisions first)** — [Help cog customization audit and roadmap](planning/help-cog-customization-audit-2026-06-09.md): unify Help catalogue/projection before guild rename/hide/order customization; gate: Q-0055–Q-0059 + coordination with Adaptive Setup/Access P1B/P1C.
- Routing ledger: [idea-to-roadmap inventory](planning/idea-roadmap-inventory-2026-06-08.md).

## Someday / ideas (NOT approved — capture only)

> These are **not** queued work — captured so the picture is complete. Promoting one
> requires the gates in [`ideas/README.md`](ideas/README.md). Do not treat anything here as
> a priority.

- [fun-and-ease-brainstorm](ideas/fun-and-ease-brainstorm-2026-06-09.md) — 24
  dedup-verified fun + ease-of-use ideas (social/competition, ambient delight, member
  UX); owner picks recorded (Q-0053; pets structured → a games-lane plan).
- [settings-presets-and-ai-template-advisor](ideas/settings-presets-and-ai-template-advisor.md) —
  the AI template/preset advisor for settings (modular prompt designs the AI can
  suggest per task); the presets-everywhere *posture* itself is decided (Q-0070 →
  settings-audit Phase 4), only the advisor is Someday.
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
