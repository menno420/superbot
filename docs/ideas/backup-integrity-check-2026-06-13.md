# Idea: backup dump integrity check

> **Status:** `idea` — captured 2026-06-13 (executor run, Q-0089).
> **Area:** operations / backup posture.

## The idea

After `backup-db.yml` produces the `.sql.gz`, add a verification step that confirms the
dump contains a minimum number of `CREATE TABLE` statements:

```bash
TABLE_COUNT=$(zcat "$FILENAME" | grep -c "^CREATE TABLE" || true)
echo "Tables found in dump: $TABLE_COUNT"
if [ "$TABLE_COUNT" -lt 10 ]; then
  echo "::error::Dump integrity check failed — only $TABLE_COUNT CREATE TABLE statements found (expected ≥10)"
  exit 1
fi
```

The threshold (10) is a conservative lower bound; the real DB has far more tables. Update it
after the first successful run by reading the actual count from the artifact.

## Why it's worth having

The current workflow exits 0 and uploads the file even if `pg_dump` produced an empty or
near-empty dump due to permission errors, wrong URL, or a truncated connection. The upload
step (`if-no-files-found: error`) only checks that the file exists and is non-zero — a
1 KB file with a pg_dump error header passes that gate. The integrity check catches
this class of silent failure before the artifact is trusted as a real backup.

This is the Q-0105 "confirm tooling output before trusting it" posture applied to the
backup workflow itself: an unverified backup artifact is not a backup.

## Implementation

Small: one `bash` step after the upload step in `.github/workflows/backup-db.yml`.
The step should run *before* the upload so a bad dump never occupies an artifact slot.
Reorder: dump → integrity check → upload.

The threshold is the only value to decide; start conservative (10) and bump it to
`actual_count - 10%` after the first verified run.

## Dedup

No existing idea in `docs/ideas/` covers this. The backup posture itself is band slot 3
(shipped #769); this is a follow-on hardening step for that posture, not a duplicate.
