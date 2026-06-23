# 2026-06-23 — Cleanup panel UX overhaul: readable whitelist, fixable warnings, custom levels

> **Status:** `in-progress` — owner-directed (screenshot + request: the cleanup panel is hard to use,
> the "legacy key" warning is unfixable, the whitelist shows other servers' channels as raw IDs, and
> presets are too limited). Open PR born-red per Q-0133; flip to `complete` as the final step.

> **Run type:** `manual · owner-directed`

## What I'm about to do

The owner sent a screenshot of `!cleanup` → Cleanup Policies and three concrete pain points. Root causes
confirmed in source:

1. **Whitelist shows all servers' channels as raw IDs** — `cogs/cleanup/panel.py` renders the *global
   static* `config.CLEANUP_WHITELIST_CHANNELS` (4 hardcoded env IDs) with `<#id>` mentions. Channels not
   in the current guild can't resolve client-side → raw IDs. **Fix:** resolve each ID against the current
   guild (`guild.get_channel`) and list only this server's channels, by name.
2. **"Legacy key — re-set to fix" warning is genuinely unfixable** — re-setting writes a *different* row
   (`scope_id=guild_id`) and leaves the stale `scope_id=0` row in place forever. **There is no delete path
   in the whole cleanup stack.** **Fix:** add an audited remove path (db `delete_cleanup_policy` →
   governance `remove_cleanup_policy` → service `remove_cleanup_change`) and a 🗑️ **Remove a policy**
   button that lists existing rows (incl. legacy/stale) so the warning is clearable in one click.
3. **Only 4 presets, no per-channel customization** — the DB + resolver already store arbitrary column
   values; only the UI is preset-locked. **Fix:** add a **⚙️ Custom…** level option → modal (delete
   invalid y/n · delete failed y/n · delete-after seconds) → same dry-run preview → audited apply.

## Files (planned)

- `disbot/utils/db/governance.py` — `delete_cleanup_policy(guild_id, scope_type, scope_id)`
- `disbot/governance/writes.py` — `remove_cleanup_policy` pipeline method + `remove_cleanup_policy_for_scope`
- `disbot/services/cleanup_diagnostics.py` — `remove_cleanup_change` + custom-columns preview/apply
- `disbot/views/cleanup/policy_panel.py` — Custom… modal + Remove-a-policy select + apply-via-columns
- `disbot/cogs/cleanup/panel.py` — guild-resolved, name-rendered, guild-filtered whitelist
- tests mirroring `tests/unit/services/test_cleanup_diagnostics.py` + `tests/unit/cogs/test_cleanup_panel.py`

## What shipped

_(filled in at close)_
