# Session — 2026-06-22 · twenty-first Q-0107 reconciliation pass (band-#1320)

> **Status:** `complete`

Docs-only reconciliation + planning pass, triggered by `reconcile` issue **#1321**
(`reconciliation-trigger.yml`). Marker was #1291 (band-#1290 pass); merged PRs crossed #1320.

## What changed
- **Ledger reconciled:** added band #1294–#1320 as **7 grouped entries** in
  `current-state.md` Recently-shipped (fishing minigame · role management · help surface ·
  BTD6 answerability · botsite React PR1 · CI/ledger/tool-pin hygiene · deps + dashboard);
  trimmed the live ledger back to 20, moving 7 oldest bands to `current-state-archive.md`;
  reset the marker **#1291 → #1320**; bumped the `Last updated` stamp, the S4-sector snapshot,
  and the top-of-file sector table.
- **Checkers green:** `check_docs --strict`, `check_current_state_ledger --strict`,
  `check_session_log` all pass (re-run after edits).
- **Control-plane (Q-0135):** `check_loop_health` SKIP (no `gh` in container); manual fallback —
  trigger issue #1321 author is `menno420` ⇒ ROUTINE_PAT set, loop self-fires. No drift.
- **Open-PR disposition (Q-0125):** #1318 (BTD6 round_xp data) + #1319 (Q-0197 retire
  needs-hermes-review) are both minutes-old, active in-flight — left to auto-merge. No stale/
  redundant opens to close.
- **Dashboard export regenerated** (Q-0167 cadence half): `dashboard/data/dashboard.json`,
  `botsite/data/site.json`, `botsite/site/data.js`.
- **Pass record:** [`reconciliation-pass-2026-06-22-band1320.md`](../docs/planning/reconciliation-pass-2026-06-22-band1320.md);
  re-badged the band-#1290 pass `historical`.
- **No new runtime bugs noticed** → nothing appended to the bug book (stayed docs-only).

## What's next
- Next reconciliation due once merged PRs cross **#1350**.
- Next band depth healthy — **no PLAN-BACKLOG-THIN flag**; queue in the pass record §4
  (Project Moon seam · botsite React PR2+ · creature leaderboards · fishing follow-ups · the
  open-PR staleness classifier idea, now `ready`).

## 💡 Session idea (Q-0089)
[`band-queue-hit-rate-metric-2026-06-22.md`](../docs/ideas/band-queue-hit-rate-metric-2026-06-22.md) —
extend `band_pr_status.py` with a `--queue-hit-rate` mode so each pass records *one number* for how much
of the previous queue actually shipped vs. unplanned buffer, turning the most-repeated qualitative finding
("the buffer became the band") into a data-driven planning signal.

## ⟲ Previous-session review (Q-0102)
The band-#1290 pass was clean (correct zero-stale open-PR disposition, accurate ledger). Its §4 queue again
over-indexed on long-horizon review-gated lanes that the next band then largely skipped for an unplanned
fishing arc — the same prediction gap every recent pass logs in prose. Not a fault (owner-steered work
rightly outranks the queue, Q-0124), but the honest fix is to *measure* the gap rather than keep noting it
— which is exactly this pass's Q-0089 idea.

## 📤 Run report

- **Did:** twenty-first Q-0107 docs reconciliation (band-#1320) — ledger/marker/dashboard reconciled, next band planned · **Outcome:** shipped
- **Shipped:** this PR — docs-only reconciliation pass (ledger band #1294–#1320, marker #1291→#1320, pass record, dashboard regen, 1 idea)
- **Run type:** `routine · reconciliation` (Q-0165)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (routine reconciliation; the Q-0089 idea is captured, not promoted to a build)
- **↪ Next:** next recon at #1350; next band = Project Moon seam · botsite React PR2+ · creature leaderboards · fishing follow-ups (no PLAN-BACKLOG-THIN flag)
