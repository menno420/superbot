# Security Policy

## Supported versions

SuperBot is **continuously deployed** from `main` (a merge to `main` auto-deploys to
the production Railway service). There are no release branches or version tags, so the
**only supported version is the currently-deployed `main`**. Fixes land on `main` and
deploy from there.

| Version | Supported |
|---|---|
| `main` (deployed) | ✅ |
| anything else | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Report privately, one of:

1. **GitHub private vulnerability reporting** — the repository's **Security → Report a
   vulnerability** tab (preferred; keeps the report and fix coordinated in one place).
2. **Email** — `mennovanhattum@gmail.com` with `[SuperBot security]` in the subject.

Please include: a description, the affected component/path, reproduction steps or a PoC,
and the impact you observed. We aim to acknowledge within **5 working days** and to
coordinate disclosure once a fix is deployed. There is no paid bug-bounty program.

## Scope

In scope:

- The **bot runtime** (`disbot/`) — commands, services, the audited mutation seams.
- The **private control API** (`disbot/control_api.py`) and **health server**
  (`disbot/healthserver.py`).
- The **developer dashboard** (`dashboard/`) — auth, session cookie, control-API client.
- **CI/CD workflows** (`.github/workflows/`) and how secrets are handled.

Out of scope: vulnerabilities in third-party platforms (Discord, Railway, OpenAI/Anthropic
APIs) themselves; findings that require a compromised maintainer machine or an already-leaked
`CONTROL_API_TOKEN`; volumetric/DoS reports without a concrete amplification vector.

## Current security posture (defense-in-depth)

For context when assessing a report, the design already assumes a hostile network:

- The **control API is dormant by default** — its `/control/*` surface registers **only**
  when `CONTROL_API_TOKEN` is set, and is intended for a **private network** path.
- Every control request must present a **bearer token**; writes pass through a
  **sliding-window rate limiter**, and the **bot re-resolves the acting user via Discord**
  before any mutation — the bot, not the API caller, remains the authority. Every mutation
  flows through the existing **audited service seam** (`services/*_mutation.py` +
  `services.audit_events.emit_audit_action()`).
- **Secrets are environment variables** (Railway-managed) and are never committed; the
  dashboard session is a stdlib **HMAC-signed cookie**.

Hardening still on the roadmap (request signing / HMAC + timestamp, idempotency keys on
writes, token rotation) is tracked in
`docs/planning/repo-structure-improvement-plan-2026-06-19.md` and router **Q-0177**.
