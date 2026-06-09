# 2026-06-08 — BTD6 mode-rules cutover (Mods/ → modes.json structured rules)

**Branch:** `claude/btd6-mode-rules-cutover` (off post-#601 main). Final build of a
multi-PR session: not-in-dump re-audit → bosses → bloon-stats (#601) → this.

## Task
Owner greenlit the mode-rules cutover as the last build, on the standing "map
**everything**" goal. Then: update docs, reflect on the workflow, leave a
continuation message.

## What shipped
A `--modes` overlay in `parse_gamedata.py` that sources structured, game-grounded
rules from `Mods/<mode>.json` into `modes.json`:
- **`_parse_mode_rules(raw_mod)`** normalizes `mutatorMods[]` → a clean `rules`
  dict: `starting_cash`/`starting_lives`, `start_round`/`end_round`,
  `cost_multiplier`/`speed_multiplier`/`income_multiplier`, `{tag}_health_multiplier`,
  `round_set`, `locked_tower_classes`/`locked_towers`, and
  `no_continues`/`no_selling`/`no_monkey_knowledge`/`no_income`/`reverse` flags.
  The **standard economy curve** (MonkeyMoney / BonusCashPerRound / SellMultiplier /
  SetHealthForBloon) is deliberately dropped — only what *varies/restricts* is kept.
- **`overlay_modes`** maps 15 modes (`_MODE_MODS`; note CHIMPS → `Clicks.json`),
  attaches `rules`, **verifies** `starting_cash`/`starting_lives` against the dump's
  absolute overrides, and writes `mode_rules_source` provenance.
- **Caught one real curated typo:** Sandbox `starting_lives` 9999999 → game model's
  999999. Everything else matched.
- **Runtime:** added `ModeEntry.rules: dict` (+ `_parse_mode` reads it). Display
  **unchanged** — wiring `rules` into the embed is the teed-up follow-up.
- Corrected the old "the dump has no game-mode rules" finding — they live in
  `Mods/`, same place MK effects do.

## Key facts for next session
- **Mods/ mutator vocabulary (24 types)** is the raw material; the mapping table +
  normalizer in `_parse_mode_rules` is the canonical decode. Tower-set bitflags:
  `_TOWER_SET` (module line ~58, **lowercase** primary/military/magic/support — reuse
  it, don't redefine: I hit a shadowing collision doing exactly that).
- `overlay_modes` reads `_DATA_ROOT/modes.json` directly → unit-test by
  `monkeypatch.setattr(mod, "_DATA_ROOT", tmp)` + a tmp `Mods/` (same pattern as the
  bloon overlay).
- `_parse_mode` ignores unknown JSON keys; `_REQUIRED_MODE_FIELDS` only checks
  presence — so additive `modes.json` fields are safe.

## ▶ Continuation — next steps (in priority order)
1. **Wire `ModeEntry.rules` into the mode display.** Data is sourced but the embed
   still shows only prose. Touch points: `cogs/btd6/_embeds.py` ~L280 (restrictions
   block) and `services/btd6_response_builder.py` ~L234 (cash/lives bits). Show
   rounds/cost/income structurally. This *completes* this cutover.
2. **Keep the "map everything" arc going:** boss skull mechanics (decodable:
   HealthPercentTrigger + SpawnBloonsAction), alternate round sets (ABR 140), then
   the gated tower-stats cutover (needs buff/zone tails first), then niche/cosmetic
   (Rogue Legends, Frontier, Achievements, Skins/TrophyStore — owner wants these too).
3. **Tech-debt flag (capture as idea, not urgent):** `parse_gamedata.py` is ~2700
   lines holding every domain's overlay. Naming discipline keeps it navigable, but
   the `_TOWER_SET` near-collision is a warning sign. A `parse_gamedata/` package
   (one module per domain + shared `_helpers`) would de-risk further growth.

## Verification
`check_quality.py --full` green (8170 passed, +3 new); `check_architecture --mode
strict` 0 errors. `--modes` re-run is idempotent (0 corrections after the first).

---

## Workflow reflection (owner-requested: what helped / hindered this session)

**File structure — easy:** The BTD6 work is genuinely turnkey because of *pattern
discipline*. `parse_gamedata.py` uses consistent `overlay_<domain>` / `_select_*` /
`_parse_*` naming, so seeing `overlay_bloons` told me exactly where `overlay_modes`
goes and what shape it takes (parse → verify-scalars → attach → provenance → test).
The data↔runtime split is clean: `data/btd6/*.json` mirrors a `*Entry` dataclass in
`btd6_data_service.py`, so "where do I surface a new field" was a 2-minute answer.
The `docs/btd6/` cluster (decode-status ledger + coverage map) is a *real* single
source of truth for "cut over vs curated" — I oriented in one read.

**File structure — hard:** `parse_gamedata.py` at ~2700 lines is the friction point.
It stays navigable only by naming convention, and I *did* collide with a 2500-lines-
distant module constant (`_TOWER_SET`); the test caught it, but that's luck-adjacent.
Flagged as continuation item 3.

**Tools — what worked:** The `--dry-run` overlay is the MVP of this workflow — seeing
the correction surface (the Sandbox typo) *before* writing de-risked the whole change.
`check_quality.py --full` as a true CI mirror is trustworthy (green local = green CI).
The `monkeypatch(_DATA_ROOT)` test idiom makes overlays unit-testable without touching
committed data.

**Tools — gaps:** (a) `context_map.py` is Python-module-only — it *errored* on
`modes.json`. For a data-cutover-heavy workflow, a "who consumes this JSON" map (loader
service + dataclass + pinning tests) would save the grep-archaeology I do each time.
(b) I had to *discover* the 24-entry `Mods/` mutator vocabulary by enumeration — a
committed "mutator $type catalog" (like the decode-status ledger but for raw dump model
shapes) would have shaved real time. (c) CodeGraph was near-useless here and correctly
so — data-shape work isn't call-graph work; the CLAUDE.md tier guidance steered me right.

**Docs / concept clarity:** The BTD6 *subsystem* concept (migrate every wiki value to
reproducible game-sourced data, ledgered) is legible fast. What's *less* obvious from
the BTD6 docs alone is how BTD6 sits in the bot as a whole — SuperBot is a Discord
server-setup/management bot with BTD6 knowledge as one feature, and a fresh agent
reading only `docs/btd6/` wouldn't infer that. A one-line "where this subsystem sits"
pointer atop the decode-status ledger would help orient a cold-start agent. (Didn't
block this task — the cutover is self-contained — but worth a small doc nudge.)
