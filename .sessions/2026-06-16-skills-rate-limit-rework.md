# 2026-06-16 — rate-limit rework: lean morning-briefing + idea-spotlight

> **Status:** `complete` — owner-directed skill tuning; shipped in one push, auto-merges on green.

## Arc

Owner ran the new scheduled skills on the live Hermes bot and reported (with screenshots): the
**output is clear and useful**, but **both** `morning-briefing` and `idea-spotlight` hit the model
provider's rate limit *mid-run* (~2 each). Root cause: both prompts had open-ended "read/scan more"
steps the model expanded into many tool calls (each = a model request) — the briefing fanned out on
the router scan (~5+ `search_files`) plus ran ~8 separate commands; the spotlight read the file +
skimmed relates + glanced at roadmap + router. On a rate-limited provider, ~12 calls trips the limit
before the skill finishes. Owner asked for both to be **slightly reworked**.

## Shipped (this PR)

- **`morning-briefing`** — pinned to **four single commands + compose** (sync+date · health pass/fail
  · PRs+CI+overnight in one `gh` block · one exact `grep` for owner-decisions). No open-ended scans.
- **`idea-spotlight`** — **two commands + compose** (sync+pick in one; one `cat` of the picked file).
  Leans on what `idea_spotlight.py` already extracts (summary + relates); no skimming relates /
  roadmap / router.
- **`skill-author`** (the meta-skill) — added a durable standing rule: *minimize tool round-trips;
  one combined command per step; never open-ended "scan/search for X"; lean on a backing script* — so
  future skills are built lean by default. Each reworked skill's Notes records the why + date.
- Regenerated the three `SKILL.md` artifacts.

`build_skills --check` ✓ (15 skills), `check_docs --strict` ✓, 21 build tests ✓. Docs/skills only —
no `disbot/`, no runtime, no `.py` logic changed.

## Context delta

- **Discovered (live, by the owner's dogfooding):** each Hermes tool call is a model request, so a
  scheduled skill's *call count* — not just its output — is load-bearing on a rate-limited provider.
  The fix is the same "deterministic layer owns the answer, model just formats" pattern, applied to
  *round-trips*: fixed combined commands instead of open-ended exploration.
- **Decision made alone:** kept it a prompt-only "slight rework" (fixed commands) rather than a new
  gatherer script — honoring the owner's "slightly" and the fact the spotlight is already
  script-backed. If the briefing still trips at four calls, the next step is a single
  `morning_briefing.py` gatherer (noted for follow-up).
- **Flagged for maintainer:** the underlying rate limit is also infra — if Hermes shares an API
  key/tier with the several concurrent Claude Code sessions, concurrent load makes 429s likely;
  worth confirming Hermes' model/tier and that its gateway backs off + retries on 429.

## 📤 Run report

- **Did:** reworked both scheduled skills to be lean (briefing 4 cmds, spotlight 2) so they finish
  within the provider rate limit; added a round-trip rule to skill-author · **Outcome:** shipped
- **Shipped:** this PR — lean `morning-briefing` + `idea-spotlight` + `skill-author` rule + regen
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** re-install the skills on the VPS to pick up the lean versions
  (`bash scripts/hermes/install-skills.sh`; no gateway restart needed for skills). Then re-run
  *"run the morning briefing"* / *"run the idea spotlight"* to confirm they now complete. *Optional:*
  check Hermes' model tier / 429 backoff if limits persist.
- **↪ Next:** if the briefing still trips at 4 calls, build a `morning_briefing.py` gatherer (1 call).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 4 (#959, #965, #966, #968; this one auto-merges on green) |
| CI-red rounds | 0 (docs/skills only; verified locally pre-push) |
| Repo-rule trips | 0 |
| New ideas contributed | 0 this follow-up (1 already this session — verdict loop) |
| Ideas groomed | 0 this follow-up |
