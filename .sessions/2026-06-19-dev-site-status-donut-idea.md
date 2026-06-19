# 2026-06-19 — Capture owner's dev-site project-status-donut idea (+ mockup)

> **Status:** `complete`

Owner returned mid-session to record a new idea so it wasn't forgotten: a modern **multi-segment status
donut** for the **dev site** (build / planned / ideas / bugs at a glance), plus a **direction** —
refocus the dev site on *projects*, not the bot (the public site now owns the bot). Captured it
plan-ready and rendered a modern mockup so we can align on the look before building.

## What was done
- **Idea doc** `ideas/dev-site-project-status-donut-2026-06-19.md` (plan-ready): chart spec; the **data
  model** — the **doc-badge lifecycle** (`ideas`→`plan`→`historical`) *is* the state machine, already
  parsed by `export_dashboard_data.py`, + an open-bug count; the **one design decision** (what
  "built/completion %" measures, a/b/c); the build path (a `dashboard.json` key → inline-SVG donut, no
  `static/` dir); and the dev-site-refocus direction. Indexed in `ideas/README.md`.
- **Mockup** `ideas/assets/dev-site-status-donut-mockup-2026-06-19.png` — modern dark-theme donut (PIL,
  supersampled), sent to the owner to react to the look.

## Decisions recorded
None new — capture only (idea is unbuilt). The dev-site-refocus is a **stated direction** captured in
the idea doc, flagged for owner confirmation (not yet a router Q). No CLAUDE.md / config edits.

## Left open / next session
Build on owner greenlight (or dispatch can pick it up — it's plan-ready). Confirm: completion
definition (a/b/c) · whole-project vs per-sector small-multiples · refocus scope.

## 💡 Session idea (Q-0089)
The **doc-badge lifecycle as a live project-state API** — `ideas`→`plan`→`historical` counts already
form a self-maintaining pipeline metric; surfacing it (a donut now, a burn-up trend later) turns the
grooming discipline into a *visible* project state. The status donut is its first consumer.

## ⟲ Previous-session review (Q-0102)
The just-merged botsite-dark-launch slice (#1147) closed cleanly — deploy verified end-to-end, Codex's
two (already-fixed) notes resolved. It surfaced the exact gap this idea begins to fill: "shipped to
`main`" vs "live + *visible*" needs a surface. The dev-site status donut is that surface for the
project's own state — the same make-the-invisible-visible thread the whole day has been pulling on.
