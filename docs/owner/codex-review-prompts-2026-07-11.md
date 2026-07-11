# Codex review prompts — 2026-07-11 (one repo each, copy-paste ready)

> **Status:** `owner-guidance` — four self-contained prompts for OpenAI Codex reviews,
> one repo per prompt (Codex is single-repo-reliable). Paste each into a Codex session
> connected to that repo.
>
> **Why these four** (exposure-weighted, from the 2026-07-11 fleet survey): the four
> repos where an independent review pays most *right now* —
> **superbot-next** (5/5: ~70 PRs merged in 48h into a production-bound bot, while the
> incumbent Codex reviewer pool was flapping), **venture-lab** (5/5: real-money Stripe
> code about to be published to paying customers), **superbot-mineverse** (4/5:
> OAuth/CSRF/HMAC security surfaces reviewed *before* real secrets are provisioned),
> **substrate-kit** (4/5: fleet-wide blast radius, 6 releases in ~2 days).
> Deliberately excluded: **pokemon-mod-lab** (PRIVATE, Nintendo-copyrighted material —
> don't feed it to an external reviewer), **trading-strategy** (program complete and
> parked; correctness matters but nothing moves until a new owner-gated protocol),
> **superbot-games** (high churn but pure-domain, no external exposure yet — next batch).
>
> **Reading Codex output:** verify-against-source applies (Q-0120) — Codex has claimed
> phantom commits/PRs three times on superbot-next (#144/#160/#178). Treat its findings
> as leads to verify, never as facts.

---

## Prompt 1 — superbot-next (the rebuilt Discord bot)

```
You are reviewing menno420/superbot-next: a ground-up rebuild of a production Discord
bot ("SuperBot"), built fresh on a workflow foundation — NOT a fork. The original bot
(separate repo, not available to you) acts as a behavioral oracle via a "golden parity"
harness in this repo: recorded golden transcripts are replayed against the rebuilt
subsystems and must match.

Context: roughly 90 PRs (#111–#191) merged in the last ~48 hours across 5 parallel
agent lanes. That volume is the reason for this review. Current claimed state: 37 of
49 subsystems ported at golden parity (the non-game map is complete), parity gate green
218/218 goldens, ~1388 unit tests passing, boots to RUNNING against real PostgreSQL.

Your job: find real correctness bugs, in priority order:
1. PARITY HARNESS SEMANTICS — PR #151 changed replay semantics for EVERY subsystem.
   Check whether the harness can now produce false greens: goldens that pass without
   actually asserting the behavior they claim to pin. A weak harness silently
   invalidates all 218 greens.
2. MONEY-LIKE DOMAINS — the economy, blackjack, and games payout paths (band 6).
   Look for payout/balance arithmetic bugs, race conditions on concurrent
   commands, and state that survives where it shouldn't (e.g. across games).
3. THE AI OPERATOR SURFACE (band 7, PRs #151/#160/#165/#177) — injection paths
   from user-controlled Discord content into AI prompts or command dispatch,
   and whether AI_ENABLED=false truly makes it inert.
4. LIFECYCLE — startup/shutdown ordering, the FAILED_STARTUP paths, and the
   plugin pin/boot verification (tools/plugin_pin.py, plugins.lock.json).

Rules: cite only commits/files that actually exist (verify every SHA — prior automated
reviews of this repo cited nonexistent commits); report findings as file:line +
a concrete failure scenario + severity (blocker/major/minor); do NOT propose
refactors or style changes; if a suspicious area turns out clean, say so explicitly.
Deliverable: a single prioritized findings report.
```

---

## Prompt 2 — venture-lab (pre-publish review; real money)

```
You are reviewing menno420/venture-lab: an agent-built "first revenue" lane. Three
digital products are BUILT and about to be PUBLISHED for real money by the owner:
1. candidates/membership-kit/ — $49 self-hostable members-area starter:
   Stripe Checkout webhook -> member grant; JSON-file store default, optional
   Supabase store over PostgREST (stdlib urllib, no SDK).
2. candidates/template-packs/ — $19 pay-what-you-want agent-workflow templates.
3. candidates/stripe-webhook-test-kit/ — $29 CLI that fires correctly-signed
   Stripe-shaped events at a local webhook endpoint; --forge mode must FAIL
   handlers that accept unsigned events.

This is a PRE-PUBLISH gate review. Real customers will run this code inside payment
paths. Find publish-blockers, in priority order:
1. STRIPE SIGNATURE VERIFICATION — in both membership-kit's webhook handler and
   the test-kit's signing/forging logic: timing-safe comparison, timestamp
   tolerance/replay handling, and whether any code path accepts an unsigned or
   badly-signed event (including error paths and malformed JSON).
2. MEMBER-GRANT CORRECTNESS — can a crafted event grant/revoke the wrong member?
   Duplicate-event idempotency? What happens on partial failure between payment
   and grant?
3. SECRET HANDLING — .env usage, defaults that could ship enabled, secrets
   leaking into logs/errors, and anything in the committed zips
   (candidates/*/dist/*.zip) that should not be distributed.
4. BUYER EXPERIENCE TRUTH — do the LISTING.md / listing-copy.md claims match what
   the code actually does? A paid product that overclaims is a refund machine.
5. The vendored Stripe fixtures (fixtures/PROVENANCE.md) — still faithful to real
   Stripe event shapes?

Rules: findings as file:line + concrete exploit/failure scenario + severity, split
into PUBLISH-BLOCKER vs FIX-SOON vs NICE-TO-HAVE. No refactors. If the signature
path is solid, say so explicitly — "verified clean" is a valuable result here.
Deliverable: a publish-gate report the owner reads before clicking Publish.
```

---

## Prompt 3 — superbot-mineverse (security review BEFORE secrets exist)

```
You are reviewing menno420/superbot-mineverse: a browser game over a Discord bot's
live mining economy. Stdlib-only Python server (server/app.py) + vanilla JS frontend.
Architecture rails: the web app NEVER touches the bot's Postgres or token; it reads a
versioned snapshot contract (mining_snapshot.v1) and will write ONLY via a bot-side
audited HMAC endpoint. Discord OAuth sign-in and the write path are BUILT BUT DORMANT:
the owner has not yet provisioned the six env vars (OAuth client id/secret, redirect
URI, session signing key, write endpoint + shared secret).

That's the point of this review: audit the security-sensitive surfaces NOW, before
real secrets make them live. Priority order:
1. OAUTH FLOW — authorization-code handling, state parameter generation/validation
   (CSRF), redirect URI validation, token handling, and what a malicious callback
   can achieve while env vars are unset (fail-closed or fail-open?).
2. SESSION COOKIES — signing scheme, algorithm choice, expiry/rotation, cookie
   flags (HttpOnly/Secure/SameSite), and whether a forged or empty signature is
   rejected with a timing-safe comparison.
3. THE HMAC WRITE PATH — request signing, replay protection (nonce/timestamp),
   canonicalization (can two different requests produce the same signed string?),
   secret comparison timing-safety, and error-path information leaks.
4. SNAPSHOT INGESTION — does the server validate the snapshot against the schema
   before rendering, or can a poisoned snapshot XSS the frontend? Check every
   place snapshot strings reach the DOM.
5. DEGRADED MODE — with zero secrets set the app runs read-only on a sample
   snapshot; verify nothing privileged is reachable in that mode.

Rules: findings as file:line + attack scenario + severity; assume the attacker is an
arbitrary internet user (the repo/site is public); no refactors; explicitly state
which of the five surfaces you verified clean. Deliverable: a pre-provisioning
security report — the owner provisions the real secrets only after reading it.
```

---

## Prompt 4 — substrate-kit (the fleet-wide foundation)

```
You are reviewing menno420/substrate-kit: a portable "agent-memory substrate" — one
stdlib-only generated file (dist/bootstrap.py, built from src/engine/) that plants a
complete AI-agent working system into any repo: templated binding docs, session logs,
checkers under one `check --strict`, staged hooks, and a benchmark lab (bench/).
Seven other repos vendor this kit; a bug here propagates fleet-wide. Six releases
shipped in ~2 days (v1.7.1 -> v1.11.0), which is the reason for this review.

Priority order:
1. THE GATE LOGIC — the merge/session-gate checks (the "session card" hold that
   keeps incomplete PRs red). A recent bug (W-3: multi-card shadowing in the gate
   tail) let the wrong card control the verdict; it was fixed on both surfaces.
   Hunt for REMAINING variants: multiple cards, renamed cards, cards edited in the
   same push as the flip, path-matching edge cases, case sensitivity. A gate that
   false-greens merges broken PRs in every adopting repo.
2. GENERATION INTEGRITY — is dist/bootstrap.py provably a pure function of
   src/engine/? Can the generator emit code that diverges from the tested source?
   Check the build/release pipeline's three-way asset verification for gaps.
3. ADOPT/UPGRADE SAFETY — `bootstrap.py adopt` and upgrade paths run inside OTHER
   repos: look for destructive file operations, template rendering that can
   clobber existing user files, and failure modes that leave a repo half-adopted.
4. CHECKER TRUTHFULNESS — do the checks under `check --strict` actually verify
   what their names claim? A checker that exits 0 without checking is worse than
   no checker (this fleet has been bitten by false-green checkers before).
5. BENCH VALIDITY — bench/ A/B-measures whether the kit helps; look for measures
   that can pass/fail for reasons unrelated to what they claim to measure.

Rules: findings as file:line + concrete failure scenario + severity; no style
comments; verify every commit/PR you cite actually exists; explicitly list which
areas you verified clean. Deliverable: one prioritized findings report, gate
findings first.
```

---

## How to run these

1. Open Codex (ChatGPT → Codex) → pick the repo's environment (all fleet repos have
   Codex environments enabled as of 2026-07-11) → paste the prompt.
2. Quota refusals are RETRY-LATER, never a wall (fleet doctrine).
3. Route each findings report back to me ("review this report" now works — the
   generalized review skill verifies its claims against source before anything acts
   on them, per Q-0120).
