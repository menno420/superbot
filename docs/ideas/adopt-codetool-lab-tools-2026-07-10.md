# Adopt the codetool-lab tools as fleet tools (2026-07-10)

> **Status:** `ideas` — raised 2026-07-10 (owner repo-disposition review, live session).
> **Subsystem:** tooling / product-forge intake.
> **Gate:** ready — all three tools are built, tested, and public.

## The idea

The three codetool-lab "test" repos each produced a real, working CLI product; instead of
letting them rot, adopt them as fleet tools:

- **mdverify** (`codetool-lab-opus4.8`) — verifies that code blocks in markdown docs
  actually run. **Released** (v0.1.0 + v0.2.0 GitHub Releases, 162 tests). Immediately
  useful for a fleet this documentation-heavy: run it over `docs/` in CI-adjacent passes.
- **envdrift** (`codetool-lab-fable5`) — .env drift checker (111 tests; tags unpushed).
  Directly relevant to the owner's environment-tidying interest.
- **cfgdiff** (`codetool-lab-sonnet5`) — semantic config diff/convert (165 tests; v0.1.1
  pending an owner tag push). Its differential-testing method (corpus vs a reference
  parser found 3 real bugs behind green tests) is worth porting into kit-lab's benchmark
  practice even if the tool itself sees little use.

## Disposition context (owner review, 2026-07-10 session)

Delete **no repos**. Keep opus4.8 unarchived (live released tool + the proven
`workflow_dispatch` release recipe). Archive sonnet5 + fable5 (GitHub read-only) **after**
this idea executes — archiving preserves the record while shrinking the active surface,
but blocks future writes, so harvest first. Also fix fable5's committed `.pyc` files +
missing `.gitignore` before archiving (the one unflagged defect of the wind-down).

## First slice

A product-forge (or superbot tooling) session: pin mdverify as a dev dependency (or
vendored script), run it over `docs/` once, triage what it finds; file envdrift into the
environments-standardization lane (round-3 pack / centralization candidate 5). Dedup:
nothing in `docs/ideas/` covers lab-tool adoption.
