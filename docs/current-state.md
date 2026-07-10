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
> | **S3 AI-Memory** | [`current-state/S3-ai-memory.md`](current-state/S3-ai-memory.md) | settle-once money-safety guard (#1454) + cross-domain routing-disjointness guard (#1470); **self-improving-workflow guards #1476/#1477/#1479/#1482/#1495**; **owner re-elevated the portable substrate-kit to top focus (fresh-rebuild vision #1589/#1590)**; **rebuild design spec shipped (#1637/#1638) + BOTH linchpins now built & measured (#1639 — Phase-0.5 golden harness `parity/` + grammar spike, verdict GO-with-amendments)**; **substrate-kit finalized (#1649 — nervous system + context-economy engine + one-step-adopt; 407 kit tests)**; **Gate V COMPLETE (#1767); owner gates RETIRED (Q-0241/#1776); Phase-2.5 CLOSED (#1775 FAIL-as-tested → adopt-render fix + re-run pair, #1778); the FINAL review ran (#1778 — verdict: plan ready, §11 amendments folded, readiness scored); the idea-consolidation pass folded today's four owner captures + hardened the §3.C risks into machinery (#1791 — §11b A-12…A-20, registry mints R-16/R-17/P-5)**; ▶ **next: the FOUR program sessions — launch index READY: [`planning/program-three-sessions-launch-index-2026-07-07.md`](planning/program-three-sessions-launch-index-2026-07-07.md)** (Q-0252/Q-0253: ① websites on Fable TODAY (last Fable day) → ②/③ kit-lab + trading founding plans → ④ `superbot-next` kickoff — **now routed through the "SuperBot" Projects coordinator** (Project created 2026-07-07, both repos in scope, `superbot-next` owner-created public-until-flip; handoff protocol incl. the calibration exchange: [`planning/projects-eap-coordinator-kickoff-2026-07-07.md`](planning/projects-eap-coordinator-kickoff-2026-07-07.md)); paste-ready prompts in each brief; owner checklist inside) — nothing blocks the start; plan of record = [`planning/rebuild-canonical-plan-2026-07-06.md`](planning/rebuild-canonical-plan-2026-07-06.md) (+ its §11/§11b); Projects-EAP as coordinator ([owner-sendable review](planning/projects-eap-product-review-2026-07-07.md)) |
> | **S4 Docs system** | [`current-state/S4-docs.md`](current-state/S4-docs.md) | 40th Q-0107 pass done (band-#1890); next recon at #1920; **no PLAN-BACKLOG-THIN flag** |
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
> **Last updated:** 2026-07-09 — **fortieth Q-0107 reconciliation pass (band-#1890, issue #1891
> — [pass record](planning/reconciliation-pass-2026-07-09-band1890.md));** reconciled band #1863–#1890
> (seven grouped entries — the band is **entirely docs/tooling**, zero `disbot/` runtime: the **EAP
> Anthropic-feedback email assembled + sent** #1864/#1866/#1867/#1868; the **EAP Project fleet founding →
> independent cross-repo review** #1873…#1877/#1887/#1889/#1890 (the fleet grew to four repos; the manager
> Project brief; headline finding — the substrate-kit's render/engage half strands in every fresh adoption,
> an upstream-kit fix); the **substrate-kit graduation to its own repo** #1878/#1879/#1881/#1882/#1883/#1884
> (v1.0.0 pinned via `substrate.config.json`; in-tree copy removed, 101 files; provenance riders + exporter
> telemetry + console.json contract as kit-lab companions); the **Dependabot PR policy Q-0256** #1886 (+ the
> #1761–#1766 backlog merge); the 39th-pass docs PR #1863; and 8 dashboard refreshes #1865/#1869/#1870/#1871/#1872/#1880/#1885/#1888),
> trimmed Recently-shipped to 20, **disposed the open-PR set** — **zero open PRs at pass start** (the
> dependabot backlog cleared under Q-0256), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires
> (issue #1891 authored by `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B canonical
> plan + the live SuperBot Project program/fleet dominate), refreshed the dashboard export, marker #1861 → #1890.
> Earlier: 2026-07-08 — **thirty-ninth Q-0107 reconciliation pass (band-#1860, issue #1862
> — [pass record](planning/reconciliation-pass-2026-07-08-band1860.md));** reconciled band #1831–#1861
> (six grouped entries — the band is **entirely docs/tooling**, zero `disbot/` runtime: the **EAP-evaluation
> Anthropic-feedback email + permission-probe arc** #1834…#1861 that dominated the band — headline: the
> auto-mode first-publish push wall is **`git push`-transport-specific**, the GitHub Contents API bootstraps
> a fresh repo prompt-free (#1847, likely unblocks rebuild step 7), the email refined to two-part/two-reviewer
> form with every claim audited to a verifiable test, campaign self-audit graded coordinator recall ≈0.98;
> plus the S1 **server-management Wave-2 audit → docs truth refresh** #1844/#1850/#1851, the S5 **per-repo
> settings ledger** #1843/#1848/#1849, the S4 **grooming waves** (idea→plan + friction→guard) #1845/#1846/#1854/#1855,
> the 38th-pass docs PR #1833, and 3 dashboard refreshes #1835/#1836/#1841), trimmed Recently-shipped to 20,
> **disposed the open-PR set** — 6 dependabot dep-bumps #1761–#1766 left in flight (runtime, not this
> docs-only lane), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires (issue #1862 authored by
> `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B canonical plan + the live SuperBot
> Project program dominate), refreshed the dashboard export, marker #1830 → #1861.
> Earlier: 2026-07-08 — **thirty-eighth Q-0107 reconciliation pass (band-#1830, issue #1832
> — [pass record](planning/reconciliation-pass-2026-07-08-band1830.md));** reconciled band #1801–#1830
> (five grouped entries — the **entirely docs-only** SuperBot Project coordinator arc that dominated the
> band: the Projects-EAP coordinator going live → kickoff/calibration rewrite #1811…#1823, the evaluation
> guidebook #1820, and the EAP findings for the owner's Friday Anthropic feedback #1821…#1830 — headline:
> the auto-mode first-publish push wall is likely un-self-clearable in cloud Projects (11-test probe #1830);
> plus the Q-0254 understand-and-reflect kit-doctrine graduation #1806/#1809, the website-design + kit-lab
> program briefs #1802/#1804, the 37th-pass docs PRs #1801/#1803, and 3 dashboard refreshes), trimmed
> Recently-shipped to 20, **disposed the open-PR set** — 6 dependabot dep-bumps #1761–#1766 left in flight
> (runtime, not this docs-only lane), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires (issue
> #1832 authored by `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B canonical plan
> + the live SuperBot Project program dominate), refreshed the dashboard export, marker #1800 → #1830.
> Earlier: 2026-07-07 — **thirty-seventh Q-0107 reconciliation pass (band-#1800, issue #1801
> — [pass record](planning/reconciliation-pass-2026-07-07-band1800.md));** reconciled band #1771–#1800
> (seven grouped entries — the **S3 rebuild final-review → plan-review → idea-consolidation → multi-repo
> program founding** arc that dominated the band: the FINAL review #1778/#1783 (verdict *plan ready*, which
> produced the §6.3 runtime fixes #1781/#1782), Phase-2.5 A/B run #1775, Projects-EAP-as-coordinator + Q-0241
> never-wait autonomy #1776/#1777, the plan-review + owner-idea capture session #1784…#1790 (incl. the S1
> **automod** spam-evasion/duplicate-content runtime fix #1789), and the consolidation → program-founding
> session #1791…#1798 (owner rulings Q-0243…Q-0252 + the three-program-sessions launch index); plus the
> 36th-pass docs PR #1772 and 5 dashboard refreshes), trimmed Recently-shipped to 20, **disposed 11 open PRs**
> — **closed the 5 Codex Gate-V evidence PRs** #1752–#1755/#1758 (evidence-consumed into the merged synthesis
> #1767; two passes had left them open — flagged for owner veto) and left the 6 dependabot dep-bumps in flight
> (runtime, not this docs-only lane), confirmed ROUTINE_PAT set / loop self-fires (issue #1801 authored by
> `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B canonical plan + the four program
> sessions dominate), refreshed the dashboard export, marker #1770 → #1800. Earlier: 2026-07-06 —
> **thirty-sixth Q-0107 reconciliation pass (band-#1770, issue #1771
> — [pass record](planning/reconciliation-pass-2026-07-06-band1770.md));** reconciled band #1741–#1770
> (four grouped entries — the **S3 rebuild foundational consolidation → ONE canonical plan (Fable 5)**
> #1768/#1769/#1770 incl. the Q-0240 decide-and-flag decision model; the **Gate V verification-fleet
> pass A–D + synthesis** #1750/#1751/#1756/#1757/#1759/#1767 (verdict *Gate V COMPLETE → Phase-B under
> Sequence C*); the **CI-followups arc** #1743/#1744/#1745/#1747/#1748 (CodeQL watchdog, `check_audit_seam`
> + `check_deferred_recovery` AST guards, ruff replaces black+isort); and 3 dashboard refreshes), trimmed
> Recently-shipped to 20, disposed **11 open PRs** (6 dependabot dep-bumps + 5 codex Gate V evidence
> reports — all left in flight, not this docs-only lane), confirmed ROUTINE_PAT set / loop self-fires
> (issue #1771 authored by `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B
> canonical plan dominates), refreshed the dashboard export, marker #1740 → #1770. Earlier: 2026-07-06 —
> **thirty-fifth Q-0107 reconciliation pass (band-#1740, issue #1741
> — [pass record](planning/reconciliation-pass-2026-07-06-band1740.md));** reconciled band #1711–#1740
> (five grouped entries — the **S3 rebuild Gate-0 grammar-freeze → Phase-B L0 build-order + Stage-2
> subsystem walk** #1713/#1716/#1725/#1735; the Stage-2 **save-fixes** 8-bug runtime backport +
> CodeQL hardening #1728/#1730 (the band's only `disbot/` change); the **CI-setup redesign → Phase-A
> hard merge gates** #1736/#1737/#1739; the 34th-pass + open-PR sweep #1712/#1719; and 16 dashboard
> refreshes), trimmed Recently-shipped to 20, disposed **0 open PRs** (none open at pass start),
> confirmed ROUTINE_PAT set / loop self-fires (issue #1741 authored by `menno420`), forward queue
> still deep (no THIN flag — the rebuild Phase-B build phase dominates), refreshed the dashboard
> export, marker #1710 → #1740. Earlier: 2026-07-04 — **thirty-fourth Q-0107 reconciliation pass
> (band-#1710, issue #1711
> — [pass record](planning/reconciliation-pass-2026-07-04-band1710.md));** reconciled band #1681–#1710
> (three grouped entries — headlined by the **S3 rebuild foundations audit → Fable-5 judgment →
> design-prep arc** #1689/#1690/#1691/#1693/#1700/#1701/#1703/#1704/#1705 (both foundations audits,
> the two confirmed prod loss-path fixes #1693, and the capstone judgment's 7 Tier-1 owner decisions
> Q-0237); plus the 33rd-pass docs PR #1682 and the per-merge dashboard refreshes), trimmed
> Recently-shipped to 20, disposed 13 open PRs (none a stale session PR — #1708 is the active in-flight
> foundational-design session), confirmed ROUTINE_PAT set / loop self-fires (issue #1711 authored by
> `menno420`), forward queue still deep (no THIN flag — the rebuild Stage-2/design phase dominates),
> refreshed the dashboard export, marker #1680 → #1710. Earlier: 2026-07-03 — **thirty-third Q-0107
> reconciliation pass (band-#1680, issue #1681
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
> **Last reconciliation pass:** PR #1890 (2026-07-09, fortieth Q-0107 cadence pass, band-#1890 —
> [the pass record + next-band queue](planning/reconciliation-pass-2026-07-09-band1890.md); marker reset
> to the latest merged PR **#1890**). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #1920 (every
> multiple of **30** — Q-0107 cadence raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
> Q-0134; `check_reconciliation_due.py` flags it, and `.github/workflows/reconciliation-trigger.yml`
> auto-opens a `reconcile` issue at the boundary that fires the docs-reconciliation routine). Reset
> this marker to the latest PR after a pass.

- **#1920 (2026-07-10, overnight shift D — dashboard.json pinned-feed contract, first slice)** —
  the #1884 console-contract pattern applied to the feed websites renders ~12 pages from:
  new versioned `dashboard/data/dashboard_data_contract.json` (**slice semantics** — only
  `contracted_families` are pinned; growth is family-by-family with a version bump; first slice
  `meta` + `bugs`), producer `DASHBOARD_*` parity constants + `meta.schema_version` stamp in
  `export_dashboard_data.py` (feed regenerated), fail-closed `check_dashboard_contract` +
  `--dashboard-contract` flag in `check_dashboard_data.py`, +14 tests incl. a
  committed-file-passes-contract guard. Ride-along (Q2): `check_architecture` `baseview_inheritance`
  now *recognizes* the in-tree justifying-comment convention (`# Extends discord.ui.View directly
  (not BaseView): …` right above the class) so documented direct-View extensions converge instead of
  warning forever; the 5 remaining undocumented sites got genuine lifecycle comments (comment-only,
  zero runtime delta) — baseview warnings 13 → 0, +4 checker tests. The conformance ratchet
  (`test_view_base_class_conformance.py`) still pins the raw 13-entry inventory via
  `respect_justifying_comments=False`, so a new direct view can't slip in behind a self-written
  comment. Tooling/data/docs/comments-only.
- **#1919 (2026-07-10, overnight shift B — claim visibility across un-merged branches)** —
  `check_lane_overlap.py --remote` scans recent un-merged `origin/claude/*` / `origin/bot/*`
  branch tips for `docs/owner/claims/` files not on `main` (tip-state `ls-tree` compare —
  shallow-clone-safe, degrades gracefully offline), so a sibling session's claim is visible
  **before its PR exists** — closing the pre-PR race window of a parallel wave
  (idea `claim-remote-visibility-scan-2026-07-08`, now shipped; +5 unit tests, protocol line
  in `docs/owner/claims/README.md`). Ride-alongs: Recently-shipped trimmed to the 20 ratchet,
  fresh-container dev-tools bootstrap row in the journal ⚡ Quick reference (Q-0194). Tooling/docs-only.
- **#1918 (2026-07-10, tooling — static command-collision checker)** — new
  `scripts/check_command_collisions.py` + 18-test suite: pure-stdlib AST walk over `disbot/cogs/**`
  that fails when two declarations claim the same top-level command name/alias within a namespace
  (prefix registry incl. aliases · slash tree incl. `app_commands.Group` assignments) — the static,
  pre-merge half of the #1541/#1544 `give`-collision prod-outage guard (the #1544 boot guard stays
  the runtime backstop). Live tree at ship: 403 token claims, 0 collisions; a standing
  `test_live_tree_has_zero_collisions` regression runs in every pytest pass. Q-0105 unverified-tier
  header; `code-quality.yml` step wiring deliberately deferred (noted in the idea file).
- **#1917 (2026-07-10, codex — docstring)** — codex-authored one-liner adding a return description
  to `format_duration` in `disbot/utils/duration.py`; verified accurate against source (Q-0120) and
  merged on green CI by the overnight session (codex branches don't auto-arm, so it was merged
  directly after confirming green on head).
- **#1913 (2026-07-09/10, EAP — independent fleet wind-down audit)** — a fresh `superbot`
  session ran an adversarial, evidence-based audit of the 2026-07-09 gen-1 fleet wind-down:
  cloned all 9 EAP repos fresh, then had one agent per lane read its succession package and
  a **separate** agent per cited incident try to refute it against live GitHub PR/commit/CI
  data. Result: all 7 wind-down lanes (substrate-kit, websites, trading-strategy, the three
  codetool-lab arms, superbot-games/exploration) shipped complete, substantive succession
  packages — 21/21 spot-checked incidents resolved to real evidence, zero fabricated content
  found — plus the new `venture-lab` seed (11/11 files, genuinely lesson-derived, not
  boilerplate). Five real (non-fabrication) inaccuracies surfaced and are logged with exact
  evidence; the most consequential is inside **fleet-manager's own ping-test report**, which
  falsely claims `websites` never acknowledged a coordination test — a real, delayed ack
  (PR #44, +1h39m) contradicts it. Full report:
  [`eap/fleet-winddown-audit-2026-07-09.md`](eap/fleet-winddown-audit-2026-07-09.md). Also
  groomed the `cross-repo-eap-verification-orientation-pointer` idea into a new
  `AGENT_ORIENTATION.md` task route, having just lived the exact flow. Docs-only.
- **#1864 · #1866 · #1867 · #1868 (2026-07-08/09, S3 rebuild / EAP — the Anthropic-feedback email assembled + sent, close-out)** —
  the owner's Friday Anthropic feedback email reached final form and was sent: **#1864** assembled the full
  two-part email (landed Menno's **Part 1**, made the agent **Part 2** complementary), **#1866** signed Part 2
  as Claude (two-author sign-off), **#1867** closed out the projects-testing feedback thread, and **#1868**
  shipped the **rebuild-direction handoff + marked the EAP email sent**. Docs-only.
- **#1873 · #1874 · #1875 · #1876 · #1877 · #1887 · #1889 · #1890 (2026-07-08/09, S3 rebuild — EAP Project fleet founding → independent fleet review)** —
  the Claude Code Projects (EAP) fleet grew to **four repos** (`superbot`, `superbot-next`, `substrate-kit`,
  `websites`) and got an oversight layer: **#1877** added the **EAP Project fleet plan** (7 domain projects +
  3-model comparison + kit-lab), **#1874** a **second Project** kickoff (rebuild status site + Railway test),
  **#1876** the **websites Project** kickoff (superseding the draft), **#1873** the **rebuild-Project audit
  checklist** (+ a planning/README homing fix, Q-0166), **#1875** updated the settings ledger (rulesets now
  live on `superbot-next` + `substrate-kit`). **#1887/#1889/#1890** ran the **independent cross-repo fleet
  review** ([`eap/fleet-review-2026-07-09.md`](eap/fleet-review-2026-07-09.md) — honest verdict + first-party
  clone-and-run verification: `superbot-next` 998 pass / 1 skip under Py3.11) and the **manager-Project brief**.
  Headline finding: the substrate-kit's **render/engage half strands in every fresh adoption** (`adopt`
  plants-but-doesn't-render/wire) — an upstream-kit fix, captured for kit-lab. Docs-only.
  **Follow-on (2026-07-10):** an independent **gen-1 → gen-2 doctrine review** comparing the new
  `fleet-manager` doctrine against superbot's original
  ([`eap/gen1-gen2-doctrine-review-2026-07-10.md`](eap/gen1-gen2-doctrine-review-2026-07-10.md) —
  verified against both repos at HEAD; headline: gen-2 kept the hard-won machinery, but its
  reconciliation gate is hollow and one env-secrets rule contradicts itself). Docs-only.
- **#1878 · #1879 · #1881 · #1882 · #1883 · #1884 (2026-07-08/09, S3 — substrate-kit graduated to its own repo; superbot as first consumer + kit-lab companions)** —
  the substrate-kit **graduated to [menno420/substrate-kit](https://github.com/menno420/substrate-kit)** (v1.0.0)
  and superbot became its first downstream consumer: **#1878** substrate-kit planning, **#1879** pinned the kit
  via a root **`substrate.config.json`** (`kit_version: 1.0.0`, kit-lab founding-plan §4.2 consumer half),
  **#1882** **removed the in-tree `substrate-kit/` + `tests/unit/substrate_kit/` copy** (101 files; the kit now
  lives upstream), **#1881** added **program-law provenance riders** (PL-001…PL-009) to the eight origin Q-blocks
  in the router (KL-2 companion), **#1883** shipped the exporter **`telemetry` family** in
  `export_dashboard_data.py` (KL-6 companion — reads `telemetry/model-usage.jsonl`, field-whitelisted, fail-open),
  and **#1884** pinned the **`console.json` cross-repo shape contract**. Docs/tooling only (no `disbot/`).
- **#1886 (2026-07-09, S5/ops — Dependabot PR policy, owner decision Q-0256)** —
  captured the owner's **review-on-sight dependabot rule** (durable home
  [`operations/repo-settings-state.md`](operations/repo-settings-state.md) § Dependabot PR policy; the
  not-shipped auto-arm alternative is Q-0257) and executed the **backlog review/merge of #1761–#1766**
  (see the entry below).
- **#1863 (2026-07-08, workflow — thirty-ninth Q-0107 reconciliation pass, band-#1860)** —
  the 39th docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-07-08-band1860.md)): reconciled band #1831–#1861, trimmed
  Recently-shipped to 20, disposed the open-PR set, confirmed the control-plane, refreshed the dashboard
  export, reset the marker #1830 → #1861.
- **#1865 · #1869 · #1870 · #1871 · #1872 · #1880 · #1885 · #1888 (2026-07-08/09, docs — dashboard-data refreshes, Q-0167)** —
  eight per-source-merge refreshes keeping the committed `dashboard/data/dashboard.json` export fresh as the
  EAP-email / fleet-founding / substrate-kit-graduation arc landed.
- **#1762 · #1763 · #1764 · #1765 · #1766 (2026-07-09, dependabot backlog cleared under the new Q-0256 policy)** —
  the six stuck dependabot PRs (opened 2026-07-06, CI-green ~3 days with no merge actor — `dependabot/*`
  branches are never armed by the enabler, by design) were reviewed and dispositioned per the owner's
  new **review-on-sight rule (Q-0256**, durable home `docs/operations/repo-settings-state.md`
  § Dependabot PR policy**)**: **#1764** discord.py ≥2.7.1, **#1763** anthropic ≥0.116, **#1766**
  Pillow ≥12.3, **#1762** uvicorn 0.50.2 (botsite + dashboard lockfile) — all floor/patch bumps fresh
  builds already resolved; **#1765** psutil ≥7.2.2 (**major** 5→7) merged after a real breaking-change
  assessment (only `Process().memory_info().rss` / `cpu_percent()` / `virtual_memory()` used — all
  unchanged through 7.2.x; removed APIs unused; full suite green with 7.2.2 installed). **#1761 closed**
  as a strict subset of #1762 (both bumped the same `dashboard/requirements.*` lines). Policy Q-block +
  the not-shipped auto-arm alternative: router Q-0256/Q-0257 (session PR #1886).
- **#1834 · #1837 · #1838 · #1839 · #1840 · #1842 · #1847 · #1852 · #1853 · #1856 · #1858 · #1859 · #1861 (2026-07-07/08, S3 rebuild / EAP-evaluation — the Anthropic-feedback email + permission-probe arc)** —
  the band's headline: the coordinator kickoff continued (**#1834/#1837**) and the EAP evaluation produced
  the owner's **Friday Anthropic feedback email**, refined across the band with **every claim audited to a
  verifiable test** (**#1838** compaction + verifiability audit → **#1840** two-layer clear-path flagship
  (classifier-vs-credential) → **#1853** refresh + forward-only Project custom instructions → **#1856**
  two-part / two-author / two-reviewer restructure → **#1858** Part-2 first-person agent narrative). The
  **permission-probe** thread hardened the central finding: the auto-mode first-publish push wall is
  **`git push`-transport-specific** — the **GitHub Contents API bootstraps a fresh empty public repo
  prompt-free** (**#1847** — both `substrate-kit` + `superbot-next` seeded, likely unblocking rebuild step 7),
  with the clear-path (**#1839**) and standing-grant-row (**#1842**) addenda. **#1852** = the EAP-direction
  handoff; **#1859** = the campaign self-audit (coordinator same-day recall graded **≈0.98 precision / ~1.0
  event-level recall** vs git ground truth, 6 friction entries logged); **#1861** = the projects-testing
  Anthropic-feedback close-out. Docs-only throughout (no `disbot/`).
- **#1844 · #1850 · #1851 (2026-07-08, S1 — server-management subsystem audit → Wave-2 docs truth refresh)** —
  the owner's campaign Wave-2 over the server-management subsystem: **#1844** ran the audit; **#1851**
  shipped the **docs truth refresh** (findings F1–F5 reconciled in `docs/subsystems/server-management.md`);
  **#1850** added the **W2-F6 AST write-boundary invariant** for the reaction-role tables (a new checker +
  tests — tooling/tests only, no `disbot/` runtime).
- **#1843 · #1848 · #1849 (2026-07-08, S5/ops — per-repo settings ledger: forward-only Project experiment)** —
  a readable per-repo settings ledger so future sessions **read state, not guess**: **#1843** captured the
  forward-only Project experiment idea + the ledger plan; **#1848** shipped **Phase 1** — the `superbot-next`
  General settings captured from the owner's screen recording (frames extracted via a dev-only
  `imageio-ffmpeg`) into [`operations/repo-settings-state.md`](operations/repo-settings-state.md); **#1849**
  corrected it (new repos are **bare** + the full auto-mode API capability map). Phase 2 (a generator that
  auto-maintains the rows) stays queued.
- **#1845 · #1846 · #1854 · #1855 (2026-07-08, S4/workflow — grooming waves: idea→plan + friction→guard)** —
  the campaign's grooming lanes, all idea-lifecycle / self-improvement: **#1845** (lane C) promoted the
  **usage-limit-aware routines** idea → a 2-PR plan + roadmap S5 horizon; **#1846** (lane B) shipped the
  **supersede-banner integrity checker** (`scripts/check_supersede_integrity.py` + a warn-first `check_docs`
  soft check, 16 tests); **#1854** groomed the #1846 follow-ons; **#1855** closed the "green-by-skip" gap by
  wiring **`check_plan_homing --strict` as an always-run pre-setup gate** in `code-quality.yml` so the
  docs-only fast path can no longer land an unhomed plan (Q-0194 friction→guard).
- **#1833 (2026-07-08, workflow — thirty-eighth Q-0107 reconciliation pass, band-#1830)** —
  the 38th docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-07-08-band1830.md)): reconciled band #1801–#1830,
  trimmed Recently-shipped to 20, disposed the open-PR set (6 dependabot bumps in flight), confirmed the
  control-plane, refreshed the dashboard export, reset the marker #1800 → #1830.
