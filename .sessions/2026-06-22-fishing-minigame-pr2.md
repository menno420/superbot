# 2026-06-22 — Fishing minigame PR2: the trophy reel-fight (completing the hybrid)

> **Status:** `complete` — trophy reel-fight shipped & verified (full CI mirror green, 11,573 tests).
> Owner-directed implementation (Q-0175, continues #1298). PR #1299 → auto-merges on green (Q-0191).

## Arc (what I'm about to do)

PR1 (#1298) shipped the core `cast → wait → BITE → reel`: ordinary fish land on the first reel.
The owner's **hybrid** decision (2026-06-22) was: *single reel for ordinary fish, a reel-fight for
trophies*. This PR2 adds the **reel-fight**:

- Hooking a **trophy** (top third of your unlocked band — `minigame.is_trophy`) no longer commits
  immediately; it starts a short **reel-fight**: 2–4 more timed reel taps (scaling with fish size),
  each its own generous presence-check window, each able to let the fish **snap free** with a small
  escape chance. Land every tap → the trophy is committed; miss a window or get snapped → it gets
  away (owner: missed reel = no catch).
- Kept fair: fight windows stay the *full* generous window (NOT the sim's tighter `w*0.8` — over
  Discord a tighter window punishes latency, not skill; trophies are harder via more taps + escape).
- Concurrency: each armed window carries a `_round_id` staleness token so a previous round's
  background task (still sleeping out its window) exits on wake instead of false-failing the fish.
- `escape_resist` is already a parameter on the escape helpers (defaults 0) so the PR3 **rod ladder**
  can buy it down without touching this code.

Pure helpers (`reel_fight_taps`, `fight_escape_chance`, `roll_escape`) added to
`utils/fishing/minigame.py` (testable, no Discord). No workflow/DB change — the fight just gates
when `commit_catch` runs. **Deferred to PR3+:** rod ladder, energy pacing + sell-value rebalance,
boat/deepwater.

## Shipped (PR #1299)

- **Pure fight helpers** in `utils/fishing/minigame.py`: `reel_fight_taps(species)` (2–4, scales with
  size), `fight_escape_chance(species, escape_resist=0)` + `roll_escape(...)`, and the `FIGHT_*`
  constants. `escape_resist` defaults 0 now so PR3's rod ladder turns it without touching this code.
- **The reel-fight in `views/fishing/cast_view.py`** — refactored to a small phase machine
  (`bite`/`fight`). Hooking a trophy (`is_trophy`) → `_on_hooked` starts the fight instead of
  committing; `_run_fight_round` arms each tap (suspense beat + a generous full window + a tension
  bar `▰▰▱▱`); `_on_fight_tap` resolves it (snap-free roll → got away, else advance / land). The
  catch commits only after the final tap. Generalised the single-window arm into `_arm()` with a
  `_round_id` staleness token so a superseded round's sleeping task exits instead of false-failing.
- **Tests** — `test_fishing_minigame.py` +5 (taps scaling, escape-chance/resist, roll determinism);
  `test_fishing_cast_view.py` rewritten to 12 (ordinary-commits-first-reel, trophy-starts-fight,
  final-tap-commits, non-final-advances, snap-loses, between-round-mash-ignored, + the prior bite
  cases). Full CI mirror green.
- Docs: games folio fishing entry updated (PR2 reel-fight shipped, rod `escape_resist` knob noted).
- No workflow/DB/dashboard change (the `!fish` help text is unchanged; the fight only gates *when*
  `commit_catch` runs).

## Session enders

- **💡 Session idea (Q-0089):** *A "the big one got away" follow-up hook.* When a trophy snaps free
  in the fight, record a lightweight "one that got away" marker for that user+species so the next
  cast can occasionally offer a **rematch / grudge bite** ("the trout that broke your line is back…")
  — turning a frustrating loss into a motivating re-hook. Cheap (reuses the catch-log seam), and it's
  the design doc's "a big one got away → bait the next cast" soft-fail idea made concrete. Logged
  here; a fuller capture belongs with the rod-ladder PR where escape stakes rise.
- **♻ Grooming (Q-0015):** advanced the fishing minigame down its lifecycle — the owner's "hybrid"
  mechanic decision is now fully built (PR1 ordinary reel + PR2 trophy fight). Games folio + this log
  reflect it; the remaining deferred slices (rod ladder / energy / boat) are named for PR3+.
- **⟲ Previous-session review:** PR1 (#1298) set this up well — splitting `roll_cast`/`commit_catch`
  in PR1 meant PR2 needed *zero* workflow/DB change (the fight just delays the existing commit), and
  the background-task + window machinery generalised cleanly. **What PR1 could have anticipated:** it
  hard-committed on the first successful reel, so PR2 had to refactor the reel button into a phase
  machine; had PR1 routed the success path through a single `_land_or_continue` seam from the start,
  PR2 would've been purely additive. Minor — the refactor was small and well-tested. **System note:**
  when a feature is known to ship in slices, the first slice benefits from leaving the obvious
  extension seam (here: "what happens after a successful reel") as a named method, not inline.
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓ (in the pre-PR suite), games folio updated, no
  new orphan docs, no dashboard regen needed. Ledger auto-updates on merge. Nothing left only in chat.

## ⚑ Self-initiated: none — owner-directed implementation ("Continue from where you left off" → the
   next planned slice, PR2 trophy reel-fight).
