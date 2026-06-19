# Reconciliation pass — 2026-06-19 · the band-#1110 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1110**
> (cadence = every **30th** merged PR per Q-0134; `#1110 = 30 × 37`; previous cadence pass
> [the band-#1080 pass](reconciliation-pass-2026-06-19-band1080.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1111**
> (`.github/workflows/reconciliation-trigger.yml`) — the **twelfth** consecutive real cadence fire of
> the autonomous issue-trigger and live proof the loop self-fires: #1111 was authored by
> **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities restated ·
> §4 the next band · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1110** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#1080 pass (band #1095–#1110):** the band's headline is the **website two-site
split** — planned end-to-end (Q-0178/Q-0179) and its serial foundation built — plus the tail of the
ultracode fleet and workflow tooling.

- **Website two-site split — planning band (#1099/#1100/#1102/#1104/#1107/#1110, Q-0178/Q-0179).**
  The public bot-site / private dev-site split planned end-to-end: the
  [planning brief](website-two-site-split-plan-2026-06-19.md) (#1099) → the full implementation plan +
  file-disjoint **ultracode decomposition** (#1100) → routing the control-panel-placement decision Q-0179
  (#1102) → **locking the open decisions + resolving Q-0179** (#1104) → making the §5 decomposition truly
  file-disjoint pre-ultracode (#1107) → the owner site-identity vision + fan-out enablers (#1110). Owner
  decisions LOCKED 2026-06-19 (plan §7) — the build run is decision-unblocked.
- **Website two-site split — serial foundation (#1109).** The first build wave: the public-data subset
  (`site.json` + the redaction-whitelist guard, S1), the submissions DB (S2), and the first bot-site page
  set (P1) — the serial foundation the parallel P1–P8 wave builds on.
- **Fleet A4 — diagnostic embeds → `services/` (#1097).** The ultracode-fleet Lane-A A4 unit (callers
  mapped first) — the large diagnostic-embed relocation the band-#1080 queue flagged as careful work.
- **Workflow tooling + CI hygiene (#1103/#1105/#1106/#1108).** `scripts/router_status.py` question-router
  digest (#1103); Codex reviews the **final head** (`@codex review` on the session-card flip, #1105); the
  `pr-conflict-guard` now polls through GitHub's UNKNOWN-mergeability window (#1106); `.gitignore` ignores
  transient background-agent worktrees (#1108).
- **#1101** dashboard-data refresh; **#1098** the band-#1080 Q-0107 reconciliation pass (docs-only).

**Ledger reconciled:** `check_current_state_ledger --strict` flagged 11 missing (#1097–#1109). A per-PR
grep of the whole #1095–#1110 band confirmed them absent from the live ledger. Recorded as six grouped
Recently-shipped entries (the website planning band · the serial foundation · fleet A4 · the
tooling/CI four · #1101 · #1098) and trimmed the live list back to the 20 newest, moving #1042 … #1037 to
`current-state-archive.md`. `--strict` now green; `check_docs --strict` green.

**Control-plane reconciled:** `check_loop_health.py` reported SKIP (`gh` unavailable in-container), so the
live read was done via the trigger-issue author — #1111 authored by **`menno420`** confirms `ROUTINE_PAT`
is set + the loop self-fires. Added #1111 to the canonical control-plane table row 1
(`operations/autonomous-routines.md`).

**Dashboard freshness:** regenerated `dashboard/data/dashboard.json` (`export_dashboard_data.py`);
`check_dashboard_data --drift` reported OK pre-regen (no structural identifier drift), so the change is
volatile-count freshness only (ideas/bugs/updates/changelog) — committed with the pass.

### Open-PR disposition (Q-0125)

| PR | State | Disposition |
|---|---|---|
| #1074 (dependabot python-minor-patch dev group) | open | **Left** — routine dependabot dev-dep bump; merging needs the 3-place version sync (workflow / `requirements-dev.txt` / `.pre-commit-config.yaml`), which is a code change out of docs-only scope. Will auto-merge / owner-handle. |

No red-CI orphan PRs found; no superseded/stale `claude/*` PRs. The Lane-B ultracode fleet that was
in-flight at the band-#1080 pass has since merged (folded into the #1095–#1110 band on `main`).

## 2. Band scorecard (vs. the band-#1080 next-band queue)

The band-#1080 queue named **landing the ultracode Lane-B fleet + finishing Lane A** as the top ungated
work. **Lane A A4 shipped (#1097)** and the Lane-B fleet merged into `main`. The band then **pivoted to
the website two-site split** — a higher-leverage owner-aligned initiative (the owner's #1099 brief +
Q-0178/Q-0179), planned end-to-end and with its serial foundation already built (#1109). The pivot is
on-strategy: the website split is the S5/operations + public-facing surface the roadmap's "Someday
website" horizon (Q-0042) finally makes concrete, and it is decision-unblocked (plan §7).

## 3. Priorities restated (current-state ▶ Next action)

The live queue is **healthy — no PLAN-BACKLOG-THIN flag.** The dominant lane is now the **website
two-site split build run** (its serial foundation shipped #1109; the parallel P1–P8 additive wave is the
next buildable depth — bot-site marketing pages, the public `/submit` intake form, the dev-site
`/admin/moderation` UI + the least-privilege GitHub-issue mirror). Behind it, the consistency-linter
lanes (AI-nav rule-1 redesign), procedures→skills batches, and the owner-review-inbox phases remain
ungated buildable work.

## 4. The next band (depth to #1140)

#1140 is 30 merges out. Ranked, highest-value first:

1. **Website two-site split — parallel P1–P8 wave** ([plan](website-two-site-split-plan-2026-06-19.md) §5):
   bot-site pages, the public `/submit` intake form (honeypot + rate-limit v1), the dev-site
   `/admin/moderation` UI, and the least-privilege GitHub-issue mirror. The first wave is additive; the
   control-panel migration rides the control-API public-exposure security review (plan §7).
2. **Consistency-linter rule 1 (`edit_in_place`) AI-nav redesign** —
   [plan](ai-panel-inplace-navigation-plan-2026-06-19.md) PR 1; needs a runtime/Q-0086 live-walk session,
   `needs-hermes-review`. Graduating `edit_in_place` follows once it reaches 0.
3. **owner-review-inbox Phase 2+** ([plan](owner-review-inbox-plan-2026-06-17.md)) once Phase 1 lands.
4. **procedures→skills remaining batches** ([plan](procedures-to-skills-conversion-plan-2026-06-17.md)).
5. **Small stdlib guards** as fresh mechanical-consistency shapes surface (e.g. extending consistency
   rule 4 to `disbot/cogs/`); forced filler ≠ work.

Gated/owner-paced (not in the buildable count): BTD6 floors (exhausted), fishing follow-ons (Q-0175
owner-design-gated), dashboard *writes* / control-API (owner-paced + the security review), image-mod /
security tiers (shipped 2026-06-18). The website control-panel migration is gated on the same
control-API public-exposure security review.

## 5. Pruned / fixed this pass

- Reset the `Last reconciliation pass` marker #1094 → **#1110**; next due at **#1140**.
- Added #1111 to the control-plane ROUTINE_PAT row (twelfth consecutive self-fire).
- Regenerated `dashboard/data/dashboard.json` (cadence freshness — volatile counts only; no structural drift).
- No new runtime bugs noticed. BUG-0016 (stale "multiple-of-20" / "next ~9 PRs" copy in
  `reconciliation-trigger.yml`) remains OPEN from the band-#1080 pass — still out of docs-only scope here;
  the issue-body wording is the residue of that not-yet-shipped fix.

## 6. The system improvement this pass made

**The control-plane live-read fallback held again under `gh`-unavailable — and the evidence chain is now
twelve fires deep.** `check_loop_health.py` SKIPped (no `gh` in this container), the exact Q-0135 failure
mode, and the trigger-issue-author read (`menno420` → PAT set) gave the same verdict with zero ambiguity.
The recurring SKIP across every recent pass is itself a signal: the in-container `gh` probe never works in
this routine, so the *author read* is the de-facto canonical control-plane check here, not the
`check_loop_health.py` script. Captured as the Q-0089 idea this pass — make `check_loop_health.py`
fall back to the GitHub API / a cached author read when `gh` is absent, so the routine's control-plane row
is verifiable by the script and not only by hand.
