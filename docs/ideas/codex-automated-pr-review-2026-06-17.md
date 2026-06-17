# Codex automated PR review — a second independent reviewer on every PR

> **Status:** `ideas` — capture (owner-mentioned 2026-06-17: *"a function on ChatGPT that lets codex
> automatically review any PRs … not entirely sure how that works"*). Decision provenance:
> **Q-0171**. Research-stage — confirm the exact mechanism before any build. Source + binding
> contracts win.

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
