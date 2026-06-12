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

If Hermes could **trigger a Claude Code session from Telegram**, the full loop closes:

```text
idea on your phone (or a nightly Hermes diagnosis)
  → Hermes orients (session-brief / prompt-builder / log-triage, read-only)
  → Hermes dispatches a Claude Code session with that work order
  → Claude Code builds, tests, opens a PR (merge gated — see below)
  → Hermes reports the result back to Telegram (repo-health / log-triage)
```

That is the "nearly fully autonomous from anywhere" the maintainer is after — and it
**preserves the safety split**: Hermes stays read-only (it decides and dispatches; it does
not edit code), and Claude Code does the mutation under CI gates.

## The concrete mechanism: Claude Code **Routines** (verified 2026-06-12)

The dispatch surface this idea needed already exists — **Routines**
(https://code.claude.com/docs/en/routines): a saved Claude Code config (prompt + repos +
connectors + environment) that runs autonomously in the cloud, with three trigger types:

- **API** — `POST` to a per-routine `/fire` endpoint with a bearer token and an optional
  freeform `text` payload that is passed to the run alongside the saved prompt.
- **Scheduled** — hourly/daily/weekly/cron (min interval 1h) or a one-off future time.
- **GitHub** — `pull_request.*` and `release.*` events only (NOT issues/pushes/comments),
  with filters on author/title/body/branch/labels/draft/merged.

**Recommended wiring — API trigger.** Hermes (already an HTTP-capable agent on the VPS)
`POST`s the diagnosed work order as `text` to the routine's `/fire` endpoint; the routine
session implements it and opens a `claude/` PR. This is Anthropic's own documented "Alert
triage" pattern (a monitoring tool POSTs an alert body → routine opens a draft PR with a
fix), and it means **Hermes never needs repo write access** — it just sends text. Token
lives in the VPS secret store.

**Alternative — GitHub-PR trigger (the maintainer's original framing).** Hermes opens a
docs-only / work-order PR (branch `hermes/orders-*` or label `claude-continue`); a routine
with a filtered `pull_request.opened` trigger continues the work. Viable but costs more: it
requires graduating Hermes from read-only to "can open a PR", and the hand-off must be a PR
(GitHub triggers don't fire on issues/comments).

**Note:** the "highest-value docs fix" / "new idea" half can also be a *pure scheduled
routine* (no Hermes) — the documented "Docs drift" / "Backlog maintenance" patterns. Hermes
adds the mobile, human-in-the-loop diagnosis + dispatch layer on top.

## Open decisions (why this is discuss-lane, not build-now)

1. **Routines run with no mid-run approval** and can use any included connector's write
   tools. Guardrails = the prompt, the environment network policy, the included connectors,
   and the branch-push setting (keep the default `claude/`-only). Each must be scoped tight.
2. **Self-merge gating** — this repo lets an interactive Claude *session* self-merge on
   green CI; a *routine* doing it fully unattended is a bigger step. Proposal: routine
   **opens** the PR (CI runs), but merge stays behind green-CI + docs-only/test-covered
   rules, or a one-tap Telegram confirm via Hermes — keeping the maintainer on the
   irreversible step.
3. Routines act as the maintainer's identity, draw down a daily run cap, and are research
   preview (API behind a dated beta header).

## Routing

**Discuss first (router Q-block)** — turning this on is an autonomy/safety-boundary
decision for the maintainer (decisions 1–3 above), not an agent call. The mechanism is now
verified and concrete, so the discussion can be a yes/no on scope rather than research.
Headline next lever for the autonomous loop; pairs with the installed skill pack +
operating prompt shipped 2026-06-12 (PR #730).
