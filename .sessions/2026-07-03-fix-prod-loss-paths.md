# 2026-07-03 — Fix two confirmed prod loss paths (from the engine-room audit)

> **Status:** `complete`
> **Branch:** `claude/fix-prod-loss-paths-2026-07-03` · **PR:** #1693
> **Session type:** runtime bug-fix (owner-directed follow-up to the PROMPT-A engine-room
> audit #1690). Owner picked "fix the 2 prod bugs" from the question panel.

## What happened

Both bugs verified against source before scoping, then fixed with regression tests.
Full CI mirror green (14,059 passed) + `check_architecture --mode strict` clean (no new
violations).

**Bug 1 — blackjack tournament entry-fee forfeit on a `VERSION` bump** (`blackjack_cog.py`
`_recover_blackjack_tournament`). The version-mismatch branch did `clear_by_id` + `continue`,
skipping the refund → a schema-version bump forfeited every live tournament's entry fee on the
merge=deploy restart. **Nuance found mid-fix:** this was a *deliberate, tested* tradeoff — an
existing test (`test_..._drops_version_mismatch_without_refund`) asserted the forfeit on purpose,
rationale "the `bet` field may be in a foreign schema, refunding a wrong amount is worse." My
audit mislabeled it a clean bug. **Surfaced to the owner** rather than silently reversing a tested
money decision; owner chose **fix it** (2026-07-03 question panel). **Fix:** refund `state["bet"]`
(guarded by the existing `int>0` check) regardless of version, then clear — the fee is owed
whether or not the rest of the schema still parses; whoever bumps the version owns keeping `bet` =
entry fee. Counter-test rewritten to assert the refund.

**Bug 2 — XP (and every additive on_message effect) double-fires during the LP-4 deploy handoff**
(`core/runtime/message_pipeline.py`). `main()` releases the runtime lock *before* `bot.close()`
drains, so the incoming replica connects while this instance is still draining; Discord delivers
`MESSAGE_CREATE` to both gateway connections during the overlap and `db.add_xp` is additive with no
per-message idempotency → double XP. **Fix (root, whole class):** gate
`message_pipeline.dispatch()` on `lifecycle.is_shutting_down()` — a draining instance runs no
stages, so xp / counting / chain / cleanup / rps / four_twenty / btd6 (all pipeline stages) can't
double-apply during the overlap; the incoming replica owns ongoing traffic. Does **not** regress
LP-4 (the fast lock release stays).

Tests: +2 pipeline tests (draining→no stages; running→stages run), rewrote the blackjack
version-mismatch test to assert the refund. `disbot/core/runtime/message_pipeline.py` gains an
intra-`core` import of `lifecycle` (allowed; the existing `services` import is the tracked one).

## Decisions made alone

- **Bug 2 fix approach:** gate the pipeline `dispatch` chokepoint on draining, rather than adding
  per-message idempotency keys (a schema + dedup table). Rationale: one chokepoint covers the whole
  additive-on_message class, no schema change, and it doesn't regress the LP-4 fast lock release.
  (Bug 1's *direction* was owner-ratified via the panel, not decided alone.)

## Flagged for maintainer (known limits)

- **Bug 2 drain-gate leaves a tiny gap, by design:** messages sent during the ~1–2s handoff overlap
  that the *old* instance received but the *new* instance didn't (not yet gateway-connected) get
  **no** XP/moderation. That's a couple of messages per deploy — vastly better than double-awarding,
  and moderation of persistent violations is unaffected.
- **Bug 2 covers pipeline STAGES only.** All current additive on_message effects are pipeline stages
  (verified against the stage-order table), so they're covered. A *future* additive effect added as
  an independent (non-pipeline) `on_message` listener would need the same `is_shutting_down()` guard —
  worth a checker if that pattern recurs.
- **Bug 1** now refunds on any version mismatch; the residual risk the original code guarded against
  (a future schema repurposing `bet`) is now owned by whoever bumps `BLACKJACK_TOURNAMENT_VERSION` —
  they must keep `bet` = entry fee or update this handler. Owner-accepted.

## 💡 Session idea (Q-0089)

**Audit-finding triage heuristic: "flagged behavior that has a test asserting it = a deliberate
tradeoff, not a bug."** Before an audit reports a behavior as a bug, grep for a test (or a code
comment) that asserts the *current* behavior — if one exists, re-tag the finding "deliberate
tradeoff to revisit" and cite the counter-rationale, rather than "confirmed bug." Grounded in this
session: the engine-room audit called Bug 1 a "CONFIRMED critical" money bug, but
`test_..._drops_version_mismatch_without_refund` proved it was an intentional choice — which changed
it from "silently fix" to "ask the owner." Distinct from the previous session's class-4 absence-claim
linter; this is a rung on the adversarial-verify pass. *(Recorded here; merits filing as an idea +
index entry in a non-parallel session — deferred to avoid the shared-append collision with session B.)*

## ⟲ Previous-session review (Q-0102)

The PROMPT-A engine-room audit (#1690, this same conversation) delivered excellent breadth and
cite-accuracy, but its Bug 1 finding **mislabeled a deliberate, tested tradeoff as a clean bug** —
it cited `blackjack_cog.py:250-262` correctly but didn't grep for the counter-test that documents
the forfeit as intentional. **System improvement it surfaces:** exactly the audit-triage heuristic
above (check for a test asserting the flagged behavior before calling it a bug). The self-auditing
loop worked here — verifying the audit's own finding before acting caught the mislabel and routed a
money decision to the owner instead of a silent reversal.

## 🛠 Friction → guard (Q-0194)

**Friction:** an audit finding tagged "CONFIRMED critical" turned out to be a deliberate,
test-encoded tradeoff — I nearly reversed a tested money decision on the audit's word. **Guard
applied this session (process):** grepped for a test asserting the current behavior *before*
treating the finding as a clean bug, found the counter-test, and surfaced the tradeoff to the owner
(CLAUDE.md "look at the target before overwriting"). **Durable capture:** the Q-0089 audit-triage
heuristic above — the enforcing form is a lint/step in the audit workflow ("finding + a test
asserting it ⇒ downgrade to tradeoff"), routed as the session idea. No code guard shipped this
session (the fix is the deliverable); the durable prevention is the recorded heuristic.

## Grooming (Q-0015) · Self-initiated

- **Grooming:** closed two of the audit's ranked issues end-to-end (its ledger's two silent-loss-path
  findings) — advancing the audit → fix pipeline. The Bug-1 mislabel is fed back as a triage-heuristic
  idea so the audit itself improves.
- **⚑ Self-initiated:** none — executed owner-directed work (the panel choice "fix the 2 prod bugs",
  and the Bug-1 direction ratified live). No self-initiated idea→plan→build promotion.
