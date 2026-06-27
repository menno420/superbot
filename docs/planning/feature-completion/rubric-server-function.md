# Definition of Complete — server functions

> **Status:** `reference` — the completeness rubric for a **server-function** unit (moderation,
> economy, roles, welcome, settings, …). Grounded in
> [`command-integration-standard`](../../building-roadmap/command-integration-standard.md),
> [`config-input-standard`](../../building-roadmap/config-input-standard.md),
> [`capability-authority`](../../capability-authority.md), and
> [`ownership`](../../ownership.md). System: [`README.md`](README.md).

A server function is **complete** when it correctly does what it is supposed to in every case, is
reachable the most convenient way, has every option a best-in-class bot would offer for that job,
and is safe and audited. Copy the template at the bottom into `units/<key>.md`, tick each box **or
waive it with a one-line reason**, and list every gap as a **punch-list** item. The unit cannot be
`✔ certified` until the punch-list is empty and the owner signs off.

---

## A. Functional completeness — "does its job, in every case"

- [ ] **The core promise is fully delivered** — the function does what its name/Help says, for the
      normal case and the awkward ones (empty input, already-applied, target absent, permission
      denied).
- [ ] **Every sub-option a best-in-class bot offers for this job exists** — benchmarked against the
      category leader (e.g. Carl-bot/MEE6/Dyno for the equivalent function). Missing options are
      listed explicitly, not silently absent.
- [ ] **Failure modes are honest** — a blocked/failed action says *why*; no silent no-ops.
- [ ] **Idempotent / re-runnable** where that is the expectation (re-applying a setting, re-running
      setup) does the right thing.

## B. Reachability & UI — "the most convenient way"

- [ ] **A command panel exists** (`command-integration-standard` § 1) summarizing the function,
      listing primary actions as buttons/selects, linking to its settings, and linking back.
- [ ] **Reachable every natural way** — its command(s) **and** the relevant hub **and** Help all
      lead to it; an admin function is in the admin/Platform menus.
- [ ] **Integrated into the Setup wizard** where a server operator would expect to configure it
      during onboarding (or explicitly N/A).
- [ ] **Return navigation everywhere** — no dead-end views (`command-integration-standard` § 3).
- [ ] **In-place, not spammy** — actions edit the panel in place rather than posting ephemeral
      follow-ups where the house style expects an edit.

## C. Convenience

- [ ] **No needless steps** — the common operator path is short and obvious; bulk actions exist where
      a real server needs them (e.g. bulk role/channel ops).
- [ ] **Sensible defaults + presets** — the function works well out of the box; presets cover the
      common server shapes.
- [ ] **Clear feedback** — every action confirms what changed (and is auditable).

## D. Authority & safety

- [ ] **Authority is re-checked at callback time** (`capability-authority.md`) — opening a panel does
      not authorize later mutations; the capability/permission floor is enforced on execute.
- [ ] **All mutations go through the audited service seam** — no direct DB writes from cogs/views;
      `audit_events.emit_audit_action()` fires on auditable changes (`ownership.md`).
- [ ] **Resource creation uses the provisioning pipeline** — channel/role/category creation is
      previewed, confirmed, audited, and fails safe (no direct Discord create APIs).
- [ ] **Reuses governance** for any "where does this work" access control — no second allowlist.

## E. Configuration

- [ ] **Settings route through the settings/binding pipeline** — scalars via `SettingsMutationPipeline`,
      resource pointers via `BindingMutationPipeline`; no raw keys, no IDs-as-scalars
      (`command-integration-standard` §§ 5–7).
- [ ] **Setting widgets follow `config-input-standard`** — typed inputs, validation, clear labels,
      disabled-state messaging.
- [ ] **Every option that should be configurable is** — and nothing security-sensitive is editable
      below its authority floor.

## F. Wiring & discoverability

- [ ] **Registered in the subsystem registry** with correct `entry_points`, `category`,
      `visibility_tier`, and `capabilities`; homed in `ownership.md` / the navigation map.
- [ ] **Discoverable in Help** with a clear short description (`command-integration-standard` § 2).

## G. Tests & evidence (required for `✔ certified`)

- [ ] **Behavior tests** — the core promise + the awkward cases (empty/denied/absent/idempotent).
- [ ] **Authority tests** — unauthorized callers are rejected at execute time.
- [ ] **Mutation-seam tests** — writes go through the audited service; audit events fire.
- [ ] **Live walkthrough recorded** — `/verify-bot` boot + a scripted click-through (panel · each
      action · settings · setup step), with screenshots, attached to the certificate.
- [ ] **Owner ✔** — the maintainer has used it and confirms "it does its job the most convenient way;
      nothing left I'd add or move."

---

## Certificate template

Copy into `units/<registry-key>.md`:

```markdown
# <Function name> — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate. System: [`../README.md`](../README.md).

> **Unit:** `<registry-key>` · **Type:** server-fn · **Family:** <moderation|economy|community|…>
> **State:** ◐ assessed · **Assessed:** <date> · **Certified:** —
> Source: <cog> · <views/> · <service> · <settings schema>

## Rubric (server function)
A. Functional completeness — <tick/notes per item>
B. Reachability & UI — …
C. Convenience — …
D. Authority & safety — …
E. Configuration — …
F. Wiring & discoverability — …
G. Tests & evidence — …

## Punch-list (open gaps → certify by clearing these)
1. …

## Evidence
- Tests: <paths>
- Walkthrough: <link / pending>
- Owner sign-off: <pending | ✔ date>
```
