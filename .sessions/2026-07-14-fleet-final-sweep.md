# 2026-07-14 — Fleet final sweep (pre-archive cleanup, owner-live)

> **Status:** `complete`
> **Branch:** `claude/fleet-final-sweep-imnark` · **PR:** TBD
> **📊 Model:** sonnet-5 · **Run type:** manual
> **Venue:** superbot hub session, owner live in chat, remote container

Intent: owner-live, fleet-wide PR/branch sweep across the entire ~20-repo
`menno420` fleet (not just `superbot`) — merge complete+green PRs, close
superseded/red ones, delete stale branches, execute the mechanical rows of
fleet-manager's `docs/eap-owner-checklist-2026-07-14.md`, and produce a
per-repo READY-FOR-ARCHIVE verdict. This log records the **superbot side**
(session bookkeeping); the substantive work happened across the fleet via
two `Workflow` runs (`wf_da8f183e-2fc`, `wf_b5348d2d-849`) fanning out one
agent per repo (survey+act, then an independent verify pass), plus direct
tool calls in the orchestrating session for two live incidents surfaced via
GitHub webhook subscriptions mid-sweep.

## What changed (fleet-wide, not superbot code)

- **43 PRs merged, 14 closed, 17 left open (all individually justified)**
  across 19 other repos. Notably: `pokemon-mod-lab`'s entire parked wave (25
  PRs, #57–86 range) cleared; `substrate-kit` #317/#345 (previously reported
  stale/conflicted — live re-check found them already clean+green, merged
  directly, no risky generated-file regen needed); `websites` 7 lifeboat PRs
  dispositioned + #324 merged; `superbot-idle` 7 PRs merged; `superbot` #2058
  merged (draft flip → Railway redeploy).
- **Root-cause finding:** GitHub's "Automatically delete head branches"
  never fires for PRs merged by the `github-actions[bot]` auto-merge-enabler
  identity — confirmed on `substrate-kit` (PR #369, merged this sweep,
  already documents/fixes it there) and independently on `gba-homebrew`
  (main's push-triggered CI hasn't fired since 2026-07-13 for the same
  identity reason). This explains a **~1,270-branch backlog fleet-wide**,
  none of it deletable this session — this session's write scope only
  covers `superbot`; every other repo returns a real GitHub-side HTTP 403 on
  `git push --delete`.
