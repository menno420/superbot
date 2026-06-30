# 2026-06-30 — Bot-owner override: completeness follow-up (view gates + command decorators)

> **Status:** `complete`

**Run type:** owner-directed (bug report — "It still does not work", screenshot)

## What I'm about to do

#1573 (Q-0212) gave the bot owner full config authority at the governance / service / setup-access /
canonical-view seams — but the owner **still hits "❌ Administrator permission required."** (owner
screenshot). Root cause: #1573's view sweep was **incomplete** (its grep was truncated at 50 results),
so two whole gate classes were missed:

1. **View `interaction_check`s never routed through the canonical helper:** the entire
   `views/ai/policy/*` family (channel / category / role / chooser / list / preview), `views/ai/routing/
   matrix.py`, and `views/{xp,roles}/main_panel.py`. These do raw `guild_permissions.administrator`
   checks → deny the owner. **This is the screenshot bug** (AI policy = "the AI and which channels").
2. **Cog command decorators:** `@commands.has_permissions(administrator=True)` (101) +
   `@app_commands.checks.has_permissions(administrator=True)` (28) gate `!ai`, `/setup`, etc. *before*
   the body/view runs — `is_platform_owner` never touched these, so the owner can't use admin-config
   commands directly.

**Plan (complete + guarded this time):**
- New `core/runtime/permission_checks.py`: `admin_or_owner()` (prefix) + `app_admin_or_owner()` (slash)
  — administrator OR `config.is_platform_owner`, raising the same `MissingPermissions` for non-owners.
- Route every remaining view admin `interaction_check` / `_admin` helper through
  `views.base.interaction_is_admin` / `member_is_admin`.
- Replace every `has_permissions(administrator=True)` decorator (both forms) with the owner-aware check.
- **Guards (friction → guard, the exact miss-class):** a CI test that fails if (a) any view does a raw
  `guild_permissions.administrator` check outside the canonical helpers, or (b) any cog uses
  `has_permissions(administrator=True)` instead of `admin_or_owner`. These would have caught #1573's miss.
- Tests for the new checks; update Q-0212 / capability-authority with the decorator + view seams.

## What shipped (PR #1577)

- **`core/runtime/permission_checks.py`** — `admin_or_owner()` (prefix) + `app_admin_or_owner()` (slash)
  + `member_has_admin_or_owner()`: administrator **or** `config.is_platform_owner`, raising the same
  `MissingPermissions` for non-owners (identical UX for everyone else).
- **Command decorators — 129 swapped bot-wide:** every `@commands.has_permissions(administrator=True)`
  (101) + `@app_commands.checks.has_permissions(administrator=True)` (28) → `@admin_or_owner()` /
  `@app_admin_or_owner()`, across 18 cogs (script-driven) **plus** the 5 **bare** `@has_permissions(...)`
  in `chain_cog` the script's `commands.`-prefixed pattern missed (caught by the new guard's broader match).
- **View gates routed through the canonical helper:** the whole `views/ai/policy/*` family (channel /
  category / role / chooser / list / preview), `views/ai/routing/matrix.py`, `views/{xp,roles}/main_panel.py`,
  and the feature-admin gates `views/{starboard,tickets,btd6/ct_group_flow,games/blackjack_panel}` — all now
  `interaction_is_admin` / `member_is_admin` / `is_platform_owner`. **Not touched:** `manage_roles` gates
  (server-role mutation = "altering the server") + bot own-capability (`me.guild_permissions`) checks.
- **Two CI guards** (`tests/unit/invariants/test_owner_override_guards.py`): no raw `.administrator` in a
  view `interaction_check`; no `has_permissions(administrator=True)` decorator in cogs. Both fail the build
  on re-introduction — the exact class #1573 shipped.
- **Docs:** router Q-0212 completeness addendum + `capability-authority.md` cross-seam pointer.
- **Verified:** extension-integrity (every cog imports with the new decorators) + guards + the #1573
  override suite green; full `check_quality --full` mirror green.

## 📤 Run report

- **Did:** closed the #1573 gap that left the owner denied — made every `administrator`-tier gate
  (129 command decorators bot-wide + the missed view `interaction_check`s) honour the platform owner, via a
  new owner-aware decorator seam + the canonical view helpers, and added two CI guards so the miss-class
  can't recur · **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1577 — `core/runtime/permission_checks.py` · 19 cogs (decorator swap, incl. chain_cog bare
  form) · `views/ai/policy/*` + `views/ai/routing/matrix` + `views/{xp,roles,starboard,tickets,btd6,games}`
  · `tests/unit/invariants/test_owner_override_guards.py` · router Q-0212 addendum · capability-authority.md.
