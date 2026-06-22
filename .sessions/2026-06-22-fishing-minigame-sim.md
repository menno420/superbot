# 2026-06-22 — Fishing minigame: design simulation + analysis

> **Status:** `complete` — sim + analysis shipped & verified (CI-clean). Owner-directed research/
> design session (no runtime `disbot/` code). PR #1296 → auto-merges on green (Q-0191).

## Arc (what I'm about to do)

Owner wants the fishing subsystem (today: prefix-only deterministic roll) to become an
**interactive minigame** — leaning toward a real "cast line → wait… → bite! → reel in" loop,
but he's **not sure that's the best option** and is "still finalizing the idea." He explicitly
asked me to **create and run a simulation** to find: the most fun way to play, the right
bite-timing, how long the reaction window should be, the best rod-upgrade system, and how the
**boat / deepwater fish** (Phase 2 of the plan) should differ from shoreline fishing. He
welcomes other ideas.

This session (research + tooling, fully reversible, no runtime code):
1. **Build `tools/sim/fishing_minigame_sim.py`** — a stdlib-only Monte-Carlo sim that models the
   *full Discord latency chain* (message-edit push → human reaction → button round-trip) so the
   reaction-window numbers are realistic, not twitch-game fantasy. Scores candidate mechanics on
   fun/fairness/reward proxies across a player population (varied reaction time + network latency).
2. **Run it**, sweep parameters (bite-time distribution, reaction-window length, rod tiers,
   shoreline vs deepwater), and capture the output.
3. **Write `docs/planning/fishing-minigame-design-2026-06-22.md`** — findings, recommended numbers,
   the rod-upgrade ladder, the boat/deepwater design, and alternative mechanic ideas. Route the
   genuinely owner-level direction choices to him.

Grounded in: `docs/planning/fishing-open-world-expansion-plan-2026-06-18.md` (Q-0175 vision),
current `fishing_workflow` / `utils/fishing/` (21 fish, 7 levels, fish now sellable+cookable per
#1289).

## Shipped (PR #1296)

- **`tools/sim/fishing_minigame_sim.py`** — stdlib-only Monte-Carlo sim (3k players × 40 casts).
  Models the **full Discord latency chain** (`L_down + R + L_up` vs window `W`) — the insight that
  a reaction window over Discord is a *presence check*, not a reflex test, and sub-second windows
  are unwinnable on lag. Scores 3 mechanics (`roll`/`bite_reel`/`tension`) on catch-rate, *unfair*
  (latency) vs *fair* (attention) failure, agency, lag-unfairness, frustration, pacing. Sweeps the
  reaction window, bite timing, a 5-tier rod ladder, and shore-vs-deepwater. Provenance + verifiable
  + disposable header per Q-0105.
- **`docs/planning/fishing-minigame-design-2026-06-22.md`** — the sim-backed design: recommends
  `cast → wait → BITE → reel` (owner's instinct, confirmed) with a ~2.5 s window, randomised 3–6 s
  bite + fake-out, a 4-knob rod ladder (window/speed/rarity-pull/escape-resist, none gating basic
  success), and deepwater-as-a-choice (worth it only with a good rod). Multi-action panel design +
  starting numbers table + 5 open owner-call questions. Linked from the Q-0175 expansion plan.
- Answered the Q-0175 "catch mechanic" open question with data; added the cross-link in the
  expansion plan.

## Session enders

- **💡 Session idea (Q-0089):** `sim-assumption-telemetry-loop-2026-06-22.md` — ship a one-line
  telemetry counter alongside any sim-designed feature, logging the *exact* quantity the sim assumed
  (here: the bite→click round trip), so a later session can replay live data through the sim and
  validate/correct its load-bearing constants. Makes a design sim self-verifying (the ground-truth
  path the Q-0105 "unverified" header asks for). Indexed in `docs/ideas/README.md`.
- **♻ Grooming (Q-0015):** moved the Q-0175 fishing "catch mechanic" open question down its
  lifecycle — from an unanswered design question in the expansion plan into a concrete, sim-backed
  `docs/planning/` recommendation. The fishing self-build idea advanced one real step.
- **⟲ Previous-session review (Q-0102):** the predecessor fishing-arc session
  (`2026-06-22-mining-fish-cooking.md`, #1289) did a clean, well-scoped job making fish *tangible*
  (sellable + cookable) and honestly flagged the balance caveat that "fishing is currently unpaced,
  so fish sell value is kept low." That flag is exactly right — but it was left as a TODO without a
  *mechanism* to ever resolve it. **What it could have done better:** named *what* would make fishing
  paced (a minigame? energy? cooldown?) so the low-value caveat had a path to lifting, instead of an
  open-ended "documented." This session closes that gap (the minigame is the pacing mechanism; §6 Q4
  of the design doc routes the energy/cooldown decision to the owner). **System improvement
  surfaced:** balance caveats deferred "for later" should carry a pointer to the idea/plan that will
  resolve them, or they quietly become permanent — the sim-telemetry idea above is the durable form
  of that instinct (don't leave an assumption un-falsifiable).
- **🧾 Doc audit (Q-0104):** `check_current_state_ledger --strict` ✓, `check_docs --strict` ✓
  (new plan linked from the expansion plan, no orphans), `check_quality --check-only` ✓. No runtime
  code → no current-state ledger entry needed beyond the auto on-merge. Nothing left only in chat.

## ⚑ Self-initiated: none — this session was owner-directed (the owner asked for the simulation).
   The new idea (above) is *captured*, not promoted-to-implementation, so no build flag applies.
