# Session — 2026-06-25 · Project Moon — Limbus Sinner literary origins

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.

## What this run did

Empty-fire dispatch → advanced the S1 ▶ Project Moon program. PR 1 (#1453) shipped the standalone Limbus
knowledge domain, but each of the 12 Sinners carried only a generic description ("one of the twelve fixed
roster Sinners"). This run adds the **defining structural/lore fact** for each Sinner — its **canonical
literary origin** (the work + author each Limbus Sinner is drawn from) — as a provenanced
`literary_origin` field, surfaced in the browse detail card + a new "Origins" cross-reference view.

**PR #1456 — Limbus Sinner literary origins (Slice A lore depth).**
- **Data** (`disbot/data/projmoon/limbus/sinners.json`): each of the 12 Sinners gains a
  `literary_origin: {work, author}` (Yi Sang→Yi Sang's poetry, Faust→Goethe, Don Quixote→Cervantes,
  Ryōshū→Akutagawa's *Hell Screen*, Meursault→Camus' *The Stranger*, Hong Lu→*Dream of the Red Chamber*,
  Heathcliff→*Wuthering Heights*, Ishmael→*Moby-Dick*, Rodion→Dostoevsky's *Crime and Punishment*,
  Sinclair→Hesse's *Demian*, Outis→Homer's *Odyssey*, Gregor→Kafka's *Metamorphosis*) plus a one-line
  real description each; `data_version` bumped; README provenance updated (source literature noted).
- **Service** (`projmoon_data_service.py`): `literary_origin` added to `_EXTRA_FIELDS["sinner"]` with
  shape validation (must be a `{work, author}` mapping, both non-empty); a typed `sinner_origins()`
  accessor + `SinnerOrigin` dataclass returns the roster-ordered cross-reference.
- **Surface** (`views/projmoon/browse.py` + `project_moon_cog.py`): the detail card renders a "Literary
  origin" line; a new `build_origins_embed()` lists all 12 ↔ their source work, reachable via a 📖
  **Origins** browse-panel button and `!pm origins` (aliases `origin`/`literary`).
- **Tests:** +7 (data: every-Sinner-has-origin, accessor full-roster + order, malformed-origin rejected;
  cog/view: detail card shows origin, origins embed lists all 12, `!pm origins` command).

Read-only, offline, no DB / no AI hot-path change (the gated AI grounding path stays PR 2).

## Verification
- `check_quality.py --full` GREEN (12499+ passed; the 4 generated-artifact tests went red on the new
  `origins` command → regenerated via `scripts/export_dashboard_data.py`, re-confirmed green) ·
  `check_architecture --mode strict` exit 0 (pre-existing rank_view WARN only) · `--check-only` all
  green (black/isort/ruff/check_docs/check_consistency). One ruff COM812 + a black collapse on the new
  button were fixed (multiline + trailing comma, matching the sibling buttons).

## Deferred → PR 2 (needs live-bot / Q-0086 walk)
The AI grounding path (`AITask.PROJMOON_ANSWER` + `projmoon_context_service` wired into
`natural_language_stage.py`) stays the next slice — it touches the gated AI hot-path (faithfulness
guard, deterministic floors) and wants a runtime walk; building it offline-byte-identical is feasible
but the verification belongs to the owner's walk, so I did not force it this run. The `has_limbus_context`
detector is already complete (Sinner names present, ambiguous ones deliberately excluded) — PR 2 reuses
it as-is.

## 💡 Session idea (Q-0089)
*A committed-data ↔ keyword-detector coverage guard for knowledge domains.* The Limbus
`literary_origin` data and the `has_limbus_context` keyword list both enumerate the same 12 Sinner names
by hand, in two files, with no link — exactly the drift class BTD6 hit repeatedly (a new entity in the
data, never added to the router keywords, so it never grounds). A tiny disposable check —
`check_knowledge_domain_keywords.py` — could assert that every *distinctive* canonical name in
`disbot/data/projmoon/limbus/*.json` (and the BTD6 dataset) is reachable by its domain's
`has_*_context` detector (directly or via the resolver), flagging a data entity the router will never
route. It turns "remember to also add it to keywords" into a CI invariant, and it generalises across the
`KnowledgeDomain` seam the program is heading toward. (Genuinely useful, tied to today's two-list edit —
not filler.)

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-25 setup-wizard PR 3a) did its best work in *disposition discipline*: retiring 7
dead wizard sections by judging each against the plan's "does this step do real work?" rubric, and
correctly splitting the contained offline half (PR 3a) from the live-bot half (PR 3b) instead of
half-doing both. What it could have done better: nothing major — but its own Q-0102 note nailed a real
gap, that the ▶ Next handoff mixes offline-buildable and needs-live-bot startables with no tag, and an
autonomous run only learns which is which by spelunking the plan. **This run is direct evidence:** I
spent a chunk of orient-time discovering that PR 3b (setup) *and* Project Moon PR 2 *and* botsite cutover
are all needs-live-bot/owner-gated, and only the data-depth slice was cleanly offline. **System
improvement it surfaces (carrying the prior note forward into a concrete proposal):** make the
`offline` / `needs-live-bot` / `owner-gated` tag a **convention on every ▶ Next startable** in the
per-sector `current-state/*` files, and teach `scripts/dispatch_menu.py --unattended` to read it directly
rather than re-deriving fit from roadmap prose (its current `🟢/🟡/🔵` inference was close but listed a
stale "P1-1 BTD6 eval cases" lane whose offline half already shipped). That would cut every autonomous
run's orient cost. Worth a router DISCUSS block if it recurs once more.

## Doc audit (Q-0104)
Ledger in sync (`check_current_state_ledger --strict` green; the #1442–#1455 merges newer than the #1441
marker are benign newest-merge lag, Q-0166). S1 sector ▶ Project Moon bullet + the plan progress banner
de-staled to this slice. No owner decision this run (executes the owner-greenlit Q-0192 program along its
stated Slice A lore arc). `check_docs --strict` + `check_consistency` green. Claim file deleted at close.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** **PR #1456** — Project Moon Limbus Sinner `literary_origin` data + `sinner_origins()`
  accessor + the `!pm origins` / Origins-button cross-reference surface; +7 tests; dashboard data
  regenerated; S1 sector + plan banner de-staled.
- **⚑ Self-initiated:** none — this is the S1 ▶ Project Moon program (owner-directed Q-0192), advanced
  along its own Slice A lore arc via an empty-fire dispatch.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (data + read-only surface; merge auto-deploys; no seed/data step).
- **Bug-book:** none fixed (BUG-0009 newest-towers data-gated, BUG-0011 needs VPS repro, BUG-0019 #1
  awaits an owner behavior decision — all stay OPEN).
