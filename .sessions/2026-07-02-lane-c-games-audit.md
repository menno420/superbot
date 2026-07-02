# 2026-07-02 — Lane C new-bot capability audit (Games & Community)

> **Status:** `in-progress`
> **Branch:** `claude/lane-c-games-audit-q35nkr` · **PR:** #1664
> **Session type:** ultracode audit (docs-only) — new-bot-capability-audit Lane C

## What I'm about to do

Complete Lane C of the new-bot capability audit: verify + tier every surface unit of the 10
Games & Community subsystems (games, blackjack, deathmatch, rps_tournament, counting, chain,
leaderboard, community, community_spotlight, karma) against the §2 grammar spike, write manifest
sketches, disposition every tier-3 (reuse G-1…G-6 / propose new G-<n> / mark deliberate escape
hatch), compute fit numbers, flag structural danger zones, and add MAP→RECONSIDER→SIMULATE→OPTIMIZE
recommendations. This is the hardest grammar-fit lane (blackjack measured 44% in the spike). The
central question: do stateful game/community loops need a new game-state primitive family, or do
they express as tier-1/2 with existing amendments + deliberate tier-3 escape hatches?

Output is docs-only: `docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-C-games.md`.
No `disbot/` / runtime / test edits.

<!-- born-red: flipped to `complete` as the deliberate final step (Q-0133) -->
