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

## Follow-on #2 (maintainer-directed) — Bloons children + immunity cutover

Maintainer chose the Bloons cutover (via AskUserQuestion) over wrapping up. Sourced the two
`bloons.json` fields exactly reproducible from the dump from game data instead of bloonswiki.

- **Immunity → game data, verified identical.** New public `immunities_for_bloon_properties`
  in `utils.btd6.damage_types` inverts the existing projectile-side `_DAMAGE_TYPES` bitmask
  (one source of truth): a bloon with property bit `p` is immune to every damage type whose
  mask shares `p`. **23/23 exact** vs the curated lists → the overlay leaves immunity
  byte-identical (provenance-only).
- **Children → game data, one wiki correction.** `parse_gamedata.py --bloons` reads
  `SpawnChildrenModel`, resolves each child to its base via `baseId`, and **preserves** the
  variant's camo/regrow/fortified modifiers (matching the curated Glass Bloon children). One
  genuine dump-vs-wiki correction: **BAD** `3 DDTs` → `3 Camo DDTs` (BAD's DDTs are camo; wiki
  dropped it).
- **Model-selection bug — caught by the maintainer.** First pass matched each bloon to its
  directory's *base* model. But a DDT is inherently Camo, and the base `Ddt.json` is a non-camo
  *template* (children `CeramicRegrow`); the real in-game DDT is `DdtCamo` (children
  `CeramicRegrowCamo`). So the first pass wrongly dropped Camo from DDT's children. Maintainer
  flagged it ("they're definitely camo in game"); re-checked the dump, found `DdtCamo`, and
  added `_select_bloon_model` to pick the model whose flags match the bloon's own `properties`.
  DDT now correctly stays `Camo Regrow Ceramic`. **Lesson: a bloon's directory base file isn't
  always its canonical model — match by the bloon's inherent modifiers.** Regression-pinned.
- **The discipline that paid off:** verifying decodability *before* coding caught that the wiki
  *already* carried child modifiers (Glass), so a naive base-normalize would have regressed
  Glass; and the maintainer's domain check caught the DDT model-selection miss that the
  23/23-on-statted-bloons verification didn't (DDT's base template still "verified" wrongly).
- Overlay is provenance-marked + re-runnable; coverage map note updated. Inverter + parser +
  data_service tests (one pre-existing DDT test corrected to the game value). `check_quality
  --full` green (**8140 passed**). Third commit on PR #593.

## Follow-on #4 — Geraldo item effects (PR #595) + provenance principle (Q-0037)

After #593 merged, continued on the same branch:

- **Geraldo item effects** (PR #595, merged): five items whose named behaviour model carries
  clean, description-confirmable numbers gained a structured `effect` (mirroring
  `PowerEntry.effect`) — Sharpening Stone `{pierce_increase:1, rounds:10}`, Jar of Pickles
  `{damage_increase:1, attack_speed_scale:0.75, rounds:5}`, Fertilizer `{cash_scale:1.2, rounds:4}`,
  Rejuv Potion `{lives_gained:50}`, See Invisibility `{rounds:5}`. Projectile/summon/non-numeric
  items stay `effect == {}` (never fabricated).
- **Owner decision Q-0037 — dump-vs-wiki provenance:** maintainer's standing principle —
  **trust the dump wherever it's complete and accurate** (direct export of the game's internal
  files; most recent). Routed to the question router + decode-status provenance note.
- **Diamond false-alarm withdrawn.** I'd flagged "Diamond health dump 60 vs wiki 80" as a possible
  cutover. Re-checking with the parser's variant-aware `_select_bloon_model`: canonical
  `DiamondBloon` = **80**, matching our data. The "60" was a `DiamondbackDiamondBloon` variant my
  ad-hoc check grabbed — **the DDT trap again.** All 23 dump-modelled bloons already match the dump
  on health *and* speed. No change. (This is the second time a naïve "first matching file" pick read
  a wrong value the maintainer caught — the model-selection caveat is now in Q-0037 + decode-status.)

**Both PRs merged this session:** #593 (power_effect + Geraldo lookup + bloon children/immunity
cutover + DDT fix) and #595 (Geraldo effects + Q-0037 provenance docs).

**Still owed (maintainer-gated):** MK magnitudes (curate from wiki vs descriptive-only),
Steam-API patch-detect refresh trigger (sign-off on the GH Actions workflow). The big remaining
dump-trust opportunity is the **tower stat cutover** — large + architecturally heavy; scope as its
own planned effort.

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
- **★ The biggest recurring trap (hit twice — DDT children, Diamond health):** the BTD6 dump
  has **template/variant models** that look internally consistent but aren't the canonical one a
  committed bloon maps to. `Bloons/<X>/<X>.json` is **not** reliably the right model — a DDT is
  inherently camo (`DdtCamo`), Diamond's "60" is a Diamondback-spawned variant (canonical
  `DiamondBloon` = 80). **Always select by the entity's own properties (`_select_bloon_model`),
  and sanity-check a surprising value against gameplay before asserting it.** Both misses were
  caught by the maintainer's domain knowledge, *not* the "23/23 verified" structural check —
  because the wrong model still verified self-consistently. When a dump value contradicts the
  wiki *and* your game sense, suspect the model pick before trusting the number. (Owner principle
  Q-0037: trust the dump where complete/accurate — with this caveat attached.)
