# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action — one live queue:** the **[band-#870 decade queue](planning/reconciliation-pass-2026-06-14-band870.md)** §4 — the seventh Q-0107 pass (2026-06-14; the band-#870 cadence fire, cadence now every 30th PR per Q-0134). *(Pointer references the pass by name, never by a PR-number range — a range here silently masks the band from the ledger guard; see [the band-#800 pass §6](planning/reconciliation-pass-2026-06-13-band800.md).)* **The P0 integrity spine AND P1-2 are now COMPLETE; the next band finishes the P1 tier (eval-matrix offline half + Layer B, P1-3 invariants) and reserves a slot for the active autonomous-loop / Hermes thread (Railway log-triage skill).** **The production-hardening P0 integrity spine is now COMPLETE** (P0-2 ✅, P0-3 ✅, P0-4 ✅ — every gating decision answered): **P0-4** (channel-ownership convergence, Q-0100) — PR 1 (#820) clone + permission-overwrite, PR 2 (#825) ad-hoc channel creation + category lifecycle through `ChannelLifecycleService`; **P0-2 media retention (Q-0099, #829)** — bounded metadata projection at the cache write + the scheduled `MediaMaintenanceCog` purge owner + thumbnail-URL validation; **P0-3** (delegated-Setup apply, #817). **The standing priority now advances to the P1 correctness tier, integrity-first: next = P1-1 eval-smoke matrix** (versioned AI/BTD6 gates/fallback/grounding-refusal, relates BUG-0009) → **P1-2 health findings lifecycle** → **P1-3 invariants**. P0-2 follow-ups: **content-free media diagnostics now SHIPPED** (PR #854 — `!platform media` + the `media` diagnostics provider + cache-health/provider-outcome counters, content-free); the remaining two (provider-execution hardening · maintainer live-verification) stay queued behind P1-1. **P0-3 is complete: arc PR 3 shipped the delegated-Setup apply authority (Q-0098) in #817** (arc PR 2 retired the XP-announce + economy-log scalar pointers in #794; arc PR 1 foundation #777). **The owner's active strategic thread is the [portable substrate-kit](planning/portable-substrate-kit-extraction-2026-06-13.md)** (OSS agent-memory/workflow package; PR 1a+1b DONE, resume at the 1b tail → PR 2) — it consumed the #781–#800 band and runs in parallel as owner-steered. The safety/community band (slots 4–6: #772/#774/#775) is **COMPLETE**; its remainder (security tiers 1+2 · image-mod · welcome phase 2) is plan-first behind the P0 spine. Product lanes (mining/BTD6/AI) stay open as owner-steered alternates. The full scorecard + deferred list live in the queue doc; [`roadmap.md`](roadmap.md) stays the index, now organised **by sector** (S1–S5 dispatch queues). **Status is per-lane below — a session edits ONLY its own lane's bullet** (convention: [`owner/ai-project-workflow.md`](owner/ai-project-workflow.md) §9 "Cross-cutting ledger discipline"). **Owner-teed sector mapping DONE (2026-06-14, PR #877):** the roadmaps/plans are now organised under the **S1–S5 planning sectors** as **per-sector dispatch queues** — each sector a Hermes-dispatch target (name a sector + an action, read its live `Now`) — [`roadmap.md`](roadmap.md) § "By sector — the live dispatch queues" + the dispatch contract in [`repo-sector-map.md`](repo-sector-map.md) § "dispatch targets"; the [brief](planning/next-session-sector-roadmap-mapping-2026-06-14.md) is executed. Hermes/routine *wiring* stays Q-0137 Thread 1 (owner-undecided). **#704 live-test screenshots triaged + closed** (2026-06-14): mostly-working bot; one AI capability/grounding-consistency finding feeds P1-1 — [`audits/pr704-live-test-triage-2026-06-14.md`](audits/pr704-live-test-triage-2026-06-14.md).
>
> - **Consolidated batches:** **Batches 1–8 ALL executed + verified merged 2026-06-10** ([EOD verification](audits/past-day-verification-2026-06-10.md)) — #650 truth/clarity · #651 surface-classification invariant · #652 service boundaries · #654 Settings Phase 2 core · #656 adaptive P1C subpanels · **#657 Help projection seam** (HLP-2: `services/help_catalogue.py` + `services/help_projection.py`, all five render paths on one reason-coded `HelpProjection`; Q-0074 executed in the same PR) · **#659 HLP-3 guild overlay** (migration 064 `help_overlay`, audited `help_overlay_mutation` seam, cached read model, hide/rename through every render path; Q-0055 display-only pinned by an admission import fence) · **Batch 7 via the mining stack** (#661 + #663/#664/#665 → #667) · **Batch 8 = the #649 cutover**. **The queue-remainder session (PR #671, merged 2026-06-10) executed the RS07 chain-service slice** (audited `services/chain_service.py`, Batch 3 pattern, repo-wide write fence) **+ Batch 9's RS08 slice** (diagnostic read models out of the cog layer; new no-raw-SQL-in-cogs/views invariant) **+ the EOD audit's Tier-2 Help-Preview fix** (now consumes `project_help_with_execution`); **its continuation (PR #672) completed Batch 4** (proof-channel binding/resource declaration + binding-first read; logging rows verified satisfied) **and executed the Batch 10 selections** (wizard PR1–PR3 tranche verified shipped via #435 → setup-lane next = PR4 `/myprofile` planning session; next AI §7 family = **§7.5 multi-entity comparison**, sequenced after the maintainer's prod check — banners in the two plans carry the evidence). **The Help overlay editor UI executed 2026-06-10 ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → PR A #677 + PR B #679, both MERGED same day):** the hide/rename/re-describe editor (staff-hub `✏️ Help editor` button + the Settings-hub "Help appearance" domain group, 13th group) and the Q-0059 Home-message embed builder (migration 067, **mandatory preview**, shared `home_embed_frame` composer, byte-identical default pinned) — both live-verified on real Postgres. **Batch 9 then executed in PR #681** (open at write time): the RS05 publish-accepted delivery contract (runtime_contracts §2) + bus delivery stats / failure metric / the `event_bus` diagnostics provider, and the RS10 economy view family onto BaseView (conformance ratchet 17→13, arch warnings 84→80). **The consolidated plan's queue is FULLY EXECUTED (Batches 1–10; #681 MERGED).** A follow-on slice (PR #682, open at write time) migrated the **mining family** onto BaseView — the last true lifecycle-duplication family; ratchet 13→11 with a disposition note (remaining direct-View entries are ephemeral pipeline-gated follow-ups / bespoke admin checks, not RS10 duplication). **The PR4 `/myprofile` planning session ran (PR #684, open at write time):** [`planning/myprofile-foundation-plan-2026-06-10.md`](planning/myprofile-foundation-plan-2026-06-10.md) — §6 backend re-verified exact (4 audited pipeline entrypoints, typed accessors, schema registry, zero UI callers); PR A = read-only profile card (zero writes, turn-key) · PR B = the pipeline's first UI consumer · PR C onboarding **gated** on an owner decision; Q-0080 stranger-grade envelope applied throughout. Remaining plan-first/gated: Help audit Phase 4 records (Q-0057 rider) · AI §7.5 (post-eval).
> - **BTD6 data + answerability:** the `--all` cutover **#649 merged 2026-06-10; post-cutover VERIFIED + every carry-forward DECODED the same day** (#653 wave 1 ∥ PR #655 — dump fidelity byte-identical · 2,022 menu embeds in-limits · AI battery green · `_CUTOVER_CARRYFORWARD` empty, audit 91 CLEAN / 0 DELTA / 0 SUSPECT · banana economy answerable · fixes for mode-rules dark data / `!btd6 diagnostics` 400 / stamp-rot / path leak); **answerability items 5+6d shipped in PR #658**; **the Navarch "no coins" live miss diagnosed (missing ROUTING, not data) + fixed end-to-end with items 6a–c — #662 MERGED 2026-06-10** (paragon grounding gains income + effect lines · article-tolerant/shorthand paragon names · minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV) · Pouākai diacritic-fold · honest dataset source labels/summary); follow-up slice **#666** adds `scripts/btd6_probe.py` (grounding triage) + structures item 7 into [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md); **item 7 slice 1 (conversation carryover) + the zero-fact sweep fixes (ranking rosters · bare distinctive shorthand) shipped same day in #668**. **The 2026-06-11 morning screenshots (3 live AI-knowledge misses) fixed end-to-end in PR #703** — BUG-0002 (elite boss HP: dataset had no elite figures + boss names never routed BTD6 → standard table served as "Elite"; elite_tiers backfilled from the pinned v55.1 dump for all 7 bosses, boss canonicals route + name-index, variant-labeled grounding) · BUG-0003 ("despos on impop" hallucinated as PMFC; impop/despo keywords, Desperado alias, resolver plural fold, the `<quantity> <crosspath> <tower>` pricing leg — "10 041 despos" = ten 0-4-1s, owner-corrected) · BUG-0001 recurrence (round-cash refusals in #general: the workflow was profile-gated OFF on default channels — compatible_default/balanced_helper now declare analyze_execute_verify (Q-0048), matcher gained the money-question gate + by-round anchors). **Owner action: run `!btd6ops seed-data` after the deploy** (bosses/towers json are blob-lane data; owner-confirmed done 2026-06-11 ~12:38 — despos answers correct in prod). **The live re-test round shipped in PR #706 (merged 2026-06-11):** BUG-0004 (r-shorthand rounds + "end of r53" start shift — the $71,315.20 cumulative mislabel; truth $56,318.70) + the bulleted capabilities list (owner format ask; boss_health/crosspath/projection rows advertised). **The absence-claim guard's Layer A (path/line-aware retrieval) shipped in #855** — `<tower> <top|middle|bottom> path` phrasing now grounds its whole tier line instead of resolving to nothing (the canonical false-"no" trigger removed at the root); Layer B (the negative-existential gate) stays design-for-review. **Next:** decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check) · P1-1 eval-smoke matrix (creds-gated) + absence-guard Layer B.
> - **Gated:** the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table.
>
> *(The 8-lane scoreboard completed 2026-06-09/10 — record: [`planning/multi-lane-execution-plan-2026-06-09.md`](planning/multi-lane-execution-plan-2026-06-09.md), now `historical`.)*
>
> 1. **Mining character platform** — **the 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed in one 4-PR stack — all four merged 2026-06-10:** **#661** (RS01 — atomic shop-purchase workflow + the Q-0071 transaction plumbing) → **#663** (RS02 stage 1 — pure domain relocated to `utils/mining/`, `services/mining_workflow.py` owns the workshop ops, views→cogs allowlist entries deleted) → **#664** (RS02 stage 2 — *every* mining write behind the workflow service, one transaction per op; AST ratchet; recipes.json reconciled to the catalog under a new alignment lint — **Batch 7 COMPLETE**) → **#665** (shared **game-XP** service + leaderboards + depth records (migrations 065/066) · **deeper ladders** incl. the diamond lantern that makes MAGMA reachable (it never was) · Gear panel + Recipe browser + fuzzy names + `!fastmine` · **duels gear wear — Q-0054 CLOSED** · PIL inventory + stat cards). Session decisions: **Q-0075** (curated economy + deeper ladders) + **Q-0076** (both PIL cards) — router §32. *(Merge mechanics note: the stacked bases didn't auto-retarget, so #663/#664/#665 merged into their parent branches — the content reached `main` via the same-day completion PR **#667**, content-verified EOD; migrations renumbered 065/066 around #659's 064.)* Earlier Wave-1 chain: #606–#610, #624. **The V-16 phase-1 gear slice shipped 2026-06-11 (PR #702, full Q-0092 scope):** 9-slot set-piece model (+ migration 068 legacy fold) · same-tier set bonus with set-aware Equip Best + "breaks set" picker warnings · bronze/silver ores · sim-pinned numbers ([record](planning/gear-set-numbers-2026-06-11.md)) · picker stat previews · the paper-doll compositor (placeholder sprites; owner pack drops into `disbot/assets/gear/`). **Next slice: V-16 phase 2** (owner's PNG pack + anchor tuning) **or structures §7.5 (Forge/Vault/Home)**, then the §7.4 skill tree (its `game_xp` substrate now exists). Route in: `docs/ideas/mining_exploration_brainstorm.md` §7.7 + the games folio.
> 2. **Adaptive Setup/Access platform** — Phase 0 complete; Phase 1 underway: Q-0026 identity repair + Phase 0 contracts **#588**, P1A Access Map projection **#589**, P0C groundwork **#591**, P0C seam conversion + P1B `routing_access_conflict` **#592**; **P1B remainder shipped in #632 (2026-06-09, execution-plan Lane 2 — verify merged on live GitHub):** the Q-0045 governance tier-input path (`GovernanceContext.member_tier`, declared tier preferred verbatim, simulation-labeled per §16.4) + the `help_advertises_locked` drift provider + the full Q-0036 denial-copy **draft** (in the PR body for maintainer read-through — **not live-wired**; wiring follows his markup). **P1C merged 2026-06-10 (consolidated plan Batch 5, #656):** Access Map + Help Preview shipped as **staff-hub subpanels, no new command names** (Q-0032), on the tier path as-is. **The Batch 6 Help projection seam consumed this lane 2026-06-10 (#657, merged):** Help's five render paths now compose governance + the projection contract end-to-end (`services/help_projection.py`, incl. an execution-enriched mode over `access_projection`). **Next: P2** Feature Profile preview (own planning first). Q-0028–Q-0031 + Q-0033 are also **answered** (catalogue committed · availability owns quiet mode · snapshots compound+high-risk · risk policy approved · account links deferred — router §20). Route in: plan §16.8.
> 3. **AI tooling (orchestration + answerability)** — orchestration Phases 1–3 shipped (**#612**, **#618**, **#619** — including the gate-lifted `ai:tools` Tools & Workflows operator UI; default byte-identical); answerability Phase 1A/1B (**#612**, Q-0043: range cash **inclusive**) + Phase 2 read model (**#616**) shipped. **Orchestration Phase 4 MVP (Q-0046) built 2026-06-09 in PR #634** (execution-plan Lane 3, parallel session): the round-cash plan→execute→verify workflow + the one typed answer-with-evidence contract, profile-gated, default byte-identical — **model loop awaits the maintainer's production check** (no sandbox provider key). **Answerability Phase 3 shipped 2026-06-09 in PR #639** (execution-plan Lane 4, **Q-0047**): the three read-only self-awareness tools — `get_ai_tool_catalog` ("what can you do here?") · `get_ai_policy_explanation` ("why didn't you reply?") · `btd6_answerability` ("what BTD6 data do you know?") — audience-tiered **at construction** over the #616 read model; **model loop awaits the maintainer's prod check** (no sandbox key). **Next:** the remaining orchestration §7 workflow families; answerability Phases 4/5 stay gated (settings UI per-exposure ask · dashboard schema acceptance). Standing posture **Q-0048**: read-only deterministic tools ship without a per-case ask; writes/external/UI stay per-exposure. Plans: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) · [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **The first Q-0086 joint live session ran 2026-06-11 (PR #707): the model-loop gate is LIFTED** (keys in agent sessions; full loop verified on both providers); BUG-0005…0008 fixed live (tool quantity laundering · carryover routing/forcing · conversation-meta floor copy + guard haystack · farm/possessive/double-cash routing); **BUG-0009** (claim assembly) OPEN in the [bug book](health/bug-book.md); **BUG-0010 (ABR qualifier) FIXED same day in the follow-up slice (PR #709** — shared ABR cue → grounding round legs + the round-cash workflow compute/label the ABR set, modifier honesty deterministic**)**; **Q-0094** (memory floor canon) + **Q-0095** (Haiku-4.5 allocation for the two NL tasks · the guild-default-provider trap · sandbox floor-testing posture) recorded; the owner-requested **AI panel rework** captured ([idea](ideas/ai-panel-inplace-navigation-2026-06-11.md)). Gear/mining (#702) is still never owner-played — the eval-checklist Tier 2+ walk stays queued.
>
> Cross-cutting: **Community Spotlight** (side-lane **#613**/**#614** + hotfixes **#615**/**#617**) was hardened in the review session (canonical `utils/db/xp.py` read, `member_count` crash fix, first tests) and **Q-0044 is executed**: the Q-0025 `scripts/new_subsystem.py` scaffold was built and used to register Spotlight as a `community`-hub child (**#626**, 2026-06-09 — execution-plan Lane 1; merged, verified live), and the `!hub`/`!server` aliases were **dropped same day** (kept `!spotlight`/`!activity`). Also decided: BTD6 data-refresh automation = **manual-dispatch workflow** (Q-0049 — **built same day in #633**, execution-plan Lane 5: `workflow_dispatch`-only, opens a reviewable PR, never pushes to main); mining descent lights **permanent, owner-confirmed** (Q-0050); the five product-vision questions (Q-0038–Q-0042) got their **draft-answer session** (Q-0051) **and the maintainer marked all five up same day (Lane 6, PR #631, structured choices)**: Q-0038 server-scoped clans, Q-0039 cosmetic-only donations (no bot-side billing), Q-0041 YouTube-first/dual-opt-in/voice-deferred, Q-0042 staged-Someday website — all approved as drafted; **Q-0040 adjusted: the AI dungeon master picks quests/rewards/difficulty from bounded, hard-capped menus** (not pure narration, not free-form authority). Posture decisions only — every lane still needs its own plan/promotion + the AI per-exposure lift; conclusions routed to the four roadmap drafts + router §21. Full repo review: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md) · agent-memory system review (did the orientation/memory system work in practice?): [`audits/agent-memory-system-review-2026-06-09.md`](audits/agent-memory-system-review-2026-06-09.md).
>
> **Last updated:** 2026-06-14, **sector tooling — the partition is now self-maintaining (PR #882)** —
> closed the loose ends from the dispatch work: `scripts/check_sector_map.py` (validator — folio homing
> + executor + startability convention, was prose-asserted) and `scripts/dispatch_menu.py` (resolver —
> the machine version of the dispatch test: per sector, the first ▶ startable item + executor, flags a
> starving/blocked sector). Both stdlib, read-only, disposable (Q-0105), tested (19 tests); not CI-wired
> (ask-first). Building `dispatch_menu` caught a real convention bug (a ▶ glyph used in S2 `Now` *prose*,
> not as an item tag) — fixed. CI green (9664); arch 0. ·
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
> next P0 = P0-4 channel-ownership.** CI green (9442); arch 0; real-Postgres + clean-boot proven. ·
> 2026-06-13, **fourth Q-0107 reconciliation pass (the band-#800 cadence
> fire)** — scored the just-merged band (2/10 planned P0-spine slots executed — the owner's
> **portable substrate-kit OSS arc** + the **native auto-merge migration** consumed it),
> planned the next ~9 PRs ([band-#800 decade queue](planning/reconciliation-pass-2026-06-13-band800.md)),
> and **fixed a masking ledger drift**: a forward-looking PR-number range in the `▶ Next
> action` pointer had hidden ~14 merged PRs (the whole substrate-kit arc + the auto-merge
> migration) from the `check_current_state_ledger` guard, which reported
> green while the ledger was short — added their real Recently-shipped entries below and
> **dropped the range from the live pointer** so it can't recur (pass doc §6). Re-badged the
> third pass `historical`; marker reset #780→**#800**. No new runtime bugs. ·
> 2026-06-13, **hardening P0-3 arc PR 2 — retired the XP-announce +
> economy-log scalar pointers (PR #794)**. Deleted both editable scalar
> `SettingSpec`s so each Discord-resource pointer has one canonical binding owner; repointed
> the writers (XP channel modal, economy `_record_log_channel` ×3) + the stale legacy reads
> (XP config panel, economy `_ensure_log_channel`) to the binding lane. **Design fix:** a
> *retired* pointer reads binding-first regardless of the OFF-by-default `bindings.primary`
> flag (new `config_arbitration` `pointer_retired=True`) — so the retirement deploys safely
> with no coordinated flag flip; legacy KV stays the rollback fallback. Extended
> `BindingMutationPipeline` for `actor_type='system'` writes (the economy auto-provision);
> fixed two adjacent binding-name bugs (`logging_presets.py` + `channels.py` keyed the
> economy/xp channel bindings by their legacy *settings* keys); emptied `CONVERGEABLE_POINTERS`
> + added the `test_no_dual_declared_pointer` invariant. CI green (9328); arch 0 errors; proven
> on real Postgres + clean boot. Next P0 = arc PR 3 (delegated-apply, Q-0098).
> · 2026-06-13, **third Q-0107 reconciliation pass** — the first
> cadence pass **auto-fired by the `reconcile` issue trigger** (#781), proving #778's self-fire fix.
> Band #761–#780 scored (**7/10 slots to plan** — safety band 4–6 COMPLETE + P0-3 foundation #777;
> the two unplanned items #778/#780 were both high-value), the **next ~9 PRs planned integrity-first**
> ([decade queue for that band](planning/reconciliation-pass-2026-06-13-q0107.md)), the night-pass
> record re-badged `historical`, marker reset #763→**#780**, and the **`▶ Next action` line tightened**
> from a ~15-line history wall to one scannable priority (the system improvement). No new runtime bugs.
> · 2026-06-13, **workflow reconciliation + hardening pass** —
> a by-judgment Q-0107-style pass: re-badged 2 executed ideas + the server-mgmt tracker `historical`,
> routed the loose ideas (backup-integrity → tooling PR · bot-self-test-walker → Later · hermes-bug-triage
> → Q-0121), proposed the journal's earned candidate rules (Q-0120), added the **Control-plane state
> ledger** to `autonomous-routines.md`, and reconciled the #778 ledger gap. Record: [`planning/reconciliation-pass-2026-06-13-workflow.md`](planning/reconciliation-pass-2026-06-13-workflow.md).
> · 2026-06-13, **fix: routine-trigger author → `ROUTINE_PAT` (PR #778)** — root-caused why the
> autonomous loop never self-fired (bot-authored trigger issues don't start a routine); inert until the
> owner adds the secret. · 2026-06-13, **hardening P0-3 settings pointer-lane convergence
> (PR #777, foundation)** — the carried hardening spine's next slot, behavior-preserving.
> Root-fixed the broken governance-role backfill (reframed the permanently
> `BLOCKED_NO_SCHEMA` `MIGRATED_KEYS` into honest `MIGRATED_KEYS`/`DEFERRED_KEYS` — the
> `governance` reserved-namespace finding), added two parity invariants (backfill-target
> declaration + the **pointer-lane ratchet** that catches new pointer-as-scalar additions
> like #775's welcome/counters), the `scripts/settings_lane_matrix.py` inventory tool, and
> the [convergence plan](planning/settings-pointer-lane-convergence-plan-2026-06-13.md)
> (migration order · delegated-apply contract Q-0098 · smoke checklist). Router **Q-0119**
> (OPEN): the governance role-pointer binding home. Scalar retirement + delegated-apply
> impl = arc PRs 2–3. · 2026-06-13, **welcome v1 + server counters (PR #775, band slot 6 —
> Q-0110)** — the safety/community lane's final two slices, as **two hub-less new
> subsystems**. **welcome** (`services/welcome_service.py` + `welcome_config.py`): greet on
> join · optional farewell on leave · optional **entry role** granted on join through the
> audited `role_automation` seam; embed-first ({user}/{server}/{count} templates, the PIL
> card stays phase 2); listeners on `WelcomeCog`. **counters** (`services/counter_service.py`
> + `counter_config.py`): statdock-style channel renames (total/humans/bots) on a slow
> `tasks.loop` — **never per join** (Discord's ~2-renames/10-min cap) + change-detection.
> Both default OFF; advisory `welcome.member_greeted`/`counters.updated` events; deliberately
> hub-less (surfaced via Help hook + `!settings` + `!welcome`/`!counters`, like
> `ai`/`channel`/`ux_lab`) so they don't clutter the user-tier Community hub. No migration.
> **The safety/community band (slots 4–6) is COMPLETE; next = the carried P0-3/P0-4/P0-2
> hardening spine.** · 2026-06-13, **native auto-merge migration (PRs #779 + #786, Q-0123)** —
> merge mechanics moved off the Claude session: `auto-merge-enabler.yml` arms GitHub-native
> auto-merge on every non-draft `claude/*` PR so it merges itself on green `code-quality`,
> attributed to the owner via the now-widened `ROUTINE_PAT` (which also unblocked the PAT-less
> routine triggers — the secret had never existed); the Q-0084 self-merge envelope is struck
> from CLAUDE.md. Proven live on #786 (hands-off, ~15 s). · 2026-06-13, **server event logging v1 (PR #774, band slot 5)** — the
> passive-event layer of `services/server_logging.py` (Q-0109): message edits/deletions ·
> member joins/leaves · role grants/revocations, gated by the master `logging.enabled` + a
> per-category flag (all default OFF), with owner-configurable combined-vs-per-category
> routing (`logging.event_routing`) on the shared route table; listeners on `LoggingCog`,
> read model in `services/server_logging_config.py`, schema v3, no migration; deleted-message
> privacy disclosed in the setting hint + the setup wizard. Next band slot = **welcome v1 +
> counters (slot 6, Q-0110)**. · 2026-06-13, **safety/community family plan + automod v1 (PR #772, band slot 4)** — the lane's [family plan](planning/safety-community-family-plan-2026-06-13.md) entry doc + automod v1 (spam/invite/caps/mass-mention filtering, new `automod` subsystem, all flags default OFF, routes through `moderation_service`); next band slot = **server event logging v1 (slot 5, Q-0109)**. · 2026-06-12 (night), **P2 doc-drift sweep (PR #764, band slot 2)** — all five readiness-map P2 fixes landed (smoke route · AI README · ADR-006 addendum · media-folio honesty · flag owner per ADR-007); next band slot = **backup posture**. · 2026-06-12 (night, second pass), **the second Q-0107 reconciliation ([record](planning/reconciliation-pass-2026-06-12-night.md))** — band scored (the two owner-steered arcs consumed it; hardening+safety queue carried intact), the #753–#761 autonomous-loop arc ledger gap reconciled, **both checkers' shared "Merge PR #N:" regex blindness root-fixed** (the ledger check had been green while five PRs were missing), marker → #762, next pass at #780. · 2026-06-12 (late night), **the UX Lab BUILD (PRs #758/#760/#762, Q-0116)** — the owner steered "start building it" and the full 3-PR plan executed + merged in one session; `!uxlab` live, [`ux/pattern-library.md`](ux/pattern-library.md) is the new design-vocabulary export; **the Q-0107 reconciliation pass is now overdue** (crossed #750 — next session or the #752 Routine). · 2026-06-12 (night), **UX Lab design session (PR #755)** — owner-commissioned interface-gallery cog design (plan + Q-0116) + CV2 platform-limit corrections; **the next Q-0107 reconciliation pass is DUE** (merged PRs crossed #750 — next session, or the #752 nightly Routine if wired). · 2026-06-12 (evening), **the first Q-0107 reconciliation pass (PR #741)** — every #715–#740 plan mapped, the decade queue set ([pass record](planning/reconciliation-pass-2026-06-12.md)), ledger + roadmap drift fixed; stamp-line history older than 2026-06-11 moved to [`current-state-archive.md`](current-state-archive.md) § Stamp-line history. · 2026-06-11 (afternoon), **first Q-0086 joint live-testing session (PR #707)** — model-loop gate lifted, BUG-0005…0008 fixed live, BUG-0009/0010 opened, Q-0094/Q-0095 recorded — see the AI lane bullet. · 2026-06-11, **AI-knowledge bug session (PRs #703 + #706 + process record #705): the morning's 3 live misses + the re-test round's BUG-0004 + the capabilities format fixed** — see the BTD6 lane bullet above. · Earlier same day: **gear-lane session (PR #702): V-16 phase 1 executed** — see the mining lane bullet above; this stamp line otherwise preserves the 2026-06-10 marathon record below.

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
> **Last reconciliation pass:** PR #870 (2026-06-14, seventh Q-0107 cadence pass —
> [the pass record + decade queue](planning/reconciliation-pass-2026-06-14-band870.md)). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #900 (every
> multiple of **30** — Q-0107 cadence raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
> Q-0134; `check_reconciliation_due.py` flags it, and `.github/workflows/reconciliation-trigger.yml`
> auto-opens a `reconcile` issue at the boundary that fires the docs-reconciliation routine). Reset
> this marker to the latest PR after a pass.

- **#878 + #879 (2026-06-14, P1-1 — versioned AI eval/smoke matrix, offline half + its drift guard)**
  — the standing #1 priority's deterministic, CI-gated half. The live golden set
  (`tests/evals/cases.py`) is creds-only (`scripts/run_evals.py`), and CI exercised only the harness
  *machinery* — there was no CI proof of the AI path's **deterministic contract**. **#878:** new
  **`tests/evals/smoke.py`** drives the **real gateway** with scripted providers (no API) — 16 cases
  across **gates · fallback · tool-dispatch · audit-visibility · safety · redaction · config** —
  gated by `tests/evals/test_smoke_matrix.py` on every PR, and rendered as one **versioned scorecard**
  (`scripts/run_evals.py --smoke`, creds-free); both halves version-stamped (`GOLDEN_SET_VERSION` /
  `SMOKE_MATRIX_VERSION`); the **#855 Layer-A** MOAB-path probe added to the golden set. **#879:** an
  **eval-coverage drift guard** (`tests/evals/test_eval_coverage.py`) — a self-cleaning ratchet so a
  new canonical AI tool/`AITask` can't silently fall outside the matrix (referenced ∪ acknowledged ==
  surface; coverage floor; meta-tested to actually fire). `check_quality --full` green (9645); arch 0.
  **Still owed (P1-1):** the live-quality battery (needs prod creds) + absence-guard **Layer B**
  (design-for-review).
- **#870 + #869 + #868 (2026-06-14, Hermes operating-layer hardening arc)** — three docs-only PRs
  maturing the Hermes autonomous-loop control plane. **#868 (Q-0142):** fixed a real misread — a
  stale reconciliation dispatch fired because a decade-queue slot was read as a reserved PR number;
  Hermes' dispatch skill + operating prompt now pick the next slice **by description verified
  against the live ledger**, never a predicted PR number (the band-#870 queue §4 banner restates
  this). **#869:** Hermes' VPS skills (dispatch / log-triage / repo-health / skill-author +
  `build_skills.py`) run stdlib-only tooling under the VPS's `python3`, not the repo's CI-pinned
  `python3.10`. **#870:** recorded the verified deadsnakes **Python 3.10 VPS prerequisite** in the
  Hermes control-plane doc. Docs only.
- **#867 (2026-06-14, ledger: ad-hoc band #841–#860 window catch-up)** — an *ad-hoc* ledger-hygiene
  reconcile **between** cadence passes (not a Q-0107 pass — it did not reset the cadence marker or
  write a planning doc, correctly): added eight live `Recently shipped` entries
  (#866/#865/#864/#863/#862/#859 + the #856+#853 and #851/#850/#848/#852 groups) and archived eight
  old ones into [`current-state-archive.md`](current-state-archive.md). Docs only.
- **#866 (2026-06-14, #704 live-test triage + close + sector-roadmap handoff)** — triaged all
  11 PR #704 live-test Discord screenshots (2026-06-11): verdict **predominantly working**
  (mining/crafting RPG + BTD6 hub functional and polished). One substantive finding — the BTD6
  capability message ("round cash per-round/range") **over-states** vs. the bot's correct
  grounding-refusal on round-economy questions, plus a grounding-consistency check (asserted Despo
  price / Elite Lych HP must be confirmed grounded) → routed to the active **P1-1 eval-smoke** lane.
  Wrote [`audits/pr704-live-test-triage-2026-06-14.md`](audits/pr704-live-test-triage-2026-06-14.md)
  and **closed #704** (findings preserved; images stay in git history). A chat sweep confirmed the
  day's substantive items (Q-0134–Q-0141, sector map, refreshed operating prompt) are captured. Docs only.
- **#865 (2026-06-14, fix: robust `routine_fire.py` dispatch helper — Q-0141)** — live-testing
  Hermes' new operating prompt, Hermes diagnosed a **real bug**: the dispatch skill's inline
  `curl -d "$(python3 -c … "$WORK_ORDER")"` is shell-quoting-fragile for multi-line work orders.
  The owner then decided **Hermes may write its own code (Q-0141)**, making it a parallel build.
  `scripts/hermes/routine_fire.py` (stdlib-only) takes the work order on **stdin** (zero shell
  quoting), loads `CLAUDE_ROUTINE_*` from env / `~/.hermes/routine.env`, POSTs `{"text": …}`,
  **never prints the token**, and supports `--dry-run`; plus a bounded-work prompt addition.
- **#864 (2026-06-14, tooling: harden the ledger drift guard — band-#840 slot 9)** — two paired
  slices on `scripts/check_current_state_ledger.py` (the very checker the autonomous loop relies on
  to catch `current-state.md` drift between reconciliation passes): (1) it now **prints each missing
  PR's merge-commit subject** beside its number, collapsing the manual `git log --grep "#N"` loop
  every Q-0107 pass ran by hand; (2) **scoped range-expansion to the ledger proper** so a
  forward-looking planning range in the `▶ Next action` pointer can't mask a merged band (the
  band-#800 false-green class, now structural). Pure stdlib.
- **#863 (2026-06-14, Hermes skill-author meta-skill + docs-only-PR write scope — Q-0140)** —
  built the Hermes self-extension layer: the **`superbot-skill-author`** meta-skill
  (`docs/operations/hermes-skills/skill-author.md` + generated artifact; 11 skills) guides Hermes to
  design/write a new skill in the canonical format and **commit it as a docs-only PR**, closing the
  "Hermes-authored skills are VPS-only" round-trip gap. **Q-0140** expands Hermes' sanctioned writes
  to two — review-merge (Q-0117) **+** docs-only PRs (work summary / bug report / new skill source);
  code still routes via dispatch. Operating prompt refreshed. Docs only.
- **#862 (2026-06-14, fix: repair the daily Postgres backup — PGDG pg18 client)** — live-verifying
  the backup (after the owner set `DATABASE_PUBLIC_URL`) drove a real production bug to ground:
  Railway Postgres is **v18.3** but the workflow used the Ubuntu-default client **v16**, and pg_dump
  refuses to dump a newer server with an older client. Fixed in two parts — install the **PGDG v18
  client** (apt default is v16 on Ubuntu 24.04) **and** invoke pg_dump by explicit **highest-version
  path** (`/usr/lib/postgresql/*/bin`, since pg16 at `/usr/bin/pg_dump` shadows it on PATH); both
  future-proof. Verified by dispatching the fixed workflow on the branch ref; documented the
  version-mismatch failure mode in the workflow's failure-issue body.
- **#859 (2026-06-14, docs: 3-tap sector map + hook-vs-rule policy — Q-0137/Q-0139)** — two
  owner-directed substrate pieces. **`docs/repo-sector-map.md`** — the 3-tap nav top layer: **5
  sectors** on a mechanism-vs-content axis — S1 Bot · S2 BTD6 · **S3 AI-Memory system** (the
  *mechanism*, a shippable engine of its own) · **S4 Documentation system** (the *product* the
  engine generates) · S5 Operations (owner's load-bearing clarification: *"the docs are not the
  system, the docs are a product of the system"*). Plus a **hook-vs-rule decision policy** (Q-0139).
  Docs only.
- **#855 (2026-06-14, P1-1 Layer A — BTD6 path/line-aware resolution)** — the first concrete,
  fully-completable slice of P1-1 (the standing #1 priority): the BTD6 absence-claim guard's
  **Layer A** (the design's Recommendation #1, "ship Layer A first"). Path/line phrasing like
  *"bomb shooter middle path"* resolved to no single upgrade (`resolve_upgrade(...)` → `none`,
  re-verified live this session), so the path grounded **nothing** and the model could
  confabulate a false negative ("that path has no MOAB bonus") — the canonical absence-claim
  trigger, a *retrieval* gap (the +15/+30/+99 vs MOAB-Class data is committed and reachable,
  just unqueried). Now `btd6_upgrade_service.resolve_path_reference` detects a `<tower>
  <top|middle|bottom> path` reference (direction synonyms; conservative — needs a tower **and**
  the literal `path` token, so "top tier"/"bottom line" never fire) and
  `btd6_upgrade_detail_service.path_grounding_for_query` grounds a header naming **every tier on
  the path** + each tier's detail (named tiers skipped — Pass 3c grounds those), wired into
  `btd6_context_service.build` as **Pass 3f**. Retrieval only — no guard. **Layer B** (the
  negative-existential gate, §4.3 crux) stays design-for-review + needs prod creds. +22 tests;
  `check_quality --full` green (9579); arch 0. **Next P1-1 = the versioned eval/smoke matrix
  (live half needs prod-like creds) + Layer B.**
- **#849 (2026-06-14, born-red session merge-gate — Q-0133)** — closed the auto-merge race
  that landed **#843** without its ledger entry (native auto-merge, Q-0123, fires the instant
  Code Quality is green, so a session pushing code first and close-out docs second merges a
  *partial* PR). The owner's fix, as refined live: one per-session file that is **both** the
  start-declaration (*what's about to happen*, visible to parallel/next sessions on the open PR)
  **and** the end-record (*what happened*) — the existing `.sessions/<date>-<slug>.md` log —
  whose `> **Status:**` badge gates the merge. Created in the **first** commit as `in-progress`
  (PR **born red**, race-free), flipped to `complete` as the deliberate **final** step → green →
  merge. `scripts/check_session_gate.py` (folded into the required `code-quality` check — no
  branch-protection change) fails when a PR *adds* a session card that isn't ready;
  **engage-when-present** (a PR adding no card isn't gated, so routines / workflow-authored PRs
  never deadlock); only newly-*added* cards inspected. +11 tests; the gate was **dogfooded on its
  own PR** (born red, then flipped). Follow-up: tighten to airtight once routine adoption is proven.
- **#843 (2026-06-14, hardening P1-2 — health findings lifecycle + operational retention,
  Q-0097)** — closed the two **code** gaps in the health/diagnostics readiness map (the
  remaining gap to production-ready is now the owner-led live walk only). Before: in normal
  operation every persisted finding stayed `open` forever (no transition path → the retention
  roll-up was unreachable) and retention ran **only at startup** (a long-lived replica never
  re-swept). Now, **operator-managed (Q-0097)** through the **sole writer**: (1)
  `utils/db/health_findings.set_finding_status` (CTE `UPDATE … RETURNING` the prior status; added
  to the sole-writer AST guard) + `health_findings_service.set_status` (the one transition path,
  `open`↔`resolved`/`ignored`, validates status, emits `audit.action_recorded` on a real operator
  change — system recording stays audit-free) + `!platform finding resolve/ignore/reopen
  <fingerprint>` (admin command, kept **out** of the read-only platform hub). (2) A new
  `HealthMaintenanceCog` reruns `run_retention()` on a daily `tasks.loop` (mirrors
  `MediaMaintenanceCog`); the startup sweep stays. Pinned the platform-hub typed-only exclusion of
  `startup`/`findings`/`finding`. +15 tests; `check_quality --full` green (9551); arch 0; the new
  `set_finding_status` SQL verified on real Postgres. *(The code + Slice-A/B/C doc updates merged in
  #843; this ledger entry + the session-close docs land as a small follow-up — the auto-merge fired
  on the first green before the session-close push, see the session log.)* **Next P1 = P1-1
  eval-matrix** (needs prod-like creds for the live half).
- **#856 + #853 (2026-06-14, external-systems watchlist + workflow-health review)** — **#856:** a
  new **`docs/research/`** home for *external* intelligence (vs. `docs/ideas/` for our own);
  `external-systems-watchlist.md` — 7 lesson-first entries (Voyager · Reflexion · Generative Agents
  · MemGPT/Letta · SWE-agent · OpenHands/Devin · …) a future session can re-check for ideas. **#853:**
  a workflow-health review verifying the autonomous loop fires live + documenting the cron lag. Docs only.
- **#851 + #850 + #848 + #852 (2026-06-14, P0-3 legacy-pointer backfill command + health/routine
  housekeeping)** — **#851/#850:** root-caused the production consistency warning — the
  binding-backfill had **no runtime trigger** (it only ran in tests) — and shipped the **`!platform
  backfill`** admin command to complete the legacy-pointer migration in production. **#848:** the
  startup-health check now **logs finding detail when not healthy** (follow-up to #845). **#852:**
  field-notes improvements for the Hermes-dispatch loop.
- **#840 (2026-06-14, Railway agent-access — live-verify fix: `RAILWAY_API_KEY` alias +
  Cloudflare User-Agent)** — an `auth probe` routine verifying the owner-provisioned Railway
  credentials (the standing next-fresh-session action from the #827–#837 session) found the
  access was **entirely inert** for two independent reasons, both fixed: (1) the credential was
  provisioned under **`RAILWAY_API_KEY`**, a var name `railway_logs.py`/`railway_vars.py` didn't
  read → added it as an account-token alias (`RAILWAY_API_TOKEN` still wins when both are set); (2)
  Cloudflare fronts `backboard.railway.com` and **1010-bans urllib's default User-Agent** → the
  GraphQL transport now sends an explicit non-default UA. **Verified live after the fix:**
  `railway_logs.py --whoami` returns the owner identity, `railway_vars.py list` reads live prod
  vars (masked). +5 regression tests; `check_quality --full` green (9509); arch 0. *(The
  Railway-auth-fix PR referenced by the #827… entry below — this is "below". Its docs-only
  session close-loop merged as **#842**: the `agent-env-credential-smoke-check` Q-0089 idea + the
  Q-0102 review that this exact breakage class sat silent until a routine probed it by hand.)*
- **#839 + housekeeping #838/#833/#830/#826/#824 (2026-06-14, Q-0132 chat-export capture +
  Railway-session ledger/session-close handoffs)** — **#839 (Q-0132):** mined the owner's exported
  plain-claude.ai chats (a sub-agent read all 13, dedup-grepped the owner docs) and captured the
  genuinely-durable items to their homes — router **Q-0132** as the provenance index + the headline
  decision rationale (**why the bot's AI routes to Anthropic/Claude, not GPT**: GPT failed the
  owner's prompt-injection-resistance + tool-calling eval battery, so it is a **trust/safety**
  decision — the env wiring was in the repo, the *why* never was) · `maintainer-working-profile.md`
  §7 (phone-only zero-stakes operating reality · the code-reading boundary · "green tests ≠
  verdict; extracted ≠ reachable ≠ answerable") · the journal **phantom-tool keyword-injection
  pattern** · a BTD6 answer-cache key constraint. Docs only; `check_docs --strict` ✓. **#838 +
  #833/#830/#826/#824:** ledger reconciliation + session-close handoffs for the Railway
  agent-access session (docs only — the routine-spawned ledger updates that batch the session's
  current-state + `.sessions/` writes).
- **#829 (2026-06-14, hardening P0-2 PR 1 — media/YouTube data-minimization + retention
  enforcement, Q-0099)** — closed the two privacy/retention P0 gaps in the media readiness map.
  The video-reference cache stored the **full raw YouTube provider payload** (descriptions, id,
  statistics) and **never physically purged** expired rows (`purge_expired_video_cache` had no
  caller). Now: (1) `youtube_context_service._project_metadata` runs before the cache write so
  only the bounded sanitized projection is persisted — never the raw payload; it is **idempotent**
  so legacy raw rows re-project transparently on read (no migration / cutover flag). (2)
  `_safe_thumbnail_url` keeps only HTTPS `*.ytimg.com`/`*.youtube.com` URLs before storage/embed.
  (3) A new **`MediaMaintenanceCog`** owns a scheduled 6-hour `purge_expired` loop (content-free —
  logs only a row count), the shared-platform lifecycle owner per ADR-007 (not AI/BTD6). (4)
  Added the `media` (YouTube) subsystem row to `docs/ownership.md`. Output facts are byte-identical
  for fresh fetches — only what is *stored* changed. +18 tests; `check_quality --full` green
  (9467); arch 0; `check_docs` clean. **Next = P0-2 follow-ups** (content-free media diagnostics ·
  provider-execution hardening · maintainer live-verification) → P1-1 eval-matrix.
- **#825 (2026-06-14, hardening P0-4 PR 2 — channel creation + category lifecycle convergence,
  Q-0100)** — the **second half** of the channel-ownership convergence; **closes the final P0
  integrity track.** Ad-hoc operator channel creation (`!create`/`!evt`/`!bulkcreate` + the
  create panel) has **no declared subsystem binding**, so it never fit the catalogue-driven
  `ResourceProvisioningPipeline` (which resolves a `(subsystem, binding_name)` option and writes
  a binding row). It is now owned by a new audited **`ChannelLifecycleService.create_channels`** —
  the channel-domain sibling of the allowlisted `RoleLifecycleService` (the manual-role creator):
  bot-perm check → category resolve/get-or-create → safe-named text/voice create → typed per-name
  `LifecycleResult` + audit companion + `channel.lifecycle_changed` event. Subsystem-*bound*
  creation stays with the provisioning pipeline. The three cog commands + the create panel route
  through it; `test_no_direct_channel_mutations.py` now pins
  `create_text_channel`/`create_voice_channel`/category creation, and
  `test_no_silent_auto_create.py` lists the service as the one sanctioned manual `guild.create_*`
  caller (cog + create_panel **removed** from its allowlist — a net tightening). **Corrected a
  readiness-map drift:** the `create_panel` row claimed "uses the resource-provisioning lane" but
  the source called Discord directly until this PR. No migration. `check_quality --full` green
  (9453); arch 0 errors. **P0-4 complete; next P0 = P0-2 media retention (Q-0099).**
- **#820 (2026-06-14, hardening P0-4 PR 1 — channel clone + permission-overwrite convergence,
  Q-0100)** — the first half of the server-mgmt channel-ownership convergence: `.set_permissions()`
  and `.clone()` are now pinned by the channel-mutation invariant, routed through
  **`ChannelLifecycleService`**. The service gained `set_overwrite` (REVERSIBLE) + `clone`
  (COMPENSATABLE) ops — request fields `overwrite_target_id/type/overwrites` + `clone_name`;
  target resolution via `guild_resources.resolve_role/resolve_member` (the guild-resource
  invariant, **not** raw `guild.get_*`); a `LookupError`→failed-step path for a vanished
  overwrite target; audit `_summary` branches. Every direct call site migrated (`set_access`,
  `lock_channel`, `unlock_channel`, `modify_permissions`, `create_channel_with_role`'s
  post-create overwrite, and `views/channels/restrict_panel.py`'s batched apply mapped back to
  its succeeded/forbidden/failed buckets); `visibility_panel.py` was a map false-positive
  (already routes through `governance_service`). `test_no_direct_channel_mutations._FORBIDDEN`
  now pins `.set_permissions` + `.clone`. **Layering side-quest:** the convergence pushed
  `channel_cog.py` over the 800-LOC ceiling, so the `!list` paginator view (~180 LOC) was
  extracted to `views/channels/list_panel.py` (cog 739→640 LOC — a real layering smell removed,
  not dodged). `check_quality --full` green (9446); arch 0 errors. **P0-4 PR 2 (creation/category
  under `ResourceProvisioningPipeline`) carried** — resume recipe in the open `continue` issue
  (ad-hoc operator `!create`/`!evt`/`!bulkcreate` channels have no declared binding; design
  that fit).
- **#814 + #815 (2026-06-14, CI efficiency arc — Q-0126 + ~3× test speedup)** — `code-quality.yml`
  dominated June Actions cost (940 runs / 2,396 min/mo). **#814** shipped the safe levers
  (`concurrency: cancel-in-progress` on superseded PR runs · `pip` + `.mypy_cache` caching) +
  recorded **Q-0126** (the `docs/owner/active-work.md` claim ledger + push-batching convention,
  now in CLAUDE.md). The big lever (parallel pytest) was tried & reverted there — the suite
  wasn't parallel-safe. **#815** root-fixed that: three process-global singletons
  (`core.runtime.lifecycle` phase, `feature_flags._REGISTRY` defaults, a leaked `server_logging`
  bus subscription) leaked across tests, colliding only under parallel scheduling; one autouse
  `conftest.py` fixture resets lifecycle/startup_outcome/feature_flags (snapshot-restore) per
  test + `server_logging._reset_for_tests()` now tears down its subscription, then re-enabled
  `pytest -n auto` (pinned `pytest-xdist==3.6.1`). CI ~109s→~35s, 8 parallel runs all green;
  auto-merged hands-off (Q-0123).
- **Older merges (#813 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are archived (`scripts/check_docs.py` soft-ratchets the count). *(The #878 P1-1 eval/smoke session (2026-06-14) added its own entry and archived the oldest live one — the #802…#813 portable-substrate-kit group — to hold the ratchet at 20. The band-#870 reconciliation pass (2026-06-14) added two live entries — the #870+#869+#868 Hermes operating-layer arc and #867 ledger window catch-up — and archived the two oldest to hold the ratchet at 20: the #803… reconciliation+workflow-rules group and the #827… Railway agent-access session. Earlier: the band #841–#860 ledger-reconciliation added eight live entries — #866, #865, #864, #863, #862, #859, the #856+#853 group, and the #851/#850/#848/#852 group — and archived the eight oldest: the #788…#798 substrate-kit arc, #817, #794, the #786+#787 group, #778, #777, #775, #774. Earlier still: the #772 automod-v1 entry was archived to offset #855; the #765+#767+#769+#770 backup-posture entry to offset #849; the #764 P2 doc-drift-sweep entry to offset #843; the band-#840 reconciliation pass archived the #763 second-reconciliation-pass record, the #758/#760/#762 UX-Lab BUILD, and the #753/#754/#756/#759/#761 autonomous-loop wiring; the #755 entry to offset #829; the #746–#754 entry to offset #825; the #741/#742/#745/#748 entries by the band-#820 pass.)*

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

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

- **Autonomous loop — blocked on a maintainer secret (2026-06-13):** the loop is wired but has
  **never self-fired**; root-caused in #778 (cron/cadence trigger issues were bot-authored). It stays
  inert until the owner adds the **`ROUTINE_PAT`** repo secret — tracked with the other 5 maintainer
  actions in [`operations/autonomous-routines.md`](operations/autonomous-routines.md) § Control-plane
  state (the source of truth no in-repo checker can see; the first reconciliation still fires at #780).
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
