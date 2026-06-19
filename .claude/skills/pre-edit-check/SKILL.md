# /pre-edit-check

Before editing any `disbot/*` file, map its blast radius and confirm it is on the right side of the
layer boundaries — the standing "run `context_map.py` before any `disbot/` edit" step from
`.claude/CLAUDE.md` and the `.claude/rules/*` pre-edit checklists, in one command.

## What this does

Runs the two pre-edit checks the repo asks for before touching runtime code, so you know *what
depends on the file* and *which layer rules apply* before you change it:

1. **Blast radius + ownership** — `python3.10 scripts/context_map.py <file>` (who imports this, what
   it imports, the owning subsystem/service).
2. **Layer compliance** — `python3.10 scripts/check_architecture.py --mode strict` (current ERROR/WARN
   state, so you don't *add* a violation).

This is the invokable form of the `.claude/CLAUDE.md` CodeGraph guidance ("`context_map.py <file>` +
targeted grep is usually faster than the graph for a contained change") and the
`.claude/rules/mutation-and-db.md` / `discord-views.md` "Run before editing" blocks. It is a wrapper
around those existing procedures, not new policy.

## Invocation

```
/pre-edit-check disbot/services/economy_mutation.py
/pre-edit-check disbot/views/settings/edit_channel.py
```

The file path is required — pass the file you are about to edit.

## Instructions for Claude

When this skill is invoked with a file path:

### Step 1 — blast radius

Run and read the output:

```bash
python3.10 scripts/context_map.py <file>
```

Note: importers (who breaks if you change the public surface), imports (what this file depends on),
and the owning subsystem/service. For a `disbot/services/*` or `utils/db/*` file also confirm the
ownership against `docs/ownership.md` (which table/write this path owns).

### Step 2 — layer compliance

Run and read the output:

```bash
python3.10 scripts/check_architecture.py --mode strict
```

ERRORs are blocking; WARNs are pre-existing tracked violations. The target before you edit is to know
the **current** count so you can prove afterward you added none. The one rule with **zero tolerance**
for new violations is `services/ -> views/`.

### Step 3 — pick the right reading rule

If the file is a service / DB module -> the `.claude/rules/mutation-and-db.md` rules apply (write
through the domain `*_mutation.py`, never raw `pool.execute()` outside `utils/db/`, always emit
`audit_events.emit_audit_action()` for auditable mutations, use `settings_keys` constants).

If the file is a view -> the `.claude/rules/discord-views.md` rules apply (extend `BaseView`/`HubView`/
`PersistentView`, never import from `cogs/`, re-check authority at callback time).

These `.claude/rules/*.md` files are **glob-triggered** — they load automatically when you open the
matching file. This skill just front-loads the *command* half so you run it deliberately.

### Step 4 — report

Print a short summary:

- **File:** `<file>` — layer: `<utils|core|services|governance|views|cogs>`
- **Importers:** N (the files that break if the public surface changes)
- **Architecture:** N errors / M warnings (must add 0 new errors)
- **Applicable rule file:** `mutation-and-db` / `discord-views` / none

### Notes

- CodeGraph false positives still apply — `dead-unresolved`, name-collision merged caller graphs,
  Discord-decorator invisible entry points, empty `callees`, and EventBus/registry edges invisible to
  both tools. See `.claude/CLAUDE.md` § CodeGraph before trusting any "no callers" verdict.
- This skill is read-only. It does not edit anything; it tells you what to watch before you do.
