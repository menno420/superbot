# Phase 2 — Completion readiness

> **Status:** `historical` — a **historical Phase-2 snapshot; superseded as
> a live next-work queue.** PR-10 consistency diagnostics and later setup work shipped
> after this snapshot. Preserve this file for blocker-name/doc-test and migration
> history, but use `docs/current-state.md`, subsystem folios, source, and active
> initiative trackers for current status. The platform-consistency ledger's contract
> shapes remain useful, but its implementation-status cells also require source
> verification.

This page captures **what is done**, **what is open**, and **what
should NOT start yet** as Phase 2 reaches completion.  It exists to
help the next contributor avoid:

* re-deriving status from `git log`,
* duplicating in-flight runtime work,
* starting a large UI / settings phase before the substrate is stable.

---

## Done on `main`

| PR | Title | Notes |
|---|---|---|
| #70 | Phase 0/1 ownership protocols + roadmap |
| #71 / #72 | Phase 2a unified resource runtime |
| #73 / #74 | Phase 2b subsystem bindings + circular-import hotfix |
| #75 | Platform consistency ledger + stale-doc classification |
| #76 | Guild teardown cleanup; binding cleanup primitive split |
| #77 | Feature flag evaluator foundation (Phase 2d) |
| #78 | Rollout mutation pipeline + feature flag audit |
| #79 | Central config arbitration (`ConfigReadResult`) |
| #80 | Integration: land #77 + #78 + #79 onto `main` |
| #81 | Binding backfill dry-run + reconciliation + checkpoints (migration 026) |
| #82 | Binding backfill write phase (idempotent apply, advisory lock) |
| #83 | `bindings.primary` canary support via arbitration accessors |
| #84 | Participation storage + cache foundation (migration 027) |
| #85 | Integration: land #82 + #83 + #84 onto `main` |
| #86 | Phase 2.9: participation mutation pipeline + XP opt-out proof (migration 028) — merged 2026-05-18 |
| #87 | Phase 2 completion-readiness punch list — merged 2026-05-18 |

Migration ladder on `main` after PR #86: `022` → `028`.

## Open right now (historical snapshot — not current)

| PR | Title | State |
|---|---|---|
| **PR-10** | **Phase 2 PR-10: Unified Consistency & Readiness Diagnostics** | in progress — adds `!platform consistency` backed by `services/platform_consistency.py`.  No migration, no behavior changes, no flag flips. |

---

## Behavior defaults preserved on `main` today

These guarantees hold without operator action:

* `bindings.primary` — default **OFF**.  XP, Economy, Governance reads
  resolve via the legacy `guild_settings` path; the arbitration helper
  short-circuits to legacy.
* `participation.enabled` — default **OFF**.  After #86 merges, the
  XP listener gate falls through to the legacy behaviour without
  consulting the participation accessors.
* `feature_flag.primary` — default **OFF**.  The evaluator returns
  declared defaults without touching the DB.
* All Phase 2 audit tables (`binding_audit_log`, `feature_flag_audit`,
  `user_participation_audit`) are **preserved** on guild leave.
* All Phase 2 active-state tables for departed guilds are purged on
  guild leave; the same user's data in OTHER guilds is preserved.

---

## Still pending at the time (historical — do not execute as a current queue)

### PR-10 — diagnostics consistency surface (recommended next)

Goal: unify the platform's diagnostics providers behind one shape so
`!platform consistency` / `!platform migrations` / `!platform health`
can render reliably.

What it should surface in one place:

* Binding drift — bindings pointing at MISSING/INVALID resources.
* Config arbitration counters — `by_source` / `by_binding_status` /
  `by_flag_state` / fallback rate.
* Participation cache health — hits / misses / evictions / size.
* Participation audit pulse — recent mutation counts by `mutation_type`.
* Feature flag fallback usage — bootstrap fallback counter.
* Missing settings / bindings — per-subsystem readiness rollup.
* Setup-readiness blockers (see below).

Scope discipline for PR-10:

* No new domain.  No new migration.
* Read-only — providers never mutate.
* Use the existing `services.diagnostics_service` registry; do not
  build a parallel registry.
* Keep the rendering simple (text embeds).  Anything fancier is its
  own PR.

### Setup-readiness blockers (informational)

For the wizard / setup phase to start, these must be in place.  The
list below is mirrored verbatim in
`services.platform_consistency.SETUP_READINESS_BLOCKERS` and
surfaced by `!platform consistency` as an informational section.
The doc test
`tests/unit/docs/test_phase_2_readiness_doc.py` enforces that every
constant entry appears here in humanised form, so adding a new
blocker requires updating both this doc and the constant.

