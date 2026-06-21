# Reconciliation pass — 2026-06-19 · the band-#1140 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + **planning-weighted** pass for the band that crossed
> **#1140** (cadence = every **30th** merged PR per Q-0134; `#1140 = 30 × 38`; previous cadence pass
> [the band-#1110 pass](reconciliation-pass-2026-06-19-band1110.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1141**
> (`.github/workflows/reconciliation-trigger.yml`) — the **thirteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1141 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`. This pass ran **extra-thorough, weighted toward planning**, per the
> owner's #1140-fire directive (top of `current-state.md`, now consumed).
> Sections: §1 verified state + open-PR disposition · §2 the owner directive executed · §3 band
> scorecard · §4 the next band · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1140**.

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#1110 pass (band #1127–#1140):** the band's headline is the **ultracode-fleet
close-out + the Q-0181 ground-truth-audit tooling**, plus the mining hub declutter and Codex-review
integration.

- **Ultracode-fleet close-out + Q-0181 tooling (#1134–#1140).** `scripts/check_plan_code_drift.py` +
  the [ground-truth-audit protocol](../operations/ground-truth-audit-protocol.md) (#1135), rebadging
  A3/A4 historical + wiring the drift check into `/session-close` (#1136), the fleet pre-flight
  overlap-check rule + `scripts/check_lane_overlap.py` (#1137/#1139), the premature-closure self-check
  + Codex-safety/sector-boot idea captures (#1138/#1134), and the recon-trigger docs + voice-brainstorm
  pack (#1140).
- **Mining hub declutter — Option A PR2 (#1131).** Split the 16-button mining hub into Character +
  Explore sub-hubs (`views/mining/explore_hub.py`, `MiningExploreHubView`). **This pass's Explore-hub
  plan re-parents that sub-hub into a top-level world hub.**
- **Codex-review integration B5 (#1132)** — routines fix flagged-real issues first; Hermes 6H pr-check
  skill (Q-0174/Q-0180). **Open-question sweep + router-status detector + dashboard lockfile (#1130).**
  **Dashboard refresh (#1127).**

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 10 merged PRs newer than the
#1110 marker (benign-lag class). A per-PR grep confirmed #1127/#1130/#1131/#1132/#1134–#1140 absent
from the live ledger (#1133 was **superseded by #1128**, closed unmerged — only #1074 is open).
Recorded as five grouped Recently-shipped entries; trimmed the live list back to the 20 newest, moving
#1061 … #1046 to `current-state-archive.md`. `--strict` green; `check_docs --strict` green.

**Control-plane reconciled:** `check_loop_health.py` reported SKIP (`gh` unavailable in-container — the
recurring Q-0135 mode), so the live read was done via the trigger-issue author — #1141 authored by
**`menno420`** confirms `ROUTINE_PAT` is set + the loop self-fires. Added #1141 to the canonical
control-plane table row 1 (`operations/autonomous-routines.md`) — thirteenth consecutive self-fire.

**Dashboard freshness:** regenerated `dashboard/data/dashboard.json` (`export_dashboard_data.py`);
`check_dashboard_data --drift` checked for structural identifier drift first.

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1074 (dependabot python-minor-patch dev group) | open | **Left** — routine dependabot dev-dep bump (ruff/pytest/pytest-xdist); merging needs the 3-place version sync (workflow / `requirements-dev.txt` / `.pre-commit-config.yaml`), a code change out of docs-only scope. Will auto-merge / owner-handle. (Carried from the band-#1110 pass — still the only open PR; no red-CI orphan, no superseded `claude/*` PR.) |

## 2. The owner #1140-fire directive — executed (planning-weighted)

The owner directed an extra-thorough, planning-weighted pass: **(1) surface the day's open design
questions into the router (DISCUSS lane); (2) promote the idea backlog into buildable plans** — Explore
hub first, then the feedback-board/owner-inbox generalization; the AI-ticket service stays
plan-the-questions-first.

**(1) Questions routed (DISCUSS lane):**
- **Q-0182** — federated Explore-hub **world model** (four open design questions: hub shape / survival
  overlay / docking / cross-game identity). The ungated spine is planned; these gate the deferred layers.
- **Q-0183** — AI correction-report → audience-routed **ticket service** (plan-the-questions-first per the
  owner; the seven open questions the dedicated session must answer, incl. the two-gates / opposite-safe-
  defaults rule).
- **Q-0184** — bot **memory** global-vs-per-guild scope (user-chosen vs. per-guild default).
- **Q-0185** — public **bot-site one-line pitch** (owner's voice should drive it; agents must not invent it).

**(2) Plans promoted (idea→plan gate, Q-0172):**
- **[Federated Explore-hub spine plan](explore-hub-federated-world-plan-2026-06-19.md)** — 3 ungated PRs
  (top-level Explore world hub + world registry; global/per-game XP split; cross-game identity read
  surface), re-parenting the #1131 mining Explore sub-hub. Gated layers (gear auto-equip · survival
  overlay · biome map) deferred to Q-0182.
- **[Feedback-board generalization plan](feedback-board-generalization-plan-2026-06-19.md)** — add
  `type`+`location` facets to the shipped `/reviews` board, **gated on moving it behind owner auth
  first** (it is currently public; carrying server-private facets requires the auth move). Provides the
  destination + facet schema the AI-ticket router (Q-0183) needs.
- **AI-ticket *build* plan: deliberately NOT written** — the owner flagged it needs its own extensive
  session; routed as Q-0183, board planned separately. Flagged on the run report `⚑ Self-initiated` line.

## 3. Band scorecard (vs. the band-#1110 next-band queue)

The band-#1110 queue named the **website P1–P8 parallel wave** as the top ungated work. The band instead
shipped the **ultracode-fleet close-out + the Q-0181 ground-truth-audit tooling** (a workflow/quality
investment surfaced by the owner's "verify docs against code, not badges" directive) plus the mining hub
declutter (#1131) and the #1120 dispatch-run bug fixes (BUG-0016/BUG-0017, recorded in the prior ▶ Next
action). The website wave remains the dominant *next* buildable lane — it did not regress, the band
simply prioritized a workflow-hardening season + the owner's live design brainstorm.

## 4. The next band (depth to #1170)

#1170 is 30 merges out. **No PLAN-BACKLOG-THIN flag** — well over 30 PRs of buildable depth. Ranked:

1. **Website two-site split — parallel P1–P8 wave** ([plan](website-two-site-split-plan-2026-06-19.md) §5):
   bot-site pages, public `/submit` (honeypot + rate-limit v1), dev-site `/admin/moderation`, the
   least-privilege GitHub-issue mirror. Additive; the control-panel migration rides the security review.
2. **Federated Explore-hub PR 1** ([plan](explore-hub-federated-world-plan-2026-06-19.md)): top-level
   Explore world hub + world registry — ungated, re-parents the #1131 mining Explore sub-hub.
3. **Consistency-linter rule 1 (`edit_in_place`) AI-nav redesign** —
   [plan](ai-panel-inplace-navigation-plan-2026-06-19.md) PR 1; runtime/Q-0086 live-walk, `needs-hermes-review`.
4. **procedures→skills remaining batches** ([plan](procedures-to-skills-conversion-plan-2026-06-17.md)).
5. **Explore-hub PR 2/PR 3** (global/per-game XP split; cross-game identity card) once PR 1 lands.

Gated/owner-paced (not in the buildable count): feedback-board PR 1 (owner dashboard auth) · the
AI-ticket build (Q-0183, own session) · the gated Explore-hub layers (Q-0182) · dashboard writes /
control-API (security review) · fishing follow-ons (Q-0175) · BTD6 floors (exhausted).

## 5. Pruned / fixed this pass

- Reset the `Last reconciliation pass` marker #1110 → **#1140**; next due at **#1170**.
- Added #1141 to the control-plane ROUTINE_PAT row (thirteenth consecutive self-fire).
- Consumed the owner #1140-fire directive at the top of `current-state.md` (replaced with a consumed note).
- Regenerated `dashboard/data/dashboard.json` (cadence freshness).
- Indexed both promoted plans in `docs/ideas/README.md`.
- No new runtime bugs noticed (BUG-0016/BUG-0017 were fixed in the #1120 dispatch run).

## 6. The system improvement this pass made

**Closed the loop on the owner's own correction.** The owner's #1140-fire directive grew directly out of
the Q-0181 finding (docs were being "made correct" as internal consistency, not truth-against-code). This
pass honored that by re-deriving the missing-ledger set from a **per-PR git grep** (not the checker's
count alone) and by **disproving** the apparent #1133 "merged" status (it was superseded/closed, not
merged — confirmed against the branch head, not the PR title). The Q-0089 idea this pass captures
generalizes that habit (see the session log).
