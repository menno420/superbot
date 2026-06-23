# 2026-06-23 — Game-result continuation buttons (never-stranded follow-up)

> **Status:** `complete` — owner-directed follow-up to PR #1382. That PR made every *panel* one
> click from Help + its hub; this one fixes the **game-result dead-ends** it explicitly left: terminal
> game-state views that disable all their buttons and strand the player with no continuation. PR this
> session; auto-merge armed on green (Q-0127); owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## The dead-ends (owner-reported)

- **Deathmatch vs bot** — `_BotDuelView._finish` / `on_timeout` disable every button and re-render the
  result with the same dead view → **no continuation at all** (the worst case; explicitly reported).
- **Fishing** — `FishingCastView` interaction terminals (`_finish` catch, `_terminate_interaction`)
  `_disable()` + `view=self`; only a footer hint ("!fish to cast again") → soft dead-end (forces a command).
- **Casino** — `PokerEndView` already has **Deal next hand / End table**; not a dead-end → left as-is.

## Approach (reuses PR #1382's mechanism)

Terminal screens become **`HubView`s with `SUBSYSTEM` set** so `attach_standard_nav` auto-gives them
**📚 Help + ↩ ‹hub›**, plus a game-specific **"… again"** button:

- `_BotDuelResultView(HubView, SUBSYSTEM="deathmatch")` — **🔁 Play again** (re-fetch gear, fresh
  `_BotDuelView`) + auto Help + Back-to-Games. Used in `_finish` and `on_timeout`.
- `_FishingDoneView(HubView, SUBSYSTEM="fishing")` — **🎣 Cast again** (mirrors `FishingMenuView.cast_btn`
  → `prepare_cast`) + auto Help + Back-to-Games. Used in the interaction terminals.

## Close-out

**Verification:** `check_quality --full` green — **12157 passed**, 48 skipped; `mypy disbot/` clean;
`check_architecture --mode strict` 0 errors; `check_consistency` green (incl. the new auto-nav
exemption + opt-out tests); ledger + `check_docs --strict` pass (Q-0104).

**Durable fix beyond the two views:** the static `back_button` consistency rule (`scripts/check_consistency.py`)
now recognises a `SUBSYSTEM`-declaring panel as having a back affordance via `attach_standard_nav` (the
runtime auto-nav), so it no longer false-flags the leaf panels PR #1382's mechanism already covers —
and it still flags a `STANDARD_NAV = False` opt-out (Q-0120: a check that contradicts the evidence is a
bug in the check). Two new tests pin both directions.

**💡 Session idea (Q-0089):** *A runtime "no terminal dead-end" invariant for game-state views.* PR #1382
made the static checker understand panels; this PR fixed two game-result dead-ends by hand. The gap that
remains: `discord.ui.View`-direct game-state views (blackjack hands, rps rounds, the casino seat views)
have no machine guarantee that their *terminal* state offers a continuation. A test that drives each
game's terminal path (or asserts every `self.stop()`-reaching render swaps to a view with ≥1 enabled
control) would convert "never stranded" into a contract for game screens too, not just panels. Distinct
from the `back_button` rule (which only covers `HubView` panels, not transient game-state views).

**⟲ Previous-session review (Q-0102):** the previous session (PR #1382, universal panel nav) shipped the
mechanism cleanly and even *flagged* this exact follow-up ("game-result dead-ends … separate small fix")
in its PR body and session card — good forward-handoff discipline; this session just executed that named
item, which is the system working as intended. What it could have done better: it left the static
`back_button` checker unaware of the new auto-nav, so the very first leaf panel built on the new
mechanism (`_FishingDoneView`) tripped a false-positive — i.e. the mechanism and its checker shipped a
session apart. **System improvement (applied):** when a PR introduces a new "the constructor provides X"
mechanism, update the static checker that asserts X *in the same PR*, so the checker and the mechanism
never drift. Did that here for `back_button`.

**Claim** `docs/owner/claims/claude__game-result-continuations.md` deleted at close (Q-0126).

