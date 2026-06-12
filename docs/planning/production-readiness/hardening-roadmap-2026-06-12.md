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
| Server management | Partial | Mixed channel-mutation ownership (some audited, some direct) | [server-mgmt](server-management-production-readiness-map-2026-06-12.md) |
| AI / Setup Advisor | Partial | Live-eval defect rate; no versioned eval/smoke matrix | [ai](ai-production-readiness-map-2026-06-12.md) |
| BTD6 | Partial (gated) | Model-faithfulness + absence-claim safety; manual blob seeding | [btd6](btd6-production-readiness-map-2026-06-12.md) |
| Health / diagnostics | Partial | Findings have no lifecycle transition; smoke/hub drift | [health](health-diagnostics-production-readiness-map-2026-06-12.md) |

---

## P0 — integrity (do before any public posture)

### P0-1 · Games wager money-safety
**Evidence:** [games map](games-production-readiness-map-2026-06-12.md) — RPS/blackjack PvP
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

### P0-3 · Settings pointer-lane convergence + setup authority  ·  needs **Q-0098**
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

### P0-4 · Server-management channel-ownership convergence  ·  needs **Q-0100**
**Evidence:** [server-mgmt map](server-management-production-readiness-map-2026-06-12.md) —
channel creation, clone, permission-overwrite, and category lifecycle paths sit **outside**
the one audited lifecycle/provisioning seam; the same operator action gets different audit,
confirmation, and failure behavior depending on path. The channel invariant only pins
`.edit()`/`.delete()`, giving a false sense of completeness.
**Why P0:** audit-trail integrity; uneven confirmation on destructive guild mutations.
**Bounded session:** decide the canonical owner per direct path (Q-0100), then converge under
it + extend the invariant. → server-mgmt map "Recommended next session".

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

### P1-2 · Health findings lifecycle + retention + diagnostics drift  ·  needs **Q-0097**
**Evidence:** [health map](health-diagnostics-production-readiness-map-2026-06-12.md) —
findings are filterable as `resolved`/`ignored` but **nothing transitions them** (open
forever); retention is startup-only on a long-lived process; the smoke checklist points at a
nonexistent `!platform diagnostics`; the Platform-hub "groups every subcommand" claim is false.
**Bounded session:** answer Q-0097, implement the chosen lifecycle through the sole writer
`health_findings_service`, schedule retention via the managed-task owner, fix the smoke/hub
drift (P2-1 overlaps). → health map "Recommended next session".

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

## P2 — drift & quick wins (cheap, no owner gate)

A single **doc-drift sweep** session clears all of these; each is small and removes active
operator/agent misrouting:

| Fix | Evidence |
|---|---|
| Health smoke checklist: replace nonexistent `!platform diagnostics` with real `!platform runtime`/`consistency`; correct the Platform-hub completeness claim | health map |
| AI `core/runtime/ai/README.md`: drop stale "inert scaffold" wording for active code | ai map |
| ADR-006: reconcile stale BTD6 pause wording + decode-status summary rows | btd6 map |
| Media folio: "bounded cached metadata" vs. the raw-payload reality (fix doc or code per Q-0099) | media map |
| `YOUTUBE_CONTEXT_ENABLED` ownership label `ai` → shared platform (ADR-007) | ai + media maps |

---

## Owner decisions gating the roadmap

| Q | Decision | Gates | Status |
|---|---|---|---|
| Q-0077 | BTD6 auto-seed-on-boot | BTD6 data-lane proof | pre-existing |
| Q-0097 | Health finding lifecycle (open/resolved/ignored) | P1-2 | Open (asked 2026-06-12) |
| Q-0098 | Delegated-Setup apply authority contract | P0-3 | ✅ **ANSWERED 2026-06-12 — (a) delegates may apply** → P0-3 unblocked |
| Q-0099 | Media/YouTube retention & data-minimization policy | P0-2 | ✅ **ANSWERED 2026-06-12 — (a) bounded projection + scheduled purge** → P0-2 unblocked |
| Q-0100 | Canonical owner for direct channel mutations | P0-4 | ✅ **ANSWERED 2026-06-12 — (a) converge under existing seams** → P0-4 unblocked |

**Net effect:** P0-2, P0-3, P0-4 are now **unblocked** (each has its decided design above).
Only P1-2 still waits on an owner answer (Q-0097, health finding lifecycle).

## Recommended first three sessions

1. **P2 doc-drift sweep** — cheapest, no gate; immediately stops operators/agents acting on
   wrong commands and stale ownership. One session.
2. **P0-1 games wager money-safety** — highest concrete harm (mints/loses currency),
   self-contained, no owner gate, test-injectable.
3. **P0-3 / P0-4** — now unblocked (Q-0098 / Q-0100 answered): settings pointer-lane +
   delegated-apply route, or server-mgmt channel-ownership convergence under the existing
   seams. Both are now design-decided; sequence by the owner's pick.

> As a track lands, update the relevant map's rows from Partial/Not Done → Done with the PR
> as evidence, and tick the verdict table above.
