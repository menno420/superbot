# 2026-07-07 — Owner rulings #2 (test-driver account + permission-tiered operation)

> **Status:** `in-progress`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` (restarted from main after #1792)
> **Continues:** `.sessions/2026-07-07-owner-rulings-followup.md` (same conversation)

## What is about to happen

Two more live owner rulings to record + one small owner-directed live-bot slice:

1. **Q-0245 — the owner's second account becomes a declared elevated test actor.** Owner asked to
   "hardcode that user ID into the bot so it has free reign to test moderator functions." Safer
   equivalent shipped: env-declared (`EXTRA_OWNER_USER_IDS`), never source-hardcoded — extends
   `config.is_platform_owner()` (the canonical owner seam) and `bot.is_owner()` (the command-access
   bypass seam) together. Zero behavior change until the owner sets the variable. + router entry,
   plan §11b A-21, companion C lane-B update.
2. **Q-0246 — permission-tiered operation.** Server owners choose Full (administrator) vs Lite
   (games + no-elevated-permission features); features degrade visibly when their permission is
   absent. → router entry, plan §11b A-22 + rider R-18 mint, Q-D5 row rider.

## Close-out

_(to be written at close)_
