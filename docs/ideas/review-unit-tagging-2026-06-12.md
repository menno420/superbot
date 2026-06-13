# Review-unit tagging — make the repo-review-map a signal, not just a doc (2026-06-12)

> **Status:** `historical` — **EXECUTED 2026-06-12** (owner-approved); re-badged `historical` by the
> 2026-06-13 workflow reconciliation pass (an implemented idea has reached its lifecycle outcome —
> `docs/ideas/README.md` §5). Session idea (Q-0089)
> from the session that shipped [`docs/repo-review-map.md`](../repo-review-map.md) (PR #715).
> Shipped as `scripts/review_scope.py` + `scripts/_review_units.py` + the `context_map.py`
> "Review unit" header line — see [`context-map-tooling.md`](../context-map-tooling.md)
> § "Companion — review scope". Kept for the design rationale below.

## The idea

The new [`repo-review-map.md`](../repo-review-map.md) defines the unit of independent
review (Axis B: a **subsystem slice** vs. a **shared platform layer**). Right now that's
knowledge a reviewer has to *remember to apply*. Operationalize it: have the tooling
**tell you the review unit automatically**.

Two small, additive surfaces:

1. **File-level tag in `scripts/context_map.py`.** The tool agents already run before
   editing a `disbot/` file prints importers + blast radius. Add one line: the file's
   **review unit** — the subsystem slice name (resolved from `utils/subsystem_registry.py`
   + the `repo-navigation-map.md` cheat sheet) or, for `core/ · governance/ · utils/ ·
   views/base.py · entry files`, the **shared-platform layer** label with its review bar.

2. **PR-level classifier (new, e.g. `scripts/review_scope.py`).** Given a changed-file
   set (`git diff --name-only origin/main...HEAD`), classify the change as one of:
   - **single-slice** — all files in one subsystem slice (+ its mirrored tests) → low-bar, self-contained review;
   - **multi-slice** — touches two+ slices → flag "should this go through the EventBus / a shared service instead?";
   - **platform** — touches a B-platform layer → "blast-radius review, run `context_map.py` on the touched layer files."

## Why I believe in it

- **Closes the doc→practice gap.** A partition that only lives in a doc decays; one the
  toolchain emits on every edit/PR gets *used* — the self-improving-workflow ethos
  (`docs/collaboration-model.md`): each session leaves the next better-equipped.
- **Cheap + verifiable.** Pure read-only AST/path classification over data that already
  exists (registry + the cheat sheet); no runtime risk. Fits the "custom tooling on the
  repo's own AST" preference (`.claude/CLAUDE.md` § Tooling).
- **Catches the exact failure the review-map exists to prevent** — a PR that quietly grew
  from one slice into a cross-slice or platform change, which is where review scope blows up.

## Rough mechanics / open questions

- Source of truth for "file → slice": prefer `subsystem_registry` + the navigation cheat
  sheet; needs a small path→slice resolver (some slices span `cogs/ + views/ + services/ +
  utils/db/`).
- Could later become a soft CI annotation on PRs (print the scope classification), but
  **start as a local dev tool only** — no gate, no CI redness.
- Overlaps with `context_map.py` and `wiring_map.py`; reuse, don't duplicate.

## Routing

Captured. Small/safe/clear-direction → **quick-win lane** (could be one focused PR), but
not auto-promoted (`docs/ideas/README.md` routing rule). Next step when picked up: confirm
the path→slice resolver against the registry, then add the `context_map.py` line first
(smallest slice of value) before the PR-level classifier.
