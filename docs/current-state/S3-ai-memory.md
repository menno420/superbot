# S3 — AI-Memory system (the mechanism) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S3 · Map:
> [`../repo-sector-map.md`](../repo-sector-map.md).
>
> *The self-improving-agent engine — checkers, hooks, router, context tooling. Shippable on its
> own; distinct from S4 (the docs content it produces) and S5 (its operation).*

**Recently shipped (this sector):**
- **PROGRAM SESSION 2 RAN — the kit-lab founding plan SHIPPED (PR #1804, 2026-07-07 — Fable 5 ultracode).**
  [`kit-lab-founding-plan-2026-07-07.md`](../planning/kit-lab-founding-plan-2026-07-07.md) — the
  executable founding plan for the extracted kit repo + self-improvement lab: multi-consumer
  release discipline (semver v1.0.0 + pinned `bootstrap.py` asset + `release.json` + the new
  `upgrade` verb w/ 3-way planted-doc diff + rollback), the four benchmark families to runnable
  depth (B1 cold-start A/B routine post-auto-draft · B2 Q-0248 model-allocation dataset on the
  console's declared contract · B3 guard-fire/FP telemetry · B4 ideas-that-ship-and-survive),
  the ONE daily lab loop (9-part prompt skeleton, enumerated destructive tier, warm-session
  never-grades rule), work-surface order (console → Railway → 👤 bot token), the `docs/program/`
  PL-register governance home (cite-never-copy), the `friction`-issue protocol, and 6 build
  bands KL-1…KL-6 (12–14 PRs). 24 decisions ⚑ (D-1…D-24) + 11 gate flags (KF-1…KF-11) + 13
  provisioning rows (P1…P13); zero new router Q-blocks needed. A 4-lens adversarial review
  fleet's 26 confirmed findings were folded before close (§13 lists the load-bearing ones).
  The plan travels to the kit repo at extraction (kickoff = session 4).
- **OWNER-RULINGS + KICKOFF-READINESS ROUND (PRs #1792–#1795, 2026-07-07, same conversation as #1791).**
  Live owner rulings recorded with landings: **Q-0243** pricing-by-simulation · **Q-0244** slash
  verification inherits prefix (never a blocker) · **Q-0245** the second account as declared
  elevated test actor (`EXTRA_OWNER_USER_IDS` **shipped on the live bot**, both owner seams, 8
  test pins) · **Q-0246** permission-tiered operation Full/Lite (A-22 + rider R-18) · **Q-0247**
  multi-repo sequencing ratified · **Q-0248** empirical model-for-task allocation · **Q-0249**
  budget observe-first (~2-month telemetry window). Program vision captured strengthened
  ([multi-repo: kit lab + trading](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md));
  **kickoff brief READY** ([steps 6–8](../planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md));
  **the Projects-coordinator route is READY too (2026-07-07 evening)** — the "SuperBot" Project
  exists (both repos in scope; `superbot-next` owner-created, empty, *deliberately public* until
  the flagged flip), and the full handoff protocol (Custom Instructions → **owner→coordinator
  calibration exchange** → kickoff message) is
  [`projects-eap-coordinator-kickoff-2026-07-07.md`](../planning/projects-eap-coordinator-kickoff-2026-07-07.md).
  The **three/four program sessions are prepared** (PR #1798) — the
  [launch index](../planning/program-three-sessions-launch-index-2026-07-07.md) plus the paste-ready
  founding briefs: [program websites (Fable, session 1)](../planning/website-design-fable-brief-2026-07-07.md) ·
  [kit-lab founding (session 2)](../planning/kit-lab-repo-founding-brief-2026-07-07.md) ·
  [trading-repo founding (session 3)](../planning/trading-repo-founding-brief-2026-07-07.md).
- **IDEA-CONSOLIDATION PASS — today's four owner captures folded + the plan re-verified (PR #1791, 2026-07-07 — Fable 5 ultracode, 9-lane fan-out).**
  Canonical-plan **§11b amendments A-12…A-20** + registry mints **R-16/R-17/P-5**
  ([report](../planning/rebuild-idea-consolidation-report-2026-07-07.md)): the **role-scoped
  authority lane** (`Lane.ROLE_SET` + channel-access role-sets, allow *and* deny-until-role —
  landed before K6 is built, A-12); the **user-self-service automation scheduler** on K9's
  due-queue (category B structurally reserved but compile-fenced OFF pending its own pricing
  session; fire-time creator-ActorRef, quiet-hours + condition-poll carriers, A-13);
  moderation **decide-at-port anchors** (A-14) + **privacy export / guild-config restore** (A-15);
  and the §3.C re-verify hardened four norms into machinery — the **parity-depth floor** at the
  `pending→ported` flip (A-16), the **deterministic knowledge-eval gate** for band 7 (A-17), the
  **human verified_live lane budgeted** (~150–250 units, per-band batches, CUT-3 debt list, A-18),
  and the **escape-hatch ratchet wired permanent** (it had no landing step anywhere, A-19);
  N=7d affirmed with a targeted post-window checklist (A-20). 16 decisions logged ⚑ (IC-1…IC-16).
- **THE REBUILD FINAL REVIEW RAN (PR #1778 + fix PRs #1781/#1782, 2026-07-07 — Fable 5 ultracode, the brief's A–H mandate).**
  Verdict: **the plan is ready — the new repo can start now; zero blocking work ahead of §5 step 6**
  ([the A–H report](../planning/rebuild-final-review-report-2026-07-07.md); readiness scored per
  step, biggest risk = layer V is the least-built part now that Q-0241 retired the human gates).
  Shipped with it: the **Phase-2.5 G2 close-out** (the adopt-renders-what-it-knows kit fix —
  derived provisional slots + UNRENDERED banner + vendored bootstrap.py, 432 kit tests — plus the
  T2/T4 **re-run pair**, results in the G2 report's addendum); **canonical-plan §11 amendments
  A-1…A-11** (schema-growth ledger → K2, nav-completeness golden → K8, sim-runner harness/oracle
  decomposition + `check_sim_gate` contract pointer → step 11, K7 audit-fence AST complement,
  off-Discord surface + release-loop + background-obligation landings, setup-wizard hardening incl.
  the G-19 freeze/widen + the draft-lane fork decision, D-17 role_menu correction); **20 stale
  owner-gate prose sites fixed** across 6 live docs; companion C's interaction-token constraint
  **validated against official Discord docs + frozen**; the **[Projects-EAP product
  review](../planning/projects-eap-product-review-2026-07-07.md)** (owner-sendable); and the
  **§6.3 live-bot fixes** #1781/#1782 (see the hub ledger). O-1…O-7 recommendations decided-and-flagged
  in the report's decisions log.
- **OWNER GATES RETIRED + Phase-2.5 RAN + Projects-EAP as coordinator (PRs #1775/#1776, 2026-07-07).**
  **Q-0241 (#1776)** retired the rebuild's owner gates — the coordinator builds in logical order,
  **live-tests each piece in a server**, and **never waits (silence = consent = done)**; the destructive
  tier stays reversible (shadow-first, N=7d rollback, reverse-import valve), not gated. **Phase-2.5
  cold-start A/B RAN (#1775)** with 8 paired sessions + Opus judge → **verdict FAIL as-tested** (adopt
  ships the kit inert with unrendered `${...}` templates; 0/3 measures beaten) → remainder = the
  adopt-render fix + one re-run pair (`planning/phase-2.5-cold-start-report-2026-07-07.md`). Kit tail ①
  (#1775) + `tools/check_amendments.py` (#1775) also shipped. **Plan of record =**
  [`rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md). New idea:
  [Claude Code Projects (EAP) as the rebuild coordinator](../ideas/claude-code-projects-for-the-rebuild-2026-07-07.md).
- **GATE V — verification-fleet pass COMPLETE → Phase-B under Sequence C (PRs #1750/#1751/#1756/#1757/#1759/#1767, 2026-07-06).**
  All arms A–D + the Codex evidence layer + the final **synthesis (Arm Σ, #1767,
  [`GATE-V-SYNTHESIS.md`](../analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md))** are done: verdict
  **Gate V COMPLETE → proceed to Phase-B per-step planning under Sequence C** (frozen L3→L4/L5 games edge
  fabricated → games defer; audited-write atomicity a systemic contract-freeze, not a live defect; K7
  urgency borrowed). *(Readiness note: the two owner gates named here were RETIRED by Q-0241 (#1776) —
  see the top entry; Phase-2.5 has since RUN, #1775.)* The Arm D live-testing detail:
- **GATE V Arm D — empirical live-testing evidence pack (PR #1751, 2026-07-06).** Executed
  [`rebuild-gate-v-verification-fleet-2026-07-06.md`](../planning/rebuild-gate-v-verification-fleet-2026-07-06.md)
  §7 against the sandbox's dedicated test bot/guild + local throwaway Postgres (never
  production/Railway):
  [`LIVE-VERIFIED-EVIDENCE-PACK.md`](../planning/LIVE-VERIFIED-EVIDENCE-PACK.md) — real economy/XP/
  inventory/settings goldens; the PvP wager escrow/settle engine (`game_wager_workflow`) proved
  idempotent under a real concurrent race (refutes the plan's blanket "wager double-pay" framing for
  that primitive); a **genuine open gap confirmed**: the human deathmatch duel (`_DuelView`,
  `disbot/cogs/deathmatch_cog.py`) lacks the `SettleOnceMixin` guard its sibling PvP views have, and a
  real concurrent double-write was reproduced empirically; restart-persistence (`proof_channel_locks`)
  survived a real bot kill+restart; the games-deferral exercisability table shows every primitive
  tested — including the wager engine, today only called from game views — is exercisable **without**
  invoking a game via a direct service-layer harness. Arms A (Sonnet)/B (Codex)/C (Agent Mode) of the
  same fleet + the Σ synthesis are now all complete (see the Gate-V-COMPLETE entry above).
- **Stage-2 subsystem walk: L1a + L1b fully decided (PR #1725, 2026-07-05 — owner-led, live)** —
  the canonical walk artifact
  [`rebuild-stage2-subsystem-walk-2026-07-05.md`](../planning/rebuild-stage2-subsystem-walk-2026-07-05.md)
  (52-row progress index) now carries **19 decided rows**: all of L1a (settings, diagnostic, help)
  and all of L1b, the operator spine (admin, server_management, setup [split into new row 5a],
  moderation, logging, automod, security, cleanup, counters, channel, role, ticket,
  image_moderation, proof_channel) — 2 `keep`, 1 `redesign`, 16 `improve`. Found **7 current-bot
  bugs, owner-decided "fix now"** (exact file:line specs in the walk doc §7.1 — not implemented
  this session, docs/planning-only) and a **committed "implement now" scope list spanning 6 rows**
  (§7.2). Resolved 2 long-standing cross-cutting decisions as a side effect: G-22 staging-lanes
  standardization and the auto-mod-tier operator-surface consolidation. Also: the owner redirected
  `hermes_cog`'s dropped bug-report intent onto the future "boards family" row (an AI-assisted
  "tell us what to improve" surface) rather than dropping the idea outright. **Next session (owner
  plan): an Opus session that fixes the §7.1 bugs directly in the current bot and starts
  implementing some of §7.2's committed scope** — a deliberate detour from the walk to structure
  the *current* bot before the walk itself continues at **L1c** (34+ rows remain).
- **THE MEMORY SUBSTRATE IS FINALIZED (#1649, 2026-07-02 — the handoff §5.B Fable-5 ultracode
  session; the K0 gate deliverable).** The substrate-kit's full nervous system shipped on the
  declaration layer: mode *behaviors* (observe/guided/active now change quota / orientation /
  mandates / actuator gating / graduation), trigger→mandatory-question sessions, the R-NNNN
  reflection buffer + miner + episodic index, the §6 maintenance loop (compaction State Delta ·
  blocking-question escalation · promotion downgrade), the anti-anchor review seam (provisioned,
  not hard-wired), the **context-economy engine** (class taxonomy · gauges incl. the ≤7,000-word
  orientation budget · triple-filter harvest-gated deletion · tombstone shards · the generalized
  retention simulator — retention plan §10 + Q-0214), the [D-NNNN] decisions ledger + stamp
  discipline, portable namespace/seam-authority/orientation-budget checkers, 4 Claude-Code hooks
  (staged, never live-written), the complete 16-template set, and the **one-step adopt flow**
  (`bootstrap adopt` on a bare dir + the stdlib-only single-file `dist/bootstrap.py`;
  `render --live`; AgentContextPack generator, index-or-manifest). 117→407 kit tests; proven
  end-to-end in a scratch repo. **Remaining owner-gated:** the Phase-2.5 cold-start A/B (still
  gates Phase 3) + the extract-to-standalone-repo step.
- **Reconcile-marker band-consistency guard** (`scripts/check_reconcile_marker.py`, warn-first,
  dispatch run 2026-06-27) — asserts the `Last reconciliation pass` marker in `current-state.md` is
  internally consistent (leading `PR #N` == the stated reset target · `band-#M` == `(N // 30) * 30` ·
  the linked pass-record doc exists); caught + fixed the live band-#1470 drift (marker read `#1472`,
  the pass's own PR, vs the reset target `#1470`). Idea `reconcile-trigger-band-consistency-guard`.
- **`check_ledger_hygiene` de-staled for the Q-0195 per-claim-file layout** (dispatch run 2026-06-27) —
  the retired shared `active-work.md` claim ledger left the linter's Active-claims scan no-op'ing
  against a pointer stub; repointed to scan `docs/owner/claims/*.md` and flag a `claude/<branch>`
  claimed by >1 file.
- **Settle-once money-safety guard** (`check_consistency` **Rule 6**, warn-first, #1454) — pins the
  settle-once terminal pattern on game-state views (#1444) + blackjack PvP (#1445, shared mixin
  relocated to `utils/`) so a money-paying game can't double-settle without tripping a checker.
- **Cross-domain routing-disjointness guard** (#1470) — a registry-driven harness pinning the AI
  task-router invariant *"BTD6 keywords never collide with the distinctive Limbus tokens"* (routing ·
  token disjointness across every domain pair · priority total-order), so adding the next knowledge
  domain is a one-line registration.
- **Per-claim / per-sector coordination-file restructure** (Q-0195) — `active-work.md` →
  one-file-per-claim (`scripts/check_lane_overlap.py` reads the directory; `check_stale_claims.py`
  GC) + `current-state.md` → per-sector files. Justified by `tools/sim/claim_layout_sim.py`.
- **Lane-overlap claim-scan** (#1223) and the **repo-consistency-linter** (back-button /
  edit-in-place rules, #1189) mechanisms; the linter's **`edit_in_place` rule graduated
  warn→error** (#1375) once the `views/ai/` in-place-nav migration cleared its last findings
  ([plan, now historical](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)).

**▶ Next startable:**
*(offline-fit tags — `[offline]` self-mergeable now · `[needs-live-bot]` needs a running bot / runtime
creds · `[owner]` needs an owner decision/action; see [`../repo-sector-map.md`](../repo-sector-map.md)
§ "the offline-fit startability tag".)*

- **📍 READ FIRST — THE CANONICAL REBUILD PLAN (2026-07-06, PR #1770):**
  [`../planning/rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md)
  — the single source of truth consolidating the whole rebuild corpus: corrected layer taxonomy
  (AI = K10 · automation = K5+K9+K7 spread · verification = layer V), one phase arc, the gate
  census (G1/G2 **retired as blockers by Q-0241/#1776** — kept as sequencing + rationale), and the
  17-step start sequence. **Steps 1–3 executed (PR #1775, 2026-07-07):** kit tail ① shipped (427
  kit tests) · **Phase-2.5 RUN — verdict FAIL as-tested** (`adopt` deploys unrendered templates:
  orientation cost in 3/4 pairs, no measured benefit —
  [the G2 report](../planning/phase-2.5-cold-start-report-2026-07-07.md)) ·
  `tools/check_amendments.py` built + CI-wired. **The G2 remainder executed 2026-07-07 (this
  band): the adopt-renders-what-it-knows kit fix + the A/B re-run pair** — see the
  [final-review report](../planning/rebuild-final-review-report-2026-07-07.md). The §1 flag list
  stays the owner's *veto surface* (react anytime), not a sitting. Companions:
  [test-guild (C)](../planning/rebuild-test-guild-design-2026-07-06.md) · [Phase-2.5 procedure
  (D)](../planning/rebuild-phase-2.5-procedure-2026-07-06.md).
- `[owner]` **▶ THE REBUILD REVIEW-THEN-PLAN PHASE IS LIVE** (owner-directed 2026-07-03): the pre-build
  **new-bot capability audit** is complete (#1662…#1668/#1674, verdict **GO-with-amendments**, measured
  all-43 fit **85.1%**) and
  [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  is the **frozen reference**; the owner-live **Phase-A** then began — a **Stage-1 global review**
  ([decisions log](../planning/rebuild-stage1-global-review-2026-07-03.md), #1679, Q-0219…Q-0223) and a
  **conventions freeze** (naming · four-rung invocation ladder · mod-actions-as-data · authority +
  bot-owner override; [decisions log](../planning/rebuild-conventions-invocation-authority-2026-07-03.md),
  #1680, Q-0224…Q-0228). **Stage 2 — the per-subsystem walk is underway** (process now canonical in
  [`planning/rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md) §3;
  progress + full handoff:
  [`planning/rebuild-stage2-subsystem-walk-2026-07-05.md`](../planning/rebuild-stage2-subsystem-walk-2026-07-05.md)
  §7) — **L1a + L1b decided (19 rows, PR #1725, 2026-07-05)**; 34+ rows remain. `[owner]` **▶ next:
  a bug-fix + initial-implementation session against the *current* bot** (walk doc §7.1/§7.2), then
  the walk continues at **L1c**. *(Historical: this lane's "behind the Phase-3 owner gate" framing
  was retired by Q-0241/#1776 — the rebuild is un-gated; the walk paces port bands, not the repo
  start.)*
- ~~**🔒 THE REBUILD OWNER GATE**~~ — **RETIRED by Q-0241/#1776 (2026-07-07).** The Phase-2 design
  spec is DONE (2026-07-02): [`rebuild-design-spec-2026-07-02.md`](../planning/rebuild-design-spec-2026-07-02.md)
  (Fable-5 judge panel + Opus/GPT adversarial review), backed by
  [`rebuild-linchpin-validation-2026-07-02.md`](../planning/rebuild-linchpin-validation-2026-07-02.md)
  (#1639) — both previously-unproven linchpins built + measured (golden harness `parity/` +
  grammar spike, verdict **GO with amendments**). Its §10.2 ratification list is now the
  **decide-and-flag F-2/F-3 veto payload** in the canonical plan §1 — the owner reacts to it
  anytime; it no longer blocks new-repo code (silence = consent). Telemetry-sidecar capture
  (P0.5 sibling) stays open — runs before any old-repo freeze (canonical §5 step 14).
- ~~**▶ FINALIZE THE MEMORY SUBSTRATE**~~ — **✅ DONE #1649 (2026-07-02**, the
  [handoff §5.B](../planning/rebuild-ultracode-handoff-2026-07-02.md) Fable-5 ultracode session —
  see Recently shipped above). What remains of this lane: ~~the Phase 2.5 cold-start A/B~~ —
  **RUN #1775 (FAIL as-tested), then the adopt-render fix + re-run pair executed 2026-07-07**;
  it no longer gates anything (Q-0241 retired the gates, and the go/no-go sitting with them);
  `[owner]` the *extract to a standalone repo* step (owner-paced, not blocking). The old
  "PR 2 remainder + PR 3" framing of
  [the extraction plan](../planning/portable-substrate-kit-extraction-2026-06-13.md) is fully
  subsumed and shipped.
- `[offline]` **procedures→skills Batch 2**
  ([plan](../planning/procedures-to-skills-conversion-plan-2026-06-17.md)).
- `[offline]` The **bot self-test walker** eval harness (pairs with S1 P1-1) — the harness scaffold is
  offline-buildable; `[owner]` the **Hermes bug-triage** write side stays gated on the VPS write scope
  (Q-0121).

**Note:** S3 runtime depth is self-initiated mechanism work; the old `needs-hermes-review` review gate
is **retired** (Q-0197) — every PR now auto-merges on green CI. A fresh idea may be promoted
idea→plan→build at any time (Q-0172) — flag self-initiated promotions on the session-log
`⚑ Self-initiated:` line.
