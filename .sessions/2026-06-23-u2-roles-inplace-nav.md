# 2026-06-23 — U2 Roles & access panels: in-place nav + temproles reachability

> **Status:** `complete` — coordinator Phase-2 verified (2026-06-23): `!temproles` GAP→0 (surfaced via
> the Time Roles panel + allowlisted; stale `_BASELINE` emptied → reachability test green); the 2 Create
> buttons converted to true in-place. The 14 remaining `views/roles/` `edit_in_place` findings were
> independently re-verified against source as genuine sub-flow-picker / report-toast cases (matching the
> already-allowlisted `delete_btn`/`add_btn`/`run_btn` siblings) and are allowlisted in the coordinator PR
> #1375 — forcing `edit_message` would destroy the builder/draft context. Diff scoped to roles views +
> reachability test/baseline + temproles allowlist + mirrored test only. Both checks green on CI (sole red
> = the born-red gate). Flipped + merged by the coordinator (work by two U2 workers).
>
> Ultracode fleet **worker U2**. Born-red by design — the **coordinator** flips this
> badge and merges in Phase 2 (per the worker-scope contract).

## Arc

Ultracode Phase-1 leaf for Unit U2 (Roles & access panels), de-risked to a
views-only change. Two tasks:

- **Task A — `views/roles/` `edit_in_place` findings → fix the true navigation cases.**
- **Task B — fix the `!temproles` command-reachability GAP.**

## Shipped

### Task A — in-place navigation (16 findings triaged; 2 fixed, 14 reported)

The 16 `views/roles/` `edit_in_place` findings split into two classes against the
checker's own documented policy (`architecture_rules/consistency_exceptions.yml`):

- **2 true navigation inconsistencies → FIXED to `interaction.response.edit_message(...)`:**
  - `main_panel.py RoleHubView.create_btn` — its sibling hub buttons (`manage_btn`,
    `time_roles_btn`, `xp_roles_btn`, `reaction_btn`, `diagnostics_btn`) all navigate
    in place; **Create** was the lone outlier sending a fresh ephemeral. Now swaps the
    anchor to `RoleCreatePanel` in place.
  - `management_panel.py ManagementPanel.create_btn` — same hub-level navigation; now
    edits the anchor in place to `RoleCreatePanel`.
  - Made `RoleCreatePanel` carry a **Back button** when opened with a `parent`
    (mirrors `ManagementPanel`/`ReactionRolesPanel`/`TimeRolesPanel`), so the new
    in-place navigation is reversible. The back-builder tolerates a sync
    (`RoleHubView`) **or** async (`ManagementPanel`) parent `build_embed` via
    `inspect.isawaitable`.

- **14 GENUINE new-message sub-flow / report-toast cases → REPORTED to coordinator**
  (I do **not** edit the coordinator-owned `consistency_exceptions.yml`). Each is the
  *same class* as already-allowlisted role entries (`ManagementPanel.delete_btn`,
  `TimeRolesPanel.add_btn/remove_btn`, `DiagnosticsPanel.run_btn`): an interactive
  sub-flow picker / builder the operator drives next, with the parent re-rendering in
  place on completion — or a terminal action-result toast. Converting them in place
  would contradict the documented policy and lose the operator's draft/picker context.
  → see "Flagged for coordinator" below.

`views/roles/` `edit_in_place`: **16 → 14**. Repo-wide `edit_in_place`: **36 → 34**.

### Task B — `!temproles` reachability GAP → 0

- Added a **⏳ My Temp Roles** button to `TimeRolesPanel` (the role hub's time-related
  surface) that navigates in place to a new read-only `_TempRolesView` listing the
  viewer's active temporary grants — the no-arg `!temproles` form — read through the
  public `role_grants_service.list_active_grants` seam (pure read; no signature change).
  Modeled on #1372's `btd6strat` buttonization. The listing view has a Back button.
