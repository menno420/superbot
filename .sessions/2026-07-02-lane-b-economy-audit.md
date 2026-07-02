# 2026-07-02 — Lane B new-bot capability audit (Economy & Character-sim)

> **Status:** `in-progress` — docs-only, ULTRACODE. Auditing the 11 Lane B subsystems
> (economy·inventory·treasury·mining·fishing·creature·farm·xp·casino·four_twenty·counters)
> against the §2 manifest grammar (`tools/grammar_spike/`): completing the surface-unit ledger
> from source, filling both tier columns, sketching each manifest, dispositioning tier-3s,
> computing fit numbers, flagging structural danger zones, and adding MAP→RECONSIDER→SIMULATE→
> OPTIMIZE recommendations. Output: `lanes/lane-B-economy.md` only. No `disbot/` / runtime code.

## What I'm about to do (born-red hold)
- Verify + complete each subsystem's surface-unit ledger against shipped source (cite `file:line`).
- Tier each unit as-written and with amendments G-1…G-6; propose new `G-<n>` only for recurring gaps.
- Deep focus (Lane B danger zones): deep persistent state, transactional multi-write mutations,
  escrow/settlement + double-settle risk, inventory/item taxonomy, mining grid / creature battle /
  farm growth state, XP + leaderboard derivation, scheduled loops + cooldowns, irreversible economy ops.

_(This card opens the PR born red; flipped to `complete` as the deliberate final step.)_
