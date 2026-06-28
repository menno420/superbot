# 2026-06-28 — Document owner answers + decide the router-vs-durable-home convention

> **Status:** `complete`

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

## What shipped (PR #1522)

- **10 router Q-blocks documented** (append-only, PROPOSED → ANSWERED, answers preserved, `Home:`
  set): Q-0182, Q-0184, Q-0185, Q-0186, Q-0187, Q-0194-rider, Q-0198, Q-0200, Q-0206, Q-0207.
- **Conclusions routed to homes:** creature plan (Q-0187), Pokétwo plan + wild-encounters idea
  (Q-0186), explore-hub plan (Q-0182), mining-grid-encounters idea + mining-hub-redesign plan
  (Q-0198), honcho-memory idea (Q-0184), website-split plan (Q-0185), `helper-policy.md` §2 +
  CLAUDE.md helper rules (Q-0200), CLAUDE.md Working agreement [binding] (Q-0194), `code-quality.yml`
  warn-only stale-claim step (Q-0206), `repo-sector-map.md` [blessed] (Q-0207).
- **New Q-0210** — the router-vs-durable-home decision: router stays the canonical append-only
  Q-block ledger (Q-numbers never move); conclusions route to homes; size managed by **archiving**
  old blocks (reconciliation pass owns it), mirroring `current-state-archive.md`. Recorded in
  `ai-project-workflow.md` §9 + the reconciliation routine; **scaffolded `maintainer-question-router-archive.md`**.
- Verified: `check_docs --strict` ✓ · `check_consistency --strict` ✓ · `check_architecture` 0 errors
  · `check_current_state_ledger --strict` exit 0 (benign newest-merge lag only) · YAML valid.

## 💡 Session idea (Q-0089)

[`router-q-index-generator-2026-06-28.md`](../ideas/router-q-index-generator-2026-06-28.md) — a stdlib
`build_q_index.py` emitting one line per Q (number · title · status · Home · file) over the router +
its archive, so a `Q-0NNN` lookup (~9k refs repo-wide) greps ~215 lines instead of loading the 490 KB
router. The **findability** half of Q-0210's **size** fix. Genuine — it's the friction I hit firsthand
this session (had to slice-read the router to find the open questions).

## ⟲ Previous-session review (Q-0102)

Reviewed [`2026-06-28-feature-completion-assessments.md`](./2026-06-28-feature-completion-assessments.md).
**Did well:** ran the assess→close loop the framework exists for — assessed 3 game units *and* closed a
real surfaced gap (counting's dead leaderboard) in one PR, not just paperwork. **Could improve:** it
surfaced two genuinely **owner-gated** punch-list items (Word Chain mis-classification; counting
XP/coin reward decision) but left them only in the per-unit cert files — where a future session won't
see them unless it opens that exact cert. Per the routing discipline, an owner-gated completion blocker
should **also** become a router DISCUSS Q (or at least the sector `▶ Next [owner]` queue) so it's
discoverable. **System improvement this surfaces:** the same gap that made *this* session necessary —
**ten** DISCUSS Q-blocks had accumulated unanswered because nothing routinely surfaces "open questions
awaiting the owner." A cheap fix: SessionStart (or the empty-fire dispatch) prints the **count of
`PROPOSED` router blocks**, and the feature-completion certs' owner-gated blockers feed the same digest.
Captured the adjacent half (cheap Q-lookup) as today's Q-0089 idea; the digest itself is a natural next
idea/guard.

## ⚑ Self-initiated

None beyond the owner's explicit request. The owner directed this session (document all answers + decide
the durable-home approach); every edit routes a now-answered owner decision or implements the convention
he chose. Q-0210, the CLAUDE.md/helper-policy/CI edits are applied under the Q-0106 live-owner exception
(he answered each via the panel).

