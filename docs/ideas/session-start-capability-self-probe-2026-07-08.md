# Idea — session-start capability self-probe (know your own toolset before you plan)

> **Status:** `ideas` · raised 2026-07-08 (EAP-email-refresh session) · workflow/infrastructure

## The problem it solves

Multiple EAP findings this program hit came from a session **not knowing its own toolset up front**:
- The standing-grant permission-probe row landed `NOT ATTEMPTED` because the receiving coordinator
  session had **no Bash tool** — discovered only *after* dispatch, from inside the session
  (`projects-eap-permission-probe-report-2026-07-08.md`, standing-grant addendum).
- `send_later` is documented in the coordinator's own instructions but is **absent / rejected on
  call** (evaluation log 2026-07-07) — a phantom tool a session planned around before learning it
  didn't work.

Both are the same failure: a protocol premised on a capability the session doesn't actually have,
caught late and expensively.

## The idea

A tiny **session-start self-probe** — the session records, once, which of a short checklist of
capabilities it actually has (direct Bash/shell, `git` write, GitHub MCP, self-wake timer, sub-agent
spawn, `subagent_type`s available) — and writes the result to a known line (session card / eval log).
Cheap, non-destructive, read-only. Then any dispatch or protocol can check "does the target session
have a shell?" against a real answer instead of an assumption.

## Why it's worth having

- Turns a class of *late, expensive* discoveries into *free, up-front* ones.
- Directly complements the email's ask for spawn-time capability introspection — this is the
  **self-serve** version we can build now, without waiting on Anthropic.
- Generalizes past the EAP: any cloud/CLI/coordinator session type benefits from knowing its own
  envelope before it commits to a plan that needs a tool it lacks.

## Dedup

Distinct from the probe report (which maps the *permission* boundary, not the *toolset*) and from the
"spawn-time capability introspection" email ask (a feature request to Anthropic); this is our own
session-start convention, buildable now.
