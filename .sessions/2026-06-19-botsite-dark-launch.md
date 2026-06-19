# 2026-06-19 — Stand up the public bot site DARK on Railway (owner-delegated)

> **Status:** `complete`

Owner-delegated unattended task ("wire the website … you have my Railway account token, full
permissions … I'll see what happened when I wake up"). Executed the website-split **rollout step 2 —
stand the bot site up dark**: created its Railway service, deployed from `main`, verified it serves,
and recorded the live facts in the canonical homes. Deliberately stopped at the documented owner gate
(submissions DB + secrets + domain) rather than touch secrets/DB unattended.

## What was done
- **Verified the delegated token before acting** (the session's own ground-truth rule): the
  `RAILWAY_API_KEY` is a real **account** token (`me` → `mennovanhattum@gmail.com`), Railway's API is
  reachable, and `botsite/` is fully on `origin/main` (all build files) — so a `main`-tracking service
  builds the current code.
- **Created the `botsite` Railway service configured-first** (so the first build ran from the right
  folder, not repo root): bare `serviceCreate` → `serviceInstanceUpdate` (Root Dir = `botsite`, start =
  `uvicorn app:app …`) → `serviceConnect` (`menno420/superbot` @ `main`) → auto-build → **SUCCESS** →
  `serviceDomainCreate` (port 8080, the `${PORT:-8080}` fallback the dashboard also uses).
- **Secret-free / dormant** (the §4.4 public posture, by construction): the service carries only
  Railway's auto-injected `RAILWAY_*` — no DSN, no OAuth, no tokens. (Confirmed the dashboard has no
  submissions DSN either → the submissions DB is genuinely unprovisioned; nothing to "move.")
- **Verified live in prod:** `/ /commands /features /changelog /status /submit /healthz` all **HTTP
  200**; `/submit` shows the **dormant** "temporarily unavailable" state. Public URL:
  **https://botsite-production-1ea7.up.railway.app**.
- **Recorded durably** in the canonical homes (not the contended `current-state.md` mega-block — the
  PR is benign-lag past the #1140 marker, so the next recon pass logs it): `botsite-deploy.md` ▶ Live
  status block + the `website-split-next-steps.md` §2b rollout checklist ticks.

## Decisions recorded
None new (no router Q). This is an **ops execution of the already-decided** plan (Q-0178 / website
two-site-split §6) — not a new decision. **No CLAUDE.md / hooks / settings edits** (Q-0106 respected).
**Owner-delegated, not self-initiated** (Q-0172 n/a) — the maintainer explicitly asked for it.

## Stopped at the owner gate — on purpose
Did **not** provision the submissions Postgres / create the INSERT-only role / set `SUBMISSIONS_DB_DSN`
/ cut over a domain. Those are rollout steps 3–4 (`botsite-deploy.md`), and they create a
least-privilege DB role + put a secret on a service — security-sensitive + irreversible-ish work that
the design explicitly defers to the owner. The site is fully functional **except** intake (which fails
safe). Lighting up `/submit` is one clean owner/next-session step (provision DB → grant INSERT-only →
set DSN). I can do it on request.

## Left open / next session (all owner-paced)
1. Submissions DB + `SUBMISSIONS_DB_DSN` (INSERT-only) → lights up `/submit`.
2. Dev-site env (`GITHUB_ISSUE_MIRROR_TOKEN`, full DSN) → end-to-end submit→moderate→mirror.
3. Marketing-domain cutover (Q-0178 defers to cutover).

## 💡 Session idea (Q-0089)
**`scripts/check_deploy_liveness.py`** — read the URL(s) recorded in `botsite-deploy.md` ▶ Live status
(and the dashboard's) and curl `/healthz`, reporting up/down. This session exposed the gap it would
close: the bot site was **code-complete + reviewed since ~#1119/#1122 but never deployed**, and nothing
made "shipped to `main`" vs "live in prod" visibly diverge — so the ledger kept framing the *build* as
the next step when the real remaining step was *rollout*. A mechanical liveness check turns "is the
website actually live?" from tribal knowledge into one command. Disposable Q-0105 dev tool (stdlib +
network-gated, skip when offline).

## ⟲ Previous-session review (Q-0102)
The predecessor (#1140 recon-trigger + voice pack) did its job well — the directive it planted **worked
end-to-end**: the band-#1140 recon pass (#1142) ran tonight, routed Q-0182–Q-0185, and promoted two
buildable plans. What it (and the whole chain) **missed**: no session noticed the website was sitting
*code-complete-but-dark* — the un-deployed state was invisible because "merged to main" was treated as
"done." **System improvement:** make deploy-liveness a first-class, checkable signal (the session idea
above) so a finished-but-unshipped service can't hide behind a green ledger again. This is the same
"pair every truth-claim with a check" through-line the recent tooling sessions have been building.

## 📋 Doc audit (Q-0104)
- Deploy facts recorded in their canonical home (`botsite-deploy.md`) + the rollout tracker
  (`website-split-next-steps.md`) — both already reachable; no new orphan docs.
- `current-state.md` intentionally **not** edited: the new PR is newer than the `#1140` reconciliation
  marker → **benign lag** by the ledger checker's own rule; the next recon pass records it (avoids
  racing the live routines on the contended mega-block).
- `check_docs --strict` + `check_quality --check-only` green before the badge flip.
