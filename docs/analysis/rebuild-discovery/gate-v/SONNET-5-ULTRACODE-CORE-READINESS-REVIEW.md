# SONNET-5-ULTRACODE-CORE-READINESS-REVIEW

> **Status:** `audit` — Arm A (Claude Sonnet 5, Anthropic Ultracode) of the GATE V verification
> fleet reviewing the SuperBot fresh-rebuild program. PRIMARY owner of the sequencing verdict,
> the architecture-invariant pressure-test, and the games-deferral design logic
> (`docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md` §2). Read-only throughout; this
> file is the review's single permitted write. Other arms own source/test truth (Codex, Arm B),
> external/migration/live-GitHub truth (ChatGPT Agent Mode, Arm C), and empirical live proof
> (operator live-testing, Arm D) — this report cites them as consumers, not as verified inputs.
>
> **Method.** This review was produced by an 11-agent internal research fleet: four parallel
> research lenses covering L0 (foundation/kernel), L1a–c+ (operator spine & presentation), L2
> (deterministic non-game foundations), and L4/L5 (post-core platform & control plane); three deep
> PRIMARY-deliverable drafts (sequencing, architecture-invariants, games-deferral design); and
> three independent adversarial verification passes, one per draft, each tasked with actively
> trying to refute the draft it reviewed. **Every claim below reflects the post-adversarial,
> corrected version** — where a verifier found an error, the correction is applied directly rather
> than reporting the original claim; the adversarial passes' own findings are cited so the
> correction is checkable. Evidence labels follow §3.2 (`CONFIRMED`/`INFERRED`/`STALE`/
> `CONTRADICTED`/`UNVERIFIED`), tagged `source-read` throughout — no pytest suite was executed
> against a live Postgres in this sandbox (unavailable, per §3.5); two test suites *were* actually
> run and are marked `test-confirmed`: `tests/unit/tools/test_grammar_spike.py` (13 passed) and
> `tests/unit/parity/` (10 passed, 1 skipped).

---

## 1. Executive verdict

**Gate V does not yet lift for the program as a whole, but the blocking conditions are narrower
and more tractable than the frozen corpus implies, and none of them require building any L3 game
feature.**

The single most consequential finding of this review is that **the rebuild's strongest empirical
argument for its own urgency is not what the frozen documents say it is.** `FINAL-REVIEW.md`
cites two live production money bugs (deathmatch PvP double-settle, blackjack free-tournament
double-pay) as proof that the unbuilt K7 workflow/compound-op engine and its `settle_once` seam
are needed "structurally" before anything else. Source verification this session found that the
fix pattern for both bugs — `SettleOnceMixin` (`disbot/utils/terminal_guard.py:44`) — **already
exists, is already tested, and is already adopted in 4 of the 5-6 places that need it**; both bugs
are non-adoption gaps in the current bot, fixable today in a small, contained, reversible PR,
**independent of K7, independent of Gate-0, independent of any L3/L4/L5 sequencing decision**.
This does not mean K7 is unnecessary — a kernel-owned, non-optional version of this pattern is a
real and durable improvement over "a mixin a class must remember to inherit" — but it means the
program's most emotionally load-bearing justification for building games-adjacent kernel
infrastructure early is not, on inspection, an argument for building games early at all.

Layered on top of that: **K7 itself has zero code, zero prototype, and zero oracle** — the
starkest validation gap of any component in the L0 kernel, disproportionate to its stated
criticality ("the strand-2 keystone," "the largest kernel band"). **Two hard gates block all
new-repo code** (Gate-0 owner ratification of 12 `Q-D` rows + `L-21`, and the Phase-2.5 substrate
cold-start A/B) and **neither has started**, despite Gate-0's own README naming the ratification
sitting "step 1 of what's next," as of a 2-day-old gap at review time. Until these lift, no L0
component can honestly be `READY_FOR_TEST_DESIGN` against *new* code, only against the *current*
bot's already-shipped analogues.

**On sequencing specifically:** the frozen build order's L3-before-L4/L5 half has **no supporting
dependency edge anywhere in the codebase** — an exhaustive, independently-cross-checked grep of
every L4/L5 module found zero imports of, or references to, any L3 game/wager/session module. The
one real, load-bearing dependency the program's K7/G-12 argument rests on — turn-based,
dual-entry-point settlement concurrency — is **already substantially proven by non-game production
code** (economy, treasury, shop-purchase, xp-curve, 4-of-12 leaderboard providers) and the two
narrow slices that are genuinely game-unique (accept-handshake turn concurrency; `G-17`
tournament-lobby pot/checkpoint settlement) have concrete, cheap, **headless, non-Discord**
deterministic replacement oracles that can be built now, before any sequencing decision is even
made. **Recommendation: Sequence C** (capability-class, with a narrow, bounded K7-concurrency
spike interleaved early, essential L4/L5 platform work proceeding without an L3 gate, and true
game *features* — mining's world, casino's tables, blackjack's UI, wild encounters — deferred
freely) over both the frozen order (Sequence A, whose L3→L4/L5 edge is fabricated) and strict
games-last (Sequence B, which over-reads "defer games" as "defer the one concurrency contract
everything downstream needs").

**On readiness generally:** L1a+L1b (19 rows, the operator spine) are genuinely owner-decided and
current — all 8 queued bug fixes were independently re-verified present at HEAD. Everything from
L1c onward (34+ rows: L1c, L2, L3, L4, L5) is still capstone-inherited, not owner-walked — and this
review's own fresh research surfaced **a sixth and even a de-facto seventh capstone-accuracy
contradiction** beyond the Stage-2 walk's already-known five: the L1c visual card engine (already
built, 517 lines, 5 live consumers, misclassified as "ADD-from-scratch") and the L5 boards family
(already has a complete, tested create→moderate→GitHub-mirror pipeline on the web tier, missed by
both the capstone and the walk doc's own contradiction sweep because it lives in `botsite/`/
`dashboard/`, not `disbot/cogs/`). The web dashboard's live editor — which even the walk doc's own
*correction* frames as the one genuinely-new part of row 49 — turns out to already exist too
(`disbot/control_api.py`, 861 lines, 45 tests). **The frozen capstone corpus systematically
undercounts what already ships whenever the artifact lives outside `disbot/cogs/*.py`.**

None of this changes the underlying grammar-fit verdict (**GO-with-amendments** stands); it
changes *what remains to prove* and *in what order*, and it identifies several small, contained,
reversible fixes that should not wait for any gate.

---

## 2. Verified current state

