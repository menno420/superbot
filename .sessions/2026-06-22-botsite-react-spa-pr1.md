# 2026-06-22 — botsite React-SPA migration PR 1 (foundation: a buildable, data-fed React app)

> **Status:** `in-progress` — born-red card (Q-0133). Flips to `complete` as the final step.
> Routine · dispatch (scheduled fire, no work order → advance the next S1 plan slice).

## Arc (what I'm about to do)

Empty scheduled dispatch fire. Fishing PR4 (#1304) and reaction-roles PR6 (#1279) are in
flight (not mine). S2 is creds-gated; the procedures→skills batch edits CLAUDE.md (Q-0106,
owner-review territory). The cleanest non-gated high-value S1 startable item is the
**botsite React-SPA migration** ([plan](../docs/planning/botsite-react-spa-migration-plan-2026-06-20.md))
— owner-requested, removes the manual "port React → vanilla SPA" step. Building **PR 1**
(additive, the live vanilla SPA stays serving until PR 2).

This PR (foundation only — no cutover):
1. **App shell + hash router** — `design-system/src/app/` (`main.tsx` + `App.tsx`) routing the
   existing page components: `#/` → LandingPage · `#/features` → FeaturesPage · `#/commands` →
   CommandsPage · `#/games` → games view (FeaturesPage games group) · `#/changelog` →
   ChangelogPage · `#/status` → StatusPage. Hash router (matches the SPA URL scheme; no server
   route changes).
2. **Data adapter** — `design-system/src/app/data.ts`: `fetch()` the live `/site-data.json`,
   map the SBDATA shape (`areas/commands/games/changelog/status` + `addUrl`) onto each page's
   props. Pure mappers + a bundled sample for fallback/tests.
3. **Install URL fix** — thread the real `ADD_TO_DISCORD_URL` (already in `botsite/chrome.py`)
   through `/site-data.json` → adapter → every page's `addUrl`, so the live "Add to Discord"
   CTA stops being a dead `#/` link.
4. **Build target** — `build:app` (Vite, already a devDep) → static `dist-app/`; the existing
   `build` (tsup library + tailwind) untouched.
5. **Data delivery (Decision B(a))** — `botsite/` route `GET /site-data.json` returning the same
   data `build_prototype_data` produces, as pure JSON (no new disbot coupling; same public subset).
6. **Tests/CI** — vitest data-adapter smoke test (sample SBDATA → valid page props) + a botsite
   test that `/site-data.json` is truthful; `tsc --noEmit` covers `src/app/`; `design-system-ci.yml`
   gains a `build:app` + `test` step.

**Deferred (later PRs / out of scope):** serving the React build from `botsite/` + cutover
(PR 2/3); per-detail routes (`#/command/<name>` etc.) and a dedicated GamesPage component;
BUG-0023 command-count *breakdown in the public data* (touches the redaction contract — its own
slice). PR 1 leaves visitors on the vanilla SPA.

## Shipped

_(filled at close)_

## Session enders

_(filled at close)_
