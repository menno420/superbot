# Server-management contract-vs-code audit — 2026-07-08

> **Status:** `audit` — dated contract-vs-code audit of the **server-management**
> subsystem (Wave-1 lane A of the owner-directed 3-lane campaign, docs-only session,
> PR #1844). Every finding is verified against shipped source with file:line evidence.
> **Source code and merged PRs win** over this snapshot. **Sector:** S1 — Bot product.
> Findings are deliberately **not fixed here** (audit-only lane); each carries a
> proposed durable fix for a follow-up session.

## Scope & method

Audited the server-management subsystem (moderation + automod + server logging +
channel/role lifecycle + reaction roles + cleanup + setup-draft ops) against its own
binding contracts:

- `docs/subsystems/server-management.md` (folio)
- `docs/ownership.md` (service/table/event ownership — binding)
- `docs/architecture.md` layer rules (via `scripts/check_architecture.py --mode strict`)
- `docs/runtime_contracts.md` §2/§9 (event + mutation contracts)
- `docs/server-logging.md`

Method: read the contract → read the shipped source → grep the wiring (EventBus
names, registry callbacks — the CodeGraph/Grimp-blind edges) → run the relevant
invariant tests. Checks run this session: `check_architecture --mode strict`
(**0 errors**, 49 known warnings), and the five server-management write-boundary
invariant suites (`test_no_direct_moderation_writes`, `test_no_direct_channel_mutations`,
`test_no_direct_role_mutations`, `test_no_direct_role_threshold_writes`,
`test_setup_draft_op_kind_parity`) — **15/15 passed**.

## Headline

**The runtime seams conform.** Every mutation path spot-checked routes through its
audited service exactly as the contracts demand: automod → `moderation_service.auto_delete`/`warn`
(`disbot/cogs/automod/listener.py:78,88`), security kick → `moderation_service.kick`
(`disbot/services/security_service.py:405`), cleanup-stage deletes →
`moderation_service.auto_delete` (`disbot/cogs/cleanup_cog.py:250`), counting deletes
routed (`disbot/cogs/counting/handler.py:266`), prohibited-word writes →
`prohibited_words_service` (`disbot/cogs/cleanup_cog.py:512,535,616,643,728`),
`_record_action`'s three-signal fan-out with shared `mutation_id`
(`disbot/services/moderation_service.py:181-238`), setup op-kind three-place parity
(dispatcher `setup_operations.py:135` = DB gate `setup_draft.py:47` = migration 059
CHECK), the cleanup guild-scope gotcha closed via `cleanup_scope_id`
(`disbot/services/cleanup_levels.py:103`, consumed at `setup_operations.py:1540`),
moderation panel re-checks authority at callback time
(`disbot/views/moderation/main_panel.py:45`). **Zero RISKY findings.** What drifted is
the **binding ownership doc and the folio**, which lag several shipped arcs — plus one
missing enforcement guard.

## Findings (prioritized)

### F1 — ownership.md has no owner for the five reaction-role-overhaul tables (LOW)

**Evidence:** `docs/ownership.md:71` (role subsystem row) lists tables owned as
`role_thresholds`, `reaction_roles` only, and says reaction_roles is written
"direct via `utils/db/roles.py`". Shipped reality: migrations
`078_reaction_role_menus.sql` (`role_menus`, `role_menu_options`),
`079_reaction_role_message_modes.sql`, `080_role_grants.sql`,
`081_role_menu_pickup_stats.sql` (+ card/counts columns in 089/103) — and **none of
these five tables appears anywhere in ownership.md** (`grep -c role_menus
docs/ownership.md` → 0). Their real write seams are the audited
`services/reaction_role_service.py` (e.g. `bind_emoji:42`, `unbind_emoji:66`,
`create_menu:358`, `delete_menu:603`, all emitting `audit.action_recorded` via the
`_emit*` helpers at `:855-925`) and `services/role_grants_service.py`
(`grant_temp_role:32`, `sweep_expired:93`, audit `_emit:144`). Even the legacy
`reaction_roles` writes now route through the service, so the "direct via
utils/db/roles.py" clause is stale too (no callers of
`add_reaction_role`/`remove_reaction_role` exist outside the service — verified by
grep; `cogs/role_cog.py:691` is a same-named command that delegates to
`unbind_emoji:698`).

