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

| Component | Mirrors (in `botsite/`) |
|---|---|
| `Button` | the "Add to Discord" CTA + secondary buttons |
| `Badge` | command status (`finished`/`in-progress`), `game`, changelog kinds |
| `Card` | the standard bordered surface |
| `StatTile` | the homepage capability band counts |
| `FeatureCard` | the "what it does" / `/features` category cards |
| `CommandCard` | the `/commands` reference row |

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
