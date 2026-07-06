# 2026-07-06 — Ruff migration (A3): ruff replaces black + isort

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). `check_quality.py --full`
> green (ruff format+check, tool_pins, docs, consistency, artifacts, mypy, **14126 pytest passed**);
> the 5 `test_atlas` errors are the pre-existing sandbox-only grimp `bot1` flake (CI unaffected).

## What this session did

Owner-directed continuation of the CI-setup arc (after #1744 merged; owner picked ruff over the
audit-seam guard / gh-permission checker via AskUserQuestion). Executed handoff item #3 / design §C.4
**A3**: **ruff replaces black + isort**, taking the python merge gate from **5 tools → 3** and removing
two-thirds of the formatter pin-drift surface (the #1074/#1315/#1556 recurring drift class).

## Shipped (PR #1745)

- **`pyproject.toml`** — enabled the `I` (isort) rule + `[tool.ruff.lint.isort]`
  (`known-first-party = ["disbot"]`); removed `[tool.black]` / `[tool.isort]`. Ignored the
  formatter-conflicting `COM812`/`COM819`/`ISC001` (ruff format now owns trailing commas + string layout;
  ruff *warns* if these lint rules stay on). Per-file-ignored `I001` on `disbot/core/runtime/__init__.py`
  (ruff's combine garbles its per-line `# noqa: F401 — re-exported` comments; kept its clean layout).
- **Reformat** — `ruff format` the tree (~95 files) + `ruff check --fix --select I` (8 import
  normalizations). Behavior-preserving (net −80 lines, mostly import combining). Magic-trailing-comma
  parity vs `black 26.5.1` verified: black agreed on all but the 14 known ruff-vs-black files.
- **Regenerated the 2 committed artifacts the reformat drifted** (the full CI mirror caught them):
  substrate-kit `dist/bootstrap.py` (bundles reformatted `src/`) + `docs/operations/env-vars.md`
  (a line-number moved 1417→1418).
- **Swapped black/isort → ruff across every surface** (same commit, or local/CI drift): the design's five
  (`code-quality.yml`, `requirements-dev.txt`, `.pre-commit-config.yaml` [→ `ruff-format` hook],
  `check_quality.py`, `claude_post_edit.py`) **plus** three the design didn't name —
  `claude_stop_check.py` (Stop hook), `check_routine_permission_surface.py`, `setup_dev_env.sh` — and the
  two guard tests (`test_check_quality_ci_parity`, `test_check_tool_pins`). `check_tool_pins._TOOLS` →
  `("ruff","mypy")`. Narrative comments in 2 app-CI workflows + 2 scripts de-drifted.
- **Docs** — handoff item #3 + design A3/progress-block marked shipped.

## State after this session

- ✅ Python merge gate is now **ruff (format+lint+import-sort) · mypy · pytest** — 3 tools, 1 pin family.
- ✅ `check_tool_pins` guards the single remaining formatter pin (ruff) across the 3 surfaces.
- ▶ Remaining CI backlog (handoff): the `ci.yml`/`web-ci.yml`/`pr-freshness.yml` restructure (A5/A8/A9,
  owner-gated cutover), the two AST guards, `check_session_slug_unique` gate, the live-verify items.

## 🛠 Friction → guard (Q-0194)

- **The migration's "5 files" was really 8+ surfaces.** Hunting them down was a manual grep sweep; a
  missed one (e.g. a leftover `black` hook in pre-commit) would silently drift local vs CI. **Guard
  proposed (this session's Q-0089 idea):** extend `check_tool_pins` to assert the formatter tool *set* is
  identical across surfaces, not just versions. Filed, not built (checker idea, validate-then-adopt).
- **The full CI mirror is load-bearing for a reformat.** `check_quality.py --check-only` was green but the
  reformat had drifted 2 committed *generated* artifacts (bootstrap bundle, env-vars line-number head) that
  only the full pytest catches. Lesson (already a rule): never trust `--check-only` alone before pushing a
  whole-tree change — run `--full`. No new guard needed; the existing tests did their job.

## Context delta (reflection interview)

- **Needed but not pointed to:** nothing routed me to the fact that a whole-tree reformat drifts *generated
  artifacts* (bootstrap bundle, env-vars doc). The reformat→regenerate coupling is only discoverable by the
  failing tests. A one-liner in the ruff-migration recipe ("re-run `build_bootstrap.py` + `scan_env_usage.py
  --write-doc` after the reformat") would pre-empt it — added to the handoff's item #3 record implicitly.
- **Pointed to but didn't need:** the design's "the five files" list — accurate but incomplete; I relied on
  a repo-wide `grep` instead, which is the reliable method for a swap like this.
- **Discovered by hand:** (1) ruff format conflicts with the `COM`/`ISC` lint rules (must ignore COM812/
  COM819/ISC001) — ruff warns but the design didn't call it out; (2) ruff's isort *combines* same-module
  imports where the old isort didn't, garbling per-line comments in one re-export aggregator.
- **Decisions made alone:** ignoring COM812/COM819/ISC001 (formatter owns them); per-file-ignoring `I001`
  on `core/runtime/__init__.py`; `known-first-party=["disbot"]` (mirrors the old isort `src_paths`). All
  reversible config choices; none is product intent.
- **Weak point / unverified half:** the 14 files where ruff and black diverge are now ruff-authoritative —
  a reviewer skimming the 95-file diff should know it's format-only (no behavior change; 14126 tests green
  prove it). The pre-existing `test_atlas` grimp `bot1` sandbox flake is noise, not a regression.

## ⟲ Previous-session review (Q-0102)

Previous = #1744 (my own CodeQL stuck-scan watchdog + `owner_alert`). **Strong:** clean foundation→feature
arc, honest about the unverified codeql run-shape (shipped alerting-only, not pretending it's proven), and
it caught + fixed the adjacent `issues: write` gap. **What it (and the #1743 handoff) got wrong:** the
handoff's ruff recipe said "swap in all **five**" — the real swap needed **8+** surfaces. A turn-key recipe
that under-counts its blast radius is a trap for the executing session (I only found the extra three by
grep). **System improvement (initiated):** turn-key migration recipes should be **grep-validated when
written** (list the *actual* match set, not the remembered one) — and the mechanized version of that is
this session's formatter-tool-set-consistency idea.

## 💡 Session idea (Q-0089)

**`check_tool_pins` should assert the formatter tool *set*, not just versions** — so a partial tool swap
(this migration touched 8+ surfaces) can't leave a stale `black`/`isort` reference that drifts local vs CI.
Plus a smaller finding: `.pre-commit-config.yaml` is not run by any workflow (CI only reads its pins), so a
broken hook config is unguarded. Filed:
[`ideas/formatter-tool-set-consistency-checker-2026-07-06.md`](../docs/ideas/formatter-tool-set-consistency-checker-2026-07-06.md)
+ README index entry.

## 🧹 Grooming (Q-0015)

Moved the CI backlog's highest-ranked buildable item (handoff #3, ruff) from `plan` → shipped, and re-cut
its handoff entry to record the *actual* recipe (the 8+ surfaces, the COM/ISC ignores, the `I001` exemption,
the regenerate-artifacts step) so the next tooling session inherits the real map, not the under-counted one.

## 📋 Docs audit (Q-0104)

`check_docs --strict` green (new idea reachable + indexed; handoff/design updated in place). **No new owner
decision** (the AskUserQuestion answer directed A3; it executes within Q-0239's Phase-A envelope). **Ledger:**
this session's PR #1745 is in flight; the next reconciliation folds #1744 + #1745 (marker #1740; next recon
at #1770; a manual session doesn't run the pass, Q-0124).

## 📤 Run report

- **Did:** migrated the python gate from black+isort+ruff to ruff-only (format + lint + import-sort),
  5 tools → 3, across all 8+ surfaces + 2 guard tests + 2 regenerated artifacts. · **Outcome:** shipped
- **Shipped:** #1745 — ruff migration (121 files: ~95 reformat + config/hooks/tests/docs).
- **Run type:** `manual` (owner-directed — AskUserQuestion picked A3).
- **⚑ Owner decisions needed:** none new (Q-0239 tail unchanged).
- **⚑ Owner manual steps:** none. (Pure tooling; no bot-runtime or data step. Local devs get ruff via the
  next `requirements-dev.txt` install; pre-commit users get the `ruff-format` hook automatically.)
- **⚑ Self-initiated:** the COM/ISC ignore + `I001` exemption + the 3 extra surfaces beyond the design's
  five + the formatter-tool-set checker idea — all within the owner-directed A3 scope (Q-0172).
- **↪ Next:** the CI backlog's remaining offline items — the two AST guards (bugs-first) or the
  `ci.yml`/`web-ci.yml` restructure (owner-gated cutover); or the cheap live-verify (handoff #1).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1745) |
| Python gate tools | 5 → **3** (ruff, mypy, pytest) |
| Formatter pin surfaces | black+isort removed from 8+ places; 1 pin family left (ruff) |
| Files reformatted | ~95 (net −80 lines; behavior-preserving) |
| Tests green | 14126 passed (2 stale-artifact failures regenerated + fixed) |
| CI-red rounds | born-red hold only (intended) |
| New ideas contributed | 1 (formatter-tool-set consistency checker) |
| Ideas groomed | 1 (handoff #3 → shipped, recipe corrected to the real 8+ surfaces) |
