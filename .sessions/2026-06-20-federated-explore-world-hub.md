# 2026-06-20 — Federated Explore world hub (spine PR 1)

> **Status:** `complete` — PR #1156 (`needs-hermes-review`, auto-merge disabled; awaiting human review/merge).

> **Run type:** routine · dispatch

## What I did

Built **PR 1 of the federated Explore-hub spine plan**
(`docs/planning/explore-hub-federated-world-plan-2026-06-19.md` §4) — the ungated keystone slice
named as a ▶ Next startable in `current-state.md`. Scheduled (empty-order) dispatch fire; picked the
top ungated startable. Bugs-first checked first: the one OPEN bug (BUG-0009 newest-towers ordering)
is data-gated, so no bug jumped the queue.

## What shipped
- **`disbot/services/world_registry.py`** (NEW) — the world-registry seam. `WorldEntry`
  (`key/label/emoji/description/opener/order`) + idempotent `register_world_entry` (de-dup by key,
  `replace=` override), deterministic `get_world_entries` (sorted by `order, label`),
  `get_world_entry`, `clear_world_entries` (test reset). **Pure**: stores the opener as an opaque
  callable and imports no view module, so it never creates a `services → views` edge (the layer's
  hardest rule). This is the seam pets/survival dock into later (Q-0182).
- **`disbot/views/explore/world_hub.py`** + `__init__.py` (NEW) — `ExploreWorldHubView(HubView,
  SUBSYSTEM="games")` + `build_world_hub_embed()`, the top-level "town square". One button per
  registered world (registry-driven, mirrors `views/games/hub.py`): **Mine** swaps to the mining
  hub (degrades to the static hub embed if the live overview read fails / DM), **Fish** shows the
  fishing entry card pointing at `!fish`/`!fishlog`/`!fishtop` and stays on the hub. An opener-less
  entry renders a generic coming-soon card. `ensure_default_world_entries()` registers Mine + Fish
  idempotently.
- **`disbot/views/mining/main_panel.py`** (EDIT) — the mining `🗺️ Explore` button (custom_id
  `mining:explore_hub`, **preserved** — persistent panel keeps working) now forwards to the new
  world hub. Module docstring de-staled.
- **`disbot/views/mining/explore_hub.py`** + `tests/unit/views/test_mining_explore_hub.py`
  (DELETED) — the 2026-06-15 pure stub (`MiningExploreHubView`, Fishing/Roam/Quests coming-soon) the
  world hub supersedes. Sanctioned by plan §4 ("the mining sub-hub button becomes a thin forward").
- **`disbot/cogs/games_cog.py`** (EDIT) — added the `!world` command opening the world hub.
  `!explore` is **kept** for the hidden mining depth-event mechanic (a different concept).
- **Tests** (NEW) — `tests/unit/services/test_world_registry.py` (8: register/de-dup/replace/sort/
  clear/missing/opener-default), `tests/unit/views/test_explore_world_hub.py` (8: default
  registration, embed lists worlds, registry-driven buttons, Mine-forwards, Fish-card-stays,
  opener-less coming-soon), `+2` in `test_games_cog.py` (`!world` registered + opens the hub).
- **Generated artifacts** regenerated for the new `!world` command — `botsite/data/site.json` +
  `dashboard/data/dashboard.json` (the freshness umbrella + `test_committed_site_json_matches_a_fresh_build`
  would otherwise redden; this is the expected new-command flow, not drift).
- **Docs** — plan §4 status block (PR 1 BUILT → next PR 2/3); `current-state.md` ▶ Next action
  sharpened (PR 1 shipped → PR 2 next; also de-staled the website P1–P8 wave, which shipped #1109+
  with no open website PRs).

## Verification
- `python3.10 scripts/check_quality.py --full` → after regenerating artifacts + black: pytest
  green (10920+ passed; the 4 initial failures were exactly the new-command artifact freshness
  tests + one black reflow, both fixed), black/isort/ruff/`check_consistency --mode strict` clean.
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0, no findings for the new
  `services/world_registry.py` or `views/explore/` files (services-layer boundary respected).
