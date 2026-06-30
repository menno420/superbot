# 2026-06-30 — Fishing rod-recipe browser (live progress toward each tier)

> **Status:** `complete`

**Run type:** manual · user-directed (Claude Sonnet 5, autonomous pick — "find something to do, go big")

## What this run did
S1's live queue (`docs/current-state/S1-bot.md` § Fishing follow-ups) named two turn-key, offline,
self-mergeable "next offline successor" picks on the rod-craft seam shipped in #1515/#1508: a new
rare-material drop, or the **rod-ladder recipe browser UI**. Picked the browser — the lower-risk,
clearly-scoped option (no new balance numbers to invent) that closes a real UX gap: the rod shop
advertised a recipe's bare requirement ("10 fish, size ≤ 6") but never showed the player's *current*
eligible-fish count toward it.

### What shipped
- **`📋 Recipes` panel** — a new button on `RodShopView` + a standalone `!rodrecipes` (aliases
  `!rodrecipe`/`!rrecipes`) command, opening `RodRecipeBrowserView`
  (`views/fishing/rod_recipe_browser.py`). Lists every craftable tier (1–`MAX_TIER`) with:
  - ✅ already-wielded tiers,
  - the immediate **▶** next tier with live `"{eligible}/{required} eligible fish"` progress + a
    "ready to craft!" flag once met,
  - 🔒 further-out tiers shown for planning only (only the next tier is actually craftable — mirrors
    `craft_rod`'s "always crafts the rod directly above the one owned" behavior).
  - A **Craft next** button (re-gated off at the top tier) and a **Back to rod shop** button.
- **`services/fishing_workflow.py`** — extracted `_eligible_fish()` out of the existing
  `_plan_fish_spend` planner (used by bait/charm/rod crafting) and added a public
  `eligible_fish_total()` for the progress readout. Behavior-preserving refactor — `_plan_fish_spend`'s
  existing tests pass unchanged.
- The rod shop's existing "or craft from N fish" line now points at the new panel
  ("📋 Recipes shows your live progress") for discoverability.
- Regenerated `dashboard/data/dashboard.json` + `botsite/data/site.json` + `botsite/site/data.js` — the
  new `!rodrecipes` command tripped the generated-artifact freshness guard
  (`tests/unit/scripts/test_check_generated_artifacts_fresh.py`), caught by CI on the first push.

### Tests / checks
- +18 tests: `services/eligible_fish_total` (4 cases), `views/rod_recipe_browser` (embed assembly +
  view craft/back behavior, 9 cases), a new `RodShopView.recipes_btn` test.
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors (only pre-existing tracked
  warnings, none in touched files).
- `python3.10 scripts/check_quality.py --full` — green after the dashboard/site re-export (the only
  failure surfaced was the artifact-freshness drift above, not a code defect).

## 💡 Session idea
**A generic "recipe progress" embed helper for the fish→X craft family.** Bait, charm, and now rod
crafting all share the exact same "{eligible}/{required} eligible fish (size ≤ N)" progress shape (the
new `_recipe_line` in `rod_recipe_browser.py` is structurally identical to what a bait/charm recipe
browser would need). If a future session builds a recipe browser for bait or charms too, factor the
embed-line builder into a shared `utils/fishing/recipe_display.py` rather than copy-pasting
`rod_recipe_browser._recipe_line` a third time — today there's only one consumer, so premature to
extract, but worth flagging before a second copy lands. Dedup-checked `docs/ideas/` — not present.

## ⟲ Previous-session review
The previous run (#1584, Diagnostics pagination + metrics reconcile) was a clean completion-first
deepening slice that closed Diagnostics' entire offline punch-list in one PR — good scoping, matched
the standing S1 dispatch lane exactly. One thing this run's experience suggests as a system
improvement: **the generated-artifact freshness guard (`check_generated_artifacts_fresh.py`) only
fires in the full `pytest tests/` run, not in the fast targeted-test loop a session naturally reaches
for first** (`scripts/context_map.py`'s "Suggested checks after editing" for a cog/view file lists the
file-scoped test + `check_architecture` + `check_quality.py --full`, but a session that runs the
targeted tests + architecture check and feels "done" before the full suite can still push a PR that
fails CI on a stale dashboard artifact, exactly as happened here). Worth considering: have
`scripts/check_quality.py --check-only` (the fast pre-push pass) also run the artifact-freshness check
specifically when a new command/cog is added — it's cheap (no DB, pure source scan) and would catch
this class of drift before the push instead of after, on the first CI round-trip.

## 📤 Run report
- **Run type:** manual · user-directed
- **PR:** #1585 (Fishing — rod-recipe browser with live craft progress) — self-merge on green.
- **⚑ Self-initiated:** yes — autonomous pick from S1's own published `▶ Next startable` queue
  (`docs/current-state/S1-bot.md`), not a dispatched work order. Promoted directly from the live queue
  to a build in this session (no separate idea→plan stage needed; the item was already turn-key per
  the queue's own offline-fit tag).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (no migration, no data step; merge auto-deploys).
- **Bugs:** none opened; none fixed. One CI miss caught and fixed in-session (stale dashboard/site
  artifacts after adding `!rodrecipes` — regenerated via `scripts/export_dashboard_data.py` before
  flipping this card to complete).

## Documentation audit
- `docs/current-state/S1-bot.md` — added a Recently-shipped entry (PR #1585) and updated the Fishing
  follow-ups bullet to mark the recipe-browser UI done, leaving the rare-material-drop variant as the
  sole remaining "next offline successor."
- No new binding doc, ADR, or subsystem folio needed — this is an additive UI feature on an existing,
  already-documented seam (`docs/subsystems/games.md` / the fishing minigame design doc already cover
  the rod-craft mechanic; no contract changed).
- Claim file `docs/owner/claims/claude__fishing-rod-recipe-browser.md` removed at session close.
