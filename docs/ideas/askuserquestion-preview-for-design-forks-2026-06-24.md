# Use `AskUserQuestion`'s per-option `preview` to show design-fork mockups

> **Status:** `ideas`. Not a plan, not approval. Source code and the binding contracts win.
> **Subsystem:** none — an agent-workflow / owner-interaction convention (touches no bot subsystem).

> **Provenance:** first captured as a session idea in
> `.sessions/2026-06-24-setup-log-channel-rework.md` (Q-0089), then re-surfaced twice in the
> settle-once dispatch run (2026-06-24) as an example of a *strong idea stranded in a session log
> where grooming can't find it*. Promoted here during the run's grooming pass (Q-0015) so it lives in
> the backlog. The deeper lesson it carries — *don't let a good idea die in the log it was born in* —
> is the reason this file exists.

## The gap

When an agent asks the maintainer to choose between design options with the `AskUserQuestion` tool, it
passes each option a `label` + `description` — plain text. The tool **also supports a per-option
`preview` field** that we don't use for design/UX forks. For a choice whose *whole point* is "which
resulting screen do you want?", a text description under-communicates: the owner can't see what he's
picking, so he picks the option that *reads* safest rather than the one that *looks* best.

## The cost this caused (the motivating case)

In the 2026-06-24 setup-log-channel work, the agent offered "Moderation log only (Recommended)" vs a
two-channel multi-select as plain-text options. The owner picked the narrower "Recommended" one — read
as a *permanent* scope cap — then clarified the next day he meant a *first slice* and wanted the richer
flow. Result: a full PR (#1429) built and **reworked the same day** (#1432). Had each option rendered a
quick mockup of its resulting step screen, the owner would likely have seen the richer flow was what he
wanted and skipped the rework.

## The idea

For **design/UX-shaped** `AskUserQuestion` forks (not yes/no or factual questions), populate each
option's `preview` with a compact rendering of that option's outcome:

- the resulting embed/panel layout (an ASCII or fielded mock of the step screen),
- or the concrete settings bundle it would apply,
- or a before/after of the surface it changes.

Pair it with a framing convention for **scope-narrowing** options: when one option is narrower than
another, the question should state whether the narrow choice is a *final scope* or a *starting slice*
(the second half of the motivating miss — recommending the narrowest option as "(Recommended)" without
that framing is what nudged the misread).

## Why it's worth having

- Cheap: the tool already supports `preview`; this is a usage convention + a small per-option mock
  builder, not new infrastructure.
- Directly prevents the same-day-rework class (a real, logged cost).
- Reinforces the self-improving-workflow premise: the owner *designs/visualizes*, so showing him the
  visual of each fork is exactly the altitude he works at (`docs/owner/maintainer-working-profile.md`).

## Not yet decided / open

- Which question shapes qualify as "design forks" (a heuristic, or an explicit agent judgment call).
- Whether to build a shared `preview`-mock helper or leave it per-call. Start per-call; promote to a
  helper only if 2–3 uses share structure (helper-policy).
