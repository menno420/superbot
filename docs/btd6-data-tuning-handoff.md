# BTD6 dataset & grounding — tuning handoff

Working notes for continuing to fine-tune the BTD6 answer quality. This is a
**handoff doc, not a binding contract** — when it disagrees with source, source
wins. Start here, then open the files it points at.

The goal of this line of work: the bot answers BTD6 questions **from verified
data**, never from a hallucinated prior. When it lacks a fact it should say so
(and that "stick to verified data, don't cave to 'you're wrong'" behaviour is
**intentional** — do not soften it).

> **Data source:** fixtures default to `disbot/data/btd6/` but the backend is
> swappable via `BTD6_DATA_BACKEND` (`file` / `postgres` / `cloud`) — see
> **`docs/btd6-data-backends.md`** (Postgres is the recommended production
> backend; it reuses the DB the bot already depends on). The read seam is
> `services/btd6_data_provider.py`; everything funnels through
> `btd6_data_service._load_file`, so the backend swap is invisible to consumers.

---

## 1. How a BTD6 answer is produced (the pipeline)

A user message classified as `AITask.BTD6_ANSWER` flows through:

1. **Resolver** — `services/btd6_resolver_service.resolve(text)` (+ `btd6_resolver_vocabulary.py`). Deterministic, no AI. Extracts towers / heroes / bloons / maps / modes / rounds / CT relics. Token-boundary matching (so "mad" ≠ "madness").
2. **Grounding** — `services/btd6_context_service.build(message_text)` assembles a flat list of `[btd6_*]` fact lines from the JSON fixtures + live DB. **Every line is capped at 240 chars** (`_FACT_TEXT_CAP`, applied via `_cap()`), and the line is truncated with `…` if longer — *losing the `(source: …)` suffix*, so keep rendered lines under 240.
3. **Delivery** to the model — two paths, both call `build()`:
   - **Automatic grounding** (uncapped) for `BTD6_ANSWER` messages, via `core/runtime/ai/natural_language_stage.py::_gather_feature_facts`.
   - **`btd6_lookup` tool** (`services/ai_tools.py::_btd6_lookup`) — slices `build()` output to **`_BTD6_LOOKUP_FACT_CAP = 80`** facts. This is the path the model actually leans on, so a cap here silently truncates lists (this was the CT-relic "19 of 24" bug — see §5).
4. **Model** — BTD6 chat runs on **Haiku** (`core/runtime/ai/routing.py`: `AITask.BTD6_ANSWER → claude-haiku-4-5`). **Key behavioural fact:** Haiku reliably calls a tool only when a *directly-matching* tool exists. So the durable fix for "it answered from memory" is almost always **add/extend a tool + its keywords**, not swap the model. (Switching `BTD6_ANSWER` to Sonnet is the agreed last resort, deferred by the maintainer.)

