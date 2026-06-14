# Production-readiness hardening roadmap — 2026-06-12

> **Status:** `plan` — consolidated, prioritized hardening queue derived from the seven
> per-subsystem [production-readiness maps](README.md). **Not implementation approval.**
> Source code and merged PRs win; each item links to the map that is its evidence. Every
> subsystem is currently rated **Partial / not-yet-production-ready** — this doc turns that
> into a ranked, bounded backlog.

## How this is prioritized

By **production risk**, not effort:

- **P0 — integrity** — could cause real harm if shipped: money loss/duplication, privacy
  exposure, authority/audit inconsistency. Fix before a public posture.
- **P1 — correctness & operations** — wrong answers, unobservable failures, no live proof,
  no regression guards. Needed for confidence, not catastrophic.
- **P2 — drift & quick wins** — stale docs / mislabels that misroute operators and agents.
  Cheap, safe, do anytime (some are one-line fixes).

Each track is a **bounded session** that maps back to a single map's "Recommended next
session". Tracks needing an owner decision name the routed Q-block.

## Verdict at a glance

| Subsystem | Verdict | Principal blocker | Map |
|---|---|---|---|
| Games | Partial | Wager settlement not atomic — can mint coins / lose entry fees | [games](games-production-readiness-map-2026-06-12.md) |
| Media / YouTube | **Not ready** | Cache never purged + raw metadata stored indefinitely (privacy) | [media](media-youtube-production-readiness-map-2026-06-12.md) |
| Settings / bindings / provisioning | Partial | Dual-lane pointers bypass binding validation; delegated-setup authority mismatch | [settings](settings-bindings-provisioning-production-readiness-map-2026-06-12.md) |
| Server management | Partial | ~~Mixed channel-mutation ownership~~ → **converged (P0-4 complete)**; remaining gap = live verification only | [server-mgmt](server-management-production-readiness-map-2026-06-12.md) |
| AI / Setup Advisor | Partial | Live-eval defect rate; no versioned eval/smoke matrix | [ai](ai-production-readiness-map-2026-06-12.md) |
| BTD6 | Partial (gated) | Model-faithfulness + absence-claim safety; manual blob seeding | [btd6](btd6-production-readiness-map-2026-06-12.md) |
| Health / diagnostics | Partial (improving) | ~~Findings have no lifecycle transition~~ → **transitions + scheduled retention shipped (P1-2)**; remaining gap = owner live walk | [health](health-diagnostics-production-readiness-map-2026-06-12.md) |

---

## P0 — integrity (do before any public posture)

### P0-1 · Games wager money-safety  ·  ✅ **SHIPPED (PR #748, 2026-06-12)**
**Done:** `services/game_wager_workflow.py` (D1 escrow-at-accept; atomic + idempotent settle/
refund/payout; `enter_tournament` debit+row in one txn), all four call sites migrated, AST
fence `test_game_wager_write_boundary`, failure-injection / terminal-matrix / idempotency
tests. Record: [games-wager-money-safety-plan](../games-wager-money-safety-plan-2026-06-12.md).

**Evidence (original):** [games map](games-production-readiness-map-2026-06-12.md) — RPS/blackjack PvP
settle with sequential winner-credit + overdraft loser-debit (a crash between calls **mints
coins**); paid tournament registration **debits before** writing a recovery checkpoint (a
crash loses the fee with no row to refund — contra ADR-002); multi-call payouts/refunds have
no durable idempotency key.
**Why P0:** real currency can be created or lost. No owner gate; fully test-injectable.
**Bounded session:** design one economy-service-backed wager workflow (atomic-or-idempotent
debit→checkpoint→settle), add failure-injection tests at each boundary, characterize
terminal-state behavior. → games map "Recommended next session".

### P0-2 · Media/YouTube data-minimization & retention  ·  needs **Q-0099**
**Evidence:** [media map](media-youtube-production-readiness-map-2026-06-12.md) —
`purge_expired_video_cache()` has **no caller** (expired transcripts/metadata kept forever);
`metadata_json` stores the **full unsanitized** YouTube payload (descriptions etc.), contra
the folio's "bounded cached metadata".
**Why P0:** privacy/data-minimization exposure for a public bot; the feature is also
mis-owned (`YOUTUBE_CONTEXT_ENABLED` labeled `ai` despite ADR-007 shared-platform ownership).
**Bounded session:** ratify the retention/data-minimization contract (Q-0099), store only a
bounded projection, wire purge through a managed-task owner, fix the flag ownership, add
content-free media diagnostics.

