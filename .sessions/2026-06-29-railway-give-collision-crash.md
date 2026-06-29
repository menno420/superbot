# 2026-06-29 — PROD hotfix: `give` command collision crashed boot (bot offline)

> **Status:** `complete`

**Incident:** Railway emailed repeated "Deploy Crashed for worker in reliable-grace". The
bot was offline — build succeeded but the process aborted at startup in a crash loop.
Owner-directed live session. ⚑ **Self-initiated:** the broader cross-cog duplicate-command
guard (below) goes beyond the literal "ban give" ask — added as root-cause prevention for the
whole collision class.

## Root cause (confirmed from Railway logs)

```
❌ Failed to load cogs.mining_cog: CommandRegistrationError:
   The command give is already an existing command or alias.
→ Subsystem 'mining' has no loaded commands — marking INTERNAL
→ entry_point 'minemenu'/'mine' declared by 'mining' is not a loaded command
→ Identity-contract findings | total=2 | fatal=2 | STRICT=on | abort=yes
→ Identity-contract: STRICT mode aborting startup.
```

Top-level command-name collision in the global namespace. **Provenance traced via git
(unshallowed the clone):** mining's admin-only `give` has existed since the **initial commit**
(`330c7716`, 2025-08-10) — never PR'd. **PR #1541** (`839d6f9`, `feat(economy): !give / !pay`,
merged ~2 days ago) added a *second* global `give`, turning a dormant duplicate into a
boot-crash. economy loads first and wins; `mining_cog` then fails `add_cog` → its entry points
(`mine`, `minemenu`) vanish → STRICT identity-contract aborts boot. Crash loop, never reaches
the gateway → offline. A full scan confirmed `give` was the **only** collision (1 of 333
top-level tokens).

## What changed (owner directive Q-0211 — `give` retired surface-wide)

Two escalating in-session owner answers: (1) remove mining's `give` entirely; (2) "remove
**every** give command and make sure none is ever added again" → delete all three + a hard ban.

- **`disbot/cogs/mining_cog.py`** — removed the admin `give` command.
- **`disbot/services/mining_workflow.py`** — removed its now-orphaned only caller
  `admin_grant` (+ `__all__` entry). `update_mining_item` (16+ callers) and `admin_reset` kept.
- **`disbot/cogs/economy_cog.py`** — removed the `!give`/`!pay` peer coin-transfer command
  entirely (owner chose "delete it all, incl. feature"). Kept `economy_service.transfer` — it
  **predates** the feature (`b53647aa`), is the canonical audited balance-move primitive
  referenced as a precedent in 6+ files, and is no longer user-invocable; ripping it out would
  be over-reach beyond removing the give *feature*.
- **`disbot/cogs/karma_cog.py`** — renamed the `!karma give` subcommand → **`!karma add`**
  (function `karma_give` → `karma_add`; docstrings updated). Internal `karma_service.give`
  (the grant logic) is a service method, not a command — out of scope, kept.
- **Guard (enforce, don't exhort — Q-0194/Q-0132):** `tests/unit/invariants/test_extension_integrity.py`
  gains two CI checks, importlib-only (no DB/Discord):
  - `test_no_banned_command_tokens_anywhere` — fails if any command/alias named `give` is ever
    re-added, at any nesting depth (`BANNED_COMMAND_TOKENS = {"give"}`).
  - `test_no_duplicate_top_level_command_names_across_cogs` — the root-cause guard: catches
    **any** cross-cog duplicate top-level command name/alias pre-merge. The runtime
    `command_surface_ledger` only sees duplicates *after* all cogs load (which a collision
    prevents), so it structurally could not catch this; the static check does.
- **Docs:** `docs/subsystems/karma.md` + `docs/help-command-surface-map.md` (`karma give` →
  `karma add`); router **Q-0211** records the decision + scope boundary.
- **Generated data:** regenerated `dashboard/data/dashboard.json`, `botsite/data/site.json`,
  `botsite/site/data.js` (command surface changed: 458 commands) — the freshness checkers
  required it.

## Verification

- `python3.10 scripts/check_quality.py --full` → green (lint + mypy + 12989 tests; the 4
  dashboard-freshness failures were fixed by regenerating the export).
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0 (no new violations).
- Scans: 0 commands named `give` remain; 0 top-level command collisions.
- The new guards fail loudly if `give` returns or any cog pair collides.

**Recovery:** merge → Railway auto-redeploys `worker` → bot back within minutes (the merge IS
the deploy; no manual restart — Q-0193).

## 💡 Session idea (Q-0089)

Extend the identity-contract STRICT abort to **degrade, not die, on a single cog's load
failure**: if one cog fails to load but the rest are healthy, boot the bot with that subsystem
marked DEGRADED (and a loud operator webhook) instead of aborting the whole process. Today one
cog's `CommandRegistrationError` takes the *entire* bot offline — a blast radius far larger
than the fault. A partial-availability boot would have kept 54/55 cogs serving while this was
fixed. (Idea only; STRICT-abort exists for good reasons — gate behind an env flag + per-cog
criticality tiers. Worth an `docs/ideas/` file if it survives owner review.)

## ⟲ Previous-session review (Q-0102)

The session that shipped **PR #1541** (`!give`/`!pay`) introduced a boot-crashing collision: it
added a top-level `give` without grepping for an existing global `give` (mining's, present since
genesis). The **Q-0200 exact-name guard is same-module only**, so it could not catch a
*cross-cog* clash — a real gap. Compounding it, the next session (#1542, Farm leaderboard)
merged on top of an already-crash-looping `main` without noticing prod was down. **System
improvement (shipped this session):** the cross-cog duplicate-command CI guard closes the
exact hole — what Q-0200 does within a module, `test_no_duplicate_top_level_command_names_across_cogs`
now does across all cogs, so this class fails at CI instead of at boot. The deeper lesson —
*nothing watches whether a merge actually stayed up in prod* — is the Q-0089 idea's territory
(degrade-don't-die) and a candidate for a post-merge prod-health check.

## 📋 Doc audit (Q-0104)

Owner decision recorded in router (**Q-0211**). Living docs with command refs updated
(karma.md, help-command-surface-map.md). No `give`/`pay` command refs remain in living docs
(historical planning/ideas docs left as dated snapshots). Ledger was in sync at session start;
this PR will be picked up by the next reconciliation pass (#1560).
