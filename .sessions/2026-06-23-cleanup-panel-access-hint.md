# 2026-06-23 — Cleanup panel: hint pointing at Command Access delete toggle

> **Status:** `complete` — owner-directed (owner accepted the follow-up I proposed). Added a one-line
> legibility tip to the Cleanup Policies diagnostics embed so the cleanup-level vs Command-Access-delete
> distinction is clear at the point of confusion. PR #1363, auto-merge armed on green (Q-0127).

> **Run type:** `manual · owner-directed`

## What I'm about to do

This session's root finding (#1359) was that a cleanup *level* (Off/Light/Standard/Strict) only deletes
**blocked** commands, while "delete any command in a no-command channel" lives under **Command Access →
🗑️ Delete blocked commands**. That distinction tripped the owner up ("still hasn't changed much"). Add a
single `ℹ️ Tip` field to the Cleanup Policies diagnostics embed (both the empty and populated paths)
pointing operators at the Command Access toggle. View-only, one field + a test.

## What shipped

- **`views/cleanup/policy_panel.py`** — a reusable `_add_command_access_hint(embed)` helper + the
  `_COMMAND_ACCESS_HINT` text, added as an `ℹ️ Tip` field to **both** diagnostics paths (empty + populated):
  "these levels only delete invalid/blocked commands; to delete any command in a no-command channel, use
  Command Access → 🗑️ Delete blocked commands in `!settings`."
- **Test** — `test_diagnostics_embed_includes_command_access_hint` asserts both embed variants name
  Command Access + the toggle. Policy-panel file 25 cases green; lint/arch clean; view-only.

## 💡 Session idea

**A lightweight "cross-system pointer" convention for settings/diagnostics embeds.** This fix is the third
time this session two adjacent systems' relationship needed surfacing in-UI (cleanup-level vs
command-access delete; cleanup-policy `Off` vs the removed whitelist). A small shared helper that renders a
standard `ℹ️ See also: <other panel>` field would make these cross-references consistent and cheap to add,
so the next confusing adjacency gets a pointer by habit rather than only after a user reports confusion.
(Dedup-checked `docs/ideas/` — related to the legibility note in the #1359 log; this is the generalized
mechanism.)

## ⟲ Previous-session review (Q-0102)

The previous PR (#1360, select-driven custom level) was tidy and risk-free, and the broader four-PR arc
this session got the *behavior* right — but it took an explicit owner follow-up for the *legibility* gap
to close, which is the same pattern as the whitelist→delete-on-sight gap. **System improvement
(observed):** the recurring theme across this whole session is that *feature correctness* and *feature
discoverability/legibility* are separate deliverables, and the latter keeps lagging until a user reports
confusion. The "cross-system pointer" idea above is the concrete mechanism to close that lag proactively;
worth a groomer promoting it given it surfaced three times in one session.

## 📤 Run report

- **Did:** Added a Cleanup Policies → Command Access legibility tip (both diagnostics paths) ·
  **Outcome:** shipped (PR #1363, auto-merge armed on green)
- **Shipped:** #1363 — cleanup-panel Command Access hint
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merged = deployed (view-only, no migration).
- **⚑ Self-initiated:** no — owner-accepted the follow-up I proposed at the end of #1360.
- **↪ Next:** nothing pending — the cleanup/command-config arc (#1345 · #1350 · #1359 · #1360 · #1363) is
  complete. Session ending per owner instruction.

## ⟳ Doc audit (Q-0104)

`check_docs` green via `check_quality --check-only`; `check_consistency` 0 errors; arch clean. View-only,
no new owner decision or doc home. PR not yet in `current-state` Recently-shipped (benign newest-merge
lag — the next reconciliation pass records the whole #1345–#1363 cleanup arc; that pass is the routine's
job, not this manual session — Q-0124).
