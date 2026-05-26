# Discord smoke-test checklist

> **Status:** SuperBot 2.0 — PR-05.
> Run this checklist before merging anything that touches startup,
> task ownership, the consistency report, or the readiness snapshot.

This page is the manual companion to the readiness snapshot
(`services.platform_consistency.build_readiness_snapshot()`).  Every
checklist item below corresponds to a field on the
`ReadinessSnapshot` dataclass, so once you have looked at the live
`!platform diagnostics` output you can tick each item directly from
the rendered snapshot.

The doc-test `tests/unit/docs/test_smoke_test_checklist.py` pins
this 1:1 correspondence, so adding a field to `ReadinessSnapshot`
without surfacing it here (or removing one without removing the
matching bullet) will fail CI.

---

## Boot path

- [ ] **Boot completes without unhandled exception** — `bot.log`
      shows the "Starting bot..." line followed by the discord.py
      ready event.
- [ ] **Runtime lock acquired** — `services.runtime` log line
      "Runtime lock acquired ...".  A loser replica should exit with
      code 0; a leader should proceed to startup.
- [ ] **Heartbeat task spawned** — heartbeat task appears in the
      managed task supervisor.  See *tasks > active_names* below.

## Health & readiness probes

- [ ] **`GET /health`** returns 200 with non-empty body.
- [ ] **`GET /ready`** returns 200 (or 503 until `bot.is_ready()`
      flips).
- [ ] **`GET /metrics`** returns a Prometheus expo with at least
      `task_outcome_total` and `identity_contract_findings_total`.

## Consistency report

Inspect `!platform consistency` and the readiness snapshot's
`consistency_overall_status` / `consistency_blocking_sections`:

- [ ] **`consistency_overall_status` is CLEAN** *or* every WARNING /
      FATAL / SKIPPED section in `consistency_blocking_sections`
      has been triaged.
- [ ] **`consistency_report_at`** is recent (within the last hour
      on a long-running replica).  A `None` value indicates
      `collect_report` was never called — run `!platform consistency`
      to populate the cache.
- [ ] **No collector raised** — every typed `ReadinessKind` must
      have a corresponding section in the report, all stamped by
      the orchestrator.

## Startup outcomes

Inspect the readiness snapshot's `startup_outcomes`:

- [ ] **`command_surface_ledger`** outcome.success == True
- [ ] **`settings_registry`** outcome.success == True
- [ ] **`customization_catalogue`** outcome.success == True
- [ ] **`resource_provisioning_catalogue`** outcome.success == True

A failure here is non-fatal at boot but blocks subsequent setup /
diagnostic surfaces.  Cross-check the `bot.log` warning for the
exception summary.

## Catalogue & registry state

Inspect the snapshot's `catalogues` block (also surfaced as
`get_cached_*()` accessors):

- [ ] **`ledger_built`** == True (`command_surface_ledger.get_cached_ledger()` non-null)
- [ ] **`settings_registry_built`** == True
- [ ] **`customization_catalogue_built`** == True
- [ ] **`provisioning_catalogue_built`** == True

If any of these are False, the corresponding `startup_outcomes`
entry should explain why.

## Background tasks

Inspect the snapshot's `tasks` block (or `!platform tasks`):

- [ ] **`tasks_active_count`** matches the expected set (heartbeat,
      health server, session_gc, process_memory_sampler, optional
      scheduler — see `tasks_active_names` for the canonical list).
- [ ] **No task showing up twice** — PR-02b removed the
      double-supervision of the automation scheduler.  Two entries
      with the same name is a regression.

## Setup wizard smoke

The 5 setup slash commands are all live; smoke each one to confirm
the wizard's read-only surfaces respond without raising.  The
prefix `!setup` opens the wizard hub.

- [ ] **`!setup`** opens the wizard hub without raising.
- [ ] **`/setup-status`** returns the current draft state (read-only).
- [ ] **`/setup-reset`** clears staged operations.  Verification:
      stage one no-op operation via the hub, run `/setup-reset`,
      observe the draft empties.
