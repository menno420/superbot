# Session: capture — routine dispatch, staged deep-clean reconciliation, planning sectors

> **Status:** `in-progress`

**Branch:** `claude/modest-ptolemy-2xipoh` · **PR:** TBD · **Date:** 2026-06-14 · **Type:** owner design discussion — capture + opinion (manual)

## What I'm about to do
Owner dropped a substantial design direction in chat (three threads): (1) dispatch every routine via
Hermes *except* reconciliation; (2) evolve reconciliation into a larger **staged deep-clean** (surface
problems, de-stale docs, dispose of open PRs/branches, review shipped work, refactor the roadmap, keep
a healthy balance of stability vs. new-feature backlog); (3) divide the repo into **planning sectors**
— bot · BTD6 (added mid-discussion) · the agent/AI-memory substrate · the documentation system · with
in-bot AI treated as integrated into the bot. Asked my opinion + "have I forgotten anything?".

Capture this durably (owner intent must not stay in chat) as an idea doc + a DISCUSS-lane router
Q-block, mark it provisional (discussion still flowing), and clear my stale active-work claim from the
merged #856 watchlist session (Q-0126 drift). Opinion delivered in chat; key addition = a missing
**Operations / control-plane** sector.
