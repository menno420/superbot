# Session — 2026-07-12 — email finalization → fleet-drive → websites backlog

> **Status:** `complete`
> **Branch:** `claude/session-close-2026-07-12-fleet-drive` (close-out; work spanned several branches)
> **Venue:** owner-live chat (remote container). **Model:** Opus 4.8 family.
> **Scope:** long owner-live session — shipped the 2nd Anthropic email, then drove the fleet
> (cross-repo PR merges, root-cause fixes) with the owner live-authorizing.

## What this session delivered (in order)

1. **The 2nd Anthropic EAP email — finalized + SENT** (owner sent 2026-07-12 13:24Z, msg
   `19f568051da9e3d6`, reply on July 8 thread `19f41cd2e5380bb3`, To `claude-code-early-access@`,
   cc `dliu@`/`omid@`/`mattg@`). Staged as a clean Gmail draft (scaffolding stripped, owner's
   Part 1 verbatim); owner sent with final tweaks + the figure gallery linked instead of attachments.
   PRs: #2032 (staged pointer) · #2034 (SENT state). Gallery: #2033, then **#2038 fixed the image
   links** (relative → full `blob/main/...?raw=true` URLs — they were routing to the repo root).
2. **Two owner work-orders written + merged** (paste-in for the target Projects):
   - Websites review-site refresh + on-site AI assistant + homepage → `docs/owner/websites-review-site-order-2026-07-12.md` (#2035).
   - Project-Manager trigger-health check (per-wake WEDGED/DROPPED/DEAD detection) → `docs/owner/trigger-health-order-2026-07-12.md` (#2037).
3. **Fleet PR drive (owner live-authorized merges across repos):**
   - **superbot-mineverse #42** — login-CSRF security fix merged → the Games **flagship's last
     admission gate is cleared** (owner can now provision the 6 OAuth secrets to go live).
   - **fleet-manager #113** (midday sweep) merged; **#117** merged to **land a fresh roster**
     (the roster was 5.6h stale, red-gating every manager-authored PR).
   - **websites — 11 of 14 non-draft PRs merged** (#167 auto-merge-enabler, #165, #173, #179,
     #159, #175, #174, #170, #168, #172, #176). The review-site refresh (order-017: #175 data +
     #174 AI assistant + #172 control) and tester-recruitment (order-018: #176/#179) all landed.
4. **Two systemic root-causes found + fixed:**
   - **fleet-manager roster-regen fails every run** — the workflow regenerates + force-pushes to
     `bot/roster-regen` fine, but `gh pr create` is **denied** because "Allow GitHub Actions to
     create and approve PRs" is OFF (`OQ-FM-ACTIONS-PR-PERMISSION`). So the roster never lands and
     goes stale, red-gating the repo. Worked around via #117; **permanent fix is the owner toggle**.
   - **websites "stuck merges"** = branch protection **"Require branches up to date"** ON + no
     merge queue → serial cascade (only one PR merges per main-tip; the rest fall behind; agents
     can't clear it). **Owner removed the rule mid-session** → the backlog then cleared in one pass.

## Live EAP data points captured this session (worth folding into the EAP thread)

- **Auto-mode classifier requires the *specific target named* for a destructive op.** A general
  "yes, delete branches" did NOT clear a branch delete; verbatim: *"[Git Destructive] … the user
  encouraged branch deletion generally but did not name this specific branch as the target —
  clears only if the user names the destructive operation and the exact branch."* It cleared the
  instant the owner named `menno420-patch-1` explicitly. (Owner also offered a PAT-workaround; the
  agent declined to route around the guard's intent — held the line until the specific
  authorization was given. Clean positive example of the permission model.)
- **Closing a PR + deleting its branch does NOT purge exposed files** — `refs/pull/51/head` still
  resolves after branch deletion, so a closed PR's diff/blobs stay public. Full purge needs repo-
  private or GitHub Support (a pull ref can't be deleted by owner or agent).
- **"Require up-to-date branches" without a merge queue is a project-stalling anti-pattern at
  fleet velocity** — with a stack of green PRs, only one merges per main-tip and the rest re-fall-
  behind; the agents literally cannot drain it. This is a strong native-merge-queue ask.

## ⚑ OWNER-ACTION QUEUE (pending — centralized for the next session)

| # | Action | Unblocks | Where |
|---|---|---|---|
| 1 | **fleet-manager:** enable "Allow GitHub Actions to create and approve pull requests" | roster-regen self-lands forever (stops the recurring stale-roster red-gate) | fleet-manager → Settings → Actions → General |
| 2 | **mineverse:** provision the 6 OAuth/write env vars | the Games flagship goes live (CSRF fix #42 is merged) | mineverse Railway/env |
| 3 | **venture-lab:** publish the $29 Stripe Test Kit (Owner Launch Hour) + post one distribution channel | first external revenue | upload `dist/stripe-webhook-test-kit-v0.1.zip` to Gumroad/Lemon Squeezy; post `gotcha-article.md` |
| 4 | **websites:** add `ANTHROPIC_API_KEY` secret to the review service | the on-site AI review assistant (order-017 B, merged) actually runs | websites Railway/env |
| 5 | Paste the two orders into their Projects | review-site upgrade + trigger-health check execute | Websites chat / Project-Manager chat (or fleet-manager `control/inbox.md`) |
| 6 | (optional) Matt's 10–15 min EAP interview | concept-fit half of the feedback | listenlabs link in his 2026-07-10 mail |

## ▶ NEXT-AGENT TASKS (things I could NOT finish)

- **websites: 3 PRs have genuine merge conflicts and need rebasing** (real conflict resolution,
  best done by the websites lane which knows the code): **#160** (order-012 records-reconcile),
  **#161** (order-014 arcade slice-1), **#166** (order-015 owner-environments). #163 is a draft
  session card (leave). Route these to the websites Project or resolve by clone+rebase per-PR.
- **fleet-manager:** #116 is a by-design born-red HOLD (its own session flips it). Nothing to do.

## Session enders

- **💡 Session idea (Q-0089):** *A `docs/owner/OWNER-QUEUE.md` single-source owner-action ledger,
  generated/aggregated across the fleet.* This session produced a 6-item owner-action queue that
  currently lives only in this log; the fleet-manager already has a roster/owner-queue candidate
  feed, and the websites "Owner Launch Console" order targets exactly this. One canonical, always-
  current owner-action list (per-repo clicks/keys/toggles, each with a deep link + what it
  unblocks) is the highest-leverage "clear overview" artifact — the maintainer's recurring pain is
  *"which of my N projects is waiting on me and for what."* Dedup-checked: the Owner Launch Console
  (websites) + fleet-manager owner-queue-candidates are adjacent; the new bit is *cross-repo
  aggregation into one owner-facing screen/file*. Worth building next.
- **⟲ Previous-session review (Q-0102):** the 2026-07-12 close-out (PR #2031) set up the email
  finalization beautifully — the `▶▶ TOP PRIORITY` banner + step-by-step handoff meant this
  session shipped the email in minutes. **System improvement it surfaces:** the handoff assumed
  the email work was self-contained, but this session cascaded into a multi-repo fleet drive that
  needed 4 repos added mid-session (`add_repo`) and hit cross-repo merge walls the superbot docs
  couldn't see. The fleet lacks a *cross-repo* live-state surface an agent can read at boot — the
  session idea above (aggregated owner-queue) is half of it; a machine-readable cross-repo PR/CI
  status roll-up (the fleet-manager roster is trying to be this, but it was itself stale-gated all
  session) is the other half. The recurring theme all session: **the truth is spread across N
  repos and no single surface shows it** — that is the thing to centralize.
- **📄 Doc audit (Q-0104):** current-state top pointer updated with the fleet-drive summary +
  owner-action queue; this log is the durable home for the cross-repo work. Ledger check run
  pre-push. No new owner *decisions* to route (the changes were owner-directed execution, not
  policy). New docs reachable via current-state.
- **⚑ Self-initiated:** none — every action was owner-directed in-session (email, orders, the
  cross-repo merges, the branch delete, the roster fix, the websites backlog).
