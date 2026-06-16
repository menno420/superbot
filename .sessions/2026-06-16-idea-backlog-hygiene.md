# 2026-06-16 — idea-backlog hygiene (tie off the #995 deferrals) + validate the union fix

> **Status:** `complete` — docs/ideas only (no `disbot/` runtime, no Python). One PR (#1004).

## Arc

Tied off the idea-backlog hygiene I **deferred** out of PR #995 to escape the merge-conflict livelock
— now safe because PR #1003 made `docs/ideas/README.md` auto-merge (`merge=union`). This PR is also the
**first real-world test** of that fix: it appends to the union-protected idea index, which should merge
cleanly even as `main` moves (the same kind of edit that conflicted 3× before #1003).

## Shipped (PR #1004)

- Marked the **subcog→parent-subsystem** idea **SHIPPED (#995)** — re-applied the file Disposition +
  README index update that #995 reverted out to escape the livelock.
- Filed the two captured-in-card ideas as proper indexed idea files:
  - **`cog-declares-its-subsystem`** (Q-0089 from #995) — replace the dashboard's class-name guessing +
    three hand-maintained lists with an authoritative subsystem declaration the scanner reads.
  - **`ledger-dedup-linter`** (Q-0089 from #1003) — flag the duplicate/stale claim & idea lines the
    `union` driver can leave behind (its one accepted downside).

`check_docs --strict` green (both new files reachable; ideas badge 70→72); `check_quality --check-only`
green. No runtime/Python touched.

## Status checklist

- [x] subcog idea → shipped (file + README entry)
- [x] file `cog-declares-its-subsystem` idea + README entry
- [x] file `ledger-dedup-linter` idea + README entry
- [x] `check_docs --strict` green
- [x] session enders + flip card `complete`

## 💡 Session idea (Q-0089)

This session's genuine idea contribution **is** the two idea files filed above (`cog-declares-its-
subsystem` + `ledger-dedup-linter`) — both ideas I believe in, surfaced by the #995/#1003 work and now
properly indexed. A pure-bookkeeping session, so per Q-0089's own bar I'm **not hallucinating a third
filler idea**: the honest observation is that the idea backlog now *grows* friction-free (the union fix
removed the one thing that slowed appends), which makes backlog **drain** — not capture — the live
constraint. That is already captured as `idea-spotlight-verdict-loop` (a drain-rate ledger); no new
idea needed here.

## ⟲ Previous-session review (Q-0102)

Reviewed **`2026-06-16-gitattributes-union-ledger.md`** (#1003 — my prior session). **Did well:** chose
the *root-cause* fix over a fourth round of escape-by-shedding, **verified it before shipping**
(`git merge-file --union` + `git check-attr` proving `union` on the two ledgers and `unspecified`
elsewhere), kept it minimal + zero-contention so the contention-fix couldn't itself livelock, and
documented the caveats + a revert note in the file. **Honest gap it left (by design):** the union
driver's no-dedup downside — which it correctly deferred to an idea rather than scope-creeping the
fix. This session filed that idea (`ledger-dedup-linter`), closing the loop. **System note:** the
union fix + this hygiene pass together demonstrate the intended pattern — fix the *mechanism* (#1003),
then let the *bookkeeping* (this PR) ride the now-frictionless path. Nothing to improve beyond the
already-captured drain-rate concern.

## ♻️ Backlog grooming (Q-0015)

This session **is** a grooming pass: moved the subcog idea to its terminal **shipped** state and routed
two captured-in-card ideas into proper indexed files (capture → filed). The backlog is now accurate for
the #995/#1003 work; the next genuinely-unfiled item is none — the remaining ideas are all indexed.

## Documentation audit (Q-0104)

- All three idea files reachable + indexed; `check_docs --strict` + `check_quality --check-only` green.
- No owner decision (a deferred-hygiene tie-off under Q-0129 self-initiated improvement), so no router
  Q-block. **Ledger untouched (Q-0124):** reconciliation backlog is the routine's job; #1004 unmerged.

## Context delta

- The #995 idea-backlog state is now accurate (subcog = shipped); the two follow-up ideas
  (cog-declares-subsystem, ledger-dedup-linter) are filed + indexed, ready for a future tooling lane.
- This PR confirmed the #1003 `merge=union` fix in practice (an append to the idea index that would
  previously have entered the livelock).
- Still-open non-conflicting slices for a future session: the deferred Paragon/Setup/Hermes parent
  mapping (needs owner intent), the "your authority" pre-auth preview (plan's ready read-only slice),
  and the two newly-filed tooling ideas.