- [ ] **`/setup-skip <section>`** marks a section skipped without
      mutating its underlying state (read-only effect on bindings;
      writes only `setup_session_skipped_sections`).
- [ ] **`/setup-unskip <section>`** clears the skip flag.
- [ ] **`/setup-depth <level>`** updates the wizard depth hint —
      verify the chosen depth appears in `/setup-status` afterwards.

### Setup readiness + preflight

- [ ] **`!platform setup-readiness`** renders the per-guild
      readiness inventory and matches the readiness snapshot's
      setup blocker summary.
- [ ] **Setup preflight diff** appears in Final Review when
      `SETUP_PREFLIGHT_DIFF` is on (default).  Each staged op shows
      a current → proposed line OR a "preflight unavailable" badge
      for op kinds without a read adapter.  Type-equivalent values
      (e.g. boolean `True` vs string `"true"`) must NOT show as a
      diff — see `services.setup_change_plan.values_equivalent`.
- [ ] **Setup blocker output** in `!platform consistency` matches
      the dynamic `services.setup_blockers.BLOCKERS` registry
      (resolved blockers drop out; pending blockers retain their
      `doc_anchor` link).

### Apply path

- [ ] **Final Review apply** runs through
      `services.setup_operations.apply_operations` (verify via the
      audit row: per-op `mutation_id` present, per-op `error`
      empty).

## Help / navigation

- [ ] **`!help`** dropdown opens; the route resolver does not raise.
- [ ] **`!help <subsystem>`** routes to the canonical hub for every
      hub-routable subsystem (smoke a few: economy, games, admin).
- [ ] **`!platform setup-readiness`** renders the per-guild
      inventory and matches the readiness snapshot's setup blocker
      summary.

## Command-access onboarding

The command-access onboarding fix (migrations 050 + 051) is the
canonical admission path for every prefix + slash command.  Smoke
each shape so a regression in resolver / cog wiring / settings UI /
migration is caught before it strands fresh guilds again.

- [ ] **Fresh guild, no DB row** — invite the bot to a clean test
      guild.  `!help` works for the operator (bootstrap bypass) and
      `!bj` works in any channel (unconfigured guild defaults to
      `all_channels`).  `/blackjack` matches.
- [ ] **`!settings → Command access`** opens the policy panel and
      renders the current mode + allowed channels.  Switching to
      `selected_channels` mode, picking one channel, and clicking
      back to Hub returns to the hub embed without raising.
- [ ] **`selected_channels` denial** — with the policy from the
      previous step, `!bj` in a non-allowed channel posts the
      "Commands aren't enabled in this channel…" reply
      (`delete_after=10`) and the command does not run.
      `/blackjack` in the same channel posts the same text as an
      ephemeral.
- [ ] **`disabled_except_bootstrap`** — switching to this mode and
      running `!bj` posts the "Commands are disabled…" feedback;
      `!setup` and `!settings` still work for the operator
      (bootstrap bypass intact).
- [ ] **`!platform command-access [#channel]`** prints the
      structured decision embed: configured mode, allowed
      channels, decision (yes/no), reason code, source, and the
      bootstrap probe.  No audit row is emitted by the probe
      (check the `audit_log` table after the run).
- [ ] **Main-server backfill** — confirm migration 051 wrote a
      `selected_channels` row for the main server (
      `SELECT * FROM guild_command_access_policy WHERE
      guild_id = <main_server_guild_id>;`).  Verify `!bj` still
      works in the configured channels and is denied elsewhere.
- [ ] **Metric stream** — scrape `/metrics` while exercising the
      above.  `command_access_decisions_total{decision="allow"}`
      and `…{decision="deny"}` both increment with the correct
      reason/source labels.


## Shutdown drain

Trigger `SIGTERM` (or run `kill -TERM $PID`) and observe:

- [ ] **Heartbeat stops** — log line "Runtime lock released" or
      similar within 1 s.
