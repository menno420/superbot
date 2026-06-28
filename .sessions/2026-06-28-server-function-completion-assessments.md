# 2026-06-28 — Server-function completion assessments (Q-0209)

> **Status:** `complete`
> **Run type:** routine · dispatch

## What I did
Empty-fire scheduled dispatch, continuing the Q-0209 **completion-first** arc. Every game unit was
already `◐ assessed`; the unassessed completion-ledger set was all server-functions. This run assessed
**four server-functions** against `rubric-server-function.md` (`▢ → ◐`), authored a completion
certificate each, and — during the XP assessment — found and **root-fixed a real audit gap**.

### Assessed (4 new server-fn certs, all `◐`)
- **Moderation** (`units/moderation.md`) — structurally excellent: one audited mutation seam
  (`moderation_service`, AST-invariant-pinned), persistent warnings + mod-logs, OR-gate authority
  (Discord perm **or** capability) re-checked at every button, a 7-action panel, Setup integration.
  Gaps: best-in-class breadth (tempban/softban, case-ID system, appeal flow, role-mute, bulk warn).
- **Economy** (`units/economy.md`) — core loop money-safe + fully audited (INV-F seam, atomic
  transfers, audit + event per change), persistent dead-end-free panel. Gaps: **no public `give`/`pay`
  command** (primitive exists — turn-key), no admin balance panel, hardcoded currency, no bank/wallet.
- **Roles** (`units/role.md`) — broad + clean: Carl-bot-mature reaction roles + role menus + admin ops
  + temp-roles, every mutation through an audited seam (two AST invariants), classified failures,
  dead-binding self-heal, presets/packs. Gaps: gated web builder, exclusive role groups, emoji
  temp-roles, bulk grant.
- **XP & levels** (`units/xp.md`) — solid: message XP, quintic curve, H3 rank card, level-up role
  rewards (stacking toggle), admin give/reset, persistent hub. **Closed an audit gap (BUG-0029).**
  Gaps: best-in-class breadth (no-XP channels, XP multipliers, voice XP, tunable curve).

### Fixed — BUG-0029 (root): XP level-up role grants bypassed the audited role seam
`cogs/xp/listener.py::_apply_xp_threshold_roles` granted/removed XP-threshold roles with a **direct**
`member.add_roles`/`remove_roles` call — so the role change fired **no `audit.action_recorded`** and
skipped the shared hierarchy preflight, unlike every other role mutation in the bot (Welcome's
entry-role, the role cog). Fixed at the root: it now builds `role_automation.Assignment` rows and
routes through the audited `role_automation.apply(actor_type="system")` seam (audit per change +
preflight; behaviour otherwise identical). **Stays-fixed guard:** new AST invariant
`tests/unit/invariants/test_no_direct_xp_role_mutations.py` (no direct member-role mutation in the XP
listener) + the updated `test_xp_listener_roles.py` behaviour tests (assert the audited seam, the
`Assignment` shape, and `actor_type="system"`). Bug-book entry added.

### Ledger
Flipped the four ledger rows to `assessed` + linked certs; regenerated the scoreboard
(`scripts/completion_scoreboard.py --write`): **15/36 assessed (was 11), 0 certified.** De-staled the
S1 ▶ Next-startable bullet to point at the remaining server-fns (Economy's public `give`/`pay` flagged
as the lowest-effort *deepening* win).

## CI / verification
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (49 pre-existing warnings).
- Targeted: `test_xp_listener_roles.py` + `test_no_direct_xp_role_mutations.py` green (4 passed).
- `python3.10 scripts/check_quality.py --full` → **green** (12976 passed, 48 skipped; ruff/black/isort
  clean after autofix; mypy clean).

## 💡 Session idea (Q-0089)
**A completion-axis sibling of the audit invariants: a "role-grant goes through `role_automation`"
invariant scoped to the *whole* cog tree, not just the role cog.** BUG-0029 existed because
`test_no_direct_role_mutations.py` is deliberately scoped to `cogs/role_cog.py` + `views/roles/`, and
its own docstring *assumes* "the automation apply path is already audited" — but any other cog (XP
here; tomorrow welcome-variants, a new game, a moderation auto-role) can call `member.add_roles`
directly and silently skip the audit channel. The XP-specific invariant I shipped closes the XP hole;
a repo-wide `member.add_roles`/`remove_roles` fence (allowlisting only `services/role_automation.py`
and `services/role_grants_service.py`) would close the *class*. Captured as a candidate; a follow-up
dispatch run can build it (it would need a one-time triage of existing call sites — Welcome already
uses the seam, so the surface is likely small).

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (PR #1534, mining/creatures/welcome assessments) did the completion-first arc
well — it correctly assessed Welcome against the *server-function* rubric (the first server-fn) and
produced an honest, evidence-dense cert that became the template I followed here. What it (and the
whole arc so far) **missed**: assessing a unit is the natural moment to *find* latent bugs, but the
prior certs recorded gaps as punch-list items without acting on the contained ones. This run's
improvement is the model to carry forward: **when an assessment surfaces a contained, root-causable
defect (BUG-0029), fix it in the same PR rather than only logging it** — the assessment then leaves the
unit measurably better, not just measured. Worth promoting into the rubric README as a one-line norm
("a contained defect found during assessment is fixed in the assessing PR, not deferred").

## ✅ Doc audit (Q-0104)
- Bug book: BUG-0029 added (FIXED root, with stays-fixed guard named).
- Ledger + scoreboard regenerated; S1 ▶ Next sharpened.
- New owner decisions: none (no owner-gated choices made; the XP fix is a contained correctness fix).

## 📤 Run report

- **Did:** assessed 4 server-fns (Moderation · Economy · Roles · XP) `▢→◐` + root-fixed BUG-0029 (XP
  role-grant audit gap) · **Outcome:** shipped
- **Shipped:** #1536 — 4 completion certs + ledger/scoreboard (15/36 assessed) + BUG-0029 root fix
  (XP role grants through the audited `role_automation` seam) + new AST invariant
- **Run type:** `routine · dispatch` (Q-0165)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (the BUG-0029 fix auto-deploys on merge; no data step)
- **⚑ Self-initiated:** `none` (dispatched completion-first arc; BUG-0029 is a bugs-first root fix on
  the assessed unit, not a self-initiated feature)
- **↪ Next:** assess the remaining server-fns (Settings · Karma · Leaderboards · Counters · Tickets ·
  Spotlight · Channels · Setup wizard · AI · Logging · Diagnostics · Help · Admin · Inventory ·
  Treasury · Cleanup · Automod · Image-moderation · Security · Proof-channel · Utility), one cert each;
  Economy's public `give`/`pay` command is the lowest-effort *deepening* win.
