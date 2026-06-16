# 2026-06-16 — idea-backlog hygiene (tie off the #995 deferrals) + validate the union fix

> **Status:** `in-progress` — born-red per Q-0133; flipped to `complete` as the deliberate
> final step. Docs/ideas only (no `disbot/` runtime, no Python).

## What I'm about to do

Tie off the idea-backlog hygiene I **deferred** out of PR #995 to escape the merge-conflict livelock —
now safe and contention-free because PR #1003 made `docs/ideas/README.md` auto-merge (`merge=union`).
This PR is also the **first real-world test** of that fix: appending to the union-protected idea index
should merge cleanly even as `main` moves.

- Mark the **subcog→parent-subsystem** idea SHIPPED (#995) — file Disposition + README entry (the
  edits #995 reverted out to escape the livelock).
- File the two captured-in-card ideas as proper indexed idea files:
  - **cogs declare their subsystem** (Q-0089 from #995) — replace the dashboard's class-name guessing
    + 3 hand-maintained lists with an authoritative declaration.
  - **ledger dedup linter** (Q-0089 from #1003) — flag duplicate/stale claim/idea lines the union
    driver can leave behind.

## Status checklist

- [ ] subcog idea → shipped (file + README entry)
- [ ] file `cog-declares-its-subsystem` idea + README entry
- [ ] file `ledger-dedup-linter` idea + README entry
- [ ] `check_docs --strict` green (all idea files reachable)
- [ ] session enders + flip card `complete`