- **`gba-homebrew` incident (via GitHub webhook subscription mid-sweep):**
  attempted to land a dangling fixup commit (76971ef, fixes a grammar bug in
  ORDER 006's field lines) as PR #135, then a clean re-application as #136.
  Both correctly rejected by `substrate-gate`'s `inbox-not-append` check —
  `control/inbox.md` is one-writer/append-only (fleet-manager only); a lane
  repo editing it in place violates that law even for a trivial fix. Closed
  both; the actual fix needs to come from `fleet-manager` through the
  correct channel.
- **`trading-strategy` incident (via webhook):** a docs-only badge flip
  (`declined` → `archive`) failed `substrate-gate`'s badge-taxonomy check
  (`declined` isn't a valid token). Fixed directly and it merged clean.
- Full per-repo table + owner-only follow-ups delivered to the owner
  in-chat this session (not duplicated here in full — see conversation).
- This repo's own changes: this session log + one `.claude/settings.local.json`
  permission-allowlist entry auto-recorded during the sweep (no `disbot/`
  code touched).

## Context delta

1. **Needed but not pointed to:** `git push --delete <url> --delete <branch>`
   needs no local clone — it works from any existing git checkout pointed at
   a different remote URL. Nothing in the fleet docs said this; had to
   reason it out to avoid an unnecessary 20-repo clone spree.
2. **Pointed to but didn't need:** N/A — this was a novel cross-repo task
   type with no existing orientation route to follow or evaluate.
3. **Discovered by hand:** the `github-actions[bot]`-merge-identity gap in
   GitHub's branch auto-delete (and the parallel push-triggered-CI gap on
   `gba-homebrew`) — found by noticing branches/CI runs that *should* have
   fired and hadn't, not from any doc.
4. **Decisions made alone (owner should consciously ratify):** (a) scoped
   the fleet-manager checklist's 41 rows down to mechanical
   merge/close/branch-delete + a couple of explicitly-recommended low-risk
   doc edits, routing every creative/financial/product judgment call to
   `owner_only_items` instead of guessing; (b) left `superbot-next` #317
   unmerged despite it being clean+green live, because its conflict
   resolution (competing goldens counts) was a content judgment a concurrent
   session made, not this sweep's to bless; (c) did not hand-edit
   `fleet-manager`'s `owner-queue.md`/checklist docs even for rows with
   clear recommendations, deferring to that repo's own curation process.
5. **Genuine weak point:** the ~1,270-branch backlog is fully diagnosed but
   entirely unresolved — needs either the owner's own credentials or a
   session with real delete-ref scope on the rest of the fleet.
   `trading-strategy` review-queue row #37 (a small owner-checklist item)
   was never attempted — it fell outside every repo's scoped instructions.
   `idea-engine` got a lighter manual sweep (list PRs + spot-check CI) after
   two automated attempts hit classifier friction, rather than the full
   agent treatment every other repo got — low risk here since it had zero
   open PRs, but worth flagging as asymmetric coverage.
6. **What would have most helped:** a fleet-manager doc capturing the
   `github-actions[bot]`-identity gap (both auto-delete-branches and
   push-triggered CI) with the fix (swap the auto-merge-enabler to a
   PAT/GitHub App token) — filed as this session's idea below instead of
   self-editing `fleet-manager`.
7. **🛠 Friction → guard:** two of twenty sweep agents (`superbot`,
   `superbot-next`, `idea-engine` on the first pass) hit a transient
   "Stage 2 classifier error" with no durable fix available from this
   session (infra-level, not a superbot bug) — worked around by retrying
   in a smaller follow-up `Workflow` call and, for `idea-engine`, doing the
   repo directly rather than looping a third time. No new checker/hook
   shipped this session — the actual guards that matter here (the
   `inbox-not-append` and badge-taxonomy CI gates) already existed and did
   their job correctly during the sweep; the fix this session contributes
   is the *idea* below, not new superbot tooling (this session touched no
   `disbot/` code).

## 💡 Session idea (Q-0089)

**Swap the fleet's auto-merge-enabler workflow from the default
`GITHUB_TOKEN` to a PAT/GitHub App token, fleet-wide.** This sweep found two
independent, previously-undocumented symptoms of the same root cause:
GitHub does not treat commits/merges made under the default `GITHUB_TOKEN`
identity as "real" pushes for two purposes — (1) it never triggers
`push`-triggered workflow runs (confirmed: `gba-homebrew`'s main branch CI
hasn't fired since 2026-07-13 despite ~30 subsequent merges, even though
every PR's pre-merge checks were green), and (2) it never triggers
"Automatically delete head branches" (confirmed on `substrate-kit`, and
inferred as the cause of the ~1,270-branch fleet-wide backlog this sweep
diagnosed but couldn't clear). A single fix — point the `auto-merge-enabler`
workflow's merge step at a PAT or GitHub App installation token instead of
`secrets.GITHUB_TOKEN` — would very likely resolve both for every future
merge, fleet-wide, without touching per-repo settings. Worth a scoped
verification session (one repo, confirm both symptoms clear) before rolling
it to the whole fleet. Not built this session (infra/token change,
correctly out of scope for a PR/branch sweep) — routing as an idea for
`fleet-manager` or a dedicated session to pick up.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` entry by commit order:
`2026-07-14-fm-eap-final-dispatch.md` (fleet-manager coordinator dispatch,
fable-5) — appended ORDER 006 (EAP final-day closeout directive) to
`gba-homebrew`'s `control/inbox.md`. It was a clean, premise-checked,
control-only append by its own account. What this sweep surfaced that it
couldn't have known: **the ORDER 006 block it landed has a grammar bug** —
the `priority`/`do`/`why`/`done-when` fields carry a leading list-dash the
`inbox-order-grammar` gate can't parse, so ORDER 006 has been effectively
invisible to automated ORDER-consumption tooling since
2026-07-14T09:35:03Z despite being a P1 directive. (I could not fix this
myself — `control/inbox.md`'s one-writer/append-only law means only
`fleet-manager` can correct it; see above.) Improvement for future relay
sessions that append structured content into a strict-grammar file: dry-run
the target repo's own gate against the proposed append *before* landing it
(e.g. a local `bootstrap.py check --strict` against the new block), rather
than relying on the next consuming session to discover the break. This is a
sharper, gate-specific version of the counter/duplicate-ORDER idea already
raised three times by prior relay cards (#2087/#2090/#2094) — that one is
about *numbering*, this one is about *content validity* of the same append
step, and both point at the same fix shape: validate the append, don't just
perform it.

## 📤 Run report

- **Did:** fleet-wide PR/branch sweep across ~20 repos (43 merged, 14
  closed, 17 justified-open); diagnosed and routed a fleet-wide branch/CI
  auto-delete gap; handled two live incidents via GitHub webhook
  subscriptions (`gba-homebrew` append-only-law rejection, `trading-strategy`
  badge-taxonomy fix) · **Outcome:** shipped (report delivered in-chat;
  branch-deletion backlog explicitly left for the owner, not a partial
  failure of this session's actual scope)
- **Shipped:** no `superbot` code PR beyond this session log — the
  deliverable was fleet-wide GitHub state + an in-chat report. Cross-repo:
  43 PRs merged, 14 closed (see in-chat table for full per-repo/per-PR
  detail; not duplicated here)
- **Run type:** `manual` (owner live in chat, not a dispatched routine)
- **⚑ Owner decisions needed:** E#28 (fleet-manager owner-queue, expires
  2026-07-14) — 3 undecided sub-items (Lumen Drift go/no-go, pokemon
  playtest verdicts, gba Track B concept pick) + 2 confirmable
  recommendations (routine posture, websites cutover); `superbot-next` #317
  needs an owner/coordinator merge decision (clean+green but content-judgment
  ambiguous per this session's account); full owner-only list (Settings
  toggles, PATs, product/creative/financial calls) delivered in-chat.
- **⚑ Owner manual steps:** enable "Automatically delete head branches" in
  Settings fleet-wide (stops future branch pileup at the source); the
  ~1,270-branch existing backlog needs either the owner's own git
  credentials or an elevated-scope session to actually delete.
- **⚑ Self-initiated:** none — this was the owner's own explicit,
  live-chat-directed task, not an unprompted idea promotion.
- **↪ Next:** owner resolves E#28 + the `superbot-next` #317 call; a future
  session verifies and rolls out the auto-merge-enabler PAT/token swap
  (this session's idea, above) fleet-wide; a future session (with real
  delete-ref scope, or the owner directly) clears the ~1,270-branch backlog.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 43 (fleet-wide, across 19 repos other than `superbot`'s own code work) |
| CI-red rounds | 2 (`gba-homebrew` #135/#136 append-only rejection; `trading-strategy` #124 badge-taxonomy rejection — both fixed/resolved same session) |
| Repo-rule trips | 2 (the same two CI gate rejections above — both were the gate correctly doing its job, not a bug) |
| New ideas contributed | 1 (Q-0089, above) |
| Ideas groomed | 0 (capacity this session went entirely to the fleet sweep itself, an owner-directed task, not backlog grooming) |
