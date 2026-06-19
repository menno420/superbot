# /cog-review

Run the standard cog-improvement audit on a named cog and write the findings — the
`cog-improvement-audit` pass (`docs/ideas/cog-improvement-audit-2026-06-08.md`) on one cog, as a
command. Pairs with the owner review inbox (Q-0169).

## What this does

Audits a single cog the way the 2026-06-08 cog-by-cog review session did: read the cog + its view
package + service + DB module, check it against the binding contracts and the known gap-list, and
write a findings note (gaps, UX issues, architectural debt, quick-wins) routed to its durable home.
Turns "review this cog" into one command. Wrapper around the existing audit procedure, not new
policy.

## Invocation

```
/cog-review economy
/cog-review setup            # the standing P0 — the wizard is too long / half its steps do nothing
```

Pass the cog name (the `<name>` in `<name>_cog.py`).

## Instructions for Claude

### Step 1 — locate the cog's surface

Use `docs/repo-navigation-map.md` (the subsystem cheat-sheet) to find the cog's package, view
package, service, and DB module. For a high-traffic area, start at its folio
(`docs/subsystems/<area>.md`). Confirm mutation ownership in `docs/ownership.md` and the Help route in
`docs/help-command-surface-map.md`.

### Step 2 — read the existing audit findings

Check `docs/ideas/cog-improvement-audit-2026-06-08.md` for this cog's already-captured gaps and the
owner's stated priorities (e.g. "fix setup wizard first" is the standing P0). Don't re-discover what's
already logged — build on it.

### Step 3 — audit against the standard axes

For the named cog, assess:

- **Functional gaps** — missing commands / features the owner flagged or that are obviously absent.
- **UX / interaction patterns** — back buttons present? edits-in-place vs. ephemeral follow-ups?
  panel base-class correct (`BaseView`/`HubView`/`PersistentView`)? typed input where a select menu
  belongs? (These are the axes the `repo-consistency-linter` idea targets — check by hand here.)
- **Architecture** — `python3.10 scripts/check_architecture.py --mode strict` clean for its files?
  mutations through the `*_mutation.py` service? no cross-cog imports / `services -> views`?
- **Settings honesty** — any panel setting wired to nothing (a known confusion class)?

### Step 4 — write the findings

Write the findings to their durable home:

- Add / update this cog's section in `docs/ideas/cog-improvement-audit-2026-06-08.md` (or the area
  folio's "Next candidates"), each item sized (S/M) and prioritized.
- A concrete, decided improvement can be *promoted to a plan* (`docs/planning/`) and built — promotion
  needs no approval (Q-0172); flag it `⚑ Self-initiated`.
- When the owner review inbox exists (Q-0169 / the review-inbox plan), post the review there with an
  open->resolved status so it isn't forgotten mid-session.

### Step 5 — report

Print: cog · files audited · N findings (by priority) · architecture clean (Y/N) · where the findings
were written · any item promoted to a plan.

### Notes

- This is a *review*, not a build — surface the work, route it, then let `/groom-ideas` or a dispatch
  run pick it up. A small, safe, decided quick-win you can fix in the same pass, fix it (and flag it).
- Source files are authoritative when a doc and the code disagree.
