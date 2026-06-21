# 2026-06-21 — Creature PvP: challenge-expiry on timeout (⚑ self-initiated)

> **Status:** `complete` — PR #1265. **⚑ Self-initiated** (Q-0172).

> **Run type:** `routine · dispatch`

## Arc

Third slice of this dispatch run. The first two — creature-PvP result-recording + leaderboard (#1257)
and the rematch button (#1262) — merged and are live. This slice built the captured slice-2 session
idea (⚑ self-initiated, Q-0172): close the creature-PvP challenge view's **silent-timeout gap**.

## What shipped (PR #1265)

`CreatureBattleChallengeView` (`!cbattle`) has `timeout=60` but inherited `BaseView.on_timeout`, which
only disabled the buttons silently — an unanswered challenge read as dead. This is the same gap the
deathmatch **BUG-0013** fix closed for its own challenge view.

- `views/creature_battle/challenge.py` — override `on_timeout` to edit the message with an explicit
  *"⌛ {opponent} didn't respond — the creature challenge from {challenger} expired"* notice + disable
  the buttons. A `_resolved` flag (set at the top of accept/decline) guards the BUG-0013 race so a
  resolved challenge is never overwritten by a late timeout (accept/decline already call `self.stop()`,
  which cancels the timeout — the flag is belt-and-suspenders).
- `tests/unit/views/test_creature_challenge_timeout.py` — unanswered → expiry notice + buttons disabled;
  resolved → no overwrite; no-message → no-op.

Pure view — no service/DB/command, so no artifact regen.

## Findings / decisions

- **Self-initiation (the decision):** with both dispatched/idea slices merged and budget left, I took
  one more small reversible improvement I'd flagged myself (slice-2's session idea) rather than stop.
  ⚑ self-initiated on the run report + the claim. Kept to a single increment.
- **Decision made alone — `_resolved` guard over relying on `stop()` alone.** `self.stop()` cancels the
  timeout, so `on_timeout` shouldn't fire after accept/decline — but the deathmatch BUG-0013 entry
  documents a real race where a click lands as the timeout is already firing. Mirroring that fix's
  belt-and-suspenders flag is cheap insurance against overwriting a resolved challenge.

## Context delta

- **Needed but not pointed to:** nothing new — the deathmatch BUG-0013 entry (`bug-book.md`) was the
  exact precedent (silent challenge-timeout → explicit expiry + `_resolved` guard), and `BaseView`
  already tracks `self.message` for the edit.
- **Discovered by hand:** `BaseView.on_timeout` *does* edit the message (disabled view) but keeps the
  content — so to show an expiry notice you override it and set `content`, you don't just disable.
- **Decisions made alone:** see Findings (self-initiation; the `_resolved` guard).
- **Weak point / unverified:** not live-walked — the 60s real-timeout path is offline-tested only by
  calling `on_timeout()` directly. The expiry copy is a taste call, trivially editable.

## 📤 Run report

- **Did:** closed the creature-PvP challenge view's silent-timeout gap — an unanswered `!cbattle`
  challenge now shows an explicit expiry notice · **Outcome:** shipped (PR #1265, full CI mirror green,
  auto-merge armed by owner)
- **Shipped:** #1265 — creature PvP challenge-expiry notice
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none — **self-initiated**; one-file revert if undesired.
- **⚑ Owner manual steps:** none — merge auto-deploys; view-only, no migration/data.
- **⚑ Self-initiated:** **YES** — the challenge-expiry notice (captured slice-2 idea, Q-0172). The
  *run's* other self-initiated slice was #1262 (rematch); #1257 was the dispatched lane.
- **↪ Next:** creature-game PvP v1 is feature-complete + polished (catch · dex · battle · records ·
  leaderboard · rematch · timeout-expiry). Next ungated build = ▶ Next action lane (b) botsite React-SPA
  migration, (c) a `needs-hermes-review` lane, or (d) a fresh idea (Q-0172). **Recon is DUE (#1260
  crossed)** — that's the separate docs-reconciliation routine's job (auto-triggered), not dispatch's.

## 💡 Session idea

**A `views/` consistency-linter rule: a timed challenge/confirm view must override `on_timeout` with
user-visible copy.** Three challenge views now have the same lesson independently (deathmatch BUG-0013,
this creature fix, and any future PvP) — a `discord.ui.View`/`BaseView` subclass constructed with a
finite `timeout` that has interactive buttons but no `on_timeout` override is *probably* a silent-timeout
gap. A heuristic `check_consistency.py` rule (warn-only) flagging "timed interactive view with no
`on_timeout`" would catch the class at authoring time instead of one bug report at a time. (Dedup-checked
`docs/ideas/` — not captured; distinct from the existing `edit_in_place`/`back_button` rules.)

## ⟲ Previous-session review

This run's slice 2 (#1262 rematch) was a clean self-initiated increment, but it *introduced* the surface
this slice fixes without noticing it: the rematch flow re-issues a `CreatureBattleChallengeView`, which
is exactly the view with the silent-timeout gap — so #1262 made the gap *more* reachable (every rematch
is another challenge that can silently expire) without addressing it. Not a defect, but a missed
adjacency. **System improvement:** when a slice *re-instantiates* an existing view in a new path, it's
worth a 30-second check of that view's failure/timeout edges in the new context — the consistency-linter
idea above would have surfaced it mechanically. The good news: the "review the previous session" ender
caught it one slice later, which is the loop working.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this run | 3 (#1257 ✓merged · #1262 ✓merged · #1265 auto-merge on green) |
| CI-red rounds (this slice) | 0 real (born-red HOLD only) |
| New ideas contributed | 1 (timed-view on_timeout consistency rule) |
| Ideas groomed | 1 (built the captured challenge-expiry idea) |
| Files touched | 1 view + 1 test + 1 card |
