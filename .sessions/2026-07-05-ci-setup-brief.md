# 2026-07-05 — CI-setup redesign brief (owner-directed prep)

> **Status:** `in-progress` — born-red card; flips to `complete` as the deliberate final step.

## What this session is doing

Owner set the *next* session's topic: **find the best-possible CI setup for the bot** — get the same
coverage with **fewer separate checks** where that helps, and **add what's genuinely needed**. Owner
aiming decisions (this session's `AskUserQuestion`): **scope = everything end-to-end** (17 Actions
workflows + 40 `check_*.py` + the Claude Code hooks); **optimize for = reliability + cost** (Actions
minutes) — consolidation is the *means* to those, not the goal.

This session **primes** that work: it inventories the current CI landscape and writes the scoping
brief, so the CI-setup session starts on the redesign, not the discovery. Docs/planning only.

<!-- Did/Outcome/enders filled in at the deliberate final flip. -->
