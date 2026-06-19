# 2026-06-19 — Consistency-linter: triage the `back_button` backlog (rule 2)

> **Status:** `complete`

## Arc (what I'm about to do)

Third slice of this dispatch run (after #1058 edit_in_place triage). Triage the consistency linter's
**`back_button` rule (7 findings)** — the last untriaged warn-only backlog
([plan](../planning/repo-consistency-linter-plan-2026-06-17.md)).

**Investigation:** traced each flagged `HubView`'s construction site. **All 7 are top-of-stack ROOT
panels** opened directly by a cog command (no parent to return to), the known FP class the plan and
rule docstring predicted:

- `AccessExplorerView` — settings cog `send_panel` (root).
- `_ChannelManagerView` — the root of the channels stack; its sub-panels (create/delete/visibility/move)
  restore back *to* it.
- `CleanupPolicyPanelView` — cleanup cog command (root).
- `AutomationPanelView` — `!platform automation` via `open_panel` (not a child of the platform/diagnostics
  hub — the hub doesn't open it; `platform_panel` only imports its embed builder).
- `_DiagnosticsHubView` — diagnostic cog command (root hub).
- `DeathmatchPanelView` — deathmatch cog command (root).
- `_XpHubView` — xp cog command (root hub).

## Shipped (#PR)

- Added the `back_button:` section to `architecture_rules/consistency_exceptions.yml` with 7 per-class
  entries, each citing the root-panel reason + a re-verify note ("if a future root is opened FROM
  another panel it needs a back button, not an allowlist entry"). `back_button` warn-only **7 → 0**.
- No code/view change: there is no genuine missing-back-button bug right now — the rule's real target
  is a *child* sub-panel without a back affordance, and it will still catch a future one (entries are
  scoped per root class). `test_back_allowlist_suppresses_by_class` already pins the mechanism.
- Consistency tests green (29 passed); the rule runs clean on the whole tree.

## Continuation (the handoff)

Three consistency rules are now at **0** on a clean tree — `select_option_truncation` (#1056),
`panel_base_class` (#1057), and `back_button` (this slice). Per plan step 3, graduate each once it
stays clean across a couple more sessions: flip to `error` + wire into `code-quality.yml`. **Rule 1
(`edit_in_place`) cannot graduate** until the AI-nav redesign clears its remaining 17 — promote
`ideas/ai-panel-inplace-navigation-2026-06-11.md` to a `docs/planning/` plan (Q-0172) to unblock it.

## Context delta

- **Pointed to and needed:** the plan's first-run note ("back_button=7, mostly top-of-stack hub
  openers, the known external-attach FP") set the exact expectation; verified each rather than
  trusting it (Q-0120) and it held for all 7.
- **Discovered by hand:** that `AutomationPanelView` is a *root* (`!platform automation`), not a child
  of the platform hub — `platform_panel` imports only its embed builder, not the view. Recorded in the
  allowlist reason.

## ⟲ Previous-session review (Q-0102)

The immediately previous slice (#1058, this run) correctly *fixed the checker's blind spot* before
mass-allowlisting (the `_rerender` FP). This slice applied the same discipline in reverse: it confirmed
the back_button rule has **no** blind spot to fix here — all 7 are genuine roots, so allowlisting (not a
code change, not a rule change) is the right move. **System improvement:** the linter lane would benefit
from a shared "is this view a root or a child?" helper — both the back_button triage (roots are exempt)
and a future graduated rule need that distinction, and right now each triage re-derives it by hand
(grepping construction sites). A small `views/navigation` introspection (does any module construct this
class as a *child* of another panel?) could turn the root/child judgment into a rule input. Captured as
the session idea.

## 💡 Session idea (Q-0089)

**A root-vs-child classifier for the consistency linter.** The back_button rule's entire FP class is
"root panels have no parent to go back to." Today that's resolved by hand-grepping each panel's
construction sites. A small AST pass — "class X is a *child* if any other view module constructs `X(...)`
inside a `@ui` callback / passes a `parent=`/anchor, vs. only a cog command constructs it" — would let
back_button (and any future nav rule) flag *only children* missing a back affordance, eliminating the
root FP class structurally instead of via a growing allowlist. It generalizes the manual trace this
slice did. Dedup-checked the plan + `docs/ideas/`: distinct from #1058's `--diff` baseline idea (that's
about regression-guarding; this is about a smarter rule input). Worth having; captured, not built.

## 📊 Doc audit (Q-0104)

- Updated the linter plan (back_button triage + "three rules at 0" graduation note) and current-state
  ▶ Next action.
- No new owner decisions; no router entry.
- Ledger lag (#1053/#1055) unchanged — benign newest-merge lag deferred to the #1080 reconciliation
  pass per the prior sessions' standing decision (see #1058's card doc audit).

## 📤 Run report

- **Did:** triaged consistency rule 2 (`back_button`) — verified all 7 findings are top-of-stack root
  panels and allowlisted them with per-class reasons; `back_button` 7 → 0. · **Outcome:** shipped
- **Shipped:** #PR — `consistency_exceptions.yml` `back_button:` section (7 entries) + plan/current-state
  updates.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (continued the dispatched consistency-linter initiative — the #1058
  handoff named back_button as the next slice).
- **↪ Next:** graduation prep for rules 2/3/4 (all at 0); promote the AI-nav idea to a plan (Q-0172) to
  clear rule 1's 17.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session (run total) | 2 (#1058 edit_in_place · this PR back_button) |
| `back_button` findings | 7 → 0 |
| Roots verified by construction-site trace | 7 |
| CI-red rounds | 1 (born-red session gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (root-vs-child classifier for the linter) |
