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

- `claude/modest-ptolemy-2xipoh` · design capture — routine dispatch / staged deep-clean /
  planning sectors (owner discussion) · `docs/ideas/` + router Q-0137 · 2026-06-14
- `claude/hopeful-allen-home-slice-c` · mining Slice C — Home structure (character-card backdrop) ·
  `disbot/{utils/mining/structures,services/mining_workflow,utils/character_render,views/mining,
  cogs/mining_cog,utils/mining/market}` + plan/numbers · 2026-06-15

## Recently cleared

- `claude/brave-sagan-s9th8h` · Hermes investigation + model swap — context-compaction fix, SOUL
  git-pull sync fix, `apply_context_fixes.sh` + size guard, self-healing repo sync, model/provider
  playbook; **gpt-5.4-mini now live on the owner's own OpenAI key** · 2026-06-15 ·
  **PRs #913–#919 (merged) + close-out**
- `claude/amazing-volta-auxt2d` · mining hub UX overhaul — in-place image cards · Workshop sub-hub
  + Craft consolidation · 3-layer Category→Type→Variant browsers (craft + market) + shared
  `utils/mining/taxonomy.py` · rarity/body ordering · shields→Weapons + shield damage · stat
  previews · the **3-layer menu doctrine** (hub-ui-standard.md) · 2026-06-15 ·
  **PR #911 (auto-merge on green)**
- `claude/hopeful-allen-sfus5i` · P1-3 machine-checkable contract invariants — 2 new CI invariants
  (settings declared→consumer parity · games wager-boundary completeness) + AI/BTD6 closed via
  disposition doc · `tests/unit/invariants/` + `docs/planning/production-readiness/` · 2026-06-15 ·
  **PR #917 (open, auto-merge on green)**
- `claude/hopeful-allen-sdjqjs` · mining Slices E + F — respec polish + skill/milestone titles ·
  `skill_service`/`skills_panel` (E) + `utils/mining/titles` + `title_service` + `titles_panel` +
  `character_panel` + migration 074 (F) · 2026-06-15 · **PR #912 (open, auto-merge on green)**
- `claude/hopeful-allen-r7qsg8` · Railway log-triage analyzer (Slice 4, Q-0130) — deterministic
  content-free triage tool + skill wiring · `scripts/hermes/log_triage.py` +
  `docs/operations/hermes-skills/log-triage.md` · 2026-06-15 · **PR #906 (merged)**
- `claude/eval-coverage-expansion-2026-06-15` · P1-1 eval-coverage expansion — 6 golden
  tool-selection probes (14→20/34) · `tests/evals/cases.py` + `test_eval_coverage.py` · 2026-06-15 ·
  **PR #886 (open, auto-merge on green)**

- `claude/exciting-brahmagupta-1duzde` · mining §7.5 **Vault** (safe stash) + turn-key
  **structures/skill-tree plan** for the night session · `disbot/{migrations,utils/db/games,
  services/mining_workflow,views/mining,cogs/mining_cog}` + the plan doc · 2026-06-14 ·
  **PR #884 (open, auto-merge on green)**
- `claude/ecstatic-euler-bslyvd` · sector tooling — `check_sector_map.py` (validator) +
  `dispatch_menu.py` (resolver) + 19 tests + folio map · 2026-06-14 · **PR #882**
- `claude/wizardly-edison-xw34kb` · P1-1 — close eval-coverage gap on BTD6 hotspot tools (dog-food
  #879; 8→14/34) · `tests/evals/cases.py` + `test_eval_coverage.py` · 2026-06-14 ·
  **PR #881 (open, auto-merge on green)**
- `claude/ecstatic-euler-bslyvd` · dispatch-test fixes — executor dimension + startability tags +
  S1 freshness (Q-0143) · docs-only (`repo-sector-map.md` · `roadmap.md` · router · `current-state.md`) ·
  2026-06-14 · **PR #880**
- `claude/wizardly-edison-xw34kb` · eval-coverage drift guard (Q-0089 idea, owner-approved) ·
  `tests/evals/test_eval_coverage.py` · 2026-06-14 · **PR #879 (merged)**
- `claude/wizardly-edison-xw34kb` · P1-1 — versioned AI eval/smoke matrix (offline half:
  gates/fallback/tool-dispatch/audit) · `tests/evals/` + `scripts/run_evals.py` · 2026-06-14 ·
  **PR #878 (merged)**
- `claude/ecstatic-euler-bslyvd` · map roadmaps/plans onto the 5 sectors → dispatchable per-sector
  queues + dispatch contract + S↔A reconcile · docs-only (`roadmap.md` · `repo-sector-map.md` ·
  `repo-review-map.md` · `current-state.md`) · 2026-06-14 · **PR #877**

- `claude/modest-ptolemy-2xipoh` · external-systems watchlist (owner-directed docs) ·
  `docs/research/` + orientation/idea cross-links · 2026-06-14 · **PR #856 (merged)**
- `claude/nifty-allen-uwt95o` · P1-1 Layer A — BTD6 path/line-aware resolution (absence-claim
  trigger removal, design Rec #1) · 2026-06-14 · **PR #855**
- `claude/p0-2-content-free-media-diagnostics-2026-06-14` · P0-2 follow-up — content-free
  media diagnostics (`!platform media` + `media` provider + cache-health/provider-outcome
  counters) · 2026-06-14 · **PR #854 (open, auto-merge on green)**
- `claude/epic-turing-p8tyux` · P1-2 health findings lifecycle + operational retention (Q-0097) ·
  2026-06-14 · **PR #843 (merged; session-close docs in a small follow-up PR)**
- `claude/trusting-goldberg-po4p7s` · central test-isolation registry (Q-0089, owner-directed
  guardrail) · `tests/_isolation.py` + conftest + guardrail invariant test · 2026-06-14 ·
  **PR #833 (open, auto-merge on green)**
- `claude/gracious-ramanujan-o5wcw1` · P0-2 PR 1 — media/YouTube data-minimization +
  retention enforcement (Q-0099) · 2026-06-14 · **PR #829 (merged)**
- `claude/gracious-ramanujan-a8nnjf` · P0-4 PR 2 — channel creation + category lifecycle
  convergence (Q-0100) · 2026-06-14 · **PR #825 (merged)**
- `claude/funny-bohr-skbaoz` · P0-3 arc PR 3 — delegated-Setup apply authority (Q-0098) ·
  2026-06-14 · PR #817
- `claude/trusting-goldberg-po4p7s` · parallel-safe test suite → re-enabled `pytest -n auto`
  (~3× CI speedup; #814 follow-up) · autouse singleton resets + server_logging bus teardown ·
  2026-06-14 · **#815 (open, auto-merge on green)**
- `claude/trusting-goldberg-po4p7s` · CI-cost reduction + duplicate-work convention (Q-0126) ·
  concurrency-cancel + pip/mypy caching + claim ledger + push-batching · 2026-06-14 · **#814 (merged)**

- `claude/laughing-curie-f45zyu` · Hermes retune for gpt-5.4-mini + base/memory cleanup
  (SOUL.md capability re-tune · verified model specs · memory prune recs · investigation-doc
  archive · `apply_context_fixes.sh` slim) · `docs/operations/hermes-*` + `scripts/hermes/` ·
  2026-06-15 · **PR (open, born-red per Q-0133)**

_(move claims here with their PR # as they close, then prune older entries)_
