# /new-subsystem

Scaffold and verify a new subsystem's registration touch-points — fronts the existing
`scripts/new_subsystem.py` scaffold so it's discoverable, plus the "Adding a new subsystem / cog"
reading route from `docs/AGENT_ORIENTATION.md`.

## What this does

A real script already exists — `scripts/new_subsystem.py` scaffolds + verifies the ~8 subsystem
registration touch-points. This skill makes it discoverable and pairs it with the binding reading
route, so a new cog gets wired the standard way instead of by hand. Wrapper around the existing
script + orientation route, not new policy.

## Invocation

```
/new-subsystem
```

Then provide: the subsystem key (snake_case), the cog class name, the panel entry command, and the
parent hub it belongs under.

## Instructions for Claude

### Step 1 — read the binding route first

Follow `docs/AGENT_ORIENTATION.md` § "Adding a new subsystem / cog":

1. `docs/architecture.md` § "Where to add a new subsystem" + "Subsystem decomposition" + "PersistentView placement".
2. `docs/ownership.md` § "Subsystem ownership" + "Dependency direction".
3. `docs/runtime_contracts.md` § 1 (Subsystem identity contract) + § 3 (PersistentView contract) + § 7 (Managed task lifecycle).
4. `docs/building-roadmap/command-integration-standard.md` — required panel / Help / settings wiring.
5. `docs/building-roadmap/mother-hub-map.md` — where the new subsystem fits in the hub tree.
6. `docs/helper-policy.md` — where any new helpers belong.

Also confirm you're **not duplicating** an existing subsystem — folio coverage is intentional
(Q-0101); the ~24 smaller cogs are entered through `docs/repo-navigation-map.md`.

### Step 2 — check the touch-points

See what's already registered / missing:

```bash
python3.10 scripts/new_subsystem.py --key <key> --cog <CogClass> --panel-command <command> --parent-hub <hub> check
```

Use `--no-panel` for a config-only subsystem (no `KNOWN_PANEL_COMMANDS` entry — surfaced via
`!settings` + a summary command, like ai/welcome/counters/automod).

### Step 3 — scaffold

When ready, generate the registration touch-points:

```bash
python3.10 scripts/new_subsystem.py --key <key> --cog <CogClass> --panel-command <command> --parent-hub <hub> scaffold
```

Read the script's `--help` for the full flag set; it is the source of truth for which touch-points it
covers.

### Step 4 — verify

Re-run `... check` to confirm all touch-points are now present, then:

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
```

Both must exit 0. Boot the bot (`/verify-bot`) to confirm the new subsystem registers and its panel
opens.

### Notes

- The script is authoritative for the touch-point list — if it and this skill ever disagree, the
  script wins. This skill just routes you to it + the binding contracts.
- A new subsystem is real runtime code (`disbot/`) — size the PR small and risk-aware, mutations
  through a `*_mutation.py` service, views extending `BaseView`/`HubView`/`PersistentView`.