**Root cause:** the reaction-role overhaul (#1219…#1279) updated the folio
(`docs/subsystems/server-management.md:174-185`) but never back-filled the binding
ownership doc — the ownership row predates the overhaul.

**Proposed fix (docs-only):** extend the `role` subsystem row (and the audit-log
semantics section if desired) with the five tables, naming
`reaction_role_service` / `role_grants_service` as sole writers and noting reads stay
direct via `utils/db/role_menus.py` / `utils/db/role_grants.py`.

**Risk class: LOW** — pure docs; a follow-up session can fix now.

### F2 — ownership.md contradicts itself (and the code) on ChannelLifecycleService scope (LOW)

**Evidence:** `docs/ownership.md:46` (services table) scopes the service to
"rename / move / delete / reorder" and asserts "**Not yet owned:** create / clone /
overwrites / lock / arbitrary before-after reorder / category CRUD UI (still on
cog/util paths)". That is contradicted **within the same document** by
`docs/ownership.md:87` (channel subsystem row: "rename/move/delete/reorder/overwrite/clone
**and ad-hoc operator creation** via `services/channel_lifecycle_service.py` (P0-4,
Q-0100)") and by the Known-drift entry `docs/ownership.md:444-453`
("Channel create/edit lifecycle — converged (P0-4, Q-0100)") — and by shipped code:
`disbot/services/channel_lifecycle_service.py:59-68` (`_OPERATIONS` = rename, move,
delete, reorder, `set_overwrite`, `clone`, `set_slowmode`, `set_topic`) and
`create_channels` at `:260`. Owner ruling Q-0100 (ANSWERED 2026-06-12,
`docs/owner/maintainer-question-router.md:3996`) directed exactly this convergence.

**Root cause:** the P0-4 PRs updated the subsystem row + known-drift note but not the
services-table row — two restatements of one fact inside one binding doc, one updated.

**Proposed fix (docs-only):** rewrite the `:46` row to the true operation set (incl.
`set_slowmode`/`set_topic`, which neither row mentions) + `create_channels`, keeping
the genuinely-unowned remainder (category CRUD UI, arbitrary before/after positioning).

**Risk class: LOW.**

### F3 — event-table payload for `channel.lifecycle_changed` undercounts operations (LOW)

**Evidence:** `docs/ownership.md:236` documents the `operation` payload key as
(`rename`/`move`/`delete`/`reorder`). The service emits the event for **all** its
operations — the eight `_OPERATIONS` (`channel_lifecycle_service.py:59-68`) plus the
create path — through the single `_emit_event` (`:596-613`), so subscribers coded to
the documented set silently miss `set_overwrite`/`clone`/`set_slowmode`/`set_topic`/
`create` payloads. (`role.lifecycle_changed` at `:237` is accurate —
`role_lifecycle_service.py:53` matches create/edit/delete.)

**Root cause:** same as F2 — payload row not updated when the operation set grew.

**Proposed fix (docs-only):** update the payload row; consider noting the operation
vocabulary is `_OPERATIONS` + `create` so the doc names the source of truth.

**Risk class: LOW.**

### F4 — ownership.md's `server_logging` row is stale at v1; v2 shipped (LOW)

**Evidence:** `docs/ownership.md:40` describes "Server event logging **v1** (Q-0109)"
with exactly five listeners (`on_message_delete`/`on_message_edit`/`on_member_join`/
`on_member_remove`/`on_member_update`) and three categories. Shipped v2
(the band-#1620 server-logging depth arc, #1594/#1618/#1619):
`disbot/cogs/logging_cog.py:258` `on_audit_log_entry_create`, `:268`
`on_voice_state_update`, `:286` `on_raw_message_delete`, delegating to
`server_logging.log_audit_entry` (`disbot/services/server_logging.py:1631`),
`log_voice_state` (`:1740`), `log_uncached_message_delete` (`:1808`); four new
categories (`moderation`/`channels`/`server`/`voice`,
`disbot/services/server_logging_config.py:89-94`) plus exclusion lists (`:98-100`).
`docs/server-logging.md:338+` documents v2 correctly — only the binding ownership row
lags. The routing contract itself verifies clean: event routes terminate at `events`,
never `mod` (`server_logging.py:209-224` `_ROUTE_FALLBACK`), auto-create is opt-in
gated (`:142-145`) and routes through the sanctioned
`core.runtime.guild_resources.ensure_channel` (allowlisted in
`tests/unit/invariants/test_no_silent_auto_create.py:68`).

**Root cause:** v2 shipped against the subsystem doc without touching the ownership
row (the same one-fact-two-homes pattern as F2).

**Proposed fix (docs-only):** refresh the row to "v1+v2", listing the eight listeners
or (better) pointing at `docs/server-logging.md` for the listener/category inventory
instead of restating it — restatement is what drifted.

**Risk class: LOW.**

### F5 — folio still says clone/overwrites/creation are outside the lifecycle service (LOW)

**Evidence:** `docs/subsystems/server-management.md:118-119`: "Channel creation
remains owned by resource provisioning; clone, overwrites, and some
category/lifecycle follow-ups remain outside the shipped lifecycle service." Stale on
both clauses after Q-0100/P0-4 (see F2 evidence): clone + set_overwrite are owned
operations, and **ad-hoc operator** creation routes through
`ChannelLifecycleService.create_channels` (subsystem-*bound* creation stays with
`ResourceProvisioningPipeline`). The folio's own last-updated stamp (2026-06-23)
post-dates the Q-0100 convergence (2026-06-12), so the stale text survived an update
pass.

**Root cause:** folio "Current state" prose restates ownership facts instead of
linking them (the folio's own §"Rules & approved structures" says "link, don't
restate" — this paragraph predates that discipline).

**Proposed fix (docs-only):** correct the sentence and point at `docs/ownership.md`'s
channel row for the split.

**Risk class: LOW.**

### F6 — no write-boundary invariant fences the reaction-role/role-menu/temp-role tables (LOW)

**Evidence:** every neighboring server-management write seam is AST-fenced:
thresholds (`tests/unit/invariants/test_no_direct_role_threshold_writes.py`, empty
allowlist), moderation (`test_no_direct_moderation_writes.py`), channel + role
lifecycle (`test_no_direct_channel_mutations.py` / `test_no_direct_role_mutations.py`),
chain (`test_chain_write_boundary.py`), mining (`test_mining_write_boundary.py`).
The reaction-role family has **no** equivalent: nothing pins `role_menus` /
`role_menu_options` / `reaction_role_message_modes` / `role_grants` /
`reaction_roles` writes to `reaction_role_service` / `role_grants_service`
(grep of `tests/unit/invariants/` for `reaction_role|role_menus|role_grants` →
only an unrelated XP-listener test). Today all writers conform (F1 evidence) and the
only view-level DB touch is a read (`disbot/views/roles/diagnostics_panel.py:125`
`get_pickup_stats`) — but conformance is unenforced, and this is the subsystem's
newest, largest mutation surface (11 PRs).

**Root cause:** the overhaul shipped the audited seam without the ratchet step the
older seams got ("enforce, don't exhort" — Q-0132/Q-0194).

**Proposed fix (tests-only, contained):** add
`tests/unit/invariants/test_reaction_role_write_boundary.py` mirroring
`test_chain_write_boundary.py` — forbid `utils.db.role_menus` / `utils.db.role_grants`
write-primitive calls (and `add_reaction_role`/`remove_reaction_role`) outside the two
services; allowlist `guild_lifecycle.py` teardown.

**Risk class: LOW** (tests/tooling only; no runtime behavior change).

## Observations (not findings)

- **Second slowmode writer is sanctioned, not drift:** the security raid lockdown
  edits a channel's slowmode directly (`docs/ownership.md:45` documents it) while
  `ChannelLifecycleService.set_slowmode` is the audited operator path. Two writers,
  one documented carve-out — worth a one-line cross-reference in the channel row if
  F2 is fixed, not a violation.
- **Dual read paths for the `logging_enabled` master switch** —
  `server_logging.is_enabled` (`server_logging.py:136`, raw `db.get_setting` +
  `_truthy`, default OFF) vs `server_logging_config.load_policy` (`resolve_value`,
  `DEFAULT_ENABLED = False`, `server_logging_config.py:85`). Defaults agree and a
  schema test pins spec-vs-policy defaults, so no behavior gap today; noted because
  `runtime_contracts.md` §9 prefers the `resolve_setting` seam for scalar reads.

## Counts

| Risk class | Count |
|---|---|
| LOW (docs/tooling, fixable by a follow-up session now) | 6 |
| RISKY (runtime/money/auth — flag-only) | 0 |

## Best Wave-2 dispatch candidate

**F1 (batched with F2–F5 as one docs-only "ownership/folio truth refresh" PR)** —
one session, five stale statements in two docs, all evidence lines above; zero
runtime risk. F6 is the best *second* dispatch (a small tests-only PR, the durable
guard).
