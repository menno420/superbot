# S3 — AI-Memory system (the mechanism) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S3 · Map:
> [`../repo-sector-map.md`](../repo-sector-map.md).
>
> *The self-improving-agent engine — checkers, hooks, router, context tooling. Shippable on its
> own; distinct from S4 (the docs content it produces) and S5 (its operation).*

**Recently shipped (this sector):**
- **GATE V Arm D — empirical live-testing evidence pack (this PR, 2026-07-06).** Executed
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
  same fleet + the Σ synthesis still need to run.
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
  (AI = K10 · automation = K5+K9+K7 spread · verification = layer V), one phase arc, the canonical
  gates (**G1** owner go/no-go sitting reading its §1 flag list · **G2** Phase-2.5 A/B), and the
  17-step start sequence. ▶ next startable per its §5: **step 1 kit tail ①** (Q-0223 re-entrant
  txn fix, small PR) → **step 2 run Phase-2.5** per
  [companion D](../planning/rebuild-phase-2.5-procedure-2026-07-06.md) → **step 3
  `tools/check_amendments.py`**. Companions: [test-guild design
  (C)](../planning/rebuild-test-guild-design-2026-07-06.md) · Phase-2.5 procedure (D). *(Supersedes
  the 07-05 next-session-priority assessment — same recommendation, now sequenced.)*
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
  the walk continues at **L1c**. Still behind the Phase-3 owner gate below (no new-repo code until
  design-spec ratification).
- `[owner]` **🔒 THE REBUILD OWNER GATE — the Phase-2 design spec is DONE and the evidence package
  is IN** (2026-07-02): [`rebuild-design-spec-2026-07-02.md`](../planning/rebuild-design-spec-2026-07-02.md)
  (Fable-5 judge panel + Opus/GPT adversarial review), now backed by
  [`rebuild-linchpin-validation-2026-07-02.md`](../planning/rebuild-linchpin-validation-2026-07-02.md)
  (#1639) — **both previously-unproven linchpins built + measured**: the Phase-0.5 golden harness
  (`parity/` — replay-deterministic, coverage in `parity/COVERAGE.md`) and the grammar spike
  (tier-1/2 fit 73% as-specced → 85% with six named amendments; verdict **GO with amendments**).
  The owner ratifies the design + the backward-compat contract + the rebuild go/no-go (§10.2 lists
  exactly what approval means); **no Phase-3 new-repo code until then.** `[offline]` remaining
  ungated phases: Phase 0 (substrate-kit adaptive half) · Phase-0.5 telemetry sidecar capture ·
  Phase 1 (harvest) · Phase 2.5 (cold-start proof) — see the
  [strategy §3](../planning/fresh-rebuild-strategy-2026-07-02.md).
- ~~**▶ FINALIZE THE MEMORY SUBSTRATE**~~ — **✅ DONE #1649 (2026-07-02**, the
  [handoff §5.B](../planning/rebuild-ultracode-handoff-2026-07-02.md) Fable-5 ultracode session —
  see Recently shipped above). What remains of this lane: `[offline]` **Phase 2.5 cold-start
  substrate-on/off A/B** (a fresh scratch repo adopted from `dist/bootstrap.py`, agent sessions
  with vs. without the substrate — the owner-flag-2 acceptance tier that still gates Phase 3);
  `[owner]` the *extract to a standalone repo* step + the full rebuild go/no-go. The old
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
