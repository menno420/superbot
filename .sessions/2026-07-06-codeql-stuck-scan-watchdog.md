# 2026-07-06 — Verify PR #1743 + CodeQL stuck-scan watchdog

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). 30 watchdog tests green,
> `check_quality --check-only` + `check_architecture --mode strict` + `check_docs --strict` +
> `check_workflow_concurrency` all green; workflow YAML parses; both scripts SKIP-degrade cleanly.

## What this session did

Continuation of the CI-setup arc (PRs #1737 / #1739 / #1743). Two parts, as the task named — **verify
the previous session's work, then continue it.**

## Part 1 — verification of PR #1743 (result: correct ✓)

Read the rewritten `scripts/check_ci_coverage.py` + its 13 tests and ran them (21 pass with the 8
workflow-concurrency tests). Findings:

- **`classify_head` is sound.** It classifies by **triggering event**, not check-run-name presence: a
  `pull_request`/`push` run (any status) → COVERED; a completed `workflow_dispatch` re-kick with no
  PR-event run → ESCALATE; no run past grace → REKICK; else WAIT. This correctly removes the
  self-silencing bug (a re-kick can no longer mark a still-blocked head "covered"), and is correct
  **either way** the unverified "does dispatch satisfy the required check?" question resolves.
- **Tests are comprehensive** — every branch covered incl. the failure-is-covered-not-rekicked case and
  the escalate case. The `code-quality.yml` comment correction and the doc updates (live CodeQL ruleset)
  are honest and accurate.
- **No defects found in the shipped logic.** One *latent gap adjacent* to it (not in the script): the
  escalation opens an issue via `gh issue create`, but `ci-rerun-watchdog.yml` never granted
  `issues: write` — so under the `GITHUB_TOKEN` fallback the alert would silently fail. Fixed this
  session (see below).

## Part 2 — continued the ranked handoff (`ci-followups-handoff-2026-07-05.md`)

Executed the next offline-buildable items (item #2 + the #1743 Q-0089 idea it depends on):

- **`scripts/lib/owner_alert.py`** (new) — the shared idempotent owner-alert issue opener (Q-0089).
  `ensure_issue(repo, marker, title, body)` centralizes the marker-based dedupe (search → dedupe →
  create, gh primitives injectable for tests); conservative when gh is unavailable (won't risk a
  duplicate). `check_ci_coverage.open_alert_issue` now delegates to it.
- **`scripts/check_codeql_coverage.py`** (new) — the **CodeQL stuck-scan watchdog** (design §C.2 / A10).
  Bounds the residual the `codeql-merge-protection` ruleset leaves open — a scan that *starts then
  errors/hangs*, or a dropped codeql event. `classify_codeql_head` → HEALTHY / RERUN / ESCALATE / WAIT,
  keyed on `run_started_at` so a hung in-progress scan is distinguishable from a normal one; never
  touches a live scan within the hang window. Reuses `check_ci_coverage`'s proven PR-listing + head
  fetch I/O. 12 pure-logic tests.
- **`.github/workflows/ci-rerun-watchdog.yml`** — added the **alerting-only** stuck-scan leg (A10
  "alerting-only first"; `--rerun` re-dispatch stays gated until the codeql run shape is live-confirmed)
  + `issues: write` (also closes the #1743 escalation gap above). Additive leg on a non-required routine
  workflow — one-commit-revertible, changes no required context.
- **Docs** — handoff item #2, design §C.2 / A10, and the what-runs-where map reflect shipped.
- **Housekeeping** — deleted the stale claim left by the merged #1743 branch (fix-on-sight, Q-0166).

## State after this session

- ✅ CodeQL merge-race CLOSED (owner ruleset, #1743).
- ✅ Dropped-`synchronize` watchdog de-self-silenced + **verified correct** (#1743).
- ✅ CodeQL stuck-scan watchdog SHIPPED **alerting-only** (this PR) + shared `owner_alert` extracted.
- ▶ Remaining (turn-key, handoff): live-verify the ruleset + the two run-shape questions → flip the
  codeql leg to `--rerun`; ruff consolidation (A3); the `ci.yml`/`web-ci.yml`/`pr-freshness.yml`
  restructure + owner-gated Q-0239 tail; the two AST guards.

## 🛠 Friction → guard (Q-0194)

- **Latent gh-permission gap** (the #1743 `issues: write` miss): a workflow step's script can call
  `gh issue create` while the job's `permissions:` never grants `issues: write` → silent no-op under the
  `GITHUB_TOKEN` fallback. **Guard shipped now:** the fix (`issues: write`) + a warn-first checker idea
  ([`ideas/workflow-gh-permission-coverage-checker-2026-07-06.md`](../docs/ideas/workflow-gh-permission-coverage-checker-2026-07-06.md))
  that cross-checks a script's `gh` ops against the invoking workflow's `permissions:`. (Checker is
  free-to-ship tooling; recorded as an idea to build validated, not a naive stub.)
- **`tests/unit/scripts/test_atlas.py` sandbox flake** — 5 grimp `ModuleNotPresent: "bot1"` errors,
  **pre-existing** (reproduced with my changes stashed; my PR's own CI pytest is unaffected — only the
  born-red session-gate was red). Not my regression; noted so the next agent doesn't chase it. No guard
  (it's a sandbox grimp-graph environment issue, not a code bug).

## Context delta (reflection interview)

- **Needed but not pointed to:** the script-sibling-import convention (`sys.path.insert(scripts/)` +
  flat/`lib.` import, `# noqa: E402`) is only discoverable by reading `check_session_slug_unique.py` /
  `check_phase_gate.py`. A one-line note in `docs/repo-navigation-map.md` ("shared script helpers →
  `scripts/lib/`, imported via the sys.path-insert pattern") would save the next tooling session the grep.
- **Pointed to but didn't need:** the huge `current-state.md` narrative — the handoff doc + design doc
  were the only load-bearing reads for this task; the ledger paged out at 25k tokens without adding signal.
- **Discovered by hand:** that `.github/workflows/*.yml` edits are within a `claude/*` session's Phase-A
  ambit (additive, non-required, one-commit-revertible) — inferred from #1739's precedent + design §E, not
  stated in one place. The owner-gated line is *required-context / deletion / branch-protection / hooks*.
- **Decisions made alone:** (1) `HANG_MIN=45` / `MAX_RETRIES=2` / `GRACE_MIN=8` defaults for the codeql
  watchdog (tunable via flags); (2) alerting-only default with `--rerun` gated (matches A10); (3) added
  `issues: write` to the watchdog workflow. All reversible; none is product intent.
- **Weak point / unverified half:** the codeql `workflow_runs` shape (its `.path`, whether a re-run is a
  fresh row) is offline-built — the leg is alerting-only precisely because that's unconfirmed. Handoff
  item #2 now spells out the exact live checks to enable `--rerun`.

## ⟲ Previous-session review (Q-0102)

Previous = #1743 (the watchdog self-silencing fix). **Strong:** the event-classification rewrite is
genuinely correct and the tests are thorough; it was honest about the one thing offline testing can't
confirm and encoded that honesty into the code + comment (no false green). **What it missed:** (1) it
left its **claim file undeleted** at close (I cleaned it — `check_stale_claims` is the existing failsafe,
so low-harm); (2) more consequentially, its own escalation path shipped a **latent permission gap** — it
added `gh issue create` without granting the workflow `issues: write`, so the alert it built couldn't
actually fire under the `GITHUB_TOKEN` fallback. **System improvement (initiated):** the
gh-permission-coverage checker idea above — the class of "a script's side-effect can't execute because the
workflow doesn't grant the scope" is mechanizable and currently unguarded.

## 💡 Session idea (Q-0089)

**`check_workflow_gh_permissions`** — a warn-first checker mapping each `gh` op a workflow step's script
runs to the required `permissions:` scope and asserting the job grants it. Genuinely believed-in (it would
have caught the #1743 gap I found this session), mechanizable, and distinct from the existing
`check_routine_permission_surface` (Claude-settings layer). Filed:
[`ideas/workflow-gh-permission-coverage-checker-2026-07-06.md`](../docs/ideas/workflow-gh-permission-coverage-checker-2026-07-06.md)
+ README index entry.

## 🧹 Grooming (Q-0015)

Advanced the CI backlog down its lifecycle: executed handoff item #2 (CodeQL stuck-scan watchdog,
alerting-only) + the #1743 Q-0089 idea (shared `owner_alert`), and re-cut the handoff so item #2 now reads
"shipped alerting-only; remaining = live-confirm → enable `--rerun`" with the exact live checks named — so
the next agent starts on the (cheap, live) verification, not a rebuild. Second DRY observation noted for a
possible future third watchdog: `check_ci_coverage` + `check_codeql_coverage` now share `owner_alert` + the
PR-listing I/O; a shared `pr_head_watchdog` skeleton is the rule-of-three unification if a third appears.

## 📋 Docs audit (Q-0104)

`check_docs --strict` green (all new docs reachable + link-valid). Design/handoff/map updated in-place; the
idea is indexed. **No new owner decision** (executes within Q-0239's Phase-A envelope; the task itself
directed the continuation). **Ledger:** no merged PR to record here — this session's PR #1744 is in flight;
the next reconciliation pass folds #1743 + #1744 (Recon marker is #1740; not due until #1770, and per Q-0124
a manual session doesn't run the pass).

## 📤 Run report

- **Did:** verified PR #1743's watchdog fix is correct (21 tests), then built the next handoff items — the
  shared idempotent `owner_alert` helper (Q-0089) + the CodeQL stuck-scan watchdog (A10, alerting-only) +
  its `ci-rerun-watchdog` leg, and fixed the #1743 `issues: write` escalation gap. · **Outcome:** shipped
- **Shipped:** #1744 — 2 new scripts (+17 tests) · 1 refactor · 1 workflow leg · 3 doc updates · 1 new idea.
- **Run type:** `manual` (owner-directed — "continue PR #1743 + verify").
- **⚑ Owner decisions needed:** none new (Q-0239 tail unchanged; all in the handoff + router).
- **⚑ Owner manual steps:** none blocking. When convenient, the cheap live-verify in handoff item #1/#2
  (one trivial PR to confirm the ruleset holds-then-releases + the codeql run-shape) unlocks flipping the
  codeql leg from alerting-only to `--rerun`.
- **⚑ Self-initiated:** the `owner_alert` extraction + CodeQL stuck-scan watchdog + the `issues: write`
  fix + the gh-permission checker idea — all within the task's "continue PR #1743" directive (Q-0172).
- **↪ Next:** handoff items #1/#2 live-verify (cheap) → then ruff consolidation (A3).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1744) |
| Handoff items advanced | item #2 (CodeQL stuck-scan, alerting-only) + the #1743 Q-0089 idea (owner_alert) |
| Real gaps closed | 1 (the #1743 `issues: write` escalation gap) + 1 residual bounded (codeql errors/hangs) |
| Tests added | 17 (5 owner_alert + 12 codeql) |
| CI-red rounds | born-red hold only (intended) |
| New ideas contributed | 1 (`check_workflow_gh_permissions`) |
| Ideas groomed | 1 (CI handoff item #2 re-cut to "shipped → live-confirm") |
