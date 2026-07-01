# 2026-07-01 — PROD hotfix: fishing `dock` command collided with `sail`'s `dock` alias (crash loop)

> **Status:** `in-progress`

**Incident:** Railway `worker` in a boot crash loop (restart every ~30s, never reaching the
gateway). Reported via attached deploy logs. Owner-directed live session. ⚑ **Self-initiated:**
the guard-generalization below (broadening the duplicate-token CI check to catch *same-cog*
collisions) goes beyond the literal one-line alias fix — added as root-cause prevention for the
whole same-cog collision shape.

## Root cause (confirmed from the deploy logs)

```
❌ Failed to load cogs.fishing_cog: CommandRegistrationError:
   The command dock is already an existing command or alias.
→ Subsystem 'fishing' has no loaded commands — marking INTERNAL
→ entry_point 'fish'/'fishlog' declared by 'fishing' is not a loaded command
→ Identity-contract findings | total=2 | fatal=2 | STRICT=on | abort=yes
→ Identity-contract: STRICT mode aborting startup.
```

A **same-cog** top-level token collision inside `FishingCog`:

- `!sail` (`disbot/cogs/fishing_cog.py:112`) has carried `dock` as an **alias** since `98a692d`
  (2026-06-29) — "dock back on shore", the venue toggle.
- **PR #1599 / commit `8744a7b`** (`feat(fishing): Dock — bite-speed coral structure`) added a
  first-class command literally **named** `dock` (the Tide Pool's sibling: view + embed + audited
  build seam + tests, all keyed to `structures.DOCK = "dock"`).

At `add_cog`, `sail` registers first (claiming alias `dock`); the new `dock` command's name then
collides → `CommandRegistrationError` → the whole cog fails to load → its declared entry points
(`fish`, `fishlog`) vanish → STRICT identity-contract aborts boot. Crash loop, never reaches the
gateway → offline.

## Why CI didn't catch it (the guard gap)

The `give` crash (2026-06-29) added `test_no_duplicate_top_level_command_names_across_cogs`, but it
de-duplicated claimants **by cog** (`len(set(cogs)) > 1`) — so a single cog claiming a token twice
(here `dock` = `sail`'s alias **and** the `dock` command's name, both in `FishingCog`) looked like
*one* claimant and slipped through. This fell in the gap **between** the two existing guards:
Q-0200's exact-name guard is same-*module* but matches `def` names (sees `def sail` ≠ `def dock`),
and the cross-cog guard dedupes by cog. Neither models a same-cog **name-vs-alias** clash. The
runtime `command_surface_ledger` can't help either — it only sees commands *after* they load, which
a collision prevents.

## What changed

- **`disbot/cogs/fishing_cog.py`** — dropped the vestigial `dock` alias from `!sail`
  (`aliases=["setsail", "dock"]` → `["setsail"]`); the new `!dock` structure command owns the name
  (its natural, discoverable entry point). `!sail` + `!setsail` still fully cover the venue toggle;
  docstring reworded ("dock back on shore" → "return to shore") so nothing implies `!dock` toggles.
- **`tests/unit/invariants/test_extension_integrity.py`** — broadened the guard (enforce, don't
  exhort — Q-0194/Q-0132): `_top_level_command_tokens` → `_top_level_command_claims`, now counting
  distinct **commands** per token (identity-deduped, so a command's own name+aliases is one claim
  but two commands are two). Renamed the test `…_across_cogs` → `test_no_duplicate_top_level_command_tokens`
  — it now catches **same-cog and cross-cog** token collisions uniformly. Regression-proven: with the
  alias re-added it fails `!dock: FishingCog.dock, FishingCog.sail`; removed, it's green. A full scan
  found **no other** same-cog collisions in the bot.
- **Generated data** — regenerated `dashboard/data/dashboard.json`, `botsite/data/site.json`,
  `botsite/site/data.js` so the displayed alias lists no longer show `!dock` under `sail` (command
  *names* unchanged, so no structural-drift surface moved; timestamp/changelog churn is volatile).

## Verification

_(pending final run — see close-out)_

**Recovery:** merge → Railway auto-redeploys `worker` → bot back within minutes (the merge IS the
deploy; no manual restart — Q-0193).