### P0-3 · Settings pointer-lane convergence + setup authority  ·  🟡 **FOUNDATION SHIPPED (2026-06-13)** · Q-0098 answered
**Foundation slice (arc PR 1):** [pointer-lane convergence + Setup-delegate authority plan](../settings-pointer-lane-convergence-plan-2026-06-13.md)
— `scripts/settings_lane_matrix.py` (the rec-#1 matrix), the broken `governance.trusted_role`
backfill **reframed** into `DEFERRED_KEYS` (Required #2 fixed; no permanent `BLOCKED_NO_SCHEMA`),
and **two parity invariants** (`test_backfill_target_declaration_parity` +
`test_pointer_lane_ledger` — the latter is the ratchet that blocks new pointer-as-scalar
additions like the welcome/counters #775 ones). **Still sequenced (arc PRs 2–3):** retiring the
XP-announce/economy-log scalars + the delegated-apply `setup_delegate` authority route (designed
in the plan §4, Q-0098). Family-3 governance role-pointer home is gated on router **Q-0119**.

**Evidence:** [settings map](settings-bindings-provisioning-production-readiness-map-2026-06-12.md)
— legacy Discord pointers remain editable scalar settings while canonical bindings exist
(two operator-visible truths; generic editors bypass binding validation); the delegated-Setup
apply gate disagrees with the mutation-pipeline admin floor (a delegate passes Final Review
then fails per-op writes); `binding_backfill.MIGRATED_KEYS` references an **undeclared**
`governance.trusted_role`.
**Why P0:** authority/lane integrity — silent divergence between what an operator is told and
what actually writes.
**Bounded session:** plan pointer-lane convergence (migration order for the four pointer
families) + decide the delegated-Setup apply contract (Q-0098) + add the parity invariants
(P1-3). → settings map "Recommended next session".

### P0-4 · Server-management channel-ownership convergence  ·  ✅ **SHIPPED (PR 1 #820 + PR 2, 2026-06-14)** · Q-0100 answered
**Done:** every operator channel mutation routes through the audited
`ChannelLifecycleService`. **PR 1 (#820):** `set_overwrite` + `clone` ops, all
`.set_permissions()`/`.clone()` call sites routed off, invariant pins both. **PR 2:** ad-hoc
operator creation (`!create`/`!evt`/`!bulkcreate` + the create panel) + category lifecycle via
`ChannelLifecycleService.create_channels` (audit + `channel.lifecycle_changed` event + typed
per-name result); `test_no_direct_channel_mutations.py` now pins `create_text_channel`/
`create_voice_channel`/category creation, and `test_no_silent_auto_create.py` lists the service
as the one sanctioned manual `guild.create_*` caller.
**Design decision (Q-0100):** ad-hoc creation has *no* declared binding, so it does NOT fit the
catalogue-driven `ResourceProvisioningPipeline`; it is owned by `ChannelLifecycleService`
(the channel sibling of the audited `RoleLifecycleService`). Subsystem-*bound* creation stays
with the provisioning pipeline.

**Evidence (original):** [server-mgmt map](server-management-production-readiness-map-2026-06-12.md) —
channel creation, clone, permission-overwrite, and category lifecycle paths sat **outside**
the one audited lifecycle/provisioning seam; the same operator action got different audit,
confirmation, and failure behavior depending on path. The channel invariant only pinned
`.edit()`/`.delete()`, giving a false sense of completeness.

---

## P1 — correctness & operations

### P1-1 · AI answer correctness + a versioned eval/smoke harness
**Evidence:** [ai map](ai-production-readiness-map-2026-06-12.md) (ongoing live-eval defect
rate; PRs #703/#706/#707/#709 each fixed live-found routing/grounding/workflow bugs) +
[btd6 map](btd6-production-readiness-map-2026-06-12.md) (PMFC/POD entity substitution,
long-list omission/miscount, absence-claim guard **unimplemented**).
**Bounded session:** build a short **versioned eval/smoke matrix** (gates · fallback · tool
use · BTD6 prompts · grounding refusal · audit) run with production-like credentials, and
implement the BTD6 absence-claim guard. *(BTD6 broad expansion stays gated regardless.)*

### P1-2 · Health findings lifecycle + retention + diagnostics drift  ·  ✅ **SHIPPED (2026-06-14)** · Q-0097 answered
**Done:** the operator-managed lifecycle (Q-0097) shipped through the sole writer:
`health_findings_service.set_status` (DB primitive `set_finding_status`, pinned by the
sole-writer AST guard) transitions `open`↔`resolved`/`ignored` and emits
`audit.action_recorded`; `!platform finding resolve/ignore/reopen <fingerprint>` is the
admin command. Retention is now operational on long-lived replicas — `run_retention()` runs
at startup **and** on the daily `HealthMaintenanceCog._retention_loop` (mirrors
`MediaMaintenanceCog`). The Platform-hub typed-only exclusion of `startup`/`findings`/`finding`
is now pinned by a test; smoke `!platform diagnostics` drift was already fixed in the P2 sweep
(#764). **Remaining = the owner-led live walk only.**

**Evidence (original):** [health map](health-diagnostics-production-readiness-map-2026-06-12.md) —
findings are filterable as `resolved`/`ignored` but **nothing transitions them** (open
forever); retention is startup-only on a long-lived process.

### P1-3 · Machine-checkable contract invariants (cross-cutting)
**Evidence:** recurs in settings (declared-setting → runtime-consumer parity; no dual
pointer+binding; backfill-target parity), games (cross-game terminal-state matrix), AI
(declared-vs-consumed tools), BTD6 (derived-value provenance).
**Why:** every map verified its contracts **manually** — without an invariant, the next
regression ships silently.
**Bounded session(s):** add AST/registry parity tests, ideally one per track as it lands
(not a single mega-session). This is the durable "stays fixed" layer.

### P1-4 · Production live-verification (the #1 cross-cutting blocker, owner-led)
**Evidence:** **all seven** maps explicitly lack maintainer live-walk + real
Postgres/Discord end-to-end proof despite strong unit coverage.
**Bounded action:** extend the existing
[production-eval checklist](../../audits/production-eval-checklist-2026-06-10.md) to cover the
newer surfaces each map flagged (health findings/startup · media fetch/cache/purge · games
terminal-states & refunds · settings three-lane smoke · server-mgmt channel paths), then run
it. Owner-dependent — pairs with the commissioned
[untested-surface checklist](../../audits/untested-surface-checklist.md).

---

## P2 — drift & quick wins (cheap, no owner gate) — ✅ **SWEPT 2026-06-12 (night)**

All five cleared in one docs-sweep session (band queue slot 2), each verified
against source before editing:

| Fix | Evidence | Done |
|---|---|---|
| Health smoke checklist: replace nonexistent `!platform diagnostics` with real `!platform runtime`/`consistency`; correct the Platform-hub completeness claim | health map | ✅ checklist route + `platform_panel.py` docstring (grouped ≠ every subcommand) |
| AI `core/runtime/ai/README.md`: drop stale "inert scaffold" wording for active code | ai map | ✅ rewritten for the live gateway/routing/NL-stage package |
| ADR-006: reconcile stale BTD6 pause wording + decode-status summary rows | btd6 map | ✅ dated status addendum (decision text untouched per ADR immutability) + decode-status header v55.0→v55.1 + duplicate backlog №3 renumbered |
| Media folio: "bounded cached metadata" vs. the raw-payload reality (fix doc or code per Q-0099) | media map | ✅ folio states the raw-payload reality; bounded projection = the Q-0099/P0-2 target (queue slot 9) |
| `YOUTUBE_CONTEXT_ENABLED` ownership label `ai` → shared platform (ADR-007) | ai + media maps | ✅ `owner="platform"` with ADR-007 comment |

---

## Owner decisions gating the roadmap

| Q | Decision | Gates | Status |
|---|---|---|---|
| Q-0077 | BTD6 auto-seed-on-boot | BTD6 data-lane proof | pre-existing |
| Q-0097 | Health finding lifecycle (open/resolved/ignored) | P1-2 | ✅ **ANSWERED 2026-06-12 — (a) operator-managed** via the sole writer → **P1-2 SHIPPED 2026-06-14** |
| Q-0098 | Delegated-Setup apply authority contract | P0-3 | ✅ **ANSWERED 2026-06-12 — (a) delegates may apply** → P0-3 unblocked |
| Q-0099 | Media/YouTube retention & data-minimization policy | P0-2 | ✅ **ANSWERED 2026-06-12 — (a) bounded projection + scheduled purge** → P0-2 unblocked |
| Q-0100 | Canonical owner for direct channel mutations | P0-4 | ✅ **ANSWERED 2026-06-12 — (a) converge under existing seams** → P0-4 unblocked |

**Net effect (updated 2026-06-12 evening):** **every gating owner decision is answered** —
P0-2/P0-3/P0-4 (Q-0098–Q-0100) and now P1-2 (Q-0097 = operator-managed). No hardening track
waits on a decision; sequencing lives in the
[reconciliation-pass decade queue](../reconciliation-pass-2026-06-12.md). **P0-1 is
owner-picked as the next implementation session — design pinned:**
[games-wager-money-safety-plan](../games-wager-money-safety-plan-2026-06-12.md).

## Recommended first three sessions

1. **P2 doc-drift sweep** — cheapest, no gate; immediately stops operators/agents acting on
   wrong commands and stale ownership. One session.
2. **P0-1 games wager money-safety** — highest concrete harm (mints/loses currency),
   self-contained, no owner gate, test-injectable.
3. **P0-3 / P0-4** — ✅ **both SHIPPED.** P0-3 (settings pointer-lane + delegated-apply,
   #777/#794/#817) and P0-4 (channel-ownership convergence, #820 + PR 2, 2026-06-14) are
   complete. **Next implementation track = P0-2 media retention (Q-0099), then P1-1 eval
   matrix.**

> As a track lands, update the relevant map's rows from Partial/Not Done → Done with the PR
> as evidence, and tick the verdict table above.
