# Active work — moved to one-file-per-claim

> **Status:** `reference` — this single shared ledger was retired on 2026-06-22 (owner decision
> **Q-0195**). Live claims now live as **one file per claim** under
> [`docs/owner/claims/`](claims/README.md).

## Why it moved

The single shared `## Active claims` / `## Recently cleared` lists made every session **append to
the same line**, which a real-`git merge` simulation (`tools/sim/claim_layout_sim.py`) measured at a
**~98% merge-conflict rate** under concurrent sessions. Splitting by *sector* only halved it (and
worsened with concurrency). **One file per claim is structurally conflict-free** — the simulation
confirmed **0% conflicts at every concurrency level** — because two sessions never touch the same
file.

## Where claims live now

- **Read the convention + how-to:** [`docs/owner/claims/README.md`](claims/README.md)
- **List current claims:** `ls docs/owner/claims/`
- **Scan a scope for overlap:** `python3.10 scripts/check_lane_overlap.py <scope> ...`

The mechanics are unchanged (Q-0126: claim before you start; a claim is a soft signal, not a lock) —
only the storage changed from one shared file to one file per claim. The durable record of *merged*
work remains `docs/current-state.md`; there is no "recently cleared" list to maintain (delete your
own claim file at close).
