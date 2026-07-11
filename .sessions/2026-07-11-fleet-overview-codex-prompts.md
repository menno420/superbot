# 2026-07-11 — Fleet overview: Codex prompts · PR hygiene · owner queue · product catalog · review-skill generalization

> **Status:** `in-progress`

📊 Model: Fable 5 · owner-directed hub session (fleet management) · day

## What is about to happen

Owner-directed (in-chat, 2026-07-11, while he writes Anthropic email #2):

1. **4 Codex review prompts** — one per repo (Codex is single-repo-reliable), targeting the
   4 most review-valuable repos, self-contained + copy-paste ready.
2. **Fleet PR hygiene** — enumerate open PRs across all fleet repos, classify stale vs live,
   safely merge the mergeable, close the dead, flag the ambiguous.
3. **Owner-action queue distillation** — sweep all repos for owner-only steps; decide/do
   everything decidable with logic/facts (Q-0240 decide-and-flag); leave only the genuinely
   owner-only items.
4. **Plain-language product catalog** — every produced product: what it does, who it's for,
   how to use/deploy, what only the owner can do.
5. **Generalize the `review` vocab word + skill** — object dispatch ("review this repo /
   report / prompt / PR") instead of the fleet-night-review hardcode; apply the same
   general-verb pattern to the vocab so sessions behave consistently.

Mapping agents fan out across the 14 fleet repos while local skill work proceeds.
