# Hook policy — when a fix becomes a hook (vs. a rule, a checker, config, or a doc)

> **Status:** `reference` — the decision guide for *which mechanism* a recurring problem
> should be solved with. The executable-config analogue of [`helper-policy.md`](../helper-policy.md):
> read it before reaching for a hook so a fix lands in the right layer. Owner-directed
> (Q-0139, 2026-06-14). Binding contracts and source win over this.

## Why this exists

When something goes wrong repeatedly — a stale branch merges dirty, an edit lands un-formatted,
a session forgets to close out — there are **five** different places the fix can live, and
choosing wrong is costly: a hook that should have been a doc adds noise to every turn; a rule
that should have been a hook keeps getting forgotten. This doc names the five mechanisms and
the test for each, so future situations route correctly the first time.

> **Authority boundary (CLAUDE.md Q-0106).** Hooks, `.claude/settings.json`, and `CLAUDE.md`
> are **executable config the agent does not self-edit on its own initiative** — you *propose*
> a change as a router Q-block (DISCUSS lane), unless the **maintainer directs it in-session**
> (then apply it and record the Q). This policy tells you *which* mechanism fits; it does **not**
> lift that boundary.

## The five mechanisms

| Mechanism | Where | Solves | Trigger |
|---|---|---|---|
| **Hook** | `.claude/settings.json` `hooks` + a `scripts/*.py` | something that must happen **automatically, every time**, at a lifecycle moment — the agent *forgetting* is the failure | a Claude Code event: `PreToolUse` · `PostToolUse` · `Stop` · `SessionStart` |
| **Checker** | `scripts/check_*.py` | a **verifiable pass/fail** condition | run on demand, in CI, or *called by* a hook |
| **CLAUDE.md rule** | `.claude/CLAUDE.md` | a **principle / judgment call** that can't be fully mechanized | the agent reads it and applies judgment |
| **settings.json config** | `.claude/settings.json` (non-hook) | **configuration** — permissions, env, enabled MCP servers | static, read at session start |
| **Doc** | `docs/**` | **knowledge to consult** for a task | the agent reads it on the relevant read-path |

## What qualifies as a hook — the five-part test

Reach for a **hook** only when **all** of these hold. If any fails, it belongs in another mechanism.

1. **Automatic & forgettable.** It must fire *without the agent choosing to*, and the failure mode
   it prevents is *the agent forgetting* (or not noticing). If a reliable agent reading CLAUDE.md
   would always do it anyway, a rule is enough.
2. **Event-anchored.** There is a real lifecycle event to attach to — `PreToolUse` (before a tool
   runs, can gate), `PostToolUse` (after, e.g. auto-fix), `Stop` (end of turn), `SessionStart`
   (boot). No matching event ⇒ not a hook (use a rule + a checker).
3. **Mechanizable at fire-time.** The trigger condition and the action are expressible as code with
   **no judgment needed when it fires**. If deciding *whether* to act needs context, it's a rule.
4. **Cheap & safe.** Fast (sub-second for the common path), side-effect-light, and **non-blocking
   by default** — an advisory that prints and exits 0. Only *gate* (block the tool) when the
   condition is a true must-not-proceed, and even then prefer a checker in CI.
5. **Recurring.** The situation happens across many sessions. A one-off doesn't earn a hook —
   hooks run on *every* matching event forever, so each one is a standing tax.

### Quality bar for an accepted hook
- **Defensive:** every failure path swallows the error and exits 0 — a buggy hook must never break
  a tool call or a turn. (A `PreToolUse` hook on `Bash` runs before *every* shell command.)
- **Self-filtering:** if it only cares about a sub-case (e.g. `git push`), it returns immediately
  for everything else — no latency on unrelated calls.
- **Disposable kill-switch header (Q-0105):** *why* it was added, the date, "unverified — confirm
  over a few sessions," and "delete this if it proves noisy/unreliable." A convenience hook is
  removable, not load-bearing.
- **Paired test:** a hook with logic gets a `tests/unit/scripts/test_*.py` (the repo convention).

## Decision tree

```
A recurring problem needs a durable fix. Where does it go?

1. Must it happen AUTOMATICALLY at a lifecycle moment, with no judgment at fire-time,
   and is "the agent forgot" the failure mode?
   ├─ YES → is there a matching event (PreToolUse/PostToolUse/Stop/SessionStart)?
   │         ├─ YES → HOOK (calls a checker/script if the logic is non-trivial). Apply the
   │         │         five-part test + quality bar above.
   │         └─ NO  → no event fits → CLAUDE.md RULE + a CHECKER it can run.
   └─ NO ↓
2. Is it a verifiable PASS/FAIL condition? → CHECKER (scripts/check_*.py); wire into CI
   and/or have a hook call it. (Enforcement ≠ trigger: the checker verifies, CI/hook fires it.)
3. Is it a principle / needs judgment / is context-dependent? → CLAUDE.md RULE
   (propose via a router Q-block unless owner-directed in-session).
4. Is it permissions / env / enabled-MCP configuration? → settings.json CONFIG (non-hook).
5. Is it knowledge to look up for a task? → DOC (on the right read-path; keep it reachable).
```

Note the **common composite**: a single concern often spans layers — e.g. *"services must not
import views"* is a **rule** (CLAUDE.md), enforced by a **checker** (`check_architecture.py`),
gated in **CI**. The mechanisms compose; "is it a hook?" is only the *automatic-trigger* question.

## Worked examples (from this repo)

| Concern | Mechanism | Why |
|---|---|---|
| Auto-format every edit | **Hook** (`claude_post_edit.py`, PostToolUse) | automatic, mechanizable, recurring, every edit; agent would forget |
| Warn when the branch is stale before/after pushing | **Hook** (`check_branch_freshness.py`, PreToolUse+Stop; Q-0138) | event-anchored, advisory, recurring; webhooks don't deliver it |
| Build the CodeGraph index at boot | **Hook** (`claude_session_start.sh`, SessionStart) | must run automatically at session start |
| Layer-boundary violations | **Checker** (`check_architecture.py`) + CI | verifiable pass/fail; no lifecycle trigger of its own |
| "Open a PR every session, born-red → green" | **CLAUDE.md rule** (+ `check_session_gate.py` checker) | needs judgment on scope/timing; the checker only gates the card |
| Which Bash/MCP calls are allowed | **settings.json config** | pure permissions configuration |
| How to scope a review unit | **Doc** (`repo-review-map.md`) | knowledge consulted per task |

## When you're unsure
Default to the **least automatic** mechanism that works: a doc or a checker is cheaper to remove
than a hook, and a hook is the only one that taxes *every* event. Escalate to a hook only when the
five-part test is unambiguous — and remember it's owner-territory (Q-0106): propose unless directed.
