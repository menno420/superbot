# 2026-06-21 — BTD6: seed-data reports which files it changed

> **Status:** `in-progress`

## Arc
Final completion of the BTD6 data-freshness story (#1235/#1249/#1251/#1255/#1258). The
`!btd6ops seed-data` receipt showed only a blob **count** ("Upserted 64 blobs"). Now that
`content_drift()` (PR #1258) gives the exact changed-file list, the receipt can name what the
seed **applied** — so the operator *confirms* e.g. the buff fix landed, not just that something
ran. This is the operator-feedback close of the same `seed-data` step the owner still runs once
for the same-version buff data.

## Shipped (PR #1259)
- `btd6_ops_cog._seed_embed()` — capture `content_drift()` **before** seeding, then add an
  "**Applied N changed file(s):** …" line to the receipt (postgres only; absent for the file
  backend / an in-sync store, so the message is unchanged there). Truncates to 8 names + "+N more".
- Test: `test_seed_embed_reports_changed_files` (existing count test still passes — file backend
  → no changed line).

## Verification
- `python3.10 scripts/check_quality.py --full` (run at close).