- Added the `temproles` entry to `architecture_rules/command_reachability_exceptions.yml`
  as reachable-via-panel, source-citing the new button (mirrors #1372's `btd6strat`
  entry). This is the one allowlist edit my scope permits ("ADD ONLY the `temproles`
  entry").
- `check_command_reachability`: **1 GAP → 0 GAP** (214 prefix commands, 75 reachable,
  139 exempt, 0 GAP).

### Tests (same PR)

`tests/unit/views/test_role_inplace_nav.py` — pins both Create buttons navigate in
place (edit, not send) + open a parented `RoleCreatePanel`; the back button presence;
the temp-roles button navigates in place; `_TempRolesView` reads the viewer's grants
and renders / empty-states correctly; its back button. 7 tests, all green. Existing
role view/cog suite (54 tests) still green.

## Verification

- `python3.10 scripts/check_quality.py --full` — (recorded at handoff)
- `python3.10 scripts/check_architecture.py --mode strict` — **0 errors** (only
  pre-existing `[known]` + unrelated `baseview_inheritance` warnings; none in my files).
- `python3.10 scripts/check_command_reachability.py` — **0 GAP**.
- `python3.10 scripts/check_consistency.py` — `views/roles/` `edit_in_place` 14 (all
  genuine new-message, awaiting coordinator allowlist).

## Files changed

- `disbot/views/roles/main_panel.py` — `create_btn` in-place navigation.
- `disbot/views/roles/management_panel.py` — `create_btn` in-place navigation.
- `disbot/views/roles/creation_panel.py` — `RoleCreatePanel` back button when parented
  (+ `inspect` import).
- `disbot/views/roles/time_roles_panel.py` — `temp_roles_btn` + `_TempRolesView`.
- `architecture_rules/command_reachability_exceptions.yml` — `temproles` entry (ADD ONLY).
- `tests/unit/views/test_role_inplace_nav.py` — new.
- `docs/owner/claims/u2-roles-inplace-nav.md` — claim (deleted at close).
- `.sessions/2026-06-23-u2-roles-inplace-nav.md` — this card.

## Flagged for coordinator

**14 `views/roles/` `edit_in_place` findings are genuine new-message cases — allowlist
them in `consistency_exceptions.yml`** (I must not edit it). They match the existing
allowlisted role pattern exactly. file:line · qualname · justification:

- `creation_panel.py:183` · `RoleCreatePanel.packs_btn` — opens the `RolePackView`
  bulk-create sub-flow; the creation panel re-renders in place on completion.
- `management_panel.py:110` · `ManagementPanel.edit_btn` — opens the role-edit picker
  (`_EditRolePickView` → modal); the panel re-renders in place via `_rerender` on submit
  (same class as the already-allowlisted sibling `delete_btn`).
- `management_panel.py:338` · `_ConfirmDeleteView.confirm` — terminal batched-delete:
  defers, then a per-role success/failure **report toast** via `followup.send` while the
  parent re-renders in place (same class as the allowlisted `run_btn` report toasts).
- `reaction_panel.py:141` · `ReactionRolesPanel.add_btn` — opens the `_AddSourceView`
  add-binding sub-flow (pick message → emotes → per-emote role pickers).
- `reaction_panel.py:176` · `ReactionRolesPanel.remove_btn` — opens a
  `PaginatedSelectView` binding-removal picker; panel re-renders in place after removal.
- `reaction_panel.py:237` · `ReactionRolesPanel.mode_btn` — opens a `PaginatedSelectView`
  per-message mode picker; panel re-renders in place after the mode is set.
- `role_menu_builder.py:605` · `RoleMenuBuilder.roles_btn` — opens the multi-role picker
  sub-flow that folds the selection back into the live builder draft (`_rerender`).
- `role_menu_builder.py:620` · `RoleMenuBuilder.colours_btn` — opens the colour/gradient
  auto-create sub-flow; folds new roles into the builder draft.
- `role_menu_builder.py:643` · `RoleMenuBuilder.packs_btn` — opens `RolePackView` with an
  `on_created` hook folding new roles into the builder draft.
- `role_menu_builder.py:671` · `RoleMenuBuilder.template_btn` — opens a starter-template
  picker; applies to the builder draft in place.
- `role_menu_builder.py:691` · `RoleMenuBuilder.card_btn` — opens the banner-card picker
  sub-flow; applies to the builder draft in place.
- `role_menu_builder.py:712` · `RoleMenuBuilder.theme_btn` — opens an embed-theme picker;
  applies to the builder draft in place.
- `role_menu_builder.py:733` · `RoleMenuBuilder.mode_btn` — opens a member-pick-mode
  picker; applies to the builder draft in place.
- `role_menu_builder.py:778` · `RoleMenuBuilder.channel_btn` — opens a channel picker for
  the post target; applies to the builder draft in place.

These 14 are the *field-editor / sub-flow picker* idiom: the builder/panel preview must
stay coherent behind the transient picker, so a fresh ephemeral is correct — exactly the
class the existing allowlist documents. (If the coordinator prefers an in-place redesign
of the whole role-menu builder instead, that's a larger UX change beyond this leaf.)

**Known limitation / unverified half:** the in-place Create navigation and the temp-roles
button are unit-tested but **not** live-verified in Discord (worker leaf — no runtime). The
back-builder's sync/async `build_embed` handling is the one subtle bit; covered by the
parented-panel test but worth a glance in live verification.

## Finish-worker addendum (2026-06-23, `claude/u2-roles-finish` → PR #1377)

A second Ultracode FINISH worker picked up where the foundation worker came to rest
early. Status stays `in-progress` (coordinator flips + merges in Phase 2).

- **Task A (was open) — DONE.** The reachability `_BASELINE` in
  `tests/unit/invariants/test_command_reachability.py` still listed the now-fixed
  `("disbot/cogs/role_grants_cog.py", "temproles")` entry, so
  `test_baseline_has_no_stale_entries` was FAILING (a HARD test failure). Emptied
  `_BASELINE` to `frozenset()` and updated the preceding comment to note all baseline
  gaps are cleared. `check_command_reachability.py` → **0 GAP** (214 cmds, 75 reachable,
  139 exempt); all 7 reachability tests green.
- **Task B (the 14 flagged `edit_in_place` findings) — re-verified, disposition unchanged.**
  Independently re-checked each of the 14 against live source (not rubber-stamped). The
  foundation worker's triage holds: all 14 are the genuine *field-editor / sub-flow picker
  / report-toast* idiom already documented-correct in `consistency_exceptions.yml`
  (matching the allowlisted `delete_btn`, `TimeRolesPanel.add_btn/remove_btn`,
  `xp_roles_panel.add_btn/remove_btn`, `run_btn` precedents). **0 additional FIXes; 14
  remain FLAGGED for coordinator allowlisting** (per-finding precedent in the coordinator
  report). `views/roles/` `edit_in_place` count stays 14 (the residual the coordinator
  clears by allowlisting). Forcing `edit_message` on any of these would contradict the
  checker's own documented policy and break the operator's picker/draft context.

## Context delta

- **Needed but not pointed to:** the decisive signal for triaging `edit_in_place`
  findings is the **existing `consistency_exceptions.yml` allowlist reasons** — they
  encode the coordinator's "sub-flow picker / report toast = genuine new-message" policy.
  The Ultracode worker prompt and the shared-dependency map don't point at it; reading it
  first is what let me classify 16 findings correctly instead of mechanically converting.
- **Pointed to but didn't need:** CodeGraph — this was a contained, file-local change;
  reading the checker source + grep carried it (matches the CLAUDE.md "reach for the right
  tool by task size" guidance).
- **Discovered by hand:** the `edit_in_place` checker clears a finding when the callback
  calls a **same-class in-place helper** (`self._rerender()` → `self.message.edit`), not
  only a direct `interaction.response.edit_message` — so threading the anchor `message`
  to a sub-view and re-rendering it counts as in-place. Only lives in the checker source
  (`_inplace_helper_names` / `_calls_inplace_helper`).
- **Decisions made alone:** (1) homed the `!temproles` surface on the **Time Roles**
  panel (closest conceptual hub neighbour for "temporary roles"); (2) treated 14 of 16
  findings as genuine new-message and reported rather than force-converting — both
  reversible and consistent with documented policy.

## ⚑ Self-initiated

None beyond the assigned U2 tasks. No idea promoted to a plan/implementation this session.

## 🛠 Friction → guard

**Friction:** invoking a `@discord.ui.button` callback in tests — `Cls.method.callback`
fails (`'function' has no attribute 'callback'`); the working idiom is to call the
decorated method directly (`Cls.method(view, interaction, button)`), already used by
`test_role_management_panel.py`. **Guard:** the new test file uses the correct idiom and
documents it inline; this is a recurring test-authoring footgun → candidate journal Rule
(noted), not worth a checker.

## 💡 Session idea

A tiny checker/test asserting **every role-hub navigation button** (a button whose body
constructs a `views/roles/*Panel`/`*View` and opens it) uses `edit_message`, not
`send_message` — the inverse of the `edit_in_place` allowlist. The current rule warns on
the *symptom* per-callback; a positive "hub navigation must swap in place" assertion would
have caught the `create_btn` outlier structurally (siblings navigate in place, it didn't)
rather than relying on a human noticing the inconsistency. Worth ~20 lines if the pattern
recurs across other hubs (channels, settings). Believe in it: it encodes the owner's
"headline inconsistency" as a structural invariant, not a warn-only lint.

## ⟲ Previous-session review

The predecessor (coordinator session `claude/laughing-bohr-xdlits` @ `c23448f`,
#1373/#1374) did the Ultracode partition groundwork well — the
`shared-dependency-ownership-map.md` + `worker-scope-template.md` made this leaf genuinely
self-contained, and de-risking U2 to views-only (fencing the held `role_*_service`
signatures + `subsystem_registry`) was exactly the right call: I never needed to touch a
forbidden file. **What it could improve:** the worker prompt lists the 16 `edit_in_place`
findings as a flat "drive to 0" target without flagging that the repo's *own*
`consistency_exceptions.yml` already documents most of them as a *correct* pattern — a
worker reading the prompt literally could over-convert and regress UX. **System
improvement it surfaces:** the worker-scope template should add a standing line — *"before
fixing a lint finding, read that checker's allowlist reasons; many 'findings' are
documented-correct cases to report, not convert."* That's a docs change to
`docs/ultracode/worker-scope-template.md` (free to ship) — proposing it here for the
coordinator since editing the shared Ultracode docs mid-fleet risks a collision with the
coordinator's own edits.
