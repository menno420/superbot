# Rebuild FINAL review — the A–H report (2026-07-07)

> **Status:** `audit` — the final pre-build review of the rebuild plan of record
> ([`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md)), executed per the
> [Fable-5 ultracode brief](rebuild-final-review-fable5-ultracode-brief-2026-07-07.md) §3 (mandates
> A–H) under **Q-0241** (never-wait, live-test, silence=consent) and **Q-0240** (decide-and-flag).
> Evidence: 15 parallel research agents (coverage census ×3, per-idea evaluation ×10 ideas,
> stale-prose sweep ×2, sim audit ×2, §6.3 bug verification ×4, ground-truth readiness ×1, official
> Discord-docs validation ×1) + 4 A/B session agents + 1 independent judge + first-hand source
> reads. Source wins over every claim here (Q-0120). The plan edits this review produced are the
> canonical plan's **§11 amendments A-1…A-11**; the shipped code is PRs **#1781** (settle-once
> fixes, merged) and **#1782** (`!pay`/`!transfer` wiring, merged) + the substrate-kit adopt fix
> (this session's PR).

---

## A. Final opinion + readiness score

### The candid opinion

**This plan is ready to execute, and it is the best-grounded plan this repo has ever produced.**
Its unusual strength is that nearly every load-bearing claim carries a verification tier — live >
source-read > inference — and where this review hunted for rot it mostly found the plan *ahead* of
its critics (three of the brief's four named coverage gaps turned out to already have explicit
walk-row landings). The consolidation discipline (one plan, §9 dispositions, decisions log with
rationale) held up under a 15-agent adversarial sweep: we found **one internal contradiction**
(D-17 vs §2.2 on `role_menu`'s CI status — now corrected), **one under-specified build step**
(step 11's `check_sim_gate`, whose real contract lives in the design spec — now pointered), and
**one genuinely thin subsystem story** (the setup wizard — now hardened as A-9). That is a very
short defect list for a corpus this size.

The plan's honest weak edge is not the plan text — it is that **layer V (the verification
substrate) is the least-built thing in the program at exactly the moment Q-0241 removed the human
gates.** Parity is broad but shallow (events 21% / tables 25% / settings 2%), and `verified_live`,
the `sim/` runner, and `check_sim_gate` have zero code. The plan sequences all of this correctly
(step 11 before the port bands; capture-before-freeze at step 14), so the risk is not a plan gap —
it is an *execution-discipline* gap: a future band session tempted to port against thin goldens.

### Readiness score, per §5 start-sequence step (ground-truth-verified at head)

| §5 step | State at head (verified, not claimed) | Blocking? |
|---|---|---|
| 1 kit tail ① | ✅ shipped #1775 (427 → **432** kit tests after this session's fix) | — |
| 2 Phase-2.5 | ✅ **COMPLETE this session**: RUN #1775 (FAIL as-tested) → adopt-render fix + T2/T4 re-run pair (§H below) | — |
| 3 check_amendments | ✅ built #1775; runs green; green **spot-checked truthful** (G-1 → design-spec §2.8, Q-0105 verification) | — |
| 4 Stage-2 walk | 17/53 rows decided (L1a+L1b); 36 remain, owner-live | No — paces *port bands*, not the start |
| 5 G1 sitting | 🗑 retired (Q-0241); §1 = react-anytime veto surface | — |
| 6 create repo | **startable TODAY** — nothing precedes it anymore | ← the actual start line |
| 7 bootstrap kit | ready — adopt now proven **cold** (this session's fix + re-run), not just warm | — |
| 8 control plane | specified (design-spec §6 six named gates + CODEOWNERS; railway plan §4) — build-at-step | — |
| 9–10 kernel S1→S15 | specs frozen; K1 NamespaceRegistry + K7 engine are the zero-code items, both sequenced | — |
| 11 layer V wiring | `sim/` runner / `check_sim_gate` / `verified_live` = **zero code** (verified); parity 466 golden files, replay workflow exists (manual, non-required by design) | The pivotal step — see The Risk |
| 12 K10 + test guild + CUT-1 | designed (companion C; interaction-token constraint now **validated + frozen**, A-10) | — |
| 13 port bands | Sequence C; walk rows land per band | — |
| 14 telemetry capture | open; correctly pinned *before any freeze* | — |
| 15–17 CUT-2/3 | prose now states the reaction-window model + the honest CUT-3 justification (mandate E) | — |

**The score: the new repo can start now — zero blocking work remains ahead of step 6.**
Completeness **9/10** (was 8 before the §11 folds — the misses were real but small: background-
obligation landings, wizard hardening, off-Discord surface). Internal consistency **9/10** (one
contradiction found + fixed; one frozen-doc fork decided in A-9). Start-readiness **10/10** (steps
1–5 all cleared or retired; step 6 is un-gated). Estimated remaining pre-CUT-1 volume: steps 6–12,
≈ the plan's own 5–8-day kernel figure + step-11's verification build — unchanged by this review.

### The single biggest risk

**The machine gates that replace the retired human gates are the least-built part of the program.**
Q-0241 moves the owner from approval-before to reaction-after; what keeps that safe is layer V
(deep goldens, `verified_live`, sim gate) plus the reversibility rider — and layer V is exactly
where the zero-code items cluster. If any port band starts before step 11 lands at real depth
(P-5: curated event/table/settings goldens per band), the program is running never-wait with
neither human nor machine verification at depth. **Mitigation already in the plan** (step ordering
+ born-red parity), **plus this review's addition:** the step-11 text now carries the concrete
oracle decomposition and the `check_sim_gate` contract pointer so the step cannot be
"minimally satisfied." Watch this one step; everything else has slack.

---

## B. Feature-vs-existing coverage — what the plan forgets (and what it doesn't)

The brief named four suspected misses. **Three were already landed** — the census verified against
the corpus, correcting the brief (Q-0120):

| Brief's suspect | Verdict | Where it actually lands |
|---|---|---|
| HealthMaintenanceCog retention (Q-0097) | ✅ explicit landing | walk row 44: "ManagedTaskSpec (health_maintenance's daily retention loop) — reused" |
| MediaMaintenanceCog purge (Q-0099) | ⚠ **implicit only — never named** (its health twin IS named) | → folded as **§11 A-8** (named ManagedTaskSpec consumer + `StoreSpec.retention`) |
| hermes `/bugreport` | ✅ deliberate-drop, redirected | walk row 50 boards family (user-facing `/suggest`) |
| Setup wizard surface | ⚠ **confirmed thin** | → hardened as **§11 A-9** (roster row + G-19 freeze/widen + draft-lane fork decided) |

The full census (two agents: `tasks.loop`/schedulers/boot-jobs + glue-cogs/one-shots/egress; ~30
items) found the plan's §2.4 B-2 class-level catch-all gives everything at least implicit
coverage; the genuine finds beyond the brief's list, all now folded via **A-8/A-11**:

- **WebhookReporter operator-alert feed** — the runtime Discord-webhook egress (startup/shutdown/
  cog-fail/task-died/command-log embeds) with its `redact_text` secret-redaction obligation:
  appeared in **no corpus doc**. Now a named K5/observability sink spec (A-8).
- **role_grants expiry sweep** (privilege-retention: temp roles must drop) and **session_gc TTL
  sweep** (session/anchor data-minimization) — mechanism-covered but obligation-unnamed; both now
  named spec-09/K9 consumers (A-8).
- **hermes `/dispatch`** — owner-dropped 2026-07-05 with the capability reconstituted nowhere;
  now explicitly dispositioned (A-11: it lives in the agent-workflow layer, not the bot) so future
  censuses stop re-finding it.
- Wizard detail (the confirmed-thin story): setup had **no standalone roster row** (one clause on
  the server_management row); **G-19 WizardSectionSpec** sits in the amendment registry as
  `pending-gate-0, spec_ref: null` with consumers `[cleanup, role, ticket]` — **6 of the 10 live
  `views/setup/sections/*` registrants missing**; and two frozen docs disagreed on the setup draft
  lane (spec-06 preserves it; walk row 5a retires it). A-9 fixes all three, deciding the fork as:
  the K9 draft pipeline ships as specced (many producers), the setup *feature* folds into
  Essential's direct lane, `Producer.HUMAN_SETUP` stays reserved-but-unconsumed. ⚑ flagged.

## C. Un-added ideas — dispositions (all 10 evaluated)

| Idea | Verdict | Landing |
|---|---|---|
| Schema-growth ledger (Q-0219 enforcement) | **fold-now** | §11 A-2 → K2/S3 (+ K2 row pointer) |
| Navigation-completeness golden (Q-0231) | **fold-now** | §11 A-3 → K8 / step 11 |
| Unified layout-success simulator (Q-0235) | **fold — scoped** (harness + first oracle, NOT a subsume-all engine; hub-topology fits natively, settings-grouping is half-in, dense-panel is a different oracle — grounded in the 5 sims' actual scoring functions) | step 11 text + §11 A-4 |
| Critical-review checkers (audit-AST + state-mutation fence) | **fold-partially** (the two residual holes the K7 fence concedes) | §11 A-5 → K7 + S11 |
| Websites cutover role + progress dashboard | **fold-partially** (producer repoint + CUT-3 comms role; dashboard stays an open fork) | §11 A-6 → steps 13/17 |
| In-server release→test→verify loop | **fold-partially** (announcer + usage-coverage oracle + test/debug mode; the 4th part is already V-5's UI) | §11 A-7 |
| `check_doc_cites.py` | **defer** — current-repo doc hygiene; routes as its own idea/PR, gates nothing in S0–S15 | not folded (recorded) |
| Projects-EAP as coordinator | **defer** — plan stays product-agnostic; thin wiring note lands on §5 if the owner accepts the EAP | not folded; see the [product review](projects-eap-product-review-2026-07-07.md) |
| C-7 one-description-surface | **already covered** (K2 manifest + help-as-projection + manifest-generated intent surface) | none needed |
| START-HERE doc index | **already covered** — the canonical plan + §9 *are* it | none needed |

## D. Forgotten items / stale prose — swept and fixed

Two sweep agents classified every owner-gate hit in 19 rebuild docs into stale-live /
historical-ok / already-fixed. **20 stale-live sites found; all fixed this session:**
`rebuild-owner-briefing-2026-07-07.md` (6 — it was written hours before Q-0241 and still told the
owner a sitting was required; now carries an amendment banner + in-line corrections),
`rebuild-ultracode-handoff-2026-07-02.md` (4 + banner), `rebuild-phase-2.5-procedure-2026-07-06.md`
(3 — incl. "owner accepts at the G1 sitting" → agent-accepted per Q-0241),
`current-state/S3-ai-memory.md` (4 lower ▶-startable bullets incl. the "🔒 REBUILD OWNER GATE"
block), `docs/planning/README.md` (2 rows + the initiative header), and the design-spec's top
banner (1 — its §10.2 list re-labeled as the veto payload). Superseded/frozen docs
(strategy §3, parallel-execution, planning-phase, GATE-V synthesis + corrections,
linchpin-validation, NEW-BOT-BUILD-PLAN/FINAL-REVIEW) were deliberately **not** edited — the
canonical plan's §9 dispositions govern them; fixes belong at citing sites only.
Also validated + frozen: companion C's interaction-token constraint (A-10, official Discord docs —
Ed25519-signed webhook delivery, Discord-minted 15-min tokens, no cross-app invocation endpoint;
user-installable apps / Components v2 don't change the model).

## E. The Q-0241 work, reviewed (CUT-2/3 + the Q-0213 boundary)

The five governance homes are mutually consistent (grounding-confirmed; re-read here). The two
named nails are now driven: **(1)** §5 steps 15–17 read as reaction windows — the dry-run
reconciliation is *posted*, not *awaited*; shadow-first is named as the reversibility that
replaces approval. **(2)** CUT-3's justification is restated honestly on the step itself: it is
safe to run un-gated **not because it is shadow** (it is live prod) but because **every leg stays
reversible while the owner reacts** — token swap reverses by swap-back, N=7d + archived backup +
reverse-import valve round-trip the data tier, and nothing is deleted until the window closes.
The Q-0213 prod-data brake is **satisfied by the rider, not bypassed** — that phrasing now lives
on step 17 so no future reader derives "shadow-ness" as the safety argument.

## F. Projects-EAP product review

Delivered as the standalone owner-sendable artifact:
**[`projects-eap-product-review-2026-07-07.md`](projects-eap-product-review-2026-07-07.md)** —
organized on the EAP's seven feedback axes, grounded in this repo's hand-rolled equivalents of
every Projects feature, with the cross-cutting normal-Claude-Code ideas separated in its §9
(7 items, each traced to a concrete incident — including two from this very session).

## G. Simulator centralization audit

**Verdict: NOT centralized today — grouping+naming is validated by ≥8 disconnected mechanisms**
(4 sim-side: help_menu_grouping reachability, settings_order routes, role_menu drift-pin,
grammar_spike tiering; 4+ checker-side: command-reachability, settings-reachability, setup-copy
jargon ratchet, settings-hub dropdown test), with **zero shared abstraction** — which is exactly
what §5 step 11's `sim/` runner + `check_sim_gate` exist to fix, and they have **zero code**.
Found + fixed: the **D-17 ↔ §2.2 contradiction** (role_menu is a *live CI drift-pin* via
`test_role_menu_layout_sim.py::test_inventory_matches_the_live_builder`; D-17 mis-filed it as
archived — corrected in D-17 with provenance). Coverage gaps with **no** sim/checker at all:
command-name conventions, K1 collision rules (future K1/K2 machinery covers this), cross-subsystem
navigation completeness (now A-3), general dense-panel layout, description quality beyond the
setup tree. Step 11 was **under-specified** (the `check_sim_gate` contract lives only in the
design spec §5) — the step now pointers it explicitly and carries the harness/oracle decomposition
(shared runner + pluggable per-surface oracles; the layout-success idea is the *first oracle*, not
a subsume-all engine — the 3 planned manifest sims are genuinely different oracles, per their
actual scoring functions).

## H. Repo prep + live-bot work — shipped this session

1. **Phase-2.5 remainder (the G2 close-out).** The **adopt-renders-what-it-knows** kit fix:
   new `engine/derive.py` (deterministic slot derivation: project name, language incl.
   `requires-python`, verify command, docs root → recorded as *provisional* interview answers —
   seeds the interview, never overwrites, never graduates unconfirmed); docs still carrying
   unfilled `${...}` slots plant under a **loud UNRENDERED banner** (auto-stripped by
   `render --live` once a file fully renders); adopt **vendors the single-file `bootstrap.py`**
   into the target root so staged/live hook commands resolve in-repo (the second FAIL cause);
   `run_session` no longer downgrades a derived value to an `ASSUMED:` placeholder. 432/432 kit
   tests; `dist/bootstrap.py` regenerated; live-smoked cold (adopt → `check --strict` clean →
   `render --live` strips the banner). **Re-run pair (T2 build-a-feature + T4 resume-cold, ON vs
   OFF, same model, fixed kit) — reported honestly: the overhead did NOT flip.** M1: T2 ON=1700
   vs OFF=549; T4 ON=3106 vs OFF=952 — rendered docs get *read* (they no longer look inert), and
   reading costs more than skipping raw templates did; completion tied (both arms shipped working
   features); **the ON sessions twice failed to end cleanly** (no commit) while OFF committed
   both times; and **no ON session wrote back to any kit surface** — the same write-back failure
   as the original run, now decoupled from readability. Full verdict + what it means for K0:
   the [G2 report's re-run addendum](phase-2.5-cold-start-report-2026-07-07.md). The mechanical
   fix stands on its own merits (hooks resolve, docs render, cold `check --strict` green — all
   prerequisites for real adoption); the *cold-start benefit claim* remains unproven and the
   report says so. `check_amendments.py` output spot-checked truthful (Q-0105).
2. **Settle-once fixes — PR #1781, MERGED (live in prod).** Deathmatch `_DuelView` mixin retrofit
   (the Arm-D live-confirmed double-write); blackjack FREE-tournament double-pay guard; **plus a
   third instance of the same class found during verification** — RPS `check_tournament_progress`
   races its two semifinal resolvers to the FREE-reward payout (both await between deleting their
   match entries and the `not self.matches` check); fixed with a per-tournament claim via the new
   documented `SettleOnceMixin.rearm_settlement()` seam. **Rule 6 widened** (cogs/ root +
   `payout_tournament`/`update_leaderboard` sinks) so the checker catches this non-adopter class;
   8 concurrency regressions + 4 checker regressions.
3. **`!pay` / `!transfer` — PR #1782, MERGED (live in prod).** The ready-but-unwired
   `economy_service.transfer()` wired — **as `pay`/`transfer`, NOT `give`** (banned token,
   Q-0211 boot-collision history; the brief's `!give/!pay` shorthand predates the ban).
   Live-exercised against real local Postgres (Arm-D pattern): balances 70/35 exact, exactly two
   audit rows, insufficient-funds clean.
4. **§6.3 items verified already fixed (no action, recorded):** cleanup word/strict toggles +
   `!cleanuphistory` audit (both closed by #1728's commit — note: the toggles route through the
   new `prohibited_words_service` seam, not ChannelLifecycleService as the frozen doc guessed),
   bot_spam greeting, raid-lockdown slowmode, role 3-table teardown (#1728).

## Decisions log (Q-0240 — every call this review made; ⚑ = flagged for veto)

| # | Decision | Rationale (one line) |
|---|---|---|
| ⚑ R-1 | O-6 (deathmatch fix shape) = **SettleOnceMixin retrofit**, executed #1781 | uniform with all 4 sibling adopters + checker-recognizable; a bespoke guard needs custom checker exceptions |
| ⚑ R-2 | Blackjack/RPS free-leg guard = in-process claim, not sentinel escrow rows | smallest diff, matches PvP sibling idiom; no recovery path replays the free leg, so in-process suffices |
| ⚑ R-3 | Transfer ships as `!pay`/`!transfer`, **ungated** | Q-0211 bans `give`; siblings (daily/work) are ungated self-serve verbs on an audited seam; reversible kill-switch path named in #1782 |
| ⚑ R-4 | A-9 draft-lane fork: K9 pipeline ships as specced; setup feature uses the direct lane; `Producer.HUMAN_SETUP` reserved-but-unconsumed | reconciles the two frozen docs without editing either; many non-setup producers need the pipeline |
| ⚑ R-5 | O-1 (atomicity) recommendation: **single-transaction multi-leg money/progression writes** as ONE systemic P-1 contract across economy+karma+xp | the `*_in_txn` helpers exist; per-subsystem policies re-create the drift the rebuild kills |
| ⚑ R-6 | O-2 (XP audit) recommendation: gameplay awards stay **event-only**; operator/manual adjustments go through the audited seam | audit what operators do, not what gameplay does — XP award is the hottest write path in the bot |
| ⚑ R-7 | O-3 (workflow engine): **one generic K7 engine**, built at S8 in sequence (urgency correctly de-borrowed by Gate V R-2) | three domain engines would each re-solve preview/apply/audit/idempotency |
| ⚑ R-8 | O-4 (EventBus durability): per-event `DeliveryClass` as spec-05 already encodes — durable outbox for audit-twin + money-adjacent + cross-boundary; in-process advisory default | matches the frozen grammar; blanket durability taxes every event for three consumers' needs |
| ⚑ R-9 | O-5 (inventory migration): BIGINT `user_id` cast + `guild_id=0` legacy bucket folded at the CUT-2 importer | the dry-run reconciliation surfaces the delta; the reverse-import valve keeps it reversible |
| R-10 | O-7 (advisory→hard): **no change in this repo** (owner-gated executable config); the new repo's equivalents are born required per the CI design | respects Q-0106; the new repo needs no graduation path — it starts hard |
| R-11 | Brief corrections recorded, not adopted (Q-0120): health/hermes-bugreport "no landing" claims were stale; `substrate-kit/tests` path is wrong everywhere (real home `tests/unit/substrate_kit/`); kit test base is now 432 | source wins over the brief |

**⚑ Self-initiated beyond the brief's letter:** the RPS free-tournament fix (same class, found
during verification); the `rearm_settlement()` mixin seam; the A-8/A-11 landings; the D-17
correction; the owner-briefing amendment banner.

## What the owner may want to veto (the compact list)

R-1…R-9 above (each reversible; R-1–R-3 already live and trivially revertable), plus §11 A-9's
wizard fork. Silence = consent (Q-0241). Nothing in this review waits.
