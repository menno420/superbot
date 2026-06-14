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

_(no active claims)_

## Recently cleared

- `claude/trusting-goldberg-po4p7s` · parallel-safe test suite → re-enabled `pytest -n auto`
  (~3× CI speedup; #814 follow-up) · autouse singleton resets + server_logging bus teardown ·
  2026-06-14 · **#815 (open, auto-merge on green)**
- `claude/trusting-goldberg-po4p7s` · CI-cost reduction + duplicate-work convention (Q-0126) ·
  concurrency-cancel + pip/mypy caching + claim ledger + push-batching · 2026-06-14 · **#814 (merged)**
