# 2026-06-30 — Bot-owner platform-admin override (full config authority in any guild)

> **Status:** `complete`

**Run type:** owner-directed (in-session request)

## What I'm about to do

Owner request: *"as bot owner I always have full bot permissions in any server that I'm in, even if
I don't actually have permissions there — not to alter the server, but to make sure the bot is
properly set up and has the right settings enabled, like the AI and which channels it can do
certain things in."*

**Finding (research):** the bot already treats the configured owner (`config.BOT_OWNER_USER_ID`,
the documented `PLATFORM_OWNER` tier) specially for **AI scope** (`_derive_scope` →
`AIScope.PLATFORM_OWNER`), **global settings** (owner-only), and a **bootstrap-command channel
bypass** (`command_access.py`). But there is **no** owner override for *per-guild configuration
authority*: a bot owner who is a plain member of a guild resolves to `tier="user"` and is denied
by every guild-config seam (settings/AI-policy/setup/governance). So today the owner can *open*
`!settings`/`!setup` (bootstrap bypass) but cannot actually apply AI / channel / setup changes.

**Plan — one source of truth, wired into every authority seam (additive: only ever GRANTS the
configured owner; one-user blast radius keyed on exact id match):**

1. `config.is_platform_owner(user_id)` — single canonical helper (config is a leaf importable by
   every layer; conceptually the right home for the deploy-declared owner id).
2. Governance: `capability.actor_holds_capability` (settings/binding/resource mutations),
   `resolver._resolve_member_tier` (visibility + `resolve_execution`/`can_execute`),
   `writes._validate_authority` (governance writes = per-channel subsystem visibility).
3. Services: the 5 duplicated `_check_admin` gates (ai_policy / ai_instruction / ai_orchestration /
   btd6_source / help_overlay) + `setup_access` (is_setup_admin / can_apply_setup / by-id).
4. Views: `base.interaction_is_admin` (canonical) + the inline raw-`guild_permissions` config gates
   (AI panel / behavior / tools, settings command-access, essential_setup) so the owner can *see &
   use* the config UI, not just pass the mutation check.
5. Consolidate the existing inline `== BOT_OWNER_USER_ID` checks onto the new helper.

Tests per seam (grant for owner, unchanged for non-owner), docs + a router Q-block recording the
owner decision, then flip this card to `complete`.

## What shipped (PR #1573)

Owner decision **Q-0212**. One single-source helper wired into every authority seam — purely
**additive** (only ever grants the one configured owner id; one-user blast radius).

- **`config.is_platform_owner(user_id)`** — the single source of truth (config is a layer-free leaf,
  importable by governance / services / views alike). Returns `False` for `None` / unconfigured.
