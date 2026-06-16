# Dashboard cog↔registry coverage check

> **Status:** `ideas` — captured 2026-06-16 (session idea, Q-0089). Small, safe, decided-lane
> (dashboard tooling). Source + merged PRs win.

## The gap (hit while building the `/commands` management surface)

The dashboard joins each scanned cog to the SUBSYSTEMS registry by its `subsystem` key
(`scripts/scan_commands.py` `_cog_to_subsystem`) to show the cog's emoji / display name and its
**routing key**. When that key doesn't resolve to a registry entry, the join silently degrades —
the cog renders with the generic 🧩 + its raw class name, and its routing-state panel can't say
which subsystem it routes on. This session fixed one whole class of it (acronym cogs:
`BTD6Cog`→`btd6`, `AICog`→`ai`, `XPCog`→`xp` — they were `b_t_d6`/`a_i`/`x_p` and matched nothing),
but the failure was **invisible** until someone eyeballed the page. ~10 of 42 scanned cog entries
still don't resolve (the `bot1.py` module, mixins, and `hermes`/`paragon`/`setup`/`rps`/the BTD6
sub-cogs — some legitimately have no registry entry, some may be real drift).

## The idea

A tiny **coverage self-check** over the export: list every scanned cog whose `subsystem` does **not**
resolve to a registered subsystem, split into *expected* (an allow-list: `(bot1.py)`, mixins, known
hub-less cogs) vs *unexpected* (real drift the registry should cover). Surface it as either:

- a `--check` mode on `scripts/export_dashboard_data.py` (prints the unresolved set, non-zero exit on
  an *unexpected* miss), or
- a stdlib unit test `tests/unit/scripts/test_scan_commands.py` that asserts the unexpected-miss set is
  empty against a small curated allow-list.

So a future cog rename / a new acronym cog / a registry key change that breaks the join **fails a
check** instead of silently giving that cog a degraded dashboard card.

## Why it's worth having

- Pure stdlib, read-only, no bot change — same disposable-tooling lane as the other `scan_*` scripts
  (Q-0105 provenance header applies).
- Turns an invisible degradation into a caught one — the dashboard's correctness depends on this join
  for two surfaces now (`/commands` header + routing state) and more as the management surface grows.
- Cheap: the allow-list is short and the resolve logic already exists.

## Disposition

**SHIPPED 2026-06-16 — PR #990**, broader than the original sketch: `scripts/check_dashboard_data.py`
validates the whole exported `dashboard.json` — **cog→subsystem resolution** (this idea, with the
curated allow-list of legitimately-unregistered cogs) **plus** count integrity (`meta.counts.*` vs
actual) and required-field presence. A unit test validates the freshly-built export so a new
unregistered cog / broken join / count drift **fails CI**. → `scripts/check_dashboard_data.py` ·
`tests/unit/scripts/test_check_dashboard_data.py`.
