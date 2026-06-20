# 2026-06-20 — Wire the Claude-designed SPA into the bot site (live data)

> **Status:** `complete`

## Arc

Owner uploaded `SuperBot_Design_System.zip` — a Claude-Design handoff containing a finished
vanilla-JS SPA (neon theme: Home / Features / Commands / Games / Changelog / Status) whose only
wire-up task per its README is to regenerate `prototype/data.js` from the real bot. Owner asked to
"make sure the current state of the website will be built and linked to the current botsite, follow
the Claude-design instructions to provide the proper data, eventually all data should dynamically
load," and invited a better/more-efficient approach (owner is still learning Claude Design).

**Decision (owner via AskUserQuestion):** SPA becomes the served bot-site front-end; data delivered
via a **dynamic FastAPI endpoint + a committed generated fallback**. The efficiency win: instead of
hand-writing `data.js` (instant drift), **generate it from the existing CI-guarded `site.json`
pipeline** so it stays truthful with zero manual upkeep.

## Plan (what this PR adds)

- `botsite/site/{index.html,app.js,app.css}` — the design SPA, copied **verbatim** (handoff rule:
  do not edit these; only the data layer).
- `botsite/site_data.py` — stdlib-only generator: `site.json` (public subset) → the SBDATA
  contract (ICONS/AREAS/COMMANDS/GAMES/CHANGELOG/STATUS + lookup helpers + `window.SBDATA`).
  Lives inside `botsite/` so the runtime endpoint can use it (Railway deploys only `botsite/`).
- `botsite/site/data.js` — generated committed fallback (so the SPA also opens as a static file).
- `botsite/app.py` — `/` serves the SPA shell; `/app.js`,`/app.css` static; **`/data.js` dynamic**
  (generated from live `site.json` per request); legacy page routes redirect into the SPA hash.
- `scripts/export_dashboard_data.py` — also regenerates the committed `data.js` (one pipeline).
- Tests: rewrite `test_app.py` for the new `/`; add `test_site_data.py` (contract invariants,
  CI-running, stdlib-only). Docs: `botsite/README.md`.

## Suggestions surfaced to owner

- The SPA's "Add to Discord" CTA is `href="#/"` (design placeholder). The handoff forbids editing
  `index.html`/`app.js`, so wiring the real install URL should originate from the next Claude-Design
  round (a 1-line change), or via a future `install_url` field the SPA reads. Flagged, not patched.

## ⚑ Self-initiated

None — owner-directed (wire the design into the site + dynamic data). Approach choices confirmed
via AskUserQuestion.

## Shipped

- **`botsite/site/{index.html,app.js,app.css}`** — the Claude-Design SPA, verbatim.
- **`botsite/site_data.py`** — stdlib-only generator: `site.json` → `window.SBDATA`. Maps the 8+1
  command categories → AREAS (data-driven `points` from the catalogue), 308 commands → 280 unique
  COMMANDS (deduped — names key the detail URLs), 8 is_game entries → GAMES (each pointed at a real
  command, with safe fallbacks), bot_changelog → CHANGELOG (CalVer), and an honest operational
  STATUS (no fabricated incidents). All contract cross-refs guaranteed to resolve.
- **`botsite/site/data.js`** — committed static fallback (regenerated from `site.json`).
- **`botsite/app.py`** — `/` serves the SPA shell; `/app.js`,`/app.css` static; **`/data.js`
  dynamic** (live from `site.json` per request); legacy Jinja page routes kept as fallback.
- **`scripts/export_dashboard_data.py`** — also regenerates `site/data.js` (one pipeline).
- **Tests** — `test_site_data.py` (12 stdlib contract guards, CI-running) + rewrote the `/`-tests
  in `test_app.py` for the SPA shell + dynamic `/data.js`. `pyproject.toml` per-file T201 ignore.

Verification: `pytest tests/unit/botsite/ + test_export_dashboard_data.py` 104/104 · `check_quality
--check-only` ✓ · `check_architecture --mode strict` exit 0 · `node --check data.js` ✓ · every field
`app.js` reads is present in the generated data.

## Suggestions for the owner (Claude-Design workflow)

- **The "Add to Discord" button is a placeholder (`href="#/"`).** The handoff forbids editing
  `index.html`/`app.js`, so I did not patch it. Fix it in the *next Claude-Design round* (a 1-line
  href), or ask Claude Design to add an `install_url` field the SPA reads — then it stays
  data-driven like everything else. This is the one dead link on the site.
- **The round-trip is now: edit in Claude Design → only `data.js` regenerates from `site.json`.**
  You never hand-edit data; change the bot, re-run the export, and the site follows. That's the
  "dynamic data" goal met end-to-end.

## 💡 Session idea (Q-0089)

**A `scripts/check_design_contract.py` guard that asserts `botsite/site/app.js` only reads
`window.SBDATA` fields the generator emits.** This session verified it by hand (grep app.js field
accesses vs. the generated shape). When Claude Design ships a new SPA build that reads a *new* field,
`data.js` would silently render it `undefined` and a page breaks with no test failure. A tiny checker
(regex the `.field` accesses in the verbatim `app.js`, diff against `build_prototype_data` keys) turns
that into a CI signal — the design↔data contract becomes *checked*, not hoped. Lane: tooling.

## ⟲ Previous-session review (Q-0102)

The previous run (#1183, creature-game sim) did its job well — it used a simulator to *de-risk before
building*, which is exactly the "balance before build" instinct this project should have. **What it
could have done better:** it left the dev-only `fastapi`/`httpx` install assumption implicit; this
session hit the same wall (botsite tests `importorskip` and silently skip unless you `pip install -r
botsite/requirements.txt`). **System improvement:** the `.session-journal.md` Quick-reference should
carry a one-liner — *"botsite/dashboard tests need `pip install -r botsite/requirements.txt`; they
skip otherwise"* — so a web-touching session doesn't mistake skipped tests for passing ones. (The
generator's contract tests are deliberately stdlib-only so they *do* run in CI — the right split.)

## 📤 Run report

- **Did:** wired the Claude-Design SPA as the bot-site front-end with a live, generated-from-
  `site.json` data layer · **Outcome:** shipped
- **Shipped:** SPA at `/` + dynamic `/data.js` + `site_data.py` generator + one-pipeline export
- **Run type:** `manual · owner-task (website + data wiring)`
- **⚑ Owner decisions needed:** none (front-end + data-delivery confirmed via AskUserQuestion)
- **⚑ Owner manual steps:** Railway redeploys the `botsite` service on merge; the "Add to Discord"
  link needs wiring in the next Claude-Design round (see Suggestions)
- **⚑ Self-initiated:** none (owner-directed; approach choices confirmed)
- **↪ Next:** wire the install URL (Claude-Design round) · optional `check_design_contract.py` guard

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 (web tier only; `site_data.py` never imports `disbot`) |
| New tooling | 1 (`site_data.py` generator + 12 contract tests) |
| Commands wired into the site | 280 unique (from 308, deduped) across 9 areas, 8 games |
| Tests | 104 passing (12 new stdlib contract guards run in CI) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (`check_design_contract.py` design↔data guard) |
