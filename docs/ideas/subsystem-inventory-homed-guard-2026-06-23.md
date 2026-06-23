# Idea — a `check_subsystem_inventory_homed` guard (close the inventory-table drift class)

> **Status:** `ideas`. Not a plan, not approval. Source + binding contracts + `current-state.md` win.
> **Subsystem:** none (S4/S3 docs-system tooling). Captured 2026-06-23 (Q-0089) by the ultracode
> shared-dependency-map session.

## The drift this catches (verified, not hypothetical)

While building the [ultracode map](../ultracode/shared-dependency-ownership-map.md), four read-only
mapping agents found the repo's **own inventory docs had silently fallen behind source**:

- `docs/repo-navigation-map.md` § "Subsystem cheat sheet" **table** lists ~36 subsystems and is
  **missing 18 shipped cogs** (automod, image_moderation, role_grants, bootstrap_access, farm, casino,
  treasury, creature, creature_battle, starboard, paragon, hermes, health_maintenance,
  media_maintenance, btd6_events/ops/reference/strategy). Source has **54 `*_cog.py`** / **41**
  registered `SUBSYSTEMS`.
- `docs/ownership.md` ownership tables list **only `fishing`** of the newer subsystems — treasury,
  farm, casino, creature, starboard have shipped sole-writer services but no ownership row.

Both are exactly the "ledger lags source" drift the project already fights with the reconciliation
pass — but here the source-of-truth is a **per-subsystem table**, and nothing asserts each shipped cog
has a row. The seeding verification report inherited this drift (it reported "36 subsystems").

## The guard

A stdlib checker `scripts/check_subsystem_inventory_homed.py` (+ a warn-first ratchet test in
`tests/unit/invariants/`, allowlist `architecture_rules/inventory_homed_exceptions.yml`) that asserts:

1. every `disbot/cogs/*_cog.py` (or every `subsystem_registry.SUBSYSTEMS` key) is present as a row in
   the **canonical inventory surface**, and
2. every subsystem that owns a `services/*_service.py` sole-writer + a table appears in the
   `ownership.md` ownership table.

Mirror the proven 3-file guard shape (script + ratchet test + exceptions yml) used by
`check_command_reachability.py` (#1370) and `check_migration_collision.py` (#1322) — warn-first so it
doesn't redden CI on day one, ratcheted so a *new* unhomed cog fails the build.

## Why it's worth having (and the honest caveats)

- It closes the drift class **at the root** instead of relying on a reconciliation pass to notice 18
  missing rows months later.
- **Dedup / prior art:** distinct from `check_docs._INVENTORY_COUNT_RE` (a soft *count* guard — doesn't
  assert per-cog presence), from `new_subsystem.py`'s checker (#1346, checks loader/extension-role/
  sector-folio/claim/born-red gaps — not cheat-sheet/ownership-table rows), and from the
  [`new-subsystem-followup-tracker`](new-subsystem-followup-tracker-2026-06-23.md) idea (that's about
  follow-up *depth*, this is about *inventory presence*).
- **Caveat — pick the right target doc.** Per CLAUDE.md, `docs/help-command-surface-map.md` is the
  *authoritative* command surface; the nav-map cheat-sheet table is partly superseded. The guard should
  assert presence in whichever doc is declared canonical, and the cheat-sheet table itself may want
  reconciling-or-retiring first (a separate follow-up the ultracode map § 7 flags).
- **Disposable (Q-0105):** if it proves noisy/low-value over a few sessions, delete it.

## Immediate (separable) follow-up regardless of the guard

Reconcile the two lagging tables now that the verified 18-cog / 5-service delta exists (it's enumerated
in [`ultracode/report-reconciliation-2026-06-23.md`](../ultracode/report-reconciliation-2026-06-23.md)
§ 2–3): add the missing cheat-sheet rows + the 5 ownership rows. A docs-only reconciliation slice.
