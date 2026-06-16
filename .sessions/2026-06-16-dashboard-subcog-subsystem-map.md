# 2026-06-16 — dashboard: map sub-cogs to their parent subsystem

> **Status:** `in-progress` — born-red per Q-0133; flipped to `complete` as the deliberate
> final step. Scanner + data + tests only (no `disbot/` runtime, no dashboard templates/app).

## What I'm about to do

Continue the bot's main website (`dashboard/`), non-conflicting with the owner's active sessions
(website OAuth + editors; the control-API write side already merged #993). Execute my own filed idea
(`docs/ideas/dashboard-subcog-parent-subsystem-2026-06-16.md`, Q-0089 from #990):

The integrity guard (#990) *allow-lists* the real cogs whose `subsystem` doesn't resolve to a
registry key, but several genuinely **belong** to a parent subsystem — so on `/commands` they render
with a generic 🧩 + no routing key. Add an explicit cog-class→subsystem override map in
`scan_commands.py` so they inherit the parent's registry identity (emoji / name / routing key), and
**shrink the guard's allow-list** to the truly-unregistered few.

**Verified correct against the registry:** `btd6` (display "BTD6 Assistant") and `rps_tournament`
(display "Rock Paper Scissors") exist. Map the unambiguous ones:

- `BTD6EventsCog` / `BTD6OpsCog` / `BTD6ReferenceCog` / `BTD6StrategyCog` → `btd6`
- `RockPaperScissorsCog` (in `rps_tournament_cog.py`) → `rps_tournament`

Leave `ParagonCog` / `SetupCog` / `HermesCog` allow-listed (parent intent is genuinely ambiguous —
Paragon *could* be btd6, Setup is the hub-less wizard, Hermes is ops; defer to owner intent).

Touches only `scripts/scan_commands.py` · `scripts/check_dashboard_data.py` (allow-list) ·
`dashboard/data/dashboard.json` (regenerate) · `tests/` — guaranteed non-conflicting with the
control-API + OAuth/editor sessions. No template change needed (the existing `sysmap` join resolves
the header once the subsystem string is correct).

## Status checklist

- [ ] `_COG_SUBSYSTEM_OVERRIDES` in `scan_commands.py` + test
- [ ] shrink `_UNREGISTERED_COG_ALLOWLIST` to {Paragon, Setup, Hermes} + guard still green
- [ ] regenerate `dashboard.json`; verify 5 cogs now resolve + `/commands` renders
- [ ] dashboard smoke test + `check_quality --check-only`
- [ ] idea file update (5 done, 3 deferred) + session enders + flip card `complete`
