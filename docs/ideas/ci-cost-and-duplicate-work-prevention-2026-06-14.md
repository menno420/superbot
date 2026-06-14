# Code-quality CI cost + duplicate-work prevention (early-claim convention)

> **Status:** `ideas` — captured 2026-06-14 (owner-asked, in-session; routed via Q-0126).
> Not a plan; not approval. Source + merged PRs win. The CI-efficiency half (a) was
> **applied the same session**; the convention half (b) is **open for owner decision**.

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

| Change | Lever | Effect |
|---|---|---|
| `concurrency: { group: code-quality-${{ github.ref }}, cancel-in-progress: <non-main> }` | fewer **runs** | cancels superseded PR runs; `main` runs to completion |
| `cache: pip` (setup-python) | per-run **minutes** | no re-download of pinned tools + requirements.txt |
| `.mypy_cache` via `actions/cache` | per-run **minutes** | mypy re-checks only changed modules |
| `pytest -n auto` (pytest-xdist) | per-run **minutes** | **verified 109s → 35s (~3×)**, identical 9,422 passed / 34 skipped |

`-n auto` is wired into CI **and** `scripts/check_quality.py` (graceful serial fallback when
xdist is absent) **and** `requirements-dev.txt`, so the local pre-PR mirror matches CI. Kill
switch: drop `-n auto` if it ever flakes under parallelism (a test sharing a fixed temp
path/port would be the cause).

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

## (b) Duplicate-work prevention — OPEN for owner decision

The owner's flow — *open a small PR immediately listing intended changes; others check open +
recent PRs before starting; hold pushes until the PR is complete* — is right in spirit. Two
mechanics need adjusting:

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

### Recommendation

Adopt **push-batching** (hold intermediate pushes; push once the PR is complete) as the cost
rule — it compounds with (a)'s concurrency cancel — and **option 1 (claim ledger)** for the
duplicate-work signal, keeping the existing early-PR rule for the *real* PR. If the owner
prefers the PR-based feel, option 2 is the fallback. Decision tracked in Q-0126; once picked,
the convention lands in CLAUDE.md § Session & plan workflow (+ `active-work.md` if option 1).

## Lifecycle

- (a) → **implemented** this session; re-badge `historical` after the PR merges.
- (b) → **discussed**; awaiting the owner's pick in Q-0126 before any CLAUDE.md edit.
