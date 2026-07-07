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

## What shipped

- **`CONSTITUTION.md.tmpl`** — new "Understand-and-reflect" bullet under Working agreement
  (restate the fuller picture, feasibility-first framing) + the unattended-question routing
  clause folded into the existing "Ask" bullet.
- **`collaboration-model.md.tmpl`** — new "Guiding questions" section (the rare, selective,
  matters-and-actionable filter + big-idea escalation to research/dedicated session).
- **`question-router.md.tmpl`** — header clarifies any session, not just the interview, may
  append a Q-block.
- **`dist/bootstrap.py`** regenerated; **440/440 kit tests green**, dist byte-pin holds.
- **Third router addendum on Q-0254** — the owner's later confirmations recorded verbatim
  (kit-graduation, unattended-routing, the guiding-questions filter confirmation, big-idea
  escalation, deferred threshold calibration).
- **`.claude/CLAUDE.md`** Q-0254 bullet extended with the graduation note + the two new
  mechanisms; a pre-existing line-wrap formatting glitch in the same paragraph fixed in passing.
- **`docs/AGENT_ORIENTATION.md`** pointer extended to match.
- **Idea filed:** `cold-start-ab-vague-idea-task-2026-07-07.md` — a T6 benchmark task so the
  doctrine's own drift would eventually get caught, not just assumed to hold forever.

## Context delta (reflection interview)

- **Needed but not pointed to:** the kit's own template files were the right read, but I had to
  check for hidden test coupling (line-count caps, exact-content assertions) before editing —
  none existed, which was good luck as much as good design; a future template edit doing
  something riskier should check the same way.
- **Pointed to but didn't need:** none.
- **Discovered by hand:** a real formatting glitch in the Q-0254 CLAUDE.md bullet (an awkward
  mid-sentence line-break artifact from an earlier edit) — fixed while extending the same
  paragraph rather than left for a future session to trip over.
- **Decisions made alone:** exact placement of each new template bullet (Working agreement vs.
  autonomy rails vs. a new "Guiding questions" section) — all reversible wording/placement calls,
  not product decisions.
- **Flagged for maintainer:** none — every substantive call in this session was a direct,
  already-confirmed owner directive from the live conversation, not a judgment call needing a
  flag.
- **One docs change that would have helped most:** none beyond what shipped.
- **🛠 Friction → guard:** none new this session.

## ⟲ Previous-session review (Q-0102)

The understand-and-reflect-rule session (PR #1806, same day, immediately prior) did the CLAUDE.md
port correctly and iterated cleanly across two live refinements before merge — but in hindsight
it should have asked the "does this belong in the kit, not just here?" question itself, since it
had *just finished* the kit-lab founding plan session and knew the kit-vs-repo distinction better
than anyone. It didn't, and the owner had to raise it explicitly a turn later. **Concrete
improvement:** when a session ships a new working-agreement rule immediately after researching a
sibling system's portability model, it should proactively ask "does this rule's natural home
match what I just learned," not wait to be told.

## 💡 Session idea (Q-0089)

[`cold-start-ab-vague-idea-task-2026-07-07.md`](../docs/ideas/cold-start-ab-vague-idea-task-2026-07-07.md) —
a T6 benchmark task so the just-shipped doctrine's own future drift gets caught mechanically,
matching the B3 guard-telemetry "did it actually fire" instinct applied to a written rule.

## 📤 Run report

- **Did:** ported the understand-and-reflect + guiding-questions doctrine into the substrate-kit's
  portable templates, regenerated dist, verified 440/440 tests · **Outcome:** shipped
- **Shipped:** #1809 — the template port + CLAUDE.md graduation note + one idea
- **Run type:** `manual` (owner live-directed, in-chat, continuing the same conversation)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — direct owner directive
- **📊 Model:** Sonnet 5 · standard · docs-only (kit template edit + regenerate + test)
- **↪ Next:** nothing blocking; the T6 benchmark idea is a kit-lab program (band KL-5) candidate

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged | 1 (#1809, auto-merge on card flip) |
| CI-red rounds | 0 unexpected (born-red gate holds by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (cold-start-ab-vague-idea-task) |
| Ideas groomed | 0 |