### Render functions to know (in `btd6_context_service.py`)
- `_render_fixture_bloon` — bloon lines (3 lines: head=category+immunities+`popped_by`; stats=`properties`+health+RBE+speed+children; then `description`).
- `_render_paragon` / `_render_paragon_abilities` / `_render_paragon_stats` — paragons (+ non-linear degree note).
- `_render_tower` / `_render_tower_stats`, `_render_hero` / `_render_hero_stats`.
- CT: `_ct_active_tile_lines` (orchestrates) → `_ct_tile_breakdown_lines` (totals by type/mode), `_relic_tile_lines`, `_specific_tile_lines` (+ `_render_ct_tile_full`), `_ct_relic_location_lines`, `_render_ct_relic`.
- `_paragon_roster_facts`, `_paragon_name_facts` (paragon questions don't go through tower resolution).

---

## 2. Data files (`disbot/data/btd6/`)

| File | Holds |
|---|---|
| `bloons.json` | every bloon: `category`, `immune_to`, `children`/`children_list`, `properties`, `rbe`(+`_fortified`), `health`(+`_fortified`), `layers`, `speed`, `aliases`, `description`, `popped_by` |
| `towers.json`, `heroes.json`, `maps.json`, `modes.json`, `rounds.json` | core entities |
| `paragon_abilities.json` | curated paragon abilities (name/kind/cooldown/description) |
| `paragon_descriptions.json` | paragon overview prose |
| `ct_relics.json` | 24-relic CT catalog (id/canonical/abbrev/effect/aliases) |
| `stats/` + `stats/paragons/` | per-tier combat stats (attacks/projectiles/buffs/abilities), the `BTD6_stats` Lua-derived JSON |

**Loader:** `services/btd6_data_service.py` (turns JSON into typed entries). **Stats:** `services/btd6_stats_service.py`.

### bloon schema gotchas (learned the hard way)
- `immune_to` is **damage-TYPE immunity only** (Sharp, Cold, Energy, Explosion, Plasma, Acid, Fire, …). Empty `[]` renders as "no damage-type immunity".
- **Movement-impairment immunity** (slow/knockback/blowback/stun) and **special mechanics** (damage caps, pierce reduction, auras, barriers) go in **`description`** + a short **`properties`** tag — NOT `immune_to`. (BAD and the Frontier Legends bloons are the models.)
- `properties` are free descriptive tags; popping-capability matching does **not** read them (it reads tier `cannot_pop` notes in `btd6_capability_service`), so adding descriptive tags is safe.
- **RBE is children-inclusive** and consistent: `rbe ≈ health + Σ child rbe` (e.g. Diamond 194 = 80 + fortified-ceramic 114). Don't change RBE without re-checking; `tests/unit/services/test_btd6_rbe.py` guards it.
- Put the single most important mechanic in `popped_by` (renders in the **headline** line) and the rest in `description` (its own line) so neither overflows 240 chars.

---

## 3. Data sourcing recipe (bloonswiki.com)

Source of truth is **www.bloonswiki.com** (MediaWiki + Cargo), **CC BY-NC-SA — always paraphrase, never copy verbatim**. **Not** fandom (`bloons.fandom.com` is Cloudflare-blocked → "Just a moment…").

- Canonical fetcher: **`scripts/fetch_bloonswiki.py`** (stats/towers/heroes via Cargo + `Module:BTD6_stats/<Page>/new?action=raw`). Output is committed; the bot never fetches at runtime.
- Pinned User-Agent: `SuperBotDataPipeline/1.0 (https://github.com/menno420/superbot; bot data pipeline)`.
- Quick prose fetch for a bloon/article (what was used to fill the Frontier Legends bloons):
  ```bash
  UA="SuperBotDataPipeline/1.0 (https://github.com/menno420/superbot; bot data pipeline)"
  curl -s -A "$UA" "https://www.bloonswiki.com/<Page_With_Underscores>?action=raw"
  # then strip {{templates}}, <ref>, [[links]] to read the lead prose
  ```
- The Ninja Kiwi **live** API (`https://data.ninjakiwi.com/btd6/...`) is reachable directly with the same UA — used for CT events/tiles/leaderboards. It does **not** publish per-tile ownership or a guild→team mapping (verified — see §6).

---

## 4. AI tools & instruction (`services/ai_tools.py`, `services/ai_instruction_service.py`)

`build_registry(scope, guild_id, …)` assembles the read-only toolset. Current BTD6 tools:
`btd6_lookup`, `btd6_capability_lookup` (towers + paragons; camo/popping), `btd6_superlative_lookup` (cost/DPS/damage/pierce/range rankings), `btd6_difficulty_cost`, `btd6_paragon_calculate`, `btd6_paragon_requirements`, `btd6_paragon_stats_at_degree`, `btd6_ct_team_status` (guild-scoped).

Routing/discipline lives in `_TASK_CONTRACT` in `ai_instruction_service.py` (one big string). It tells the model which tool to call for which phrasing, that paragons scale **non-linearly** (never interpolate degree stats), that DPS is a rough estimate, that tile ownership isn't published, etc.

**To add a tool:** define `_*_SPEC = AIToolSpec(...)` + a handler (guild-scoped ones use a `_make_*(guild_id)` factory closure), add `(SPEC, handler)` to the `build_registry` catalog, add a routing sentence to `_TASK_CONTRACT`, and **update the registry snapshot tests** (`tests/unit/services/test_ai_tools.py` asserts the exact tool-name set for USER and ADMIN scopes).

---

## 5. What shipped this session (so don't rebuild it)

- **Upgrades resolvable** by name/abbrev/path (`btd6_upgrade_service` + `btd6_upgrade_detail_service`): PMFC, POD, Prince of Darkness, etc., with minion/projectile detail.
- **Paragon abilities** dataset (searchable), **superlative/sort** queries, **non-linear degree scaling** (`utils/btd6/paragon_degrees.py`) + `btd6_paragon_stats_at_degree` (per-attack breakdown; DPS labelled rough, never asserted as one precise number).
- **Paragon camo capability + 13-paragon roster grounding** (heroes are never paragons).
- **CT relics** — `btd6_lookup` cap raised 25→80 so a full 24-relic list isn't truncated by live-event preamble (PR #451).
- **CT tiles** — full 169-tile inventory (counts by type & battle mode) + lookup any tile by 3-letter code, verified against the live tile set (PR #452-adjacent / earlier).
- **CT per-team bracket standings** (PR #452) — `services/btd6_ct_team_service.py` owns the per-guild `BTD6_CT_GROUP_ID` (settings key) + `get_ct_bracket()` (on-demand fetch of the per-event `group` endpoint, ranks teams, flags a **stale** id). Set via `!btd6 ctteam <id|group URL>`; read via the `btd6_ct_team_status` AI tool. Migration `053` enabled the `nk_btd6_ct_lb_group` source.
- **Frontier Legends bloons** (PR #453) — Diamond + Dynamite, Aura, Glass, Retribution, Ringleader all had stats but **empty descriptions/no mechanics**; now filled from bloonswiki.

---

## 6. Known remaining gaps / candidate next steps

- **Basic bloons** (Red/Blue/Green/Yellow/Pink) still have empty `description` — low priority (no special mechanics; spawn chain already in `children`).
- **Global CT leaderboards** (the maintainer's "ideal" nice-to-have): the per-team plumbing is reused — just enable `nk_btd6_ct_lb_team` / `nk_btd6_ct_lb_player` sources (new migration, like 053) + add a read path + a tool/command. **No per-tile ownership and no auto "your team" detection exist** in the NK public API (probed exhaustively: tiles = static layout; leaderboards = scores only; guild/user profiles have no CT-team link; guessed ownership endpoints 404).
- **Bracket-id UX is fiddly** — the user must copy the `…/leaderboard/group/<id>` link. Could make `!btd6 ctteam` help locate it from a team name (bounded — the team leaderboard is ~165 pages and crawling is disallowed by the fetch service).
- **Spot-check other data** as testing surfaces issues: tower/hero per-tier stats completeness, other DLC content, any newly-added bloon modifiers.
- Whatever the **screenshot loop** turns up (see §7).

---

## 7. Workflow & gates (do these every time)

**The fix taxonomy** (when a screenshot shows a wrong/empty answer):
1. **Tool/keyword gap** — the question has no directly-matching tool → add/extend one + keywords in `_TASK_CONTRACT`.
2. **Data gap** — the fact isn't in the fixtures → curate it from bloonswiki (§3).
3. **Model** — a good tool exists and it *still* answers from memory → escalate `BTD6_ANSWER` to Sonnet (last resort; confirm with maintainer first).

**Before every push** (CI runs **Python 3.10**; match it exactly):
```bash
python3.10 scripts/check_quality.py --full          # black/isort/ruff + mypy + full pytest (true CI mirror)
python3.10 scripts/check_architecture.py --mode strict
```
**Invariants that bite when adding tools/commands/settings** (each has a guard test):
- `tests/unit/services/test_ai_tools.py` — exact tool-name set per scope (update when adding a tool).
- `tests/unit/cogs/test_btd6_command_parity.py` — every prefix command needs a slash twin unless in `PREFIX_ONLY`/`SLASH_ONLY`.
- `tests/unit/invariants/test_cog_size.py` — `*_cog.py` must stay **< 800 LOC** (`btd6_cog.py` is at **799** — it's full; put new command bodies in `cogs/btd6/_builders.py`, which is uncapped).
- `tests/unit/invariants/test_no_direct_settings_keys_writes.py` — `db.set_setting` callers are allowlisted; new settings get a typed service (e.g. `btd6_ct_team_service`).
- `tests/unit/docs/test_settings_customization_doc.py` — every `settings_keys.__all__` constant must appear in `docs/settings-customization-command-map.md`.
- `tests/unit/services/test_btd6_rbe.py` — RBE consistency.

**Process:** develop on the session's feature branch; **open a PR every session** (maintainer's standing request = advance consent); the maintainer merges, Railway auto-redeploys. Do not put the model identifier in commits/PRs/code.

**Verification:** after a fix, render the affected grounding locally to confirm content + 240-char cap, e.g.:
```python
python3.10 -c "import sys,asyncio; sys.path.insert(0,'disbot'); from services import btd6_context_service as c; \
print('\n'.join(f for f in asyncio.run(c.build('what does the diamond bloon do')).facts if f.startswith('[btd6_bloon]')))"
```

---

## 8. Small gotchas
- The red **"14"** badge in the user's Discord screenshots is the unread-message count, **not** a data count — don't chase it.
- CT **tile codes** are `[A-F][A-G][A-G]` (+ centre `MRX`, quirk `FAH`); positions are fixed across events, only each tile's type/relic/mode changes weekly. The CT **bracket/group id is per-event** (rotates weekly) — a saved one goes "stale".
- `btd6_live_query_service` is a **DB-read** layer (no HTTP). On-demand fetches (like the CT bracket) live in domain services (`btd6_ct_team_service`), patterned after `youtube_context_service`.

---

## 9. Live-events display — fixed vs remaining (cog-split PR3)

**Fixed:** the "current race button does nothing" dead-end. In
`views/btd6/live_events_view.py`, when a kind has no stored events the
event-select used to offer a `(no events)` option that **silently deferred**
on click (looked broken). It is now a **disabled** control, and the defensive
`__none__` path edits in an explicit "no active/recent events" message. The
list embed already renders a clear empty-state. `build_event_detail_embed` is
already limit-safe (≤9 fields; 1024-char truncation), so embed overflow is
**not** the cause of empty detail views.

**Remaining (needs live NK data + a running bot to do safely):**
- **Active vs old events.** `btd6_live_query_service._is_active_window` is
  intentionally lenient — it returns `True` when `end_ms` is absent/invalid, so
  events without a window leak into the "active" list. Tightening it requires
  knowing the real fact-body shape per kind (does every active fact carry
  `end_ms`?); changing it blind risks hiding genuinely-active events.
- **Daily vs custom challenges.** Challenges ingest via the `nk_btd6_challenges`
  parent source (entity kind `btd6_challenge`, `btd6.challenge_list`, daily
  cadence). Splitting "daily" from user-made "custom" challenges needs the NK
  `/btd6/challenges/filter/daily` endpoint wired as a registry source (pattern:
  enable via `services.btd6_source_mutation` + an idempotent migration) and a
  filter in `get_active_events` / `build_live_events_embed`. Confirm the
  endpoint's payload shape against live data before coding.
