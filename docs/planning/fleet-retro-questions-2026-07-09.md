# Fleet retro questions — gen-1 self-review protocol (2026-07-09)

> **Status:** `owner-guidance` — manager-authored self-review protocol for the gen-1 fleet; answers feed the gen-2 blueprint.

## Purpose

Every gen-1 fleet Project answers this question set **in its own repo**, in a new file
`docs/retro/self-review-2026-07-09.md` (superbot-games answers per lane:
`docs/retro/self-review-mining-2026-07-09.md` / `docs/retro/self-review-exploration-2026-07-09.md`).
Rules of the exercise:

- **Question IDs are kept** — answer by ID so answers are comparable across repos.
- **Honest > flattering.** Friction, dead ends, and "I don't know" are the deliverable.
- **Every claim linked to repo evidence** (PR / commit / file) where possible.
- **Self-assessments are data, not verdicts** — the manager cross-checks each one against git.

Each repo received `docs/retro/QUESTIONS.md` (the universal core below plus that repo's addendum)
and an inbox ORDER to answer same-session as a READY PR. This master copy is the canonical text:
the universal core (sections A–F) followed by every per-repo addendum.

---

# Fleet self-review — gen-1 retro (2026-07-09)

Answer by ID. Honest > flattering. Link evidence (PR/commit/file). "I don't know" is a valid answer; invented certainty is not.

## A. Work & correctness

A1. What did you actually ship to main, vs what exists only on branches/drafts? Explain any gap.
A2. Which of your claims were verified against an external oracle (live run, real deploy, recorded goldens, a human) vs only your own tests?
A3. Which piece of your work are you LEAST confident in, and what concrete check would prove or disprove it?
A4. What did you build that turned out unnecessary, duplicated, or already existing somewhere you didn't look?

## B. Errors & friction

B1. List every error you hit (environment, CI, permissions, tooling, API). For each: time lost, and was it preventable by you, by better setup, or genuinely external?
B2. What did you have to figure out that was already documented somewhere you didn't find? Where SHOULD it have been for you to see it at the moment you needed it?
B3. What broke silently (no error, wrong result)? How was it eventually discovered?
B4. Which line of your Custom Instructions or orders was ambiguous, contradictory, or missing exactly when you needed it? Quote it.

## C. Efficiency

C1. Rough % of your working time spent on: orientation/reading · building · verifying · CI/merge mechanics · blocked/waiting. Biggest single time sink?
C2. What context did you rebuild from scratch that should have been durable (a file, an index, a summary)?
C3. Which tool/check/practice gave the most value per minute? Which the least?
C4. Redoing your work with what you know now: how much faster, and what's the biggest ORDERING change you'd make?

## D. Autonomy & owner input

D1. List every point you stopped for owner input or a human click. For each: truly owner-only (taste/money/irreversible), or unblockable by a pre-granted rule/scope? Name the grant.
D2. Which decisions did you route upward that you now think you should have taken decide-and-flag?
D3. Which decisions did you take while unsure you were allowed to? What written rule would have made it unambiguous?
D4. The smallest set of standing grants that would have let you ship end-to-end with zero humans: list it.
D5. Did you always know what "done" meant for your current order? Where was it undefined?

## E. Protocol & environment

E1. Did the control/ ritual (inbox first, status last, never edit inbox) fit how you actually work? Where did it cost you, or where did you skip it — and why?
E2. What should the ENVIRONMENT have contained at first boot that it didn't (deps, tools, config, data)?
E3. What should the REPO have contained at seed that it didn't (structure, CI, templates, examples, docs)?
E4. If a fresh session started on your repo tomorrow with no chat history, what would it misunderstand first, and what single document would prevent that?

## F. Redesign (the payload)

F1. Write the THREE rules you'd put into the next Project's founding instructions that weren't in yours.
F2. What should the MANAGER have done differently for you — orders too vague/too detailed, too many/few, wrong priorities, wrong timing?
F3. One capability you lacked that you'd trade almost anything for.
F4. If your Project were relaunched tomorrow "built right from the start": describe its ideal seed state in ≤10 bullet points.

## G. Addendum — SBNEXT (superbot-next)

G1. The presentation gap: what, at build time, would have made you LOOK at rendered output sooner — a rule, a gate, a tool? Be specific.
G2. Red-by-design masked per-defect signal. How would you keep honest-pending accounting AND per-red visibility with the least ceremony?
G3. The goldens sat on disk unused during the build. Would a binding "replay your band's goldens before merge" rule have been workable in your band flow, and what would it have cost?
G4. What made booting the composition root wait until PR #54? What would have made a walking skeleton natural at PR #2?

## G. Addendum — KIT (substrate-kit)

G1. Both fresh adopters stranded half-engaged before KL-7, and today two lanes in one repo double-adopted. What in the adopt UX invites these, and what's the kit-side fix beyond gates?
G2. What telemetry from adopters would change your decisions, in priority order — and the cheapest transport for each given you must never write adopter repos?
G3. Your release cadence today was 3 releases in one day. Right pace or churn for adopters? What's the ideal upgrade rhythm?

## G. Addendum — WEBSITES (websites)

G1. You were the most protocol-compliant lane today. What made compliance CHEAP for you — and which of those conditions are missing in the other repos?
G2. The #19 empty-merge incident predates today's gates. Is the current born-red machinery sufficient, or is a class of empty/premature merges still open?
G3. The /fleet page order: what data do you WISH heartbeats carried that they don't?

## G. Addendum — TRADING (trading-strategy)

G1. Why did P0 end as a draft PR? Reconstruct the reasoning honestly — instruction wording, caution, or something else?
G2. The env setup script failed at your provision. What exactly did you see, and what env contract would have made your first session frictionless?
G3. The holdout discipline: what would tempt a future session to peek, and what enforcement (beyond the loader warning) closes it?

## G. Addendum — ARMS (codetool-lab)

G1. You built WITHOUT the substrate-kit deliberately. What discipline did you invent yourself, and what did you miss that the kit would have given? Cost/benefit verdict.
G2. Model-comparison honesty: what about YOUR run do you suspect differs from the sibling arms because of the model, vs because of environment/timing noise?
G3. The tag/release wall (if you hit it): what release flow should agents have?

## S. Addendum — sonnet5-specific

S1. Nothing reached your repo for ~2h after seeding and after a direct wake order. Reconstruct what happened session-side: did sessions run and produce nothing, die, or never start? What error/UX state did the owner see?

## G. Addendum — GAMES (superbot-games, both lanes)

G1. The kit-adoption collision: reconstruct it from YOUR side — what did you check before adopting, what didn't you, and what rule/mechanism would have prevented it (claim file, lock file, seed-time adoption)?
G2. Per-lane control files: does the split work, or does anything still collide (session journal, .substrate/, claims dir)?
G3. Shared-surface development (games/shared/): is claim-first workable long-term or does it need something stronger (CODEOWNERS-style lanes, kit support)?
