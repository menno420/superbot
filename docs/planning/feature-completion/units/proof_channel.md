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
- [ ] **Authority re-checked at callback** — ⚠ **partial.** Prefix commands carry
      `@has_permissions(manage_channels=True)`; the **modal-submit paths re-resolve the channel but do
      not re-check the actor's permission**. → punch #1.
- [ ] **All mutations through the audited seam** — ❌ **gap.** `_lock_for_winner`/`_unlock` call
      `proof_channel.edit(overwrites=...)` directly (cog L83/L94) with **no `emit_audit_action`** — a
      prize session leaves no audit trail. (It is an ephemeral access grant, not a persisted DB mutation,
      so the risk is low — but other access surfaces audit.) → punch #2.
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
- [ ] **Authority tests** — ❌ none for `manage_channels` enforcement / modal re-check → punch #1.
- [ ] **Mutation-seam tests** — ❌ none asserting the overwrite changes / audit emission → punch #2.
- [ ] **Live walkthrough recorded** — pending → punch #4.
- [ ] **Owner ✔** — pending → punch #5.

## Punch-list (clear these to certify)
1. **Modal authority re-check + tests** *(offline, minor)* — re-verify the actor holds `manage_channels`
   in the modal-submit paths before `_lock_for_winner`; add command-authority tests.
2. **Audit the lock/unlock** *(offline/owner, deepening)* — route the permission change through (or
   alongside) `emit_audit_action` so prize sessions leave a trail; add a mutation test mocking
   `channel.edit`. (Low risk — ephemeral access grant, not a DB mutation.)
3. **Binding-write UI** *(offline, deepening)* — wire the Settings Phase-3 binding widget so the proof
   channel can be bound from the settings hub (today: provisioning catalogue + name fallback).
4. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, run `+prize`/`timedprize`/`-prize`,
   confirm the overwrites + auto-unlock + panel, with screenshots.
5. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_proof_channel_schema.py` (8 cases) ·
  `tests/unit/services/test_resource_provisioning_*` (provisioning catalogue exercises the proof resource)
- **Walkthrough:** pending (punch #4)
- **Owner sign-off:** pending (punch #5)

## Verdict
Proof Channel **delivers its core promise** — exclusive, optionally-timed prize sessions with a binding-
first channel read that degrades safely — and is well wired (command/panel/Help/registry) with thorough
binding tests. It is **not yet `✔ certified`**, and unlike the other moderation units it carries two real
maturation gaps: the lock/unlock mutates channel permissions **directly without an audit event** (#2) and
the **modal paths don't re-check actor authority** (#1, low risk since prefix commands are gated), plus a
missing binding-write UI (#3) and the live walkthrough/sign-off (#4/#5). No dead-ends; risk is low (an
ephemeral access grant, not money/DB), but the audit + authority gaps should close before wider use.
