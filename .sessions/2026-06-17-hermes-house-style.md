# 2026-06-17 — Hermes plain-language house style — rollout (Q-0168)

> **Status:** `in-progress`
> Manual, owner-greenlit ("about hermes, that should ideally be done pretty soon, this session is
> good for that"). Docs + generated-skill artifacts only. Born-red per Q-0133; flip to `complete`
> when CI is green.

**Branch:** `claude/hermes-house-style`

## Goal

Roll out the owner-approved plain-language **house style** (Q-0168) to Hermes' owner-facing output
skills, so every report reads the same plain, grouped, bottom-line-first shape instead of each skill's
bespoke, jargon-heavy format. The owner approved the morning-briefing before→after sample 2026-06-17
("much cleaner and easy to read with clear sections").

## What was done

- **Promoted** the approved sample `_house-style-proposal.md` → canonical **`_house-style.md`** (the 5
  rules + the owner-approved morning-briefing exemplar + "how a skill uses this"). Still `_`-prefixed
  so `build_skills.py` skips it (it's a style reference, not a skill).
- **Rewrote the owner-facing output skills** to the house style (bottom-line first · fixed sections ·
  plain words / jargon translated · group-don't-list · one screen):
  - `morning-briefing` — full conversion to the AFTER shape the owner approved.
  - `repo-health` — 6-dimension status table → 4 plain grouped lines + a bottom line.
  - `open-questions` — 4 dense Q#-tables → plain grouped bullets + a bottom line.
  - `idea-spotlight` — card → plain, bottom-line-first card.
  - `review-merge` — STEP 4 report + the ADVISORY-mode ping rewritten plain.
- **Rebuilt** the generated `SKILL.md` artifacts (`build_skills.py`); `--check` green (15 up to date).
- Updated router **Q-0168 → rolled out**; fixed the `_house-style-proposal` links + the build_skills
  comment.

The COMMANDS each skill runs + the rate-limit budgets are **unchanged** — this changes only the
wording and grouping of the output (per the proposal's own rollout note).

## Left open / next session

- The remaining skills (`session-brief`, `log-triage`, `btd6-status`, `intake`, `ideas-triage`,
  `dispatch-resolve`, `prompt-builder`) can get the house-style reference in a quick follow-up — the
  recurring daily owner-facing reports were prioritized first.
- **Owner manual step:** redeploy on the VPS (`bash scripts/hermes/install-skills.sh` → restart) to
  pick up the new prompts.

## 💡 Session idea

**Idea:** `check_house_style.py` — a warn-only lint over `hermes-skills/*.md` that flags an
owner-facing skill's `## Prompt` still emitting raw internal jargon (`needs-hermes-review`,
`dead-unresolved`, `▶ startable`, `check_*`) in its DELIVER block without a plain-language
translation, and that opens with a "Bottom line". **Why:** the house style is now a written rule but
nothing enforces it; a cheap stdlib guard keeps a future skill edit from quietly drifting back to
jargon. Disposable (Q-0105).

## ⟲ Previous-session review

The previous run (the Q-0172 governance change, this same conversation) correctly **grepped every
surface** before declaring the phase gate advisory — it caught 6 doc copies that would otherwise have
contradicted the new rule. **System improvement it surfaces:** retiring/changing a CLAUDE.md rule has
no single "here are all its mentions" index, so completeness depends on remembering to grep. A small
**"rule-change checklist"** (grep the Q-number + the rule's key phrases across `docs/` + `scripts/`
before flipping a rule's state) would make rule changes reliably complete — worth a line in the
collaboration model if it recurs.

## 📤 Run report

- **Did:** rolled out the approved plain-language house style to Hermes' owner-facing output skills (Q-0168) · **Outcome:** shipped
- **Shipped:** (this PR) — Hermes house-style rollout: canonical `_house-style.md` + 5 skills rewritten + rebuilt
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** redeploy Hermes on the VPS (`bash scripts/hermes/install-skills.sh` → restart) to pick up the new prompts
- **⚑ Self-initiated:** `none` (owner-greenlit this session) (Q-0172)
- **↪ Next:** house-style the remaining non-daily skills (quick follow-up); then build the fishing plan under the new Q-0172 gate

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1029 earlier; this is the 2nd) |
| CI-red rounds | TBD (filled at flip-to-complete) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`check_house_style.py`) |
| Ideas groomed | 0 (this run is execution, not grooming) |
