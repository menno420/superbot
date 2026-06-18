# Plan — Repo consistency linter (`check_consistency.py`)

> **Status:** `plan` — executable plan for the UX/interaction-pattern linter
> ([idea](../ideas/repo-consistency-linter-2026-06-17.md); decision **Q-0170**, 2026-06-17). Built
> incrementally, one rule per PR — a real buildable lane that feeds the backlog (Q-0164). Source +
> the binding contracts win.

## Goal

Catch **interaction/UX-pattern inconsistencies** that `check_architecture.py` (import layers) can't
see — the owner's examples: panels missing a back button, cogs sending ephemeral follow-ups instead
of editing in place, views that should be `BaseView`/`HubView` but aren't.

## Shape (matches the repo's tooling house style)

- **`scripts/check_consistency.py`** — stdlib AST over `disbot/views/` + `disbot/cogs/`, modeled on
  `check_architecture.py`: a list of `Rule` objects, `--mode strict`, a per-rule **allowlist** under
  `architecture_rules/consistency_exceptions.yml` (the only valid bypass — never suppress the check).
- **Warn-first, disposable (Q-0105)** with a provenance header. A rule graduates to error + a
  `code-quality` wire-in only once it runs **clean on a fresh tree** (no false positives) across a
  few sessions (the Q-0120 / `dead-unresolved` discipline: a noisy checker trains people to ignore it).
- **Tested:** each rule ships with a `tests/unit/scripts/test_check_consistency.py` case (a positive
  + a negative fixture), mirroring the architecture-checker tests.

## Rule backlog (one PR each — the buildable lane)

| # | Rule | Flags | Notes / exception source |
|---|------|-------|--------------------------|
| 1 | **Edit-in-place** | a panel callback replying with a *new* `followup.send(ephemeral=True)` / `response.send_message` where the house pattern edits in place | the owner's headline example; allowlist genuine "new message" cases (e.g. a fresh DM, a confirmation toast) |
| 2 | **Back-button presence** | a `HubView`/panel subclass with child buttons but no back/nav affordance | seed the "nav affordance" detector from the shared back mixin / breadcrumb composer |
| 3 | **Panel base-class** | a button/select view extending `discord.ui.View` directly outside the `views/rps`,`views/blackjack` game-state allowlist | the arch doc states this in prose; this enforces it |
| 4+ | (grow as the owner / reviews surface more) | … | each new mechanical-consistency rule the review inbox turns up |

## Build order

1. **PR 1 — the harness + rule 1 (edit-in-place), warn-only.** ✅ **SHIPPED 2026-06-18** —
   `scripts/check_consistency.py` (the `Finding`/`Rule` framework, the
   `architecture_rules/consistency_exceptions.yml` allowlist loader, the `--mode`/`--file` CLI) +
   rule 1. The rule scopes to `views/` panel button/select callbacks, flags an **ephemeral** new
   message (`response.send_message` / `followup.send`) when the callback **never edits in place** and
   the send isn't an early-return guard (`send; return` validation toasts are excluded). **First-run
   count: 45 candidates** (allowlist left empty — warn-only, triage in follow-up). Genuine signal
   confirmed (e.g. `DiagnosticsPanel.refresh_btn` shows "list refreshed" as an ephemeral instead of
   re-rendering the panel). Tests: `tests/unit/scripts/test_check_consistency.py` (positive +
   edits-in-place/guard/non-ephemeral/non-callback negatives + allowlist + live-tree warn-only).
2. **PR 2 — rule 2 (back button)**, same pattern; **PR 3 — rule 3 (panel base-class)**.
3. **Graduation:** once a rule is quiet on a clean tree, flip it to error and add it to
   `code-quality.yml` (or the pre-pr suite). Keep noisy rules warn-only. Rule 1 stays warn-only until
   the 45 candidates are triaged to real fixes / allowlist entries across a few sessions.

## Verification (each PR)

- `python3.10 scripts/check_consistency.py --mode strict` runs; the new rule's fixtures pass;
  `python3.10 scripts/check_quality.py --full` green; `check_architecture --mode strict` exit 0.
- The triage of real hits is fixed *in the same band* (not just allowlisted away) where contained —
  e.g. converting the flagged ephemeral follow-ups to edit-in-place is the *point*, not noise to mute.

## Why a strong next lane

Owner-requested, concretely specified, **low-risk (read-only tool), incremental (one rule = one real
PR), and self-feeding** (every rule both finds and motivates real fixes). Prime reconciliation-band
material under Q-0164.
