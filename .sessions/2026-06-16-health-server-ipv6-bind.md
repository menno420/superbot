# Session — health server IPv6 dual-stack bind (Railway private networking)

> **Status:** `complete`

## Origin

Discovered while wiring up the control panel (#989/#993/#996 + the Railway env vars): the bot's health
server — which now also hosts the **control API** (`/control/*`) — binds **`0.0.0.0` (IPv4 only)**.
**Railway's private network is IPv6-only**, so the decoupled dashboard could never reach the bot at
`worker.railway.internal:8080`; the cross-service call would fail with connection refused. This is the
prerequisite that makes the live editors actually work end-to-end.

## What shipped

- **`disbot/healthserver.py`** — bind host is now `HEALTH_HOST` (default **`::`**), so the health
  server listens IPv6 **dual-stack**: reachable over Railway private networking *and* (via IPv4-mapped
  addresses on Linux) still answers IPv4/local health probes. `web.TCPSite(runner, _HEALTH_HOST, …)` +
  the log line + the module docstring updated.
- **Kill-switch (Q-0105 ethos):** if a runtime ever lacks IPv6, set `HEALTH_HOST=0.0.0.0` — no code
  change, no redeploy-from-revert.
- **`docs/operations/env-vars.md`** regenerated (`HEALTH_HOST` is the 36th variable).

## Why this is safe

`::` on Linux defaults to `IPV6_V6ONLY=0` → one socket serves both stacks, so existing IPv4 probes
keep working. The startup path already surfaces a bind failure (main waits on `bind_ready`); the
`HEALTH_HOST` override is the fallback if `::` is ever unavailable.

## Verification

- `python3.10 scripts/check_quality.py --full` → **green (10273 passed)** — the `test_healthserver.py`
  suite mocks `web.TCPSite`, so the host change is covered without a real socket; env-doc sync test
  passes after regeneration.
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors.
