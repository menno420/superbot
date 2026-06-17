# PROPOSAL — Hermes plain-language house style (owner review)

> **Status:** `ideas` — **NOT wired, NOT source of truth.** A sample for the owner to react to
> (Q-0168, 2026-06-17). The `_` filename prefix marks it a draft the skill-builder skips
> (`scripts/hermes/build_skills.py`), not a skill. If the owner approves the direction, a follow-up
> session applies this style to every `hermes-skills/*.md` output block + rebuilds — then this file
> is deleted.

## The problem (owner, 2026-06-17)

Hermes is useful but "doesn't feel like part of the system yet." Its output is "hard to read,
filled with stuff that is unnecessary or hard to understand." **The biggest single problem is the
message format** — it should be "better grouped and more easily readable," report "in plain
language" (some jargon is fine "as long as I can understand most of it").

Root cause (from the skills audit): **there is no shared house style.** Each skill defines its own
output shape inline in its prompt — bullets+emoji (morning-briefing), a traffic-light table
(repo-health), prose headers (idea-spotlight), a findings table + gates (review). So every report
reads differently and the owner context-switches between styles, and jargon (`needs-hermes-review`,
`dead-unresolved`, `▶ startable`) leaks straight from internal docs into owner-facing messages.

## The proposed house style (5 rules)

1. **Bottom line first.** Every Hermes message opens with one plain sentence: the answer / the
   verdict / "all clear." The owner should get the gist without reading further.
2. **Fixed section order, same in every report.** `Bottom line → What's the state → What got done →
   What needs YOU → (optional) details`. Same shape every day = no re-learning.
3. **Plain words, jargon translated on use.** Keep the few tokens the owner knows (PR #numbers,
   ✅/⚠️/❌). Translate the rest: not "needs-hermes-review carve-out" but "parked for a human to
   review and merge"; not "CI red on check_session_gate" but "the automatic checks are still
   running / failed."
4. **Group, don't list.** Related items under one labelled heading, not a flat bullet stream.
   Numbers and PRs collapse ("5 PRs merged, all green") with the few that need attention called out.
5. **Short. One screen.** If a section needs depth, it goes under a `Details` heading at the bottom,
   so the top stays scannable on a phone.

## Sample — morning briefing, before → after

**BEFORE (current format):**

```
## ☀️ SuperBot morning briefing — 2026-06-17
- **Health:** ✅ docs + arch ok
- **Open PRs:** 3 — #941 needs-hermes-review, #929 needs-hermes-review, #1026 claude/*
- **CI:** 5/6 recent runs passed; 1 failure on claude/quirky-bardeen-70d0cb
- **Overnight:** #1024, #1023, #1020, #1019, #1018 merged
- **⚑ Waiting on you:** nothing
- **💡 Idea of the day** is posted separately.
### Verdict
Today is clear to work in.
```

**AFTER (proposed plain-language house style):**

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

## What changes in the rollout (if approved)

- Add a short **"House style"** block to each `hermes-skills/*.md` output spec referencing these 5
  rules instead of re-describing a bespoke shape, and rewrite each sample into plain language.
- The structural shells (the four-command budget in morning-briefing, the rate-limit rules) stay —
  this changes the **wording and grouping of the output**, not the commands Hermes runs.
- Rebuild + redeploy: `python3.10 scripts/hermes/build_skills.py` → `bash scripts/hermes/install-skills.sh`.

**Owner: react to the AFTER sample above.** Too terse? Want the health line kept compact? Want PR
titles even plainer? Your edits to this one sample set the style for all of Hermes.
