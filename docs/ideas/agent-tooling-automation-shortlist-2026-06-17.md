# Agent tooling + automation shortlist — Claude skills, scripts, a repo-native discovery aid

> **Status:** `ideas` — capture (owner-directed 2026-06-17: *"we never actually made skills for
> claude … I feel like we could improve the workflow if we created dedicated skills … find ways to
> automate more functions with scripts … a lot more is possible than we currently use … probably
> because I've never explicitly asked"*). Decision provenance: **Q-0170**. Builds on
> [`claude-code-plugins-evaluation-2026-06-12.md`](./claude-code-plugins-evaluation-2026-06-12.md).
> Source + binding contracts win.

## Framing

The owner is right that we've under-used Claude Code's automation surface. We *do* have a few project
skills already — **`/pre-pr`, `/session-close`, `/architecture-review`** — but no deliberate skill
strategy, and several recurring multi-step chores have no skill or script. This is the **shortlist**
to pick from; each item is small and the owner chooses which to build. (Distinct items get their own
idea/plan — the two biggest already do: the consistency linter and the review inbox.)

> **▶ Executable plan (2026-06-17, owner-confirmed approach):** the §A skill conversion is now planned
> in detail — [`procedures-to-skills-conversion-plan-2026-06-17.md`](../planning/procedures-to-skills-conversion-plan-2026-06-17.md)
> (the 33-procedure inventory, the thin-pointer convention, the must-NOT-move safety list, and the
> batched build order). Owner's framing: relocate procedures to on-demand skills (load when needed),
> keeping a thin pointer + the binding rules in CLAUDE.md.

## A. Dedicated Claude Code skills (slash commands for recurring flows)

| Skill | Wraps the recurring flow | Why |
|-------|--------------------------|-----|
| `/route-idea` | classify a raw idea → file it in `docs/ideas/` with the right template + index it in README + (if owner-decided) a router stub | the intake step the owner does constantly; today it's hand-done each time |
| `/cog-review` | run the standard cog-improvement audit (`cog-improvement-audit` idea) on a named cog and write findings | turns "review this cog" into one command — pairs with the review inbox (Q-0169) |
| `/plan-band` | the **dedicated planning session** the Q-0164 backlog flag asks for: assess buildable depth, promote ideas→plans to fill the band | makes "we're low on plans → plan more" a one-command session |
| `/fix-drift` | the **drift-on-sight** pass (Q-0166): run the ledger/docs checkers, fix what's actually drifted, no full reconcile | lets any session clean spotted drift fast without doing a whole reconciliation |
| `/new-subsystem` | front the existing `scripts/new_subsystem.py` scaffold | a real script already exists; a skill makes it discoverable |

## B. Consistency / quality scripts (CI-for-inconsistencies family)

- **`scripts/check_consistency.py`** — the UX/interaction-pattern linter (back buttons, edit-in-place
  vs. ephemeral follow-ups, panel base-class). **Has its own idea + plan**
  ([repo-consistency-linter](./repo-consistency-linter-2026-06-17.md)). The flagship of this thread.
- **`scripts/check_plan_backlog.py`** — a small, disposable (Q-0105) verified signal for the Q-0164
  backlog flag: count genuinely-buildable `ready` slices left in the band plan vs. the 30-PR cadence
  and print `BACKLOG THIN` when short, so the "are we running low on plans?" judgment becomes a
  number the SessionStart hook / reconciliation can surface instead of a vibe.

## C. A repo-native discovery aid (owner idea, 2026-06-17)

The owner wants *"something like codegraph or grimp but specifically built for our needs"* to help
agents **find files and information**.

- **The gap a generic graph leaves:** CodeGraph (symbols/edges) and Grimp (imports) are
  *language*-level; they don't know SuperBot's **domain vocabulary** — subsystems, folios, table
  **ownership**, `settings_keys`, panels, commands, the EventBus wiring. Agents still cross-reference
  `repo-navigation-map.md` + `ownership.md` + `context_map.py` by hand to answer *"where does X live /
  what owns table Y / which cog serves command Z / what panel hosts feature W."*
- **The idea:** a small **SuperBot-semantic index** (stdlib, reads the registries the dashboard
  export already parses — subsystem registry, settings_keys, command scan, ownership) that answers
  those domain questions directly: `find.py command <name>` → its cog + file + routing; `find.py owns
  <table>` → the owning service; `find.py subsystem <key>` → folio + entry points + related. It's the
  **machine version of the navigation map**, kept fresh from source.
- **Do-not-duplicate (check first, `docs/helper-policy.md`):** `scripts/context_map.py` (file blast
  radius), `scripts/wiring_map.py`, the `docs/agent/` context packs, `repo-navigation-map.md`,
  CodeGraph/Grimp. The win is only real if it **complements** these with domain-semantic lookups they
  don't offer — otherwise it's redundant. Prototype against 5 real "where is X?" questions from past
  session logs before committing.

## How to proceed (owner's choice)

The owner asked "what's possible" — this *is* the menu. Recommended: build the **consistency linter**
first (own plan, highest leverage), then pick 1–2 skills from §A that match his actual repeated pain.
The discovery aid (§C) needs the prototype-against-real-questions check before it earns a build.
