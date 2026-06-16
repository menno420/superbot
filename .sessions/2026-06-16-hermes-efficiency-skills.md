# 2026-06-16 — Hermes efficiency: idea-spotlight + briefing + dispatch-resolve + 6h auto-reset

> **Status:** `complete` — shipped; PR #959 auto-merges on green CI.

## Arc

Owner-requested live (this session): make the Hermes control-plane agent more efficient — new
specialised skills + an automatic chat-session reset. Researched the whole Hermes setup, then asked
two steering questions (`AskUserQuestion`); owner chose **morning-briefing + dispatch-resolve**
(alongside the core idea-spotlight) and **reset every 6h** ("never a long session; the repo updates
fast so old context isn't always valuable"). Recorded as **Q-0153**.

## Shipped (PR #959)

- **`superbot-idea-spotlight`** (NEW scheduled skill, the headline) — `30 6 * * *`. Picks one active
  `docs/ideas/` capture per day (deterministic, rotating) via the new
  `scripts/hermes/idea_spotlight.py` (status-badge filtered, `--json`/`--list`/`--date`), and Hermes
  posts a card with **pros · cons/risks · options & expansions**; the owner's EOD verdict routes back
  through `superbot-intake`. 9 unit tests.
- **`superbot-morning-briefing`** (NEW scheduled skill) — `0 6 * * *`. One consolidated digest
  (health · open PRs · CI · overnight routine activity · decisions waiting on the owner). Absorbed
  `repo-health`'s daily schedule (the "one ping not several" the owner picked); `repo-health` stays
  on-demand.
- **`superbot-dispatch-resolve`** (NEW skill) + **`scripts/dispatch_menu.py --json`** — resolves a
  vague "work on SX" into a concrete work order routed by the resolved executor. The Hermes-wiring
  half of `dispatch-resolution-json-hermes` (→ `historical`); 5 new tests.
- **6h interactive session auto-reset** — `scripts/hermes/session_reset.sh` (safe wrapper:
  logs, no-ops until configured) + the runbook `docs/operations/hermes-session-reset.md` (systemd
  timer, `OnCalendar` every 6h). The one UNVERIFIED knob (`HERMES_RESET_CMD`) is documented.
- Supporting: `build_skills.py` EXTRAS (15 skills now), regenerated `SKILL.md` artifacts, skill-pack
  README + operating-prompt skill list, skill-author "how to schedule" line, Q-0153 router block.

CI: `check_quality.py --full` green (10045 passed); `check_docs --strict`, `build_skills --check`,
`check_architecture --mode strict` all clean; arch 0 new (no `disbot/` touched).

## Context delta

- **Needed but not pointed to:** the Hermes `blueprint.schedule` self-scheduling mechanism — the
  single most relevant fact for this task — was only discoverable by reading `build_skills.py`'s
  `EXTRAS`. Nothing in `skill-author.md` / the skill-pack README said "to schedule a skill, add
  `schedule=`". *Fixed this session* (added the line to `skill-author.md` + the README schedule note).
  Hermes hosting facts were spread across control-plane / cheatsheet / operating-prompt /
  token-efficiency docs; had to assemble them.
- **Pointed to but didn't need:** the giant `current-state.md` ▶ callout is bot-product-centric and
  added little for a Hermes-tooling task (minor).
- **Discovered by hand:** cron skills run **stateless** (`skip_memory=True`) — key to answering the
  auto-reset question (scheduled skills don't need resetting; only the interactive chat does). Also:
  an importlib-loaded script using `@dataclass` must be registered in `sys.modules` before
  `exec_module` (only implicit in `test_build_skills.py`).
- **Decisions made alone (all reversible; in Q-0153):** removed `repo-health`'s daily schedule
  (consolidated into the briefing); date-`%`-len rotation for idea selection; briefing 06:00 /
  spotlight 06:30 UTC; shipped auto-reset as a parameterized wrapper + runbook (owner confirms the
  reset command on the VPS).
- **Flagged for maintainer / known limits:** the auto-reset's `HERMES_RESET_CMD` is **unverified**
  (can't be from the repo — confirm on the VPS). All 3 new skills are UNVERIFIED until they've run a
  few times (Q-0105 headers). The idea-spotlight pick shifts when the active-idea count changes
  (inherent to the simple rotation; acceptable).

## 💡 Session idea (Q-0089)

`docs/ideas/idea-spotlight-verdict-loop-2026-06-16.md` — the spotlight asks for a verdict but the
selector has no memory of what's already decided, and nothing measures backlog drain. Give it a tiny
**verdict ledger** (persist each `intake` route), bias selection toward un-decided ideas, and add a
weekly drain-rate line to the briefing — a self-draining decision queue. Genuinely believe in it: it
closes the loop this very PR opened.

## ⟲ Previous-session review (Q-0102)

Previous run (`2026-06-16-act-on-autonomous-run-review`, PR #956 / Q-0152): **did well** to batch the
autonomous-run review's loop-closing changes and, notably, to *correct propagating misinformation*
(the "merge needs a manual Railway deploy" myth) at the root rather than just patching one mention —
good systemic hygiene. **System improvement it surfaces:** it made the `📤 Run report` footer
*required* in session logs but there's no checker that a log actually contains it (the way
`check_session_gate` checks the card status but not the footer). Extending `check_session_log.py` to
assert the footer + its two `⚑` lines would make the convention self-enforcing — worth a future
slice (not built here; out of scope).

## 🔎 Doc audit (Q-0104)

`check_docs --strict` green (all new docs reachable + badged). The SessionStart "12 merged PRs not in
current-state" is **benign newest-merge lag**, not drift (the reconciliation routine owns the ledger;
Q-0124 — a manual session doesn't reconcile). Owner decisions recorded in the router (Q-0153); the
dispatch-resolution idea re-badged `historical` with its README entry updated.

## 📤 Run report

- **Did:** shipped 3 new Hermes skills (idea-spotlight · morning-briefing · dispatch-resolve) + a 6h
  interactive-session auto-reset runbook · **Outcome:** shipped (PR #959, auto-merges on green)
- **Shipped:** #959 — Hermes efficiency skills + `dispatch_menu --json` + session-reset wrapper/runbook
- **⚑ Owner decisions needed:** `none` (the choices were made live via AskUserQuestion → Q-0153)
- **⚑ Owner manual steps:** VPS, off-repo — (1) re-install: `install-skills.sh` → `install-soul.sh`
  → `systemctl restart hermes-gateway` (picks up the 3 new skills + the updated operating prompt);
  (2) wire the 6h reset per `docs/operations/hermes-session-reset.md` (set `HERMES_RESET_CMD` for
  your Hermes build + enable the timer). Both detailed in Q-0153.
- **↪ Next:** when the daily spotlight cards are confirmed landing, build the **idea-spotlight
  verdict loop** (`docs/ideas/idea-spotlight-verdict-loop-2026-06-16.md`).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (this session's #959 auto-merges on green) |
| CI-red rounds | 0 real (1 intentional born-red gate hold; 1 local ruff/black auto-fix before push) |
| Repo-rule trips | 0 (no new arch violations; no `disbot/` touched) |
| New ideas contributed | 1 (idea-spotlight verdict loop) |
| Ideas groomed | 1 (dispatch-resolution-json-hermes → `historical`, executed) |
