# Claim remote-visibility scan — make claims travel without waiting for a merge

> **Status:** `ideas` — session idea (2026-07-08, Q-0089, grooming wave-1 lane C, PR #1845).
> **Subsystem:** none (agent workflow / parallel-session safety, S3/S5 tooling).
> Not a plan, not approval.

## The gap, observed live this session

This session ran as lane C of a deliberate 3-lane parallel wave. At orientation, lanes A and B
were known to be running *right now* — yet they were invisible to every claim channel:

- `ls docs/owner/claims/` (and `check_lane_overlap.py`, which reads the same local dir —
  `scripts/check_lane_overlap.py:47`) sees only claims **merged to the checked-out tree**.
  A claim file committed on a sibling's un-merged branch never appears there; in practice the
  claims dir on `main` is almost always just `README.md`, because claims are deleted at close
  before the PR merges.
- The open-PR scan works only **after** the sibling's first push + PR open. Two lanes starting
  within the same few minutes see nothing of each other — the exact window Q-0189 (open fast)
  shrinks but cannot close.

So the *tool* half of the Q-0126 protocol under-delivers: the claim's real transport today is
"the open PR," and the pre-PR window is uncovered.

## The idea

1. **`check_lane_overlap.py --remote`:** `git fetch origin` + enumerate `origin/claude/*` (and
   `bot/*`) branches whose tip is newer than N days (`git for-each-ref --sort=-committerdate`),
   read each branch's `docs/owner/claims/*.md` additions vs `origin/main` (`git diff --name-only
   origin/main...<ref>` + `git show <ref>:<file>`), and fold those claims into the overlap check.
   A sibling that has pushed its born-red first commit becomes visible **before** its PR exists
   and **without** any local checkout of its branch. Stdlib + git only; warn-first; disposable
   (Q-0105).
2. **Protocol line (docs):** in a known-parallel wave, re-run the overlap scan **once more right
   after your own claim push** — the cheap mitigation for the simultaneous-start race (if both
   lanes do this, the second pusher always sees the first).

## Why it's worth having

The owner explicitly runs multi-lane waves now (this campaign, the dispatch fleet, the rebuild's
worker fan-outs), and the #1221 duplicate-PR lesson already cost real work once. This closes the
remaining visibility gap at the claim's *native* layer (git refs) instead of adding a new shared
file that would re-introduce the Q-0195 conflict point.

**Dedup-checked:** `bug-book-claimed-signal-2026-06-19.md` (bug-book pickups unclaimed — different
surface), `ci-cost-and-duplicate-work-prevention-2026-06-14.md` (the claim ledger's origin — no
remote-visibility mechanism), `ultracode-worker-pr-scope-guard-2026-06-23.md` (post-work diff
audit, not pre-work visibility). `claim_layout_sim.py` measured storage-layout conflicts, not
propagation latency.
