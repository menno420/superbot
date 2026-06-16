# 2026-06-16 — Hermes efficiency: idea-spotlight + briefing + dispatch-resolve + 6h auto-reset

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` as the last step.

## Intent (what this run is about to do)

Owner-requested (live, this session): make the Hermes control-plane agent more efficient with
new specialised skills + an automatic session reset.

- **`idea-spotlight`** (NEW scheduled skill, the headline) — picks **one** active idea from
  `docs/ideas/` each day and posts a structured card (summary · pros · cons/risks · options &
  expansions · suggested next step), so the owner can mull it during the day and **report back at
  EOD**; the report-back routes through the existing `intake` skill. Backed by a deterministic
  selector `scripts/hermes/idea_spotlight.py` (+ tests).
- **`morning-briefing`** (NEW scheduled skill) — one consolidated morning digest (health · open
  PRs · CI · overnight routine activity · decisions waiting on the owner · pointer to today's
  spotlight) so there's one ping instead of several; absorbs `repo-health`'s daily schedule.
- **`dispatch-resolve`** (NEW skill) + `scripts/dispatch_menu.py --json` — resolve a vague
  "work on sector SX" into a concrete work order routed by executor (the read-side of the
  captured `dispatch-resolution-json-hermes` idea; owner greenlit the Hermes-wiring half).
- **Auto session-reset every 6h** — `scripts/hermes/session_reset.sh` + a systemd-timer runbook
  (`docs/operations/hermes-session-reset.md`); owner installs on the VPS (the one unverified knob
  is the reset invocation, documented).

Supporting: `build_skills.py` EXTRAS for the 3 new skills, regenerate `SKILL.md` artifacts,
update the skill-pack README + operating prompt, mark the dispatch-resolution idea executed,
record the owner's in-session decisions in the question router.
