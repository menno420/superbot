# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action — one live queue:** the **[decade queue (band #781–#800)](planning/reconciliation-pass-2026-06-13-q0107.md)** §4 — the third Q-0107 pass (2026-06-13). **The standing priority is the production-hardening P0 spine, integrity-first** (every gating decision is answered): **next = P0-3 arc PR 2** (retire XP-announce/economy-log scalars — turn-key against the [convergence plan §3](planning/settings-pointer-lane-convergence-plan-2026-06-13.md)) → P0-3 arc PR 3 (delegated-apply) → P0-4 channel-ownership → P0-2 media retention → P1-1 eval-matrix. The safety/community band (slots 4–6: #772/#774/#775) is **COMPLETE**; its remainder (security tiers 1+2 · image-mod · welcome phase 2) is plan-first behind the P0 spine. Product lanes (mining/BTD6/AI) stay open as owner-steered alternates. The full scorecard + deferred list live in the queue doc; [`roadmap.md`](roadmap.md) stays the per-area index. **Status is per-lane below — a session edits ONLY its own lane's bullet** (convention: [`owner/ai-project-workflow.md`](owner/ai-project-workflow.md) §9 "Cross-cutting ledger discipline").
>
> - **Consolidated batches:** **Batches 1–8 ALL executed + verified merged 2026-06-10** ([EOD verification](audits/past-day-verification-2026-06-10.md)) — #650 truth/clarity · #651 surface-classification invariant · #652 service boundaries · #654 Settings Phase 2 core · #656 adaptive P1C subpanels · **#657 Help projection seam** (HLP-2: `services/help_catalogue.py` + `services/help_projection.py`, all five render paths on one reason-coded `HelpProjection`; Q-0074 executed in the same PR) · **#659 HLP-3 guild overlay** (migration 064 `help_overlay`, audited `help_overlay_mutation` seam, cached read model, hide/rename through every render path; Q-0055 display-only pinned by an admission import fence) · **Batch 7 via the mining stack** (#661 + #663/#664/#665 → #667) · **Batch 8 = the #649 cutover**. **The queue-remainder session (PR #671, merged 2026-06-10) executed the RS07 chain-service slice** (audited `services/chain_service.py`, Batch 3 pattern, repo-wide write fence) **+ Batch 9's RS08 slice** (diagnostic read models out of the cog layer; new no-raw-SQL-in-cogs/views invariant) **+ the EOD audit's Tier-2 Help-Preview fix** (now consumes `project_help_with_execution`); **its continuation (PR #672) completed Batch 4** (proof-channel binding/resource declaration + binding-first read; logging rows verified satisfied) **and executed the Batch 10 selections** (wizard PR1–PR3 tranche verified shipped via #435 → setup-lane next = PR4 `/myprofile` planning session; next AI §7 family = **§7.5 multi-entity comparison**, sequenced after the maintainer's prod check — banners in the two plans carry the evidence). **The Help overlay editor UI executed 2026-06-10 ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → PR A #677 + PR B #679, both MERGED same day):** the hide/rename/re-describe editor (staff-hub `✏️ Help editor` button + the Settings-hub "Help appearance" domain group, 13th group) and the Q-0059 Home-message embed builder (migration 067, **mandatory preview**, shared `home_embed_frame` composer, byte-identical default pinned) — both live-verified on real Postgres. **Batch 9 then executed in PR #681** (open at write time): the RS05 publish-accepted delivery contract (runtime_contracts §2) + bus delivery stats / failure metric / the `event_bus` diagnostics provider, and the RS10 economy view family onto BaseView (conformance ratchet 17→13, arch warnings 84→80). **The consolidated plan's queue is FULLY EXECUTED (Batches 1–10; #681 MERGED).** A follow-on slice (PR #682, open at write time) migrated the **mining family** onto BaseView — the last true lifecycle-duplication family; ratchet 13→11 with a disposition note (remaining direct-View entries are ephemeral pipeline-gated follow-ups / bespoke admin checks, not RS10 duplication). **The PR4 `/myprofile` planning session ran (PR #684, open at write time):** [`planning/myprofile-foundation-plan-2026-06-10.md`](planning/myprofile-foundation-plan-2026-06-10.md) — §6 backend re-verified exact (4 audited pipeline entrypoints, typed accessors, schema registry, zero UI callers); PR A = read-only profile card (zero writes, turn-key) · PR B = the pipeline's first UI consumer · PR C onboarding **gated** on an owner decision; Q-0080 stranger-grade envelope applied throughout. Remaining plan-first/gated: Help audit Phase 4 records (Q-0057 rider) · AI §7.5 (post-eval).
> - **BTD6 data + answerability:** the `--all` cutover **#649 merged 2026-06-10; post-cutover VERIFIED + every carry-forward DECODED the same day** (#653 wave 1 ∥ PR #655 — dump fidelity byte-identical · 2,022 menu embeds in-limits · AI battery green · `_CUTOVER_CARRYFORWARD` empty, audit 91 CLEAN / 0 DELTA / 0 SUSPECT · banana economy answerable · fixes for mode-rules dark data / `!btd6 diagnostics` 400 / stamp-rot / path leak); **answerability items 5+6d shipped in PR #658**; **the Navarch "no coins" live miss diagnosed (missing ROUTING, not data) + fixed end-to-end with items 6a–c — #662 MERGED 2026-06-10** (paragon grounding gains income + effect lines · article-tolerant/shorthand paragon names · minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV) · Pouākai diacritic-fold · honest dataset source labels/summary); follow-up slice **#666** adds `scripts/btd6_probe.py` (grounding triage) + structures item 7 into [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md); **item 7 slice 1 (conversation carryover) + the zero-fact sweep fixes (ranking rosters · bare distinctive shorthand) shipped same day in #668**. **The 2026-06-11 morning screenshots (3 live AI-knowledge misses) fixed end-to-end in PR #703** — BUG-0002 (elite boss HP: dataset had no elite figures + boss names never routed BTD6 → standard table served as "Elite"; elite_tiers backfilled from the pinned v55.1 dump for all 7 bosses, boss canonicals route + name-index, variant-labeled grounding) · BUG-0003 ("despos on impop" hallucinated as PMFC; impop/despo keywords, Desperado alias, resolver plural fold, the `<quantity> <crosspath> <tower>` pricing leg — "10 041 despos" = ten 0-4-1s, owner-corrected) · BUG-0001 recurrence (round-cash refusals in #general: the workflow was profile-gated OFF on default channels — compatible_default/balanced_helper now declare analyze_execute_verify (Q-0048), matcher gained the money-question gate + by-round anchors). **Owner action: run `!btd6ops seed-data` after the deploy** (bosses/towers json are blob-lane data; owner-confirmed done 2026-06-11 ~12:38 — despos answers correct in prod). **The live re-test round shipped in PR #706 (merged 2026-06-11):** BUG-0004 (r-shorthand rounds + "end of r53" start shift — the $71,315.20 cumulative mislabel; truth $56,318.70) + the bulleted capabilities list (owner format ask; boss_health/crosspath/projection rows advertised). **Next:** decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check).
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
> **Last updated:** 2026-06-13, **third Q-0107 reconciliation pass (this session)** — the first
> cadence pass **auto-fired by the `reconcile` issue trigger** (#781), proving #778's self-fire fix.
> Band #761–#780 scored (**7/10 slots to plan** — safety band 4–6 COMPLETE + P0-3 foundation #777;
> the two unplanned items #778/#780 were both high-value), the **next ~9 PRs planned integrity-first**
> ([decade queue band #781–#800](planning/reconciliation-pass-2026-06-13-q0107.md)), the night-pass
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
> **Last reconciliation pass:** PR #780 (2026-06-13, third Q-0107 cadence pass —
> [the pass record + decade queue](planning/reconciliation-pass-2026-06-13-q0107.md)). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #800 (every
> multiple of **20** — Q-0107 cadence raised 10→20 on 2026-06-12; `check_reconciliation_due.py`
> flags it, and `.github/workflows/reconciliation-trigger.yml` auto-opens a `reconcile` issue
> at the boundary that fires the docs-reconciliation routine). Reset this marker to the latest
> PR after a pass.

- **#778 (2026-06-13, fix: routine-trigger issues now authored by `ROUTINE_PAT`)** —
  root-caused why the autonomous loop had **never self-fired**: `executor-nightly.yml` +
  `reconciliation-trigger.yml` created their trigger issue with `GITHUB_TOKEN`, so it was authored
  by `github-actions[bot]` — and a **bot-authored issue does not start a Claude routine**
  (A/B-verified: real-user issue #776 fired in <1 min; the cron's #768 sat ~12h, never fired). Both
  workflows now author with `secrets.ROUTINE_PAT` (fallback `GITHUB_TOKEN` + a loud `::warning::`
  when unset). **Inert until the owner adds the `ROUTINE_PAT` repo secret** — tracked with the other
  maintainer-side actions in [`operations/autonomous-routines.md`](operations/autonomous-routines.md)
  § Control-plane state. Docs + workflows only.
- **#777 (2026-06-13, hardening P0-3 settings pointer-lane convergence — FOUNDATION)** —
  the [pointer-lane convergence + Setup-delegate authority plan](planning/settings-pointer-lane-convergence-plan-2026-06-13.md)
  (arc PR 1, behavior-preserving). **Root-fix (settings readiness map "Required #2",
  High):** the binding-backfill's governance trusted/moderator role pointers targeted a
  `(governance, *)` binding with no schema home — `governance` is a *reserved* capability
  namespace, not a feature subsystem — so every guild got a permanent `BLOCKED_NO_SCHEMA`.
  Reframed: split honest `MIGRATED_KEYS` (xp, economy — homed) from new `DEFERRED_KEYS`
  (governance roles — home TBD); no runtime read/write change. **Durable layer (P1-3):**
  `test_backfill_target_declaration_parity` (every migrated target is a declared
  `BindingSpec`; deferred targets are not) + `test_pointer_lane_ledger` (the ratchet — every
  channel/role pointer is in a known bucket; a new pointer-as-scalar fails, catching the #775
  welcome/counters pattern). **Tooling:** `scripts/settings_lane_matrix.py` (the rec-#1 lane
  matrix; ground truth 65 settings / 17 bindings vs the dated map's 36/13). **Decision:**
  router **Q-0119** (OPEN) — the governance role-pointer binding home. **Sequenced (arc PRs
  2–3):** scalar retirement + the `setup_delegate` delegated-apply authority route (Q-0098,
  designed in plan §4). `check_quality --full` green (9303); arch 0 errors; `check_docs`
  clean.
- **#775 (2026-06-13, welcome v1 + server counters — band slot 6, Q-0110)** — the
  safety/community lane's final two slices ([family plan](planning/safety-community-family-plan-2026-06-13.md)
  §4), shipped as **two hub-less new subsystems** (checked the extend-before-mint rubric:
  nothing existed to extend; both kept off the user-tier Community hub so operator config
  doesn't clutter it). **welcome** — `services/welcome_service.py` + `welcome_config.py` +
  `cogs/welcome_cog.py`: greet on join · optional farewell · optional **entry role** granted
  on join via the audited `role_automation.apply` (no parallel role/audit path);
  injection-safe `{user}/{server}/{count}` templates; embed-first (PIL card = phase 2);
  advisory `welcome.member_greeted`. **counters** — `services/counter_service.py` +
  `counter_config.py` + `cogs/counters_cog.py`: statdock channel renames (total/humans/bots)
  on a 10-min `tasks.loop`, **never per join** (Discord's ~2/10-min rename cap) +
  change-detection; advisory `counters.updated`. Both default OFF (master switch) → a fresh
  guild is unaffected; **no migration** (scalar `welcome_*`/`counters_*` KV settings,
  channel/role pickers via `input_hint`). Root-fix: channel/role lookups route through
  `core.runtime.resources.resolve_*` (the guild-resource invariant), not raw `guild.get_*`.
  65 new tests; `check_quality --full` green (9292); `check_architecture` 0 errors; live
  boot on Galaxy Bot (real Postgres): both cogs loaded, 0 ERROR/CRITICAL. **The
  safety/community band (slots 4–6) is COMPLETE; next = the carried hardening spine (P0-3).**
- **#774 (2026-06-13, server event logging v1 — band slot 5)** — the safety/community
  family plan's slot 5 (Q-0109): a passive Discord-event layer **extending the existing
  `logging` subsystem** (no new subsystem → no pinned-surface cascade). Logs **message
  edits/deletions · member joins/leaves · role grants/revocations**. New
  `services/server_logging_config.py` (`EventLoggingPolicy`/`load_policy` over `logging_*`
  KV settings, **no migration**); five `format_*_embed` builders + five fail-safe `log_*`
  handlers + `resolve_event_channel` in `services/server_logging.py`; four event routes on
  the shared route table (`events` + per-category, falling back to `events` never `mod`);
  five `@commands.Cog.listener()` methods on `LoggingCog` (cheap filters → delegate). Each
  category needs the master `logging.enabled` **and** its per-category flag — all default
  OFF. Owner-configurable routing (`logging.event_routing` = `combined`/`per_category`,
  the `mock_logging_routing` choice made real). Schema **v3** (3 flags + routing enum + 4
  channel bindings + 4 resource reqs). Deleted-message **privacy disclosed** in the
  `messages_enabled` hint + the setup wizard. Root-fix: the routes panel's hardcoded
  "(via mod fallback)" label now names the real fallback target. New
  `test_server_logging_events.py`; CI green; live-boot verified. **Next band slot:
  welcome v1 + counters (slot 6).**
- **#772 (2026-06-13, safety/community family plan + automod v1 — band slot 4)** —
  the safety/community lane's **entry doc**
  ([family plan](planning/safety-community-family-plan-2026-06-13.md): shared
  architecture + sliced build order for all five approved features, citing
  `ux/pattern-library.md` pattern_ids) **+ the first slice, automod v1** (Q-0108):
  a new `automod` subsystem (twin of `cleanup`) filtering spam bursts · `discord.gg/`
  invite links · excessive caps · mass mentions. Pure detectors + `SpamTracker` in
  `services/automod_service.py`; `AutomodPolicy` read-model in `services/automod_config.py`
  (KV settings, **no migration**, all flags default OFF); an order-5 `AutomodStage`
  in the message pipeline (never a parallel `on_message`); on a hit, delete + `warn`
  through `moderation_service` (escalation/audit stay one authority — no second
  ladder). New advisory event `automod.rule_triggered`; config via the `!settings`
  widget. 31 tests; CI green; live-boot verified. **Next band slot: server event
  logging v1 (slot 5).**
- **#765 + #767 + #769 + #770 (2026-06-12/13, backup posture + autonomous-loop
  follow-ups)** — **#769** Postgres backup posture (band slot 3 — daily `pg_dump` to a
  GitHub Actions artifact; [production-deployment §Backups](operations/production-deployment.md))
  · **#767** `executor-nightly.yml` cron moved off `:00` to dodge scheduler congestion ·
  **#770** permissions: the autonomous executor may push to `main` without prompting ·
  **#765** the autonomous-loop session close (loop live + Hermes dual-platform control
  plane — [session log](../.sessions/2026-06-13-autonomous-loop-hermes-control-plane.md)).
  *(Reconciled here by the automod session; #771 is a parallel ledger-update PR for the
  same band — UNION-merge if both land.)*
- **#764 (2026-06-12 night, the P2 doc-drift sweep — band slot 2)** — all five
  hardening-P2 fixes, source-verified then applied: smoke checklist's nonexistent
  `!platform diagnostics` → `runtime`/`consistency` + the platform-panel
  completeness claim honest · the AI runtime README rewritten ("inert scaffold" →
  the live gateway/routing/NL-stage platform) · **ADR-006 dated status addendum**
  (pause condition satisfied; decision untouched per ADR immutability) +
  decode-status header v55.0→**v55.1** + duplicate backlog № fixed · media folio
  states the **raw-payload reality** (bounded projection = the Q-0099/P0-2 target)
  · `YOUTUBE_CONTEXT_ENABLED` owner `ai`→`platform` (ADR-007). P2 table marked
  SWEPT. **Next band slot: backup posture.**
- **#763 (2026-06-12 night, the second Q-0107 reconciliation pass)** — band #741–#762
  scored ([record + next-band queue](planning/reconciliation-pass-2026-06-12-night.md):
  slots 1+3 executed; the hardening+safety queue carried intact — capacity went to the
  two owner-steered arcs) · the #753–#761 ledger gap reconciled (the arc entry below) ·
  **both audit checkers' shared merge-subject regex root-fixed** ("Merge PR #N:" was
  invisible — the cadence checker froze at #751 and the ledger checker was **green
  while five PRs were missing**; tests pin all three subject styles now) · marker
  reset, next pass at **#780**. Docs + tooling only.
