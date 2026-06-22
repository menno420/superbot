# 2026-06-22 — Allow read-only network probes (curl) + claim-ledger drift prune

> **Status:** `in-progress`

## What I'm about to do
Owner-directed in-session change: move `curl` from the permissions `ask` list to `allow` in
`.claude/settings.json` (plus the `timeout` wrapper) so read-only network probes — e.g. the
`timeout 15 curl -sS -o /dev/null …` wiki-feasibility check — no longer prompt. Destructive /
other-network commands (`wget`, `docker`, `railway`, `psql`, `pg_dump`, `pg_restore`, `rm -r`,
force-push) stay gated in `ask`. Also prune one stale `active-work.md` claim (BUG-0023, PR #1272
already merged — drift-on-sight, Q-0166).

Owner-directed (Q-0106 in-session exception — the owner is the live reviewer for executable-config
edits). Q-0191: owner-directed → merge immediately on green.
