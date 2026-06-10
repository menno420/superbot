# Setup Wizard — Finalization Analysis & Plan

> **Status:** `plan` — **finalization tranche COMPLETE; PR4–PR6 are the designed
> future roadmap.** Source-verified 2026-06-10 (consolidated-plan **Batch 10 /
> DT09** re-verification): the PR1–PR3 tranche this plan sequenced **shipped via
> #435** — PR1 (config-arbitration fallback *attribution* + the
> `services/wizard_finalization.py` readiness rollup, incl.
> `SETUP_PREFLIGHT_DIFF` surfaced as a visible env-only gate), PR2 (flag-manager
> friendly labels + operator/internal split), and PR3 (the AI advisor wired as
> the optional read-only review action — `services/setup_advisor_review.py`,
> mutation-safety pinned by
> `tests/unit/invariants/test_setup_advisor_readonly.py`). The §3 "broken /
> incomplete" list and §10's PR1–PR3 text below are the *historical* analysis
> that drove that tranche — do not re-execute them. **What remains is PR4
> (`/myprofile` per-user foundation — its planning session ran 2026-06-10:
> [`../planning/myprofile-foundation-plan-2026-06-10.md`](../planning/myprofile-foundation-plan-2026-06-10.md),
> ready to execute), PR5 (visibility
> bridge), and PR6 (migration cleanup, gated on fallback=0).**
>
> When this doc disagrees with a source file, **the source file wins** — open a PR
> to reconcile. Authored 2026-05-31 against `main` @ commit `370cf4b`.

---

## Context

SuperBot already ships an **active guild setup wizard** (`cogs.setup_cog`, registered
in `disbot/config.py`), but it was built and live-tested *ahead of* the docs that
govern it, so it reads as "active but not 100% functional." This document is the
repo-state analysis and the finalization plan.

