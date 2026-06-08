# 2026-06-08 — P0C drift fence + plan review for the next agent

**Task:** After P1A merged (#589), do *one more bounded step* if it's not too large, then
sharpen the docs/plan so the next session has a clear, turn-key continuation path.

**Branch:** continues `claude/access-map-projection-p1a` (P1A merged from it; new commits
stack cleanly on main).

## What I assessed (and why the "one step" is a guard, not the refactor)

The natural next code lane is **P0C** (route role-threshold writes through the audited
`role_automation` seam). I mapped it: the audited seam already exists
(`role_automation.set_time_threshold` / `set_xp_threshold` — identical DB write **plus**
audit), but the drift is **6 direct `db.set_role_threshold*` calls across 5 files**
(`time_roles_panel.py` ×2, `creation_panel.py`, `_helpers.py`, `xp_roles_panel.py`,
`cogs/role_cog.py`). That's a medium refactor on a **live role-assignment mutation path**
+ panel-test updates — over the "not too large" line. So instead of a risky partial
refactor, the bounded, **zero-risk** step is a fence that protects + targets it.

## Shipped

1. **`tests/unit/invariants/test_no_direct_role_threshold_writes.py`** — a deterministic
   AST drift fence (sibling of `test_no_direct_role_mutations.py`, which covers role
   *object* mutations but explicitly **not** thresholds). It pins the exact 5 files that
   write thresholds directly today as a **shrinking allowlist**: a *new* direct write in
   any other file fails immediately (drift can't grow), and each converted file must be
   removed from the allowlist (so the punch list stays honest) — empty set = P0C done.
   Plus a positive check that the audited seam exists + emits audit. 3 tests, all green.

2. **Plan made turn-key for the next agent (the requested "improvements"):**
   - **§16.5** now carries the full P0C **punch list** (the 6 sites + the per-site
     `actor_id` to pass) + the **swap recipe** (behavior-preserving write + additive
     audit) + the fence/test-update pointers.
   - **§16.8 (new)** — four refinements I learned building P1A that re-scope P1B/P1C:
     (1) **drop `identity_mismatch`** from P1B — it's already covered by
     `validate_identity_contract` + the ledger identity tests; (2) the P1B drift providers
     are **runtime/per-guild** (they need live DB policy + a member), not static; (3) the
     **audience-simulation gap** — the governance axis needs a real `discord.Member`, but
     Help Preview/drift simulate by *tier*; `AccessContext.member_tier` is a forward hook
     but unconsumed — decide synth-member vs tier-aware-governance **before P1C**;
     (4) `project_access_map(ctx)` is the batch surface a P1C table renders.
   - `docs/ownership.md` drift note + §9 P0C row + §15 next-destination + `current-state`
     all updated to point at the fence + recipe.

## Verification

- `python3.10 -m pytest tests/unit/invariants/test_no_direct_role_threshold_writes.py` → **3 passed**.
- `python3.10 scripts/check_quality.py --full` → green (full suite; the new fence runs with it).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors.
- `python3.10 scripts/check_docs.py` → passed.

## Next (clear continuation path)

1. **P0C** — convert the 6 sites in §16.5 onto `role_automation.set_{time,xp}_threshold`,
   shrink `_ALLOWED_DIRECT_THRESHOLD_FILES` to empty, update the panel/selector tests.
   Behavior-preserving + additive (audit). Live-boot a role assignment to confirm.
2. **P1B** — the three runtime drift providers + locked-reason denial integration
   (§16.5/§16.8), built on `resolve_feature_access`.
3. **P1C** — read-only Access Map + Help Preview panels; **resolve §16.8 item 3
   (audience simulation) first**.

## Context delta

- **Needed but not pointed to:** that the threshold-writer drift spans **`cogs/role_cog.py`
  too** (not just `views/roles/*`) — the planning §5 panel map only named "the role panel."
  The 6th site (`role_cog.py:454`) only showed up on a direct grep of both surfaces.
- **Pointed to but didn't need:** the broader P1B/P1C view/diagnostics stack — this step
  deliberately stayed at fence + docs, so none of the UI/diagnostics source was needed.
- **Discovered by hand:** that `test_no_direct_role_mutations.py` **excludes** member
  assignment + threshold writes by design ("the automation apply path … is already
  audited") — so the *threshold-write* drift had no guard at all. That gap is what the new
  fence fills; captured here + in the new test's docstring.
