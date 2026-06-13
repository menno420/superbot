# Idea: lane-scoped session state to cut parallel-session merge tax

> **Status:** `ideas`

**Captured:** 2026-06-12 · **Context:** orientation review, agent-memory system follow-up

## Problem
Parallel sessions keep colliding on shared artifacts: the journal, `current-state.md`, and the Q-router can race, producing duplicate Q-numbers, overwritten ledger bullets, and post-hoc merge resolution. The current resolution (UNION / answered-entry-wins / renumber-to-tail) works, but it is cleanup after the fact, not prevention.

## Proposal
Move to **lane-scoped state** as the default for in-flight session data:
- Each session writes only its own lane/lane-prefix sub-file under `.sessions/` and `docs/ideas/`
- A lightweight aggregation step builds the merged view for humans/Routines on demand
- For the Q-router, require scoped prefixes per lane/Q-block and disallow bare reuse of already-taken numbers

## Value
Fewer merge conflicts, cleaner history, less “small-feature” tax from reconciliation, and simpler extraction to a portable package later (each session’s contribution is already namespaced).
