# Active work — parallel-agent claim ledger

> **Status:** `living-ledger` — append-only coordination file. Not a roadmap, not a tracker
> of merged work (that's `docs/current-state.md`). Source + merged PRs win. Owner decision
> Q-0126 (2026-06-14).

## What this is

A lightweight **claim ledger** so parallel agent sessions don't duplicate each other's work.
The maintainer runs several Claude Code sessions at once; two of them picking up the same task
is pure waste. This file makes "what is someone already on?" answerable **before** a PR exists.

## How to use it (per CLAUDE.md § Session & plan workflow)

1. **Before starting**, scan **this file's Active claims** *and* the open / recently-closed PRs
   (`list_pull_requests`). If your task is already claimed or in flight, coordinate or pick
   something else — don't duplicate it.
2. **Append one claim line** under **Active claims** in the format:
   `` `branch` · scope · expected files/area · date · (optional) agent ``
3. **At session close**, remove your line (or move it to **Recently cleared** with the PR #).
   A claim is a soft signal, not a lock — stale lines are fine to prune when you see them.

Keep it short. This is a whiteboard, not an audit trail — the durable record is the PR + the
living ledger (`docs/current-state.md`).

## Active claims

- `claude/magical-rubin-jnpnuw` · **dashboard.json structural-drift reporter** + freshness catch-up
  (executes the #1020 💡 idea + finding) · `scripts/check_dashboard_data.py` ·
  `dashboard/data/dashboard.json` · tests · 2026-06-17 · **auto-merge on green**
- `claude/tender-noether-h5lpp1` · **night work queue** (owner directive) — seed a grounded queue of
  read-only deterministic BTD6 floor builders (AI §7.5/§7.6 lane) for the scheduled dispatch fires +
  repoint `current-state.md` ▶ Next action · `docs/planning/night-queue-2026-06-16.md` ·
  `docs/current-state.md` · 2026-06-16
- `claude/dashboard-vision-review` · **review the finalized-state vision plan** (owner directive) +
  session close — reviewer note (status correction + 4 refinements) on
  `dashboard-vision-finalized-state.md`; fold the write-side PRs into the ledger; mark the control panel
  LIVE · `docs/planning/` · `docs/current-state.md` · 2026-06-16
- `claude/dashboard-data-integrity-guard` · `scripts/check_dashboard_data.py` — stdlib integrity
  guard for the exported `dashboard.json` (cog→subsystem resolution · count integrity · required
  fields) + test · `scripts/` · `tests/unit/scripts/` · 2026-06-16
- `claude/upbeat-einstein-7rz9z0` · act on the 2026-06-16 autonomous-run review + owner answers —
  run-report footer · ledger guard-exemption + drift line · bug-fix-guard convention · auto-deploy
  misinformation fix · Q-0147 DM gate · Q-0085/0120/0121/0127 records · ledger tidy · 2026-06-16
- `claude/epic-noether-qgis28` · BTD6 Live Events — fix the dead event drill-down
  (`build_event_detail_view_model` `TypeError`) + current-event-first overview redesign (show only
  the live event + all its info; history behind 📜 Past events) · `services/btd6_view_model_service.py`
  · `views/btd6/live_events_view.py` · `cogs/btd6/_event_helpers.py` · 2026-06-16

- `claude/peaceful-tesla-vvayya` · PR mergeability keepers — auto-update behind + red-on-conflict
  guard (Q-0154) · `.github/workflows/{pr-auto-update,pr-conflict-guard}.yml` · 2026-06-16

## Recently cleared

- `claude/magical-rubin-bq71go` · manifest spine **PR3** — control-API `GET /control/manifest` read +
  cross-manifest reconciliation (`dangling_panel_action`) + AST-vs-panel-registry drift guard +
  deploy-SHA badge · 2026-06-17 · **PR #1020 (auto-merge on green)**
- `claude/magical-rubin-p92toz` · manifest spine **PR2** — panel registry + `PanelManifest`
  (`core/runtime/panel_manifest.py` + `persistent_views` PANEL_ID/enumeration + command-panel join) ·
  2026-06-17 · **PR #1019 (auto-merge on green)**
- `claude/inspiring-wozniak-i92q58` · dashboard **Phase E** — control-API read endpoints + see-then-change
  editor · 2026-06-17 · **PR #1013 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard **R3** — live-surface hardening (CSRF + rate-limiting) ·
  2026-06-17 · **PR #1014 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard **vision-roadmap reconcile** (Phase C read workspace was
  built in parallel by **#1015** and merged first — authoritative; this run's duplicate was dropped) ·
  2026-06-17 · **PR #1016**
- `claude/health-server-ipv6-bind` · health server IPv6 dual-stack bind (Railway private networking) · 2026-06-16 · **PR #1001 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard finalized-state vision plan · 2026-06-16 · **PR #1002 (merged)**
- `claude/control-panel-web` · control panel — Discord OAuth login + editors (write side step 2) · 2026-06-16 · **PR #996 (merged)**
- `claude/control-api-write-side` · control API mutation endpoints (write side step 1) · 2026-06-16 · **PR #993 (merged)**
- `claude/practical-turing-pnppjf` · dashboard `/commands` management surface (READ side) — Manage
  button on every command + cog, per-item panels + per-command alias box · 2026-06-16 · **PR #988 (merged)**
- `claude/kind-carson-736rnk` · dashboard `/settings` + `/access` read-only pages + live help-editor
  design doc (Q-0156) · 2026-06-16 · **PR #977 (merged)**
- `claude/jolly-cannon-gn9ddg` · developer dashboard (personal website) — design + read-only MVP (Phase 1) · 2026-06-16 · **PR #967 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · count-citation guard + session-close notes (Q-0151, atlas thread #3)
  — soft `check_docs` inventory-count rule · 2026-06-16 · **PR #964 (auto-merge on green)**
- `claude/peaceful-tesla-vvayya` · Hermes efficiency — idea-spotlight · morning-briefing ·
  dispatch-resolve skills + 6h auto session-reset · 2026-06-16 · **PR #959 (auto-merge pending)**

> Trimmed 2026-06-16 (Q-0152): stale claims whose PRs merged are dropped — the durable record is the
> PR + the `current-state.md` ledger. Keep this to the most recent handful, newest-first.

- `claude/reconcile-1021-docs` · band-#1020 Q-0107 docs reconciliation (issue #1021) — ledger fix + trim · control-plane tick · moderation-DM idea→plan · next-band plan · 2026-06-17 · **docs-only, self-merge on green**
- `claude/gifted-noether-37tiwr` · BUG-0015 — "d67 dart paragon" misread as "0-6-7": parse + route + ground a paragon degree (1-100) · 2026-06-16 · **PR #963 (auto-merge on green)**
- `claude/magical-rubin-u3arq6` · AI §7.5 paragon base-cost comparison floor (last unbuilt comparison member) · 2026-06-16 · **PR #962 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · thin architecture atlas (PR 2, Q-0151a) — `scripts/atlas.py` composer + `role` in `context_map.py` + companion doc + tests · 2026-06-16 · **PR #960 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · extension-taxonomy crosswalk (Q-0151c) — overlay + generator + CI guard + plan · 2026-06-16 · **PR #958 (merged)**
- `claude/hopeful-meitner-772pv8` · architecture-atlas / structure-review idea intake (owner-uploaded review) · router Q-0151 · 2026-06-16 · **PR #957 (merged)**

- `claude/coglist-command` · `!coglist` real command → admin "📋 Cog List" view · 2026-06-16 · **PR #951 (merged)**
- `claude/fix-coglist-resolution-loop` · BUG-0014 — `!coglist` infinite "assumed from" loop · 2026-06-16 · **PR #949 (merged)**
- `claude/keen-heisenberg-xqro71` · runtime lock early release (fix ~85s deploy downtime) · 2026-06-16 · **PR #948 (merged)**
- `claude/hopeful-allen-qt5ax3` · games-economy faucet/sink diagnostic (`!platform economy`) · 2026-06-16 · **PR #937 (merged)**
- `claude/myprofile-card-pra` · myprofile PR A + B — `/myprofile` card + self-service editor · 2026-06-16 · **PR #938 / #940 (merged)**

_(move claims here with their PR # as they close, then prune older entries)_
