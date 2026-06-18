# Hermes house style (owner-facing output) — the single shape for every report

> **Status:** `reference` — **the canonical output style for all owner-facing Hermes skills**
> (owner-approved 2026-06-17, Q-0168). The `_` filename prefix keeps the skill-builder
> (`scripts/hermes/build_skills.py`) from treating it as a skill — it is a *style reference* the
> output skills cite, not a skill itself. Every `hermes-skills/*.md` that produces a report the owner
> reads should follow these 5 rules and translate jargon on use.

## Why

Hermes was useful but "didn't feel like part of the system" — its output was "hard to read, filled
with stuff that is unnecessary or hard to understand," and the **message format** was the biggest
problem (owner, 2026-06-17). Root cause: **no shared house style** — each skill defined its own output
shape inline, so every report read differently and internal jargon (`needs-hermes-review`,
`dead-unresolved`, `▶ startable`) leaked straight into owner-facing messages. This doc is the shared
style so every report reads the same way and speaks plainly.

## The 5 rules

1. **Bottom line first.** Every message opens with one plain sentence: the answer / the verdict /
   "all clear." The owner gets the gist without reading further.
2. **Fixed section order, same in every report.** `Bottom line → State → What got done → Waiting on a
   human → Needs YOU → (optional) Details`. Same shape every day = no re-learning.
3. **Plain words, jargon translated on use.** Keep the few tokens the owner knows (PR #numbers,
   ✅/⚠️/❌). Translate the rest: not "needs-hermes-review carve-out" but "parked for a human to
   review and merge"; not "CI red on check_session_gate" but "the automatic checks failed / are still
   running."
4. **Group, don't list.** Related items under one labelled heading, not a flat bullet stream. Numbers
   and PRs collapse ("5 changes merged, all passed their checks") with the few that need attention
   called out.
5. **Short. One screen.** If a section needs depth, it goes under a `Details` heading at the bottom,
   so the top stays scannable on a phone.

## The reference exemplar — morning briefing

This is the owner-approved shape; every owner-facing skill mirrors its plainness and grouping
(adapting the sections to its own content).

```
☀️ Morning briefing — Tue 17 Jun

Bottom line: All clear. The bot is healthy and the overnight runs landed cleanly —
nothing needs you before you start.

🩺 State of things
   Health: good (docs + structure checks pass).
   The bot's running normally.

🛠️ What got done overnight (5 changes merged, all passed their checks)
   • Better BTD6 answers — paragon abilities + boss health comparisons
   • Server owners can now choose which moderation actions send a DM
   • Dashboard groundwork — the website can now read the bot's live command list
   (Full list on the Updates page.)

⏳ Waiting on a human (not blocking you)
   • Two new features are parked for a review-before-merge — they're bigger or
     touch security, so they wait for a second set of eyes:
       – #941 image moderation
       – #929 raid/account-age protection

👉 Needs YOU
   Nothing today. (Anything only you can decide would be listed here.)

💡 Today's idea is in the next message.
```

## How a skill uses this

In each owner-facing skill's `## Prompt`, replace the bespoke output-format block with a short line —
"COMPOSE in the house style (`_house-style.md`): bottom line first, fixed sections, plain words,
grouped, one screen" — plus a skill-specific plain-language sample of the same shape. The commands a
skill runs and its rate-limit rules **stay**; this governs only the **wording and grouping of the
output**.

After editing any skill doc, rebuild + redeploy:
`python3.10 scripts/hermes/build_skills.py` → `bash scripts/hermes/install-skills.sh`.
