# 2026-07-13 — Friend-onboarding prompt (webshop beginner)

> **Status:** `in-progress`
> **Branch:** `claude/multi-repo-orientation-review-p5ztfi` (restarted from main; prior PRs #2064/#2065/#2066 merged)
> **📊 Model:** Opus 4.8 (owner switched mid-chat)
> **Venue:** owner-live chat, remote container (hub repo)

## What is about to happen

Owner ask: create a prompt the owner's friend pastes into **free claude.ai** (no Claude
Code, no subscription). The friend wants to sell things online (Stripe-style digital
products + AI-generated things) but doesn't yet grasp how to use AI well or run a
GitHub repo that tracks his work. The prompt must point his Claude at specific **real,
public** files in our repos, degrade gracefully if his free-tier chat can't browse,
teach the repo-as-memory discipline via the Stripe kit as the worked example, and end
with a concrete starter plan for his webshop + honest guidance on when the paid tools
are worth it.

All linked URLs pre-verified HTTP 200 (venture-lab Stripe LAUNCH-LOG + README,
superbot current-state/CLAUDE/collaboration-model/ender, substrate-kit README).
Deliverable: `docs/owner/friend-onboarding-prompt-webshop-2026-07-13.md` (the
paste-ready prompt + a short usage header) + the prompt text in chat.
