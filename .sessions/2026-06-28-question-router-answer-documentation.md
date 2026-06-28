# 2026-06-28 — Document owner answers + decide the router-vs-durable-home convention

> **Status:** `in-progress`

**Run type:** owner-directed (in-chat)

## What this run is doing

The owner ran an open-question sweep via the panel and answered ten open router DISCUSS/DECIDE
Q-blocks (Q-0182, Q-0184, Q-0185, Q-0186, Q-0187, Q-0194-rider, Q-0198, Q-0200, Q-0206, Q-0207).
This session:

1. **Documents every answer** in its Q-block (preserve the answer, flip status PROPOSED → ANSWERED,
   set the `Home:` routing) — append-only, no renumber (router §9 / Q-0060).
2. **Routes each durable conclusion to its real home** (the creature/Pokétwo/explore-hub plans,
   the mining-grid-encounters idea + mining-hub-redesign plan, the honcho-memory idea, the
   website-split plan, `helper-policy.md`, `.claude/CLAUDE.md`).
3. **Answers the owner's meta-question** — should answers get a more durable home, or stay in the
   router given Q-number cross-references? — as a new decision (Q-0210) + `ai-project-workflow.md` §9.

## Evidence behind the convention decision (Q-0210)

- Router is **491 KB / 7,619 lines / 215 Q-blocks** and exceeds the file-read limit (real friction).
- **9,084 `Q-0XXX` references across 1,307 files** — the Q-number is the repo's stable cross-ref key.
- **Only ONE anchor-style link (`#q-0017`) exists repo-wide** — every other reference is plain text,
  so moving a Q-block to an archive file keeps it grep-resolvable; physically re-homing answers to
  scattered new docs would orphan the Q-number anchor.

→ Best option: **router stays the canonical, append-only Q-block ledger (Q-numbers never move);
conclusions keep routing to homes (already the convention); size is managed by archiving OLD
answered+routed blocks to `maintainer-question-router-archive.md`, exactly mirroring the
`current-state.md`/`current-state-archive.md` split — driven by the reconciliation pass.** NOT a
wholesale re-route.

_(Enders — idea / prev-session review / doc audit — appended before the card flips to `complete`.)_
