# 2026-06-07 — Docs structure: maintainer-question router + context-map tool + badges

- **Arc:** broad docs-architecture review + question-prep session. Verified repo state
  + the two overlapping Codex docs PRs (#557 ideas-only, #559 = superset: router +
  ideas + read-path), then asked the maintainer 4 gating multiple-choice questions via
  `AskUserQuestion`. He chose: **consolidate** #557/#559 onto this branch, **build** the
  context-map tool **with Grimp**, **execute now**, **and** do the badge cleanup → did all
  three (3 commits) on `claude/laughing-davinci-lP6zv`.
- **Shipped:**
  - **Docs consolidation** — `docs/owner/maintainer-question-router.md` (+ `owner/README`),
    `docs/ideas/future-product-direction-2026-06-07.md` (pulled byte-exact off #559 to avoid
    transcription drift), lightweight read-path wiring (CLAUDE.md/AGENT_ORIENTATION/current-state),
    and a new **"load context in layers — don't read the whole docs/ tree"** rule. Supersedes
    #557/#559 (maintainer to close them).
  - **`scripts/context_map.py`** — given a file → role, imports (module-level + lazy, labelled),
    importers, blast radius, ownership, docs/tests, risk, read/verify set. Reuses
    `check_architecture._ImportVisitor` + `architecture_rules/*.yaml` (one source of truth).
    Importers/blast-radius via **Grimp** with an **AST fallback**. `docs/context-map-overrides.yml`
    + `tests/unit/scripts/test_context_map.py` + `docs/context-map-tooling.md`.
  - **Badge cleanup** — badged the 15 truly-bare docs + normalized the 8 building-roadmap
    `Status:` lines; extended the badge taxonomy (audit/owner-guidance/archive) in AGENT_ORIENTATION.
- **Findings worth keeping:**
  - **CodeGraph file edges are dead here** (verified: `file_deps`/`impact_analysis` → 0). **Grimp**
    builds the 572-module graph in **0.3s** over the flat `disbot/`-rooted layout and resolves the
    **7 importers + 60-module blast radius** CodeGraph misses — incl. lazy-importer edges.
  - **CI does NOT install `requirements-dev.txt`** (see new CI rule) — drove the Grimp-optional design.
  - **Badge audit refined to 15, not "49 unbadged":** my first scan used `**Status**:` but docs use
    `**Status:**`; 50 already standard-badged, 34 self-declare non-standard, only **15 truly bare**.
- **Gates:** `check_quality --full` green (**7749 passed**, 16 skipped); `check_architecture --mode
  strict` **0 errors**. Docs/tooling only — no `disbot/` runtime change, so no boot needed. **For
  project state see `docs/current-state.md`.** (PR pending.)
