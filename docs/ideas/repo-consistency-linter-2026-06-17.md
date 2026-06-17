# Repo consistency linter — "CI for inconsistencies" (UX + pattern drift, not just layers)

> **Status:** `ideas` — capture (owner-directed 2026-06-17). Decision provenance: **Q-0170**. Plan:
> [`repo-consistency-linter-plan-2026-06-17.md`](../planning/repo-consistency-linter-plan-2026-06-17.md).
> Source code + the binding contracts win over this file.

## The problem (owner, 2026-06-17)

The owner wants *"something like CI but specifically to find inconsistencies"* — and notes we have
*"not much of that, if any"* beyond the architecture checker. Concrete examples he gave:

- **Panels missing a back button.**
- **Cogs that don't correctly follow the architectural rules** (beyond import layering).
- **Cogs that send ephemeral panel follow-ups instead of editing the panel in place** — *"it would
  be nice if a script could spot those kinds of inconsistencies immediately."*

These are **interaction/UX-pattern** inconsistencies: real, findable, and currently invisible to
tooling because `check_architecture.py` enforces *import layers*, not *interaction patterns*.

## What exists vs. the gap

- **`scripts/check_architecture.py`** — layer boundaries + the `architecture_rules/` YAML. Covers
  imports, raw-SQL fences, mutation seams. **Does not** see UX/interaction patterns.
- The **BaseView conformance ratchet** (RS10) nudges views onto `BaseView` but doesn't check
  per-panel UX (back button present, edit-in-place vs. ephemeral follow-up).
- **Gap:** no checker for *"does this panel follow the house interaction patterns?"* — exactly the
  owner's three examples.

## The idea

A new **`scripts/check_consistency.py`** (stdlib AST, the `check_architecture.py` house style):
a registry of **pattern rules** over `disbot/views/` + `disbot/cogs/`, each a small AST/structural
check with a clear message and an `architecture_rules/`-style allowlist for legitimate exceptions.
Seed rules from the owner's examples:

1. **Back-button presence** — a `HubView`/panel subclass with children but no navigation/back
   affordance (a `_back`/`Back`/breadcrumb button or the shared back mixin) → flag.
2. **Edit-in-place vs. ephemeral follow-up** — a panel callback that responds with a NEW ephemeral
   message (`followup.send(..., ephemeral=True)` / `response.send_message(...)`) where the house
   pattern is `response.edit_message` / `interaction.edit_original_response` → flag. (The owner's
   "edits in place" rule.)
3. **Panel base-class conformance** — a view that *acts* like a panel (buttons/selects) but extends
   `discord.ui.View` directly outside the game-state allowlist → flag (the rule the arch doc states
   in prose but nothing enforces).

Each rule: **warn-first**, disposable (Q-0105), with an explicit exception list — false positives
are the enemy (Q-0120: a checker that fights the evidence is the tool's bug). Graduate a proven rule
to error + CI-wired once it's quiet on a clean tree.

## Why it's worth having (high-leverage)

- It turns a class of **review findings the owner currently carries in his head** into an
  **immediate, repeatable signal** — the same leverage `check_architecture.py` gave layering.
- It's a **standing buildable lane** (one rule per PR is a real, meaningful slice) — directly feeds
  the "running out of plans" fix (Q-0164). The plan lists the rule backlog.
- It pairs with the **review inbox** (Q-0169): the linter catches *mechanical* inconsistencies; the
  inbox catches the *judgment* ones the owner spots by eye.

## Do-not-duplicate

- Extend the **`architecture_rules/` + AST** house style; don't build a parallel framework.
- Confirm against the **BaseView conformance** test so the base-class rule complements, not
  duplicates, it (`docs/helper-policy.md`).
