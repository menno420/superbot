# 2026-06-20 — Design-system: compose the rest of the site (Features/Commands/Changelog/Status)

> **Status:** `in-progress`

## Arc

Third PR of this session (after #1175 landing page + #1176 connector docs). The owner — mid
Claude Design exploration, re-syncing the repo into a fresh project — asked "anything we can do
meantime?" and chose **compose the rest of the site** so Claude Design can edit *every* page, not
just the landing page. Extends Path 1 (whole-page source-backed components) across all routes.

First I ran a fidelity audit of the existing landing-page components against the real
`botsite/templates/*.html` — they match class-for-class (only 3 cosmetic button drifts, deferred).
Then built the remaining pages from the actual templates.

## What shipped (this PR)

New components mirroring the real templates (verified against `botsite/templates/`):
- **Building blocks:** `PageHeader` (plain + bordered/"generated" variants), `SearchBar`, `Pill`
  (active + link/button), `FeatureShowcaseCard`, `CommandDetail` + `CommandEntry` (native
  `<details>`, JS-free), `ChangelogEntry`, `StatusCard`.
- **Full page compositions** (each inside `PageShell` + header/footer, sample-data defaults):
  `FeaturesPage`, `CommandsPage`, `ChangelogPage`, `StatusPage` — joining `LandingPage`.
- A Storybook story per new component + page (the canvas / `/design-sync` preview surfaces).
- `index.ts` exports + README components table (new Sections group + a Pages group) updated.

Now all five public routes are real, source-backed components → Claude Design can edit the whole
site. Additive + isolated; production stays Jinja (`botsite/`), ported back by Claude Code.

## Verification (in-container)

- `npm run typecheck` (`tsc --noEmit`) → clean.
- `npm run build` → exit 0; `dist/index.d.ts` 10 KB → **19.4 KB** (all new components), CSS rebuilt.
- `design-system-ci` re-runs on the PR (path filter) — mirrors the local typecheck + build.

## Decisions made alone

- Mirrored the templates **class-for-class** (faithful starting blocks port cleanly); kept the
  interactive `<details>` for commands so it works JS-free like the template.
- Built `FeatureShowcaseCard` as a NEW component (distinct from the homepage `FeatureCard`, which
  is a category card) rather than overloading the latter.
- Changelog kind badge uses the template's exact classes (`px-2.5`/`text-xs`/`font-medium`/`ring-1`)
  rather than the uppercase `Badge` atom — Badge's `new/improved/fixed` tones differ in size, so
  faithfulness won over reuse here.
- Sample-data defaults on every page so they render standalone in Storybook / on the canvas; the
  live site passes real data.

## Fidelity audit (recorded, deferred)

The landing-page components match `botsite/` exactly except three cosmetic button drifts: hero
"Explore features" is `font-semibold` (site: `font-medium`); the bottom CTA uses the standard size
(site: larger `px-7 py-3`); primary buttons add `text-white` + `transition-colors`. All inherited
from the #1168 button atom; left for the owner (they're restyling on the canvas anyway).

## Session enders

Session-level enders (Q-0089 idea, Q-0102 prev-session review, Q-0015 grooming, Q-0104 doc audit,
telemetry) were completed in `.sessions/2026-06-20-design-system-landing-page.md` — this is the
same session's 3rd PR, so not duplicated (the Q-0089/Q-0102 no-filler bar). One genuine **new idea**
this build surfaced: a **route manifest** mapping each `*Page` → its `botsite/` template + URL, so a
coverage check can assert every route has a component (complements the parity-guard idea from #1175).

## 📤 Run report

- **Did:** composed the remaining four site pages (Features/Commands/Changelog/Status) + their
  components as real, source-backed parts faithful to `botsite/`, so Claude Design can edit the
  whole site. · **Outcome:** built + verified (typecheck/build green); PR auto-merges on green.
- **Run type:** `manual` (owner-directed, interactive).
- **⚑ Owner manual steps:** re-sync the Claude Design project; the new pages appear under `Pages/`
  (FeaturesPage, CommandsPage, ChangelogPage, StatusPage).
- **⚑ Self-initiated:** the fidelity audit + the route-manifest idea (proactive); the page-build
  itself was owner-chosen.
- **↪ Next:** owner designs pages on the canvas → tell Claude Code to port to `botsite/`. Optional:
  the 3 button-drift fixes; the parity / route-manifest guards.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | #1175 + #1176 merged; this is #3 (auto-merge on green) |
| New components | 8 building blocks + 4 page compositions |
| CI-red rounds | 0 real (born-red gate only) |
| New ideas | +1 (route manifest) |
