# Session — settings reverse-parity invariant (complete the declared ⇔ consumed bijection)

> **Status:** `in-progress`

## What I'm about to do

Second slice of the same dispatch run that shipped P1-3 (#917, merged). #917 added settings
**forward** parity — every declared `SettingSpec` has a runtime consumer. This adds the **reverse**
direction: every literal `resolve_value`/`resolve_setting(g, subsystem, name)` read must target a
*declared* setting, so the settings lane becomes a true **bijection** (declared ⇔ consumed).

The gap it closes is a real silent-bug class: a typo'd or stale read —
`resolve_value(g, "welcom", "enabld", default)` — never matches a written key, so it resolves to the
**fallback forever**, an invisible always-default bug no test catches today. This was the Q-0089
session idea from the #917 close-out; building it now rather than orphaning it (it reuses the same
AST walk in `test_settings_declared_vs_consumed_parity.py`). Holds today: 0 violations across 48
literal reads.
