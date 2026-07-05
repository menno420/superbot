# 2026-07-05 — CI-setup redesign (best-possible CI: current bot + fresh repo)

> **Status:** `in-progress` — born-red gate (Q-0133). Held until the design + migration plan
> + fresh-repo divergence analysis land and the deliverable is verified.

## What this session is doing (born-red declaration)

The dedicated **CI-setup redesign** session the brief (#1736) primed. Owner-directed, ultracode.
Goal: the **best-possible CI** for (a) the current bot and (b) the future fresh-rebuild repo —
and explicitly **verify whether the fresh repo's CI should differ** from the current bot's, since
the new repo's code structure is ours to shape.

Method (per the brief + owner's extra ask): build the authoritative **what-runs-where matrix**,
classify every check (merge-gating / advisory / routine / dev-only), design the **target-state CI**
(≈one deterministic required context; fix the CodeQL race + dropped-synchronize root cause; retire
compensators), and produce the **fresh-repo CI design + convergence/divergence analysis**. Many
cross-checking agents (ultracode workflow). Destructive executable-config changes are **owner-gated
→ proposed**; safe additive/reversible wins ship now.

Early correction already banked: **the repo is PUBLIC → Actions minutes are free/unlimited**, so
"cost" = wall-clock latency + PR-UI clutter + merge-race hazards, not billed minutes.
