# 2026-06-21 — Reaction-roles overhaul PR 3 + 4 + 5 (modes · temp roles · analytics)

> **Status:** `complete` — the back half of the reaction-roles overhaul
> ([plan](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md)), built as **one
> owner-directed PR** (Q-0191 — owner-directed work merges immediately, NOT
> `needs-hermes-review`). Runtime code, but additive + behaviour-preserving (existing
> reaction roles work identically; the `reaction_roles_enabled` toggle defaults ON; new
> tables are empty no-ops) → auto-merges on green.

> **Run type:** `manual`

## Arc

Owner asked me to continue the reaction-roles plan: **PR 3** (Carl-parity modes on the emoji
surface + convert the read-only emoji panel to interactive + `reaction_roles_enabled` settings
bridge) · **PR 4** (free temp roles) · **PR 5** (role-pickup analytics) · **PR 6** optional (PIL
cards). Mid-session the owner issued a standing directive — *"anything that I personally direct
the agents to do should never be held for review, always merge immediately"* — recorded as
**Q-0191** and applied to this session. *(Drafted in-session as Q-0189; renumbered to Q-0191
when merging `origin/main`, which had concurrently taken Q-0189 ("open PR fast") + Q-0190
("free for everyone"). The commits/PR body reference the original Q-0189; the router Q-0191
block is canonical.)*

Built PR 3 + 4 + 5 as **one PR on one branch**: they share the migration sequence (079/080/081)
and the `reaction_role_service` / `role_menus` files, so one branch avoids self-conflicts and the
born-red session-card lifecycle stays simple; the four logical commits keep review per-concern.
**PR 6 (PIL cards) deferred** — explicitly optional/owner-paced, and image-attach-on-message-edit
is real surface; deferring kept the core arc tight.

## What shipped

- **PR 3 — Carl-parity modes + interactive panel + settings bridge.**
  - Migration **079** `reaction_role_message_modes` (per-message `normal`/`unique`/`verify`; no
    row ⇒ `normal`, so every existing binding is unchanged). DB CRUD in `utils/db/roles.py`.
  - `reaction_role_service` gained the mode-aware emoji handlers (`handle_reaction_add` /
    `handle_reaction_remove`) — `unique` swaps the held sibling on the same message, `verify` is
    add-only + signals the cog to strip the reaction — plus audited `set_message_mode` and the
    `reaction_roles_enabled` settings consumer (default ON; gates the listeners *after* the
    binding lookup so unrelated reactions pay no settings read).
  - `role_cog` listeners route through the service; `_strip_reaction` removes the member's
    reaction for `verify`. (cog 743 LOC, under the 800 ceiling.)
  - **`ReactionRolesPanel` is now interactive** (closes the `ui-view-adoption-audit` P1
    read-only finding): ➕ Add (modal → role picker → bind + best-effort reaction), 🗑️ Remove
    (paginated binding picker), ⚙️ Mode (message → mode picker), all through the audited seam.
  - `reaction_roles_enabled` SettingSpec on `cogs/role/schemas.py` + `settings_keys/role.py`.
- **PR 4 — free temp roles** (Carl gates `temp` behind Patreon; ours is free).
  - Migration **080** `role_grants` + `utils/db/role_grants.py`; `services/role_grants_service.py`
    (`grant_temp_role` audited + `sweep_expired` — removes lapsed roles, keeps a row when the role
    is unmanageable so a later sweep retries, cleans up vanished member/role).
  - `RoleGrantsCog` — a `@tasks.loop(minutes=5)` sweep (media/health-maintenance pattern) +
    `!temprole @member 2h @role`; registered in `config.py`. New `utils/duration.py`
    (`30m`/`2h30m`/`7d`, bare-number = minutes, 1-year cap).
- **PR 5 — role-pickup analytics** (§10; nearly free given the audited seam).
  - Migration **081** `role_menu_pickup_stats` rollup + CRUD in `utils/db/role_menus.py`;
    increments wired into the central `_apply` seam (so **menu *and* emoji** pickups both count),
    best-effort so a stats blip never blocks an assignment. Aggregate-only (no per-member history).
  - Diagnostics panel "📊 Role Pickups" section (top-5 + a "barely-used — archive?" nudge).
- **Guild teardown** steps 24 (modes) / 25 (grants) / 26 (pickup stats) — INV-I for every new
  guild-keyed table, each failure-isolated.
- **Workflow:** recorded **Q-0191** (router + the `.claude/CLAUDE.md` auto-merge bullet) and
  **closed the superseded duplicate PR #1221** (a second build of PR 2; #1219 already shipped it).

