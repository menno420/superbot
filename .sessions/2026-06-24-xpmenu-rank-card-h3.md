# 2026-06-24 — `!xpmenu` hub renders the rank image card (visual card-engine H3)

> **Status:** `in-progress`

> **Run type:** `routine · dispatch`

## What I'm about to do
Scheduled dispatch fire, no work order. Bugs blocked/data-gated (BUG-0009 newest-towers
needs release-order data · BUG-0011 needs a VPS repro); BUG-0009/0019 rootfix backlog
both blocked. Taking the **S1 consolidation polish tail · visual card-engine H3**:
the `!xpmenu` hub panel (`_XpHubView`) currently shows a plain rank **embed** while
`!rank` already renders the themed image **card** (`utils/rank_render.py`, #1401).

This slice migrates the **direct `!xpmenu` surface** onto the same image card:
- `_XpHubView.build_response(stat)` → `(embed, card)` via the existing
  `services.xp_helpers.build_rank_response` (the same fetch-once embed+card the
  `!rank` view uses); the stat-switch buttons re-render with `attachments=[card]`,
  exactly mirroring `_RankSelect.callback` (the established H3 toggle grammar).
- `XpCog.xp_menu` sends the card via `send_panel(..., file=card)` (already supports it).
- Pillow-less hosts degrade to the embed (card `None`) — byte-identical fallback.
- `build_help_menu_view` stays **embed-only** (the help-nav seam is embed-only by
  contract across the whole codebase — threading a file through every hub seam is a
  separate cross-cutting change, out of scope here).

Idea→ship is self-initiated (Q-0172) — flagged on the run-report ⚑ Self-initiated line.
Plus regression tests; full CI mirror green; auto-merge on green.