- **HEAD:** `cf5a234` (`Merge pull request #1749 from menno420/bot/dashboard-refresh`) on `main`;
  this review's checkout is `claude/gate-v-arm-a-review-qsn378`, identical tip. `git log
  --oneline -30`, independently checked by three lenses against their own scopes, shows the last
  30 merges are entirely CI/tooling/reconciliation work (ruff migration, CodeQL watchdog, dashboard
  refreshes, the 35th Q-0107 pass) — **nothing touches kernel code, `sb/`, or any runtime file any
  lens's scope depends on.**
- **Open PRs:** exactly one — **#1750**, `docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md`
  itself (the launch pad this fleet executes), not yet merged to `main`. No other open PR exists to
  reconcile against.
- **Claims:** `docs/owner/claims/` contains only its `README.md` — no active claim files. No
  parallel-agent collision risk detected for this scope.
- **Reconciliation cadence:** last Q-0107 pass at PR #1740 (band-1740); next due at #1770 per
  `check_reconciliation_due.py`'s cadence. Not yet crossed as of HEAD.
- **Two hard gates, both unstarted, both fully blocking new-repo (`sb/`) code:**
  1. **Gate-0 owner ratification.** `docs/analysis/rebuild-discovery/foundations/gate-0/
     owner-decision-packet.md` (dated 2026-07-04) renders 12 owner-only rows (`Q-D5, Q-D8, Q-D13,
     Q-D14, Q-D15, Q-D16, Q-D17, Q-D18, Q-D19, Q-D20, Q-D21, Q-D24`) plus `L-21` for the owner's
     ruling, each currently shipping a conservative built-until-ruled default. `gate-0/README.md`
     §6 names this sitting **"step 1 of what's next,"** *before* the Phase-B L0 build. A grep of
     `docs/owner/maintainer-question-router.md` for every `Q-D` identifier returns **zero
     matches** — none of these twelve-plus-one items has been routed to the router that is this
     project's own designated durable home for exactly this kind of open owner question. At HEAD
     (2026-07-06), this is a 2-day gap with no visible progress on the stated literal first item of
     the critical path.
  2. **Phase-2.5 substrate cold-start A/B.** `docs/current-state/S3-ai-memory.md:42-43,79,96-107`
     confirms the substrate-kit's declaration layer is finalized (#1649, 407 kit tests, proven in a
     scratch repo) but the cold-start on/off A/B — the acceptance tier that "still gates Phase 3" —
     has not run anywhere in this repo's history as evidenced.
  - These two gates are independent; neither substitutes for the other. **Every readiness
    classification below that would otherwise read `READY_FOR_TEST_DESIGN` against *new* code is
    capped at `BLOCKED_BY_GATE`** until both lift — there is no scenario in which new-repo (`sb/`)
    code can legally exist yet.
- **Stage-2 subsystem walk status** (`docs/planning/rebuild-stage2-subsystem-walk-2026-07-05.md`):
  confirmed unchanged since its 2026-07-05 pause — **only L1a+L1b (19 rows) are owner-decided.**
  Rows 17–52 (L1c onward, 34+ rows, all of L2/L3/L4/L5) remain `mapped`/`not-started`, per the
  walk doc's own explicit §7.5 disclaimer ("do not infer a disposition… from this session"). This
  review's four lenses independently re-confirmed that disclaimer's accuracy and, in doing so,
  surfaced source-level findings (below) the eventual owner walk has not yet seen.
- **The 8 current-bot bug fixes queued in the walk doc's §7.1** were independently re-verified
  present at HEAD by direct source read (not doc-trusted): settings' AI-projection mitigation
  (`services/settings_mutation.py:364-400`), admin's `bot_spam` typo fix (`admin_cog.py:430`) and
  audit-trail wiring (`admin/cog_manager.py:115,152`), moderation's slash-authority fix
  (`moderation_cog.py:115-130`, including the noted `@default_permissions` drop, confirmed
  verbatim in a source comment), security's slowmode audit-seam fix (`security_service.py:190-251`),
  cleanup's word-list audit fix (`services/prohibited_words_service.py:19-92`), role's
  guild-teardown gap fix (`guild_lifecycle.py:186-193,791-840`), and proof_channel's
  restart-recovery fix (`proof_channel_cog.py:25-51`). The one post-2026-07-05 merge touching any
  of these files (`973417e`, the ruff migration) was confirmed behavior-preserving via diff
  inspection. **None** of the §7.2 committed "implement now" scope (14 items across 6 rows) has
  shipped — spot-checked directly (channel voice-wiring, role's 5 sub-items, ticket's
  category/ping-staff exposure, the shared auto-mod-tier panel; all absent).

---

## 3. Contradiction ledger

Keyed per §3.3 (`path:Lnn`). "Status" uses §3.2's evidence labels. Ordered by consequence, most
load-bearing first.

| # | Claim | Claimed source | Live evidence | Status | Consequence |
|---|---|---|---|---|---|
| C-1 | "Two live money bugs... would both be structurally impossible under the kernel-owned `settle_once` seam — the strongest empirical argument for the grammar bet." | `FINAL-REVIEW.md:114-117`, `:386-389` | `disbot/utils/terminal_guard.py:44`'s `SettleOnceMixin` is an already-built, already-tested, already-4-place-adopted (RPS PvP, blackjack `_PvPState`, deathmatch bot-duel `_BotDuelView`, creature battle) fix for exactly this bug class, and is already applied to the structurally-identical bot-duel sibling of the cited deathmatch bug (`views/games/deathmatch_panel.py:192,302,323`) but not to the human-PvP `_DuelView` class the bug is actually cited against (`deathmatch_cog.py:94,151,214`, which imports no settlement guard at all). A dedicated checker (`scripts/check_consistency.py` Rule 6) exists but scopes to `{settle_pvp, refund_pvp}` only, missing both bugs by construction (deathmatch has no coin escrow; blackjack's free-tournament leg calls a different function, `payout_tournament`). | **CONTRADICTED** | K7's claimed necessity is real for *future* subsystems but overstated for the two specific bugs motivating it today; they need a contained, ~non-trivial retrofit (see §6.4 — the naive "mirror the mixin" fix is under-scoped per the adversarial pass), not a kernel workflow engine. |
| C-2 | Row 17 (visual card engine): `Current cog(s) = none (new)`; BUILD-PLAN tags it `ADD-from-plans`, "built before the consumers that need it." | `rebuild-stage2-subsystem-walk-2026-07-05.md:72`; `NEW-BOT-BUILD-PLAN.md:73,158` | `disbot/utils/card_render.py` (517 lines) is a working, tested, themeable engine (`Theme`/`THEMES` registry, `CardCanvas` primitives) with **5 live production consumers**: `welcome_render.py`, `rank_render.py`, `profile_render.py`, `role_menu_render.py`, `ux_patterns/image_builders.py` — added in the *same* PR (#1677/#1702, 2026-07-03) that produced the capstone audit files making this claim. | **CONTRADICTED** | An owner deciding row 17 on the current text evaluates the wrong question (build-vs-not instead of formalize-into-`CardTemplateSpec`-and-finish-2-holdout-migrations); a sequencing decision moving the engine "before" welcome would be moot since welcome already uses it today. |
| C-3 | Row 49 (dashboard): "genuinely new is only the write-capable live editor." | `rebuild-stage2-subsystem-walk-2026-07-05.md` §3.6 item 5 (the walk doc's own correction of the capstone) | `disbot/control_api.py` (861 lines) already registers a **complete** `/control/*` write surface (settings, help/overlay, help/home, routing) fronting real audited seams, matched by `dashboard/app.py:1085-1168`'s POST routes with CSRF+rate-limit+session-admin gating, exercised by 45 tests (`tests/unit/runtime/test_control_api.py`). Merged (~PR #1536, 2026-06-28) *before* the capstone (2026-07-03). | **CONTRADICTED (a correction of a correction)** | The walk doc's own accuracy-fix is itself stale. Row 49's true remaining scope is smaller than even the corrected framing states — dormant only behind an unset `CONTROL_API_TOKEN`/`CONTROL_API_URL` production-safety default, not unbuilt. |
| C-4 | Row 50 (boards family): "none (new)." | `rebuild-stage2-subsystem-walk-2026-07-05.md:105`; `NEW-BOT-BUILD-PLAN.md:104` | `botsite/submit.py` (honeypot + per-IP rate limit + INSERT-only intake) → `dashboard/app.py:764-959` (owner-only moderation queue, approve/reject) → `dashboard/github_mirror.py` (idempotent GitHub-issue mirror on approve) is a **complete, tested** create→moderate→durably-index→idempotent-sync pipeline, matching the BUILD-PLAN's own stated done-definition for this row verbatim. Missed by **both** the frozen capstone and the walk doc's own §3.6 five-item contradiction sweep — a sixth miss, methodologically caused by the sweep scoping to `disbot/cogs/*.py` only. | **CONTRADICTED** | Row 50's true remaining scope is "wire the existing web pipeline to the new owner-decided Discord-side (`/suggest` + NL) intake," materially smaller than "none (new)." |
| C-5 | K9 = "kernel/ai: gateway extended in place…"; K10 = "the loops: sim/ runner… golden harness… `check_compat_frozen`. The repo is born red on parity and green on everything else." | `rebuild-design-spec-2026-07-02.md:1614-1616` (`current-state.md`'s named "frozen reference," status `DONE`) | `gate-0/phase-b-l0-build-order.md:57` — the *later* (2026-07-04), also-treated-as-authoritative Gate-0 consolidation — silently renumbers K9 to the strand-2 durability band and marks K10 **"reserved,"** with kernel/ai's hardening tasks (redaction port, socket-deny egress guard) and the sim/golden-harness CI discipline **entirely absent** from the 87-primitive frozen grammar and 16-step build order. No reconciliation note anywhere explains the drift. | **CONTRADICTED (doc-vs-doc, both "frozen")** | A builder following Gate-0 literally (which is explicitly meant to replace reading all 14 specs) never lands kernel/ai's hardening or the sim/golden-parity CI gate anywhere in L0. Needs an explicit reconciliation pass before Phase-B, independent of either hard gate. |
| C-6 | "Mining… the acceptance test for the whole game-primitive stack: if the grammar can regenerate mining, it can regenerate the lane." | `NEW-BOT-BUILD-PLAN.md:96,182-184` | The *same document*'s own idea **I-2** (`:337-341`) names **giveaways**, not mining, as "the cleanest fully-unshipped plan… cheap, docs-only… before Gate 1" for exactly this grammar-proof purpose — and independently, this review found the primitives mining would jointly exercise (G-12/G-13/leaderboard) are already proven by non-game L2 consumers (§6.3). | **CONTRADICTED (internal to the corpus)** | Mining's designation as *the* necessary acceptance test is not internally consistent with the same document's own cheaper alternative, and is further undercut by the finding that most of what mining would "prove" is proven elsewhere. Mining's position as *last-within-L3* is still correct (depth/breadth reasons); its position as *the* grammar-proof gate is not load-bearing. |
| C-7 | "L4 — Knowledge & AI (deliberately after the deterministic platform)." | `NEW-BOT-BUILD-PLAN.md` §2 build-order narrative | Exhaustive, independently-cross-checked grep across `ai_cog.py`, `ai_tools.py`, all `btd6_*` services, `project_moon_cog.py`, `media_maintenance_cog.py`, `control_api.py`, the dashboard, and the migration assistant's design doc for any economy/inventory/blackjack/deathmatch/casino/game-state reference: **zero relevant hits** (BTD6's own in-game bloon-money fact is the only "economy" match). The one real cross-layer coupling found (`ai_tools.py`'s `get_user_standing`) reaches L1a (permission tier) and L2 (XP level), never L3. | **CONTRADICTED** | The frozen L3-before-L4/L5 ordering is not supported by any dependency this review could find in either the Lens D or the games-deferral pass — it reads as the current bot's historical growth order, not a build-order requirement. Directly informs §5's sequencing verdict. |
| C-8 | Project_moon is the shared IngestionPipeline's implied second consumer, positioned mid-chain before youtube ("third consumer"). | `NEW-BOT-BUILD-PLAN.md:99-100,195` | `project_moon_cog.py` (198 lines) has **zero** DB, ingestion, or AI-gateway code today; its own docstring states "No writes, no DB, no AI gateway," deferring AI-grounding wiring to "a later PR." | **STALE** | The mid-chain-consumer framing is aspirational, not grounded in current or near-term need — a minor internal inconsistency (the row's own note, `:99`, is more accurate than the surrounding narrative). |
| C-9 | "PR C decided (Q-0147) but unbuilt" (profile surface). | `NEW-BOT-BUILD-PLAN.md:82` | `disbot/cogs/utility_cog.py:114-146` (`!myprofile`/`/myprofile`) + `views/profile/profile_view.py` (318 lines) + `views/profile/editor.py` (620 lines, full self-service editor: subsystem/subscription/preference selects + a free-text modal), tested (`test_profile_card.py`, `test_profile_editor.py`, `test_profile_render.py`), goldened (`parity/goldens/utility/sweep_myprofile.json`, `sweep_slash_myprofile.json`). | **CONTRADICTED (still uncorrected in the frozen doc)** | Already flagged by the walk doc's own §3.6 item 1 (2026-07-05) — but **the frozen `NEW-BOT-BUILD-PLAN.md` itself, one of only two documents this fleet's shared orientation names as canonical frozen reference, has not been corrected.** A Phase-B agent reading the frozen doc directly (rather than the walk doc) would still allocate a from-scratch build for a shipped, tested feature. |
| C-10 | Economy row 20: "`transfer()` ready-but-unwired to `!give`/`!pay` — live gap," framed as a plain not-yet-attempted gap. | `rebuild-stage2-subsystem-walk-2026-07-05.md:75` | `transfer()` **was** wired to `!give`/`!pay` in PR #1541 — it collided with a dormant `mining_cog` admin `give` command (present since the initial 2025-08-10 commit), the collision aborted boot via the STRICT identity-contract, the bot crash-looped in production (Q-0211), and PR #1544 retired the `give` surface entirely + added a *runtime* (post-deploy) duplicate-command guard. The proposed CI-time static preflight (`docs/ideas/command-collision-checker-2026-06-29.md`) was never built. | **STALE** | Technically accurate but omits a real production incident whose root cause (no pre-merge namespace-collision detection) is still unaddressed — a planner re-implementing this row without that context risks repeating it exactly. |
| C-11 | `tests/unit/invariants/test_inv_k_karma_service.py`'s own docstring: "INV-K regression — every karma mutation flows through `karma_service`." | The test file itself | `docs/architecture.md:126-139`'s catalogued `INV-A`–`INV-N` unambiguously defines `INV-K` as the `create_task`/`core.runtime.tasks.spawn` rule — unrelated to karma. The karma/economy/xp audited-write-seam AST-guard family has no catalogued letter of its own for karma. | **CONTRADICTED** | Low-severity rubric class-10 naming collision — a future agent grepping "INV-K" to understand the `create_task` rule could be misdirected. (The rebuild's own design-spec has *already* fixed the general pattern by renaming the task-spawn invariant to `INV-T` and reserving invariant tags via `StoreSpec.invariant_tag`, per §4 below — this is a live current-bot instance of a class the rebuild design already anticipated.) |
| C-12 | Bucket (d): "**SettingsPresetSpec** (→ existing `presets` + kernel `WorkflowRef`; its 'atomic apply' claim was false)" — read as "the preset/template fragmentation problem is solved by folding into existing fields." | `FINAL-REVIEW.md:235` | The *same corpus*'s own later adversarial pass (`presentation-verification-mechanics-2026-07-03.md:427,436`) independently concludes the primitive should be **scoped**, not fully unified — "keep the policy/value presets… as a SEPARATE 'named value set' concept" — because at least two-to-three structurally distinct families exist (draft-bundle staged presets vs. immutable policy/value presets). That scoping correction was never folded back into `FINAL-REVIEW.md`'s bucket assignment. (A precision note: the two documents also disagree on the raw count — "~14×" per `runtime-logic-mechanics-2026-07-03.md:403` vs. "~13×" per `presentation-verification-mechanics-2026-07-03.md:427,435-436,799` — a minor but real discrepancy the draft smoothed over without flagging.) | **CONTRADICTED (doc-vs-doc)** | The ratified amendment set (`design-spec:698`'s `SettingSpec.preset_kind` field) only folds the narrowest slice (scalar-setting numeric/text presets). The draft-bundle family (`setup_role_templates.py`, `governance/role_templates.py`, `governance/templates.py`) and the immutable policy/value family (`ai_orchestration_presets.py`, `ai_preset_service.py`, `ai_behavior_profile_service.py`, `automation_templates.py`) remain **entirely unconsolidated** — a live, checkable gap between what Gate-0 believes is closed and what a deeper pass in the same corpus already found is not. |
| C-13 | The `G-20`/`G-21`/`G-22` bucket-(b) families are ratified on equal footing with the rest of the amendment set. | `FINAL-REVIEW.md:184-186` | The same corpus applies its own "no abstraction without a durable role" (≥2-recurrence) bar correctly twice elsewhere in the same pass — holding `P-1 EventFeedProjectionSpec` to bucket (c) ("one instance today — held per the ≥2-recurrence bar," `:213-215`) and refusing `G-17`'s bracket-topology generalization outright ("recurrence = 1," `:181`) — but ships `G-20 InstanceLifecycleSpec` (1 real consumer, ticket; 1 *speculative*, unbuilt giveaways), `G-21 RecordTableSpec` (1 real consumer, role; self-labeled thin), and `G-22 StagedBuilderSpec` (1 real consumer, no second consumer even speculated) as full ratified families rather than holding them provisional. | **CONTRADICTED (internal inconsistency in bar application)** | The review process demonstrably knows how to apply its own discipline correctly and simply didn't apply it uniformly within the same pass — worth an explicit owner ruling before Gate-0 folds these three (hold to bucket (c) alongside `P-1`, or document why their bar differs). |
| C-14 | R-11 (`HelpEntrySpec.dropdown_target: PanelRef`) "retires the ~10 near-identical `build_help_menu_view` bodies + get_cog/getattr dispatch." | `FINAL-REVIEW.md:205` | This is accurate for **one** sub-shape of the views→cogs violation class (cross-subsystem navigation dispatch, e.g. `views/server_management/hub.py:147-148`) but a **second, more severe sub-shape** — a view directly invoking a private cog mutation method (`views/roles/diagnostics_panel.py:177-178` and `views/roles/time_roles_panel.py:203-205`, both calling `RoleCog._assign_roles`) — is not named by R-11 or any other amendment. The class *is* closed in the new design, but incidentally (there is no addressable "RoleCog" object with a private method to fetch, once cogs become generic `SubsystemHost` instances), not because R-11 or any deliberate fix targets it. | **CONTRADICTED (mischaracterized scope, not a wrong outcome)** | R-11 should not be cited as "the fix" for the full views→cogs violation class in Phase-B planning; the sub-shape-B closure should be verified explicitly (e.g. a contract test asserting no `WorkflowHandler`/`PanelActionSpec.handler` registration ever needs a live cog reference) rather than assumed covered. |

---

## 4. Critical findings

Ordered Blocker → Important → Cleanup; Future items separated at the end per §4's own future-is-separate instruction.

### Blockers

1. **K7 (workflow/compound-op engine) has zero code, zero prototype, and zero oracle, and is the
   sole cited mechanism for closing two live production bugs it does not actually need to close.**
   `grep -r "workflow_engine|class Workflow" disbot/` returns zero matches. Unlike K2 (a real,
   tested `tools/grammar_spike/` prototype validating grammar fit against three live subsystems,
   test-confirmed 13/13 passing this session) or K1/K3–K6/K8 (all with either source-proven
   current-bot analogues or a concrete field-level design), K7 has none of: existing code, a
   spike/prototype, a paper stress-test, or an oracle — a disproportionate gap for a component the
   plan itself calls "the strand-2 keystone" and "the largest kernel band." §3 C-1 shows the two
   bugs cited as its empirical justification are independently fixable today without it. This does
   not remove the need for K7 — it removes the urgency argument the corpus currently rests on, and
   the actual remaining case for prioritizing K7 (kernelizing `settle_once` as *engine* behavior
   rather than an opt-in mixin, so a future class can never repeat the mistake) deserves its own
   honest justification, not a borrowed one. *(evidence: `disbot/utils/terminal_guard.py:44`;
   `disbot/cogs/deathmatch_cog.py:94,151-160,214-237,477-483`; `disbot/views/games/
   deathmatch_panel.py:192,302,323`; `disbot/views/blackjack/tournament_views.py:100-235`;
   `disbot/services/game_wager_workflow.py:280-345`; `scripts/check_consistency.py:893`; Lens A
   readiness row K7; sequencing/invariants/games-deferral deep-dives + all three adversarial
   verifications.)*

2. **K1 (namespace registry) and its S0 prerequisite are both unbuilt, despite the build order
   declaring K1 must exist before K2 — the one component with a real prototype — can even validate
   itself.** `gate-0/phase-b-l0-build-order.md` states K1's `validate()` is literally called by K2's
   compiler pass P3 (RC-7): a hard, non-deferrable prerequisite to the very first real kernel build
   step. K1 has zero code and zero prototype (unlike K2). Separately, S0 — explicitly labeled
   "Blocks: Gate-0" — requires `tools/check_amendments.py`, which does not exist anywhere in the
   repo despite Gate-0's document set being marked "complete." This is a real gap between "the docs
   consolidation is done" and "the build's own stated prerequisites are in place." *(evidence:
   `gate-0/phase-b-l0-build-order.md:69,71`; filesystem search for `check_amendments*` returns
   nothing; `grep -r "namespace_registry\|NamespaceRegistry\|validate_registry" disbot/` finds only
   the unrelated current-bot `utils/subsystem_registry.py`.)*

3. **Two independent hard gates (Gate-0 owner ratification; the Phase-2.5 substrate A/B) both fully
   block any L0 code, neither has begun, and the ratification sitting's twelve `Q-D` items are not
   even visible in the router that exists specifically to hold exactly this kind of open owner
   question.** See §2 above for full detail. Every readiness classification in this report that
   would otherwise be `READY_FOR_TEST_DESIGN` against new code is necessarily capped at
   `BLOCKED_BY_GATE` until both lift.

### Important

4. **`GameXpProvider`-adjacency notwithstanding, G-12/G-13/leaderboard — the three primitives the
   rebuild plan most often cites games for — are already richly, independently proven by shipped
   non-game L2 consumers.** `shop_purchase_workflow.py` (AST-enforced via
   `test_no_view_level_purchase_writes.py`) and `treasury_service.py` already prove G-12's
   one-transaction multi-leg pattern; `utils/db/xp.py:level_progress()` already proves G-13's curve
   across 6 modules; 4 of `rank_providers.py`'s 12 registered providers (`Xp`, `Coins`, `GameXp`,
   `Karma`) are non-game and already prove the LeaderboardSpec-merge design at 12-provider scale.
   The two genuinely game-unique primitive shapes with no existing non-game proof — (a) two-party
   accept-handshake + alternating-turn-with-dual-timeout concurrency, and (b) G-17's pot/entry-fee
   tournament-lobby settle — both have concrete, cheap, headless synthetic-harness replacements
   (§6.5) requiring no Discord UI and no L3 subsystem to exist. *(evidence:
   `disbot/services/shop_purchase_workflow.py:1-92`; `disbot/services/treasury_service.py:1-182`;
   `disbot/utils/db/xp.py:19`; `disbot/services/rank_providers.py:107-643`; `FINAL-REVIEW.md:176-179`.)*

5. **K9 and K10 are defined contradictorily by two documents both currently treated as
   frozen/authoritative, with no reconciliation note anywhere.** See §3 C-5.

6. **Gate-0's owner-ratification sitting — explicitly named "step 1 of what's next" — has not
   started, and none of the twelve `Q-D` rows appear in the maintainer-question router.** See §2.

7. **karma_service.give() is billed as the rebuild's exemplar audited seam but its three writes
   (`credit_karma`, `increment_given`, `insert_karma_audit`) are not transactionally composed** —
   each is a separate, un-transacted call, even though every primitive already accepts an optional
   `conn` for exactly this composition (the pattern `treasury_service.py` and
   `shop_purchase_workflow.py` use correctly). A genuinely new finding, not previously flagged
   anywhere in the corpus. *(evidence: `disbot/services/karma_service.py:168-186`; `disbot/utils/
   db/karma.py:161-225` (conn params present, unused by the only caller); contrast
   `treasury_service.py:82-96`.)*

8. **Row 49's write-capable live editor and row 50's boards pipeline are not future deliverables —
   both already ship, tested.** See §3 C-3, C-4. This is a *methodology* gap worth flagging beyond
   its content impact: any sweep scoped to `disbot/cogs/*.py` will systematically miss web-tier
   (`botsite/`, `dashboard/`) prior art.

9. **Views→cogs has a second, more severe sub-shape than the one named fix (R-11) covers.**
   `views/roles/diagnostics_panel.py:177-178` and `views/roles/time_roles_panel.py:203-205` both
   call `interaction.client.get_cog("RoleCog")._assign_roles(...)` — a view directly invoking a
   private cog mutation method, not navigation dispatch. R-11's stated scope is the navigation
   sub-shape only. The class is likely closed *incidentally* by the composition-root redesign
   (no addressable "RoleCog" object exists once cogs become generic `SubsystemHost` instances), but
   this should be verified with an explicit contract test, not assumed. *(evidence:
   `disbot/views/roles/diagnostics_panel.py:177-178`; `disbot/views/roles/time_roles_panel.py:203-205`;
   `disbot/cogs/role_cog.py:295`.)*

10. **Preset/template fragmentation (C-3/Q-0228) is only partially addressed by the ratified
    amendment set, and the frozen corpus disagrees with its own later adversarial pass about
    whether it's closed.** See §3 C-12.

11. **Economy's `!give`/`!pay` target contract already caused a production boot-crash, and the
    proposed fix for the root cause (a pre-merge command-collision preflight) was never built.**
    See §3 C-10.

12. **The `inventory` REDESIGN target hides a real user_id-type and guild-scope data migration, not
    just a table rename.** `inventory` uses `BIGINT user_id` and has always been guild-scoped;
    `mining_inventory` uses `TEXT user_id` (documented legacy, deferred conversion) and only gained
    a `guild_id` column via migration 002, with all pre-migration rows defaulted to `guild_id=0` as
    a permanent "legacy/global" bucket (migration 017's own comment: "preserved by design," never
    backfilled). Merging into G-15's single audited item kernel needs an explicit owner decision on
    both the type cast and the guild-0 rows' disposition — neither is decided anywhere. *(evidence:
    `disbot/utils/db/games/mining.py:1-20`; `disbot/migrations/002_guild_scope_fixes.sql`;
    `disbot/migrations/017_mining_fix_pk.sql`.)*

13. **`community_spotlight`'s "Games" sub-panel is hard-coupled to 4 L3 game providers
    (mining/rps/deathmatch/counting), an L2-into-L3 dependency not flagged anywhere in the
    sequencing corpus.** It degrades gracefully today (`empty_hint` per provider), but if L2 (row
    26) ships before any L3 game exists under any sequence that still builds L2 first, this is a
    real, currently-undesigned interim-state question: does the panel ship showing all-empty game
    boards, or is it itself deferred? *(evidence: `disbot/cogs/community_spotlight_cog.py:213-228`;
    `disbot/services/rank_providers.py:627-643`.)*

14. **`G-20`/`G-21`/`G-22` are ratified with a thin-recurrence profile the same review pass
    correctly rejected elsewhere.** See §3 C-13.

15. **Six of the current bot's fourteen named, mechanism-backed invariants (`INV-B`, `INV-C`,
    `INV-D`, `INV-H`, `INV-I`, `INV-J`) have no rebuild mechanism named anywhere in the design
    spec** — confirmed by targeted grep against `rebuild-design-spec-2026-07-02.md` for each
    invariant's subject matter, independently by the invariants adversarial pass. `INV-C` and
    `INV-D` (≤1 `panel_anchors`/`runtime_sessions` row per user/channel/subsystem, both currently
    DB-`UNIQUE`-enforced) are the most consequential omission: a "one active panel per
    user/channel/subsystem" guarantee doesn't fall out for free from a generic `SubsystemHost` or a
    durable due-queue — it needs its own explicit uniqueness contract in the new schema, and
    nothing in the corpus commits to one. *(evidence: `docs/architecture.md:126-139`; targeted grep
    of `rebuild-design-spec-2026-07-02.md` for each invariant's mechanism, zero hits for six of
    fourteen.)*

16. **`mining_render.py` and `character_render.py` remain unmigrated onto the shared
    `card_render.py` engine** — an unflagged L1c→L3 coupling. `card_render.py`'s own docstring
    names both as the exact duplicated-code problem it exists to solve; both still define
    independent font/palette primitives. Since mining/creature-battle are L3, any L3 rebuild work
    on these renderers inherits this fragmentation unless closed first — cheap and mechanical to
    close now. *(evidence: `disbot/utils/card_render.py:1-8`; grep confirms no `card_render` import
    in either holdout file.)*

### Cleanup

17. All 8 §7.1 bug fixes verified present at HEAD, no regression (§2).
18. §7.2's 14 committed-scope items across 6 rows remain entirely unbuilt — worth naming plainly so
    the "IMPLEMENTED" banner on §7.1 isn't over-read as broader progress than exists.
19. `welcome` has zero slash-command mirror, unflagged anywhere in the walk artifacts unlike
    role/ticket's equivalent named gaps. *(evidence: no `@app_commands.command` in
    `welcome_cog.py`.)*
20. `welcome.member_greeted` has zero golden coverage despite `parity/goldens/welcome/
    sweep_welcome.json` existing — the golden doesn't exercise the join/leave emission path.
21. `ticket`'s near-total unit-test gap (`close`/`add_participant`/`remove_participant`/
    `update_config`/`set_blacklist`, 4 of 5 views) re-confirmed still open — new committed work
    (auto-close, category picker, slash mirrors) will land on an under-tested base.
22. `general_cog.py` (371 lines, zero-state content pack) has zero dedicated behavioral test
    coverage — low-risk but the least-verified item in the entire L4/L5 scope.
23. `NEW-BOT-BUILD-PLAN.md:82`'s stale "profile surface unbuilt" claim remains uncorrected in the
    frozen document itself (§3 C-9) — docs-only, zero code risk, immediately fixable.
24. The `INV-K` docstring collision (§3 C-11) — the rebuild's own design already fixes the general
    pattern (renamed `INV-T`, namespace-reserved tags); this is a live current-bot instance of the
    class it anticipated.
25. Several xp-adjacent goldens (`sweep_resetxp.json`, `sweep_xpimport.json`, `sweep_xpconfig.json`,
    `sweep_givexp.json`) are filed under `parity/goldens/_unmapped/` instead of `xp/` — a golden-
    taxonomy hygiene gap that understates xp's true oracle coverage when browsing by folder.
26. Utility's (row 47) own cited target contract (G-9 for reminders) is only half-ratified — only
    G-10 (ModalFormSpec, for poll) is actually frozen grammar per the Gate-0 amendment registry;
    G-9 (DeferredActionSpec) remains `pending-gate-0`.

### Future (separate per §4 instruction)

27. K7's core justification (the two live money bugs) is proven only against blackjack and
    deathmatch — subsystems the owner-led Stage-2 walk has not yet reached. If the eventual L3 walk
    reclassifies either subsystem (e.g., `redesign` vs `keep`), K7's shape-defining example shifts
    underneath an already-built kernel component. Worth tracking, not blocking.
28. The concurrency-under-real-Postgres oracle gap (`test_economy_service_concurrent.py`'s own
    docstring admits Postgres is unavailable in CI) is repo-wide, not game-specific — closing it
    once (a disposable-Postgres integration-test tier) benefits every G-12 consumer simultaneously,
    games included, and should not be scoped as "games work."
29. Real Railway/ops control-plane infrastructure already exists outside cog code (a live
    "Superbot Admin" HQ guild with a restored deploy-alert webhook; a CI backup-integrity gate) —
    worth carrying into row 52's eventual dossier as a starting inventory rather than a blank
    slate, but not itself blocking.
30. A parallel botsite React-SPA migration (PR #1305, merged 2026-06-22) is modernizing the
    public-facing front-end independently of the L5 dashboard rebuild target — legitimate,
    owner-requested, but worth a coordination note when row 49 is eventually walked so the two
    efforts don't diverge.

---

## 5. Sequencing review

### 5.1 The three sequences compared

| | Sequence A (frozen: L0→L1→L2→L3→L4→L5) | Sequence B (strict games-last: L0→L1→L2→L4→L5→L3) | **Sequence C (capability-class, bounded interleave) — recommended** |
|---|---|---|---|
| Dependency correctness | L0→L1→L2→L3 real; **L3→L4/L5 fabricated** (§3 C-7); contains an internal contradiction (deathmatch declares "mining (gear)" as upstream yet mining ships LAST — a genuine class-1 dependency-order inversion inside the frozen plan itself, confirmed: `deathmatch_cog.py:68-91,163,238` calls `mining_workflow.wear_tick()` on every duel resolution) | Removes the fabricated edge; dependency-correct throughout | Separates the *real* edge (K7's concurrency shape needs proving before anything composes multi-trigger settlement) from the fabricated edge (L4/L5 needs L3) and the irrelevant-to-sequencing edge (most of L3's own feature work depends on nothing but frozen L0-L2) |
| Contract-freeze needs | Same K1-K8 needs as B/C; no games-specific reduction | Same, but K7's game-specific facets (turn/escrow/lobby choreography) get their first real pressure-test very late | Narrower, more precise: K7's *first* deliverable scoped specifically to the headless settlement-concurrency contract (using `SettleOnceMixin` as reference), not the full grammar at once |
| Testability | Builds the highest-risk, worst-oracle-coverage layer (games) while the harness is thinnest (`parity/COVERAGE.md`: bus events 21%, DB tables 25%, settings keys 2%) | Best of the two extremes for early layers; game-shaped harness practice deferred to when it's needed | Best overall: essential L4/L5 work proceeds against a harness maturing on L1/L2's better-covered surfaces, while the one real concurrency gap gets a deterministic, game-free oracle immediately |
| Lost oracles | None (baseline) | Real, named cost: turn-based dual-entry-point settlement race (§6.5 #1), `G-17` round-graph checkpointing (§6.5 #3), mining's "acceptance test" role (already undercut, §3 C-6) | Same three, but two of three (settlement race, multi-leg atomicity) get their replacement built *as part of this sequence's own K7 step*, not deferred indefinitely; only the round-checkpointing spike is legitimately a thin, non-UI slice of game-shaped machinery |
| Rollout/migration safety | Front-loads the riskiest, lowest-oracle code into the middle of the build — a schedule slip mid-L3 leaves the riskiest half-finished longest | If forced to an early cutover, could ship with *zero* games (the lowest-fit, most build-effort-heavy cluster) — a materially different, and untested-for-tolerance, product state | Best for a forced-early-cutover scenario: more of the operator/platform surface complete, fewer game features, at a smaller and more bounded product-risk (see caveat below) |
| Owner-intent fit | Contradicts the stated direction almost directly | Matches the *letter* most literally | Matches the *substance* while refusing to over-read "defer games" as "defer the one concurrency contract everything downstream needs" — exactly the distinction §1 of the launch-pad doc asks every arm to preserve |
| Premature-generalization risk | Low on its own terms, but the deathmatch/mining inversion shows "clean layer stack" is already false in source | Moderate — conflates shippable-late game *features* with must-prove-early game-adjacent *primitives* | Lowest — makes the narrowest possible claim (one concurrency contract, proven headlessly, before anything composing multi-trigger settlement) |
| Stage-completeness discipline | Strong in principle, undercut by its own internal contradiction | Clean, but means the largest, most heterogeneous layer (L4/L5) reaches "100% production-grade" before the concurrency-proving spike informs anything downstream of it | Real cost: harder to state "100% before next" cleanly when stages interleave — mitigated by the interleave being small, named, and bounded (one K7 spike + L2 + essential L4/L5), not "everything, all at once" |

### 5.2 The primitive-vs-feature table

The crux distinction this review keeps sharp throughout: **"a shared primitive must be proved
early" is not the same claim as "a game feature must ship early."**

| Shared primitive | Must be proven early? | Evidence it's already de-risked | Real remaining gap | Game *feature* that can genuinely wait |
|---|---|---|---|---|
| `settle_once` (turn/dual-entry-point settlement) | **Yes** | `terminal_guard.py:44`, 4/6 correct production adoptions, a checker (Rule 6, too narrow) | Kernelize as an *enforced*, non-optional contract; widen the AST check beyond `{settle_pvp, refund_pvp}`; fix `deathmatch_cog._DuelView` and `_BjTournament`'s non-adoption (both fixable in the *current* bot today) | Deathmatch's combat UI, blackjack's card rendering, casino's table UI |
| G-12 `EconomyTransactionSpec` | **Yes, but already substantially proven** | `economy_service.transfer()`, `treasury_service` contribute/disburse, `shop_purchase_workflow`'s conditional-upsert+debit — 3 non-game production exemplars (though `transfer()` itself uses an older manual `pool.acquire()+conn.transaction()` idiom rather than the newer `db.transaction()` primitive — a real but non-fatal inconsistency the pattern's maturity claim should acknowledge) | `IdempotencyKey`/`once()` replay envelope (confirmed genuinely absent); `db.transaction()` itself is not a gap — it has 11+ production callers | Mining's ~10 legs, farm/fishing's sell legs — apply the already-proven pattern to each subsystem as it's built |
| `G-17 TournamentLobbySpec` (round-graph checkpointing) | **Yes, narrowly** | None found — genuinely novel capability | Needs a headless spike (abstract N-participant, M-round state machine with induced-crash/resume) — buildable without Discord, without a real bracket UI. Caveat: if this spike, once attempted, needs enough real game-shaped state to stop being distinguishable from "build a game," its classification shifts from provable-headlessly to needs-a-thin-real-slice — see §5.3's change-conditions. | rps_tournament's actual bracket display, blackjack's actual tournament UI |
| K1 namespace / K2 compiler | **Yes (already recognized, unrelated to games)** | K2 has a real, tested grammar spike | S0's `tools/check_amendments.py` doesn't exist despite being a declared Gate-0 blocker | N/A — not game-coupled at all |
| Mining's full-stack "acceptance test" role | No — a validation milestone, not a prerequisite | The frozen plan itself calls it "LAST" for this reason; §3 C-6 shows the plan's own I-2 idea already proposes a cheaper proof | Deathmatch's real gear-wear dependency on mining needs re-sequencing regardless of the L3/L4 debate | Mining's world-generation, seed-deterministic grids — pure feature work, correctly last |

### 5.3 Recommendation

**Sequence C** (capability-class, bounded interleave). Sequence B's dependency graph is already
correct; C is a refinement of B, not a competing novel sequence.

1. Sequence A's L3→L4/L5 edge is unsupported by any dependency found across three independent
   passes (Lens D's exhaustive grep; the games-deferral pass; the sequencing pass's own
   re-derivation), and it carries an internal ordering bug that undermines confidence in its other
   ordering claims.
2. Sequence B is dependency-correct but over-reads "defer games" as "defer the one concurrency
   contract everything downstream needs" — which the owner's own stated framing explicitly warns
   every arm not to do.
3. **The primitive the whole K7/G-12 argument rests on is not hypothetical** — it has a working
   reference implementation, a checker (too narrow, but real), and three non-game production
   exemplars, all in the *current* bot, today, independent of both hard gates and of any
   L3/L4/L5 sequencing decision at all. Sequence C's "narrow headless spike" step is largely "take
   what already runs, kernelize it, widen its checker, and fix its two known non-adoption bugs" —
   squarely within this project's own "bugs first, durably" and "checker → hook, enforce don't
   exhort" working agreement, startable **immediately**.
4. Sequence C best matches the testability evidence: essential-platform work (already
   substantially built per Lens D's `control_api.py`/boards findings) proceeds without an
   artificial games gate, while the one real primitive-proving dependency is still respected.

**Conditions under which this recommendation would change:**
- If the headless `G-17` checkpointing spike, once attempted, turns out to need enough real
  game-shaped state (turn order, roster, bracket topology) to stop being distinguishable from
  "build a game," the honest classification for `G-17` shifts from provable-headlessly to
  needs-a-thin-real-slice — pulling a small, named slice of L3 (rps_tournament's bracket *engine*,
  not its UI) forward regardless of which sequence wins.
- If Arm D's empirical live-testing finds `SettleOnceMixin`'s "no `await` before the claim"
  contract is violated by a dependency not traced here (e.g. a `defer()` call landing before the
  claim in some view not audited this session), the "already de-risked" argument weakens and the
  recommendation shifts back toward B.
- If the owner states an explicit product requirement that the rebuild ship with day-one feature
  parity (games cannot lag at all) — a business constraint no sequencing argument here can
  override — the recommendation shifts toward A or a compressed C with less interleave.

**Owner-intent pressure-test, stated plainly:** the maintainer's stated direction survives
pressure-testing for the large majority of L3 — every actual game *feature* has zero dependency
edge into L4/L5 or the platform, so deferring it costs nothing. It does **not** survive
pressure-testing *unmodified* for the one concurrency contract the rebuild's own G-12 argument is
built on — but the resolution there is "prove the contract early using evidence that already
exists in the current bot," not "therefore build a game early." That is a narrower, cheaper, and
more owner-intent-consistent action than either extreme.

---

## 6. Games-deferral impact

### 6.1 What depends on L3

Import-edge search across `disbot/services`, `disbot/views`, `disbot/core`, `disbot/utils`,
`ai_cog.py`, `utility_cog.py`, `general_cog.py`, `project_moon_cog.py`, `media_maintenance_cog.py`,
`botsite`, `dashboard` for any reference to an L3 game module returns effectively nothing outside
L3 itself, plus **one real, non-cosmetic presentation-layer coupling** understated by a pure
import grep: **`rank_providers.py` (L2, `services/`) registers 12 `RankProvider` subclasses, 8 of
which are L3 domains** (`Mining`, `Creatures`, `Fishing`, `Farm`, `GameXp`, `Crafting`,
`Deathmatch`, `Rps` — the remaining 4, `Xp`/`Coins`/`Karma`/plausibly `GameXp` itself, are
non-game). `leaderboard_cog` and `community_spotlight_cog` both read this registry and degrade
gracefully via `empty_hint` when a provider has no data — but a rebuilt L2 leaderboard kernel
genuinely cannot render 8 of its 12 declared boards until the corresponding L3 subsystem exists,
quietly contingent on L3 landing, undesigned anywhere in the corpus.

### 6.2 What L3 depends on

Confirmed from the grammar spike's own `blackjack.py` manifest (`dependencies=("economy",)`) and
direct reads of `game_wager_workflow.py`/`mining_workflow.py`/`shop_purchase_workflow.py`: every
L3 money/item/progression leg composes L2 primitives (`economy_service.debit_in_txn`/
`credit_in_txn`, `db.try_grant_unique_item`, `xp.level_progress()`, `game_state_service`'s
checkpoint/refund infrastructure). L3 depends on L2 heavily and one-directionally; L2 does not
depend on L3 except for the presentation coupling above. The frozen order's L2-before-L3 half is
well-supported; only its L3-before-L4/L5 half is unsupported (§3 C-7).

### 6.3 Primitive-by-primitive: does it actually originate in / require games?

| Primitive | Claimed game-origin | Non-game proof that already exists | Verdict |
|---|---|---|---|
| G-12 `EconomyTransactionSpec` | "every L3 wager via `bet_and_settle`" | `shop_purchase_workflow.py` (AST-enforced), `treasury_service.py` — 3 of G-12's own 6 named consumers are non-game and already ship the pattern | **Already richly proved without games.** Mining/farm/fishing are more legs of an already-proven pattern, not a new proof. |
| G-13 `ProgressionSpec` | economy/xp/mining/fishing/creature/farm | `utils/db/xp.py:19` `level_progress()`, reused verbatim by 6 modules | **Curve already proven, cross-cutting**; only the cooldown/streak gate-shape generalization (R-15) is undecided, and that's a design question, not a concurrency one |
| Leaderboard merge-into-kernel | 8 of 12 providers are L3 | 4 of 12 registered providers (`Xp`/`Coins`/`GameXp`/`Karma`) are non-game, consumed identically by 3 subsystems today, at the exact same 12-provider registry the plan cites as its exit bar | **Falsified as game-exclusive.** The design is mechanically proven by non-game producers; games are 8/12 of the *content*, 0/12 of the *proof burden* |
| `settle_once` seam | "the exact seam that would have prevented both known live money bugs" | The fix already exists, is production-adopted; the two cited bugs are closeable today without any kernel engine (§3 C-1) | The claim conflates "a kernel-owned `settle_once` seam" (K7, unbuilt) with "a `settle_once` discipline" (already built, adopted 4/6 places) |
| `ChallengeSessionSpec`'s accept/turn/stale-timeout shape | blackjack's 3 specs | No non-game two-party accept-then-turn-loop exists (no P2P-trade feature; `ticket`'s G-20 lifecycle shares the create→state-machine→close shape but not the escrow/turn-alternation part) | **Genuinely game-unique** for the accept-handshake + turn-alternation shape specifically |
| Restart persistence for a checkpointed session (ADR-002) | blackjack tournament (the ADR's own stated first validator) | The setup wizard's draft lane (`setup_draft.py`, migrations 035/045/059) proves "a multi-step stateful workflow survives a restart" via a different persistence class, without any game | **Partially game-unique.** The JSONB-checkpoint *mechanism* is validated only by blackjack; the *general claim* has a non-game proof via a different mechanism |
| Concurrency under a realistic race | implied by G-12/`settle_once` | `test_economy_service_concurrent.py`'s own docstring admits Postgres is unavailable in CI — the real DB-level race is unproven for *any* consumer, game or not | **Not game-specific at all** — a repo-wide oracle gap, orthogonal to L3 sequencing |
| Mining as "whole-stack acceptance test" | "if the grammar regenerates mining, it regenerates the lane" | The corpus's own idea I-2 (giveaways) already proposes a cheaper alternative for the *grammar-expressiveness* proof specifically (§3 C-6) | **Overstated by the plan's own self-correction.** Mining proves breadth at maximum cost/position-in-queue; a synthetic manifest proves the actual open question far more cheaply |

### 6.4 The two "live money bugs" — do they actually need K7?

This is the single highest-leverage finding in this section (see also §3 C-1, §4 Blocker #1).

**Deathmatch PvP double-settle.** `_DuelView` (`deathmatch_cog.py:94`) imports no settlement
guard at all. Its sibling, the bot-duel path (`views/games/deathmatch_panel.py:192`,
`_BotDuelView(SettleOnceMixin, ...)`), correctly guards both its finishing-button path and its
`on_timeout`. The fix pattern already exists, in the same subsystem, one file away — it was simply
never retrofitted to the PvP class. **The adversarial pass found the actual defect is more precise
than a naive port suggests**: `_DuelView.on_timeout` *does* have a synchronous `if duel.is_over:
return` guard; `_resolve` (the button-click win path) does not check it at all — an *asymmetric*
guard, not an absent one. Because `SettleOnceMixin.claim_settlement()` is a synchronous
check-and-set with no internal `await`, a naive `asyncio.gather`-race test would not actually
manufacture a race (asyncio only interleaves at `await` points) — the exploitable mechanism is a
**double-click / duplicate-interaction delivery**, not a timeout-vs-click race, which is in fact
the exact scenario `SettleOnceMixin`'s own docstring names. The correct fix retrofits
`SettleOnceMixin` into `_DuelView` and **reconciles or removes** the existing ad hoc
`duel.is_over` mechanism (auditing every other read site of that flag) rather than simply adding a
guard alongside it — a slightly larger, but still small, contained, same-session fix.

**Blackjack free-tournament double-pay.** `game_wager_workflow.py`'s `payout_tournament()` docstring
asserts the free-reward leg is "single-call by construction," an assumption resting on
`tournament_views.py:222`'s `_check_tourn_done` genuinely being single-call. It is called from two
independent finish-sites (`:116`/`:139`, bust and stand, both funneling through the shared
`_finish_round` at line 86) with a real, exploitable `await self.channel.send(...)` yield point
between the `tourn.results[...]` write and the `_check_tourn_done` call — two players finishing in
quick succession can both pass the length guard before either settlement completes. The precedent
fix is already proven in the same codebase (`_PvPState(SettleOnceMixin)`, a *services state
object*, not a view) — give `_BjTournament` a `claim_settlement()` call at the top of
`_check_tourn_done`, taken before the `await`.

**Both are closeable today, independent of K7, independent of the rebuild, independent of Gate-0**
— a same-day, contained, reversible current-bot fix that satisfies this project's own "bugs first,
root cause over symptom" working agreement and needs no gate.

### 6.5 Lost-oracle table and deterministic replacements

| # | Lost oracle | Deterministic replacement | Where it lives |
|---|---|---|---|
| 1 | Two-party accept-handshake concurrency (challenger sends, opponent accepts/declines/times-out) | A synthetic `ChallengeSessionSpec` conformance harness, no Discord UI: race `accept()` against a simulated `expire()` via `asyncio.gather`; assert exactly one terminal state | `tests/unit/kernel/test_challenge_session_accept_race.py` (new) |
| 2 | Turn-loop + turn-timeout vs. stale-session GC (two independent timeout clocks racing) | A pure-asyncio turn-clock simulation with a fake clock, seeded, across N randomized interleavings | `tests/unit/kernel/test_turn_and_stale_timeout_interaction.py` (new) |
| 3 | Settle-once under a realistic dual-trigger race (the exact deathmatch/blackjack bug shape) | A **sequential** double-call regression test per adopter (matching the existing `test_blackjack_pvp_settle_once.py` precedent — not an `asyncio.gather` race, since `claim_settlement()` has no internal `await`; see §6.4's correction) | Extend `tests/unit/views/test_deathmatch_pvp_settle_once.py` (new) + a `_BjTournament`-specific sibling |
| 4 | Restart-safety for a checkpointed multi-step session (ADR-002's stated first-validator gate) | A `game_state_service` conformance test against a synthetic subsystem key — write a checkpoint, simulate a fresh service instance, assert round-trip + version-mismatch fallback | `tests/unit/services/test_game_state_service_restart_conformance.py` (new) |
| 5 | A raced money+item grant at *real* Postgres concurrency (not the asyncio-mock the current test admits it can't do) | A disposable-Postgres integration tier (skipped when Postgres unavailable) racing `shop_purchase_workflow.purchase_unique_item()` twice for the same item | `tests/integration/test_economy_race_real_postgres.py` (new) — closes the gap for **every** G-12 consumer at once, games included |
| 6 | A fully-populated leaderboard rendered for an L3-owned category | A synthetic 13th `RankProvider` registered only at test time, proving the registry mechanism generalizes with zero production wiring | Add to the existing `tests/unit/services/test_rank_providers.py` |
| 7 | `ChallengeSessionSpec`'s escrow-refund coupling with restart semantics, *together* | A shutdown-hook conformance test simulating SIGTERM against a fake session with an open escrow, asserting `economy_service.refund(...)` fires exactly once | `tests/unit/core/test_shutdown_refund_hook_conformance.py` (new) |

**None of these seven require a game UI, a Discord interaction, or waiting for L3 to be
scheduled.** One honest caveat, surfaced by the games-deferral adversarial pass and not fully
resolved: a synthetic/deterministic harness is *stronger* than a live game within the exact
interleaving its author anticipated, but *categorically blind* to interleavings nobody thought to
construct — which is precisely how both real bugs above went undetected through however many real
games were played (they were found by a source audit, not by any existing test, game-derived or
otherwise, ever observing a double-settle). This asymmetry does not overturn the recommendation
(synthetic oracles are still cheaper, faster, and cover the *known* risk shapes completely) but it
means "these seven replacements substitute for games" should be read as "sufficient for the risk
shapes identified so far," not "provably equivalent to live-game exercise" — Arm D's empirical
pass is the right venue to close that residual gap.

### 6.6 Falsifying both extremes

**"Games must stay before L4/L5."** Strongest case: K7/`settle_once` is the largest unbuilt kernel
band, and the two live money bugs are unambiguously L3. *Survives scrutiny only partially*: both
cited bugs are closeable today without K7 at all (§6.4), and G-12/G-13/leaderboard are already
proven by non-game consumers (§6.3). What does **not** get falsified: the accept-handshake/
turn-alternation concurrency shape and the JSONB-checkpoint-under-restart shape are genuinely
under-proven by any non-game consumer that exists today. **Verdict: the strong form ("games are
the sole proving ground") is refuted; a narrow form ("two specific concurrency shapes have no
non-game analog today") survives as a real but small, now-explicitly-listed residual risk,
addressable by §6.5's harnesses without L3 being built at all.**

**"Games can move to the very end, after L4/L5, with zero primitive lost."** Strongest case: zero
L4/L5 import edges into L3 (§3 C-7), and the money/progression/leaderboard primitives are already
proven by non-game consumers. *Refuted on two independent grounds*: (1) the accept-handshake and
ADR-002 checkpoint rows are genuinely not proven by any non-game consumer today — deferring games
to dead-last without first building the §6.5 replacements leaves those shapes wholly unvalidated
until the very end; (2) `G-17`'s pot/entry-fee settle has **no non-game analog anywhere in the
current bot** — giveaways (the nearest neighbor) is explicitly designed under a different,
non-escrow shape (`G-20-adjacent`, per `FINAL-REVIEW.md:184`), so it does not substitute.
**Verdict: "zero primitive lost" is false. A bounded, named set (accept-handshake, checkpoint-
restart, pot-settle) would go unvalidated until L3 ships if deferred without §6.5's replacements
being built first — but building those replacements costs a small, fixed amount of work regardless
of when L3 itself ships.**

---

## 7. Readiness matrix

53 systems/components classified across four research lenses (L0 kernel + L1a/L1b/L1c + L2 +
L4/L5); L3 (rows 29-42, games) is addressed structurally in §6 rather than per-row, since it has
not yet been through any owner walk and this review's mandate does not include producing one.
Full per-row detail (verified state, target contract, tests, oracle, upstream/downstream) for
every row below is preserved in the lens research outputs cited throughout §3/§4/§6; this table is
the at-a-glance index. Classification enum per §3.1.

### 7.1 L0 — Kernel/foundation

| Component | Classification | Why |
|---|---|---|
| K0 config/observability substrate | `NEEDS_CONTRACT_FREEZE` | Flat `os.getenv` module today, no preflight/validation; target is a typed `Config` + `IntentSpec`; F-3/Q-D5/Q-D19/Q-D21 unresolved |
| Hardcoded 60+-cog loader | `NEEDS_SOURCE_RECONCILIATION` | No design-spec section explicitly retires this shape or specifies its manifest-driven replacement in code-ready terms |
| K1 namespace registry | `NEEDS_OWNER_DECISION` | Zero code, zero prototype (unlike K2); hard prerequisite to K2's own validation (RC-7); §4 Blocker #2 |
| K2 manifest compiler + snapshot | `NEEDS_CONTRACT_FREEZE` | Prototype-proven only (`tools/grammar_spike/`, 13 tests, test-confirmed passing); the actual compiler (`tools/manifest_compile.py`) does not exist |
| K3 DB seam | `NEEDS_CONTRACT_FREEZE` | Pooling/migrations/`pg_advisory_lock` (INV-I) already source-proven; only `IdempotencyKey`/`once()` are genuinely missing — narrower gap than the full 05-spec suggests |
| K4 EventBus → durable outbox | `NEEDS_CONTRACT_FREEZE` | In-process bus source-proven and tested; the durable-outbox upgrade (`event_outbox` table, atomic claim) has zero code |
| K5 lifecycle + managed-task supervisor | `READY_FOR_TEST_DESIGN` | Source-proven, mature, extensively tested; the one new element (PollSupervisor) has no prototype but is small |
| K6 authority engine | `NEEDS_CONTRACT_FREEZE` | Current authority model (split across `governance/capability.py` + `command_access.py`) is real and tested but not the same shape as the target unified `AuthorityDecision` engine |
| K7 workflow/compound-op engine | `NEEDS_ORACLE` | Zero code, zero prototype, zero oracle; §4 Blocker #1 |
| K8 interaction runtime | `NEEDS_CONTRACT_FREEZE` | Extensive current-bot machinery (interaction router, panel manager, nav stack) drives the live 465-golden parity harness; not the target `resolve()` single-seam shape; carries the known views→cogs violation (§4 Important #9) |
| K9 (contradictory definition) | `NEEDS_SOURCE_RECONCILIATION` | §3 C-5 — two frozen docs disagree on what K9 even is |
| K10 (contradictory definition) | `NEEDS_SOURCE_RECONCILIATION` | §3 C-5 — same issue |
| Substrate-kit adoption | `BLOCKED_BY_GATE` | Declaration layer finalized (#1649); Phase-2.5 A/B unrun |
| Gate-0 ratification | `NEEDS_OWNER_DECISION` | §2, §4 Blocker #3 |

### 7.2 L1a + L1b — Operator spine (owner-decided, 17 rows)

All 17 rows are `READY_FOR_TEST_DESIGN` — genuinely owner-decided, all 8 queued bug fixes
independently re-verified present at HEAD, no contradicting source drift found. Two rows carry a
`PARTIAL`-depth caveat (verified via progress-index only, not re-read dossier-by-dossier this
pass; no contradicting evidence found either way): `server_management`, `setup`(5a), `logging`,
`automod`, `counters`, `image_moderation`.

| Row | Classification | Note |
|---|---|---|
| settings | `READY_FOR_TEST_DESIGN` | R-10 rejection-at-pipeline golden still to add |
| diagnostic | `READY_FOR_TEST_DESIGN` | `DiagnosticProviderSpec` sketched, not ratified |
| help | `READY_FOR_TEST_DESIGN` | R-11 is Phase-B kernel work; help itself is settled |
| admin | `READY_FOR_TEST_DESIGN` | 9→8 nav collapse depends on diagnostic's hub-merge landing (decided, not built) |
| server_management | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | |
| setup (5a) | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | Highest execution-risk verdict of any L1b row; exact fold mapping is explicit Phase-B work |
| moderation | `READY_FOR_TEST_DESIGN` | Case/appeal + bulk actions committed, zero oracle since zero implementation |
| logging | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | 97% fit, near-rubber-stamp |
| automod | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | Consolidation panel resolved-on-paper, NOT built (checked, no button in `cleanup_cog.py`) |
| security | `READY_FOR_TEST_DESIGN` | Raid-slowmode path still zero test coverage |
| cleanup | `READY_FOR_TEST_DESIGN` | G-24 confirm-UX for `!cleanuphistory` still open |
| counters | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | Rubber-stamp row |
| channel | `READY_FOR_TEST_DESIGN` | Committed voice-wiring + orphan-string deletion confirmed NOT shipped |
| role | `READY_FOR_TEST_DESIGN` | Committed slash mirrors / legacy-duplicate collapse confirmed NOT shipped |
| ticket | `READY_FOR_TEST_DESIGN` | §4 Cleanup #21 — thinnest test coverage of any L1b row |
| image_moderation | `READY_FOR_TEST_DESIGN` *(PARTIAL)* | Consolidation panel NOT built |
| proof_channel | `READY_FOR_TEST_DESIGN` | Thin test coverage for a subsystem that just had a restart-safety bug fixed |

### 7.3 L1c — Presentation foundation (not yet owner-walked)

| Row | Classification | Why |
|---|---|---|
| visual card engine | `NEEDS_SOURCE_RECONCILIATION` | §3 C-2 — misclassified as ADD-from-scratch; already built, 5 consumers |
| welcome | `NEEDS_OWNER_DECISION` | Not yet walked; substantively already implements its target contract (BindingSpecs-equivalent, R-1 role-grant workflow) — should be a fast walk |
| ux_lab | `NEEDS_OWNER_DECISION` | Not yet walked; lowest-risk of the 3, zero-write, invariant-tested, bare `keep` verdict already |

### 7.4 L2 — Deterministic non-game foundations (not yet owner-walked)

| Row | Classification | Why |
|---|---|---|
| economy | `NEEDS_CONTRACT_FREEZE` | `transfer()` built but unwired, with a documented production-crash history (§3 C-10, §4 Important #11) — command-collision safety is a real unresolved design question independent of any gate |
| inventory | `NEEDS_OWNER_DECISION` | §4 Important #12 — a genuine data-migration decision (type + guild-0 legacy bucket), not just "merge two tables" |
| treasury | `READY_FOR_TEST_DESIGN` | Clean exemplar; no open question found |
| xp | `NEEDS_SOURCE_RECONCILIATION` | R-15 split-ownership open; the shared curve (`level_progress()`) is already de facto proven kernel infrastructure |
| karma | `NEEDS_CONTRACT_FREEZE` | §4 Important #7 — billed exemplar, un-transacted writes |
| community hub | `READY_FOR_TEST_DESIGN` | 100%/100% measured fit — near rubber-stamp |
| community_spotlight | `NEEDS_SOURCE_RECONCILIATION` | §4 Important #13 — undesigned L3-panel sequencing question |
| leaderboard | `READY_FOR_TEST_DESIGN` | MERGE-into-kernel verdict independently validated — already half-executed via the 12-provider registry |
| profile surface | `NEEDS_SOURCE_RECONCILIATION` | §3 C-9 — fully built, frozen doc still says unbuilt |

### 7.5 L4 + L5 — Post-core platform & control plane (not yet owner-walked)

| Row | Classification | Why |
|---|---|---|
| ai (platform) | `NEEDS_OWNER_DECISION` | Genuine platform primitive, cross-domain consumed; no L3 dependency found |
| btd6 | `NEEDS_OWNER_DECISION` | KnowledgeDomainSpec exemplar; 53.8% as-written fit is Lane D's honest floor |
| project_moon | `NEEDS_OWNER_DECISION` | §3 C-8 — "third consumer" framing is aspirational; zero ingestion code today |
| youtube / shared ingestion | `NEEDS_SOURCE_RECONCILIATION` | Already ships bespoke (ADR-007); genuinely new is only the shared abstraction |
| utility | `NEEDS_CONTRACT_FREEZE` | §4 Cleanup #26 — its own cited target contract (G-9) is only half-ratified |
| general | `READY_FOR_TEST_DESIGN` | Lowest-risk item in L4/L5; zero test coverage is the one verification hole (§4 Cleanup #22) |
| web dashboard + live editor | `NEEDS_SOURCE_RECONCILIATION` | §3 C-3 — already ships, dormant behind an env var, not a future build |
| boards family | `NEEDS_SOURCE_RECONCILIATION` | §3 C-4 — a 6th capstone-accuracy contradiction; already has a working web pipeline |
| bot-migration assistant | `NEEDS_OWNER_DECISION` | Zero code exists; a buildable plan exists, explicitly not yet greenlit; confirmed zero L2/L3/L4 dependency |
| Railway / ops control-plane | `BLOCKED_BY_GATE` | Explicitly owner-gated in the frozen plan itself; real supporting infra already exists outside cog code (§4 Future #29) |

---

## 8. Per-system testing architecture

Mapping each testing-architecture class to the systems where it is most load-bearing, given
`parity/COVERAGE.md`'s measured gaps (prefix 96%, slash 88%, persistent-panel components 94%,
persistent panels 82%, **bus events 21%**, **DB tables 25%**, **settings keys 2%**):

- **Parity-golden**: the strongest class today — L1a/L1b's 465-case harness (94%/82% panel
  coverage) is the closest thing to a mature oracle in the corpus. Weakest exactly where it matters
  most: money-moving/state-mutating surfaces (settings 2%, DB tables 25%).
- **Characterization**: mining (108 units, the plan's own "acceptance test") and the `command_
  surface_ledger`'s 479-entry live-command ground truth (superseding the stale 271-row JSON) are
  the two natural characterization targets — both already have real tooling to build on.
- **Contract**: K7's `atomic_db_only`/`audit_completeness`/`idempotency_posture_declared` compiler
  fences (design-only today) are the target mechanism; `test_no_view_level_purchase_writes.py` is
  the one AST-enforced contract test that already exists for this class in production.
- **Integration**: the repo-wide gap is real-Postgres concurrency — every "concurrency" test found
  this session (economy, treasury) explicitly documents Postgres is unavailable in this CI and
  only asserts asyncio-layer behavior. §6.5 item 5's disposable-Postgres integration tier is the
  single highest-leverage new test infrastructure this review identifies.
- **Concurrency-race**: `settle_once` (deathmatch/blackjack, §6.4), `_check_tourn_done`'s two-site
  race, karma's un-transacted 3-write sequence (§4 Important #7), and G-17's pot-settle are the
  four concrete, named race classes with no adequate oracle today.
- **Mutation-audit**: INV-F/INV-G (economy/xp) are the only AST-scanned domains; karma has no
  catalogued invariant letter of its own (§3 C-11) despite being billed the audited-seam exemplar.
- **Event-atomicity**: INV-A (KNOWN_EVENTS) is a runtime warning, not a boot-time failure, today;
  37 of 47 catalogued bus events have zero golden coverage, including `welcome.member_greeted`
  (§4 Cleanup #20).
- **Restart/lifecycle**: proof_channel's fix (just shipped) and the still-open RPS-tournament
  forfeit bug (`rps_tournament/_persistence.py:104-115`, confirmed still live by the invariants
  pass) are the two concrete current-bot instances; ADR-002's checkpoint mechanism (§6.5 item 4) is
  the class's un-built-but-well-specified target.
- **Authority**: `command_access.py`/`governance/capability.py`'s current model has substantial
  existing test coverage; the callback-time re-check rule is documented but review-enforced, not
  mechanism-enforced, today — the rebuild's design (generated-callback re-resolution) is the
  strongest single invariant answer in the whole corpus (§ per invariants deep-dive §4-equivalent),
  but is entirely `[design-only, zero code]`.
- **Navigation-UX**: the `build_help_menu_view` get_cog+getattr dispatch pattern (43 of 58
  extensions) and its two sub-shapes (§4 Important #9) are the class's concrete current-bot defect;
  Back/Home's non-stack-awareness (a known, tracked Phase-B nav-engine item) is the other.
- **Deterministic-provider**: the AI platform's 66-golden + 16-BTD6-probe eval corpus
  (`tests/evals/`) is a real, separate oracle, explicitly reported as a "sibling asset, not
  double-counted" — worth folding into the main harness's accounting rather than leaving it
  invisible to `parity/COVERAGE.md`'s headline numbers.
- **Live-co-test**: this is Arm D's lane entirely; this review's contribution is the concrete list
  of what to exercise (§6.4's two bugs, §6.5's seven synthetic-harness targets, community_
  spotlight's empty-state rendering, `SettleOnceMixin`'s await-ordering contract).

---

## 9. Required planning deltas

| Delta | Evidence | Why | Canonical owning artifact | Owner decision? | Gate impact |
|---|---|---|---|---|---|
| Fix `deathmatch_cog._DuelView` and `_BjTournament`'s settle-once non-adoption now, independent of the rebuild | §6.4 | Both cited live money bugs are closeable today; the fix is small, contained, reversible | Current-bot bugfix PR (not a planning doc) | No — contained, act-vs-ask "act" bucket | None — orthogonal to Gate-0/Phase-2.5 |
| Widen `check_consistency.py` Rule 6's `_WAGER_SETTLE_CALLS` frozenset beyond `{settle_pvp, refund_pvp}` | §3 C-1 | The checker's scope is why both bugs went undetected by an existing guard | `scripts/check_consistency.py` | No | None |
| Give K7 a paper stress-test/spike comparable to K2's `grammar_spike`, before Gate-0 treats the workflow engine as settled | §4 Blocker #1 | Disproportionate validation gap for the plan's own "largest kernel band" | `design/strand-2-runtime-durability/07-workflow-engine.md` | Recommended, not currently owner-gated | Should inform Gate-0 ratification |
| Reconcile K9/K10's contradictory definitions between `rebuild-design-spec-2026-07-02.md` and `gate-0/phase-b-l0-build-order.md` | §3 C-5 | A builder following Gate-0 literally never lands kernel/ai hardening or the sim/golden-parity gate | Both documents | Yes — which numbering wins | Blocks clean Phase-B L0 execution |
| Route the 12 `Q-D` rows + `L-21` to `docs/owner/maintainer-question-router.md` and hold the ratification sitting | §2 | Named "step 1 of what's next," unstarted, invisible to the router | `gate-0/owner-decision-packet.md` → router | Yes, explicitly | Blocks all new-repo code |
| Reclassify visual card engine (row 17) from ADD-from-scratch to formalize-existing-plus-finish-2-migrations before the next Stage-2 walk touches L1c | §3 C-2 | An owner deciding on stale text evaluates the wrong question | `NEW-BOT-BUILD-PLAN.md`, `rebuild-stage2-subsystem-walk-2026-07-05.md` | Yes — small, but should be corrected before the live walk | None |
| Migrate `mining_render.py`/`character_render.py` onto `card_render.py` now | §4 Important #16 | Cheap, mechanical; closes an L1c→L3 coupling before L3 work compounds it | N/A — small code PR | No | None |
| Reconcile row 49/50's actual remaining scope (both already substantially built) before Phase-B allocates build effort | §3 C-3, C-4 | Two capstone-accuracy misses beyond the walk doc's own five; a sixth methodology gap (web-tier prior art is systematically missed by cog-scoped sweeps) | Walk doc + `NEW-BOT-BUILD-PLAN.md` | No — factual correction | None |
| Fix `karma_service.give()`'s un-transacted 3-write sequence | §4 Important #7 | The rebuild's own cited exemplar audited seam is less atomic than treasury's | Current-bot bugfix PR | No | None |
| Build a CI-time command-collision preflight before any `!give`/`!pay` re-wiring attempt | §4 Important #11 | Exact same incident class (Q-0211) already happened once in production | `docs/ideas/command-collision-checker-2026-06-29.md` → build it | No | None |
| Decide `inventory`'s user_id-type + guild_id=0-legacy-bucket migration strategy | §4 Important #12 | A genuine data-migration decision, bigger than "merge two tables" | Row 21's future Stage-2 dossier | Yes | Feeds L2 walk, not gated |
| Decide `community_spotlight`'s Games-panel L2-before-L3 interim-state (empty boards vs. deferred panel) | §4 Important #13 | Undesigned anywhere; a real L2-into-L3 dependency | Row 26's future Stage-2 dossier | Yes | Feeds L2 walk |
| Reconcile `FINAL-REVIEW.md`'s bucket-(d) `SettingsPresetSpec` refutation against the corpus's own later, more precise scoping | §3 C-12 | Two frozen docs disagree about whether C-3/Q-0228 is closed | `FINAL-REVIEW.md` + `presentation-verification-mechanics-2026-07-03.md` | Yes — how many distinct preset families really exist | Feeds Gate-0's amendment fold |
| Rule on `G-20`/`G-21`/`G-22`'s thin-recurrence profile — hold to bucket (c) like `P-1`, or document why their bar differs | §3 C-13 | Internal inconsistency in the review's own stated discipline | `FINAL-REVIEW.md` §3.2/§3.3 | Yes | Feeds Gate-0's amendment fold |
| Verify the views→cogs sub-shape-B closure (private-cog-method calls from views) is real, not assumed, via a contract test | §4 Important #9 | R-11 only names sub-shape A | K8/S9's absorption-edit design | No | None |
| Add rebuild mechanisms (or an explicit `NEEDS_SOURCE_RECONCILIATION` acknowledgment) for `INV-B/C/D/H/I/J`, especially the two DB-uniqueness invariants | §4 Important #15 | Six of fourteen named invariants have zero rebuild mechanism anywhere in the design spec | `rebuild-design-spec-2026-07-02.md` | Yes | Should inform Gate-0 ratification |
| Correct `NEW-BOT-BUILD-PLAN.md:82`'s stale profile-surface claim in the frozen document itself | §3 C-9 | Uncorrected for 2 days after the walk doc flagged it | `NEW-BOT-BUILD-PLAN.md` | No — docs-only, zero risk | None |
| Build the 7 headless synthetic-oracle replacements before deciding L3's exact build slot | §6.5 | De-risks the genuinely game-unique primitives without needing L3 scheduled at all | New test files, listed in §6.5 | No | None |

---

## 10. Simplification opportunities

- **Leaderboard dissolution is lower-risk than a fresh design would suggest** — the current
  `rank_providers.py` 12-provider registry is already the target shape at production scale; the
  rebuild's job is mechanical re-registration per subsystem, not a from-scratch pattern.
- **The two "current state" projections for the dashboard** (`export_dashboard_data.py`'s static
  AST scan vs. `control_api.py`'s live `/control/manifest` read) should be reconciled or unified —
  two independent sources of truth for the same data with no drift-check between them.
- **The web-only boards pipeline and the new owner-decided Discord-side intake should land on one
  primitive from day one** rather than being designed separately and unified later — the web half
  already exists and works; design the Discord half against it directly.
- **`mining_render.py`/`character_render.py` → `card_render.py` migration** (§4 Important #16,
  §9) — small, mechanical, and removes a live fragmentation instance before L3 work compounds it.
- **Preset/template consolidation (C-3)** should be re-scoped against the corpus's own later,
  more precise finding (2-3 distinct families, not 1) rather than the earlier, over-broad
  "unify everything" framing that bucket (d) partially retreated from.
- **K9/K10 doc reconciliation** (§3 C-5) is cheap (a docs-only pass) and removes a real source of
  confusion for whoever executes Phase-B's L0 build literally from the Gate-0 packet.
- **`db.transaction()` vs. the older manual `pool.acquire()+conn.transaction()` idiom**: migrate
  `economy_service.transfer()` onto the newer primitive so the codebase's flagship G-12 exemplar
  actually demonstrates the pattern being vouched for, rather than a parallel one.

---

## 11. Deferred scope

Per `NEW-BOT-BUILD-PLAN.md` §5 (unchanged by this review, re-confirmed still deliberate): voice/
music (Q-0041 gate, zero voice code verified), external feeds (no feed primitive today, would ride
G-1/G-3/ManagedTaskSpec if ever wanted), premium/paywall architecture (anti-goal, not a gap),
Mudae-style gacha (deliberate omission), open-domain AI chat (grounded/eval-first by design),
external analytics dashboards, deep BTD6 decode/live spot-checks (demand-gated), the ideas-lab §6
rejection ledger (binding), and vector DB/durable-execution-engine/external-agent-framework/model
pinning (explicit non-goals per design-spec §10.3).

This review adds, with evidence: **the `G-17` pot/checkpoint concurrency proof can be deferred
behind a cheap headless spike** rather than requiring L3 itself to be scheduled (§6.5 #1, #3); and
**mining's position as *last-within-L3* is independently validated** by this review (its depth/
breadth make it a genuine, if expensive, stress-test) even though its position as *the necessary*
acceptance-test gate is not load-bearing (§3 C-6).

---

## 12. Genuine owner decisions remaining

1. The 12 Gate-0 `Q-D` rows + `L-21` (owner-decision-packet.md) — the literal first item on the
   program's own stated critical path, currently invisible to the router.
2. Whether K9/K10's contradictory definitions resolve to the design-spec's meaning, the Gate-0
   packet's meaning, or a deliberate merge of both.
3. `inventory`'s data-migration strategy (user_id type cast; guild_id=0 legacy-bucket disposition).
4. The command-namespace-collision-safety approach for re-wiring `!give`/`!pay` (a CI preflight,
   per the existing idea doc, or an alternative).
5. `community_spotlight`'s Games-panel interim state during an L2-before-L3 build window.
6. Whether the `G-20`/`G-21`/`G-22` bucket-(b) families should be held provisional (bucket (c),
   like `P-1`) or ratified as-is with a documented rationale for the asymmetric bar.
7. Whether preset/template consolidation (C-3) targets one unified primitive or the corpus's own
   later-found 2-3 distinct families.
8. `R-15`'s xp split-column-ownership resolution (xp table: xp.service writes xp/level, economy
   writes coins; fishing writes 2 mining-owned tables).
9. Whether the L1c visual-card-engine row is re-scoped (formalize + finish 2 migrations) before or
   during the next live Stage-2 walk session.
10. `G-22`'s embedded question (standardize `StagedBuilderSpec` vs. bless 3 staging lanes) —
    **already resolved** per the Stage-2 walk (row 13, 2026-07-05: `RoleMenuBuilder` blessed as the
    sole instance) — noted here only so a future session doesn't re-open it believing it's still
    open; not a genuinely remaining decision.

---

## 13. Inputs required by the final synthesis

- **From Arm B (Codex, source/test truth):** independently re-verify the precise counts this
  review found imprecise or disputed — the preset/template family count (13× vs. 14× vs. actual),
  `db.transaction()`'s exact caller count, `SettleOnceMixin`'s exact adoption count (this review's
  own adversarial pass corrected 5→4), whether additional views→cogs sub-shape-B instances exist
  beyond the two found here, and a full `INV-A`..`INV-N` cross-check against every rebuild spec
  document (this review checked six of fourteen against `rebuild-design-spec-2026-07-02.md` only).
- **From Arm C (external/migration/live-GitHub):** confirm PR #1750's live status and whether any
  newer PR has landed since this review's HEAD snapshot (`cf5a234`); external Discord/discord.py
  2.7 constraints specifically relevant to K8's target interaction-runtime redesign; whether the
  Railway/ops control-plane infrastructure this review found outside cog code (the HQ guild's
  deploy-alert webhook, the CI backup-integrity gate) is externally verifiable as currently
  functioning.
- **From Arm D (empirical live-testing):** whether `SettleOnceMixin`'s "no `await` before the
  claim" contract is actually honored everywhere it's adopted (this review found it honored in
  every instance checked, but did not exhaustively trace every call path); a live double-click
  race against `deathmatch_cog._DuelView` and `_BjTournament` to confirm both bugs reproduce as
  described; whether `community_spotlight`'s Games-panel empty-state rendering is visually
  acceptable with all 4 L3 categories showing zero data; whether the RPS-tournament forfeit bug
  (`rps_tournament/_persistence.py:104-115`, confirmed still present in source by the invariants
  pass) reproduces live; and — the single most decision-relevant empirical question for the
  overall Gate-V verdict — whether any of the §6.5 synthetic-harness replacements, once built,
  actually catch the two known bugs as reliably as Arm D's own live exercise would.

---

## 14. Evidence appendix

**Test suites actually executed this session (test-confirmed, not merely source-read):**
- `python3.10 -m pytest tests/unit/tools/test_grammar_spike.py` — 13 passed.
- `python3.10 -m pytest tests/unit/parity/` — 10 passed, 1 skipped.

**Primary source files read in full or substantially, by lens/phase (non-exhaustive index; full
citations are inline throughout §3–§9):**
- *Lens A (L0):* `disbot/bot1.py`, `disbot/config.py`, `disbot/core/events.py`, `disbot/core/
  runtime/{tasks,lifecycle,command_access}.py`, `docs/capability-authority.md`, `disbot/utils/db/
  migrations.py`, `disbot/cogs/deathmatch_cog.py`, `tools/grammar_spike/manifests/blackjack.py`,
  every Gate-0 deliverable (`README.md`, `owner-decision-packet.md`, `phase-b-l0-build-order.md`,
  `frozen-l0-grammar.md`), `docs/current-state/S3-ai-memory.md`, `docs/planning/rebuild-
  amendments.yml`.
- *Lens B (L1a/b/c):* the full Stage-2 walk doc sections 6-7, `disbot/utils/card_render.py`,
  `disbot/services/welcome_service.py`, `disbot/cogs/welcome_cog.py`, `disbot/cogs/ux_lab_cog.py`,
  and per-row source files for all 8 §7.1 fixes and representative §7.2 spot-checks.
- *Lens C (L2):* `disbot/cogs/economy_cog.py` (full, 410 lines), `disbot/services/{economy_
  service,karma_service,treasury_service}.py` (full), `disbot/utils/db/{karma,xp}.py`, `disbot/
  cogs/{inventory_cog,community_cog,community_spotlight_cog,leaderboard_cog}.py`,
  `disbot/services/rank_providers.py` (full, 708 lines), `disbot/views/profile/{profile_view,
  editor}.py`, migrations 002/017/092, `docs/planning/reconciliation-pass-2026-06-29-band1560.md`.
- *Lens D (L4/L5):* `disbot/services/{ai_gateway,ai_task_router,ai_tool_catalogue,ai_tools}.py`,
  6-cog btd6 split + `btd6_ai_service.py`, `disbot/cogs/project_moon_cog.py`, `disbot/cogs/media_
  maintenance_cog.py` + 4 youtube services, `disbot/cogs/{utility_cog,general_cog}.py`, `disbot/
  control_api.py` (full, 861 lines), `dashboard/app.py`, `botsite/submit.py`, `dashboard/
  github_mirror.py`, `docs/planning/bot-migration-assistant-plan-2026-06-24.md`, `.github/
  workflows/backup-db.yml`, `docs/ideas/central-admin-and-logging-guilds-2026-07-02.md`.
- *Sequencing/invariants/games-deferral deep-dives + adversarial passes:* `disbot/utils/terminal_
  guard.py` (full), `disbot/views/games/deathmatch_panel.py`, `disbot/views/blackjack/
  tournament_views.py`, `disbot/services/game_wager_workflow.py`, `disbot/services/blackjack_
  state.py`, `disbot/utils/db/games/{deathmatch,player_skills,mining_structures}.py`,
  `disbot/utils/db/pool.py`, `docs/decisions/002-game-state-not-restart-safe.md`,
  `docs/planning/rebuild-design-spec-2026-07-02.md` (targeted, ~40 cited line ranges),
  `docs/analysis/rebuild-discovery/foundations/design/strand-2-runtime-durability/{07-workflow-
  engine,09-scheduler-state}.md`, `docs/analysis/rebuild-discovery/foundations/{runtime-logic-
  mechanics,presentation-verification-mechanics}-2026-07-03.md`.

**Live GitHub / git checks performed:** `git log --oneline -30` (three times, independently, from
different lenses, all scoped to their own files-of-interest); `mcp__github__list_pull_requests`
(state=open) → exactly one result, #1750; `ls docs/owner/claims/` → empty but README.

**Grammar-fit and coverage numbers cited throughout, re-verified against source this session:**
`FINAL-REVIEW.md` §2's 43-subsystem table (63.8%→85.1% overall; games cluster casino 24%/blackjack
44%/deathmatch 75.5%/rps 78%; governance cluster moderation 64.2%/role 69.4%/admin 72.5%);
`parity/COVERAGE.md`'s 465-golden-case summary (prefix 96%, slash 88%, panel-components 94%,
panels 82%, bus events 21%, DB tables 25%, settings keys 2%).
