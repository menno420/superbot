# 2026-07-07 — Port understand-and-reflect + guiding-questions into the substrate-kit

> **Status:** `in-progress`
> **Model:** Sonnet 5 · **Governance:** Q-0106 owner-directed-in-session exception applies

## What is about to happen

Across several live-chat turns, the owner directed that Q-0254 (understand-and-reflect: restate
the fuller picture before substantive work, expand a rough idea toward its possible fullest
shape, surface the possibility space when feasibility is uncertain) should graduate from a
superbot-local `CLAUDE.md` rule into **kit doctrine** — it should travel to every future repo,
not stay pinned here. In the same conversation he added: unattended sessions should route a
genuinely useful, non-derivable question into the repo (the question router) rather than skip
it; sessions should ask the *one* well-chosen guiding question during brainstorming (rare,
never during routine execution, only when it matters and is actionable); and big/vague ideas
should get a dedicated research pass or their own session rather than an answer from memory.

This session ports the synthesized rule into the substrate-kit's portable templates
(`CONSTITUTION.md.tmpl`, `collaboration-model.md.tmpl`, `question-router.md.tmpl`), regenerates
`dist/bootstrap.py`, and verifies the kit's test suite stays green. Superbot's own `CLAUDE.md`
Q-0254 entry gets a note that it graduated to kit doctrine (not removed — superbot is itself a
kit consumer and keeps its local copy until it upgrades from a real release).