- **Governance:** `capability.actor_holds_capability` (new step 3 — after target-guild membership so no
  cross-guild escalation, before the revoke overlay so a guild can't revoke the owner) ·
  `resolver._resolve_member_tier` (elevates to `owner` tier → flows into `resolve_visibility` /
  `resolve_execution` / `can_execute`; the audience-**simulation** path stays honest) ·
  `writes._validate_authority` (governance writes = per-channel subsystem visibility).
- **Services:** the 5 duplicated `_check_admin` gates (`ai_policy` / `ai_instruction` /
  `ai_orchestration` / `btd6_source` / `help_overlay`) + `setup_access` (`is_setup_admin` /
  `can_apply_setup` / `can_apply_setup_by_id`).
- **Views:** canonical `base.interaction_is_admin` + new `base.member_is_admin`; the inline raw
  `guild_permissions` config gates (AI panel/behavior/tools, settings command-access, essential_setup)
  routed through them so the owner can *see & use* the config UI, not just pass the mutation.
- **Consolidation:** the pre-existing inline `== BOT_OWNER_USER_ID` checks (settings global scope,
  `ai_tools`, `bot_knowledge_service`, `_derive_scope`) now call the single helper.
- **Tests:** `tests/unit/test_platform_owner_override.py` (37 cases — every seam: grant for owner,
  unchanged for non-owner, simulation-not-overridden, cross-guild still denied, revoke-can't-revoke-owner,
  unconfigured-grants-no-one). Existing touched-module suites green (329). Full mirror green (13,253).
- **Docs:** `capability-authority.md` §1 step 3 · `permission_tiers.py` PLATFORM_OWNER docstring · router
  Q-0212 · regenerated `docs/operations/env-vars.md` (line shifts from the new config helper).

## 📤 Run report

- **Did:** gave the configured bot owner full bot-*configuration* authority in any guild they're a member
  of (AI / channels / setup / settings / governance), via one single-source helper wired into 11 seams ·
  **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1573 — `disbot/config.py` (`is_platform_owner`) · `governance/{capability,resolver,writes,
  permission_tiers}.py` · `services/{ai_policy,ai_instruction,ai_orchestration,btd6_source,help_overlay}_mutation.py`
  · `services/{setup_access,settings_mutation,ai_tools,bot_knowledge_service}.py` ·
  `core/runtime/ai/natural_language_stage.py` · `views/base.py` + 8 AI/settings/setup view gates ·
  `tests/unit/test_platform_owner_override.py` · `docs/capability-authority.md` · router Q-0212 ·
  regenerated `docs/operations/env-vars.md`.
- **Run type:** `owner-directed`
- **⚑ Owner decisions needed:** none — the request **is** the decision (Q-0212), owner-directed in-session.
- **⚑ Owner manual steps:** none (no migration / data step — pure authorization logic; live on next
  auto-deploy). To verify in prod: as the owner, join a server where you have no admin role and open
  `!settings` / `!setup` / the AI panel — you should now be able to apply config.
- **⚑ Self-initiated:** the *feature* was owner-directed; the *consolidation* of the 4 pre-existing inline
  owner checks onto the helper (and the view-gate sweep beyond the strict minimum) was self-initiated for
  one-source-of-truth hygiene (Q-0172) — additive, reversible.
- **↪ Next:** none required. Possible follow-on if desired: a friction→guard test asserting no NEW
  `== BOT_OWNER_USER_ID` / raw-`administrator` config gate is added without routing through
  `is_platform_owner` (would pin the single-source rule the way Q-0200 pins same-name helpers).

## 💡 Session idea (Q-0089)

**A `check_owner_identity_single_source.py` guard (or an `architecture_rules` entry) that fails CI if a
new `== BOT_OWNER_USER_ID` comparison or a raw `guild_permissions.administrator` *config* gate appears
outside the sanctioned single source (`config.is_platform_owner`) / canonical view helpers.** This
session had to hunt down ~9 scattered inline owner/admin checks by grep; the whole point of the
single-source helper is that the next one should be caught mechanically, not by the next reader's
diligence. Genuine (it's the exact "enforce, don't exhort" pattern Q-0200 applied to same-name helpers),
not filler — route to `docs/ideas/` if a later session wants it; it's the natural enforcement tail of
Q-0212.

## ⟲ Previous-session review (Q-0102)

The previous run (#1570, reaction-roles counter) isn't the most instructive neighbour; the more relevant
predecessor is the **Q-0211 `give`-collision hotfix** (#1544), which is a strong example of the
completion-first, root-cause posture — it didn't just rename the colliding command, it retired the verb
surface-wide *and* shipped a cross-cog duplicate-command boot guard so the whole class can't recur. **The
improvement it surfaces, which this session leaned on:** that hotfix proved how much latent risk lives in
*scattered, duplicated gates* (5 identical `give` registrations; here, 5 identical `_check_admin` +
~9 inline owner checks). The system-level lesson is the same both times — **duplication of a
security-relevant check is a latent bug farm**, and the durable fix is *one source + a guard that keeps
it one source*. Q-0211 built the guard for duplicate command names; the Q-0089 idea above proposes the
sibling guard for duplicate owner/admin checks. The workflow itself is healthy; this is additive hardening.

## Doc audit (Q-0104)

`check_current_state_ledger --strict` → exit 0 (the 9 PRs newer than marker #1560 are benign newest-merge
lag the next reconciliation pass records — not drift; this session adds no *prior*-merge ledger change).
New behaviour reachable + documented: `capability-authority.md` §1 step 3, `permission_tiers.py`
docstring, `config.is_platform_owner` docstring, router Q-0212. `check_docs --strict` + `check_consistency`
green. No chat-only decisions left unrouted (Q-0212 captures the owner directive). env-vars.md regenerated
so its generated head stays in sync (the scanner test that caught the stale line numbers).

## 🛠 Friction → guard (Q-0194)

- **Friction:** inserting `is_platform_owner` into `config.py` shifted every `os.getenv` line below it,
  staling the generated `docs/operations/env-vars.md` head → the `test_scan_env_usage` sync test failed.
  **Guard (already exists, worked as designed):** that very test *is* the enforcing guard — it caught the
  drift and named the fix command (`scan_env_usage.py --write-doc`), which I ran. No new guard needed;
  noting it so the next config-editor expects the regen step.
- **Friction:** the real owner/admin-check duplication (≥9 inline sites) was only discoverable by grep.
  **Guard (proposed, owner-gated):** the Q-0089 single-source CI guard above — a checker is free-to-ship,
  but since it would gate CI I've recorded it as a candidate rather than wiring it unilaterally.

## Context delta

- **Needed but not pointed to:** the orientation route doesn't surface that **`config` is a layer-free
  leaf importable from every layer** — the key fact that made a single-source helper possible (utils
  *can't* import config; governance/services/views all *can*). Worth a line in `helper-policy.md` or
  `architecture.md`: "cross-layer leaf constants/helpers belong in `config` (or a similar non-layer
  module), since `utils` is forbidden config/IO." Also not pointed to: that the bot-owner concept was
  *already half-implemented* in three different places (`_derive_scope`, `ai_tools`, `bot_knowledge`,
  `settings_mutation` global) with no shared helper — found by grep.
- **Pointed to but didn't need:** the CodeGraph stats / most of `current-state.md`'s historical narrative
  — for a cross-cutting authority change, plain grep + the per-file context-map hook (importers + blast
  radius + related-docs) carried the whole session; that hook is the MVP for this kind of work.
- **Discovered by hand:** the five `_check_admin` functions are byte-identical duplicates (one per
  AI/btd6/help mutation service) — tribal knowledge with no doc home; the canonical-helper consolidation
  + the Q-0089 idea is where it now lives.
- **Decisions made alone:** scoped the override to *bot configuration* (AI/settings/setup/governance),
  deliberately NOT broadening command-access or feature/game-admin moderation gates; placed the
  governance override *after* the target-guild membership check (preserve cross-guild invariant) and
  *before* the revoke overlay (a guild can't revoke the owner). Recorded in Q-0212's scope-boundary note
  for owner ratification.
