# docs/planning — the plan index (read this before reading any plan)

> **Status:** `living-ledger` — the durable map of `docs/planning/`. **Last updated:** 2026-06-19.
> Source code + merged PRs win over this file; `docs/current-state.md` owns *what is live right now*;
> [`docs/roadmap.md`](../roadmap.md) owns *cross-area sequencing*. **This page owns one thing: which
> plan files are ACTIVE vs. HISTORICAL, and where each active plan is homed.**

## Why this exists

`docs/planning/` holds ~85 files. Most are **not** the current plan — they are shipped-plan records,
reconciliation snapshots, sim-pinned number files, and superseded roadmaps kept for history. A new
agent that opens the folder and starts reading hits stale/shipped plans before reaching live work.
This index fixes that: **read the Active section, ignore the rest unless you're chasing history.**

**The badge is the authority signal.** Every doc carries a `> **Status:**` badge (`plan` =
buildable spec · `historical` = superseded, do not act · `reference` = stable companion · `audit` =
dated snapshot). When a plan's work ships, it is rebadged `historical` in place (links stay intact) and
moves from "Active" to "Historical" below — **it is never deleted**, so provenance survives.

> **One-fact-one-home:** this page restates nothing — it links the authoritative plan + its folio.
> A plan's own body, the folio, and `current-state.md` win over any one-line summary here.

---

## Active plans — by sector

The buildable / in-flight / current-spec set. Each homes to **exactly one** of the five planning
sectors ([`repo-sector-map.md`](../repo-sector-map.md)); the live `Now/Next/Later` horizons are in
[`roadmap.md`](../roadmap.md). `gate` = what must clear before it is startable.

### S1 — Bot product

