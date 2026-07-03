# Idea — the unified layout-success simulator (instruction-driven, deterministic + AI)

> **Status:** `ideas` — capture only. **Subsystem:** none (rebuild UX-optimization tooling).
> **Provenance:** rebuild-planning session 2026-07-03 (PR #1687, Q-0235). Builds on the
> simulation-driven-design standing rule (2026-07-02).

## The idea

One simulator that scores any generated hub/menu layout by **task success rate**: given only a
natural instruction ("create roles", "play the mining game", "set up logging"), does a **user
model** navigate to the correct node? Two user models:

- **Deterministic** — a reproducible heuristic user (semantic label-match + click model). For
  CI/regression: a layout change that lowers success rate reddens the build.
- **AI-driven** — an LLM acting as a *naive* user, shown the menu + the instruction, asked what it
  clicks. Catches **label ambiguity** a heuristic can't (does it look for roles under "Community"
  or "Server"?).

Metrics per (instruction × layout): **success** (reached the right node?), **path length**
(clicks), **wrong turns**. Success rate is the quantitative proxy for **"self-explanatory to use"**
(the Q-0234 oracle) — measurable *before* the live co-test.

## Why now — centralize the 5 bespoke sims

Five separate UX-layout sims already exist — `claim_layout_sim`, `help_menu_grouping_sim`,
`role_menu_layout_sim`, `settings_order_sim`, `setup_wizard_sim` — each with its own model. That is
the rubric's **fragmentation** class in the tooling itself. Centralizing quickly is what lets **one**
sim **define the proper settings/layout for *everything*** (arrangement, grouping, defaults, order)
over the manifest, instead of each surface being tuned in isolation. Because the hub is generated,
generating candidate layouts to test = permuting the manifest — *the manifest is the search space,
the simulator is the search* (the standing rule made real).

## The pipeline — sim narrows, live co-test signs off

1. **Sim** scores candidate layouts/settings by success rate → picks the best (cheap, at scale).
2. **Live bot co-test** in the test server is the **final review** — the human confirms *works ·
   logical · self-explanatory* on the sim's winner (Q-0234). Sim replaces guessing; the live test
   replaces trusting the sim blindly.

Bonus reuse: the **instruction corpus** ("create roles" → target node) tests **both** menu
discoverability *and* the NL router (invocation rung 3) — one test set, two consumers.

## Routing

Belongs to the rebuild's UX-optimization tooling (Gate-0-adjacent; runs during Stage 2 to choose
hub arrangement, and at Gate V as part of the verification fleet). Detail on how it fits:
[`../planning/rebuild-hub-navigation-presets-2026-07-03.md`](../planning/rebuild-hub-navigation-presets-2026-07-03.md)
(arrangement) · [`../planning/rebuild-critical-review-rubric-2026-07-03.md`](../planning/rebuild-critical-review-rubric-2026-07-03.md)
(class 8 oracle) · `simulation-driven-design-2026-07-02.md` (the standing rule). Not current-repo
work, though the 5 existing sims are the prior art to fold in.
