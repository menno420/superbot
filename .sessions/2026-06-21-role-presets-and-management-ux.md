# 2026-06-21 — Role presets + role-management UX overhaul

> **Status:** `complete` — owner-directed (Q-0191 → merge on green). PR #1245.

> **Run type:** `manual` (owner-directed, screenshots + in-chat requirements)

## Arc

Owner-directed from a `!roles` → 🔧 Diagnostics screenshot ("Role Automation ⚠️ missing: Neu,
Normal, Iron, Gold, Diamand, Netherite, Beacon") plus three follow-up UX asks (Create/Edit/Delete
screenshots). Four threads, all inside the role-management subsystem
(`disbot/views/roles/` + `cogs/role_cog.py` + `_helpers`):

1. **Removed the hardcoded German/Minecraft tier names.** Deleted `_DEFAULT_THRESHOLDS`
   (`Neu/Normal/Iron/Gold/Diamand/Netherite/Beacon`) and the `_ensure_defaults` seed routine
   entirely (4 call sites: `main_panel`, `role_cog` ×3). Role automation now loads **only roles that
   exist on the server**. The "🔄 Seed Defaults" button (which seeded those names) is replaced by a
   **🧹 Clear Missing** button that bulk-clears stale/phantom threshold rows through the audited
   `role_automation.clear_time_threshold` seam — directly clears the "missing:" diagnostics line.
2. **Create role** is now a *menu* (`RoleCreatePanel`): a **preset role-name** select
   (`ROLE_PRESETS` — 6 generic roles) + a **colour preset** select (`_COLOR_OPTIONS`), with
   **✏️ Custom…** still opening the full free-text modal. Presets are surfaced **only here**
   (owner constraint) — never in automation/diagnostics. Create routes through the audited
   `RoleLifecycleService`, then offers the same XP-automation follow-up as the modal.
3. **Edit role** opens a **role picker** (windowed, filtered to bot+admin-manageable via
   `manageable_roles`) → the edit modal, instead of typing the role name. The modal shows the
   chosen role in its title and edits id-first.
4. **Delete role** is a **multi-select** of deletable roles → an explicit **confirmation** listing
   every role → batched delete via `RoleLifecycleService`. (Was: single-select, immediate delete.)

## Findings / decisions

