# 2026-06-10 — Batch 2: surface-classification completeness invariant (DT04)

**PR:** #651 (draft → ready same session). **Queue:** consolidated plan
(`docs/planning/consolidated-implementation-plan-2026-06-10.md`) §5 Batch 2,
executed as one of **two parallel sessions** — the sibling ran Batch 1
(runtime truth/clarity). Per the §9 parallel-lane convention: Batch 1's six
files untouched, grooming pass skipped, `docs/current-state.md` deliberately
left for the reconciliation pass (both lanes would edit the same ▶ line —
the next session should fold "Batch 2 shipped #651" into it).

## Arc

Read the queue + mapping findings (A01/A05/B04/B07, Q-A03) → prototyped the
AST enumeration to size the real population (40 hidden routes, 2 alias
piles, 21+6 top-level slash namespaces) → built the ledger rules → declared
every classification → static CI mirror + runtime bucket → full CI mirror +
live boot proof.

## Shipped

- `core/runtime/command_surface_ledger.py`: `HIDDEN_ROUTE_CLASSIFICATIONS`,
  `ALIAS_DELIBERATION_THRESHOLD` (=3), entry fields `discord_hidden` /
  `classification_declared` / `alias_classification`, and the
  previously-reserved `findings.unclassified_entry_points` finally populated
  (`hidden:<name>` / `aliases:<name>`).
- Declarations: mining 21 (16 panel_action · 4 hidden · mineinv
  legacy_duplicate), moderation 7 panel_action, role 9 (2 legacy · 5
  panel_action · 2 internal_admin), utility 3 (2 legacy · avatar hidden),
  leaderboard aliases → legacy_duplicate (**Q-A03 held default implemented**),
  deathmatch aliases → power_user_shortcut, `/setup-hub` → legacy_duplicate.
- Static mirror in `tests/unit/runtime/test_command_surface_ledger.py`:
  rules V (canonical literals — typo can't silently default), H (hidden ⇒
  why), A (alias pile ⇒ disposition), S (two-way top-level slash pin),
  sentinel self-checks; explicit exception sets, empty by design.
- Verified: `check_quality --full` 8543 passed / 22 skipped; arch strict 0
  errors; 79 ledger tests; 200 Help/touched-cog tests; **live boot** with
  `unclassified_entry_points == ()` over the real 255-prefix/60-slash
  surface (offline `load_extension` rebuild — see gotcha below).

## Context delta

- **Needed but not pointed to:** FIND-B07 claimed "the ledger has no slash
  classification wiring" — **stale**: `_walk_slash_commands` already reads
  `extras` via `_classification_from_command`. The fix was a one-line
  declaration, not a seam. (The "verify cross-agent output vs source" rule
  earned its keep again — the consolidated plan's "may need a small
  slash-side seam" hedge was inherited from the unverified finding.)
- **Pointed to but didn't need:** the mapping reports' per-subsystem §3.1
  records; only the FIND blocks + command tables mattered for this batch.
- **Discovered by hand:** (1) ai_cog declares BOTH a prefix group `!ai` and
  a slash group `/ai` — any "(file, command-name)" key collides; index by
  kind too. (2) `getattr(cmd, "hidden", False) is True` is the only safe
  read over MagicMock-based test doubles (truthy Mock attrs). (3) FIND-A01's
  blanket "21 → panel_action" was wrong for 5 commands: `use`/`equip`/
  `unequip`/`gear` have no panel surface (grep-verified) and `mineinv`
  invokes `!inventory` — honest classes differ from the mapper's verdict.

## Decisions made alone (ratify if wrong)

- `ALIAS_DELIBERATION_THRESHOLD = 3`: 1–2 aliases = fluency (repo-wide
  norm), ≥3 = compatibility surface needing a declared disposition. Only
  leaderboard (9) and dm_challenge (3) cross it today.
- Hidden routes may NOT declare `primary_entrypoint`/`power_user_shortcut`
  (visible-only classes) — a contradictory declaration counts as
  unclassified.
- Top-level slash surface pinned name-by-name (27 namespaces); group
  *subcommands* ride their group's surface decision (documented in-test).
- Mining `use`/`equip`/`unequip`/`gear` = `hidden` (not panel_action):
  typed-only equipment interface until an Equipment panel exists.

## Flagged for maintainer / known limits

- The static mirror only sees **inline dict-literal** `extras=` declarations
  (enforced convention, documented in-test); a dynamically-built extras dict
  reads as "no declaration" and fails rule H/A — by design, but worth
  knowing.
- Q-A03 alias **display** (hiding the 9 leaderboard aliases in Help's two
  alias-render sites) is deliberately NOT wired — Batch 6's Help projection
  seam owns render changes; this batch ships the data + policy.
- The 7 live ledger findings that remain are the pre-existing documented
  orphan-cog entries (split BTD6 cogs, setup, RPS naming) — Batch-2-adjacent
  but out of scope (they're identity-contract territory, not
  classification).

## Gotcha worth keeping (boot-verification pattern)

To prove a build-time finding bucket empty against the REAL surface without
driving Discord: `await db.pool.init()` → `commands.Bot(...)` →
`load_extension` over `config.INITIAL_EXTENSIONS` → `build_ledger(bot)` —
no gateway login needed. One cog (`help_cog`) fails offline because the
scratch Bot still has the default `help` command (`bot1` uses
`help_command=None`); harmless for this purpose, but remember it when
counting.
