# Settings presets everywhere + AI template advisor — idea capture (2026-06-10)

> **Status:** `ideas` — the *posture* in §1 is an **answered owner decision**
> (router **Q-0070**, verbatim there); the AI template-advisor in §2 is
> **captured only, not approved** for implementation. Route §2 through
> [`README.md`](./README.md)'s lifecycle before building anything.
> Source: maintainer in chat, 2026-06-10, reacting to four live free-text
> editor modals (`moderation.warn_timeout_minutes`, `ai.ai_default_model`,
> `moderation.dm_template`, `ai.ai_guild_instruction_profile`).

## 1. The decided posture (Q-0070 — decision, not an idea)

Wherever feasible, every setting editor offers, in this order:

1. **Clear defined presets** (curated, named options) as the primary path;
2. **preset-then-edit** — pick a preset, then customize from it;
3. **completely manual entry** — always available as the final fallback.

**Implementation home:** settings audit
[§11 Phase 4](../planning/settings-cog-centralization-audit-2026-06-09.md)
("structured editors / less text") + its §7 conversion table. The posture
*upgrades* §7's "keep as plain text" rows — `moderation.dm_template` and the
AI instruction body should gain curated starting templates + edit-from-preset,
not stay blank boxes — while §7's existing numeric/enum/pointer conversions
(e.g. `warn_timeout_minutes` → numeric presets) proceed as already planned.

Supporting polish observations from the same live walk (fold into Phase 4):

- Empty-value text modals render their placeholder as the confusing
  `current=" · default="` string — the current/default preview needs an
  empty-state form.
- Editor modal titles show raw qualified keys
  (`Edit ai.ai_guild_instruction_profile`) instead of a human-readable setting
  name with the stable key alongside (the Q-0058 admin-display pattern).

## 2. The idea (NOT approved): AI template/preset advisor

The maintainer's framing: hardcode **multiple prompt designs/styles as modular
settings for the AI cog**, so the AI can **suggest the right kind of
templates/presets for every task** — a "custom AI design" option offered
alongside the fixed presets.

Shape sketch (capture only, to make later promotion concrete):

- A curated, versioned **catalogue of prompt/template designs** (modular
  building blocks) owned like other AI config — typed storage in the
  instruction-profile direction Q-0063 already set (converge-gradually), never
  free-typed blobs.
- An **advisor surface** that recommends a preset for the task/setting at hand
  — read-only suggestion first; applying a choice still flows through the
  normal audited settings/AI mutation seams.
- Always composes with the §1 posture: *suggest → preset → edit-from-preset →
  manual* — the advisor adds a recommendation layer, it never removes the
  manual path.

**Gates before promotion:** the AI per-exposure UI gate (Q-0048's standing
lift covers read-only deterministic tools only — an advisor UI needs its own
lift); Q-0063's typed-profile convergence (instruction bodies should be typed
before an advisor writes them); and settings-audit Phase 4 shipping the preset
infrastructure this advisor would ride on.

## 3. Lifecycle state

`captured` (this file; owner words preserved verbatim in router Q-0070).
Next state: a Phase-4-rider plan once Phase 4 is queued — or a router
discussion first if the advisor's scope needs narrowing.
