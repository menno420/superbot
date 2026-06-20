# 2026-06-20 — Design-system component library (for Claude Design `/design-sync`)

> **Status:** `complete`

## Arc

Owner conversation about **Claude Design** (the Anthropic Labs product) and the `/design-sync`
command, which "did nothing" when they tried it. Diagnosed the root cause, then — at the owner's
explicit choice — built the prerequisite it was missing.

**Why `/design-sync` did nothing (verified):** the skill converts an *existing* React/TS component
library (a buildable `dist/`, ideally Storybook) and uploads it to a claude.ai/design design-system
project. SuperBot had **no JS/component library at all** — confirmed by repo scan: no `package.json`,
no `.tsx/.jsx/.ts`, no Storybook, no `dist/`. The web tier (`botsite/`, `dashboard/`) is
FastAPI + Jinja2 + Tailwind-CDN with no JS build. So there was nothing for the skill to sync.

The owner chose (AskUserQuestion) to **build a component library** so `/design-sync` becomes usable.

## What shipped (this PR)

New top-level **`design-system/`** — `@superbot/design-system`, a real, buildable React + Tailwind
component package:

- **Build:** `tsup` (esbuild) → `dist/index.js` + `dist/index.d.ts`; `tailwindcss` → `dist/styles.css`.
  This compiled `dist/` is exactly what `/design-sync` consumes ("ship what you already built").
- **Components (6, faithful to `botsite/`):** `Button` (Add-to-Discord CTA), `Badge`
  (finished/in-progress/game/changelog kinds), `Card`, `StatTile` (capability band), `FeatureCard`,
  `CommandCard` — same Tailwind palette the live site renders (slate/indigo/sky/emerald/amber).
- **Storybook 8 (Vite)** with a story per component (the high-fidelity preview source `/design-sync`
  uses) + `.storybook/{main,preview}.ts`.
- **Tooling:** `tsconfig.json`, `tsup.config.ts`, `tailwind.config.cjs`, `postcss.config.cjs`,
  `README.md` (rationale + Jinja-relationship + how to run `/design-sync`).
- `.gitignore` += `node_modules/`, `storybook-static/`, `*.tsbuildinfo` (`dist/`/`build/` already ignored).

## Verification (all green, in-container)

- `npm install` → 304 packages, no install errors (5 advisories are Storybook dev-dep tree; not forced).
- `npm run build` → **exit 0**; `dist/` = `index.js` (3.5 KB) · `index.d.ts` · `index.js.map` · `styles.css`.
- `npm run typecheck` (`tsc --noEmit`) → **clean**.
- `npm run build-storybook` → **exit 0** (manager + preview built).
- `check_quality --check-only`, `check_architecture --mode strict`, `check_docs --strict` → pass
  (the new non-Python dir is inert to the Python toolchain; pre-existing warnings unrelated).

**Bug fixed mid-build:** with `"type": "module"`, the `module.exports` config files broke Vite's
PostCSS loader (`module is not defined in ES module scope`). Fixed by giving the CommonJS configs an
explicit `.cjs` extension (`postcss.config.cjs`, `tailwind.config.cjs`). Build + Storybook green after.

## Decisions

- **Location:** new top-level `design-system/` (peer of `disbot/`, `botsite/`, `dashboard/`).
- **Stack:** React 18 / TS / Tailwind 3 / tsup / Storybook 8 — deliberately *conventional* so
  `/design-sync`'s heuristics recognise it without custom config.
- **Production stays Jinja.** This library is the **design-system source of truth that feeds Claude
  Design**, not the live site's runtime. Loop: build → `/design-sync` → design on the canvas with real
  components → port back into `botsite/` Jinja via Claude Code (Tailwind classes transfer 1:1). A future
  `botsite/`→JS migration would make this the production UI and drop the port step — separate decision,
  not assumed. Recorded in `design-system/README.md`.
- **PR: auto-merge on green** (the normal `claude/*` flow, owner-directed). The change is additive and
  isolated — nothing imports `design-system/`, Python CI is untouched, the new dir triggers no existing
  workflow, and it's fully reversible — so it meets the contained/verifiable bar for the standard flow
  rather than the hold carve-out.

## ⚑ Owner decision captured

- **2026-06-20 (AskUserQuestion):** build a React component library so `/design-sync` is usable
  (chosen over "design on the canvas" and "DS lives elsewhere"). Provenance for the new `design-system/`.

## ⟲ Previous-session review (Q-0102)

The website two-site-split chain (the immediately-relevant prior work) shipped `botsite/` as
Jinja2 + Tailwind-CDN — the right call for a fast, secret-free marketing site. What it didn't
anticipate: that framework choice means design tooling like `/design-sync` (JS/component-oriented) has
nothing to attach to. Not a fault — but a **system signal**: when we pick a web-tier framework, we
should note its downstream tooling implications. **Improvement:** `docs/planning/website-two-site-split-plan-2026-06-19.md`
could carry a one-line "design-tooling note" (Jinja = no component-library sync; use the canvas +
port) so the next agent doesn't rediscover this.

## 💡 Session idea (Q-0089)

**Extend the planned `web-ci.yml` matrix with a `design-system` leg** (`npm ci` + `npm run build` +
`npm run typecheck`). The web-tier-centralization proposal already plans a matrix over `dashboard` +
`botsite` (Python pytest); the design-system needs a *JS* leg so it stays green like the other tiers
(today nothing in CI builds it). Small, additive, and it closes the "new toolchain with no CI" gap this
session opened. Dedup-checked: the proposal mentions the matrix but not a JS/design-system leg.

## 📊 Doc audit (Q-0104)

- Rationale + usage durably in `design-system/README.md`; owner decision in this log + the active-work
  claim. `check_docs --strict` green (the README is package-local, not a `docs/` node).
- Follow-ups noted (not yet built): a JS CI leg; porting any canvas output back into `botsite/` Jinja.

## 📤 Run report

- **Did:** diagnosed why `/design-sync` no-ops on SuperBot (no component library); at the owner's choice,
  built + verified a real React+Tailwind+Storybook component library (`design-system/`) that the skill
  can sync. · **Outcome:** built + verified; PR opened, **auto-merge on green**.
- **Run type:** `manual` (owner-directed, interactive).
- **⚑ Self-initiated:** `none` — the build was the owner's explicit choice; scope/stack/location were my
  judgment within it. (The earlier botsite restyle attempt was reverted when the owner clarified intent.)
- **↪ Next:** run `/design-sync` against this branch to upload the components; add the JS CI leg; port
  Claude Design canvas output back into `botsite/` Jinja.
