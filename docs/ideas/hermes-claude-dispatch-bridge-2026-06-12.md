# Idea: Hermes → Claude Code (web) dispatch bridge

> **Status:** `ideas`. **Not approved for implementation.** Capture only — a Q-block
> discussion is the gate (see Routing). Source code and the binding contracts win over
> anything here.

**Captured:** 2026-06-12 (session idea, Q-0089) · **Owning area:** agent workflow /
control plane (not the bot runtime).

## The idea

Hermes can already *prepare* a structured Claude Code prompt from a spoken idea
(`superbot-prompt-builder`). The missing link is **dispatch**: the maintainer still has
to open a Claude Code session and paste the prompt by hand.

If Hermes could **trigger a Claude Code-on-the-web session from Telegram** — via the web
trigger / session API documented at https://code.claude.com/docs/en/claude-code-on-the-web
— the full loop closes:

```text
idea on your phone
  → Hermes orients (session-brief / prompt-builder, read-only)
  → Hermes dispatches a Claude Code web session with that prompt
  → Claude Code builds, tests, opens a draft PR, self-merges on green CI
  → Hermes reports the result back to Telegram (repo-health / log-triage)
```

That is the "nearly fully autonomous from anywhere" the maintainer is after — and it
**preserves the safety split**: Hermes stays read-only (it decides and dispatches; it does
not edit code), and Claude Code does the mutation under the existing CI / draft-PR /
self-merge gates. No new write power is granted to the always-on agent.

## What it would need (research, not yet decided)

- The Claude Code web trigger/session API surface: how a session is started
  programmatically, what auth it needs, and whether a token can live safely on the VPS.
- A thin Hermes skill (`superbot-dispatch`) or tool wrapper that posts the prompt + repo +
  branch and returns the session/PR link.
- A guardrail: Hermes dispatches but the resulting PR still goes through CI + self-merge
  rules; the maintainer can cap what kinds of tasks may be auto-dispatched vs. require a
  confirm.

## Routing

**Discuss first** — this grants the always-on agent the ability to *start work*, which is
an autonomy/safety boundary and depends on an external API surface. Open a router Q-block
before any implementation. Until then this is the headline next lever for the autonomous
loop and pairs with the installed skill pack + operating prompt shipped 2026-06-12
(PR #730).