**Why now:** the wizard was heavily stabilized 2026-05-29 (a 3-PR series — *"unify
apply path + gating" (1/3)*, *"depth tiers … apply-all" (2/3)*, *"partial-apply
'Finish anyway' escape + spine tests" (3/3)* — plus *"Fix 4 runtime bugs surfaced by
live interactive testing"* and *"populate section registry … (fix empty wizard)"*),
yet two **binding docs** still listed it as "forbidden / not even a stub." This plan's
first action reconciles those docs.

**Premise correction (verified):** the wizard is neither "broken" nor "production-ready."
It is **structurally complete and architecturally well-behaved** (routes every write
through canonical mutation pipelines, read-only preflight enforced by an AST invariant
test, audited session lifecycle, recovery flows, persistent launcher) but has **real
finalization gaps**: an orphaned AI advisor flow, an ad-hoc env feature flag, a
declaration-only flag whose pipeline now has a live consumer, coarse diagnostics that
cannot pinpoint config-arbitration fallback, a lagging flag-manager UI, and (until this
PR) stale governing docs.

### Scope decisions (confirmed with maintainer)
- **Per-user customization** ("users pick which channels/commands/notifications they
  see") → **plan-only**. Designed below as a future tranche; **built: none**. Respects
  the locked docs and the "no per-user channel visibility via permission overwrites"
  stop-condition.
- **Stale binding docs** → **reconcile** (CLAUDE.md: source file wins).
- **AI advisor** → **wire into the wizard** (service-boundary PR), as an optional,
  advisory-only, read-only review action.

### Deliverable & sequencing
- **This PR (documentation only — HARD PREREQUISITE for the code PRs):** this analysis
  doc + reconciliation of `phase-2-completion-readiness.md` and
  `platform-consistency-ledger.md` so they stop contradicting the shipped wizard.
- **Code tranche (follow-up PRs):** PR1 → PR3 below (CLAUDE.md caps a plan at 2–3 PRs).
- **Future roadmap (designed, unscheduled):** PR4 → PR6 below.

---

## 1. Current state summary

| Dimension | State |
|---|---|
| Loaded? | **Yes** — `disbot/config.py` → `"cogs.setup_cog"`. |
| Entry points | `!setup` (prefix), `/setup` (slash, admin-gated), `/setup-hub` (legacy), persistent **launcher button** (`setup:start`), auto-post on `on_guild_join` + re-sync on `on_ready`. Helpers: `/setup-depth|-skip|-unskip|-reset|-delegate|-undelegate|-status`. (`disbot/cogs/setup_cog.py`) |
| Scope | **Guild-only.** Session row in `setup_session`, draft in `setup_draft_operations`. Does **not** touch per-user participation (grep-verified). |
| Write model | Stage → preview → commit. Staging writes only to the draft table; commit (`services.setup_operations.apply_operations`) routes every op through canonical pipelines. **No direct DB writes** in the dispatcher. |
| Op kinds (apply path) | `bind_*`, `clear_binding`, `set_setting`, `set_cog_routing`, `create_channel/role`, `add/enable/disable_automation_rule`, `set_cleanup_policy`. (`disbot/services/setup_operations.py`) |
| Preview | `preflight_operations()` → `ChangePlanEntry` (current/proposed/would_change/risk/rollback_note). **Read-only by AST invariant** (`tests/unit/invariants/test_setup_preflight_readonly.py`). Gated by raw env `SETUP_PREFLIGHT_DIFF` (default on). |
| Audit | Session lifecycle (`started/completed/dismissed`) via `setup_session._emit_session_audit`; op-level `mutation_id` flows from the underlying pipelines. |
| Recovery | Single-flight apply lock; phase-ordered apply; partial-apply recovery ("Retry / Finish anyway / Cancel"); per-section recovery. **No true rollback** of already-applied ops (relies on pipeline idempotency / `use_existing`). |
| Tests | ~19 setup test files, no skips found; AST invariant + spine tests present. |

The guild wizard exists and its happy path works end-to-end through real pipelines. The
gaps are integration / clarity / observability, not a broken core.

## 2. Confirmed working parts

- **Entry + lifecycle**: prefix/slash/button/auto-join resolve through
  `cogs.setup._wizard_entry` / `setup_session`; launcher is persistent (`timeout=None`,
  static custom_ids) and re-synced in place on `on_ready` (`setup_cog.py:663-731`).
- **Section registry**: populated via `import views.setup.sections` side-effect at
  `setup_cog.py:38` (the fix for the "empty wizard" bug).
- **Canonical write routing**: `setup_operations.py` dispatches to
  `BindingMutationPipeline`, `SettingsMutationPipeline`, `ResourceProvisioningPipeline`,
  `AutomationMutationPipeline`, `cleanup_mutation`, `command_routing` — matching every
  "Wizard consumer" contract in `docs/health/platform-consistency-ledger.md`.
- **Preflight diff**: real current/proposed for `bind_*`/`clear_binding`/`set_setting`/
  `set_cog_routing`; other kinds labelled "preflight unavailable" rather than dropped.
- **Presets**: `views/setup/sections/preset_select.py` (+ `template_picker.py`,
  `logging_presets.py`, `setup_operations.preset_operations_to_setup_operations`) — wired.
- **Access ladder**: owner > delegated admin > administrator > denied (`services.setup_access`).
- **Readiness**: `services.setup_readiness` + `services.setup_blockers.BLOCKERS` feed the
  `SETUP_READINESS` section of `!platform consistency` (informational).

## 3. Confirmed broken / incomplete parts

1. **AI advisor is orphaned.** `services/setup_ai_advisor.py`, `views/setup/ai_review/`,
   and the `ai_setup` section exist but are **not referenced** by `wizard.py`,
   `wizard_nav.py`, or `_wizard_entry.py` (grep-verified). → **Wire in** (PR3).
2. **No true rollback.** Partial-apply recovery exists but already-applied ops are not
   reverted; the flow depends on idempotency. Acceptable, but the apply summary should
   state this explicitly and surface the rollback_note at commit time.
3. **`resource_provisioning.primary` is unwired, and "primary" is the wrong frame.** The
   wizard routes `create_channel/create_role` through `ResourceProvisioningPipeline`, but
   the pipeline does **not** consult the flag (docs still said "zero production callers").
   Unlike `bindings.primary`, provisioning has **no legacy alternative path** for the
   wizard, so a "primary/migration routing" meaning is empty — the only coherent meaning
   is an *availability* gate. **Decision §D1: do NOT enforce it this tranche**; mark it
   truthfully inactive and document the kill-switch design for a later PR.
4. **AI advisor needs a graceful-degrade path** once wired (missing API key / timeout
   must not block the linear wizard) — design in PR3.

## 4. Architecture drift / inconsistencies

| Drift | Evidence | Fix tranche |
|---|---|---|
| Wizard's preflight gate is invisible, not "in the wrong place" | `SETUP_PREFLIGHT_DIFF` raw env at `setup_operations.py:302-309`, not surfaced anywhere | PR3 (§D2): **keep env-only** (a safety/diagnostic gate, not a runtime feature), default ON, but **surface it as a visible env-only gate in diagnostics**. Do **not** make it DB-editable. |
| Binding docs contradict shipped code | `phase-2-completion-readiness.md` + `platform-consistency-ledger.md` listed setup wizard / `/myprofile` as "locked / not even a stub"; `roadmap_setup_platform.md` already says "the shipped setup wizard is a pragmatic subset." | **This PR**: reconcile the two stale docs. |
| Provisioning flag declared but semantically empty for the wizard | `resource_provisioning.primary` declaration-only while wizard calls the pipeline; no legacy path to "route" | **Defer** enforcement (§D1); mark inactive/no-consumer now; document the availability-gate design. |
| Flag-manager UI lags the read-only embed | `views/diagnostic/flag_manager.py` dropdown uses `label=name` (raw key), no operator/internal split; `_platform_embeds.build_flags_embed` already shows friendly labels + splits by `audience` | PR2. |

## 5. Setup wizard dependency map

**Depends on (today):**
- Mutation pipelines: `binding_mutation`, `settings_mutation`, `resource_provisioning`,
  `automation_mutation`, `cleanup_mutation`, `command_routing`.
- Registries / runtime: `services.setup_sections.REGISTRY`, `core.runtime.bindings`,
  `core.runtime.settings_registry`, `core.runtime.config_arbitration` (preview provenance),
  `core.runtime.feature_flags` (`is_enabled` reads).
- Diagnostics: `services.setup_blockers`, `services.platform_consistency`,
  `services.audit_events`.
- Storage: `utils.db.setup_session`, `utils.db.setup_draft`, `utils.db.bindings`,
  `utils.db.get_setting`.

**Should depend on but does not yet:**
- A **visible** ownership for its preflight gate (currently invisible raw env — §D2).
- A **fallback-source attribution** signal from `config_arbitration` so previews can
  explain *which* binding/key is still on legacy (today only a count exists — §D6).

## 6. Per-user customization roadmap (PLAN-ONLY — build nothing now)

**Backend that already exists:** four tables (`user_participation`, `user_subscriptions`,
`user_preferences`, `user_visibility_overrides`; migrations 027/028 audit), typed
accessors (`utils/user_config_accessors.py`), per-(user,guild) cache with TTL+size
eviction (`core/runtime/user_config.py`), and `services/participation_mutation.py`
(4 entrypoints, 7-step contract, inline cache invalidation, audit + events). **Zero UI
callers.** Only consumer is the XP listener gate behind `participation.enabled` (default OFF).

**Entirely absent (needs design, not built here):** any `/myprofile` or participation hub
UI; `on_member_join` onboarding trigger; command/help filtering by participation; **any
channel/command visibility bridge** (no `set_permissions` / `PermissionOverwrite` tied to
participation anywhere).

**Designed future tranche (PR4/PR5):** reuse the existing pipeline + accessors; **never**
collapse the four tables into one blob (ledger hard rule); **prefer role-based visibility**
over per-user permission overwrites; treat the guild wizard's draft→preview→commit pattern
as the template for the user hub. **Do not** build the permission bridge without an explicit
scalability / rollback / Discord-edge-case design.

## 7. Feature flag status table

| Flag | Default | Real consumer? | Recommended end-state |
|---|---|---|---|
| `feature_flag.primary` | off | meta-gate (env-only, never DB) | **Keep env-only.** Add "primary OFF → overrides ignored" warning in the flag manager (PR2). |
| `settings.manager_cog.enabled` | **on** | `cogs/settings_cog.py:89` | **Keep** as operator flag. Good live test of override plumbing. |
| `youtube.context.enabled` | off | `services/youtube_context_service.py` | **Keep** as operator/AI flag. |
| `bindings.primary` | off | `config_arbitration.py:213` (module-only) | **Keep** migration flag. Do **not** flip/delete until fallback=0 proven (PR6). |
| `participation.enabled` | off | `cogs/xp/listener.py:64` | **Keep disabled** until the per-user flow ships; tie to it then. |
| `resources.unified` | off | **none** | Mark **inactive/no-consumer** in UI; keep declaration; add diagnostics note (PR2). |
| `settings.mutation.primary` | off | **none** (pipeline ignores it) | Mark **inactive/no-consumer**; keep as kill-switch declaration (PR2). |
| `resource_provisioning.primary` | off | **declaration-only** (wizard calls the pipeline, not the flag) | **Mark inactive/no-consumer now** (§D1). Defer any kill-switch wiring; when provisioning genuinely needs operator control, add an *availability* gate (default ON, blocked-preflight UX) — preferably a clearly-named `resource_provisioning.enabled` rather than overloading "primary". |

## 8. Diagnostics / observability gaps

1. **Arbitration fallback is a bare count.** `config_arbitration.py` tracks
   `by_source/by_binding_status/by_flag_state` but **not which key/subsystem/binding**
   fell back. `!platform consistency` says "investigate per `!platform flags`" but cannot
   pinpoint. → **Add per-(subsystem, binding, legacy_key) fallback attribution** (bounded,
   redacted) surfaced in a new diagnostic (PR1, shape per §D6).
2. **Flag-manager UI** shows raw keys, no operator/internal split, no
   `feature_flag.primary`-off warning, no inactive/no-consumer marking. The read-only
   `!platform flags` embed already does labels + audience split — port that parity into
   the interactive manager (PR2).
3. **Wizard readiness** is informational-only today; add an explicit "wizard finalization
   readiness" rollup (AI advisor wired? preflight flag source visible?) so progress is
   observable (PR1).

## 9. Missing tests (to add per PR)

- **PR1:** fallback-attribution captures `(subsystem, binding_key, legacy_key, source,
  flag_state, timestamp)` **and no values/names** (§D6); buffer is bounded (per-process and
  per-guild/subsystem cap); `platform_consistency` degrades safely if attribution fails;
  wizard-readiness rollup renders even when optional deps are unavailable.
- **PR2:** flag-manager renders friendly labels + operator/internal groups; warns when
  `feature_flag.primary` off; marks `resources.unified`, `settings.mutation.primary`,
  `resource_provisioning.primary` as inactive/no-consumer; env-only flags visible but not
  DB-editable. (No provisioning-enforcement test — enforcement deferred §D1.) Keep a
  boundary test asserting the wizard routes resource creation **only** through
  `ResourceProvisioningPipeline`.
- **PR3 (AI advisor — mutation safety is non-negotiable):** an invariant/service test
  (mirroring `tests/unit/invariants/test_setup_preflight_readonly.py`) that the advisor
  **cannot write** to setup draft/session, bindings, settings, routing, provisioning,
  automation, or cleanup; advisor is reachable only as an optional review action;
  missing-key and timeout both degrade gracefully and never block; commit + partial-apply
  recovery labels render the explicit no-rollback caveat; `SETUP_PREFLIGHT_DIFF` source is
  visible/deterministic in diagnostics.

## Pre-implementation decisions (resolved)

Each is the **safe, reversible** default, marked "confirm before the relevant PR."

- **§D1 — `resource_provisioning.primary` semantics → DEFER + DOCUMENT.** Provisioning has
  no legacy path for the wizard, so "primary/migration routing" is meaningless here; the
  flag is only coherent as an *availability* kill-switch. Enforcing it now (default OFF)
  would break live provisioning, so this tranche **does not enforce it** — PR2 only marks
  it truthfully inactive. When operator control is actually needed, implement it as an
  availability gate that **defaults ON** and shows a **blocked-preflight** state when OFF
  (never a commit-time failure); prefer a clearly-named `resource_provisioning.enabled` over
  overloading "primary". *(Confirm before any future provisioning-gate PR.)*
- **§D2 — `SETUP_PREFLIGHT_DIFF` ownership → ENV-ONLY + VISIBLE.** It is a safety/diagnostic
  gate, not a runtime feature, so it stays env-only and default ON; PR3 surfaces it as a
  read-only env-only gate in diagnostics so operators can see why preview behavior changed.
  Do **not** promote it to a DB-editable feature flag.
- **§D3 — AI advisor placement → OPTIONAL / ADVISORY / READ-ONLY.** Invoked only from an
  optional "Ask AI to review this setup" action on the preview/commit screen; consumes the
  staged draft + preflight summary as read-only input; returns advisory text only; never on
  the critical path; enforced read-only by the §9 PR3 invariant test.
- **§D6 — fallback-attribution shape (PR1).** Store only stable internal keys `(guild_id,
  subsystem, binding_key, legacy_key, source, flag_state, timestamp)`; **never** setting
  values, channel/role/user names, or message content; cap per-process and
  per-guild/subsystem; degrade quietly if the collector is unavailable.

## 10. Recommended PR sequence

**This PR (docs only — HARD PREREQUISITE):** this doc + reconcile
`phase-2-completion-readiness.md` & `platform-consistency-ledger.md` so they stop calling
the shipped wizard "forbidden/locked." Reviewers must not read PR1–PR3 against docs that
contradict the code.

**PR1 — Diagnostics clarity & wizard-readiness (no behavior change beyond diagnostics).**
Add config-arbitration fallback **attribution** (bounded, redacted — §D6); add a
wizard-finalization-readiness rollup to `platform_consistency`; everything read-only,
fail-safe, and degrades if the attribution collector is unavailable.

**PR2 — Feature-flag manager clarity (UI/diagnostics only; no behavior change).**
Friendly labels + operator/internal grouping in `flag_manager.py`; `feature_flag.primary`-off
warning; mark inactive/no-consumer (`resources.unified`, `settings.mutation.primary`,
`resource_provisioning.primary`) and env-only flags clearly. **No kill-switch enforcement**
(deferred — §D1), so PR2 stays low-risk and needs no split.

**PR3 — Setup-wizard service-boundary cleanup + AI advisor wire-in.**
Wire the AI advisor as an **optional, advisory-only, read-only review action on the
preview/commit screen** (§D3) — it consumes the staged draft + preflight summary, returns
advisory text only, and **must not** mutate draft/session/bindings/settings/routing/
provisioning/automation/cleanup (enforced by the §9 mutation-safety invariant test);
graceful degrade on missing key/timeout, never blocking the linear flow. Keep
`SETUP_PREFLIGHT_DIFF` **env-only but visible in diagnostics** (§D2; not a DB flag). Make the
**no-automatic-rollback** caveat explicit in the commit summary (per-op rollback notes where
available) and in the partial-apply recovery labels (Cancel does not undo applied ops).

> CLAUDE.md caps plans at 2–3 PRs; PR1–PR3 is the finalization tranche. PR4–PR6 below are a
> **designed future roadmap**, executed only after this tranche lands.

**PR4 (future) — Per-user `/myprofile` foundation** (read-only first, then opt-in/
subscription/preference writes via the existing pipeline; `on_member_join` onboarding).
**PR5 (future) — Channel/command visibility bridge** (role-based; explicit scalability/
rollback/edge-case design; no per-user permission overwrites by default).
**PR6 (future) — Migration cleanup** (only after fallback=0: consider flipping
`bindings.primary`, removing legacy `guild_settings` rows).

## 11. Risks & rollback notes

- **Diagnostics PRs are low-risk** (read-only, fail-safe collectors). Risk: a new collector
  throwing must not blank the report — keep the per-section try/except.
- **`resource_provisioning.primary`**: enforcement is **deferred** (§D1) precisely because
  flipping a previously-ignored, default-OFF flag would disable live wizard provisioning.
  When eventually wired, it must default to preserve current behavior (availability gate,
  default ON) and OFF must show a **blocked-preflight** state at preview, never a
  commit-time failure.
- **AI advisor**: must degrade gracefully (no key/timeout) — never block the linear flow.
- **Fallback attribution**: must redact values (keys/IDs only, no setting values) to avoid
  leaking config into diagnostics; bound memory with a small ring buffer.
- **Doc reconciliation** is reversible via git; lowest risk.

## 12. Clear "DO NOT do yet" list

- ❌ Build any per-user `/myprofile` / participation hub UI (plan-only).
- ❌ Build a channel/command visibility bridge via per-user **permission overwrites**.
- ❌ Flip `bindings.primary` to primary, or delete it, while fallback > 0.
- ❌ Remove legacy `guild_settings` rows for migrated keys.
- ❌ Enable `participation.enabled` by default before the user flow exists.
- ❌ Make `feature_flag.primary` DB-editable.
- ❌ Collapse the four participation tables into one "user settings" blob.
- ❌ Delete the AI advisor (maintainer chose to wire it in, not remove).
- ❌ Add slash-command entrypoints that *set* feature flags or participation.

## 13. Verification (how to validate each tranche)

- **This PR:** `git diff` shows only this new doc + the two doc reconciliations; no `.py`
  changed.
- **PR1:** `python3.10 -m pytest tests/unit/services/test_platform_consistency.py
  tests/unit/runtime -q`; manually run `!platform consistency` / new fallback view in a
  guild with a known legacy fallback and confirm the offending subsystem/key is named.
- **PR2:** `python3.10 -m pytest tests/unit/views/.../test_flag_manager*.py -q`; open the
  flag manager and confirm friendly labels, grouping, `feature_flag.primary`-off warning,
  and that the no-consumer flags are clearly marked inactive.
- **PR3:** run `/setup` end-to-end with and without an AI key (advisor degrades, never
  blocks); confirm preflight gate source is visible in diagnostics; confirm commit summary
  shows the no-rollback note.
- **Every code PR:** `python3.10 scripts/check_architecture.py --mode strict &&
  python3.10 scripts/check_quality.py --check-only && python3.10 -m pytest tests/ -q`
  (CI is Python 3.10 — match it exactly per CLAUDE.md).
