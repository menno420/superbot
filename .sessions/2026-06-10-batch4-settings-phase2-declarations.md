# 2026-06-10 — Batch 4: Settings Phase 2 declaration coverage + Q-0064 BTD6 rows

**Arc:** same continuation session as Batch 3 (#652 merged mid-session);
executed the consolidated plan's **Batch 4 core** on the same branch — the
declaration mechanism, the DT06 coverage invariant, and the decided Q-0064
BTD6 rows. Full CI mirror green.

**Shipped (PR — see branch; verify merged):**

- **`DomainPanelSpec` + `SubsystemSchema.domain_panels`** — domain-config
  Settings groups are now *declared per subsystem* in its own schema
  (registered at cog_load), replacing the Phase 1 curated
  `DOMAIN_CONFIG_SUBSYSTEMS` frozenset (deleted; regression-pinned gone).
  Cleanup is the first real registration (`cogs/cleanup/schemas.py`).
- **DT06 coverage invariant** (`test_domain_panel_declarations.py`): the
  declared set is pinned (`{"cleanup"}`), declarations must be well-formed +
  consumed by `actionable_settings_groups()`, and the frozenset stays retired.
- **Q-0064 row 1** — `btd6.version_announce_channel` is a first-class
  **binding**: declared in the BTD6 schema; `btd6_version_announce` reads
  binding-first with legacy-KV fallback (read failure degrades to KV;
  bound-but-deleted channel skips loudly rather than announcing at a stale
  pointer); `!btd6ops announcechannel` still writes the KV lane and **warns
  when a binding shadows it**. Write-path convergence = Phase 3.
- **Q-0064 row 2** — the CT group is a **guided flow** (parse → preview →
  confirm; `views/btd6/ct_group_flow.py`): `!btd6 ctteam <url/id>` now
  previews (live standing best-effort) with Confirm/Cancel — never an
  immediate write; Confirm re-checks Manage Server at callback time; the
  typed `btd6_ct_team_service` stays the mutation owner. No-arg + Manage
  Server gets a "Set CT team…" modal button. `clear` stays immediate.
- **Q-0073-B verified satisfied as-is**: economy declares both the
  `log_channel` binding and the `economy_log_channel` scalar (native
  selector) — the `!setlogchannel` pointer already projects into Settings;
  nothing built, recorded in the audit/plan stamps.
- Docs: settings audit §11 Phase 2 stamp · command-map BTD6 rows (also fixes
  the `test_schema_bindingspec_names_appear` doc pin for the new binding) ·
  plan/current-state/roadmap stamps.

**Open Phase 2 tail:** per-subsystem pointer-migration *classification*
(proof/logging rows) — a later slice; the dual-write seam untouched (Phase 3).

## Decisions made alone (ratify if they matter)

1. **Declaration home = `SubsystemSchema.domain_panels`** (not a separate
   registration API) — the audit's §10.1 "SubsystemSchema remains the
   declaration owner" line decided it; additive defaulted field, 40 importers
   unaffected.
2. **Bound-but-deleted announce channel skips (loud log) instead of falling
   back to KV** — falling back to a pointer the operator superseded would be
   surprising; the binding is the declared intent.
3. **CT guided flow surfaced on the existing `!btd6 ctteam` path** (preview
   replaces immediate set; entry button on the no-arg embed) rather than a
   new Settings-hub panel — Q-0064 decided the *shape*, not a surface move;
   this lands it where operators already configure it.
4. **`clear` stays immediate** — reversible, nothing to preview.

## Flagged for maintainer / known limits

- The announce channel now has **two write lanes** (binding via the canonical
  flow; KV via the typed command) with binding-first reads + a shadow warning
  on the command. Honest but temporary — Phase 3 converges them (audit §4
  economy has the same accepted duplication).
- The CT preview's live standing is best-effort: API down → "couldn't fetch,
  you can still confirm". Deliberate (config must not require the NK API).
- `CTGroupFlowModal` opens only from the entry button (interaction-bound);
  the prefix command can't open modals — pasted-arg path covers prefix users.

## Context delta

- **Needed but not pointed to:** the `test_schema_bindingspec_names_appear`
  doc pin (a new BindingSpec reddens CI until the settings command map
  documents it) — discovered via the full-mirror failure, not the route; the
  binding-add recipe should mention it (folio candidate).
- **Discovered by hand:** the settings subsystem view renders bindings
  read-only (editing is the wizard/binding flow) — "native selector" comes
  free with the declaration; no new editor needed.
- **One change that would have helped:** a one-line "what reddens when you
  add a binding/setting" checklist in the settings folio.
