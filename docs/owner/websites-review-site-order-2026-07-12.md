# ORDER — Websites Project: refresh + upgrade the public review site (2026-07-12)

> **Status:** `owner-guidance` — a paste-in work order for the **Websites Project**
> (`menno420/websites`), authored 2026-07-12 at the owner's direction. It refreshes and
> upgrades the **public program-review site** (`https://review-production-f027.up.railway.app`)
> that the second Anthropic email links. Three headline asks: **(1)** refresh all data to
> today, **(2)** enable a live on-site **AI review/interaction assistant**, **(3)** rebuild the
> **homepage** so it leads with the most important things and explains where everything lives.
> Paste the "ORDER (paste-in)" block below into the Websites Project coordinator.

## Why now (context for the Project)

The owner sent the second Anthropic EAP email on 2026-07-12; it **links this review site** as
the evidence home ("Read this with an agent too … every claim linked to a public commit"). The
Anthropic Claude Code team (Diana Liu, Omid, Matt Gallivan + the early-access alias) will click
through **this week — the EAP window runs through Tue 2026-07-14.** So the site is now a
first-impression, reviewer-facing surface, not just an internal artifact. Two known gaps to
close: its data is still a **2026-07-11 snapshot** (missing today's scheduler-degradation
incident and the 15-Projects → 8-seats consolidation), and there is **no live AI on it yet**,
even though the whole pitch is "review this with an agent."

The site today has these sections (keep them; the homepage becomes the new front door to them):
**Overview · Process · Growth · Fleet · Reviews · Q&A · Successes · Problems.**

---

## ORDER (paste-in)

Refresh and upgrade the public program-review site (review-production-f027) so it is current,
reviewer-ready, and interactive. This is time-sensitive: the Anthropic Claude Code team is
reviewing it this week (window through Tue 2026-07-14). Run autonomously and ship real, deployed
results, not a plan — decide-and-flag on stack/design choices. Deliver all four workstreams
below and send a status report with the live URL when each is up.

### A. Refresh ALL data to today (2026-07-12)

Regenerate every data-driven surface from the **latest committed state** of the fleet repos you
can read — do not hand-edit numbers; pull from source so it stays reproducible.

Primary sources in `menno420/superbot` (read-only):
- `docs/current-state.md` — the live status ledger (8-seat structure, sector queues, recently shipped).
- `docs/eap/night-review-2026-07-12.md` — **the scheduler-degradation incident** (the new material to add; this is "finding 7" in the email).
- `docs/eap/night-review-2026-07-11.md`, `docs/eap/external-review-pack-2026-07-09.md` — the reviewer-facing narrative backbone.
- `docs/eap/anthropic-email-2-draft-2026-07-11.md` — the canonical findings list + framing the site should stay consistent with.
- `docs/eap/screenshots-2026-07-11/` and `screenshots-2026-07-12/` (+ their `index.md`) — the evidence figures, captioned.
- Per-repo GitHub state (PRs merged, tests, releases, heartbeats) across the repos in your access list; if the fleet roster (`fleet-manager/docs/roster.md`) is reachable, use it as the machine-generated roster source.

