# 2026-06-23 — Game-result continuation buttons (never-stranded follow-up)

> **Status:** `in-progress` — owner-directed follow-up to PR #1382. That PR made every *panel* one
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

(Close-out enders at session close.)
