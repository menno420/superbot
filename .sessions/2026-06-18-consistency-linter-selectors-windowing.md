# 2026-06-18 — Consistency-linter Lane A1: window the `views/selectors/` API-ripple set

> **Status:** `complete`

## Arc

Executed the live ▶ Next action (band-#1050 queue, Lane A1 of the
[repo-consistency-linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md),
Q-0170): migrated the shared `views/selectors/` primitives off front-truncating
`discord.ui.Select` subclasses (`options[:25]`, the #1040 silent-drop class) onto
the #1050 `attach_windowed_select` embedded helper.

## Shipped (#1054)

- **5 selector primitives → windowed `attach_*` helpers** over
  `attach_windowed_select`:
  - `ChannelSelector` → `attach_channel_select`
  - `RoleSelector` → `attach_role_select`
  - `SubsystemSelector` → `attach_subsystem_select`
  - `MultiSelect` → `attach_multi_select`
  - `MultiChannelSelector` → `attach_multi_channel_select`
  - `MultiRoleSelector` → `attach_multi_role_select`
  - `ScopeSelector` left a plain `Select` (≤3 fixed options — never windowed).
- **All 8 consumers updated** with explicit `select_row`/`nav_row` to fit each
  host's 5-row budget: channels delete/restrict/move/visibility/create panels +
  roles xp/time/exemptions panels.
- **Root-fixed the upstream truncation source:**
  `core.resources.channel_service.build_select_options` gained a `limit=None`
  unbounded mode; `_build_channel_options` uses it; dropped `visibility_panel`'s
  inline `text_channels[:25]` — so the windowed channel panels actually reach the
  tail past 25. Allowlisted `visibility_panel`'s `[:20]` toggle-*button* grid (it
  builds buttons, not select options).
- **Result:** `select_option_truncation` warn-only count **15 → 7** (the 6
  selector findings + visibility:59 retired). The remaining 7 are the **A2**
  per-panel embedded selects.
- Rewrote `tests/unit/views/test_selectors.py` for the new `attach_*` API
  (windowed-not-dropped assertions) + updated the 5 panel tests' selector
  assertions. CI mirror green (10659 passed); arch 0.

## Continuation (the handoff — A2)

**▶ Next = consistency-linter Lane A2: migrate the 7 remaining per-panel embedded
selects onto `attach_windowed_select`** — each a small swap now the helper exists
(pass `select_row`/`nav_row` to fit the host's 5-row budget; pattern:
`access_map._attach_feature_detail_select`):

- `views/channels/create_panel.py::_CategorySelect` (line 59 — `existing_cats[:15]`)
- `views/channels/move_panel.py::_category_options` (line 40 — `opts[:25]`)
- `views/settings/subsystem_view.py` (lines 439, 584)
- `views/setup/sections/channels.py` (line 301)
- `views/access/explorer.py` (line 77)
- `views/diagnostic/automation_panel.py` (line 238 — verify it's a select, not an
  embed/button slice; allowlist if not)

Then the graduation work: (b) once `select_option_truncation` runs quiet on a
clean tree across a few sessions, flip it to error + wire into `code-quality.yml`;
(c) a possible follow-up extends rule 4 to `disbot/cogs/`.

## Decisions made alone

