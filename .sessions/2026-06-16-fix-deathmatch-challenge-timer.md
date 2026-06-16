# Session — fix BUG-0013: deathmatch 1v1 challenge timer overwrites the live duel

> **Status:** `complete`

## Origin — the intake pipeline working end to end

The owner reported a bug to **Hermes** (gpt-5.4-mini) on Discord: the 1v1 deathmatch challenge
accept-timer kept running while a match was active and clobbered the result with "player didn't
respond in time". Hermes' new **`intake` skill** (shipped #928 earlier this session) routed it as a
bug, did genuine root-cause analysis against the real source, pinpointed `_ChallengeView` in
`deathmatch_cog.py`, and offered to bug-book it. This session is Claude Code **verifying that
diagnosis and fixing it** — the full reported-bug → Hermes-triage → Claude-fix loop, live.

## The bug (verified against source — Hermes was right)

`_ChallengeView` (the accept/decline pre-match prompt) is created with `timeout=30.0`, but:
- `btn_accept()` starts the real `_DuelView` yet **never called `self.stop()`**,
- `btn_decline()` also never stopped the view,
- `on_timeout()` had **no guard** for an already-answered challenge.

So the challenge view lived on; when its 30s timeout fired it edited its message — the *same* message
now showing the duel — to "⚔️ Challenge Expired". `_DuelView` was never the problem (it guards on
`duel.is_over`).

## Fix

`disbot/cogs/deathmatch_cog.py`:
- `__init__`: add a `_resolved` flag.
- `btn_accept` / `btn_decline`: set `_resolved = True` + call `self.stop()` (cancels the pending
  timeout — the duel owns the message lifecycle now).
- `on_timeout`: return early when `_resolved` (belt-and-suspenders for the race where the timeout was
  already firing). Behaviour-preserving for the genuine no-answer case.

Contained to `_ChallengeView` — no signature changes, blast radius 2 modules (per the context map),
neither affected.

## Verification

- `tests/unit/cogs/test_deathmatch_challenge_timeout.py` (NEW, 3 tests) — accept/decline stop the
  view + guard a late `on_timeout`; an un-answered challenge still expires. All fail against the old
  code, pass against the fix.
- `python3.10 scripts/check_quality.py --full` → green (9893 passed).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 new (only pre-existing `xp` warnings).
- Bug-book entry **BUG-0013** added (FIXED, regression test named).

## 💡 Session idea (Q-0089)

A lightweight AST invariant for Discord views: **any `discord.ui.View` with a finite `timeout=` whose
button handlers transition to another view must call `self.stop()` (or set a resolved-guard).** This
exact class — a stale timed view overwriting its successor — is easy to reintroduce and invisible to
existing tests. A `test_timed_views_stop_on_resolution.py` guard would catch the next one. (Captured;
not built — would need careful AST scoping to avoid false positives.)

## ⟲ Previous-session review (Q-0102)

The whole session built the Hermes base + the `intake` skill; this is the **first time it paid off in
a real fix** — the owner reported a bug, the intake skill triaged it correctly, and it became a clean
fixed bug here. What it proves: the front-door router + bug-book + Claude-fix chain composes exactly
as designed. The one gap it surfaced (the idea above) is that the *bot's own view code* lacked an
invariant for this timer-lifecycle class — worth a guard so the fix stays fixed.
