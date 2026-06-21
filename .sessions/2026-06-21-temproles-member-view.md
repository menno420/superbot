# 2026-06-21 — `!temproles` member-facing temp-role listing

> **Status:** `complete` — built the flagged loose-end from the reaction-roles PR 3–5
> session: a member-facing view consuming the orphaned `role_grants.list_for_member`.
> Additive runtime (a new read-only command + a read seam on the existing audited
> service); existing grant/sweep behaviour unchanged → self-merge on green.

> **Run type:** `routine · dispatch`

## Arc

Empty scheduled fire (no work order). Oriented → no open PRs, no actionable ungated open
bug (BUG-0019 #1 owner-routed design fork; BUG-0009 newest-towers data-gated; the previous
session's Q-0089 config-extension-integrity idea was **already implemented** —
`tests/unit/invariants/test_extension_integrity.py`). Took the explicit `↪ Next` handoff
from the reaction-roles PR 3–5 session: *"a member-facing `!temproles` view consuming
`role_grants.list_for_member`."*

## What shipped

- **`role_grants_service.list_active_grants(guild, member_id)`** — a pure read seam over
  `utils.db.role_grants.list_for_member` that resolves roles and drops two kinds the caller
  should never see: a grant whose role has vanished, and an already-lapsed grant the 5-min
  sweep has not yet collected (so the listing only ever names a role the member still
  effectively holds). No mutation, no audit — reads stay off the audited write path.
- **`!temproles [@member]`** on `RoleGrantsCog` — `@guild_only`; lists the caller's own
  active temp roles (role mention + relative `<t:…:R>` expiry). An optional `@member` is
  **staff-only** (`isinstance(author, discord.Member)` + `manage_roles`); a non-staff
  attempt to view another member is denied without touching the DB.
- Tests: service read (lapsed/vanished filtering · empty) + the command
  (self-list · empty · other-denied · staff-views-other · staff-self-phrasing).
- Regenerated the command-count artifacts (313 → 314): `botsite/data/site.json`,
  `botsite/site/data.js`, `dashboard/data/dashboard.json` via
  `scripts/export_dashboard_data.py`.

## Verification

- `check_quality.py --full` (CI mirror: black/isort/ruff + `mypy disbot/` + full pytest) →
  **GREEN — 11328 passed, 47 skipped**, mypy clean (761 files), all formatters/consistency pass.
- `check_architecture --mode strict` → 0 errors (pre-existing `[known]` warnings only).
- Not live-interaction-tested in Discord (no click harness in-env).

## Context delta

- **Needed but not pointed to:** nothing new — the role-grants stack (#1227) was well
  factored; `list_for_member` was deliberately left for this consumer.
- **Decision made alone:** the active-listing filter (drop lapsed-but-unswept + vanished
  roles) lives on the **service** read, not the cog, keeping the cog a thin shell consistent
  with its existing contract. The optional `@member` staff view is a low-cost addition over
  the minimal "your own" listing.

## 💡 Session idea (Q-0089)

**A `!temproles` member self-cancel (`!temprole cancel @role`) — let a member voluntarily drop
a temp role early.** Today only the 5-min sweep or a staff role-removal ends a grant; a member
who picked up a temp role (e.g. an opt-in event role) cannot release it themselves before
expiry. The audited seam already exists (`role_grants.remove` + a `member.remove_roles`
through a new `role_grants_service.release_own_grant`), so it's a small additive slice — and
it pairs naturally with this listing (list → release). Dedup-checked: no such command exists;
not in `docs/ideas/`. Worth an idea file if not built next.

## ⟲ Previous-session review (Q-0102)

**Reviewed: the reaction-roles PR 3–5 session (#1227).** *Did well:* a disciplined
loose-end handoff — it explicitly flagged `list_for_member` as an unconsumed seam in both
its run-report `↪ Next` and its Context-delta, which is exactly what let *this* session pick
up a clean, well-scoped slice with zero rediscovery. That is the handoff loop working as
designed. *What it could have done better:* it bundled PR 3+4+5 into one PR (defensible for
the shared migration sequence) but that makes the **per-feature** revert granularity coarser —
if PR 5's analytics had a bug, reverting it also reverts the temp-roles + modes work.
**System improvement:** when bundling N plan-PRs onto one branch for migration-sequence
reasons, keep them as **separate commits with feature-scoped messages** (the session did this)
*and* note the bundling rationale in the plan's Build-progress (it did) — this is already good
practice; the only gap is there's no lightweight convention reminding a bundling session to
record *how to partially revert* (which commit drops which feature). A one-line "partial-revert
map" in such a session's card would close it. Captured here rather than as a rule proposal —
it's a soft convention, not binding.

## 📤 Run report

- **Did:** added `role_grants_service.list_active_grants` + the `!temproles [@member]` member
  command consuming the previously-orphaned `list_for_member`; regenerated command-count
  artifacts · **Outcome:** shipped (routine dispatch, self-merge on green)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions recorded:** none
- **⚑ Owner manual steps:** none — merge auto-deploys; no migration (reads an existing table).
- **⚑ Self-initiated:** the whole slice — taken from the previous session's `↪ Next` handoff
  (not a dispatched work order; the empty scheduled fire advances the plan). Contained,
  reversible, additive, test-covered.
- **↪ Next:** the session idea above (`!temprole cancel` member self-release); else a fresh
  ▶ ungated startable from current-state — creature-PvP **leaderboards** (reuse `game_xp`,
  additive) or the **botsite React-SPA migration**.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1242, routine dispatch, self-merge on green) |
| Migrations added | 0 (reads existing `role_grants`) |
| New tests | 7 (2 service read + 5 command) |
| CI-red rounds | 2 — round 1: command-count artifact drift (313→314, regenerated) + 1 mypy union-attr (`guild_permissions` on `User|Member`, fixed with isinstance); round 2 green |
| Repo-rule trips | 0 (arch 0 errors; `role_grants_cog` 143 LOC) |
| New ideas contributed | 1 (`!temprole cancel` member self-release) |
