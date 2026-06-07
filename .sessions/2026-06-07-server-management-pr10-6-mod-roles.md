# 2026-06-07 — Server-management PR10 (final slice): moderator/trusted roles + capabilities

- **Arc:** Autonomous session — maintainer was testing a multi-agent workflow ("find out
  for yourself what to do, start implementing once you understand the goal, standing by
  for questions"). Followed the orientation route → the `current-state.md` ▶ Next action
  was unambiguous: PR10's last item, the **capability-native mod-roles** grant (owner
  decision Q-0006 → A, the highest-stakes change in the server-management plan — it
  changes *who can ban members*). Source-verified the whole authority model first, then
  asked **one** focused product question (config surface) → *"Settings-hub role setting"*.
  Branch `claude/gifted-planck-HYMqp`. **PR #___.** This completes **PR10**.

- **Decision of record:** **ADR-008**
  (`docs/decisions/008-moderator-role-capability-native-authority.md`).

- **Key design call (source-grounded):** route the grant through the **tier resolver**,
  not a new per-capability matrix. `resolve_execution` *already* gates moderation at the
  `moderator` tier (the moderation subsystem's `visibility_tier`), and
  `_resolve_member_tier` was *already* role-aware (trusted role, ISSUE-015). So the whole
  feature is **one tier promotion** + an OR-gate on the surfaces — it reuses the existing
  capabilities, the existing `resolve_execution`, and the existing `input_hint="role"`
  Settings widget. The owner picked A (role→tier) over option (b) the per-capability
  matrix, so `actor_holds_capability` / `capability-authority.md §5` stays **untouched**
  and that matrix stays deferred.

- **Shipped:**
  - **`MODERATOR_TIER_ROLE_ID`** key + **`config_arbitration.get_moderator_tier_role`**
    (mirrors `get_trusted_tier_role`).
  - **`governance/resolver.py::_resolve_member_tier`** — moderator-role grant symmetric to
    the trusted-role grant, via a new `_role_grants_tier` helper. Grants only **raise** a
    tier (never demote a real admin/owner), compose (higher wins), and **fail toward the
    lower tier** on a config-read error (a role can only ever *add* standing).
  - **`ui_permissions.can_execute_ctx`** — prefix-`Context` mirror of `can_execute`.
  - **Mod cog** — eight prefix commands swap `@commands.has_permissions(...)` for
    `@_require_mod(cap, perm)`: `Discord-perm OR capability`, raising `MissingPermissions`
    on denial (preserves the exact error UX). **Panel `interaction_check`** OR-gated the
    same way. `/moderation` slash left as-is (Discord `default_permissions` UI default —
    documented boundary).
  - **Settings hub** — `moderator_role` + `trusted_role` role-typed `SettingSpec`s
    (`input_hint="role"`, schema → **v6**), written through the audited
    `SettingsMutationPipeline`, gated by `moderation.settings.configure` (admin floor).
    This also finally un-inerts the trusted role (it had **no** operator surface before).

- **Behaviour-preserving:** the Discord-perm path is unchanged and checked first, so no one
  who can moderate today loses access; the role grant only *adds*. Configuring the role
  needs admin. A role-granted moderator can take actions but cannot change mod *config*.

- **Tests / gates:** `test_role_tier_grants.py` (grant-via-role, no-escalation,
  no-regression, precedence, cross-guild deny, fail-toward-lower, helper) +
  `test_moderation_role_authority.py` (cog + panel OR-gate) + `test_moderation_schemas.py`
  v6/role specs. `check_quality --full` **green (7852 passed, 16 skipped)**, mypy clean,
  `check_architecture --mode strict` **0 errors**, doc-pins green. **Live-booted** (Postgres
  brought up, Galaxy Bot#6724): clean start, `settings_registry … 0 findings`, ModerationCog
  loaded, **no ERROR/CRITICAL/Traceback**.

- **Docs routed:** ADR-008 · tracker (PR10 → COMPLETE, queue starts at PR11) · folio ·
  `capability-authority.md` §5/§6 · `settings-customization-command-map.md` ·
  `current-state.md` (▶ Next action → PR11) · router Q-0006 (Routed → ADR-008). Project
  state → `current-state.md`; authoritative queue → the server-management tracker.

## Workflow notes (meta — the maintainer asked for these)

What **helped** (keep):
- **The orientation chain is excellent.** `CLAUDE.md` → `collaboration-model` →
  `current-state` (with a single **▶ Next action** pointer) → tracker took me from cold
  start to "the exact approved next task + the owner's decision verbatim" in ~4 reads. The
  ▶ Next action line carrying the *decision* (Q-0006 → A) and the *reason it's sensitive*
  inline is the single highest-leverage thing in the repo for an autonomous start.
- **Decisions are pre-routed.** The owner answer + agent interpretation living in the
  router §19 (not just a PR body) meant I didn't have to reconstruct intent or re-ask the
  architecture — I only had to verify it against source and ask the *one* genuinely-open
  product question.
- **CI mirror + arch checker + doc-pins are a real safety net.** `check_quality --full`
  caught the two doc-pin gaps (new key + SettingSpec names must be documented) and mypy
  caught the `User|Member` narrowing — both *before* push, exactly as intended.
- **The "source wins / verify cross-agent output" culture paid off:** the surface area was
  much larger than the prompt implied (there are two parallel authority resolvers, and the
  trusted role was *fully* inert with no UI), and only reading source surfaced that.

What **worked against me** (friction):
- **High doc surface for one change.** A single feature touched ~6 doc homes
  (current-state, tracker, folio, capability-authority, command-map, router) plus the ADR.
  The one-fact-one-home rule is right, but a small "where to update when PR-N of an
  initiative lands" checklist per tracker would cut the rediscovery. (Idea, not done.)
- **Two same-named authority resolvers** (`resolve_execution` vs `actor_holds_capability`)
  + a "capability resolver" phrase in the owner decision created a real fork I had to
  resolve from source. A one-line map in `capability-authority.md` ("executions →
  resolve_execution; config mutations → actor_holds_capability") would have saved time —
  I added exactly that note in §5 this session.
- **Settings keys vs SettingSpec ownership:** the role keys are governance-owned but the
  SettingSpec lives on the moderation schema; nothing enforced/clarified that this is OK.
  It works, but a future reader may wonder. Left a comment + doc note.

Improvement ideas (captured, not acted on): a per-initiative "landing checklist" of doc
homes to refresh when a slice ships; consider promoting the ★ "boot is always safe" +
"run check_quality --full before push" rules — they held perfectly again this session.
