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

- `claude/hopeful-meitner-772pv8` · count-citation guard (Q-0151, atlas thread #3) — soft `check_docs`
  rule flagging uncited inventory counts in binding docs · `scripts/check_docs.py` + tests + idea-doc
  updates · 2026-06-16
- `claude/upbeat-einstein-7rz9z0` · act on the 2026-06-16 autonomous-run review + owner answers —
  run-report footer · ledger guard-exemption + drift line · bug-fix-guard convention · auto-deploy
  misinformation fix · Q-0147 DM gate · Q-0085/0120/0121/0127 records · ledger tidy · 2026-06-16
- `claude/epic-noether-qgis28` · BTD6 Live Events — fix the dead event drill-down
  (`build_event_detail_view_model` `TypeError`) + current-event-first overview redesign (show only
  the live event + all its info; history behind 📜 Past events) · `services/btd6_view_model_service.py`
  · `views/btd6/live_events_view.py` · `cogs/btd6/_event_helpers.py` · 2026-06-16

## Recently cleared

> Trimmed 2026-06-16 (Q-0152): stale claims whose PRs merged are dropped — the durable record is the
> PR + the `current-state.md` ledger. Keep this to the most recent handful, newest-first.

- `claude/hopeful-meitner-772pv8` · thin architecture atlas (PR 2, Q-0151a) — `scripts/atlas.py` composer + `role` in `context_map.py` + companion doc + tests · 2026-06-16 · **PR #960 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · extension-taxonomy crosswalk (Q-0151c) — overlay + generator + CI guard + plan · 2026-06-16 · **PR #958 (merged)**
- `claude/hopeful-meitner-772pv8` · architecture-atlas / structure-review idea intake (owner-uploaded review) · router Q-0151 · 2026-06-16 · **PR #957 (merged)**

- `claude/coglist-command` · `!coglist` real command → admin "📋 Cog List" view · 2026-06-16 · **PR #951 (merged)**
- `claude/fix-coglist-resolution-loop` · BUG-0014 — `!coglist` infinite "assumed from" loop · 2026-06-16 · **PR #949 (merged)**
- `claude/keen-heisenberg-xqro71` · runtime lock early release (fix ~85s deploy downtime) · 2026-06-16 · **PR #948 (merged)**
- `claude/hopeful-allen-qt5ax3` · games-economy faucet/sink diagnostic (`!platform economy`) · 2026-06-16 · **PR #937 (merged)**
- `claude/myprofile-card-pra` · myprofile PR A + B — `/myprofile` card + self-service editor · 2026-06-16 · **PR #938 / #940 (merged)**

_(move claims here with their PR # as they close, then prune older entries)_
