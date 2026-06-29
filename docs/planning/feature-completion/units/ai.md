# AI assistant — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `ai` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/ai_cog.py` (`!ai`/`/ai` group + `aimenu` panel) · `disbot/cogs/ai/schemas.py`
> (M1 settings) · `disbot/core/runtime/ai/natural_language_stage.py` (the single NL reply stage, order 70)
> · `disbot/services/ai_natural_language_policy.py` (mode/scope resolver) · `ai_task_router` ·
> `ai_instruction_service` · `disbot/services/ai_policy_mutation.py` (audited policy seam) ·
> `ai_decision_audit_service` · `disbot/cogs/ai_review_cog.py` · folio AI / `docs/subsystems/`

> Assessed during the completion-first arc (Q-0209). AI is the **natural-language assistant + AI platform
> control** unit: a single message-pipeline NL stage routes every passive reply through one policy
> resolver (modes `always_reply`/`mention_only`/`disabled`/`inherit`, scope cascade channel>category>
> guild>role, level + cooldown gates) → task router (BTD6/general/projmoon/video) → grounding →
> gateway, recording **exactly one** decision-audit row per message (replied/denied/skipped/errored/
> degraded). The operator surface is an admin-gated read-only diagnostics panel + `!settings → AI`
> config. Q-0048 posture: read-only deterministic tools ship freely; live model calls are env-gated
> (sandbox degrades to deterministic). **OPEN: BUG-0019 #1** (`always_reply` barges into others'
> conversations — routed to owner). This is the most env-gated unit assessed; the live model-loop walk
> is owner-paced.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — central NL stage answers/chats with per-feature grounding; task
      router classifies intent; honest decision-audit on every path; degraded (never raises) when a
      provider is down.
- [x] **Every best-in-class sub-option** — modes + per-channel/category/role policy + cooldown/level +
      tool catalog + the three read-only self-awareness tools (Q-0047).
- [ ] **Failure modes honest** — ✓ for the gateway/audit, **but** the `always_reply` mode lacks an
      "addressed to someone else?" guard → **BUG-0019 #1 OPEN** (replies to messages aimed at other
      bots/users + "you pinged me" framing). → punch #1.
- [x] **Idempotent** — `forget_channel` re-callable; policy resolver is a pure read; the mutation seam is
      the single chokepoint.

### B. Reachability & UI
- [x] **A command panel / operator UI exists** — `!ai`/`/ai` group (status/diagnostics/providers/routing/
      readiness/policy/settings/forget/why-no-response/support-report) + the persistent `aimenu` panel
      (read-only diagnostic buttons).
- [x] **Reachable every natural way** — `!ai`/`!aimenu` + `build_help_menu_view` hook + Admin-hub child;
      config via `!settings → AI`.
- [N/A] **Integrated into Setup** — AI is opt-in per guild via settings; the extras menu links it.
- [x] **Return navigation** — panel buttons re-render in place; policy preview has a back path.
- [x] **In-place, not spammy** — panel buttons edit in place; slash commands ephemeral; the NL reply is
      the product, gated by policy + cooldown.

### C. Convenience
- [x] **Defaults** — `ai_enabled`/`ai_natural_language_enabled` OFF, default provider `deterministic`
      (no key needed), min level 2, cooldown 30s — safe fresh guild.
- [x] **Presets** — numeric-preset widgets (level 0–10, cooldown 0–300, memory window 0/15/30/60/120).
- [x] **Clear feedback** — `!ai status`/`readiness`/`policy` (dry-run precedence trace)/`why-no-response`
      give operators exact, human-readable diagnostics.

### D. Authority & safety
- [x] **Authority re-checked at callback** — every command + the panel enforce `administrator`; the NL
      stage is passive (gated by policy, not authority).
- [x] **All config writes through the audited seam** — `ai_policy_mutation` is the single chokepoint
      (authority → DB → cache invalidate → typed result), emitting `audit.action_recorded`; the audit
      channel binding via `BindingMutationPipeline`.
- [N/A] **Provisioning pipeline** — no resource creation.
- [x] **Reuses governance + the Q-0048 gate** — read-only deterministic tools ship freely; live model
      calls env-gated; writes/external/UI stay per-exposure.

### E. Configuration
- [x] **Settings pipeline** — `AI_CONFIG_SCHEMA` (8 settings + audit-channel binding) auto-rendered in
      `!settings`; validators + input hints.
- [x] **config-input widgets** — provider/model text (allowed-values), toggles, numeric presets, channel
      binding; M2 adds channel/category/role policy panels.
- [x] **Everything configurable that should be** — modes, scopes, level, cooldown, memory, provider; the
      typed instruction-profile table is the M2 successor to the transitional scalar → punch #2.

### F. Wiring & discoverability
- [x] **Registry** — key `ai`, `visibility_tier: administrator`, entries `ai`/`aimenu`,
      `parent_hub: admin`, 6 capabilities (view/diagnostics/provider/routing + settings view/configure).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; commands discoverable on both surfaces.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_natural_language_stage.py` (+ `…_memory`), `test_gateway.py`
      (never-raises/degraded), `test_ai_policy_command.py`, `test_ai_why_no_response_format.py`,
      `test_ai_cog.py`, `test_ai_review_cog.py`.
- [x] **Authority tests** — admin gate on commands/panel/settings writes.
- [x] **Mutation-seam tests** — `ai_policy_mutation` upsert + cache invalidation + audit;
      `test_ai_natural_language_policy_dry_run.py`; the eval harness (`scripts/run_evals.py`, key-gated).
- [ ] **Live walkthrough (model loop) recorded** — owner-paced, env-gated → punch #3.
- [ ] **Owner ✔** — pending → punch #4.

## Punch-list (clear these to certify)
1. **BUG-0019 #1 — `always_reply` barges in** *(owner, blocking the cert)* — the open owner design fork:
   stay silent when a message pings another user/bot and not SuperBot (agent recommendation: option (a)).
   Routed to the owner; changes ambient semantics, so not patched unilaterally.
2. **M2 typed instruction profiles + channel/category/role policy UI** *(offline, deepening)* — replace
   the transitional `ai_guild_instruction_profile` scalar with the typed table + wire the policy panels.
3. **Live model-loop walkthrough** *(needs-live-bot / owner)* — `/verify-bot` boot with a provider key,
   exercise the full loop on both providers, confirm grounding + audit, with screenshots.
4. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."
5. **`always_reply` design doc** *(offline, minor)* — document when ambient mode is appropriate + its
   risk, once #1 is decided.

## Evidence
- **Tests:** `tests/unit/runtime/ai/test_natural_language_stage.py` · `…/test_gateway.py` ·
  `tests/unit/services/test_ai_natural_language_policy_dry_run.py` · `tests/unit/cogs/test_ai_cog.py` ·
  `…/test_ai_policy_command.py` · `…/test_ai_review_cog.py` · `tests/unit/invariants/test_ai_btd6_boundaries.py`
- **Walkthrough:** pending (punch #3) · **Owner sign-off:** pending (punch #4)

## Verdict
AI is an **architecturally strong, fully-audited** assistant platform — one NL stage, one policy resolver,
one audited mutation seam, honest per-message decision-audit, the Q-0048 read-only/deterministic posture,
and broad config + diagnostics, with a strong test suite + eval harness. It is **not yet `✔ certified`**,
and it carries the one **open owner-routed behavior bug** of the batch — **BUG-0019 #1** (`always_reply`
barging into others' conversations, #1) — plus the M2 deepening (#2) and the **env-gated live model-loop
walkthrough/sign-off** (#3/#4). No money/data-safety issues; the cert gate is the owner decision + the
live walk.
