# BTD6 Data Scaffold

Hand-curated source data for SuperBot's BTD6 cog. Editable here as CSV
(human-friendly, spreadsheet-compatible). The runtime reads JSON from
`disbot/data/btd6/`; the import script converts CSV → JSON when the
team is ready to ship.

## Files

| File | Purpose |
|---|---|
| `towers.csv` | All 24 BTD6 towers. Identity columns prefilled (`id`, `canonical`, `category`, `aliases`, `wiki_url`). Content columns blank — your team fills these. |
| `heroes.csv` | 16 heroes through Rosalia (v45.0). Identity columns prefilled. |
| `README.md` | This file. |

## Workflow

### Editing in a spreadsheet

The CSVs are designed for collaborative editing in Google Sheets / Excel
/ Numbers. Recommended flow:

1. Upload `towers.csv` and `heroes.csv` to a shared Google Sheet.
2. Distribute rows across the team (one tower per person, or by
   category).
3. Fill in the empty columns:
   - **`base_cost`** — integer, Medium difficulty default (verify in
     game info screen)
   - **`description`** — short prose in your team's voice (do NOT
     copy/paste from the wiki; the wiki is CC-BY-SA and copying
     verbatim creates an attribution obligation)
   - **`top_1`..`top_5`**, **`mid_1`..`mid_5`**, **`bot_1`..`bot_5`** —
     the 5 upgrade names per path, in tier order (verify in game)
   - **Heroes**: `ability_3_name`, `ability_3_summary`,
     `ability_10_name`, `ability_10_summary` — the two ability levels
     standard heroes get
4. Export back to CSV. **Important:** keep the column order identical
   to the scaffold — the import script reads columns by header name,
   but treat preserving order as belt-and-braces.
5. Commit the updated CSV files to the repo.

### Importing CSV → JSON

```bash
python3.10 scripts/import_btd6_data_from_csv.py
```

The script:

- Reads `data/btd6/towers.csv` and `data/btd6/heroes.csv`
- Validates every row (category whitelist, cost > 0, exactly 5 tiers
  per path, no empty required fields)
- Writes `disbot/data/btd6/towers.json` and
  `disbot/data/btd6/heroes.json` in the shape the runtime expects
- On validation error, prints the offending row + column with a
  human-readable reason; nothing is written

After a successful import, commit the regenerated JSON files alongside
the CSV changes so the runtime picks them up on next deploy.

## Schema reminders

### `towers.csv` columns

| Column | Type | Required | Notes |
|---|---|---|---|
| `id` | snake_case | yes | Must be unique. Used in URLs, logs, the API-key map. |
| `canonical` | string | yes | The official tower name (e.g. "Super Monkey"). |
| `category` | enum | yes | One of `primary`, `military`, `magic`, `support`. |
| `aliases` | comma-separated list | yes | Community nicknames the resolver should match. Must not collide with any other tower/hero/map/mode alias. |
| `base_cost` | positive int | yes | Medium difficulty base cost. |
| `description` | string | yes | Short prose, your team's voice. |
| `top_1`..`top_5` | string | yes | Tier 1–5 upgrade names on the top path. |
| `mid_1`..`mid_5` | string | yes | Same, middle path. |
| `bot_1`..`bot_5` | string | yes | Same, bottom path. |
| `wiki_url` | URL | yes | Link to the tower's wiki page (already prefilled). |

### `heroes.csv` columns

| Column | Type | Required | Notes |
|---|---|---|---|
| `id` | snake_case | yes | Must be unique. |
| `canonical` | string | yes | Official hero name. |
| `aliases` | comma-separated list | yes | Community nicknames. |
| `base_cost` | positive int | yes | Medium difficulty base cost. |
| `description` | string | yes | Short prose. |
| `ability_3_name` | string | yes | Name of the level-3 ability. |
| `ability_3_summary` | string | yes | One-line summary. |
| `ability_10_name` | string | yes | Name of the level-10 ability. |
| `ability_10_summary` | string | yes | One-line summary. |
| `wiki_url` | URL | yes | Already prefilled. |

## Roster note

The scaffold lists 24 towers and 16 heroes — accurate as of BTD6 v45.0
(Rosalia release). If Ninja Kiwi has shipped a new tower/hero in
v46–v54 that we missed, add a row in the CSV and the matching API-key
mapping in `disbot/services/btd6_live_query_service.py` (`_TOWER_ID_TO_API_KEY`
or `_HERO_ID_TO_API_KEY`) — the coverage test in
`tests/unit/services/test_btd6_live_query_service_mapping_coverage.py`
will fail loudly if you forget the mapping.

## Why CSV instead of editing JSON directly

- **Multi-person editing.** Google Sheets handles concurrent edits;
  JSON merge conflicts on a single file are painful.
- **Diff visibility.** Spreadsheet cells make missing data obvious at
  a glance.
- **No JSON syntax errors.** No bracket / comma debugging.
- **One-way derivation.** The CSV is the source of truth; the JSON is
  generated. If the CSV is wrong, the JSON regenerates cleanly.
