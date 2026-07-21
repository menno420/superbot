# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger; **not binding — source code + merged PRs win.**
>
> ### 🧭 2026-07-17 — fresh-start cleanup: the autonomous apparatus is winding down
> **superbot is FROZEN as the behavioral oracle for the `superbot-next` rebuild.** No new
> feature work is expected here; the live production bot is stable and the forward queue is
> docs / oracle maintenance, not new features. Ranked next steps: [`NEXT-TASKS.md`](NEXT-TASKS.md).
>
> **EAP status (Claude Code Projects Early-Access Program):** the review window was **extended
> to Tue 2026-07-21**, when the Projects go **read-only** — *not* 2026-07-14, as older entries
> lower in this ledger still say (that earlier date is superseded). The owner is **winding down
> the autonomous coordinator→worker apparatus** and will **recreate the Projects** with better
> coordination after the read-only cutover.
>
> **⚠️ The "permission-classifier denies merges" scare did NOT hold (verified 2026-07-18):**
> mid-July sessions recorded a belief that an Anthropic permission-classifier change was
> **denying** autonomous merges and ready-flips, and each later session copied and amplified the
> restriction. **Ground truth: agents CAN merge their own/sibling green PRs, flip draft→ready, and
> arm auto-merge — merging is normal agent work.** (A direct MCP merge succeeded on 2026-07-18.)
> The dated escalation emails
> ([`eap/anthropic-email-4-classifier-regression-sent-2026-07-16.md`](eap/anthropic-email-4-classifier-regression-sent-2026-07-16.md),
> [`eap/permission-classifier-findings-consolidated-2026-07-16.md`](eap/permission-classifier-findings-consolidated-2026-07-16.md))
> are **historical records** of that scare, not a current wall — do not re-derive a merge
> restriction from them.
>
> **Merge doctrine (corrected 2026-07-18):** open PRs **READY** and **merge your own green PR
> directly** (MCP/REST) the moment it's mergeable — or let the `auto-merge-enabler` workflow land
> it on green; either path is fine, and you never route a mergeable green PR to the owner. The one
> gate is **CI green** (plus the `do-not-automerge` carve-out). If a *specific* permission refusal
> ever occurs on a call, it's **attempt-once, specific to that call/venue/permission-mode** — read
> it, report it verbatim, and **never write it into the docs as a new standing wall**. Full rule:
> `.claude/CLAUDE.md` § "Session & plan workflow". The **real** walls stay real: ref/branch
> deletion (403), tag-push/release (403), raw `api.github.com` (blocked), and repo
> Settings/secrets/env (owner console).
>
> **✅ 2026-07-17 — fleet-wide PR backlog cleared.** The frozen CI-green work across the fleet
> was dispositioned/landed; on superbot specifically the open-PR surface is now empty.
>
> **In flight (verify against live GitHub):** **zero open PRs** (verified live 2026-07-19, band-#2160
> reconcile). The former sole open PR **#2061** (mineverse FLAG 2, the HMAC-signed mining WRITE
> endpoint) was **closed unmerged on 2026-07-17** — it carried a real merge conflict with `main` and
> a live web-write endpoint is an owner deploy-safety call, so it was retired rather than landed.
> FLAG 1 (#2058, the READ relay) remains merged and dormant-by-default; if the WRITE endpoint is ever
> wanted it reopens as fresh work off the current `main`, not by reviving the stale draft.
>
> **Recent records (historical pointers):** fleet-wide cleanup audit
> [`eap/fleet-cleanup-audit-2026-07-13.md`](eap/fleet-cleanup-audit-2026-07-13.md); the 07-13
> doctrine-night review [`eap/night-review-2026-07-13.md`](eap/night-review-2026-07-13.md); the
> 07-12 night review [`eap/night-review-2026-07-12.md`](eap/night-review-2026-07-12.md). The dated
> fleet-dispatch / re-arm order docs under `owner/` are **retired scaffolding — historical only**
> (see `NEXT-TASKS.md` and their in-file banners).
> **Ledger note:** living status ledger (project state). **Not binding.**
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
> | **S3 AI-Memory** | [`current-state/S3-ai-memory.md`](current-state/S3-ai-memory.md) | settle-once money-safety guard (#1454) + cross-domain routing-disjointness guard (#1470); **self-improving-workflow guards #1476/#1477/#1479/#1482/#1495**; **owner re-elevated the portable substrate-kit to top focus (fresh-rebuild vision #1589/#1590)**; **rebuild design spec shipped (#1637/#1638) + BOTH linchpins now built & measured (#1639 — Phase-0.5 golden harness `parity/` + grammar spike, verdict GO-with-amendments)**; **substrate-kit finalized (#1649 — nervous system + context-economy engine + one-step-adopt; 407 kit tests)**; **Gate V COMPLETE (#1767); owner gates RETIRED (Q-0241/#1776); Phase-2.5 CLOSED (#1775 FAIL-as-tested → adopt-render fix + re-run pair, #1778); the FINAL review ran (#1778 — verdict: plan ready, §11 amendments folded, readiness scored); the idea-consolidation pass folded today's four owner captures + hardened the §3.C risks into machinery (#1791 — §11b A-12…A-20, registry mints R-16/R-17/P-5)**; ▶ **next: the rebuild runs LIVE in `superbot-next`** (50/51 parity rows ported; live items = merge-wall drain — see [`owner/next-session-brief-2026-07-13.md`](owner/next-session-brief-2026-07-13.md) §3 — + the D-0043 deep-game go/no-go (D-0043 is a **superbot-next** decision — owning artifact: [menno420/superbot-next decisions ledger, entry D-0043](https://github.com/menno420/superbot-next/blob/main/docs/decisions.md), which names the deep-game successor-port scope)); plan of record = [`planning/rebuild-canonical-plan-2026-07-06.md`](planning/rebuild-canonical-plan-2026-07-06.md) |
> | **S4 Docs system** | [`current-state/S4-docs.md`](current-state/S4-docs.md) | 50th Q-0107 pass done (band-#2190); next recon at #2220; **⚠️ PLAN BACKLOG THIN** (superbot frozen as oracle — forward queue is `superbot-next` + docs upkeep, not in-repo features) |
> | **S5 Operations** | [`current-state/S5-ops.md`](current-state/S5-ops.md) | merge=deploy clarity (Q-0193); loop self-fires; ▶ website rollout (owner/Hermes); **review-site refresh + AI-assistant + homepage order → [`owner/websites-review-site-order-2026-07-12.md`](owner/websites-review-site-order-2026-07-12.md)**; **trigger-health check order (fleet-manager) → [`owner/trigger-health-order-2026-07-12.md`](owner/trigger-health-order-2026-07-12.md)** |
>
> **📋 2026-07-11 fleet review + centralization + dispatch kit (owner-directed hub session):**
> verified full-fleet triage (keep/replace/archive/delete per repo) →
> [`planning/fleet-review-2026-07-11.md`](planning/fleet-review-2026-07-11.md); the
> `fleet-manager`-as-single-source-of-truth design →
> [`planning/fleet-centralization-plan-2026-07-11.md`](planning/fleet-centralization-plan-2026-07-11.md);
> the 6 paste-ready help-session prompts + the fleet permissions/workarounds block →
> [`owner/dispatch-prompts-2026-07-11.md`](owner/dispatch-prompts-2026-07-11.md); and the
> synthesis of 4 independent external strategy reviews (next-batch shortlist + the 3 portfolio
> decisions) → [`planning/fleet-strategy-synthesis-2026-07-11.md`](planning/fleet-strategy-synthesis-2026-07-11.md);
> and the **consolidation + next-round blueprint** (4 owner decisions finalized → each
> project's fate + the superbot-next cutover threshold) →
> [`planning/fleet-consolidation-and-next-round-2026-07-11.md`](planning/fleet-consolidation-and-next-round-2026-07-11.md);
> and the **next-round founding-prompt kit** (verified every project prompt/instruction; the
> improvement delta + the 2 new merged-Project instruction bodies) →
> [`owner/next-round-founding-prompts-2026-07-11.md`](owner/next-round-founding-prompts-2026-07-11.md).
> **▶ CURRENT fleet structure (8 standing Projects — supersedes the "one Games Project" framing):**
> [`owner/fleet-8seat-structure-2026-07-11.md`](owner/fleet-8seat-structure-2026-07-11.md) (per-seat
> repos / environment / mission + dispatch guidance for canonicalizing the registry). The **latest
> session's next-session brief** (5/8 seats' startup prompts delivered; Ideas Lab / Game Lab /
> Websites remaining; owner env-mapping open) is in `.sessions/2026-07-11-fleet-dispatch-prompts.md`.
> **Earlier post-compact record** (fleet wrap-up, merge-session results, owner-action queue) →
> [`eap/session-handoff-2026-07-11-fleet-management.md`](eap/session-handoff-2026-07-11-fleet-management.md).
>
> **2026-07-13 doctrine-night reviewed (owner-live, Q-0272 path end-to-end)** — the first
> fully-doctrined unsupervised night verified: ~190+ PRs across 12 repos, 18 hands-free
> idea→verdict cycles, superbot-next at 51/51 parity rows (CUT-1 done), venture 3→6
> publish-READY (~215k words verified real); the scheduler degraded again (~01:07–02:08Z)
> but **zero seat deaths** (the failsafe doctrine held); 3 manager-tally narrative
> distortions found (every checkable number was exact); binding constraint = owner clicks.
> Per-lane digest + consolidated owner queue →
> [`eap/night-review-2026-07-13.md`](eap/night-review-2026-07-13.md) (PR #2064).
>
> **2026-07-12 overnight batch reviewed** — the **trigger-scheduler incident** (~02:30–08:00Z:
> 9 dropped `send_later` one-shots + 2 wedged crons; the Q-0265 failsafe doctrine validated in
> production; Venture Lab dark, kit-lab manually re-fired; cross-session trigger revival is
> org-disabled) + per-seat digest, lessons, fix-first list and owner-action queue →
> [`eap/night-review-2026-07-12.md`](eap/night-review-2026-07-12.md).
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
> **Last updated:** 2026-07-21 — **fiftieth Q-0107 reconciliation pass (band-#2190, issue #2191
> — record in [`.sessions/2026-07-21-reconcile.md`](../.sessions/2026-07-21-reconcile.md));** reconciled
> band #2161–#2190 (20 PRs — **entirely docs/CI/tooling + generated artifact + 2 dep bumps, zero
> `disbot/` runtime**, matching the oracle-freeze posture: the **49th-pass reconcile** #2162, **2
> Dependabot bumps** #2174 (fastapi) / #2179 (anthropic), and **17 dashboard refreshes**
> #2163…#2170/#2180…#2183/#2186…#2190), trimmed Recently-shipped to 20, **disposed the open-PR set** —
> **8 open Dependabot dep-bump PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2184/#2185 — the runtime dep
> lane, Q-0256, left in flight; not this docs-only pass), no stale session PR; confirmed ROUTINE_PAT set /
> loop self-fires (issue #2191 authored by `menno420`), **⚠️ carried PLAN BACKLOG THIN** — the in-repo
> product backlog is intentionally frozen (oracle-freeze), so there is no 30-PR feature band to plan; the
> honest forward queue is `NEXT-TASKS.md` (superbot-next rebuild cutover + docs curation + owner-gated
> calls), refreshed the dashboard export, marker #2160 → #2190. Supersede-banner soft warnings unchanged
> at **9** (honest cross-repo phantom successors in fleet-manager the in-repo checker can't resolve).
> Earlier: 2026-07-19 — **forty-ninth Q-0107 reconciliation pass (band-#2160, issue #2161
> — record in [`.sessions/2026-07-19-reconcile.md`](../.sessions/2026-07-19-reconcile.md));** reconciled
> band #2132–#2160 (29 PRs — **entirely docs/CI/tooling + generated artifact, zero `disbot/` runtime**,
> matching the oracle-freeze posture: 6 docs/CI/tooling PRs #2132/#2133/#2136/#2145/#2146/#2148 — the
> **48th-pass reconcile** #2132, its **Codex follow-up** #2133, the **fresh-start oracle-freeze
> banner + `NEXT-TASKS.md`** #2136, the **"dewall"** removing the false *"agents cannot merge"* wall
> #2145, a **manual branch-cleanup workflow** #2146, and **EAP follow-up evidence** #2148; plus **23
> dashboard refreshes**), trimmed Recently-shipped to 20, **disposed the open-PR set** — **zero open
> PRs** (the former sole open PR #2061, the mineverse FLAG 2 WRITE draft, was **closed unmerged
> 2026-07-17** — real merge conflict + owner deploy-safety call; `NEXT-TASKS.md` item 1 updated to
> "reopens as fresh work if wanted"), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires
> (issue #2161 authored by `menno420`), **⚠️ raised PLAN BACKLOG THIN** — the in-repo product backlog
> is intentionally frozen (oracle-freeze), so there is no 30-PR feature band to plan; the honest
> forward queue is `NEXT-TASKS.md` (superbot-next rebuild cutover + docs curation + owner-gated calls),
> refreshed the dashboard export, marker #2130 → #2160. Supersede-banner soft warnings unchanged at **9**
> (honest cross-repo phantom successors in fleet-manager the in-repo checker can't resolve).
> Earlier: 2026-07-17 — **forty-eighth Q-0107 reconciliation pass (band-#2130, issue #2131
> — [pass record](planning/reconciliation-pass-2026-07-17-band2130.md));** reconciled band #2102–#2130
> (grouped entries — the band is **entirely docs/tooling/control**, zero `disbot/` runtime: the
> **fleet pre-archive sweep + EAP closeout arc** #2104/#2105/#2110/#2111/#2121/#2126 — the owner-live
> fleet-wide pre-archive sweep session log #2104, the **EAP project audit + closeout walkthrough (ORDER
> 006)** #2105 (raised the top-level-docs ratchet 21→22 to pin the walkthrough path), the **ORDER 005
> supersession stubs + ORDER 003 stale live-Schedule annotations** #2110 (Codex review folded), the
> **Q-0275 decision to DECLINE the fleet-wide "owner review" language scrub** #2111, and the **auto-mode
> permission-classifier EAP findings** #2121/#2126 (consolidated 2026-07-16 findings + archived the sent
> classifier-regression email); the **47th-pass reconcile PR** #2102; and **22 dashboard refreshes**
> #2103/#2106/#2107/#2108/#2109/#2112/#2113/#2114/#2115/#2116/#2117/#2118/#2119/#2120/#2122/#2123/#2124/#2125/#2127/#2128/#2129/#2130),
> trimmed Recently-shipped to 20, **disposed the open-PR set** — **1 open PR left in flight** (#2061,
> the deliberately-held owner-controlled mineverse FLAG 2 WRITE draft, deploy-safety Q-0193), no stale
> session PR; confirmed ROUTINE_PAT set / loop self-fires (issue #2131 authored by `menno420`), forward
> queue still deep (no THIN flag — the rebuild live in superbot-next + the live SuperBot Project 8-seat
> program dominate), refreshed the dashboard export, marker #2100 → #2130. Supersede-banner soft
> warnings grew 5 → **9** (+4 phantom cross-repo successor links in the fleet-centralization / fleet-review /
> trigger-health docs) — all honest cross-repo supersessions the in-repo checker can't resolve (successors
> live in fleet-manager), carried forward unchanged.
> Earlier: 2026-07-14 — **forty-seventh Q-0107 reconciliation pass (band-#2100, issue #2101
> — [pass record](planning/reconciliation-pass-2026-07-14-band2100.md));** reconciled band #2072–#2100
> (grouped entries — the band is **mostly docs/control/tooling** with **one `disbot/` runtime fix**: the
> **`!mine` breakage fix** #2089 (stringified `suid` → BIGINT-keyed `get_skills` `DataError`, plus a
> real-Postgres regression guard), the **fleet-manager relay ORDERs** #2087/#2090/#2094 (I1b
> frozen-trigger disposition · EAP final-night worklist · supersession-pointer ORDER), the **dashboard-conflict
> recipe + reconcile PR + session doc + repo-audit + EAP closeout** #2072/#2074/#2088/#2092/#2096,
> **11 dashboard refreshes**
> #2075/#2076/#2085/#2086/#2091/#2093/#2095/#2097/#2098/#2099/#2100, and **7 Dependabot bumps**
> #2077/#2078/#2080/#2081/#2082/#2083/#2084), trimmed Recently-shipped to 20, **disposed the open-PR
> set** — **1 open PR left in flight** (#2061, the deliberately-held owner-controlled mineverse FLAG 2
> WRITE draft, deploy-safety Q-0193); **#2058 (mineverse FLAG 1 READ-relay) merged to main mid-pass**
> — the owner flipped it ready, so it is recorded below as a merged entry (a late low-numbered merge;
> marker stays at the highest, #2100), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires (issue
> #2101 authored by `menno420`), forward queue still deep (no THIN flag — the rebuild live in
> superbot-next + the live SuperBot Project 8-seat program dominate), refreshed the dashboard export,
> marker #2071 → #2100. The 5 remaining supersede-banner soft warnings are honest cross-repo
> supersessions (successors live in fleet-manager `projects/superbot-next/`, registry PR #39 — the
> in-repo checker can't model them), carried forward unchanged.
> Earlier: 2026-07-13 — **forty-sixth Q-0107 reconciliation pass (band-#2070, issue #2073
> — [pass record](planning/reconciliation-pass-2026-07-13-band2070.md));** reconciled band #2041–#2071
> (grouped entries — the band is **entirely docs/tooling/control**, zero `disbot/` runtime: the
> **multi-repo orientation-review night → doctrine refresh** #2064/#2065/#2066/#2068 (the Q-0272
> orientation path's first full end-to-end exercise + boot-triad Q-0270 + fleet-reading-path + the living
> grounding file + session-ender v3.4), the **owner-queue execution → fleet re-arm + night-orders** arc
> #2043/#2045/#2046/#2048/#2049/#2051/#2053/#2055/#2057/#2059/#2060 (owner-live credentialed queue
> execution + 8-seat re-arm under the Q-0271 autonomy rider), the **hub-upkeep + Codex P2 follow-up**
> #2054/#2056, the **control-plane live review + EAP email-3 send-ready + owner batch** #2069/#2070/#2071,
> the 45th-pass reconcile PR #2042, and 7 dashboard refreshes #2044/#2047/#2050/#2052/#2062/#2063/#2067),
> trimmed Recently-shipped to 20, **disposed the open-PR set** — **3 open PRs left in flight** (#2072
> docs/tooling auto-merging; #2061 + #2058 deliberately-held owner-controlled mineverse drafts,
> deploy-safety Q-0193), no stale session PR; confirmed ROUTINE_PAT set / loop self-fires (issue #2073
> authored by `menno420`), forward queue still deep (no THIN flag — the rebuild live in superbot-next +
> the live SuperBot Project 8-seat program dominate), refreshed the dashboard export, marker #2040 →
> #2071. The 5 remaining supersede-banner soft warnings are honest cross-repo supersessions (successors
> live in fleet-manager `projects/superbot-next/`, registry PR #39 — the in-repo checker can't model
> them), carried forward unchanged.
> Earlier: 2026-07-12 — **forty-fifth Q-0107 reconciliation pass (band-#2040, issue #2041
> — [pass record](planning/reconciliation-pass-2026-07-12-band2040.md));** reconciled band #2012–#2040
> (four grouped entries — the band is **entirely docs/control/tooling**, zero `disbot/` runtime: the
> **2026-07-12 owner-live fleet-drive** #2032/#2033/#2034/#2035/#2037/#2038/#2039 (2nd Anthropic email
> SENT + gallery-link fix + the two owner work-orders + cross-repo fleet PR drive), the **Projects
> overnight batch review + EAP figure gallery** #2017…#2031 (the trigger-scheduler incident review +
> fig-20…fig-32), the **routine-arming doctrine correction + band-#2010 reconcile follow-up** #2013/#2014,
> and 6 dashboard refreshes #2015/#2016/#2022/#2028/#2036/#2040), trimmed Recently-shipped to 20,
> **disposed the open-PR set** — **zero open PRs at pass start**, no stale session PR; confirmed
> ROUTINE_PAT set / loop self-fires (issue #2041 authored by `menno420`), forward queue still deep (no
> THIN flag — the rebuild Phase-B canonical plan + the live SuperBot Project 8-seat program dominate),
> refreshed the dashboard export, marker #2011 → #2040. The 5 remaining supersede-banner soft warnings
> are honest cross-repo supersessions (successors live in fleet-manager `projects/superbot-next/`,
> registry PR #39 — the in-repo checker can't model them), carried forward unchanged.
> Earlier: 2026-07-11 — **forty-fourth Q-0107 reconciliation pass (band-#2010, issue #2012
> — [pass record](planning/reconciliation-pass-2026-07-11-band2010.md));** reconciled band #1981–#2011
> (four grouped entries — the band is **entirely docs/tooling/control**, zero `disbot/` runtime: the
> **EAP Anthropic-feedback email + fleet-review arc** #1982/#1985/#1986/#1990/#1992/#1993/#1994/#1996/#1997/#2007
> that dominated the band — the fleet night review, the ORDER-002 self-review, the two-part reviewer
> email draft, and the email-fleet-handoff session; the **8-seat consolidation → next-round
> founding-prompt arc** #1983/#1998/#2002/#2004/#2005/#2006/#2008/#2011 (external-strategy synthesis +
> Codex-PR disposal, the consolidation blueprint + founding-prompt kit, the 8-seat fleet structure);
> the **`check_consistency` Rule-6 guard** #2000 (friction→guard, graduated to error); and 4 dashboard
> refreshes #1984/#1991/#1999/#2009 — plus the already-carded #1995/#2003), trimmed Recently-shipped to
> 20, **disposed the open-PR set** — **zero open PRs at pass start**, no stale session PR; confirmed
> ROUTINE_PAT set / loop self-fires (issue #2012 authored by `menno420`), forward queue still deep (no
> THIN flag — the rebuild Phase-B canonical plan + the live SuperBot Project 8-seat program dominate),
> refreshed the dashboard export, marker #1980 → #2011. The 5 remaining supersede-banner soft warnings
> are honest cross-repo supersessions (successors live in fleet-manager `projects/superbot-next/`,
> registry PR #39 — the in-repo checker can't model them), carried forward unchanged.
> Earlier: 2026-07-11 — **forty-third Q-0107 reconciliation pass (band-#1980, issue #1981
> — [pass record](planning/reconciliation-pass-2026-07-11-band1980.md));** reconciled band #1951–#1980
> (four grouped entries — the band is **entirely docs/tooling**, zero `disbot/` runtime: the **round-3
> dispatch program run to CAPSTONE + the games program founded** arc #1953…#1978 that dominated the band
> — all six core seats BOOTED→LIVE, owner rulings Q-0264…Q-0267 folded to live doctrine, world/idle +
> Retro-Games + mining-web game Projects founded; the fleet-manifest ORDER-002 re-stamp #1954; the
> 42nd-pass docs PR #1952; and 6 dashboard refreshes #1956/#1960/#1970/#1976/#1979/#1980 — plus the
> already-carded #1974/#1977), **fixed 5 of 10 supersede-banner drift findings** (re-badged the five
> registry-superseded round-3 founding packages `plan`→`historical`; the remaining 5 "no successor" soft
> warnings are honest cross-repo supersessions the in-repo checker can't model), trimmed Recently-shipped
> to 20, **disposed the open-PR set** — **zero open PRs at pass start**, no stale session PR; confirmed
> ROUTINE_PAT set / loop self-fires (issue #1981 authored by `menno420`), forward queue still deep (no
> THIN flag — the rebuild Phase-B canonical plan + the live SuperBot Project round-3/games program
> dominate), refreshed the dashboard export, marker #1950 → #1980.
> Earlier: 2026-07-10 — **forty-second Q-0107 reconciliation pass (band-#1950, issue #1951
> — [pass record](planning/reconciliation-pass-2026-07-10-band1950.md));** reconciled band #1921–#1950
> (five grouped entries — the band is **entirely docs/tooling/dashboard**, zero `disbot/` runtime logic:
> the **gen-1 EAP fleet close-out → gen-2/round-3 program launch** arc #1926/#1931/#1932/#1934/#1935/#1936/#1944/#1945/#1946/#1947/#1949
> that dominated the band — the cross-fleet overnight review, the round-3 launch pack + dispatch runbook +
> manager founding package v3, the gen-1 coordinator close-out + Anthropic email Part 1, and **owner ruling
> Q-0259** (five round-3 rulings incl. the 3-repo games program + venture profit-mandate); the **cross-agent
> GPT-5.6 Sol / Codex evaluation thread + owner ruling Q-0258** #1938/#1939/#1940/#1941/#1942/#1943 (@codex
> the standing reviewer; Codex audits verified against source per Q-0120); the **codex design docs**
> #1930/#1937 (EventBus wiring inventory, guild quiet-hours); the 41st-pass docs PR #1922; and 4 dashboard
> refreshes #1925/#1927/#1933/#1950 — plus the already-carded #1923/#1924), trimmed Recently-shipped to 20,
> **disposed the open-PR set** — **1 open PR (#1948, the owner-attended live round-3 dispatch session)
> left in flight**, no stale session PR; confirmed ROUTINE_PAT set / loop self-fires (issue #1951 authored
> by `menno420`), forward queue still deep (no THIN flag — the rebuild Phase-B canonical plan + the live
> SuperBot Project round-3/gen-3 program dominate), refreshed the dashboard export, marker #1920 → #1950.
> Earlier: 2026-07-10 — **forty-first Q-0107 reconciliation pass (band-#1920, issue #1921
> — [pass record](planning/reconciliation-pass-2026-07-10-band1920.md));** reconciled band #1891–#1920
> (four grouped entries — the band is **entirely docs/tooling**, zero `disbot/` runtime logic: the
> **gen-1 EAP fleet wind-down → gen-2 doctrine arc** #1892…#1915 that dominated the band — 10-Project
> fleet manifest kept live as repos armed, evaluation-log findings (fleet-view permission gaps / GraphQL
> quota exhaustion / setup-script failures) for the owner's Anthropic feedback, the gen-1 grand review +
> retro protocol + external review pack, and the independent gen-1→gen-2 doctrine review #1914; the
> **GPT-5.6 Sol research brief + Codex eval suite** #1916; the **telemetry-append merge gate** #1894
> (Q-0194 friction→guard); and 5 dashboard refreshes #1899/#1906/#1907/#1908/#1912 — plus the
> already-carded #1913/#1917/#1918/#1919/#1920), trimmed Recently-shipped to 20, **disposed the open-PR
> set** — **zero open PRs at pass start**, no stale session PR; confirmed ROUTINE_PAT set / loop
> self-fires (issue #1921 authored by `menno420`), forward queue still deep (no THIN flag — the rebuild
> Phase-B canonical plan + the live SuperBot Project program/fleet dominate), refreshed the dashboard
> export, marker #1890 → #1920.
> Earlier: 2026-07-09 — **fortieth Q-0107 reconciliation pass (band-#1890, issue #1891
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
> **Last reconciliation pass:** PR #2190 (2026-07-21, fiftieth Q-0107 cadence pass, band-#2190 —
> record in [`.sessions/2026-07-21-reconcile.md`](../.sessions/2026-07-21-reconcile.md); marker reset
> to the latest merged PR **#2190**). The band (#2161–#2190, 20 PRs) was **17 dashboard-refresh PRs
> + the 49th-pass reconcile PR #2162 + 2 Dependabot bumps (#2174 fastapi / #2179 anthropic)** — no
> `disbot/` runtime, matching the oracle-freeze posture. Open-PR set at pass = **8 Dependabot dep-bump
> PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2184/#2185 — the runtime dep lane, Q-0256, left in flight;
> not this docs-only pass). **⚠️ PLAN BACKLOG THIN** carried: the
> in-repo product backlog is intentionally frozen (oracle-freeze), so there is no 30-PR feature band
> to plan — the forward queue is [`NEXT-TASKS.md`](NEXT-TASKS.md) (rebuild cutover + docs curation +
> owner-gated calls), not in-repo feature churn. The next **docs-only review + planning
> reconciliation** is due once merged PRs cross #2220 (every multiple of **30** — Q-0107 cadence
> raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per Q-0134; `check_reconciliation_due.py` flags
> it, and `.github/workflows/reconciliation-trigger.yml` auto-opens a `reconcile` issue at the
> boundary that fires the docs-reconciliation routine). Reset this marker to the latest PR after a pass.

- **#2162 · #2174 · #2179 (2026-07-19…07-21, S4/deps — the band-#2190 non-dashboard work, docs + dep bumps)** —
  the band's entire non-dashboard, non-runtime surface: #2162 the **49th-pass Q-0107 reconcile**
  (band-#2160 — ledger + Recently-shipped trim + marker #2130→#2160 + the PLAN-BACKLOG-THIN oracle-freeze
  carry); #2174 a **Dependabot `fastapi` bump** and #2179 a **Dependabot `anthropic` requirement update**
  (dep-manifest only, no `disbot/` logic). Matches the oracle-freeze posture — zero `disbot/` runtime.
- **#2163 · #2164 · #2165 · #2166 · #2167 · #2168 · #2169 · #2170 · #2180 · #2181 · #2182 · #2183 · #2186 · #2187 · #2188 · #2189 · #2190 (2026-07-19…07-21, docs — dashboard-data refreshes, Q-0167)** —
  seventeen `dashboard/data/dashboard.json` regenerations keeping the committed export fresh across the
  band under the Q-0167 refresh loop; generated artifact only, zero `disbot/` runtime.
- **#2132 · #2133 · #2136 · #2145 · #2146 · #2148 (2026-07-17…07-18, S4/S5/EAP — the band-#2160 docs/CI/tooling work, docs-only)** —
  the band's entire non-dashboard surface, **zero `disbot/` runtime**: #2132 the **48th-pass Q-0107
  reconcile** (band-#2130 — telemetry session row + the pass itself); #2133 the **Codex-review
  follow-up** on #2132 (export regen, self-initiated-flag form, idea refinement); #2136 the
  **fresh-start cleanup** — the 2026-07-17 oracle-freeze current-state banner + `NEXT-TASKS.md` (raised
  the top-level-docs ratchet 22→23 to pin the new queue file, dropped a residual arm-auto-merge clause);
  #2145 the **"dewall"** — removed the false *"agents cannot merge"* wall from `.claude/CLAUDE.md` while
  keeping the real walls (ref-deletion, tag-push, raw API, Settings); #2146 a **manual branch-cleanup
  workflow** (server-side ref deletion via `workflow_dispatch`); #2148 **EAP follow-up evidence** —
  telemetry rows for the 2026-07-18 EAP cards (the trigger-tooling forced-approval finding).
- **#2134 · #2135 · #2137 · #2138 · #2139 · #2140 · #2141 · #2142 · #2143 · #2144 · #2147 · #2149 · #2150 · #2151 · #2152 · #2153 · #2154 · #2155 · #2156 · #2157 · #2158 · #2159 · #2160 (2026-07-17…07-19, docs — dashboard-data refreshes, Q-0167)** —
  twenty-three `dashboard/data/dashboard.json` regenerations keeping the committed export fresh across the
  band under the Q-0167 refresh loop; generated artifact only, zero `disbot/` runtime.
- **#2102 · #2104 · #2105 · #2110 · #2111 · #2121 · #2126 (2026-07-14…07-16, S4/S5/EAP — fleet pre-archive sweep + EAP closeout arc, docs/control-only)** —
  the band-#2130 non-dashboard work, **entirely docs/tooling/control**: #2102 the **47th-pass Q-0107
  reconcile PR** (band-#2100); #2104 the **owner-live fleet-wide pre-archive sweep** session log; #2105
  the **EAP project audit + closeout walkthrough (ORDER 006)** — raised the top-level-docs ratchet
  21→22 to pin the walkthrough path; #2110 **ORDER 005 supersession stubs + ORDER 003 stale
  live-Schedule annotations** (Codex review folded — historical dispatch wording, `/fire` pause note,
  fleet-review rebadge); #2111 **Q-0275 — DECLINED the fleet-wide "owner review" language scrub** (the
  Auto-Mode-classifier false-flag fix routed to the classifier, not a doc scrub); #2121/#2126 the
  **auto-mode permission-classifier EAP findings** (consolidated 2026-07-16 findings + archived the
  sent classifier-regression email + open threads). Zero `disbot/` runtime.
- **#2103 · #2106 · #2107 · #2108 · #2109 · #2112 · #2113 · #2114 · #2115 · #2116 · #2117 · #2118 · #2119 · #2120 · #2122 · #2123 · #2124 · #2125 · #2127 · #2128 · #2129 · #2130 (2026-07-14…07-17, docs — dashboard-data refreshes, Q-0167)** —
  twenty-two `dashboard/data/dashboard.json` regenerations keeping the committed export fresh across the
  band under the Q-0167 refresh loop; generated artifact only, zero `disbot/` runtime.
- **#2058 (2026-07-14, S1/mineverse — mining snapshot READ-relay projection, owner-flipped from a held draft)** —
  a late low-numbered merge (opened 2026-07-13 as a deploy-safety draft, Q-0193; the owner flipped it
  ready during the band-#2100 reconcile pass). Adds `services/mining_snapshot_service.py` (`build_snapshot()`
  — one v1 envelope per configured guild, every miner's depth/energy/coins/XP/gear/inventory/vault/skills/
  structures) + `push_snapshot()` and `cogs/mining_relay_cog.py` (a command-free 60s `tasks.loop`).
  **Feature-off by default** — with `MINING_SNAPSHOT_RELAY_URL` / `MINING_SNAPSHOT_RELAY_GUILD_ID` unset
  (every current deploy) there is no loop and no network call; a relay outage can never affect bot
  operation. Contract of record: mineverse `schemas/mining_snapshot.v1.schema.json` (vendored under
  `tests/fixtures/mineverse/`). Record:
  [`.sessions/2026-07-13-mineverse-flag-1.md`](../.sessions/2026-07-13-mineverse-flag-1.md).
- **#2089 (2026-07-13, S1/mining — `!mine` runtime bug fix, a `disbot/` change)** —
  `build_grid_embed` passed a stringified `suid` to the BIGINT-keyed `db.get_skills`, so asyncpg raised
  `DataError` on **every** `!mine` open (the Mining Hub never reads `player_skills` on its overview path,
  which is why only `!mine` broke); introduced by `0c4b70b6` (BUG-0026). Fixed to the int `user_id` +
  a real-Postgres regression guard (the mocked-DB unit test couldn't see the type mismatch). Owner-directed
  from a Discord screen-recording; a repo-wide sweep found `grid_mine_view.py:48` the sole instance.
  Record: [`.sessions/2026-07-13-mining-command-breakage.md`](../.sessions/2026-07-13-mining-command-breakage.md).
- **#2087 · #2090 · #2094 (2026-07-13/14, S5/control — fleet-manager relay ORDERs, control-only)** —
  three append-only `control/inbox.md` ORDERs relaying fleet-manager coordinator dispatch to the hub seat:
  **ORDER 003** #2087 (I1b frozen-trigger disposition — two dormant owner-paused pre-fleet dispatch
  triggers, recommend delete/annotate-and-leave-paused; + a dispatch-console doc-drift rider), **ORDER 004**
  #2090 (EAP final-night worklist, fm ORDER 045 relay), **ORDER 005** #2094 (supersession pointers on three
  superseded superbot docs → their living fleet-manager counterparts). Each premise-checked against source
  per Q-0120. Control-only; no `disbot/` runtime.
- **#2072 · #2074 · #2088 · #2092 · #2096 (2026-07-13/14, workflow/EAP — dashboard-conflict recipe + reconcile PR + session doc + repo-audit + EAP closeout, docs-only)** —
  #2072 the **dashboard-conflict merge recipe** (a docs/tooling note for resolving `dashboard/data`
  conflicts); #2074 the **forty-sixth Q-0107 reconcile PR** (band-#2070); #2088 the **07-13 owner-live
  review + cross-repo merge sweep** session doc + enders; #2092 the **repo-audit PR cleanup** (dependabot
  backlog + fleet stale-PR sweep); #2096 the **EAP final-closeout**. Docs/control-only.
- **#2075 · #2076 · #2085 · #2086 · #2091 · #2093 · #2095 · #2097 · #2098 · #2099 · #2100 (2026-07-13/14, docs — dashboard-data refreshes, Q-0167)**
  and **#2077 · #2078 · #2080 · #2081 · #2082 · #2083 · #2084 (dependabot dep-bumps)** — eleven
  `dashboard/data/dashboard.json` regenerations keeping the committed export fresh, plus seven grouped
  Dependabot bumps (codeql-action, actions/checkout·cache·upload-artifact, uvicorn, openai, the
  python-minor-patch group) landed under the Q-0256 auto-merge policy.
- **#2064 · #2065 · #2066 · #2068 (2026-07-13, EAP/S4 — the multi-repo orientation-review night → doctrine refresh, docs-only)** —
  the band's headline. The **Q-0272 multi-repo orientation path's first full end-to-end exercise**
  (owner said the *review* word): `fleet_status.py` → reading path → fleet-manager baseline → five
  parallel read-only survey agents (each re-verifying the manager's tally at HEAD per Q-0120) →
  hub-side MCP verification, producing [`eap/night-review-2026-07-13.md`](eap/night-review-2026-07-13.md)
  (≈22 exact / 3 narrative-mismatch / 2 undercount scorecard; trigger degradation absorbed with
  **zero seat deaths**; 10-lane digest + consolidated owner queue). Plus the doctrine surfaces this
  arc landed: the **boot-triad** (Q-0270 — know model/venue/envelope every session), the
  **fleet-reading path** [`fleet-reading-path.md`](fleet-reading-path.md) (Q-0272), the **living
  grounding file** [`owner/fleet-grounding.md`](owner/fleet-grounding.md) (Q-0274), the **universal
  session-ender v3.4** [`owner/universal-session-ender-v3.4.md`](owner/universal-session-ender-v3.4.md)
  (#2065 — "wind down and land"), the **websites data-plane design** #2066, and the **07-14 next-session
  brief** [`owner/next-session-brief-2026-07-14.md`](owner/next-session-brief-2026-07-14.md).
  Entirely docs/orientation; **zero `disbot/` runtime**.
- **#2043 · #2045 · #2046 · #2048 · #2049 · #2051 · #2053 · #2055 · #2057 · #2059 · #2060 (2026-07-12/13, S5/fleet — owner-queue execution → fleet re-arm + night-orders, docs/control-only)** —
  the **owner-queue execution** #2043 (owner-live, credentialed: websites `ANTHROPIC_API_KEY` set on
  both review services, both work-orders delivered as fleet-manager ORDER 019/020, mineverse web host
  created + LIVE, Actions-toggle bridge) — full record
  [`.sessions/2026-07-12-owner-queue-execution.md`](../.sessions/2026-07-12-owner-queue-execution.md)
  + the evening mineverse-signin part-2; the **fleet re-arm** #2048 (all 8 seats re-dispatched with the
  Q-0271 autonomy rider) + **night orders v2** and the **direct-order paste-set**
  [`owner/fleet-direct-orders-2026-07-13.md`](owner/fleet-direct-orders-2026-07-13.md) + the **manager's
  final order** (prompt centralization → v3.5) + the **07-13 next-session brief**; plus the
  **settings-permission sweep** #2045 and the **07-12 session close-out** #2046. Docs/control-only; no
  `disbot/` runtime.
- **#2054 · #2056 (2026-07-13, hub-upkeep — stale rebuild pointers + Codex P2 follow-up, docs-only)** —
  #2054 refreshed stale rebuild pointers in the hub docs; #2056 fixed the two verified-genuine Codex P2
  line comments it drew (D-0043 qualified to its owning superbot-next artifact; the retired "▶ Rebuild
  review-then-plan" framing re-badged historical). Docs-only.
- **#2069 · #2070 · #2071 (2026-07-13, EAP/S5 — codex onboarding-telemetry + control-plane live review + EAP email-3 send-ready + owner batch, docs/control-only)** —
  #2069 the friend-onboarding webshop prompt + a telemetry append; #2070 the **control-plane live
  centralization review** [`planning/control-plane-centralization-review-2026-07-13.md`](planning/control-plane-centralization-review-2026-07-13.md)
  (headline: the same fleet renders as **6 different sizes** across pages = non-centralization made
  visible; six findings + prioritized fixes, homed in S5-ops); #2071 the **EAP email-3 draft made
  send-ready** [`eap/anthropic-email-3-draft-2026-07-13.md`](eap/anthropic-email-3-draft-2026-07-13.md)
  (Part 2 evidence filled from the morning night review: 51/51 parity, 18 hands-free idea→verdict
  cycles, ~215k words prose, 6 game builds, 41 website PRs, zero seat deaths) + the owner do-now /
  question batch. Entirely docs/control; **zero `disbot/` runtime**.
- **#2042 (2026-07-12, workflow — forty-fifth Q-0107 reconciliation pass, band-#2040)** —
  reconciled band #2012–#2040, trimmed Recently-shipped to 20, disposed the open-PR set (zero open),
  marker #2011 → #2040 ([pass record](planning/reconciliation-pass-2026-07-12-band2040.md)).
- **#2044 · #2047 · #2050 · #2052 · #2062 · #2063 · #2067 (2026-07-12/13, docs — dashboard-data refreshes, Q-0167)** —
  seven `dashboard/data/dashboard.json` regenerations keeping the committed export fresh as the
  owner-queue / fleet-rearm / orientation-review arc landed structural surfaces.
- **#2032 · #2033 · #2034 · #2035 · #2037 · #2038 · #2039 (2026-07-12, EAP/S5 — the owner-live fleet-drive: 2nd Anthropic email SENT + fleet PR drive + two owner work-orders, docs/control-only)** —
  the band's headline. The **second Anthropic EAP email finalized + SENT** (owner sent 2026-07-12
  13:24Z, reply on the July 8 thread) — staged as a clean draft #2032, gallery figures #2033, SENT
  state recorded #2034, and the **gallery image links fixed** #2038 (relative → full
  `blob/main/...?raw=true` URLs). Two **owner work-orders** written + merged for paste-in to the
  target Projects: the **websites review-site refresh + on-site AI assistant + homepage** order #2035
  and the **Project-Manager trigger-health check** order #2037. Session close-out (fleet-drive record
  + centralized owner-action queue) #2039. The live fleet-drive itself merged cross-repo (mineverse
  #42 CSRF → Games flagship gate cleared; fleet-manager #113/#117; websites 11/14 PRs) and found two
  systemic root-causes (fleet-manager roster-regen blocked on the Actions-create-PR toggle; websites
  serial-merge cascade from "require branches up-to-date" without a merge queue, owner-removed
  mid-session). Full record: [`.sessions/2026-07-12-fleet-drive-and-websites.md`](../.sessions/2026-07-12-fleet-drive-and-websites.md).
  Entirely docs/control; **zero `disbot/` runtime**.
- **#2017 · #2018 · #2019 · #2020 · #2021 · #2025 · #2026 · #2027 · #2029 · #2030 · #2031 (2026-07-12, EAP — the Projects overnight batch review + EAP figure gallery, docs-only)** —
  the overnight cross-fleet batch review ([`eap/night-review-2026-07-12.md`](eap/night-review-2026-07-12.md)):
  the **trigger-scheduler incident** (~02:30–08:00Z — 9 dropped `send_later` one-shots + 2 wedged
  crons; the Q-0265 failsafe doctrine validated in production; Venture Lab dark, kit-lab manually
  re-fired; cross-session trigger revival org-disabled) + the per-seat digest, lessons, fix-first
  list and owner-action queue — and the **EAP figure gallery** (fig-20…fig-32 screenshots +
  [`eap/email-attachment-set-2026-07-12.md`](eap/email-attachment-set-2026-07-12.md), the set linked
  from the sent email). Includes the Q-0174 post-merge Codex pass on #2017 (5 verified findings fixed).
  Entirely docs/control; **zero `disbot/` runtime**.
- **#2013 · #2014 (2026-07-11/12, S4 — routine-arming doctrine correction + band-#2010 reconcile follow-up)** —
  #2013 corrected the routine-arming doctrine (routines are **agent-armed, never owner-armed**) in the
  `.claude/` control docs; #2014 is the band-#2010 reconcile follow-up (ledger + archive + the
  `check-docs-cross-repo-path-awareness` idea). Docs/control-only.
- **Older merges (#2011 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are trimmed to the archive (newest-first), which `scripts/check_docs.py` soft-ratchets at 20 and `check_current_state_ledger.py` treats as present. *(Thematic grouping by date means the live/archive PR-number spans overlap slightly — the floor pointer is approximate prose, not a strict bound; the per-band pass records carry the exact moved sets.)* *(The fiftieth Q-0107 pass — band-#2190, 2026-07-21 — added the band #2161–#2190 work as two grouped entries (the 49th-pass reconcile #2162 + 2 dep bumps #2174/#2179 + 17 dashboard refreshes); trimmed the live ledger to 20, moving the #2015-band dashboard refreshes + the #1982-band Anthropic-feedback/fleet-review arc to the archive.)* *(The forty-ninth Q-0107 pass — band-#2160, 2026-07-19 — added the band #2132–#2160 work as two grouped entries (6 docs/CI/tooling #2132/#2133/#2136/#2145/#2146/#2148 + 23 dashboard refreshes); trimmed the live ledger to 20, moving the #1983-band fleet-consolidation arc + #2000 to the archive.)* *(The twenty-first Q-0107 pass — band-#1320, 2026-06-22 — added the band #1294–#1320 work as seven grouped entries (fishing minigame #1296/#1298/#1299/#1301/#1303/#1304, role management #1300/#1302/#1306, help surface #1294/#1297, BTD6 answerability #1295/#1316, botsite React PR1 #1305, CI/ledger/tool-pin hygiene #1308/#1317/#1320, dependency bumps + dashboard #1307/#1309/#1311/#1312/#1313/#1314/#1315); trimmed the live ledger to 20, moving #1208-band · #1226-band · #1211-band · #1210 · #1203-band · #1209-band · #1183-band to the archive.)* *(The twentieth Q-0107 pass — band-#1290, 2026-06-22 — added the band #1265–#1291 work as six grouped entries; trimmed the live ledger to 20, moving #1186 · #1156-band · #1147-band · #1143-band · #1162-band · #1149-band to the archive.)*

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
