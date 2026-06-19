# Session — extend consistency linter (select-option truncation) to `disbot/cogs/`

> **Status:** `in-progress`

**Lane B4 (ultracode fleet).** Extending `scripts/check_consistency.py` rule 4
(`select_option_truncation`) to also scan `disbot/cogs/` — the cog-layer blind spot
BUG-0017 (Cog Manager dropdown silently dropped 22/46 cogs via `options[:25]`) lived in.
The SelectOption module-gate stays so leaderboard `[:10]` slices in non-select cogs stay
out; the new cog coverage is **warn-only** (no graduation this PR — the graduated `views/`
coverage stays error). Evaluating `panel_base_class` for cogs (likely N/A — cogs are
`commands.Cog`, not `discord.ui.View`). Code + tests + allowlist + plan + PR, born-red → green.
