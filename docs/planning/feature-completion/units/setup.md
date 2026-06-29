# Setup wizard — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** Setup wizard · **Type:** server-fn · **Family:** management
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> **Registry note:** Setup is **not** a `subsystem_registry` entry (it is a platform surface, not a
> hub-routed subsystem). Source: `disbot/cogs/quicksetup_cog.py` (`!setup`/`/setup` → Essential Setup) ·
> `disbot/cogs/setup_cog.py` (`!setupadvanced` + on-join launcher) · `disbot/views/setup/essential_setup.py`
> (the spine) · `disbot/views/setup/sections/` + `disbot/views/setup/final_review.py` (advanced draft lane) ·
> `disbot/services/setup_operations.py` / `setup_access.py` / `setup_session.py` / `setup_readiness.py` ·
> `scripts/check_setup_copy.py` (jargon CI guard) · folio `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Setup is the **guided server onboarding** surface,
> two coexisting paths: the **Essential Setup spine** (`!setup`/`/setup`, the primary path since #1438) —
> a linear, plain-language, **one-action-per-step, direct-apply** wizard (8 steps: server-type →
> greet → mods → block-spam → log channel → reward activity → help desk → command channels), with a
> server-type starter preset, a "Check my setup" readiness health check, an extras menu, and restart-safe
> resume (migration 099); and the **advanced wizard** (`!setupadvanced`) — the per-section draft →
> Final-Review apply lane. Admin-gated (+ Q-0098 `setup_delegate`); every write routes through the
> canonical pipelines (settings / binding / channel+role lifecycle / `apply_operations`); zero-jargon is
> CI-enforced. The named ▶ Next is the **PR-3b draft→Final-Review editor rework** + the live walkthrough.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — guided, jargon-free, one-action-per-step, direct-apply spine
      (`essential_setup.py`); 8 steps cover the six readiness essentials + command access; advanced path
      covers per-section config.
- [x] **Every best-in-class sub-option** — server-type presets, skip/back per step, "Check my setup"
      readiness, extras menu, custom naming; meets/exceeds MEE6/Carl-bot onboarding (not formally
      benchmarked → punch).
- [x] **Failure modes honest** — each step validates picks before apply (ephemeral error, no silent
      no-op); resource-create failures surface + don't advance.
- [x] **Idempotent / re-runnable** — each step write is reapply-safe; the spine persists position and
      can be re-run; settings overwrite cleanly.

### B. Reachability & UI
- [x] **The wizard IS the panel** — `!setup`/`/setup` (Essential), `!setupadvanced`/`/setup-advanced`
      (advanced), + the bot-join launcher in `#superbot-setup`.
- [x] **Reachable every natural way** — commands + on-join launcher + (re)entry via Resume button;
      docstrings are plain-language.
- [x] **Integrated into Setup** — it *is* Setup.
- [x] **Return navigation** — Back/Skip on every step (after step 0); persistent Resume after restart.
- [x] **In-place, not spammy** — step embeds edit in place; session persists `essential_step` +
      `essential_message_id`.

### C. Convenience
- [x] **No needless steps** — exactly the essentials; extras deferred to a menu; direct-apply (no draft
      phase on the primary path).
- [x] **Sensible defaults + presets** — five server-type starter bundles (community/gaming/support/
      creator/exploring), all reversible.
- [x] **Clear feedback** — per-step summary lines + a recap embed; "Check my setup" ✅/➖ checklist;
      step counter "Step X of 8".

### D. Authority & safety
- [x] **Authority re-checked at callback** — `administrator` gate on entry; `setup_access` (owner /
      admin / delegated admin); Final Review re-checks `can_apply_setup` at apply (Q-0098).
- [x] **All writes through audited seams** — `_set` → `SettingsMutationPipeline`; `_bind` →
      `BindingMutationPipeline`; `apply_operations` dispatches to the canonical pipelines; single-flight
      apply lock.
- [x] **Resource creation uses the provisioning pipeline** — channels via `ChannelLifecycleService`,
      roles via `RoleLifecycleService` / `role_automation`; previewed + audited.
- [x] **Reuses governance** — the capability/tier floor + `setup_delegate` minted only after a live
      `can_apply_setup` re-check; no second allowlist.

### E. Configuration
- [x] **Configures OTHER subsystems via their pipelines** — the spine writes welcome/moderation/automod/
      logging/xp/ticket/command-access settings + bindings through the audited seams.
- [x] **Draft / Final-Review lane (advanced)** — sections stage `SetupOperation` rows; Final Review
      applies in canonical phase order (create → bind → set). The editor rework is the ▶ Next → punch #1.
- [x] **config-input widgets** — plain-language step widgets + the advanced section widgets.

### F. Wiring & discoverability
- [x] **Registered** — not a registry subsystem (by design); cogs loaded in `config.py`; commands
      discoverable.
- [x] **Discoverable in Help** — plain-language command descriptions; extras menu links each optional
      feature's command; the jargon CI guard (`check_setup_copy.py`) keeps copy plain.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_essential_setup.py` (flow nav, first-step-no-back, step validation,
      direct-apply via mocked pipelines) + the setup-simulator + section tests +
      `test_setup_operations*.py`.
- [x] **Authority tests** — `test_setup_access.py` (owner/admin/delegated); Final-Review apply gate.
- [x] **Mutation-seam tests** — `test_setup_operations.py` / `…_draft.py` (dispatch, idempotence);
      `test_setup_copy_jargon.py` (zero-jargon ratchet).
- [ ] **Live walkthrough recorded** — pending → punch #2.
- [ ] **Owner ✔** — pending → punch #3.

## Punch-list (clear these to certify)
1. **PR-3b: draft→Final-Review editor rework** *(offline, deepening — the named ▶ Next)* — the advanced
   wizard's multi-operation review/edit UI polish.
2. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, walk the 8-step spine end-to-end on a
   real guild (incl. the slow logging/reward steps + restart-resume), with screenshots; final jargon sweep.
3. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."
4. **Delegated-admin mid-flow revocation test** *(offline, minor)* — assert revocation between opening
   Final Review and Apply is blocked at the gate.
5. **Resource-create failure-recovery test** *(offline, minor)* — a mocked create failure must not advance
   the step and must let the operator retry without orphaning resources.
6. **Jargon baseline → 0** *(offline, minor)* — keep lowering the `check_setup_copy.py` baseline as
   sections' copy is cleaned.

## Evidence
- **Tests:** `tests/unit/views/setup/test_essential_setup.py` · `tests/unit/services/test_setup_*.py` ·
  `tests/unit/invariants/test_setup_copy_jargon.py` · `tests/unit/views/setup/sections/test_*`
- **Walkthrough:** pending (punch #2)
- **Owner sign-off:** pending (punch #3)

## Verdict
Setup is a **structurally complete, fully-audited** onboarding surface — a plain-language, direct-apply
8-step Essential spine (primary) plus an advanced draft→Final-Review lane, admin- and delegate-gated,
writing through every canonical pipeline (settings/binding/lifecycle), restart-safe, with zero-jargon
CI enforcement and a strong test suite. It is **not yet `✔ certified`**: the gaps are the **PR-3b
advanced-editor rework** (#1, the named ▶ Next), the **live walkthrough/sign-off** (#2/#3), and a couple
of edge-case tests (#4/#5). No safety/audit/dead-end issues found.
