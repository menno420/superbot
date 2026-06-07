# 2026-06-07 — Map the #562 owner-workstyle capture into the right homes

- **Arc:** #562 (`chatgpt/owner-workstyle-capture`) landed a 374-line ChatGPT-drafted
  doc, `docs/owner/maintainer-working-profile-and-idea-intake.md`, whose own §14/§15 asked
  for a dedicated Opus mapping session. Maintainer invoked exactly that: "propose how to
  map the information into the right places, and get some questions answered." Branch
  `claude/dazzling-noether-SkuC4`.
- **Verified first:** no open PRs (live GitHub); old doc had **zero inbound references** and
  **no doc-pinning test** touches the owner docs → safe to restructure. `context_map.py` +
  `docs/context-map-overrides.yml` confirmed real (so §11 describes a true tool).
- **Maintainer answered a 4-question batch (all = recommended):**
  1. **Split** the capture into a short profile + a separate workflow doc.
  2. Store **pipeline + handoff templates** only (don't mirror full ChatGPT instructions).
  3. **"New idea ≠ new priority"** becomes a **binding rule + reference**.
  4. **Reconcile** the idea-states list into the existing promotion path / router lifecycle.
- **Shipped (docs-only, net −75 lines):**
  - **Split** → `docs/owner/maintainer-working-profile.md` (the *person*: profile, idea-flow
    insight, non-goals) + `docs/owner/ai-project-workflow.md` (the *process*: pipeline,
    per-project roles, **handoff templates**, idea-state vocabulary, failure modes, context-map
    tooling). Removed the old combined doc.
  - **De-duplicated** the restated sections (planning→execute, multiple-choice, router
    relationship, doc-scale) to links instead of fresh prose.
  - **Routed the binding rule** "a new idea is not a new priority / idea order ≠
    implementation order" into `.claude/CLAUDE.md` (Working agreement) + `docs/collaboration-model.md`.
  - **Reconciled idea states** — the workflow doc's states map onto `docs/ideas/README.md`'s
    promotion gates + the router lifecycle (no parallel tracker); added a note in ideas/README.
  - **Wired discovery** — AGENT_ORIENTATION classification + `docs/owner/README.md` links;
    pointed the journal's Cross-Agent Workflow Preferences at the new canonical pipeline doc;
    `current-state.md` Recently-shipped line.
- **Gates:** `check_docs --strict` clean (badges/links/pins); `check_architecture --mode
  strict` exit 0 (only pre-existing WARNs). Docs/tooling only — no `disbot/` runtime change.
  **Project state: `docs/current-state.md`.**