- **#1835 · #1836 · #1841 (2026-07-07/08, docs — dashboard-data refreshes, Q-0167)** —
  three per-source-merge refreshes keeping the committed `dashboard/data/dashboard.json` export fresh as the
  EAP-email / settings-ledger / grooming arc landed.
- **#1807 · #1810 · #1811 · #1812 · #1813 · #1814 · #1816 · #1817 · #1818 · #1819 · #1820 · #1821 · #1822 · #1823 · #1825 · #1826 · #1827 · #1828 · #1829 · #1830 (2026-07-07/08, S3 rebuild — the SuperBot Project coordinator kickoff → live calibration → EAP-evaluation arc)** —
  the band's headline: the **Claude Code Projects (EAP) coordinator went live** and ran the rebuild
  program's first stretch. **#1807/#1810** stood up the early-access / repo-first kickoff (owner creates
  `superbot-next` first, multi-repo picker test) + fixed pre-existing badge/plan-homing drift on sight
  (#1808, Q-0166). **#1811…#1823** rewrote the [coordinator kickoff + calibration doc](planning/projects-eap-coordinator-kickoff-2026-07-07.md)
  through ~13 owner-steered addenda — thin pointer-first Custom Instructions, the 13-item **calibration
  exchange** (the coordinator scored a strong pass, Q7 verified against live GitHub), the **SECOND MANDATE**
  evaluation guidebook (**#1820** — the Projects-EAP journal + seven EAP axes, so the Project both *executes*
  the rebuild and *evaluates Claude Code Projects* for the owner's standing-Anthropic-channel goal), tempo
  correction (3-day free-window *stretch goal*, correctness first), the Q-0247 kit-extraction sequence made
  explicit, the don't-spare-on-agents fan-out mandate, and the §7 **working-relationship inquiry** →
  a durable operating model (kickoff §8). **The EAP findings for the owner's Friday Anthropic feedback**
  (the evaluation's whole point) landed across #1821…#1830: the **auto-mode permission / consent-wall**
  (falsified-then-corrected several times as the owner probed the UI — headline = the first-publish push
  wall is likely **un-self-clearable in cloud Projects** (auto-mode-only, no permissions UI)); the
  **secrets-field** thread raised → recalibrated → **dropped as a non-incident** (#1826/#1827/#1828, owner
  editorial call — feedback stays incident-backed only); the **4 KiB `start_project_session` dispatch cap**
  (#1829); and the direct **11-test permission-boundary probe report** (**#1830** — constructive/reversible
  actions run prompt-free, destructive-git-to-a-published-ref is hard-walled with no self-clear path).
  Docs-only throughout (no `disbot/`). ⚑ Owner-parked: the step-7 first-publish push and the stranded
  scratch branch `test/permprobe-0708` (harmless; auto mode can't self-delete a remote ref).
- **#1806 · #1809 (2026-07-07, workflow — Q-0254 understand-and-reflect rule → portable kit doctrine)** —
  graduated the **understand-and-reflect** working-agreement rule (state back the fuller picture + implied
  specs before substantive work; surface the possibility space when feasibility is uncertain) into the
  portable **substrate-kit** templates (`CONSTITUTION.md.tmpl` + `collaboration-model.md.tmpl` +
  `question-router.md.tmpl`) so it travels to every future repo, with superbot's local `.claude/CLAUDE.md`
  copy kept in sync. Docs/kit-template only.
- **Older merges (#1824 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are trimmed to the archive (newest-first), which `scripts/check_docs.py` soft-ratchets at 20 and `check_current_state_ledger.py` treats as present. *(Thematic grouping by date means the live/archive PR-number spans overlap slightly — the floor pointer is approximate prose, not a strict bound; the per-band pass records carry the exact moved sets.)* *(The twenty-first Q-0107 pass — band-#1320, 2026-06-22 — added the band #1294–#1320 work as seven grouped entries (fishing minigame #1296/#1298/#1299/#1301/#1303/#1304, role management #1300/#1302/#1306, help surface #1294/#1297, BTD6 answerability #1295/#1316, botsite React PR1 #1305, CI/ledger/tool-pin hygiene #1308/#1317/#1320, dependency bumps + dashboard #1307/#1309/#1311/#1312/#1313/#1314/#1315); trimmed the live ledger to 20, moving #1208-band · #1226-band · #1211-band · #1210 · #1203-band · #1209-band · #1183-band to the archive.)* *(The twentieth Q-0107 pass — band-#1290, 2026-06-22 — added the band #1265–#1291 work as six grouped entries; trimmed the live ledger to 20, moving #1186 · #1156-band · #1147-band · #1143-band · #1162-band · #1149-band to the archive.)*

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
