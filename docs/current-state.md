# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action — per-sector live queues (Q-0195, 2026-06-22):** the all-sector callout that used
> to live here is split into one file per planning sector under
> [`current-state/`](current-state/README.md) — read **your** sector for its live state + next ▶
> startable item:
>
> | Sector | Live state | One-line status |
> |---|---|---|
> | **S1 Bot product** | [`current-state/S1-bot.md`](current-state/S1-bot.md) | reaction-roles arc Carl-bot-mature; creature game + mining grid live; Essential Setup wizard cut over to primary + follow-ons (PR 2 / 3a, #1449/#1451); Project Moon (Limbus) knowledge domain + combat-mechanics rules layer (#1453…#1549); **NEW band-#1620 completion deepening — fishing coral structures (#1596…#1605), reaction-roles slim builder (#1608…#1615), XP import from other bots (#1607/#1610), server-logging depth (#1594/#1618/#1619), bot-owner permission-gate bypass (#1602) + a boot smoke-test CI guard (#1601)**; ▶ next: Project Moon Q-0086 live walk / StaticData exact-number ingest / botsite React migration |
> | **S2 BTD6** | [`current-state/S2-btd6.md`](current-state/S2-btd6.md) | buff-uptime + data auto-seed/drift shipped; eval anchor-complete; QA-accuracy arc — interaction grounding + honest semantic-grading eval harness (#1487…#1498); **menu-layout simulator + round-range NL answer fix (#1617); owner picked Layout B — panel category-hub SHIPPED (#1621)**; ▶ live re-test (owner) / curated counter lists / decode items 3–4 |
> | **S3 AI-Memory** | [`current-state/S3-ai-memory.md`](current-state/S3-ai-memory.md) | settle-once money-safety guard (#1454) + cross-domain routing-disjointness guard (#1470); **self-improving-workflow guards #1476/#1477/#1479/#1482/#1495**; **owner re-elevated the portable substrate-kit to top focus (fresh-rebuild vision #1589/#1590)**; **rebuild design spec shipped (#1637/#1638) + BOTH linchpins now built & measured (#1639 — Phase-0.5 golden harness `parity/` + grammar spike, verdict GO-with-amendments)**; **substrate-kit finalized (#1649 — nervous system + context-economy engine + one-step-adopt; 407 kit tests)**; ▶ **next: Phase-2.5 cold-start substrate-on/off A/B** (offline, gates Phase 3; [retention plan](planning/memory-retention-and-context-economy-plan-2026-07-02.md) / Q-0214); owner-gated: Phase-2 design approval ([handoff §5.B](planning/rebuild-ultracode-handoff-2026-07-02.md)) + extraction/publication / telemetry sidecar capture |
> | **S4 Docs system** | [`current-state/S4-docs.md`](current-state/S4-docs.md) | 33rd Q-0107 pass done (band-#1680); next recon at #1710; **no PLAN-BACKLOG-THIN flag** |
> | **S5 Operations** | [`current-state/S5-ops.md`](current-state/S5-ops.md) | merge=deploy clarity (Q-0193); loop self-fires; ▶ website rollout (owner/Hermes) |
>
> **Honest caveat (cross-sector, carried):** much buildable depth is substantial runtime work — but
> every PR now auto-merges on green CI (the `needs-hermes-review` review gate was retired, Q-0197), so
> an empty *autonomous* fire just builds the next substantial lane or promotes a fresh idea → plan →
> build (Q-0172).
> *(Trust the per-sector files + the Recently-shipped list below, never a lower "next ▶" in the
> historical narrative.)*
>
> - **Consolidated batches:** **Batches 1–8 ALL executed + verified merged 2026-06-10** ([EOD verification](audits/past-day-verification-2026-06-10.md)) — #650 truth/clarity · #651 surface-classification invariant · #652 service boundaries · #654 Settings Phase 2 core · #656 adaptive P1C subpanels · **#657 Help projection seam** (HLP-2: `services/help_catalogue.py` + `services/help_projection.py`, all five render paths on one reason-coded `HelpProjection`; Q-0074 executed in the same PR) · **#659 HLP-3 guild overlay** (migration 064 `help_overlay`, audited `help_overlay_mutation` seam, cached read model, hide/rename through every render path; Q-0055 display-only pinned by an admission import fence) · **Batch 7 via the mining stack** (#661 + #663/#664/#665 → #667) · **Batch 8 = the #649 cutover**. **The queue-remainder session (PR #671, merged 2026-06-10) executed the RS07 chain-service slice** (audited `services/chain_service.py`, Batch 3 pattern, repo-wide write fence) **+ Batch 9's RS08 slice** (diagnostic read models out of the cog layer; new no-raw-SQL-in-cogs/views invariant) **+ the EOD audit's Tier-2 Help-Preview fix** (now consumes `project_help_with_execution`); **its continuation (PR #672) completed Batch 4** (proof-channel binding/resource declaration + binding-first read; logging rows verified satisfied) **and executed the Batch 10 selections** (wizard PR1–PR3 tranche verified shipped via #435 → setup-lane next = PR4 `/myprofile` planning session; next AI §7 family = **§7.5 multi-entity comparison**, sequenced after the maintainer's prod check — banners in the two plans carry the evidence). **The Help overlay editor UI executed 2026-06-10 ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → PR A #677 + PR B #679, both MERGED same day):** the hide/rename/re-describe editor (staff-hub `✏️ Help editor` button + the Settings-hub "Help appearance" domain group, 13th group) and the Q-0059 Home-message embed builder (migration 067, **mandatory preview**, shared `home_embed_frame` composer, byte-identical default pinned) — both live-verified on real Postgres. **Batch 9 then executed in PR #681** (open at write time): the RS05 publish-accepted delivery contract (runtime_contracts §2) + bus delivery stats / failure metric / the `event_bus` diagnostics provider, and the RS10 economy view family onto BaseView (conformance ratchet 17→13, arch warnings 84→80). **The consolidated plan's queue is FULLY EXECUTED (Batches 1–10; #681 MERGED).** A follow-on slice (PR #682, open at write time) migrated the **mining family** onto BaseView — the last true lifecycle-duplication family; ratchet 13→11 with a disposition note (remaining direct-View entries are ephemeral pipeline-gated follow-ups / bespoke admin checks, not RS10 duplication). **The PR4 `/myprofile` planning session ran (PR #684, open at write time):** [`planning/myprofile-foundation-plan-2026-06-10.md`](planning/myprofile-foundation-plan-2026-06-10.md) — §6 backend re-verified exact (4 audited pipeline entrypoints, typed accessors, schema registry, zero UI callers); PR A = read-only profile card (zero writes, turn-key) · PR B = the pipeline's first UI consumer · PR C onboarding **gated** on an owner decision; Q-0080 stranger-grade envelope applied throughout. Remaining plan-first/gated: Help audit Phase 4 records (Q-0057 rider) · AI §7.5 (post-eval).
> - **BTD6 data + answerability:** the `--all` cutover **#649 merged 2026-06-10; post-cutover VERIFIED + every carry-forward DECODED the same day** (#653 wave 1 ∥ PR #655 — dump fidelity byte-identical · 2,022 menu embeds in-limits · AI battery green · `_CUTOVER_CARRYFORWARD` empty, audit 91 CLEAN / 0 DELTA / 0 SUSPECT · banana economy answerable · fixes for mode-rules dark data / `!btd6 diagnostics` 400 / stamp-rot / path leak); **answerability items 5+6d shipped in PR #658**; **the Navarch "no coins" live miss diagnosed (missing ROUTING, not data) + fixed end-to-end with items 6a–c — #662 MERGED 2026-06-10** (paragon grounding gains income + effect lines · article-tolerant/shorthand paragon names · minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV) · Pouākai diacritic-fold · honest dataset source labels/summary); follow-up slice **#666** adds `scripts/btd6_probe.py` (grounding triage) + structures item 7 into [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md); **item 7 slice 1 (conversation carryover) + the zero-fact sweep fixes (ranking rosters · bare distinctive shorthand) shipped same day in #668**. **The 2026-06-11 morning screenshots (3 live AI-knowledge misses) fixed end-to-end in PR #703** — BUG-0002 (elite boss HP: dataset had no elite figures + boss names never routed BTD6 → standard table served as "Elite"; elite_tiers backfilled from the pinned v55.1 dump for all 7 bosses, boss canonicals route + name-index, variant-labeled grounding) · BUG-0003 ("despos on impop" hallucinated as PMFC; impop/despo keywords, Desperado alias, resolver plural fold, the `<quantity> <crosspath> <tower>` pricing leg — "10 041 despos" = ten 0-4-1s, owner-corrected) · BUG-0001 recurrence (round-cash refusals in #general: the workflow was profile-gated OFF on default channels — compatible_default/balanced_helper now declare analyze_execute_verify (Q-0048), matcher gained the money-question gate + by-round anchors). **Owner action: run `!btd6ops seed-data` after the deploy** (bosses/towers json are blob-lane data; owner-confirmed done 2026-06-11 ~12:38 — despos answers correct in prod). **The live re-test round shipped in PR #706 (merged 2026-06-11):** BUG-0004 (r-shorthand rounds + "end of r53" start shift — the $71,315.20 cumulative mislabel; truth $56,318.70) + the bulleted capabilities list (owner format ask; boss_health/crosspath/projection rows advertised). **The absence-claim guard's Layer A (path/line-aware retrieval) shipped in #855** — `<tower> <top|middle|bottom> path` phrasing now grounds its whole tier line instead of resolving to nothing (the canonical false-"no" trigger removed at the root); Layer B (the negative-existential gate) stays design-for-review. **Next:** decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check) · P1-1 eval-smoke matrix (creds-gated) + absence-guard Layer B.
> - **Gated:** the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table.
>
> *(The 8-lane scoreboard completed 2026-06-09/10 — record: [`planning/multi-lane-execution-plan-2026-06-09.md`](planning/multi-lane-execution-plan-2026-06-09.md), now `historical`.)*
>
> 1. **Mining character platform** — **the 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed in one 4-PR stack — all four merged 2026-06-10:** **#661** (RS01 — atomic shop-purchase workflow + the Q-0071 transaction plumbing) → **#663** (RS02 stage 1 — pure domain relocated to `utils/mining/`, `services/mining_workflow.py` owns the workshop ops, views→cogs allowlist entries deleted) → **#664** (RS02 stage 2 — *every* mining write behind the workflow service, one transaction per op; AST ratchet; recipes.json reconciled to the catalog under a new alignment lint — **Batch 7 COMPLETE**) → **#665** (shared **game-XP** service + leaderboards + depth records (migrations 065/066) · **deeper ladders** incl. the diamond lantern that makes MAGMA reachable (it never was) · Gear panel + Recipe browser + fuzzy names + `!fastmine` · **duels gear wear — Q-0054 CLOSED** · PIL inventory + stat cards). Session decisions: **Q-0075** (curated economy + deeper ladders) + **Q-0076** (both PIL cards) — router §32. *(Merge mechanics note: the stacked bases didn't auto-retarget, so #663/#664/#665 merged into their parent branches — the content reached `main` via the same-day completion PR **#667**, content-verified EOD; migrations renumbered 065/066 around #659's 064.)* Earlier Wave-1 chain: #606–#610, #624. **The V-16 phase-1 gear slice shipped 2026-06-11 (PR #702, full Q-0092 scope):** 9-slot set-piece model (+ migration 068 legacy fold) · same-tier set bonus with set-aware Equip Best + "breaks set" picker warnings · bronze/silver ores · sim-pinned numbers ([record](planning/gear-set-numbers-2026-06-11.md)) · picker stat previews · the paper-doll compositor (placeholder sprites; owner pack drops into `disbot/assets/gear/`). **§7.5 structures started: the Vault (safe stash) shipped 2026-06-14 (#884)** — `mining_vault` (migration 070) + the audited deposit/withdraw/stash-all ops + a `🏦 Vault` panel; v1 is a pure safe store; **Slice A — Vault v2 (the cap sink) shipped 2026-06-15 (#897)**: a pack soft-cap (distinct item-types, warning-only — never blocks mining) + an upgradeable vault capacity (`!vaultupgrade` coin sink, migration 072 `vault_level`), pure cap math in `utils/mining/capacity.py`. **The §7.4 capped skill tree (the marquee) shipped 2026-06-15 (#891)** — `player_skills` (migration 071) + `services/skill_service.py`; four branches capped so you can't max all (forced specialization), points from the game-XP level, merged into `EffectiveStats` via `utils/mining/character.py` (byte-identical when empty), `🌳 Skills` panel + `!skills`/`!skill`. **Slice B — the Forge (gear-tier crafting gate) shipped 2026-06-15 (#905)**: a built structure (coin + material sink) on the generic `mining_structures` table (migration 073, reused by Slice C) — gates the **top two** gear tiers (gold → Forge I, diamond → Forge II; bronze/iron/silver gear + tools + structures stay forge-free, so most play is unchanged), pure `utils/mining/structures.py`, audited `mining_workflow.build_structure`, `🔥 Forge` panel + `!forge`. **Next slices stay turn-key + ▶ startable** in [`planning/mining-structures-skill-tree-plan-2026-06-14.md`](planning/mining-structures-skill-tree-plan-2026-06-14.md): respec-polish / skill-titles (E/F, now unblocked by #891) · **Home** (C, reuses the structures table) · the Vault-cap *hard*-enforcement follow-up (A, owner-gated). [Slices D ✅ #891 · A (Vault v2 soft-cap) ✅ #897 · B (Forge) ✅ #905.] **⛔ V-16 phase 2** (paper-doll real sprites) stays owner-blocked on the PNG pack. Route in: that plan + `docs/ideas/mining_exploration_brainstorm.md` §7.7 + the games folio.
> 2. **Adaptive Setup/Access platform** — Phase 0 complete; Phase 1 underway: Q-0026 identity repair + Phase 0 contracts **#588**, P1A Access Map projection **#589**, P0C groundwork **#591**, P0C seam conversion + P1B `routing_access_conflict` **#592**; **P1B remainder shipped in #632 (2026-06-09, execution-plan Lane 2 — verify merged on live GitHub):** the Q-0045 governance tier-input path (`GovernanceContext.member_tier`, declared tier preferred verbatim, simulation-labeled per §16.4) + the `help_advertises_locked` drift provider + the full Q-0036 denial-copy **draft** (in the PR body for maintainer read-through — **not live-wired**; wiring follows his markup). **P1C merged 2026-06-10 (consolidated plan Batch 5, #656):** Access Map + Help Preview shipped as **staff-hub subpanels, no new command names** (Q-0032), on the tier path as-is. **The Batch 6 Help projection seam consumed this lane 2026-06-10 (#657, merged):** Help's five render paths now compose governance + the projection contract end-to-end (`services/help_projection.py`, incl. an execution-enriched mode over `access_projection`). **Next: P2** Feature Profile preview (own planning first). Q-0028–Q-0031 + Q-0033 are also **answered** (catalogue committed · availability owns quiet mode · snapshots compound+high-risk · risk policy approved · account links deferred — router §20). Route in: plan §16.8.
> 3. **AI tooling (orchestration + answerability)** — orchestration Phases 1–3 shipped (**#612**, **#618**, **#619** — including the gate-lifted `ai:tools` Tools & Workflows operator UI; default byte-identical); answerability Phase 1A/1B (**#612**, Q-0043: range cash **inclusive**) + Phase 2 read model (**#616**) shipped. **Orchestration Phase 4 MVP (Q-0046) built 2026-06-09 in PR #634** (execution-plan Lane 3, parallel session): the round-cash plan→execute→verify workflow + the one typed answer-with-evidence contract, profile-gated, default byte-identical — **model loop awaits the maintainer's production check** (no sandbox provider key). **Answerability Phase 3 shipped 2026-06-09 in PR #639** (execution-plan Lane 4, **Q-0047**): the three read-only self-awareness tools — `get_ai_tool_catalog` ("what can you do here?") · `get_ai_policy_explanation` ("why didn't you reply?") · `btd6_answerability` ("what BTD6 data do you know?") — audience-tiered **at construction** over the #616 read model; **model loop awaits the maintainer's prod check** (no sandbox key). **Next:** the remaining orchestration §7 workflow families; answerability Phases 4/5 stay gated (settings UI per-exposure ask · dashboard schema acceptance). Standing posture **Q-0048**: read-only deterministic tools ship without a per-case ask; writes/external/UI stay per-exposure. Plans: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) · [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **The first Q-0086 joint live session ran 2026-06-11 (PR #707): the model-loop gate is LIFTED** (keys in agent sessions; full loop verified on both providers); BUG-0005…0008 fixed live (tool quantity laundering · carryover routing/forcing · conversation-meta floor copy + guard haystack · farm/possessive/double-cash routing); **BUG-0009** (claim assembly) OPEN in the [bug book](health/bug-book.md); **BUG-0010 (ABR qualifier) FIXED same day in the follow-up slice (PR #709** — shared ABR cue → grounding round legs + the round-cash workflow compute/label the ABR set, modifier honesty deterministic**)**; **Q-0094** (memory floor canon) + **Q-0095** (Haiku-4.5 allocation for the two NL tasks · the guild-default-provider trap · sandbox floor-testing posture) recorded; the owner-requested **AI panel rework** captured ([idea](ideas/ai-panel-inplace-navigation-2026-06-11.md)). Gear/mining (#702) is still never owner-played — the eval-checklist Tier 2+ walk stays queued.
>
> Cross-cutting: **Community Spotlight** (side-lane **#613**/**#614** + hotfixes **#615**/**#617**) was hardened in the review session (canonical `utils/db/xp.py` read, `member_count` crash fix, first tests) and **Q-0044 is executed**: the Q-0025 `scripts/new_subsystem.py` scaffold was built and used to register Spotlight as a `community`-hub child (**#626**, 2026-06-09 — execution-plan Lane 1; merged, verified live), and the `!hub`/`!server` aliases were **dropped same day** (kept `!spotlight`/`!activity`). Also decided: BTD6 data-refresh automation = **manual-dispatch workflow** (Q-0049 — **built same day in #633**, execution-plan Lane 5: `workflow_dispatch`-only, opens a reviewable PR, never pushes to main); mining descent lights **permanent, owner-confirmed** (Q-0050); the five product-vision questions (Q-0038–Q-0042) got their **draft-answer session** (Q-0051) **and the maintainer marked all five up same day (Lane 6, PR #631, structured choices)**: Q-0038 server-scoped clans, Q-0039 cosmetic-only donations (no bot-side billing), Q-0041 YouTube-first/dual-opt-in/voice-deferred, Q-0042 staged-Someday website — all approved as drafted; **Q-0040 adjusted: the AI dungeon master picks quests/rewards/difficulty from bounded, hard-capped menus** (not pure narration, not free-form authority). Posture decisions only — every lane still needs its own plan/promotion + the AI per-exposure lift; conclusions routed to the four roadmap drafts + router §21. Full repo review: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md) · agent-memory system review (did the orientation/memory system work in practice?): [`audits/agent-memory-system-review-2026-06-09.md`](audits/agent-memory-system-review-2026-06-09.md).
>
> **Last updated:** 2026-07-03 — **thirty-third Q-0107 reconciliation pass (band-#1680, issue #1681
> — [pass record](planning/reconciliation-pass-2026-07-03-band1680.md));** reconciled band #1651–#1680
> (four grouped entries — headlined by the **S3 rebuild new-bot capability audit → frozen BUILD-PLAN**
> #1662…#1668/#1674/#1677 (verdict GO-with-amendments, all-43 fit 85.1%) and the owner-live **Phase-A
> conventions freeze** #1679/#1680; plus the 32nd-pass + Q-0102 review/brainstorm routine sessions and
> the per-merge dashboard refreshes), trimmed Recently-shipped to 20, forward queue still deep (no THIN
> flag), marker #1650 → #1680. Earlier: 2026-07-02 — **thirty-second Q-0107 reconciliation pass
> (band-#1650, issue #1651 — [pass record](planning/reconciliation-pass-2026-07-02-band1650.md));**
> reconciled band #1621–#1650 (six grouped entries — the S3 fresh-rebuild arc: Fable 5 design spec +
> strategy + parallel-execution schedule + memory-retention/context-economy plan and linchpin validation
> #1639; plus S1 server-logging v2 audit-log #1624, S1 fishing Fishery #1626, S2 BTD6 Layout B #1621, and
> the 31st-pass+dashboard docs band), trimmed Recently-shipped to 20, marker #1620 → #1650.
> Earlier: 2026-07-02 — **rebuild linchpin validation shipped (#1639):** the Phase-0.5
> golden harness (`parity/`, coverage-measured) + the grammar-expressiveness spike
> (`tools/grammar_spike/`) — the owner-gate evidence package
> ([go/no-go](planning/rebuild-linchpin-validation-2026-07-02.md), verdict GO-with-amendments).
> Earlier: 2026-07-01 — **thirty-first Q-0107 reconciliation pass (band-#1620, issue #1622
> — [pass record](planning/reconciliation-pass-2026-07-01-band1620.md));** reconciled band #1591–#1620
> (seven grouped entries — fishing coral structures, reaction-roles slim builder, XP import, server-logging
> depth, an S1 completion+owner-override+boot-guard bundle, BTD6 layout sim), forward queue still deep
> (no THIN flag). Earlier: 2026-06-30, thirtieth pass —
> reflected the owner's **fresh-rebuild vision** re-elevating the AI-memory substrate-kit to top focus.
> The live state is the **▶ Next action** line above + the Recently-shipped list. *(The dated narrative
> below is historical — passes 10–25 record their state in the ▶ Next action callout + per-band records.)*
> Earlier: 2026-06-15, **ninth Q-0107 reconciliation pass (the band-#930 cadence fire,
> issue #931)** — scored the band #901–#930 against the band-#900 queue: **the planned decade queue
> nearly fully executed** — Forge ✅#905 · P1-3 invariants ✅#917/#918 · Railway log-triage ✅#906 ·
> Home/respec/titles ✅#910/#912 · BUG-0009 slices 1/2/2b ✅#924/#926 · welcome phase 2 ✅#920;
> security tiers 1+2 **in flight** (#929, `needs-hermes-review` carve-out); the buffer was the Hermes
> gpt-5.4-mini model-swap + ops-docs band (#915–#930). Reconciled the ledger (added the #915–#928
> docs band as one grouped entry; archived #862/#859/#855), **fixed a control-plane drift** (the Gates
> section claimed the loop had "never self-fired" — issue #931's `menno420` author proves ROUTINE_PAT
> is set and the loop self-fires; matched it to the canonical control-plane table), planned the next
> band ([band-#930 decade queue](planning/reconciliation-pass-2026-06-15-band930.md)), **promoted the
> games-economy faucet/sink diagnostic idea → a turn-key plan** (its sink-heavy gate cleared by respec
> #912 + structures), re-badged the band-#900 pass `historical`, disposed the one open PR (#929,
> left for Hermes review), and reset the marker #900→**#930**. No new runtime bugs. ·
> 2026-06-15, **eighth Q-0107 reconciliation pass (the band-#900 cadence
> fire)** — scored the band #871–#900 against the band-#870 queue: **slot 2 over-delivered** — P1-1's
> entire **offline eval half shipped** (#878→#896, AI tool-surface coverage **8 → 34/34 FULL** + the
> self-cleaning drift guard), proving last pass's "split the gated slot, ship the buildable half" fix
> worked; the buffer again *became the band* via three owner-steered threads (mining structures
> #884/#891/#897 · routine-consolidation/sector-dispatch #877/#880/#882/#899/#900 · loop hygiene).
> Reconciled the ledger (#898 folded into the loop-hygiene entry), planned the next ~9 PRs
> ([band-#900 decade queue](planning/reconciliation-pass-2026-06-15-band900.md)) — **next ▶ = mining
> Forge · P1-3 invariants · Railway log-triage skill** — re-pointed the live queue + roadmap Now,
> re-badged the band-#870 pass `historical`, disposed the one open PR (**#893**, the owner's mining
> handoff — left for the owner), reset the marker #870→**#900**, and **acted on the band-#870 §6
> escalation rule**: the substrate-kit (now its **fourth** carry) is **demoted from the plannable
> queue to the owner-action list** — the generalized new rule being *an `owner`-gated slot that
> carries four bands leaves the decade queue* (§6). No new runtime bugs. ·
> 2026-06-15, **routine fleet consolidated to 2 — dispatch absorbs the
> night-executor (PR #900-ish, Q-0145)** — owner directive: the dispatch + night-executor routines
> always did the same job (advance the plan); dispatch is just the steerable one, so they are now
> **one execution routine**. Merged their (already-identical, Q-0144) prompts into the single
> **dispatch** prompt (`hermes-dispatch-bridge.md`), which absorbed the executor's bug-book orient +
> bounded-continuation handoff; the `autonomous-routines.md` night-executor section → a pointer; fleet
> + label tables de-staled. **2 routine prompts now: dispatch (all execution) + docs reconciliation.**
> Trigger (Q-0146, 2026-06-15): dispatch's cadence is the Claude Code console **Schedule** trigger —
> every **2h**, cron `0 */2 * * *`, owner-enabled — superseding the Hermes-VPS-cron / GitHub-`schedule:`
> plan (both unreliable for cadence); the legacy `executor-nightly.yml` was removed 2026-06-15. ·
> 2026-06-15, **routine-prompt canon — foolproof, completion-biased, idea→plan
> (PR #899, Q-0144)** — owner-directed in-session: rewrote the dispatch + night-executor routine
> prompts onto the owner's 12-step lifecycle and made them foolproof against bad dispatch input (the
> "write a story about chickens" test). Now explicit in every routine prompt: **never-stop /
> completion bias** (a routine always ships *something real* — the dispatched work or the next plan
> slice), **sync-first** (stale clone was a named Hermes failure), **work-order-is-a-hint** (a
> dispatched order = owner asking = build it; off-plan nonsense → do the plan instead; never invent),
> the **scope-brake vs safety-brake** split (the phase gate is a scope brake for self-invented features
> only — it does **not** apply to dispatched work; irreversible safety brakes never bend), **2–3 slices
> bounded by ~700K tokens** (§10 updated), born-red mock PR, judgment-over-plan, bugs-first, and the
> standing enders. The **reconciliation** routine gained the owner's **idea→plan promotion**: when
> plans run low on executable work, promote the best `docs/ideas/` entry into a complete executable
> plan. The in-repo prompts are the canonical mirror — **owner re-pastes them into each routine's
> console config to take effect.** Docs only. ·
> 2026-06-14, **sector tooling — the partition is now self-maintaining (PR #882)** —
> closed the loose ends from the dispatch work: `scripts/check_sector_map.py` (validator — folio homing
> + executor + startability convention, was prose-asserted) and `scripts/dispatch_menu.py` (resolver —
> the machine version of the dispatch test: per sector, the first ▶ startable item + executor, flags a
> starving/blocked sector). Both stdlib, read-only, disposable (Q-0105), tested (19 tests); not CI-wired
> (ask-first). Building `dispatch_menu` caught a real convention bug (a ▶ glyph used in S2 `Now` *prose*,
> not as an item tag) — fixed. CI green (9664); arch 0. **(PR #885 same session captured a
> dispatch-resolution idea — `dispatch_menu --json` + Hermes wiring — and a checker-with-convention
> rule.)** ·
> 2026-06-14, **dispatch contract sharpened — executor dimension + startability tags
> (PR #880, Q-0143)** — a live dogfooding test of the sector dispatch structure (owner-requested) passed
> on speed (2–3 hops/sector, links resolve, the index ranks, a stale `Now` self-corrected in one hop)
> and surfaced 3 findings, all built into one docs PR: a complete dispatch is now **sector + action +
> executor** (Claude-in-repo / Hermes-VPS / maintainer — **S5 is the executor outlier**), each `Now`
> item carries a **startability tag** (▶/⛔/👤), and S1's `Now` was de-drifted for #878 (offline
> eval/smoke matrix shipped). Homes: `repo-sector-map.md` § dispatch targets + `roadmap.md` per-sector
> `Now`. ·
> 2026-06-14, **roadmap restructured by sector → dispatchable per-sector queues
> (PR #877)** — owner-directed; the next-session sector-mapping brief executed. `roadmap.md` is now
> organised under the **5 planning sectors** (S1–S5, Q-0137): a **per-sector dispatch index**
> (Now/Next/Later each) is the new top layer, and the former "Agent ecosystem" lane is split into its
> real sectors — **S3** (mechanism) / **S4** (docs content) / **S5** (operations) — populating the two
> previously-thin sectors so **every sector has a live queue** (the Q-0137 deep-clean terminal
> condition). Added the per-sector **dispatch contract** (what *plan* / *execute·continue* mean) to
> `repo-sector-map.md`, and reconciled the planning↔review (S↔A) taxonomies in both maps. The point:
> each sector is now a clean **Hermes-dispatch target** (Thread-1 wiring stays owner-undecided).
> Docs-only; no `disbot/`. ·
> 2026-06-14, **seventh Q-0107 reconciliation pass (the band-#870 cadence
> fire)** — scored the band #841–#870 (~3/10 planned slots executed: **P1-2 ✅ #843**,
> ledger-checker ✅ #864, **P1-1 Layer A 🟡 #855**; the band's headline is the unplanned
> **Hermes control-plane / autonomous-loop operationalization arc** #863/#865/#868/#869/#870 +
> the prod backup fix #862 + the #704 triage/close #866). Reconciled the ledger (#867 ad-hoc
> window catch-up + the #868/#869/#870 Hermes arc), planned the next ~9 PRs
> ([band-#870 decade queue](planning/reconciliation-pass-2026-06-14-band870.md)) — **next = finish
> the P1 tier (eval-matrix offline half + absence-guard Layer B → P1-3 invariants) + a reserved
> slot for the Railway log-triage skill** — re-pointed the live queue + roadmap Now, re-badged the
> band-#840 pass `historical`, recorded the **zero-open-PRs** disposition (the cleanest the
> snapshot has logged), and reset the marker #840→**#870**. The planning improvement this pass
> made: every queue slot now carries a **gate-state tag** and a carried-slot **escalation rule**
> (§6). No new runtime bugs. ·
> 2026-06-14, **P1-1 Layer A — BTD6 path/line-aware resolution (#855)**.
> The first concrete slice of P1-1 (the standing #1 priority): the absence-claim guard's
> **Layer A** (retrieval, the design's Rec #1). `<tower> <top|middle|bottom> path` phrasing now
> grounds its whole tier line (a header naming every tier + per-tier detail) instead of
> resolving to nothing and licensing a confabulated false "no" — the canonical
> "bomb-shooter-middle-path" trigger removed at the root (the MOAB-bonus data was reachable, just
> unqueried). Conservative resolver (needs a tower + the literal `path` token). **Layer B (the
> negative-existential gate) stays design-for-review + needs prod creds.** +22 tests; CI green
> (9579); arch 0. ·
> 2026-06-14, **born-red session merge-gate (#849, Q-0133)**. Every
> `claude/*` session now opens its PR **born red** via an `in-progress` `.sessions/` card and
> flips it to `complete` as the deliberate final step — so native auto-merge fires on a
> *complete* PR, never a partial one (the #843 race). Folded into the required `code-quality`
> check (`scripts/check_session_gate.py`); engage-when-present so routines never deadlock;
> dogfooded on its own PR. ·
> 2026-06-14, **hardening P1-2 — health findings lifecycle + operational
> retention (#843, Q-0097)**. The persistent operational-health findings store gained an
> operator-managed transition path through the sole writer (`health_findings_service.set_status`
> + DB primitive `set_finding_status`, audited via `audit.action_recorded`), surfaced as
> `!platform finding resolve/ignore/reopen <fingerprint>`; retention now reruns on a daily
> `HealthMaintenanceCog` loop (not startup-only). The two health-map code gaps are closed; the
> remaining gap to production-ready is the owner-led live walk. CI green (9551); arch 0. ·
> 2026-06-14, **sixth Q-0107 reconciliation pass (the band-#840 cadence
> fire)** — scored the band #821–#840 (2/10 planned slots executed, but the **whole
> production-hardening P0 integrity spine is now COMPLETE**: P0-2 #829 · P0-3 #817 · P0-4
> #820/#825; the buffer went to the owner-directed **Railway agent-access** arc #827–#840,
> now **verified live** in #840). Reconciled the ledger (#838/#839/#840 + the Railway-session
> housekeeping PRs), planned the next ~9 PRs ([band-#840 decade queue](planning/reconciliation-pass-2026-06-14-band840.md))
> — **next = the P1 correctness tier** (P1-1 eval-matrix → P1-2 → P1-3) — re-pointed the live
> queue + roadmap Now, re-badged the band-#820 pass `historical`, recorded both open PRs (#834
> owner-capture · #704 owner-screenshots) with state, and reset the marker #820→**#840**. No new
> runtime bugs. ·
> 2026-06-14, **hardening P0-2 media retention PR 1 — data-minimization +
> retention enforcement (#829, Q-0099)**. The video-reference cache now stores only
> a bounded sanitized projection (`_project_metadata` — never the raw provider payload), a new
> `MediaMaintenanceCog` owns a scheduled physical purge of expired rows, thumbnail URLs are
> host/scheme-validated, and `docs/ownership.md` gained the `media` (YouTube) subsystem row.
> CI green (9467); arch 0; next = P0-2 follow-ups (diagnostics · provider hardening · live
> verify) → P1-1. ·
> 2026-06-14, **hardening P0-4 PR 2 — channel creation + category lifecycle
> convergence (#825, Q-0100)**. Ad-hoc operator channel creation
> (`!create`/`!evt`/`!bulkcreate` + the create panel) routed through a new audited
> `ChannelLifecycleService.create_channels` (the channel sibling of `RoleLifecycleService`;
> unbound creation has no declared binding so it never fit `ResourceProvisioningPipeline`).
> Every operator channel mutation now flows through one seam with audit +
> `channel.lifecycle_changed`; `test_no_direct_channel_mutations` pins `create_*`,
> `test_no_silent_auto_create` names the service as the one manual creator. **P0-4 complete;
> next P0 = P0-2 media retention (Q-0099).** CI green (9453); arch 0; corrected the readiness-map
> `create_panel` "uses provisioning lane" drift. ·
> 2026-06-14, **hardening P0-3 arc PR 3 — delegated-Setup apply authority
> (#817, Q-0098)**. Bounded `setup_delegate` actor authorized at the capability floor (still
> member-checked + revocable, audited distinctly), minted only by `apply_operations` after a
> live `can_apply_setup` re-check, threaded to the three capability pipelines, `_ALLOWED_ACTOR_TYPES`
> + the settings/resource audit CHECKs widened (migration 069), AST-fenced. **P0-3 complete;
> next P0 = P0-4 channel-ownership.** CI green (9442); arch 0; real-Postgres + clean-boot proven.

> **Purpose:** the one file that answers "what is true right now?" so a new
> session does not reconstruct it from the journal + planning docs. Read it
> **second**, right after `.claude/CLAUDE.md`.

---

## Stability baseline

Operational stability **accepted after #535** (live cog walk: server-management,
economy, moderation, games, hub navigation). **Do not run a broad re-audit unless
a regression is reported** — this is an *accepted baseline*, not a fresh re-test.
Env-gated features (AI / scheduler / YouTube / Paragon / webhook) run **degraded
in the sandbox**, not broken. Known UX follow-ups remain (below).

## In flight (verify against live GitHub)

**Do not trust a hard-coded PR count here — it goes stale on every push.** Get the
real list at session start from live GitHub (`list_pull_requests`, state=open);
this snapshot deliberately names no open PRs. For an initiative's shipped/queued
status read its tracker (e.g. the server-management tracker), not this section.
Source code and merged PRs win over anything written here.

## Recently shipped (newest first)

> Convention: **merged PRs only** (with #numbers). In-flight work is *not* listed here —
> get it from live GitHub. The newest merge a session sees may not be added yet; that
> lag is expected (the next session reconciles). A merged PR tagged "pending" is the bug.
>
> **Last reconciliation pass:** PR #1680 (2026-07-03, thirty-third Q-0107 cadence pass, band-#1680 —
> [the pass record + next-band queue](planning/reconciliation-pass-2026-07-03-band1680.md); marker reset
> to the latest merged PR **#1680**). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #1710 (every
> multiple of **30** — Q-0107 cadence raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
> Q-0134; `check_reconciliation_due.py` flags it, and `.github/workflows/reconciliation-trigger.yml`
> auto-opens a `reconcile` issue at the boundary that fires the docs-reconciliation routine). Reset
> this marker to the latest PR after a pass.

- **#1683 (2026-07-03, workflow — cut permission prompts + endorse invocation centralizations, Q-0229/Q-0228)** —
  broadened `.claude/settings.json` with whole-MCP-server allow entries (`mcp__Claude_Code_Remote`,
  `mcp__github`, `mcp__codegraph`, `mcp__context7`) so tools like `send_later` stop prompting —
  the destructive-ops `ask` brake left intact (Q-0229 diagnosis: web downgrades project-scope
  `bypassPermissions`, so the explicit allow list is the reliable lever); and updated Q-0228 + the
  conventions log §6 to record the owner **endorsing** the C-1…C-7 invocation-stack centralizations
  as foundations to build toward.
- **#1680 (2026-07-03, S3 rebuild — Phase-A conventions freeze: naming · invocation ladder · mod-actions-as-data · authority, Q-0224…Q-0228)** —
  the owner-live conventions-freeze continuation of Stage 1, folded into the
  [conventions decisions log](planning/rebuild-conventions-invocation-authority-2026-07-03.md):
  command **naming** (namespace only shared verbs, computed from the corpus; safe no-arg defaults);
  the **four-rung invocation ladder** (exact → fuzzy typo matcher → NL intent → NL orchestration)
  with **additive** guild/channel/user custom triggers, silent-on-no-match, and the three-tier
  fuzzy matcher; **mod-actions-as-data** (resolving the ModerationActionSpec uncertainty to the
  envelope); **one authority layer + a global bot-owner override** (verification test + transparent
  audit); and **proposed** invocation-stack centralizations C-1…C-7 (Q-0228, pending owner
  reaction). ▶ next: **Stage 2 — the subsystem walk**.
- **#1679 (2026-07-03, S3 rebuild — Phase-A Stage-1 global review: standards + order audit + Gate-0 deltas, Q-0219…Q-0223)** —
  the owner-live **Stage-1 review** of the frozen BUILD-PLAN, folded into the
  [Stage-1 decisions log](planning/rebuild-stage1-global-review-2026-07-03.md): the **S-1
  engine/declaration/seam generalization standard** + **S-2 foundation-before-consumer ordering
  rule**; a full dependency-order audit (3 inversions — welcome re-homed to L1c after the card
  engine; deathmatch/explore take declared-seam deferrals, mining-last stands); Gate-0 deltas
  D-1…D-6 incl. a **new media-generation capability** (Q-0221) and the **3-phase container-first
  cutover model** (Q-0222 — container-only live testing → manifest-driven selective import with
  full-coverage disposition → token swap); the substrate-kit figure corrected (~90–95%, 422 tests
  green — completion is the pre-bootstrap gate, Q-0223) and per-subsystem triage made a Stage-2
  deliverable. ▶ next: **Stage 2 — the subsystem walk**.
- **#1662 · #1663 · #1664 · #1665 · #1666 · #1667 · #1668 · #1674 · #1677 (2026-07-03, S3 rebuild — new-bot capability audit → frozen BUILD-PLAN)** —
  the pre-Phase-A **new-bot capability audit**: the BRIEF hardened with prompt-refinement launch
  preconditions (#1662), then a parallel per-lane grammar-fit sweep of the whole shipped surface —
  Lane A governance (#1663), Lane B economy & character-sim (#1665), Lane C games & community (#1664),
  Lane D knowledge/AI/platform (#1667), Lane E plans & ideas forward-capability ledger (#1668), Lane G
  L0 (#1666) — folded by the **capstone** (#1674) into
  [`NEW-BOT-BUILD-PLAN.md`](analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  (verdict **GO-with-amendments**, measured all-43 fit **85.1%**) plus a `check_plan_staleness.py`
  guard; the review-then-plan process + next-session goal captured in
  [`planning/rebuild-planning-phase-2026-07-03.md`](planning/rebuild-planning-phase-2026-07-03.md) (#1677).
- **#1652 · #1653 · #1657 · #1658 · #1659 · #1661 · #1669 · #1672 · #1673 (2026-07-02/03, workflow — 32nd pass + review/brainstorm routine sessions)** —
  the **thirty-second Q-0107 reconciliation pass** (band-#1650,
  [pass record](planning/reconciliation-pass-2026-07-02-band1650.md), #1652); the review of session #1649
  (substrate-kit finalize) + ledger fix + missed-defect fixes (#1653); the review-then-plan Codex-PR
  close-out (#1657); daily-review-brainstorm sessions (#1658/#1659); a session-card PR-number fix (#1661);
  and further Q-0102 review-recent-session passes (#1669/#1672/#1673).
- **#1656 · #1660 · #1670 · #1671 · #1675 · #1676 · #1678 (2026-07-02/03, docs — dashboard-data refreshes, Q-0167)** —
  seven per-source-merge **dashboard-data refreshes** keeping the committed `dashboard/data/dashboard.json`
  export fresh as parallel sessions landed.
- **#1643 · #1647 · #1648 · #1649 (2026-07-02, S3 rebuild — memory substrate: retention/economy plan → finalized substrate-kit, Q-0214)** —
  the [memory-retention-and-context-economy plan](planning/memory-retention-and-context-economy-plan-2026-07-02.md):
  the retention half of the rebuild memory substrate — warn-forever corpus caps + diff-scoped hard gates,
  per-file harvest evidence, single-writer pruning, a 14-day floor, and a shadow-band + `do-not-automerge`
  guard on the first prune (folded from an enforcement-critic verdict). **#1649 finalized it** (the
  [handoff §5.B](planning/rebuild-ultracode-handoff-2026-07-02.md) Fable-5 ultracode session, the K0 gate
  deliverable): the substrate-kit's full nervous system + context-economy engine + one-step-adopt packaging
  shipped on the declaration layer (117→407 kit tests, proven end-to-end from the single-file dist) — see
  [S3-ai-memory](current-state/S3-ai-memory.md). Owner-gated remainder: the Phase-2.5 cold-start A/B (still
  gates Phase 3) + the extract-to-standalone-repo step.
- **#1634 · #1635 · #1637 · #1638 · #1640 · #1641 · #1642 · #1644 · #1645 (2026-07-02, S3 rebuild — Fable 5 design spec + strategy + schedule)** —
  the [fresh-rebuild strategy + verified baseline](planning/fresh-rebuild-strategy-2026-07-02.md) with the four
  Codex discovery-maps verified against shipped source (Q-0120) and folded into one
  [preserve-map synthesis](analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md) (#1634/#1642);
  the **Fable 5 Phase-2 design spec** via a 4-design judge panel (#1635/#1637/#1638/#1640); the
  [parallel-execution schedule](planning/rebuild-parallel-execution-plan-2026-07-02.md) + memory-system-as-K0-gate
  elevation (#1644/#1645); and five deduped idea captures from the arc (#1641).
- **#1639 (2026-07-02, S3 rebuild — linchpin validation: golden harness + grammar spike)** — the two
  unproven rebuild linchpins **built and measured** before the owner gate: the **Phase-0.5 golden
  behavioral harness** (`parity/` — the real bot driven in-process through the real discord.py state
  machine over a fake HTTP boundary; 400+ golden fixtures; **replay-deterministic**; coverage
  measured with the uncovered tail named in `parity/COVERAGE.md`) and the **grammar-expressiveness
  spike** (`tools/grammar_spike/` — real karma/logging/blackjack manifests in the §2 grammar;
  tier-1/2 fit **73% as-specced → 85% with six named amendments**, operator band 97%). Owner-gate
  evidence + GO-with-amendments verdict:
  [`planning/rebuild-linchpin-validation-2026-07-02.md`](planning/rebuild-linchpin-validation-2026-07-02.md).
- **#1624 (2026-07-01, S1 — server event logging v2, Discord audit-log / Dyno parity)** — server event
  logging v2 wiring Discord **audit-log** events into the log pipeline (kick/ban/role/channel actor
  attribution), closing the Dyno-parity gap on the server-logging arc (#1594/#1618/#1619).
- **#1626 (2026-07-01, S1 fishing — Fishery structure + Boathouse buildfix)** — a **Fishery** coral
  structure (rare-material processing) added to the 🏗 Structures sub-hub, plus a Boathouse build fix and
  market/rewards plumbing; extends the coral-structures arc (#1596…#1605).
- **#1621 (2026-07-01, S2 BTD6 — Layout B panel category-hub)** — the owner-picked **Layout B** menu
  restructure from the #1617 layout simulator: the BTD6 panel is now a category-hub, landing the design
  that was in flight at the thirty-first pass.
- **#1623 + 7 dashboard refreshes (2026-07-01/02, docs — thirty-first Q-0107 pass + dashboard)** — the
  **thirty-first Q-0107 reconciliation pass** (band-#1620,
  [pass record](planning/reconciliation-pass-2026-07-01-band1620.md), #1623); plus seven per-source-merge
  **dashboard-data refreshes** (#1625 · #1627 · #1628 · #1629 · #1636 · #1646 · #1650, Q-0167).
- **#1591 + 5 dashboard refreshes (2026-06-30/07-01, docs — thirtieth Q-0107 pass + dashboard)** — the
  **thirtieth Q-0107 reconciliation pass** (band-#1590,
  [pass record](planning/reconciliation-pass-2026-06-30-band1590.md), #1591); plus five per-source-merge
  **dashboard-data refreshes** (#1593 · #1597 · #1604 · #1606 · #1616, Q-0167).
- **#1596 · #1598 · #1603 · #1605 (2026-06-30/07-01, S1 fishing — coral structures arc)** — a coral
  deepwater rare-material drop → cosmetic curio collectibles (#1596), the **Dock** bite-speed coral
  structure (#1598) and the **Boathouse** energy-regen structure (#1605), folded together with the
  Tide Pool into a 🏗 **Structures sub-hub** (#1603).
- **#1608 · #1612 · #1613 · #1615 (2026-07-01, S1 reaction-roles menu builder)** — fixed the role-menu
  builder preview never updating on its ephemeral panel (#1608) and adopted the layout-sim's **slim/lean
  2-row menu-builder layout** (#1612/#1613/#1615, owner-directed after the 14-button builder felt dense).
- **#1607 · #1610 (2026-07-01, S1 XP import/migration)** — **XP/level migration from other bots** via an
  Arcane level-up-channel scan (#1607) plus a button entry point and generic "import from another bot"
  framing (#1610).
- **#1594 · #1618 · #1619 (2026-06-30/07-01, S1 server-logging depth)** — ignored-channels/users
  **exclusion lists** (#1594), a **subject avatar in every log embed** (#1618), and a per-route
  binding-crash + disappearing-back-button + settings-order simulation fix (#1619).
- **#1602 · #1599/#1600/#1601 · #1595 · #1609 · #1614 · #1620 · #1611 (2026-06-30/07-01, S1 completion + owner override + boot guard)** —
  the bot owner now **bypasses ALL permission gates**, not just `administrator` (#1602); a **boot
  smoke-test CI guard** fails the build when a cog won't load, defense-in-depth after the #1599/#1600
  cog-load outage (#1601); plus completion-first punches — inventory rarity-tier detail fields (#1595),
  user-tier `!ping`/`!botinfo`/`!membercount` + command tests (#1609), rank/leaderboard **visual polish**
  out-reading Arcane/MEE6 (#1614), **karma reaction-to-thank** (#1620), and treasury-cog tests (#1611).
- **#1617 (2026-07-01, S2 BTD6)** — a **BTD6 menu layout simulator** + a round-range NL answer fix; the
  owner picked Layout B and the panel-hub implementation is in flight (#1621).
- **#1564 + 6 dashboard refreshes (2026-06-29/30, docs — twenty-ninth Q-0107 pass + dashboard)** — the
  **twenty-ninth Q-0107 reconciliation pass** (band-#1560,
  [pass record](planning/reconciliation-pass-2026-06-29-band1560.md), #1564); plus six per-source-merge
  **dashboard-data refreshes** (#1562 · #1567 · #1576 · #1580 · #1583 · #1587, Q-0167).
- **Older merges (#1590 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are trimmed to the archive (newest-first), which `scripts/check_docs.py` soft-ratchets at 20 and `check_current_state_ledger.py` treats as present. *(Thematic grouping by date means the live/archive PR-number spans overlap slightly — the floor pointer is approximate prose, not a strict bound; the per-band pass records carry the exact moved sets.)* *(The twenty-first Q-0107 pass — band-#1320, 2026-06-22 — added the band #1294–#1320 work as seven grouped entries (fishing minigame #1296/#1298/#1299/#1301/#1303/#1304, role management #1300/#1302/#1306, help surface #1294/#1297, BTD6 answerability #1295/#1316, botsite React PR1 #1305, CI/ledger/tool-pin hygiene #1308/#1317/#1320, dependency bumps + dashboard #1307/#1309/#1311/#1312/#1313/#1314/#1315); trimmed the live ledger to 20, moving #1208-band · #1226-band · #1211-band · #1210 · #1203-band · #1209-band · #1183-band to the archive.)* *(The twentieth Q-0107 pass — band-#1290, 2026-06-22 — added the band #1265–#1291 work as six grouped entries; trimmed the live ledger to 20, moving #1186 · #1156-band · #1147-band · #1143-band · #1162-band · #1149-band to the archive.)*

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- **Website two-site split — rollout + next steps:**
  [`operations/website-split-next-steps-2026-06-19.md`](operations/website-split-next-steps-2026-06-19.md)
  is the live handoff: the v1 build is **code-complete + reviewed** (#1109–#1119, hardened by #1122), and
  what remains is the owner-paced **rollout** (provision `botsite/` + the submissions DB, then domain
  cutover), the 3 review flags (moderation race · web-CI matrix · idea→subsystem mapping), and two
  security-review-gated slices (control-panel migration · live status aggregator).
- **Cross-area sequencing + the plan index now live in [`docs/roadmap.md`](roadmap.md)**
  (by area, with Now / Next / Later / Someday horizons + gates — where to find which plan
  for which part of the code). The picks below are the current top of that list.
- Server-management is **structurally complete** *(bullet corrected 2026-06-10 — it
  still queued PR14 long after the hub merged)*: **PR10 complete** (six slices,
  ADR-008), **PR11** (#570; governance section **deferred** — revisit only with a
  scope decision), **PR12** (2026-06-07), **PR13's deterministic slice** (2026-06-08,
  incl. the migration-059 staging fix), and **PR14 — the unified Server Management
  Hub — shipped 2026-06-08 via #584**. The only remainder is the **gated PR13 AI
  generation layer**. The `docs/planning/server-management-status-2026-06-05.md`
  tracker (re-badged `historical` 2026-06-13 — initiative complete) is the historical
  record; the gated PR13 AI tail lives in [`roadmap.md`](roadmap.md) → Later. Don't duplicate it here.
- Health/diagnostics maintainer live-tests (production AI tool + grouped findings):
  see `docs/subsystems/health-diagnostics.md`.
- **Docs consolidation (Q-0010) — executed 2026-06-08.** Top-level `docs/` is now **16**
  (the 13 binding contracts + `current-state` + `roadmap` + `context-map-tooling`); plans /
  audits / inventories / historical snapshots moved into clustered subdirs behind their
  folios, and `_TOP_LEVEL_DOCS_BUDGET` lowered 41 → 16. Paired with the idea-backlog
  lifecycle + grooming secondary task (Q-0015, `docs/ideas/README.md`) and the binding-doc
  section-ownership convention (`docs/owner/ai-project-workflow.md` §9). The original handoff
  was [`planning/docs-restructure-brief-2026-06-08.md`](planning/docs-restructure-brief-2026-06-08.md).
  Verify merge status on live GitHub.
- Use the canonical subsystem folios for area-specific implementation/planning. The
  2026-06-06 readiness audit classifies stale, gated, and ready workstreams.

## Gates / blocked work

- **Autonomous loop — see the canonical [Control-plane state table](operations/autonomous-routines.md)
  § "Control-plane state".** That table is the single source of truth for the loop's state (does it
  self-fire · `ROUTINE_PAT` · Railway env · dispatch-prompt version · model pins); **do not restate
  its verdict here.** This bullet is a pure pointer on purpose — a control-plane verdict copied into
  this file drifted from the canonical table twice (the band-#870 and band-#930 passes each had to
  re-sync it by hand), so the copy is deliberately gone (idea
  `control-plane-single-source-pointer-2026-06-15`). The live read no in-repo checker can see is the
  `reconcile` trigger-issue author (`menno420` = PAT set & loop self-fires; `github-actions[bot]` =
  PAT unset); `check_loop_health.py` (Q-0135) probes live GitHub for the same truth.
- **Open bugs (bug book):** **BUG-0009** (AI list-answer mislabeling — needs the AI orchestration §7
  deterministic list-builders, plan-level) and **BUG-0011** (Hermes gateway restart crash-loop — needs
  a clean VPS foreground repro) stay OPEN — [`health/bug-book.md`](health/bug-book.md).
- **Open decisions:** **Q-0096** remainder (Context7 adopted #737; **Postgres-MCP + `pyright-lsp`**
  undecided) · **Q-0120/Q-0121** (the workflow pass's proposals — candidate-rule promotion · Hermes
  bug-triage `gh issue create` write). *(**Q-0119 answered 2026-06-13** → governance role pointers
  get their own reserved-namespace `governance` schema home (option a); P0-3 family 3 is unblocked
  for a future arc PR — router §Q-0119 + the [convergence plan §5](planning/settings-pointer-lane-convergence-plan-2026-06-13.md).)*
- **AI / BTD6 feature expansion — re-postured 2026-06-09 (Q-0048):** AI tools that are
  **read-only AND deterministic** (no writes, no external calls, audience-tiered) carry a
  **standing lift** and may ship without a per-case ask. Anything that **writes, costs
  money, calls external services, or adds UI** still needs the per-exposure lift, and broad
  expansion stays gated on *all* of: bot-wide stability **+** provider/provenance checks
  **+** caching / source-health clarity **+** AI behavior/config correctness.
- **BTD6 data extraction** — ADR-006 provenance schema **now implemented**
  (`docs/btd6/btd6-provenance-schema.md`); extraction may resume against the ordered
  backlog in `docs/btd6/btd6-gamedata-decode-status.md`. The broader AI/BTD6
  feature-expansion gate (stability + provider/provenance + caching + AI config) still
  applies.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Server-management member/role UX follow-ups: see
  `docs/subsystems/server-management.md`.
- Dense DiagnosticCog platform-subview pagination idea: see
  `docs/subsystems/health-diagnostics.md`.

## Near-term technical debt (decided, not yet implemented)

*(The Q-0025 `new_subsystem.py` scaffold that used to sit here is reconciled: built
and used to register Community Spotlight in **#626** (execution-plan Lane 1,
2026-06-09 — verify merged on live GitHub).)*

*(The Q-0026 `cog_name_to_subsystem` fix that used to sit here is reconciled: merged
in **#588**, listed under Recently shipped.)*

## Off-limits / do-not-propose

- No Redis / external state store (**ADR-001**).
- Game state is **not** restart-safe by design (**ADR-002**) — accepted, not a bug.
- Do not re-litigate the rejection ledger in
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6.
- Do not restate "bot fully tested & working" as *newly* verified without an actual
  boot + live walk — cite the #535 baseline instead.
- **No monetization that gates features** — no paywalls, premium/VIP feature tiers, freemium
  feature-gating, subscriptions, or pay-to-win (**Q-0190 North Star: free for everyone, forever**;
  generalizes Q-0039 no-P2W / no-billing). The *only* allowed money surface is a voluntary
  *zero-benefit* support/sponsor link to offset hosting + AI cost. Full statement:
  [`ideas/free-for-everyone-mission-2026-06-21.md`](ideas/free-for-everyone-mission-2026-06-21.md).

## Where to read next

The **canonical read path + "what lives where"** lives in
**`docs/AGENT_ORIENTATION.md`** ("Reading order by task" + the document-classification
lists). This file is *step 3* of that path: read it for **what is true right now**, then
follow the orientation route for your task. The read-path table is **not** duplicated
here — one canonical home (`AGENT_ORIENTATION.md`).

**One-fact-one-home rule:** if a fact belongs in one of those homes, **link** to it —
do not restate it here. Restatement across files is where drift breeds. In particular,
**don't summarize plans'/trackers' PR numbers or status here** — link to the folio or
tracker, which is authoritative for its own area.
