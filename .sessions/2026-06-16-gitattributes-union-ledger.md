# 2026-06-16 — fix the ledger-file merge-conflict livelock (.gitattributes merge=union)

> **Status:** `complete` — config + card only (no `disbot/` runtime, no Python). One PR (#1003).

## Arc

"Continue from where you left off." The thread I was on was a **merge-conflict livelock**: PR #995
hit 3× consecutive conflicts because the append-only coordination ledgers (`docs/owner/active-work.md`,
`docs/ideas/README.md`) conflict whenever two parallel sessions both add a line, and `main` was
merging entries faster than my merge→verify→push cycle could land. I escaped #995 by *shedding* my
edits to those files; this session fixes the **root cause** so no future session has to.

`main` had calmed (merges ~5–7 min apart vs the ~1–2 min control-panel burst), so it was safe to ship.

## Shipped (PR #1003)

- **`.gitattributes`** — a git **`merge=union`** driver for the two ledger files. On a conflicting
  hunk, union keeps **both** sides' lines (no markers, exit 0) instead of failing — exactly right for
  append-only lists. **No convention change** (sessions still append the same way); only git's *merge
  resolution* for those two paths changes.
- **Verified before shipping** (`git merge-file --union`): two sides each prepending a different claim
  → both kept, exit 0; the same case *without* union → exit 1 (conflict). Post-commit sanity:
  `git check-attr merge` reports `union` for both ledgers and `unspecified` for `current-state.md`
  (only the two intended files are affected).
- **Caveats documented in the file:** union never deletes (a removed claim on one side survives →
  prune it, already allowed) and near-identical concurrent adds duplicate (visible/prunable).
  Deliberately **not** applied to files where order/uniqueness matters (router Q-numbers,
  `current-state.md` prose).

Complements Q-0154's `conflict-guard`: that *detects* conflicts; this *prevents* the common class.
Touched **only** `.gitattributes` + this card — zero contended-file edits, so the fix couldn't itself
livelock.

## Status checklist

- [x] `merge=union` for active-work.md + ideas/README.md in `.gitattributes` (with rationale + caveats)
- [x] sanity: `git check-attr merge` → `union` for both; `unspecified` for a control file
- [x] `check_quality --check-only` (docs gate) green
- [x] session enders + flip card `complete`

## 💡 Session idea (Q-0089)

**Ledger dedup linter.** The union driver's one downside is that it can leave **duplicate or stale**
lines (a claim removed on one side survives; near-identical concurrent adds both land). A tiny stdlib
`scripts/check_ledger_hygiene.py` (or a `check_docs` sub-rule) that flags duplicate claim branches in
`active-work.md` and duplicate idea-file links in `ideas/README.md` would keep the now-auto-merged
ledgers clean — the natural companion to this fix. Decided-lane, small, disposable (Q-0105). *(Filed
in this card only; once #1003 lands, `ideas/README.md` is union-protected so the standalone idea file
+ index entry can be added contention-free next session.)*

## ⟲ Previous-session review (Q-0102)

Reviewed **`2026-06-16-dashboard-subcog-subsystem-map.md`** (#995 — my own prior session). **Did
well under pressure:** when the 3× conflict livelock hit, it diagnosed the cause correctly (append-only
ledger contention + a merge cycle slower than `main`'s cadence) and broke out cleanly by *shedding the
contended-file footprint* rather than fighting the merge indefinitely — the feature shipped intact.
**What it could not do (and shouldn't have to):** it treated the livelock as a one-off to *escape*,
deferring the docs hygiene as collateral. The better systemic response — *fix the merge semantics so
the class of conflict can't recur* — is what this session did. **System improvement realised:** the
"shed footprint to escape" tactic is a band-aid that costs every session its docs hygiene; `merge=union`
is the root fix. The remaining gap: the deferred #995 idea-backlog hygiene (subcog → shipped, the
cog-declares idea file) still needs re-applying — now contention-free once #1003 lands.

## ♻️ Backlog grooming (Q-0015)

Config-only session, so no idea moved this PR — but this fix is **grooming infrastructure**: it makes
the idea backlog (`ideas/README.md`) auto-merge, so the standing grooming/idea-capture enders stop
generating conflicts. The immediate beneficiary is the deferred #995 hygiene (flagged above), which a
next session can now land without the livelock.

## Documentation audit (Q-0104)

- The fix self-documents (rationale + caveats + Q-0105 revert note inside `.gitattributes`) and is
  recorded here. `check_quality --check-only` + `check_docs` green. No router Q-block: `.gitattributes`
  is repo git-config, not CLAUDE.md/`.claude/` executable config, and the change is contained +
  reversible (a contained tooling fix the working agreement says to just do).
- **Ledger untouched (Q-0124):** reconciliation backlog is the routine's job; #1003 isn't merged yet.

## Context delta

- `docs/owner/active-work.md` and `docs/ideas/README.md` now **auto-merge** (`merge=union`) — parallel
  sessions appending claims/idea entries no longer conflict. If you see a duplicate/stale line there,
  it's the union driver's expected residue — just prune it (the convention already allows pruning).
- The control panel is complete in `main` (control API read #989 + write #993 + OAuth/editors #996),
  dormant until `CONTROL_API_TOKEN` + the OAuth secret are set on both Railway services.
- Deferred (now contention-free to pick up): the #995 idea-backlog hygiene + the `cog-declares-subsystem`
  and `ledger-dedup-linter` idea files.
