# Cogs declare their subsystem (kill the dashboard's name-derivation guesswork)

> **Status:** `ideas` — captured 2026-06-16 (session idea, Q-0089, from the sub-cog mapping #995).
> Source + merged PRs win.

## The gap

The dashboard derives each cog's subsystem key from its **class name**
(`scan_commands._cog_to_subsystem`: `EconomyCog` → `economy`). That guess is wrong whenever the class
name isn't the registry key, so it needs two hand-maintained patches stacked on top:

1. an **acronym table** (`BTD6Cog` → `btd6`, #988), and
2. an explicit **override map** (`BTD6EventsCog` → `btd6`, `RockPaperScissorsCog` → `rps_tournament`,
   #995),

plus a third hand-maintained **allow-list** in `check_dashboard_data.py` for the cogs that still don't
resolve (`ParagonCog` / `SetupCog` / `HermesCog`). Three curated lists, all keyed on class name, all
drifting independently — and #995 still couldn't resolve 3 cogs because their parent is genuinely
ambiguous *from the class name alone*.

## The idea

Replace the name-derivation + override map with an **authoritative subsystem declaration** the scanner
reads, so the dashboard stops guessing. Two candidate sources (pick by what's least invasive):

- **A cog class attribute** — e.g. `class BTD6EventsCog(...): SUBSYSTEM = "btd6"`. The scanner reads the
  literal via AST (it already AST-parses every cog). One line per cog, unambiguous, lives next to the
  code it describes. Resolves Paragon/Setup/Hermes too (the owner/author states intent once).
- **The command-surface ledger / registry back-reference** — if `core/runtime/command_surface_ledger.py`
  (or the registry's `entry_points`) already maps commands → subsystem authoritatively, the scanner
  could join through it instead of the class name. No cog change, but only as reliable as that mapping's
  coverage of *sub-cog* commands (entry_points are top commands, so this may not cover sub-cogs).

Prefer whichever is authoritative for **every** cog including sub-cogs. The payoff: delete the override
map + shrink the allow-list to genuinely-unregistered cogs, and new cogs render correctly with **zero**
dashboard-side maintenance.

## Why it's worth having

- Eliminates three drifting hand-maintained lists (acronym table · override map · allow-list).
- Makes a cog's subsystem **self-describing** — the same robustness win as the registry itself.
- Resolves the 3 cogs #995 had to defer (their author states the intent in one place).

## Disposition

Decided-lane but needs a design choice (class attribute vs. ledger join) + touches `disbot/` cog
classes if the attribute route is taken (a focused, low-risk change). **Structure into a small plan
when the dashboard lane next has runtime capacity**; confirm the Paragon/Setup/Hermes parent intent as
part of it. → relates `scripts/scan_commands.py` · `core/runtime/command_surface_ledger.py` ·
`utils/subsystem_registry.py`.