- [ ] **Managed task drain completes within 5 s** — every entry in
      `tasks.active()` is either done or has been cancelled.
- [ ] **DB pool closed** — final log line "Bot exiting cleanly" or
      no `asyncpg` warnings on stderr.

## Smooth Interaction Pass — UX guarantees

These bullets pin the user-facing guarantees of the Smooth Pass
PRs (Platform hub completeness, back-button coverage, solo-game
instant replay). Smoke any UI-touching PR against them.

### Platform hub completeness

- [ ] **`!platform` overview** shows five sections: Runtime/status,
      Catalogues, Resources/rollout, Validation, Mutations/managers.
- [ ] **`lifecycle`** appears in the Runtime/status dropdown and
      renders the same embed as typed `!platform lifecycle`.
- [ ] **`setup-readiness`** appears in the Validation dropdown and
      renders the same embed as typed `!platform setup-readiness`.
- [ ] **`🚩 Flag manager` button** on row 4 opens the editable
      `FlagManagerView`, identical to typed `!platform flag`.
- [ ] **Overview** button on row 4 returns to the platform hub
      overview embed.

### Back-button coverage

Pinned by `docs/ui-view-adoption-audit.md` §9 — every user-facing
subpanel has either an `attach_back_button`-driven Back or is
classified as none-needed.

- [ ] **Channels subpanels** (`Create / Delete / Restrict /
      Visibility`) all return to `_ChannelManagerView` via Back.
- [ ] **Roles subpanels** (`Management / Diagnostics / XpRoles /
      TimeRoles / ReactionRoles`) all return to `RoleHubView` via
      Back when opened from the hub.
- [ ] **Economy subpanels** (`Shop / Work / Work-result`) all
      return to `EconomyPanelView` via Back; `_ShopSubView`
      preserves the AB2 back-target chain to Help when present.
- [ ] **`XpConfigView`** opened from `!xpmenu` → ⚙️ Configure
      returns to `_XpHubView` via Back; typed `!xpconfig`
      intentionally has no Back (no parent).

### Solo-game instant replay

- [ ] **Solo RPS result view** (`!rps 0` or `!rps <bet>`) shows
      `🔁 Play again` + `◀ Back to RPS` on row 1. Move buttons on
      row 0 remain visible-but-disabled.
- [ ] **Solo RPS replay** spawns a fresh playable round at the
      same bet. Insufficient balance → ephemeral nudge, no view
      swap.
- [ ] **Solo Blackjack result view** (`!blackjack 0` or
      `!blackjack <bet>`) shows `🔁 Play again` + `◀ Back to
      Blackjack` on row 1. Hit/Stand/Double buttons remain
      visible-but-disabled.
- [ ] **Solo Blackjack replay** routes through
      `cogs.blackjack.actions.start_solo_blackjack` — `_active`
      map is cleared first, persistence (`_save_game_state`) lands
      on the new hand. Insufficient balance / "already playing" /
      natural-blackjack auto-payout all surface correctly.
- [ ] **PvP / tournament** Blackjack and RPS hands finish with no
      replay row attached (gate is solo-only:
      `tournament_chips is None AND on_finish is None`).

### Interaction-safety wrappers

Pinned by `docs/ui-view-adoption-audit.md` §3 — hotspots converted
to `safe_defer` + `safe_edit`.

- [ ] **`_RpsView._play`** defers up front and uses `safe_edit`
      (no raw `response.edit_message` after the
      `economy_service.{credit,debit}` writes).
- [ ] **`BlackjackView.hit_btn`** defers up front and uses
      `safe_edit` (no raw `response.edit_message` after
      `_save_game_state`).

---

## Updating this checklist

When `ReadinessSnapshot` gains a new field, add a matching bullet
above (and a doc-test entry in
`tests/unit/docs/test_smoke_test_checklist.py`).  When a field is
removed, remove the bullet.  CI enforces the 1:1 correspondence so
the snapshot and the checklist cannot drift.
