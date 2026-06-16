# Dashboard: map sub-cogs to their parent subsystem

> **Status:** `ideas` — captured 2026-06-16 (session idea, Q-0089, from the integrity guard #990).
> Small, decided-lane (dashboard tooling). Source + merged PRs win.

## The gap (surfaced while building the integrity guard)

`scripts/check_dashboard_data.py` (#990) allow-lists the real cogs whose `subsystem` doesn't resolve
to a SUBSYSTEMS registry key: `BTD6EventsCog`/`BTD6OpsCog`/`BTD6ReferenceCog`/`BTD6StrategyCog`,
`ParagonCog`, `RockPaperScissorsCog`, `SetupCog`, `HermesCog`. The allow-list keeps them from
failing the guard — but it doesn't *fix* their dashboard rendering. Several of them genuinely **belong
to a parent subsystem**:

- the four `BTD6*Cog` sub-cogs are part of the **`btd6`** subsystem (the main `BTD6Cog` resolves);
- `ParagonCog` is BTD6-adjacent (arguably `btd6`);
- `RockPaperScissorsCog` lives in `rps_tournament_cog.py` → the registry key is **`rps_tournament`**
  (a class-name vs key mismatch, not a missing subsystem).

Because their `subsystem` string doesn't match a registry key, the `/commands` page renders them with
the generic 🧩 icon + the raw class name + no routing key — a degraded card for ~7 of 42 cogs.

## The idea

Add a small, explicit **cog-class → parent-subsystem map** to `scripts/scan_commands.py` (or a thin
override table the exporter applies), e.g.:

```python
_COG_SUBSYSTEM_OVERRIDES = {
    "BTD6EventsCog": "btd6", "BTD6OpsCog": "btd6",
    "BTD6ReferenceCog": "btd6", "BTD6StrategyCog": "btd6",
    "RockPaperScissorsCog": "rps_tournament",
    # ParagonCog / SetupCog / HermesCog: decide per owner intent (btd6? internal?)
}
```

so those cogs inherit their parent's registry identity (emoji / display name / **routing key**) on the
dashboard, and the `check_dashboard_data` allow-list shrinks to only the *truly* unregistered cogs
(`HermesCog`, `SetupCog` — if those stay hub-less). An explicit override table is honest (it's a small
curated map, reviewed) and beats trying to infer the parent from the file name.

## Why it's worth having

- Fixes a visible degradation on the bot's **main website** for the whole BTD6 + RPS surface.
- Read-only, stdlib, dashboard-only — same disposable-tooling lane (Q-0105). No bot change.
- Tightens the integrity guard: a smaller allow-list means more real coverage.

## Disposition

Decided-lane, small → **execute when the dashboard lane next has capacity**; pairs naturally with the
next `/commands` rendering pass. Confirm the `ParagonCog`/`SetupCog` parent intent with the owner (or
leave them allow-listed). → relates `scripts/scan_commands.py` · `scripts/check_dashboard_data.py` ·
`dashboard/templates/commands.html`.
