# Code-quality CI cost + duplicate-work prevention (early-claim convention)

> **Status:** `ideas` — captured 2026-06-14 (owner-asked, in-session; routed via Q-0126).
> Not a plan; not approval. Source + merged PRs win. The CI-efficiency half (a) shipped
> **concurrency + caching** (PR #814); **xdist was tried and reverted** (see Follow-up). The
> convention half (b) was **decided in-session** (claim ledger + push-batching). The live
> remaining idea here is the **Follow-up: parallel-safe test suite**.

## Why this exists

The owner observed (Actions usage metrics, June): `code-quality.yml` dwarfs every other
workflow — **940 runs / 2,396 minutes this month** vs. 52 runs for the next one — and asked
two things: (1) make it more efficient or trigger it less; (2) stop parallel agents from
duplicating each other's work by declaring intent early and holding pushes until a PR is done.

## How the workflow works today (answering "does it scan the whole repo or only new files?")

`code-quality.yml` triggers on `pull_request` → `main` (fires on PR open **and every push** to
the PR head) and on `push` → `main` (post-merge). For each run:

1. **Docs-only detector** — `git diff --name-only base head`; if every changed path matches
   `*.md` / `docs/` / `.session-journal.md`, the heavy steps are skipped (the job still reports
   success so the required check is satisfied and docs PRs stay mergeable).
2. Otherwise it runs **the whole repo, not just changed files**: `black --check .`,
   `isort --check-only .`, `ruff check .`, `mypy disbot/`, and the **entire 9,422-test suite**.
   The diff is used *only* for the docs-only skip decision — there is no changed-files scoping.

So: it's **all-or-nothing**. Any one non-docs file → full lint + full type-check + full suite.

**Measured cost driver:** pytest dominates — 9,422 tests in **109s** serial. Install (no cache)
+ mypy (no cache) sit on top. The 940 *run count* is inflated by per-push runs with no
concurrency cancellation.

## (a) CI efficiency — APPLIED this session (PR via Q-0126)

| Change | Lever | Status |
|---|---|---|
| `concurrency: { group: code-quality-${{ github.ref }}, cancel-in-progress: <non-main> }` | fewer **runs** | **shipped** — cancels superseded PR runs; `main` runs to completion |
| `cache: pip` (setup-python) | per-run **minutes** | **shipped** — no re-download of pinned tools + requirements.txt |
| `.mypy_cache` via `actions/cache` | per-run **minutes** | **shipped** — mypy re-checks only changed modules |
| `pytest -n auto` (pytest-xdist) | per-run **minutes** | **reverted** — 3× faster but the suite isn't parallel-safe (see Follow-up) |

Concurrency-cancel is the biggest lever on the *run count* (940); caching trims install + mypy.
With xdist reverted, pytest time is unchanged — the per-run win is install/mypy caching, and the
total-minutes win is the cancelled redundant runs.

### Considered but not shipped (with reasons)

- **Scope linters/tests to changed files.** Formatters (black/isort/ruff) are per-file and
  already finish in seconds over the whole repo — scoping saves ~nothing and adds rename-edge
  risk. mypy/pytest **must not** be scoped to changed files: a change in file A can break types
  or behavior in file B, and changed-files-only would miss it. So: full scope kept, made fast
  by caching + parallelism instead.
- **Draft-while-building.** Rejected by Q-0103 (auto-merge only arms on non-draft; "mark
  ready" was a forgotten step). Concurrency-cancel + push-batching achieve the same cost win
  without reintroducing draft.
- **`[skip ci]` on WIP commits.** Error-prone and only skips the triggering commit; concurrency
  cancellation is cleaner and automatic.

## (b) Duplicate-work prevention — DECIDED in-session (claim ledger + push-batching)

> **Decision (owner via AskUserQuestion, 2026-06-14):** **option 1 — claim ledger**, paired with
> **push-batching**. Gate-workflow changes **auto-merge like normal** (no auto-`do-not-automerge`).
> Implemented this session: `docs/owner/active-work.md` + the CLAUDE.md § Session & plan workflow
> bullet. The options below are kept as the design record.

The owner's flow — *open a small PR immediately listing intended changes; others check open +
recent PRs before starting; hold pushes until the PR is complete* — is right in spirit. Two
mechanics needed adjusting:

- GitHub can't open a PR with an **empty** diff (needs ≥1 commit → a one-line manifest commit).
- **Auto-merge collision (the blocker):** a ready docs-only PR arms native auto-merge (Q-0123)
  and GitHub **merges it the instant the trivially-green docs CI passes** — before any real work
  is pushed. An early manifest-PR would self-merge empty.

### Options

1. **Claim ledger (recommended).** A new append-only `docs/owner/active-work.md`. At session
   start an agent appends one stanza — `branch · scope · expected files/area · session date` —
   and archives/removes it at close. *Zero CI, greppable, no merge risk,* reuses the existing
   concurrent-chat append-only convention. "Check before starting" becomes: scan open PRs
   (already required — Q-0060 titles, Q-0125 health) **+ this file**.
2. **WIP PR + label.** The owner's literal version, fixed: open `do-not-automerge`, remove the
   label only when work is pushed & ready. Downside: a forgettable manual flip — the exact
   failure mode Q-0103 cited against draft PRs.
3. **WIP issue.** Manifest as a `wip-claim` issue (no CI, no merge risk). Adds a surface agents
   must also check.

## Follow-up: make the test suite parallel-safe, then re-enable xdist (the ~3× unlock)

This is the **live idea** that remains. xdist would cut pytest from ~109s to ~35s, but CI proved
the suite isn't parallel-safe. The evidence (all on a 4-core box, matching CI):

| Run | Result |
|---|---|
| CI `-n auto` | **9 failed** (`test_slash_access_check` ×7, `test_platform_consistency`, `test_flag_manager`) |
| local `-n auto` | 0 failed (green) |
| local `-n 4` | 0 failed (green) |
| local `-n 4 --dist loadscope` (run 1) | **7 failed** (slash cluster) |
| local `-n 4 --dist loadscope` (run 2) | **1 failed** — `test_platform_flags_embed` (in neither CI nor run 1) |

A *different* set fails each run → **non-deterministic cross-test state pollution** that only
surfaces under parallel scheduling. **Green locally ≠ green in CI**, and no `--dist` flag fixes
it (loadscope made it worse). The culprits are global singletons mutated by one test and read by
another without reset — candidates from the failures: the readiness-snapshot registry, the slash
access-control config, the flag registry, the platform-flags embed state.

**Plan when picked up:** (1) add autouse reset/isolation fixtures for those globals (start with
the 4+ implicated modules, then audit for more); (2) re-run `pytest -n auto` several times until
deterministically green; (3) re-enable `-n auto` in `code-quality.yml` + `scripts/check_quality.py`
and re-pin `pytest-xdist` in `requirements-dev.txt`; (4) verify across **multiple CI runs**, not
just locally (that's the trap this idea documents). Likely a `docs/planning/` plan, not a one-shot.

## Lifecycle

- (a) concurrency + caching → **implemented** (PR #814); re-badge `historical` after merge.
- (a) xdist → **reverted**; folded into the Follow-up above.
- (b) claim ledger + push-batching → **decided & implemented** this session (CLAUDE.md +
  `docs/owner/active-work.md`).
- **Follow-up (parallel-safe suite)** → the remaining live idea; groom into a plan when prioritized.
