# Creature PvP — rematch button on the outcome embed

> **Status:** `in-progress` — ⚑ self-initiated (Q-0172). Captured + built 2026-06-21.

## Idea

The creature PvP flow (`!cbattle`, shipped #1230 + #1257) ends with a static outcome embed; to play
again both players must re-type `!cbattle @x`. A single **🔄 Rematch** button on the outcome embed —
clickable by *either* participant — re-issues a fresh challenge (the clicker becomes the challenger,
the other the opponent, who then Accepts/Declines as usual). This makes laddering feel continuous,
mirroring the rps `🔁 Play again` affordance, with **no new battle logic** — it just reuses the
existing `CreatureBattleChallengeView`.

## Why it's worth having

- Removes friction from the core PvP loop (re-typing the command + mention each round).
- Pure view addition — no new service / DB / schema; reuses the audited result-recording path on the
  next battle automatically.
- Completes the creature-PvP v1 UX (the catch/dex/battle/leaderboard cluster).

## Shape

- `views/creature_battle/rematch.py` — `CreatureRematchView(BaseView)` with a two-participant
  `interaction_check` (either fighter may click) and one Rematch button that posts a fresh
  `CreatureBattleChallengeView`.
- `challenge.py` attaches the rematch view to the outcome message.

Dedup-checked `docs/ideas/` (2026-06-21) — not previously captured.
