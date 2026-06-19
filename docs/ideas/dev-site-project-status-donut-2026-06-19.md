# Dev-site project-status donut + refocus the dev site on *projects*, not the bot

> **Status:** `ideas` — capture only (not a plan, not approval). **Owner-directed 2026-06-19** — the
> maintainer came back mid-session specifically to record this so it wasn't forgotten. Source +
> binding contracts + `current-state.md` win over this file.
> **Subsystem:** none — this is a dev-site / workflow surface, not a bot feature.

## The ask (owner intent)
A status graph on the **developer site** (`dashboard/`) showing **plans & execution at a glance** —
modeled on a multi-segment donut (reference image: a "Project Completion and Status Progress
Dashboard"), but **more modern-looking**. It shows *several states at once*, e.g.
`build 68% / planned 20% / ideas 10% / bugs 2%`. Mockup rendered this session:
[`assets/dev-site-status-donut-mockup-2026-06-19.png`](assets/dev-site-status-donut-mockup-2026-06-19.png).

**Paired direction:** the dev site should **refocus on the _projects_, not the bot.** Now that the
public bot-site ships the marketing/bot surface, the two sites overlap — so the goal is to make the
**old dashboard a developer-only site about the work** (plans, execution, progress, what's shipping)
and let the public site own "here's the bot." The status donut is the first concrete beat of that
refocus.

## Why it's a strong fit — the data already exists, and the *badge is the status field*
The donut's segments map directly onto the **doc-badge lifecycle** the grooming discipline already
maintains (`docs/ideas/README.md` §5): an item is badged `ideas` → re-badged `plan` when structured →
re-badged `historical` when shipped. **That re-badging _is_ the state machine** — so a pure
badge-count over the repo gives a live, self-maintaining pipeline breakdown, parsed today by
`scripts/export_dashboard_data.py` (`_status_badge`).

| Segment | Source (proposed) | Live count (2026-06-19, by **badge**) |
|---|---|---|
| **Ideas** (backlog) | badge `ideas` | ~90 |
| **Planned** (structured) | badge `plan` | ~50 |
| **Built / shipped** | badge `historical` (re-badged on ship) | ~82 |
| **Bugs** (open) | open / partially-fixed `docs/health/bug-book.md` entries | 2 |

*(Raw file counts differ — 102 files in `docs/ideas/`, 86 in `docs/planning/` — because shipped
captures are re-badged `historical` but stay filed in place. Use the **badge**, not the folder, so the
chart reflects live state. This honest read also surfaces something useful: the idea backlog is large
relative to shipped — a real signal, not a vanity number.)*

## The one real design decision — what does "built / completion %" mean?
The three pipeline segments are clean badge counts. A **single completion ring** (the left donut in the
reference, a `43%`-style headline) needs a defined denominator to be honest:
- **(a)** `built / (ideas + planned + built)` — share of all tracked work that's shipped (~37% today).
- **(b)** `built / (planned + built)` — *execution* rate of structured work (~62% today).
- **(c)** a curated **roadmap phase %** (hand/rule-derived, like the reference's 43%).
Recommendation: ship **both rings** like the reference — one **completion ring** (option (b), the
truest "execution" number) **and** the multi-segment **pipeline donut** (ideas/planned/built/bugs as
badge counts). Owner confirms (b) vs (a) vs (c).

## Build path (plan-ready — where each piece plugs in)
1. **Data** — add a `project_status` block to **`dashboard.json`** in
   `scripts/export_dashboard_data.py` (**dev payload only**, never the public `site.json` whitelist):
   `{ideas, planned, built, bugs, completion_pct}` + each number's provenance. Reuses the existing
   badge parse + a small bug-book counter.
2. **Render** — a modern **inline-SVG donut** partial in a `dashboard/` Jinja template
   (`stroke-dasharray` ring segments + legend). Tailwind-CDN + inline only, **no `static/` dir** (the
   #970 deploy-crash gotcha; same constraint as the bot site) — so **no JS build, no chart library**.
3. **Place** — a dev-site "Project status" section/landing; the first beat of the dev-site refocus.
4. **Freshness** — `check_generated_artifacts_fresh.py` already guards `dashboard.json`; add the new
   key to its identifier set so it can't silently rot.

## Open questions for the owner
1. The completion definition above — **(a) / (b) / (c)**.
2. **Whole-project rollup, or per-sector small-multiples?** (S1–S5 — the sector map already exists; a
   row of small donuts per sector is richer.)
3. **Dev-site refocus scope** — full re-theme of `dashboard/` (nav + landing → "projects"), or add the
   status section first and evolve? (Refines the website-two-site-split plan §2 / §7.4.)

## Relations
- Refines [`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md)
  (dev-vs-public site roles) + [`../operations/website-split-next-steps-2026-06-19.md`](../operations/website-split-next-steps-2026-06-19.md).
- Data via `scripts/export_dashboard_data.py` (badge parse) + `docs/health/bug-book.md`.
- Generated-artifact freshness: `scripts/check_generated_artifacts_fresh.py`.
