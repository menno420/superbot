# Docs restructure — next-session brief (2026-06-08)

> **Status:** `historical` — a focused, ready-to-pick handoff for a dedicated docs-restructure
> **Superseded 2026-06-19 (was active):** Superseded by this planning/README + repo-structure-improvement-plan-2026-06-19. Do not act on this — current map: [planning/README](README.md).
> session. Owner-approved direction: **Q-0010** (router) + this session's binding-doc
> collision finding. **Source / merged PRs win;** this is scope, not approval to change
> behavior. It's a **meta-task that can run in parallel** with the implementation lane
> (PR13) — a different chat can take it.

## Why now

Two pressures converged this session:

1. **Top-level `docs/` is too big** (owner decision **Q-0010**, 2026-06-07). The
   `scripts/check_docs.py` census reports ~41 top-level `docs/*.md`; the agreed target is
   **~15**. The rest are plans / audits / dated snapshots that belong in subdirs behind
   their **folios** (`docs/subsystems/*`).
2. **Binding-doc edits collide across concurrent chats** (observed 2026-06-08). `main`
   moved mid-session and two chats edited `CLAUDE.md` / the owner docs at once (one shipped
   `agent-workflow-spec.md` + router Q-0013 while this chat was mid-flight). `.sessions/`
   already solved this class for the journal (per-file, no shared anchor); the binding
   docs need the same treatment.

## Goal

Make the docs **navigable + multi-chat-safe** without losing content or breaking the gates.

## Tasks (ordered)

1. **Shrink top-level `docs/` 41 → ~15.** Move plans / audits / dated snapshots into
   subdirs (`docs/planning/`, `docs/audits/`, `docs/archive/`, or behind a subsystem
   folio). Every moved doc must stay **reachable** — `check_docs.py`'s reachability gate
   fails an orphan unless it's badged `historical` / `archive` — so update the linking
   folio and the `AGENT_ORIENTATION.md` route as you move. Then **lower
   `_TOP_LEVEL_DOCS_BUDGET`** in `scripts/check_docs.py` to the new count so the ratchet
   holds the line.
2. **Make binding-doc edits section-scoped (multi-chat safety).** `CLAUDE.md` already
   carries `<!-- READ_FIRST/SESSION_WORKFLOW/CODEGRAPH/ARCH_RULES -->` markers — formalize
   them as **section ownership** so a chat edits one block and two chats touching different
   blocks never conflict. Document the convention (a short note in `CLAUDE.md` or
   `docs/owner/`), and confirm the two existing collision-safe patterns are stated: the
   **router is append-only** (next free `Q-00NN`), and `.sessions/` is **per-file**.
   Consider the same marker treatment for other frequently co-edited shared docs
   (`current-state.md`, the journal guidebook).
3. **Verify the reading route after moves.** `AGENT_ORIENTATION.md` "Reading order by task"
   and the folios must still resolve to the **moved** paths. Wire in
   `docs/owner/agent-workflow-spec.md` (the pipeline-stage spec) if a route still points
   only at the older owner docs.
4. **Keep the gates green.** `check_docs.py` — census count drops, reachability passes, the
   freshness `(pending PR)` gate is clean — and no dead links anywhere.

## Constraints

- **One-fact-one-home** — move + link, never duplicate. Source / merged PRs win over any doc.
- **Don't break** the `check_docs.py` reachability + freshness gates; only lower the docs
  budget to match the new reality.
- **Coordinate** with concurrent chats on binding docs — prefer append-only / section-scoped
  edits; expect `main` to move under you.
- **Docs-only** — no behavior change, no code, no other gate-rule loosening.

## Done when

- Top-level `docs/*.md` ≈ 15; census + `_TOP_LEVEL_DOCS_BUDGET` updated; reachability green.
- The binding-doc section-ownership convention is documented.
- `AGENT_ORIENTATION.md` + the folios resolve to the new layout (no dead links).

## Authoritative context to read first

- `docs/owner/maintainer-question-router.md` **Q-0010** (the consolidation decision) and
  **Q-0014** (branch/tooling/path latitude — relevant if you add tooling).
- `scripts/check_docs.py` — the census, the `_TOP_LEVEL_DOCS_BUDGET` ratchet, and the
  reachability + freshness gates you must keep green.
- `docs/AGENT_ORIENTATION.md` — the reading route to keep correct.
- `.sessions/2026-06-08-tooling-reliability-and-owner-memory.md` — the collision finding +
  the `CLAUDE.md` section markers that motivate task 2.
