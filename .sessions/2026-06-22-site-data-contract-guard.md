# 2026-06-22 — botsite↔design-system data-contract guard (de-risking the React-SPA cutover)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch ("Continue from where you left off" after PR #1305 merged).
> PR #1308 → auto-merges on green (Q-0123).

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

## Shipped (PR #1308)

- **Canonical contract** — `botsite/data/site_data_contract.json`: the `/site-data.json`
  top-level keys + required per-entry keys (area/command/game/changelog) + `build`/`counts`
  sub-keys. One source of truth both languages validate against. Pins the *floor* (required
  guaranteed keys), not a freeze — optional fields stay optional.
- **Producer owns assembly + validation** — `site_data.build_site_data_payload(site, add_url)`
  (pure, stdlib) now assembles the full payload; `validate_site_data_payload(payload)` returns
  a list of violations (missing/extra top-level keys, missing `build`/entry sub-keys);
  `load_site_data_contract()` reads the JSON. The `app.py` `/site-data.json` route is now a
  thin two-line wrapper over the assembler.
- **Python guard (main CI)** — `tests/unit/botsite/test_site_data.py` gained 6 stdlib cases:
  the real payload conforms; carries real data + the install URL; the validator catches a
  missing top-level key, an unexpected one, a missing entry sub-key; the contract file is the
  loaded source. These run in `code-quality` (stdlib-only), unlike the FastAPI-gated
  `test_app.py` — so producer drift fails *there*, not just in `botsite-tests`.
- **TS guard (design-system CI)** — `data.test.ts` reads the SAME contract JSON and asserts the
  adapter's consumed top-level keys ⊆ the contract, and that the bundled sample satisfies it
  (added `@types/node` for the cross-package `fs` read). 15 vitest cases pass.
- **Verification:** `test_site_data.py` 18 ✓ · `test_app.py` 13 ✓ · vitest 15 ✓ · `tsc --noEmit`
  ✓ · `build:app` ✓ · library `build` ✓ · `npm ci` lock in sync ✓ · `check_quality --check-only`
  ✓ · `check_architecture` 0 errors · dashboard-data + freshness guards green (the new JSON
  doesn't trip them — they key off `site.json` by exact path).

## Session enders

- **♻ Grooming (Q-0015):** advanced the React-SPA migration's *safety* down its lifecycle — the
  plan §6 "page props drift from `/site-data.json`" risk is now an executable guard, not just a
  flagged row. Makes PR 2 (the live cutover) trustworthy.
- **💡 Session idea (Q-0089):** *Extend the contract guard to the legacy `/data.js` seam too.*
  `window.SBDATA` (the vanilla SPA's data layer) has the SAME drift exposure as `/site-data.json`
  but no key contract — `build_prototype_data`'s output shape is only pinned by the existing
  `test_command_fields_match_contract`-style exact-set tests, which are *stricter* (freeze, not
  floor) and live only in `test_site_data.py`. Idea: once PR 3 retires `/data.js`, this guard is
  the survivor; until then, a one-line note that the two contracts must agree would prevent a
  half-migration drift. Cheap; logged here.
- **⟲ Previous-session review:** my own PR #1305 (this session's predecessor) did the foundation
  well but left the adapter's **silent sample-default fallback** as the one soft spot — a missing
  producer key degrades quietly instead of erroring, which is friendly at runtime but hides drift.
  This PR is the direct correction: the fallback stays (good UX), but CI now fails loudly on the
  drift it would mask. **System note:** "graceful degradation" and "fail-loud-on-contract-violation"
  aren't in tension when you put the loud failure in *CI* and the graceful one in *production* —
  worth generalising as a pattern (degrade for users, assert for the build).
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓; no sector-file content change needed (this is
  a guard, not a feature — the S1 "PR 2 next" pointer from PR #1305 still stands); ledger
  auto-updates on merge. Nothing left only in chat.

## ⚑ Self-initiated: yes (Q-0172) — I promoted my OWN PR-#1305 logged session idea (the design↔data
   contract guard) to a build, with no dispatch order or owner ask (the run was an empty "continue").
   It's a small, reversible, test-only-plus-thin-refactor safety guard squarely inside the
   owner-approved React-SPA migration plan (§6's named risk), so it ships self-merged on green rather
   than `needs-hermes-review`. Flagged here for the owner to review/revert.

## 📤 Run report

- **Did:** shipped a botsite↔design-system **data-contract guard** — the `/site-data.json` seam is now pinned by one canonical contract both languages validate against, so producer-side drift fails CI instead of silently shipping a broken React site post-cutover. · **Outcome:** shipped
- **Shipped:** #1308 — `site_data_contract.json` + `build_site_data_payload`/`validate_site_data_payload` (assembly out of the route), 6 stdlib Python contract tests (main CI) + a cross-package TS test reading the same contract.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **yes** — promoted my PR-#1305 logged idea (the design↔data contract guard) to a build on an empty "continue" fire; small/reversible/in-plan (§6 risk) → self-merged on green. Review/revert at will.
- **↪ Next:** botsite React-SPA migration **PR 2** — serve the built React bundle from `botsite/` (CI build → `botsite/site/`, avoid the `static/` #970 gotcha), keep the vanilla SPA/Jinja as a one-band fallback, flip `/` to React **last**. ⚠️ PR 2's own verification requires a **manual browser click-through (zero console errors)** — best run attended / owner-previewed, not flipped blind in an unattended run. The contract guard shipped here makes that cutover trustworthy on the data side. Project Moon runtime PR 1 (ingestion) remains the other S1 lane (network + IP/licensing-sensitive → weigh ask-first).