- **#753 + #754 + #756 + #759 + #761 (2026-06-12, the autonomous-loop wiring arc —
  parallel lane)** — the loop went **live**: **#753** issue-triggered docs
  reconciliation (`.github/workflows/reconciliation-trigger.yml` opens a `reconcile`
  issue at each boundary) + the **Q-0107 cadence raised 10→20** (CLAUDE.md edited
  in-session, owner-directed) · **#754** routine prompts reframed as turns of the
  self-improvement loop · **#756** the **Q-0117 Hermes independent-review merge
  gate** (substantial executor steps label `needs-hermes-review`; Hermes — a
  different model — reviews and merges on green, the one write added to its
  read-only envelope; small fixes keep Q-0113 self-merge) · **#759**
  `executor-nightly.yml` cron (03:00/05:00 continue-issue) · **#761** dispatch
  prompt handles free-form Discord `/bugreport` reports. Posture: **Q-0105
  calibration** — wired, young, trust grows per verified run. *(Entries added
  retroactively by the night reconciliation pass — these sessions run their own
  prompts, and the ledger checker that should have flagged the gap was blind to
  the "Merge PR #N:" subject style; root-caused + fixed in the same pass.)*
- **#758 + #760 + #762 (2026-06-12, the UX Lab BUILD — owner-steered same-day
  execution of the #755 design, Q-0116)** — `!uxlab` is **live**: an admin-gated,
  **zero-write** (AST-fenced) interface gallery — **64 registered patterns** across 7
  wings (buttons incl. the danger-confirm doctrine + a REAL PersistentView
  restart-survival exhibit · selects incl. the >25 pagination fix · modals incl.
  Label-wrapped selects · 14 embed archetypes · **Components V2** LayoutView renders ·
  PIL cards reusing the #665/#702 renderers + the Q-0110 welcome-card prototype) · a
  **10-probe limit bench** (dated, library-versioned) · a **mock studio for the whole
  Q-0108–Q-0112 lane** (automod pills, the Q-0109 routing toggle, welcome embed-vs-card
  A/B, RSVP, feed summary, counters, security tiers 1+2 — declined tiers test-pinned
  absent) · ⚖️ compare-with-verdict lines. **The durable artifact:
  [`ux/pattern-library.md`](ux/pattern-library.md)** — registry-generated + doc-pinned;
  future panel plans cite `pattern_id`s. 49 lab tests; CI green ×3; live-boot ×3.
  CV2 adoption for real panels stays a future ADR (plan non-decision).
- **#755 (2026-06-12, UX Lab design — owner-commissioned)** — the **interface-gallery
  cog design**: [capture](ideas/ux-lab-interface-gallery-2026-06-12.md) +
  [full plan](planning/ux-lab-interface-gallery-plan-2026-06-12.md) for a zero-write,
  admin-gated `!uxlab` gallery — 9 exhibit wings (~60 patterns: buttons / all 5 selects /
  modals incl. Label-wrapped selects / embed archetypes / **Components V2** / PIL cards /
  **mockups of the approved Q-0108–Q-0112 features**), a 10-probe platform-limit bench,
  compare-with-verdict mode, a `PatternSpec` registry exporting to a pattern-library
  doc in plan-PR C, AST zero-write fence, 3-PR slicing. **Found + fixed two
  stale platform facts** (verified on installed discord.py 2.7.1): the limits doc's CV2
  budget (25 → **40 children / 4 000-char text**) and the journal's "modals can't contain
  selects" rule (Label, 2.6+). Scheduling + audience = router **Q-0116** (open). Docs-only.
- **#746–#754 (2026-06-12, dispatch-bridge wiring + routine-fleet arc)** —
  the Hermes→Claude Code dispatch bridge went **live-verified end-to-end**: **#746**
  Context7 verify/tool-name fix · **#747** routine-creation step marked DONE (calibration
  pass) · **#749** `superbot-dispatch` wired to the verified Routines `/fire` API ·
  **#750** routed the wager-flow-map session idea into the backlog · **#751**
  Telegram-driven dispatch path live-verified · **#752**
  [`operations/autonomous-routines.md`](operations/autonomous-routines.md) — the Routine
  fleet's prompts in git (autonomous dispatch · nightly docs-reconciliation · night
  caretaker) · **#753** docs-reconciliation routine made issue-triggered + cadence raised
  10→20 (Q-0107) · **#754** routine prompts rewritten as self-improvement-loop turns with
  memory read/write and the Q-0089/Q-0102 hooks.
