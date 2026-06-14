# 2026-06-14 — `auth probe` routine: Railway access unblocked (PR #840)

**Branch:** `claude/sharp-ptolemy-yi8q5t` · **PR:** #840 (fix, auto-merge armed)

## Work order
Routine fired with the free-form payload `auth probe`. Treated as CLASS: fix —
verify the routine can authenticate/operate, and surface/fix whatever's broken.

## What happened
Verified each access path:
- git/repo ✓ · GitHub MCP ✓ (authenticated as `menno420`)
- **Railway ✗ → root-caused two independent blockers, both fixed:**
  1. **Var-name mismatch.** Owner provisioned the credential as `RAILWAY_API_KEY`
     (an account token), but `railway_logs.py`/`railway_vars.py` only read
     `RAILWAY_API_TOKEN`/`RAILWAY_TOKEN`/`RAILWAY_PROJECT_TOKEN` → `No Railway
     token found`. Confirmed token type empirically: rejected as project token
     (`Project Token not found`), valid as account Bearer (`me { email }` =
     owner). Added `RAILWAY_API_KEY` as an account-token alias (explicit
     `RAILWAY_API_TOKEN` still wins).
  2. **Cloudflare WAF.** `backboard.railway.com` 1010-bans urllib's default
     `Python-urllib/X.Y` User-Agent → every call 403'd regardless of token
     (curl/browser UA returns 200, so egress was never the issue). The GraphQL
     transport now sends an explicit non-default User-Agent.

Verified live after the fix: `--whoami` returns the owner identity; `vars list`
reads live prod vars (masked). +5 regression tests; `check_quality --full` green
(9509); arch 0 errors.

## Notes
- **No `PushNotification` / `send_later` tool in this routine env** — consistent
  with the #828/Q-0129 finding. The finding's durable home is PR #840 + the
  current-state verification note (which I updated from "must verify live" to the
  verified outcome). Could not phone-notify; the PR is the notification.
- PR created via MCP; **the `enable-auto-merge` check fired green anyway** (the
  Q-0127 "doesn't fire for MCP PRs" caveat did not bite here), and I also enabled
  auto-merge manually. Subscribed to PR activity.
- PR #840 is a multiple-of-20 boundary, but per **Q-0124** a routine pursuing its
  own work does not run the reconciliation pass — the `reconciliation-trigger`
  workflow will auto-open the `reconcile` issue for the docs-reconciliation routine.

## 💡 Session idea (Q-0089)
`agent-env-credential-smoke-check-2026-06-14.md` — a stdlib `check_agent_env.py`
doing a minimal authenticated round-trip per provisioned external credential,
PASS/SKIP/FAIL at SessionStart. Absence = SKIP, present-but-broken = FAIL. This
exact breakage sat silent until a routine probed by hand; this would flag it on
the first session after provisioning.

## ⟲ Previous-session review (Q-0102)
The #827–#837 Railway-access session built solid, well-guarded tooling
(masking, audit lines, stdin secrets, token-type handling) — genuinely good
work. **What it missed:** it never made a single real call against the live
Railway API from the agent env, so it didn't catch the Cloudflare-UA 1010 block
(a one-call discovery) and it baked in the assumption the owner would use
`RAILWAY_TOKEN`/`RAILWAY_API_TOKEN` rather than confirming the actual var name.
It couldn't fully verify (the owner set the token afterward) — but it *could*
have made one unauthenticated POST to prove the transport survives Cloudflare.
**System improvement it surfaces:** the credential smoke-check idea above —
"tooling is built" and "tooling works against the live endpoint from here" are
different claims, and only the second is what an autonomous agent can rely on.