- **Run type:** `owner-directed` (bug report)
- **⚑ Owner decisions needed:** none — same directive as Q-0212.
- **⚑ Owner manual steps:** none (pure authorization logic; live on next auto-deploy). Re-test in prod:
  as the owner with no admin role, open `!ai` / the AI policy panel / `/setup` — all should now work.
- **⚑ Self-initiated:** the bare-`has_permissions` chain_cog fix, the feature-admin view gates
  (starboard/tickets/btd6/blackjack), and the two CI guards were beyond the literal screenshot bug —
  root-cause completeness so this doesn't need a third round (Q-0172 / Q-0194).
- **↪ Next:** none required. (`manage_roles` server-role gates remain admin/manage_roles-only by design;
  revisit only if the owner wants role-management access too.)

## 💡 Session idea (Q-0089)

**Bound the AST view-gate guard to also catch the `_admin` / `_require_admin` / `_can_manage` *helper*
pattern, not just `interaction_check`.** This pass found the same raw-admin check living in three shapes
(`interaction_check` body, a module `_admin(user)` helper, a `_can_manage(interaction)` helper). The guard
currently nails the `interaction_check` shape (the demonstrated bug); a follow-up could generalise it to
"any view function that reads `.administrator` must be the canonical helper or call it" so the helper-shaped
gate is mechanically caught too. Genuine (this session fixed three helper-shaped gates by hand), not filler.

## ⟲ Previous-session review (Q-0102)

The previous session here (#1573, the Q-0212 original) shipped a genuinely good single-source design — but
it **declared victory on an unverified surface sweep**: it grepped the views, the output truncated at 50
results, and it fixed only what it saw, then reported "every seam" covered. The owner caught it in prod.
**The system improvement (built this session):** "enforce, don't exhort" — a *completeness claim about a
pattern sweep must be backed by a CI guard that enumerates the pattern*, not by a grep the author eyeballed.
The two new guards are that backstop; the durable lesson for any future "wire X into every Y" task is to
ship the guard that proves "every Y" in the same PR. (Also a concrete tooling note: `grep`/Grep output is
silently truncated by head limits — for a *completeness* sweep, always `| wc -l` first or use an
unbounded/AST pass, never trust the first page.)

## Doc audit (Q-0104)

Router Q-0212 extended with the completeness addendum (decorator + view seams + the two guards);
`capability-authority.md` gained the cross-seam pointer; `core/runtime/permission_checks.py` is referenced
from both. No *prior*-merge ledger change this session (the merged #1573 is already in the ledger via the
reconciliation convention). `check_docs --strict` + `check_consistency` green.

## 🛠 Friction → guard (Q-0194)

- **Friction:** #1573 missed gates because a `grep` of the view layer was **truncated at 50 results** and
  eyeballed as complete → shipped a half-fix the owner hit in prod. **Guard:** the two AST/source CI guards
  in `test_owner_override_guards.py` enumerate the *entire* gate population and fail on any raw gate — a
  completeness claim is now machine-checked, not eyeballed. (Free-to-ship test guard, not owner-gated.)
- **Friction:** the decorator-swap script matched only `commands.has_permissions(...)` and missed
  `chain_cog`'s **bare** `@has_permissions(...)` import form. **Guard:** the decorator guard matches the
  pattern at *any* decorator line regardless of qualifier, so the bare form is now caught too.

## Context delta

- **Needed but not pointed to:** nothing routed me to the fact that admin gating lives in **three
  independent mechanisms** — discord.py command *decorators* (`has_permissions`), view *interaction_checks*,
  and service `_check_admin` — so "make the owner admin everywhere" is a three-front change. A short
  "authority gate inventory" in `capability-authority.md` (decorator vs view-check vs service-check, and the
  owner-aware helper for each) would have made #1573 complete the first time. Worth adding.
- **Pointed to but didn't need:** the per-file context-map hook fired on ~10 view/cog files; for a
  mechanical same-shape sweep it was noise after the first couple (the pattern was identical).
- **Discovered by hand:** `chain_cog` imports `has_permissions` bare (not `commands.has_permissions`) — a
  second decorator spelling that any "swap the decorators" task must handle; now encoded in the guard.
- **Decisions made alone:** extended the override to the feature-admin view gates (starboard/tickets/btd6/
  blackjack) and replaced **all** `administrator=True` decorators bot-wide (not just AI/setup), reasoning
  "full bot permissions" + avoid-a-third-miss; held the line at `manage_roles` (server-role mutation) per
  the owner's "not to alter the server." Recorded in the Q-0212 addendum for ratification.
