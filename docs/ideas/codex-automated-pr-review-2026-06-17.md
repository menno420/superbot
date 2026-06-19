# Codex automated PR review — a second independent reviewer on every PR

> **Status:** `ideas` — **NOW LIVE (owner enabled it 2026-06-17).** Decision provenance: **Q-0171**.
> The owner turned on the Codex GitHub connector the same day; it is already auto-reacting on PRs
> (validated on **#1026** — `chatgpt-codex-connector[bot]` left a 👍 on the PR body). The research
> question is no longer "does this exist" but "how do we make its output *actionable* in the loop"
> (see the LIVE update below). Source + binding contracts win.

## ✅ LIVE update (2026-06-17)

Codex is **enabled and working** on `menno420/superbot`. What we observed + what it means for us:

- **On #1026 it left a 👍 reaction, no review body.** That is an "LGTM, no objections" signal. A bare
  *reaction* lives on a separate GitHub API surface — `get_reviews` / `get_comments` return empty for
  it, so an agent **cannot read the thumbs-up itself**. Nothing to act on when Codex only reacts.
- **A substantive Codex *review* or *review comment* IS fully readable** by an agent (`get_reviews`,
  `get_review_comments`, `get_comments`) — and, crucially, the **PR-activity subscription**
  (`subscribe_pr_activity`) **delivers Codex's review comments into a watching session as events**, so
  a watching agent can read and act on them automatically. That is the "catch errors" win: when Codex
  *finds* something, the loop already has a channel to consume and fix it.
- **To make it maximally useful:** check the Codex connector settings for a mode that **posts a review
  summary comment every time** (not just a reaction). If it only reacts when it has no objection, its
  reasoning is invisible; a per-PR review comment makes every verdict readable by the loop.

### What Codex actually caught (2026-06-17, verified) + the born-red friction

Codex moved past reactions and **left real inline review comments** (P1/P2 severity badges + a "React
👍/👎" footer); an agent reads them directly via `get_review_comments` / `get_reviews`. Two findings:

- **It catches genuine issues on docs/plan PRs.** On #1028 (the procedures-to-skills plan) it raised 4
  still-open P2 points — two **verified correct** and fixed this session: the `/session-close` skill
  still said "10th-PR / ~9 PRs" (stale vs. the 30-PR/full-band cadence, Q-0134/Q-0164) and the plan
  wasn't homed on `docs/roadmap.md` (so routines wouldn't discover it). Good signal — Codex is earning
  its keep on documentation/plan review.
- **⚠️ The born-red flow defeats most of its *code* reviews.** Codex reviews **on PR open**, which in our
  born-red workflow (Q-0133) is the **card-first commit — *before* the implementation lands.** So on
  #1023/#1024/#1027 it flagged "the implementation isn't here / flip the card / the script doesn't
  exist" — all `is_outdated` false-positives from reviewing the incomplete opening commit. **The fix to
  decide with the owner** (it touches the Codex settings he configured): to get a useful Codex pass,
  trigger it on the **final head** — comment `@codex review` after the code + card-flip, before merge —
  rather than relying on the open-time auto-review. Until then, weight Codex's docs/plan catches highly
  and treat its "missing implementation" comments on born-red code PRs as timing artifacts.

### ✅ BUILT (2026-06-19, Q-0180) — the final-head review is now automated

The "trigger on the final head" fix above is shipped: **`.github/workflows/codex-final-review.yml`**
posts `@codex review` the instant a `claude/*` PR's **session card flips to a ready status** (the
born-red final-commit signal, detected via `scripts/check_session_gate.py --require-ready-card`). Codex
now reviews the **complete diff**, not the incomplete opener. Verified empirically first: on **#1097**
Codex reviewed only the opening commit and left a P1 born-red false positive ("mark the card ready"),
never re-reviewing the final head — confirming a plain push is not a Codex trigger. The PR usually
auto-merges before Codex finishes, so the review lands on the **merged** PR; that is accepted — routines
scan recently-merged PRs for Codex comments and fix the real ones first (Q-0174). UNVERIFIED per Q-0105
— watch the first PRs; delete the workflow if it misfires. Full rationale: router **Q-0180**.

## The idea

Wire **Codex (OpenAI) to automatically review pull requests** as they open/update, posting review
comments. This adds a **second, different-model reviewer** to the loop — directly serving the
project's standing **anti-monoculture** principle (the reason `needs-hermes-review` puts a *different
model* than the author between big steps and `main`).

## How it likely works (verify before building)

The owner saw it in ChatGPT; the most likely concrete mechanisms (to confirm via research — the
`claude-code-guide` / web is the right tool, and `context7` for current docs):

- **OpenAI Codex "code review" on connected GitHub repos** — the Codex cloud agent can be pointed at
  a repo and asked to review PRs; some setups post inline review comments automatically on PR open.
- **A GitHub Action / app** that calls the OpenAI API on `pull_request` events and posts a review.
- **The `@codex` PR mention** flow, where tagging the bot triggers a review.

Each differs in setup (an OpenAI auth/token, repo connection, an Action) and in cost model — that's
the research step.

## Where it fits (and the open question)

- **Complements vs. overlaps Hermes review-merge (Q-0117).** Today Hermes (gpt-5.4-mini) is the
  independent reviewer + merge gate for `needs-hermes-review` PRs. Codex review could either:
  - *Augment* — Codex auto-comments on **every** `claude/*` PR (cheap continuous second opinion),
    while Hermes keeps the **merge authority** on substantial PRs; or
  - *Replace* part of Hermes' review load with a more capable model.
  **Open decision for the owner** once the mechanism is known: which model holds merge authority, and
  whether two external reviewers is worth the cost vs. noise.
- **Cost + noise are the risks.** A review on every push can be chatty and burns API spend; gate it
  (PR-open only, or `needs-review`-labeled only) like the morning-briefing rate-limit lesson.

## Next step

Research the exact Codex-PR-review mechanism + its cost/auth, write it up here, then put the
augment-vs-replace + merge-authority question to the owner (router). No build until the mechanism and
the cost envelope are confirmed (the Q-0082 spend cap applies).
