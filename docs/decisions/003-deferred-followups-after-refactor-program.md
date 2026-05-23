# 003 — Deferred follow-ups after the SuperBot 2.0 refactor program

> Status: planning notes (PR-07).
> Supersedes: nothing.
> Related: [`/home/user/superbot/.claude/plans/1-recommended-target-agent-zazzy-eclipse.md`](../../.claude/plans/1-recommended-target-agent-zazzy-eclipse.md)
> (the program plan that PR-01a..PR-06c implements).

The refactor program that lands as PR-01a → PR-06c on this iteration
stabilises the readiness contract, runtime task ownership, the
dynamic blocker registry, the setup operation preflight, the
smoke-test checklist, and the command-classification pipeline.  This
ADR captures the work that was deliberately **deferred** so a later
contributor can pick it up without re-deriving context.

Each section below is a scoping note, not an implementation plan.

---

## 1. PR-02c — Delete `_APP_TASKS` after canary

**Status:** ready once PR-02b (#247) has run a clean canary release.

**Why deferred:** PR-02b's shutdown drain switches to
`core.runtime.tasks.cancel_all()` but keeps `_APP_TASKS` populated
as a one-release safety mirror.  PR-02c is the mechanical deletion
of `_APP_TASKS`, `_supervised_task`, and `_on_app_task_done` from
`bot1.py` after operators confirm the new drain path is stable in
production.

**Scope when picked up:**

- Delete `_APP_TASKS: list[asyncio.Task]` and every `.append()` site.
- Delete `_supervised_task` body; call `core.runtime.tasks.spawn`
  with the existing `on_error` hook directly at each callsite.
- Delete `_on_app_task_done` (replaced by the `on_error` hook).
- Tighten the invariant allowlist in
  `tests/unit/invariants/test_no_unmanaged_create_task.py` — only
  `core/runtime/tasks.py:62` and `bot1.py:613` remain.
- `bot1.py` line count drops by roughly 50 lines.

**Risk:** Low (mechanical; PR-02b already proved parity).

---

## 2. PR-04b — Flip `SETUP_PREFLIGHT_DIFF` to default-on + Final Review render

**Status:** ready once PR-04a (#252) has run a clean canary release.

**Why deferred:** PR-04a ships the `preflight_operations` contract
behind `SETUP_PREFLIGHT_DIFF=false` (default).  PR-04b flips the
default and wires the Final Review embed to render the current /
proposed diff for staged operations.

**Scope when picked up:**

- Flip default to `SETUP_PREFLIGHT_DIFF=true` in
  `is_preflight_enabled` (or remove the env-gated branch entirely
  if the canary is clean).
- Add Final Review embed render branch in
  `disbot/views/setup/final_review.py` that:
  - Calls `await preflight_operations(ops, guild=guild)` before
    rendering.
  - Renders each `ChangePlanEntry` with `current → proposed`,
    `risk`, `rollback_note`, and `read_error` (when present).
  - Falls back to validation-only preview if preflight raises (the
    fail-safe is per-entry; entries with `read_error` should still
    show, just with a "preflight unavailable" annotation).
- Add render snapshot tests in
  `tests/unit/views/setup/test_final_review_diff.py`.

**Risk:** Medium — touches the Final Review apply gate.  Apply
behaviour itself stays unchanged; only the pre-apply render changes.

---

## 3. PR-06c Part B — Mass command annotation sweep

**Status:** ready anytime; deliberately defer until needed.

**Why deferred:** PR-06c shipped the classification pipeline
(`extras["classification"]` → `CommandSurfaceEntry.classification`
→ help filter) with no per-cog annotations.  Defaults remain
`primary_entrypoint`, so every existing command's effective
behaviour is unchanged.  Mass annotation crosses the >50-file
threshold from the program plan's stop condition.

**Scope when picked up:**

- Audit every `@commands.command` and `@app_commands.command`
  callsite in `disbot/cogs/**/*.py`.
- Classify each:
  - `power_user_shortcut` — short aliases like `!d` for `!daily`.
  - `panel_action` — invoked from a panel button rather than typed.
  - `legacy_duplicate` — alias kept for backward compat.
  - `internal_admin` — staff/operator only (already covered by
    visibility tier, but the classification refines further).
  - `hidden` — never surfaced in help.
  - `deprecated` — surfaced with a deprecation warning.
- Acceptance: `LedgerFindings.unclassified_entry_points` is empty
  on boot.  (The default makes every command "classified" today;
  Part B converts opt-out absences into opt-in tags so the help
  surface can shrink.)

**Risk:** Low-medium (broad surface annotation, but mechanical).

---

## 4. Setup repair mode

**Status:** ready once PR-04b lands.

**Why deferred:** Setup repair needs the `ChangePlanEntry` contract
to render "current broken → proposed fix" diffs in a repair embed.

**Scope when picked up:**

- `services/readiness_repair.py` **already exists** with
  `RepairPreview` / `RepairResult` dataclasses and per-action
  helpers (`_apply_clear_stale_binding`, `_apply_bind_existing`,
  `_apply_create_missing`, `_apply_enable_logging`).  The
  migration is to **produce `SetupOperation` batches** and route
  them through `services.setup_operations.apply_operations`
  instead of calling the per-action helpers directly.
- Reuse `preflight_operations` so the repair embed and Final Review
  share the same diff renderer.
- Estimated: 1 PR.

**Risk:** Medium — touches existing repair flow.

---

## 5. Feature maturity labels

**Status:** ready once PR-06c Part B lands.

**Why deferred:** Maturity labels (alpha / beta / stable /
deprecated) ride on top of the classification pipeline.  Without
per-command opt-in (Part B), there is no surface to attach
maturity to.

**Scope when picked up:**

- Add a `maturity: Literal["alpha"|"beta"|"stable"|"deprecated"]`
  field to `SUBSYSTEMS` entries.
- Render the badge in help / `!platform consistency` / readiness
  snapshot.

**Risk:** Low.

---

## 6. Operator changelog panel

**Status:** ready once PR-01b (#248) lands and a release-manifest
contract is designed.

**Why deferred:** A changelog panel needs the **release manifest**
contract (what shipped, when, who owns it) which does not exist
yet.  PR-01b's readiness snapshot is one input; a markdown
source-of-truth committed alongside ADRs is the other.

**Scope when picked up:**

- Define the release manifest format (JSON file? markdown
  front-matter?  ADR-style?).
- Add a panel surface that reads the manifest and renders the
  N most recent releases.
- Consumes `ReadinessSnapshot.startup_outcomes` to flag releases
  that landed on a degraded boot.

**Risk:** Low (read-only).

---

## 7. Runtime danger-signs dashboard

**Status:** **WONTFIX** — merged into the PR-01b readiness snapshot.

The original source plan proposed a separate "runtime danger
signs" dashboard.  The revision plan merged this into the PR-01b
`ReadinessSnapshot` so there is exactly one place that composes
deploy-relevant signals (`tasks.active()`, `runtime_lock_owned`,
`recent_fatal_logs`, etc.).  Future danger-signal surfaces should
extend the snapshot, not build a parallel dashboard.

---

## 8. Tournament platformization

**Status:** large; multi-PR; defer until lifecycle / setup /
sessions / locks / command navigation foundations are stable.

**Why deferred:** Per the revision plan, tournament platformization
needs every PR-01a..PR-06c foundation in place first.  Even after
that, the migration is too large for a single PR.

**Scope when picked up:**

- Migrate `services/tournament_state_service.py` and the
  `cogs/rps_tournament_cog.py` / `cogs/deathmatch_cog.py` cogs to
  produce `SetupOperation` batches routed through
  `services.setup_operations.apply_operations` instead of calling
  mutation pipelines directly.
- Split per-cog (rps_tournament first, deathmatch second) to keep
  reviewable diff size.

**Risk:** Medium-high.

---

## 9. Config arbitration / per-guild access audit

**Status:** flagged by the source plan for "before more setup
sections are added".  Not a hard prerequisite for any PR-01a..PR-06c
work (none of those PRs added a new setup section).

**Why deferred:** A broad audit of direct `db.get_setting()` and
`guild_settings` reads in moderation / roles / logging / deathmatch /
blackjack / governance is its own coordinated effort.  It would
duplicate work if attempted alongside PR-04a / PR-04b which are
already touching the setup mutation path.

**Scope when picked up:**

- Audit every direct `db.get_setting` / `guild_settings` read.
- Add an arbitration accessor per migrated key (mirroring the
  existing XP / economy / governance accessors).
- Move static `ALLOWED_CHANNELS` (in `disbot/config.py`) behind a
  per-guild access policy service so fresh-guild onboarding
  becomes a config rather than a code change.

**Risk:** Medium (broad surface, but each accessor is mechanical).

---

## 10. Automated Discord smoke runner

**Status:** Ideas Lab — not on the critical path.

**Why deferred:** PR-05 ships the smoke checklist as a **doc**.  The
revision plan deliberately defers an automated runner to keep PR-05
small and operator-facing.  An automated runner is an Ideas Lab
follow-up.

**Scope when picked up (if approved):**

- Periodic background task (`tasks.spawn("smoke_test:loop", ...)`)
  that runs every 5 minutes when `SMOKE_TEST_GUILD_ID` is set.
- Each smoke step is read-only (fetch guild channels, fetch own
  member, fetch first persistent panel anchor, etc.).
- Per-step 5 s timeout.
- Surfaces results via a new `smoke_test` diagnostics provider
  and bumps a `smoke_test_failures_total{step}` Prometheus
  metric.

**Risk:** Low (env-gated; off by default).

---

## Tracking

When any of the above ships, replace the **Status** line with
`shipped in #NNN — YYYY-MM-DD` and leave the rest of the section
intact for archaeology.
