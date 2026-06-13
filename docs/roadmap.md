# SuperBot — Implementation Roadmap

> **Status:** `living-ledger` — the one cross-area "what's planned, for which area, in
> what order" index. **Last updated:** 2026-06-12 (Q-0107 reconciliation pass).
>
> **▶ The live decade queue (next ~9 PRs):**
> [`planning/reconciliation-pass-2026-06-12.md`](planning/reconciliation-pass-2026-06-12.md)
> §4 — set by the first Q-0107 pass (hardening P0s + backup posture + the new Q-0108–Q-0112
> safety/community lane). That doc owns the queue; this page stays the per-area index.
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
>
> **▶ Production-readiness:** the seven per-subsystem readiness maps + the consolidated
> [**hardening roadmap**](planning/production-readiness/hardening-roadmap-2026-06-12.md)
> (P0 integrity → P1 correctness → P2 drift, with the gating owner Qs) are the
> risk-ranked "what's left to be production-ready" view across all subsystems. Index:
> [`planning/production-readiness/`](planning/production-readiness/README.md).
> **All gating decisions answered as of 2026-06-12 evening** (Q-0098/Q-0099/Q-0100 + Q-0097
> = operator-managed findings lifecycle); no hardening track waits on a decision. **Next
> implementation session (owner-picked): P0-1 —**
> [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md).

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
| **Now** | The **[band queue](planning/reconciliation-pass-2026-06-12-night.md)** (second Q-0107 pass): backup posture ✅ #769 and the **safety/community band (slots 4–6) ✅ COMPLETE** (#772 automod · #774 logging · #775 welcome+counters). Active Now = the **production-hardening P0 spine** ([hardening roadmap](planning/production-readiness/hardening-roadmap-2026-06-12.md) — **P0-3 settings convergence next**, then P0-4/P0-2, all owner-unblocked). The product lanes stay open as owner-steered alternates: **mining** (V-16 phase 2 — gated on the owner's PNG pack; or structures §7.5) · **BTD6** (decode ⭐ item 3 demand-driven; owner live spot-check owed) · **AI** (§7 workflow families post-prod-check; BUG-0009 open in the [bug book](health/bug-book.md)) |
| **Next** | Safety/community lane remainder (image moderation · security tiers 1+2 · NL event scheduler — all plan-first, see the lane section) · P1-1 versioned AI eval/smoke matrix · myprofile PR A ([plan](planning/myprofile-foundation-plan-2026-06-10.md), turn-key) · help home/navigation plan (editor-UI gate cleared via #677/#679) · V-14 harvest structuring ([dossier](ideas/competitive-teardown-2026-06-10.md); ecosystem-#2 = fishing, owner ratification pending) · the 2026-06-10 [consolidated implementation plan](planning/consolidated-implementation-plan-2026-06-10.md) is **FULLY EXECUTED** (`historical`; [EOD verification](audits/past-day-verification-2026-06-10.md)) |
| **Later** | P1-2 health findings lifecycle (Q-0097 answered 2026-06-12 — operator-managed; ready when queued) · continuation dispatch = the **Routine seam** (Stage 0's GH Action folded in — Q-0115; activates on Routine wired + calibrated) · BTD6 post-cutover decode backlog · server-management **PR13 AI generation layer** + deferred governance setup (gated — Q-0008/Q-0011) · broad AI expansion beyond the active lanes (gated) · media channel-summary (now shaped by Q-0099) · games deferred follow-ups |
| **Someday** | The ideas backlog — not approved (see [§Someday](#someday--ideas-not-approved--capture-only)) |

> **Standing posture (router §35, 2026-06-10):** the end-state is a **public
> bot** (Q-0080 — every new plan inherits stranger-grade onboarding/abuse/cost
> filters) · the flagship RPG is **solo core + co-op overlays** (Q-0081) · AI
> spend = **owner-set hard ceiling, visible graceful degrade** (Q-0082 — **interim
> €30/month set 2026-06-12**; refine after first prod measurements) · the
> workflow converges toward **full self-driving — explicitly not near-term**
> (Q-0083).
>
> **Session queue → superseded 2026-06-12.** The 2026-06-10 recommended queue completed
> items 1 + 6 (untested-surface checklist **#731**/**#732** · the V-16 gear slice **#702**);
> its remainder (Stage 0 · backup posture · help home/navigation · V-14 structuring) and
> the build-ready alternates (myprofile PR A · survival **P0 balance-sim harness, Q-0087** ·
> duel-XP quick-win · **gap items 2/4/5** — [gap file](ideas/gap-analysis-2026-06-11.md))
> are folded into the **[decade queue](planning/reconciliation-pass-2026-06-12.md)** §4 and
> its "deliberately not in this decade" list. One queue home — don't restate it here.

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

### 🚨 Server safety & community platform — **first band shipped; remainder Next**

**New lane (2026-06-12):** the owner uploaded competitor/safety research (#739 →
[server-safety-and-automod](ideas/server-safety-and-automod-2026-06-12.md) ·
[community-platform-features](ideas/community-platform-features-2026-06-12.md)) and answered
the five scope questions same day (**Q-0108–Q-0112**, #740 — decisions recorded in the
router + both idea docs' routing tables). The lane's entry doc is the
**[safety/community family plan](planning/safety-community-family-plan-2026-06-13.md)**
(2026-06-13, band slot 4 — shared architecture + sliced build order, citing
`ux/pattern-library.md` pattern_ids; **automod v1 shipped in the same PR**). UI/attachment
numbers: [discord-platform-limits](operations/discord-platform-limits.md).

- **Shipped (band slots 4–6, 2026-06-13) ✅** — the family plan (slot 4) +
  **automod v1** (#772, Q-0108 — all four rule types through `moderation_service`) →
  **server event logging v1** (#774, Q-0109 — edits/deletes · join/leave · role changes,
  **extending the existing `services/server_logging.py` seam**) → **welcome v1 + server
  counters** (#775, Q-0110 — greetings/farewell/entry-role + statdock channels; two
  hub-less new subsystems, embed-first). The first band is COMPLETE.
- **Next (after the hardening spine)** — **image moderation** (Q-0108 — OpenAI
  `omni-moderation-latest` only; paid tiers declined) · **security service tiers 1+2**
  (Q-0111 — raid detection + account-age filter; tiers 3+4 **declined**, GDPR) · **welcome
  phase 2** (PIL image cards — the `render_welcome_card` prototype already exists, so this
  is a small follow-up on the stable embed-first v1) · the **NL event scheduler** (Q-0112,
  own AI-cost design under the Q-0082 ceiling). A read-only **operator landing** for the
  whole lane is captured as an idea ([safety-community-operator-landing](ideas/safety-community-operator-landing-2026-06-13.md)).
- **Later (plan-first, AI cost design)** — **NL event scheduler** (Q-0112 — NL time parsing
  from day one, metered under the Q-0082 ceiling; availability polls proposed day-one;
  check existing scheduler infra before designing reminders).
- **Later** — social feed notifications, YouTube-first (Q-0041 direction approved; the
  summarization enrichment layer rides the Q-0082 ceiling). Other sources + custom
  commands: Someday (see below).

### ⚙️ Settings / bindings / provisioning — **Next**

Folio: [settings-bindings-provisioning](subsystems/settings-bindings-provisioning.md)

- **Next** — **setup `/myprofile` foundation (wizard plan PR4)** — **plan ready
  2026-06-10:** [myprofile-foundation-plan](planning/myprofile-foundation-plan-2026-06-10.md)
  (PR A read-only card, zero writes · PR B the participation pipeline's first
  UI consumer · PR C onboarding **gated** on an owner decision; Q-0080
  stranger-grade envelope applied). The finalization tranche (PR1–PR3) was
  verified already shipped via #435 (DT09, PR #672).
- **Next** — settings coverage: pick a *verified* inconsistency from the
  [consistency ledger](health/platform-consistency-ledger.md); the three-lane model is
  [settings-customization-roadmap](setup-platform/settings-customization-roadmap.md).
- **Shipped 2026-06-09 (#640, scoreboard Lane 7)** — **settings audit Phases 0+1**:
  actionable-groups-only hub (`actionable_settings_groups()`, 11 live groups) +
  paginated >25-option reachability + per-guild routing availability markers.
  Sequencing home: [settings audit §11](planning/settings-cog-centralization-audit-2026-06-09.md).
- **Phase 2 core merged 2026-06-10 (#654**, consolidated-plan Batch 4):
  real domain-panel registrations (`DomainPanelSpec`) replaced the Phase 1
  `DOMAIN_CONFIG_SUBSYSTEMS` seam (+ DT06 coverage invariant); **Q-0064** BTD6
  announcement-channel binding + CT guided flow landed with it. Open tail:
  pointer-migration classification rows; then **Phase 3** duplicate-path
  convergence (**Q-0063** converge-gradually — router §27).
- **Phase 1 complete** — [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md):
  P0 + P1A + P1B + P1C shipped (#588/#589/#591/#592/#632 + the 2026-06-10
  Batch 5 subpanels, **merged #656**; Q-0032 hub-buttons-only honored). **P2 next** (own planning first). *(Horizon corrected
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
  — **Batches 1–8 all executed + merged 2026-06-10**; **#671** added RS07 +
  Batch 9's RS08 + the Help-Preview Tier-2 fix, and **#672** completed the
  Batch 4 pointer tail (proof-channel declaration) + the Batch 10 selections;
  Batch 9 completed in **#681** (RS05 publish-accepted contract + observability ·
  RS10 economy family onto BaseView) and the Help overlay editor UI executed
  same day (PR A #677 + PR B #679) — **the plan is fully executed** (re-badged
  `historical`); remaining work is plan-first/gated, routed from
  `docs/current-state.md` ▶.
- **Next** — **interface completion**: the live sequence is
  [mother-hub-map](building-roadmap/mother-hub-map.md) (S1–S13).
  [interface-completion-roadmap](building-roadmap/interface-completion-roadmap.md) is the
  arc; [loose-ends-audit](planning/loose-ends-audit-roadmap.md) is the source audit (its L1–L6
  sequence is superseded by mother-hub).
- **Later (planning target — Q-0078)** — the **4-button Help Home + panel
  navigation doctrine** from the owner's vision statement
  ([superbot-vision](ideas/superbot-vision-2026-06-10.md) V-02/V-03 + AG-01/AG-03):
  Play · Server & Info · My Stuff · Manage top level (layout decided Q-0078),
  update-in-place + mother/help links on every panel, one-active-panel + summon,
  and the ≤3-clicks reachability invariant (navigation depth — per-panel
  button caps rejected, Q-0079). Owner-picked as a next planning
  target; its sequencing gate — the Help overlay editor UI — **cleared 2026-06-10**
  (the editor shipped as **#677 + #679**), so it is ready to structure into its own
  plan on the same projection seam (capture-doc T-4) before building.
- **SHIPPED (2026-06-12, owner-steered same-day build)** — the **UX Lab
  interface-gallery cog** (`!uxlab`, admin-gated, zero-write): PRs **#758/#760/#762**
  — 64 registered patterns across 7 wings + a 10-probe limit bench + clickable
  **mockups of the whole Q-0108–Q-0112 lane** (review those features by clicking
  before the family plan is written) + ⚖️ compare-with-verdicts. The durable design
  vocabulary is **[ux/pattern-library.md](ux/pattern-library.md)** (registry-generated,
  doc-pinned) — future panel plans reference its `pattern_id`s instead of re-describing
  layouts. CV2 adoption for real panels stays a future ADR on the lab's evidence
  ([plan](planning/ux-lab-interface-gallery-plan-2026-06-12.md), now `historical`).
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
- **Later (UX debt — owner-requested)** — [AI panel in-place navigation](ideas/ai-panel-inplace-navigation-2026-06-11.md):
  migrate the `views/ai/` settings family off per-click ephemeral messages + the blanket
  raw-`discord.ui.View` yaml exemption onto the rest-of-bot in-place **HubView** pattern
  (V-02 navigation doctrine), and centralize the seven scattered subpanels. Clear
  direction + a source-confirmed scope sketch in the idea file; wants its own planning
  session before code.

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
  In parallel, **#653 (wave 1)** decoded thorn rings + 4-x-x sentries + the
  **banana economy** (bananaValue/bank capacity+interest as specials) —
  reconciled at the merge.
- **Answerability tail (2026-06-10)** — items 5+6d in **#658** (deterministic
  Ask parity · Pro views render Effects/Minions · Striker fraction fix);
  items **6a–c + the Navarch "no coins" routing fix in #662** (the live wrong
  answer was **routing, not data**: name-resolution miss → 0 facts, the
  cap-truncated income sentence, no paragon income/effect grounding leg —
  fixed across grounding/menus/AI tool, + minion-name grounding, the Pouākai
  diacritic tokenizer fix, honest dataset source labels).
  **Item 7 slice 1 shipped same day (#668)** — zero-fact questions now ground
  the conversation's entity via labeled `[btd6_carryover]` facts, + the
  zero-fact sweep fixes (ranking rosters · bare distinctive shorthand); the
  [conversation-carryover grounding plan](planning/btd6-conversation-grounding-plan-2026-06-10.md)
  carries the remaining unapproved tail (eval-harness pin · wider window).
  **Next:** decode-status ⭐ item 3 (buff/zone tail — demand-driven), the
  maintainer's live spot-check (item 4). Triage tool (#666):
  `scripts/btd6_probe.py "<exact user text>"`.
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

- **Now (next implementation session, owner-picked 2026-06-12)** — **P0-1 wager
  money-safety**: [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md)
  — one audited `game_wager_workflow` composing the existing `economy_service` atomic
  primitives (escrow→settle/refund, idempotent payouts), failure-injection tests, AST fence.
- **Now (active lane)** — the **mining character platform** (from the
  [mining brainstorm](ideas/mining_exploration_brainstorm.md) §7 vision). Wave-1 chain
  shipped #606–#610 + #624 (explore wiring + equipment seam, persistent Descent, combat
  gear → deathmatch, market loop, Character overview, Workshop + durability keystone).
  **The 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed as a 4-PR
  stack — all merged, landed on `main` via #667: #661 → #663 → #664 → #665** — the Q-0071/Q-0072 write
  boundary is **complete** (every mining write through `services/mining_workflow.py`,
  one transaction per op, AST-fenced; pure domain in `utils/mining/`), recipes are
  catalog-reconciled under an alignment lint (Q-0075), the **shared game-XP track**
  exists (migrations 065/066: awards atomic with their actions, daily soft cap, shared
  derived level, `gamexp`/`crafting` leaderboards, depth records), the **deeper
  ladders** land (gold/diamond tiers — the diamond lantern finally unlocks MAGMA),
  the Gear panel / Recipe browser / fuzzy names / `!fastmine` modernize the old UX,
  **duels tick weapon/armor wear (Q-0054 closed)**, and the §7.6 PIL inventory +
  stat cards ship (Q-0076). **Next slice: functional structures (§7.5
  Forge/Vault/Home sinks)**, then the **§7.4 capped skill tree** (its `game_xp`
  substrate + `EffectiveStats` merge point are now in place).
- **Later** — bounded deferred actionability follow-ups (inventory architecture,
  leaderboards, bot-duel stats, shared back-button adoption) from the completed
  [actionability roadmap](archive/games-actionability-roadmap.md). Low priority; pick one bounded
  slice.
- **Later** — [**Pet companions**](planning/pets-companions-plan-2026-06-09.md): nameable
  pets from exploration drops + a care-loop coin/ore sink + tiny non-P2W perks; the
  owner's ⭐ pick from the 2026-06-09 fun/ease brainstorm (Q-0053). Gate: Wave-1
  keystone slices (Workshop + durability) + balance review + owner promotion.
  **Amended 2026-06-10 (Q-0078 "both paths"):** quest-rescue joins as the
  rare-species path once the quest engine exists; party cap grows 1→3 later.
- **Later** — [**RPG survival & difficulty design**](planning/rpg-survival-difficulty-design-2026-06-10.md):
  difficulty modes (Easy ≡ today's game, byte-identical) + energy/health/hunger +
  fishing/cooking + biome×difficulty encounters + hard-mode death-as-rescue; from the
  owner's vision statement ([superbot-vision](ideas/superbot-vision-2026-06-10.md)
  V-05…V-08), picked as a planning target in **Q-0078** (one-way-ascent switching
  decided there). Gates: sequencing behind §7.5 structures / §7.4 skill tree + the
  owner numbers-confirm (plan G1/G2). Its D6 (duel XP both sides) is a standalone
  quick-win.

### 📺 Media / YouTube — **Later** (needs an approved plan)

Folio: [media-youtube](subsystems/media-youtube.md) · **Gate:** ADR-007 + a
privacy/provenance/moderation review before any public surface.

- **Later** — a channel-summary / content-status feature would need a bounded read-only
  first slice and an explicit privacy/security review. No public media command ships today.
- **Now (hardening P0-2, unblocked)** — retention/data-minimization per **Q-0099** (bounded
  projection + scheduled purge) — in the [decade queue](planning/reconciliation-pass-2026-06-12.md).

### 🤝 Agent ecosystem / workflow — standing lane

The workflow substrate is first-class work (CLAUDE.md working agreement); this section maps
its *plans* so they're sequenced like any other area. Ops shelf:
[hooks & plugins](operations/claude-code-hooks-and-plugins.md) ·
[MCP servers](operations/mcp-servers.md) ·
[Hermes control plane](operations/hermes-control-plane.md) +
[operating prompt](operations/hermes-operating-prompt.md).

- **Standing** — the **Q-0107 reconciliation cadence** (docs-only pass each time merged PRs
  cross a multiple of **20** (#753); fired automatically by the `reconcile`-issue trigger;
  current pass: [2026-06-12 night](planning/reconciliation-pass-2026-06-12-night.md))
  · the session enders (Q-0089 idea · Q-0102 prev-session review · Q-0104 closing audit).
- **Later — continuation dispatch = the Routine seam (Q-0115, 2026-06-12):** Stage 0's
  separate `workflow_dispatch` GH Action is **folded into the #742 Routine bridge** — one
  dispatch mechanism for Hermes-fired, one-click, and later scheduled runs. The
  bounded-session protocol ([ai-project-workflow §10](owner/ai-project-workflow.md), Q-0088)
  activates once the Routine is **wired + calibrated** (the bridge runbook's ⬜ steps).
- **Open decision** — **Q-0096 remainder**: Context7 MCP adopted (#737); Postgres-MCP +
  pyright-LSP still open ([plugins evaluation](ideas/claude-code-plugins-evaluation-2026-06-12.md)).
- **Now (seams wired 2026-06-12 — #742, Q-0113/Q-0114, parallel session)** — the
  [autonomous self-improvement loop](ideas/autonomous-improvement-loop-vision-2026-06-12.md)'s
  three repo-side seams: the Hermes `superbot-review` skill (independent non-Claude critique) ·
  `scripts/check_phase_gate.py` (fix-phase vs. invent-phase; invent requires zero OPEN bugs +
  zero Not-Done readiness rows — currently **FIX-PHASE**) · the
  [Hermes → Claude dispatch bridge](ideas/hermes-claude-dispatch-bridge-2026-06-12.md)
  (`superbot-dispatch` + runbook). Gates: routine PRs self-merge on green CI (**Q-0113**);
  human approve/deny applies to **agent-originated features only**, originated in
  invent-phase only (**Q-0114**).
- **LIVE (2026-06-12, the #753–#761 wiring arc — parallel lane):** the loop now *runs* —
  issue-triggered reconciliation (#753) · routine prompts as loop turns (#754) · the
  **Q-0117 Hermes independent-review merge gate** for substantial executor steps (#756) ·
  the **executor-nightly cron** (#759) · free-form `/bugreport` dispatch (#761); the
  HermesCog Discord entry point is in flight (**#757**, its own lane). Posture: **Q-0105
  calibration** — verify runs against ground truth before trusting unattended (the night
  reconciliation pass's checker-regex catch is calibration working).
- **Someday (vision, not approved)** — the
  [portable agent-memory package](ideas/portable-agent-memory-package-2026-06-12.md)
  (owner-shaped strategic direction).

---

## Product-growth roadmap drafts — **Later / Someday** (not approved)

- **Later** — [social/community/progression](planning/social-community-progression-roadmap-2026-06-08.md): guilds, achievements, profiles, leaderboards, and notifications; gate: privacy/new-owner decision (Q-0038 answered 2026-06-09: server-scoped clans).
- **Later** — [economy/marketplace/rewards](planning/economy-marketplace-rewards-roadmap-2026-06-08.md): trade, rewards, sinks, onboarding, and crafting; gate: economy-health review + chance-reward review (Q-0039 answered 2026-06-09: donation = cosmetic-only, no bot-side billing).
- **Later** — [games/mining/idle growth](planning/games-mining-idle-roadmap-2026-06-08.md): poker, blackjack follow-ups, mining depth/co-op/idle; gate: ADR-002 + balance/ownership review.
- **Later (needs source verification)** — **mining UX polish** (from [voice-mode capture](ideas/voice-mode-planning-capture-2026-06-11.md) §4): crafting category filters + craft-and-equip shortcut + inventory/gear display consistency. Identified as the strongest near-term candidates from the 2026-06-11 brainstorm; gate: source verification of existing crafting/equipment flow ownership before planning.
- **Later (fully gated)** — [AI product-extension routing](ai/ai-product-extension-routing-2026-06-08.md): DM/events/NL/tool ideas routed under the authoritative AI roadmap; gate: all AI readiness/orchestration/action decisions (Q-0040 answered 2026-06-09: bounded-menu DM posture; building still needs its plan + per-exposure lift).
- **Later (gated)** — [BTD6 product-extension routing](btd6/btd6-product-extension-routing-2026-06-08.md): rules/trivia, challenges, runs, leaderboards; gate: ADR-006/provenance/source-health.
- **Existing plans** — [server-management/setup/access/routine extension routing](planning/server-management-extension-routing-2026-06-08.md): announcements, anti-spam, availability, explanations, analytics; gate: authoritative trackers and privacy/AI decisions.
- **Someday / Later** — [integrations/media/voice/website](planning/integrations-media-voice-website-roadmap-2026-06-08.md): provider alerts, activity, voice, and web projection; gate: privacy/security/moderation review (Q-0041/Q-0042 answered 2026-06-09: YouTube-first posture; staged Someday website).
- **Later** — [UX/discoverability/mobile-first](planning/ux-discoverability-mobile-roadmap-2026-06-08.md): help, changelog, copy, and mobile conformance through existing UI standards; gate: authoritative interface sequencing and copy/release-manifest decisions.
- **Next (editor UI only)** — [Help cog customization audit and roadmap](planning/help-cog-customization-audit-2026-06-09.md): the **seam (#657) and the HLP-3 overlay store/mutation/render integration (#659) both merged 2026-06-10** (audit Phases 1+2+3); the **editor UI executed 2026-06-10** ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → **PR A #677** editor · **PR B #679** Q-0059 Home builder, mandatory preview, migration 067); the remaining piece is Phase 4 command/panel-action records (Q-0057 rider: no ordering until stable action identities). *(The #656 Help Preview migration onto the seam — [EOD verification §4](audits/past-day-verification-2026-06-10.md)'s Tier-2 finding — shipped in PR #671, 2026-06-10.)*
- Routing ledger: [idea-to-roadmap inventory](planning/idea-roadmap-inventory-2026-06-08.md).

## Someday / ideas (NOT approved — capture only)

> These are **not** queued work — captured so the picture is complete. Promoting one
> requires the gates in [`ideas/README.md`](ideas/README.md). Do not treat anything here as
> a priority.

- [superbot-vision-2026-06-10](ideas/superbot-vision-2026-06-10.md) — the maintainer's
  written product-vision statement + agent response: 2-minute setup KPI, panel
  navigation doctrine, 4-button help home, per-user preferences, RPG
  difficulty/survival/energy, story pets, AI-as-panel-orchestrator (inside the Q-0040
  posture); routing ledger inside. **Owner picks recorded same day (Q-0078):**
  one-way-ascent difficulty · both pet paths · the 4-button layout · next planning
  targets = RPG survival design (structured →
  [plan](planning/rpg-survival-difficulty-design-2026-06-10.md)) + help home/navigation.
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
- **Custom commands** (operator-defined trigger→template responses, sandboxed) + **social
  feeds beyond YouTube** (Twitch/RSS/Reddit/…) — captured in
  [community-platform-features](ideas/community-platform-features-2026-06-12.md) §§2/4;
  groom toward Later once the safety/community lane's first slices land.

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
