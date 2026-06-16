# Session — Reconcile command counts (website breakdown + bot status embed)

> **Status:** `in-progress`

## Origin

Owner (2026-06-16): a screenshot showed the live bot reporting **"Commands 183 / Loaded cogs 43"**
while the website `/commands` showed **"300 commands / 41 cogs"** — *"any idea why the bot and the
website both lost a different number of commands … Yes you can do both [fixes], it currently says 275
prefix and 25 slash on the website."*

## Diagnosis (root cause)

Neither lost commands — they counted **different surfaces**:

- Bot embed (`services/webhook_reporter.py`) used `len(bot.commands)` = **top-level prefix only**
  (183 = 182 in cogs + 1 in `bot1.py`). It omits group **subcommands** and **slash** commands (those
  live in `bot.tree`).
- Website AST scan counted **all** command methods: 182 top-level prefix + 93 subcommands + 25 slash =
  300.
- Cogs: 43 (bot `len(bot.cogs)`, incl. listener/task cogs) vs 41 (website classes-with-commands, which
  also wrongly listed the `PlatformCommandsMixin` mixin as a cog).

## What shipped (both fixes, as asked)

1. **Website** (`scripts/scan_commands.py` + `/commands`): the stats now break commands into
   **top-level prefix (183) · subcommands (93) · slash (25)**, with a note that the bot's status counts
   only the 183 top-level (`len(bot.commands)`). Added `is_cog` detection so mixins/modules no longer
   inflate the cog count (now **40 real cogs**), and the scanner now also picks up `bot1.py`'s one
   module-level command — so **top-level prefix = 183 exactly matches the bot.** Mixin/module rows are
   tagged in the UI.
2. **Bot** (`services/webhook_reporter.py`): the "Bot Online" embed's **Commands** field now reports the
   true total via `bot.walk_commands()` + `bot.tree.walk_commands()` — e.g. `301 (276 prefix · 25
   slash)` — instead of the misleading top-level-only `len(bot.commands)`. Best-effort / never-raises
   (the `getattr` pattern already used in `command_descriptions.py`).

## Verification

- `check_quality.py --full` → **green (10153 passed, 37 skipped)**; ruff/black/isort/mypy clean.
- `check_architecture --mode strict` → exit 0; `check_docs --strict` → green.
- scanner summary: cogs 40 · commands 301 · top-level prefix **183** · subcommands 93 · slash 25.
- `/commands` renders the reconciled breakdown (TestClient → 200).

## 💡 Session idea (Q-0089)

**One source for "commands by surface."** The bot embed and the website now both compute
prefix/subcommands/slash, but independently. Exposing a single helper (or the existing
`command_surface_ledger`) as the one "count the command surface" source would stop the bot and
dashboard drifting apart again — the concrete next step of the earlier "reconcile AST scan vs runtime
ledger" idea.

## ⟲ Previous-session review (Q-0102)

Previous: the **`/commands` explorer (#972)**. Did well: clean AST scanner, good page, full tests. What
this session exposed: it surfaced a single "300 commands / 41 cogs" without explaining it counts a
*different surface* than the bot's status — which immediately confused the owner. Lesson (now applied):
when a dashboard number mirrors one the user already sees elsewhere, show the breakdown and **name the
metric**, so the two reconcile at a glance instead of looking contradictory.

## Documentation audit (Q-0104)

- The `/commands` page now self-documents the count methodology in its intro. `check_docs --strict`
  green. A status-embed under-report (not a user/runtime bug) → no bug-book entry; root cause + fix
  live here. `current-state.md` In-flight names no open PRs (convention); the merge-time reconciliation
  (Q-0124) folds this PR into the ledger.
