# 2026-06-18 — Setup cog-routing select: paginate instead of truncating at 25

> **Status:** `complete`

## What & why
While reviewing the `needs-hermes-review` queue (#929/#941/#1033) for merge, the
full-suite CI mirror surfaced a real latent bug, not in any one PR: the setup
**cog-routing** picker built a single Discord select from
`_operator_visible_cogs()` which hard-capped at `visible[:25]`. The registry has
now grown past 25 routable subsystems (35), so the cap **silently dropped** every
cog past the 25th in sorted order — `moderation`, `role`, `rps_tournament`,
`server_management`, `settings`, `utility`, `ux_lab`, `welcome`, `xp`,
`proof_channel`. An operator literally could not route those cogs per
scope. The bug already affected `main`; the only guard test
(`test_operator_visible_cogs_returns_known_cog_names`, which checks `moderation`)
was tipped red by the fishing merge (#1033) crossing the boundary.

## Change
- `_operator_visible_cogs()` now returns the **full** sorted visible list (no
  truncation).
- New `_CogPickView(BaseView)` pages the list into ≤25-option windows with
  **◀ Prev / Next ▶** nav (buttons appear only when >1 page; edges disabled at
  bounds). `_CogPickSelect` takes an explicit page of names + page/page_count for
  its placeholder; `_cog_options(cog_names)` builds one page.
- The three scope callbacks (guild / category / channel) construct a
  `_CogPickView` instead of a bare single-select `BaseView`.
- Tests: replaced the obsolete `caps_at_25` test (it pinned the buggy truncation)
  with `test_cog_pick_view_paginates_without_dropping_any_cog` (every visible cog
  is reachable across pages; each select ≤25) and a nav-presence test.

Pure view-layer change; no service/DB/registry edits. `check_quality --full`
green (10537 passed), `check_architecture --mode strict` 0 errors.

## Context for the queue
This unblocks #941 (image-mod) and #929 (security) once it lands on `main` — each
adds another subsystem and would otherwise widen the same truncation. #1033
(fishing) was merged earlier this session; #929's raid-lockdown bug was fixed on
its branch; #929 itself needs a separate rebuild (orphan history). #941 has a
concurrent session on it.

## 💡 Session idea
Add a lightweight invariant test that asserts **every operator-facing select that
is built from a registry** (cog-routing, and any future ones) either paginates or
provably stays ≤25 options — so the next subsystem that crosses a Discord limit
fails loudly at the source instead of silently dropping entries.

## ⟲ Previous-session review
The session that added the `needs-hermes-review` PRs did the right thing gating
substantial subsystems behind human review, but each added a routable subsystem
without noticing the cumulative cog-routing select was approaching Discord's
25-option ceiling — exactly the kind of cross-PR drift no single PR's tests catch.
Workflow improvement: the session-idea test above turns that class of limit-drift
into a hard CI signal.
