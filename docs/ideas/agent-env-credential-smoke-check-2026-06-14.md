# Idea: agent-env external-credential smoke check (preflight)

> **Status:** `ideas` — capture only, **not** a plan and **not** approval for
> implementation. Source code and the binding contracts win over this file.

**Captured:** 2026-06-14 · **Source:** the `auth probe` routine that fixed the
Railway access (PR #840) · **Lane:** small / decided — implementable

## The problem it solves

The owner provisioned Railway credentials in the agent environment, and the
access was **completely inert for two independent reasons** — a var-name mismatch
(`RAILWAY_API_KEY` vs the `RAILWAY_API_TOKEN`/`RAILWAY_TOKEN` the scripts read)
and a Cloudflare UA block on urllib — yet **nothing surfaced it**. It only came
to light because a routine happened to fire with an `auth probe` work order and
ran the verification by hand. A different session would have hit
`No Railway token found` mid-task and assumed access simply wasn't granted.

The general failure class: **provisioned external-access credentials are never
verified end-to-end against the live endpoint**, so a wrong var name, an expired
token, a network/WAF block, or a transport bug stays silent until an agent needs
it under time pressure.

## The idea

A single `scripts/check_agent_env.py` (stdlib-only, fast, read-only) that, for
each optional external integration the env *claims* to provide, does the minimal
authenticated round-trip and prints a one-line PASS/SKIP/FAIL:

- **Railway** — if any `RAILWAY_*` token var is set, run the existing
  `railway_logs.py --whoami` (account) or a `vars list` (project) and report.
- **Anthropic / OpenAI** — if a key is set, a cheap models-list call.
- **Discord** — token presence + shape (no live gateway needed).

Key properties:
- **SKIP, never FAIL, when a var is absent** — absence is a valid config, only a
  *present-but-broken* credential is a failure.
- Surfaced at **SessionStart** as a one-line banner (`env: railway ✓ · anthropic ✓
  · openai SKIP`) so every session knows its real capabilities up front, and a
  routine can notify on a FAIL.
- Reuses the per-integration probes already written (the `--whoami` path here).

## Why it's worth having

It converts "silently broken until someone trips over it" into "flagged on the
first session after provisioning." It's the env-level sibling of the
control-plane state ledger in `operations/autonomous-routines.md`, and it would
have caught both PR #840 bugs the moment the owner set the var.

## Size / route

Small. One stdlib script + a SessionStart hook line + a few probe adapters.
Could grow into the `node_roles`-style "what can this session actually do?"
self-report. Groom into a tooling PR when the external-integration surface grows
past Railway.

## Evidence update (2026-07-02, Railway automation-grant session)

Two fresh instances of the failure class, both hit live:

1. **Identity, not just reachability:** the agent-container var `DISCORD_BOT_TOKEN_PRODUCTION`
   actually holds the **test bot** ("Galaxy Bot", id `1298426054636994611`) — verified via
   `GET /users/@me`. An agent trusting the name could act believing it holds the production
   bot. The smoke check should therefore print the **authenticated identity** (bot username /
   Railway account email / GH login) per credential, not merely PASS/FAIL.
2. The urllib-Cloudflare block recurred (Railway GraphQL 403 via urllib, fine via curl) and was
   re-diagnosed from scratch before finding this idea file — a shipped `check_agent_env.py`
   with its curl-based probes would have made that a non-event. (Also: Railway's API returns
   the same opaque `Not Authorized` for wrong-id, plan-gated, and permission failures — the
   probe's read-back pattern disambiguates.)