- **#748 (2026-06-12, hardening P0-1 — wager money safety)** — new
  `services/game_wager_workflow.py`: the audited money boundary for every two-party /
  paid-entry game move, composing `economy_service.*_in_txn` inside one
  `db.transaction()` (the mining_workflow precedent). **D1 escrow-at-accept** —
  `open_pvp_wager` debits both stakes + writes per-player `*_escrow` rows when a PvP
  challenge is accepted, deleting the old credit-then-overdraft-debit **mint window**;
  `settle_pvp`/`refund_pvp`/`payout_tournament` are idempotent by `FOR UPDATE`
  row-consumption (no double-pay); `enter_tournament` debits the fee + writes the
  recovery row in one txn (closes the lost-fee window). All four call sites migrated
  (RPS + blackjack PvP and tournament); dead un-escrowed `deduct_fees` removed; AST fence
  (`test_game_wager_write_boundary`) bans `economy_service.credit/.debit` in the wager
  files + `allow_overdraft=True` outside solo views. Failure-injection / terminal-matrix /
  idempotency tests (real-Postgres integration + mock CI). No schema migration (escrow
  rides existing `game_state`). Executes
  [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md);
  **closes hardening P0-1** → next P0 track = P0-2.
- **#745 (2026-06-12, the direction-lock round)** — owner question-panel round: **next
  implementation session = P0-1 wager money-safety** (design pinned:
  [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md)) ·
  **Q-0097 = operator-managed findings lifecycle** (every hardening gate now answered) ·
  **Q-0082 interim global AI ceiling = €30/month** · **Q-0115**: Stage 0 folded into the
  #742 Routine bridge (one continuation-dispatch seam; bounded protocol activates on
  wired + calibrated). (#743/#744 same day: the loop session's close + a journal
  draft-first wording fix.)
