# Idea — button ↔ text-command surface parity audit

> **Status:** `ideas`. Not a plan, not approval. Source + binding contracts win.
> Captured 2026-06-16 (Q-0089 session ender) from the `!coglist` command request (PR #951).

## The observation

The admin panel had a **📋 Cog List** button (opening `_CogManagerView`) but **no text command**
for it — so a user typing `!coglist` / `!cogs` got nothing (and, pre-#949, an infinite loop). The
owner's fix request was telling: *"there is a button that does exactly that, so link the text command
to the button as well."* Users expect an action reachable by a button to also be reachable by a
command (and often a slash). The reverse is the already-tracked direction (commands → surfaces).

## The idea

A review-lane audit (maybe a soft, advisory check) that pairs **interactive panel buttons that
perform a distinct action** with an equivalent **text/slash command**, and flags buttons whose action
has no command front door. The cog-list gap was found only because a user hit it; a periodic parity
pass would surface the rest (e.g. other `_*PanelView` action buttons).

## What to look into / cautions

- **Not 1:1 and hard to fully automate.** Many buttons are *navigation* (open a sub-panel), not
  distinct actions — those don't need a command. An AST/heuristic guard would over-flag; this is
  better as a **guided manual review** (or a checklist in the UX docs) than a hard CI invariant.
- A lighter, automatable slice: ensure the *names users actually type* exist — e.g. mine the
  `on_command_error` "command not found" telemetry (or known synonyms) for high-frequency misses and
  confirm each maps to a real command/alias. (BUG-0014 was exactly such a miss.)
- discord.py gotchas this class hits: method names can't start with `cog_`/`bot_`; a command with
  ≥3 aliases must declare `extras={"alias_classification": ...}` (the surface-ledger invariant).

## Sibling failure mode (added 2026-06-16, BTD6 live-events session)

There is a related-but-distinct "button does nothing" class this idea should **not** try to
own: a button that *does* have a callback but the callback **silently crashes** after deferring
(here, the BTD6 Live Events drill-down raised `TypeError` from a bad `search_facts(entity_key=…)`
call; the deferred ephemeral never updated and the view's `on_error` swallowed it). That's not a
missing-surface gap — it's a tested-but-broken callback — and the right guard is test-time
signature fidelity, routed to
[`autospec-mock-fidelity-guard-2026-06-16.md`](./autospec-mock-fidelity-guard-2026-06-16.md),
not a surface-parity audit. Keeping the two scopes separate stops this idea from over-reaching.

## Disposition

Review-lane idea (UX/discoverability), scoped to **missing command front doors for action
buttons** (not silently-failing callbacks — see sibling note above). Candidate to fold into
`docs/ux/` review guidance or the production eval checklist rather than ship as a brittle CI
guard. Relates: `cogs/admin_cog.py` (panel buttons),
`core/runtime/command_surface_ledger.py`, `utils/synonyms.py`.
