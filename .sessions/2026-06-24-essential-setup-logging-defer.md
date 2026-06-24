# Session — 2026-06-24 · Essential Setup logging step: defer before slow work

> **Status:** `in-progress` — fixing the live logging-step bug in the new setup wizard.

**Trigger:** Owner screen recording — the new setup wizard's logging step "is kinda broken and
just keeps building new logging channels and saying that the step failed."

## Diagnosis (root cause)

`LogChannelStep.apply` (`disbot/views/setup/essential_setup.py`) does **two channel-creation REST
calls + seven audited settings/binding writes before its only `interaction.response` call** (the
final navigation `edit_message` inside `complete()`). That work runs past Discord's **3-second
interaction-token deadline**, so the final edit 404s → the Discord client shows **"This interaction
failed"** — *after* the channels were already created. Each retry creates another `#mod-log` /
`#server-log` pair (collision-safe names → `-2`, `-3`, …). Both reported symptoms, one cause.

The other six spine steps only do a few fast DB writes, so they squeak under the deadline — which is
why only logging is broken. The codebase already has the prescribed remedy
(`core.runtime.interaction_helpers.safe_defer/safe_edit/safe_followup`, whose docstring names this
exact "Interaction Failed" symptom); Essential Setup just never adopted it.

## Fix (planned)

- `LogChannelStep.apply` — `safe_defer` up front; errors via `safe_followup`.
- `RewardActivityStep` — same latent bug (creates a role); defer its write/create paths too.
- `_StepView._show_current` → `safe_edit` (defer-tolerant nav foundation for all steps).
- Regression test: pin that the log step defers *before* creating channels.

## ⚑ Self-initiated: NO — owner-directed bug fix (the screen recording is the directive). The
RewardActivityStep hardening is the same root-cause class, fixed in the same pass per the
"fix adjacent bugs properly" working agreement.
