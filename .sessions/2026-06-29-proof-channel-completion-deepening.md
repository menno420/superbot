# Session — Proof Channel completion-deepening (audit trail + modal authority re-check)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do (born-red declaration)
Empty-fire dispatch run. S1 posture is completion-first (Q-0209); the standing offline ▶ Next is to
clear the `◐ assessed` certs' punch-lists. The **Proof Channel** completion certificate
(`docs/planning/feature-completion/units/proof_channel.md`, assessed 2026-06-29) names two real,
offline-buildable maturation gaps — unlike the other moderation units:

1. **Punch #2 — audit gap (the headline):** `_lock_for_winner` / `_unlock` call
   `proof_channel.edit(overwrites=...)` directly with **no `emit_audit_action`**, so an exclusive
   prize-access grant/revoke leaves no audit trail (every other access surface audits). → route the
   permission change alongside `services.audit_events.emit_audit_action`.
2. **Punch #1 — modal authority re-check:** the modal-submit + panel mutation callbacks re-resolve the
   channel but **don't re-check the actor holds `manage_channels`** (per the discord-views rule "opening
   a panel does not authorize later callbacks"). → re-check at every mutation callback.

Plus the missing authority + mutation-seam tests (cert rubric G).

Then, capacity permitting, a second offline slice from the assessment punch-lists.
