# Idea — mechanize the critical-review rubric (the checker backlog)

> **Status:** `ideas` — capture only. **Subsystem:** none (rebuild review tooling / workflow).
> **Provenance:** the critical-review rubric session (PR #1685, Q-0233) — the "enforce, don't
> exhort" arm of the rubric.

## The idea

The [critical-review rubric](../planning/rebuild-critical-review-rubric-2026-07-03.md) has ten
finding-classes; several are mechanizable into checkers so the review isn't purely manual:

- **Now, on the current repo (cheap, high-proven):** extend `scripts/check_plan_staleness.py` with
  an **un-anchored-`NN%` rule** — flag a `plan`-badged file that states a percentage/"complete"
  about a fast-moving component with no `as of #PR` anchor. This is the exact class that misled two
  sessions about the substrate kit; warn-only + the Q-0105 delete-if-noisy header.
- **In the rebuild (against declared manifests):** dependency-order-inversion (topological check on
  `depends_on`), thin-step (section-depth vs declared risk), fragmentation (repeated concept-name
  clusters), verification-hole (every subsystem declares a done-definition + oracle),
  UX/lifecycle-contract (the navigation-completeness golden — see
  [`rebuild-navigation-completeness-check-2026-07-03.md`](./rebuild-navigation-completeness-check-2026-07-03.md)).

### Audit-coverage AST checker — the complement to the `audit_completeness` fence (added 2026-07-05)

The rebuild's `audit_completeness` compile fence (spec `01` P6) forces every *declared*-mutating ref
onto the audited K7 engine, but is explicitly **"never an AST" — it trusts the developer-declared
`effect` field**. That leaves two holes verified against the plan (two agents, save-fixes session):
a leaf that **mis-declares** `effect="read"` yet writes through the still-legal `db.transaction()`
port, and a raw Discord **state** mutation (`channel.edit`/`member.ban`/`add_roles`) — there's a
named egress fence for `channel.send` but none for state mutations, and even that one is `PENDING`
(RC-21/Q-D26). Doc-`11` concedes it ("none reads a live row against a rule"; the "unaudited
`set_coins` mint" corruption). **The missing checker:** an AST verifier that (a) confirms a handler's
declared `effect` matches what it actually writes, and (b) fences raw Discord state-mutations the way
the egress fence fences sends. Full spec + the current-bot twin:
[`audit-seam-coverage-checker-2026-07-05.md`](./audit-seam-coverage-checker-2026-07-05.md) (it maps
onto the current bot's `check_architecture.py` now, and onto the rebuild's compile-fence stack later).

## Why it's worth having

The rubric turns instinct into a checklist; checkers turn the checklist into something CI proves.
The mechanizable classes are exactly the ones where a human reviewer's attention drifts (order,
duplication, un-anchored numbers) — mechanizing them frees the human to spend judgment on the
classes that need it (forgotten capabilities, generalization calls). Per Q-0132/Q-0194.

## Routing

Class-4 extension is a small current-repo checker PR (any session can pick it up). The rest land in
the rebuild's own review tooling (they need declared manifests to read). Full class→state map in the
rubric's "Mechanization roadmap".
