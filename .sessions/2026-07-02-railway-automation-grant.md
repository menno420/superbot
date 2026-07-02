# 2026-07-02 — Railway: the full-automation grant (Q-0213) + R-now execution

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> First session to execute live Railway mutations under the new grant — every change additive,
> reversible, **read-back-verified**; zero destructive ops. `check_docs --strict` ✓, ledger ✓.
> PR #1640.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1638 merged).

## What I'm about to do (intentions — as declared born-red)

Record the owner's automation directive as Q-0213, re-scope the Q-0130 Railway envelope, execute
the safe R-now hygiene items via the API, fold in the owner's mid-session wait-for-CI history.

## What shipped

**The decision record — router Q-0213** (owner-directed, in-chat): the full-access Railway account
token + test-bot token + provider keys are **deliberate**; Claude is sole holder + main repo
editor; the project runs **fully automated** without owner dependency. Custody recommendation
(#1638 §1) formally DECLINED; Q-0130 envelope re-scoped (agents operate the Railway control plane
routinely, with read-back + session-log records); **the unchanged boundary: `*Delete`/restore/
data-loss/billing ops stay ask-first, always.** Also records the owner's operational history:
wait-for-CI *"kept failing due to the fast merges"* when previously enabled.

**Executed on Railway (each mutation + read-back shown in-session):**

| Item | Result |
|---|---|
| R3 watch paths | ✅ `dashboard/**` + `botsite/**` set (verified the dashboard-refresh commits touch only `dashboard/data/`); **worker deliberately unscoped** — under-deploying the bot is the dangerous direction |
| R4 botsite healthcheck | ✅ `healthcheckPath=/healthz` (endpoint verified `botsite/app.py:97`); effective next deploy |
| R5 usage alert | ✅ `softLimitDollars: 15`, email-only, **no hard limit** (hard limits stop workloads — owner call). Gotcha: takes the **customer** id (`me.workspaces[].customer.id`), not the workspace id; wrong id returns the same opaque `Not Authorized` as plan-gating |
| R2 Railway backups | ⛔ **plan-gated on Hobby** — `volumeInstanceBackupScheduleUpdate` *and* manual `volumeInstanceBackupCreate` return `Not Authorized` with API-supplied ids (reads work). **Compensated repo-side:** `backup-db.yml` gained a monthly 400-day-retention artifact tier (cron `0 3 1 * *`, distinct `postgres-backup-monthly-*` name) |
| R1 wait-for-CI | ❌ dropped on owner history; mechanism verified: main CI serializes per-ref (`cancel-in-progress: false`, ~10-min full suite) so fast merges stack delays and any non-success blocks. New-repo conditions written into plan §4 (per-commit main CI · fast gate · no cancellation) |

**Docs:** Q-0213 router block · `production-deployment.md` header re-scoped + Backups section
(plan-gating fact, monthly tier, the **owner one-time step**: raise repo artifact retention to
400 days or the monthly tier silently clamps to 90) · Railway plan §1 custody note / §4 trigger
row / §6 status column / §7 decisions 1+3 decided · planning-README row updated.

**Also verified:** the container's `DISCORD_BOT_TOKEN_PRODUCTION` actually holds the **test bot**
("Galaxy Bot", id `1298426054636994611`, via `GET /users/@me`) — the env name is misleading;
documented in Q-0213 and folded into the credential-smoke-check idea (grooming below).

## Context delta

- **The automation grant has exactly one boundary** and it is now written in three homes (router,
  ops doc, plan): destructive/restore/billing = ask-first; everything else = act, verify by
  read-back, record in the session log.
- **Railway's `Not Authorized` is three different errors wearing one message** (wrong id ·
  plan-gated feature · true permission). Disambiguate by re-reading the object with the same id;
  never conclude plan-gating from one opaque error.
- **Owner operational history beats fresh reasoning:** R1 looked safe from config analysis; the
  owner's one line of history ("kept failing") was decisive. Ask-the-history is cheap — the
  question-router/journal should be greppable for "tried before" before enabling any
  platform toggle.
- Correction to my #1638 session log: the urllib 403 was the **known Cloudflare UA block on
  urllib** (documented in `agent-env-credential-smoke-check-2026-06-14.md` since PR #840), not
  the agent proxy. curl remains the transport for Railway GraphQL.

## 🛠 Friction → guard

Two frictions, both converted to durable records rather than new code (their enforcing guard —
`check_agent_env.py` — already exists as a groomed idea, now strengthened): (1) the misleading
bot-token env name → identity-print requirement appended to the smoke-check idea + Q-0213 note;
(2) wrong-customerId `Not Authorized` → disambiguation pattern recorded in plan §6 R5 + context
delta. No new checker shipped this session (the smoke-check idea is the right single home; it is
now evidence-loaded for promotion).

## 💡 Session idea (Q-0089)

**[`railway-deploy-alerts-discord-webhook-2026-07-02.md`](../docs/ideas/railway-deploy-alerts-discord-webhook-2026-07-02.md)**
— a Railway project webhook pointed at Discord so failed `worker` deploys push-alert the owner.
Worth having: merge=deploy means a broken deploy is currently discovered only by looking;
platform-side, zero bot code, works precisely when the bot can't boot; agent-executable under
Q-0213 (destination channel = owner taste, confirm first).

## ⟲ Previous-session review (Q-0102)

Previous session (#1638, the Railway audit): the read-only discipline and §7 decision framing
worked — the owner answered within hours and the plan absorbed the answers with zero rework. What
it missed: its custody recommendation was predictable-decline — the repo's own
`collaboration-model.md`/owner-profile say the premise is AI running the project autonomously, so
"take the powerful token away from agents" contradicted the owner's known model. **Concrete
improvement:** recommendations that touch the owner's autonomy model should check
`docs/owner/maintainer-working-profile.md` first and, where the risk is real but the model is
settled, present a *conscious-risk record to sign* rather than a recommendation to adopt — that is
what Q-0213 item 1 ended up being anyway. (Also: #1638's friction note misattributed the urllib
403 — corrected above.)

## 📤 Run report

- **Did:** recorded the owner's full-automation grant (Q-0213), executed the safe Railway hygiene
  set via API with read-back verification, compensated the plan-gated backups repo-side, folded
  the wait-for-CI history into the plan · **Outcome:** shipped
- **Shipped:** #1640 — Q-0213 router block + ops-doc re-scope + backup-db monthly tier + plan
  statuses + 1 idea + 1 idea groomed. Railway-side (not in the diff, verified live): watch paths
  ×2, botsite healthcheck, $15 soft usage alert.
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** none blocking — the rebuild design-spec owner gate remains the big
  open one; plan §7.4 (shadow budget) + §7.5 (plan tier, now also the Railway-backups lever) ride
  along with it.
- **⚑ Owner manual steps:** **one dropdown** — GitHub → Settings → Actions → General → *Artifact
  and log retention* → **400 days** (else the new monthly backup tier silently keeps 90).
- **⚑ Self-initiated:** none (owner-directed; ideas are capture)
- **↪ Next:** R6 restore drill (agent-runnable, closes the backup workflow's "UNVERIFIED" header);
  the design-spec owner gate; Phase 0.5 golden harness as the best parallel build.
