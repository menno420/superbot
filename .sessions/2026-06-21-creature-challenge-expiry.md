# 2026-06-21 — Creature PvP: challenge-expiry on timeout (⚑ self-initiated)

> **Status:** `in-progress` — born-red HOLD; flips to `complete` as the final step.

> **Run type:** `routine · dispatch`

## What I'm about to do

Third slice of this dispatch run (#1257 result-recording + #1262 rematch button both merged + live).
Building the captured slice-2 session idea (⚑ self-initiated, Q-0172): the creature-PvP **challenge
view times out silently** — `CreatureBattleChallengeView(timeout=60)` just disabled its buttons with no
"challenge expired" message, so an unanswered challenge read as dead. This is the same silent-timeout
gap the deathmatch **BUG-0013** fix closed for its own challenge view.

- `challenge.py` — override `on_timeout` to edit the message with an explicit "⌛ {opponent} didn't
  respond — the challenge expired" notice + disable the buttons; a `_resolved` flag (set by
  accept/decline) guards the BUG-0013 race so a resolved challenge is never overwritten.
- `tests/unit/views/test_creature_challenge_timeout.py` — unanswered → expiry notice; resolved → no
  overwrite; no-message → no-op.

Pure view, no service/DB/command — small, contained, self-merge on green.
