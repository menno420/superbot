# Explicit `subsystem:` tag on idea files (make idea↔command linking authoritative)

> **Status:** `ideas` — captured 2026-06-19 (session idea, Q-0089, from building S1.1 of the
> website command browser). Source + merged PRs win.
> **Subsystem:** none — the idea-tag mechanism itself (export tooling) — header tag (the `**Subsystem:**` in the body is an example, not read).

## The gap

The website command browser (plan unit S1.1, shipped this session) links each command to its
subsystem's **open ideas** — surfaced on the public site as "what's planned" teasers and as the
`finished`/`in-progress` maturity badge. But idea files carry **no structured subsystem field**, so the
producer (`scripts/export_dashboard_data.py` → `_subsystem_open_work`) falls back to a **heuristic**: it
matches a subsystem when every token of its key appears in the idea's *filename slug*. That works for
distinctive keys (`btd6`, `mining`, `rps_tournament`) but:

- **single common-word keys cross-match** — e.g. `chain` (the Word Chain game) matches an agent-workflow
  idea slugged `executor-chain-trigger-…`; `channel` / `community` are similarly generic.
- **ideas with no key token in the slug are silently unlinked** even when they are clearly about a
  subsystem (the slug just used different words).

The redaction lens keeps even a stray match *safe* (only title + status surface), so this is a
**precision** problem, not a safety one — but a wrong "what's planned" teaser on a command is mildly
misleading, and the heuristic is drift-bait (a new generic-word subsystem key could start cross-matching).

## The idea

Add an optional **`Subsystem:` (or `Area:`) front-matter line** to idea files — a comma-separated list of
subsystem keys the idea touches, validated against the registry:

```markdown
# Some idea title

> **Status:** `ideas`
> **Subsystem:** economy, mining
```

Then `parse_ideas` reads it into the idea record, and `_subsystem_open_work` prefers the **explicit tag**
when present, keeping the filename-slug heuristic only as the fallback for un-tagged ideas (exactly the
"explicit tag, heuristic fallback" shape the plan recommended for S1.1). A tiny `check_docs`-style guard
can warn when a tag names a non-registry key (the same fail-closed instinct as the site.json whitelist).

## Why it's worth having

- **Turns a guess into a fact** for the headline user-facing surface — the command browser's "what's
  planned" teasers and maturity badges become authoritative where it matters.
- **Cheap + incremental** — the heuristic stays as the fallback, so no idea needs the tag immediately;
  tagging just *improves* precision idea-by-idea. No big migration.
- **Reusable** — the same tag lets the dev dashboard's `/ideas` group by subsystem, and lets a future
  Hermes/roadmap view answer "what's planned for economy?" directly.
- **Closes a drift-bait seam** the S1.1 code itself flags in its own docstring caveat — the durable fix the
  comment points at.

## Neighbours (not duplicates)

- `docs/ideas/cog-declares-its-subsystem-2026-06-16.md` — that is about **cogs** declaring their subsystem
  (kills the dashboard's *cog*-name derivation). This is about **ideas** declaring their subsystem (the
  *idea*→command link). Complementary: both replace a name-derivation heuristic with a declared field.
- `docs/ideas/dashboard-registry-coverage-check-2026-06-16.md` — registry-coverage guard; adjacent but
  about cog↔registry resolution, not idea linking.

## Promotion path

Small/decided lane: extend `parse_ideas` (1 field) + `_subsystem_open_work` (prefer tag) +
`tests/unit/scripts/`, then tag a handful of ideas to demonstrate. A `docs/ideas/README.md` convention note
documents the optional tag. No owner decision needed (additive, reversible) — a future session can just
build it.
