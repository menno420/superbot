# External review — superbot-next band 1–5 runtime defect-class sweep (2026-07-10)

> **Status:** `audit` — external (Codex/GPT-5.6-Sol) runtime review, independently verified 2026-07-10 (see addendum).

Scope: public `menno420/superbot-next` HEAD `d1d7de9`, focusing on `sb/` domain/service/state-machine/persistence code, the warn-escalation regression called out in `docs/eap/fleet-quality-review-2026-07-09.md` §10, and games `Reply`-shape crash paths.

Commands run:

```bash
git clone https://github.com/menno420/superbot-next.git /tmp/superbot-next-review
cd /tmp/superbot-next-review
python -m pytest \
  tests/unit/band2/test_band2_slice1.py::test_warn_escalation_blocked_compensates \
  tests/unit/band6/test_band6_games_substrate.py::test_world_card_view_handler_reply_shape \
  tests/unit/interaction/test_handler_kit.py::test_no_domain_module_redeclares_reply -q
```

Result: `3 passed in 0.42s`.

## Executive summary

* **Highest-impact confirmed status:** the specific warn-escalation regression is **fixed at HEAD**. The implementation still performs the successful-path warn reset/history writes in the DB leg, but now threads row/count handles and declares a compensator for a Discord-refused escalation.
* **Confirmed residual bug class:** one same-shape runtime bug remains in `proof_channel.end_access`: the DB unlock row is committed before the Discord unlock effect, and the effect has neither compensator nor retry/outbox semantics. A failed Discord unlock leaves persisted history saying access ended while the external state remains locked.
* **Games `Reply` crash class:** the recently fixed `worldcard` raw-dict bug is covered by a targeted unit test and a broader “no local Reply boilerplate” invariant. I did not find another confirmed handler in `sb/domain/games` returning a raw dict where `Reply` is required.

## CONFIRMED bugs / statuses, ranked by user impact

### P0 — fixed: warn escalation no longer loses warning count/history on Discord-refused escalation

**Status:** fixed at superbot-next HEAD `d1d7de9`.

**Evidence traced:**

* The warn DB leg still writes the triggering warn row, and on threshold it clears warnings and writes escalation + `clearwarnings` rows in the transaction. It now also stores `_escalation_row_ids` and `_pre_escalation_count` in `ctx.params`, explicitly documenting that these are compensation handles for a refused escalation. (`sb/domain/moderation/ops.py:59-90` in superbot-next.)
* The warn effect leg applies timeout/kick/ban only after the DB commit. (`sb/domain/moderation/ops.py:219-237` in superbot-next.)
* The compensator opens a new transaction, restores warning count to `_pre_escalation_count`, withdraws the phantom escalation/clear rows, and records an operator finding. (`sb/domain/moderation/ops.py:300-340` in superbot-next.)
* The WARN op declares the effect as `compensatable` with `moderation.compensate_warn_escalation`. (`sb/domain/moderation/ops.py:386-391` in superbot-next.)
* The unit test now pins the oracle behavior for the blocked path: restored count is `3`, rows `(11, 12)` are withdrawn, and the op wiring points at the compensator. (`tests/unit/band2/test_band2_slice1.py:133-190` in superbot-next.)
* I ran the targeted test and it passed: `python -m pytest tests/unit/band2/test_band2_slice1.py::test_warn_escalation_blocked_compensates -q`.

**User impact if it regresses again:** high. Moderators would see phantom auto-actions and users would lose warning counts even when Discord refused the escalation.

**Minimal diff needed now:** none for the fixed regression. If tightening further, add one end-to-end `engine.run(WARN)` test with `active_actions().timeout_member` raising to prove the engine actually calls the compensator, not only that the compensator function works in isolation.

---

### P1 — confirmed: `proof_channel.end_access` commits an unlock row before the Discord unlock effect, with no compensator

**Status:** confirmed same defect class, needs fix.

