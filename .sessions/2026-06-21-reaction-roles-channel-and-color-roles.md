# 2026-06-21 — Reaction roles: channel picker + auto-created colour/gradient roles

> **Status:** `in-progress` — born-red HOLD (Q-0133). Owner-directed follow-up to #1234
> (Q-0191 → merge immediately on green). New branch (not `claude/lucid-carson-qsn1gc`, which
> just merged and is contested by the parallel creature-PvP session — Q-0014: branch identity
> is not significant).

> **Run type:** `manual`

## What I'm about to do

Three owner-requested enhancements to the role-menu builder:

1. **Choose the post channel** — a 📍 Channel picker on `RoleMenuBuilder` so a menu can be posted
   to a dedicated reaction-roles channel, not just the channel the panel is open in.
2. **Auto-create colour roles** — pick colours that don't exist yet as roles and have the bot
   create them in one smooth action, then add them to the menu. Routed through the audited
   `RoleLifecycleService` (the only sanctioned `create_role` caller), reusing a same-named role
   when one already exists.
3. **Gradient / holographic roles** — discord.py 2.7.1 supports `secondary_colour`/`tertiary_colour`
   on `create_role`/`Role.edit`. Discord gates the *Enhanced Role Styles* perk on **3 applied
   server boosts**, so the gradient UI is offered only when `guild.features` shows the perk, with a
   solid-colour fallback (and a caught-400 belt-and-suspenders).

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.
