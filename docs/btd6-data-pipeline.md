# BTD6 data & stats pipeline — working doc / handoff

> **Status:** towers fully done (data → service → UI → AI). Heroes and economy
> income are the remaining pieces. This is a *working/roadmap* doc, not a binding
> contract — when it disagrees with the source, the source wins.
>
> Tracking PR: **#374** (`claude/youthful-wozniak-gsu57`).

## Goal

Make the BTD6 cog a **trustable info & strategy source**: every tower's costs and
combat stats are correct, and the same data is fed to the AI so it can answer
questions about the game *and* about what the bot knows.

## The key discovery

`bloonswiki.com` **is reachable** from the data pipeline (the earlier
`bloons.fandom.com` source had wrong costs and is no longer used). bloonswiki is
a MediaWiki + Cargo + Scribunto site that serves clean JSON, so we fetch
everything directly — no manual pasting, no runtime fetching (data is committed;
the bot only reads files).

### Data sources (all fetched offline by `scripts/fetch_bloonswiki.py`)

| Data | Source | Notes |
|---|---|---|
| Base cost / category | Cargo `btd6_towers` (`cost`, `category`) | `where=name='<Canonical>'` |
| Per-upgrade cost / XP / name | Cargo `btd6_upgrades` (`path,tier,name,cost,cost_C,xp`) | `where=tower='<Canonical>' AND unused=0` |
| Paragon cost | Cargo `btd6_paragons` (`cost`) | optional |
| Hero cost | Cargo `btd6_heroes` (`cost`, `cost_C`) | hero costs verified already-correct |
| Combat stats | `Module:BTD6_stats/<Name>/new?action=raw` (JSON) | towers keyed by crosspath; heroes by level |
| Damage type | `Template:BTD6 dt` switch | ported in `utils/btd6/damage_types.py` |

Cargo API shape: `https://www.bloonswiki.com/api.php?action=cargoquery&format=json&tables=…&fields=…&where=…&order_by=…&limit=…` → rows under `cargoquery[].title`.

Stats JSON shape (towers): top-level keys are `_000` (base) + 15 single-path
crosspath codes `[P1][P2][P3]` (`_100`..`_500`, `_010`..`_050`, `_001`..`_005`);
nested `_NNN` keys inside a tier are crosspath **deltas** (dropped for now).
Each tier has `attacks` → `projectiles` → `effects`, plus `abilities`, each as
`{"_order": [...], "<Name>": {...}}` containers. `_last_updated` = game version.

## Decisions / conventions (don't relitigate without reason)

- **Store Medium cost only**; derive Easy/Hard/Impoppable via the fixed formula
  (`utils/btd6/difficulty_costs.py`): Easy ×0.85, Hard ×1.08, Impoppable ×1.20,
  round to nearest 5, ties down. Verified exact against the published table.
  (`cost_C` = CHIMPS cost exists in Cargo if ever needed.)
- **Normal vs Pro is a presentation policy, not a data split.** Full stats are
  stored; the *normal* view (damage, type+immunities, pierce, cooldown, range,
  camo, headline specials incl. cash income) is derived in
  `btd6_stats_service.normal_stats`. Pro = the full per-tier breakdown.
- **Stats live in per-tower lazy files** `disbot/data/btd6/stats/<id>.json`
  (loaded only when a tower is opened); the catalog `towers.json` stays lean.
- **Costs flow through the CSV.** The fetcher rewrites `data/btd6/towers.csv`
  cost/name columns; `scripts/import_btd6_data_from_csv.py` regenerates
  `towers.json`. The CSV remains the catalog source of truth.
- **Licensing (CC BY-NC-SA):** stat *numbers are facts* → stored freely; prose
  descriptions are **not** copied verbatim (paraphrase the useful parts);
  attribute bloonswiki via the `source` field. NC matters if the bot is ever
  monetised.
- **`9999999` is the game's "infinite" sentinel** (e.g. Spirit of the Forest) →
  render as `∞`.
- `game_version` varies per tower (seen 52.2–54.0); the catalog is stamped with
  the newest (54.0) and each stats file carries its own.

## Pipeline / data flow

```
bloonswiki.com
   │  scripts/fetch_bloonswiki.py  (--tower <id> | --all ; --dry-run)
   │    ├─ Cargo costs ──────────────► data/btd6/towers.csv  (cost/name columns)
   │    └─ Module:BTD6 stats JSON ──► parse_bloonswiki.parse_stats_json
   │                                    (flatten _order, decode damage types,
   │                                     drop crosspath deltas)
   ▼
disbot/data/btd6/stats/<id>.json   (rich: base/category/paragon, per-upgrade
   │                                 cost+XP, full per-tier combat stats)
   │
data/btd6/towers.csv ──► scripts/import_btd6_data_from_csv.py ──► towers.json (catalog)
   │
   ▼ runtime
services/btd6_stats_service.get_tower_stats(id)  (lazy, cached)
   ├─ normal_stats(tier) ─► utils/btd6/stats_embed.format_normal_stats ─► tower detail "📊 Base stats"
   ├─ tiers ──────────────► utils/btd6/stats_embed.build_pro_tier_embed ─► views/btd6/tower_stats_view ("🔬 Pro stats")
   └─ per-tier facts ─────► services/btd6_context_service._render_tower_stats ─► AI grounding ([btd6_tower_stats normal])
```