**Evidence traced:**

* `END_PRIZE` / `proof_channel.end_access` first runs `proof_channel.record_unlock` as a DB leg, then runs `proof_channel.apply_unlock` as an EFFECT leg. (`sb/domain/proof_channel/ops.py:154-162` in superbot-next.)
* The effect leg is declared only `reversible`, with no `compensator`. (`sb/domain/proof_channel/ops.py:160-161` in superbot-next.)
* The workflow engine commits DB/audit/outbox at step 4, stamps `committed_at`, and only then runs EFFECT legs. (`sb/kernel/workflow/engine.py:302-315` in superbot-next.)
* When an effect raises and has no compensator, the engine merely records an operator finding and returns a partial result; it does not undo the already committed DB mutation. (`sb/kernel/workflow/engine.py:326-360` in superbot-next.)

**Failure trace:** if `service.active_locks().unlock_channel(...)` raises after the DB transaction commits, the access-revoked row exists while the channel/role lock may still be applied in Discord. The next operator view/audit trail can say the prize/access ended when the user-visible permission state did not.

**Minimal diff proposal:**

1. Prefer the warn fix pattern: make the DB leg store a row id or enough identity to withdraw/mark the unlock record, set the `apply` leg to `compensatable`, and add `proof_channel.compensate_unlock_record` that restores/withdraws the unlock bookkeeping when Discord unlock fails.
2. If persistence supports idempotent retry better than withdrawal, mark the DB state as `pending_unlock` until the effect succeeds, then finalize after the effect through a second DB leg/outbox worker. That is larger, so I recommend the compensator for minimal diff.
3. Add a unit test analogous to `test_warn_escalation_blocked_compensates`: monkeypatch `unlock_channel` to raise, run `engine.run(proof_channel.end_access)`, and assert the persisted unlock bookkeeping is withdrawn/restored and the result is `partial`.

---

### P2 — fixed: games `worldcard` handler now returns `Reply`, not raw `dict`

**Status:** fixed at superbot-next HEAD `d1d7de9`.

**Evidence traced:**

* `games.world_card_view` returns `Reply(SUCCESS, await world_card_text(uid, gid))`, and the comment names the resolver crash mechanism. (`sb/domain/games/service.py:124-131` in superbot-next.)
* The targeted regression test asserts `.outcome` and `.user_message`, the exact duck-shape `resolve.py` expects. (`tests/unit/band6/test_band6_games_substrate.py:273-284` in superbot-next.)
* A broad invariant now scans `sb/domain` and fails if modules redeclare local `Reply` or `_ctx_from_req`, reducing copy/paste drift that caused shape bugs. (`tests/unit/interaction/test_handler_kit.py:57-66` in superbot-next.)
* I ran the targeted `worldcard` and handler-kit tests and they passed.

**Minimal diff needed now:** none for `worldcard`. To extend coverage, add a manifest-wide handler-shape test that resolves every registered command handler and invokes a smoke request where possible, asserting either `Reply` or a documented non-reply task shape.

## SUSPECTED / pattern-matched issues needing repro

### S1 — effect failure user messages may underreport compensation outcomes

The engine invokes compensators after failed effects but does not append the compensator `StepResult` or compensator `user_message` to the returned `WorkflowResult`; it only records a finding if the compensator itself fails. (`sb/kernel/workflow/engine.py:343-352` in superbot-next.) This is not necessarily a state-corruption bug, but it can hide from unit tests and operators whether the compensator actually restored state.

**Suggested test:** for warn escalation, run full `engine.run(WARN)` with a mocked Discord `Forbidden` and assert the returned result exposes `partial` plus either an explicit `escalation_blocked` after-state or a compensation step. If the current product intentionally keeps compensation internal, document that result-shape contract.

### S2 — `economy.work` treats XP awarding as optional post-commit effect

