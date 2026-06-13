# Session — substrate-kit PR 1b tail: the two generic checker ports

> **Status:** `reference` — completed the portable substrate-kit's **PR 1b tail** (the explicit
> "▶ RESUME HERE" item left after #791–#793 / #798). Shipped as **PR #802**. Resume point is now
> **PR 2 (capability layer)**.

## What this session did

Picked up exactly where PR 798 ended — the plan
([`portable-substrate-kit-extraction-2026-06-13.md`](../docs/planning/portable-substrate-kit-extraction-2026-06-13.md))
named the 1b tail precisely: lift `check_docs` + `check_session_log` into the kit as **generic,
config-driven** ports. Delivered:

- **config** — `Config` gained `docs_root` / `sessions_dir` / `badge_tokens` / `readpath_docs` /
  `session_markers`, each a generic default factory.
- **`engine/checks/check_docs.py`** — badge / link / reachability, every input from config; host
  ratchets + freshness rule **left behind** (project policy, not portable mechanism). Returns
  `Finding` NamedTuples (no `print`) so the CLI owns output.
- **`engine/checks/check_session_log.py`** — configurable required-marker check; current log by
  **mtime** (no `subprocess` — S603 is banned in `engine/`; git was host-CI sugar).
- **cli `check`** — doc findings + an incomplete *existing* log gate `--strict`; a *missing* log is
  advisory (lint mid-session). Wired both modules into `build_bootstrap.py` + regenerated
  `dist/bootstrap.py`.
- **templates** — added a `> **Status:** `<token>`` badge to all six orientation templates so a host
  running `bootstrap check` on rendered output is badge-clean → closes the plan's **verification
  goal (d)** (proven by a render→check integration test).
- **tests** — `test_checks.py` (19 cases); kit suite 43 → 62.

Verified: `check_quality --full` green (9367 passed, 34 skipped); `check_architecture --mode strict`
0 errors; single-file `init→render→check` smoke + negative `--strict` smoke both behave.

Authoritative record: the plan's **Execution log** (repointed RESUME HERE → PR 2). Roadmap's
agent-ecosystem lane gained a one-line index for the (previously unlisted) executing plan.

## 💡 Session idea (Q-0089)

**Kit self-dogfood gate — run `bootstrap check --strict` against `examples/sample-project/` in CI.**
The kit ships a doc/session-log checker but currently only exercises it on *synthetic* fixtures and a
flat render. The plan calls for an `examples/sample-project/` (named in PR 1b, not yet built). When it
exists, add a standing test that runs the kit's **own** `bootstrap check --strict` over that real
rendered project — so the checker is proven on a true onboarded tree, and the kit *dogfoods* the very
hygiene gate it exports. Cheapest possible proof that the export actually works end-to-end, and it
turns `examples/sample-project/` from a dead fixture into a live conformance target. (Dedup-checked
`docs/ideas/` — no existing dogfood/sample-project idea.) Small, additive, sits in the harness that
already exists; natural to fold into PR 2's `examples/` build.

## ⟲ Previous-session review (Q-0102)

Reviewing the **PR 1b session (#791–#793 + the #796 resume recipe).** *Did well:* it left the single
most useful handoff I've seen in this repo — the "▶ RESUME HERE" block named the exact target files,
the exact new config fields, and the exact CI gotchas (`print`/`assert`/`subprocess` bans,
isort-checks-tests, regenerate-the-bootstrap). I hit **zero** discovery friction; the recipe was
source-accurate. That is the memory system paying off. *Could improve:* it shipped "PR 1b" without the
checkers and renamed the remainder "1b tail" — so the plan's **verbatim phase-spec line** (PR 1b "ships
the two cleanest checkers") now disagrees with what actually shipped in that PR; only the *Execution
log* records the truth. **System improvement:** when a session defers declared-in-scope work, the
closing audit should reconcile **both** the Execution log *and* the phase-spec line (or add a one-word
"(→ tail)" marker on the spec), so a plan never silently contradicts itself between its spec and its
log. I left the approved-verbatim spec untouched on purpose (it's the settled record) but made the
Execution log unambiguously the shipped-state-of-record — the lighter fix. A standing convention here
would remove the judgment call.

## Doc audit (Q-0104)

- `check_quality --full` green (9367); `check_architecture --mode strict` 0 errors.
- `check_docs --strict` + `check_current_state_ledger --strict` green; the plan doc is reachable
  (linked from the portable-agent-memory idea + now the roadmap lane).
- **current-state.md deliberately untouched** — substrate-kit is a self-contained subtree tracked in
  its **own plan Execution log** (the precedent: #789/#791–793 added no ledger entry); #802 is also not
  merged yet, so the rolling last-15 ledger gate is unaffected. Next reconciliation (#800 boundary,
  now crossed by #802) can index merged substrate PRs if it wants them in the bot ledger.
- New owner decisions: none (the plan was already owner-approved; no `AskUserQuestion` was needed —
  the resume scope was unambiguous).

## Context delta (reflection)

- **Route miss:** none — the plan's resume recipe *was* the route; orientation → plan Execution log
  was direct.
- **Route excess:** read the full 989-line plan partially; only the Execution log (≈40 lines) + §3b/§3c
  were load-bearing. Grepping the plan's headers first (the journal's own rule) would have skipped the
  693-line read.
- **Discovered by hand:** the black↔ruff **COM812** tension on awkwardly-wrapped long strings (black
  drops the trailing comma ruff then demands) — fixed by hoisting messages to module constants. Added
  to the plan's RESUME-HERE gotcha list for PR 2.
- **Decisions made alone:** badge all six templates (vs. only docs-destined) + add the render→check
  integration test — both to close verification goal (d) without making host-layout assumptions; the
  reachability dimension is intentionally left to synthetic-tree tests (host files CLAUDE/journal
  outside `docs/`).
- **Weak point of what shipped:** the session-log "current log" heuristic is pure mtime — weaker than
  superbot's git-aware version, but `subprocess` is banned in `engine/` and mtime is the honest
  stdlib-only choice; `--file` covers explicit targeting.
- **One change that would have helped:** a kit-local fast lint+bootstrap-diff target (see the idea
  above's cousin) so the COM812 + regenerate-the-bootstrap traps surface without a full-suite run.
