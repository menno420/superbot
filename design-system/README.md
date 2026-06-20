# @superbot/design-system

SuperBot's **React + Tailwind component library** — the design-system *source of
truth* Claude Design builds with, so its agent composes pages from SuperBot's
**real components** instead of generic ones. Claude Design reads this library
straight from the repo via the **GitHub connector**; `/design-sync` is an
alternative manual upload. See [Connecting to Claude Design](#connecting-to-claude-design).

## Why this exists (read before extending)

The public site (`botsite/`) is **server-rendered Jinja2 + Tailwind (CDN)** — it
has no JavaScript components. Claude Design builds with a JS/TS component library,
so this package provides one.

**Production stays Jinja for now.** This library is *design tooling*, not the
live site's runtime: it is the source of truth that feeds Claude Design. The
intended loop is:

1. Get this library into Claude Design — via the **GitHub connector** (it reads
   the repo directly, so merging to the connected branch *is* the sync) or the
   `/design-sync` upload. See [Connecting to Claude Design](#connecting-to-claude-design).
2. Design pages on the Claude Design canvas — the agent now composes SuperBot's
   real components, so output maps 1:1 onto these parts.
3. Port the resulting design back into the `botsite/` Jinja templates via Claude
   Code (the Tailwind classes transfer directly; the markup is adapted).

This means the components here are **deliberately faithful to what `botsite/`
already renders** (same Tailwind palette: slate / indigo / sky / emerald /
amber). Keep them in sync with the templates so designs stay shippable. A future
migration of `botsite/` to a JS frontend — if ever desired — would make this
library the production UI and remove the port step; that is a separate decision,
not assumed here.

## Components

**Atoms**

| Component | Mirrors (in `botsite/`) |
|---|---|
| `Button` / `ButtonLink` | the "Add to Discord" CTA + secondary buttons — `<button>` and the anchor-as-button the live site actually renders (shared style via `buttonClasses`) |
| `Badge` | command status (`finished`/`in-progress`), `game`, changelog kinds |
| `Card` | the standard bordered surface |
| `StatTile` | a single homepage capability-band count |
| `FeatureCard` | the "what it does" / `/features` category cards |
| `CommandCard` | the `/commands` reference row (compact) |
| `SearchBar` | the `/features` + `/commands` search input |
| `Pill` | the category jump / filter chips (active + link/button variants) |

**Layout / chrome** (mirror `base.html`)

| Component | Mirrors (in `botsite/`) |
|---|---|
| `PageShell` | `<body>` dark canvas + centered `<main>` column + header/footer slots |
| `SiteHeader` | the sticky nav — logo · links · "as of last deploy" status dot · Add-to-Discord |
| `SiteFooter` | the "generated / as of last deploy" freshness footer + source link |
| `PageHeader` | a page title + subtitle (plain, or bordered with a "generated" badge) |

**Sections** (page building blocks)

| Component | Mirrors (in `botsite/`) |
|---|---|
| `Hero` | the homepage hero — wordmark · tagline · primary/secondary CTAs |
| `CapabilityBand` | the capability band (3 × `StatTile`, honest catalogue counts) |
| `Section` | the section-header pattern (title + "All features →", or centered) |
| `StepCard` | the "how it works" numbered steps |
| `FeatureShowcaseCard` | a single `/features` card — emoji · name · `game` badge · tags · "See commands" |
| `CommandEntry` / `CommandDetail` | a `/commands` expandable `<details>` card and its detail body (aliases · permissions · examples · "what's planned") |
| `ChangelogEntry` | a `/changelog` timeline entry — kind label · title · summary · "Details" |
| `StatusCard` | the `/status` "online as of last deploy" build card |

**Pages** (full per-route compositions — the surfaces Claude Design edits)

| Component | Mirrors (in `botsite/`) |
|---|---|
| `LandingPage` | the whole `index.html` homepage |
| `FeaturesPage` | `/features` — searchable, category-jump pills, feature grid |
| `CommandsPage` | `/commands` — searchable, filter pills, expandable command list |
| `ChangelogPage` | `/changelog` — date-grouped "what's new" timeline |
| `StatusPage` | `/status` — build trust card + "what's in the box" counts |

Each page is composed inside `PageShell` (with `SiteHeader` + `SiteFooter`), so **the whole site** — not just one page — is editable in Claude Design, every region mapping back to source.

## Editing the site — the hybrid loop (Claude Design ⇄ Claude Code)

Every page is now real components (`LandingPage`, `FeaturesPage`, `CommandsPage`,
`ChangelogPage`, `StatusPage`), so on the Claude Design canvas you can select and edit **any**
region of **any** page — hero, nav, cards, sections — and it maps to source. The error *"Can't save this edit — element isn't from project source"*
appears when you edit something that *isn't* a synced component; composing pages from these
parts is what avoids it. Roles:

- **Claude Design** = the visual canvas. Drive it by *prompting the agent* ("make the hero
  two-column", "warmer palette") as much as by hand-editing — property-panel edits only
  persist for source-backed components, which is now the whole page.
- **Claude Code** (the porter + reviewer) = takes canvas output and ports it into the
  `botsite/` Jinja templates (Tailwind classes transfer 1:1), keeping it correct and
  consistent — Claude Design is weak at searching this repo and mapping a design to the
  right files, so this step stays with Claude Code. Just say "port what I just designed."

### Preview without merging / redeploying

You don't have to merge to `main` (which redeploys the Railway site) to see a change — two
local previews cover the two layers:

```bash
# 1. The design layer (these components, incl. the full-page LandingPage story):
npm run storybook                  # http://localhost:6006 → Pages/LandingPage

# 2. The real site (Jinja — exactly what ships):
pip install -r botsite/requirements.txt
uvicorn botsite.app:app --reload   # http://127.0.0.1:8000
```

On Claude Code on the web, ask Claude Code to run either and screenshot the result — so the
loop is **design → port → preview → approve → merge**, with the merge (and redeploy) only at
the end.

## Build

```bash
npm install
npm run build        # tsup → dist/ (ESM + .d.ts) and the compiled dist/styles.css
npm run typecheck    # tsc --noEmit
npm run storybook    # local component gallery (also the /design-sync preview source)
```

`dist/` is git-ignored (a build artifact) — Claude Design and `/design-sync` build
from source, so only the source + config are committed.

## Connecting to Claude Design

Two ways to get these components into Claude Design — pick one:

### GitHub connector (primary — what this project uses)

Enable Claude Design's **GitHub connector** for this repo (in claude.ai → Settings →
Connectors). Claude Design then reads the component library **straight from the repo**:

- **The repo is the sync.** Whatever is on the connected branch (normally `main`) is what
  Claude Design sees — **merging a PR is what publishes new/changed components.** There is no
  separate upload step and no `/design-sync` to run.
- After a merge, **refresh / reopen the Claude Design project** so it re-reads the latest
  commit. If Claude Design lets you select a branch, you can preview a branch *before* it
  merges.
- **The connector is READ-ONLY in this project** (owner-confirmed 2026-06-20): GitHub grants
  it read access only and exposes no write toggle. So Claude Design **cannot** commit or open
  PRs back to the repo — canvas edits are exported manually (a handoff zip) and a **Claude Code
  step commits them**. The read path (repo → Claude Design) is the only automatic half.

### `/design-sync` (alternative — manual upload)

If you are *not* using the connector, run [`/design-sync`](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)
from the repo root in Claude Code. It detects this package, builds it, generates previews
(from the Storybook stories), and uploads the components to a Claude Design **design-system
project** (created on first sync). Requires a Pro/Max/Team/Enterprise plan and a claude.ai
login (`/design-login` if prompted).

## Stack

React 18 · TypeScript · Tailwind CSS 3 · tsup (esbuild) · Storybook 8 (Vite).
The package is intentionally framework-conventional so Claude Design (and
`/design-sync`) recognise it without custom config.
