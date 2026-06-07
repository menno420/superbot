# 2026-06-07 — Doc-hygiene gate + workflow definition + per-session journal

- **Arc:** follow-up to #560 (merged). Maintainer ran a 16-question multiple-choice
  batch (4 waves via `AskUserQuestion`) to define the workflow + scope doc hygiene, then
  said "execute now." Branch `claude/laughing-davinci-lP6zv`.
- **Workflow answers → routed** (`.claude/CLAUDE.md` + `docs/collaboration-model.md`):
  planning stays planning until **ExitPlanMode** approval; before approval, read-only
  research + safe prototyping (no commits); after approval, execute the whole plan
  in-session; **PR size mixed by risk**; **custom tooling over new third-party deps**.
- **Router inbox answers preserved verbatim** (`docs/owner/maintainer-question-router.md`
  §12–13). Notable: **AI may eventually gain broader actions** — owner intent, but still
  behind *all* AI gates + a dedicated decision (routed to `docs/subsystems/ai.md` as a
  not-approval note); Discord-first + later web (→ server-management folio); the rest
  confirm existing act-vs-ask / routing / reproposal rules.
- **Shipped — doc hygiene:**
  - **`scripts/check_docs.py`** (custom, stdlib-only) — hard CI gate, runs on every PR
    incl. docs-only: valid `> **Status:**` badge per doc (taxonomy pinned to
    `AGENT_ORIENTATION`; ADRs exempt), relative doc links resolve, read-path path refs
    exist. Wired into `code-quality.yml` + `check_quality.py`. Tests + a taxonomy pin-test.
  - **Normalized 60 docs** to the strict badge token (preserving each doc's description);
    de-linked a dead ADR-003 reference (`.claude/plans/` was never committed).
  - **Read-path collapsed** → `AGENT_ORIENTATION.md` is the one canonical read path;
    `current-state.md` now points to it instead of duplicating the table.
  - **Journal → per-session files** (this convention): migrated the live Session Log into
    `.sessions/`, slimmed `.session-journal.md` to the guidebook + a pointer.
- **Gates:** `check_quality --full` green; `check_architecture --mode strict` 0 errors;
  `check_docs --strict` clean. Docs/tooling only — no `disbot/` runtime change.
  **Project state: `docs/current-state.md`.**