- `python3.10 -m mypy` on the four changed disbot files → clean.
- Targeted suites (world registry · world hub · games_cog · mining-no-root-overview) → 33 passed.

## Merge gate
SUBSTANTIAL plan step (new view package + new service seam + user-facing hub) → labelled
**`needs-hermes-review`**, **auto-merge disabled** (it was auto-armed; I disabled it per Q-0117).
The born-red card flips to `complete` (CI green) as the deliberate final step, but the label + the
disabled auto-merge keep it open for Hermes/owner to merge. It also wants a runtime live-walk this
autonomous session can't perform.

## Handoff — where the next run picks up
- **Federated Explore-hub PR 2** = make the global vs per-game XP split explicit
  (`services/game_xp` global pool + a per-game tree adapter generalizing `skill_service.py`;
  verify the live schema before adding any `game_key` discriminator). Then **PR 3** = the cross-game
  identity read-card. Plan §4–§5. Stop at PR 3 (gated layers need Q-0182).
- When a third world arrives, move the Mine/Fish default registration **out of the view** into each
  subsystem's cog setup (the seam already supports it) — see 💡 below.

## ⚑ Self-initiated
None. PR 1 was an already-promoted plan lane on the live queue (band-#1140 pass promoted the spine;
current-state named PR 1 as a ▶ Next startable) — this is normal dispatch of the top ungated
startable, not an unprompted feature invention.

## 💡 Session idea
**World-entry self-registration + a parity guard.** PR 1 registers the default worlds (Mine · Fish)
from *inside* the hub view (`ensure_default_world_entries`), which is fine for two but will rot as
pets/survival arrive — the view becomes a hidden god-list. The idea: each open-world subsystem
registers its own `WorldEntry` at **cog setup** (the registry already supports it, no view edit),
plus a tiny stdlib CI guard (`check_world_registry_parity.py`) asserting every registered world
`key` maps to a real `SUBSYSTEMS` entry and (optionally) that every `parent_hub`-less
persistent-world game registers a world entry — so a new world can't silently miss the town square.
Dedup-checked `docs/ideas/` — no equivalent. Worth having at PR 2/3, not before (forced filler ≠
work: two worlds don't need it yet).

## ⟲ Previous-session review
The **website-submit-form P4** session (PR #1117) executed cleanly off the foundation's
stub-with-contract, and its own ⟲ review surfaced a genuinely good rule: *"stub tests assert the
contract (router is mounted), never the placeholder's hollowness (`routes == []`)"* — because a
hollowness assertion is guaranteed to break the very unit it hands off to. **What it missed / system
improvement:** that rule was left *only* in a session log, where it evaporates — the next ultracode
foundation unit won't read it. It belongs in the **decomposition playbook** (the website plan §5 /
the ultracode brief) as a standing rule, so the lesson actually changes future behaviour instead of
being re-learned. (This session applied the spirit of it: I retired the stub's *self-invalidating*
test wholesale rather than patching an assertion, and the new world hub's tests assert the
behavioural contract, not internal shape.)

## ⚑ Doc audit (Q-0104)
- `current-state.md` ▶ Next action updated (PR 1 shipped, website wave de-staled). Plan §4 status
  block updated.
- No new owner decisions → router untouched. New docs reachable (the plan already linked).
- Ledger: PR #1156 is unmerged (`needs-hermes-review`), so it correctly is **not** in the
  merged-PR ledger yet — the merging human/next reconciliation records it.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** federated Explore-hub spine **PR 1** — `world_registry` seam +
  `ExploreWorldHubView` + `!world` + mining-button re-parent + stub retirement (PR #1156,
  `needs-hermes-review`).
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** Hermes/owner to **review + merge PR #1156** (the `needs-hermes-review`
  carve-out — auto-merge is intentionally disabled, so it will not merge itself).
- **⚑ Self-initiated:** none
