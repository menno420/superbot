# 2026-06-18 — Paginated-select primitive (the #1040 select-truncation class, root fix)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-kv5zek`

## What I'm about to do

Empty scheduled fire — no work order. The live `▶ Next action` points at the
consistency-linter **triage/graduation** lane, and its `select_option_truncation`
rule has **53 candidates** — each an instance of the #1040 bug class (a select
front-truncates `[:25]`, silently dropping every option past Discord's 25-cap so a
user literally cannot pick it). Bugs-first.

The repo already carries **two near-identical windowed-select pagination
implementations** (`views/setup/sections/cog_routing.py` `_CogPickView` and
`views/help/editor.py` `EntityPickerView`) — and fixing 53 sites ad-hoc would breed
more. So the root fix is a **single shared primitive**:

- **PR 1 (this card):** build `views/paginated_select.py` — a canonical
  `PaginatedSelectView` (windowed single/multi select + ◀ Prev / Next ▶ nav,
  generalising the existing pattern), with unit tests; **dogfood** it by refactoring
  `cog_routing._CogPickView` onto it (delete the duplicate).
- **PR 2:** migrate the clearest standalone guild-scoped genuine-truncation pickers
  (roles delete/remove, channel move/category) onto the primitive.
- Triage the remainder (btd6/mining/settings/ux_lab): paginate genuine ones,
  allowlist legitimate bounded top-N displays in `consistency_exceptions.yml`.

Ledger: add the benign newest-merge lag (#1045, #1046) at close.
