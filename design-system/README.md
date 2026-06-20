# @superbot/design-system

SuperBot's **React + Tailwind component library** — the design-system *source of
truth* that Claude Design's [`/design-sync`](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)
uploads, so the Claude Design agent builds with SuperBot's **real components**
instead of generic ones.

## Why this exists (read before extending)

The public site (`botsite/`) is **server-rendered Jinja2 + Tailwind (CDN)** — it
has no JavaScript components. `/design-sync` can only sync a buildable
JS/TS component library, so this package provides one.

**Production stays Jinja for now.** This library is *design tooling*, not the
live site's runtime: it is the source of truth that feeds Claude Design. The
intended loop is:

1. Build & sync this library to Claude Design (`/design-sync`).
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
| `CommandCard` | the `/commands` reference row |

**Layout / chrome** (mirror `base.html`)

| Component | Mirrors (in `botsite/`) |
|---|---|
| `PageShell` | `<body>` dark canvas + centered `<main>` column + header/footer slots |
| `SiteHeader` | the sticky nav — logo · links · "as of last deploy" status dot · Add-to-Discord |
| `SiteFooter` | the "generated / as of last deploy" freshness footer + source link |

**Sections & page** (mirror `index.html`)

| Component | Mirrors (in `botsite/`) |
|---|---|
| `Hero` | the hero — wordmark · tagline · primary/secondary CTAs |
| `CapabilityBand` | the capability band (3 × `StatTile`, honest catalogue counts) |
| `Section` | the section-header pattern (title + "All features →", or centered) |
| `StepCard` | the "how it works" numbered steps |
| **`LandingPage`** | **the whole `index.html` page composed from the parts above** — the canonical surface Claude Design edits, so every region maps to source |

## Editing the site — the hybrid loop (Claude Design ⇄ Claude Code)

The whole landing page is now real components (`LandingPage` composes them), so on the
Claude Design canvas you can select and edit **any** region — hero, nav, sections — and it
maps to source. The error *"Can't save this edit — element isn't from project source"*
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
npm run storybook    # local component gallery (also used by /design-sync for previews)
```

`dist/` is git-ignored (a build artifact). `/design-sync` runs the build itself
during a sync, so only the source + config are committed.

## Syncing to Claude Design

From the repo root, in Claude Code:

```
/design-sync
```

It detects this package, builds it, generates previews (from the Storybook
stories), and uploads the components to a Claude Design **design-system project**
(it will create one on the first sync). Requires a Pro/Max/Team/Enterprise plan
and a claude.ai login (`/design-login` if prompted).

## Stack

React 18 · TypeScript · Tailwind CSS 3 · tsup (esbuild) · Storybook 8 (Vite).
The package is intentionally framework-conventional so `/design-sync`'s
heuristics recognise it without custom config.
