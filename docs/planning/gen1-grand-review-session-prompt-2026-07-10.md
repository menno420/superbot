# Gen-1 grand review — paste-ready session prompt (2026-07-10)

> **Status:** `reference` — authored 2026-07-10 in the `superbot-games` exploration-lane
> coordinator session (gen-1 close-out). This is the **paste-ready prompt** for the
> owner's Fable 5 **ultracode grand-review session**: independent review of everything
> the gen-1 Claude Code Projects fleet did, the EAP emails, an old-bot → new-bot gap
> map with improvements applied, and a full open-PR sweep to terminal states.
> **Owner judgment call baked in:** previously owner-gated PRs — superbot-games mining
> **#5/#11** and substrate-kit **#26/#49** — are authorized in this prompt for
> review-and-merge on merits. Strike that clause before pasting if unwanted.
> Companion doc: the owner's Part 1 framing questions live in
> [docs/eap/gen1-wrapup-email-part1-questions-2026-07-09.md](../eap/gen1-wrapup-email-part1-questions-2026-07-09.md).

## The prompt (paste verbatim)

````markdown
**ultracode.** You are a Fable 5 session running the **gen-1 grand review + cleanup**: independently review everything the Claude Code Projects fleet did, review the EAP emails, map old-bot → new-bot differences and apply improvements, and drive every open PR to a terminal state. No prior chat context — this is your map. Rails: decide-and-flag, never wait; honest uncertainty over invented certainty; forward-only git; READY PRs, never drafts; git history is the clock of record where docs disagree; merge = deploy on superbot (Railway auto-redeploys `worker` on merge to main) — so runtime changes there need CI green and extra care, docs are free.

**Scope.** Repos: menno420/superbot, superbot-next, superbot-games, substrate-kit; add fleet-manager and websites via list_repos/add_repo (reachable as of 2026-07-09). Emails: Gmail read-only — the sent "Claude Code Projects Review" thread (2026-07-08, to claude-code-early-access@anthropic.com). Never: send email, push tags, create releases, delete branches (403 walls; sending is owner-only).

**Read first:** (1) fleet-manager `docs/gen2-blueprint.md`; (2) superbot `docs/eap/` — fleet-manifest, external-review-pack-2026-07-09, `gen1-wrapup-email-draft-v2-2026-07-09.md` (the draft under review) — plus `docs/planning/projects-eap-evaluation-log.md`, and superbot's own CLAUDE.md + `docs/current-state.md` (binding conventions); (3) superbot-games retros, `docs/succession-exploration.md`, gen2-feedback docs, `control/status-*.md`; (4) superbot-next's retro + band-5 status + canonical rebuild plan; (5) substrate-kit's capstone/rollout/ratification PRs.

**Produce, with adversarial verification (independent agents attempt to refute each claim before it's confirmed):**
1. **Old-bot vs new-bot difference review** — a verified gap map between superbot (frozen oracle, ~1,900 PRs) and superbot-next (rebuild, band 5): what's ported, what's missing, what the rebuild does *better*, and known reds (the golden-parity report job failing on superbot-next main — diagnose it). **Apply improvements wherever contained**: fix the parity-report red, port small verified gaps, land each as its own PR under the repo's conventions (Q-0241 rebuild doctrine: never wait, live-order, CI green required).
2. **Open-PR sweep across ALL six repos** — enumerate every open PR; review each on its merits; merge on green if sound (converting sound drafts to READY — including superbot-games mining's #5/#11 and substrate-kit's ratification PRs #26/#49, which the owner has authorized for review-and-merge); close with a one-line reason if not sound; fix-then-merge where a small fix unblocks. Zero open PRs at the end, or each survivor carries a ⚑ line naming exactly why it must wait.
3. **Fact audit of the email draft** — every PR number, count, timestamp, quoted error against git/GitHub (known trap: superbot-games PR #8 merged 17:06:06Z, relayed elsewhere as ~18:30Z).
4. **Wind-down completeness audit per lane** — succession deliverables landed, status markers flipped, what's genuinely still open.
5. **Gen-2 synthesis** — reconcile all lanes' gen2-feedback + proposed custom instructions into one consolidated blueprint recommendation set, flagging inter-lane disagreements.
6. **Email finalization candidate** — compare draft v2 to the 2026-07-08 sent email; fill placeholders where repo evidence now exists (your PR sweep and gap map ARE new evidence — fold their outcomes in); produce a send-ready candidate with remaining gaps explicitly marked (owner's Part 1 slot stays open).
7. **Honest efficiency verdict** — where the fleet's time actually went; what gen-2 must do differently, evidence-backed.

**Land it:** improvements/PR-fixes as per-repo PRs under each repo's conventions; the report (`docs/eap/gen1-grand-review-<date>.md`) + email final candidate (`docs/eap/gen1-wrapup-email-final-candidate.md`) as one READY PR to superbot with a `.sessions/` card (born-red first push, flip complete last), auto-merge armed via enable_pr_auto_merge after MCP creation (if "already in clean status", squash-merge directly). Superbot's session gate also requires a `telemetry/model-usage.jsonl` row in any PR that adds a `.sessions/` card (Q-0194 guard), and new docs need a `> **Status:**` badge + a reachability link from a read-path doc. Known walls — don't re-probe: 403 on tags/releases/branch-deletes; auto-merge arming window ≈ zero on fast-CI repos; `run_in_background:false` may be ignored; subagent type must be explicit where 'general-purpose' is absent. End with a ⚑ owner-actions list — exact clicks only the owner can do, including the final email send decision.
````
