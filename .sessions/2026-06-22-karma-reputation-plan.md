# Session — 2026-06-22 · Karma (thanks/upvote reputation) — plan-first

> **Status:** `in-progress` — born-red HOLD card; flip to `complete` as the final step.

**Run type:** owner-directed (one-word prompt "Karma"). **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** maintainer dropped the idea "Karma"; clarified via AskUserQuestion → **plan it first**,
flavor **thanks/upvote reputation**. Deliverable is a `docs/planning/` plan + roadmap horizon, then
await go-ahead to build (no implementation this session).

## What I'm about to do

Design a **Karma** subsystem: members grant each other reputation (thanks/upvote), tracked per-user
with an audited mutation seam and a leaderboard provider — modelled on the existing economy/XP
patterns (DB layer → `*_service.py` with audit + EventBus emit → cog → settings spec → invariant
test → leaderboard provider). Produce: (1) an idea-capture in `docs/ideas/`, (2) a buildable plan in
`docs/planning/` (2–3 PR slices), (3) a `docs/roadmap.md` Someday/Next horizon row + `docs/planning/README.md`
index entry. Plan-only — no `disbot/` code.

## What changed

_(filled at close)_

## 💡 Session idea (Q-0089)

_(filled at close)_

## ⟲ Previous-session review (Q-0102)

_(filled at close)_

## 📋 Doc audit (Q-0104)

_(filled at close)_
