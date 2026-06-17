# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ NEXT (live — read THIS line): the buildable `ready` decade-queue is consumed — next buildable work is PLAN-FIRST *or* the dashboard lane.** **Dashboard handoff (2026-06-16, #969):** the developer-dashboard **Phase 3 env-usage map shipped** — `scripts/scan_env_usage.py` (stdlib AST scan: each env var → file/line, required/optional, layer; names + locations only, never values), surfaced on the new dashboard `/env` page + the generated `docs/operations/env-vars.md` reference. **Dashboard read-only surfaces are now ALL shipped (2026-06-16):** the Q-0156 read-only lane is consumed — `/status` (build & health, **#985**) was the last one, after `/aliases` (#982) + `/games` (#983). **Next dashboard slices are all gated:** the owner-approved **live help/panel editor** (Q-0156, the headline ask) needs the private bot control API + Discord OAuth design (see `planning/dashboard-live-editor-plan.md` L0–L3); Phase 2 (owner auth · checklist · public bug form) and Phase 4 (control board) need owner decisions first (auth method + DB — the plan's open questions); Phase 3b *value-management* needs the Railway-API integration (`creds`). So the dashboard's next pure-code slice is **owner/creds-gated** — the remaining `ready`-class buildable lanes stay the **PLAN-FIRST** ones below. **(2026-06-17, #1017): the settings global tier shipped** — `resolve_setting` now does per-guild → global (`guild_id=0`) → default and `SettingsMutationPipeline.set_value` has an owner-gated `scope="global"` path; the dashboard settings lane's **phase ③** (web editor + `POST /control/settings/{scope}` with the Global/per-server scope picker) is the named next slice but is **owner-pacing-gated** (control-API write endpoints = the owner's "don't rush" zone, needs the Railway `CONTROL_API_TOKEN`) — a future empty fire should take a different ungated lane until the owner greenlights it. The `/myprofile` lane is **buildable-complete**: PR A (read-only card, **#938**) + **PR B — self-service writes (shipped #940)** — `views/profile/editor.py`, the first UI consumer of `ParticipationMutationPipeline` (participation opt-in/out · subscription toggles · visibility toggle · preference editors bool/enum/modal; each action exactly one audited pipeline call). The only remaining myprofile slice is **PR C (join-time onboarding), owner-gated → routed as router Q-0147** (may a public bot DM strangers? — agent recommends in-guild / opt-in / no unsolicited DM). The games-economy faucet/sink diagnostic (slot 2) **shipped #937**. **So the next ▶ startable = a PLAN-FIRST slice: own a small plan for ONE of** — image moderation (Q-0108) · the AI §7 next workflow family (post-prod-check) · the Hermes bug-triage `gh issue create` write (Q-0121); **security service tiers 1+2 (#929) is owner/Hermes-review**, BUG-0009 newest-towers is `data`-gated, absence-guard Layer B is `creds`-gated. **Note:** the `diagnostic_cog.py` 800-LOC blocker is **CLEARED (#943)** — the `!platform` group moved onto `PlatformCommandsMixin` (`cogs/diagnostic/platform_group.py`), cog now 260 LOC, so the next `!platform` subcommand has room. **Security service tiers 1+2 is still IN FLIGHT** (PR #929, `needs-hermes-review` carve-out — raid detection + account-age filter, Q-0111). **BUG-0009 slices 1/2/2b all shipped** (#924 MK-related · #926 Geraldo per-level + game-mode groupings); the one remaining family — newest-towers ordering — is **data-gated** (`towers.json` has no release-order field). The rest of P1 (absence-guard Layer B · live-quality battery) is creds/review-blocked. *The live next-step is THIS sentence — **not** any other "next ▶ =" lower in this callout or in the dated `Last updated:` stamps further down (those are historical reconciliation snapshots: e.g. a stamp still reads "next ▶ = mining Forge", but Forge shipped #905). Trust this line + the Recently-shipped list, never a stamp.*
>
> **▶ NIGHT QUEUE (2026-06-16, owner directive — scheduled dispatch fires read THIS first): advance the [night queue](planning/night-queue-2026-06-16.md).** It makes the otherwise-`plan-first` "AI §7 next workflow family" lane **concrete and buildable now**: an ordered set of independent, **read-only deterministic BTD6 floor builders** (the proven #946/#950/#955/#962/#975/#1000/#1008/#1009/#1010 lane — §7.5 comparison + §7.6 roster), each **data-complete today** (reads a field already in a committed `disbot/data/btd6/*.json`), each ships under **Q-0048** (no prod-check, auto-deploys), each closes the **BUG-0009** "grounded values / wrong assembly" class (the standing P1 priority). **An empty scheduled fire builds the topmost `TODO` slice** (slot 1 hero cost-comparison shipped **#1000**; slot 2 power cost comparison shipped **#1008**; slot 3 relic category/effect roster shipped **#1009**; slot 5 hero ability roster shipped **#1010**; **slot 4 reframed → bloon *modifier explainer* shipped #1011** (camo/fortified/regrow are universal modifiers, not per-type properties — option (c) of the slot-4 reframe); both buffer slices shipped **#1011** — MK category roster + the Geraldo starting-kit angle). **The night queue is now FULLY consumed** — every ready slot, the slot-4 reframe, and both buffer slices have shipped. **But the proven, ungated BTD6 deterministic-floor lane still has thinning backlog** beyond the curated queue: **#1012 (2026-06-17)** shipped three more gaps in the same `btd6_context_service` floor — boss roster + per-difficulty map filter (`deterministic_roster_reply`) + boss damage-immunity (`deterministic_boss_immunity_reply`). Remaining ungated floor candidates are getting scarce (most rosters now covered: towers/heroes/paragons/maps/bosses/MK/relics/bloons/hero-abilities + cost comparisons + immunity); a future empty fire can add a *genuinely-asked* uncovered shape (e.g. boss tier-HP comparison, paragon-ability lookup) **or** take a fresh **plan-first lane** (image-mod #941 in-flight · security tiers #929 — both owner/Hermes-review-gated). Do NOT invent low-value floor builders to fill the queue (forced filler ≠ work). A `/bugreport` or `continue` handoff still jumps this queue (bugs-first). Seam + per-slice turn-key recipes are in the queue doc.
>
> **▶ Next action — one live queue:** the **[band-#990 decade queue](planning/reconciliation-pass-2026-06-16-band990.md)** §4 — the tenth Q-0107 pass (2026-06-16, issue #961; cadence every 30th PR per Q-0134). The band-#930 queue is fully executed (AI §7.5/§7.6 floors #946/#950/#955/#962/#975 · myprofile #938/#940 · security tiers #929 · diagnostics #937 · architecture-atlas Q-0151 #957/#958/#960/#964) and the **developer-dashboard / control-API initiative is the active thread** (#974/#990/#993/#995, Q-0155–Q-0160); its read-only surfaces all shipped, the next slices are owner/creds-gated (live editor · auth · Railway-API). The band-#900 queue is nearly fully executed (Forge #905 · P1-3 #917/#918 · log-triage #906 · Home/respec/titles #910/#912 · BUG-0009 #924/#926 · welcome #920); security tiers 1+2 is in flight (#929). **The mining structures / skill-tree lane is now COMPLETE** — every ▶ startable slice shipped (D #891 · A #897 · B/Forge #905 · C/Home #910 · E respec-polish + F titles #912); the only remaining items are owner-gated (Vault-cap *hard* enforcement · ⛔ V-16 phase 2 real sprites). **The Railway log-triage skill shipped (#906) and P1-3 invariants are now SUBSTANTIALLY COMPLETE (#917, 2026-06-15).** The 2026-06-15 P1-3 pass reviewed all four tracks, found + closed the **two** genuine buildable-now gaps with CI-runnable AST invariants — **settings** declared→runtime-consumer parity (`test_settings_declared_vs_consumed_parity.py`, 0 dead of 63 declared settings; the explicitly-named missing invariant from the settings map §Required #3) and **games** wager write-boundary completeness (`test_two_sided_economy_calls_are_accounted_for` — the hardcoded `_WAGER_FILES` fence now also fails on a *new* two-party mint path). **AI** is substantially-covered by the 34/34 catalogue/eval ratchet (closed, no new invariant); **BTD6** source-provenance is invariant-covered and uniform per-derived-value attribution is a documented design-for-review residual (brittle as an AST guard). Full record: [the P1-3 disposition](planning/production-readiness/p1-3-contract-invariants-disposition-2026-06-15.md). **The safety quick-win shipped (welcome phase 2 PIL cards, #920, 2026-06-15):** a `welcome_card_enabled` toggle (off by default) attaches a rendered PIL greeting card to the join embed; the `render_welcome_card` prototype graduated to `utils/welcome_render.py` (the UX-lab gallery now re-exports the production renderer — one source of truth); degrades cleanly to embed-only when Pillow is unavailable. **BUG-0009 slice 1 shipped (#924, 2026-06-15): the "MK related to <tower>" family** — the model no longer assembles that list (it grabbed the whole Support *category* and mislabeled it farm-related); `btd6_data_service.monkey_knowledge_referencing` derives the MK↔tower relation deterministically (description names the tower's canonical/upgrade-path name → strong; alias → weak, suppressed when another tower is strongly referenced or the MK is a Powers/Heroes-tab point), served as a **pre-emptive floor** on the BTD6 path (this class *passes* the value-only faithfulness guard, so the post-hoc roster floor never caught it). **BUG-0009 slices 2 + 2b shipped (#926, 2026-06-15): the "Geraldo items per level" + "game mode groupings" families** — the model no longer assembles either grouping. Geraldo: `btd6_data_service.geraldo_items_by_unlock_level` owns the level→items map, `deterministic_geraldo_per_level_reply` formats the full grouping / a single level's unlocks / an honest "nothing unlocks at level N". Modes: `btd6_data_service.modes_by_kind` owns the difficulty→mode→modifier grouping (the owner's "mode groupings" miss — CHIMPS is a mode, not a difficulty), `deterministic_modes_reply` fires on a clear modes enumeration and defers when "mode" is a qualifier on another entity. All three BUG-0009 builders now front one dispatcher `deterministic_btd6_list_reply` served as the pre-emptive BTD6 floor (MK → Geraldo → modes). **Next ▶ startable = security service tiers 1+2** (decade-queue slot 9, plan-first — raid detection + account-age filter, Q-0111; cite `ux/pattern-library.md` `mock_security_*` pattern_ids). *(BUG-0009 slice 3, newest-towers ordering, is **data-gated** — `towers.json` carries no release-order field; needs sourced release-order data first via the ADR-006 / `!btd6ops seed-data` provenance lane, then append its builder to `deterministic_btd6_list_reply`.)* · then security service tiers 1+2 (slot 9, plan-first); the remaining P1 (absence-guard Layer B · live-quality battery) stays **creds/review-blocked**. *(Pointer references the pass by name, never by a PR-number range — a range here silently masks the band from the ledger guard; see [the band-#800 pass §6](planning/reconciliation-pass-2026-06-13-band800.md).)* **The P0 integrity spine, P1-2, AND P1-1's deterministic half are now COMPLETE** — the versioned AI eval/smoke matrix (offline, CI-gated, #878), its self-cleaning drift guard (#879), and the first BTD6 hotspot coverage (#881, ratchet 8→14/34 tools). **Remaining P1 (where the next session starts): P1-3 is now SUBSTANTIALLY COMPLETE (#917)** — see the disposition linked above. **AI tool-surface eval coverage is COMPLETE — 34/34** (the final 7 BTD6 lookups landed; `_ACK_UNCOVERED_TOOLS` is empty and the drift guard now fails closed on any new tool). What remains on P1-1 is **creds-gated** (live-quality battery) or **design-for-review** (absence-guard Layer B), so the next *offline* plan step is **plan-first BUG-0009** (the safety quick-win — welcome phase 2 PIL cards — shipped in #920) · then the **creds/review-blocked** P1-1 remainder (live-eval battery · absence-guard Layer B). **The production-hardening P0 integrity spine is now COMPLETE** (P0-2 ✅, P0-3 ✅, P0-4 ✅ — every gating decision answered): **P0-4** (channel-ownership convergence, Q-0100) — PR 1 (#820) clone + permission-overwrite, PR 2 (#825) ad-hoc channel creation + category lifecycle through `ChannelLifecycleService`; **P0-2 media retention (Q-0099, #829)** — bounded metadata projection at the cache write + the scheduled `MediaMaintenanceCog` purge owner + thumbnail-URL validation; **P0-3** (delegated-Setup apply, #817). **The standing priority is the P1 correctness tier. P1-1's offline/CI half + P1-2 are done (above); next = P1-3 invariants + continued eval-coverage expansion, then the creds/review-blocked P1-1 remainder** (live battery · Layer B, relates BUG-0009). P0-2 follow-ups: **content-free media diagnostics now SHIPPED** (PR #854 — `!platform media` + the `media` diagnostics provider + cache-health/provider-outcome counters, content-free); the remaining two (provider-execution hardening · maintainer live-verification) stay queued behind P1-1. **P0-3 is complete: arc PR 3 shipped the delegated-Setup apply authority (Q-0098) in #817** (arc PR 2 retired the XP-announce + economy-log scalar pointers in #794; arc PR 1 foundation #777). **The owner's active strategic thread is the [portable substrate-kit](planning/portable-substrate-kit-extraction-2026-06-13.md)** (OSS agent-memory/workflow package; PR 1a+1b DONE, resume at the 1b tail → PR 2) — it consumed the #781–#800 band and runs in parallel as owner-steered. The safety/community band (slots 4–6: #772/#774/#775) is **COMPLETE**; its remainder (security tiers 1+2 · image-mod) is plan-first behind the P0 spine (welcome phase 2 shipped #920). Product lanes (mining/BTD6/AI) stay open as owner-steered alternates. The full scorecard + deferred list live in the queue doc; [`roadmap.md`](roadmap.md) stays the index, now organised **by sector** (S1–S5 dispatch queues). **Status is per-lane below — a session edits ONLY its own lane's bullet** (convention: [`owner/ai-project-workflow.md`](owner/ai-project-workflow.md) §9 "Cross-cutting ledger discipline"). **Owner-teed sector mapping DONE (2026-06-14, PR #877):** the roadmaps/plans are now organised under the **S1–S5 planning sectors** as **per-sector dispatch queues** — each sector a Hermes-dispatch target (name a sector + an action, read its live `Now`) — [`roadmap.md`](roadmap.md) § "By sector — the live dispatch queues" + the dispatch contract in [`repo-sector-map.md`](repo-sector-map.md) § "dispatch targets"; the [brief](planning/next-session-sector-roadmap-mapping-2026-06-14.md) is executed. Hermes/routine *wiring* stays Q-0137 Thread 1 (owner-undecided). **#704 live-test screenshots triaged + closed** (2026-06-14): mostly-working bot; one AI capability/grounding-consistency finding feeds P1-1 — [`audits/pr704-live-test-triage-2026-06-14.md`](audits/pr704-live-test-triage-2026-06-14.md).
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
> **Last updated:** 2026-06-15, **ninth Q-0107 reconciliation pass (the band-#930 cadence fire,
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
> **Last reconciliation pass:** PR #994 (2026-06-16, tenth Q-0107 cadence pass —
> [the pass record + decade queue](planning/reconciliation-pass-2026-06-16-band990.md)). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #1020 (every
> multiple of **30** — Q-0107 cadence raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
> Q-0134; `check_reconciliation_due.py` flags it, and `.github/workflows/reconciliation-trigger.yml`
> auto-opens a `reconcile` issue at the boundary that fires the docs-reconciliation routine). Reset
> this marker to the latest PR after a pass.

- **#1018 (2026-06-17, manifest spine slice 1 — typed CommandManifest over the ledger)** — same
  dispatch fire as #1017 (continuation). Started the **manifest spine** — the dashboard vision doc's
  "key structural investment," owner-approved (Q-0162), Phase-E predecessor shipped (#1013), schema
  finalized (#998). `core/runtime/command_manifest.py` projects the cached `CommandSurfaceLedger`
  into the typed #998 command schema (no second surface walk), built+cached at startup, surfaced as a
  `command_manifest` diagnostics provider, with the manifest-faithfully-projects-ledger CI invariant
  (the first reconciliation test that makes the metadata trustworthy). AST stays drift-detection only.
  Deferred fields (source/panels/actions/related_settings/capability_required) are shape-pinned but
  empty. PR2 (panel registry + `PanelManifest`) shipped #1019.
- **#1019 (2026-06-17, manifest spine PR2 — panel registry + PanelManifest)** — scheduled dispatch,
  empty work order → advanced the manifest-spine thread (PR1 `CommandManifest` shipped #1018; the
  execution plan + `current-state` named PR2 next; both open PRs Hermes-gated). `core/runtime/panel_manifest.py`
  projects the **persistent-view registry** (the panels with stable static custom_ids that survive
  restart — the manageable ones) into a typed `PanelManifest`, built **at startup from the runtime
  registry** (mirroring PR1's runtime-truth, not AST): each `PersistentView` is instantiated arg-free
  and its real components introspected into `PanelButton`s (`action_id`/`custom_id`/`label`/`row`;
  `command` deferred). `persistent_views.py` gained a declarative `PANEL_ID` + faithful
  `iter_registered_view_classes` so the two `help` panels (collapsed in the subsystem-keyed recovery
  dict) both surface (10 panels, 67 buttons live). `CommandManifestEntry.panels` back-populated by a
  subsystem join (`actions` deferred — no declared button→command binding). `panel_manifest` diagnostics
  provider + startup_outcome phase. Reconciliation test round-trips every manifest button against a fresh
  view-class instantiation. `check_quality --full` green (10414) · arch 0 · +20 tests. **Next: PR3** —
  control-API `manifest` read + `dashboard.json` export + the AST drift guard (sequenced in
  [`manifest-spine-execution-plan-2026-06-17.md`](planning/manifest-spine-execution-plan-2026-06-17.md)).
- **#1017 (2026-06-17, settings global tier — per-guild → global → default)** — scheduled dispatch,
  empty work order → advanced the active dashboard thread's next *ungated runtime* slice (the
  live-editor plan's settings-editor phase ②, the owner's "change things globally" ask).
  `services.settings_resolution.resolve_setting` now resolves **per-guild row → global row
  (`guild_id = utils.db.settings.GLOBAL_GUILD_ID = 0`) → spec default** (new provenance `global_kv`,
  mirroring `core.runtime.feature_flags`); an `include_global` flag keeps the mutation pipeline's
  `_read_previous` scope-local. `SettingsMutationPipeline.set_value` gained a `scope="global"` path,
  **owner-gated** (`config.BOT_OWNER_USER_ID`; system/backfill bypass), writing/auditing the
  `guild_id = 0` row through the existing audited seam (scope-`global` audit, AI per-guild projection
  skipped). An owner global write is inherited by every guild without its own row. +18 tests. The
  **next dashboard slice is now phase ③** — `POST /control/settings/{scope}` over `set_value` + the
  OAuth-gated editor UI with the Global/per-server scope picker.
- **#1015 (2026-06-17, dashboard Phase C — the read workspace)** — scheduled dispatch, empty work
  order → advanced the active dashboard thread (night/BTD6 queues consumed; R3 hardening already
  in flight on #1014). Shipped the Phase-C slice skipped when the build jumped C-auth → F-writes,
  all **read-only** over the shipped Phase E reads (no new bot endpoints, no `disbot/` code): **`/me`**
  (logged-in personal overview — who you are + the servers you administer, each card linking to its
  overview/editor; pure session data), **`/admin/{guild}/overview`** (read-only per-server
  setup-health summary — invalid settings, customisations, help overrides, disabled cogs — from
  `_fetch_current_state`), and an honest **authority preview** ("what you may read / change here")
  from the authority bridge. New pure `_setup_health`/`_authority_preview` projections + two
  templates + nav/overview links. `check_quality --full` green (10408) · arch 0 · +12 dashboard
  tests. **Dashboard ▶ next:** R3 hardening shipped (#1014); the **Phase D manifest spine** (Q-0162,
  gates command/panel management) is now the live ungated buildable thread — PR1 `CommandManifest`
  (#1018) + PR2 panel registry/`PanelManifest` (#1019) shipped; **PR3** (control-API `manifest` read +
  `dashboard.json` export + AST drift guard) is the next slice. The global-settings runtime tier
  (Q-0157) stays its own owner-paced session.
- **#1012 (2026-06-17, AI answerability floor — boss roster + per-difficulty map filter + boss
  immunity)** — scheduled dispatch fire, no work order; night queue fully consumed + both open PRs
  (#941/#929) Hermes-gated → took a fresh slice of the proven, ungated BTD6 deterministic-floor lane
  (Q-0048, BUG-0009 wrong-assembly class). Closed three real gaps: **(1)** `deterministic_roster_reply`
  never had a **boss roster** ("list all bosses" fell to the model, which can omit/add one of the 7) —
  added a boss enumeration branch; **(2)** "list all expert maps" **dumped all 86 maps** grouped by
  difficulty — `_map_roster_reply` now filters to a named tier (Beginner/Intermediate/Advanced/Expert);
  **(3)** new `deterministic_boss_immunity_reply` in `_BTD6_LIST_BUILDERS` owns boss damage-immunity
  ("what is Lych immune to" · "is Blastapopoulos immune to fire" · "which bosses are immune to fire")
  off `bosses[].immune_to`, keyed on a boss reference + immunity cue so it never overlaps the bloon
  immunity roster. `check_quality --full` green · arch 0 · +9 tests (boss-immunity + exclusivity
  corpus phrase + roster/map-filter cases).
- **#1011 (2026-06-17, AI §7.6 — night-queue buffer slices + slot-4 reframe, three floor builders)** —
  scheduled dispatch fire, no work order → advanced the now-consumed ▶ NIGHT QUEUE. Three
  deterministic BTD6 floor builders, all BUG-0009 wrong-assembly class, all under Q-0048
  (read-only, no prod-check): **(1) Monkey-Knowledge category roster** —
  `btd6_data_service.monkey_knowledge_by_category()` + `deterministic_mk_category_roster_reply`
  buckets the 134 MK by in-game tab ("what Support monkey knowledges are there?"), deferring to the
  shipped `deterministic_mk_reference_reply` when a tower is named so the two MK builders never both
  fire. **(2) Slot-4 reframe — bloon *modifier explainer*** — `bloon_modifiers()` +
  `deterministic_bloon_modifier_reply` own the grounded camo/fortified/regrow explanation off the
  three `category:"modifier"` marker entries, reframing "which bloons are camo?" instead of
  assembling the misleading `[DDT]` roster (the original slot-4 "property roster" stays rejected);
  defers whenever a tower / detect-or-pop verb / tower-subject is present (the capability roster's
  job). **(3) Geraldo starting-kit angle** — extended the shipped `deterministic_geraldo_per_level_reply`
  (no redundant sibling) so "what does Geraldo start with" maps to his level-0 items (the gap the
  per-level/list cue missed). The night queue is now fully consumed (every ready slot, the slot-4
  reframe, both buffer slices). `check_quality --full` green (10344, +14) · arch 0 · exclusivity
  invariant + per-builder tests
  (`test_btd6_mk_category_roster.py`, `test_btd6_bloon_modifier.py`, `test_btd6_geraldo_per_level.py`).
- **#1010 (2026-06-17, AI §7.6 — deterministic BTD6 hero ability roster floor + slot-4 reframe)** —
  third slice of the same scheduled dispatch fire (after #1008 + #1009). Adds the **hero ability**
  roster — the per-hero sibling of the capability / bloon / relic rosters. "what abilities does
  Quincy have?", "list Adora's abilities" lists a hero's abilities (level + name + summary) so the
  model can never mis-level / mislabel one (BUG-0009). `btd6_data_service.hero_abilities(name)`
  resolves one hero via the shared surface resolver, returns abilities ascending by level, `None`
  on miss; `btd6_context_service.deterministic_hero_ability_roster_reply` fires on an ability cue +
  exactly one resolved hero, defers on a cost cue (the hero *cost* builder's job), strategy, and
  zero/multi-hero asks; registered in `_BTD6_LIST_BUILDERS` after the relic roster. The "which
  heroes have an ability at level N" cross-query was dropped (data carries only levels 3 & 10
  uniformly → degenerate). **Also reframed night-queue slot 4** (bloon property roster) to
  `NEEDS-REFRAME`: `properties[]` does not cleanly answer "which bloons are camo/fortified/regrow"
  (those are universal modifiers, not per-type properties — a roster from it would be a fresh
  BUG-0009 mis-assembly); the queue doc carries the reframe options. Ships under Q-0048.
  `check_quality --full` green (10318, +14); arch 0; mypy clean. Tests:
  `tests/unit/services/test_btd6_hero_ability_roster.py` + the §7.6 exclusivity corpus entry.
- **#1009 (2026-06-17, AI §7.6 — deterministic BTD6 relic category/effect roster floor)** —
  same scheduled dispatch fire as #1008, continuing down the ▶ NIGHT QUEUE (slot 3) after #1008
  merged. Adds the **relic** member of the §7.6 BUG-0009 roster floor — the Contested Territory
  sibling of the shipped capability roster (towers) and bloon roster (#975). "what economy relics
  are there?" / "list all offensive relics" / "which relics are utility?" buckets the 24 CT relics
  by `category` (+ each relic's `effect`) so the model never mis-buckets the list (every relic name
  is grounded, so a mis-*grouping* slips past the value-only faithfulness guard).
  `btd6_data_service.relics_by_category()` groups `ct_relics.json` by category in a fixed order
  (offense · economy · lives · powerup · utility), name-sorted within each group;
  `btd6_context_service.deterministic_relic_roster_reply` fires on a relic subject + an enumeration
  shape (a named category → that category's relics+effects; a bare "all relics" → every relic
  grouped), with a `_mentions_specific_relic` guard that defers single-relic effect lookups ("what
  does the el dorado relic do"). Registered in `_BTD6_LIST_BUILDERS` after the bloon roster.
  Ships under Q-0048. `check_quality --full` green (10304, +12); arch 0; mypy clean. Tests:
  `tests/unit/services/test_btd6_relic_roster.py` + the §7.6 exclusivity corpus entry. Next
  night-queue `TODO` = slot 4 (bloon property roster).
- **#1008 (2026-06-17, AI §7.5 — deterministic BTD6 power cost-comparison floor)** — scheduled
  dispatch (empty work order → the live ▶ NIGHT QUEUE, slot 2). Adds the **power**
  (activated-ability) member of the §7.5 multi-entity cost-comparison floor — the power-store
  sibling of the shipped hero #1000 / paragon #962 / tower #946 / difficulty #950 builders.
  "which power is cheaper, Cash Drop or Monkey Boost?" ranks the **Monkey Money** store price of
  **two-or-more** powers — the BUG-0009 "grounded values, wrong assembly" class the value-only
  faithfulness guard can't catch. Powers cost a *fixed* Monkey-Money price (no difficulty
  scaling), so the primitive has **no difficulty axis** (the one shape difference from #1000).
  `btd6_data_service.compare_power_costs(names)` resolves each power via the shared `find_power`
  resolver, dedups on id, ranks ascending by `monkey_money_cost`, fails closed (<2 distinct);
  `btd6_context_service.deterministic_power_cost_comparison_reply` fires on a cost-compare cue +
  ≥2 resolved powers (defers on a `paragon` cue, strategy, single-power lookups), registered in
  `_BTD6_LIST_BUILDERS` after the hero builder (mutually exclusive with the tower/hero/paragon
  builders by construction). Ships under Q-0048 (read-only deterministic floor, no prod-check).
  `check_quality --full` green (10292, +38); arch 0; mypy clean. Tests:
  `tests/unit/services/test_btd6_power_cost_comparison.py` + the §7.5 exclusivity corpus entry.
  Next night-queue `TODO` = slot 3 (relic category/effect roster).
- **#1000 (2026-06-16, AI §7.5 — deterministic BTD6 hero cost-comparison floor)** — scheduled
  dispatch (empty work order → the live ▶ NIGHT QUEUE, slot 1). Adds the **hero** member of the
  §7.5 multi-entity cost-comparison floor (the hero-entity sibling of the shipped paragon #962 /
  tower #946 / difficulty #950 builders): "is Quincy or Benjamin cheaper?", "cheapest hero out of
  Gwen, Striker, Ezili" ranks the base placement cost of **two-or-more** heroes — the BUG-0009
  "grounded values, wrong assembly" class the value-only faithfulness guard can't catch.
  `btd6_data_service.compare_hero_costs(names, *, difficulty="medium")` resolves each hero via the
  shared surface resolver, dedups on id, difficulty-scales the stored Medium `base_cost`, ranks
  ascending, fails closed (<2 distinct); `btd6_context_service.deterministic_hero_cost_comparison_reply`
  fires on a cost-compare cue + ≥2 resolved heroes (defers on a `paragon` cue, strategy, single-hero
  lookups), registered in `_BTD6_LIST_BUILDERS` before the tower cost builders (mutually exclusive
  with them by construction — they need a `(tower, crosspath)` candidate a hero never yields). Ships
  under Q-0048 (read-only deterministic floor, no prod-check). `check_quality --full` green (10262,
  +40); arch 0; mypy clean. Tests: `tests/unit/services/test_btd6_hero_cost_comparison.py` + the
  §7.5 exclusivity corpus entry. Next night-queue `TODO` = slot 2 (power activated-ability cost).
- **Developer dashboard — LIVE (2026-06-16, owner-requested, Q-0155)** — a personal website /
  developer dashboard deployed as a **second Railway service**
  (https://superbot-dashboard.up.railway.app), auto-redeploying on merge to `main`. Shipped across
  **#967** (read-only MVP: functions · ideas · bugs · updates · showcase), **#969** (`/env` env-usage
  map), **#970** (deploy fix), **#972** (`/commands` cog & command explorer), **#973** (command-count
  reconcile + bot status-embed full count), **#977** (`/settings` catalogue via `scripts/scan_settings.py`
  + `/access` permissions map via `scripts/scan_access.py` — a verified mirror of
  `utils.visibility_rules`; + the live help-editor design doc), **#979** (`/settings` 500 fix — Jinja
  `domain.keys` resolved to the dict method), **#984** (`/settings` enriched with typed `SettingSpec`
  type/default/hint/choices via `scripts/scan_setting_specs.py`), **#982** (`/aliases` suggestion form with
  live collision check + prefilled GitHub issue), **#983** (`/games` showcase + the settings-editor design
  Q-0157), and **#985** (`/status` build & health surface — git-derived `meta.build` deployed-version
  banner + inventory counts + open-bug & access-tier health; the last Q-0156 *passive* read-only surface).
  **#986** + **#987** documented the free multi-user control-panel identity/authority design + the
  next-session handoff, and **#988** turned `/commands` into a **management surface** — a Manage panel on
  every command and cog (current aliases · cog-routing state · per-command alias box), front-ending
  `command_routing` + the synonym layer read-only (**Q-0160:** cog-level enable/disable now, per-command
  later). Decoupled
  FastAPI app under `dashboard/` fed by stdlib scanners; **never imports `disbot/`**. The Q-0156 read-only
  surfaces are now all shipped. **Bot-side live-editor foundation started: #989** (`disbot/control_api.py`)
  — a **dormant-by-default** private control API on the existing health server: shared-secret bearer auth
  + the **identity→authority bridge** (`/control/authority` resolves a member's visibility tier; the bot
  decides, never the browser). Read-only; **activates only when `CONTROL_API_TOKEN` is set** on the Railway
  services (zero prod change otherwise). Mutation endpoints over the audited seams come next. Phases 2 (auth + checklist + public bug form) /
  3b (Railway secret management) / 4 (multi-AI control board) remain, plus the owner-approved **live
  help/panel editor** (Q-0156): edit help live from the website via a private bot control API over the
  existing audited `help_overlay_mutation` seam + Discord OAuth — designed in
  [`planning/dashboard-live-editor-plan.md`](planning/dashboard-live-editor-plan.md) (L0–L3), built next.
  Authoritative record + handoff: [`planning/developer-dashboard-plan.md`](planning/developer-dashboard-plan.md).
- **#994 + #964 + #960 + #958 + #957 (2026-06-16, docs/architecture maturation — collaboration-model grounding + the architecture-atlas Q-0151 arc)** — one grouped entry (all docs/tooling, no `disbot/` runtime). **#994** grounded `docs/collaboration-model.md` in the Claude Code expertise research. **The Q-0151 architecture-atlas arc** (response to the owner-uploaded outside-in repo-architecture review): **#957** captured the review + agent judgment (direction right — a *generated* atlas over a filesystem reorg — but the drift diagnosis overstated and the per-file dashboard ~80% already `context_map.py`); **#958 (Q-0151c)** shipped the genuinely-new signal, an extension-type taxonomy crosswalk (43 ext ↔ 33 subsystems) via `scripts/extension_crosswalk.py` + a CI guard; **#960 (Q-0151a)** added a thin repo-wide architecture atlas (PR 2); **#964** added a soft `check_docs` inventory-count guard and closed the Q-0151 thread.
- **#993 + #990 + #974 (2026-06-16, developer-dashboard / control-API initiative — Q-0155…0160)** — the new owner-commissioned **personal developer dashboard** (a management website for the bot) begins. **#974**: the comprehensive dashboard plan + next-session handoff. **#990**: a `dashboard.json` integrity guard that catches export drift. **#993 (control-API write side)**: `feat(control-api)` mutation endpoints over the **audited service seams** (no DB bypass) — the write half of the dashboard's edit-settings / edit-help surfaces (Q-0156/0157). Owner decisions Q-0155–Q-0160 (dashboard shape · live editor · per-server settings · Discord-login multi-user panel · cog-level command toggles) are recorded in the router. **#995**: sub-cog→subsystem mapping (merged). **#996 (control panel — Discord OAuth login + editors)**: the multi-user `/admin` — sign in with Discord → pick a server you administer → edit settings / help appearance / cog routing **live** through the audited seams; stdlib HMAC-signed session (no `itsdangerous`/`multipart` — fewer deps to version-match). **#1001**: health server **IPv6 dual-stack bind** (`HEALTH_HOST=::`) so the dashboard reaches the control API over Railway's IPv6 private network. **#1002**: the finalized-state **vision plan** (`planning/dashboard-vision-finalized-state.md` — the north-star above the two execution plans; Q-0161/Q-0162). **🟢 The control panel is now LIVE in production (2026-06-17):** `CONTROL_API_TOKEN` + the Discord OAuth secret are set on both Railway services; owner-confirmed login + live edits, and the bot logs `control_api: enabled` / `Health server listening on :::8080`. **Next gap:** the control-API *read* endpoints so editors show each server's **current** value (today they write blind).
- **#981 + #978 + #976 + #971 + #968 + #966 + #965 + #959 + #952 (2026-06-16, autonomous-loop ops hardening — Hermes skills + CI conflict-guard + rate-limit hygiene)** — one grouped control-plane/ops entry (docs/skill/CI/Hermes only; no `disbot/` runtime). **Hermes:** **#959** added three skills (idea-spotlight · morning-briefing · dispatch-resolve) + a 6h interactive session auto-reset (Q-0153); **#971** made morning-briefing + idea-spotlight rate-limit-lean; **#976** captured a TPM rate-limit finding + fixed reset/compaction guidance; **#978** compared gpt-5-mini vs gpt-5.4-mini + deprecated `--set-model`; **#981** added a staleness guard to `install-skills.sh` (stale-skill root cause); **#952** retried `railway_logs` on transient 5xx / connection errors. **CI conflict-guard (Q-0154):** **#965** auto-updates behind PRs + reddens on conflict, **#966** fixed its token + bash-errexit safety, **#968** scoped it to evaluate only the triggering PR (cut noise).
- **#975 (2026-06-16, AI §7.6 — deterministic BTD6 property/capability roster floors)** — scheduled
  dispatch (empty work order → the live ▶ NEXT lane, "a *new* AI §7 workflow family beyond §7.5"). The
  §7.5 *comparison* family is COMPLETE (#946/#950/#955/#962); this opens the next family — the
  **property/capability roster** (a *list-by-property*, not a rank/diff), the same BUG-0009
  wrong-assembly class on the roster side. **Two members shipped:** (1) `deterministic_capability_roster_reply`
  fronts the authoritative `btd6_capability_service` ("which towers can pop lead / detect camo / pop
  black-white-purple?") — base 0-0-0 scope by default, an explicit "with upgrades" signal flips to the
  earliest-upgrade roster, a `paragon` cue answers the per-paragon camo roster; (2)
  `deterministic_bloon_roster_reply` fronts the committed `bloons.json` fields ("what are all the
  MOAB-class bloons", "which bloons are immune to sharp/cold/explosion?") via `category` + `immune_to`,
  modifier pseudo-bloons excluded — the bloon side the sibling `deterministic_roster_reply`
  (heroes/towers/paragons/maps) never covered. Both ride the shared `_BTD6_LIST_BUILDERS` seam (no
  integration change), are read-only deterministic (Q-0048, no prod-check), and are held to the
  `test_btd6_floor_builder_exclusivity.py` one-fires invariant (corpus extended for both). `check_quality
  --full` green (10184, +40 tests); arch 0; mypy clean. Tests:
  `tests/unit/services/test_btd6_capability_roster.py` + `tests/unit/services/test_btd6_bloon_roster.py`.
  The next AI §7 step is a further §7.6 roster member (e.g. hero/relic property lists) or a *new* family
  beyond rosters+comparison (plan-first).
- **#963 + #991 + #953 + #946 (2026-06-16, BTD6 AI floors + fixes)** — **#946**: the **first** §7.5 multi-entity comparison floor member — deterministic tower cost-comparison (`compare_crosspath_costs` + `deterministic_cost_comparison_reply`, on the `deterministic_btd6_list_reply` dispatcher) — the BUG-0009 "grounded values, wrong assembly" class; #950/#955/#962 built the difficulty/round-range/paragon members on it (**§7.5 comparison family now complete**). **#963 (BUG-0015)**: "d67 dart paragon" was misread as upgrade path "0-6-7" — fixed the parse + route + grounded a paragon *degree*; **#991** captured the BUG-0015 tail as a BTD6 shorthand-corpus eval idea (the recurring router-class guard). **#953**: current-event-first Live Events + fixed the dead event drill-down. `check_quality` green; arch 0.
- **#962 (2026-06-16, AI §7.5 — deterministic BTD6 paragon base-cost comparison floor)** — scheduled
  dispatch (empty work order → the live ▶ NEXT buildable plan-first lane, the AI §7 workflow family).
  Adds the **paragon** member — the last unbuilt §7.5 multi-entity comparison member (the
  paragon-entity sibling of the #946/#950 tower cost builders): "is Glaive Dominus or Ascended Shadow
  cheaper?" ranks the **base tier-6 build price** of **two or more** paragons (BUG-0009 wrong-assembly
  class). `btd6_data_service.compare_paragon_costs(names, *, difficulty="medium")` resolves +
  difficulty-prices each paragon via `paragon_math.base_price` over the committed `BASE_PRICES_MEDIUM`,
  dedups on id, ranks ascending, fails closed (<2 distinct); a new public
  `paragon_math.paragon_surfaces()` exposes the resolver surfaces for sentence scanning.
  `btd6_context_service.deterministic_paragon_cost_comparison_reply` fires on an explicit `paragon`
  token + a cost-compare cue + ≥2 resolved paragons, registered in `_BTD6_LIST_BUILDERS` **before**
  the tower cost builders, which now defer on the paragon cue so a "dart/ninja paragon" question is
  never priced as the base tower (exactly-one-fires invariant extended). Ships under Q-0048 (read-only
  deterministic floor, no prod-check). `check_quality --full` green (10051); arch 0; mypy clean.
  Tests: `tests/unit/services/test_btd6_paragon_cost_comparison.py` + the §7.5 exclusivity corpus
  entry. **§7.5 multi-entity comparison family is now COMPLETE — all four members shipped (tower-cost
  #946 · difficulty-cost #950 · round-range cash #955 · paragon base-cost #962).** The next AI §7
  step is a *new* workflow family beyond §7.5 (plan-first); a paragon *degree-target* resource
  comparison is captured as a session idea (needs design — the solver's "cash" axis ≠ real spend).
- **#956 + #954 + #951 + #949 + #948 (2026-06-16, fixes + tooling)** — **#956**: acted on the autonomous-run review (closed flagged loops + recorded owner answers). **#954**: `scripts/extract_video_frames.py` — view maintainer-sent videos in one command. **#951**: a `!coglist` text command wired to the admin panel's 📋 Cog List button (button↔command parity); **#949 (BUG-0014)**: stopped the `!coglist` infinite "assumed from" loop (a dangling synonym→nonexistent-command reference that failed silently). **#948**: release the runtime singleton lock early on shutdown — kills ~85s deploy downtime. `check_quality` green; arch 0.
- **#955 (2026-06-16, AI §7.5 — deterministic BTD6 round-range cash comparison floor)** — scheduled
  dispatch (empty work order → the live ▶ NEXT buildable plan-first lane, the AI §7 workflow family).
  Adds the **round-range** member of the §7.5 multi-entity comparison floor (the income sibling of
  the #946 tower-vs-tower and #950 by-difficulty *cost* members): "which earns more cash, rounds
  20-40 or 40-60?" ranks the total cash of **two or more** inclusive round ranges — the model would
  otherwise assemble that ranking itself and can mis-state which range earns more / by how much (the
  BUG-0009 "grounded values, wrong assembly" class the value-only faithfulness guard can't catch).
  `btd6_data_service.compare_round_ranges(ranges, *, roundset="default")` prices each range once via
  the existing `round_cash` primitive (the same owner the round-cash workflow uses, so per-round
  figures never drift), dedups normalized ranges, ranks descending, fails closed (<2 distinct
  priceable ranges), and is ABR-aware; `btd6_context_service.deterministic_round_range_comparison_reply`
  fires on an earning noun (`cash`/`money`/`income`/`earn`) + a comparison signal (`more`/`vs`/`or`/
  `compare`…) + **≥2** parsed round ranges (a round token required before each range's first anchor,
  so crosspath codes like `5-0-0` are never mis-read as ranges), appended to the
  `deterministic_btd6_list_reply` dispatcher. Stays non-overlapping with the single-range round-cash
  workflow on **range count**, and the floor short-circuits before that workflow ever runs.
  `check_quality --full` green (10008, +18); arch 0; mypy clean. Tests:
  `tests/unit/services/test_btd6_round_range_comparison.py`. **§7.5 comparison family now covers cost
  (tower + difficulty) + round-range cash; the one remaining member is paragon degree/resource.**
- **#950 (2026-06-16, AI §7.5 — deterministic BTD6 difficulty cost-comparison floor)** — scheduled
  dispatch (empty work order → the live ▶ NEXT buildable plan-first lane, the AI §7 workflow family).
  Adds the **difficulty member** of the §7.5 multi-entity comparison floor (the sibling of the #946
  tower-vs-tower cost comparison): "is a 0-4-1 desperado cheaper on medium or impoppable?" ranks the
  **same** upgrade state across difficulties — a single tower, so #946's multi-tower builder defers
  and the question would otherwise reach the model, which can mis-state which difficulty is cheaper
  (the BUG-0009 "grounded values, wrong assembly" class the value-only faithfulness guard can't
  catch). `btd6_data_service.compare_difficulty_costs(tower, code, difficulties)` prices the one
  upgrade state once (`crosspath_cost` already returns every difficulty), ranks ascending, fails
  closed (<2 distinct valid difficulties); `btd6_context_service.deterministic_difficulty_cost_comparison_reply`
  fires on a cost-compare cue + **exactly one** resolvable `(tower, crosspath)` (≥2 is the #946
  builder — mutually exclusive on candidate count) + **≥2** named difficulties, appended to the
  `deterministic_btd6_list_reply` dispatcher. `check_quality --full` green (9972, +14); arch 0.
  Tests: `tests/unit/services/test_btd6_difficulty_cost_comparison.py`. **§7.5 cost-comparison family
  (tower + difficulty) is now complete; the remaining §7.5 members are paragon + round-range, both
  unbuilt.**
- **#947 + #945 + #944 (2026-06-16, routine-hardening — Q-0148/0149/0150)** — **#947 (Q-0150)**: made `settings.json` hooks **cwd-robust** (resolve `$CLAUDE_PROJECT_DIR`, not relative `scripts/`), killing the cwd-deadlock trap. **#945 (Q-0149)**: expanded the routine permission allow-list so scheduled runs don't stall on a prompt. **#944 (Q-0148)**: recorded that the dispatch routine is **never "docs only"** (it always advances the plan). Config/docs only. *(This band-#990 pass's Q-0161 further narrows the `rm` permission brake to recursive-only — the same routine-stall class.)*
- **#942 (2026-06-16, docs(current-state): reconcile ledger — add #932–#936, #939)** — a dispatched
  living-ledger reconciliation: added the six then-missing PRs (#932, #933, #934, #935, #936, #939)
  to § Recently shipped and archived the eight oldest live entries to hold the ~20 soft-ratchet
  (titles verified against live GitHub). Docs only; no runtime code. *(Self-recorded by the next
  dispatch session #943 — a reconciliation PR doesn't add its own entry, the small recurring drift
  the strict ledger guard exists to catch.)*
- **#940 (2026-06-16, myprofile PR B — self-service writes: the pipeline's first UI consumer)** — the
  band-#930 decade-queue slot 3 continuation (PR A read-only card shipped #938). Makes `/myprofile`
  interactive: a new `disbot/views/profile/editor.py` owner-locked ephemeral editor stack —
  `ProfileEditorHomeView` (subsystem picker) → `ProfileSubsystemEditorView` (participation opt-in/out ·
  per-`SubscriptionSpec` toggles · visibility public/hidden · preference editors: bool→toggle,
  enum→select, int/str/float→modal). **Every control is exactly one audited
  `ParticipationMutationPipeline` call**, re-render from the typed accessors (cache-invalidated, so the
  re-read is truthful — the Help-editor stack pattern); typed `ParticipationMutationError`s render as
  ephemeral copy, never a crash. Self-scoped by construction (actor==subject; the pipeline re-validates).
  The read-only card stays mutation-free (PR A's AST pin intact) — the `⚙️ Manage settings` button lazily
  opens the editor. This is the **first real exercise of the shipped-but-unused pipeline** (migrations
  027/028). The `/myprofile` lane is now buildable-complete; PR C (onboarding) is owner-gated → router
  Q-0147. `check_quality --full` green (9933 + 13 new); arch 0; mypy clean. Tests:
  `tests/unit/views/test_profile_editor.py` (one-call-per-action spy · typed-error copy · unauthorized
  path · int-modal coercion/reject · enum-chooser-opens-no-write · AST pin: editor writes only through
  the pipeline, no `utils.db` import).
- **#939 (2026-06-16, docs(ideas): capture diagnostic_cog !platform-group extraction)** —
  backlog-grooming ender (Q-0015). The faucet/sink diagnostic (#937) pushed `diagnostic_cog.py` to
  799/800 LOC — the hard cog-size ceiling — and the cause + fix lived only in `.sessions/` logs
  (which sessions don't read top-to-bottom), so the next `!platform` subcommand would hit the wall
  cold. New idea `docs/ideas/diagnostic-cog-platform-group-extraction-2026-06-16.md`: extract the
  `!platform` command group onto a `PlatformCommandsMixin` (`cogs/diagnostic/platform_group.py`) so
  the surface can grow past the 800-LOC cog ceiling while the command identity stays on
  `DiagnosticCog` (the same F-3 "surface = cog, weight = `cogs/<sub>/`" convention the embed-builder
  extraction used). Small/safe/decided-lane pure refactor; README indexed. `check_docs --strict`
  green; docs only.
- **#938 (2026-06-15, myprofile PR A — read-only profile card)** — decade-queue slot 3. `views/profile/`
  + `/myprofile` + `!myprofile`: a schema-driven read-only card composing the typed accessors over the
  participation registry (one section per registered subsystem, every value labelled with its default,
  Q-0058 idiom), owner-locked ephemeral, zero writes (AST-pinned). The shell + `preference_key`
  convention PR B (#940) extends.
- **#936 (2026-06-16, fix: counting channel selector/whitelist UI · BTD6 overview de-clutter ·
  round-63 camo-lead data)** — three owner-reported bugs from a live manual-testing recording.
  **(1) Counting cog** — the Counting Manager (`!countingmenu`/`!cm`) only operated on the *current*
  channel, with no way to *select* a channel or enable counting on an existing one (a tester hit
  exactly "where to change whitelisted channels"). Added a `ChannelSelect` picker; a mode-picker
  that *enables counting on a non-counting channel* (the "whitelist" flow, no fresh channel); and a
  **🛑 Disable Here** button that removes a channel from the active set without deleting it (distinct
  from `!end_match`). Mutations route through new audited-pattern cog methods
  (`enable_channel`/`disable_channel`/`toggle_channel_flag`/`reset_channel_count`) holding the
  per-guild lock, in `cogs/counting/_channel_manager.py` (under the 800-LOC gate). **(2) BTD6
  overviews** — `!btd6 tower`/`hero` overviews + the hero browser detail dumped a huge "Live data"
  event-restriction section that the design says belongs only in the ⚠️ Event-status drill-down;
  the three missed call-sites now match (also drops a per-lookup event-scan DB call). **(3) Round
  63** wrongly listed "Camo Lead" (it's 75 plain Lead + 122 plain Ceramic — the only such
  inconsistency across 140 rounds); corrected to `["Lead","Ceramic"]` + a CI guard
  (`test_btd6_round_threat_consistency.py`) so a curated threat can never again claim a bloon
  modifier no group carries. `check_quality --full` green (9897); arch 0.
- **#935 (2026-06-15, ideas: re-file Honcho as a bot / AI-lane idea — per-user AI memory)** —
  owner-requested re-file of the Honcho capture as a **bot/AI-lane** idea: give SuperBot's AI
  **per-user memory** (remember a Discord user across conversations — the V-04 vision item) via
  Honcho's conclusion-extraction memory (cheaper than dumping raw history under the Q-0082 AI-spend
  ceiling). Demoted the "not for Hermes" verdict to a footnote; added a "what to look into" section
  (scope/privacy, cost, AI-cog integration seam, alternatives) + a disposition to promote to a
  `docs/planning/` plan when the AI lane has capacity. `check_docs --strict` green; docs/ideas only.
- **#934 (2026-06-15, docs(journal): durable lessons from the security-tiers session)** —
  owner-directed: after the security-tiers session (#929), recorded three lean
  `.session-journal.md` entries — the **cwd-deadlock trap** (never `cd` in the Bash tool; the
  persisted cwd breaks the repo-root-relative hooks and dead-locks Bash + Write/Edit for the turn;
  avoidance = absolute paths / `python3.10 -c` from root, recovery = a worktree-isolated Agent
  commit; durable hook fix noted as proposed Q-0106), a Quick-reference row pointing at it, and
  "check the PR file count before declaring done" (never run black/isort over `tests/`; eyeball
  `git diff --name-only`). `check_docs --strict` green; docs only.
- **#933 (2026-06-15, fix(deathmatch): stop the 1v1 challenge timer on accept/decline — BUG-0013)**
  — the first real bug caught end-to-end by the Hermes `intake` pipeline (#928): the owner reported
  it to Hermes on Discord → `intake` routed + root-caused it → Claude Code verified the diagnosis
  and fixed it. `_ChallengeView` (`disbot/cogs/deathmatch_cog.py`, `timeout=30.0`) never called
  `self.stop()` on accept/decline and `on_timeout` had no answered-guard, so its 30s timeout
  overwrote the live/finished duel message with "⚔️ Challenge Expired". Fix: a `_resolved` flag set +
  `self.stop()` in `btn_accept`/`btn_decline`, and an early return in `on_timeout` when resolved.
  Contained to `_ChallengeView` (no signature changes); behaviour-preserving for the genuine
  no-answer case. `tests/unit/cogs/test_deathmatch_challenge_timeout.py` (3 tests, fail-against-old);
  BUG-0013 recorded FIXED; `check_quality --full` green (9893); arch 0. Live on the next auto-deploy
  (a merge to `main` auto-deploys to Railway — no manual deploy step).
- **#928 + #927 + #925 + #923 + #921 + #919 + #916 + #915 (2026-06-15, Hermes gpt-5.4-mini model-swap + ops-docs maturation band)** — the docs/skill-only band between the BUG-0009 code work and this pass; entered as one grouped entry (all docs-only, same Hermes-operating-layer / ledger-hygiene theme). **#915** — self-healing repo sync (recover a diverged mirror clone). **#916** — recorded the model/provider decision in the ops docs. **#919 → #921 → #923** — the gpt-5.4-mini model-swap arc: model-switch playbook + the "flapping" open item → RESOLVED (the swap was slow propagation lag, gpt-5.4-mini live) → retune base + record verified specs. **#927** — recorded gpt-5.4-mini calibration outcomes + a lean dispatch overlap-check. **#928** — the Hermes `intake` skill (route inbound bugs / ideas / requests / questions to their canonical homes). **#925** — `docs(current-state)`: a scannable ▶ pointer + archived the re-accumulated `Last updated:` stamp wall. *(#930 — Hermes ops docs: lean-env filter how-to + Honcho evaluation + open-steps findability — was already entered.)* All docs/skill/ops only; no `disbot/` runtime code.
- **Older merges (#898 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are archived (`scripts/check_docs.py` soft-ratchets the count). *(The #1000 AI §7.5 hero-cost-comparison session (2026-06-16) added its entry and archived the oldest live one — #932 ninth-Q-0107-pass — to hold the ratchet at 20. The tenth Q-0107 reconciliation pass (band-#990, 2026-06-16) added six grouped Recently-shipped entries covering the #944–#994 band and archived the six oldest live entries to hold the ratchet at 20: #926, #924, #920, #918, #917, #912. The #975 AI §7.6 roster-floor session (2026-06-16) added its entry and archived the two oldest live ones — #910 mining Home + #906 Railway log-triage — to hold the ratchet at 20. The #950 AI §7.5 difficulty-comparison session (2026-06-16) added its entry and archived the oldest live one — #897 mining Vault v2 — to hold the ratchet at 20. The #943 diagnostic-mixin session (2026-06-16) added the #942 ledger-reconciliation entry — a reconciliation PR doesn't add its own entry — and archived the oldest live one, the #898+#892+#889 docs-hygiene group, to hold the ratchet at 20. The #932–#939 ledger reconciliation (2026-06-16) added six live entries — #939, #936, #935, #934, #933, #932 — and archived the eight oldest to hold the ratchet at 20: #884, the #878+#879+#881 P1-1 eval/smoke arc, the #870+#869+#868 Hermes operating-layer arc, #867, #866, #865, #864, #863. The #920 welcome-phase-2 session (2026-06-15) added its entry and archived the oldest live one — #849 born-red merge-gate — to hold the ratchet at 20. The #918 settings-reverse-parity session (2026-06-15) added its entry and archived the oldest live one — #843 P1-2 health-findings — to hold the ratchet at 20. The #917 P1-3 contract-invariants session (2026-06-15) added its entry and archived the four oldest live entries — #856+#853, #851+#850+#848+#852, #840, #839+housekeeping — to bring the ledger back to 20. The #912 mining-Slices-E+F session (2026-06-15) added its entry and archived the oldest live one — #829 P0-2 PR 1 — to hold the ratchet. The #897 mining-Vault-v2 session (2026-06-15) added its entry and archived the oldest live one — #825 P0-4 PR 2 — to hold the ratchet at 20. The #895 non-BTD6 eval-coverage session (2026-06-15) added its entry — folded into the #878 eval bullet, plus the #892+#889 docs-hygiene entry — and archived the oldest live one, #820 P0-4 PR 1, to hold the ratchet. The #884 mining-Vault session (2026-06-14) added its entry and archived the oldest live one — the #814+#815 CI-efficiency arc — to hold the ratchet at 20. The #878 P1-1 eval/smoke session (2026-06-14) added its own entry and archived the oldest live one — the #802…#813 portable-substrate-kit group — to hold the ratchet at 20. The band-#870 reconciliation pass (2026-06-14) added two live entries — the #870+#869+#868 Hermes operating-layer arc and #867 ledger window catch-up — and archived the two oldest to hold the ratchet at 20: the #803… reconciliation+workflow-rules group and the #827… Railway agent-access session. Earlier: the band #841–#860 ledger-reconciliation added eight live entries — #866, #865, #864, #863, #862, #859, the #856+#853 group, and the #851/#850/#848/#852 group — and archived the eight oldest: the #788…#798 substrate-kit arc, #817, #794, the #786+#787 group, #778, #777, #775, #774. Earlier still: the #772 automod-v1 entry was archived to offset #855; the #765+#767+#769+#770 backup-posture entry to offset #849; the #764 P2 doc-drift-sweep entry to offset #843; the band-#840 reconciliation pass archived the #763 second-reconciliation-pass record, the #758/#760/#762 UX-Lab BUILD, and the #753/#754/#756/#759/#761 autonomous-loop wiring; the #755 entry to offset #829; the #746–#754 entry to offset #825; the #741/#742/#745/#748 entries by the band-#820 pass.)*

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
