# Command-reachability gap list — 2026-06-23

> **Status:** `audit` — the per-cog gap list emitted by
> `scripts/check_command_reachability.py` (discoverability audit Session 1). Source
> of truth is the **live checker** + the baseline in
> `tests/unit/invariants/test_command_reachability.py`; this doc is the dated
> write-up + disposition. **Sector:** S1 — Bot product.

## What the guard checks

The per-command help-reachability guard (`scripts/check_command_reachability.py`)
classifies every **prefix** command (the `!help` text tree only models prefix
commands) as:

- **reachable** — some owning subsystem is *homed* under a top-level hub **and**
  has a help-discovery path (so the command appears in a `!help` command-list or a
  homed panel);
- **exempt** — operator/owner-tier (decorator or a runtime `is_administrator_member`
  / owner gate), Discord-hidden, an `internal` subsystem, the `help` root, or
  allowlisted in `architecture_rules/command_reachability_exceptions.yml`;
- **gap** — a **member-tier** command whose cog maps to **no homed + discoverable
  subsystem**, so it is not auto-listed under any hub.

Owning subsystems are resolved the way the live help layer does
(`cogs.help_cog._cog_for_subsystem`): the cog *class name* normalises to a
subsystem (`cog_name_to_subsystem`), **or** one of the cog's command names/aliases
is a subsystem `entry_point`.

## Run summary (2026-06-23, `e8b25e6` baseline)

```
214 prefix commands  →  75 reachable · 138 exempt · 1 GAP   (was 2 — !btd6strat fixed in PR #1372)
```

The static guard initially flagged **8** member-tier commands across 6 orphan cogs
(cog class maps to no registered subsystem → not in any auto-generated help
command-list). **Verifying each against source** (the rubric accepts a *buttonized
panel action* as reachable, and Q-0120 says a checker that fights the evidence is the
checker's bug) split them: **5 were already reachable via a hub-panel button / panel
help-text** → allowlisted with a source citation; **2 were small omissions fixed by
adding a surface** (`!cbrecord` — one line in the creature panel text, Session 1;
`!btd6strat` — a **Strategy button on `BTD6PanelView`**, PR #1372 / fleet unit U4),
then allowlisted; **1 is genuinely unsurfaced** → the baseline (`!temproles`, routed
to fleet unit U2).

### Exempt — operator-gated (allowlisted, verified by reading the cogs)

`!setup` (owner/admin/delegated, gated inside the command) · `!btd6ops`
(administrator-only data-ops, `is_administrator_member` per subcommand).

### Exempt — reachable via a panel button / panel text (allowlisted, source-verified)

| Command | Surfaced by (verified 2026-06-23) |
|---|---|
| `!btd6events` | BTD6 hub panel **"Live Events"** button (`views/btd6/panel.py`). |
| `!btd6ref` | BTD6 hub panel **"Towers" / "Heroes" / "CT"** buttons. |
| `!paragon` | BTD6 hub panel **"Paragon"** button. |
| `!cbattle` | Creature panel **help text** (`creature_cog.build_help_menu_view`). |
| `!cbattletop` | Creature panel **help text**. |
| `!cbrecord` | Creature panel **help text** — the missing line, added in Session 1. |
| `!btd6strat` | BTD6 hub panel **"Strategy"** button — added in PR #1372 (U4); opens `strategy_browse.build_browse_embed`. |

### The 1 genuine gap (the baseline — `test_command_reachability._BASELINE`)

Member-tier commands verified **not** surfaced by any homed help-list, panel button,
or panel text. Recorded (ratcheted — *new* gaps fail) as the per-cog follow-on work.

| Cog | Command | Why it's a gap (verified) | Suggested follow-on |
|---|---|---|---|
| `role_grants_cog.py` | `!temproles` | `RoleGrantsCog` maps to no subsystem; the member view of one's temp roles isn't surfaced in any roles panel. | **Fleet unit U2 (roles):** home under the `role` subsystem or surface via the roles panel + allowlist. |

## How to clear an entry

When a follow-on session homes one of these cogs (adds `parent_hub` + a
`build_help_menu_view` hook or a `*menu` entry-point) or surfaces its command via a
panel button, the gap disappears and `test_baseline_has_no_stale_entries` fails until
the matching tuple is removed from `_BASELINE` — so this ledger and the test stay in
lock-step. Re-run `python3.10 scripts/check_command_reachability.py` to confirm.

## Notes / caveats

- The guard is **warn-first and disposable** (Q-0105). It cannot see hand-wired
  hub-panel buttons (only the registry path), so a flagged command *may* already be
  reachable via its hub panel's text/buttons — confirm in a live guild before homing.
  That ambiguity is exactly why these are *recorded* (not auto-fixed) and left to a
  per-cog session that can verify live.
- `SUBSYSTEMS` has **41** registered entries (not the "70" the staging brief
  estimated — the brief counted hub_groups/capabilities loosely; the registry is the
  authority). Noted here so a later session doesn't chase the discrepancy.

## Related

- `scripts/check_command_reachability.py` — the checker.
- `tests/unit/invariants/test_command_reachability.py` — the warn-first ratchet.
- `tests/unit/invariants/test_discoverability.py` — the subsystem-level sibling.
- `docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md` — the audit mandate + per-cog rubric.
