# 2026-06-12 — Repo review map (the review/refactor partition)

> **Status:** `audit` — per-session log. Newest-first sibling of the other `.sessions/` files.

**PR:** [#715](https://github.com/menno420/superbot/pull/715) — `docs/repo-review-map.md` (merged, `9a18d1a`). Session-close artifacts ship in a follow-up PR on the same branch.
**Branch:** `claude/sleepy-hawking-tgderi`

## What was done

- **Finalized the repo division the owner asked for** into `docs/repo-review-map.md`.
  Verified the proposed 5-group split against the live tree (not the trimmed view it was
  written from) and reconciled it with the existing subsystem-folio + layer model instead
  of creating a competing taxonomy.
  - **Axis A** (coarse, top-level): bot runtime · BTD6 data pipeline · dev/CI/agent tooling ·
    docs & agent system · tests-as-mirror.
  - **Axis B** (the actual foundation): inside the bot, the review unit is the **vertical
    subsystem slice**; shared platform layers (`core/`, `governance/`, `utils/`,
    `views/base.py`, entry files) are separate higher-bar units scoped by blast radius.
  - Corrections applied where the proposal worked against the goal: BTD6 runtime (35
    `btd6_*` services + 6 cogs + `views/btd6/` + `utils/db/btd6_*`) stays in the bot;
    tests **mirror** their slice rather than forming a silo; `disbot/data` is runtime not
    pipeline.
- Wired the doc into the read-path: `AGENT_ORIENTATION.md` (reading table + reference list)
  and the `repo-navigation-map.md` header. Bumped the soft top-level-docs ratchet 16→17 in
  `check_docs.py`.
- Merged PR #715 myself (Q-0084): branch current with `main`, CI `code-quality` green,
  merge-commit method. Subscribed/auto-unsubscribed on merge.
- **Grooming move:** routed [`ai-panel-inplace-navigation-2026-06-11.md`](../docs/ideas/ai-panel-inplace-navigation-2026-06-11.md)
  one step — `captured → on the roadmap` (placed at `docs/roadmap.md` § AI **Later**, UX
  debt; idea file stamped with the routing note).

## Decisions recorded

- None new. Exercised standing grants: Q-0052 (early-draft PR + advance consent),
  Q-0084 (merge own session PR when green), Q-0089 (one new idea per session).
- Judgment call (flagged to owner): the division is documented as a **review/refactor
  lens** over the existing structure, **not** a physical folder reorg — the architecture
  already enforces the slice boundaries that make independent review possible. Owner can
  request a physical reorg (e.g. `scripts/btd6/` vs `scripts/dev/`) as a separate larger change.

## Left open / next session

- Optional **physical reorg** to make Axis A visible on disk (owner-gated, larger).
- The new idea below (review-unit tagging) sits in the quick-win lane, not auto-promoted.

## 💡 Session idea

**Idea:** Operationalize `repo-review-map.md` in tooling — have `scripts/context_map.py`
print a file's **review unit** (subsystem slice vs. shared-platform layer), and add a
PR-level `scripts/review_scope.py` that classifies a changed-file set as single-slice /
multi-slice / platform.
**Why:** A partition that only lives in a doc decays; one the toolchain emits on every
edit/PR gets used — and it catches the exact failure the map exists to prevent (a PR that
quietly grew from one slice into a cross-slice or platform change). Read-only, cheap, fits
the repo's "custom AST tooling" preference.
Idea file created: [`docs/ideas/review-unit-tagging-2026-06-12.md`](../docs/ideas/review-unit-tagging-2026-06-12.md) (indexed in the ideas README).
