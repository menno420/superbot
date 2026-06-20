# 2026-06-20 — Design-system: full landing-page composition + hybrid edit loop

> **Status:** `in-progress`

## Arc (what this session is about)

Owner is trying out **Claude Design** and kept hitting *"Can't save this edit — element
isn't from project source"* when editing the hero. Root cause: only the 6 atomic components
from `design-system/` (#1168) are source-backed; the hero / nav / section layout are
generated canvas content with **nowhere in source to save to**. Owner chose **Path 1** —
expand the design-system so the **whole landing page** is real, source-backed components, and
tighten the **hybrid Claude Code + Claude Design workflow** (me as porter/reviewer; preview
without merge+redeploy each iteration).

Owner directive this session: *"anything documented in the repo is based on the situation when
we documented it — good guidelines, not 100% strict rules. Do what's best for the vision:
correctness over temporary fixes, stability first."* So I'm free to extend `design-system/`
beyond the literal ask where it makes the loop genuinely usable.

## Plan (this PR)

- New layout/page components mirroring `botsite/` (`base.html` + `index.html`), faithful
  palette (slate/indigo/sky/emerald/amber): `PageShell`, `SiteHeader`, `SiteFooter`, `Hero`,
  `Section`, `StepCard`, `CapabilityBand`, `ButtonLink`, and a full `LandingPage` composition.
- A Storybook story per new component + the full-page `LandingPage` story (the `/design-sync`
  preview source) — so Claude Design composes/edit the *whole page* as real components.
- Expand `design-system/README.md`: components table + the **hybrid / preview-without-redeploy**
  loop (Claude Design canvas ⇄ Claude Code porter ⇄ local preview).
- Add `design-system-ci.yml` (the JS CI leg the predecessor flagged) — checkout + `npm ci` +
  `typecheck` + `build`, path-scoped to `design-system/**`, runner-preinstalled Node (only the
  already-pinned `actions/checkout` SHA, no unverified `setup-node` pin).
- Verify: `npm ci` / `npm run typecheck` / `npm run build` green in-container.

_Shipped / verification / enders filled in as the deliberate final step, then Status → complete._
