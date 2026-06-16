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

- `claude/control-api-write-side` · control API **mutation endpoints** (write side, owner directive) —
  POST over the existing audited seams (`settings_mutation` · `help_overlay_mutation` ·
  `command_routing`); dormant-by-default + per-request live-member authority · `disbot/control_api.py` ·
  `tests/unit/runtime/test_control_api.py` · 2026-06-16
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

- `claude/hopeful-allen-1darl5` · Image moderation (Q-0108) — the safety-community family's
  last buildable slice (OpenAI omni-moderation, off by default, fail-open) ·
  `services/image_moderation_*` + `core/runtime/ai/providers/openai_moderation.py` +
  `cogs/image_moderation/` · 2026-06-16 · **PR #941 (open, needs-hermes-review)**

_(move claims here with their PR # as they close, then prune older entries)_