## Verification

- `check_quality --full` (CI mirror: black/isort/ruff + `mypy disbot/` + full pytest) → **GREEN —
  11184 passed, 47 skipped**.
- `check_architecture --mode strict` → 0 errors (pre-existing `[known]` warnings only).
- New tests: mode handlers (normal/unique/verify/disabled/unbound), `set_message_mode` audit,
  settings consumer, temp-role grant+sweep (incl. unmanageable-role retry + vanished-member
  cleanup), `utils.duration` (21 cases), pickup-stat CRUD + `_record_pickups` resilience, teardown
  steps 24/25/26. Not live-interaction-tested in Discord (no click harness in-env).

## Context delta

- **Decision made alone:** package PR 3–5 as **one** PR (migration-sequence + shared-file
  coordination) rather than 3–4 separate PRs; defer PR 6. Recorded in the plan's Build-progress.
- **Loose end (deliberate):** `role_grants.list_for_member` exists but no UI consumes it yet — a
  member-facing "my temp roles" view is the natural next slice (flagged as the session idea below's
  sibling).

## 💡 Session idea (Q-0089)

**A CI guard that every `config.py` extension entry is importable and exposes an async `setup()`.**
I added `cogs.role_grants_cog` to `config.py` by hand; a typo or a missing `setup()` there would
only surface at **boot**, not in CI (the cog list is a plain string tuple). A tiny stdlib test that
imports each `EXTENSIONS` entry and asserts a coroutine `setup` attribute would catch the whole
class pre-merge — the same "boot caught it, CI didn't" gap the PR-2 session flagged for persistent
views. Cheap, stdlib-only; dedup-check first against any existing "all cogs load" smoke test.

## ⟲ Previous-session review (Q-0102)

**Reviewed: the PR 2 session (#1219).** *Did well:* a clean dropdown-default builder with
server-side mode enforcement, edit-in-place, themes, and templates — and an honest reconciliation
onto PR 1's real API after the parallel merge. *What it missed:* it shipped as `needs-hermes-review`
on **owner-directed** work, which is exactly what the owner pushed back on this session (Q-0191) —
and it didn't notice the *parallel duplicate* #1221 building the same feature, which then sat open
and conflicted. **System improvement:** the duplicate is the recurring parallel-build waste — the
claim ledger (`active-work.md`) + the "check open PRs before starting" rule exist for it, but a
*second session on the same plan PR number* slipped through because neither claimed first. The
Q-0089 idea from PR 2 (publish exact public signatures early when foundation + consumer build in
parallel) plus an **early branch/PR-title claim** would have prevented both #1221 and the PR-1→PR-2
API churn. Worth a line in `ai-project-workflow.md` §9.

## 📤 Run report

- **Did:** built reaction-roles PR 3+4+5 (modes + interactive emoji panel + settings bridge · free
  temp roles · pickup analytics); recorded Q-0191; closed superseded #1221 · **Outcome:** shipped
  (owner-directed, auto-merge on green)
- **Run type:** `manual`
- **⚑ Owner decisions recorded:** **Q-0191** — owner-directed work is never held for review; merge
  immediately (router + CLAUDE.md auto-merge bullet)
- **⚑ Owner manual steps:** none — merge auto-deploys; migrations 079/080/081 run idempotently on
  boot. Prod restart/verify stays the maintainer's (merge ≠ deploy).
- **⚑ Self-initiated:** none of the *build* (owner directed PR 3–6 explicitly); the **#1221 close**
  was a self-initiated housekeeping disposition (superseded duplicate, reversible).
- **↪ Next:** **PR 6** (optional PIL banner cards, §4.6d) when greenlit; a member-facing
  `!temproles` view consuming `role_grants.list_for_member`; Surface A (web builder) rides the
  control-API write side.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (PR 3+4+5 bundled, owner-directed) · closed #1221 (superseded dup) |
| Migrations added | 3 (079 modes · 080 role_grants · 081 pickup_stats) |
| New tests | mode handlers + temp-roles + duration (21) + pickup CRUD + teardown 24/25/26 |
| CI-red rounds | 2 local full-mirror rounds — round 1: 15 generated-artifact/doc-drift fails (new cog/command/setting) + raw-guild-lookup invariant + ruff/black; all fixed; round 2 green |
| Repo-rule trips | 0 (arch 0 errors; cog 743/800 LOC) |
| New ideas contributed | 1 (config.py extension-integrity CI guard) |
