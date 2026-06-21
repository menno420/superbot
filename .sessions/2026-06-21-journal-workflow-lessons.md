# 2026-06-21 — Journal: capture recurring workflow lessons from the reaction-roles chain

> **Status:** `complete` — docs-only (journal, free-rein). Pushed all-at-once before opening the PR
> (journal gotcha line 62: a synchronize push may not re-fire CI). Q-0191 → merge on green.

> **Run type:** `manual`

## Arc

The reaction-roles arc is complete (6 merged PRs: #1234 multi-emote + reuse, #1237 channel + colour +
gradient, #1243 message picker, #1246 gradient presets, #1248 dead-binding cleanup, #1250 listener
self-heal). Across those sessions I kept surfacing the same workflow lessons in `Context delta` /
`⚑` lines that **evaporate into per-session cards** instead of reaching the next agent. This session
moves the durable ones into `.session-journal.md`, where the next session actually reads them:

- **`### Discord interactions / views`** (new): the **modal-must-be-first-response** constraint
  (shaped the #1243 picker flow) + the **test-fake-must-gain-new-methods** trap (the #1250
  `_Guild.get_role` break). Both flagged ★ / candidate for `.claude/rules/discord-views.md`.
- **Operating Preferences**: **merged = deployed — never tell the maintainer to deploy/restart**
  (Q-0193). The maintainer had to correct this misinformation again this session; capturing it where
  sessions re-derive it (at PR close) is the fix the doc-only Q-0193 edit didn't fully achieve.

## Findings / decisions

- **Decision made alone:** journal-only (free-rein) rather than directly editing
  `.claude/rules/discord-views.md` — that file is owner-governed; the modal rule lands as a ★ candidate
  for promotion at the next REVIEW, not a unilateral binding edit.
- **Recognized the loop honestly:** the reaction-roles feature is genuinely complete + self-healing;
  rather than manufacture more micro-features (over-engineering a finished feature), this captures the
  ecosystem lessons and hands the next substantive direction back to the owner.

## 📤 Run report

- **Did:** captured the modal-first-response + test-fake + merged=deployed lessons in the journal ·
  **Outcome:** shipped (docs-only PR, auto-merge on green)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** the modal-first-response ★ candidate is ready to promote to
  `.claude/rules/discord-views.md` at your next REVIEW (I can't self-edit that file).
- **⚑ Owner manual steps:** none — merged = deployed.
- **⚑ Self-initiated:** YES — workflow-lesson capture (first-class per CLAUDE.md), after the owner's
  reaction-roles requests were all delivered.
- **↪ Next:** reaction-roles is complete; **next substantive direction is the owner's to set** — a new
  feature area, a hardening/live-walk pass, or promote the captured candidates.

## 💡 Session idea

**Put the "merged = deployed" reminder on the session-close surface, not only in a doc.** Q-0193 fixed
CLAUDE.md, yet the misinformation persisted for months because each session re-derives "you should
deploy" at PR close. A one-line `/session-close` (or Stop-hook) check — "never tell the maintainer to
deploy/restart; merge auto-deploys" — catches the misstatement at the point it's made. (Owner-governed
hook → would be a router proposal, not a self-edit.)

## ⟲ Previous-session review

The #1250 session shipped the listener self-heal cleanly, but the broader pattern this chain exposed:
I gave the owner **repeated wrong deploy guidance** and re-discovered the **same Discord-UI / context
lessons** every session without them ever landing somewhere the next agent reads. **System
improvement (this session's action):** stop letting `Context delta` findings die in cards — promote the
recurring ones to the journal's Rules/Conventions the moment they recur, which is exactly what this
session does.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending docs PR, auto-merge on green) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (merged=deployed reminder on the close surface) |
| Ideas groomed | 0 (capture/grooming of prior-session lessons into the journal) |
