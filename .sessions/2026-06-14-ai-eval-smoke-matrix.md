# Session: P1-1 — versioned AI eval/smoke matrix (offline half)

> **Status:** `complete`

**Branch:** `claude/wizardly-edison-xw34kb` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** AI hardening / tests (P1-1, band-#870 queue slot 2)

## What I'm about to do (born-red declaration)
Build the **offline/deterministic half** of the versioned AI eval/smoke matrix — the standing #1
priority (P1-1), `ready` per the [band-#870 decade queue](../docs/planning/reconciliation-pass-2026-06-14-band870.md) §4 slot 2.

The live golden set (`tests/evals/cases.py`) is paid/creds-only; CI only exercises the harness
machinery, never the AI path's **deterministic contract**. This session adds the missing
versioned, CI-gated artifact covering **gates · fallback · tool-dispatch · audit-visibility ·
redaction · safety** through the real gateway pipeline (scripted providers, no API), producing one
scorecard record. Plus: version the whole matrix and add the #855 Layer-A live regression probe.

**Out of scope (correctly gated):** absence-claim guard **Layer B** stays design-for-review (the
design doc's own definition-of-done) + the live eval battery needs prod creds.

## Coordination
Concurrent docs-only session #877 (sectors/roadmap). This PR is **bot tests + scripts** only —
no overlap on `disbot/`/roadmap. I touch `docs/current-state.md` in my own lane bullet +
Recently-shipped only (UNION-safe) and append one `active-work.md` claim.

## Shipped
- **`tests/evals/smoke.py`** — the deterministic, CI-runnable smoke matrix: 16 `SmokeCase`s
  driving the **real** `AIGateway` with scripted providers (no API) across 7 contract dimensions —
  `gate` (global/task/tool kill switches), `fallback` (recovery / no-env / bad-JSON-not-retried /
  override-disables), `tool_dispatch` (offered / un-offered / faulting-handler-contained), `audit`
  (the `DiagnosticsCollector` snapshot — the operator-visibility dimension the live harness can't
  see), `safety`, `redaction` (secret scrubbed *before* the provider boundary), `config`
  (unregistered-provider degrade). Hermetic env isolation; `guild_id=None` so the runner is DB-free.
  Versioned (`SMOKE_MATRIX_VERSION`) + a `render_report()` scorecard.
- **`tests/evals/test_smoke_matrix.py`** — CI gate: every case (parametrized) + well-formed +
  version-stamped + env-isolation round-trip.
- **`scripts/run_evals.py --smoke`** — runs the offline matrix creds-free (quiets the gateway's
  deliberate fault logging for a clean scorecard); the live record now prints both versions.
- **`tests/evals/cases.py`** — `GOLDEN_SET_VERSION` + the **#855 Layer-A** "bomb shooter middle
  path" MOAB-bonus regression probe (pins the user-facing answer affirms the bonus, not a false "no").
- Recorded offline-half-shipped in `hardening-roadmap` P1-1 + the AI readiness map; ledger entry +
  archive rebalance (held Recently-shipped at 20).

**Out of scope (correctly gated):** absence-guard **Layer B** (the negative-existential gate) stays
design-for-review per the design doc's own definition-of-done; the **live** eval battery needs prod creds.

## Verified
`check_quality --full` green (**9633 passed**, mypy/black/isort/ruff/check_docs ✓) · `check_architecture
--mode strict` **0 errors** · `run_evals.py --smoke` 16/16 (exit 0) · `check_docs --strict` ✓ (ledger
balanced at 20). PR **#878** (born-red → flipped complete last).

## Coordination outcome
The concurrent docs session **#877 merged to main mid-session**. I rebased (merged origin/main),
UNION-resolved the one conflict (`active-work.md`), and confirmed **zero overlap** on my code/doc
files — #877 was roadmap/sector docs only.

## 💡 Session idea (Q-0089)
**A CI "eval-drift" guard**: a tiny invariant that fails when a new `services.ai_tools` tool, an
`AITask`, or a routing seam is added but **no** smoke/golden case references it — so the versioned
matrix can't silently fall behind the surface it's supposed to prove (the same "enforce, don't
exhort" principle the doc-freshness gates use). Dedup-checked: no existing eval-coverage-ratchet idea.
Small follow-up; pairs naturally with the now-versioned matrix.

## ⟲ Previous-session review (Q-0102)
Reviewing **#855 (P1-1 Layer A):** an exemplary slice — it shipped *exactly* the design's
"Recommendation #1 first, separately, low risk", re-verified the canonical trigger live before
building, and left Layer B correctly gated. **What it (reasonably) left:** the eval/smoke matrix —
the *other* half of P1-1 — stayed entirely owed, and the live golden set it would have fed was
still CI-invisible (machinery-only). **System improvement this surfaced:** P1-1 bundles two very
different deliverables (a *retrieval* fix and an *eval artifact*) under one roadmap line, which made
"P1-1" feel perpetually half-done across bands. The band queue should split a multi-deliverable
hardening item into its independently-shippable sub-slices **at plan time** (Layer A · offline
matrix · live battery · Layer B), each with its own gate-state — so progress reads honestly. (This
session shipped the offline-matrix sub-slice; the split would have named it a band ago.)

## Doc audit (Q-0104)
`check_docs --strict` ✓ · `check_quality --full` ✓ · no owner decision made this session (scope was
derived from the band-#870 queue + the existing design docs — no router entry needed) · the P1-1
status is now consistent across `current-state.md`, the hardening roadmap, and the AI map.
**Known ledger drift (left for the reconciliation routine, Q-0124):** `check_current_state_ledger
--strict` flags **#872–#876** (two other sessions' ops/docs PRs — band-#870 reconcile, Hermes/branch
cheatsheets, soul-script, backup-status) as not-yet-in-ledger. They merged before this session, are
durably recorded in their own `.sessions/` cards, are not bot code, and grouping them is the
reconciliation routine's job (fires at #900) — a manual session does not run the recon pass (Q-0124).
**Grooming (Q-0015):** advanced the standing **#1 priority (P1-1)** by shipping its offline half —
the AI path's deterministic contract is now proven in CI on every PR, not just in paid live runs.