`economy.work` records coins in the DB leg and awards work XP as an optional EFFECT leg. (`sb/domain/economy/ops.py:402-407` in superbot-next.) If XP failure is acceptable degradation, this is fine; if old semantics coupled work payout and XP atomically, this is semantic drift. I did not trace the old-bot oracle for this path, so this remains suspected only.

**Suggested repro:** force `economy.award_work_xp` to fail and compare old bot behavior for a successful `work` command: should users receive coins without XP, or should the command be retried/blocked?

## Notes on tests that assert buggy behavior

I found one historical-style test name/comment that still asserts the successful warn threshold path clears the count inside the DB leg (`test_warn_escalation_ladder`), but it now explicitly points to the blocked-path oracle test and checks compensation handles. (`tests/unit/band2/test_band2_slice1.py:80-130` in superbot-next.) I do **not** consider it a current wrong-behavior pin because the old bot’s successful escalation path did clear warnings; the regression was the refused escalation path.

## Recommended next patch order

1. Fix `proof_channel.end_access` compensation first; it is the only confirmed same-class residual I traced.
2. Add a full-engine warn blocked-escalation test to supplement the direct compensator unit test.
3. Add a manifest-wide handler return-shape smoke test for games and other command surfaces.

---

## Independent verification addendum (Claude, 2026-07-10)

Every evidence claim above was re-verified against superbot-next HEAD `04436ab`
(the tree moved past the reviewed `d1d7de9`; line numbers drifted slightly but
every cited mechanism is real):

- Warn compensation handles (`_escalation_row_ids` / `_pre_escalation_count`,
  now `ops.py:89-90`), the compensator (`ops.py:300-336`), and the
  `compensatable` + compensator declaration (`ops.py:390-391`) — **confirmed**.
- `END_PRIZE` legs: DB `record_unlock` then EFFECT `apply_unlock` declared bare
  `"reversible"` with no compensator — **confirmed** (contrast `GRANT_PRIZE`,
  which declares `compensate_lock`).
- Engine behavior (commit at step 4, effects after, failed effect without
  compensator → operator finding only; compensator's own `StepResult` discarded
  at `engine.py:348`) — **confirmed**, including the S1 observation.
- The three targeted tests were re-run independently under Python 3.11 (the
  repo's CI interpreter): `3 passed` — **confirmed**.

**One correction — the completeness claim is falsified.** The review states
`end_access` is "the only confirmed same-class residual I traced." A full sweep
of every `LegKind.EFFECT` declaration in `sb/` (there are none outside
`sb/domain/*/ops.py`) finds a second instance:

- **`moderation.timeout` (P1, same class):** the DB leg `record_timeout`
  durably writes a moderation-history row via `store.log_mod_action(...,
  action="timeout")` (`ops.py:150-152`) and commits before the EFFECT leg
  `apply_timeout` runs; the effect is declared `"reversible"` with **no
  compensator** (`TIMEOUT = _op(...)`, `ops.py:396-398`). If Discord refuses
  the timeout (missing permission / role hierarchy — a common live failure),
  the history durably says the member was timed out while they weren't.
  Same minimal fix as proposed for `end_access`: thread the row id, declare
  `compensatable`, withdraw the row in a `moderation.compensate_timeout`, and
  pin it with a blocked-path test like `test_warn_escalation_blocked_compensates`.
- **Judgment case, not a defect:** `KICK` has the same record-then-effect shape,
  but its effect is deliberately declared `irreversible` behind a typed-phrase
  `ConfirmationSpec` (ledgered as D-0029). A Discord-refused kick still leaves a
  phantom "kicked" history row; worth a compensator on the *record* leg even if
  the effect stays irreversible.

Recommended patch order accordingly becomes: (1) `proof_channel.end_access`
compensation, (1b) `moderation.timeout` compensation — same pattern, same test
shape, (2) full-engine warn blocked-escalation test, (3) manifest-wide
handler return-shape smoke test.
