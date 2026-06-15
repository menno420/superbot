# Session — Hermes research deepening (context-management root cause, verified vs. source)

> **Status:** `complete`

## What I did

Owner asked for "more research" on why the Hermes control-plane agent misbehaves (errors,
forgotten tasks, misunderstood assignments, not syncing to main) and supplied a ChatGPT
deep-research report on the Nous Research Hermes Agent. I confirmed Hermes IS that agent
(`NousResearch/hermes-agent` — our SOUL.md/skills/gateway/cron match), then **verified the
report's fix-critical claims against Hermes' own source/docs** (web) and mapped them onto
SuperBot's actual setup.

**Key correction:** both the report and our own `hermes-token-efficiency-investigation` doc
mis-diagnosed the root cause as *unbounded history growth → overflow*. Hermes' source shows the
gateway has **two-layer compaction** (agent compressor at 50%, gateway net at 85%, a 400-msg
hard valve) that **summarizes middle turns and prunes tool outputs >200 chars to a stub**. The
forgetting is that pruning of the early plan/folio read — not overflow. The 2.2M "cumulative
tokens" is a *cost* metric, not the live window.

## What shipped (PR #913, docs-only)

- `docs/operations/hermes-token-efficiency-investigation-2026-06-15.md` — appended a verified
  "## Findings" section: corrected compaction model + table of what KEEPS/SUMMARIZES/PRUNES; the
  exact `compression.*` and `prompt_caching.cache_ttl` config knobs; answers to the doc's four
  "investigate first" questions; cron (stateless `skip_memory=True` + `context_from` + pre-run
  `script`) as the bounded-dispatch fix that already exists; a symptom→mechanism→fix table; the
  SOUL.md truncation risk; upstream issues to watch (#12626, #9763); reversible VPS config to try.
- `docs/operations/hermes-operating-prompt.md` — fixed the SOUL.md sync bug: `git fetch origin
  main` alone leaves a STALE working tree (Hermes read old files even after "syncing" → the
  owner's "forgets to sync to main"). Now `git pull --ff-only origin main`.
- **Verified:** `python3.10 scripts/check_docs.py --strict` ✓ (orphan/staleness/links all pass).

## Handoff / next

- **Maintainer action (VPS):** re-run `bash scripts/hermes/install-soul.sh` to install the fixed
  sync line; consider the reversible `~/.hermes/config.yaml` tweaks in the Findings section
  (`compression.protect_last_n`↑, `prompt_caching.cache_ttl: "1h"`); verify the SOUL.md byte size
  isn't being truncated.
- **Not approved to build:** the deeper fix (bounded re-grounding for the gateway) stays a plan —
  the investigation half is now done, the fix half awaits owner go-ahead.
- BUG-0011 (gateway crash-loop) still OPEN — needs a clean foreground repro on the VPS.

## 💡 Session idea (Q-0089)

**A SOUL.md truncation guard in `install-soul.sh`.** Hermes silently truncates SOUL.md if it
exceeds its budget (verified upstream) — an *invisible* cause of "Hermes forgets its rules/
identity." The script already prints `$(wc -c)` bytes; add a warning when the rendered prompt
exceeds a known/estimated truncation threshold, so a future operating-prompt edit can't silently
get cut. Small, repo-side, kill-switchable. Dedup-checked `docs/ideas/` — none.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-15-mining-home-slice-c.md` (PR #910). Strong run — shipped Slice C with
byte-identical-when-unbuilt discipline, good test coverage, and documented the `cd`-wedge harness
incident as a load-bearing system lesson. Little to fault.
**System improvement surfaced this run:** repo-side fixes to *Hermes' own behavior* (the SOUL.md
sync fix here, skill edits, operating-prompt changes) are **inert until manually re-installed on
the VPS** (`install-soul.sh` / `install-skills.sh`), and nothing in-repo signals "the VPS Hermes
is out of sync with the repo's Hermes docs." The control-plane state table tracks secrets/deploys
but not install-freshness. Worth a row there (or a router DISCUSS): a tracked "SOUL/skills
installed at repo SHA X" marker so an edit like this one doesn't quietly fail to take effect.

## 📋 Doc audit (Q-0104)

`check_docs --strict` green (both edited docs already reachable — investigation linked from
`hermes-control-plane.md`, operating-prompt linked from several). No new owner decision to route
(the config recommendations are reversible suggestions, not decisions). The active-work claim
moves to Recently-cleared when #913 merges. No chat-only content left undocumented — the findings
are in the investigation doc, the fix in the operating prompt. Ledger unaffected (docs-only).
