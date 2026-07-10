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

- **#1802 · #1804 (2026-07-07, S3 rebuild — program founding briefs: website-design + kit-lab)** —
  two of the Q-0252 three-program-sessions founding artifacts closed out: the **website-design brief**
  (#1802 — verification record + proof screenshots, docs homing, card flipped green) and the **kit-lab
  founding brief** (#1804). Part of the [three-program-sessions launch](planning/program-three-sessions-launch-index-2026-07-07.md).
- **#1801 · #1803 (2026-07-07, workflow — thirty-seventh Q-0107 reconciliation pass, band-#1800)** —
  the 37th docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-07-07-band1800.md)): reconciled band #1771–#1800,
  trimmed Recently-shipped to 20, closed the 5 consumed Codex Gate-V evidence PRs, confirmed the
  control-plane, refreshed the dashboard export, reset the marker #1770 → #1800.
- **#1805 · #1815 · #1824 (2026-07-07/08, docs — dashboard-data refreshes, Q-0167)** —
  three per-source-merge refreshes keeping the committed `dashboard/data/dashboard.json` export fresh as
  the coordinator-kickoff / EAP-evaluation arc landed.
- **#1791 · #1792 · #1793 · #1794 · #1795 · #1796 · #1797 · #1798 (2026-07-07, S3 rebuild — idea-consolidation → multi-repo program founding + owner rulings Q-0243…Q-0252)** —
  the pre-program-launch consolidation session. **#1791** folded the day's four owner captures + hardened
  the §3.C risks into the canonical-plan machinery (§11b amendments A-12…A-20; registry mints R-16/R-17/P-5).
  Owner rulings: **#1792** (Q-0243 pricing-by-simulation + Q-0244 slash verification inherits prefix, never a
  blocker), **#1796** (Q-0250 trading repo stocks-first — US large-cap tech, point-in-time universe, API-broker
  paper lane, DEGIRO manual venue), **#1797** (Q-0251 trading operating model — decision-ledger mock trades,
  sniper bucket, 3-way hybrid allocator). **#1794** captured the **multi-repo program** (repo-start mechanics ·
  kit self-improvement lab · trading research repo); **#1795** the steps-6–8 kickoff-readiness brief
  (Q-0247/Q-0248/Q-0249); **#1798** (Q-0252) prepared the **three program sessions** — kit-lab + trading
  founding briefs + the [launch index](planning/program-three-sessions-launch-index-2026-07-07.md). #1793 =
  format/lint + env-var-artifact regen for `EXTRA_OWNER_USER_IDS`.
- **#1784 · #1785 · #1786 · #1787 · #1788 · #1789 · #1790 (2026-07-07, S3 rebuild-plan review + owner-idea capture, incl. an S1 automod runtime fix #1789)** —
  an owner-review session over the rebuild plan that captured rulings/ideas and shipped one runtime fix:
  **#1785** recorded the owner ruling on auto-collect gating (coins+XP unlock), **#1786** three
  foundational/feature gaps, **#1787** the automod duplicate-content + cross-channel spam gaps; **#1789** then
  *shipped* the **S1 automod fix** (cross-channel spam-evasion + duplicate-content detection —
  `services/automod_service.py`/`automod_config.py` + `cogs/automod/schemas.py` + 3 test files; a genuine
  `disbot/` runtime change). **#1788/#1790** = the Fable-5 ultracode brief to fold the day's ideas into the
  plan (revised once #1789 shipped — the automod finding is shipped-not-a-fold candidate).
- **#1778 · #1783 (2026-07-07, S3 rebuild — the FINAL rebuild-plan review session)** —
  the final review over the frozen canonical plan (verdict: **plan ready**; §11 amendments folded; readiness
  scored — [report](planning/rebuild-final-review-report-2026-07-07.md)), which also produced the §6.3
  live-bot runtime fixes **#1781/#1782** (listed below). **#1783** hardened the substrate-kit so **adopt
  installs the enforcement** — the forcing functions ship with the kit rather than as a separate step.
- **#1776 · #1777 (2026-07-07, S3 rebuild / workflow — Projects-EAP coordinator + Q-0241 never-wait autonomy + Fable-5 final-review brief)** —
  **#1776** adopted **Claude Code Projects (EAP) as the rebuild coordinator** and recorded **Q-0241** (retire
  the owner gates as blockers — silence = consent, live-test-in-server, never-wait; the destructive tier stays
  reversible + vetoable — canonical in [`owner/agent-decision-authority.md`](owner/agent-decision-authority.md)).
  **#1777** shipped the **Fable-5 ultracode brief + prompt** for the final rebuild-plan review and the
  Projects-EAP repo prep.
- **#1775 (2026-07-07, S3 rebuild — Phase-2.5 A/B run + verdict (G2))** —
  executed the runnable Phase-2.5 package (the two-implementation A/B build + verdict, owner briefing homed):
  verdict **FAIL as-tested** → the adopt-render fix + re-run pair, folded into the final-review session #1778;
  plus a grimp-contract fix. Ran without waiting on the owner (Q-0241 gate retirement).
- **#1773 · #1774 · #1779 · #1780 · #1799 (2026-07-06/07, docs — dashboard-data refreshes, Q-0167)** —
  five per-source-merge refreshes keeping the committed `dashboard/data/dashboard.json` export fresh as the
  final-review / plan-review / consolidation arc landed.
- **#1772 (2026-07-06, workflow — thirty-sixth Q-0107 reconciliation pass, band-#1770)** —
  the 36th docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-07-06-band1770.md)): reconciled band #1741–#1770, trimmed
  Recently-shipped to 20, flagged the 5 Codex Gate-V evidence PRs for merge-or-close + captured the
  disposition-guard idea, confirmed the control-plane, refreshed the dashboard export, reset the marker
  #1740 → #1770.
- **#1781 · #1782 (2026-07-07, S1 runtime — the FINAL-REVIEW §6.3 live-bot fixes, shipped from the rebuild final-review session #1778)** —
  **#1781** closed the three unguarded settlement paths as one class: the Gate-V-live-confirmed
  **deathmatch `_DuelView` double-write** (SettleOnceMixin retrofit mirroring the bot-duel sibling),
  the **blackjack FREE-tournament double-pay** (claim past the all-finished check; the free leg has
  no escrow rows so the claim is its only guard), and a **third instance found during verification —
  the RPS free-tournament payout race** (per-tournament claim via the new
  `SettleOnceMixin.rearm_settlement()` seam); `check_consistency` **Rule 6 widened** (cogs/ root +
  `payout_tournament`/`update_leaderboard` sinks) so the checker now catches this non-adopter class;
  8 concurrency + 4 checker regressions. **#1782** wired the ready-but-unwired
  `economy_service.transfer()` to **`!pay`/`!transfer`** (NOT `give` — banned token Q-0211), guard
  rails + sibling embed idiom + regenerated command-surface artifacts, **live-exercised against real
  local Postgres** (exact balances, exactly 2 audit rows). Both merged→deployed same day. Full
  context: the [final-review report](planning/rebuild-final-review-report-2026-07-07.md).
