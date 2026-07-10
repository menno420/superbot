# Session — round-3 dispatch, part 4d: games relay pasted + manager prompt registry

> **Status:** `in-progress`
> **Run type:** owner-directed · same live dispatch chat (parts 4/4b/4c: PRs #1957/#1963/#1964, merged)
> **Model/time:** fable-5 · 2026-07-10 ~21:5xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1964).

## What is about to happen

Owner reported live: the games-mapping relay (with the read-only-data-API input) is
PASTED to the manager, and the manager is preparing a **centralized prompt registry**
(one home for all Custom Instructions / briefs / wake prompts). Record both in the
runbook (the "relay drafted, pending" rows are now stale), add the registry fact +
one-source-of-truth rule to the gen-3 standard §4 fold-back, and commit the
registry-ingest paste block durably (part-4c's review flagged that gating paste blocks
lived only in chat).
