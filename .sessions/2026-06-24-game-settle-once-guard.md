# Session — 2026-06-24 · settle-once terminal guard for game-state views

> **Status:** `complete` — shared settle-once guard + adoption in RPS PvP and the deathmatch bot-duel,
> with a cross-game regression contract. PR #1444.

**Trigger:** scheduled dispatch (empty fire, no work order). Phase gate = FIX (bugs/correctness first).
The two OPEN bug sub-cases (BUG-0019 #1 — owner design fork; BUG-0009 newest-towers — data-gated) were
both un-actionable autonomously, so I took the next correctness priority: a "Not Done" row in the games
production-readiness map — *"no cross-game test proves terminal controls cannot trigger a second
settlement after a result, timeout, or delayed duplicate interaction."* Continues the BUG-0013
challenge-timer lineage.

## What shipped

- **`disbot/views/terminal_guard.py`** (new) — `SettleOnceMixin.claim_settlement()` gives any
  game-state view one atomic claim on its terminal transition (returns `True` exactly once;
  `is_settled` property). A synchronous check-and-set, race-free on discord.py's single event loop
  **when taken before the handler's first await** (the documented contract). Mixin, not a base class,
  because game-state views intentionally extend `discord.ui.View` directly (the `views/base.py`
  divergence); declares no `__init__` so the class-level `False` default is the unclaimed state.
- **RPS PvP** (`views/rps/pvp_play.py`) — `_resolve()` is reachable twice (both-picks race · timeout
  racing a final pick); it previously relied **solely** on the wager-workflow idempotency and still
  posted a duplicate result embed. Now claims at the top → exactly one settle + one result post.
- **Deathmatch bot-duel** (`views/games/deathmatch_panel.py`) — `_finish`/`on_timeout` routed through
  the shared claim (was the bespoke `duel.is_over`, which is kept as the domain flag the embeds read).
- Silently-swallowed timeout `message.edit` failures in both views now log at debug (match
  `BaseView.on_timeout`) instead of `except: pass`.
- **Tests:** `tests/unit/views/test_terminal_guard.py` (primitive: claim-once, per-instance,
  no-init default) + 2 deathmatch + 2 RPS regression tests proving a second settlement short-circuits.

## ✅ Verification

`check_quality.py --full` → **12523 passed, 48 skipped, 2 xfailed** (mypy + black/isort/ruff green).
`check_architecture --mode strict` → **0 errors** (49 pre-existing warnings, none new — the two adopted
views already extended `discord.ui.View` directly). `check_quality --check-only` (docs/consistency) green.

## Handoff — remaining adopter (clearly scoped)

The other money-handling terminal path, **blackjack PvP/tournament settlement**, is *not* yet guarded.
Its `_resolve_pvp` is a **module-level function over a `_PvPState`** (not a view method), so it needs a
guard on the state object rather than the view mixin — a different shape, deserving its own focused PR.
It already `_pvp.pop(key, None)`s at the top but doesn't short-circuit on a missing key, so the
double-settle exposure remains (idempotent wager settle limits the money impact; the duplicate result
post is the residual). Durable home for this follow-up: the games-readiness map's "Remaining adopters"
note (updated this session).

## 💡 Session idea (Q-0089)

**An architecture-rule lint: a game-state view that has a settling path (posts a result / calls
`settle_pvp`/`refund_pvp`) and is reachable from >1 entry (a button + `on_timeout`) must adopt
`SettleOnceMixin`.** This session found the double-settle class by reading three views by hand; a
`check_architecture` rule that flags a `discord.ui.View` subclass calling a wager-settle helper in a
method *also* reachable from `on_timeout`, without a `claim_settlement()` call, would turn "I noticed it"
into a CI ratchet — the same shape as the `select_option_truncation` guard. Captured, not built (needs
the guard to prove itself across a couple of sessions first, per its own kill-switch posture).
Dedup-checked `docs/ideas/` — no existing settle-once/terminal-guard idea.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: **`2026-06-24-setup-log-channel-rework.md`** (the #1432 two-channel logging
rework). **Did well:** a clean declarative `LogChannelStep`, full green verification, and an honest
"misses" section owning the same-day #1429→#1432 rework. **Missed:** nothing in the work itself — the
recorded lesson (a scope-narrowing owner answer needs "final scope or first slice?" confirmation) is the
right one. **System improvement this surfaces:** that session's Q-0089 idea (use `AskUserQuestion`'s
per-option `preview` field for design forks) is genuinely high-leverage and currently sits only in a
session log. It should be **promoted into `docs/ideas/`** so it's groomable, not buried — a recurring
pattern where a strong session idea never leaves the log it was born in. (Routing note for the next
grooming pass; I didn't promote it this session to stay within my claimed lane.)

## 📋 Doc audit (Q-0104)

Games-readiness map updated (the Not Done → Partial row + the two silent-swallow rows). No
`current-state.md` ledger entry until #1444 merges (the ledger checker keys off merged PRs; the next
reconciliation/ledger pass picks it up). No owner *decision* made (self-initiated correctness slice). No
new top-level doc; the new primitive is documented in its own module docstring + the map note.
`check_docs --strict` green.

## 📤 Run report

- **Run type:** routine · dispatch
- **What shipped:** PR #1444 — settle-once terminal guard primitive + RPS PvP & deathmatch bot-duel
  adoption + cross-game regression contract; games-readiness map de-staled.
- **⚑ Self-initiated:** yes — advanced a production-readiness "Not Done" correctness/safety row
  (no dispatch/owner ask). Contained, reversible, test-covered.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **Bug-book:** no entry flipped (BUG-0013 already FIXED; this generalizes its class). BUG-0019 #1 and
  BUG-0009 newest-towers remain OPEN/gated.
- **Remarks:** CodeGraph built clean at session start (52415 nodes). Grimp/arch checks ran clean.