- **`RoleLifecycleService` is the only sanctioned `create_role`/edit/delete caller** (allowlisted by
  `tests/unit/invariants/test_no_silent_auto_create.py`, audited). Every create/edit/delete path —
  the new preset Create, the edit modal, the batched delete — routes through it; no raw
  `guild.*_role`. (Learned from the #1237 session card; still not in the orientation route.)
- **Decision made alone — presets are a `views/roles/_helpers` constant, not persisted.** "A few
  presets" → 6 generic roles (Member/Verified/VIP/Moderator/Admin/Muted) with palette colours, not
  the old server-specific tiers. Per-guild custom presets are deferred (see Session idea).
- **Decision made alone — the modal-can't-hold-a-select constraint forced Create into a panel.**
  Discord modals only contain text inputs, so "pick a preset name + colour" can't live *inside* the
  Create Role modal; the three entry buttons (`main_panel`, `role_cog` persistent view,
  `management_panel`) now open `RoleCreatePanel` (an ephemeral view) instead of `send_modal`.
- **Decision made alone — "Clear Missing" over leaving the phantom rows.** The German names showed
  as "missing" because old seeding persisted them; removing the code doesn't purge live DB rows, so
  the operator needs a one-click purge. Scoped to the time field (`clear_time_threshold`), which is
  exactly what the diagnostics "missing:" line reads.
- **Edit/Delete pickers filter via `utils.role_feasibility.manageable_roles`** (bot perms +
  hierarchy + @everyone/managed) so the picker only offers roles the action can succeed on.

## Context delta

- **Needed but not pointed to:** that `RoleLifecycleService` is the *single* allowlisted role-object
  mutator — discovered via the #1237 session card, not the orientation route. Same gap that card
  flagged; worth an `AGENT_ORIENTATION` line "runtime role create/edit/delete → only via
  `RoleLifecycleService`".
- **Reusable building blocks that saved time:** `views.selectors.attach_role_select` /
  `attach_multi_role_select` (windowed, #1040-safe) gave the edit picker + delete multi-select for
  free; `manageable_roles` gave the filter. No bespoke selects needed.
- **Two invariants caught real drift during `--full`:** `test_no_raw_defer` (a defensive
  `interaction.response.defer()` in the preset callback → `safe_defer`) and the mypy `name-defined`
  on a *fourth* `_ensure_defaults` call site I'd missed (the persistent-view `time_roles_btn`). The
  CI mirror earned its keep.
- **Decisions made alone:** see Findings (presets-as-constant; panel-not-modal; Clear-Missing).
- **Weak point / unverified:** the new panels are unit-tested with Discord mocked; **not live-walked**
  on a real guild. The multi-page multi-select delete carries the documented caveat (selection does
  not persist across a >25-role page flip) — fine for typical servers, noted in `paginated_select`.
- **One docs/tooling change that would help:** the orientation line above
  (`RoleLifecycleService` as the one role mutator).

## 📤 Run report

- **Did:** removed hardcoded German tier names + seeding; Create-menu name/colour presets;
  Edit-by-select; Delete multi-select + confirm; Clear-Missing purge · **Outcome:** shipped
  (PR #1245, auto-merge on green)
- **Shipped:** #1245 — role presets + role-management UX overhaul
- **Run type:** `manual`
- **CI:** `check_quality.py --full` green (11328 passed, 47 skipped); arch strict 0 new; mypy clean.
- **⚑ Owner decisions needed:** none (owner-directed). Preset *names/colours* are a judgement pick —
  trivially editable in `views/roles/_helpers.py` `ROLE_PRESETS` if you want a different set.
- **⚑ Owner manual steps:** Merge ≠ deploy — prod restart stays yours. After deploy, the German
  "missing" rows clear with one click of **!roles → ⏱️ Time Roles → 🧹 Clear Missing** (they're live
  DB rows; the code no longer reseeds them, but existing rows persist until purged).
- **⚑ Self-initiated:** none (direct owner request). The **🧹 Clear Missing** button is a small
  adjacent completion of "roles only from the server" (the audit's long-flagged missing bulk-clear).
- **↪ Next:** optional live-walk of the four flows; per-guild custom presets (Session idea).

## 💡 Session idea

**Per-guild custom role presets.** `ROLE_PRESETS` is a global code constant today. Let server admins
save their *own* quick-create presets (name + colour + hoist) that appear in `RoleCreatePanel`
alongside the built-ins — a small audited table + a "➕ Save as preset" affordance on the creation
menu. This is the natural next step from what shipped: the owner asked for "a few presets", and the
most-used real-world presets are server-specific (the very German tiers we just removed were *one
server's* presets baked into everyone's code). Cheap (one table + the existing `RoleLifecycleService`
create path) and surfaced only in the creation menu, preserving this session's constraint.
Dedup-checked `docs/ideas/` — `settings-presets-and-ai-template-advisor.md` is about *settings*
presets, not role presets; this is distinct.

## ⟲ Previous-session review

The previous session (`2026-06-21-prune-stale-claims.md`) correctly applied the Q-0166 drift-on-sight
rule — every prior `active-work.md` claim had merged, polluting `check_lane_overlap.py` with false
positives, so pruning them was exactly right. What it surfaces: the claim ledger keeps going stale
because **claim removal is a manual session-close step that sessions forget** (the same lag that made
a whole prune session necessary). **System improvement:** fold the claim-line removal into the
`/session-close` skill (it already drives the card flip + ledger checks) so a session that closes
also clears its own `active-work.md` line — turning the periodic manual prune into a no-op. The
lane-overlap scan (#1223) reads the ledger; keeping the ledger self-cleaning is the missing half.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1245, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design); 3 issues caught + fixed pre-push locally |
| Repo-rule trips | 2 caught locally by `--full` (raw-defer invariant · mypy missed call site) |
| New ideas contributed | 1 (per-guild custom role presets) |
| Ideas groomed | 0 (large owner-directed build; grooming deferred) |
