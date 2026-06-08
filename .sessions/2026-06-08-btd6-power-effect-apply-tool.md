# 2026-06-08 — BTD6 `btd6_power_effect` apply-tool (answerability next-step #2)

**Branch:** `claude/wonderful-dijkstra-sVRfK`

## Arc
Continued the BTD6 data-mapping effort. The prior session
(`.sessions/2026-06-08-btd6-buff-tail-shinobi-popandawe.md`) ended with an explicit
**"Still owed (next session), in priority order"** list whose **#1** was the
`btd6_power_effect` apply-tool — inputs (the decoded Power `effect` factors) already
extracted, the tool itself the missing piece. Built it end-to-end.

## What shipped
- **`btd6_upgrade_detail_service.power_effect(power, tower)`** — the grounded compute.
  Resolves the tower/upgrade via the deterministic `btd6_upgrade_service.resolve_upgrade`
  (upgrade name / alias / path-notation), falling back to a bare tower's base tier `000`;
  reads `attacks[0].rate`; applies the Power's decoded `rate_scale` → base vs boosted
  cooldown + attacks/sec + duration. Grounded *by construction* (factor × resolved stat).
- **`btd6_power_effect` AI tool** (`ai_tools`) registered + added to
  `BTD6_GROUNDING_TOOL_NAMES` (auto-propagates to the grounding allowlist via
  `natural_language_stage`).
- **De-dup:** Power-name fuzzy resolution moved to `btd6_data_service.find_power`
  (+ sibling `find_tower`), shared by the lookup and effect tools — one home; `_find_power`
  in `ai_tools` now delegates.
- **Honest boundaries:** only `rate_scale` modifies a tower stat today, so Thrive (cash) /
  Camo & Glue Trap (bloons) fail closed with a `btd6_power_lookup` pointer; economy towers
  (Banana Farm) report "no attack-speed stat"; unknown power / unresolved-or-ambiguous tower /
  missing args all fail closed. `_POWER_STAT_EFFECTS` is the named extension point.
- **Result:** "Crossbow Master on Monkey Boost" → **8.42 attacks/sec for 15 s (vs 4.21 base)**.

## Tests / gates
- 5 service tests (`test_btd6_upgrade_detail_service`) + 2 tool tests (`test_ai_tools`);
  both registry-roster tests updated for the new tool.
- `python3.10 scripts/check_quality.py --full` **green (8127 passed, 16 skipped)**;
  `check_architecture --mode strict` **0 errors**.

## Docs
- `docs/btd6/btd6-gamedata-decode-status.md`: answerability table row flipped to ✅, next-step #2
  marked DONE with the implementation note, new session-log entry (newest-first).

## Still owed (carried forward from the prior session)
1. **Monkey Knowledge magnitudes** — maintainer call (not dump-sourced; curate vs descriptive-only).
2. **Steam-API patch-detect refresh trigger** — design in `btd6-data-refresh-pipeline-plan.md`;
   build-id check + GH Actions workflow gated on executable-CI sign-off.

## Follow-on (same session) — Geraldo shop items ingested (next ⬜ domain)

With the apply-tool done and capacity remaining, took the next ⬜ domain off the coverage map
(`docs/btd6/btd6-dump-coverage-map.md`), mirroring the Powers/Knowledge pattern. All **16**
Geraldo shop items are now a game-data-native lookup catalog.

- **Decodability verified first** (the discipline that's saved prior sessions): each item's
  `GeraldoItemModel` has a `locsId`; the textTable keys it as `"<locsId> name"` /
  `"<locsId> description"` — **0/16 missing**. Plus structured `cost` (in-game cash),
  `levelUnlockedAt`, `startingQuantity`/`maxQuantity`, `roundsToReplenish`/`amountToReplenish`.
- **`parse_gamedata.py --geraldo`** → `geraldo_items.json` (16); **`btd6_data_service`**
  `GeraldoItemEntry` + `get_geraldo_item`/`find_geraldo_item` (optional fixture, validated);
  **`btd6_geraldo_lookup`** AI tool registered + in `BTD6_GROUNDING_TOOL_NAMES`. Coverage map
  `GeraldoItems/` → ✅.
- **Honest scope:** a *lookup* catalog (what each item is/costs/unlocks), **not** an applied
  modifier — item mechanical magnitudes live in `behaviorModels` and are not extracted; "Blade
  Trap on a Dart Monkey as a number" is not claimed. Same boundary as Powers/Knowledge.
- Parser + data_service + tool tests; `check_quality --full` green (**8130 passed**), arch
  strict 0 errors, `check_docs` clean. Shipped as a second commit on the same PR branch (#593).

## Context delta
- **Pointed to & needed:** the prior session log's "Still owed" list was the single best pointer
  to the frontier — far more actionable than current-state (which tracks the *Adaptive Setup*
  lane, a different initiative). The decode-status doc is the authoritative BTD6 tracker.
- **Needed but had to derive by hand:** the exact resolution chain
  (`resolve_upgrade` → `UpgradeIdentity{tower_id,code}` → `btd6_stats_service.get_tower_stats`
  → `tier[code]["attacks"][0]["rate"]`) is spread across three services; no doc spells out
  "how to get a tier's cooldown from a name". Captured here so the next stat-apply tool
  (e.g. cash-multiplier) doesn't re-derive it.
- **Surprise (not a bug):** `resolve_upgrade("dart 0-4-0")` → "Super Monkey Fan Club" is
  *correct* — that genuinely is Dart Monkey's mid-path tier 4 (the Fan Club line starts on the
  Dart Monkey). Mid-investigation it read as a resolver bug; it isn't.
- **Floating-point gotcha:** `round(1/cd,3)` for base vs boosted are rounded independently, so
  `boosted_aps == 2*base_aps` is off by ~0.001 — assert with a `< 0.01` tolerance, not equality.
