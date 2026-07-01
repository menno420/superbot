# 2026-07-01 — Boot smoke-test guard (never ship a cog that won't load)

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**Branch:** `claude/funny-franklin-4n38rf` (restarted from origin/main after #1600 merged).
**Run type:** `routine · dispatch` (owner-directed hardening after my own outage)

## What this run is doing

My PR #1599 (fishing Dock) named a command `!dock` that collided with `!sail`'s existing
`dock` alias inside the same cog → `CommandRegistrationError` at `add_cog` → `fishing` cog failed
to load → STRICT identity-contract aborted boot → **production crash loop**. #1600 (a separate
session) fixed it (dropped the alias) and broadened the static token guard. The owner's directive:
**shipping code that breaks the bot's startup must never happen** — this is the second such outage.

This run adds the **enforcing** prevention the Friction→guard rule (Q-0194) demands, at the layer
both outages slipped through: **a dynamic boot smoke test** (`tests/unit/invariants/test_cog_load_smoke.py`)
that constructs a bot like `bot1` and actually **loads every `INITIAL_EXTENSIONS` cog**, failing CI
if any raises at load — the "did the bot actually boot?" check that black/mypy/pytest/arch/the
command-surface ledger never performed. Plus the missing **BUG-0030** bug-book entry for the outage.
