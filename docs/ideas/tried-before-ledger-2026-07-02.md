# The tried-before ledger — operational negative results as first-class memory (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, owner-requested harvest). Not approved for
> implementation.

## The near-miss that produced this

This session an agent analyzed Railway's *wait-for-CI* toggle from config and concluded it was
safe to enable. It wasn't — the owner had tried it before and it **"kept failing due to the fast
merges."** That knowledge existed only in the owner's head; one line of history beat a correct-
looking fresh analysis, and only luck (the owner watching live) prevented a bad re-enable. The
memory system records *decisions* (the router) and *recurring problems with fixes* (the journal) —
but **experiments that failed** have no home, so every agent eventually re-runs them.

## The idea

A small, greppable **negative-results ledger** — `docs/operations/tried-before.md` — one entry per
abandoned operational experiment: *what was tried · when · what happened · why it fails · the
condition under which it could be retried · provenance (Q-number / PR / owner chat)*. Examples to
seed it: wait-for-CI (Q-0213 item 5), the shared-append claims file (~98% conflict, Q-0195), the
Hermes review-merge gate (retired Q-0197), draft PRs (Q-0103). The binding habit (one journal-Rule
line, or folded into the pre-edit checklists): **before enabling any platform toggle or reviving a
retired mechanism, grep the tried-before ledger.**

## Why it's worth having

The whole premise of the memory system is that the next agent shouldn't need the owner present;
negative results are the highest-value knowledge that currently lives nowhere. Also a natural
**portable substrate-kit template** — every project accumulates "we tried that" scar tissue, and
the kit's orientation loop is exactly where it should surface.

## Route

S3/S4 (memory system · docs) · small/decided lane — one file + a seeding pass + a journal Rule
line. Kit template promotion rides the Phase-0 substrate work.
