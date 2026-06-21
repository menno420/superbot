# 2026-06-21 — Creature PvP: rematch button (⚑ self-initiated)

> **Status:** `in-progress` — born-red HOLD; flips to `complete` as the final step.

> **Run type:** `routine · dispatch`

## What I'm about to do

Second slice of this dispatch run (the first — creature-PvP result-recording + leaderboard, PR #1257 —
merged). With the dispatched lane (a) consumed and budget remaining, I'm building **one contained,
captured idea** (Q-0172 self-initiated): a **🔄 Rematch button** on the creature-PvP outcome embed.

- `views/creature_battle/rematch.py` — `CreatureRematchView(BaseView)`: a two-participant
  `interaction_check` (either fighter may click — specialized lifecycle, commented) + one Rematch button
  that re-issues a fresh `CreatureBattleChallengeView` (clicker = challenger, other = opponent).
- `challenge.py` attaches the rematch view to the outcome message.
- No new service/DB/schema — reuses the existing challenge flow + the #1257 audited result-recording on
  the next battle automatically.

⚑ Self-initiated (Q-0172) — captured first in `docs/ideas/creature-pvp-rematch-button-2026-06-21.md`.
