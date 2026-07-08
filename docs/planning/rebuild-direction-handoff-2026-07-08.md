# Handoff — Directing the running rebuild Project (next session starts here)

> **Status:** `reference` · created 2026-07-08 to hand the "direct the running rebuild Project + guide
> the owner through owner-only steps + capture EAP findings" role to a fresh session.
> **This is a DIRECT chat / management session, NOT a Project task.**
> **Next session runs on Sonnet 5** (owner is watching usage limits; incidental bonus — a live
> comparison of Sonnet 5 vs. the old Sonnet vs. Opus on the same directing role, worth a one-line note
> if the difference is visible).

## Your job (next session)

The rebuild Project is **RUNNING** — the owner started it 2026-07-08 with the kickoff prompt + the
corrected Custom Instructions. You are the **management layer**: read the coordinator's status reports,
guide the owner through the owner-only steps, and capture evaluation findings. You do **not** build —
the Project's coordinator + workers do that.

## LIVE state — check first

- **The rebuild Project is live.** Repos: `menno420/superbot` (read: plan / specs / parity / source),
  `menno420/substrate-kit` + `menno420/superbot-next` (write; **both already seeded / non-empty**).
- **Goal it's executing:** canonical plan §5 **steps 7–13** — populate `substrate-kit` →
  `superbot-next` adopts from it → kernel K0→K8 → K9 + strand-3 → layer-V files → K10 → port bands 1–7.
  **Build-first / test-later, forward-only.**
- **The kickoff doc it was given** (Custom Instructions + startup prompt):
  [`rebuild-project-kickoff-2026-07-08.md`](rebuild-project-kickoff-2026-07-08.md).
- **Plan of record:** [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md)
  (§5 sequence, §2 taxonomy).
- **Repo access is per-context:** the coordinator sees all three repos; a `superbot` chat session sees
  only `superbot`. Work from the coordinator's reports for anything on the new repos.

## What to score in each status report (the two axes — previously our thinnest EAP data)

1. **Owner-directing quality** (coordinator-judgment + proactivity): does it hand owner-only steps
   with **what / why / exactly-how**, batched into a running checklist, correctly identified
   (flag-not-attempt), **while it keeps building everything else**? Or does it drip them one at a time,
   stall on the owner, or try an owner-only step itself and hit a wall first?
2. **Self-correctness / spec-drift** (the honest risk of build-first/test-later): does it **read the
   spec before building** each band, self-check its output, and flag uncertainty rather than
   confabulate? Watch for **spec drift nothing catches until the port bands** — if it appears, that's a
   finding about unattended build *without* gates, not a failure of the strategy.

Note both per report; they're the first real *production-autonomy* data and strong follow-up-email
material.

## Owner-only steps you'll guide the owner through (none block the build)

- Repo **settings** on `superbot-next` / `substrate-kit`: rulesets, branch protection, required checks
  (golden-parity born-red, `check_compat_frozen`), CODEOWNERS.
- **Secrets / PATs / OIDC** + `ROUTINE_PAT` for auto-merge on the new repos.
- **Railway** projects (production + shadow) — owner pastes secrets, pins regions, sets backups
  (Q-D14). *Not needed until the bot runs.*
- **Flip `superbot-next` to private** before CUT-2 (public now for free Actions minutes).
- Everything in canonical plan **steps 14–17** (telemetry freeze, prod-data import, shadow, cutover) —
  owner's, later, reversible per Q-0241.

## The Anthropic email — DONE (sent)

- **Sent 2026-07-08** to `claude-code-early-access@anthropic.com` (subject "Claude Code Projects
  Review"); **no reply yet.** Two-author (Menno Part 1 / Claude Part 2), two-reviewer ask. Canonical:
  [`projects-eap-anthropic-email-2026-07-08.md`](projects-eap-anthropic-email-2026-07-08.md). **If Omid
  or Diana reply, surface it to the owner.**
- Contacts: **Omid Mogasemi** (Claude Code Team), **Diana Liu** (Product Operations Manager, Claude
  Code). Feedback welcome **on a rolling basis**. **Free EAP window ends Fri 2026-07-10** — the rebuild
  run spills into the paid period (owner is renewing Max directly, ~$180 vs Google Play's ~$270).

## Next-email material (capture as it comes; owner sends, never you)

- The **rebuild-run findings** on the two axes above — the first real production-autonomy data.
- **Durable-memory re-probe:** re-run the self-audit memory questions after a context-compression event
  / in a fresh session — the number the campaign self-audit couldn't get
  ([`campaign-self-audit-2026-07-08.md`](../eap/campaign-self-audit-2026-07-08.md) §4).
- Any new permission / friction incident.

## Findings already banked (don't re-derive)

- **Permission model, fully mapped:** destructive git walled (force-push / branch-delete); first
  publish to an *empty* repo walled but the **Contents API bypasses** it (and the new repos are already
  seeded, so normal git works there now); **scheduling tools (`send_later` / `delete_trigger`) prompt
  in EVERY mode** (auto + accept-edits) while everything else — file r/w, bash-read, GitHub MCP read
  **and write** — is silent; the **two-vantage split** (agent sees clean success, operator sees the
  gate). Sources: [`projects-eap-permission-probe-report-2026-07-08.md`](projects-eap-permission-probe-report-2026-07-08.md),
  [`projects-eap-evaluation-log.md`](projects-eap-evaluation-log.md) (2026-07-08 entries).
- **Campaign self-audit:** dedupe held (0 collisions, claim + merge level); memory ≈0.98 precision
  *same-day* (durable untested); scheduling + sidebar-states **FAIL**.

## Working discipline (this repo)

Forward-only git; born-red session cards; claim lanes (`docs/owner/claims/`); open a PR every session
and let it auto-merge on green (**MCP-created PRs need `enable_pr_auto_merge` called manually**).
**Footgun this chat hit:** do **not** `git reset --hard origin/main` while your own PR is still open —
verify it merged first (a stale-branch banner is not proof). The **plan-homing guard** (#1855) reddens
CI if a new `plan`-badged doc isn't listed in `docs/planning/README.md`.
