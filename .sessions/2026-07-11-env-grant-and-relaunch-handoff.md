# 2026-07-11 — Env-grant docs + live-env-visibility plan + RELAUNCH/TRIAGE handoff

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed hub session (fleet management) · afternoon/evening

## ▶ NEXT SESSION — START HERE (relaunch + fleet triage)

**The next session's job, in the owner's words:** review the Codex results, **make a
plan to get all the projects running again**, and **decide which projects are worth
keeping vs replacing** — plus check **which repos are still valuable to maintain vs
should be superseded or repurposed.** This is a *planning + triage* session, not a build
session. Produce a decision-ready plan; the owner rules on it at the gate.

**What's freshly true (don't re-derive):**
- **The owner updated the setup scripts + env values for the 5 consolidated
  environments** (the archetypes: python-lab · pinned-research · bot-prod ·
  coordinator · gba-lab). So the env layer is now correctly configured — projects are
  *ready to relaunch*, no longer blocked on broken startup scripts.
- **Env docs are complete + merged:** `fleet-manager/environments/archetypes.md`
  (name mapping, ORDER 018 consolidation) + **new** `env-grant-policy.md` (fm PR #78 —
  trust tiers, per-lane templates, "where to manage each" links). These are the
  reference for what each project's env should carry.
- **4 Codex prompts were dispatched by the owner** (superbot-next, venture-lab,
  superbot-mineverse, substrate-kit; prompts at `docs/owner/codex-review-prompts-2026-07-11.md`).
  **Results are the first input to the triage** — the owner reviews them next chat; use
  "review this report" (DOC-mode of `/fleet-review`) to verify each finding against
  source (Q-0120) before acting.
- **The Anthropic review site is LIVE** at `https://review-production-fc91.up.railway.app`
  (I deployed it via the Railway API this session — new `review` service in the
  `superbot-websites` project, mirrors the other three). Email #2 is draft-complete and
  owner-blocked (send before **Tue 7/14** + apply Part 1 typos + attach 4 phone shots).

