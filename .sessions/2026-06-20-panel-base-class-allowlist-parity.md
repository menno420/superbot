# 2026-06-20 — cross-allowlist drift guard: `panel_base_class` yml ↔ arch conformance frozenset

> **Status:** `complete`

## Arc (what I'm about to do)

Dispatch routine, no work order — advancing the next plan slice. The previous run
(`2026-06-20-arch-ratchet-cog-layer.md`, #1163) extended the `baseview_inheritance` arch ratchet to
scan `cogs/` and flagged a Q-0089 idea: the `panel_base_class` consistency-linter allowlist
(`architecture_rules/consistency_exceptions.yml`) and the arch ratchet's
`_KNOWN_DIRECT_VIEW_SUBCLASSES` frozenset (`tests/unit/views/test_view_base_class_conformance.py`)
both hand-enumerate the **same** documented direct-`discord.ui.View` exceptions in two files — a
"two sources of truth" smell. When one is ratcheted down and the other isn't, they silently diverge.

Promoting that captured idea → build (Q-0172, self-initiated, flagged below). The two sets are
currently in **exact sync** (13 entries each, verified) — the right moment to pin them with a small
stdlib parity test so neither can drift from the other. Plus fix the stale "8-entry frozenset" prose
in the yml comment (it's been 13 since the cogs/ entries landed in #1163) — Q-0166 drift, fix on sight.

Contained / reversible / test-only — self-merge on green.

## What shipped

- **`tests/unit/views/test_panel_base_class_allowlist_parity.py`** (new) — asserts the
  `panel_base_class` allowlist in `architecture_rules/consistency_exceptions.yml` lists exactly the
  same `(path, class)` pairs as `_KNOWN_DIRECT_VIEW_SUBCLASSES` in
  `tests/unit/views/test_view_base_class_conformance.py`. Imports the frozenset from its sibling
  (single source on that side), parses the yml `path::Class` patterns on the other, set-diffs both
  ways with directional, actionable failure messages.
- **`architecture_rules/consistency_exceptions.yml`** — de-staled the `panel_base_class` comment
  (`8-entry frozenset` → `13 entries: 8 views + 5 cogs`, stale since the cogs/ scan landed #1163) and
  pointed it at the new parity guard.
- **`docs/owner/active-work.md`** — pruned the entirely-stale Active-claims list (every entry a
  now-merged PR; no open `claude/*` PRs remained → the duplicate-work signal was misfiring).
- **`docs/current-state.md`** ▶ Next action — appended the PR #1166 note + an honest "ungated
  self-merge depth is now thin" read for the next dispatch.
- Groomed `docs/ideas/cogs-layer-view-residence-guard-2026-06-14.md` (added the PR #1166 ▶ Update).

## Verification

- `python3.10 scripts/check_quality.py --full` → green (10944 passed, 44 skipped)
- `python3.10 scripts/check_architecture.py --mode strict` → clean
- `python3.10 scripts/check_docs.py --strict` + `check_current_state_ledger.py --strict` → clean
- The CI "failure" on the PR before this card flipped was the by-design born-red session gate
  (`check_session_gate: MERGE HELD — Status in-progress`), not a real failure.

## Context delta

The direct-`discord.ui.View` exception list lived in two hand-maintained homes (the hard arch
ratchet frozenset + the warn-only consistency-linter yml allowlist). They were in sync but only
*prose* asked a future editor to keep them so. Now a test enforces it — the two-sources-of-truth
class is closed for this pair. The broader cogs-layer *residence* guard (38 classes) still awaits an
owner decision (routed, not built — see the idea doc's ▶ Update / the run report below).

## 📤 Run report

- **Did:** pinned the `panel_base_class` consistency-linter allowlist to the `baseview_inheritance`
  arch conformance frozenset with a stdlib parity test (closes a two-sources-of-truth drift class),
  de-staled the yml comment, pruned stale active-work claims, sharpened the ▶ Next-action handoff ·
  **Outcome:** shipped
- **Shipped:** #1166 — `panel_base_class` ↔ conformance-frozenset parity guard + drift de-stale
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none new this run. (Standing/unchanged: the *residence* guard half of
  `ideas/cogs-layer-view-residence-guard-2026-06-14.md` — "must Discord view/modal classes live under
  `views/`, never inline in `cogs/`?" — remains routed, awaiting owner input.)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** the parity guard — promoted the previous run's (#1163) Q-0089 captured idea
  ("cross-allowlist drift guard") → build with no dispatch/owner ask (Q-0172). Contained, reversible,
  test-only.
- **↪ Next:** ungated self-merge depth is now thin. Prefer a **substantial `needs-hermes-review`
  lane** — consistency-linter AI-nav PR 1 (`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`,
  needs a runtime/Q-0086 live-walk) or procedures→skills Batch 2 (edits CLAUDE.md → hermes-review) —
  or **promote a fresh `docs/ideas/` idea → plan → build (Q-0172)**, over manufacturing a marginal
  guard. Bot-feature lanes (Explore-hub PR 2, fishing, feedback-board PR 1) stay owner/runtime-gated.

## 💡 Session idea (Q-0089)

**Collapse the `panel_base_class` allowlist to ONE source — derive the (path,class) set from the
conformance frozenset, keep only the reasons in the yml.** This run *pinned* the two copies together;
the cleaner end-state is to not have two copies of the *set* at all. Have the consistency linter load
its `panel_base_class` exempt-pairs from `_KNOWN_DIRECT_VIEW_SUBCLASSES` (the arch ratchet's ground
truth), and let the yml carry only per-entry `reason:` documentation keyed by `path::Class`. Then the
parity guard built this run becomes unnecessary (one source can't drift from itself), and adding a new
documented exception is a single edit. I deliberately did NOT do it this run — it couples the linter
(a `scripts/` tool) to a test module, which is backwards; the right move is to lift the frozenset into
a small non-test module (e.g. `architecture_rules/known_direct_views.py`) that both the conformance
test and the linter import. Genuinely worth having; lane = tooling/consistency, ~1 focused PR. Logged
not built to keep this PR single-purpose.

## ⟲ Previous-session review (Q-0102)

The previous run (`2026-06-20-arch-ratchet-cog-layer.md`, #1163) did the *right* thing well: it kept
its PR single-purpose (extend the ratchet to `cogs/`), explicitly deferred the cross-allowlist guard
to keep scope tight, and **captured that deferral as a Q-0089 idea** — which is exactly what let this
run pick it up cleanly. That is the self-improvement loop working as designed: a deferred-but-recorded
idea became the next run's shippable slice. One small miss: it left the *prose* in
`consistency_exceptions.yml` saying "8-entry frozenset" after it had grown the frozenset to 13 — a
stale-by-its-own-change comment (fixed here). **System improvement it surfaces:** the recurring pattern
is "a ratchet/allowlist is hand-mirrored in N files and a comment is the only thing keeping them in
sync." The durable fix is the Q-0089 idea above (one source of truth + reasons), but the *meta*-lesson
is worth a convention line: **when you extend a ratchet's scope, grep the sibling allowlist + its
comments for now-stale counts in the same PR.** Worth adding to the helper/consistency policy if it
recurs once more.
