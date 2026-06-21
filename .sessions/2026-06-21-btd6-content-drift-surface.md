# 2026-06-21 — BTD6: surface same-version data drift (sha-based seed reminder)

> **Status:** `complete`

## Arc
Completes the data-freshness story from the auto-seed work (#1255). Strict Q-0077(b)
auto-seeds only on a **version bump**, and `served_data_drift()` is **version-only** too —
so a **same-version** data edit (e.g. the #1249/#1251 buff windows, still 55.1) neither
auto-seeds NOR warns, silently staying stale on the postgres store. Closed that gap with a
**reminder** (warn-only — honors the owner's strict-(b) "surface, don't auto-write" choice).

## Shipped (PR #1258)
- **`btd6_data_service.content_drift()`** — sha over the canonical JSON (the exact digest
  `seed_postgres_from_files` writes) of every committed file vs the served store; returns the
  changed names, or `None` for the file backend / in sync. Sync, reuses `read_blob` (warmed
  in-memory store) — no DB round-trip.
- Surfaced in the **else** (same-version) branch of both existing drift surfaces:
  `btd6_cog.cog_load` boot log + the `!btd6 status` embed — so no double-warning with the
  version-drift path.
- Tests (file-backend → None / same-version change list / missing served blob); subsystems doc.

## Verification
- `python3.10 scripts/check_quality.py --full` → **all checks passed ✓** (11364 passed).
- `check_architecture --mode strict` → 0 errors.
- New tests green (44 in the data-service suite).

## Decisions made alone
- **Warn-only, in the else branch.** content_drift is a superset of version drift, so I gate
  it on "no version drift" to surface *specifically* the same-version case the version check
  misses — one clear message, never two. No auto-seed (the owner chose strict (b)).
- Sha over canonical JSON (not a DB sha-column query) — sync, no new DB code, and it matches
  the seed digest exactly so it can't false-positive on in-sync data.

## Context delta
- The data-freshness story is now complete + symmetric: **version bump → self-seeds (#1255);
  same-version edit → warns to seed (#1258)**. Both gated on the postgres backend (file can't
  drift). The "in repo ≠ live in prod" lesson is now backed by tooling, not just docs.

## ⟲ Previous-session review
The #1255 (auto-seed) session correctly implemented the owner's strict-(b) decision and was
honest that it leaves same-version edits needing a manual seed — but it left that purely as a
*documented caveat* ("you'll need to remember"). A documented human dependency is still a
silent-failure risk. **Workflow improvement (applied this session):** when a deliberate
decision leaves a known gap, build the cheapest *mitigation* immediately (here: a warning)
rather than relying on operator memory — decision → known gap → mitigation, in the same
breath. #1255 + #1258 together are that loop.

## 💡 Session idea
**Make `!btd6ops seed-data` report *what* it changed.** Now that `content_drift()` gives the
exact changed-file list, the seed command (currently "Upserted N blobs") could pre-compute the
drift and reply "synced N changed file(s): `alchemist.json`, …" — so the operator sees exactly
what the seed applied (and confirms the buff fix landed), instead of a bare count. Tiny, reuses
content_drift, closes the feedback loop. (Captured, not built.)

## 📤 Run report
- **Did:** Added a sha-based same-version data-drift reminder (boot + `!btd6 status`) ·
  **Outcome:** shipped (PR #1258)
- **Shipped:** PR #1258 — `content_drift()` + both drift surfaces + tests + subsystems doc
- **Run type:** `manual` ("continue" → complete the data-freshness story)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** still the one-time **`!btd6ops seed-data`** for the #1249/#1251
  buff windows (same-version; not auto-seeded). After #1258 deploys, `!btd6 status` will now
  *show* that pending drift as a reminder until you seed.
- **⚑ Self-initiated:** yes (Q-0172) — completes the #1255 data-freshness story off the owner's
  "continue"; captured as the prior session's idea.
- **↪ Next:** the seed-data "report what changed" idea (this session's 💡); the alch
  attack-speed-buff modeling (#1251 idea); or the current-state ▶ ungated lane.
