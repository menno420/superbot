# 2026-07-13 — Hub upkeep follow-up: Codex P2 fixes from #2054

> **Status:** complete
> **Branch:** `claude/hub-upkeep-codex-p2` · **PR:** pending
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** docs-only follow-up (Q-0174) — two verified-genuine Codex P2 line comments left on
> the just-merged #2054, fixed in a small follow-up PR off `origin/main@ab76279`.

## Arc

PR #2054 (hub upkeep: stale rebuild pointers) merged 2026-07-13T00:04:29Z with two Codex P2
review comments, both verified genuine:

- **Fix 1** — `docs/current-state.md` L67 ([comment](https://github.com/menno420/superbot/pull/2054#discussion_r3567409368)):
  the new S3 row tail names "the D-0043 deep-game go/no-go" but D-0043 resolves nowhere in THIS
  repo, and the linked 2026-07-13 brief §3 doesn't mention it — a named owner decision with no
  resolvable handoff. Fix: qualify the ID with its owning artifact — D-0043 is a
  **superbot-next** decision (`docs/decisions.md` [D-0043] "Band 6 slice 2: the CHECKPOINT
  games", verified at `menno420/superbot-next@e9f1cd5`, which names the deep-game successor-port
  scope) — while keeping the brief §3 pointer for the merge-wall item.
- **Fix 2** — `docs/current-state/S4-docs.md` ~L248–257 ([comment](https://github.com/menno420/superbot/pull/2054#discussion_r3567409369)):
  the "▶ Rebuild — the review-then-plan phase" bullet still opens with the retired "Next: (A)
  content review pass … (B) one 100%-complete design plan per step before any code" guidance
  AHEAD of #2054's new LIVE tail — contradictory guidance in one `▶ Next` item. Fix: re-badge
  the retired framing as historical/superseded (retitle `(historical)`, wrap the old (A)/(B)
  text as superseded 2026-07-07 by Q-0241/#1776), keeping the text present — append-only
  spirit, same style as the re-badged 2026-06-30 owner-steer bullet below it.

## Shipped

- Fix 1 + Fix 2 above (2-file docs diff) + the Q-0194 telemetry row. Quality mirror green:
  `python3.10 scripts/check_quality.py --full` → **All checks passed ✓**
  (13883 passed, 50 skipped, 2 xfailed). Fix 1's cross-repo pointer is a full GitHub URL
  (not a backticked path) because `check_docs` pinned-check resolves backticked `docs/...`
  paths against THIS repo.

## Session enders

- **Context delta:**
  - needed-but-not-pointed-to: none — the orchestrator handed exact file/line targets + both
    Codex comment URLs.
  - pointed-to-but-unneeded: none.
  - discovered-by-hand: D-0043's owning artifact is `docs/decisions.md` in menno420/superbot-next
    (verified live at `e9f1cd5` before wording the cross-repo pointer).
- **Decisions made alone:** exact wording of the cross-repo D-0043 qualifier and the
  historical/superseded badge phrasing (both minimal-diff, per the orchestrator's templates).
- **Flagged for maintainer:** none new — the `control/status.md` heartbeat drift flagged by the
  #2054 card still stands.
- **🛠 Friction → guard (Q-0194):** none.

## 📤 Run report

- **Did:** fixed both verified-genuine Codex P2 comments from #2054 — qualified the D-0043
  handoff with its owning artifact (superbot-next decisions ledger, verified at `e9f1cd5`) and
  re-badged the retired review-then-plan Rebuild bullet as historical/superseded.
  **Outcome:** quality mirror green; PR opened READY for the auto-merge-enabler path.
- **Shipped:** the two fixes; the Q-0194 telemetry row; this card.
- **Run type:** orchestrated docs-only follow-up (worker seat), decide-and-flag.
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated (Q-0172):** none — scope fully specified (two Codex P2s, Q-0174 practice).
- **↪ Next:** none from this slice; hub seat still owns the `control/status.md` drift.

## 📊 Telemetry

| PRs merged | CI-red rounds | rule trips | ideas contributed | ideas groomed |
|---|---|---|---|---|
| 0 (1 opened, auto-merge path) | 0 | 0 | 0 | 0 |
