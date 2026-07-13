# 2026-07-13 — Websites fleet-data-plane design (owner ask)

> **Status:** `in-progress`
> **Branch:** `claude/multi-repo-orientation-review-p5ztfi` (restarted from main; prior PRs #2064/#2065 merged)
> **📊 Model:** Claude 5 family (Fable)
> **Venue:** owner-live chat, remote container (hub repo)

## What is about to happen

Owner ask (exploratory → design): find out how all the website services get their live
data today; assess whether it can be centralized; design the failsafe the owner described
— a correctly-named file misplaced by an agent (wrong dir/repo) is still found, and
recency decides which copy is authoritative — improved per Q-0254 (reason the fragment
forward: commit-time over hand-written stamps, canonical-path precedence with drift
warnings instead of silent masking, manifest derived from kit config + fm roster).

Research: one read-only survey agent over menno420/websites (data-access map, bake
pipeline, #250 classifier) + hub-side checks (substrate.config.json heartbeat manifest,
dashboard export path). Deliverable: `docs/planning/websites-fleet-data-plane-2026-07-13.md`
(design brief, routable to the websites lane as a manager ORDER) + chat answer.
Execution stays websites-lane — no cross-repo writes from here.
