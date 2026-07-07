# 2026-07-07 — Program websites: design system + botsite v2 + console shell (Fable session 1/4)

> **Status:** `in-progress`
> **Branch:** `claude/website-design-brief-ryc3do` · **Model:** Fable 5 / ultracode
> **Brief:** [`docs/planning/website-design-fable-brief-2026-07-07.md`](../docs/planning/website-design-fable-brief-2026-07-07.md) (Q-0253 last-Fable-day design session; Q-0241 never-wait governance)

## What is about to happen

Build, in strict priority order per the brief:

1. **The program design system** — an improved evolution of the botsite neon look as a reusable
   foundation: design tokens (dark-first + real light theme), component library, layout patterns,
   accessibility, and a living style-guide page that renders every component.
2. **Botsite v2** — the improved public site on that system over the real `site.json` data.
   v1's three design-owned files (`botsite/site/index.html`/`app.js`/`app.css`) stay untouched;
   v2 = new files, v1 remains the wired fallback.
3. **The program console shell** — one-glance page with honest placeholder lanes + declared data
   contracts (run reports/⚑ flags, Q-0248/Q-0249 telemetry lanes, port-progress slot, trading slot).
4. **Sim-informed UX checks** — Playwright task-success checklist with click budgets;
   nav/perf/accessibility budgets.

Verification: run the FastAPI app live, screenshot every page in both themes at 3 widths, run the
task checklist, attach proof to the PR.

## Close-out

(to be written — flip status to `complete` as the deliberate final step)
