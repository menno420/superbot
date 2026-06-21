# Session — prune stale active-work.md claims (drift-on-sight)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/dispatch-next`

## What I'm about to do

Resume after the duplicate-work cleanup chat. With every substantial buildable lane
either in-flight (#1213 creature PvP) or owner/review-gated, the genuinely free,
on-theme task is **fixing visible claim-ledger drift** (Q-0166): all six `active-work.md`
"Active claims" had already merged (#1178/#1196/#1220/#1223/#1224 + clever-maxwell's
#1193–#1197), yet sat under Active claims — which feeds **false positives into the
`check_lane_overlap.py` claim scan I just shipped (#1223)**, undermining the very
duplicate-prevention tool.

- Verified each claimed branch is merged (GitHub PR state), then moved all six to
  Recently cleared with PR numbers; Active claims now holds only this lane.

Docs-only; self-merge on green.

## Verification
`python3.10 scripts/check_docs.py --strict`
