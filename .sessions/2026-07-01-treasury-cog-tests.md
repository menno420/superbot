# 2026-07-01 — Treasury completion tests (cog + modal)

> **Status:** `in-progress`

**Run type:** routine · dispatch (empty fire — S1 completion-first, slice 2)

## What I'm about to do

Clear Treasury completion-cert offline punch #1 + #2 (`docs/planning/feature-completion/units/treasury.md`,
`◐ assessed`) — pure test coverage, zero runtime change:
1. **Punch #1** — `tests/unit/cogs/test_treasury_cog.py`: `!treasury` panel open, `contribute` (positive +
   non-positive reject), `grant` (positive + non-positive reject + `manage_guild`/owner authority gate).
2. **Punch #2** — `tests/unit/views/test_treasury_contribute_modal.py`: `_ContributeModal.on_submit`
   edge cases (non-int, negative, zero → ephemeral errors, service not called; valid large → contribute
   + redraw).
