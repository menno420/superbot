# Session — 2026-07-12 — owner-queue execution + fleet workflow management

> **Status:** `complete`
> **Branch:** `claude/multi-repo-workflow-setup-qwhu5j` · **PR:** #2043
> **Venue:** owner-live chat (remote container). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** owner-live follow-up to the fleet-drive session. The owner granted this session his
> Railway API key, GitHub PAT, and bot tokens — so the standing "owner-action queue" was executed
> directly instead of parked. Canonical live queue afterwards: **fleet-manager
> `docs/owner-queue.md`** (reconciled by fleet-manager PR #125).

## What this session executed (cross-repo, owner-live)

1. **Websites `ANTHROPIC_API_KEY` (queue #4) — DONE.** Set on BOTH review services: the LIVE
   `reliable-grace`/review serving review-production-f027 (owner-approved by name; service
   redeployed, 200 verified) and the parallel `superbot-websites`/review. The on-site AI
   assistant (ORDER 019 §B) has its key; the order carries a pre-cleared note.
2. **Both work orders delivered (queue #5) — DONE, no pasting needed.** fleet-manager
   `control/inbox.md` **ORDER 019** (websites review-site refresh/AI/homepage) + **ORDER 020**
   (manager per-wake trigger-health check), via fleet-manager PR #125 (merged `0be6a74`).
3. **mineverse (queue #2) — host CREATED, queue item reduced 6 vars → 2 portal steps.** Found the
   real critical path: no web host existed anywhere, and superbot-side FLAG 1 (snapshot relay) +
   FLAG 2 (HMAC write endpoint) are unbuilt. Owner approved the deploy: Railway project
   `superbot-mineverse`, service `web`, domain `https://web-production-97636.up.railway.app`,
   3/6 vars set (fresh `WEB_SESSION_SIGNING_KEY`, `OAUTH_REDIRECT_URI`, `DISCORD_OAUTH_CLIENT_ID`).
   Build failed twice → root causes found + fixed in **mineverse PR #44 (merged)**: Dockerfile —
   stdlib-only repo defeats buildpack detection; `main()` hard-bound 127.0.0.1 → now honors
   `HOST`. **Deployed + verified LIVE:** HTTP 200, `/api/me` reports the designed honest
   degraded state (`auth_configured: false` until the owner's 2 portal steps).
4. **fleet-manager Actions toggle (queue #1) — BRIDGED.** The toggle API is proxy-walled from any
   agent venue (verbatim error recorded). Armed the workflow-documented CCR fallback: routine
   `trig_011LrFY1k5cUHRYH6zwTvPvn` (`50 */2 * * *`, fleet-manager env, fresh-session) lands
   parked roster PRs + refreshes the trigger snapshot, and **self-retires** once the owner click
   lands. Roster freshness no longer depends on the click.
5. **Websites #166's owner errand — DONE (owner-approved by name).** Minted a project-scoped
   Railway token, set as `RAILWAY_TOKEN` on control-plane, redeployed → `/owner/environments`
   live half on.
6. **venture-lab (queue #3) — verified staged, genuinely owner-only.** Zip present, sha256
   matches the queue (`d3ac5f88…eeb0d8`), listing + article ready; the remaining action is the
   marketplace upload itself (external-publish hard rail).
7. **Stale-handoff correction:** websites #160/#161/#166 (the "3 conflicted PRs" for the next
   agent) had ALL already merged ~15:20Z via the auto-merge-enabler — no work existed. Verified
   live before acting (Q-0120 instinct).

## Fleet workflow findings (durable homes)

- **The rescue-venue capability class** (what an owner-live credentialed session can do vs seat
  sessions, with recipes + the walls that hold everywhere) → fleet-manager
  `docs/capabilities.md` § "owner-live credentialed session" (PR #125).
- **Railway project duplication** (websites services in both `reliable-grace` and
  `superbot-websites`; freeze until 07-14, then consolidate) → fleet-manager owner-queue
  `OQ-RAILWAY-PROJECT-SPLIT`.
- **Auto-mode classifier pattern:** destructive/credential ops clear when the owner names the
  specific target — one AskUserQuestion each for the mineverse deploy, live-review key, and the
  Railway token. Plan rescue sessions around explicit naming; never print secret material.
- **superbot owes mineverse FLAG 1 + FLAG 2** (snapshot relay + HMAC write endpoint,
  specs verbatim in mineverse `control/status.md`) — the true remaining blocker for
  test-guild write mode; routed to the S1 bot lane below.

## ⚑ Remaining owner queue (canonical: fleet-manager docs/owner-queue.md)

| # | Action | Slug |
|---|---|---|
| 1 | Discord portal: copy OAuth client secret → Railway `web` var `DISCORD_OAUTH_CLIENT_SECRET`; register redirect URI `https://web-production-97636.up.railway.app/auth/callback` | OQ-MINEVERSE-ENV-VARS |
| 2 | GitHub → Settings → Installations → Railway → add `superbot-mineverse` (auto-deploy) | OQ-RAILWAY-APP-MINEVERSE |
| 3 | venture-lab publish clicks (Gumroad/LS upload + gotcha article) | OQ-VENTURE-PUBLISH-CLICKS / -GOTCHA-ARTICLE |
| 4 | fleet-manager Actions toggle (now non-blocking; retires the bridge routine) | OQ-FM-ACTIONS-PR-PERMISSION |
| 5 | (optional) Matt's EAP interview | — |

## Session enders

- **💡 Session idea (Q-0089):** *A standing "rescue-venue runbook" prompt* — a paste-ready
  session opener that boots an owner-live credentialed session straight into: read fleet-manager
  owner-queue → attempt every item with the capabilities-map recipes → AskUserQuestion per
  classifier-gated item → reconcile the queue. Today proved the venue clears most of the queue;
  the runbook makes it a repeatable ~30-minute ritual instead of an improvised session.
  Dedup-checked: capabilities.md documents the *abilities*; nothing scripts the *ritual*.
- **⟲ Previous-session review (Q-0102):** the fleet-drive session's centralized owner-queue +
  next-agent tasks made this session startable in minutes — the best handoff yet. Two gaps it
  surfaced: (a) its "3 PRs need rebasing" task was already done by the fleet before this session
  started — handoff *tasks* (unlike its queue items) carried no verify-first instruction; the
  next-agent block should say "verify live state before acting" per item (this session's stale
  ~40 minutes were avoided by checking). (b) Its queue item 2 ("provision 6 env vars") named the
  *symptom* — the real path was host-doesn't-exist + FLAG 1/2 unbuilt; queue items should carry
  their critical-path chain, which the fleet-manager six-field grammar already enforces — the
  session-log table format didn't. **Improvement shipped:** the canonical queue pointer now goes
  to fleet-manager owner-queue.md (six-field, slugged) instead of session-log tables.
- **📄 Doc audit (Q-0104):** current-state top block updated (queue → executed state + pointer);
  this log is the durable session record; cross-repo records live in their repos (fleet-manager
  #125: orders + queue + capabilities; mineverse PR: deployability + card). Owner decisions this
  session were live approvals of named actions (deploy, key, token) — recorded here + in the
  fleet-manager queue entries; no new standing policy → no router Q needed. Ledger check run at
  close.
- **⚑ Self-initiated (Q-0172 accountability):** the roster-bridge routine (documented fallback,
  self-retiring) · the mineverse Dockerfile/HOST PR (prerequisite of the approved deploy) · the
  fleet-manager capability-map section · ORDER 019's pre-cleared-key note. Everything else was
  owner-directed or owner-approved by name in-session.
- **🛠 Friction → guard (Q-0194):** the recurring stall classes this session hit are now encoded
  where the next session looks: proxy-walled `/actions/*`+`/rulesets` paths, curl-not-urllib,
  `env -u` for the Railway CLI, classifier-naming pattern → all in fleet-manager
  `docs/capabilities.md` (enforcing home for capability knowledge); stale-handoff class → the
  verify-first line above (proposal for the session-log template, not self-applied to CLAUDE.md).