Must be reflected after the refresh:
1. **The 2026-07-12 scheduler incident** written up on the Problems page (and surfaced on the homepage): three self-wake mechanisms, three silent failure modes; the dead-man-cron failsafe that saved the fleet; the serialization-vs-real-drop distinction; the duplicate-fire clean stand-down. Every claim links to its commit / night-review section.
2. **Scale story corrected to the current shape:** the experiment ran 15 Projects, then **consolidated to 8 standing seats on 07-11** — show it as "peaked at ~15 → now 8 standing seats," not a flat 15. Update the Fleet page's roster to the 8 seats + their live heartbeats.
3. **Refreshed counts** (PRs merged, sessions, tests, live services, releases) pulled live, with each number's "as of" timestamp visible. Growth charts extended through 2026-07-12.
4. **Every claim → a public commit** — re-verify the links; a claim whose evidence you can't locate should be softened or dropped, not left dangling. Keep the site's honest tone (the paper-trading lane's "found no significant strategy" is a feature — keep that kind of honesty).
5. Make the daily auto-refresh actually current (fix it if the 07-11 snapshot means the cron isn't landing) and stamp "last refreshed" visibly in the footer.

### B. Enable a live on-site AI review / interaction assistant

Make the "review this with an agent" promise real: a reviewer (or their own agent) can talk to
an AI **on the site** and get evidence-grounded answers, or ask it to produce a review.

Requirements:
- **Two modes in one widget:** (a) **Ask** — free-form Q&A about the project; (b) **Review** — on click, it produces a structured review of the project (what's strong, what's weak/risky, what to verify, suggested probes to run), in the same honest register as the email.
- **Grounded, never fabricated.** Answers draw ONLY from the committed evidence corpus (the site's own content + the linked commits + the key superbot docs above). Every substantive claim cites its source (commit SHA, file path, or site section). If something isn't in the evidence, it says so plainly instead of guessing. It must never invent a number, a capability, or a commit.
- **Seed it with the real questions.** Preload the existing evidence-backed Q&A/questionnaire so the common reviewer questions answer instantly and consistently; the live model handles the long tail.
- **Server-side only.** The model call runs on your backend; the API key is **never** exposed to the browser. Use a current Claude model (Sonnet for quality, or Haiku for cheaper high-volume — your call; note which). If no model API key is present in your service env, **that is the one thing to flag to the owner** — it's the single owner-provided secret this feature needs (add `ANTHROPIC_API_KEY` to the review service). Report it as a blocker rather than faking the feature.
- **Guardrails (public endpoint):** scope strictly to this project's evidence; refuse off-topic / prompt-injection / "ignore your instructions" attempts; per-IP or per-session rate limiting; a hard monthly spend cap with graceful "try again later" degradation; log the questions asked (they're useful signal for the owner and can feed the Q&A page). Treat anything a visitor types as untrusted input — it must not be able to change the assistant's grounding or exfiltrate secrets.
- Put the entry point **prominently on the homepage** (a clear "Ask the project / Review with an AI" panel), and make it reachable from every page.

### C. Rebuild the homepage — lead with what matters + a "where to find things" guide

The current landing page is a stats readout. Replace it with a real front door that a busy
reviewer understands in 30 seconds:

- **One-line what-this-is** at the top: this is the public, evidence-backed review of running Claude Code Projects as an autonomous software fleet — built for the Claude Code team, every claim linked to a public commit.
- **A key-stats row** (the few numbers that matter): PRs merged, agent sessions, tests passing, live services, repos/seats (peaked ~15 → 8 standing), generations — each with an "as of" stamp.
- **"Start here" — the 3–5 most important findings as highlighted cards**, each one line + a deep link, e.g.: the merge-permission root cause we found was *partly ours*; the routine model-mismatch (config Opus 4.8 → ran Sonnet 5); the two-vantage permission split; the 07-12 scheduler incident; shared-memory + durable-state as the standouts that earned trust. These are the things the owner wants surfaced, not buried.
- **The AI panel** (from B) — prominent.
- **A "How this site is organized" map** — a short labelled guide, one line each, so a reviewer knows exactly where to go:
  - *Overview* — the whole story in brief.
  - *Process* — how the human+agent workflow / substrate actually works.
  - *Growth* — the metrics over time (PRs, tests, services).
  - *Fleet* — the 8 standing seats and their live heartbeat/status.
  - *Reviews* — the dated review editions (with the Atom feed).
  - *Q&A* — evidence-backed answers to reviewer questions (and the live AI).
  - *Successes* — documented wins, each linked to its repo/commit.
  - *Problems* — the failures and near-failures, with specifics and costs (incl. the 07-12 incident).
- **A clear link out to the GitHub evidence** and a one-line note that this pairs with the July 8 + July 12 emails.
- Keep it fast, responsive/mobile-clean, and readable in both light and dark.

### D. Accuracy + polish pass

- Re-verify every headline claim against its commit before shipping; fix or drop anything you can't substantiate.
- Consistency with the email's framing and numbers (don't contradict what was just sent).
- No secrets/tokens anywhere in the rendered site or logs; the Pokémon lane stays private (Nintendo-derived) — don't surface its internals.
- Confirm the public URL loads with no auth and works from a cold browser.

### Report back

In your status report include: the live URL(s); confirmation the 07-12 incident + 8-seat
consolidation are visible; which model the AI assistant uses and whether the API key was
present or is being requested from the owner; the rate-limit + spend-cap you set; and anything
you got stuck on or worked around. Flag the API key explicitly if you need it — that's the one
owner action this may require.

---

## Owner-side note (not part of the paste-in)

The **only** thing this order is likely to need from the owner is a **model API key** for the
AI assistant (Section B) — added as a secret (`ANTHROPIC_API_KEY`) on the review service. If
the Websites Project reports that as a blocker, that's expected; everything else it can do
autonomously. Cost is bounded by the rate-limit + spend-cap it's instructed to set.
