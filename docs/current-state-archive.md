# SuperBot — Current State (Recently-shipped archive)

> **Status:** `historical` — overflow from `current-state.md` § Recently shipped.
> Merged-PR notes, newest-first, trimmed out of the live ledger to keep it lean.
> **Source code and merged PRs win over anything here.** Start at [`current-state.md`](current-state.md).

## Stamp-line history (moved from current-state.md, 2026-06-12)

> The `Last updated:` stamp keeps only recent sessions; older stamp narrative lands here
> verbatim. Session detail lives in `.sessions/`.

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

> 2026-06-10, **production-outage session (PR #685): Railway Python pin** — the Railway `worker` build broke (3 consecutive failures ~21:00 UTC): no repo-side Python pin existed, so railpack's floating default resolved to brand-new CPython **3.13.14**, which has **no python-build-standalone binary yet** → `mise install` fails. Fixed by pinning **`.python-version` = 3.13.13** (pbs asset verified HTTP 200; CI/local tooling unaffected — they pin 3.10 explicitly). Postgres was Online throughout; **no user-facing downtime (owner-corrected 2026-06-11: Railway keeps the active instance serving while builds fail — the impact was a silent ship-blocker, not an outage)**. **New [`operations/production-deployment.md`](operations/production-deployment.md)** — first durable record of how prod runs (Railway `reliable-grace`/production, worker + native Postgres, **auto-deploy on every merge to `main`**, builder/pin/bump procedure, incident log, **backups = OPEN**). **Q-0085 routed (open, router §36):** CI 3.10 vs prod 3.13 interpreter drift — alignment direction is an owner pick. Hosting answer recorded from the owner (Railway + native PG) as part of the open backups discussion. **Post-incident owner round (same conversation):** AI provider keys → agent session env for **joint live-testing** (**Q-0086**, router §36 — partially lifts the model-loop "no sandbox key" gate once set up) · an **untested-surface testing checklist commissioned** (enumerate every command/prompt neither covered by automated tests nor explicitly live-tested — routed to the roadmap session queue) · ChatGPT session-template rework = owner action item (Q-0084 addendum) · owner notes occasional **command-behavior inconsistencies** he deliberately hasn't reported yet (standing invite: drop them any session, agents classify). **Brainstorm round 2 (same conversation): Q-0087** — RPG balance philosophy answered (casual minutes/day = real progress · grinder rewards real but **never mandatory-feeling** for capability) + **simulation approved as the balance methodology** → the survival plan gains **D0** (binding philosophy) + **P0 balance-simulation harness** (CI-pinned bands), G2 now confirms numbers from sim outputs · **Q-0088 — Q-0083's timing corrected by the owner: build the self-driving foundation NOW, small** (his role → ideas + strict function/UX guidelines; on record: runaway unguided session tails + ~700–800K context degradation) → **bounded-session protocol + staged continuation designed** ([workflow §10](owner/ai-project-workflow.md)) — protocol activates when the **Stage 0 one-click continuation workflow** lands (queued, roadmap session queue; owner provides the API-key secret) · monetization note: still cosmetic-only/not-soon (Q-0039/Q-0082 unchanged); owner expects a **platform migration off Railway if/when it monetizes** (noted in T-6's context). **Rounds 3–5 (same conversation):** bot **self-test walker** idea captured ([ideas file](ideas/bot-self-test-walker-2026-06-10.md), pairs with the checklist session) · **Q-0089 installed — mandatory one-new-idea session ender** (CLAUDE.md + journal END; first execution = the morning-digest idea) · owner self-description preserved verbatim (working-profile **§6**) · **V-13 multi-ecosystem open world + V-14 competitive teardown** captured, then **Q-0090 answered**: ecosystem #2 = research-decided (**V-14 = gateway session**, game/economy bots first) · **local no-exchange currencies** · **medium cross-links** (special optional tools only — Q-0087-bounded). **Round 6 (post-midnight): the V-14 gateway research EXECUTED in-conversation** — 3 parallel background agents → [`ideas/competitive-teardown-2026-06-10.md`](ideas/competitive-teardown-2026-06-10.md) (~95 features, 30 scored harvest candidates, retention engines, V-15 MEE6 surface **live-verified** incl. exact XP curve; Lurkr/UB official APIs; parsing-fallback verdict); **ecosystem-#2 verdict = FISHING — owner ratification pending**; survival plan P3 carries an ecosystem-ready seam note; V-15 idea captured (round-5 tail). · Earlier same day: **editor-collision reconcile (PR #682)** — two sessions built the editor plan's PR A in parallel; #677 won the race (and #679 shipped PR B), the duplicate **#678 was closed superseded**, and #682 salvages the two missing deltas (settings-page **Domain configuration** block · the modal-no-defer pin) + records the **Q-0060 recurrence data point** (router §26 note; journal rule: check open PRs before starting a slice). This entry also reconciles the mega-line union (the Help-editor session entry was dropped in a prior resolution — restored). · Earlier same day: **vision-ideation capture session (PR #680)** — the maintainer wrote down his product vision ("the best bot ever made") and asked for review + the agent's own creative thinking; captured + dedup-mapped in [`ideas/superbot-vision-2026-06-10.md`](ideas/superbot-vision-2026-06-10.md): new owner items **V-01…V-12** (2-min setup KPI · panel navigation doctrine · 4-button help home · per-user preferences · RPG difficulty/survival/energy · fishing/cooking · story pets · AI-as-panel-orchestrator), agent additions **AG-01…AG-15**, tensions **T-1…T-5** flagged, full routing ledger; indexed (ideas README · roadmap Someday · mining brainstorm §7.8). **Same session, one structured-choices round → Q-0078 (router §34):** one-way-ascent difficulty · both pet paths (pets plan amended) · the 4-button Help Home layout · next planning targets = RPG survival design (**structured same session →** [`planning/rpg-survival-difficulty-design-2026-06-10.md`](planning/rpg-survival-difficulty-design-2026-06-10.md)) + help home/navigation (next grooming target, sequenced with the Help editor UI). **Follow-up Q-0079:** per-panel button caps rejected — cleaner UX = fewer or **better-defined** buttons, removal only for genuine redundancy; the vision's ≤3 is navigation **depth** only. **Same session, agent-initiated deep round → Q-0080–Q-0083 (router §35):** **public bot is the goal** (Q-0080, a design filter every new plan inherits) · flagship RPG = **solo core + co-op overlays** (Q-0081, quest engine single-party-first) · AI spend = **hard ceiling, graceful visible degrade** (Q-0082; € figure owed after first prod measurements) · workflow end-state = **full self-driving, explicitly not near-term** (Q-0083); new tension **T-6** (public scale × cosmetic-only donations × fixed AI ceiling) flagged in the capture doc §5. **Then Q-0084 — the first Q-0083 trust tier GRANTED: agents merge their own session PRs when done** (main-synced · CI-green · merge-commit · merge ≠ deploy) — routed into CLAUDE.md §Session workflow, collaboration-model, workflow §9; first exercised on PR #680 itself. Docs-only; nothing implementation-approved. Session log: `.sessions/2026-06-10-vision-ideation-capture.md`. · Same day: **Batch 9 session (PR #681, merged)** — RS05: the publish-accepted event-delivery contract decided + documented (runtime_contracts §2), per-event delivery stats, `event_handler_failures_total`, and the `event_bus` diagnostics provider (first consumer of `registered_events`); RS10: the economy view family (4 views) migrated onto BaseView — one denial copy, logged timeout failures, on_error coverage; ratchet 17→13. **Consolidated plan fully executed.** CI mirror 8,906 green; arch 0 errors / 80 warnings; clean boot. Session log: `.sessions/2026-06-10-batch9-rs05-rs10.md`. · Same day: **Help-editor session (PR A #677 + PR B #679)** — executed the #674 plan end-to-end: PR A = the hide/rename/re-describe editor (`views/help/editor.py`; staff-hub button + "Help appearance" Settings domain group; every action one audited `help_overlay_mutation` call; admin re-checked per callback; Q-0058 custom+default+key rendering; Q-0055 copy) · PR B = migration 067 + `set_home_message` + the Home embed builder with mandatory preview (one shared frame composer for render + preview; mention suppression; byte-identical default pinned). CI mirror 8,912+ green, arch 0 errors, migration 067 applied live, both flows live-round-tripped. Eval checklist §4.5 updated with the editor walk. Session log: `.sessions/2026-06-10-help-overlay-editor-ui.md`. · Earlier same day: **eval-support session (#673 checklist · #674 editor plan · #675 live-walk fixes · #676 data lane — all merged)** — the eval checklist (#673, [`audits/production-eval-checklist-2026-06-10.md`](audits/production-eval-checklist-2026-06-10.md)) + the Help overlay editor UI plan (#674, [`planning/help-overlay-editor-ui-plan-2026-06-10.md`](planning/help-overlay-editor-ui-plan-2026-06-10.md)); then the maintainer's walk began and **#675** fixed its four live findings (deterministic meta-floor for "what do you know about btd6" · qualifier-tolerant `find_boss` + per-tier boss HP grounding · crosspath validity rules · the `!restart` exit-0-never-relaunches bug) — first walk ran a **pre-#655 deploy** (the "(55.0)" stamps; checklist now opens with Step 0: verify build). Tier 1.1 round-cash **PASSED** live. §7.5 gained its acceptance cases (the "five 0-2-4 dart monkeys by round 60" screenshots). Session log: `.sessions/2026-06-10-eval-checklist-session.md`. · Earlier same day: **queue-remainder continuation (PR #672, same session)** — maintainer confirmed most commands working live + announced a dedicated eval session; **Batch 4 COMPLETE** (proof-channel binding/resource declaration, binding-first read with name fallback, identity contract clean at boot, live binding round-trip) + **Batch 10 EXECUTED** (DT09: wizard PR1–PR3 tranche verified shipped via #435, plan re-badged, PR4 selected; DT10: §7.5 multi-entity comparison selected, after-prod-check sequencing); #671 + #670 reconciled into Recently-shipped. Session log: `.sessions/2026-06-10-queue-remainder-rs07-rs08-help-preview.md` (continuation section). · Earlier same session: **queue-remainder (PR #671, merged)** — RS07 chain service (audited writes + fence, live-verified round-trip) · Batch 9 RS08 read-model extraction (+ the class-killing no-raw-SQL-in-cogs invariant; the unfinished `rank_providers` migration in `cogs/xp/_helpers.py` finished) · the EOD audit's Tier-2 Help-Preview drift fixed (first `project_help_with_execution` + `orphaned_overrides` consumer); CI mirror **8,840 passed / 22 skipped**, arch 0 errors, clean boot + live DB round-trip. Stale direct-db exception-ledger rows (chain/mining/role-thresholds) corrected to their shipped seams. Session log: `.sessions/2026-06-10-queue-remainder-rs07-rs08-help-preview.md`. · Earlier same day: EOD, **past-day verification + docs-cleanup session (PR #669)** — all 21 of the day's merged PRs (**#648–#668**) verified against `main` source: zero open PRs, migrations 052–066 contiguous, CI mirror **8,817 passed / 22 skipped**, arch 0 errors; the #667 stranded-stack landing **content-verified** (the #663/#664/#665 mining content is fully on `main`); stale "verify merged" hedges resolved across this file / `roadmap.md` / the consolidated plan, Recently-shipped rebuilt newest-first for the whole day, and the consolidated plan's §5/§8 queue state corrected (Batches 1–8 done; remainder = RS07 · Batch 4 tail · Batch 9 · Batch 10 · Help editor UI). **Verdict + findings + next-session recommendation: [`audits/past-day-verification-2026-06-10.md`](audits/past-day-verification-2026-06-10.md).** Session log: `.sessions/2026-06-10-past-day-verification-docs-cleanup.md`. · Earlier same day: **mining/tool/gear finalization session (4-PR stack #661→#663→#664→#665** — Batch 7 RS01+RS02 complete, shared game-XP track + deeper ladders + UX finalization + duels wear + PIL cards; session decisions Q-0075/Q-0076 in router §32; session log: `.sessions/2026-06-10-mining-finalization.md`**)**. · Earlier same day: **BTD6 Navarch-routing + items 6a–c session (PR #662)** — the screenshot's wrong answer diagnosed as **missing routing, never missing data** (three layers: name-resolution miss on a dropped article → 0 facts; the income sentence living exactly in the description's cap-truncated tail; no paragon income/effect grounding leg), fixed across AI grounding + menu embeds + the AI tool, with decode-status items 6a–c executed in the same PR (minion-name grounding incl. the Pouākai tokenizer diacritic fix · dataset source labels · fixture-only source summary). Session log: `.sessions/2026-06-10-btd6-navarch-routing-items-6abc.md`. · Earlier same day: **Batch 6 session, part 2 — HLP-3 guild overlay (PR #659, draft until session end)**: #657 merged mid-session (clearing HLP-3's gate), so the same session shipped the overlay store + audited mutation seam + projection/render integration (migration 064; `help_overlay_mutation`; presentations w/ defaults per Q-0058; Q-0055 import fence; `help_cog` decomposed 840→443 via `cogs/help/panels.py`); CI mirror 8,680 green; live round-trip on real Postgres (hide+rename render, audited writes, full reset byte-identical). Same session, part 1 **(merged as #657)** — the HLP-2 seam: `services/help_catalogue.py` (stable-keyed inventory, drift findings pinned empty) + `services/help_projection.py` (reason-coded `HelpProjection`, audit-§9 vocabulary), consumed by **all five** Help render paths (Home governance-aware · routes target-checked · one command display filter · click-time re-check); Q-0074 admin-tier fix executed in the same PR; CI mirror 8,621 green, arch 0 errors, live boot + render smoke clean. HLP-3 overlay is next in the Help lane (gated on #657 merge + smoke). Session log: `.sessions/2026-06-10-batch6-help-projection-seam.md`. · Earlier: **verification + queue-truth reconciliation session (PR #648)** — merged the two Codex untapped maps **#646/#647** (each PR's single red check was its own map being a `check_docs` reachability orphan — greened with one link commit per branch, then merged), **source-verified their findings (essentially all confirmed)**, fixed the stale routing they flagged (the PR14-hub queue lines in this file/roadmap/tracker-header — the hub shipped 2026-06-08 via **#584**; the mapping-campaign "Next" row; the Lane-7/8 "queued" notes; adaptive P1B wording — P1B completed via #632), re-badged the completed `multi-lane-execution-plan` + 06-09 consolidated plan `historical`, routed **Q-0071–Q-0074** (router §31), and consolidated everything into [`planning/consolidated-implementation-plan-2026-06-10.md`](planning/consolidated-implementation-plan-2026-06-10.md) — **the one live queue**. Session log: `.sessions/2026-06-10-verification-cleanup-plan-consolidation.md`. · Earlier: 2026-06-09, **execution-plan Lanes 4+7+8 session** (one sequential session, one PR per lane: Answerability Phase 3 **#639** (merged) · Settings hub Phases 0+1 **#640** · Help bounded reconciliation **#642** — scoreboard complete; the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table; session log: `.sessions/2026-06-09-lanes-4-7-8-sequential.md`) · Same evening: **platform-surface mapping standard** (PR **#641**, docs-only): the schema + verified baseline (36 extensions / 29 subsystems / 10 hubs @ `7534e3e`) + two-agent Codex split + copy-paste prompts for the full command/panel/service consistency audit — [`planning/platform-surface-mapping-standard-2026-06-09.md`](planning/platform-surface-mapping-standard-2026-06-09.md); stale prose counts corrected in the help-surface map (Lane 8 keeps its pin-test + characterization scope), the settings command-map preamble, and the repo-navigation cheat sheet (+`four_twenty`/`games`/`server_management` rows). Open draft at write time: **#638** (BTD6 data continuation); #639 merged the same evening (Lane-4 stamp above). · Earlier same day: **multi-lane-burst reconciliation** (after the first **parallel-agent execution run** — four agents on Lanes 2/3/5/6 simultaneously, all merged: **#632/#634/#633/#631**; Lane 1 **#626** preceded it. Verified live: **zero open PRs, #620–#634 all merged**. Scoreboard + lane docs were maintained by each executing agent; this pass reconciled the cross-cutting ledgers — this file's header/lanes/Recently-shipped, `roadmap.md` Now/Next + AI rows — and recorded the parallel-work lessons in `owner/ai-project-workflow.md` §9 "Parallel execution lanes". **Next: scoreboard Lane 4** (Answerability Phase 3, Q-0047), then Lanes 7–8; the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table.) · Earlier same day (end-of-day consolidation pass, **#629** — verification snapshot + queue reasoning in [`planning/consolidated-productive-session-plan-2026-06-09.md`](planning/consolidated-productive-session-plan-2026-06-09.md); its two structured-choices rounds answered **Q-0055–Q-0059 + Q-0063–Q-0065** same evening — all recommended options except **Q-0059 = embed builder** — router §25/§27/§28) · **Gate-lifting interview (same session, after #621 merged):** 16 open decisions answered and routed — Q-0028–Q-0033, Q-0036, Q-0044, Q-0045 flipped to Answered in the router; new Q-0046–Q-0051 recorded (orchestration P4 MVP slice · answerability P3 all-three-tools lift · **standing lift for read-only deterministic AI tools** · BTD6 manual-dispatch refresh · mining lights permanent · vision-batch draft-answer session). Spotlight `!hub`/`!server` aliases dropped (code). Earlier same day (repo-review pass, merged as **#621**): Reconciled every stale "(this session)" / "reconcile next session" marker against live GitHub: orchestration Phase 3 = **#619**, Character overview = **#610**, sell/buy market = **#609**, Context Compiler = **#594**, P0C seam conversion = **#592**. Recorded the side-lane **Community Spotlight** lane (**#613**/**#614** + hotfixes **#615**/**#617**) and hardened it (canonical `utils/db/xp.py` read, `member_count=None` crash fix, first tests). Docs refreshed in the same pass: `docs/roadmap.md` horizons (AI + games are now active lanes; at-a-glance table), `docs/ownership.md` (role-threshold cell → audited seam), `docs/repo-navigation-map.md` (+`community_spotlight` row), `docs/help-command-surface-map.md` (§3 open-gap banner), both AI plans + the wire-exploration plan (PR #s), adaptive plan §15/§16.8. New owner questions: **Q-0044** (spotlight integration + aliases), **Q-0045** (audience simulation — formalizes plan §16.8 item 3). Repo health at review: CI mirror green (**8352 passed, 16 skipped**), architecture **0 errors** (87 known warnings), docs checks pass. Full findings: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md). Source and live GitHub state supersede older wording; verify open PRs live.

## Recently shipped — archived (newest first)

- **#897 (2026-06-15, mining Slice A — Vault v2: inventory soft-cap + vault-cap upgrade path)** —
  the next mining-structures slice, a **dispatched (owner-directed)** `CLASS: feature` work order.
  The phase gate read FIX, but Q-0114 gates only *agent-self-originated* features — the owner
  directly corrected this exact scenario in-session (the `dispatch-phase-gate-precheck` idea's ⚠
  Correction; the prior run built Slice D / #891 on it), so a dispatched feature builds like a bug
  fix. **Pure cap math** in `utils/mining/capacity.py` (distinct item-*types*, not quantity:
  `PACK_SOFT_CAP=40`; vault capacity `30 + level×15` to tier 6; rising coin upgrade-cost ladder;
  `CapStatus`). **Pack soft-cap is warning-only** — the hub overview + every mine/harvest/explore
  swing nudge "stash at the 🏦 Vault" and **mining is never blocked**. **Vault gets an upgradeable
  capacity** — `mining_workflow.vault_upgrade` (coin debit + `vault_level` raise in one transaction,
  the `buy`/`skill_service.respec` precedent; migration 072 adds `vault_level` to
  `mining_player_state`), surfaced as `!vaultupgrade` + the vault panel's ⬆️ Upgrade button. Fully
  **additive** (level 0 = the v1 base; deposits/withdrawals never blocked) — owner directive honored
  (warn at cap, no hard cap approved). New write primitive `set_vault_level` registered in the RS02
  ratchet. Tests: `tests/unit/utils/test_mining_capacity.py` + vault-upgrade/pack-warning pins in
  `tests/unit/cogs/test_mining_vault.py`. `check_quality --full` green (9719); arch 0.
- **#898 + #892 + #889 (2026-06-15, docs-only loop/phase-gate hygiene)** — **#898 (Q-0114):**
  documented the owner's in-session clarification in its canonical homes (router Q-0114 +
  `check_phase_gate.py` docstring) so a literal agent doesn't re-derive it — a **dispatched** work
  order (the `/fire` endpoint, even `CLASS: feature`) is owner-directed and flows freely; the phase
  gate is **only** for features an agent invents itself. **#892:** captured a Hermes
  token-efficiency root-cause + an investigation plan for the next session
  (`docs/operations/hermes-control-plane.md` + a research note). **#889:** a `CLASS: feature` mining
  Phase-2 work order arrived during a FIX phase, so the phase gate correctly **gated the build**
  (Q-0114) — the work was already turn-key in the structures plan, so the PR is loop cleanup only
  (the `dispatch-phase-gate-precheck` Q-0089 idea — run the gate at the *dispatcher* — + disposed the
  redundant slice-opener #888 per Q-0125). Docs only.
- **#884 (2026-06-14, mining §7.5 Vault — a per-player safe stash)** — the first executed slice of
  the mining structures lane (the owner's bot-side steer for the night routine). A protected store
  separate from the active pack: `vault_deposit`/`vault_withdraw`/`vault_deposit_all_resources` on the
  audited `mining_workflow` boundary move items between `mining_inventory` and the new `mining_vault`
  table (migration 070) **atomically** (no coin/audit leg — item-state direct-lane); `🏦 Vault` hub
  panel + `!vault`/`!stash`/`!unstash`. **Purely additive** — v1 is a pure safe store, no inventory
  cap (that sink is the documented follow-up), so existing play is byte-identical. The RS02
  write-boundary ratchet now also guards `update_vault_item`. Verified on real Postgres
  (deposit/withdraw/stash-all round-trips · over-move guards · item conservation). `check_quality
  --full` green (9655); arch 0. **This session also promoted the rest of the lane to a turn-key plan**
  — [`planning/mining-structures-skill-tree-plan-2026-06-14.md`](planning/mining-structures-skill-tree-plan-2026-06-14.md)
  (§7.4 capped skill tree + §7.5 Forge/Home + Vault-cap, each a ▶ startable PR-sliced slice) so the
  night/next session can build mining cold.
- **#878 + #879 + #881 (2026-06-14, P1-1 — versioned AI eval/smoke matrix, offline half + drift guard + hotspot coverage)**
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
  surface; coverage floor; meta-tested to actually fire). **#881:** dog-fooded that guard — 6 golden
  tool-selection probes for the highest-value uncovered **BTD6** tools (the live-defect hotspot:
  round-cash/boss/map/paragon-degree/round-composition/answerability, each modeled on a real live
  miss), moving the ratchet **8 → 14/34** covered. `check_quality --full` green (9645); arch 0.
  **#886 (2026-06-15) advanced the ratchet 14 → 20/34** — 6 more golden tool-selection probes
  (`get_ai_tool_catalog` + the `btd6_cumulative_cost`/`paragon_requirements`/`monkey_knowledge`/
  `mode`/`list_roster` lookups), floor raised to 20.
  **#895 (2026-06-15) advanced the ratchet 20 → 27/34** — 7 probes covering the **whole non-BTD6
  uncovered surface**: the 5 server-introspection tools (`get_server_overview`/`list_server_channels`/
  `list_server_roles`/`lookup_member`/`list_all_members`) + `get_ai_policy_explanation` +
  `diagnostics_health_snapshot`; floor raised to 27.
  **#896 (2026-06-15) completed the ratchet 27 → 34/34 — FULL AI tool-surface coverage** — the final
  7 specialized BTD6 lookups (`btd6_bloon_filter`/`btd6_ct_team_status`/`btd6_geraldo_lookup`/
  `btd6_paragon_calculate`/`btd6_power_effect`/`btd6_power_lookup`/`btd6_relic_lookup`);
  `_ACK_UNCOVERED_TOOLS` is now **empty** and the floor == the catalogue, so the drift guard fails
  closed on any newly-added tool. `check_quality --full` green (9698); arch 0.
  **Still owed (P1-1):** the live-quality battery (needs prod creds) + absence-guard **Layer B**
  (design-for-review). *(This session's docs close-out tidy merged as **#883** — `▶ Next action`
  refresh + #872–876 ledger drift cleared.)*
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
  `set_finding_status` SQL verified on real Postgres.
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
  (9467); arch 0; `check_docs` clean.
- **#825 (2026-06-14, hardening P0-4 PR 2 — channel creation + category lifecycle convergence,
  Q-0100)** — the **second half** of the channel-ownership convergence; **closed the final P0
  integrity track.** Ad-hoc operator channel creation (`!create`/`!evt`/`!bulkcreate` + the
  create panel) has **no declared subsystem binding**, so it never fit the catalogue-driven
  `ResourceProvisioningPipeline`. It is now owned by a new audited
  **`ChannelLifecycleService.create_channels`** — the channel-domain sibling of the allowlisted
  `RoleLifecycleService`: bot-perm check → category resolve/get-or-create → safe-named text/voice
  create → typed per-name `LifecycleResult` + audit companion + `channel.lifecycle_changed` event.
  Subsystem-*bound* creation stays with the provisioning pipeline. The three cog commands + the
  create panel route through it; `test_no_direct_channel_mutations.py` pins
  `create_text_channel`/`create_voice_channel`/category creation, and `test_no_silent_auto_create.py`
  lists the service as the one sanctioned manual `guild.create_*` caller. No migration.
  `check_quality --full` green (9453); arch 0 errors.
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
  extracted to `views/channels/list_panel.py` (cog 739→640 LOC). `check_quality --full` green
  (9446); arch 0 errors.

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
- **#872 + #873 + #874 + #875 + #876 (2026-06-14, autonomous-loop / Hermes ops + docs housekeeping)**
  — five small ops/docs PRs from two parallel sessions, cleared straight to the archive (each is
  durably recorded in its own `.sessions/` card; not a reconciliation pass — the #900 cadence routine
  will regroup as needed): **#872** the band-#870 Q-0107 reconciliation pass (`loving-meitner`);
  **#873** install-soul-script; **#874** Hermes terminal cheatsheet; **#875** branch-hygiene
  cheatsheet; **#876** backup-status correction (`sharp-ptolemy`). Docs/ops only.
- **#802 + #805 + #811 + #812 + #813 (2026-06-13/14, portable substrate-kit — PR 1b tail + PR 2
  capability layer)** — the owner's active OSS thread advanced inside the self-contained
  `substrate-kit/` tree ([extraction plan](planning/portable-substrate-kit-extraction-2026-06-13.md)).
  **#802** the PR 1b tail (the two stdlib checker ports — generic doc-reachability + session-log
  guards). **PR 2 (the capability/modes layer) §3b/§3c COMPLETE:** **#805** task-stances (the
  capability layer) · **#811** an invokable skill pack + skill/stance precedence · **#812**
  spawnable read-only persona specialists · **#813** a PreToolUse stance-guard hook (stances now
  *enforced*, not advisory). Stdlib-only; green in-repo; never mutates superbot's live
  `.claude/`/`docs/`. **Resume: the PR-2 remainder — modes + contract templates + triggers.**