- **#742 (2026-06-12, the autonomous-loop seams — parallel Hermes session)** — Hermes
  `superbot-review` skill (independent non-Claude plan/PR critique with a maintainer
  summary) · `scripts/check_phase_gate.py` (machine-readable **fix-phase vs. invent-phase**;
  invent requires zero OPEN bugs + zero Not-Done readiness rows — reports FIX-PHASE today) ·
  the `superbot-dispatch` skill + runbook (Hermes → Claude Code Routine `/fire`). Owner
  decisions **Q-0113** (routine PRs self-merge on green CI) + **Q-0114** (human approve/deny
  for agent-originated features; invent-phase-only origination) — workflow §12. Maintainer
  follow-ups: wire the Routine + token, calibrate per Q-0105 before trusting unattended.
- **#741 (2026-06-12, the first Q-0107 reconciliation pass)** — every plan added in
  #715–#740 mapped ([pass record + decade queue](planning/reconciliation-pass-2026-06-12.md)):
  new roadmap lanes **safety/community** (Q-0108–Q-0112) + **agent ecosystem/workflow**;
  the next ~9 PRs planned (hardening P0s · backup posture · the safety lane's first
  slices); ledger drift reconciled; the cadence checker taught to fetch `origin/main`.
- **#738–#740 (2026-06-12, the cadence rule + owner research/decisions arc)** — **#738**: the
  **Q-0107 reconciliation cadence** (a docs-only review + planning pass each time merged PRs
  cross a multiple of 10; `scripts/check_reconciliation_due.py` guards the marker). **#739**:
  owner research captured — [safety/automod ideas](ideas/server-safety-and-automod-2026-06-12.md) ·
  [community-features ideas](ideas/community-platform-features-2026-06-12.md) · the
  [Discord platform-limits reference](operations/discord-platform-limits.md). **#740**: owner
  decisions **Q-0108–Q-0112** recorded (automod all-4 rule types + OpenAI-only image
  moderation · logging v1 scope with owner-configurable channels · welcome embed-first, PIL
  cards phase 2 · security tiers 1+2 only, 3+4 declined · NL event parsing from day one) →
  routed to the roadmap's new **safety/community lane**.
