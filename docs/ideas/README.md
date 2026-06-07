# docs/ideas — brainstorms (not approved)

> **Status:** `ideas`. **Nothing here is approved for implementation.** These are
> capture docs so ideas live in the repo instead of in chat. Source code, the
> binding contracts, and `docs/current-state.md` always win over anything here.

## What lives here

Pure brainstorm backlogs — capture without commitment. Each file should carry an
`ideas` badge in its header and state what it is *not* (not a plan, not approval).

Current broad captures:

- [`future-product-direction-2026-06-07.md`](./future-product-direction-2026-06-07.md) —
  source-aware future product direction across polish, extensions, reusable systems,
  and long-term expansions; capture-only, not a roadmap.

Related idea-shaped docs that live elsewhere **by design**:

- `docs/planning/superbot-ideas-lab-2026-06-05.md` — brainstorm backlog, **but** its
  §2 (operating decisions) and §6 (rejection ledger) are **binding** "do-not-propose"
  — so it stays in `planning/`, not here.
- `docs/mining_exploration_brainstorm.md` — design-intent for the mining subsystem,
  referenced by `disbot/cogs/mining/exploration.py` as design intent — stays in `docs/`.

## Promotion path (idea → shipped)

```text
chat idea
  → docs/ideas/<topic>.md                       (captured, not approved)
  → reviewed concept summary
  → approved implementation plan                (docs/planning/…)
  → docs/current-state.md "Next candidates"     (active candidate)
  → PR execution
  → shipped  (current-state "Recently shipped" + a Session Log entry)
```

An idea may graduate to an implementation plan only after **all** of:

1. **Ownership** — the owning service / cog / pipeline is identified (`docs/ownership.md`).
2. **Reuse check** — existing service/helper/abstraction reuse is confirmed; no
   duplicate systems (`docs/helper-policy.md`).
3. **Risk review** — privacy, security/permissions, cost, and moderation risk reviewed.
4. **Mechanics** — migration / cache / test / rollback needs are listed.
5. **Promotion** — `docs/current-state.md` marks it an active candidate.
