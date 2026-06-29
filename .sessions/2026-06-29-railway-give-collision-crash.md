# 2026-06-29 — PROD hotfix: `give` command collision crashed boot (bot offline)

> **Status:** `in-progress`

**Incident:** Railway emailed repeated "Deploy Crashed for worker in reliable-grace". The
bot was offline — build succeeded but the process aborted at startup in a crash loop.

## Root cause (confirmed from Railway logs)

```
❌ Failed to load cogs.mining_cog: CommandRegistrationError:
   The command give is already an existing command or alias.
→ Subsystem 'mining' has no loaded commands — marking INTERNAL
→ entry_point 'minemenu'/'mine' declared by 'mining' is not a loaded command
→ Identity-contract findings | total=2 | fatal=2 | STRICT=on | abort=yes
→ Identity-contract: STRICT mode aborting startup.
```

Top-level command-name collision in the global namespace: **PR #1541** added the economy
peer-transfer `@commands.command(name="give", aliases=["pay"])` (`economy_cog.py`), which
collides with a pre-existing admin-only `give` in `mining_cog.py`. economy loads first and
wins; `mining_cog` then fails `add_cog` → its declared entry points (`mine`, `minemenu`)
vanish → the STRICT identity-contract check aborts the boot. Crash loop, never reaches the
gateway → bot offline. A full scan confirmed `give` is the **only** collision (1 of 333
top-level command tokens).

## What I'm about to do

1. **Remove** the mining admin `give` command + its now-orphaned `mining_workflow.admin_grant`
   (owner decision this session: remove, not rename — it was a never-reachable-by-players admin
   tool squatting the global `give` verb). economy keeps `give`/`pay`.
2. **Durable guard (Q-0194 friction→guard):** extend `test_extension_integrity.py` to detect
   duplicate top-level prefix command names/aliases across all cogs at CI time — so this class
   of collision can never silently crash boot again (it currently only surfaces at runtime, too
   late, after `add_cog` has already raised).
3. Verify, flip this card to `complete`, merge → Railway auto-redeploys → bot back.
