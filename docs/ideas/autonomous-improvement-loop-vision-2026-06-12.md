# Vision: the fully-autonomous self-improvement loop

> **Status:** `ideas`. **Not approved for implementation** — this is the north-star the
> existing workflow scaffolding is *already* building toward, captured so sessions can aim
> at it. It decomposes into reviewable steps (see Routing); it is not a single build.
> Binding contracts and owner decisions win over anything here.

**Captured:** 2026-06-12 (maintainer vision, voice) · **Owning area:** agent ecosystem /
workflow (the *real artifact*, per `.claude/CLAUDE.md` Working agreement & `docs/collaboration-model.md`).

## The vision (maintainer's words, sharpened)

> "Eventually all the agents together work so the bot is continuously improved. Once all
> bugs are fixed, UX is perfect, everything works — *then* the agents come up with ideas of
> their own, carefully reviewed. The best workflow recreates what I currently do, but fully
> autonomous: one session creates an idea and stores it, the next revises it into a draft
> plan, the session after finalizes the plan or starts implementing. And that's where Hermes
> is the valuable link — it's the one mind that differs from Claude in this loop, so it can
> independently review the plans and the way the functions are made, message me to explain
> the new features, and I test and approve or deny."

Three claims, each mapped to what already exists and what is missing.

## 1. The multi-session idea → plan → implement pipeline

This is **already the documented idea lifecycle** (`docs/ideas/README.md`:
raw → captured → routed → plan → implement) and the **chaining protocol**
(`docs/owner/ai-project-workflow.md` §10: handoff → fresh bounded session → green merge →
auto-deploy → sharpened handoff). What the maintainer adds is removing the **human trigger
between stages**: today *he* starts each session; the vision is sessions that **hand off to
each other automatically**.

- *Exists today:* the lifecycle, the per-session bounded-handoff protocol, forced
  idea-generation every session (Q-0089), Railway auto-deploy on merge, agent self-merge of
  green work (Q-0084).
- *Missing:* the **automatic chaining** — session N's end state triggering session N+1.
  This is exactly the [Hermes → Claude Code Routines dispatch bridge](./hermes-claude-dispatch-bridge-2026-06-12.md):
  a scheduled/API/GitHub-event routine starts the next session with the prior session's
  artifact as its work order. **That idea is step 1 of this vision.**

## 2. The sequencing gate — correctness before invention

The maintainer is explicit about **order**: bugs first, then UX, then "everything works,"
and **only then** agent-originated features. This matches `.claude/CLAUDE.md` ("Bugs first,
durably") and must be enforced, not assumed: an autonomous loop left ungated would invent
features while bugs remain. The loop needs a **phase signal** — a machine-readable "are we
in the fix/polish phase or the invent phase?" gate (candidate source: the readiness
scoreboard + bug-book open count + the production-readiness maps). Agent-*generated* feature
work stays gated behind that signal; bug/UX/correctness work is always in-season.

## 3. Hermes as the independent reviewer — the keystone

This is the genuinely **new architectural insight**, and the strongest reason the loop is
trustworthy. In a Claude-only loop, every author *and* every reviewer is Claude — a
**monoculture**: the same model's blind spots are invisible to itself, so self-review
catches less than it appears to. Hermes is **a different model (Nous Research), a different
mind**. Putting it in the loop as the independent reviewer breaks the monoculture:

- **Independent plan review** — before a plan is finalized, Hermes (read-only, repo-aware)
  critiques it: is the approach sound, does it fit the architecture, what did the Claude
  author miss? A dissent from a different model is worth far more than another Claude pass.
- **Independent implementation review** — Hermes reviews "the way the functions are made"
  on the PR diff: not CI (that's mechanical) but design/clarity/missed-cases judgment from
  outside the author's model family.
- **Human liaison + approve/deny gate** — Hermes **messages the maintainer in plain
  language** explaining each new feature, who **tests and approves or denies**. This keeps
  the irreversible step (shipping an agent-originated feature) human, reached through a
  *different* agent than the one that built it. The maintainer's verdict routes back into
  the loop (merge / revise / reject-to-ledger).

This also reframes Hermes' role across all three captures: not just dispatcher (idea 1) and
monitor (`log-triage`/`repo-health`), but **the independent-review + human-gate seam**.

## What exists vs. what's missing (honest)

| Capability | State |
|---|---|
| Idea lifecycle + forced generation | ✅ exists (`ideas/README.md`, Q-0089) |
| Bounded session handoff protocol | ✅ exists (`ai-project-workflow.md` §10) |
| Plan→execute model split (premium plans, cheaper executes) | ✅ exists (§11) |
| Auto-deploy on merge + agent self-merge | ✅ exists (Q-0084, production-deployment) |
| Automatic session→session chaining | ❌ needs Routines bridge (idea 1) |
| Correctness-vs-invention phase gate | ❌ needs a machine-readable signal |
| Independent (non-Claude) plan/impl review | ❌ needs the Hermes-reviewer seam |
| Human explain → approve/deny loop via Hermes | ❌ needs a Hermes review/notify skill + a verdict-routing convention |

So the substrate is largely built; the loop is **~3 seams** short of closing.

## Open questions (why this is discuss-lane)

1. **Is Hermes capable enough to be the reviewer that matters?** Its review only adds value
   if it catches real issues. Needs the "unverified — confirm against ground truth a few
   times" discipline (CLAUDE.md tooling rule) before its dissent is trusted to gate work.
2. **Where is the human gate, exactly?** Every agent-originated *feature* through the
   approve/deny step? Or only above a risk threshold, with docs/bug-fixes flowing freely?
3. **Self-merge under full autonomy** — the gating from idea 1 (routine opens PR; merge
   behind green-CI + scope rules or a one-tap Telegram confirm) applies here too.
4. **Loop stop-conditions** — what halts a runaway loop (cost cap, daily-run cap, a
   red-readiness freeze)? §11 cost discipline is the budget side of this.

## Routing

**Discuss first (router Q-block).** This is the ecosystem north-star, not a single PR — it
is the explicit *real artifact* of this repo, so the maintainer owns its shape. It
decomposes into reviewable, independently-valuable steps:

1. **[Dispatch bridge](./hermes-claude-dispatch-bridge-2026-06-12.md)** (Routines) — the chaining.
2. **Hermes-reviewer seam** — a read-only `superbot-review` skill (plan + PR-diff critique)
   + a notify/approve-deny convention. Independently useful even with manual chaining.
3. **Phase gate** — a readiness/bug-count signal that says fix-phase vs. invent-phase.

Each step is shippable and reviewable on its own; none requires committing to the whole
loop up front. Build them in that order, review each in production, and the autonomous loop
assembles itself from verified parts rather than as one leap.
