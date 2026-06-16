# Readiness/audit maps should cite a regeneration command, not freeze counts

> **Status:** `ideas` — captured 2026-06-13 (Q-0089 session idea, from the P0-3 settings
> pointer-lane foundation session). Not a plan; not approved. Source + merged PRs win.
>
> **⚙ Mechanism SHIPPED for binding docs (2026-06-16, PR #964, Q-0151); the readiness-map widening
> was investigated and DROPPED as not-worth-it.** The architecture-review count-citation guard built
> this mechanism in `check_docs.py` (`inventory_count_flags` / `print_inventory_count_report`): a
> **soft** warning when a bare inventory count lacks a regen citation (`scripts/*.py`), a `generated`
> marker, or `<!-- count-ok -->`. Scope: **`binding` docs** (clean baseline, 0 flags).
>
> **Why widening to `production-readiness/*` was dropped (verified 2026-06-16):** 8 of the 10
> `production-readiness/*` docs are badged **`audit`** — dated point-in-time snapshots where a frozen
> count is *correct by design*; flagging them would be pure noise (the same reason ADRs/historical docs
> are exempt). The one *live* map that matters
> (`settings-bindings-provisioning-production-readiness-map`) **already self-cites**: its top line is
> `python3.10 scripts/settings_lane_matrix.py (65 settings / 17 bindings, not the 36/13 below)` — the
> exact cite-the-regen-command convention this idea asked for, already applied by hand. So there is no
> valuable widening to do; the convention lives on as good practice for any *new* live readiness map.
> **This idea is effectively resolved** (mechanism shipped where it adds value; the rest is moot).

## The gap

The `docs/planning/production-readiness/*` maps are dated audit snapshots that embed
**hard inventory counts** ("36 registered `SettingSpec` … 13 `BindingSpec`"). Agents read
those numbers as ground truth when picking up a hardening track. But the counts rot the
moment a feature lands: the settings readiness map was **one day old** when the P0-3 session
ran `scripts/settings_lane_matrix.py` and found the real inventory was **65 settings / 17
bindings** — #774 (logging v1) and #775 (welcome/counters) had shipped after the audit. The
map wasn't wrong when written; it became wrong silently, and there's no signal that it has.

This is the same drift class the living-ledger checker (`check_current_state_ledger.py`) and
the "source wins over dated docs" rule already fight elsewhere — but the readiness maps are
*the* docs most prone to it (they're inventory-heavy and frozen by design) and have no guard.

## The idea

A lightweight convention, ideally enforced by a `check_docs` soft rule:

- Any `production-readiness/*` (or `audits/*`) doc that states an inventory count must place
  the **regeneration command** beside it — e.g. "65 settings / 17 bindings (live:
  `python3.10 scripts/settings_lane_matrix.py`)". The number becomes *citable + reproducible*
  instead of a silent claim.
- The existing inventory tools already exist to back this: `settings_lane_matrix.py` (this
  session), `command_surface_dump.py` (#732). The convention just makes maps *point at them*.
- Soft-ratchet only (warn, don't block) — readiness maps are judgment docs, not generated
  artifacts; the goal is a freshness pointer, not forcing every count to be machine-generated.

## Why I believe in it

I watched it fail in real time: a careful, recent audit was already misleading a hardening
session on its headline numbers, and only an ad-hoc tool run surfaced the truth. The fix is
cheap (a one-line citation per count) and compounds — every future map that cites its
regen command stays trustworthy as features land underneath it. It's the
one-fact-one-home / source-wins principle applied to the doc class that needs it most.

## Adjacent (not this idea)

The P0-3 session also built `test_pointer_lane_ledger` (a CI ratchet) and noted a future
**authoring-time** nudge (a PostToolUse warning on `input_hint="channel"/"role"` scalar
settings, pointing at the binding lane). Those guard the *pointer-lane* class specifically;
this idea is about *readiness-map freshness* generally. Keep them separate.
