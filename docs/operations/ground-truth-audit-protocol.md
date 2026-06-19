# Ground-truth audit protocol — verify docs/claims against the code, not against themselves

> **Status:** `reference` — the durable contract for any *"make the docs correct / verify this / audit X"*
> task. Owner-directed 2026-06-19 (router **Q-0181**), after a docs-cleanup verified docs against *each
> other* (internal consistency) instead of against the *code* (ground truth) and missed shipped-but-
> `plan`-badged plans (A3/A4). **Worked template:**
> [`docs/audits/repo-wide-audit-2026-05-29.md`](../audits/repo-wide-audit-2026-05-29.md).

## When to invoke this

Any task whose correctness hinges on *"is this actually true / done?"* — *"make sure all docs are correct
and up to date"*, *"verify this was all the intended work"*, *"audit subsystem X"*. The ambiguity in those
asks is **never the goal** — it's the **evidence standard**. This protocol pins the evidence standard so
the cheap reading ("the doc says so") can't substitute for the true one ("the code says so").

## The contract (distilled from the 2026-05-29 audit's own method line)

1. **Verify against the code at a pinned commit — never against a badge, a PR title, a plan's own prose,
   or a subagent's self-report.** (The template's words: *"re-verified against `main` … not taken from PR
   titles."*)
2. **Read every file in scope, in full.** Breadth is the point. When scope is large, **fan out scoped
   auditors** (the Agent tool, one per area) and have each *read* its files — not skim, not infer from docs.
3. **Cite `file:line` evidence for every finding.** A claim with no code citation is `unverified`.
4. **Treat every status/badge as a claim to *disprove*, not a given.** For each `plan`-badged doc: does its
   named implementation exist and is it wired? If yes, the badge lies → rebadge `historical`.
5. **"Done fast" is a red flag, not a green one.** A real ground-truth pass is slow by construction; a
   quick finish means the cheap proxy got checked, not the code.

## Evidence standard (paste this into the task prompt)

> *For every 'shipped' / 'dropped' / 'correct' / 'done' claim, cite the proving artifact — `file.py:symbol`
> that exists AND is wired into a caller, or a merged PR# you actually read. A doc badge, a plan's own
> prose, a commit message, or a same-named file is NOT sufficient evidence. Where you can't find proof, say
> 'unverified' — never infer. Output a verdict table: item · claim · evidence (`file:line` / PR#) · verdict.*

The transferable rule: **when an instruction's correctness depends on a judgment, the ambiguity is in the
evidence standard, not the goal — so state what evidence proves it.**

## The automated slice (catches the recurring class with no prompt at all)

The badge-drift class is now machine-checkable:

```bash
python3.10 scripts/check_plan_code_drift.py        # advisory
python3.10 scripts/check_plan_code_drift.py --strict  # exit 1 on candidates (gate once trusted)
```

It flags every `plan`-badged doc whose named implementation already exists in `disbot/` (`STRONG` = named
file **and** a plan-specific symbol both present), turning *"read 36 plans against code"* into *"verify ~7
candidates."* It would have caught A3/A4 automatically. It is a **heuristic triage** (a plan may *extend*
existing code), not the full audit — it narrows the field; the human/auditor confirms.

## Output shape

Match the template: an executive summary + a per-finding table (`item · status ✅/⚠️/❌ · file:line · note`),
**every row re-verified against `main`.** See `docs/audits/repo-wide-audit-2026-05-29.md`.
