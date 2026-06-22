# Skill: `superbot-morning-briefing`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Self-schedules one daily digest.
> Update it when the health checks, the routine fleet, or the decision homes change. Provenance:
> owner-directed 2026-06-16 ("one message instead of several pings").

**Window:** once each morning (self-scheduled)
**Purpose:** One consolidated start-of-day digest — repo health, open PRs, recent CI, what the
autonomous routines did overnight, and any decisions waiting on the owner — so the day starts from
a single message instead of several separate pings.

**When to use:** it self-fires each morning via its `blueprint.schedule`. Invoke by hand any time
the owner asks "where are we?" / "what happened overnight?". This is a **thin composite**: it
chains the cheap checks the atoms already define (`repo-health`, `open-questions`) into one rollup —
it does not replace them as on-demand tools.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Read-only. Produce ONE morning briefing, under 400 words. Use ✅/⚠️/❌ on the health line.

IMPORTANT — the model provider rate-limits, so keep this to FOUR commands. Run each block below as
a SINGLE shell command exactly as written; do NOT fan out into extra searches or file reads. Then
compose from their output — no further commands.

A) SYNC + DATE:
   cd /home/hermes/repos/superbot && git fetch -q origin main && git checkout -q -B main origin/main && date '+%Y-%m-%d'

B) HEALTH (pass/fail only — known arch warnings are fine):
   (python3 scripts/check_docs.py --strict >/dev/null 2>&1 && echo "docs: ok" || echo "docs: FAIL"); (python3 scripts/check_architecture.py --mode strict >/dev/null 2>&1 && echo "arch: ok" || echo "arch: errors")

C) PRS + CI + OVERNIGHT (one block):
   echo "== open PRs =="; gh pr list --repo menno420/superbot --state open --json number,headRefName,labels --jq '.[]|"#\(.number) \(.headRefName) [\(.labels|map(.name)|join(","))]"'; echo "== recent CI =="; gh run list --repo menno420/superbot --limit 6 --json conclusion,headBranch --jq '.[]|"\(.conclusion // "running") \(.headBranch)"'; echo "== merged ~24h =="; gh pr list --repo menno420/superbot --state merged --limit 8 --json number,title --jq '.[]|"#\(.number) \(.title)"'

D) DECISIONS WAITING ON THE OWNER (one grep — do not scan further):
   grep -niE "awaiting (maintainer|owner)|status:\s*open|owner-gated|needs (owner|maintainer)" docs/owner/maintainer-question-router.md | head -15

COMPOSE in the HOUSE STYLE (docs/operations/hermes-skills/_house-style.md — 5 rules: bottom-line
first · fixed section order · plain words, translate jargon · group don't list · short, one screen).
Translate internal jargon for the owner: "do-not-automerge" -> "held back on purpose, not merging
yet"; a red check -> "the automatic checks failed / are still running"; a "claude/* PR" -> just the
change + its #number. Collapse the numbers ("5 changes merged, all passed their checks") and call out
only the few that need attention.

DELIVER in this shape (plain language, scannable on a phone):

---
☀️ Morning briefing — [Day DD Mon]

Bottom line: [one plain sentence — "All clear, nothing needs you before you start" OR the one thing
that does].

🩺 State of things
   Health: [good / the problem in plain words] (docs + structure checks [pass/fail]).
   [The bot's running normally / the one health issue.]

🛠️ What got done overnight ([N] changes merged, [all passed their checks / N need attention])
   • [each merged change in plain language — what it MEANS for the bot, not the raw PR title]
   (Full list on the Updates page.)
   [or, if nothing merged: "Quiet overnight — no changes landed."]

⏳ Waiting on a human (not blocking you)
   • [each parked-for-review PR in plain words + its #number — omit this whole section if none]

👉 Needs YOU
   [the few decisions only the owner can make, in plain words — or "Nothing today."]

💡 Today's idea is in the next message (superbot-idea-spotlight).
---

RULES:
- Four commands, then compose — minimize round-trips (the provider rate-limits).
- Bottom line first: the owner gets the gist from the first sentence without reading on.
- Plain words: translate every internal token; keep only #numbers and ✅/⚠️/❌.
- Verify, don't assume — every line comes from the output above; say "gh unavailable" + ⚠️ if so.
- Short: one screen on a phone. Any depth goes under a "Details" line at the very bottom.
- No actions (no merges, no dispatch) — the briefing is a hint; a dedicated skill acts.
```

---

## Notes

- **Replaces the separate health ping.** `repo-health` previously self-scheduled its own daily
  digest; the briefing now carries the daily health line, so `repo-health`'s `blueprint.schedule`
  was removed (it stays a full on-demand traffic-light). This is the "one message instead of
  several" the owner asked for — re-add `repo-health`'s schedule in `build_skills.py` if you ever
  want both.
- **Thin composite (skill-author rule).** It encodes the *decision flow* and runs the cheap checks
  inline; it references `repo-health` (full health) and `open-questions` (decision scan) rather than
  duplicating their bodies. If it grows a heavy section, split that section back into its atom.
- **Lean by design (rate-limit, 2026-06-16).** Hermes' model provider rate-limits and each tool call
  is a request; the first version fanned out (~12 calls — many `search_files` for the router scan)
  and tripped the limit mid-run. It's now pinned to **four single commands + compose**. Keep it that
  way — don't re-add open-ended "scan/search" steps or split the combined commands back apart.
- **Self-schedules.** `blueprint.schedule` (`0 6 * * *`) is set in
  `scripts/hermes/build_skills.py`; the idea spotlight follows 30 min later. Change the times there.
- **Provenance + reliability (Q-0105).** Added 2026-06-16, owner-directed. UNVERIFIED until a few
  briefings have been seen to read accurately against live state. Delete or revise if it drifts.
