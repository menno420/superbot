# 2026-06-12 — UX Lab design (interface-gallery cog, owner-commissioned)

> **Status:** `audit`

**PR:** #755 (ready, open at write time; merged in-session per Q-0084)
**Branch:** `claude/wizardly-planck-c04laf`

## Context

Owner-commissioned brainstorm continuation + design: "design the most versatile and
inclusive UX testing cog" — a gallery for browsing every Discord UX pattern and
comparing against the bot's current panels. Input: the owner's original ask + a ChatGPT
draft (treated per the verify-don't-trust rule — several of its claims needed source
verification). Design session, not implementation (owner said "design"; idea lifecycle
says structure, don't auto-promote).

## What shipped (PR #755, docs-only)

- [`docs/ideas/ux-lab-interface-gallery-2026-06-12.md`](../docs/ideas/ux-lab-interface-gallery-2026-06-12.md)
  — capture: owner intent, durable-value case, scope fences.
- [`docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md`](../docs/planning/ux-lab-interface-gallery-plan-2026-06-12.md)
  — the design: thin cog + 9 view wings + `utils/ux_patterns/` registry (no service
  layer), `PatternSpec` schema, ~60-exhibit inventory, 10-probe limit bench,
  compare/verdict mode, AST zero-write fence, 3-PR slicing (A core · B CV2+PIL ·
  C mock studio + pattern-library export), acceptance criteria.
- **Two stale-fact corrections** (both verified against installed discord.py 2.7.1 by
  introspection): `discord-platform-limits.md` CV2 budget 25 → **40 children +
  4 000-char text** (25 is the legacy `View` ceiling); journal rule "modals cannot
  contain selects" corrected (`ui.Label`, 2.6+, wraps selects in modals).
- Router **Q-0116** (scheduling + audience, OPEN) · roadmap 🖥️ lane horizon · ideas
  README index entry.

## Key verification notes (for the implementing session)

- discord.py 2.7.1 exports the full CV2 set (`LayoutView`/`Container`/`Section`/
  `TextDisplay`/`MediaGallery`/`File`/`Separator` + modal `Label`); `LayoutView`
  raises at >40 children and documents the 4 000-char display budget.
- ChatGPT's draft was right about the 40-component figure (repo doc was wrong) and
  right that CV2 replaces content/embeds; its "gate on library support" caution is
  resolved — support is present on the pin. Its suggested `ux_lab_service` was dropped
  (no business logic, no writes → no service; ownership doc logic).
- Rejection-ledger fences honored: no second panel/router framework (canonical view
  lineage + one commented `LayoutView` exemption); no grab-bag helper module
  (`utils/ux_patterns/` is single-purpose); slash = one front door.

## Process notes

- **The Q-0107 reconciliation pass is DUE** (`check_reconciliation_due`: crossed #750,
  last pass #741). This session was owner-steered to the UX Lab design, so the pass is
  deliberately left to the next session — or the #752 nightly docs-reconciliation
  Routine if the owner has wired it (its gate + marker-reset design dedupes correctly).
- Grooming (Q-0015): satisfied by the main task itself — a brand-new owner idea was
  moved intake → captured → routed-to-plan (+ roadmap horizon + router Q) in one
  session; no additional backlog pull made given the due reconciliation pass should be
  the next session's focus.

## 💡 Session idea (Q-0089)

**`scripts/ui_component_census.py`** — offline AST census of every `discord.ui`
component the codebase constructs: button styles, select types, per-view child counts,
modals, and a "views within N of the 25-child ceiling" warning list. Why I believe in
it: it is the **"current bot" half of the UX Lab's compare mode** (the lab shows what
*could* be; the census shows what *is* — per-view, greppable, no boot needed), and it
catches the cap-regression class that bit twice (the V-16 catalogue trips, PR #702)
*before* a live panel silently truncates. Companion to `command_surface_dump.py`
(commands) — same offline-AST family, different surface. Dedup-checked: nothing in
`docs/ideas/` or the roadmap covers component-level census. Small, read-only,
quick-win lane.

## ⟲ Previous-session review (Q-0102) — PR #752 (autonomous-routines.md)

**Did well:** exactly the right durable home — the Routine fleet's prompts now live in
git (reviewable, improvable) instead of only in the console, and the nightly
docs-reconciliation Routine reuses `check_reconciliation_due` as its self-gate with a
marker-reset that makes re-fires exit cleanly; that mutual-exclusion design also covers
the interactive-session-vs-routine duplicate-claimant case I went looking for (no fix
needed — verified before claiming a gap).
**Missed:** #752 wrote **no `.sessions/` log** (this review had to be reconstructed
from the commit message + doc) and so also skipped the Q-0089 idea ender — the
mandatory enders were dropped, likely because it ran as a quick continuation session.
**Workflow improvement:** the session-log checker / Stop-hook advisory apparently
doesn't bite on short continuation sessions that commit via a merge from another
branch's flow. Worth one look at `scripts/check_session_log.py`'s trigger condition
next time someone touches it: a session that *merges a PR* should be in scope even if
it edited only docs. (Captured here, not built — docs-only session.)

## Context delta (reflection interview)

- **Route hit:** CLAUDE.md → collaboration-model → current-state → journal →
  AGENT_ORIENTATION → ideas README + platform-limits + hub-ui-standard was exactly the
  right chain for a design session; the ideas README's lifecycle section made the
  "capture + plan + Q-block, don't implement" shape unambiguous.
- **Route miss (small):** nothing pointed at `views/navigation.py` as the canonical
  in-place-transition helper — found via grep from the vision doc's V-02 row. The
  hub-ui-standard would be a natural home for one pointer line.
- **Discovered by hand:** the discord.py 2.7.1 CV2 surface (the load-bearing facts) —
  by deliberate introspection, which is the right method, but note for future agents:
  **the installed library is the cheapest ground truth** for "does the pin support X?"
  questions; prefer it over web docs for version-pinned claims.
- **Decisions made alone:** no service layer for the lab; CV2 wing as commented
  LayoutView exemption; verdicts as copy-paste lines instead of persistence (preserves
  zero-write). All three are reversible design choices recorded in the plan.
- **Weak point of what shipped:** the ~60-exhibit inventory is a design-time list —
  implementation will likely merge/cut some exhibits once rendered side by side; the
  plan says PR A may trim wings, but expect drift between inventory and v1.
- **One change that would have helped:** none structural — the orientation route fit
  this task well.
