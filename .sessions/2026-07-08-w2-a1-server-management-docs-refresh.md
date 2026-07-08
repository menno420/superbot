# 2026-07-08 — Wave-2 lane A1: server-management docs truth refresh (audit F1–F5)

> **Status:** `complete`

Wave-2 dispatch of the server-management audit (`docs/analysis/server-management-audit-2026-07-08.md`,
Wave-1 lane A, PR #1844): fixed the five stale-doc findings F1–F5, each re-verified
against shipped source before editing (Q-0120). Docs-only; F6 (the reaction-role
write-boundary invariant) belongs to a sibling tests-only session and was not touched.

## Shipped (PR #1851)

- **F1** — `docs/ownership.md` role subsystem row: added the five reaction-role-overhaul
  tables (`role_menus`, `role_menu_options`, `reaction_role_message_modes`, `role_grants`,
  `role_menu_pickup_stats`; migrations 078–081 + 089/103 columns) with
  `services/reaction_role_service.py` / `services/role_grants_service.py` as the audited
  writers; retired the stale "`reaction_roles` direct via `utils/db/roles.py`" clause
  (verified: the service is the only `add_reaction_role`/`remove_reaction_role` caller;
  `cogs/role_cog.py:691` is a same-named command delegating to `unbind_emoji`).
- **F2** — `docs/ownership.md` services-table `ChannelLifecycleService` row now matches
  source (`channel_lifecycle_service.py:59-68` `_OPERATIONS` + `create_channels:260`):
  8 change ops incl. `set_overwrite`/`clone`/`set_slowmode`/`set_topic`, plus ad-hoc
  operator creation (P0-4, Q-0100); "Not owned" reduced to the true remainder
  (subsystem-bound creation, before/after positioning, category CRUD UI) + the
  security-slowmode carve-out cross-reference (audit "Observations" suggestion).
- **F3** — `channel.lifecycle_changed` payload row now enumerates all 9 `operation`
  values and names `_OPERATIONS` + the create path as the vocabulary's source of truth.
- **F4** — `server_logging` row refreshed v1 → v1+v2 (band-#1620 arc): the three v2
  listeners (`logging_cog.py:258/268/286`) → `log_audit_entry`/`log_voice_state`/
  `log_uncached_message_delete` (`server_logging.py:1631/1740/1808`), the four new
  categories + exclusion lists, and a pointer to `docs/server-logging.md` as canonical
  inventory instead of restating it.
- **F5** — folio `docs/subsystems/server-management.md:118-119` stale
  "creation/clone/overwrites outside the lifecycle service" prose replaced with the
  converged P0-4/Q-0100 statement, linking `ownership.md`'s channel row (link, don't
  restate).

Verification: `check_docs --strict` ✓, `check_current_state_ledger --strict` ✓,
`check_quality --check-only` ✓.

## Context delta

- **Needed but not pointed to:** nothing — the audit's file:line evidence was a
  complete route; every finding re-verified in one grep/read each.
- **Pointed to but didn't need:** none of substance.
- **Discovered by hand:** `reaction_role_message_modes` DB primitives live in
  `utils/db/roles.py` (not `utils/db/role_menus.py` as the table-name grouping
  suggests) — now reflected in the ownership row's reads clause.
- **Decisions made alone:** folded the audit's "Observations" security-slowmode
  carve-out cross-reference into the F2 row rewrite (audit suggested it "if F2 is
  fixed"); listed migrations 089/103 as column additions in the role row.
- **Flagged for maintainer / known limits:** conformance of the reaction-role write
  seam is still *unenforced* until F6's invariant test ships (sibling session).

⚑ Self-initiated: none — owner-directed campaign task (Wave-2 A1 dispatch).

💡 Session idea: an **event-payload parity checker** — a small `check_docs`-style lint
that parses the ownership.md event-table `operation`/enum vocabularies and diffs them
against the emitting service's source-of-truth tuple (e.g. `_OPERATIONS`,
`role_lifecycle_service`'s create/edit/delete). F3's drift class (payload row not
updated when the operation set grows) is mechanical and recurring — exactly the
"enforce, don't exhort" (Q-0132/Q-0194) shape. Dedup-grepped `docs/ideas/`: no
existing payload-parity idea. Recorded here only (no `docs/ideas/` file — that area
is claimed by a sibling session this wave).

⟲ Previous-session review: the Wave-1 audit session (#1844) set the standard for
dispatchability — every finding carried file:line evidence *and* a proposed fix, which
made this session's Q-0120 re-verification nearly free (zero contradictions found).
One improvement: the audit quotes the stale claims but not the exact doc spans to
replace; a fixer still re-greps to locate row boundaries in 1000-char table rows.
Workflow improvement: the audit template should include a "stale text (verbatim)"
snippet per finding so a Wave-2 fixer can Edit directly from the report.

Documentation audit: both strict checkers green; this session's conclusions live in
`docs/ownership.md` + the folio + this card; no new owner decisions to route; nothing
chat-only left behind.