**A triage scaffold to build the plan on** (raw material — the next session decides):
| Lane / repo | Current state | Triage lens |
|---|---|---|
| superbot (prod bot) | live on Railway (`reliable-grace`/`worker`) | KEEP — the oracle + production |
| superbot-next | 37/49 ported, non-game map complete | KEEP — the rebuild; nearing cutover territory |
| substrate-kit | v1.11.0, 7 adopters | KEEP — the real artifact |
| fleet-manager | manager repo, live | KEEP — coordination substrate |
| websites | 4 services live (control-plane/botsite/dashboard/**review**) | KEEP — being put back to work (repo-coverage lag + the live-env-visibility feature, PR #143) |
| venture-lab | 3 launch-ready products, owner-click-gated | KEEP — first-revenue; Codex pre-publish review pending |
| superbot-games / superbot-idle / superbot-mineverse | engines built, gated on the plugin contract | KEEP but SEQUENCE — need `superbot-plugin-hello` seeded + the contract shipped in superbot-next |
| gba-homebrew | Lumen Drift v1.3 shipped | KEEP (low-maintenance) — publish decision is owner's |
| pokemon-mod-lab | QoL+ mod, PRIVATE, idle | KEEP but PARKED — playtest-gated; never public |
| trading-strategy | program complete, paper lane running | KEEP-as-is — mostly autonomous; low touch |
| sim-lab / idea-engine / product-forge | process lanes, live | KEEP — the idea→evidence→build loop |
| codetool-lab ×3 (fable5/opus4.8/sonnet5) | wound-down, STALE-BY-DESIGN ~2 days | **ARCHIVE / REPURPOSE candidates** — the clearest triage targets; finished CLIs, no active mission |
| superbot-plugin-hello | EMPTY public repo | **SEED or DROP** — blocks the games lanes; seed package sits in superbot-next `examples/` (one owner word: "push the plugin seed") |
| mobile-lab | held/unlaunched JS lane | **DECIDE** — launch or drop; only JS lane |

**Open owner-action queue (the short "only you" list):**
1. **Send Anthropic email #2 before 7/14** + Matt's interview (top item).
2. **Review the 4 Codex reports** (feeds the triage).
3. Revenue sitting: Stripe test keys → publish venture-lab's 3 products.
4. "push the plugin seed" (one word → unblocks the games lanes).
5. The values-vs-names decision for the live-env-visibility feature (websites #143).
6. Relaunch the fleet routines (the whole point of next session) — the envs are ready.

## What this session shipped (all merged unless noted)

- **fleet-manager #78 (merged):** `environments/env-grant-policy.md` — trust-tier
  authorization model + per-lane paste templates + "where to manage each" console links;
  cross-linked from archetypes.md.
- **websites #143 (auto-merging):** `docs/planning/live-env-visibility-plan-2026-07-11.md`
  — revives the deferred live-Railway-read half of the env surface: a gated
  `/owner/environments` page loading Railway variables via a **project-scoped** token +
  per-var manage-links. One owner decision flagged (values vs names+status).
- **websites #132 (merged) + the `review` service DEPLOYED live** — the Anthropic
  review site.
- **websites #137, superbot-games #34/#36/#38/#46/#47/#48/#32/#27, substrate-kit #217
  (all merged):** fleet PR-hygiene backlog cleared.
- **superbot #1996 (merged):** refreshed Codex prompt 1 numbers.
- **Earlier in the session (merged #1990/#1992/#1993/#1994):** the 4 Codex prompts doc,
  the product catalog (`docs/owner/product-catalog.md`), the generalized `review`
  vocab/skill, and the email-2 draft + fig-19.

## Key durable findings (carry forward)

1. **Live human context IS the permission.** Confirmed both sides this session: merges +
   the Railway service creation cleared the classifier only under the owner's live,
   specific, in-chat authorization; a general "you can do those" was denied until named.
2. **Account Railway token = keys to the prod bot.** `reliable-grace`/`worker` is the
   live bot; the account `RAILWAY_API_KEY` + production IDs reach it. The safe pattern
   (documented in env-grant-policy.md) is **project-scoped tokens** per lane.
3. **codetool-labs are the cleanest archive candidates** — wound-down, finished, no mission.
4. **The games lanes are all blocked on one thing:** the plugin contract + a seeded
   `superbot-plugin-hello` (empty repo; package ready in superbot-next examples/).

## Session mechanics for the next session

- A fresh session starts scoped to `superbot` only — re-`add_repo` the fleet lanes as
  needed (they're not in default scope).
- "review" → `/fleet-review` dispatcher (fleet / repo / doc / prompt). For the Codex
  reports: "review this report" = DOC mode, verifies claims against source first.
- This hub session CAN merge normally; Project sessions hit the classifier wall.
- Railway account token lives in `RAILWAY_API_KEY` (env); the `superbot-websites`
  project is `70198ece…`, the **production bot** project is `reliable-grace` `285dfbcd…`
  (never mutate it).

## 💡 Session idea (Q-0089)

**A fleet "keep / replace / repurpose" register** — a single living doc
(`fleet-manager/docs/fleet-triage.md`) with one row per repo: mission · last-shipped ·
maintenance cost · verdict (KEEP / ARCHIVE / REPURPOSE / SEQUENCE) · rationale.
Tonight's handoff scaffold is the seed; the next session's triage should *land* its
decisions there rather than in chat, so "which repos still earn their keep" becomes a
standing, re-reviewable ledger instead of a one-time call. Distinct from the roster
(freshness) and product-catalog (what each is) — this is the *should-it-exist* lens.
(Dedup-checked: neither the roster, the product catalog, nor archetypes.md carries a
lifecycle/keep-verdict column.)

## ⟲ Previous-session review (Q-0102)

The prior turn (env-grant policy + live-env-visibility plan) did the research well —
it *found* that the env-visibility "lost function" was a deliberate deferral, not a
bug, which saved the next session from re-hunting. What it could have done better:
it opened three PRs across three repos in quick succession, which is more PR churn
than necessary — the env-grant policy (fleet-manager) and its website-feature spec
(websites) are tightly coupled and a reader now has to cross two repos to see one idea.
**Workflow improvement:** when a single owner idea spans repos, lead with the
source-of-truth doc and make the others thin pointers (which I did — the websites spec
points at env-grant-policy.md rather than restating it), but consider whether the
pointer-target should live in the repo the owner actually reads first. No fix needed
this session; noting it as a cross-repo-doc-locality question for the triage session,
which will touch exactly this (where should shared fleet docs live).

## Documentation audit (Q-0104)

`check_current_state_ledger --strict` ✓ at boot (ledger in sync). Everything this
session shipped is captured in its own merged PR + this card; the handoff scaffold and
owner-queue are recorded above (not chat-only). New owner decision this session (grant
Railway via project-scoped tokens; the values-vs-names fork) is documented in
env-grant-policy.md + the websites plan, not only here. Telemetry row appended. No
claim file was open (this closing work needed none). Nothing left un-homed.

## Grooming (Q-0015)

Groomed by routing: the "owner env-grant ideas" were moved a full lifecycle step from
chat → a durable policy doc (fleet-manager) + an executable feature spec (websites) the
reactivated websites lane can build. The session idea above (fleet-triage register) is
teed up for the next session to execute rather than left as a raw idea.
