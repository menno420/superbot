# 2026-07-10 — Overnight shift B: `check_lane_overlap.py --remote` + docs hygiene

> **Status:** `complete`
> **Branch:** `claude/shift-b-lane-overlap-remote` · PR **#1919** (born-red → auto-merge armed)

## What happened

Session B of the overnight maintenance shift (shift-plan items **K2 + Q1 + Q3**; Session A
owns K1/#1917 — verified no file overlap; worked from a worktree because Session A is active
in the main clone). Safe-merge class throughout: tooling + docs only, zero `disbot/` runtime.

1. **K2 — `check_lane_overlap.py --remote`** (`--remote-days`, `--no-fetch`), shipping
   `docs/ideas/claim-remote-visibility-scan-2026-07-08.md` (re-badged SHIPPED + index):
   enumerates recent un-merged `origin/claude/*` / `origin/bot/*` tips and folds their
   `docs/owner/claims/` files (vs `origin/main`) into the overlap scan — a sibling's
   born-red first push is visible **before its PR exists**. Implementation deviates from
   the idea sketch on purpose: **tip-state `ls-tree` compare instead of
   `git diff origin/main...ref`** — live testing in this container (a **shallow clone**)
   showed the diff approach dies with `no merge base` on 32/34 recent refs; tip-state needs
   only the tip object and matches the claim lifecycle (created at open, deleted at close).
   Own branch skipped; all git/network failures degrade to warnings + local-only results.
   +5 unit tests (18 total pass); Q-0105 provenance header (unverified tier).
   **Ground-truth verified live:** from the main clone, this session's own pushed branch
   surfaced as a REMOTE CLAIM hit on `scripts/check_lane_overlap.py`; from the worktree the
   own-branch skip held; `--strict` exits 1 on the hit.
2. **Q1** — Recently-shipped trimmed 22 → 20 (`trim_recently_shipped.py --apply`; floor
   pointer recomputed to #1799; #1791-band + #1784-band → archive). #1919 ledger entry added.
3. **Q3** — journal ⚡ Quick reference row: fresh container → `python3.10 -m pip install -r
   requirements-dev.txt` before trusting a checker red (Q-0194; the scout pass burned a
   cycle on exactly that false-red).
4. Protocol line in `docs/owner/claims/README.md`: use `--remote` in a known-parallel wave
   and re-run the scan once right after your own claim push (second pusher always sees the
   first).

## Verification

- `python3.10 scripts/check_quality.py --full` (with `set -o pipefail`): **All checks
  passed ✓** — 13,842 passed, 49 skipped, 2 xfailed.
- `python3.10 scripts/check_architecture.py --mode strict`: exit 0 (0 errors; known warns).
- `python3.10 scripts/check_docs.py --strict`: all checks passed ✓ — Recently-shipped 20/20
  (the shift-plan's one soft warning cleared).
- `python3.10 scripts/check_current_state_ledger.py --strict`: exit 0 (only benign
  newest-merge lag ≤ #1916; recon #1920 is routine-owned, not run here per Q-0124).

⚑ Self-initiated: none — all three items came from the owner-directed shift plan (K2, Q1,
Q3); the ls-tree-over-diff implementation change is a Q-0014 better-path call, noted above.
Telemetry `task_class`: recorded as `test writing` (closest of the 8 Q-0248 classes for a
new checker capability + tests — the taxonomy has no tooling/checker class; decide-and-flag).

## 💡 Session idea

**`scripts/open_lane.py` — one-command session-open ritual** (dedup-grepped `docs/ideas/` +
`scripts/`: no existing open-lane/session-bootstrap helper). The Q-0126/Q-0133/Q-0189 open
ritual is currently 5 manual steps (overlap scan → claim file → born-red card → branch →
push) that every session re-derives from prose and sometimes fumbles (late PR opens, missed
claims). A small script — `open_lane.py <slug> <scope>...` — could run
`check_lane_overlap --remote`, refuse on a hit, then generate the claim file + born-red card
from templates and print the push/PR commands. It would also *mechanically* enforce the new
"re-scan right after your own claim push" protocol line instead of exhorting it ("enforce,
don't exhort", Q-0132). Script-tier, so free to ship per Q-0194 ownership split.

## ⟲ Previous-session review

Previous relevant session: the overnight **scout pass** that produced the shift plan (plus
the #1915/#1916 night-prep pair before it). Genuinely strong: full checker baseline table
with honest "no reproducible in-tree red" disposition, and per-item risk/verification lines
made this session near-zero-orientation. Two things it surfaced: (1) its K2 sketch
prescribed `git diff origin/main...ref`, which live testing showed fails on the shallow
clones agent containers use — plans' implementation sketches are guidance to verify against
the real environment, exactly as CLAUDE.md says of prompts; (2) it burned a cycle on the
fresh-container false-red yet routed the fix as a plan item rather than shipping the
journal row itself (scout scope discipline — defensible, but the Q-0194 "before the session
ends" bar arguably wanted the one-line guard shipped in-pass). **Concrete workflow
improvement:** shift/scout plan templates should carry the dev-tools bootstrap line in
their own preamble ("run `python3.10 -m pip install -r requirements-dev.txt` before the
baseline table") so the false-red can't recur even before the journal row is read — done
for the journal this session; the plan-template half is the open_lane/templates idea above.

## Docs audit (Q-0104)

Ledger strict: exit 0. Docs strict: all passed (20/20 ratchet). New owner decisions this
session: none (no owner interaction — overnight autonomous). Idea lifecycle: one idea
SHIPPED (claim-remote-visibility), one new idea recorded above (in-card per Q-0089; will be
promoted to a file if a later session picks it up). Nothing captured only in chat that
belongs in a durable home.
