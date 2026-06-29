# Proof Channel — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `proof_channel` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/proof_channel_cog.py` (`!prizemenu`/`!prizestatus`/`!timedprize` + `+prize`/
> `-prize` + `PrizeManagerView`) · `disbot/cogs/proof_channel/schemas.py` (BindingSpec + optional
> ResourceRequirement) · `disbot/core/runtime/bindings` (binding-first read) · folio
> `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Proof Channel runs **time-limited exclusive-access
> prize sessions** in a bound `#proof` channel: `+prize @winner` locks the channel read-only to everyone
> but the winner (Discord permission overwrites), `timedprize` auto-unlocks after N minutes (cancellable
> task, GC'd on unload), `-prize` ends it, `prizestatus` renders the current overwrites. The channel
> pointer is declared as a `BindingSpec` (capability `proof_channel.settings.configure`) and read
> binding-first with a name-lookup fallback that degrades safely on a bad/deleted row (well tested). The
> honest gaps: the lock/unlock mutates `channel.edit(overwrites=...)` **directly** (no
> `emit_audit_action`) and modal-submit paths re-resolve the channel but don't re-check the actor's
> permission; plus there are no command-authority / mutation tests and no binding-write UI yet.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — lock-for-winner / unlock / timed-unlock via permission overwrites
      (`_lock_for_winner`/`_unlock`, cog L76–94); idempotent (pure permission state, no DB writes);
      channel-not-found degrades gracefully; member-parse errors return a friendly message.
- [x] **Every best-in-class sub-option** — grant / timed-grant / status / end + an interactive panel;
      the niche (exclusive proof sessions) is fully covered. No standalone "revoke" beyond `-prize`.
- [x] **Failure modes honest** — binding-read failure degrades to name lookup (one bad row never kills a
      prize command); modal member-not-found → `❌`.
- [x] **Idempotent / re-runnable** — re-locking re-applies the same overwrites; unlock returns to
      read-only deterministically.

### B. Reachability & UI
- [x] **A command panel exists** — `!prizemenu` → `PrizeManagerView` (Grant Access / Timed Access / End
      Session buttons).
- [x] **Reachable every natural way** — entry points `prizemenu`/`prizestatus`/`timedprize` + `+prize`/
      `-prize` + `build_help_menu_view` hook + Moderation-hub child (`parent_hub: moderation`).
- [N/A] **Integrated into Setup** — the channel binding is optional; no dedicated wizard step (configured
      via Settings once the binding-write UI lands → punch #3).
- [x] **Return navigation** — panel actions edit in place; status is a leaf.
- [x] **In-place, not spammy** — all effects are in-channel permission changes + confirmations.

### C. Convenience
- [x] **Low-step** — one command per action; the panel exposes all three.
- [x] **Defaults** — no per-guild knobs; the permission model is fixed (deny-all-but-winner; bot keeps
      view). Acceptable for the niche.
- [x] **Clear feedback** — every command confirms the winner/duration/read-only state; `prizestatus`
      tabulates the overwrites.

### D. Authority & safety
- [x] **Authority re-checked at callback** — ✅ **fixed (punch #1, 2026-06-29).** Prefix commands carry
      `@has_permissions(manage_channels=True)`; the modal-submit + panel mutation callbacks now re-verify
      the actor holds `manage_channels` via `_reject_without_manage_channels(interaction)` before acting
      (grant / timed / End Session + both modal `on_submit`s), so opening the panel no longer authorizes a
      later callback. Defensive (missing perms → deny, never raises).
- [x] **All mutations through the audited seam** — ✅ **fixed (punch #2, 2026-06-29).**
      `_lock_for_winner`/`_unlock` now emit `audit.action_recorded` (subsystem `proof_channel`,
      `prize_access_grant`/`prize_access_revoke`, `target=channel:<id>`, actor threaded from the invoker;
      timer auto-unlock is `actor_type="system"`) via `_emit_prize_audit` after the overwrite change. The
      audit is best-effort (a bus failure never blocks the access change).
- [x] **Resource binding via the binding pipeline (read)** — channel read binding-first
      (`get_binding(guild.id, "proof_channel", "proof_channel")`) with safe fallback; the BindingSpec +
      optional ResourceRequirement are declared. The binding **write** UI is pending → punch #3.
- [x] **Reuses governance** — staff visibility tier + the declared capabilities; no second allowlist
      (enforcement is `manage_channels` today, see punch #1).

### E. Configuration
- [x] **Binding pipeline (declared)** — `BindingSpec(name="proof_channel", kind=CHANNEL, required=False,
      capability_required="proof_channel.settings.configure")`; resource requirement OPTIONAL (suggested
      `proof`). Schema registered idempotently at cog load.
- [ ] **config-input widgets** — ⚠ no binding-write widget yet (Settings Phase 3); the channel is bound
      via the provisioning catalogue / name fallback today. → punch #3.
- [x] **Everything configurable that should be** — the only config surface is the channel binding (above);
      no scalars by design.

### F. Wiring & discoverability
- [x] **Registry** — key `proof_channel`, `category: moderation`, `visibility_tier: staff`,
      `parent_hub: moderation`, entry points + 4 capabilities (`proof_channel.access.grant/revoke/timed`,
      `proof_channel.settings.configure`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook → the prize panel; KNOWN_PANEL_COMMANDS entry.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_proof_channel_schema.py` (schema declaration, idempotent register,
      binding-first read precedence + 4 fallback/degrade cases, settings actionability) — 8 cases.
- [x] **Authority tests** — ✅ `test_proof_channel_authority_audit.py` pins that a non-`manage_channels`
      actor is denied at every mutation callback (both modals + grant/end buttons) and the mutation is
      not performed (punch #1).
- [x] **Mutation-seam tests** — ✅ same file asserts lock/unlock emit the `prize_access_grant`/
      `prize_access_revoke` audit events (with the right target/actor/scope), the timer unlock is a
      `system` actor, and a bus failure never blocks the access change (punch #2).
- [ ] **Live walkthrough recorded** — pending → punch #4.
- [ ] **Owner ✔** — pending → punch #5.

## Punch-list (clear these to certify)
1. ~~**Modal authority re-check + tests**~~ ✅ **DONE 2026-06-29 (dispatch run, PR #1550)** — every
   mutation callback (both modals + grant/end buttons) re-verifies `manage_channels` via
   `_reject_without_manage_channels`; `test_proof_channel_authority_audit.py` pins it.
2. ~~**Audit the lock/unlock**~~ ✅ **DONE 2026-06-29 (dispatch run, PR #1550)** — lock/unlock emit
   `prize_access_grant`/`prize_access_revoke` via `_emit_prize_audit` (subsystem `proof_channel`); the
   timer auto-unlock is a `system` actor; best-effort so a bus failure never blocks access. Tested.
3. **Binding-write UI** *(offline, deepening)* — wire the Settings Phase-3 binding widget so the proof
   channel can be bound from the settings hub (today: provisioning catalogue + name fallback).
4. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, run `+prize`/`timedprize`/`-prize`,
   confirm the overwrites + auto-unlock + panel, with screenshots.
5. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_proof_channel_schema.py` (8 cases) ·
  `tests/unit/cogs/test_proof_channel_authority_audit.py` (9 cases — authority re-check + audit emission) ·
  `tests/unit/services/test_resource_provisioning_*` (provisioning catalogue exercises the proof resource)
- **Walkthrough:** pending (punch #4)
- **Owner sign-off:** pending (punch #5)

## Verdict
Proof Channel **delivers its core promise** — exclusive, optionally-timed prize sessions with a binding-
first channel read that degrades safely — and is well wired (command/panel/Help/registry) with thorough
binding tests. The two real maturation gaps it carried are **now closed (2026-06-29, PR #1550):** the
lock/unlock emit an audit event (#2) and every mutation callback re-checks actor authority (#1), both
test-pinned. It is **not yet `✔ certified`** only on the deferred items: a missing binding-write UI (#3,
deepening) and the owner-paced live walkthrough + sign-off (#4/#5). No dead-ends; no money/DB risk.