### Files (what each does)

- `scripts/fetch_bloonswiki.py` — network fetcher (Cargo + stats module); writes CSV + stats files. `--dry-run`, `--tower`, `--all`. Resilient to economy towers (404 on stats module → costs only).
- `scripts/parse_bloonswiki.py` — `parse_stats_json` (stats), `parse_upgrades_page` (pasted upgrade pages, legacy/back-up). Auto-detects JSON vs text.
- `utils/btd6/difficulty_costs.py` — Medium→difficulty cost formula.
- `utils/btd6/damage_types.py` — `immuneBloonProperties` → `(damage type, what it can't pop)`.
- `utils/btd6/stats_embed.py` — `format_normal_stats`, `build_pro_tier_embed`, `tier_label`. Duck-typed `Any` inputs to keep `utils → services` boundary (like `response_embed.py`).
- `services/btd6_stats_service.py` — lazy loader + `NormalStats`/`TowerStats` + `normal_stats`.
- `services/btd6_context_service.py` — `_render_tower_stats` adds per-tier AI grounding lines.
- `views/btd6/tower_stats_view.py` — Pro tier-picker view + `attach_pro_stats_button`.
- `views/btd6/tower_browser_view.py` — detail embed now adds the base-stats field + Pro button.

## How to run the pipeline

```bash
# Preview one tower (no writes):
python3.10 scripts/fetch_bloonswiki.py --tower bomb_shooter --dry-run
# Fetch the whole roster (writes CSV cost columns + stats/*.json):
python3.10 scripts/fetch_bloonswiki.py --all
# Regenerate the catalog from the corrected CSV:
python3.10 scripts/import_btd6_data_from_csv.py --allow-empty-descriptions --skip-incomplete --game-version 54.0
# Gate:
python3.10 scripts/check_architecture.py --mode strict && python3.10 scripts/check_quality.py --check-only && python3.10 -m pytest tests/ -q
```

## Done (PR #374)

Towers, end to end: corrected costs (roster 22→25, incl. Desperado / Mermonkey /
Beast Handler), per-tower stats files, `btd6_stats_service`, base + Pro tower UI,
and AI grounding with per-tier stats incl. cash income. ~70 new tests; full
suite green (6152 passed).

**Cash-generation note:** income for Sniper, Heli, Engineer, Druid, Alchemist,
Buccaneer is already captured (it rides inside their stats modules as
`abilities`/`collectables`/`cashPerRound`/`cashMinimum`/`cashMultiplier`). Obyn
does **not** generate cash. See the income gaps below.

## Next steps

### 1. Heroes — per-level stats (a real subsystem)
- Costs: already correct (Cargo `btd6_heroes` verified). No action.
- Stats: `Module:BTD6_stats/<Hero>/new?action=raw` is keyed by **level**
  (`_2`..`_20`) and the levels are **deltas over the base** (the wiki's
  `parse_tower_full` merges them). So this needs:
  - a hero-stats parser that **merges level deltas** into full per-level stats
    (different from `parse_stats_json`, which assumes complete crosspath tiers);
  - hero stats files (`disbot/data/btd6/stats/heroes/<id>.json`?) or extend the
    existing dir with a `levels` shape;
  - level-aware variants of `btd6_stats_service` / `stats_embed` / the hero
    detail view / grounding (or generalise the tower ones over "tier key").
- Some heroes have **no** stats module (Obyn, Benjamin 404'd) — handle like
  economy towers (no combat stats). Geraldo has one but no cash field (his cash
  is shop items).

### 2. Economy income (Banana Farm, Monkey Village)
- These 404 on the stats module (no combat stats). Income lives in:
  - the page's *"Cash Generated per Farm"* rendered table (Income/Banana,
    Income/Round per upgrade), and
  - upgrade `description` text in Cargo `btd6_upgrades` (e.g. "Grows 2 extra
    bunches per round", "$300 crates").
- **Investigate first:** does Cargo expose a numeric income/value field
  (check full `btd6_upgrades` / `btd6_towers` field lists via
  `action=cargofields`)? If yes, clean. If not, parse the page income table or
  derive from base ($80/round) + descriptions.

### 3. Smaller polish (optional)
- Paraphrased tower descriptions (the `description` column is still empty by
  design — CC-BY-SA prose was skipped). Curate short factual blurbs.
- Show derived per-difficulty costs in the UI (formula already exists).
- Surface crosspath-delta stats in the Pro view (data is in the module; deltas
  currently dropped on ingest).

## Gotchas

- `bloonswiki.com` is reachable here; `bloons.fandom.com` was the **wrong** old
  source — don't reintroduce it for costs.
- Don't dump full Pro stats into AI grounding (too large); per-tier *normal*
  headlines are enough and are what `_render_tower_stats` emits.
- Test files are **not** linted by CI (`ruff`/`black` run on `disbot/` +
  `scripts/` only); don't be alarmed by `check_quality` flagging test drift.
- Run all tooling under **Python 3.10** to match CI.
