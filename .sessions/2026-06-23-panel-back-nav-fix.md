# 2026-06-23 — Panel back/help navigation-completeness fixes

> **Status:** `in-progress` — owner live-walk of the post-fleet bot surfaced a **pervasive
> navigation-completeness class** the static `back_button` guard can't catch (false green): panels drop
> their help/hub Back button when you return to them after an action, and several game-result screens
> dead-end with no continuation. Six reported (AI · blackjack · rps · deathmatch · mining · fishing) +
> siblings found by source audit. PR this session, auto-merge armed on green (Q-0127). Owner-directed →
> merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## ⚠ Corrected diagnosis (mid-session — owner said it all worked THIS MORNING)

Initial "pre-existing dead-ends" read was **wrong** (owner correction). The real mechanism, proven from
`views/farm/menu.py:170-190`: the action callbacks **redraw onto a *fresh* view instance** (`view =
FarmMenuView(...)` — comment: *"so the classifier sees a real in-place update"*, i.e. to satisfy the
`edit_in_place` linter). A fresh instance does **not** carry the Back-to-Help / Back-to-Games button the
hub/help layer attached to the *original* instance → the back vanishes on the action. AI is the same
shape (`ai_home_page()` rebuilds a fresh `AIPanelView()`) and is the one **confirmed fleet (U1)
regression**. **Systemic root cause:** the *"redraw onto a fresh view"* idiom (rewarded by the
`edit_in_place` rule graduated today, #1375) drops externally-attached back buttons.

**Open gap (awaiting owner):** `farm`/`blackjack`/`deathmatch`/`mining` code was NOT changed today (only
AI/fishing/roles/community/games-hub were) — so for those the mechanism is either latent-surfaced or a
half-applied deploy from 6 rapid redeploys. Two disambiguators sent to owner: (1) open-path (help/hub vs
direct command) + which back vanishes; (2) does a clean worker restart clear any of them.

**Fix direction:** one architectural seam — a redraw must **carry its `_back_target` forward** (store on
the view, re-attach on rebuild — the threading the hub already does for children, applied to self-redraws)
— not 30 per-panel patches. Start with the confirmed AI regression. **HELD pending the 2 owner answers.**

## Two unified root causes (from source)

1. **Return-to-panel drops the grandparent back-target.** `help_cog` attaches Back-to-Help to a panel
   *instance* at open time; navigating into a game/sub-screen and back rebuilds the panel as a **fresh
   instance** that never re-attaches it. The shared `views/games/common.BackToPanelButton` already
   re-threads a `grandparent` target — it just isn't passed through. Confirmed: **AI** (`_nav.ai_home_page`
   → fresh `AIPanelView()`, `bt=0`; the one **fleet (U1) regression**), rps/blackjack (drop it on the
   return rebuild despite threading it into sub-views).
2. **Game-result screens are flat dead-ends.** The end-of-game view has no replay/back at all —
   **deathmatch** (`bt=0`), **fishing** catch, **casino** poker table (`bt=0`).

## Plan (one focused pass)

- Fix the **AI regression first** (ours): thread the panel's back-target through the choosers →
  `ai_home_page` so returning to AI home re-attaches Back-to-Help.
- Thread the back-target through each game's play→result→return path (rps/blackjack/mining).
- Add a back + continuation (Play again) to every terminal result view (deathmatch/fishing/casino).
- **Per-panel regression tests** asserting the result/return view carries a back affordance — the
  reliable guard the static rule can't be (it checks a class has a back *somewhere*, not that every
  runtime screen does).

(Close-out enders at session close.)
