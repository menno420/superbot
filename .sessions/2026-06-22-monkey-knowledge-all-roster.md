# 2026-06-22 — "list all monkey knowledge" regression (whole-catalog MK roster)

> **Status:** `complete`

Owner-directed (live Discord screenshots). The bot refused "list all monkey
knowledge" / "list all monkey knowledge and their buffs" with the
version-stamped no-data message, but answered "list all **primary** monkey
knowledge" fine — a clear regression on the un-scoped (all-tabs) ask.

## Root cause

`deterministic_mk_category_roster_reply` (BUG-0009 §7.6 MK roster floor) required
a recognised tab (Primary/Military/Magic/Support/Heroes/Powers) and returned
`None` otherwise. So "list all monkey knowledge" (no tab) had **no deterministic
builder**, fell through to the model, and the model's 70+ item list tripped the
value-only faithfulness guard → the version-stamped refusal. The all-tabs data
already existed (`monkey_knowledge_by_category()` returns every tab) — nothing
served it for the no-tab case. The per-tab ask worked because "primary" matched a
tab cue and the code-built grounded list answered.

## Shipped

- **`disbot/services/btd6_context_service.py`** —
  - New `_MK_ALL_ROSTER_RE`: a *strong* whole-catalog cue (all/every/list/
    complete/full/entire/how-many/are-there), a deliberate subset of
    `_MK_ROSTER_LIST_RE` that **excludes a bare which/what** (those fire on a
    single-MK effect lookup, "what does More Cash do", which must still defer).
  - New `_all_mk_roster_reply(grouped)` helper: every non-empty tab grouped,
    `**All Monkey Knowledge (N) by tab:**` + per-tab sections. No length cap —
    the natural-language stage chunks via `_split_for_discord`.
  - Restructured `deterministic_mk_category_roster_reply`: moved the tower-defer
    check ahead of the tab match, then — when no tab is named — require the
    strong cue and serve the whole-catalog roster instead of returning `None`.
- **`tests/unit/services/test_btd6_mk_category_roster.py`** — 5 new tests: all
  tabs listed when no tab named, every point covered, "how many" routes to it,
  dispatcher routes the whole-catalog roster, and it is the **only** builder that
  fires on "list all monkey knowledge" (exclusivity preserved).

Verified: `check_quality --full` ✓ (11649 passed, 47 skipped, 2 xfailed) ·
`check_architecture --mode strict` 0 errors · MK-roster + floor-exclusivity
suites green (46 passed).

## ⚑ Self-initiated

No — owner-directed (the maintainer posted the failing Discord exchange and
asked to find/fix the regression). PR #1316 opened ready, auto-merge armed; per
Q-0191 owner-directed work is never held for review.

## 💡 Session idea (Q-0089)

**A "deterministic floor coverage" sim/guard for the BUG-0009 roster family.**
This regression is the third of a recurring shape: a roster builder handles the
*scoped* ask (per-tab, per-tower) but silently has **no branch for the
broad/un-scoped ask**, which then refuses. A small stdlib check could enumerate,
for each roster domain (MK, relics, heroes, towers, bloons…), the canonical
"list all X" / "list all X in tab Y" phrasings and assert each returns a
non-`None` deterministic reply — turning "an agent noticed a live refusal" into a
CI gate. Genuine because the same class has now bitten MK twice (the
"related to the farm" mis-group and this all-tabs miss).

## ⟲ Previous-session review (Q-0102)

The prior MK work (BUG-0009 §7.6) built the per-tab roster cleanly and even left
a precise docstring explaining *why* the deterministic layer must own the
grouping — that documentation is what made this root-cause a 20-minute find. What
it **missed**: it scoped the builder to "a named tab" and never asked "what about
no tab at all?", leaving the most natural phrasing ("list all monkey knowledge")
to refuse. The system improvement is the §7.6 idea above: the builders are narrow
by design (good), but narrowness needs a coverage guard so the *un-scoped*
phrasing isn't a silent gap. Each new roster domain should ship with a "list all"
smoke assertion, not just per-scope tests.

## 🔎 Doc audit (Q-0104)

- `check_quality --full` ✓ · `check_architecture --mode strict` 0 errors.
- No owner-decision/router change (a bug fix, not a policy change).
- No `current-state` ledger touch — recorded by the auto-triggered Q-0107
  reconciliation pass (next at #1320). Unmerged PR #1316 correctly absent.
- Behaviour change documented in-code (builder docstring + `_MK_ALL_ROSTER_RE`
  comment); the §7.6 subsystem prose already describes the roster family, so no
  doc drift.

## Context delta

- **Needed but not pointed to:** nothing missing — `context_map.py` +
  `docs/subsystems/btd6.md` and the builder's own docstring pointed straight at
  the failure. The BUG-0009 dispatcher's "narrow builders, exclusivity invariant"
  design made the fix a contained one-branch addition.
- **Pointed to but didn't need:** the MK↔tower relation machinery
  (`deterministic_mk_reference_reply`) — relevant only as the thing to defer to
  when a tower is named, not part of the fix.
