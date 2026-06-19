# Reconciliation pass — 2026-06-19 · the band-#1080 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1080**
> (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#1050 pass](reconciliation-pass-2026-06-18-band1050.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1095**
> (`.github/workflows/reconciliation-trigger.yml`) — the **eleventh** consecutive real cadence fire of
> the autonomous issue-trigger and live proof the loop self-fires: #1095 was authored by
> **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities restated ·
> §4 the next band · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1094** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#1050 pass (band #1060–#1094):** the band's headline is a **repo-governance
turn** plus the launch of the **ultracode parallel-fleet** build run — distinct from the previous
bands' product/linter focus.

- **Repo-governance + supply-chain baseline (#1064).** The first open-source-grade governance layer:
  a CodeQL workflow, `dependabot.yml`, issue/PR templates, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CITATION.cff`, and a dashboard-CI workflow — plus the
  [repo-structure-improvement plan](repo-structure-improvement-plan-2026-06-19.md).
- **Dependabot dependency-bump band (#1065–#1073, #1075–#1078).** The new `dependabot.yml` immediately
  raised the backlog of pinned deps: GitHub Actions majors (cache-5, codeql-action-4, github-script-9,
  checkout-7, setup-python-6) + pip deps (anthropic, uvicorn, httpx, fastapi, jinja2 — root + dashboard).
- **Ultracode fleet — plan + wave A (#1079, then #1081/#1083/#1084/#1087/#1092).** #1079 added the
  [ultracode-fleet plan](ultracode-fleet-plan-2026-06-19.md) (16 file-disjoint units across Lane A
  architecture-debt burndown + Lane B tooling quick-wins). Wave A merged five Lane-A helper-extraction
  slices: moderation helpers (A2 #1081), governance exceptions (A6 #1083), BaseView conformance
  (A8 #1084), `utils/db` wrappers (A7 #1087), blackjack state (A3 #1092).
- **Consistency-linter graduation (#1094).** The three clean rules (`back_button`, `panel_base_class`,
  `select_option_truncation`) flipped `warning`→`error` and `check_consistency.py --mode strict` is now
  wired into `code-quality.yml` + the local `check_quality.py` mirror — a finding now fails CI.
  `edit_in_place` stays warn-only (BLOCKED on the AI-nav redesign).

Plus #1060 (AI-nav idea→plan), #1061 (dashboard-data refresh).

**Ledger reconciled:** `check_current_state_ledger --strict` (window 15) flagged 13 missing; a per-PR
grep of the whole #1060–#1094 band confirmed ~21 merges absent from the live ledger. Recorded them as
four grouped Recently-shipped entries (#1094 graduation · the ultracode wave-A five · #1064/#1079
governance+fleet-plan · the #1065–#1078 dependabot band, written as expand-able ranges) and trimmed the
live list back to the 20 newest, moving #1036 … #1028 to `current-state-archive.md`. `--strict` now
green; `check_docs --strict` green.

**Control-plane reconciled:** `check_loop_health.py` reported SKIP (`gh` unavailable in-container), so
the live read was done via the trigger-issue author — #1095 authored by **`menno420`** confirms
`ROUTINE_PAT` is set + the loop self-fires. Added #1095 to the canonical control-plane table row 1
(`operations/autonomous-routines.md`).

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1063 (consistency-linter graduation rails) | open, **dirty** | **CLOSED — superseded.** The rails (per-rule severity + tracker + strict wiring) shipped via #1062 (tracker) + #1094 (graduation); #1063 conflicts and would *regress* the now-graduated rules to warn-only. The fleet plan's "let #1063 settle" note was stale → fixed. |
| #1082/#1085/#1086/#1088/#1089/#1090/#1091/#1093 (ultracode **Lane B** wave) | open, in-flight | **Left — active fleet.** The 8 Lane-B tooling units (governance-files guard, ledger-hygiene, routine-permission, plan-backlog, autospec, SHA-pin, review-inbox, procedures→skills), opened ~08:40 today. Not stale; auto-merge on green. |
| #1074 (dependabot python-minor-patch dev group) | open | **Left** — routine dependabot dev-dep bump, will auto-merge. |

No red-CI orphan PRs found.

## 2. Band scorecard (vs. the band-#1050 next-band queue)

The band-#1050 queue named the consistency-linter selector-windowing lanes (A1/A2) and graduation as the
top ungated work. **All of it shipped** in the #1050→#1062 window (recorded last pass + the #1094
graduation this pass). The #1060–#1094 band then **pivoted to repo-governance + the ultracode fleet** —
a higher-leverage, owner-aligned use of the parallel-agent edge (breadth on file-disjoint units) than
continuing single-file linter slices. The pivot is on-strategy: it burns down the architecture
boundary-debt the structure review flagged (76 warnings → target ~28) while the linter rules are now
CI-enforced.

## 3. Priorities restated (current-state ▶ Next action)

The live queue is **healthy — no PLAN-BACKLOG-THIN flag.** The next band is largely **already in
flight** via the ultracode fleet:

- **In flight now (~9 PRs):** the 8 Lane-B tooling units (#1082/#1085/#1086/#1088–#1091/#1093) + the
  #1074 dep bump.
- **Remaining Lane A** (not yet open at pass time): A1 (economy/xp `_helpers` → `services/`),
  A4 (diagnostic embeds — large, map callers first), A5 (deathmatch circular import).
- **Held serial arch-fixes** (do *after* Lane A lands, one careful PR each): `core/runtime → services`
  (arch-fix-11, ~13 files) and `utils/db/pool.py` (arch-fix-6).

## 4. The next band (depth to #1110)

#1110 is 16 merges out from #1094 — the in-flight fleet alone covers it. Ranked, highest-value first:

1. **Land the ultracode Lane-B fleet** (8 PRs in flight) — tooling/ops guards (B1–B8).
2. **Finish ultracode Lane A** — A1, then the careful A4/A5 (map every caller, incl. lazy imports).
3. **Held serial arch-fixes** — `core/runtime → services` + `utils/db/pool.py`, one PR each, post-Lane-A.
4. **Consistency-linter rule 1 (`edit_in_place`) AI-nav redesign** —
   [plan](ai-panel-inplace-navigation-plan-2026-06-19.md) PR 1; needs a runtime/Q-0086 live-walk
   session, `needs-hermes-review`. Graduating `edit_in_place` follows once it reaches 0.
5. **owner-review-inbox Phase 2+** ([plan](owner-review-inbox-plan-2026-06-17.md)) once Phase 1 (B7) lands.
6. **procedures→skills remaining batches** ([plan](procedures-to-skills-conversion-plan-2026-06-17.md)).

Gated/owner-paced (not in the buildable count): BTD6 floors (exhausted), fishing follow-ons (Q-0175
owner-design-gated), dashboard *writes* / control-API (owner-paced), image-mod / security tiers (shipped
2026-06-18). The owner-side lever to rebalance toward bot features is a Q-0175 fishing decision or a
dashboard-write greenlight.

## 5. Pruned / fixed this pass

- Reset the `Last reconciliation pass` marker #1050 → **#1094**; next due at **#1110**.
- Closed superseded PR #1063 (with a reason comment) + de-staled the fleet plan's #1063 "held" note.
- Added #1095 to the control-plane ROUTINE_PAT row.
- Regenerated `dashboard/data/dashboard.json` (cadence freshness — ideas/bugs/updates counts drifted).
- Captured **BUG-0016** (stale "multiple-of-20" / "next ~9 PRs" copy in
  `.github/workflows/reconciliation-trigger.yml`) for a dispatch routine — out of docs-only scope here.

## 6. The system improvement this pass made

**The control-plane live-read fallback held under `gh`-unavailable.** `check_loop_health.py` SKIPped
(no `gh` in this container), exactly the failure mode the Q-0135 fallback exists for — and the
trigger-issue-author read (`menno420` → PAT set) gave the same verdict with zero ambiguity. This pass
adds the **eleventh** consecutive `menno420`-authored cadence issue to the row-1 evidence chain, so the
"loop self-fires" claim is now over-determined. No tooling change needed — the fallback is doing its job;
the improvement is the recorded confirmation that the SKIP path is non-blocking.
