# /fleet-review — the owner's general "review" word (object dispatcher)

The owner says **"review \<object\>"** and this skill reviews *whatever the object
is* — a repo, a report/doc, a prompt, a PR, a diff, or (default, no object) the
whole fleet. One word, one consistent behavior across every session.

> **Owner vocabulary:** this is the executable behind the **review** row in
> `docs/owner/fleet-vocab.md`. Revised 2026-07-11 (owner-directed, in-session):
> generalized from the fleet-night-review hardcode to object dispatch — the
> original skill answered only "review the fleet"; the owner wants "review this
> repo / this report / this prompt" to work the same way everywhere.

## Dispatch table — pick the mode from the object

| Owner says | Mode | What you do |
|---|---|---|
| "review" / "review the fleet" | **FLEET** (default) | Full fleet night/status review — §Fleet mode. |
| "review \<repo\>" (e.g. "review venture-lab") | **REPO** | Single-repo deep review — §Repo mode. |
| "review this report" / "review \<doc path\>" | **DOC** | Document review — §Doc mode. |
| "review this prompt" / a pasted prompt | **PROMPT** | Prompt critique + improved rewrite — §Prompt mode. |
| "review PR #N" / a PR URL | **PR** | Delegate to the `/review` skill (GitHub PR review). |
| "review this diff" / "review my changes" | **DIFF** | Delegate to `/code-review`. |
| Anything else (an idea, a plan, an email draft…) | **GENERIC** | §Generic mode — the four questions. |

Ambiguous object → make the best-evidence call, say which mode you picked, and
offer the alternative in one line. Never stall on the dispatch.

## Universal conventions (every mode)

- **Cite, don't assert** — every load-bearing claim links a PR / commit / file / CI run.
- **Honesty over polish** — "no report yet", "stuck on X", "this section is wrong"
  are the valuable findings; never paper over problems.
- **Verify against ground truth** (Q-0120) — a doc's claim is checked against the
  tree/GitHub before it's repeated as fact.
- **Opinionated output** — end with: what's strong · what's concerning ·
  fix-first list · owner-action queue (only genuinely owner-only items).
- **Decide-and-flag** reversible calls; route only genuine product/irreversible
  forks to the owner. Family-level model names only.
- Document durable findings in the right home (`docs/eap/` for fleet reviews, the
  target repo's `docs/` for repo reviews; a chat-only prompt/doc critique may stay
  in chat unless the owner wants it committed).

## Fleet mode (default — the original night review)

1. **Baseline** — read `menno420/fleet-manager` → `docs/roster.md` (machine-generated
   each manager wake) + `control/status.md` head + `docs/owner-queue.md`. Trust the
   roster as backbone; verify anything load-bearing against the tree (Q-0120).
2. **Bring the fleet into scope** — `add_repo` each active lane repo.
   `get_file_contents` works post-add without a full clone; status files are huge,
   so read only heads + target reports/PRs.
3. **Fan out survey agents** (grouped, e.g. build / games / ventures) — per lane:
   merged PRs + headlines since the window, *did it add a valuable report?* (check
   `docs/findings`, `docs/retro`, dated docs — name it or say "none yet"), health +
   blockers + anything stuck, and the model each session self-reports (`📊 Model:`
   line) for the model-attribution check.
4. **Routine + model audit** — from the roster's trigger table: which routine drives
   which lane, its cron, whether the repo is attached (known failure: routines spawn
   without their repo), and any configured-vs-self-reported model mismatch.
5. **Synthesize** — per-lane digest · strong/concerning · fix-first priority list ·
   lessons · owner-action queue. Document in `docs/eap/night-review-<date>.md` and
   send the organized chat version.

## Repo mode ("review <repo>")

1. **Orient** — README + `control/status.md` head + latest `docs/findings` /
   `docs/retro` docs + the fleet-manager roster row for that lane.
2. **Work review** — merged PRs over the window (default: since the last review of
   this repo, else 48h): what shipped, does the code/report match the claims,
   test/CI posture, anything merged red or force-pushed.
3. **Open surface** — open PRs (classify: safe-merge / close-stale / leave-live /
   ambiguous, with evidence), stale branches, unanswered inbox orders.
4. **Quality pass** — for code repos, run the repo's own checkers if cloned (or
   sample key files via MCP); for doc/report repos, spot-verify claims against
   ground truth.
5. **Verdict** — strong/concerning · fix-first · owner-only items · a 1–5
   "independent-review-worthiness" score (would a Codex/second-opinion pass pay
   off, and on what). Offer to generate the Codex prompt when the score is ≥4.

## Doc mode ("review this report/doc")

Read the whole document, then:
1. **Claims vs ground truth** — spot-check every load-bearing claim (PR numbers,
   dates, "X is done/merged/green") against live GitHub/tree; list mismatches first.
2. **Completeness** — what's missing that the document's own purpose requires?
3. **Actionability** — are next steps concrete, owned, and dated?
4. **Structure/clarity** — flag only where it impedes use, not style for style's sake.
Output: mismatches · gaps · a keep/fix/cut list · (if asked) the corrected text.

## Prompt mode ("review this prompt")

1. **Goal extraction** — state what the prompt is actually trying to achieve.
2. **Failure modes** — where an agent would misread, over/under-scope, or stall
   (missing context, implicit assumptions, contradictions, unbounded asks).
3. **Fit to target** — right model/tool for the job? Single-repo constraint
   respected (Codex)? Context the target can't discover included inline?
4. **Rewrite** — deliver an improved version, not just critique.

## Generic mode (anything else)

Answer four questions with evidence: What is it trying to be? Does it achieve
that? What's the highest-leverage fix? What should the owner decide (if anything)?
Then give the improved version or the fix-first list.

## Invocation

```
/fleet-review                                       # fleet mode (default)
/fleet-review venture-lab                           # repo mode
/fleet-review docs/eap/night-review-2026-07-11.md   # doc mode
/fleet-review <pasted prompt>                       # prompt mode
```

The owner saying the bare word "review …" in chat is equivalent — the vocab file
routes it here.

## Session close

A review that produced durable committed findings ends with the standard session
close (`/session-close`): born-red card, PR, merge. A chat-only critique
(prompt/doc mode with nothing committed) doesn't need a PR.
