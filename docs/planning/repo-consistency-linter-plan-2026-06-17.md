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
| 4 | **Select-option truncation** | a select-building view that *front-truncates* a collection (`options[:25]`, `roles[:25]`) instead of paginating — Discord caps a select at 25 options, so the slice silently drops the tail (the **#1040** class) | surfaced by #1040 + the previous session's session-idea; allowlist a genuine top-N *display* truncation |
| 5+ | (grow as the owner / reviews surface more) | … | each new mechanical-consistency rule the review inbox turns up |

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
2. **PR 2 (rule 2, back button) + PR 3 (rule 3, panel base-class) — SHIPPED 2026-06-18**
   (one session, same warn-only house pattern). **Rule 2** flags a `HubView` panel that
   declares its own `@ui.button`/`@ui.select` callbacks but whose **module** references no
   back affordance (`views/navigation.py`'s `attach_back_*` / `chain_back` helpers, or a
   back-labelled button) — **first-run count: 7** (mostly top-of-stack hub openers, the known
   external-attach FP; allowlist left empty, warn-only). **Rule 3** flags a class extending
   `discord.ui.View` **directly** outside the `views/rps`/`views/blackjack` game-state
   allowlist + the `views/base.py` framework home — **first-run count: 30** (the AI picker /
   settings-select / btd6-admin views; the arch-doc prose rule, now mechanical). Tests:
   positive + negative (edits-via-base, path-allowlist, framework-home, no-controls, helper,
   back-button) + allowlist fixtures for each rule.
   **PR 4 (rule 4, select-option truncation) — SHIPPED 2026-06-18** (same warn-only
   house pattern). Scopes to `views/` files that construct at least one
   `discord.SelectOption`; flags a *front* slice `expr[:N]` (lower `None`/`0`, upper
   integer constant **≤ 25**, no step). **First-run count: 53** — proving the #1040
   silent-drop is a *widespread* class, not an isolated bug (shared `selectors/`,
   roles/channels panels, mining market, btd6 browsers, settings enum-editor all
   truncate select options). Windowed pagination (`x[start:start+N]`, variable bounds)
   and string-length slices (`label[:100]`, N > 25) are correctly **not** flagged. A
   small subclass of the 53 are genuine top-N *display* truncations (e.g. a preview
   `operations[:10]`, an error-message `valid_towers[:8]`) — allowlist those during
   triage; the rest are real selects to paginate. Tests: positive (front-truncated
   options) + windowed / string-limit / non-select / cogs-scope / allowlist negatives.
   *Possible follow-up:* extend rule 4 to `disbot/cogs/` (the SelectOption module-gate
   keeps leaderboard `[:10]` slices out) if a cog-level select truncation ever surfaces.
   **Select-truncation migration — standalone pickers (#1048, 2026-06-18):** the three
   *cleanly standalone single-select ephemeral pickers* moved onto the shared
   `views/paginated_select.py` `PaginatedSelectView` — `EnumSettingSelectView`/`_EnumSelect`
   (→ `build_enum_select_view`), `_TimeRemoveView`/`_TimeRemoveSelect`, and
   `_XpRemoveView`/`_XpRemoveSelect`. Each retired **both** its `select_option_truncation`
   and `panel_base_class` finding (counts 31→28 and 29→26) and ratcheted the
   `baseview_inheritance` arch debt 12→9. The remaining 28 `select_option_truncation`
   candidates are all **embedded in multi-control views** (selectors/, mining, subsystem_view,
   channels move/visibility panels, access/explorer): `PaginatedSelectView` is a *standalone*
   view, so they need either a new windowed-*embedded*-select helper or per-view ◀/▶ nav — a
   design step that warrants its own focused PR.
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
