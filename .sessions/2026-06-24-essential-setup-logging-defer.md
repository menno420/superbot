# Session — 2026-06-24 · Essential Setup logging step: defer before slow work

> **Status:** `complete` — root-cause fix for the live logging-step bug in the new setup wizard.
> CI mirror green (12495 passed); arch 0 new; PR #1439.

**Trigger:** Owner screen recording — the new setup wizard's logging step "is kinda broken and
just keeps building new logging channels and saying that the step failed."

## Diagnosis (root cause)

`LogChannelStep.apply` (`disbot/views/setup/essential_setup.py`) does **two channel-creation REST
calls + seven audited settings/binding writes before its only `interaction.response` call** (the
final navigation `edit_message` inside `complete()`). That work runs past Discord's **3-second
interaction-token deadline**, so the final edit 404s → the Discord client shows **"This interaction
failed"** — *after* the channels were already created. Each retry creates another `#mod-log` /
`#server-log` pair (collision-safe names → `-2`, `-3`, …). **Two symptoms, one cause.**

The other six spine steps only do a few fast DB writes, so they squeak under the deadline — which is
why only logging is broken. The codebase already ships the prescribed remedy
(`core.runtime.interaction_helpers.safe_defer/safe_edit/safe_followup`, whose docstring literally
names this "Interaction Failed" symptom, CRIT-2); Essential Setup just never adopted it, while the
other slow setup views (`wizard.py`, `final_review.py`) all do.

## What changed (`disbot/views/setup/essential_setup.py` + its test)

- **`LogChannelStep.apply`** — `safe_defer` up front (ACK within 3 s); the two error paths
  (`_create_channel`, the apply `except`) route through `safe_followup`.
- **`RewardActivityStep`** — same latent bug (it creates a role): `apply` and the no-rewards
  `on_next` branch defer; its three error paths + the phase-swap nav route through the safe helpers.
- **`_StepView._show_current`** → `safe_edit`, so navigation edits the wizard message in place
  whether or not the step deferred (a defer-tolerant foundation every step inherits).
- **Tests** — the interaction double is now defer-stateful (`is_done()` flips after ack); 3 asserts
  updated to the followup route; **new regression test** `test_log_channel_defers_before_slow_work`
  pins that the step defers *before* any channel is created. 39/39 in the file; 698 across the setup
  surface; full `check_quality --full` green.

No copy/schema changes — the setting/binding names were already valid; the only defect was the
missing acknowledgement.

## 💡 Session idea (Q-0089)

**A static guard for "I/O before defer" in interaction callbacks.** This whole bug is the CRIT-2
class `interaction_helpers.py` was built for ("Adoption across cogs lands in F5") — but nothing
*enforces* adoption, so a brand-new flow shipped without it and reached production. A disposable
Q-0105 AST checker (sibling of `check_setup_copy.py`) could flag any `async def callback`/`apply`
that `await`s a known-slow seam (`create_channels`, `set_value`, `set_binding`, `RoleLifecycleService`,
`ChannelLifecycleService`, `*MutationPipeline`) **before** any `safe_defer` / `response.defer` /
`response.send_message`. Warn-first, scoped to `views/` + `cogs/`. That converts "remember to defer"
from tribal knowledge into a ratchet — and would have caught this PR's bug at author time.
(Dedup-checked `docs/ideas/`: no existing defer/interaction-deadline-lint idea — grep empty.)

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: the **setup-copy jargon guard** (PR #1420). Did well: built the
Q-A-independent slice and *measured* the real jargon baseline (207 vs the modelled 44) — exactly the
"leave the next session better-equipped" discipline. What the *arc* missed: the Essential Setup spine
was **cut over to the primary `!setup` / `/setup` the same day (#1435 + 63b83e2)**, and we guarded its
*copy* (the jargon ratchet) but had no guard — and apparently no live interaction-latency walk — for
the *3-second-deadline behavioural class* that actually broke in front of the owner. **System
improvement (this session acts on it via the Q-0089 idea):** when a new interactive flow is promoted
to *primary*, a "slow-callback defer audit" (lint or a one-time live walk) should be part of the
cutover checklist, not discovered by a screen recording. We had a copy ratchet on the spine; the
missing peer is a *deferral* ratchet.

## 📋 Doc audit (Q-0104)

`check_current_state_ledger.py --strict` green (in sync); `check_docs --strict` + `check_consistency`
green. No owner *decision* was made (owner-directed bug fix, no new Q). No `current-state.md` ledger
entry needed yet — the ledger checker keys off **merged** PRs, so the next reconciliation pass picks
up #1439 (same convention the jargon-guard session used for #1420). Claim file deleted at close.

## Context delta

- **Surprise:** the fix the codebase *already had* (`interaction_helpers`) was simply never wired
  into the new wizard — the bug wasn't a missing capability, it was un-adopted infrastructure. That
  is the strongest argument for the Q-0089 *enforcement* idea: the remedy exists; only adoption was
  optional.
- **For next session:** if the owner wants belt-and-suspenders, the remaining fast spine steps
  (ServerType has 9 writes) could also defer — they're proven under-deadline today but would be
  immune to future write-count growth. Low priority; not done here to keep the fix surgical.

## ⚑ Self-initiated: NO — owner-directed bug fix (the screen recording is the directive). The
RewardActivityStep hardening + the `_show_current` foundation are the same root-cause class, fixed in
the same pass per the "fix adjacent bugs properly / approving the goal approves the path" working
agreement. The Q-0089 defer-lint is captured as an *idea*, not built.
