# Session — reconcile shipped fishing v1 to the owner's design (Q-0175)

> **Status:** `complete`

## Context — why this follow-up exists

The fishing v1 PR (#1033) **merged** while this session was away, but it merged at
the *interim* head: a self-authored design (14 fish, 5 rarity tiers, **coins per
catch**) that was built **before** the owner's detailed fishing design landed. The
owner's design merged separately as **#1036 (Q-0175)**
(`planning/fishing-open-world-expansion-plan-2026-06-18.md`) and is the
authoritative spec — and the shipped #1033 code **contradicts it**:

| | shipped #1033 (interim) | owner #1036 / Q-0175 (authoritative) |
|---|---|---|
| fish set | 14, 5 rarity tiers | **21, ranked by size** |
| catch | rarity-weighted roll over all | **level-gated** — 7 levels × 3, unlock bigger |
| leveling | n/a | **reuse `game_xp`** |
| reward | **coins per catch** | **no coins — value is an OPEN question** |

This card reconciles the shipped code to the owner's spec. It is a **correction**,
not a re-submission of #1033 (which is merged + closed).

## What shipped (the reconciliation)

- **Data** `disbot/data/fishing/fish.json` — the **21-fish, size-ranked** dataset.
- **Domain** `utils/fishing/fish.py` (loads + sorts the catalog; owns the 7×3 level
  bands: `max_size_rank_for_level`, `unlocked_species`) + `rewards.py`
  (`roll_catch(level)` — level-gated deterministic roll, inverse-size weighted,
  seed-deterministic). The old rarity/`rod_bonus` model is gone.
- **Service** `services/fishing_workflow.py` — `fish()` now derives the fishing
  level from the player's per-game `GAME_FISHING` xp (`fishing_level_from_xp`,
  reuses the shared level curve, capped at 7), rolls within the unlocked band,
  records the catch + awards xp in ONE transaction, and flags `unlocked_bigger`.
  **`economy_service` is removed from the fishing path — no coins.**
- **Migration** `075_fishing_catch_log.sql` — simplified (count + first/last; the
  `total_value`/`best_weight` columns dropped — value is deferred).
- **DB** `utils/db/games/fishing.py` — `record_catch` (no value) / `get_fishing_log`
  (`{species: count}`) / `top_fishers` (by total catches).
- **Cog** `cogs/fishing_cog.py` — `!fish` shows the fish + its size rank + a
  level-up "you can now catch bigger fish" note; `!fishlog` shows the X/21
  collection with unlocked-vs-locked bands; `!fishtop` ranks by total catches.
- **Game-XP** — the `"fish"` award bumped 3 → 5 (a reasonable band-unlock pace).
- **Docs** — deleted my redundant interim plan; the owner's #1036 plan is the
  single authoritative design. Updated current-state ▶ Next action, ownership.md,
  and the settings-command-map fishing section (no coins; the size/level model).
  Resolved the origin/main merge (kept the owner's Q-0175; my auto-merge-enabler
  proposal stays Q-0176).
- **Deferred per Q-0175 (owner's OPEN questions — NOT decided here):** minigame vs
  roll · leveling shape (rod-tier vs skill) · loadout-preset UI · value/cook/sell ·
  the boat/open-world (Phase 2+).

**Verification:** `check_quality --full` GREEN · `check_architecture --mode strict`
0 errors · `check_docs` ✓ · `check_generated_artifacts_fresh` ✓.

**Review gate:** `needs-hermes-review` — this changes just-shipped runtime behaviour
to match the owner's design, so the owner consciously merges it (Q-0117).

## 💡 Session idea

**A "design-landed-mid-build" guard for the dispatch routine.** This session's whole
rework happened because the owner dropped an authoritative design (#1036) *while* a
conforming-but-interim build was in flight, and the two merged independently. A cheap
guard: when a dispatch run promotes an idea→plan→build, it should **re-scan open PRs +
the last ~10 merges for a same-topic owner-directed plan/Q-block before opening its PR**
(a title/keyword match on the idea), so a freshly-landed owner design is caught before,
not after, the build ships. (Captured here; extends the Q-0176 "routines check recent
PRs first" direction.)

## ⟲ Previous-session review

The previous run (this session's own #1033) shipped a clean, well-tested fishing v1 —
but its miss is the reason this card exists: it **invented a fishing design instead of
checking whether the owner had one in flight.** Fishing was the canonical Q-0172
candidate precisely *because* the owner cared about it, which should have been a signal
to look for owner input first (open PRs / recent merges / the router) before authoring a
design. The interim design also **pre-decided questions the owner later marked OPEN**
(coins, the catch mechanic). Lesson, now a session idea above: **on a high-owner-interest
topic, scan for an owner-directed design before authoring your own.** The recovery was
correct (reconcile rather than ship contradicting code), and #1033 being open at resume
made it cheap — but catching it pre-build would have avoided the churn entirely.

## Documentation audit (Q-0104)

- `check_current_state_ledger.py --strict` ✓ (the merge brought the #1030–#1037 band in).
- Current-state ▶ Next action rewritten to flag #1033's interim-design merge + this
  reconciliation; ownership/settings-map de-coined; the redundant interim plan deleted.
- `check_docs --strict` ✓; `check_generated_artifacts_fresh` ✓.

## 📤 Run report

- **Did:** reconciled the just-merged fishing v1 (#1033, interim design) to the owner's
  authoritative #1036 / Q-0175 spec — 21 size-ranked fish, 7×3 level-gated catch, no
  coins · **Outcome:** correction PR open, `needs-hermes-review`
- **Shipped:** the reconciliation (this branch) — `data/fishing/fish.json` + the
  rewritten `utils/fishing/` + `fishing_workflow` (no economy seam) + migration/cog/db +
  docs. CI mirror green; arch 0.
- **⚑ Self-initiated:** **yes** — a self-initiated correction to align shipped code with
  the owner's written design (no work order). Flagged for owner review; gated
  `needs-hermes-review` so the owner consciously decides.
- **⚑ Owner decisions needed:** **(1)** merge or close this reconciliation — does the
  owner want the #1036 design now, or keep the interim v1 and evolve later? **(2)** the
  Q-0176 auto-merge-enabler proposal (unchanged). **(3)** the open Q-0175 mechanics
  (minigame/leveling/value/loadout/boat) when the owner is ready.
- **⚑ Owner manual steps:** `none` off-repo (a merge auto-deploys; migration runs on boot).
- **↪ Next:** after this merges — fishing Phase 1 step 2 (unified loadout presets) →
  Phase 2 (boat/world). Per current-state ▶ Next action.
- **Run type:** `routine · dispatch`