* **command surface ledger** — the catalogue of slash / prefix
  entrypoints that the wizard / panels would link from.
* **panel registry** — version-stamped persistent-view registration.
* **settings registry** — typed setting metadata for the wizard's
  preview/commit flow.
* **settings mutation pipeline** — mirrors binding / rollout /
  participation mutation services.
* **governance trusted role schema** — `governance` `SubsystemSchema`
  declaration for `trusted_role` so the binding backfill can
  complete for that key (currently `BLOCKED_NO_SCHEMA`).
* **role service extraction** — pull role-management primitives out of
  the cog layer into a service.
* **cleanup policy extraction** — pull cleanup policy out of
  moderation_service / cog layer into a dedicated service.
* **logging settings integration** — once PR-11's server-logging
  foundation lands, surface its toggles through the settings
  registry.
* **slash panel entrypoints** — `/setup`, `/settings` etc. wired into
  the panel registry.
* **setup wizard readiness bridge** — gating signal published by the
  consistency surface that the wizard can consume.
* **setup wizard** — end-user-facing onboarding flow.

None of these are in scope for PR-10 itself; PR-10 only **reports**
them as informational tracking.

---

## Do NOT start yet

> **Status update (2026-05-31) — reconciled with shipped code.** The
> **setup wizard shipped** after this snapshot (`cogs.setup_cog`,
> registered in `disbot/config.py`; see
> `docs/setup-platform/setup_wizard_finalization_plan.md`). It is removed from the
> lock-box below — it is now in *finalization*, not greenfield. The
> remaining items stand.

These are explicit lock-boxes — opening any of them before the
substrate is stable will re-introduce the duplicate-systems risk that
the consistency ledger exists to prevent:

* `/myprofile` or participation hub UI *(still locked — plan-only)*
* ~~Setup wizard~~ → **SHIPPED**; finalization tracked in
  `docs/setup-platform/setup_wizard_finalization_plan.md`
* Resource provisioning runtime (channel/role auto-creation) — *note: the
  provisioning pipeline is now invoked by the shipped wizard with explicit
  confirmation (no silent auto-create); the broader auto-provisioning
  runtime stays locked*
* Notification routing / DMs / reminders
* Slash-command entrypoints for setting feature flags or participation
* Component registry implementation (planning is fine)
* Settings registry implementation
* Role / cleanup service extraction
* Production flip of `bindings.primary`
* Legacy `guild_settings` row removal for migrated keys
* Any "user settings" generic blob that collapses participation /
  subscriptions / preferences / visibility into one entity
* XP threshold role binding (the 1:N shape does not fit
  `subsystem_bindings`; a dedicated `xp_threshold_roles` table is the
  right shape, in a separate small PR motivated by admin-UX needs)

---

## Migration numbering ladder

| Migration | Source PR | Status |
|---|---|---|
| `022_subsystem_bindings.sql` | #73 | on main |
| `023_feature_flag_state.sql` | #77 | on main |
| `024_environment_tiers.sql` | #77 | on main |
| `025_feature_flag_audit.sql` | #78 | on main |
| `026_platform_migration_checkpoints.sql` | #81 | on main |
| `027_user_participation.sql` | #84 | on main |
| `028_user_participation_audit.sql` | #86 | on main |
| 029 | next free number | — |

---

## Stable-stack hygiene reminders

Two recent integration PRs (#80 and #85) repaired stacked-PR delivery
problems where intermediate PRs were merged into stack branches
instead of `main`.  To avoid a third occurrence:

* **Branch each new PR off `main` directly** unless there is an
  unavoidable dependency on an unmerged PR.
* If you must stack, set the PR's base to the upstream stack
  branch AND make sure merges go to `main` in order.  The simplest
  rule: if a PR's diff makes no sense without unmerged work, do not
  merge it into anything other than `main`.
* The cherry-pick recipe for the integration PRs is in #80 and #85's
  bodies — re-usable verbatim if it happens again.

---

## How to update this file

* When a PR merges: move its row from "Open right now" to "Done on
  `main`", and bump the migration ladder.
* When a recommended next PR ships: replace its planning bullet with
  the merged-PR row.
* When a "do not start yet" item is unlocked by a substrate PR: move
  it to a new "in flight" section and add the PR link.
* Keep this file short — it is a punch-list, not a design doc.
