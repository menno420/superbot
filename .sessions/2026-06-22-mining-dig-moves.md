# 2026-06-22 — Mining grid: dig-moves-you (unified mine+move)

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` last.

## Arc

Owner design correction (in-chat, right after the grid Mine #1281 merged): *"each mining action
would move you on the grid — mining down goes down one cell, mining forwards goes one cell forward,
etc."* The shipped grid Mine had **separate** movement buttons + a "Mine here" button; the owner's
actual intent is **unified directional digging** — every dig moves you one cell in that direction
**and** mines the cell you move into.

About to change: replace `mining_workflow.move` + `mine_here` with one `dig(direction)` (move into the
adjacent cell + mine it, atomic); collapse the navigator's 6 move buttons + Mine-here into **6
directional dig buttons**; update tests + docs. No command-surface change (buttons are ephemeral;
`!mine`/`!fastmine`/`!mineworld` unchanged) → no artifact regen. Owner-directed → auto-merge on green.