- **#827 + #828 + #831 + #832 + #835 + #836 + #837 (2026-06-14, the Railway agent-access +
  permission-autonomy session — owner-directed, manual)** — **#827** set
  `permissions.defaultMode: bypassPermissions` (+ empty `ask`, pre-accepted bypass dialog) in
  `.claude/settings.json` so routines never stall on confirmation prompts (Q-0128); **#828** made
  unattended self-initiated action explicit in CLAUDE.md + `collaboration-model.md` and recorded
  that `send_later` isn't provisioned here (Q-0129); **#831** captured the
  routine-activity-visibility idea; **#832** shipped read-only Railway **logs** access
  (`scripts/hermes/railway_logs.py`, unblocking the gated log-triage skill) + **#835** Railway
  **env-var read/write** (`scripts/hermes/railway_vars.py` — list/get/set/unset, masked list,
  audit lines, stdin secrets, `--no-deploy`), both Q-0130; **#836** aligned token config to
  `RAILWAY_TOKEN` + a "which token?" guide; **#837** recorded the manual-step risk-labelling rule
  (Q-0131). **Owner set the Railway credential + project/service/env IDs in the agent env after
  the session; VERIFIED LIVE 2026-06-14** by an auth-probe routine (the `RAILWAY_API_KEY` alias +
  Cloudflare-UA fixes landed in #840). *(Archived by the band-#870 reconciliation pass.)*
- **#803 + #806 + #808 + #810 + #816 + #818 (2026-06-13/14, reconciliation + workflow rules +
  session-close housekeeping)** — **#803** the **band-#800 Q-0107 reconciliation pass** (scored
  #781–#800, planned #801–#820, fixed the masking-range ledger drift; now `historical`). **#806**
  two workflow rules: **Q-0124** (a manually-started session does NOT run the reconciliation pass —
  the routines always do, automatically) + **Q-0125** (reconciliation passes must disposition stale
  open PRs via the GitHub MCP — the gap that left #766/#771 rotting). **#808** preserved the specs
  from issues #229/#232 into `docs/ideas/` before closing them. **#818** the #817 merge note + router
  **Q-0127** (the `auto-merge-enabler` workflow doesn't fire for MCP-created PRs). **#810/#816**
  session-close logs (workflow cleanup · the CI-efficiency arc). *(Archived by the band-#870
  reconciliation pass.)*
- **#788 + #789 + #790 + #791 + #792 + #793 + #795 + #796 + #798 (2026-06-13, the portable
  substrate-kit extraction — PR 1a + 1b)** — the owner's strategic refocus (the
  [portable agent-memory package](ideas/portable-agent-memory-package-2026-06-12.md) idea)
  executed under a self-contained `substrate-kit/` tree that **never mutates superbot's live
  `.claude/`/`docs/`** ([extraction plan](planning/portable-substrate-kit-extraction-2026-06-13.md),
  owner-approved after 10 external-review rounds; [revision report](planning/portable-agent-substrate-revision-2026-06-13.md)).
  **PR 1a (#789)** the locked-contract skeleton + state-backend interface; **PR 1b
  (#791→#792→#793)** the staged-learning loop — interview engine (provisional self-answers
  never self-graduate), template render + core orientation docs, the 6-doc orientation
  template set. Plus the revision report (#788/#795), the PR-1b-done resume recipe (#796), a
  main→branch sync (#790), and the dev-command allowlist (#798). **Resume point: the 1b tail
  (two stdlib checker ports) → PR 2 (capability/modes layer).** Stdlib-only; green in-repo.
  *(Recorded by the band-#800 reconciliation pass — these PRs had been masked from the ledger
  guard by a planning range; see the [pass record §5–6](planning/reconciliation-pass-2026-06-13-band800.md).)*
- **#817 (2026-06-14, hardening P0-3 arc PR 3 — delegated-Setup apply authority, Q-0098)** —
  closed the "you may apply, then every per-op write fails" gap for a server-owner-delegated
  **non-administrator** member. A bounded `actor_type="setup_delegate"` is authorized at the
  capability floor (`governance.capability`) like `system`/`backfill` — but, deliberately not
  the step-1 short-circuit, it still requires target-guild membership AND stays subject to the
  revoke overlay, and is **audited as `setup_delegate`** (distinguishable from an admin write).
  It is minted **only** by `services.setup_operations.apply_operations`, which re-verifies the
  live delegation (`setup_access.can_apply_setup`) against a fresh `SetupSession` before
  minting (never trusts the view gate); owner/admin keep `"user"`, delegation-lost falls back
  to `"user"` so the floor denies. Threaded to all three capability pipelines (binding now
  forwards `actor_type`); `setup_delegate` added to their `_ALLOWED_ACTOR_TYPES` + the
  settings/resource audit CHECK constraints (**migration 069** — finds each auto-named
  constraint by definition, re-adds a named idempotent widened one). Four non-escalation
  guards: AST fence (`test_setup_delegate_actor_boundary`) confines the token to 5 contract
  files; setup-lane only; revoke overlay; live re-verification. `check_quality --full` green
  (9442); arch 0 errors; real-Postgres + clean-boot proof (constraint accepts `setup_delegate`
  / rejects unknown; idempotent). **P0-3 complete; next P0 = P0-4 channel-ownership (Q-0100).**
- **#794 (2026-06-13, hardening P0-3 arc PR 2 — retire XP-announce + economy-log scalar
  pointers)** — deleted both editable scalar `SettingSpec`s so each Discord-resource pointer
  has one canonical binding owner; repointed the writers (XP channel modal, economy
  `_record_log_channel` ×3) + the stale legacy reads to the binding lane. A *retired* pointer
  reads binding-first regardless of the OFF-by-default `bindings.primary` flag (new
  `config_arbitration` `pointer_retired=True`), so it deploys with no coordinated flag flip
  (legacy KV = rollback fallback). Extended `BindingMutationPipeline` for `actor_type='system'`
  writes; fixed two adjacent binding-name bugs (`logging_presets.py` + `channels.py`); emptied
  `CONVERGEABLE_POINTERS`; added `test_no_dual_declared_pointer`. CI green (9328); arch 0
  errors; proven on real Postgres + clean boot. **Next P0 = arc PR 3 (delegated-apply, Q-0098).**
- **#786 + #787 (2026-06-13, native auto-merge migration — Q-0123)** + **#781–#785 / #797 /
  #799 / #800 (reconciliation + session-close + owner-decision housekeeping)** — merge
  mechanics moved off the Claude session (`auto-merge-enabler.yml` arms GitHub-native
  auto-merge on every non-draft `claude/*` PR; the Q-0084 manual self-merge envelope struck
  from CLAUDE.md — removes the #778 forgotten-deferred-merge class server-side), the **third
  Q-0107 reconciliation pass** (#781, now `historical`), four session-close PRs (#782–#785,
  #797), the **Q-0119** decision (governance role pointers get a reserved-namespace
  `governance` schema home — P0-3 family 3 unblocked, #799), and two earned calibration rules
  captured to the journal (#800).
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

- **#844 (2026-06-14, the sixth Q-0107 reconciliation pass — band #841–#860 plan)** —
  the band-#840 docs-only reconciliation that produced the current live ledger
  ([record](planning/reconciliation-pass-2026-06-14-band840.md)): **P0 integrity spine
  COMPLETE** (P0-2 #829 · P0-3 #817 · P0-4 #820/#825); priority advances to the P1
  correctness tier; marker reset #820→#840 (next at #860); decade queue #841–#860 planned.
  *(Recorded here at the P1-2 session close to keep the strict ledger green — it merged
  without its own ledger entry on the same auto-merge race as #843; its full fold is the
  next pass's, per Q-0124.)*
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
  widget. 31 tests; CI green; live-boot verified.
- **#765 + #767 + #769 + #770 (2026-06-12/13, backup posture + autonomous-loop
  follow-ups)** — **#769** Postgres backup posture (band slot 3 — daily `pg_dump` to a
  GitHub Actions artifact; [production-deployment §Backups](operations/production-deployment.md))
  · **#767** `executor-nightly.yml` cron moved off `:00` to dodge scheduler congestion ·
  **#770** permissions: the autonomous executor may push to `main` without prompting ·
  **#765** the autonomous-loop session close (loop live + Hermes dual-platform control
  plane — [session log](../.sessions/2026-06-13-autonomous-loop-hermes-control-plane.md)).
- **#764 (2026-06-12 night, the P2 doc-drift sweep — band slot 2)** — all five
  hardening-P2 fixes, source-verified then applied: smoke checklist's nonexistent
  `!platform diagnostics` → `runtime`/`consistency` + the platform-panel
  completeness claim honest · the AI runtime README rewritten ("inert scaffold" →
  the live gateway/routing/NL-stage platform) · **ADR-006 dated status addendum**
  (pause condition satisfied; decision untouched per ADR immutability) +
  decode-status header v55.0→**v55.1** + duplicate backlog № fixed · media folio
  states the **raw-payload reality** (bounded projection = the Q-0099/P0-2 target)
  · `YOUTUBE_CONTEXT_ENABLED` owner `ai`→`platform` (ADR-007). P2 table marked
  SWEPT.
- **#763 (2026-06-12 night, the second Q-0107 reconciliation pass)** — band #741–#762
  scored ([record + next-band queue](planning/reconciliation-pass-2026-06-12-night.md):
  slots 1+3 executed; the hardening+safety queue carried intact — capacity went to the
  two owner-steered arcs) · the #753–#761 ledger gap reconciled · **both audit checkers'
  shared merge-subject regex root-fixed** ("Merge PR #N:" was invisible — the cadence
  checker froze at #751 and the ledger checker was **green while five PRs were missing**;
  tests pin all three subject styles now) · marker reset, next pass at **#780**. Docs +
  tooling only.
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
  calibration** — wired, young, trust grows per verified run.
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
- **#737 (2026-06-12, Context7 MCP adopted)** — wired `@upstash/context7-mcp@3.2.0` (live
  library docs → kills the "API-from-memory" bug class) as a pinned `.mcp.json` server +
  [`docs/operations/mcp-servers.md`](operations/mcp-servers.md) (when-to-use, key setup, Q-0105
  provenance). Q-0096 answered (Context7 yes; Postgres-MCP/pyright-lsp still open).
- **#736 (2026-06-12, CodeGraph health check + doc pin fix)** — verified CodeGraph 3.11.2 is
  healthy (no regression from the bump; the "problems" are the cold-start availability blip + the
  documented false positives). Fixed the real bug: `docs/codegraph-usage.md` told agents to run the
  old `@optave/codegraph@3.10.0` while the live pin is 3.11.2 — bumped all command refs.
- **#732 (2026-06-12, command-surface dump tool)** — `scripts/command_surface_dump.py`:
  offline AST dump of every prefix/slash command by subsystem (+ `--json` and
  `--diff-checklist` against the untested-surface checklist); 8 tests. The #731 session's
  grooming companion; roadmap queue item 1 closed with it.
- **#733–#735 (2026-06-12, the agent-workflow/memory hardening arc)** — **#733**: **Q-0102**
  (mandatory `⟲ Previous-session review` session-ender) + **Q-0103** (open session PRs **ready not
  draft**; every PR reaches a terminal state). `scripts/check_session_log.py` + post-edit/Stop-hook
  wiring enforce the Q-0089/Q-0102 enders. New
  [`docs/operations/claude-code-hooks-and-plugins.md`](operations/claude-code-hooks-and-plugins.md)
  (the 6 wired hooks + brainstorm + plugins posture → Q-0096). `.claude/settings.json`
  permission-friction cut (`acceptEdits` + curated allowlist; force-push/destructive still prompt).
  **#734**: reconciled this ledger's drift (added #730/#733, relabeled #731, added #724–#728) and
  built `scripts/check_current_state_ledger.py` (the living-ledger self-check) + **Q-0104** (closing
  documentation audit) + **Q-0105** (adopt-tooling-with-a-delete-if-unreliable kill-switch) +
  permissions-posture doc. **#735**: **Q-0106** — agents propose `CLAUDE.md` rule changes via a
  router Q-block, never self-edit (binding for a session but not pinned; read-only to a fully
  autonomous agent). Captured ideas: autonomous self-improvement loop · Hermes→Claude Routines
  dispatch bridge · portable OSS memory/workflow package · ledger session-arc aggregation.
- **#731 (2026-06-12, untested-surface checklist)** — the owner-commissioned
  [`docs/audits/untested-surface-checklist.md`](audits/untested-surface-checklist.md):
  18 sections, 70+ `[ ]` items covering every command/UI surface that automated CI
  cannot verify and has no live-walk record. Persistent successor to the 2026-06-10 eval
  checklist. Linked from hardening roadmap.
- **#730 (2026-06-12, Hermes skills installable)** — `scripts/hermes/build_skills.py` generates
  installable `SKILL.md` files (Hermes frontmatter) from the skill docs + `install-skills.sh`
  deploys them to the VPS; `repo-health` self-schedules a daily Telegram digest via a frontmatter
  `blueprint.schedule`. New `log-triage` skill (read-only prod/gateway log diagnosis) +
  [`hermes-operating-prompt.md`](operations/hermes-operating-prompt.md) (the Hermes-side `CLAUDE.md`).
- **#729 (2026-06-12, 429 login crash-loop fix)** — `_maybe_backoff_on_rate_limit()`:
  when `bot.start()` returns HTTP 429 (Discord/Cloudflare 1015 rate limit), the
  process now sleeps 60 s before exiting so Railway's on-failure restart fires after
  the backoff has elapsed rather than immediately. Breaks the rapid crash loop that
  deepened the ban (live incident 2026-06-12). 5 targeted tests added.
- **#724–#728 (2026-06-12, the readiness/roadmap/tooling arc)** — **#724** indexed + reconciled
  the seven production-readiness maps; **#725** the consolidated hardening roadmap + the
  `repo-manageability` ideas + routed Q-0098–Q-0100; **#726** the four manageability tools
  (`review_scope.py` + readiness scoreboard + doc-freshness guard + the `current-state.md`
  trim/auto-archive ratchet); **#727** closed that arc's session; **#728** recorded owner
  decisions Q-0098–Q-0101 (all the recommended option). Docs/tooling.
- **#715–#723 (2026-06-12, the review-map + readiness-map set)** — **#715** founded `docs/repo-review-map.md` (the review/refactor partition: Axis A repo domains · Axis B subsystem-slice vs. shared-platform review units); **#716** closed that session. Then **seven per-subsystem production-readiness maps** (#717 AI · #718 health/diagnostics + Q-0097 · #719 server-management · #720 settings/bindings/provisioning · #721 BTD6 · #722 games · #723 media/YouTube) landed under [`planning/production-readiness/`](planning/production-readiness/README.md) — each a source-verified Done/Partial/Not-Done inventory of one slice, linked from its folio. A reconciliation pass added the directory README index, normalized two badges to `audit`, and linked the set from the review map. Docs-only; recurring cross-map themes = settings pointer-lane debt · server-management channel-ownership convergence · AI projection dual-store · BTD6 runtime/data split.
- **#706** — **BUG-0004 + capabilities format (the owner's live re-test round)**: r-shorthand round anchors (`r53`/`r 53`, digit-boundary-guarded) across the round-cash matcher · "end of round N" completion-cue start shift with stated assumption (the $71,315.20 cumulative-as-total mislabel; truth $56,318.70) · had/held balance cues · router r-round leg (two tokens or one + money cue) · `deterministic_meta_reply` renders one bullet per capability + Lookups line, advertising boss_health Standard+Elite, crosspath/bulk pricing, and balance projections. Code-only (no seed-data needed). (#705 same day: the Q-0093 in-turn merge process record.)
- **#703** — **AI-knowledge live-miss fixes (BUG-0001r/0002/0003, the owner's morning screenshots)**: elite boss tiers backfilled from the pinned v55.1 dump for all 7 bosses + variant-labeled boss grounding · boss canonicals/impop/despo route to `btd6.answer` (the unguarded-general-path class) · resolver plural fold · the `<quantity> <crosspath> <tower>` pricing leg ("10 041 despos" = ten 0-4-1s, owner-corrected; per-purchase $5 rounding) with `btd6_cumulative_cost` crosspath/quantity parity · round-cash workflow on the **default + balanced profiles** (Q-0048) + money-question gate + by-round anchors · `btd6_probe.py --route`. **Owner action: `!btd6ops seed-data` after deploy** (bosses/towers are blob-lane data).
- **#702** — **V-16 phase 1: the gear-lane slice (full Q-0092 scope)**: 9-slot set-piece equipment model (weapon/shield/helmet/chestplate/leggings/boots; migration 068 folds legacy "armor" items/slot into the taxonomy — live-replay-verified) · same-tier full-set bonus with **set-aware Equip Best** + "⚠ breaks set bonus" picker warnings · **bronze + silver join the ore ladder** (smelt→forge per tier, 44 recipes) · 30-item stat/economy tables **pinned by a duel-simulation test** (`test_gear_set_numbers.py`; rationale: [gear-set-numbers](planning/gear-set-numbers-2026-06-11.md)) · gear-picker stat previews · the **paper-doll compositor** (`utils/character_render.py`, placeholder sprites, owner-pack hot-swap dir + README) wired to `!gear` + the hub Gear button · market/workshop panels restructured past the 25-option/1024-char caps.
- **#694** — **BUG-0001 fixed (runtime)**: the round-cash matcher gained clause-separated-anchor support + starting-balance projection (grounded in the evidence ledger); bug book founded (`health/bug-book.md`); actions bumped to Node-24 majors; Q-0091 canon recorded. Production phrasing pinned as regression tests + a live-battery eval case.
- **#685–#698 (the 2026-06-10/11 marathon conversation, 14 merged PRs)** — production Python pin + ops doc (#685) · Q-0087–Q-0091 + V-13–V-16 captures · self-driving foundation (workflow §10) · Q-0089 idea-ender installed · the V-14 competitive-teardown dossier + fishing verdict · gap analysis · model-allocation policy (workflow §11) · working-profile §6 + timeline calibration + origin story. Full arc: `.sessions/2026-06-10-vision-ideation-capture.md`.
- **#679 / #677** — **the Help overlay editor UI (audit Phase 5, plan #674)**: PR A = the hide/rename/re-describe editor (staff-hub button + "Help appearance" Settings domain group; one audited `help_overlay_mutation` call per action; Q-0055/Q-0058 rendering) · PR B = migration 067 + `set_home_message` + the Q-0059 Home embed builder with **mandatory preview** (shared `home_embed_frame` for render+preview, mention suppression, byte-identical default pinned).
- **#671** — **queue remainder: RS07 + RS08 + the Help-Preview Tier-2 fix**: the audited `services/chain_service.py` (typed results, real `prev_value`, repo-wide write fence — Batch 3 COMPLETE; a latent chain-create limit-reset bug fixed en route) · Batch 9's RS08 (diagnostic builders render-only, SQL in the owning `utils/db` modules; `_build_rank_embed` finished its `rank_providers` migration; new no-raw-SQL-in-cogs/views invariant) · the Help Preview rebuilt on `project_help_with_execution` (first consumer; governance hides render as Hidden; overlay state + orphaned overrides render). Stale exception-ledger rows (chain/mining/role-thresholds) corrected.
- **#670** — **BTD6 closeout: Navarch eval regression probes + ledger reconcile** (tests/evals + docs).
- **#668** — **BTD6 conversation-carryover grounding (item 7 slice 1) + zero-fact sweep fixes**: a zero-fact BTD6 question with channel identity now grounds the newest entity-bearing conversation turn (read-only over the existing bounded `ai_conversation_service` floor; every carried fact labeled `[btd6_carryover]`), closing the live "Does **it** make coins" turn-2 miss; plus the proactive-sweep fixes — ranking rosters ("best paragon"/"strongest tower") and bare distinctive shorthand ("navarch"). Plan (slice 1 executed; tail unapproved): [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md).
- **#667** — **landed the stranded mining stack on `main`**: the stacked bases of #663/#664/#665 didn't auto-retarget when #661 merged, so all three merged into their *parent branches* — this completion PR brought the full content to `main` (content-verified EOD) + fixed the agent-context manifest (`cogs/mining/` deleted in RS02). Stacked-merge lesson: `.sessions/2026-06-10-mining-finalization.md`.
- **#666** — **BTD6 `scripts/btd6_probe.py` grounding-triage tool** (replay grounding for any user text — the diagnosis snippet the Navarch session rewrote four times) + the item-7 carryover plan doc (the Q-0015 grooming move).
- **#665 / #664 / #663 + #661** — **the mining/tool/gear finalization 4-PR stack (consolidated-plan Batch 7 + the Wave-2 seed; content on `main` via #667)**: atomic shop-purchase workflow (RS01, Q-0071=A) → pure mining domain relocated to `utils/mining/` + `services/mining_workflow.py` owning the workshop ops (RS02 stage 1, Q-0072=C) → **every** mining write behind the workflow service, one transaction per op, AST-fenced (`test_mining_write_boundary.py`), recipes catalog-reconciled under an alignment lint (RS02 stage 2 — **Batch 7 COMPLETE**) → shared **game-XP** track (migrations 065/066, awards atomic with their actions, daily soft cap, `gamexp`/`crafting` boards, depth records) · deeper ladders (the diamond lantern finally unlocks MAGMA) · Gear panel / Recipe browser / fuzzy names / `!fastmine` · **duels gear wear (Q-0054 closed)** · PIL inventory + stat cards (Q-0075/Q-0076 — router §32).
- **#662** — **BTD6 Navarch "no coins" routing fix + answerability items 6a–c**: the live wrong answer was **missing routing, never missing data** (name-resolution miss on a dropped article → 0 grounding facts; the cap-truncated income sentence; no paragon income/effect grounding leg) — fixed across AI grounding, menu embeds, and the paragon AI tool; plus minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV), the Pouākai diacritic tokenizer fix, and honest dataset source labels/summary. Backlog: [`btd6/btd6-gamedata-decode-status.md`](btd6/btd6-gamedata-decode-status.md) ⭐ (item 7's slice 1 shipped same day, #668).
- **#659** — **HLP-3: the guild Help overlay (display-only hide/rename)**: migration 064 `help_overlay` + sole-writer DB module + the audited `help_overlay_mutation` seam (admin gate · write-time catalogue-key validation · partial-edit merge · per-field/full reset · cache invalidation · audit events) + a cached fault-tolerant read model, flowing through the #657 projection into **all five** render paths (hide parity with governance hides; renames as presentations; orphans reported, never rendered; no-rows = byte-identical, pinned). Q-0055 display-only pinned by an admission-path import fence; `help_cog` decomposed via `cogs/help/panels.py`. **Open Help tail: the overlay editor UI** (audit Phase 5) + Phase 4 records.
- **#660** — **BTD6 backlog handoff truth-up** (docs-only): decode-status item 5 struck (shipped in #658), items 6a–c given turn-key notes — the #662 session consumed them.
- **#658** — **BTD6 deterministic-Ask parity + dark renders (decode-status items 5+6d)**: `deterministic_answer` gained the bloon branch; powers/MK/bosses ground via Pass 3e; Pro views render 🌀 Effects + 🤖 Minions; Striker fraction-semantics fix.
- **#657** — **Batch 6: the Help projection seam (HLP-2) + Q-0074**: `services/help_catalogue.py` (stable-keyed inventory; four drift-finding kinds pinned empty) + `services/help_projection.py` (reason-coded `HelpProjection`, audit-§9 vocabulary; only `display_hidden`/`governance_hidden` hide — lock states stay advertised, HLP-4), consumed by **all five** Help render paths (Home governance-aware · typed/dropdown routes target-checked, hidden ⇒ not-found · one command display filter · click-time re-check). Q-0074 executed in the same PR (admin `visibility_tier` owner → administrator; placement==admission pinned by the catalogue `tier_mismatch` finding). The HLP-3 overlay followed the same day (#659, merged).
- **#655** — **BTD6 post-cutover: full verification + every carry-forward decoded**: dump fidelity re-proven (byte-identical regeneration; rounds parity 140/140), 2,022 menu embeds + the AI battery green, `_CUTOVER_CARRYFORWARD` emptied (audit **91 CLEAN / 0 DELTA / 0 SUSPECT**); fixed mode-rules dark data, the `!btd6 diagnostics` 400, the version-stamp-rot class, and the container-path leak.
- **#656** — **Batch 5: Adaptive P1C — Access Map + Help Preview staff-hub subpanels** (`views/server_management/access_map.py`, the first `project_access_map` consumers; Q-0032 hub-buttons-only; Q-0045 declared-tier simulation with the §16.4 label; display-only pinned by a mutation-import test).
- **#654** — **Batch 4 core: Settings Phase 2 declaration coverage (DT06) + Q-0064 BTD6 rows**: `DomainPanelSpec`/`SubsystemSchema.domain_panels` replaced the curated `DOMAIN_CONFIG_SUBSYSTEMS` frozenset under a coverage invariant; the `btd6.version_announce_channel` binding + the CT-group guided flow landed with it. Open tail: pointer-classification rows.
- **#653** — **BTD6 post-cutover decode wave 1**: druid/paragon thorn rings, engineer 4-x-x typed sentries, the **banana economy** (bananaValue / bank capacity+interest as specials).
- **#652 / #651 / #650** — **consolidated-plan Batches 3 / 2 / 1**: service-boundary fixes (routing `set_policy` owns audit with real `prev_value`; audited role-threshold *clear* seam + widened fence; **RS07 chain slice still open**) · the surface-classification completeness invariant (DT04 — all 40 hidden routes + both alias piles + `/setup-hub` declared) · runtime truth/clarity (binding no-op cache hook deleted, `ResourceMutationPipeline` shell deleted, `ensure_and_get_economy` rename, `panel_command` deprecated).
- **#648** — **queue-truth reconciliation + the consolidated implementation plan** (docs-only): merged + source-verified the #646/#647 maps, fixed the queue-truth drift they flagged, routed Q-0071–Q-0074, and produced [`planning/consolidated-implementation-plan-2026-06-10.md`](planning/consolidated-implementation-plan-2026-06-10.md) — the one live queue.
- **#649** — **BTD6 v55.1 towers cutover (Q-0066/Q-0067/Q-0068)**: every committed stats file game-native (25 towers + 17 heroes + 13 paragons) via `parse_gamedata.py --all` through the new cutover merge layer (curated names preserved, set-level name guard 55/55); Farm/Village first committed tiers + prose-pinned income-aura decodes; per-tier beast names; source labels now "BTD6 game data {version}". Post-cutover backlog: [`btd6/btd6-gamedata-decode-status.md`](btd6/btd6-gamedata-decode-status.md) ⭐.
- **#647 / #646** — the two **untapped mapping audits** (Codex, merged 2026-06-10): the docs/tests/verification map (FIND-DT01–DT15 + implementation-readiness batches) and the runtime/services/workflows map (FIND-RS01–RS18 — economy two-commit purchase, mining direct writes, binding-cache no-op invalidation, role-threshold-clear seam bypass, dead resource-pipeline shell, …). **Source-verified + reconciled the same day**: essentially all findings confirmed; queue-truth drift fixed; dispositions, batch order, and the live queue in [`planning/consolidated-implementation-plan-2026-06-10.md`](planning/consolidated-implementation-plan-2026-06-10.md).
- **#645** — **Q-0070 presets-everywhere posture** captured + routed (defined presets primary · preset-then-edit · manual always — settings audit Phase 4; the AI template-advisor stays a gated idea). Docs-only; router §30.
- **#644 / #643** — **platform-surface mapping Agents B + A** (Codex): the admin/platform-surface + user-surface reports under the #641 standard — 19 findings, zero severity-1; dominant pattern = **ledger classification drift** (hidden/panel/legacy routes unclassified → consolidated-plan Batch 2). The mapping campaign is **complete**.
- **#638** — **BTD6 decode-tail continuation** (dump v55.1): ABR rounds + income sets ingested game-natively (roundset-aware `btd6_round_composition`/`btd6_round_cash`); subtower mechanisms 7/7; buffs 15/38 confirmed (rest provably unconfirmable pre-cutover). The `--all` towers cutover followed 2026-06-10 (PR #649 — Q-0066–Q-0069 executed, router §29; verify merge).
- **#642** — **Help bounded reconciliation (Lane 8, help audit §13)**: `docs/help-command-surface-map.md` preamble counts reconciled against the live registries — **10 hubs · 29 subsystems · 36 loaded extensions · 28 of 36 define `build_help_menu_view`** (the doc had carried "9 hubs" and two differently-stale hook claims) — and **pinned by test** (`test_preamble_counts_match_live_registries`) so the rot class is closed; plus a **28-test characterization net** for the five Help render paths (Home · Advanced · typed routes · generic embed · dedicated panels) pinning today's behavior — including the hub-shadows-subsystem route quirk and the `diagnostic`→Platform-Hub builder override — so the future Help projection seam lands against a regression net. **No behavior changes**; Q-0055–Q-0059 stay design posture. Audit: [`planning/help-cog-customization-audit-2026-06-09.md`](planning/help-cog-customization-audit-2026-06-09.md).
- **#640** — **Settings hub: actionable-groups discovery + >25 reachability (Lane 7, settings audit Phases 0+1)**: the hub no longer blindly lists every non-internal subsystem (28 listed, 3 silently truncated, many empty pages) — discovery now follows the audit's §6 inclusion rule via `services/customization_catalogue.actionable_settings_groups()` (editable scalar · binding · provisionable resource · declared domain panel; live taxonomy = **11 groups**, exactly audit §4/§5), with **select pagination** past Discord's 25-option cap (no silent truncation, no empty pages by construction) and **actor-aware availability** (`SettingsHubView.create(author, guild_id)` pre-reads per-guild cog routing and marks routed-off groups "⛔" while keeping them reachable; callbacks still re-check authority). Discovery/navigation only — no mutation-service absorption; Phases 2/3 stay behind the decided Q-0063/Q-0064 directions. Audit: [`planning/settings-cog-centralization-audit-2026-06-09.md`](planning/settings-cog-centralization-audit-2026-06-09.md) §11.
- **#641** — **platform-surface mapping standard** (docs-only): the schema + verified baseline (36 extensions / 29 subsystems / 10 hubs @ `7534e3e`) + the two-agent Codex split + copy-paste prompts; its §7.1 carries the merge-session contract (extended 2026-06-10 with the campaign-complete + question-routing record).
- **#639** — **AI answerability — Phase 3, the three self-awareness tools (Lane 4, Q-0047/Q-0048)**: the #616 introspection read model exposed as three read-only AI tools, **audience-tiered at construction** (the registry bakes the request `AIScope` into each handler — no scope/target tool arguments exist): `get_ai_tool_catalog` (tier-filtered capability catalog; higher-tier tools counted, never named; one-line purposes for token bound), `get_ai_policy_explanation` (effective mode/source/min-level/cooldown for the asking user in the asking channel via a new optional `build_registry(channel=...)` binding; precedence trace + recent audit admin-only), and `btd6_answerability` (domain inventory + explicit unsupported gaps; carries `grounding_domain="btd6"` — and therefore the `btd6_*` name — so its counts/versions join the faithfulness ledger instead of being blocked by the BTD6-path number-guard). New `self_awareness` toolset; narrow instruction-stack clause routes the three meta-questions to the tools (pinned by test). **Model loop awaits the maintainer's prod check** (no sandbox provider key). Plan: [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md) Phase 3.
- **#634** — **AI tool orchestration — Phase 4 MVP (Lane 3, Q-0046)**: the plan→execute→verify workflow for the round-cash question family (`services/ai_round_cash_workflow.py`) + the first **typed answer-with-evidence contract** (Q-0043 inclusive-range semantics carried in the contract), hung off `natural_language_stage._invoke_gateway` and **activated only under an orchestration profile that selects it** — default behaviour byte-identical (the Phases 1–3 compatibility bar). The faithfulness verifier is a comma-normalised substring check, so ledger entries carry both number forms. Deterministic tests; **the live model loop awaits the maintainer's prod check** (no sandbox provider key). Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) Phase 4. **Next:** remaining §7 families + the §12.1 audit trace.
- **#633** — **BTD6 data-refresh workflow, manual-dispatch only (Lane 5, Q-0049)**: committed `.github/workflows/btd6-data-refresh.yml` — `workflow_dispatch` is the **only** trigger (a `schedule:` needs a new owner ask); clones the dump to `/tmp` (~320 MB, never committed), runs the plan's tested chain (validate-anchors gate → overlay → audit → coverage map; opt-in decode-inventory regen), and opens a **reviewable PR** via a SHA-pinned action — never pushes to main; empty diff → no PR. **Root-cause fix in the same PR:** the decode-inventory generator now emits the `Status:` badge itself (the committed artifact had it hand-added, so any regeneration would have stripped it and reddened CI) — pinned by tests. Plan: [`btd6/btd6-data-refresh-pipeline-plan.md`](btd6/btd6-data-refresh-pipeline-plan.md).
- **#632** — **Adaptive Setup P1B remainder (Lane 2, Q-0045/Q-0036)**: the **governance tier-input path** (`GovernanceContext.member_tier` — declared tier preferred verbatim, role grants skipped, invalid input ignored; the projection's governance axis consumes `AccessContext.member_tier` with the §16.4 simulation label) + the **`help_advertises_locked` drift provider** (advertised-to-baseline = ledger-shown ∧ governance-visible at tier `user`; per-feature warnings for routed-off advertised features; one guild-level finding per guild-wide command-access lock) + the full **Q-0036 denial-copy draft** in `_SAFE_TEXT` (table in the PR body — **not live-wired**; wiring follows the maintainer's markup). 24 new tests; read-only AST invariants green. **Next: P1C** (plan §16.8).
- **#631** — **Vision draft-answers for Q-0038–Q-0042 (Lane 6, Q-0051)**: one concrete proposed answer per product-vision question, appended under each router entry — and the maintainer **marked all five up the same day** (structured choices): server-scoped clans (Q-0038) · cosmetic-only donations, no bot-side billing (Q-0039) · YouTube-first/dual-opt-in/voice-deferred (Q-0041) · staged-Someday website (Q-0042) approved as drafted; **Q-0040 adjusted — the AI dungeon master picks from bounded, hard-capped menus**, not pure narration. Posture decisions only; every lane still needs its own plan + the AI per-exposure lift. Router §21.
- **#620–#630** — **the 2026-06-09 docs/audit/decision burst** (docs-only, batched here to keep this ledger scannable): repo review **#621** + agent-memory-system review; settings-cog audit **#625** (Codex) and help-system audit **#627** (Codex) — sources of scoreboard Lanes 7–8; gate-lifting-interview routing **#622/#623**; mining Workshop+durability **#624** (the one *code* PR — migration 063, Workshop panel, `!repair`/`!craft`/`!quickcraft`; narrated in ▶ lane 1); Lane 1 scaffold+Spotlight **#626** (see below); end-of-day consolidation **#629** + interview-answers routing **#630** (Q-0055–Q-0059, Q-0063–Q-0065). Details: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md) · [`planning/consolidated-productive-session-plan-2026-06-09.md`](planning/consolidated-productive-session-plan-2026-06-09.md).
- **#626** — **`scripts/new_subsystem.py` scaffold + Community Spotlight registration (Lane 1, Q-0025/Q-0044)**: the registration-touch-point checker/scaffolder (verifies all ~9 touch-points incl. the parent hub's `primary_children`; prints paste-ready snippets, edits nothing) and its first consumer — Spotlight registered as a `community`-hub child, help-map §3 banner resolved, `!hub`/`!server` aliases dropped.
- **#619** — **AI tool orchestration — Phase 3 (typed policy storage + resolver + operator UI)**: closes the orchestration foundation. Migration **062** adds a nullable `orchestration_profile` column to `ai_guild_policy` / `ai_channel_policy` / `ai_category_policy`. New `services/ai_orchestration_presets.py` (built-in presets — `compatible_default` reproduces today's behaviour byte-for-byte, plus `balanced_helper` / `btd6_grounded` / `btd6_grounded_strict` / `no_tools`), `services/ai_orchestration_policy.py` (the most-specific-wins resolver — channel → category → guild → default — generation-cached, DB-fault-tolerant, dry-run trace), and `services/ai_orchestration_mutation.py` (the audited write seam: admin gate + built-in-key validation + `bump_generation` + cache-invalidate + `ai.orchestration.*_changed` events). `AIConfigSnapshot` gained a read-only `orchestration` sub-namespace (I-2 preserved + pinned). The resolved policy is wired into `natural_language_stage._invoke_gateway` (toolset narrowing via `build_registry` + `tool_choice`/`tool_budget` on `AIRequest`; **default byte-identical** — every guild that never opens the panel is unchanged). The **Tools & Workflows** AI-panel button (`ai:tools` → `views/ai/tools/`) gives per-scope profile pickers (through the audited seam) + a dry-run analyzer showing the resolved profile, offered/withheld tools with reason codes, and the loop budget. **The maintainer lifted the AI-exposure gate for this operator UI this session** (as with `btd6_round_cash`). ~40 tests + a live DB round-trip + clean boot (migration 062 applies, panel shows `ai:tools`, preview resolves). Binding doc `docs/ai-config-ownership.md` updated (read model / mutation seam / resolved semantics / custom_ids). Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 3 / PR D+E). **Next: Phase 4** (complex BTD6 workflow) + the durable per-decision orchestration audit trace (§12.1, deferred).
- **#618** — **AI tool orchestration — Phase 2 (provider-neutral tool-choice + budgets)**: `core/runtime/ai/contracts.py` gained `ToolRequirementMode` (NONE / AUTO / REQUIRED_ANY / REQUIRED_GROUP / REQUIRED_TOOL), `AIToolChoice`, and `AIToolBudget`, plus `tool_choice`/`tool_budget` fields on `AIRequest`. A shared `ToolLoopState` + `cap_tool_result` (`core/runtime/ai/providers/base.py`) bound the model↔tool loop by hop / call / wall-time / result-size; the **OpenAI and Anthropic** adapters map the five modes onto their native `tool_choice` (`_openai_tool_choice` / `_anthropic_tool_choice` — REQUIRED_* forces a tool on the first hop then relaxes to auto; REQUIRED_GROUP rides the resolver-narrowed set; NONE offers no tools). **Defaults reproduce today's behaviour byte-for-byte** (AUTO + hop-bounded, no other caps) — every existing provider/gateway test stayed green. The gateway's redaction seam now uses `dataclasses.replace`, closing a latent drop-bug class for any future `AIRequest` field. 18 tests (all five modes × both adapters + budget exhaustion + redaction preservation). Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 2 / PR C). **Next: Phase 3** (typed orchestration-policy storage + projection + Tools & Workflows admin UX).
- **#617** / **#615** / **#614** / **#613** — **Community Spotlight (side-lane)**: a live server-activity dashboard — `!spotlight` (panel: XP/coin leaders via `rank_providers`, per-game leaderboards, an EventBus-fed recent-level-ups feed). #613 and #614 merged 19 minutes apart outside the session workflow, then two hotfixes followed: **#615** (file rename → `community_spotlight_cog.py`) and **#617** (nonexistent `utils.logger` import → stdlib logging). Hardened in the 2026-06-09 review session: the inline `xp`-table SQL moved onto the canonical owner (`utils/db/xp.py get_guild_xp_totals` — was the only raw SQL in any cog), the `guild.member_count=None` format crash fixed, and the cog's first tests added. **Since resolved (2026-06-09):** registered as a `community`-hub child via the Q-0025 scaffold (**#626**) and the greedy `!hub`/`!server` aliases dropped — Q-0044 answered *and executed*; the help-map §3 banner is gone.
- **#616** — **AI + BTD6 answerability — Phase 2 (central introspection read model)**: new read-only `services/ai_introspection_service.py` — a side-effect-free composition over the existing AI owners with **audience filtering at construction** (AR-08 tiers): `build_tool_catalog(scope)` (joins the new `ai_tools.all_tool_specs()` + the canonical `ai_tool_catalogue.CATALOGUE`; higher-scope tools are counted, never named), `build_btd6_answerability()` (deterministic fixtures + calculations + the one live domain + explicit unsupported gaps, from `btd6_data_service`), `build_ai_settings_view(guild_id, scope)` (reuses `ai_config_projection_service.build_snapshot`, redacted by tier — provider diagnostics platform-owner-only), and `build_policy_explanation(ctx, scope)` (composes the `ai_natural_language_policy.resolve` dry-run precedence trace + bounded `ai_decision_audit_service` history; trace + cross-user history admin+ only). Added the runtime-independent `ai_tools.all_tool_specs()` accessor (pinned == the catalogue). **No AI exposure, no UI** — those are the gated Phase 3/4; this is the additive read-*model* (the Phase 1A precedent: a deterministic owner ships before its gated exposure). 16 tests + a live smoke (real catalogue/dataset/DB; redaction verified per tier; full CI mirror **8307 passed**). Plan: [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md) Phase 2. **Next: Phase 3** (the scope-filtered self-awareness tools that expose this — gated).
- **#612** — **AI tool orchestration — Phase 1 foundation (canonical catalogue + selector)**: new `services/ai_tool_catalogue.py` — the single source of truth for per-tool selection metadata (`AIToolMetadata` in `core/runtime/ai/contracts.py`: toolsets, grounding domain, freshness, …) with one `CATALOGUE` entry per registered tool, named toolset constants (§5.2), and a deterministic `select_tools` (with `ToolExclusionReason` codes). `build_registry` now consults it and gained optional `enabled_toolsets`/`disabled_tools` params that can only **narrow** the offered set — never grant above `AIScope` (proven live + tested). `BTD6_GROUNDING_TOOL_NAMES` is now **derived** from the catalogue (kills the hand-maintained drift). Default behaviour byte-identical (compatibility). This is the orchestration foundation **AR-10** wanted first; it now houses `btd6_round_cash`. Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 1 / PR A+B). **Next: Phase 2** (neutral tool-choice + budgets).
- **#612** — **AI + BTD6 answerability — Phase 1A + 1B (round-cash, end-to-end)**: **1A** — `btd6_data_service.round_cash(round_start, round_end=None)`, the BTD6-owned, read-only round / **inclusive**-range cash query: the deterministic owner derives the range total (`range_cash`) instead of asking the model to subtract cumulative endpoints; structured per-round / range / cumulative-endpoint / `assumptions` fields + `invalid_range` / `cash_unavailable` refusals (never a fabricated number). **1B** — the read-only **`btd6_round_cash` AI tool** registered in the existing `ai_tools.build_registry` (not a parallel registry) + added to the BTD6 grounding allowlist; the instruction stack now defers range cash to the tool. **The maintainer explicitly lifted the AR-10 orchestration-first sequencing for this one read-only BTD6 tool.** **Owner decision Q-0043: range cash is INCLUSIVE of both endpoints** (r50→r60 = $19,840), correcting the prior exclusive `cumulative(B)−cumulative(A)` in the instruction stack + smoke checklist. Full CI mirror green (8266 passed); arch 0 errors. Plan: [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **Next: Phase 2** (read-only AI introspection read model).
- **#610** — **Mining Character overview (§7.6 profile seed)**: read-only `!character`/`!profile` + a hub Character button (`views/mining/character_panel.py`) that aggregates position, equipped gear + `EffectiveStats`, coins, and inventory net worth from their existing owners — owns no data, grows as game-XP/skills/titles land. The stat-card-first step as an embed (PIL later). Tests + clean boot.
- **#609** — **Mining sell-ore / buy-gear market (Wave 1 economy loop)**: new `cogs/mining/market.py` (pure sell/buy prices — sell reuses `items.item_value`, the gear shop is a tunable coin catalogue) + `views/mining/market_panel.py` (Sell-All button + buy-gear select) + a hub Market button + `!sell`/`!sellall`/`!buy`/`!market`. Coins move **only** through the audited `economy_service` (`credit`/`debit`); inventory stays direct-lane; combat gear added to the item taxonomy so it's non-sellable + grouped correctly. Closes the mine→sell→upgrade→descend loop. 28 tests + a **live money round-trip** (sell→+coins, buy→−coins+item, insufficient-funds→rejected, coins safe).
- **#608** — **Mining combat gear → deathmatch (Wave 1 cross-game stat seam)**: promoted the pure gear→stats model from `cogs/mining/equipment.py` to **`utils/equipment.py`** (a shared, stdlib-only seam — brainstorm §7.4, extracted now that a 2nd game needed it; zero behaviour change); added **weapon/armor slots + combat gear** (`sword`/`iron sword`/`shield`/`armor` → `damage`/`defense`/`max_health`, craftable via recipes); and made **deathmatch duels read each fighter's `EffectiveStats`** (HP/attack/flat-reduction from equipped gear — a small, fair edge, tunable in `_GEAR`). 30+ new/updated tests; live-verified (clean boot, all cogs load, 0 errors).
- **#607** — **Mining "The Descent" (Wave 1 persistent depth)**: migration `061_mining_player_state` + direct-lane owner `utils/db/games/mining_player_state.py` (`get_depth`/`set_depth`) + pure `cogs/mining/world.py` (depth↔biome + descent gating, deriving one canonical `BIOME_ORDER` shared with `exploration.py`). `!explore` and `!mine` now resolve the player's **real biome** (deeper = richer ore + light-gated deep finds) instead of always Surface; new `!descend`/`!ascend` commands + hub Descend/Ascend buttons, gated by the equipped light's `depth_access` (torch→Cavern, lantern→Deep; **persistent, not consumed** — descent-gating decision in brainstorm §6.8, *flagged for owner confirm*). 31 new/updated mining tests; live-verified (migration 061 applies, `mining_player_state` table correct, MiningCog loads, 0 boot errors).
- **#606** — Mining **character-platform foundation** (brainstorm §7 vision + Wave 0/equipment): `!explore` wired to the loadout/depth engine, typed Inventory panel + net worth, the **equipment seam** (migration 060 `mining_equipment` + the `EffectiveStats` gear→stats read model + `!equip`/`!unequip`/`!gear`), and exploration reading equipped gear's stats. The reusable cross-game stat block the Descent (above) builds on; mining writes are intentional **direct-lane game state**, not an audited-service gap.
- **#594** — **SuperBot Context Compiler**: `docs/agent/index.yml` (7-subsystem manifest, curated for every folio + binding docs + source roots + do-not-create warnings + gates + verification), `tools/agent_context/build_pack.py` + `validate_pack.py`, 7 generated context packs in `docs/agent/generated/`, 13 pinning tests in `tests/unit/docs/test_agent_context_index.py`, `docs/agent/README.md`, `.claude/rules/` path-scoped Claude guidance files (mutation-and-db, discord-views, context-compiler), and updates to `docs/AGENT_ORIENTATION.md` + `docs/repo-navigation-map.md`.
- **#591** — Adaptive Setup **P0C groundwork**: the role-threshold direct-write drift-fence invariant (`tests/unit/invariants/test_no_direct_role_threshold_writes.py`) + a turn-key swap recipe (planning §16.5) + §16.8 plan-review refinements for the next agent. (The conversion itself shipped next; see ▶ Next action.)
- **#589** — Adaptive Setup **P1A**: the **Access Map projection service** (`services/access_projection.py`) — a side-effect-free composed read model (command-access + routing + governance + help axes, reusing existing owners) with 19 tests; no UI, no persistence.
- **#588** — Adaptive Setup **Q-0026 identity repair** (`cog_name_to_subsystem` CamelCase → snake_case; registry key `server_management`; latent `proof_channel`/`four_twenty` collapse fixed, regression-pinned) + Phase 0 **direct-vs-draft** and **access read-model** contracts (planning §16, `ownership.md`).
- **#585** — captured and routed owner decisions Q-0017–Q-0027 for the Adaptive Setup/Access/Routine planning lane.
- **#584** — merged the unified Server Management Hub as a first-class subsystem and completed the non-AI server-management lane.
- **#582** — server-management **PR13 deterministic slice**: `services/setup_role_templates.py` (built-in permission-free role bundles + pure `plan_template`) + the audited **`create_managed_role`** op-kind (routes through `RoleLifecycleService`, optional time/XP tier companion) + a **Role templates** setup section. Fixed a **latent PR11 regression** (the roles section's `set_role_threshold` op was never added to the DB op-kind gate/CHECK → couldn't stage): **migration 059** + a dispatcher↔gate↔CHECK drift-guard test close it. The **PR13 AI generation layer** + PR14 (hub) remained queued. (PR12 setup diagnostics & repair shipped 2026-06-07.)
- **#581** — idea-backlog grooming demo (Q-0015): promoted the mining-brainstorm `!explore` wiring into a structured plan + a `docs/roadmap.md` horizon; the standing end-of-session secondary task in action.
- **#570** — server-management **PR11** (moderation + roles setup sections) + workflow tooling + ecosystem docs (owner decision **Q-0008**: Moderation + Roles now, Governance deferred). The moderation section stages `set_setting` drafts for the PR10 knobs; the roles section adds the `set_role_threshold` op-kind for time/XP auto-role tiers. Setup diagnostics & repair (PR12) builds on top.
- **#567** — server-management **PR10 fourth slice**: optional post-kick/ban **message cleanup** (`post_action_cleanup`: none/kick/ban/both up to `post_action_cleanup_limit`, **default OFF**), owned at the `moderation_service` kick/ban seam and *requested from* `services/history_cleanup.py` (new author-scoped plan + a shared `apply_history_cleanup_plan` extracted from `!cleanuphistory` — one delete path). Best-effort: a blocked sweep never undoes the action.
- **#566** (merged) — **cross-area implementation roadmap** (`docs/roadmap.md`): the one by-area "what's planned, in what order" index (relative Now/Next/Later/Someday horizons + gates, not dates), linking each authoritative plan + folio, with a clearly-marked not-approved ideas section. Its AI section defers to the AI roadmap. Re-badged two mis-badged historical plans (`phase_2b_bindings_plan`, BTD6 extraction). Wired into `current-state` + `AGENT_ORIENTATION`.
- **#565** (Codex, merged) — source-verified **AI roadmap** (`docs/planning/ai-roadmap-2026-06-07.md`, Phase 0–11) + a 10-question batch. Opus-reviewed (sound; read-only boundary preserved). Owner answers (router §18): **AR-10** first Opus target = lock the orchestration foundation; **AR-08** tiered audience; **AR-09** explanation-only now. AR-01–07 hold at safe defaults until their lanes activate.
- **#564** — docs reachability cleanup: consolidated the 14-file BTD6 doc island into `docs/btd6/` behind the folio; archived the retired 2026-06 planning/audit burst into `docs/archive/`; corrected `AGENT_ORIENTATION`'s stale self-count and wired the orphaned `docs/context-map-tooling.md`. Added a **hard reachability gate** to `scripts/check_docs.py` (an unreachable doc fails CI unless badged `historical`/`archive`).
- **#563** — owner-workflow mapping: split the #562 capture into `docs/owner/maintainer-working-profile.md` (the *person*) + `docs/owner/ai-project-workflow.md` (the multi-agent pipeline, per-project roles, handoff templates, idea-state vocabulary); de-duplicated the restated rules to links; routed the **"a new idea is not a new priority"** rule into `.claude/CLAUDE.md` + `docs/collaboration-model.md`. Docs-only.
- **#558** — server-management **PR10 third slice**: configurable **warn escalation** owned at the `moderation_service` seam: `warn_escalation_action` (timeout/kick/ban/none at `warn_threshold`), `warn` returns a `WarnOutcome`, escalation deduplicated out of the cog + panel modal. Scalar/KV, no migration, behaviour-preserving by default.
- **#556** — server-management **PR10 second slice**: `require_reason` enforcement at the `moderation_service` seam (warn/kick/ban; timeout exempt) + a read-only bot-readiness diagnostics line on the mod panel (`utils/moderation_feasibility.py`).
- **#555** — server-management **PR10 first slice**: config-backed moderation behaviour (`moderation_config` policy + `dm_on_action` / `dm_template` / `ban_delete_message_days` / `max_timeout_minutes`) applied at the `moderation_service` mutation seam; behaviour-preserving by default.
- **#554** — implementation-readiness reconciliation: source-grounded readiness audit (`docs/audits/implementation-readiness-review-2026-06-06.md`) + reclassified stale Phase-2 / platform-consistency status cells so they aren't mistaken for current work queues; docs-only.
- **#553** — consistency-warning presentation fix (the health snapshot no longer flags benign `SKIPPED` consistency sections — bindings-from-DM / no-backfill-rows — as "needs attention") + role-hierarchy tiebreak (`role_feasibility` / `role_automation` compare hierarchy by (position, id) like discord.py, not raw `position`).
- **#552** — session journal made lean + self-maintaining: archive split (`.session-journal-archive.md`), a Quick reference, Rules regrouped, and a "tidy-each-session" protocol step (mirrored in `.claude/CLAUDE.md`); docs-only.
- **#551** — role-automation degradation fix: `role_automation.apply` preflight-guards at the mutation seam (via `utils.role_feasibility`), classifies failures, and keeps predictable Manage-Roles/hierarchy blockers off the ERROR-only health surface; operator + role-Diagnostics surfaces show the cause.
- **#550** — collaboration-model doc + truth-layer restructure (goal-first, prompts-as-guidance); docs-only.
- **#549** — server-management cleanup PR8+PR9: `policy_version` marker, presets builder + dry-run + panel diagnostics, and the guild-default `scope_id=0` no-op fix.
- **#548** — closed the migration-`057` persistence/dedupe/retention integration-test gap (test-only).
- **#546** — canonical subsystem folios (health/diagnostics, server-mgmt, settings, BTD6, games, media).
- **#544** — freshness-oriented docs route, lifecycle labels, ideas area, and subsystem-folio model.
- **#543** — boot / test-bot capability doc correction.
- **#542** — docs reconciled to shipped bot-awareness status.
- **#541** — bot-awareness **PR4–PR6**: grouped recent-error findings (opt-in),
  owner-gated `diagnostics_health_snapshot` AI tool (D1 resolved), persistent
  operational-health findings (migration `057`).
- **#539** — AI extra-tool capability **ideas backlog** (capture only, not approved work).
- **#537** — bot-awareness **PR1–PR3**: health contracts + aggregator, `!platform
  health`, startup-health snapshot.
- **#535** — back-to-Help navigation fix; stability baseline accepted.
