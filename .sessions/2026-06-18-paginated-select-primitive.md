# 2026-06-18 — Paginated-select primitive (the #1040 select-truncation class, root fix)

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-kv5zek` · **PR:** #1047

## What this run did

Empty scheduled fire — no work order. The live `▶ Next action` pointed at the
consistency-linter **triage/graduation** lane; its `select_option_truncation`
rule flagged **53 candidates** — each an instance of the #1040 bug class (a
select front-truncates `[:25]`, silently dropping every option past Discord's
25-cap so a user literally cannot pick it). Bugs-first.

Rather than fix 53 sites ad-hoc (the repo already carried **two** near-identical
windowed-select implementations — `cog_routing._CogPickView` and
`help/editor.EntityPickerView`), I fixed the class at the root:

1. **`views/paginated_select.py` `PaginatedSelectView`** — a reusable windowed
   single/multi select (≤25-option pages + ◀ Prev / Next ▶ nav, optional
   `extra_items` preserved across page flips), generalising the two bespoke
   implementations into one primitive. +18 unit tests.
2. **Dogfooded** it: refactored `cog_routing._CogPickView` onto the primitive
   (deleted the duplicate paging classes; existing pagination tests updated).
3. **Migrated a second real consumer** — the role-delete picker
   (`ManagementPanel`): windows the deletable roles instead of `[:25]`
   (real >25-roles bug fixed), retiring the direct-`discord.ui.View`
   `_DeleteRoleView` → ratchets `panel_base_class` 30→29. Conformance +
   discord.py-compat tests updated.
4. **Triaged all 53 candidates → 31 genuine.** Allowlisted **22** false
   positives (embed/text top-N displays + bounded fixed-catalog selects) with
   per-callback reasons in `architecture_rules/consistency_exceptions.yml`.
5. **Fixed a latent linter bug** (bugs-first, on sight): the documented
   `::Class.method` allowlist scoping silently didn't work for
   `select_option_truncation` (it passed `qualname=''`). Added
   `_front_truncations_with_scope` so the finding now carries its enclosing
   class/method qualname — a file mixing a display slice with a real select can
   now allowlist only the display. +2 tests.
6. **Ledger:** added the benign newest-merge lag (#1045, #1046) to
   Recently-shipped; repointed `▶ Next action` with the handoff.

**Verification:** `check_quality.py --full` green (10650 passed, 38 skipped);
`check_architecture --mode strict` 0 errors; `check_consistency` warn-only.

## Handoff — what remains

The **31 remaining genuine `select_option_truncation` selects** are now
mechanical to migrate via `PaginatedSelectView`. Start with the standalone
ephemeral pickers (`roles/time_roles_panel`/`xp_roles_panel` remove-selects,
`channels/move_panel`/`visibility_panel`, `settings/subsystem_view` edit/reset,
`access/explorer`, `settings/edit_enum`). The mining market/recipe/gear panels
and the shared `selectors/` `Select` subclasses are embedded in multi-control
views → need per-consumer windowing (a host-view change, not a drop-in). These
touch runtime UX in persistent panels, so prefer small per-panel PRs with
eventual owner review over a batch migration. Then graduate the rule to error +
wire into `code-quality.yml` once it runs quiet on a clean tree.

## 💡 Session idea (Q-0089)

**A `PaginatedSelectView` graduation: make the genuine-select migration
self-checking.** Once a select is migrated, nothing pins that it stays
paginated. Idea: a tiny CI-runnable invariant (in the consistency-linter
family) that asserts every `views/` `discord.ui.Select` whose option source is
an *unbounded runtime collection* (a guild's roles/channels, a per-guild config
table) is either built through `PaginatedSelectView` or explicitly allowlisted —
turning the warn-only triage into a ratchet that can't regress. It reuses the
qualname-scoping just added. Worth having because the 31-item backlog will be
migrated piecemeal across sessions, and without a ratchet a new unbounded select
silently reintroduces the #1040 class. (Genuinely believe in this — it's the
"flip to error" graduation step (b) made precise rather than all-or-nothing.)

## ⟲ Previous-session review (Q-0102)

Previous run (#1044, consistency-linter rule 4) did the right thing shipping
the *detector* one-rule-per-PR — but it left **53 raw candidates** with the
allowlist empty and the rule's own message pointing at a private symbol
(`cog_routing._CogPickView`) as the canonical fix pattern. That coupled the
linter's guidance to an implementation detail with no shared primitive behind
it — so the "fix pattern" was copy-paste, not reuse, which is exactly what bred
the two duplicate implementations this run consolidated. **System improvement
surfaced & acted on:** a detector PR should land *with* the canonical fix
primitive (or a follow-up explicitly scoped to build it), not just the warning —
otherwise the triage backlog accumulates against a non-existent shared fix. This
run closed that gap (primitive + repointed message); the graduation idea above
keeps it from reopening.

## 📋 Doc audit (Q-0104)

- `check_current_state_ledger --strict`: #1045/#1046 added → expected green
  (verify in the close commit).
- New code is reachable: `views/paginated_select.py` is imported by
  `cog_routing` + `roles/management_panel`; the allowlist + linter change are
  in their canonical homes.
- No new owner decision this run (pure execution on the existing Q-0170 lane);
  no router entry needed.

## 📤 Run report

- **Run type:** routine · dispatch
- **PR:** #1047 (self-merge on green — small/contained refactor + tooling)
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none (executed the dispatched/standing `▶ Next action`
  consistency-linter triage lane; the latent linter-qualname bug fix is a
  bugs-first fix-on-sight within that lane, not a new self-promoted feature)
