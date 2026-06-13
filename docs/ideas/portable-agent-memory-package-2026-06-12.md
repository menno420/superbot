# Vision: a portable agent-memory + workflow package (open source)

> **Status:** `ideas`. **Not approved for implementation** — strategic product direction,
> the maintainer's to shape. Captured so the in-repo work is steered toward it. Binding
> contracts and owner decisions win over anything here.

**Captured:** 2026-06-12 (maintainer vision, voice) · **Owning area:** agent ecosystem /
the workflow substrate itself (the *real artifact*, per `.claude/CLAUDE.md`).

> **▶ UPDATE 2026-06-13 — GRADUATED TO AN APPROVED PLAN.** This vision is now a concrete,
> owner-approved, finalization-ready **executable plan** (10 external-review rounds + ExitPlanMode
> approval): [`../planning/portable-substrate-kit-extraction-2026-06-13.md`](../planning/portable-substrate-kit-extraction-2026-06-13.md).
> This file is preserved as the **origin capture**; the discuss-lane questions below were resolved
> by the maintainer directing the work in-session. Execution = that plan (entry point: PR 1a).

## The idea

Extract the thing this repo is *actually* building — **consistent cross-session memory +
a self-improving agent workflow** — into a standalone, **open-source, installable package**
(the way CodeGraph is a package others `npx`/`pip install` and use freely). Anyone running
agents on their own codebase installs it and gets the orientation chain, the durable memory,
the session lifecycle, and the self-audit loop, instead of hand-rolling it like SuperBot did.

The maintainer's framing carries a **priority reorientation**: focus deliberately on
*improving the memory system and the autonomous workflow* — because once those are good
enough, **sessions execute the actual bot work by themselves**, which frees maintainer +
agent attention to keep improving the system. The substrate is the leverage; the bot is the
proving ground.

## Why this is the natural next artifact (not a tangent)

`.claude/CLAUDE.md` already states it outright: *"You are building a self-improving agent
ecosystem. The bot is the substrate; the real artifact is this workflow."* This idea is just
the **externalization** of that — taking the workflow from "a thing that happens to live in
SuperBot" to "a thing anyone can install." Everything needed already exists in-repo as
working, audited, git-versioned parts:

| SuperBot component | What it becomes in the package |
|---|---|
| `.claude/CLAUDE.md` + orientation chain (`AGENT_ORIENTATION`, read-order) | the orientation engine (project supplies content; package supplies the mechanism) |
| `.session-journal.md` + `.sessions/` + `current-state.md` living ledger | the durable cross-session memory + handoff format |
| Idea lifecycle (`docs/ideas/`) + question router | the idea/decision conveyor (no orphaned ideas; owner-intent capture) |
| Hooks (`claude_session_start` / `pre_edit` / `post_edit` / `stop`) | the lifecycle enforcement layer (surface tooling at the right moment) |
| `check_docs.py` / `check_architecture.py` / context packs | the freshness/reachability gates that keep memory from rotting |
| The session-ender rules (grooming Q-0015, idea Q-0089, review Q-0102) | the self-audit loop that makes it *self-improving*, not just persistent |

The Q-0096 plugins evaluation already noted memory plugins (claude-mem, memsearch) are
"skip — ours is the artifact." This idea is the inverse: **ours is good enough to be the
artifact *for others*.**

## The core hard problem

The whole system is currently **tightly coupled to SuperBot** — its paths, its architecture
rules, its subsystem names. Extraction is fundamentally a **mechanism-vs-content separation**:
the reusable engine (memory format, lifecycle hooks, gate framework, orientation router) has
to be pulled out from the SuperBot-specific *content* (the actual docs, the `disbot/` layer
map, the BTD6 specifics). That separation is the real work, and it is non-trivial — much of
the value is in the *conventions*, which are easy to copy but hard to package without
becoming either too rigid (one-size-fits-none) or too empty (a README telling people to do
what we did).

## Sequencing — prove it here first

The honest order, which also matches the priority reorientation:

1. **Harden the in-repo system** (now): make the memory + workflow genuinely excellent and
   *consistent* — e.g. the Q-0102 review loop, the session-close completeness hook
   (`claude-code-hooks-and-plugins.md` § brainstorm #1), the pre-compaction handoff hook.
   This is the priority the maintainer is pointing at, and it pays off immediately *in*
   SuperBot regardless of whether extraction ever happens.
2. **Identify the seam** while hardening: each time something is added, ask "is this
   mechanism or content?" and keep the mechanism cleanly separable. Cheap insurance.
3. **Extract** only once the in-repo system is proven and stable — a package built from a
   shaky substrate would just export the shakiness.

So this idea does not compete with bot work; it **reframes which improvements get priority**
(memory/workflow-substrate ones lead) and gives the eventual extraction a clean source.

## Open questions (why discuss-lane)

1. **Scope of v1** — full framework, or a thin, opinionated starter (the memory format +
   the session-ender rules + a couple of hooks) that others adapt? Thin-and-opinionated is
   likelier to actually get used.
2. **Maintenance commitment** — open source is a standing burden (issues, docs, versioning).
   Is that wanted now, or is the goal just to *keep the seam clean* and extract later?
3. **Naming / overlap** — position against existing memory plugins (which we deliberately
   skip) and CodeGraph (a sibling, not a competitor — this would *use* it).

## Routing

**Discuss first (router Q-block).** This is a product-direction call (does the maintainer
want to ship and maintain an OSS package?) plus a priority reorientation (substrate work
leads). Neither is an agent decision. **But step 1 (harden the in-repo memory/workflow) needs
no approval** — it is squarely the existing self-improvement mandate, so sessions should keep
doing it now, with the "mechanism vs. content" question (step 2) kept in mind. Pairs with
[`autonomous-improvement-loop-vision-2026-06-12.md`](./autonomous-improvement-loop-vision-2026-06-12.md)
(the loop this substrate runs) and the hooks brainstorm in
[`../operations/claude-code-hooks-and-plugins.md`](../operations/claude-code-hooks-and-plugins.md).
