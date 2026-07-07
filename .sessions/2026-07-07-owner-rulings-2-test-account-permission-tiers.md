# 2026-07-07 — Owner rulings #2 (test-driver account + permission-tiered operation)

> **Status:** `complete`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` (restarted from main after #1792) · **PR:** #1793
> **Continues:** `.sessions/2026-07-07-owner-rulings-followup.md` (same conversation)

## What happened

Two more live owner rulings recorded + one small owner-directed live-bot slice shipped:

1. **Q-0245 — the owner's second account as a declared elevated test actor.** The owner asked to
   "hardcode that user ID into the bot so it has free reign to test moderator functions." Shipped
   the better-implementation equivalent (Q-0014 clause): a comma-separated **`EXTRA_OWNER_USER_IDS`**
   env var — `disbot/config.py` gains `_parse_extra_owner_ids` (boot-safe: malformed tokens dropped,
   never crash) + a widened `is_platform_owner()` (the documented single-source owner predicate every
   governance/mutation/setup/view gate routes through), and `disbot/bot1.py` gains a thin
   `_SuperBot.is_owner` override delegating to the same predicate so the discord.py command-access
   bypass seam extends identically. **Empty default = zero behavior change**; the owner sets the
   variable (Railway + local test bot) with his second account's id. 8 new test pins in
   `tests/unit/test_platform_owner_override.py`. Companion C's lane-B "no second account" known-gap
   marked RESOLVED. ⚑ flagged: ids in the set are full-power operator credentials in every guild.
2. **Q-0246 — permission-tiered operation (Full vs Lite).** Server owners choose the full bot
   (administrator) or a Lite tier (games + no-elevated-permission features) — the failsafe for
   servers that won't grant admin. Folded as canonical plan **§11b A-22** + rider **R-18**
   (manifest-declared per-feature Discord permissions → derived invite tiers + visible degradation),
   extending Q-D5's DEGRADE from failure posture to a supported product tier (F-2 row rider added).

Checks: `check_architecture --mode strict` 0 errors · `check_docs --strict` ✓ · `check_amendments` ✓
· targeted pytest file 45/45 · full `check_quality --full` run before the flip push.

## Session enders

Same conversation as the main consolidation session — the Q-0089 idea, Q-0102 review, Q-0104
audit, and Q-0015 grooming live in `.sessions/2026-07-07-rebuild-idea-consolidation.md`. Nothing
from this follow-up lacks a durable home (router Q-0245/Q-0246; plan A-21/A-22 + R-18; companion C;
code + tests shipped in this PR).