- **#732 (2026-06-12, command-surface dump tool)** — `scripts/command_surface_dump.py`:
  offline AST dump of every prefix/slash command by subsystem (+ `--json` and
  `--diff-checklist` against the untested-surface checklist); 8 tests. The #731 session's
  grooming companion; roadmap queue item 1 closed with it.
- **#737 (2026-06-12, Context7 MCP adopted)** — wired `@upstash/context7-mcp@3.2.0` (live
  library docs → kills the "API-from-memory" bug class) as a pinned `.mcp.json` server +
  [`docs/operations/mcp-servers.md`](operations/mcp-servers.md) (when-to-use, key setup, Q-0105
  provenance). Q-0096 answered (Context7 yes; Postgres-MCP/pyright-lsp still open).
- **#736 (2026-06-12, CodeGraph health check + doc pin fix)** — verified CodeGraph 3.11.2 is
  healthy (no regression from the bump; the "problems" are the cold-start availability blip + the
  documented false positives). Fixed the real bug: `docs/codegraph-usage.md` told agents to run the
  old `@optave/codegraph@3.10.0` while the live pin is 3.11.2 — bumped all command refs.
- **Older merges (#735 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~15 newest; older entries are archived (`scripts/check_docs.py` soft-ratchets the count). *(The #733–#735 agent-workflow/memory hardening arc was archived 2026-06-13 to offset the #778 entry — keeping the live ledger at the ratchet.)*

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
  undecided) · **Q-0119** (governance role-pointer home, P0-3 family 3) · **Q-0120/Q-0121** (this
  workflow pass's proposals — candidate-rule promotion · Hermes bug-triage `gh issue create` write).
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
