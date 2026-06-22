# 2026-06-22 — Fishing minigame PR1: the interactive cast → wait → BITE → reel loop

> **Status:** `complete` — interactive cast→bite→reel minigame shipped & verified (CI mirror green).
> Owner-directed implementation (Q-0175 fishing minigame). PR #1298 → auto-merges on green (Q-0191).

## Arc (what I'm about to do)

The owner greenlit building the fishing minigame. This is **PR1 of a 2–3 PR plan** — the core
interactive loop, kept focused (runtime `disbot/` code → small PRs):

1. **Split the reward seam** — `fishing_workflow` currently rolls *and* writes in one call. Split
   into `roll_cast()` (read-only roll, so we know what's on the line at bite time) + `commit_catch()`
   (the audited atomic write), with `fish()` composing them (keeps existing `!fish`/tests green).
2. **Pure minigame domain** — `utils/fishing/minigame.py`: the sim-recommended tuning (randomised
   3–6 s bite + 1.5 s floor, ~2.5 s reaction window, trophy threshold) + pure resolve helpers, unit-
   testable, no Discord.
3. **The interactive view** — `views/fishing/cast_view.py` (`discord.ui.View`, mirrors
   `views/blackjack/solo_view.py`): cast → a managed background task arms the BITE after the delay →
   the **Reel** button resolves it. Miss (too slow) or premature reel = **the fish gets away** (owner
   decision: missed reel = no catch). On success, `commit_catch` writes it. Fake-out shake before the
   real bite. Active-cast guard (no double-casting) for soft pacing.
4. **Wire `!fish`** to launch the view; keep `fishlog`/`fishtop`.
5. **Tests** — pure minigame domain + the workflow split.

**Deferred to PR2/PR3** (kept out to stay focused): the trophy **reel-fight** (hybrid), the **rod
ladder** (new persistence + tackle UI), **energy** integration + **sell-value** rebalance, and the
**boat/deepwater** venue. Owner decisions already recorded: hybrid mechanic, fish-gets-away, soft
energy/cooldown, bait-later, shore-first.

## Shipped (PR #1298)

- **Split the reward seam** — `fishing_workflow` now has `roll_cast()` (read-only roll, returns a
  `Cast`) + `commit_catch()` (the audited atomic write: catch-log + inventory grant + xp on one
  txn, emit after commit). `fish()` composes them (legacy `!fish` path + all prior tests unchanged).
- **Pure minigame domain** — `utils/fishing/minigame.py`: sim-recommended tuning (2.5 s window,
  3–6 s bite + 1.5 s floor, 45% fake-out) + pure helpers (`roll_bite_delay`, `roll_fakeout`,
  `is_trophy`, `reel_is_in_time`). No Discord/clock → fully unit-tested.
- **The interactive view** — `views/fishing/cast_view.py` `FishingCastView` (mirrors
  `views/blackjack`): a managed `tasks.spawn` background task waits → optional fake-out nibble →
  arms the BITE (records the monotonic timestamp *before* the edit, so network latency counts
  against the generous window exactly as the sim models) → the single **Reel** button resolves.
  Reel early = spooked; in-window = `commit_catch`; too-late/ignored = the fish gets away. Author-
  restricted, disable-on-terminal, `active_casts` guard = soft pacing (no double-casting).
- **Wired `!fish`** to launch the view (rolls the cast, sends the embed+view, `view.start()`);
  `fishlog`/`fishtop` unchanged.
- **Tests** — `tests/unit/utils/test_fishing_minigame.py` (7), `tests/unit/views/test_fishing_cast_view.py`
  (5: premature/in-time/too-late/double-reel/not-your-line), + 3 new workflow-split tests. All green.
- **Checker plumbing** — fishing is a game-state view lane: added `views/fishing/` to
  `architecture_rules/canonical_helpers.yaml § base_view.exemptions` **and** the mirrored
  `_BASE_CLASS_ALLOWED_PATHS` in `check_consistency.py` (the durable fix vs. a per-class allowlist —
  covers future fishing game views; parity + conformance tests pass). Regenerated dashboard/site
  artifacts (the `!fish` help text changed).

## Session enders

- **💡 Session idea (Q-0089):** *Reaction-window auto-calibration from the bite→click telemetry.*
  This PR's window (2.5 s) is a sim assumption; PR-next should log the real bot-measured bite→click
  round trip (the `sim-assumption-telemetry-loop` idea from the design session) and, once enough
  data exists, surface a tiny report comparing the live latency distribution to the sim's `NET_*`
  constants — so the window is tuned from reality, not a guess. (Logged here; the parent idea file
  already exists, so no new file — this is the concrete fishing application of it.)
- **♻ Grooming (Q-0015):** advanced the fishing minigame idea down its lifecycle — design plan →
  shipped runtime PR1. The games folio + planning index now reflect "PR1 building/shipped, rest
  deferred".
- **⟲ Previous-session review:** the design session (#1296) did well to make the window's *fairness*
  the load-bearing finding and to route the feel-calls to the owner before any code — building this
  PR was frictionless because every number was already decided. **What it could have flagged:** the
  design doc's "panel actions" list (Cast/Bait/Tackle/Fishdex/Cook/Boat) didn't note that surfacing
  them needs the checker lane-exemption + dashboard re-export that this PR hit — a small "first
  runtime PR will trip these gates" heads-up would have saved a CI round. **System improvement:** a
  design→implementation handoff could carry a one-line "gates the build will hit" note (checker
  lanes, generated artifacts) so the first build PR isn't surprised. Minor; captured here.
- **🧾 Doc audit (Q-0104):** games folio + planning index updated; `check_docs --strict` ✓ (run in
  the pre-PR suite). New code modules need no doc links. Ledger auto-updates on merge.

## ⚑ Self-initiated: none — owner-directed implementation ("you can start implementing this").
