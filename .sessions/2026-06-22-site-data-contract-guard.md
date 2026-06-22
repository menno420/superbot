# 2026-06-22 — botsite↔design-system data-contract guard (de-risking the React-SPA cutover)

> **Status:** `in-progress` — born-red card (Q-0133). Flips to `complete` as the final step.
> Routine · dispatch ("Continue from where you left off" after PR #1305 merged).

## Arc (what I'm about to do)

PR #1305 (botsite React-SPA migration PR 1) merged. The plan's next slice (PR 2) is the
**live-site cutover** — flip `/` to the React build — whose own verification step requires a
manual browser click-through (zero console errors). Flipping the public site's `/` blind, in an
unattended run, is imprudent, so I'm **not** doing the cutover here. Instead I'm shipping the
**design↔data contract guard** I logged as PR 1's session idea — the executable form of the
plan §6 "page prop shapes drift from `/site-data.json`" risk. It makes the eventual cutover
trustworthy and fails *loudly* on producer-side drift (today the React adapter silently falls
back to sample defaults on a missing key — exactly the drift that would ship a broken site).

This PR:
1. **One canonical contract** — `botsite/data/site_data_contract.json`: the top-level keys of the
   `/site-data.json` payload + the required sub-keys per entry type (area/command/game/changelog).
2. **Producer owns + assembles + validates** — move the payload assembly out of the `app.py`
   route into a pure `site_data.build_site_data_payload(site, add_url)` (stdlib, testable without
   FastAPI), with `validate_site_data_payload()` checking it against the contract. The route
   becomes a thin wrapper.
3. **Both languages check the same file** — a stdlib botsite test (runs in the main `code-quality`
   CI, unlike the FastAPI-gated `test_app.py`) asserts the real payload conforms; a design-system
   vitest test reads the same contract JSON and asserts the React adapter never consumes a
   top-level key the contract doesn't promise. Neither side can drift silently.

**Why not just trust tsc:** tsc covers the *consumer* shape, but a producer (Python) that
renames/drops a key compiles fine on the TS side and only surfaces as a silent `undefined` →
sample-default fallback at runtime. The contract test catches it at the seam.

## Shipped

_(filled at close)_

## Session enders

_(filled at close)_
