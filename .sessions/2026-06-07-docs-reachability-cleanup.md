# 2026-06-07 — Docs assessment → reachability cleanup + hard orphan gate

- **Arc:** after #563 merged, the maintainer asked for an honest assessment of the docs
  system. I surveyed all 105+ docs (badges, sizes, reachability), then he answered a
  2-question batch: **subfolder + archive sweep** and a **hard reachability gate**.
  Executed both on branch `claude/dazzling-noether-SkuC4` (continues the session that
  shipped #563).
- **Honest correction recorded:** my first orphan pass (direct refs from 3 read-path docs
  + folios only) reported ~33 "unreachable" docs. A proper **transitive** walk (markdown
  links + backtick `docs/*.md` refs from all folios/READMEs/read-path docs) showed **100/106
  reachable, 3 true orphans** — "unreachable" was overstated; the *top-level clutter* point
  held.
- **Shipped (this PR):**
  - **BTD6 island → `docs/btd6/`** — `git mv` 14 `docs/btd6-*.md`; rewrote ~dozen full-path
    refs repo-wide (docs, 5 scripts, 3 `disbot/` comments, `.gitattributes`, a test comment);
    added `docs/btd6/README.md` index; folio points at it.
  - **Archive sweep** — moved the retired 2026-06 planning/audit burst (7 files:
    cartography, source-of-truth-index, next-session-roadmap, architecture-priority-map, 2
    stability plans, cog-functionality-audit) into `docs/archive/`, re-badged `archive`,
    added `docs/archive/README.md`; AGENT_ORIENTATION points at it. **Left
    `phase-2-completion-readiness.md` in place on purpose** — it has a user-facing runtime
    string (`platform_consistency.py`) + a content-pinning test; moving it is high-churn /
    low-value and it's already `historical` + reachable.
  - **Hard reachability gate** — `check_docs.py` gains `check_reachable()`: BFS from
    read-path roots + folios + READMEs + CLAUDE.md; orphans fail `--strict` unless badged
    `historical`/`archive`, an ADR, or in `_REACHABILITY_ALLOWLIST` (empty). 3 unit tests +
    a repo-level zero-orphan pin in `tests/unit/scripts/test_check_docs.py`.
  - **Honesty fixes** — corrected AGENT_ORIENTATION's stale "23 files / 3 ADRs" self-count
    (→ 100+ docs, 7 ADRs); de-duped the new `ai-project-workflow.md` §6 down to a pointer to
    the canonical `docs/context-map-tooling.md` (and wired that orphan into AGENT_ORIENTATION).
- **Gates:** `check_docs --strict` clean (incl. reachability); `check_architecture --mode
  strict` exit 0; `check_quality --full` green (**7759 passed, 16 skipped**). Touched
  `disbot/` only via doc-path comments — no behaviour change. **State: `docs/current-state.md`.**
