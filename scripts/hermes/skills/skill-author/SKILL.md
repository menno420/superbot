---
name: superbot-skill-author
description: "Turn a recurring Hermes workflow into a new, well-formed, version-controlled SuperBot skill — design it, write it in the repo's skill format, regenerate the installable artifact, and open a docs-only PR so it is reviewed and committed (not left as a VPS-only scratch file)."
version: 1.0.0
author: "SuperBot agents"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Meta, SuperBot, SelfExtension]
    related_skills: [superbot-prompt-builder]
---

<!-- GENERATED — DO NOT EDIT. Source of truth: docs/operations/hermes-skills/skill-author.md. Regenerate with scripts/hermes/build_skills.py. -->

You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
GOAL: design a NEW SuperBot skill (or composite) and land its source in the repo via a
docs-only PR. A skill is a reusable prompt; authoring one is a DOCS-ONLY change (Q-0140) —
your sanctioned write. You never edit code or push runtime changes.

STEP 1 — JUSTIFY (read-only). Before writing anything:
  - git -C /home/hermes/repos/superbot fetch origin main
  - Confirm the workflow RECURS (a one-off doesn't earn a skill) and is not already covered:
      ls docs/operations/hermes-skills/ ; grep -ril "<the-job>" docs/operations/hermes-skills/
    If an existing skill already does this, STOP and use it instead.
  - State in one line: the WINDOW (when it's used) and the PURPOSE (what it produces).

STEP 2 — DESIGN. Decide:
  - name: superbot-<kebab-case> (lower-case, hyphens).
  - For an ATOM: the ordered read-only steps + the single output it produces.
  - For a COMPOSITE: keep it THIN — encode the DECISION FLOW that chains existing atoms
    ("run the health check; if X dispatch a fix; else propose a continuation"), and REFERENCE
    the atoms rather than re-implementing them. Do not duplicate another skill's body.
  - Bake in the standing rules so the skill is safe on its own:
      * read-only by default; the only writes are docs-only PRs and the review-merge gate;
      * anything touching code is DISPATCHED to Claude Code, never edited here;
      * verify, don't assume (railway_vars.py / check_* / gh) — say what you verified;
      * never print secrets; reference env vars by name only;
      * end with one clear verdict or next step (a hint, not an action you take).

STEP 3 — WRITE THE SOURCE. Create docs/operations/hermes-skills/<name>.md in the canonical shape
  (copy an existing skill's structure exactly — e.g. session-brief.md or dispatch.md):
      # Skill: `superbot-<name>`
      > **Status:** `living-ledger` — <one line>.
      **Window:** ...   **Purpose:** <one sentence — the builder lifts this verbatim>
      **When to use:** ...