- **#1768 · #1769 · #1770 (2026-07-06, S3 rebuild — foundational consolidation → ONE canonical plan (Fable 5) + Q-0240 decide-and-flag)** —
  the band's headline: the pre-Phase-B consolidation of the scattered rebuild plan into a single
  correctly-layered source of truth, launched under Fable 5 / Ultracode. **#1768** shipped the **Fable 5
  Ultracode launch brief** (finalize the new-repo-start method); **#1769** shipped the **Q-0240
  decide-and-flag decision model** (new durable doc [`owner/agent-decision-authority.md`](owner/agent-decision-authority.md) —
  agents decide reversible-until-a-gate calls themselves with recommend+rationale+flag rather than
  routing them up; the safety brake reframed so only *executing* something irreversible before the gate
  stops-and-waits) + the surgical `.claude/CLAUDE.md` Act-vs-ask clarification + the Fable brief revision
  folding in the decide-and-flag model and the foundational-completeness scope; **#1770** executed the
  consolidation via a 7-lane Ultracode source-verification fan-out → [`planning/rebuild-canonical-plan-2026-07-06.md`](planning/rebuild-canonical-plan-2026-07-06.md)
  (corrected foundational taxonomy: **K10 = AI-invocation kernel** with a domain-registered task registry
  replacing the `AITask` enum + the grounded-answer engine hoisted; **automation = the K5+K9+K7 spread**,
  no new band; **verification = a defined layer V** with a named build step; settings-engine /
  panel-runtime / findings-engine landing steps added) plus the test-guild design + runnable Phase-2.5
  package. (Ledger drift caught here 2026-07-06: the Gate-0 `tools/check_amendments.py` enforcer named in
  the #1716 entry was never shipped — the canonical plan's §5 step 3 builds it.)
- **#1750 · #1751 · #1756 · #1757 · #1759 · #1767 (2026-07-06, S3 rebuild — Gate V verification-fleet pass (Arms A–D + Codex + synthesis), Q-0234)** —
  the multi-agent verification-fleet pass between Phase A and Phase B, over the frozen rebuild plan. **#1750**
  documented the **verification-fleet launch pad** (corrected review prompts, multi-Codex arm, dedicated
  live-testing arm); **#1751** ran **Arm D — the empirical live-testing evidence pack** ([`planning/LIVE-VERIFIED-EVIDENCE-PACK.md`](planning/LIVE-VERIFIED-EVIDENCE-PACK.md),
  exercising every shared primitive incl. the PvP wager engine service-layer against the real test guild +
  throwaway Postgres, never production); **#1756** documented the **verified Codex C2–C5 + Agent-Mode
  evidence corrections**; **#1757** shipped **Arm A** (architecture & core-readiness review); **#1759**
  took the fleet to **COMPLETE** (verify C1 re-run + Arm A Ultracode review — all arms sound); **#1767**
  reconciled it into the **final synthesis (Arm Σ)** ([`analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md`](analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md)):
  **Gate V COMPLETE → proceed to Phase-B per-step planning under Sequence C** (the frozen L3→L4/L5 games
  edge is fabricated — games can defer; audited-write atomicity is a systemic contract-freeze not a live
  defect; K7's urgency is borrowed). **Readiness note (updated 2026-07-07):** Q-0241 (#1776) retired both
  owner gates as blockers (silence=consent; live-test-in-server), and Phase-2.5 has since RUN (#1775,
  verdict FAIL as-tested — adopt-render fix + one re-run pair remain). *(The five raw Codex sub-report PRs remain OPEN as the
  evidence layer — C1 #1758 + C2–C5 #1752/#1753/#1754/#1755 — their verified corrections are folded into
  the #1756/#1759 docs; disposition below.)*
- **#1743 · #1744 · #1745 · #1747 · #1748 (2026-07-05/06, S5/CI — CI-followups arc: watchdogs + AST guards + ruff, no `disbot/` runtime)** —
  the completion of the CI-setup follow-ups handoff ([`planning/ci-followups-handoff-2026-07-05.md`](planning/ci-followups-handoff-2026-07-05.md)),
  all tooling/CI (no runtime): **#1743** fixed the `check_ci_coverage` self-silencing watchdog + homed the
  handoff; **#1744** added the **CodeQL stuck-scan watchdog** (`check_codeql_coverage.py`) + the shared
  idempotent `scripts/lib/owner_alert.py` issue opener (A10, Q-0089) + granted `issues: write`; **#1745**
  executed the **ruff migration (A3)** — ruff replaces black + isort, taking the python merge gate from
  **5 tools → 3** and removing two-thirds of the formatter pin-drift surface (the #1074/#1315/#1556 drift
  class); **#1747** added the **`check_audit_seam`** AST guard (per-function audit-seam reachability, the
  #1728 save-fixes bug class as a CI signal; advisory); **#1748** completed the arc with the 2nd AST guard
  **`check_deferred_recovery`** (deferred-mutation-without-persisted-deadline) + tail cleanup (dropped
  dormant `check_doc_freshness`, wired the slug-unique advisory). All advisory/`continue-on-error` with
  triaged allowlists + gate-bites meta-tests.
- **#1746 · #1749 · #1760 (2026-07-06, docs — dashboard-data refreshes, Q-0167)** —
  three per-source-merge **dashboard-data refreshes** keeping the committed `dashboard/data/dashboard.json`
  export fresh as the CI-arc + Gate V + consolidation work landed.
- **#1713 · #1716 · #1725 · #1735 (2026-07-04/05, S3 rebuild — Gate-0 grammar-freeze → Phase-B L0 build-order + Stage-2 subsystem walk)** —
  the Phase-A/B bridge after the foundational-design session (#1708). The **Gate-0 grammar-freeze**
  (#1713 prep brief → #1716 consolidation, docs/spec only — the fresh-repo `sb/` package does not
  exist yet): the 14 shipped design specs folded into one authoritative **frozen L0 manifest-grammar**,
  an **amendment registry** (`rebuild-amendments.yml`; its named enforcer `tools/check_amendments.py`
  was NOT shipped — ledger drift caught 2026-07-06 (#1770), the canonical plan's §5 step 3 builds it;
  G-9…G-24), closed pending
  cross-spec wiring (`ActorRef.member_tier`/RC-12, spec-02 absorbing 04's authority contracts,
  `WorkflowContext.test_mode`, the `ChannelEmitter` egress port), register resolution (19
  RATIFY-DEFAULT rows frozen · 12 OWNER-ONLY + L-21 rendered into an owner-decision packet), the L-24
  presentation riders, and the **16-step Phase-B L0 build-order** (S0–S15) — under
  `analysis/rebuild-discovery/foundations/gate-0/`. The owner-led **Stage-2 subsystem walk** (#1725 —
  `planning/rebuild-stage2-subsystem-walk-2026-07-05.md`, a 52-row index mapping all 58 live
  `disbot/cogs/` extensions to 43 BUILD-PLAN + 9 ADD rows, an explicit owner disposition per
  command/listener/task/panel, 4 reconciliation findings). Plus #1735 — next-session prep (bank the
  save-fixes findings + assess substrate-kit priority).
- **#1728 · #1730 (2026-07-05, S1 runtime — Stage-2 "save-fixes" 8 current-bot bug fixes + CodeQL log-injection hardening)** —
  the **only runtime change** in the band: the Stage-2 walk's **Class-A backport** (#1728 — 8
  owner-decided "fix now" bugs that harden the *current* production bot and lock accepted rebuild
  contracts into executable form, deliberately refusing Class-C new-design items): AI-scalar → typed-policy
  projection made transactional/non-silent · `bot_spam`→`bot-spam` dead-greeting typo · audit trail on
  5 high-privilege admin mutations (cog load/unload/reload · restart · log-level) · `/moderation` now
  honours the configured `moderator_role` · raid-lockdown slowmode + cleanup toggles routed through the
  audited `ChannelLifecycleService` seam · 3 missing role guild-teardown tables cleaned on guild-leave ·
  proof-channel unlock deadline persisted + boot reconcile sweep (restart-safe); plus zero-risk dead-code
  deletions + §7.4 unit coverage. #1730 — CodeQL follow-up hardening the AI-projection drift log against
  log injection.
- **#1736 · #1737 · #1739 (2026-07-05, S5/CI — CI-setup redesign: brief → divergence analysis → Phase-A hard merge gates)** —
  the CI-setup redesign arc (#1736 brief → #1737 best-possible-CI-for-current-bot + fresh-repo divergence
  analysis, `planning/ci-setup-redesign-2026-07-05.md`, shipping `check_workflow_concurrency` advisory).
  **#1739 Phase-A** promoted three should-gate-but-didn't invariants to **hard merge gates** by adding
  them to the already-required `code-quality` context (reversible, no branch-protection change):
  `check_architecture --mode strict` (layer boundaries — previously only a local Stop hook),
  `check_tool_pins` (formatter-pin drift, reached `main` in #1315), `check_workflow_concurrency` (the
  #1275 head-run-cancel race) + flipped `codeql.yml` to `cancel-in-progress: false`; each verified green
  on `main` first. Remainder proposed as router Q-0238(C)/Q-0239.
- **#1712 · #1719 (2026-07-04, workflow — 34th Q-0107 reconciliation pass + open-PR review/merge sweep)** —
  the **thirty-fourth Q-0107 docs-only reconciliation pass** (band-#1710,
  [pass record](planning/reconciliation-pass-2026-07-04-band1710.md), #1712) and the **open-PR review +
  merge sweep** (#1719) that dispositioned the backlog of Codex review docs #1695–#1699 + the dependabot
  batch #1555…#1560/#1720 onto `main`.
- **#1714 · #1715 · #1717 · #1718 · #1722 · #1723 · #1724 · #1726 · #1727 · #1729 · #1731 · #1732 · #1733 · #1734 · #1738 · #1740 (2026-07-04/06, docs — dashboard-data refreshes, Q-0167)** —
  sixteen per-source-merge **dashboard-data refreshes** keeping the committed `dashboard/data/dashboard.json`
  export fresh as the S3 rebuild Gate-0/Stage-2 arc, the save-fixes runtime change, and the CI redesign landed.
- **#1695 · #1696 · #1697 · #1698 · #1699 (2026-07-03/04, S3 rebuild — five Codex rebuild-planning reviews, merged via the open-PR sweep #1719)** —
  the owner-launched Codex review fan-out over the 2026-07-03 Phase-A corpus, merged after
  verification + fixes (badge `review`→`audit`, reachability links, and a **post-review status note**
  on each — all five were written *before* the design bridge #1708 and the Gate-0 freeze #1716, so
  their still-open items must be reconciled against the Gate-0 packet before acting): the
  **planning sanity review** (#1695 — gate/phase map verified, no blocking inconsistency, stale-claim
  table); the **decision-log consistency review** (#1696 — conflict table incl. authority-vocabulary /
  C-1-status / preset-semantics rows, missing-durable-home + vocabulary-normalization tables, 10 owner
  questions); the **foundational-mechanics ultracode review** (#1697 — Prompt A trust **high**, 10
  source-verified samples); the **Stage-2 readiness review** (#1698 — subsystem-walk contract +
  template, normalized verdict vocabulary, lane split); and the **verification review** (#1699 —
  10 missing oracle/checker classes, 6 acceptance-criteria rewrites, block-Phase-B checker-spec list).
  The stale June **unfinished-work audit #1509** (already harvested by #1510; its top finding since
  resolved) was **closed with reason**, per the band-#1530 pass disposition.
- **#1555 · #1556 · #1557 · #1558 · #1559 · #1560 · #1720 (2026-07-04, deps — dependabot batch, merged via the open-PR sweep #1719)** —
  the six stale (5-day-old) dependabot PRs dispositioned: fastapi 0.138.2 → **0.139.0** + uvicorn
  **0.50** (dashboard + botsite), openai ≥2.44, **Pillow 11 → 12** (major; CI-proven on the bumped
  install + render tests re-verified locally on 12.3 against today's main), asyncpg ≥0.31,
  prometheus-client ≥0.25, grimp 3.15. #1556 was fixed rather than rubber-stamped: dependabot had
  bumped `requirements-dev.txt`'s tool pins alone (the #1074/#1315 drift class the `tool-pins` check
  caught), so the sweep did the deliberate **three-place toolchain bump** — **ruff 0.15.20 · pytest
  9.1.1 · pytest-xdist 3.8.0** aligned across `code-quality.yml` / `requirements-dev.txt` /
  `.pre-commit-config.yaml` — verified by the full local CI mirror (14 059 passed) + one ERA001
  prose-comment fix in `botsite/app.py`. Conflict-rotted #1560 and the recreated group PR #1720
  were conflict-resolved on-branch and merged on green.
- **#1689 · #1690 · #1691 · #1693 · #1700 · #1701 · #1703 · #1704 · #1705 (2026-07-03, S3 rebuild — foundations audit → Fable-5 judgment → design-prep, Q-0236/Q-0237)** —
  the pre-Phase-B foundations arc that dominated the band: the **engine-room audit** (PROMPT A,
  #1690 — a 75-agent ultracode discovery+audit of the runtime/logic foundation, 18 → 35 mechanics,
  each with a how-now (`file:line`) + 2–3 alternatives + pressure-test, adversarially verified vs
  shipped source per Q-0120) and the **surface + proving audit** (PROMPT B, #1691 — 46
  presentation/UX + verification mechanics); the **two confirmed prod loss-path fixes** the
  engine-room audit surfaced (#1693 — blackjack tournament entry-fee forfeit on a VERSION bump +
  XP double-fire during the deploy-handoff overlap, the band's only runtime change); the **Fable-5
  capstone final judgment** over all 2026-07-03 Phase-A work (#1700 prepare prompt → #1701 verdict:
  *engine-rich · grammar-thin · oracle-empty*), which produced the **7 Tier-1 owner decisions**
  (#1703, Q-0237) and captured **2 owner ideas** (#1704 — in-server release→test→verify loop +
  websites cutover-role); plus the prep of the **foundational-design opus ultracode prompt** (#1705,
  now executing in #1708) and ultracode quick-launch prompts (#1689).
- **#1682 (2026-07-03, workflow — thirty-third Q-0107 reconciliation pass, band-#1680)** — the
  thirty-third Q-0107 docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-07-03-band1680.md)): reconciled band
  #1651–#1680, trimmed Recently-shipped to 20, disposed 7 open PRs, confirmed the control-plane,
  refreshed the dashboard export, reset the marker #1650 → #1680.
- **#1692 · #1694 · #1702 · #1706 · #1707 · #1709 · #1710 (2026-07-03/04, docs — dashboard-data refreshes, Q-0167)** —
  seven per-source-merge **dashboard-data refreshes** keeping the committed `dashboard/data/dashboard.json`
  export fresh as the S3 rebuild foundations arc landed.
- **#1688 (2026-07-03, S3 rebuild — two parallel ultracode prompts prepared, Q-0236)** —
  owner-directed preparation (not launched): [two paste-ready ultracode session
  prompts](planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md) to brainstorm +
  audit every foundational mechanic (use-now + could-use) against today's decisions — session A =
  runtime/logic engine room, session B = presentation/UX + verification — disjoint scopes,
  rubric-scored issues ledgers, each its own claim + PR. Owner sends them in parallel; survivors
  feed the Stage-2 walk / Gate-V fleet.
- **#1687 (2026-07-03, S3 rebuild — unified layout-success simulator idea, Q-0235)** —
  captured the idea to unify the 5 bespoke UX-layout sims into one **instruction-driven
  layout-success simulator** (deterministic + AI user models; "create roles" → does a user model
  reach the right node?) that quantifies the "self-explanatory" half of the Q-0234 oracle and is
  the mechanism behind "sim optimizes arrangement" (Q-0230); sim defines settings bot-wide, live
  co-test is the final review.
- **#1686 (2026-07-03, S3 rebuild — new-feature oracle + verification-fleet gate + repo-as-artifact strategy, Q-0234)** —
  resolved the rubric's class-8 verification hole: the correctness oracle = parity goldens (ported) +
  **competitor-benchmark & live co-test** ("works · logical · self-explanatory", reusing the Q-0222
  `verified_live` sign-off) for new features. Recorded **Gate V** (a multi-agent verification-fleet
  pass over the finished plan, using the ten-class rubric as its shared lens) between Phase A and
  Phase B, and the **migration-as-its-own-plan / repo-as-artifact** framing (current repo = what/why/
  how artifact; new repo = clean source of truth) in the phase sequence.
- **#1685 (2026-07-03, S3 rebuild — the critical-review rubric, Q-0233)** —
  owner-directed [reusable review lens](planning/rebuild-critical-review-rubric-2026-07-03.md): the
  ten gap-classes caught reviewing the rebuild plan this session (dependency-order inversion,
  forgotten capability, thin step, stale un-anchored claim, fragmentation, under-generalization,
  missing standard, verification hole, UX-contract gap, naming/collision) turned into probing
  questions with mechanization tags — run against every subsystem in the Stage-2 walk + every
  Phase-B plan (it *is* the adversarial-completeness checklist). Mechanizable classes routed as a
  [checker backlog](ideas/rebuild-critical-review-checkers-2026-07-03.md).
- **#1684 (2026-07-03, S3 rebuild — Phase-A hub topology + navigation contract + interface presets, Q-0230…Q-0232)** —
  owner-live [hub/navigation decisions log](planning/rebuild-hub-navigation-presets-2026-07-03.md):
  one **unified help hub** (admin a permission-gated node + `!admin` direct-open, re-checked at
  click time); the **navigation contract** (Back+Home injected into every rendered state, every
  node directly openable by command, **persistent restart-safe panels** that also survive the
  merge=deploy redeploys); and **per-guild interface presets** with live preview — verified as an
  existing-but-fragmented surface (setup preset_select + help overlay editor + ~7 preset impls) to
  be improved + centralized onto one preset/template primitive (C-3). Open: preset exclusion =
  hide-vs-disable.
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
- **#1573 · #1577 · #1582 (2026-06-30, bot-owner platform-admin override)** — full bot-config authority
  in any guild for the bot owner (#1573), a completeness follow-on extending the override to view gates +
  admin command decorators (#1577), and an ephemeral persistent-panel ownership **fail-close** fix (#1582).
  Follows the Q-0211 `give`-collision prod hotfix from the prior band.
- **#1565 · #1566 · #1568 · #1575 · #1588 (2026-06-29/30, S1 feature-completion certification deepening — Q-0209)** —
  cert sync + S1-bot de-stale (#1565); cleanup **history content-type/age filters** + cert (#1566);
  **counters completion** (presets + slash + channel-type/integration tests, #1568) and a per-guild
  loop-backoff punch (#1575); and the **spam-duplicate window** promoted to a real per-guild setting
  (cleanup cert punch #4, #1588). *(Sibling to the already-listed #1561 operator-command-gaps entry below.)*
- **#1570 · #1571 · #1585 · #1579 · #1581 (2026-06-30, reaction-roles + fishing + welcome depth)** —
  role-menu live **signup counts** (migration 103) on the reaction-roles overhaul (#1570/#1571); the
  fishing **rod-recipe browser** (#1585); **welcome opt-in DM greeting on join** (completion punch #2,
  #1579) + the age-gate/delete-after close-out (#1581).
- **#1569 · #1574 · #1584 · #1586 (2026-06-30, workflow / orientation system)** — the AI answer-storage /
  review-backlog loop + a `check_quality` **artifact-freshness guard** (#1569/#1574); a journal ruff-scope
  rule (#1584); and the **orientation-cost-reduction plan** (CLAUDE.md + router conciseness, #1586).
- **#1572 · #1578 (2026-06-30, BTD6)** — captured a prod **DDT-confabulation finding** into the regression
  corpus from the review-log export (#1572); BTD6 **track lengths** (Red Bloon Seconds) + estimator
  escape-margin (#1578).
- **#1589 · #1590 (2026-06-30, owner-vision capture — fresh-rebuild + Fable 5)** — captured the maintainer's
  **fresh-rebuild vision** + verified Fable 5 research (#1589) with two maintainer fact-corrections folded
  in (#1590). **Idea-stage, not approved** — gated on Fable 5 (withdrawn since 2026-06-12) + the owner's
  keep/change spec + a multi-agent planning sequence; **re-elevates the AI-memory substrate-kit to top
  focus** (reverses the band-#870 §6 demotion). [doc](ideas/superbot-fresh-rebuild-vision-2026-06-30.md).
- **#1561 · #1550 · #1551 (2026-06-29, operator command gaps + proof-channel audit — S1 best-in-class)** —
  `!slowmode` · `!topic` (through the audited mutation seam) + `!roleinfo` — the operator commands
  that close best-in-class gaps vs. mature management bots (#1561); plus a proof-channel
  completion-deepening that **audits** prize lock/unlock and **re-checks `manage_channels`** at the
  modal/panel callbacks (authority re-check at execution time, not panel-open, #1550/#1551).
- **#1546 · #1548 · #1553 (2026-06-29, S1 game depth + workflow guards)** — the Creatures **interactive
  game panel** + dex browser + `entry_points` + settle-once terminal guard (#1546); a
  **session-slug-uniqueness guard** (hardens the born-red merge gate, BUG-0027 class) + a Mining how-to
  button (#1548); and a **registry↔ledger completion-parity guard** plus inventory sort-cycle / type-filter
  + display-logic tests on the category view (#1553).
- **#1540 · #1542 (2026-06-29, unified-hub leaderboard providers — completion-first deepening)** —
  **Fishing** (#1540) and **Farm** (#1542) leaderboard providers registered in the unified leaderboard hub.
- **#1549 (2026-06-29, Project Moon (Limbus) — combat-mechanics knowledge layer)** — the clash / speed /
  IDs+passives rules layer on the Limbus knowledge stack (extends the #1453…#1470 grounding arc).
- **#1541 · #1544 (2026-06-29, PROD hotfix — `give`-collision boot crash, Q-0211)** — #1541 added a
  `!give` / `!pay` peer coin-transfer command, which **collided** with mining's admin `give` (dormant
  since the initial commit, never PR'd) → the STRICT identity-contract aborted startup → **bot offline in
  a crash loop**. #1544 **retired `give` surface-wide** (removed economy `!give`/`!pay` + mining's admin
  `give` + its orphaned `admin_grant` caller) and added a **cross-cog duplicate-command boot guard** so the
  whole collision class can't recur (owner-directed root-cause prevention beyond the literal ask).
- **#1534 · #1536 · #1538 · #1545 (2026-06-29, S1 feature-completion certification arc — Q-0209)** —
  assessed every S1 bot unit against the #1513 certification framework to **100% assessed**: Mining /
  Creatures (◐) + Welcome (#1534), Moderation / Economy / Roles / XP **+ root-fix BUG-0029** (XP level-up
  role grants bypassed the audited role seam — no `audit.action_recorded`, no shared hierarchy preflight)
  (#1536), Settings / Leaderboards / Tickets / Karma (#1538), and the **final 17 server-fn units →
  completion ledger 100% assessed** + a fix-on-sight cleanup of 6 stale claim files for already-merged
  branches (#1545, Q-0166).
- **#1532 + 8 dashboard refreshes (2026-06-28/29, docs — twenty-eighth Q-0107 pass + dashboard)** — the
  **twenty-eighth Q-0107 reconciliation pass** (band-#1530,
  [pass record](planning/reconciliation-pass-2026-06-28-band1530.md), #1532); plus eight per-source-merge
  **dashboard-data refreshes** (#1533 · #1535 · #1537 · #1539 · #1543 · #1547 · #1552 · #1554, Q-0167).
- **#1504 · #1505 · #1508 · #1515 · #1518 · #1521 (2026-06-27/28, fishing acquisition-depth + gear arc — S1 game depth)** —
  fishing-specific gear stats that make the loadout presets a real optimisation (#1504); an
  `EffectiveStats` knob-coverage guard that surfaced two dead stats — `light_radius`/`luck` —
  before they were wired (#1505); a **fish → charm craft** path (#1508); a **fish → rod craft** path
  plus the 🍀 lucky-double-catch chance (#1515); a **"pearl"** rare-material drop + premium-bait pearl
  craft (#1518); and a fishing + counting **completion punch-list** (un-trap shops, fix menu nav/rules,
  add the player entry point, #1521).
- **#1513 · #1519 · #1523 · #1530 (2026-06-27/28, S1 feature-completion certification framework)** —
  a reusable **feature-completion certification framework** for the S1 bot units (#1513), then the first
  assessments against it: Fishing / Counting / Word Chain + surfacing the counting leaderboard (#1519);
  RPS / Deathmatch / Chicken-farm (#1523); and **Casino (poker) → ◐ assessed** (#1530, Q-0209).
- **#1512 · #1524 · #1527 · #1529 (2026-06-27/28, game-view robustness + arch guards)** —
  wired `light_radius` + `luck` into mining gameplay (**BUG-0026**, #1512); fixed the **born-red gate
  slug-collision hole** (**BUG-0027**) + restored a clobbered session log + game completion certs (#1524);
  made deathmatch **PvP terminal views** no longer dead-ends + root-fixed a panel-PvP context crash (#1527);
  and added an **arch guard flagging no-swap terminal handlers** in game views (#1529, friction→guard Q-0194).
- **#1510 · #1511 (2026-06-27, BTD6 grounding — corpus + absence-guard Layer B)** — expanded the BTD6
  regression corpus with 4 fixed-live-miss probes (reviewing the codex audit #1509, #1510); and shipped the
  **absence-guard Layer B** — the grounded-contradiction gate (#1511, the design half left open by #855's
  Layer A).
- **#1522 (2026-06-27, router — owner answers + a durable-home convention)** — documented owner answers
  **Q-0182…Q-0207** and decided the **router-vs-durable-home convention** (when a Q-block stays in the
  router vs. graduates to a binding doc).
- **#1502 + 10 dashboard refreshes (2026-06-27/28, docs — twenty-seventh Q-0107 pass + dashboard)** — the
  **twenty-seventh Q-0107 reconciliation pass** (band-#1500,
  [pass record](planning/reconciliation-pass-2026-06-27-band1500.md), #1502); plus ten per-source-merge
  **dashboard-data refreshes** (#1503 · #1506 · #1507 · #1514 · #1516 · #1517 · #1520 · #1525 · #1526 · #1528, Q-0167).
- **#1487 · #1488 · #1490 · #1491 · #1492 · #1493 · #1494 · #1498 (2026-06-27, BTD6 QA-accuracy arc — grounding + an honest eval harness, live-test driven)** —
  the band's marquee, owner-directed from live Discord screenshots: damage-type/status-effect **interaction
  grounding** + a VERIFIED Q&A corpus (#1487); the corpus **wired into the eval system** as an offline
  grounding test + a live action suite (#1488); a **faithful "exactly live" answer-path replay**
  (`tests/evals/btd6_live_path.py`, #1490) graded **semantically** by the same `llm_judge` to kill grader
  false-negatives (a 2/12 scorecard was the grader, not the bot — #1491); plus an **AI answer review-log**
  capturing didn't-know + user corrections (#1494). The DDT-counter sub-thread is the band's honesty story:
  #1492 grounded a VERIFIED DDT counter-tower list to fix over-refusal, the owner live-tested it and found
  3 wrong recommendations, so #1498 **reverted the auto-derived list at the root** (the committed stats
  encode neither MOAB-class targeting nor config quality, so grounding it = grounding misinformation) and
  replaced it with correct curated pop-guide prose — grounding the *rules*, not specific towers. #1493
  consolidated the arc + a live-verification checklist. Eval-only / data-only; `disbot/` answer path
  unchanged where noted. Live re-test + the still-open golden-set over-refusals stay owner-paced.
- **#1476 · #1477 · #1479 · #1482 · #1495 · #1500 (2026-06-26/27, self-improving-workflow guards — the loop closing its own drift classes)** —
  the S3/S4 mechanism lane, several slices *executing prior passes' own ideas*: a **▶ Next freshness guard**
  (#1476) wired into `/session-close` (#1477); a **session-close-gate meta-check** asserting every checker
  declaring the `[session-close-gate]` sentinel is actually referenced in `/session-close` Step-4 (#1479,
  builds #1477's Q-0089 idea); **per-sector offline-fit startability tags** so the dispatch menu can pick an
  offline-runnable item (#1482, owner decision Q-0207 DISCUSS); the **reconcile-marker band-consistency
  guard** `check_reconcile_marker.py` + the live `#1472`→`#1470` marker-conflation fix (#1495, executes the
  band-#1470 pass's own Q-0089 idea); and an **offline-startable S1 ▶ Next** handoff-hygiene sharpening
  (#1500). All read-only / stdlib / offline.
- **#1483 · #1496 · #1499 (2026-06-27, S1 feature depth — economy observability · setup · mining)** — a
  games-economy **per-day faucet/sink trend view** (economy observability, #1483); a new Essential Setup
  spine step **"Where can people use commands?"** surfacing the enforced per-channel Command Access control
  (#1496); and **mining gear loadout presets** (V-14 / Q-0175 Phase-1 unified-loadout model, migration 101 —
  applies automatically on next boot/auto-deploy, #1499).
- **#1485 · #1486 (2026-06-27, autonomous test coverage — Media/YouTube)** — focused YouTube **fetch service +
  renderer/embed tests** (#1485) and **YouTube cache DB-primitive tests** (#1486); empty-fire dispatch slices
  that hardened a previously thin-covered subsystem.
- **#1472 + 9 dashboard refreshes (2026-06-26/27, docs — twenty-sixth Q-0107 pass + dashboard)** — the
  **twenty-sixth Q-0107 reconciliation pass** (band-#1470,
  [pass record](planning/reconciliation-pass-2026-06-26-band1470.md), #1472); plus nine per-source-merge
  **dashboard-data refreshes** (#1473 · #1474 · #1475 · #1478 · #1480 · #1481 · #1484 · #1489 · #1497, Q-0167).
- **#1453 · #1456 · #1467 · #1469 · #1470 (2026-06-25/26, NEW Project Moon (Limbus) knowledge domain — data → grounding → faithfulness guard)** —
  a standalone Limbus knowledge domain modeled on the BTD6 stack: committed structural/lore facts
  (`disbot/data/projmoon/limbus/`: 12 Sinners · 7 Sins · damage types · E.G.O grades, provenance-tagged) +
  a typed `services/projmoon_data_service.py` + a browsable `!pm` / `/pm` surface with its own top-level
  **Project Moon** Help hub (PR 1, #1453); each Sinner's canonical `literary_origin` + an **Origins**
  cross-reference view (lore-depth Slice A, #1456); the **AI grounding path** — `AITask.PROJMOON_ANSWER`
  routing + provenanced fact injection into `_gather_feature_facts`, BTD6 path byte-identical (PR 2, #1467);
  a **faithfulness guard** (`projmoon_grounding_service`, the projmoon analogue of `validate_btd6_reply` —
  reject → regenerate-once → deterministic refusal, #1469); and a **cross-domain over-route guard** pinning
  BTD6↔Limbus token disjointness + a detector-curation recipe so the next domain (LoR / LobCorp) is a
  one-line registration (Slice B prep, #1470). Read-only, offline-unit-tested; the live Q-0086 runtime walk
  stays owner-paced.
- **#1458 · #1460 · #1461 · #1466 (2026-06-25/26, BTD6 eval-anchor hardening — S2 P1-1)** — a fixture-drift
  anchor guard for the contains-grader grounding cases (#1458); projected-total eval figures anchored,
  nailing the starting-cash convention (#1460); the #855 MOAB-class bonuses +15/+30/+99 anchored (#1461);
  and the **eval-anchor coverage report + distractor negative-anchor guard** — every cleanly-derivable
  dollar/HP truth must be anchored or on a documented distractor/user-input allowlist (#1466). The BTD6
  grounding cases are now anchor-complete for every cleanly-derivable truth.
- **#1444 · #1445 · #1454 (2026-06-24/25, settle-once money-safety for game-state views)** — a settle-once
  terminal guard for game-state views (#1444), the blackjack-PvP settle-once guard + the shared mixin
  relocated to `utils/` (#1445), and a `check_consistency` **Rule 6** warn-first adoption guard so the
  settle-once money-safety pattern can't silently regress (#1454).
- **#1449 · #1450 · #1451 (2026-06-25, Essential Setup wizard follow-ons)** — **PR 2**: the "All done"
  **extras menu** (a plain menu of the optional features the spine skips) + a jargon-free **"Check my
  setup"** readiness health check (#1449); **claim-GC automation** (Q-0206) + an Essential Setup
  status-badges follow-on (#1450); **PR 3a**: retire the 7 dead read-only/metadata wizard sections +
  demote cleanup to advanced-only (#1451).
- **#1463 · #1464 (2026-06-25, BUG-0025 image-card navigation fix)** — the `/myprofile` hero-card image is
  now preserved across editor navigation (#1463) and the stranded rank card is cleared when opening the XP
  **Configure** panel (#1464); together they close **BUG-0025** (the cross-panel image-card transitions
  that omitted `attachments=`).
- **#1443 · #1447 + dashboard refreshes (2026-06-24/26, docs / grooming / dashboard)** — the **twenty-fifth
  Q-0107 reconciliation pass** (band-#1440, [pass record](planning/reconciliation-pass-2026-06-24-band1440.md),
  #1443); grooming to promote two ideas into the backlog (#1447); plus nine per-source-merge **dashboard
  refreshes** (#1446 · #1448 · #1452 · #1455 · #1457 · #1459 · #1462 · #1465 · #1468, Q-0167).
- **#1418 · #1420 · #1422 · #1425 · #1427 · #1429 · #1432 · #1434 · #1435 · #1436 · #1437 · #1438 · #1439 (2026-06-24, Essential Setup wizard restructure — one action per step, zero jargon)** —
  the marquee S1 arc: a plan + simulator (#1418) and a **banned-jargon CI guard** (measured baseline 207
  strings, #1420) drove a **plain-language sweep** (guild → server, jargon 207 → 154, #1422); then the
  **Essential Setup spine** itself (#1425) — a linear, **direct-apply**, plain-language wizard, one action
  per step — fleshed out step by step: steps 3–4 block-spam · help-desk (#1427), a "Choose a log channel"
  step that binds + auto-creates (#1429) and grew into a **two-channel** mod + activity multi-select (#1432),
  a "Reward active members" step (XP rate + level/time role rewards, #1434), spine polish + optional custom
  naming (#1435), a **step-0 server-type starter preset** (#1437), and a logging-step defer fix before slow
  channel-creation work (#1439). It was **cut over to the primary `!setup` / `/setup`** (#1438); the
  setup-wizard plan + S1 state were reconciled to the shipped spine (#1436). Owner decisions Q-0202–Q-0205.
- **#1417 · #1421 · #1423 (2026-06-24, support tickets — discoverability + full button setup)** — the
  #1405 ticket subsystem was **wired into the `!setup` wizard + bot-join welcome** (#1417), the setup
  **readiness scan now grades tickets** as a discoverability nudge (#1421), and ticket setup became a
  **fully button/dropdown** flow that auto-creates the log channel (#1423).
- **#1413 · #1430 · #1431 (2026-06-24, visual card-engine H3 — image cards through Help)** — the
  `xpmenu` hub renders the **rank image card** (#1413); the **help-nav attachment seam** carries hub image
  cards through Help (#1430), hardened with forward-path regression pins (#1431). Extends the card-engine
  H2/H3 rollout (#1396…#1403).
- **#1419 · #1424 · #1426 (2026-06-24, BTD6 unification + slash-sync runtime)** — the five BTD6 command
  groups **unified under one `/btd6`** (flattest layout, #1419); a **diff-gated startup command-tree
  auto-sync** (+ post-unification docs cleanup, #1424) with `!syncslash global` gated through the same
  diff-aware helper (+ a force escape, #1426).
- **#1415 · #1416 (2026-06-24, idea → plan — bot-migration assistant)** — captured the owner idea (#1415)
  and structured the plan (#1416): detect → map → replicate → retire other bots.
- **#1412 · #1414 · #1428 · #1433 · #1441 (2026-06-24, docs — 24th Q-0107 pass + dashboard refreshes)** —
  the **twenty-fourth Q-0107 reconciliation pass** (band-#1410,
  [pass record](planning/reconciliation-pass-2026-06-24-band1410.md), #1412); plus four per-source-merge
  **dashboard-data refreshes** (#1414 · #1428 · #1433 · #1441, Q-0167).
- **#1405 · #1410 (2026-06-24, NEW support-ticket subsystem — command + AI natural language)** — a complete
  new `ticket` subsystem (migration 098 `ticket_config`/`tickets`/`ticket_blacklist`, audited
  `ticket_mutation` seam, anchor-free persistent launcher + in-channel control panel + staff hub + describe
  modal, `!ticket`/`!ticketpanel`/`!ticketsetup`/`!ticketblacklist`) modeled on the best ticket bots —
  clickable panels, categories, per-ticket private channels, claim/add/remove, transcripts, per-user limits +
  blacklist (#1405). It also introduces the **first write-capable AI *action* tool**, `open_support_ticket`,
  through the deterministic audited mutation service; the follow-up (#1410) re-postured it so **the AI opens
  a ticket via a one-click confirm, not autonomously** (router **Q-0201**, superseding #1405's direct-open
  draft).
- **#1408 · #1409 (2026-06-24, BTD6 AI floor coverage + admin slash-command fix)** — range RBE answers + the
  paragon **elite-boss damage multiplier** in the AI floor set (#1408, extends the #1402/#1404 round-economy +
  elite-boss lineage); plus two owner-reported Discord-thread fixes (#1409) — a **`!syncslash clear`** scope
  that drops duplicate guild-local slash copies (the global+guild double-render), and a **`/btd6ref round`
  range** (combined per-round RBE/cash/cumulative table).
- **#1407 (2026-06-24, docs — twenty-third Q-0107 reconciliation pass, band-#1380)** —
  the previous docs-only reconciliation + planning pass
  ([pass record](planning/reconciliation-pass-2026-06-24-band1380.md)).
- **#1359 · #1360 · #1361 · #1363 · #1366 · #1367 · #1369 · #1370 · #1371 · #1372 · #1373 · #1374 · #1375 · #1376 · #1377 · #1378 · #1382 · #1383 · #1385 (2026-06-23/24, consolidation & discoverability audit — execution arc)** —
  the audit brief executed as a multi-session **ultracode fleet**: Session 1 help-findability foundation + a
  per-command reachability guard (#1370), Phase-0 shared hub-child primitive + settings-orphan guard + the
  fleet plan (#1371), the extracted shared **`HubChildButton`** (#1373) with a shared-dependency/ownership
  map (#1374) and the fleet coordinator (#1375); in-place navigation for AI (#1376) / roles (#1377) /
  games (#1378); `!btd6strat` surfaced via a BTD6 Strategy panel button (U4, #1372); **universal Help +
  Back-to-hub on every leaf panel** (#1382) and **game-result continuation buttons** (#1383) — the
  never-stranded pair; a **static settings-reachability guard** (#1385); cleanup-policy panel tips
  (#1360/#1363), a delete-blocked-commands surface (#1359), and a Final-Review create-count guard (#1361);
  plus the audit/findings briefs (#1366/#1367/#1369).
- **#1355 · #1357 · #1386 · #1390 (2026-06-23/24, AI natural-language setup wedge — Q-0048 write-lift / Q-0199)** —
  the first AI surface that *applies* setup changes after confirmation: `/setup-describe` natural-language
  setup wedge (#1355) → propose resource **creation** from a description (create+bind, #1357) → the
  **AI-setup advisor (Accept · Deny · Edit)** finalizing the Q-0048 write lift (#1386, recorded as router
  Q-0199) with an edit-rebind follow-up (#1390).
- **#1364 · #1396 · #1397 · #1398 · #1399 · #1401 · #1403 (2026-06-23/24, themeable card-render engine — H2/H3 rollout)** —
  the visual card engine rolled onto real features: render-structure ("golden") tests (#1364), image
  renderers rebased onto **`CardCanvas`** (H2, #1396) behind a card-engine guard (#1397) and a
  theme-conformance guard (#1403); the **leaderboard image card** shipped as a real feature (#1398) with
  per-category themes (#1399), and the **rank card** as a themed image (#1401, first feature card / H3).
  Executes the band-#1350 C1 slice.
- **#1384 · #1387 · #1402 · #1404 (2026-06-23/24, BTD6 mechanics + round-economy depth)** — round-scaled
  bloon health (late-game/freeplay MOAB-class HP ramp, #1384), a freeplay health-curve fix + ground-truth
  round-scaled RBE (#1387), the **paragon elite-boss damage multiplier** (×2, all degrees, #1402), and
  **per-round economy slash commands** (cash / RBE / bloons, #1404).
- **#1351 · #1356 · #1365 (2026-06-23, fishing minigame follow-ups)** — per-species **trophy records**
  (biggest-caught, #1351), a soft-fail clue + heaviest-catch leaderboard (#1356), and the
  **`premature_grace` rod knob** (the design's 5th knob, #1365). Executes the band-#1350 D2 slice.
- **#1394 (2026-06-23, moderation)** — an **obfuscation-resistant word filter** (out-filters Sapphire's
  content filter — leet/spacing/zero-width normalization).
- **#1354 · #1362 · #1389 · #1391 · #1392 · #1393 (2026-06-23/24, docs / ideas / router / dashboard)** —
  the **twenty-second Q-0107 reconciliation pass** (band-#1350, #1354); promote loose session ideas into the
  backlog (#1362); router **Q-0199** (AI may apply setup changes after confirmation, #1389); BTD6
  runtime-mechanics extraction (#1391) + BTD6 cash-model empirical-validation (#1393) ideas; a reconcile of
  the consolidation-audit docs to shipped work (#1392); plus six per-source-merge **dashboard refreshes**
  (#1358 · #1368 · #1380 · #1388 · #1395 · #1400, Q-0167).
- **#1328 · #1331 · #1332 · #1333 · #1334 · #1344 (2026-06-23, NEW economy/game subsystems — farm · Karma · casino · treasury)** —
  a burst of brand-new subsystems: an **idle egg/chicken farm** game (lazy-accrual idle loop, #1328) plus a
  fresh-coop fix (no longer starts full + a "while you were away" idle summary, #1331); a **Karma**
  thanks/upvote reputation subsystem (#1332, plan #1330); a **Casino** subsystem — a multiplayer card-game
  **table framework + Texas Hold'em poker** (#1333); and a **Treasury** — a server-owned coin pool on the
  economy↔governance seam (#1334) with a Treasury button wired into the Economy panel (panel-link fix, #1344).
- **#1329 · #1337 · #1338 · #1340 · #1341 · #1342 · #1351 (2026-06-23, fishing minigame — economy knobs + venues + polish)** —
  the fishing game gained its second pre-cast economy knob, **Bait** (coin sink + rarity bias, #1329), a **bait
  speed knob** (faster bites, #1337) and **bait-crafting** (turn caught fish into bait — closes the catch→bait
  loop, #1338); plus a **deepwater boat venue** (⛵ Set sail / Dock, #1340), a **daily weather forecast**
  (date-seeded global bias, #1341), a test-helper consolidation of the duplicated `roll_catch` mock (#1342),
  and **per-species trophy records** (your heaviest catch per species in the Fishdex, #1351).
- **#1324 · #1325 · #1326 (2026-06-23, BTD6 round economy)** — surfaced **round XP** in the NL reply +
  round-embed Economy field (#1324), then the **unified round-economy reply** (RBE + cash + XP in one answer,
  #1326), backed by validated **XP-per-round data** (`round_xp.json`, #1318 — merged via #1325, which also
  routed the mining-grid encounters idea to the owner, Q-0198).
- **#1345 · #1350 (2026-06-23, cleanup channel surface)** — a **cleanup panel UX** pass (readable whitelist,
  fixable warnings, custom per-channel levels, #1345) and then the root simplification — **removed the legacy
  cleanup channel whitelist** entirely (#1350).
- **#1349 (2026-06-23, themeable card-render engine — out-visual Dank Memer, PR 1)** — a reusable themeable
  **card-render engine** + the first profile card (the foundation for best-in-class visual cards;
  [vision](ideas/visual-card-engine-vision-2026-06-23.md)).
- **#1322 · #1343 · #1346 (2026-06-23, tooling / CI guards)** — a **migration-collision guard** (pre-push
  duplicate-number check + tests, #1322), a `check_quality` **isort scope** fix (stop false-reds on `tests/`,
  #1343), and an extended **`new_subsystem.py` checker** (loader + extension-role + sector-folio + claim +
  born-red card gaps, #1346).
- **#1327 (2026-06-23, Hermes ops)** — a Hermes **one-command redeploy** (auto redeploy, no terminal needed,
  #1327).
- **#1323 · #1330 · #1335 · #1336 · #1339 · #1347 · #1348 · #1352 (2026-06-23, docs / plans / dashboard)** —
  the **twenty-first Q-0107 reconciliation pass** (band-#1320, #1323); the **Karma plan** (#1330); plans for
  **hub child-rendering consistency + placement** (#1347) and a **native giveaway system** (beat GiveawayBot,
  #1348); the **competitive-positioning north-star** vision doc (#1352); and three per-source-merge
  **dashboard-data refreshes** (#1335 · #1336 · #1339, Q-0167).
- **#1296 · #1298 · #1299 · #1301 · #1303 · #1304 (2026-06-22, NEW fishing minigame — design → full game)** —
  a complete new minigame stood up in one arc: a stdlib **design simulation + analysis** (#1296) drove the
  interactive **cast → wait → BITE → reel loop** (PR1, #1298), then the **trophy reel-fight** completing the
  hybrid (PR2, #1299), the **rod ladder** (buy rods with coins, wires the 4 tuning knobs; PR3, #1301), **real
  menu buttons** (Cast · Rod · Fishdex panel, #1303), and **separate energy pacing + a generous sell
  rebalance** (PR4, #1304).
- **#1300 · #1302 · #1306 (2026-06-22, role management — bulk creation + per-role colours)** — **bulk role
  creation via preset packs** (#1300), then enhancements — enlarged multi-select presets, bulk custom roles,
  optional colour presets (#1302) — and a **role-list colours** surface + optional per-role colour for bulk
  custom roles (#1306).
- **#1294 · #1297 (2026-06-22, help surface slimming + reachability guard)** — removed the redundant
  "All Commands / Advanced" help surface (#1294) and added a **help-reachability CI guard** that fails the
  build when a subsystem isn't homed in the help tree (#1297).
- **#1295 · #1316 (2026-06-22, BTD6 answerability)** — a **P1-1 grounding-anchor eval guard** (asserted
  numbers must be grounded, #1295, closes #704's eval-guard ask) and a **whole-catalog roster** answer for
  "list all monkey knowledge" (#1316).
- **#1305 (2026-06-22, botsite React-SPA migration PR 1 — foundation)** — a buildable, data-fed React app
  foundation (Vite + `design-system/src/app/`, data layer + tests, `botsite/app.py` wiring) — the first slice
  of migrating the live bot-site onto the design-system React stack.
- **#1308 · #1317 · #1320 (2026-06-22, CI / ledger hygiene + tool-pin guard)** — fixed the #1279 ledger
  under-marker drift + design-system CI-coverage paths + reverted a Dependabot **ruff pin drift** back to
  three-places parity (#1308/#1317, with stale-claim GC), then **CI-enforced the tool-pin guard**
  (`tool-pins.yml` + `check_tool_pins.py`) to close the #1315 three-places-drift class at the root (#1320).
- **#1307 · #1309 · #1311 · #1312 · #1313 · #1314 · #1315 (2026-06-22, dependency bumps + dashboard refresh)** —
  Dependabot bumps (fastapi #1309, python-json-logger #1311, aiohttp #1312, youtube-transcript-api #1313 with a
  v1.x API fix, openai #1314, dev-deps group #1315) and a per-source-merge `dashboard-data-refresh` regen
  (#1307, Q-0167).
- **#1281 · #1282 · #1284 · #1286 · #1289 (2026-06-22, mining grid Mine + economy/energy rebalance)** — the
  descent game became a **(x,y,z) seed-deterministic grid world** with 6-direction movement (hub-redesign PR 3,
  #1281, migration 085), then **unified dig + move** so each directional dig moves you into the cell (#1282); a
  stdlib **economy/balance simulator** (`tools/game_sim/mining_economy_sim.py`, #1284) drove the **sim-pinned
  rebalance + energy system** (food/booster refill, #1286) and **cook + sell fish** energy refill via a campfire
  (#1289). [plan](planning/mining-hub-redesign-2026-06-15.md).
- **#1270 · #1265 · #1268 (2026-06-22, Starboard PR 2 + creature PvP + BTD6 buff-uptime)** — Starboard PR 2:
  self-star exclusion + ignore-channels + the `BaseView` config panel (#1270, the planned B1 slice, builds on
  #1259); creature PvP gained a ⌛ **challenge-expiry timeout notice** (#1265); BTD6 buff-uptime now models
  **attack-speed buffs on the Alchemist** (`alch_speed`, #1268).
- **#1275 · #1288 · #1280 (2026-06-22, CI / autonomous-loop reliability)** — root-fixed the **CI-strand** class:
  `code-quality`'s `cancel-in-progress` was dropping the *head-commit* run (#1275), and a new
  **`ci-rerun-watchdog`** re-kicks `code-quality` when GitHub drops the `synchronize` event (#1288,
  `check_ci_coverage.py`); plus a **wrong-branch guard** hook institutionalizing the friction→guard reflex (#1280).
- **#1283 · #1285 · #1271 (2026-06-22, Q-0195 coordination-file restructure + workflow tooling)** — the
  **state-file restructure** — `active-work.md` → one-file-per-claim (kills the merge-conflict class) +
  `current-state.md` → per-sector files under [`current-state/`](current-state/README.md) (#1283, justified by
  `tools/sim/claim_layout_sim.py`); an **unattended-fit dimension** in the per-sector dispatch contract so
  empty-fire runs stop stalling (#1285); and `band_pr_status.py --themes`, a grouped-entry skeleton drafter (#1271).
- **#1267 · #1291 · #1272 (2026-06-22, bug fixes — dashboard determinism + command scanner)** — root-caused the
  dashboard `generated_at` nondeterminism (deterministic timestamp + refresh self-heal, #1267) then a **hermetic
  determinism test** killing the `-n auto` flake (**BUG-0024**, #1291); **BUG-0023** root fix — the command
  scanner now discovers `app_commands.Group` attribute slash commands (#1272).
- **#1276 · #1278 · #1274 · #1269 · #1273 · #1287 (2026-06-22, docs / chore / config + dashboard refresh)** —
  repo navigation cleanup + prune the stale claim ledger (#1276); deleted the disproven "synchronize doesn't
  re-fire CI" journal claim (#1278); allow read-only network probes (`curl`) in settings + prune a stale claim
  (#1274); and the per-source-merge `dashboard-data-refresh` cadence regen (#1269 · #1273 · #1287, Q-0167).
- **#1235 · #1249 · #1251 · #1255 · #1258 · #1263 (2026-06-21, BTD6 buff-uptime + data auto-seed/drift)** — a
  long BTD6 data session: the **buff-uptime upgrade-detail** model — `btd6_upgrade_detail_service` + an AI tool
  + `parse_gamedata` extraction (#1235), data verify + populate (alchemist, #1249), **multi-target** buff
  uptime (#1251); then the **data-lifecycle hardening** — auto-seed BTD6 blob data on boot (`btd6_data_service`
  + env-var, #1255), a **content-drift surface** (#1258), and the `!btd6ops seed-data` **changed-report**
  (#1263). Closes the standing "owner must remember to run `seed-data`" manual step.
- **#1234 · #1237 · #1242 · #1243 · #1245 · #1246 · #1248 · #1250 (2026-06-21, reaction-roles arc —
  continuation / polish past the overhaul's PR 1–5)** — multi-emote-per-message + menu reuse/repost (#1234),
  post-channel picker + auto-created colour/gradient roles (#1237), free temp-roles **member view** (#1242,
  `role_grants_cog`), message picker for the Add flow — no more copy-paste message ID (#1243), role presets +
  management-panel UX (#1245), gradient presets gallery (#1246), **dead-binding self-heal** — cleanup on
  role-delete + panel hint (#1248) and auto-heal on the live reaction-listener path (#1250). The arc is now
  Carl-bot-mature; **PR 6 (PIL banner cards) shipped 2026-06-22 (#1279** — optional `role_menus.card_template`
  banner via the `welcome_render` PIL pattern, graceful embed-only fallback); only the gated web builder
  (Surface A) remains ([plan](planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **#1238 · #1239 · #1240 (2026-06-21, Project Moon knowledge-domain program — design, Q-0192)** — a NEW
  large program stood up as design: the **wiki-feasibility idea** ("can we serve a fandom wiki like BTD6
  data?", #1238), the **full-parity program plan** (#1239, Q-0192), and the **pre-build recon** — data
  sources + the generalized `KnowledgeDomain` seam contract (#1240). Docs-only; the runtime build is a
  buildable lane ([plan](planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
- **#1244 · #1254 (2026-06-21, creature leaderboard provider + Starboard plan)** — the creature-PvP
  **leaderboard rank provider** (`rank_providers`, #1244) feeding the shared ranking surface; and the
  **Starboard / Hall-of-Fame plan** (#1254, idea B1) whose PR 1 (#1259, migration 082) is in flight on the
  reaction-listener seam. [plan](planning/starboard-plan-2026-06-21.md).
- **#1247 · #1253 · #1256 (2026-06-21, workflow / docs)** — **Q-0193 merge=deploy clarity** (Railway
  auto-redeploys `worker` on merge → never tell the owner to "restart/deploy" a merge; CLAUDE.md +
  `production-deployment.md` + router, #1247); a journal capture of recurring **reaction-roles-chain workflow
  lessons** (#1253); a repo-state review + `check_docs` guard hardening (#1256).
- **#1236 · #1241 · #1252 (2026-06-21, dashboard generated-data refresh band)** — the per-source-merge
  `dashboard-data-refresh` cadence regen of `dashboard/data/dashboard.json` (Q-0167).
- **#1215 · #1216 · #1217 · #1218 · #1220 · #1219 · #1227 (2026-06-21, reaction-roles / role-menu overhaul —
  Carl-bot parity, end-to-end)** — the plan (#1215 overhaul plan · #1216 UI direction = web dashboard vs
  in-Discord · #1217 presentation/editing §4.6 · #1218 owner decisions locked + role-pickup analytics) then
  the build: **PR 1** audited `reaction_role_service` seam + `utils/db/role_menus` data layer + migration 078
  + cog routing/teardown (#1220); **PR 2** the in-Discord role-menu builder (Surface B, buttons/selects/modals,
  #1219); **PR 3–5 together** (one owner-directed PR, Q-0191 merge-immediately, #1227) — per-message emoji
  modes [migration 079] · free temp-roles `RoleGrantsCog`/`!temprole`/`utils/duration` [migration 080] ·
  role-pickup analytics [migration 081]. **PR 6 (PIL banner cards) shipped 2026-06-22 (#1279);** only the
  gated **web builder (Surface A)** remains ([plan](planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **#1208 · #1213 (2026-06-21, creature game — design → runtime)** — **catch + collection/dex** shipped as the
  first runtime slice (#1208 — `disbot/cogs/creature_cog.py`, fishing-mirrored spine, `utils/creatures/` pure
  domain + `services/creature_workflow.py` audited write + migration 077 + the 36-creature catalog +
  `GAME_CREATURE` xp track), and the **level-normalized PvP battle engine** graduated into pure domain
  `disbot/utils/creatures/battle.py` (#1213, `needs-hermes-review`) with 24 fairness-gate tests. The
  user-facing PvP flow shipped (#1230 — `!cbattle`, `BaseView`-locked challenge → read-only
  `services/creature_battle_service.py` → engine; auto-resolves at `NORMALIZED_LEVEL`). [plan](planning/creature-game-design-and-sim-2026-06-20.md) §4.
- **#1226 · #1228 · #1229 · #1231 (2026-06-21, "free for everyone, forever" product North Star + license)** —
  codified the North Star (Q-0190, #1226), answered the open-source/self-host posture under it (#1228), and
  recorded the **license decision — stay MIT for now** (free-use-only deferred, #1229/#1231). Owner-directed
  design decisions; also folded in the creature sim↔engine combat-constant parity guard (#1229).
- **#1211 · #1212 · #1223 · #1224 · #1225 (2026-06-21, workflow tooling)** — a **permission-overlap guard** +
  force-push ask-residual fix (#1212) on the `git push --force-with-lease`/`cd` allowlist (#1211); the
  **lane-overlap claim-scan** now reads the `active-work.md` claim ledger (#1223, `scripts/check_lane_overlap.py`);
  **Q-0189 — open the session PR fast (~2 min)** codified (#1224); pruned stale `active-work.md` claims (#1225).
- **#1210 (2026-06-21, `public-data-contract-field-snapshot` redaction guard)** — the public `site.json`
  redaction guard now pins **leaf fields per family** (`SITE_FIELD_CONTRACT` in `export_dashboard_data.py` +
  the within-family whitelist in `check_dashboard_data.check_site_subset`), so keys *and* leaves both fail
  closed — completing the ungated stdlib-guard cluster.
- **#1203 · #1205 · #1206 · #1207 (2026-06-21, bug fixes + CI/design-system)** — recorded the Claude-Design
  connector as read-only (migration-plan Decision D, #1203); aligned Storybook deps on v10 to fix the
  design-system CI install (#1205); root-fixed **BUG-0020** (`trim_recently_shipped.py` floor-pointer prose
  contamination) + **BUG-0021** (flaky lock-wait test) + **BUG-0022** (suite clobbers tracked `data.js`)
  (#1206); **BUG-0023** botsite command-count reconcile + a tool-pin drift guard (#1207).
- **#1209 · #1214 · #1222 (2026-06-21, dashboard generated-data refresh band)** — the per-source-merge
  `dashboard-data-refresh` cadence regen of `dashboard/data/dashboard.json` (Q-0167).
- **#1183 · #1185 · #1193 · #1194 (2026-06-20, NEW creature-catch/PvP game — design + sim + catalog +
  combat, no runtime yet)** — an original-IP (no Pokémon names) creature game stood up as design+tooling+data:
  a stdlib deterministic Monte-Carlo **playability simulator** (`tools/game_sim/creature_battle_sim.py`,
  verdict **PLAYABLE**, surfaced the core rule *PvP must be level-normalized*) + v1 ruleset + the copyright
  answer (#1183), creature roster sizing + legal music-bot findings (#1185), a data-driven **36-creature
  catalog** sim-validated playable (#1193), and the **complete combat model** — moves / damage types / 6v6
  (#1194). No `disbot/` cog yet — the runtime build is the next buildable lane (Q-0187;
  [plan](planning/creature-game-design-and-sim-2026-06-20.md)).
- **#1180 · #1182 (2026-06-20, Pokétwo + MusicBot research → feature-mapping plan + BUG-0019)** — a
  research report → a feature-mapping plan ([plan](planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md),
  #1180), plus **BUG-0019** capture (the AI replied to *other bots'* mentions) + the Pokétwo demand signal
  (#1182). Docs-only. (BUG-0019 #2 — the `@everyone`/`@here` false-ping leg — is the #1186 entry below.)
- **#1187 · #1188 · #1191 (2026-06-20, CI PR-guard determinism)** — the pr-conflict-guard now uses a
  deterministic `git merge-tree` (kills the "only occasionally red" flake, #1187); pr-auto-update gets the
  same deterministic behind-detection fix for the identical async race (#1188); both were then extracted
  onto **one shared, unit-tested git merge-state helper** (#1191).
- **#1175 · #1176 · #1178 · #1196 · #1198 · #1199 (2026-06-20, Claude-Design bot-site)** — the full
  landing-page composition (#1175), the GitHub-connector design workflow docs (#1176), composing the rest of
  the site (Features / Commands / Changelog / Status, #1178), serving the Claude-Design SPA with a **live
  generated data layer** (#1196), a plain-language website explainer + the Claude Design loop (#1198), and the
  plan to migrate the live bot-site onto the React design-system app
  ([plan](planning/botsite-react-spa-migration-plan-2026-06-20.md), #1199).
- **#1177 · #1189 (2026-06-20, mining/community fix + consistency-linter)** — `!character` now shows the
  paper-doll + missing back buttons added (#1177); the consistency-linter `back_button` rule now also catches
  dynamically-built (`add_item`) hubs (#1189).
- **#1174 · #1181 · #1192 · #1195 (2026-06-20, workflow tooling)** — `check_loop_health.py` gained the
  `gh`-absent stdlib-REST fallback so the control-plane ROUTINE_PAT row is **script-verifiable in-container**
  (#1174, [plan](planning/loop-health-gh-fallback-plan-2026-06-20.md)); the **band PR-status classifier +
  Recently-shipped trim actuator** shipped (#1181, building the band-#1170 pass's Q-0089 idea —
  `scripts/band_pr_status.py` + `scripts/trim_recently_shipped.py`, both wired into this routine); a
  SessionStart branch-freshness warning (#1192, Q-0188); re-landed a dropped status-move decision (#1195,
  born-red slip).
- **#1172 · #1179 · #1184 · #1190 · #1201 (2026-06-20, dependabot + dashboard generated-data refresh band)** —
  the dependabot design-system npm bump (#1172) and the per-source-merge `dashboard-data-refresh` cadence regen
  of `dashboard/data/dashboard.json` (#1179 · #1184 · #1190 · #1201, Q-0167).
- **#1186 (2026-06-20, BUG-0019 #2 — `@everyone`/`@here` false-personal-ping hardening)** — the AI
  natural-language stage computed `is_mention` via `ClientUser.mentioned_in`, which short-circuits
  `True` on `message.mention_everyone`, so a server-wide blast flipped the `mention_only` policy gate
  open. Replaced with `natural_language_stage._is_direct_bot_mention` (bot id in `message.mentions`);
  stays-fixed guard `test_everyone_blast_is_not_a_personal_ping`. Bug-book mechanism **#1** (the
  `always_reply` "barge into others' conversations" design fork) stays OPEN, routed to the owner.
- **#1156 · #1158 · #1160 (2026-06-19/20, federated Explore-hub spine + world registry)** — spine
  **PR 1** (#1156): a top-level Explore *world* hub (town-square) + the world registry, re-parenting the
  #1131 mining Explore sub-hub. **PR 3** (#1160): the cross-game world card — `game_xp_service.world_identity()`
  (global level + per-game standings, read-only), `views/explore/world_card.py`, a `🪪 World Card` hub button +
  `!worldcard`/`!mystats`. **#1158**: the world-registry parity invariant + games-folio spine docs. Spine **PR 2**
  (global/per-game XP split) is reframed **owner/runtime-gated** (a `player_skills` PK migration + an earning-model
  design call) — not an empty-fire lane. [plan](planning/explore-hub-federated-world-plan-2026-06-19.md).
- **#1147 · #1151 · #1152 · #1154 · #1168 (2026-06-19, public bot-site dark launch + botsite polish)** — stood
  the public bot site up **dark on Railway** (#1147), repointed the URL → `superbot-app.up.railway.app` (#1151),
  wired the "Add to Discord" install buttons to the real install link (#1152) + fixed the dead `/submit` button a
  Codex review caught (#1154), and added the Claude Design React+Tailwind component library (`/design-sync`, #1168).
  The website v1 is code-complete; the remaining work is the owner-paced rollout (see Next candidates).
- **#1143 · #1144 · #1146 · #1148 · #1157 (2026-06-19, bug-book guards + BUG-0016/0018 root-fixes)** — the
  deferred-root-fix backlog guard (#1144, self-initiated Q-0172) + two hardenings from review (scope the root-fix
  guard to the status label / short-circuit on terminal `FIXED`, #1146/#1148); **BUG-0018** root-fix (#1143 — the
  `site.json` hard-equality test no longer reddens on idea-doc churn); **BUG-0016** (#1157 — single-source the
  reconcile-issue body to kill the drift class).
- **#1162 · #1163 · #1166 (2026-06-19, instruction-core + arch/consistency guards)** — pinned the always-loaded
  `.claude/` instruction core against pointer rot (#1162); extended the `baseview_inheritance` arch ratchet to the
  **cog layer** (#1163, closing the direct-View blind spot the consistency linter already covered); pinned the
  `panel_base_class` consistency allowlist to the `baseview_inheritance` conformance frozenset with a parity test
  (#1166, retiring the two-sources-of-truth drift).
- **#1149 · #1150 · #1153 · #1159 · #1167 (2026-06-19, ideas + journal captures)** — dev-site project-status donut
  + dev-site-refocus direction (#1149), donut refinements (#1150), the public-site "customize before you invite" cog
  chooser (#1153), the bug-book claim-gap idea + subsystem-tag grooming (#1159), and the "git push doesn't re-fire
  PR CI" env gotcha journal entry (#1167). Docs-only.
- **#1169 (2026-06-19, AI self-introduction advertises real capabilities)** — a new always-assembled
  `_CAPABILITIES_OVERVIEW` system layer so the bot's self-intro names its **games / economy / progression**, not
  just BTD6 (with prompt discipline keeping BTD6 general so the faithfulness guard doesn't floor it) + intro-phrasing
  catalog triggers + pinning tests + an AI-folio note.
- **#1145 · #1155 · #1161 · #1164 · #1165 · #1170 (2026-06-19/20, dashboard generated-data refresh band)** — the
  per-source-merge `dashboard-data-refresh` workflow's cadence regen of `dashboard/data/dashboard.json` (Q-0167).
- **#1142 (2026-06-19, band-#1140 Q-0107 reconciliation pass)** — the previous docs-only, planning-weighted
  reconciliation ([record](planning/reconciliation-pass-2026-06-19-band1140.md)): reconciled the ledger to #1140,
  routed four design questions (Q-0182 federated-world model · Q-0183 AI-ticket audience routing · Q-0184 memory
  scope · Q-0185 bot-site pitch), and promoted the Explore-hub + feedback-board plans (Q-0172).
- **#1135 · #1136 · #1137 · #1138 · #1139 · #1140 · #1134 (2026-06-19, ultracode-fleet close-out + Q-0181 ground-truth tooling)** —
  the fleet's close-out band + the ground-truth-audit work: `scripts/check_plan_code_drift.py` +
  the [ground-truth-audit protocol](operations/ground-truth-audit-protocol.md) (#1135, Q-0181), rebadging
  A3/A4 `historical` + wiring the drift check into `/session-close` (#1136), the fleet pre-flight
  overlap-check rule + `scripts/check_lane_overlap.py` (#1137/#1139), the premature-closure self-check idea
  (#1138), the Codex-safety-fix + sector-boot idea captures (#1134), and the recon-trigger docs + the
  [voice-brainstorm pack](operations/voice-brainstorm-pack.md) (#1140). Docs/tooling; newer than the #1110
  marker — recorded on sight (Q-0166).
- **#1131 (2026-06-19, mining hub declutter — Option A PR2: Character + Explore sub-hubs)** — split the
  16-button mining hub into the Option A information architecture (mining-hub-redesign): a top-level
  `🧍 Character` sub-hub and a `🗺️ Explore` sub-hub (`views/mining/explore_hub.py`,
  `MiningExploreHubView`). The Explore sub-hub is the seam the [federated Explore-hub plan](planning/explore-hub-federated-world-plan-2026-06-19.md)
  re-parents into a top-level world hub. Newer than the marker — recorded on sight.
- **#1132 (2026-06-19, B5 — Codex-review integration: routine fix-first + Hermes 6H pr-check skill)** —
  the Codex-review consumer wiring (Q-0174/Q-0180): routines fix flagged-real issues first; a Hermes
  6-hour PR-check skill. Recorded on sight.
- **#1130 (2026-06-19, open-question sweep + router-status detector + dashboard lockfile)** — recorded a
  batch of owner decisions, added a router-status next-free-Q detector, and a dashboard dependency
  lockfile. **#1127** — `chore(dashboard): refresh generated data` (per-source-merge cadence regen,
  Q-0167). Both recorded on sight.
- **#1129 (2026-06-19, docs/ideas — lock owner brainstorm design + ledger reconcile)** — locked the
  owner's approved brainstorm design into the idea docs and reconciled the ledger (added the
  #1124/#1125/#1126 entries above). Docs-only; newest merge — recorded on sight (Q-0166).
- **#1126 (2026-06-19, ideas — owner brainstorm capture)** — captured two owner-directed idea docs from a
  live brainstorm (the **federated Explore hub**: one world / each subsystem its own game; and the **AI
  correction-report → audience-routed ticket service**), indexed in `ideas/README` with subsystem tags.
  Later extended in-place with the owner's approved design (the three-track XP + hybrid-gear model; the
  unified tagged feedback board + dual-gate submission moderation; the opt-in/declared memory policy on
  `honcho-memory-evaluation`). Docs-only; recorded on sight.
- **#1125 (2026-06-19, tooling — ledger-drift checker hardening)** — reworked
  `scripts/check_current_state_ledger.py` (detection window now **scales to the reconciliation marker**;
  sharper benign-lag-vs-drift split) + its tests, and refreshed the `ledger-guard-benign-lag` /
  `ledger-window-scale-to-marker` idea docs (tooling + docs; recorded on sight).
- **#1124 (2026-06-19, docs — planning/audit/idea map cleanup)** — a durable plan index, rebadged stale
  plans/audits, idea subsystem tags, and de-staled routing pointers across `docs/planning/`,
  `docs/subsystems/`, and `roadmap.md` (80 files, docs-only; recorded on sight).
- **#1115 (2026-06-19, ideas — per-command feedback threads + idea→command mapping)** — captured two
  workflow/product ideas (per-command feedback threads · an idea→cog-command mapping) with their idea docs
  + README index entries (docs-only; merged to `main` just after this pass's marker — recorded on sight).
- **#1109 (2026-06-19, website two-site split — serial foundation S1 + S2 + P1)** — the first build wave:
  the public-data subset (`site.json` + the redaction-whitelist guard, S1), the submissions DB (S2), and the
  first bot-site page set (P1). The serial foundation the parallel P1–P8 wave builds on.
- **#1112 · #1113 · #1114 · #1116 · #1117 · #1118 · #1119 (2026-06-19, website two-site split — parallel
  back-half fan-out)** — the file-disjoint back half on the #1109 foundation: S1.1+P2 interactive command
  browser (#1112), P3 changelog/status templates (#1114, #1116), P4 public `/submit` intake (#1117), P5+P6
  dev-site moderation UI + GitHub-issue mirror (#1118), P7+P8 redaction-audit + deploy/env docs (#1113), and
  the `env-vars.md` freshness fix (#1119), capped by the **rollout + next-steps handoff** doc
  ([`operations/website-split-next-steps-2026-06-19.md`](operations/website-split-next-steps-2026-06-19.md),
  #1123). Reviewed + refactored in the ultracode pass (see
  [`operations/website-split-review-2026-06-19.md`](operations/website-split-review-2026-06-19.md)): the
  test-isolation `sys.modules` collision, the `_clean` C1 gap, the `chain` idea-mis-map, and the
  `env-vars.md` web-tier marker. All newer than the #1110 reconciliation marker (recorded on sight, Q-0166).
- **#1101 · #1121 (2026-06-19, dashboard generated-data refresh)** — the per-source-merge
  `dashboard-data-refresh` workflow (Q-0167) regen of `dashboard.json` (two cadence refreshes).
> *(Trimmed from the live ledger by the sixteenth Q-0107 pass — band-#1170, 2026-06-20.)*

- **#1099 · #1100 · #1102 · #1104 · #1107 · #1110 (2026-06-19, website two-site split — planning band, Q-0178/Q-0179)** —
  the public bot-site / private dev-site split planned end-to-end: the planning brief (#1099), the full
  implementation plan + file-disjoint **ultracode decomposition** (#1100), routing the control-panel-placement
  decision Q-0179 (#1102), locking the open decisions + resolving Q-0179 (#1104), making the §5 decomposition
  truly file-disjoint pre-ultracode (#1107), and the owner site-identity vision + fan-out enablers (#1110).
- **#1103 · #1105 · #1106 · #1108 (2026-06-19, workflow tooling + CI hygiene)** — `scripts/router_status.py`,
  a question-router digest reporting the next free Q + the open queue (#1103); Codex reviews the **final head**
  (`@codex review` on the session-card flip, #1105); the `pr-conflict-guard` now polls through GitHub's
  UNKNOWN-mergeability window (#1106); `.gitignore` ignores transient background-agent worktrees (#1108).
- **#1098 (2026-06-19, band-#1080 Q-0107 reconciliation pass)** — the docs-only reconciliation
  ([record](planning/reconciliation-pass-2026-06-19-band1080.md)): reconciled the ledger, planned the next band.
- **#1097 (2026-06-19, fleet A4 — diagnostic embeds → `services/`)** — the diagnostic embed builders
  relocated into the services layer (the ultracode-fleet Lane-A A4 unit; callers mapped first).
- **#1094 (2026-06-19, consistency-linter graduation — 3 rules flipped to error, Q-0170)** — the
  `back_button` / `panel_base_class` / `select_option_truncation` rules ran clean across #1056→#1062,
  so each `Rule.severity` flipped `"warning"`→`"error"` and `python3.10 scripts/check_consistency.py
  --mode strict` is now wired into `code-quality.yml` (deps block) + the `check_quality.py` local mirror.
  `edit_in_place` stays warn-only (BLOCKED on the AI-nav redesign).
- **#1081 · #1083 · #1084 · #1087 · #1092 (2026-06-19, ultracode-fleet wave A — helper extraction)** —
  the executed half of the [ultracode-fleet plan](planning/ultracode-fleet-plan-2026-06-19.md): paired
  helper-extraction / refactor slices — moderation helpers (#1081), governance exceptions (#1083),
  BaseView conformance (#1084), `utils/db` wrappers (#1087), blackjack state (#1092).
- **#1064 · #1079 (2026-06-19, repo-governance + supply-chain baseline + ultracode-fleet plan)** —
  #1064 added the open-source governance / supply-chain baseline (CodeQL workflow, `dependabot.yml`,
  issue/PR templates, LICENSE, SECURITY.md, CONTRIBUTING.md, CITATION.cff, dashboard-CI) + the
  repo-structure-improvement plan; #1079 added the ultracode-fleet plan that spawned waves A/B.
- **#1065–#1073 · #1075–#1078 (2026-06-19, dependabot dependency-bump band)** — the dependency bumps
  the new `dependabot.yml` (#1064) immediately raised: GitHub Actions majors (cache-5, codeql-action-4,
  github-script-9, checkout-7, setup-python-6) + pip deps (anthropic, uvicorn, httpx, fastapi, jinja2 —
  root + dashboard `requirements`). (#1074, the python-minor-patch dev group, remained open at this pass.)
- **#1061 (2026-06-19, dashboard generated-data refresh)** — `Merge pull request #1061 from
  menno420/bot/dashboard-refresh` — the per-source-merge `dashboard-data-refresh` workflow (Q-0167)
  regenerated the committed `dashboard/data/dashboard.json` from live source.
- **#1060 (2026-06-19, consistency-linter — AI-nav idea → executable plan, Q-0172 self-initiated)** —
  promoted [`ideas/ai-panel-inplace-navigation-2026-06-11.md`](ideas/ai-panel-inplace-navigation-2026-06-11.md)
  into [`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`](planning/ai-panel-inplace-navigation-plan-2026-06-19.md)
  (the only blocker for graduating consistency rule 1 `edit_in_place`); updated the ideas-README + roadmap.
- **#1055 (2026-06-18, dashboard generated-data refresh)** — `Merge pull request #1055 from
  menno420/bot/dashboard-refresh` — the per-source-merge `dashboard-data-refresh` workflow regen.
- **#1053 (2026-06-18, twelfth Q-0107 reconciliation pass — band-#1050)** — the docs-only
  reconciliation pass ([record](planning/reconciliation-pass-2026-06-18-band1050.md)): reconciled the
  ledger (added #1022/#1029, trimmed to the 20 newest → archive), planned the next band, reset the
  `Last reconciliation pass` marker to #1050.
- **#1052 (2026-06-18, dashboard generated-data refresh)** — `Merge pull request #1052 from
  menno420/bot/dashboard-refresh` — the per-source-merge `dashboard-data-refresh` workflow (Q-0167)
  regenerated the committed `dashboard/data/dashboard.json` from live source.
- **#1050 (2026-06-18, consistency-linter — embedded windowed-select helper + bounded-catalog triage)** —
  the design step the #1048 handoff named: refactored `views/paginated_select.py` to share **one**
  windowing core — a `SelectWindow` controller that manages a *band* of items (a windowed `Select` +
  ◀/▶ nav) inside **any host view**, removing only its own items on a page flip so it composes with a
  multi-control panel; `PaginatedSelectView` is now a thin wrapper over it (constructor unchanged) and a
  new `attach_windowed_select(view, options, on_select, …)` exposes the embedded path. **Triaged the 28
  `select_option_truncation` candidates → 15**: dogfooded the helper on `access_map`'s feature
  drill-down (`_FeatureDetailSelect` → `_attach_feature_detail_select`, a genuinely-dynamic select that
  could exceed 25), and **allowlisted 12** backed by a fixed in-repo catalog / game-data roster (btd6
  tower roster + live-events feed; the curated mining taxonomy market/recipe/workshop/gear selects) —
  same standard as the existing btd6-catalog allowlist entries (not the #1040 bug). The **15 remaining**
  are all genuinely guild-scaled embedded selects — the shared `views/selectors/` primitives
  (role/channel/multi/multi_role/subsystem; the API-ripple set) + the channels move/visibility/create
  panels, `settings/subsystem_view` edit/reset selects, `setup/sections/channels`, `access/explorer`,
  and `diagnostic/automation_panel` — see the ▶ Next-action handoff.
- **#1049 (2026-06-18, dashboard refresh)** — `Merge pull request #1049 from
  menno420/bot/dashboard-refresh` (newest-merge lag catch-up; recorded on sight per Q-0166).
- **#1048 (2026-06-18, consistency-linter — standalone select pickers → `PaginatedSelectView`)** —
  migrated the three cleanly-standalone single-select ephemeral pickers onto the shared
  `views/paginated_select.py` primitive: `settings/edit_enum` (`EnumSettingSelectView`/`_EnumSelect`
  → the `build_enum_select_view` factory), `roles/time_roles_panel` (`_TimeRemoveView`), and
  `roles/xp_roles_panel` (`_XpRemoveView`). Each retired **both** its `select_option_truncation`
  (31→28) and `panel_base_class` (29→26) consistency finding and fixed the latent #1040 >25-option
  silent-drop; the `baseview_inheritance` arch debt ratcheted 12→9. The remaining
  `select_option_truncation` candidates are all embedded in multi-control views (need an
  embedded-windowing design step — see the ▶ Next-action handoff).
- **#1046 (2026-06-18, dashboard generated-data refresh)** — `chore(dashboard): refresh generated
  data` — regenerated the committed `dashboard/data/dashboard.json` from live source (the cadence-regen
  routed to the docs-reconciliation routine in #1025).
- **#1045 (2026-06-18, dashboard-data-refresh CI fix)** — `fix(ci): make dashboard-data-refresh
  actually work` — corrected the dashboard-data-refresh workflow to use the PR-flow auto-merge path so
  the generated-data refresh lands instead of stalling.
- **#1042 (2026-06-18, repo-consistency-linter PR 1 — Q-0170)** — the owner-directed "CI but for
  UX/interaction inconsistencies" tool, `scripts/check_consistency.py` (stdlib AST over `disbot/views/`,
  `check_architecture`-style `Rule` registry + an `architecture_rules/consistency_exceptions.yml`
  allowlist, warn-only/disposable per Q-0105). PR 1 = the harness + **rule 1 (edit-in-place)**: a panel
  button/select callback that delivers its result as a standalone ephemeral instead of editing the panel
  in place (45 first-run candidates, allowlist empty). Built one rule per PR; rules 2+3 followed (#1043).
- **#1041 (2026-06-18, fishing reconciliation Codex follow-ups)** — addressed the Codex review on the
  fishing-v1→#1036-spec reconciliation: migration hygiene (the value-column drop), the legacy-count
  guard (a player who fished under the superseded interim catalog can have rows the current 21-fish
  catalog doesn't, so `!fishlog`/`!fishtop` count only current-catalog species), and a dependency tidy.
- **#1040 (2026-06-18, setup cog-routing picker pagination)** — the cog-routing select hard-capped at
  `visible[:25]`; the routable-subsystem registry has grown past 25 (35), so the cap silently dropped
  every cog past the 25th (moderation, role, settings, …) — an operator literally could not route them.
  `_operator_visible_cogs()` now returns the full sorted list and a new `_CogPickView(BaseView)` pages
  it into ≤25-option windows with ◀ Prev / Next ▶ nav. Bug already on `main`; a registry-drift class.
- **#1039 (2026-06-18, fishing v1 reconciled to the owner's #1036 design — Q-0175)** — the interim
  fishing v1 (#1033: 14 fish, 5 rarity tiers, coins per catch) was built before the owner's #1036 spec
  landed and contradicted it. Reconciled the shipped code to the spec: the 21-size-ranked-fish
  `data/fishing/fish.json`, the level/size-band deterministic-roll catch (7 levels × 3), a no-coins
  collection log (`economy_service` dropped from the fishing path; migration 076 drops the value cols).
- **#1038 (2026-06-18, BTD6 "which MK affects <tower>" — owner live-test)** — the model no longer
  assembles the class-wide MK list itself; `btd6_data_service`/`btd6_context_service` derive and list the
  class-wide Monkey Knowledge for a tower deterministically, and a sniper routing miss (the question
  not reaching the BTD6 path) was fixed in `ai_task_router`.
- **#1037 (2026-06-18, BTD6 round_cash identity ABR fix — Codex P2 on #1035)** — gated the inclusive
  range `identity` sentence to emit only when the cumulative subtraction reconciles with `range_cash`;
  it was contradicting `range_cash` for ABR ranges spanning the unplayed rounds 1-2 (the cumulative
  totals start at round 3). Self-validating, so the existing `cumulative_note` covers the excluded case.
- **#1036 (2026-06-18, fishing v1 + open-world expansion plan — Q-0175, docs-only)** — captured the
  owner's fishing/boat brain-dump as a buildable plan: Phase 1 (fishing v1 — 21 fish, 7 levels × 3 fish,
  reuses tier/`game_xp`; one character with named swappable gear-type loadouts, gear never required —
  only boosts bonuses) + Phase 2+ (boat as 2nd home base · bounded travel · seed-grid destinations with
  coordinates/biome, ties Q-0173); indexed on the roadmap.
- **#1035 (2026-06-18, BTD6 AI answer fixes — owner live-test screenshots)** — fixed 4 owner-spotted
  BTD6 answer bugs at the deterministic data/grounding/tool layer: MK reference reply grammar +
  tab-wide scope note (Come On Everybody / Flanking Maneuvers disclosure); grounded the total bloons
  entering a round so "how many bloons spawn on rN" is answerable instead of refused (the derived sum
  tripped the value-only faithfulness guard); `round_composition` `roundset_label` so ABR vs standard
  figures don't read as self-contradiction; `round_cash` ready-to-quote inclusive-range `identity`
  sentence (a same-day P2 follow-up gated it to ranges where the cumulative subtraction reconciles —
  it was emitting a contradictory identity for ABR ranges that span the unplayed rounds 1-2).
- **#1034 (2026-06-18, Codex edits-live note — Q-0174 resolved, docs-only)** — documented that Codex
  has no write access: its "make changes" output is a comment describing a diff in its own sandbox, so
  agents read the proposed change from the comment, verify against `main`, and apply it themselves
  (never hunt for a phantom Codex branch/PR); Q-0174 resolved → trial comment-only as-is.
- **#1032 (2026-06-17, settle decisions + Codex integration — docs-only)** — settled **Q-0173** (the
  mining grid world = a seed-deterministic procedural grid we generate, not literal Minecraft-terrain
  replication) and **Q-0174** (Codex review integration: routines check Codex first but verify, the
  "real bug" bar, the issue-only Hermes 6H PR-check spec); fixed 3 verified-real Codex-flagged drift
  items (`/session-close` 10th-PR→30-PR cadence · `roadmap.md` "decade queue" → full-band wording ·
  a session card's `Previous-slice review` → `Previous-session review`).
- **#1031 (2026-06-17, local character-render preview tool — Q-0172, self-initiated)** —
  `scripts/preview_character.py` renders the live V-16 compositor (`utils/character_render.py`) to a PNG
  locally so sprite positioning is a render→look→tune-`manifest.json`→re-render loop instead of manual
  Discord uploads; Q-0105 dev tool (stdlib + Pillow, not CI-wired, disposable). Also recorded the
  owner's vault-cap decision (keep it soft / warning-only).
- **#1030 (2026-06-17, Hermes plain-language house style — Q-0168)** — promoted the owner-approved
  sample to a canonical `_house-style.md` (5 rules + the morning-briefing exemplar) and rewrote the
  owner-facing output skills (`morning-briefing`/`repo-health`/`open-questions`/`idea-spotlight`/
  `review-merge`) to cite it and speak plainly (jargon translated, grouped not listed); the commands +
  rate-limit budgets are unchanged. Owner manual step: redeploy on the VPS.
- **#1029 (2026-06-17, idea→plan gate opened — Q-0172)** — the owner directive that removed the
  old idea→plan→build approval gate: any agent may now promote a `docs/ideas/` idea into a
  `docs/planning/` plan and build it without owner approval, flagged on the run-report
  `⚑ Self-initiated:` line for review; `scripts/check_phase_gate.py` is now **advisory-only** (a
  "bugs-first season" readout, no longer a block). Recorded in the CLAUDE.md working agreement +
  router Q-0172; also slimmed the Hermes dispatch-skill batch-1 docs. Safety brakes (irreversible/external) unchanged.
- **#1028 (2026-06-17, procedures→skills conversion plan — docs-only)** — captured the 33-procedure
  skills-conversion inventory (A/B/C buckets) as an executable plan
  (`planning/procedures-to-skills-conversion-plan-2026-06-17.md`): the thin-pointer convention, the
  must-NOT-move safety list, the batched build order. Owner-confirmed approach (relocate procedures to
  on-demand skills, keep a thin pointer + the binding rules in CLAUDE.md). Extends Q-0170.
- **#1026 (2026-06-17, autonomous-routines review + workflow hardening)** — first-unattended-run review:
  hardened the routine prompts (full-band planning depth + the ⚠️ PLAN BACKLOG THIN flag Q-0164;
  drift-on-sight Q-0166; `Run type:` labels Q-0165), added the `dashboard-data-refresh` workflow (Q-0167
  — per-source-merge regen of dashboard.json), and approved the Hermes plain-language house-style sample
  (Q-0168). Mapped the owner's brain-dump observations to their durable homes.
- **#1025 (2026-06-17, dashboard.json freshness reporter)** — warn-only structural-drift reporter
  (`check_dashboard_data.py --drift`, identifier-sets only, never the volatile churn) + regenerated the
  stale committed dashboard.json + routed the cadence-regen to the docs-reconciliation routine.
- **#1024 (2026-06-17, BTD6 paragon-ability + boss tier-HP floors — BUG-0009 §7.5/§7.6)** — scheduled
  dispatch, empty work order → built the two BTD6 deterministic-floor shapes current-state named as
  still-valid empty-fire candidates (the night queue was fully consumed). **Two floor builders on the
  `_BTD6_LIST_BUILDERS` seam:** `deterministic_paragon_ability_roster_reply` (paragon sibling of the
  hero-ability roster — lists a paragon's curated activated/passive abilities off `paragon_abilities.json`
  via `btd6_stats_service`, owns the empty case so Apex Plasma Master never gets an invented ability;
  mutually exclusive via the literal `paragon` token) and `deterministic_boss_hp_comparison_reply`
  (§7.5 comparison — ranks bosses by per-tier health off `bosses[].tiers`/`.elite_tiers`, two shapes:
  named-boss ranking + superlative-over-all, **tier 1-5 REQUIRED** so it fails closed on an ambiguous
  no-tier ask, elite handling, defers on an immunity cue). Each adds a `_SHOULD_FIRE` exclusivity-corpus
  entry + a test file. The proven ungated BTD6 floor lane is now essentially exhausted (all towers/heroes/
  paragons/bosses/MK/relics/bloons roster+comparison shapes covered). `check_quality --full` green
  (10468) · arch 0 · check_docs ✓.
- **#1023 (2026-06-17, moderation per-action DM policy — Q-0147)** — scheduled dispatch, empty work
  order → built the band-#1020 §4 named ungated slice (the `moderation-dm-config` plan). Turns the
  `dm_on_action` master switch into an owner-controlled **per-action** DM policy on the existing
  audited `moderation_service` seam — **no migration, no new module**: new `MOD_DM_ACTIONS`
  (`moderation_dm_actions`) key; a `dm_actions` field + validated `dm_action_set` property +
  `parse_dm_actions` helper on `ModerationPolicy`; `_notify_target` now gates on master **and**
  per-action membership; a `dm_actions` `SettingSpec` (csv subset of warn/timeout/kick/ban) on
  `!settings → Moderation` + `dm_on_action` relabelled the master switch (schema v6→v7). **Deviation
  from the plan (documented):** default = all four notify-eligible actions (not `warn,timeout`) so the
  master switch keeps today's behaviour and an owner *narrows* it — a `warn,timeout` default would
  silently drop kick/ban DMs for guilds that already enabled the switch; `auto_delete` is excluded
  (never reaches `_notify_target`). `check_quality --full` green (10443) · arch 0 · check_docs ✓.
- **#1022 (2026-06-17, eleventh Q-0107 reconciliation pass — band-#1020)** — the band #991→#1020
  docs-only reconcile + planning pass (issue #1021): reconciled the ledger, planned the band-#1020
  decade queue, promoted the moderation-DM-config idea → a turn-key plan, added a ledger-tally
  soft-lint idea, and reset the marker #990→#1020.
- **#1020 (2026-06-17, manifest spine PR3 — control-API manifest read + cross-manifest
  reconciliation)** — scheduled dispatch, empty work order → advanced the manifest-spine thread (PR1
  #1018 + PR2 #1019 shipped; the execution plan named PR3 next). Makes the typed manifest **readable
  over the live control API** and **self-reconciling** (the spine's core purpose — verified, not
  guessed, metadata): **(1)** `GET /control/manifest` on the dormant control API (token-only, global —
  mirrors `/control/help/catalogue`) serves `CommandManifest` + `PanelManifest`, building on demand
  when the startup cache is empty; + `control_client.get_manifest()`. **(2)** `core/runtime/manifest_reconciliation.py`
  — a `panel_action`-classified command whose subsystem owns no registered panel is a
  `dangling_panel_action` finding, surfaced in `CommandManifest.to_dict()["findings"]` (was reserved
  `[]`) + the `command_manifest` diagnostics. **(3)** CI drift guard (`test_manifest_drift.py`): the
  AST `scan_commands` `panel_action` subsystems ⊆ the runtime `PanelManifest` subsystems — the cheap
  "AST is drift-detection" check (holds: {mining, moderation, role}). **(4)** the manifest envelope's
  `bot_build` now defaults to the deploy SHA (`RAILWAY_GIT_COMMIT_SHA`, short) so the live read is
  freshness-badged. `check_quality --full` green (10431, +16) · arch 0. **Deferred to PR4** (no
  declared button→command binding yet — verified: `panel_action` cmd names ≠ button action-id
  suffixes, so a name-level guard would be false-positive-prone, Q-0120): per-button `command` binding
  + button-level reconciliation + the panel-layout editor (owner-paced control-API *writes*).
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
  gates command/panel management) — PR1 `CommandManifest` (#1018) + PR2 panel registry/`PanelManifest`
  (#1019) + **PR3 control-API `/control/manifest` read + cross-manifest reconciliation + AST drift
  guard + deploy-SHA badge (#1020)** all shipped. **The remaining manifest-spine work is PR4 — the
  panel-layout editor (H / L3 "move buttons"): a declared button→command binding + button-level
  reconciliation + the DB-backed layout overlay + the website editor.** PR4 is **owner-paced** (it is
  a control-API *write* surface, needs `CONTROL_API_TOKEN`) **and architecturally significant** (the
  binding must be declared across every persistent view — verified this session that `panel_action`
  command names do NOT map to button action-ids, so it can't be inferred). So the manifest spine's
  next pure ungated read-code is **exhausted** — a future empty fire should plan PR4 (with the owner
  on the write-side pacing) or take a different ungated lane. The committed `dashboard.json` export of
  the manifest was dropped from PR3: the export can't import disbot, so it stays the AST `cogs` view;
  the live truth is `/control/manifest`. The global-settings runtime tier (Q-0157) stays its own
  owner-paced session.
- **#1016 + #1014 (2026-06-17, dashboard R3 hardening + vision-roadmap reconcile)** — the overnight
  dashboard run's hardening + docs tail. **#1014 (R3 — live-surface hardening):** the finalized-vision
  plan's reviewer note R3 (the control panel is public+live but had no rate-limiting and only
  `SameSite=Lax`) — adds a per-session **CSRF token** (signed-cookie, hidden field, constant-time
  reject) on every `/admin/{guild}` POST, a stdlib sliding-window **rate-limiter** (`dashboard/ratelimit.py`)
  on `/auth/login` (per IP) + edit POSTs (per user), and a defense-in-depth per-(guild,user) write
  limiter in `disbot/control_api.py` (HTTP 429, dormant-safe). Additive; the audited-seam write path
  is unchanged. **#1016 (docs):** reconciled the dashboard vision roadmap (`dashboard-vision-finalized-state.md`)
  to mark Phase E (#1013) + R3 (#1014) shipped. Dashboard read+write surfaces are now live + hardened;
  the manifest spine (#1018–#1020) is the next structural lane (PR4 owner-paced).
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
- **#1005 · #1006 · #1007 (2026-06-17, dashboard-vision docs + a routing-corpus test)** — the
  dashboard finalized-vision plan review + owner panel decisions (#1005 review/close · #1006 solidify
  with owner panel decisions) and the BTD6 community-shorthand class-guard corpus (#1007, test-only).
  Docs/test band; no runtime change.
- **#1004 + #1003 + #997 (2026-06-16, loop-hygiene band — union-merge ledger fix + ideas + night
  queue)** — one grouped docs/repo-infra entry (no `disbot/` runtime). **#1003 (`fix(repo)`):** set
  `merge=union` on the append-only ledger files (`.gitattributes`) so parallel sessions stop
  livelocking on ledger-line merge conflicts — the structural fix for the recurring conflict class
  the reconciler used to resolve by hand. **#1004 (`docs(ideas)`):** tied off the #995 backlog-hygiene
  grooming and filed two captured ideas. **#997 (`docs(planning)`):** seeded the grounded
  [night-work queue](planning/night-queue-2026-06-16.md) so the overnight scheduled dispatch fires
  advanced real BTD6 deterministic-floor work (#1008–#1012) instead of stalling on the thin `ready`
  queue — now fully consumed.
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
- **#1027 (2026-06-17, generated-artifact freshness umbrella)** — generalized #1025 into
  `scripts/check_generated_artifacts_fresh.py`, a registry-driven warn-only umbrella over all three
  committed-generated families (dashboard.json · `env-vars.md` · `docs/agent/generated/*.context.md`);
  Q-0105 dev tooling (read-only/stdlib/disposable), not hard-CI-wired.
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
- **#941 + #929 (2026-06-18, the two `needs-hermes-review` carve-outs — image moderation + security tiers 1+2 — now MERGED)** — both Q-0117 anti-monoculture review carve-outs landed on the same day (#929 04:17, #941 04:24): **#929** = security service tiers 1+2 (raid detection + account-age filter, Q-0111); **#941** = image moderation. Recorded as shipped here (the prior passes carried them as "in flight, awaiting human merge" — that state is now stale; the band-#1050 pass corrected the ▶ Next action + plan to drop them as open gates).
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
- **#932 (2026-06-15, docs reconciliation — band-#930, ninth Q-0107 pass)** — ninth Q-0107 docs-only
  reconciliation + planning pass (fired by `reconcile` issue #931). Reconciled the ledger (added the
  #915…#928 Hermes model-swap / ops-docs band as one grouped entry; archived #862/#859/#855 to hold
  the ratchet at 20); **FIXED a control-plane drift** (the Gates bullet still claimed the autonomous
  loop had never self-fired — stale, since trigger issue #931 was authored by the PAT owner, which
  only happens when `ROUTINE_PAT` is set and the loop self-fires); scored the band-#900 queue +
  planned the next band ([`reconciliation-pass-2026-06-15-band930.md`](planning/reconciliation-pass-2026-06-15-band930.md));
  promoted the now-ungated games-economy faucet/sink diagnostic idea to a turn-key plan; reset the
  cadence marker #900→#930 (next at #960). Open-PR disposition (Q-0125): only #929 open
  (`needs-hermes-review` carve-out). Docs only.
- **#926 (2026-06-15, BUG-0009 slice 2 — deterministic "Geraldo items per level")** — the next ▶
  startable plan slice (the live ▶ pointer's named next step), same proven shape as slice 1 (#924).
  "what items does Geraldo unlock at each level" had the model assemble the level→item grouping
  itself and mislabel which item unlocks when — every name grounded, so the value-only faithfulness
  guard passed the wrong *grouping* (this class never reaches the post-hoc roster floor). Fix: the
  deterministic layer OWNS the labelled answer. `btd6_data_service.geraldo_items_by_unlock_level()`
  is the ascending level→items map; `btd6_context_service.deterministic_geraldo_per_level_reply`
  detects the per-level / by-level / "level N" shape (Geraldo cue + level/list cue; `None` for
  single-item lookups like "what does the Genie Bottle do" and strategy questions) and formats the
  full grouping, a single level's unlocks, or an honest "no new item unlocks at level N". The same
  PR also fixed the owner's third named mislabel (**slice 2b — game mode groupings**):
  `btd6_data_service.modes_by_kind` + `deterministic_modes_reply` own the difficulty→mode→modifier
  grouping (CHIMPS is a mode, not a difficulty), guarded against the qualifier over-route ("which
  towers work on impoppable mode" defers to the model). All three BUG-0009 builders now front one
  dispatcher `deterministic_btd6_list_reply`, served as the pre-emptive BTD6 floor in
  `natural_language_stage` (MK → Geraldo → modes) — the last family (newest-towers, data-gated)
  appends its builder there. `check_quality --full` green (9889); arch 0; +29 tests. One BUG-0009
  family remains OPEN (newest-towers ordering, data-gated).
- **#924 (2026-06-15, BUG-0009 slice 1 — deterministic "Monkey Knowledge related to <tower>")** —
  the next ▶ startable plan slice (band-#900 decade queue slot 6; clears the headline of the OPEN
  AI list-assembly bug). "what are all the monkey knowledges related to the farm" listed the whole
  22-entry Support *category* and mislabeled it farm-related — every name was grounded, so the
  value-only faithfulness guard passed the wrong *grouping* (and this class never reached the
  post-hoc roster floor). Fix follows the proven shape (the deterministic layer OWNS the labelled
  answer): `btd6_data_service.monkey_knowledge_referencing(tower)` derives the relation from the MK
  description text (canonical/upgrade-path name → strong; alias → weak, suppressed when the MK
  strongly references a *different* tower or is a Powers/Heroes-tab point), memoized per dataset
  version; `btd6_context_service.deterministic_mk_reference_reply` detects the "which MK relate to
  <tower>" shape (`None` for single-MK lookups / strategy / no-tower) and formats the honest list;
  wired as a **pre-emptive floor** on the BTD6 path in `natural_language_stage` (before the model,
  since this class passes the value guard). Farm now lists the 7 genuinely-referencing MK, not 22;
  ordinary BTD6 questions still reach the model. Two BUG-0009 families remain OPEN (per-level item
  lists · newest-towers). `check_quality --full` green (9863); arch 0; +14 tests.
- **#920 (2026-06-15, welcome phase 2 — optional PIL greeting card on join)** — band-#900 decade
  queue slot 7, the safety-lane quick-win (Q-0110). Adds a `welcome_card_enabled` setting (off by
  default) that attaches a rendered greeting card (avatar initials-disc + greeting + member number)
  to the join embed, degrading to embed-only when Pillow is unavailable or the toggle is off. The
  `render_welcome_card` prototype graduated from the UX-lab gallery to the production renderer
  `disbot/utils/welcome_render.py`; the gallery now re-exports it, so the preview and the live
  feature share one renderer (one source of truth — the prototype/feature split is gone). Wired
  end-to-end: settings_key → `welcome_config` default + `WelcomePolicy.card_enabled`/`show_join_card`
  + `load_policy` read → schema `SettingSpec` → `welcome_service.handle_member_join` render+attach.
  No-network/content-free (the embed still carries the real avatar thumbnail). `check_quality --full`
  green (9847); arch 0; settings declared⇔consumed parity stays green (now 64 declared, 0 dead).
- **#918 (2026-06-15, settings reverse-parity invariant — complete the declared ⇔ consumed
  bijection)** — second slice of the #917 dispatch run, promoting that PR's Q-0089 idea straight to
  shipped code. #917 added settings *forward* parity (every declared `SettingSpec` has a reader);
  this adds the *reverse* direction —
  `test_settings_declared_vs_consumed_parity.py::test_every_literal_setting_read_targets_a_declared_setting`
  asserts every literal `resolve_value`/`resolve_setting(g, subsystem, name)` read targets a
  *declared* setting. Closes the silent-bug class where a typo'd/stale read
  (`resolve_value(g, "welcom", "enabld", default)`) never matches a written key and resolves to the
  fallback forever (invisible, uncaught). 0 violations across 48 literal reads; reuses the same AST
  walk; verified to fire. `check_quality --full` green (9811); arch 0; test-only.
- **#917 (2026-06-15, P1-3 contract invariants — close the cross-cutting "stays fixed" layer)** —
  the next ▶ startable plan slice (band-#900 decade queue slot 3 · hardening roadmap §P1-3). Reviewed
  all four named tracks and closed the **two** genuine buildable-now gaps with CI-runnable AST
  invariants, plus a [disposition doc](planning/production-readiness/p1-3-contract-invariants-disposition-2026-06-15.md)
  closing the other two. **Settings** (the explicitly-named missing invariant — settings map
  §Required #3 / §Bugs): `tests/unit/invariants/test_settings_declared_vs_consumed_parity.py` proves
  every declared `SettingSpec` (63) has a runtime consumer across all four real read patterns
  (literal `resolve_value`/`resolve_setting`, `resolve_batch`/dynamic-name whole-subsystem reads,
  and key-constant/raw-key references incl. the binding/governance lane) — **0 dead settings**, so a
  future editable-no-op fails CI. **Games**: a third check on `test_game_wager_write_boundary.py`
  (`test_two_sided_economy_calls_are_accounted_for`) — the hardcoded `_WAGER_FILES` fence only caught
  *deletion* staleness; the new check fails on a *new* two-party game pairing
  `economy_service.credit`+`.debit` outside `game_wager_workflow` even without `allow_overdraft`
  (the mint signature). **AI** closed (34/34 catalogue/eval ratchet); **BTD6** source-provenance
  invariant-covered, per-derived-value attribution = design-for-review residual. Both new guards
  verified to fire. `check_quality --full` green (9810); arch 0; test-only + docs.
- **#912 (2026-06-15, mining Slices E + F — respec polish + skill/milestone titles)** — the last two
  ▶ startable slices of the structures/skill-tree plan, closing the lane (D/A/B/C already shipped).
  Built **away from** the one open PR (#911, owner's live mining-hub UX restructure on
  `main_panel.py`/`gear_panel.py`) to avoid collision: Slice E lives in `skill_service`/`skills_panel`,
  Slice F's title display goes on the `character_panel.py` aggregator + a `🏆 Titles` button on the
  Skills panel (not the main hub). **Slice E (respec polish):** the Respec button now opens a confirm
  card (cost + point preview, nothing charged until you choose) and offers a cheaper **single-branch**
  respec (`skill_service.respec_branch`, same audited economy lane / one-transaction atomicity).
  **Slice F (titles):** a pure `utils/mining/titles.py` catalogue whose **earned** set is *derived*
  from existing progression (skill branch at cap · deepest biome · game level) — nothing granted on a
  mutation path; only the equipped *choice* persists (`mining_player_state.equipped_title`, migration
  074) via `services/title_service.py` (the `set_equipped_title` write primitive on the RS02 boundary
  ratchet), displayed only while **still earned** (a respec silently un-displays a mastery title).
  Surfaced via `!titles` + a `🏆 Titles` Skills-panel button + the Character embed; **additive** — no
  title equipped → byte-identical. Depth-milestone titles are biome-*named* so they extend when the
  **P6 grid** (owner-flagged) deepens the world. Numbers pinned in
  [`respec-numbers-2026-06-15.md`](planning/respec-numbers-2026-06-15.md) /
  [`titles-numbers-2026-06-15.md`](planning/titles-numbers-2026-06-15.md). `check_quality --full`
  green (9808); arch 0.
- **#910 (2026-06-15, mining Slice C — the Home structure: character-card backdrop)** — the next
  mining-structures slice (the plan's last startable structure), built on a fresh resume now that
  **#905 (Forge)** shipped the generic `mining_structures` foundation; zero open PRs at start (no
  collision). A **built** Home (coin + material sink) that personalizes the Character card —
  **art-light v1**: Home level selects a backdrop colour (Cozy Cabin → Stone Keep → Grand Hall),
  **no sprites**, so unrelated to the owner-blocked V-16 phase-2 PNG pack. **Fully additive** — Home
  level 0 renders **byte-identical** (proven by test). Generalized #905's forge-specific
  `build_structure` off a per-structure registry in `utils/mining/structures.py`
  (`build_cost`/`level_name`/`max_level`/`display_name`; forge helpers delegate, byte-identical);
  `utils/character_render.py` gained `CharacterSpec.backdrop` + `home_backdrop(level)` wired through
  `render_character_for(..., home_level=)` at both card render sites; UI =
  `views/mining/home_panel.py` + a `🏠 Home` hub button + `!home`. Numbers pinned in
  `docs/planning/home-numbers-2026-06-15.md`. `check_quality --full` green (9782); arch 0.
- **#906 (2026-06-15, Railway log-triage analyzer — Slice 4, Q-0130)** — the band-#900 queue's
  reserved autonomous-loop slot, taken because the work order was empty/stale and the mining lane
  it pointed at was **in flight as #905** (Forge, parallel session — not duplicated). The
  `superbot-log-triage` skill's error-scan + crash-loop steps used to ask the model to *eyeball*
  raw logs and group by hand — the fragile "model assembles the answer" class. New
  **`scripts/hermes/log_triage.py`** (stdlib, read-only, **content-free**) owns those steps
  deterministically: parses the `railway_logs.py` text format (or stdin/file), groups errors by
  signature (traceback · login/connection · database · command/interaction · generic), **redacts**
  every example (snowflakes/tokens/emails/urls/ips → placeholders — no log bodies/PII leak),
  detects restart loops, and prints a one-line production status + the report blocks the skill
  pastes verbatim. Skill doc rewired (steps 2–3 → pipe the analyzer) + the `log-triage/SKILL.md`
  artifact regenerated. 18 tests; `check_quality --full` green (9737); arch 0. **Slot 4 done; the
  read-only Railway *token* is still the only thing gating live-data triage (owner-provisioned).**
- **#905 (2026-06-15, mining Slice B — the Forge structure: gear-tier crafting gate)** — a
  **dispatched (owner-directed)** mining work order. *(Dispatch note: the order asked for Slice D /
  §7.4 capped skill tree, but that **already shipped as #891**, and the "retire the duplicate
  `docs/plans/…` doc" precondition was moot — no such file/dir exists; per the dispatch routine's
  already-shipped rule the run built the genuine **next** plan slice instead. Recurring Q-0142
  dispatch-by-prediction misfire — flagged for the owner.)* A **built** structure (coin + material
  sink) on the **generic `mining_structures` table** (migration 073 — reused by Slice C Home) +
  `utils/db/games/mining_structures.py` (`set_structure_level` on the RS02 boundary ratchet); pure
  `utils/mining/structures.py` (forge build-cost ladder + the `equipment.gear_tier`-derived
  requirement map). **Gates only the top two gear tiers** — gold → Forge I, diamond → Forge II;
  bronze/iron/silver gear, tools, and structures stay forge-free, so most progression is unchanged
  (a deliberate, documented, reversible behavior change for end-game gear). `mining_workflow.build_structure`
  (coin debit + material consume + level raise in ONE transaction, the `vault_upgrade` precedent);
  a `_forge_gate` on `craft`/`quick_craft` that does **zero extra I/O** for forge-free recipes
  (existing craft paths unchanged — characterization net stays byte-identical). UI: `🔥 Forge` hub
  panel + `!forge` + the recipe browser shows the lock. Numbers pinned in
  [`planning/forge-numbers-2026-06-15.md`](planning/forge-numbers-2026-06-15.md). `check_quality
  --full` green (9754); arch 0.
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
