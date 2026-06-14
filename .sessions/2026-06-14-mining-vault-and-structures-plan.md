# Session: mining Vault structure (ship) + turn-key structures/skill-tree plan (for the night session)

> **Status:** `in-progress` — born-red session card (Q-0133). Flipped to `complete` as the
> deliberate final step once the work + close-out docs are in.

**Branch:** `claude/exciting-brahmagupta-1duzde` · **Date:** 2026-06-14 · **Type:** product (S1 games / mining) + handoff

## What I'm about to do (declared up front — visible to the night session on the open PR)

The owner is going to sleep; a Hermes-guided **night routine** starts ~30 min out and may run for as
long as it wants, executing **any documented plan, preferably bot-side (mining cog + related)**. My
job this session:

1. **Ship a contained, additive mining slice myself** — the **§7.5 Vault** (a per-player *safe stash*
   separate from the active inventory): migration + DB module + workflow ops + panel + hub button +
   `!vault`/`!stash`/`!unstash` + tests. Purely additive (no existing play changes), so it's safe to
   land late at night, and it proves the structures-lane path end-to-end.
2. **Write the turn-key plan the night session needs** — the §7.5 structures (Forge/Vault/Home) +
   §7.4 capped skill tree currently live only in a *brainstorm* (`docs/ideas/`, status `ideas`), not
   an executable plan. I'll promote them to a source-verified `docs/planning/` plan with PR-sized,
   turn-key slices so the night session can pick the next one up cold.
3. **Verify the mining lane is correctly planned + write the night-session handoff** (current-state ▶
   pointer, roadmap, a clear "you can work as long as you want; here's the queue" note).

(Close-out — what actually happened, the Q-0089/Q-0102/Q-0104 enders, and the badge flip — is written
at the bottom as the final step.)
