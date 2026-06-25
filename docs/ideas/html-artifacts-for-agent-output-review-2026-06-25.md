# HTML artifacts as the review medium for agent output

> **Status:** `ideas` — capture only (not a plan, not approval). **Owner-shared 2026-06-25**
> (chat): the maintainer flagged an InfoQ writeup of Anthropic's HTML-vs-Markdown-for-agents
> argument as *"might be useful for us, not per se necessary — and we already have a little
> bit of this through our websites."* Source + binding contracts + `current-state.md` win
> over this file.
> **Subsystem:** none — agent-workflow / dev-site surface, not a bot subsystem.

## The seed

InfoQ, *"HTML vs Markdown for AI Agents"*
([link](https://www.infoq.com/news/2026/06/anthropic-html-markdown-agent/)), reporting
Anthropic's Thariq Shihipar: as agent outputs grow past ~100 lines, **Markdown becomes a
restrictive review format** — a wall of text the human skims and rubber-stamps. He advocates
**single-file HTML artifacts** (color-coded, scannable, lightly interactive) for spec/planning
docs, code review/comprehension, data exploration, and prototyping — the goal being to **keep a
human genuinely engaged at the decision points** (goal-setting, requirement refinement, output
validation) rather than passively accepting.

**Caveat up front:** the piece is an opinion + visual examples with **zero quantitative
results** — no productivity numbers, no study. Treat it as a design intuition to test, not a
proven technique.

## Why it lands harder for *us* than for most teams

This project's whole premise (`docs/collaboration-model.md`,
`docs/owner/maintainer-working-profile.md`) is that the maintainer **designs and visualizes,
can't read code**, and steers a fleet of agents that emit a *lot* of long-form Markdown:
session logs (`.sessions/`), reconciliation + band-planning reports, `current-state.md`, the
question router, the idea backlog. That is **exactly the "100+ line Markdown nobody really
reviews" failure mode** the article describes — and the review bottleneck it targets is the
human (the owner), which is the real artifact this project is building.

## Distinct from what we already have

Not a duplicate of the existing dashboard work — those are *data-surfacing products*; this is
about *agent output itself* being rendered as an HTML review artifact at decision points:

- [`developer-dashboard-2026-06-16.md`](./developer-dashboard-2026-06-16.md) — LIVE dashboard
  that *reads* structured project data (registry, ideas, bug book). Complementary substrate.
- [`dev-site-project-status-donut-2026-06-19.md`](./dev-site-project-status-donut-2026-06-19.md)
  — a status-graph widget. A consumer of the same idea, not the idea.

The new angle: a **reusable "emit-as-HTML-artifact" habit/seam** for agent deliverables, so a
session can hand the owner a scannable HTML review surface instead of (or alongside) a Markdown
report. We already have the `.tsx` dev-site substrate (PR #1455 dashboard-refresh, 56 tsx
files), so this is **incremental, not a new system** — the strongest argument for it.

## Candidate slices (highest → lowest leverage, none approved)

1. **Workflow-review board** — session history, open PRs, idea backlog, router Q-blocks, recon
   status as one scannable HTML surface, so the owner reviews agent activity at a glance instead
   of grepping `.sessions/` + `docs/`. Highest leverage: targets the owner's actual review
   bottleneck. Overlaps the live developer dashboard — likely a *phase* of it, not a rival.
2. **Per-session "what I did" HTML summary** as a PR artifact — color-coded decisions / risks /
   self-initiated promotions (`⚑`) so a session can be validated at a glance. Pairs naturally
   with the born-red→green session-card flow.
3. **Plan / spec docs as HTML artifacts** — for `docs/planning/` plans the owner signs off on,
   render the decision forks visually (cf.
   [`askuserquestion-preview-for-design-forks-2026-06-24.md`](./askuserquestion-preview-for-design-forks-2026-06-24.md),
   same "let the owner pick what *looks* right" instinct).
4. Bot-facing output (Discord embeds) — **low fit**; Discord already has its own rich-render
   layer and this is about *human review of agent work*, not bot output. Listed to scope it out.

## Open questions before this becomes a plan

- Is slice 1 just the next phase of the existing developer-dashboard plan rather than a separate
  effort? (Probably — route there first.)
- Where does an agent-emitted HTML artifact *live* and get served — committed to the dev site,
  or a transient artifact attached to the PR? Affects whether this is plumbing or just a habit.
- Worth a small experiment (one real session log rendered as HTML) to sanity-check the
  unquantified premise before investing.

## Lifecycle

Capture only. Natural next step during grooming: fold slice 1 into the developer-dashboard
plan as a "render agent-workflow state" phase, or open a router DISCUSS block if the owner wants
the broader "emit-as-HTML" habit treated as policy.
