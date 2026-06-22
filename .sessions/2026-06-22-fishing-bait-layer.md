# 2026-06-22 — Fishing Bait economy layer

> **Status:** `complete`

**Run type:** routine · dispatch

## Arc

Empty-fire dispatch run (no work order). Oriented (synced live `main`, read the
working agreement → collaboration model → current-state → newest sessions →
bug-book), confirmed the open bugs are gated/owner (BUG-0009 data-gated, BUG-0011
needs a VPS repro, BUG-0019 #1 owner design fork), and picked a clean, ungated,
fully-buildable product lane: the **Bait** layer for the fishing minigame — the
fishing design doc's named "second economy knob" follow-up (band-queue D1 /
[`fishing-minigame-design`](../docs/planning/fishing-minigame-design-2026-06-22.md)
§4), preferred over a marginal tooling guard per the band-#1320 pass's empty-fire
steer.

## Shipped (PR #1329)

Bait is an optional, coin-bought consumable that loads N charges and, while held,
spends one per cast and multiplies the rod's `rarity_pull` to bias the catch
toward bigger fish within your unlocked band (never a new band — that stays the
fishing-level axis). A coin sink (fish became sellable/cookable in #1289) + a
pre-cast decision beside the rod. Built house-style, mirroring the existing
fishing seams:

- `utils/fishing/bait.py` — pure bait catalog (Worm / Glow Grub / Shimmer Lure),
  like `rods.py`.
- `disbot/migrations/091_fishing_bait.sql` + `utils/db/games/fishing_bait.py` —
  per-(user,guild) active-bait loadout (key + charges), conn-aware CRUD, wired
  into `utils/db/__init__`.
- `services/fishing_workflow.py` — `buy_bait` audited coin sink (mirrors
  `buy_rod`, stacks same-bait / replaces different-bait), `get_active_bait`
  resolver, and per-cast consume in `begin_cast` (compounds rarity, clears the
  pack when the last charge is spent); `roll_cast` gained a `rarity_pull`
  override.
- `views/fishing/bait_shop.py` — 🪱 Bait shop panel (BaseView + a buy select),
  plus a Bait button on `FishingMenuView` and the cast panel's bait note.
- `cogs/fishing_cog.py` — `!bait` (aliases `baitshop`/`buybait`).
- Tests: `tests/unit/utils/test_fishing_bait.py`,
  `tests/unit/db/test_fishing_bait_db.py`,
  `tests/unit/services/test_fishing_workflow_bait.py` (catalog invariants, SQL
  shapes, purchase coin-sink incl. stack/replace/insufficient/unknown, per-cast
  consume + rarity compounding + clear-on-last-charge). Updated the two existing
  `begin_cast` tests for the new bait read.
- Regenerated the committed generated artifacts (`site.json` / `data.js` /
  `dashboard.json`) for the new `!bait` command (373 commands).

CI mirror green: `check_quality.py --full` (11757 passed after the artifact
regen) + `check_architecture.py --mode strict` 0 errors.

## Decisions made alone

- **Bait affects rarity only** (multiplies the rod's `rarity_pull`), not bite
  speed — the contained, fully-offline-testable half. The "faster bites" knob is
  a clean future addition on the same `CastStart`/cast-view seam (noted in the
  plan §4 + the bait module docstring). Owner can ratify or ask for the speed
  half later.
- **Buying stacks same-bait charges, replaces a different bait** (no refund of
  the dropped pack) — the simplest predictable contract; the purchase message
  says which happened.
- One **active bait at a time** (not a bait inventory) — matches the rod's
  single-equipped model and keeps the pre-cast decision a single clear choice.

## Flagged for maintainer

- Unverified half: the live Discord cast/shop UX wasn't exercised (no live bot);
  the logic + the audited coin-sink seam are unit-covered, but a Q-0086-style
  live walk of `!bait` → load → cast would confirm the panel + the cast-panel
  bait note read well in-channel.
- Bait prices / rarity-pull values + charge counts are tuning constants
  (`utils/fishing/bait.py`) — first-pass numbers, tune against live play like the
  rod ladder.

## Context delta

- **Needed but not pointed to:** that **adding any prefix/slash command stales 4
  committed generated-artifact tests** (`site.json` / `data.js` / `dashboard.json`
  via `test_check_generated_artifacts_fresh` + `test_committed_site_json_matches_a_fresh_build`)
  — the fix is `python3.10 scripts/export_dashboard_data.py`. Not surfaced by the
  fishing folio or the cog context map; only learned at full-suite time. (Captured
  in the friction line below.)
- **Pointed to but didn't need:** the broad orientation route (architecture /
  ownership / mutation rules) was light-touch here — the fishing subsystem's own
  files (`rods.py` / `buy_rod` / `fishing_energy`) were the real template; reading
  one sibling seam end-to-end beat the binding contracts for a same-pattern add.
- **Discovered by hand:** the rod ladder is the canonical "audited coin-sink +
  per-(user,guild) tier table + pure catalog" pattern; bait is its consumable
  twin. Worth a one-line folio pointer (groomed below).

## 💡 Session idea (Q-0089)

**Bait crafting from caught fish** — close the fishing economy loop: let the
cook/campfire loop (#1289) also turn small/common caught fish into bait, so the
catch → cook → bait → bigger-catch cycle feeds itself instead of bait being a
pure coin sink. Genuine product depth on top of today's layer; captured at
[`ideas/fishing-bait-crafting-2026-06-22.md`](../docs/ideas/fishing-bait-crafting-2026-06-22.md).

## ⟲ Previous-session review (Q-0102)

The previous logged sessions (the band-#1320 reconciliation + the Starboard PR2
polish) were clean; the band-#1320 pass's honest "empty-fire should prefer a
substantial lane over a marginal guard" steer directly shaped this run's pick
(bait, a real product vertical, over the staleness-classifier tooling guard) —
evidence the pass's §4 guidance is doing its job. **System improvement surfaced:**
the generated-artifact staleness on a new command (the friction below) is a
recurring class every command-adding session re-learns at full-suite time;
cheapest durable help is a folio/pre-pr pointer, done below.

## 🛠 Friction → guard

- **Friction:** adding the `!bait` command silently staled 4 committed
  generated-artifact tests; only caught after a 3-min full-suite run.
- **Guard shipped:** the hard tests already *enforce* it (they fail on stale
  artifacts — enforcing, not exhort), so the durable guard exists. Added a journal
  Rule candidate + this delta so the *recovery* (`scripts/export_dashboard_data.py`)
  is one grep away next time. A PostToolUse/pre-pr hook nudge ("you added a
  command — regen artifacts") would be cheaper still but is **owner-gated**
  (hook/settings) — proposing, not shipping.

## 📤 Run report

- **Did:** shipped the fishing Bait layer (the design plan's named second economy knob) end-to-end · **Outcome:** shipped
- **Shipped:** #1329 — fishing Bait: coin-bought rarity consumable (catalog + migration 091 + audited `buy_bait` + per-cast consume + 🪱 shop panel + `!bait`), tests + regenerated artifacts; CI green
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none (bait's rarity-only scope + stack/replace + single-active-bait are reversible defaults, ratify-if-you-disagree)
- **⚑ Owner manual steps:** none (a merge auto-deploys; no data seed — bait knobs live in code, the table defaults to bait-less)
- **⚑ Self-initiated:** transparency note — the *implementation* was an autonomous empty-fire pick of band-queue lane **D1** / design-plan §4 (an existing plan, not a fresh idea→plan promotion), so no new plan was created; flagging it so the unprompted build is reviewable. The Q-0089 **bait-crafting** idea was *captured* (not built).
- **↪ Next:** current-state ▶ Next action sharpened below — fishing follow-ups (bait *speed* knob on the same seam · the #1289 sell-value upward re-tune now that pacing+bait landed · boat/deepwater), then the other S1 ▶ lanes (Project Moon runtime PR1 / botsite React PR2).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (1 auto-merging on green: #1329) |
| CI-red rounds | 1 (full-suite: generated-artifact staleness from the new command → regen → green) |
| Repo-rule trips | 0 (arch strict 0 errors) |
| New ideas contributed | 1 (bait crafting) |
| Ideas groomed | 1 (marked design-plan §4 bait SHIPPED; folio-pointer delta) |
