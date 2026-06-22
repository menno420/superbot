# 2026-06-22 — botsite React-SPA migration PR 1 (foundation: a buildable, data-fed React app)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch (scheduled fire, no work order → advance the next S1 plan slice).
> PR #1305 → auto-merges on green (Q-0123/Q-0191; owner-requested plan lane, not held for review).

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

## Shipped (PR #1305)

- **App shell + hash router** — `design-system/src/app/{main,App}.tsx`. `routeFromHash`
  (pure, in `data.ts`) maps `#/`, `#/features`, `#/commands`, `#/games`, `#/changelog`,
  `#/status`; detail hashes (`#/command/foo` …) fall back to their parent list; unknown → home.
  Each route renders the existing page component with mapped props. `#/games` reuses
  FeaturesPage with the game catalogue only (a dedicated GamesPage is a PR 2+ component).
- **Data adapter** — `design-system/src/app/data.ts`: a typed `SiteData` (the `/site-data.json`
  shape) + pure `to{Landing,Features,Games,Commands,Changelog,Status}Props` mappers +
  `loadSiteData()` (fetch with a bundled-sample fallback on any failure). The real
  `ADD_TO_DISCORD_URL` threads onto every page's `addUrl` → the dead `#/` "Add to Discord"
  CTA is fixed at the data seam.
- **Build target** — `index.html` + `vite.config.ts`; `build:app` (Vite) → static `dist-app/`
  (gitignored — PR 2 commits/serves it). The tsup library `build` (dist/, the `/design-sync`
  artifacts) is untouched and still green.
- **`GET /site-data.json`** (`botsite/app.py`) — `build_prototype_data` shape +
  `build`/`counts`/`addUrl`, as pure JSON. No new `disbot/` coupling; same public subset &
  redaction posture as `/data.js`.
- **Tests/CI** — `src/app/data.test.ts` (13 vitest cases: route mapping, every mapper,
  install-URL threading, loader fallback) + `test_site_data_json_is_truthful_for_the_react_app`
  (botsite). `tsc --noEmit` covers `src/app/`; `design-system-ci.yml` runs `npm test` + `build:app`.
- **Verification:** `npm run typecheck` ✓ · `npm test` 13/13 ✓ · `npm run build:app` ✓ ·
  `npm run build` (library) ✓ · `npm ci` lock in sync ✓ · botsite tests 13/13 ✓ ·
  `check_architecture --mode strict` (no new warnings) · `check_quality --check-only` ✓ ·
  `check_docs --strict` ✓.

**Deferred (PR 2/3):** serve the React bundle from `botsite/` + cutover; per-detail routes +
a dedicated GamesPage; the BUG-0023 command-count *breakdown in the public data* (touches the
`SITE_FIELD_CONTRACT` redaction guard — its own focused slice).

## Session enders

- **♻ Grooming (Q-0015):** advanced the botsite React-SPA migration plan down its lifecycle —
  PR 1 (foundation) now real; PR 2 (serve + cutover) is the next ▶ startable on the S1 sector
  file, which I de-staled (PR 1 moved to "In flight").
- **💡 Session idea (Q-0089):** *A `site-data` ↔ page-props contract guard.* The adapter maps a
  JSON payload onto strongly-typed page props, but a field the Python `/site-data.json` route
  renames/drops would only surface as a silent `undefined` at runtime (the pages fall back to
  sample defaults, masking it). Idea: a tiny CI check (botsite + design-system) that asserts the
  `/site-data.json` keys the route emits == the keys `data.ts` reads — the design↔data contract
  the plan §6 flags, made executable. Cheap; logged here (not yet an idea file — promote if PR 2
  makes the contract load-bearing).
- **⟲ Previous-session review:** the fishing-PR3 session (#1301) modelled exactly the discipline
  this repo wants — a born-red card, a clearly-scoped "deferred to PR4+" list, and a *forward seam*
  (PR2 left `escape_resist` defaulted-0 so PR3 turned it with zero churn). Its own review note —
  *pin invariants on behaviour, not module shape* — is a genuinely reusable rule. **One thing it
  (and the fishing arc) could do better:** four single-slice PRs in a day on one minigame is a lot
  of merge/CI overhead for tightly-coupled work; some of those slices (rod ladder + energy pacing)
  could have been one PR. **System note:** the "small PRs for risky runtime" rule (CLAUDE.md) is
  right, but *sequential same-file slices* that each rev the same workflow/migration chain pay the
  full CI cost N times — worth a journal note that closely-coupled game slices can batch when the
  blast radius is one cog + its pure-domain module.
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓; S1 sector file de-staled (PR 1 in-flight,
  PR 2 next); ledger auto-updates on merge (the recently-shipped reconciliation routine owns it).
  Nothing left only in chat. The plan's PR-1 §4 checklist is fully covered (per-detail routes +
  cutover were always PR 2/3, not PR 1).

## ⚑ Self-initiated: none — this advances an owner-requested, owner-approved plan lane
   (botsite React-SPA migration, the plan's PR 1). The empty scheduled fire → "advance the next
   non-gated plan slice" is the dispatch routine's standing instruction, not an unprompted feature.
   The two in-PR design picks (hash router over `react-router-dom`; `#/games` reusing FeaturesPage
   until a GamesPage exists) are implementation choices within the plan, flagged in the PR.

## 📤 Run report

- **Did:** built the botsite React-SPA migration **PR 1** — a runnable, routable, data-fed React app (the foundation that removes the manual React→vanilla port). · **Outcome:** shipped
- **Shipped:** #1305 — `design-system/src/app/` (hash router + page wiring), `data.ts` adapter + 13 vitest cases, `build:app` → `dist-app/`, botsite `GET /site-data.json` + test, design-system CI runs vitest + build:app. Additive — live vanilla SPA untouched.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (a merge auto-deploys; PR 2 handles the live cutover)
- **⚑ Self-initiated:** `none` — advances the owner-requested/approved botsite-react-spa-migration plan (its PR 1)
- **↪ Next:** botsite React-SPA migration **PR 2** — serve the built React bundle from `botsite/` (CI build → `botsite/site/`, avoid the `static/` #970 gotcha) + keep the vanilla SPA/Jinja as a one-band fallback, flip `/` to React last. Per-detail routes + a GamesPage component, and the BUG-0023 count-breakdown-in-data slice, remain. Project Moon runtime PR 1 (ingestion — network + IP/licensing-sensitive, weigh ask-first) is the other S1 lane.