| Plan | Status / gate | Folio · related ideas |
|---|---|---|
| [consolidation-discoverability-audit-brief](consolidation-discoverability-audit-brief-2026-06-23.md) | **✅ COMPLETE (2026-06-23)** — the full per-cog consolidation/discoverability audit: every command findable + buttonized (#1370), no loose ends / never-stranded nav (#1375/#1382/#1383), settings centralized (#1385), AI advisor finalized (#1386/#1389/#1390). Remaining = optional polish (setup-wizard section walk · card-engine migration · channel-deployed-component primitive). Kept for the rubric + provenance. | cross-cutting · `competitive-positioning-north-star` |
| [hub-child-rendering-and-placement](hub-child-rendering-and-placement-2026-06-23.md) | **▶ research session** (owner asked for a plan to research with a fresh session) — generalize hub child-button rendering so registered children always get a panel button (2 of 6 hubs auto-render today; the rest hardcode → the treasury #1344 gap), add a **panel-link CI guard**, and audit `cross_link_children` double-placement (mining/leaderboard/counting/chain) for placement coherence. 3 PRs; PR 3 is owner-taste-gated | help-surface / hub architecture |
| [fishing-open-world-expansion](fishing-open-world-expansion-plan-2026-06-18.md) | Phase 1 (fishing v1 + gear-switching) **▶ buildable**; the unified-loadout / value-cook-sell / minigame tail is **owner-design-gated (Q-0175)** | [games](../subsystems/games.md) · `mining_exploration_brainstorm` |
| [fishing-minigame-design](fishing-minigame-design-2026-06-22.md) | **▶ buildable** — sim-backed (`tools/sim/fishing_minigame_sim.py`) catch-loop design answering the Q-0175 mechanic question. **Owner decisions recorded (2026-06-22):** hybrid reel/reel-fight, missed reel = fish gets away, soft energy/cooldown pacing, bait later, shore-first. ~2.5 s window, 3–6 s bite, 4-knob rod ladder, deepwater-as-a-choice | [games](../subsystems/games.md) · fishing-open-world-expansion |
| [poketwo-musicbot-feature-mapping](poketwo-musicbot-feature-mapping-plan-2026-06-20.md) | maps the owner's Pokétwo/JMusicBot research report → repo lanes; net-new lanes (Wild Encounters · collection filters · quests · shiny) spec'd, **build sequence gated on Q-0186**; marketplace/premium-currency = gated/rejected, music → arch-review pack | [games](../subsystems/games.md) · `wild-encounters-activity-spawning` |
| [creature-game-design-and-sim](creature-game-design-and-sim-2026-06-20.md) | owner-directed creature **PvP** + a runnable playability simulator (`tools/game_sim/creature_battle_sim.py`, verdict PLAYABLE); decisions (original roster · level-normalized PvP · art) routed to **Q-0187** | [games](../subsystems/games.md) · `wild-encounters-activity-spawning` |
| [mining-hub-redesign](mining-hub-redesign-2026-06-15.md) | owner-picked Option A; **not yet built** (no hub-redesign commits) — ▶ startable | [games](../subsystems/games.md) · `voice-mode-planning-capture` |
| [myprofile-foundation](myprofile-foundation-plan-2026-06-10.md) | PR A/B shipped (#938/#940); only **PR C onboarding** remains, **owner-gated (Q-0147)** | [settings](../subsystems/settings-bindings-provisioning.md) |
| [settings-pointer-lane-convergence](settings-pointer-lane-convergence-plan-2026-06-13.md) | P0-3; families 1+2 done, **pointer retirement gated** | [settings](../subsystems/settings-bindings-provisioning.md) |
| [ai-panel-inplace-navigation](ai-panel-inplace-navigation-plan-2026-06-19.md) | **✅ SHIPPED (2026-06-23)** — fleet unit U1 (#1376) migrated all 17 `views/ai/` findings to in-place nav, unblocking the `edit_in_place` graduation (#1375); the AI-advisor generative half shipped as Accept/Deny/Edit (#1386/#1390). | [ai](../subsystems/ai.md) · `ai-panel-inplace-navigation` |
| [safety-community-family](safety-community-family-plan-2026-06-13.md) | lane entry doc; automod/logging/welcome **shipped** + image-mod #941 + security tiers 1+2 #929 **shipped 2026-06-18**; remainder = **NL event scheduler** (plan-first, Q-0112) | roadmap safety lane · `server-safety-and-automod`, `community-platform-features` |
| [reaction-roles-overhaul](reaction-roles-overhaul-plan-2026-06-21.md) | **largely SHIPPED** — PRs 1–6 merged (#1219/#1220/#1279), Carl-bot-mature (`reaction_role_service` + role-menu builder/view + migrations 078/079/081/089); **remainder = web builder Surface A** (owner-paced). See [current-state S1](../current-state/S1-bot.md). | [server-management](../subsystems/server-management.md) · `fun-and-ease-brainstorm` §B1, `community-platform-features` §4 |
| [starboard](starboard-plan-2026-06-21.md) | **SHIPPED** — PR 1 #1259 + PR 2 #1270 (`starboard_service` + config panel + migrations 083/084); Hall-of-Fame live. Any deferred §6 tail is owner-paced. | `fun-and-ease-brainstorm` §B1 · reaction-roles-overhaul §6 |
| [explore-hub-federated-world](explore-hub-federated-world-plan-2026-06-19.md) | **partially shipped** — top-level Explore *world* hub + world registry (PR 1 #1156) + cross-game world card (PR 3 #1160) shipped; **PR 2** (global/per-game XP split — `player_skills` PK migration + earning-model call) is **owner/runtime-gated** | [games](../subsystems/games.md) |
| [karma-reputation](karma-reputation-plan-2026-06-22.md) | **SHIPPED #1332** (PR 1+2 — `karma_service` + cog + leaderboard + migration 093; folio [`subsystems/karma.md`](../subsystems/karma.md)); **PR 3 (reaction-grant + karma-roles) owner-deferred.** Plan kept as design record. | community lane · `karma-reputation-system` |
| [giveaway-system](giveaway-system-plan-2026-06-23.md) | **owner-directed (competitive teardown of jagrosh's GiveawayBot), plan-first** — native giveaways that **beat** GiveawayBot: button entry + auto-end + reroll **plus** entry requirements, weighted/bonus entries, and auto-paid coin prizes (reuses the reaction/economy/scheduler seams). 2–3 PRs; PR 3 (recurring auto-payout) owner-gated; 4 design Qs | community lane · `giveaway-competitive-teardown` |
| [bot-migration-assistant](bot-migration-assistant-plan-2026-06-24.md) | **owner-directed (chat), plan-first** — the consolidation engine: a `bot_migration` setup section that detects the *other* bots in a server, maps each (curated app-id catalog → subsystem registry) to the SuperBot subsystems that replace it, stages the replacement through Final Review, then offers a **guarded per-bot kick**. Built on existing seams (setup section · guild snapshot · `moderation_service.kick`); the one hard constraint is no cross-bot command introspection → curated catalog + observable signals. 3 PRs (PR 1 detect-report read-only · PR 2 replicate · PR 3 retire owner-gated); 5 design Qs | setup / consolidation · `bot-migration-assistant`, V-14 `competitive-positioning-north-star` |
| [setup-wizard-restructure](setup-wizard-restructure-plan-2026-06-24.md) | **owner-directed (chat), plan-first** — fix the wizard the owner flagged P0 ("half the steps do nothing… too long… loses people"). Four design laws (one real action per step · zero jargon · bot auto-creates what a step needs · short linear button-only spine) → a 6-step essentials spine applied **per-step via the direct lane**, with diagnostics + long tail moved to an Extras menu + one "Check my setup" button. Sim-backed ([`tools/sim/setup_wizard_sim.py`](../../tools/sim/setup_wizard_sim.py): ~4%→~79% modelled finish). Full current→disposition table for all 18 sections + jargon rename table + a banned-jargon CI guard. 3 PRs (spine · extras+health · retire dead sections); 5 design Qs | [settings](../subsystems/settings-bindings-provisioning.md) · `cog-improvement-audit`, consolidation §3.5 |

### S2 — BTD6

| Plan | Status / gate | Folio · related ideas |
|---|---|---|
| [ai-btd6-answerability-roadmap](ai-btd6-answerability-roadmap-2026-06-09.md) | Phases 1–3 shipped; Phases 4/5 (settings UI · dashboard) **gated** on per-exposure asks | [btd6](../subsystems/btd6.md) |
| [ai-roadmap](ai-roadmap-2026-06-07.md) | the **AI-area authority** (Phase 0–11, planning-only); orchestration foundation shipped, §7 workflow families next | [ai](../subsystems/ai.md) · [btd6](../subsystems/btd6.md) · *referenced by `agent/index.yml`* |
| [project-moon-knowledge-domain](project-moon-knowledge-domain-plan-2026-06-21.md) | **owner-directed (Q-0192): full parity, all 3 Project Moon games** as a generalised `KnowledgeDomain` seam (BTD6 = instance #0). Program, not a 2–3-PR plan; **first slice = a proof-first minimal Limbus lore-Q&A vertical** ▶ buildable; 3 follow-up design Qs routed | [btd6](../subsystems/btd6.md) · [ai](../subsystems/ai.md) · `project-moon-wiki-knowledge-domain` |

### S3 — AI-Memory system (the mechanism)

| Plan | Status / gate | Related ideas |
|---|---|---|
| [repo-consistency-linter](repo-consistency-linter-plan-2026-06-17.md) | active buildable lane (Q-0170); **all 4 rules graduated to error** — rules 2/3/4 (#1094) + `edit_in_place` (#1375, ultracode consolidation fleet cleared the backlog to 0) | `repo-consistency-linter` |
| [codex-review-integration](codex-review-integration-plan-2026-06-17.md) | partially wired (CI posts @codex on card flip); Hermes-timer + routine-fix-first remain | `codex-automated-pr-review` |
| [portable-substrate-kit-extraction](portable-substrate-kit-extraction-2026-06-13.md) | owner-approved OSS arc; in-repo layers shipped, **external package not yet extracted** — **owner-action** (demoted from the plannable queue after its fourth band-carry) | `portable-agent-memory-package`, `autonomous-improvement-loop-vision`. Review companion: [portable-agent-substrate-revision](portable-agent-substrate-revision-2026-06-13.md) |

### S4 — Documentation system (the content)

| Plan | Status / gate | Related ideas |
|---|---|---|
| [procedures-to-skills-conversion](procedures-to-skills-conversion-plan-2026-06-17.md) | relocate ~25% of always-loaded `CLAUDE.md` into on-demand skills; **batch 1 shipped (#1029/#1093), batches 2–4 next** | `agent-tooling-automation-shortlist` |
| [orientation-cost-reduction](orientation-cost-reduction-plan-2026-06-30.md) | owner-directed (in-chat, 2026-06-30); compresses CLAUDE.md's "Working agreement" narrative density (the section procedures-to-skills' safety list protects from relocation) **and** executes the overdue Q-0210 router-archive mechanism (130/217 router blocks unclassified; archive unused 2 reconciliation passes after being decided) | — |
| [memory-retention-and-context-economy](memory-retention-and-context-economy-plan-2026-07-02.md) | **owner-directed (in-chat brainstorm, 2026-07-02, PR #1643)** — the retention/deletion policy + hard caps the orientation plan deliberately leaves open: per-class delete/archive/tombstone windows (session logs · historical plans · ideas · ledger tails), sim-derived numbers ([`tools/sim/retention_policy_sim.py`](../../tools/sim/retention_policy_sim.py): ~70% lower context cost, corpus bounded, zero modeled retrieval loss), enforced by a `check_retention.py` checker+actuator. 3 PRs, ▶ implementation-ready; exports to the substrate-kit as the context-economy engine | `orientation-doc-linecap-guard` · [orientation-cost-reduction](orientation-cost-reduction-plan-2026-06-30.md) (companion) |
| [repo-structure-improvement](repo-structure-improvement-plan-2026-06-19.md) | governance baseline shipped (#1064/#1082); remaining items buildable | `governance-files-presence-guard` |
| [extension-taxonomy-crosswalk](extension-taxonomy-crosswalk-plan-2026-06-16.md) | crosswalk PR1 **shipped #958**; the thin-atlas **PR2** is the live remainder | `architecture-atlas-and-structure-review` |
| [ultracode-fleet](ultracode-fleet-plan-2026-06-19.md) | parallel-build fleet coordination brief; Wave A shipped, Wave B in-flight (near-consumed) | — |
| [consolidation-fleet-plan](consolidation-fleet-plan-2026-06-23.md) | **✅ EXECUTED (2026-06-23) — historical** — the ultracode run that drove the audit: coordinator #1375 + workers U1 #1376 / U2 #1377 / U3 #1378; settings guard shipped #1385. Kept for the parallel-run model + unit roster. | [consolidation brief](consolidation-discoverability-audit-brief-2026-06-23.md) |

### S5 — Operations / control-plane

| Plan | Status / gate | Related ideas |
|---|---|---|
| [web-tier-centralization-proposal](web-tier-centralization-proposal-2026-06-19.md) | web-CI matrix consolidation (`dashboard-ci` + `botsite-ci` → one matrix); **owner-greenlight gated** | tracked in [website-split-next-steps §2a](../operations/website-split-next-steps-2026-06-19.md) |
| [botsite-react-spa-migration](botsite-react-spa-migration-plan-2026-06-20.md) | make the live bot-site **be** the `design-system/` React app so Claude Design edits land with **no porting** (2–3 PRs); **owner-decision gated** (build-in-CI vs Railway-build; cutover timing) | follow-up to PR #1196 · [website-explained](../owner/website-explained.md) · `design-system/README` |
| [loop-health-gh-fallback](loop-health-gh-fallback-plan-2026-06-20.md) | 1 PR; **ungated, self-merge on green**; `urllib` REST fallback so `check_loop_health.py` verifies the ROUTINE_PAT row in-container (Q-0135) instead of SKIPping | `loop-health-gh-unavailable-fallback` |
| [voice-music-architecture-review](voice-music-architecture-review-2026-06-20.md) | the **Q-0041-required** voice/music decision pack (legal · infra · architecture fit · permissions · cost); **no playback code** — owner makes the go/no-go + legal-lane call to lift the gate | tracked under Q-0041 · `voice-mode-planning-capture` |

### Dashboard / control-API / website — the cross-cutting initiative

The project's **dominant active thread** spans S1 (user surface) + S5 (control-plane) and was previously
unrouted from the roadmap/folios. It is homed here. **Live-now status: `docs/current-state.md` ▶
Next action.** Remaining website work has its own durable handoff:
**[`operations/website-split-next-steps-2026-06-19.md`](../operations/website-split-next-steps-2026-06-19.md)**.

| Plan | Status / gate |
|---|---|
| [developer-dashboard-plan](developer-dashboard-plan.md) | **LIVE in production**; read-only surfaces all shipped; Phases 2/4 + Phase 3b value-mgmt **owner/creds-gated** |
| [dashboard-vision-finalized-state](dashboard-vision-finalized-state.md) | the **north-star** convergence doc (write side activated) |
| [dashboard-live-editor-plan](dashboard-live-editor-plan.md) | live help/panel editor; foundation shipped, **write side owner-paced** (control-API + OAuth) |
| [manifest-spine-execution-plan](manifest-spine-execution-plan-2026-06-17.md) | owner-approved "Build it" (Q-0162); panel-layout editor PR4 **owner-paced** (control-API write side) |
| [owner-review-inbox-plan](owner-review-inbox-plan-2026-06-17.md) | Phase 1 shipped (#1091 `/reviews`); Phases 2–3 owner-paced |
| [website-two-site-split-plan](website-two-site-split-plan-2026-06-19.md) | v1 build **code-complete + reviewed** (#1109–#1123); remaining = rollout + the control-API security-review-gated slices → tracked in the next-steps handoff |

### Fresh from-scratch rebuild — cross-cutting planning initiative

Owner-directed **planning** thread (not yet an approved build) for a from-scratch SuperBot rebuild
"designed as one picture," with the current repo as a frozen reference and the substrate-kit finished
first as its foundation. **Rebuild go/no-go stays owner-gated** (after the Fable design + owner review).
The source-grounded discovery evidence — 4 Codex maps, verified against shipped source per Q-0120
(48/59 load-bearing claims confirmed, the corrections binding) — is folded into one artifact:
[`analysis/rebuild-discovery/codex-preserve-map-synthesis`](../analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md).

| Plan | Status / gate |
|---|---|
| [rebuild-design-spec](rebuild-design-spec-2026-07-02.md) | **the Phase-2 design spec — the owner-gate deliverable, ⏳ awaiting owner approval.** The "one picture": architecture + manifest grammar (simulable, S/A/O-classified) + central namespace + settings model (safe-default-ON) + data/backward-compat contract + control plane + build order. Produced by the Fable-5 judge panel (4 designs → judges → synthesis → Opus + GPT adversarial review); **rev. 2 (2026-07-02) folds in the owner's two external GPT review sessions** — now opens with a plain-language summary + TOC + glossary. **No Phase-3 new-repo code until the owner approves it** |
| [fresh-rebuild-strategy](fresh-rebuild-strategy-2026-07-02.md) | the **verified baseline + end-to-end order** (Phase 0→5 + gates); analysis-grade, **not an approved execution plan** |
| [rebuild-parallel-execution-plan](rebuild-parallel-execution-plan-2026-07-02.md) | the **schedule companion** to the design spec (which has no clock): grounds "how long?" in the measured agent-fleet velocity (~16 parallel lanes, ~20–40 PRs/day) → **~2 weeks active build, ~1.5-week hard floor**; separates the sequential kernel critical path from the parallel port fan-out; names the **two gates** (linchpin proof = *commit*; finished AI-memory system = *start the repo*) |
| [simulation-driven-design](simulation-driven-design-2026-07-02.md) | owner-directed **standing rule** — structure (grouping / ordering / layout) is discovered by simulation; the manifest is the search space |
| [rebuild-ultracode-handoff](rebuild-ultracode-handoff-2026-07-02.md) | **START-HERE launch pad** — paste-ready ultracode session prompts (harvest · finish substrate-kit · golden harness · Fable design) |
| [rebuild-stage1-global-review](rebuild-stage1-global-review-2026-07-03.md) | **Phase-A Stage-1 decisions log (owner-live, 2026-07-03, PR #1679)** — the S-1 engine/declaration/seam standard + S-2 ordering rule (Q-0219/Q-0220); full dependency-order audit (3 inversions dispositioned — welcome re-homed after the card engine); Gate-0 deltas D-1…D-6 (card engine · **new media-generation capability** Q-0221 · **3-phase container-first cutover** Q-0222 · substrate-kit pre-bootstrap gate + per-subsystem triage Q-0223); corrected kit state (~90–95%, 422 tests green). ▶ next: **Stage 2 — the subsystem walk** (decisions log §6 agenda) |
| [rebuild-conventions-invocation-authority](rebuild-conventions-invocation-authority-2026-07-03.md) | **Phase-A conventions-freeze decisions log (owner-live, 2026-07-03, PR #1680)** — the cross-cutting contracts the subsystem walk needs: command naming (shared-verb namespacing from the corpus + safe defaults, Q-0224); the **four-rung invocation ladder** (exact → fuzzy typo matcher → NL intent → NL orchestration; additive custom triggers, silent-on-no-match, Q-0225); **mod-actions-as-data** (resolves ModerationActionSpec → envelope, Q-0226); **one authority layer + bot-owner override** (Q-0227); and invocation-stack centralizations C-1…C-7 (Q-0228, owner-endorsed) |
| [rebuild-stage2-readiness-review](rebuild-stage2-readiness-review-2026-07-03.md) | **Phase-A Stage-2 readiness review (2026-07-03)** — verdict: `ready after Prompt B merge`; defines the exact subsystem-walk contract/template, normalized triage vocabulary, preconditions, non-negotiable rules, owner decisions, recommended parallel lane split, and Stage-2 stop conditions. |
| [rebuild-hub-navigation-presets](rebuild-hub-navigation-presets-2026-07-03.md) | **Phase-A hub/navigation/interface-presets decisions log (owner-live, 2026-07-03, PR #1684)** — one **unified help hub** with admin as a gated node + `!admin` direct-open (Q-0230); the **navigation contract** — Back+Home injected into every state, every node directly openable, **persistent restart-safe panels** (Q-0231); **per-guild interface presets** with live preview, improving + centralizing the existing (≥7×-fragmented) preset surface onto one primitive (Q-0232). Open: preset exclusion = hide-vs-disable |
| [rebuild-decision-log-consistency-review](rebuild-decision-log-consistency-review-2026-07-03.md) | **`audit` — Codex consistency review of the 2026-07-03 rebuild decision logs (PR #1696)** — verdict: mostly consistent but not Stage-2/Gate-0-safe without consolidation; conflict table (authority vocabulary · C-1 status · preset semantics …), missing-durable-home table, vocabulary-normalization tables, 10 owner questions. Dated snapshot: predates #1708/#1716 — reconcile rows against the Gate-0 packet before acting |
| [rebuild-critical-review-rubric](rebuild-critical-review-rubric-2026-07-03.md) | **the reusable review lens (owner-directed, 2026-07-03, PR #1685, Q-0233)** — ten finding-classes (dependency-order inversion · forgotten capability · thin step · stale un-anchored claim · fragmentation · under-generalization · missing standard · verification hole · UX-contract gap · naming/collision), each a probing question + the day's example + a mechanization tag. Run against every subsystem in the Stage-2 walk and every plan in Phase B; it *is* the adversarial-completeness checklist |
| [rebuild-foundational-mechanics-ultracode-brief](rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md) | **two paste-ready parallel ultracode prompts (owner-directed, 2026-07-03, PR #1688, Q-0236)** — session A (engine room: grammar/namespace/invocation/resolver/authority/mutation/composition/events/persistence/settings/kit) + session B (surface+proving: hub/nav/card+media/presets/help/response-grammar/rubric/oracle/layout-sim), disjoint scopes, shared method (find-now + research + pressure-test → adversarial-verify → completeness-loop → synthesize), rubric-scored issues ledgers. **Prepared, not launched** — owner sends them in parallel |
| [foundational-mechanics-ultracode-review](../analysis/rebuild-discovery/foundations/foundational-mechanics-ultracode-review-2026-07-03.md) | **`audit` — Codex adversarial review of the foundational-mechanics ultracode outputs (2026-07-03, PR #1697)** — Prompt A (runtime/logic) trust verdict **high** with 10 source-verified high-impact samples (resolver-already-ships · lock-before-drain · process-local scope locks · best-effort events · owner-override gaps · refund-before-drop); flags the 246-issue ledger as needing synthesis + the owner-gated queue as needing filtering. Dated snapshot: predates #1701/#1708/#1716 which consumed both foundations reports |
| [rebuild-foundational-design-opus-brief](rebuild-foundational-design-opus-brief-2026-07-03.md) | **paste-ready Opus-4.8 ultracode prompt for the overnight foundational-*design* session (owner-directed, 2026-07-03, PR #1705)** — designs the ~10 kernel functions that were AUDITED but never DESIGNED (compiler+snapshot linchpin · C-1 resolver · error envelope · C-2 draft pipeline · workflow engine · outbox · scheduler/state · K1 · authority · ops-kernel) to *buildable* depth, closes the 5 never-surfaced concerns (security/data-integrity/credentials/backup-DR-rollback/platform-governance), and harvests one question register. Grounded by a 13-agent per-function source map (Appendix). **EXECUTED → PR #1708** — delivered the 14 buildable specs + frozen shared vocabulary + seam-consistency matrix + retirement-coverage map (0 evaporations) + 31-row question register under [`design/`](../analysis/rebuild-discovery/foundations/design/README.md); feeds the Gate-0 grammar freeze (brief below). Companion to the two foundations audits + the Fable-5 judgment below |
| [rebuild-gate0-grammar-freeze-opus-brief](rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md) | **paste-ready Opus-4.8 ultracode prompt for the Gate-0 grammar-freeze + Phase-B L0 build-order session (owner-directed, 2026-07-04, PR #1713)** — the step after the design bridge (#1708): consolidates every pinned grammar-field addition from the 14 kernel specs into ONE ratifiable frozen grammar, builds the amendment registry, closes the pending cross-spec wiring, resolves the register (freeze the 19 mechanical defaults + an owner-decision packet for the 12 owner-only calls), designs the L-24 riders to depth, and sequences the Phase-B L0 build order. Grounded by the harvested [work-list companion](rebuild-gate0-worklist-2026-07-04.md). **Prepared, not launched** — feeds the owner's Gate-0 ratification sitting + the (deferred) new-repo Phase-B L0 build |
| [rebuild-gate0-worklist](rebuild-gate0-worklist-2026-07-04.md) | **`reference` — the grounded work-list for the Gate-0 brief above (2026-07-04, PR #1713)**: harvested from the 14 shipped design specs (Q-0120) — Part 1 the grammar fold list (87 primitives / 18 attach-points), Part 2 the register disposition (19 ratify-default / 12 owner-only), Part 3 the Phase-B L0 build order (16 steps). The Gate-0 session's start index |
| [rebuild-planning-sanity-review](rebuild-planning-sanity-review-2026-07-03.md) | **`audit` — Codex repo-grounded sanity review of the rebuild planning state (2026-07-03, PR #1695)** — gate/phase map verified from the repo (verdict: mostly clear, no blocking inconsistency), stale-claim table, and the gate-state-ledger / wording-normalization improvements. Dated snapshot: predates the design bridge #1708 + Gate-0 freeze #1716 |
| [rebuild-phase-a-final-review-fable5-brief](rebuild-phase-a-final-review-fable5-brief-2026-07-03.md) | **`historical` — the Fable-5 capstone-judgment launch brief (owner-directed, 2026-07-03, PR #1700)**; delivered [`final-judgment-fable5`](../analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md) (PR #1701): verdict **GO-with-amendments**, the reconciled master ledger L-1…L-25, re-prioritization, the 17 surviving gaps, and the tiered owner queue (7 Tier-1 answered → **Q-0237**) |
| [rebuild-linchpin-validation](rebuild-linchpin-validation-2026-07-02.md) | **the owner-gate EVIDENCE package (2026-07-02)** — both unproven linchpins built + measured: the **Phase-0.5 golden harness** ([`parity/`](../../parity/README.md), replay-deterministic, coverage measured in [`COVERAGE.md`](../../parity/COVERAGE.md)) and the **grammar-expressiveness spike** ([`tools/grammar_spike/`](../../tools/grammar_spike/RESULTS.md) — tier-1/2 fit 73% as-specced → **85% with six named grammar amendments**; operator band 97%). Verdict: **GO with the amendments folded into the design spec before K2** |
| [rebuild-verification-review](rebuild-verification-review-2026-07-03.md) | **`audit` — Codex verification-strategy review (2026-07-03, PR #1699)** — verdict: promising, not yet Phase-B-ready; ported-feature oracle (`parity/`) strong, new-feature "competitor benchmark + live co-test" too vague to scale; names 10 missing oracle/checker classes, rewrites 6 vague acceptance criteria, per-subsystem done-definition format, and the block-Phase-B / block-Phase-C checker lists. Dated snapshot: predates #1708/#1716 — fold unconsumed items into the Phase-B plan template |
| [railway-setup-plan](railway-setup-plan-2026-07-02.md) | **the runtime half of the control plane** (design-spec §6 is the GitHub half): verified Railway token-capability audit + as-is inventory + the new-project setup + the Phase-5 cutover choreography. **R-now hygiene executed 2026-07-02 under the Q-0213 automation grant** (watch paths ✅ · botsite healthcheck ✅ · $15 soft usage alert ✅ · wait-for-CI dropped per owner history · Railway backups plan-gated → monthly pg_dump tier instead); remaining: R6 restore drill ▶ |

### Horizon backlog drafts (Later / Someday — routed, not stale)

The 2026-06-08 product-growth roadmap drafts are **active as routed backlog** — each is wired into
[`roadmap.md`](../roadmap.md) as a Later/Someday horizon, not a buildable plan:
[economy-marketplace-rewards](economy-marketplace-rewards-roadmap-2026-06-08.md) ·
[games-mining-idle](games-mining-idle-roadmap-2026-06-08.md) ·
[social-community-progression](social-community-progression-roadmap-2026-06-08.md) ·
[integrations-media-voice-website](integrations-media-voice-website-roadmap-2026-06-08.md) ·
[ux-discoverability-mobile](ux-discoverability-mobile-roadmap-2026-06-08.md) ·
[server-management-extension-routing](server-management-extension-routing-2026-06-08.md) ·
[pets-companions](pets-companions-plan-2026-06-09.md) ·
[rpg-survival-difficulty-design](rpg-survival-difficulty-design-2026-06-10.md).

[superbot-ideas-lab-2026-06-05](superbot-ideas-lab-2026-06-05.md) is mostly advisory, but its **§2
operating decisions + §6 rejection ledger are binding** "do-not-propose" — read before proposing UX/feature ideas.

### Production-readiness (the risk-ranked tier — [index](production-readiness/README.md))

| Doc | Status |
|---|---|
| [hardening-roadmap](production-readiness/hardening-roadmap-2026-06-12.md) | the **live P-tier spine** (P0 ✅ · P1-1 offline/P1-2/P1-3 ✅ · open: absence-guard Layer B + live battery) |
| [btd6-production-readiness-map](production-readiness/btd6-production-readiness-map-2026-06-12.md) | **has unique open findings** — absence-claim Layer B, the BUG-0009 model-faithfulness class |
| [settings-bindings-provisioning-production-readiness-map](production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md) | marginal open — `moderation.mod_log` binding, governance role-pointer home (router **Q-0119**) |
| [p1-3-contract-invariants-disposition](production-readiness/p1-3-contract-invariants-disposition-2026-06-15.md) | closing record for §P1-3 (cited live by current-state) |

*The other five per-subsystem readiness maps (ai · games · health-diagnostics · media-youtube ·
server-management) are **superseded** — their blockers shipped; they are rebadged `historical` (see below).*

### Feature-completion (the completeness tier — [index](feature-completion/README.md))

The *feature/UX-completeness* axis (orthogonal to the risk-ranked tier above — Q-0209): per-feature
units scored `▢ → ◐ → ✔`, certified only on evidence + owner sign-off.

| Doc | Status |
|---|---|
| [feature-completion/README](feature-completion/README.md) | the system + the completion ledger of every S1 unit + the generated certified-% scoreboard |
| [rubric-game](feature-completion/rubric-game.md) · [rubric-server-function](feature-completion/rubric-server-function.md) | the two Definition-of-Complete checklists |
| [units/blackjack](feature-completion/units/blackjack.md) | the worked pilot certificate (◐ assessed) |

---

## Historical / superseded — kept for provenance, **do not act on these**

Everything in `docs/planning/` **not listed in "Active" above** is historical or a reference satellite.
Each carries a `historical` (or `reference`) badge and a banner pointing at its replacement. Grouped:

- **Executed plans (work shipped):** [mining-structures-skill-tree](mining-structures-skill-tree-plan-2026-06-14.md)
  (all slices shipped — Vault #884 · skill tree #891 · Forge #905 · Home/respec/titles #910/#912) ·
  [help-overlay-editor-ui](help-overlay-editor-ui-plan-2026-06-10.md) (#677/#679) ·
  [mining-wire-exploration](mining-wire-exploration-plan.md) (#606) ·
  [games-wager-money-safety](games-wager-money-safety-plan-2026-06-12.md) (#748) ·
  [moderation-dm-config](moderation-dm-config-plan-2026-06-17.md) (#1023) ·
  [ux-lab-interface-gallery](ux-lab-interface-gallery-plan-2026-06-12.md) (#758/#760/#762 → durable artifact `ux/pattern-library.md`) ·
  [server-management-pr14-hub](server-management-pr14-hub-plan.md) (#584) ·
  [games-economy-faucet-sink-diagnostic](games-economy-faucet-sink-diagnostic-plan-2026-06-15.md) (#1044) ·
  [p0-2-content-free-media-diagnostics](p0-2-content-free-media-diagnostics-plan-2026-06-14.md) (#1044).
- **Server-management initiative** (structurally complete through PR14; only the gated PR13 AI tail
  remains): the authoritative record is [server-management-status](server-management-status-2026-06-05.md)
  (`historical`, *referenced by `agent/index.yml`*); the
  [roadmap](server-management-roadmap-2026-06-05.md) + [implementation-plan](server-management-implementation-plan-2026-06-05.md)
  are superseded scope docs (the status tracker wins).
- **Completed area audits / mapping campaigns:** [help-cog-customization-audit](help-cog-customization-audit-2026-06-09.md) ·
  [settings-cog-centralization-audit](settings-cog-centralization-audit-2026-06-09.md) ·
  [adaptive-setup-access-routine-platform](adaptive-setup-access-routine-platform-2026-06-08.md) ·
  [platform-mapping-a-user-surface](platform-mapping-a-user-surface.md) ·
  [platform-mapping-b-admin-surface](platform-mapping-b-admin-surface.md) ·
  [platform-surface-mapping-standard](platform-surface-mapping-standard-2026-06-09.md) ·
  [untapped-runtime-services-workflows-map](untapped-runtime-services-workflows-map-2026-06-10.md) ·
  [untapped-docs-tests-verification-map](untapped-docs-tests-verification-map-2026-06-10.md) ·
  [btd6-conversation-grounding](btd6-conversation-grounding-plan-2026-06-10.md) (slice 1 #668; tail demand-driven).
- **Superseded routing / inventory docs:** [docs-restructure-brief](docs-restructure-brief-2026-06-08.md)
  (→ this README + [repo-structure-improvement](repo-structure-improvement-plan-2026-06-19.md)) ·
  [idea-roadmap-inventory](idea-roadmap-inventory-2026-06-08.md) (→ [ideas/README](../ideas/README.md)) ·
  [loose-ends-audit-roadmap](loose-ends-audit-roadmap.md) (→ `building-roadmap/mother-hub-map.md`) ·
  [next-session-sector-roadmap-mapping](next-session-sector-roadmap-mapping-2026-06-14.md) (#877 → the sectorized roadmap) ·
  [website-two-site-split-planning-brief](website-two-site-split-planning-brief-2026-06-19.md) (→ the plan it produced) ·
  [superbot-audit-consolidation](superbot-audit-consolidation-2026-06-05.md) (the 06-05 audit-burst reconciliation).
- **Multi-PR session execution records (already `historical`):**
  [consolidated-implementation-plan](consolidated-implementation-plan-2026-06-10.md) ·
  [consolidated-productive-session-plan](consolidated-productive-session-plan-2026-06-09.md) ·
  [multi-lane-execution-plan](multi-lane-execution-plan-2026-06-09.md).
- **Sim-pinned number records (`reference` satellites of the shipped mining features):**
  `forge-numbers` · `gear-set-numbers` · `home-numbers` · `respec-numbers` · `titles-numbers` —
  the source of truth is the `disbot/utils/mining/*` code + its tests; these pin the design numbers.
- **Superseded production-readiness maps:** `ai-` · `games-` · `health-diagnostics-` · `media-youtube-` ·
  `server-management-` (their blockers shipped; the live spine is `hardening-roadmap` above).
- **Reconciliation-pass snapshots:** the 30-PR cadence (Q-0107/Q-0134) writes one dated band snapshot.
  **Only the newest is live** — currently [reconciliation-pass-2026-06-19-band1110](reconciliation-pass-2026-06-19-band1110.md)
  (its §4 is the live next-band queue). **All earlier passes are `historical`** — read only for band history.

---

## Where current truth lives (not here)

| Question | Authoritative home |
|---|---|
| What is live right now? | [`docs/current-state.md`](../current-state.md) ▶ Next action + Recently-shipped |
| Cross-area sequencing / horizons? | [`docs/roadmap.md`](../roadmap.md) (by sector) |
| Per-area state, rules, next candidates? | the area's [`docs/subsystems/<area>.md`](../subsystems/README.md) folio |
| Remaining website work? | [`operations/website-split-next-steps-2026-06-19.md`](../operations/website-split-next-steps-2026-06-19.md) |
| Captured-but-unapproved ideas? | [`docs/ideas/README.md`](../ideas/README.md) |
| Retired snapshots (cartography, stability, 06-05 burst)? | [`docs/archive/README.md`](../archive/README.md) |

**Living-ledger audits that stay in `docs/audits/`** (not plans — companions to binding docs, still
updated): `helper-debt-inventory` · `mutation_boundary_audit` · `ui-view-adoption-audit` ·
`untested-surface-checklist` (script-coupled) · `direct-db-exception-ledger`. These are routed from
[`AGENT_ORIENTATION.md`](../AGENT_ORIENTATION.md) § "Living inventories"; the rest of `docs/audits/` is
dated `historical` snapshots.

## Adding / retiring a plan

- **New plan** → drop the file here with a `plan` badge, then **add one row to the right sector table
  above** + its folio's "Plans" list. A plan with no inbound link is invisible (and orphans
  `check_docs --strict` unless badged `historical`/`archive`).
- **Plan shipped/superseded** → rebadge it `historical` **in place** (keep the file + its inbound links),
  add a one-line banner to its replacement, and move its row from "Active" to "Historical" above.
- **Verify** after editing: `python3.10 scripts/check_docs.py --strict`.
