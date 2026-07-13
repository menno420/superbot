# 2026-07-13 — Control-plane live centralization review (owner ask)

> **Status:** `in-progress`
> **Branch:** `claude/control-plane-live-review` (restarted from main)
> **📊 Model:** Opus 4.8
> **Venue:** owner-live chat, remote container (hub repo)

## What is about to happen

Owner refreshed all seats' ender + boot prompts and still senses the website isn't fully
centralized; asked for a thorough review of the live control-plane
(https://control-plane-production-abb0.up.railway.app/). I crawled the live site
(homepage + /fleet /freshness /projects /prompts /queue /directory via WebFetch) and
cross-referenced against the architecture I mapped for the #2066 data-plane design.

Headline finding: the same fleet is rendered as **6 different sizes** across pages
(homepage 4 · prompts 9 · projects 11 · directory 15 · fleet 18 · freshness 18) — the
non-centralization made visible. Deliverable:
`docs/planning/control-plane-centralization-review-2026-07-13.md` (live gap-analysis +
prioritized fixes; complements the #2066 design) + chat answer. Execution routes to the
websites lane.
