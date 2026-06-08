# 2026-06-08 — Docs consolidation (Q-0010) + idea-backlog lifecycle (Q-0015)

## Arc

Started as a recon/assessment request: map the doc structure against the repo, verify every
tool works, and judge whether the system is complete enough to run a long, low-supervision
plan→build→review loop — **before** changing anything. Reported back, then the maintainer
clarified the real goal twice (see Q-0015) and greenlit execution. Turned into the scheduled
Q-0010 docs restructure **plus** the idea-lifecycle productivity layer.

**Key reframe (Q-0015):** the goal is **not** full autonomy — the human-verification +
multi-agent-revision gates are deliberate (keeps it manageable/reviewable). The goal is
**productivity-per-step + role clarity**, and a **continuous idea conveyor**: random intake →
map → route (roadmap horizon / plan / discuss-if-excessive) → groom → every idea ends
implemented or discussed. Grooming the backlog is the standing **end-of-session secondary
task** so an agent always has a next thing to do. (An earlier draft of this session proposed
an "unmonitored self-approval mode" — explicitly dropped per the maintainer's clarification.)

## Shipped

- **#579 — restructure.** Top-level `docs/` 41 → 16. Plans/audits/inventories/historical
  moved into clustered subdirs (`docs/ai/`, `docs/setup-platform/`, `docs/health/`) + type
  buckets, behind their folios (+ cluster READMEs). All inbound refs rewired (folios,
  `AGENT_ORIENTATION`, `roadmap`, `repo-navigation-map`, `context-map-overrides.yml`, 7
  doc-pinning tests, disbot/ comment pointers). `_TOP_LEVEL_DOCS_BUDGET` 41 → 16.
- **Workflow PR (this batch, 2 commits)** — stacked on #579:
  - **Idea-backlog lifecycle (Q-0015):** rewrote `docs/ideas/README.md` as intake → map →
    route → groom → outcome + the no-orphan guarantee; wired the grooming secondary task into
    `agent-workflow-spec.md` §7.6, the journal END protocol, `collaboration-model.md`,
    `ai-project-workflow.md` §4, `roadmap.md`, and a CLAUDE.md pointer. Captured Q-0015 in the
    router (verbatim).
  - **Concurrent-editing safety + self-review + housekeeping:** documented binding-doc
    **section-ownership** (`ai-project-workflow.md` §9 + a CLAUDE.md pointer) so parallel chats
    don't collide; added a self-review checkpoint (`agent-workflow-spec.md` §7.7); refreshed
    `current-state.md`; this log.

## Gates

All green at each step: `check_docs.py --strict` (census 16 / ratchet 16; reachability +
links + pinned + freshness), `check_architecture.py --mode strict` (exit 0),
`check_quality.py --full` (7960 passed, 16 skipped — run after the disbot/ comment-pointer
edits in #579). The workflow PR is docs-only (CI fast-path).

## Context delta

- **Needed but not pointed to:** that a docs *move* is not link-rewiring alone — **7 of the
  26 movable docs were pinned by tests and/or `context-map-overrides.yml`**, and ~13 had stale
  pointers in `disbot/` comments. Nothing in orientation flagged this; I found it by grepping
  tests/disbot and running the suite. Worth a one-liner in the restructure playbook: *moving a
  doc may also touch `tests/unit/docs/*` path constants, `context-map-overrides.yml`, and
  `disbot/` comment references — the gates (`check_docs --strict` + full suite) are the catch-net.*
- **Pointed to but didn't need:** the deep binding contracts (`architecture` / `ownership` /
  `runtime_contracts`) — correctly, the orientation says read them only when the task touches
  them, and a docs-only session doesn't.
- **Discovered by hand:** (1) a literal `docs/X.md` rewrite covers backtick refs + test string
  paths + the override YAML, but **markdown relative links** (`](name.md)`, `](../x.md)`) and
  **`_DOCS / "name.md"` test constants** need separate handling — `check_docs --strict` + the
  doc-pinning tests reliably flag the remainder. (2) `check_docs` reachability follows **both**
  markdown links and backtick `docs/X.md` refs, so updating a folio's link is enough to keep a
  moved doc reachable.

## Next

- Reconcile `current-state.md` "Recently shipped" once #579 + the workflow PR merge (this
  session can't name them as merged — freshness gate).
- Server-management **PR13** (role templates) remains the next *implementation* lane.
- First grooming candidates live in `docs/ideas/` (`future-product-direction`,
  `ai-extra-tool-capability-ideas`) — now routable via the new lifecycle.
