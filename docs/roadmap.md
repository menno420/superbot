# SuperBot — Implementation Roadmap

> **Status:** `living-ledger` — the one cross-area "what's planned, for which area, in
> what order" index. **Last updated:** 2026-06-09.
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
| **Now** | The three active lanes (`docs/current-state.md` ▶ Next action is authoritative): **mining character platform** Wave 1 (Workshop + durability + live overview built 2026-06-09, PR #624; structures or game-XP next; tuning Q-0054) · **Adaptive Setup/Access** Phase 1 (**P1B complete** — remainder shipped #632; **P1C next**, Q-0032) · **AI tooling** (orchestration **P4 MVP shipped #634**; **answerability P3 shipped #639** — the three self-awareness tools, Q-0047; read-only deterministic tools have a standing lift, Q-0048) |
| **Next** | Adaptive **P1C** (staff-hub subpanels — Q-0032; tier path shipped #632) · Settings **Phase 2** (declaration/coverage map; Q-0064 BTD6 binding+guided flow) · Help **projection seam → Q-0055–Q-0059 overlay** (design-ready; lands on the #642 characterization net) · Server-management **PR13 AI** template layer + Hub follow-ups (PR14) · health/diagnostics production live-tests (owed) — *(shipped out of this row 2026-06-09: the Q-0025 scaffold → Spotlight registration **#626**, the Q-0049 BTD6 refresh workflow **#633**, settings hub actionable-groups + >25 reachability **#640** — Lane 7, Help counts + characterization net **#642** — Lane 8)* |
| **Later** | Broad AI expansion beyond the active lanes (gated) · BTD6 `--all` towers cutover (dedicated session — Q-0066; extraction itself resumed 2026-06-09, see the BTD6 section) · media channel-summary (privacy review) · games deferred follow-ups |
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
- **Shipped 2026-06-09 (#640, scoreboard Lane 7)** — **settings audit Phases 0+1**:
  actionable-groups-only hub (`actionable_settings_groups()`, 11 live groups) +
  paginated >25-option reachability + per-guild routing availability markers.
  Sequencing home: [settings audit §11](planning/settings-cog-centralization-audit-2026-06-09.md).
- **Next** — settings audit **Phase 2** (declaration/coverage map: real domain-panel
  registrations replacing the Phase 1 `DOMAIN_CONFIG_SUBSYSTEMS` seam; **Q-0064**
  BTD6 announcement-channel binding + CT guided flow), then **Phase 3** duplicate-path
  convergence (**Q-0063** converge-gradually — router §27).
- **Later** — [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md): one source-grounded orchestration roadmap; Phase 0 identity/read-model foundations and owner questions precede product mutation.
- **Later** — [setup-platform roadmap](setup-platform/roadmap_setup_platform.md) is the *aspirational*
  8-phase vision; the shipped wizard is a pragmatic subset. Direction, not queue.

### 🖥️ Building / interface (Discord-native UI) — **Next**

- **Next** — **platform-surface mapping campaign** (2026-06-09): two parallel
  Codex mapping agents (A: user surface · B: admin/platform surface) map every
  subsystem/command/panel/service against the
  [mapping standard](planning/platform-surface-mapping-standard-2026-06-09.md)
  (verified baseline · schema · split · copy-paste prompts), then one
  merge/implementation session lands the consistency fixes. Mapping-only;
  Lanes 7–8 / adaptive P1C keep their queued scopes. Gate: #641 merged +
  re-verify in-flight PR state live before launching the agents (#639/Lane 4
  merged 2026-06-09; #638 was still an open draft at the late-2026-06-09
  reconciliation).
- **Next** — [untapped runtime/services/workflows map](planning/untapped-runtime-services-workflows-map-2026-06-10.md)
  (2026-06-10, Codex): the below-the-surface seam audit behind the mapping
  campaign (mutation ownership, cache/event invalidation gaps, helper
  duplication) — input to the merge/implementation session.
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

### 🎈 BTD6 data / tools — **Now** (extraction resumed; cutover is the next session)

Folio: [btd6](subsystems/btd6.md) · index: [docs/btd6/](btd6/README.md) · ADR-006
provenance schema is implemented; extraction resumed against the decode-status backlog.

- **Now (resumed 2026-06-09 — PR #638, verify merge)** — ABR rounds + income sets
  ingested game-natively (roundset-aware `btd6_round_composition`/`btd6_round_cash`);
  subtower mechanisms 7/7; buffs 15/38 confirmed (the rest are provably unconfirmable
  pre-cutover). **Next: the dedicated `--all` towers-cutover session (owner decisions
  Q-0066–Q-0069, router §29)** — game-native committed stats, Farm/Village **full**
  tier structures (attack-suppressed), per-tier beast names, name-guard joins, ~25
  value-pinned test updates.
  Status: [decode-status](btd6/btd6-gamedata-decode-status.md).
- **Built (2026-06-09, Q-0049 — PR #633, scoreboard Lane 5; verify merge)** — the
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
  Character overview (#610), and — built 2026-06-09 (verify the PR merged on live
  GitHub) — the audited **Workshop + durability** keystone (brainstorm §7.5; migration
  063, tuning = Q-0054) with the **mother-panel live overview** (§6.3). **Next Wave-1
  slices:** functional **structures** (Forge/Vault/Home — the remaining §7.5 sinks),
  the owner-approved **duels-tick-weapon/armor-wear** slice (Q-0054), then Wave 2's
  **game-XP service** (§7.4).
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
