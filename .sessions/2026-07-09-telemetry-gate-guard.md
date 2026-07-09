# 2026-07-09 — telemetry-gate-guard

> **Status:** `complete` — PR #1894; guard shipped, tests green, own telemetry row appended.

**Intent:** Owner-directed (fleet-review coordinator, 2026-07-09, finding #3 of the superbot kit-handling assessment): the telemetry-append rule (`telemetry/README.md`) is exhortative and already leaking — 3 rows in `telemetry/model-usage.jsonl` vs ≥4 sessions carded since the lane shipped (#1884). Per Q-0194 (friction → guard, "enforce, don't exhort" Q-0132), extend `scripts/check_session_gate.py` so a PR that **adds** a `.sessions/` card dated ≥ 2026-07-09 must also append ≥1 row to `telemetry/model-usage.jsonl` in the same PR. Engage-only-on-card-adding shape, so routine/workflow PRs never deadlock; date floor avoids retroactive redness on older cards.

## What shipped (PR #1894)

- `scripts/check_session_gate.py` — telemetry-append guard in the merge-gate path:
  `_card_date` / `telemetry_required_cards` (ADDED cards only, filename date ≥ 2026-07-09;
  undated filenames skipped fail-open) + `telemetry_rows_added` (`git diff --numstat` on
  `telemetry/model-usage.jsonl`; CI = base..head, local = `origin/main...HEAD` + working
  tree; `None` on git failure = fail-open, same bias as the card scan). A missing row holds
  the merge with an actionable message; both holds (born-red + telemetry) print together.
  Q-0105 provenance + kill-switch header on the guard block. The `--require-ready-card`
  Codex-trigger path is untouched.
- `tests/unit/scripts/test_check_session_gate.py` — 9 new tests (date parse, floor filter,
  held/pass/fail-open/exempt-old/exempt-modified/both-holds, plus a real-git end-to-end
  round trip); hardened `test_main_ready_card_passes` to pin `added_session_cards` (it was
  reading live repo state, which the new code path would have made branch-dependent flaky).
- `telemetry/model-usage.jsonl` — this session's own row (self-consistency: this PR adds a
  card, so the guard applies to itself; `task_class: runtime bugfix`).
- `telemetry/README.md` — one enforcement note pointing at the guard.

**Verified against ground truth (Q-0105):** both directions exercised live — committed
diff without the row → `MERGE HELD — telemetry row missing` (exit 1); with the row in the
tree → only the born-red hold remains. Full suite: 13837 passed / 49 skipped / 2 xfailed;
`check_architecture --mode strict` clean (pre-existing WARNs only);
`check_quality.py --full` all green.

## Session enders

- **⚑ Self-initiated:** none — owner-directed via the fleet-review coordinator (2026-07-09
  fleet review, superbot finding #3); the only judgment calls were the ADDED-only + date-floor
  engage shape and the `runtime bugfix` task class, both flagged in the PR body.
- **💡 Session idea:** the guard enforces *presence*, not *validity* — a malformed JSON line,
  a wrong `task_class`, or a schema-drifted row passes it. Add a tiny
  `check_telemetry_schema.py` (or fold into the guard): each appended line must parse as
  JSON with the canonical keys and `task_class` ∈ the Q-0248 classes. Dedup-grepped
  `docs/ideas/` (`telemetry`, `model-usage`) — the nearest is `context-cost-telemetry-2026-07-02.md`
  (different feed); nothing covers row validation. Worth having because a silently-invalid
  feed is worse than a missing row — the dashboard/export consumes it.
- **⟲ Previous-session review** (`2026-07-09-projects-eap-fleet-review.md`): strong session —
  it verified coordinator claims first-party (cloned superbot-next, re-ran the suite) instead
  of trusting prose, exactly the Q-0120 instinct. Concrete workflow improvement it surfaces:
  its "ship-now" findings were handed off without the enforcement trigger condition spelled
  out, so build sessions must re-derive the engage shape; assessors should state the exact
  trigger (files, date floors, engage-only conditions) in the finding row — this session's
  coordinator prompt did exactly that, and it measurably cut the build time.
- **Docs audit:** `check_current_state_ledger.py --strict` → only the 2-PR benign
  newest-merge lag past marker #1890 (#1892, #1893) — the explicit Q-0166 exception for the
  next reconciliation pass; no drift introduced or spotted otherwise. New rule's durable
  homes: the guard's provenance header (script), its tests, and the `telemetry/README.md`
  enforcement note — nothing left only in chat. No new owner decisions to route (Q-0194/Q-0105
  already cover the doctrine used).
- Claim file `docs/owner/claims/claude-telemetry-gate-guard.md` deleted at close.
