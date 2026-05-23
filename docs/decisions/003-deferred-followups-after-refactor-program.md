# 003 — SuperBot 2.0 refactor program: final state + deferred follow-ups

> Status: ADR (PR-07).
> Supersedes: nothing.
> Related: [`/home/user/superbot/.claude/plans/1-recommended-target-agent-zazzy-eclipse.md`](../../.claude/plans/1-recommended-target-agent-zazzy-eclipse.md)
> (the program plan that PR-01a..PR-06c implement).

The refactor program landed as 13 stacked PRs (#244..#256) plus this
ADR.  This document records, in this order:

1. Completed and merged in this stack
2. Open, ready, blocked only by canary
3. Intentionally deferred
4. Rejected / WONTFIX
5. Ideas Lab follow-ups

The post-review fixes (snapshot-before-cancel for the shutdown drain,
strict bool/int separation in the preflight normalizer, embed-field
1024-char enforcement, centralized help-visibility policy with
deprecated commands rendered per contract) are part of the stack and
are reflected below.

---

## 1. Completed and merged

| PR | Code | Notes |
|---|---|---|
| #244 | PR-01a — typed readiness contract | merged |
| #245 | PR-02a — task compat wrapper + `on_error` hook | merged |
| #246 | PR-06a — command classification contract types | merged |
| #247 | PR-02b — shutdown drain through `core.runtime.tasks` | merged; `cancel_all()` returns the cancellation snapshot, drain runs on every exit, timeout WARNING logged |
| #248 | PR-01b — startup outcome + sync readiness snapshot | merged |
| #249 | PR-03 — dynamic setup blocker registry | merged |
| #250 | PR-06b — slash command ledger ingestion | merged |
| #251 | PR-05 — Discord smoke-test checklist | merged; doc-only, pins all 5 setup slash commands + preflight + blockers |
| #252 | PR-04a — setup operation preflight | merged; `values_equivalent` normalizer replaces the original `str()` comparison |

---

## 2. Open, ready, blocked only by canary

These PRs are technically complete (rebased on current main, tests
green, lint clean).  They should land **only after the parent's
canary window** has elapsed without regressions.

### #253 — PR-06c · classification ingestion + help filter

**Status:** open, mergeable, ready for review.

**Review-fix highlights:**
- Single source of truth for visibility policy in
  `core/runtime/command_surface_ledger._HELP_HIDDEN_CLASSIFICATIONS`.
  `cogs/help_cog` consumes the canonical helper via
  `is_command_hidden_from_help`; no local re-declaration.
- Hidden set narrowed to `{"hidden", "legacy_duplicate"}` —
  **`deprecated` commands stay visible** per the Classification
  Literal contract ("surfaced with a deprecation warning").
- Operators who want a command to disappear immediately classify it
  `hidden`; the deprecation badge itself is a follow-up (see §3).

**Merge condition:** ready now; PR-06a (#246) and PR-06b (#250) are
already on main.

### #255 — PR-02c · remove `_APP_TASKS` mirror

**Status:** open, rebased on current main, single commit on
`bot1.py`.

**Contract:** consumes the PR-02b review contract on main:

```python
cancelled = _runtime_tasks.cancel_all()  # returns the snapshot
if cancelled:
    _, still_pending = await asyncio.wait(cancelled, timeout=5.0)
    if still_pending:
        logger.warning("Shutdown drain timeout ...")
```

* No re-snapshot via `tasks.active()` in the finally-block.
* Drain runs on every exit path, not just SIGTERM.
* Five supervised app tasks (heartbeat, health, session_gc, memory
  sampler, automation scheduler) all spawn through
  `core.runtime.tasks.spawn` with `on_error=_on_app_task_died_webhook`.

**Merge condition:** clean canary of #247 — one release window with
no shutdown / drain regressions.  After that this PR is mechanical;
the diff is a single-commit removal of `_APP_TASKS` /
`_supervised_task`.

### #256 — PR-04b · flip preflight default-on + diff render helper

**Status:** open, rebased on current main, 3 commits (default-on
flip, render helper, review fix).

**Review-fix highlights:**

- **`values_equivalent` strict bool/int separation.**  Drops `"0"` /
  `"1"` from bool token sets.  Adds a strict-bool guard so
  `True != 1` and `False != 0` in the preflight comparison.  An
  operator-staged boolean against a stored numeric setting (or vice
  versa) no longer collapses into a silent no-op render.  Operator-
  safe rule: when in doubt, show the diff.
- **`render_change_plan` field-limit guard.**  When
  `field_limit < len(_TRUNCATION_SUFFIX)` (degenerate small budget),
  the renderer drops the suffix instead of appending it, so the body
  never exceeds the cap.  `RenderedChangePlan.truncated` still
  reports the truncation programmatically.

**Merge condition:** clean canary of #252 — one release window with
no false no-op / false diff complaints from operators.  The Final
Review embed integration that consumes the render helper is a
separate small follow-up (see §3).

---

## 3. Intentionally deferred

### Final Review embed render integration

`FinalReviewView` builds its embed in a sync constructor.  Calling
`preflight_operations` requires an async context, so wiring the diff
into the pre-apply embed needs either an async pre-render method on
the view or a small refactor of the render path.

* Scope: add an async pre-render hook on `FinalReviewView`, call
  `preflight_operations` when `is_preflight_enabled()`, pass the
  resulting `RenderedChangePlan` to `build_final_review_embed` as a
  new optional parameter, add an embed field "Preflight diff" with
  `RenderedChangePlan.body`.
* Risk: low (additive UI change, gated by the flag).

### Deprecated-command warning badge in help

PR-06c (#253) correctly flips deprecated commands to **visible** per
the contract.  The badge itself ("deprecation warning") still needs
to render — currently deprecated commands appear in help looking
identical to primary commands.

* Scope: extend `cogs/help/route.py` (or the cog-embed render path)
  to inspect `cmd.extras["classification"]` and prepend a
  `⚠️ DEPRECATED` marker to the help entry when present.

### PR-06c Part B — Mass command annotation sweep

* Audit every `@commands.command` and `@app_commands.command`
  callsite in `disbot/cogs/**/*.py`.
* Classify each: `power_user_shortcut`, `panel_action`,
  `legacy_duplicate`, `internal_admin`, `hidden`, `deprecated`.
* Acceptance: `LedgerFindings.unclassified_entry_points` is empty
  on boot.

### Setup repair mode

Reuse `services/readiness_repair.py` — produce `SetupOperation`
batches and route through `apply_operations`.  Shares the diff
contract + `render_change_plan` with Final Review.

### Feature maturity labels

Adds `maturity: Literal["alpha"|"beta"|"stable"|"deprecated"]` to
`SUBSYSTEMS` entries; renders the badge in help + readiness embed.
Depends on Part B annotation sweep.

### Operator changelog panel

Needs a release-manifest contract.  Reads from a markdown source-of-
truth committed alongside ADRs; consumes
`ReadinessSnapshot.startup_outcomes` to flag releases that landed on
a degraded boot.

### Tournament platformization

Migrate `services/tournament_state_service.py` and the
`cogs/rps_tournament_cog.py` / `cogs/deathmatch_cog.py` cogs to
produce `SetupOperation` batches routed through
`services.setup_operations.apply_operations`.  Large; split per-cog.

### Config arbitration / per-guild access audit

Audit direct `db.get_setting` / `guild_settings` reads in
moderation / roles / logging / deathmatch / blackjack / governance.
Move static `ALLOWED_CHANNELS` in `disbot/config.py` behind a
per-guild access policy service.

---

## 4. Rejected / WONTFIX

### Runtime danger-signs dashboard

Merged into the PR-01b readiness snapshot.  The original source plan
proposed a separate dashboard; the revision plan merged this into
`ReadinessSnapshot` so there is exactly one place that composes
deploy-relevant signals.  Future danger-signal surfaces should
extend the snapshot, not build a parallel dashboard.

---

## 5. Ideas Lab follow-ups

### Automated Discord smoke runner

PR-05 (#251) ships the smoke checklist as a doc.  An automated
runner is a stretch goal that would call read-only Discord APIs on a
5-minute interval when `SMOKE_TEST_GUILD_ID` is set.  Off by default;
env-gated.

---

## Recommended merge order

1. Foundation already on main: #244 .. #252.
2. Open now, no canary gate: **#253** (PR-06c help filter).
3. After **#247 canary**: **#255** (remove `_APP_TASKS`).
4. After **#252 canary**: **#256** (preflight default-on + render).
5. Last (this ADR): **#254** — merges after #253, #255, #256 are
   either merged or definitively decided.

## Tracking

When a deferred item ships, replace its **Status** line with
`shipped in #NNN — YYYY-MM-DD` and leave the rest of the section
intact for archaeology.