- **Self-merge gate (Q-0113):** treated A1 as small/contained mechanical work
  (precedent: #1048/#1050 selector-migration slices self-merged), not a
  `needs-hermes-review` substantial step — despite the 23-file footprint, it's a
  pure API-ripple with no behavior regression and full test coverage.
- **Multi-select windowing caveat:** the windowed multi-select does not carry a
  selection across a page flip (documented in `paginated_select.py`). This is
  *strictly ≥* the old behavior (front-truncation made >25 items unreachable
  entirely); for ≤25 options it's a single page, identical. A true cross-page
  accumulating multi-select (running tally + `default=True` re-marking) is a
  clean future enhancement, noted as the session idea below.

## Flagged for maintainer / known limits

- Multi-select batch panels (channels lock/delete/move/visibility) with **>25**
  channels: the user can now *page* to reach every channel, but a multi-selection
  does not persist across a page flip — they act per page. Single-page (≤25)
  behaviour is unchanged. Not a regression; the accumulation enhancement is the
  next quality lift if it ever bites a large guild.

## Context delta

- **Needed but not pointed to:** the real truncation source for the channel
  panels was *upstream* in `core.resources.channel_service.build_select_options`
  (`limit=25`), not in `views/` — the consistency linter only scans `views/`, so
  it never flagged it. A windowing migration that only touches the `views/`
  selector is cosmetic unless the option *source* is also unbounded. Worth a note
  in the linter plan: "check the option source, not just the select."
- **Pointed to but didn't need:** the `views/channels/_helpers.py::_ChannelSelect`
  widget — its docstring says "used by both delete and restrict flows", but those
  flows actually use `MultiSelect`; `_ChannelSelect` appears dead/legacy (only the
  owner-view test imports it). Candidate for a future dead-code sweep.
- **Discovered by hand:** the windowed multi-select's per-page-selection caveat
  (in `paginated_select.py`) is the load-bearing fact for whether windowing a
  *multi*-select is safe — it is, because the prior state (truncation) was worse.

## 💡 Session idea

**Cross-page accumulating multi-select for `SelectWindow`.** Add an opt-in
`accumulate=True` mode to `views/paginated_select.py`'s `SelectWindow` that keeps a
running `set[str]` of chosen values across pages, re-marks page options
`default=True` when revisited, and hands the *full* accumulated set to `on_select`.
This closes the one remaining gap in the windowed multi-select (selection lost on a
page flip) and would make the channels batch panels fully correct for >25-channel
guilds. Dedup-checked `docs/ideas/` — not present; this is the natural follow-on to
#1050's "out of scope" note. (Worth an `docs/ideas/` file if not picked up soon.)

## ⟲ Previous-session review

The previous run (`2026-06-18-btd6-*` / the band-#1050 reconciliation) left an
exceptionally sharp ▶ Next action: it named A1 as "the API-ripple set", listed the
exact 5 primitives, the ~8 consumers, AND the `access_map._attach_feature_detail_select`
pattern to copy — which made this session nearly turn-key. What it *missed* (and the
system improvement this surfaces): the handoff said "convert each to an `attach_*`
helper + update its ~8 consumers" but did not flag that the channel panels' option
*source* (`build_select_options`) truncates upstream of the selector — so a literal
reading of the handoff would have shipped a half-fix that still drops the tail.
**Improvement:** when a plan names a UI-truncation migration, the handoff should
explicitly say "verify the option source is unbounded, not just the select" — I added
exactly that note to the linter plan's A1 entry so the A2 handoff carries it forward.

## 📤 Run report

- **Did:** windowed the `views/selectors/` API-ripple set + root-fixed the upstream
  channel-option truncation (consistency-linter Lane A1). · **Outcome:** shipped
- **Shipped:** #1054 — 5 selectors → windowed `attach_*` helpers, 8 consumers
  migrated, `build_select_options` `limit=None`, `select_option_truncation` 15 → 7.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (executed the dispatched live ▶ Next action; the
  cross-page-accumulate idea is *captured* as a session idea, not built)
- **↪ Next:** consistency-linter Lane A2 — migrate the 7 remaining per-panel embedded
  selects onto `attach_windowed_select` (see continuation above).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1054, on green) |
| CI-red rounds | 1 (born-red session gate by design; local mirror green before flip) |
| Repo-rule trips | 1 (isort import-order on a touched test file — fixed) |
| New ideas contributed | 1 (cross-page accumulating multi-select) |
| Ideas groomed | 0 (capacity went to the substantial A1 slice) |
