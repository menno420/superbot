# Session 2026-07-09 — KL-6 companion: exporter telemetry family + kit-lab console lane

> **Status:** `complete` — PR #1883, the superbot-side half of kit-lab band
> KL-6 (the kit-side half is substrate-kit PR #18).

## What I did

Superbot-side companion to substrate-kit PR #18 (kit-lab founding plan §7.3,
band KL-6 — the exporter lives here, not in the kit):

- **Exporter `telemetry` family** (`scripts/export_dashboard_data.py`): new
  `parse_telemetry()` reads `telemetry/model-usage.jsonl` (the PL-004/Q-0248
  per-session record) into the full payload + the console feed.
  Field-whitelisted by construction (`CONSOLE_TELEMETRY_FIELDS` +
  `TELEMETRY_OUTCOME_FIELDS` — the site.json posture); tolerant by contract
  (a malformed line/row is skipped or nulled, never fatal — one bad append
  must not blank the lane); capped to the newest 200 rows.
  `CONSOLE_TOPLEVEL_KEYS` gains `telemetry`.
- **`telemetry/model-usage.jsonl` seeded** (+ `telemetry/README.md`):
  superbot is not an adopted kit install, so rows are **hand-authored** at
  session close against the kit's canonical schema (plan §4.2/§5.2) until it
  adopts; first row = this session. `telemetry/*.jsonl merge=union` added to
  `.gitattributes` (same append-only rationale as the existing ledger
  entries).
- **Console lane flip** (`botsite/console/console.js`): the declared "Model
  & spend telemetry" lane renders **real rows** when `data.telemetry` is
  non-empty (model/effort/task-class badges, null-tolerated `tokens_out` per
  KF-9) and falls back to the declared pending form when empty — the
  honest-lane rule unchanged. Contract string corrected to the `.jsonl`
  source (the kit plan's D-10 refinement: the lane binds to record shape,
  not file encoding).
- **New declared lane "Kit lab — benchmarks & guards"** with its exact §7.3
  contract `bench/results/*/index.json → [{date, kit_version, family,
  verdict, headline}]` — declared, NOT faked: the kit's results indexes ride
  the kit's owner-blessing bench PR (substrate-kit #17), and the cross-repo
  read waits on the kit going public (P11) or the read-only PAT (P13).
- `dashboard.json` + `console.json` regenerated (site.json/data.js
  deliberately untouched — no site-family change; the BUG-0022 desync class
  avoided). Exporter tests extended (+3: whitelist/tolerance, missing-file +
  cap, console-subset telemetry shape).

**Gates:** `check_quality.py --check-only` green · mypy clean (881 files) ·
`tests/unit/scripts/` + `tests/unit/botsite/` 1220 passed, 4 skipped ·
`check_dashboard_data` OK · `check_generated_artifacts_fresh` OK (4 fresh) ·
`node --check` on console.js. Full suite = CI (auto-merge armed on green).

## Context delta

- **Needed but not pointed to:** the fact that the console *UI* now renders
  in TWO places — superbot's botsite service (`botsite/console/console.js`)
  AND the websites repo's dashboard service (reads the same committed
  `console.json` via raw GitHub) — lives only in websites'
  `docs/current-state.md`; nothing superbot-side mentions the second
  consumer of `console.json`'s shape.
- **Pointed to but didn't need:** nothing notable.
- **Discovered by hand:** `check_generated_artifacts_fresh` ignores volatile
  meta, so regenerating only the two changed artifacts is safe and
  sufficient; the console subset raises on non-whitelisted keys at build
  time (so the new family HAD to be added to the frozenset first).
- **Decisions made alone:** telemetry rows enter `build_data()`'s full
  payload (so `dashboard.json` carries the family too) rather than being
  read privately by the console subset — the "single producer, subsets
  whitelist" architecture; the 200-row export cap; the kit-lab lane ships
  declared-only until the kit feed is readable.

## 🛠 Friction → guard

Two parallel PRs (this one + substrate-kit #17) both append one telemetry
row at EOF — a guaranteed conflict class on an append-only feed. Shipped the
guard: `telemetry/*.jsonl merge=union` in `.gitattributes` (checker-free,
standard git feature, same pattern as the existing ledger entries). Kit-side
twin shipped in substrate-kit #18.

## 💡 Session idea

**A console.json shape contract shared with the websites repo:** websites'
dashboard now renders superbot's committed `console.json`, but nothing pins
the shape both sides assume — a renamed family here silently blanks a page
there. Cheapest durable form: a `botsite/data/console.schema.json` (or a
listed-fields doc block) that superbot's exporter test asserts against and
websites' data_source cites by URL — one source of truth for a two-repo
contract, exactly the kit's "contract string on the lane" instinct applied
to the feed itself. Dedup-grepped `docs/ideas/` (no console/feed-contract
idea exists).

## ⟲ Previous-session review (remove-intree-kit, #1882)

Genuinely clean execution of a named chore: redundancy verified before
deleting (repo-wide reference grep + post-deletion collection count), the
deletion flagged prominently with its reversal command, and history left in
place rather than rewritten — the right instincts for a 101-file deletion.
One improvement it surfaces: it verified nothing *imports* the deleted tree
but didn't sweep for *docs that route readers into it* (orientation-route
links to `substrate-kit/` paths would now 404 for an agent) — a
"pointer-sweep after deletion" line in the deletion checklist would close
that class. Not filler: this session's own change relied on finding the
kit's living docs in the graduated repo instead.

## 📤 Run report

- **Did:** exporter `telemetry` family + real console telemetry lane + declared kit-lab lane (kit-lab KL-6, superbot half) · **Outcome:** shipped
- **Shipped:** #1883 — exporter telemetry family, console lane flip + new declared kit-lab lane, telemetry/ seeded, artifacts regenerated, tests +3
- **Run type:** `manual` (coordinator-dispatched kit-lab band work)
- **⚑ Owner decisions needed:** none new here (the kit-lab band's 👤 P5/P11/P13 items are ledgered in substrate-kit's current-state)
- **⚑ Owner manual steps:** none superbot-side
- **⚑ Self-initiated:** none (band KL-6 is planned work — kit `docs/planning/kit-lab-founding-plan-2026-07-07.md` §7.3/§10)
- **↪ Next:** kit-lab lane flips real once substrate-kit #17 is blessed AND P11-or-P13 makes the kit's `bench/results/*/index.json` readable; superbot sessions append their hand-authored telemetry row at close (`telemetry/README.md`)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1883, auto-merge on green) |
| CI-red rounds | 0 (born-red card gate only) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (console.json shape contract) |
| Ideas groomed | 0 (companion-PR session; grooming capacity went to the kit-side band work) |
