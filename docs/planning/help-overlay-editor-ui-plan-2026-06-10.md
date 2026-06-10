# Help overlay editor UI — implementation plan (audit Phase 5)

> **Status:** `plan` — **EXECUTED same day: PR A = #677 · PR B = #679**
> (both live-verified on real Postgres — editor round-trip incl. the
> hide/rename → live-Help agreement, and the Home builder's
> stage → mandatory-preview → save → byte-identical reset). Produced by the
> 2026-06-10 eval-support session as the queue's "Help overlay editor UI
> (plan-first)" item — [help audit](help-cog-customization-audit-2026-06-09.md)
> Phase 5. Two PRs; PR A has no migration and rides entirely on shipped seams.
> As-built deviations: none of substance — the §4 design shipped as written
> (the Home builder lives in `views/help/home_builder.py` beside the editor;
> Reset-all's copy was extended to mention the Home message it also clears).

## 1. Goal

Give operators a Discord UI to edit what `#659` made storable: per-guild Help
**hide / rename / re-describe** of hubs and subsystems, plus the **Q-0059
embed-builder Home message** — with mandatory preview, per-field and full
reset, and every write through the existing audited seam. Today the overlay
is live in all five render paths but only mutable from code; the eval
checklist explicitly tells the maintainer "nothing for you to click-edit yet".

## 2. What already exists — duplicate nothing

| Piece | Where | State |
|---|---|---|
| Storage | `help_overlay` (migration 064; CHECK kinds `hub`/`subsystem`) | shipped #659 |
| Audited writes | `services/help_overlay_mutation.py` — `set_overlay_fields(guild_id, entity_kind, entity_key, *, actor, display_hidden=…, display_name=…, description=…)` (UNSET = untouched · value = override · `None` = reset field; all-NULL row deleted), `reset_guild_overlay(guild_id, *, actor)`; admin gate, catalogue-key validation, cache invalidation, `audit.action_recorded` | shipped #659 |
| Read model | `services/help_overlay.py` — `get_guild_help_overlay`, `VALID_ENTITY_KINDS`, bound constants | shipped #659 |
| Valid keys | `services/help_catalogue.py` `build_help_catalogue()` — the editor's pickers enumerate **catalogue** hubs/subsystems (never the registries directly), so written keys are valid by construction | shipped #657 |
| Render + preview | `services/help_projection.py` (+ `project_help_with_execution`); staff-hub **👁 Help Preview** shows overlay state + `orphaned_overrides` | shipped #657/#656/#671 |
| Settings-hub integration idiom | `DomainPanelSpec` on a subsystem's `SubsystemSchema` (see `cogs/cleanup/schemas.py`) → the hub discovers a domain-config group | shipped #654 |
| Staff-hub pattern | `views/server_management/hub.py` buttons (`custom_id="server_management:<panel>"`), subpanel files beside `access_map.py` | shipped #656 |

## 3. Decisions already made — the design envelope

- **Q-0055 (executed):** hiding is **display-only**; the import fence on
  admission paths must stay untouched. The editor copy labels hidden entries
  "hidden from Help but still executable".
- **Q-0056 (executed):** renames are **Help-only** — the editor lives under
  Help branding, not a generic "rename subsystem" surface.
- **Q-0058 (executed):** operator surfaces always show **custom + default +
  stable key** (presentations already carry the defaults).
- **Q-0059:** Home message = **embed builder** (title / description / color),
  safety floors mandatory regardless: bounded lengths, embed limits enforced,
  **mentions suppressed**, validation + **preview before save**,
  reset-to-default. **No variables/templating** (not chosen).
- **Q-0032 posture:** no new command names — entry points are the staff hub
  and the Settings hub.
- Views write **only** through `help_overlay_mutation` (no direct db);
  callbacks re-check admin at execution time (opening ≠ authority).

**Out of scope (do not drift into):** audit Phase 4 command/panel-action
records and any ordering (Q-0057 rider: blocked on stable action
identities); the optional setup-section/final-review lane (draft-lane op
kinds + migration for a focused, reversible, single-domain edit is the wrong
lane per `ownership.md` — revisit only if the maintainer asks for staged
Help changes); templating/variables.

## 4. Design

### 4.1 Entry points (both route to the same view)

1. **Staff hub:** new `✏️ Help editor` button on
   `views/server_management/hub.py` (`custom_id="server_management:help_editor"`),
   placed beside 👁 Help Preview — edit and verify live next to each other.
2. **Settings hub:** new `cogs/help/schemas.py` registering a
   `SubsystemSchema(subsystem="help", domain_panels=(DomainPanelSpec(
   name="Help appearance", …, capability_required="help.settings.configure"),),
   version=1)` in `HelpCog.cog_load`, plus the `help.settings.configure`
   capability on the `help` SUBSYSTEMS entry. The Settings hub then
   discovers "Help appearance" as a domain-config group (13th group; the
   coverage invariant `test_domain_panel_declarations.py` and the
   settings-hub taxonomy tests pin the count — update both).

### 4.2 View architecture (`views/help/editor.py`, new package)

`BaseView`-derived, ephemeral, admin-checked at every callback:

- **HelpEditorHomeView** — overview embed: counts of current overrides
  (hidden / renamed / re-described, from `get_guild_help_overlay`), orphan
  count if any, buttons: `Hubs` · `Subsystems` · `Home message` (PR B) ·
  `Reset all…` (confirm step) · `Back`.
- **Entity picker** — paginated select over `build_help_catalogue()` entries
  (reuse the Settings-hub >25 pagination idiom); option label = current
  display (custom if set), description = `default · stable key` per Q-0058,
  "🙈" prefix when hidden.
- **HelpEntityEditorView** — one entity: embed shows custom + default + key
  for each field; buttons: `Hide`/`Unhide` (display_hidden toggle),
  `Rename…` (modal, 1 text input, ≤ the shipped bound), `Re-describe…`
  (modal), `Reset name` / `Reset description` (field `None`), `Reset entity`.
  Every action: one `set_overlay_fields` call → re-render from the read
  model (the write's cache invalidation makes the re-read truthful) → footer
  line "live in Help now — verify with 👁 Help Preview".
- A Discord **modal cannot contain a select** (journal rule) — all entity
  choice happens in views; modals carry only text inputs.

### 4.3 PR B — the Q-0059 Home-message embed builder

- **Migration 067 (or next free):** widen the `entity_kind` CHECK with
  `'home'` exactly as migration 064's header pre-plans, and add bounded
  home-only columns — do **not** overload the 100-cap presentation columns:
  `home_title` (≤ 256, embed-title cap), `home_body` (≤ 2000), `home_color`
  (int, nullable). One `home` row per guild (`entity_key='home'` constant).
- **Service:** extend `help_overlay_mutation` with
  `set_home_message(guild_id, *, actor, title=UNSET, body=UNSET, color=UNSET)`
  + reset semantics identical to `set_overlay_fields` (all-NULL ⇒ row
  deleted ⇒ default Home byte-identical — pin it). Bounds enforced in the
  service; CHECK is the backstop. Same audit event shape.
- **Render:** Help Home composes the custom embed (title/body/color) when a
  home row exists; **mention suppression** at render (`allowed_mentions` none
  + escape `@` in stored text); absence ⇒ today's Home **byte-identical**
  (extend the existing no-rows pin test).
- **Builder UI:** `HomeMessageBuilderView` — `Edit title…` / `Edit body…`
  (modals), `Color` (select of named colors — no free-form hex parsing
  in v1), **`Preview`** (renders the exact embed ephemerally), and **save is
  the explicit `Save` button only** (mandatory-preview rule: `Save` stays
  disabled until the staged draft has been previewed at least once;
  staged-not-saved state lives on the view).

## 5. PR slicing

| PR | Content | Risk | Migration |
|---|---|---|---|
| **A** | `views/help/editor.py` (+ `__init__`), staff-hub button, `cogs/help/schemas.py` + capability, taxonomy/coverage test updates, view/service tests, live round-trip | Low — writes ride the shipped audited seam | none |
| **B** | migration 067, `set_home_message` + bounds, Home render consumption, `HomeMessageBuilderView` with mandatory preview, byte-identical-default pin, tests + live round-trip | Medium — migration + render path | one, additive |

## 6. Tests & invariants

**Keep green (the ones this work can redden):** the Q-0055 admission-path
import fence; the no-rows byte-identical Help pins; `test_no_raw_sql_in_cogs`
(editor views call services only); `test_cog_size` (wire from `bot1`/existing
cog_load, don't grow `help_cog.py` toward 800); settings taxonomy counts
(12 → 13); `views` may not import `cogs`.

**New:** editor callbacks re-check admin (non-admin actor → no write, no
audit row); every editor action maps to exactly one mutation-service call
(AST or mock-spy); Home save without preview impossible; Home bounds +
mention suppression; reset-all confirm path; orphan display when the
catalogue loses a key.

**Live round-trip recipe (each PR):** boot → staff hub → editor → hide +
rename a subsystem → `!help` as member (hidden absent, rename rendered) →
👁 Help Preview agrees → reset all → byte-identical default; PR B: build →
preview → save → Home shows custom embed → reset → default. Audit rows
present for every write (`audit_log`).

## 7. Verification

`python3.10 scripts/check_quality.py --full` · `python3.10
scripts/check_architecture.py --mode strict` (0 errors) · `python3.10
scripts/check_docs.py` · the live recipe above on the sandbox bot.
