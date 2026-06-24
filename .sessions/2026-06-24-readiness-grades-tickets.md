# 2026-06-24 — Setup readiness scan grades tickets

> **Status:** `complete` — the setup readiness scan now grades tickets. Full CI mirror green (12393 passed
> after regenerating env-vars.md); arch 0 errors.

> **Run type:** `manual` — self-initiated follow-up flagged in the previous session (see ⚑ below).

**Branch:** `claude/readiness-grades-tickets` (off `main`). Third follow-up in the tickets thread
(#1405 subsystem, #1410 AI confirm, #1417 setup-wizard discoverability).

## What this session is doing

The setup readiness scan (`build_setup_readiness_embed`) grades each subsystem from its declared
config schema, but **tickets register no subsystem schema** — their config lives in a dedicated table
(`services.ticket_service`) — so tickets were absent from the scan entirely. This adds a dedicated
**🎫 Support Tickets** readiness line that reads `ticket_service.get_config` directly: 🟢 enabled (with
log on/off + max-open) or 🔴 not set up (pointing at the `!setup` step / `!ticketsetup`). It both grades
tickets and acts as another discovery nudge. Best-effort: a read failure is logged and the line omitted —
the readiness embed never fails on this add-on.

- `disbot/services/diagnostic_embeds.py`: module `logger` + `_render_ticket_readiness` helper, called
  from `build_setup_readiness_embed`.
- `tests/unit/services/test_setup_readiness.py`: not-set-up line, enabled grade, and omit-on-read-failure.

## ⚑ Flagged for maintainer / known limits

- **Self-initiated.** This was the "readiness scan grades tickets" idea I flagged at the end of the
  #1417 session, not a directly-requested task. The owner had been replying "continue" on the tickets
  thread; I judged this contained, reversible, on-theme follow-up worth building under the standing
  autonomy guidance (Q-0129/Q-0172) rather than asking a fourth time. Easy to revert if unwanted.
- **Not live-verified** (no Discord boot): confirm the 🎫 line shows in `!setup` → Run Readiness Scan /
  `!platform readiness`, both for a configured and an unconfigured guild.
- **Bespoke by necessity:** ticket config isn't a registered subsystem schema, so it can't ride the
  score-driven per-subsystem table — hence a dedicated line. If tickets ever gain a real schema, fold
  this into the generic path and delete the helper.

## 🛠 Friction → guard (worked as intended)

`scripts/scan_env_usage.py` generates `docs/operations/env-vars.md` with **line-number** references, so any
edit that shifts lines in a file containing an env-var usage reddens `test_scan_env_usage`. The guard caught
my edit immediately; fix is `python3.10 scripts/scan_env_usage.py --write-doc`. Worth knowing: editing
`diagnostic_embeds.py` (and similar env-var-touching files) means regenerating that doc in the same commit.

## 💡 Session idea

**Make every discovery surface ticket-aware in one place.** Tickets now appear in help, the wizard, the
launcher, and readiness — but each was wired separately. A tiny `services.feature_status` helper returning
`(name, configured: bool, nudge: str)` per optional subsystem would let all four surfaces render the same
status from one source, so the next optional subsystem is discoverable everywhere by adding one entry.
Captured for grooming; don't build speculatively.

## ⟲ Previous-session review

The #1417 session ended by *naming* this follow-up but leaving it unbuilt — correct at the time (it wasn't
asked for). What it could have done better: it didn't note that ticket config being schema-less means the
readiness integration is necessarily bespoke, which I had to rediscover here. **System improvement:** when a
session flags a follow-up idea, a one-line "implementation note / gotcha" on the idea would save the next
session the re-discovery — worth adding to the session-idea convention (Q-0089). Low-stakes; mention if it
recurs rather than a router block now.

## 📤 Run report

- **Did:** added a Support-Tickets line to the setup readiness scan · **Outcome:** shipped
- **Shipped:** #pending — readiness now grades tickets (enabled / not set up) + nudges setup
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none — revert if the self-initiated scope wasn't wanted
- **⚑ Owner manual steps:** spot-check the 🎫 line in the readiness scan live
- **⚑ Self-initiated:** YES — built the previous session's flagged idea unprompted (see ⚑ above)
- **↪ Next:** live-verify; optionally the `feature_status` consolidation idea
