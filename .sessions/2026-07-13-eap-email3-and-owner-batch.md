# 2026-07-13 — EAP email-3 send-ready + owner action/question batch

> **Status:** `complete`
> **Branch:** `claude/eap-email3-and-owner-batch` (restarted from main)
> **📊 Model:** Opus 4.8
> **Venue:** owner-live chat, remote container (hub repo)

## What happened

Owner is heading back to work — today is likely his last active-management day for a while;
game testing spreads across the week. His ask reframed the goal: **don't finalize decisions;
make sure a LOT gets built so he has a review backlog**, plus "work on the email for a while"
and give him a clear do-now list + a batch of answerable questions.

**Shipped:** upgraded [`docs/eap/anthropic-email-3-draft-2026-07-13.md`](../docs/eap/anthropic-email-3-draft-2026-07-13.md)
from probe-dependent first draft → **send-ready**: Part 2 evidence filled with the verified
figures from this morning's night review (51/51 parity, 18 hands-free idea→verdict cycles,
~215k words prose + 0-promoted trading null, 6 game builds, 41 website PRs, zero seat deaths
through a real scheduler wobble), a "send in 5 minutes" header, and the 7 probes reframed as
*optional* sharpeners (owner won't have probe time). Plus (in chat) the two lists he asked
for — the self-merge-settings clicks (the multiplier that keeps the fleet building while he's
away) and the batchable direction questions with recommendations.

## Strategy note (why self-merge settings are the #1 do-now)

His goal = "a lot gets built while I'm away." The multiplier is letting seats **self-land**:
every repo without auto-merge/required-checks parks its PRs waiting for him (babysitting);
turning those settings on converts the whole fleet into a continuous build engine that
produces his review backlog with zero owner presence. So the do-now list leads with the
settings clicks (B#49/B#50/B#51 + superbot-next merge-queue + trading/mineverse), not the
review-later decisions.

## ⚑ Self-initiated (Q-0172)

None — owner-directed. Email + lists are the deliverable.

## 💡 Session idea (Q-0089)

**A "self-land readiness" fleet check.** One script that, per repo, reports whether
auto-merge + a required check are configured (the precondition for a seat to build
unattended) — so "which lanes still park PRs on the owner?" is a one-command answer instead
of a queue-archaeology task. It directly serves the build-while-away goal and would keep the
settings backlog visible. Dedup: no existing idea covers self-land-readiness auditing (the
owner-queue tracks the individual asks, not the rollup). Routes to fleet-manager/websites.

## ⟲ Previous-session review (Q-0102)

The control-plane review (#2070) landed clean (Codex found no issues) and pre-empted the
docs-reachability trip that bit the prior two sessions — the "home the doc before push"
lesson finally stuck. Good. **System improvement:** three sessions in a row hand-assembled
close-outs and I only stopped tripping the orphan check by manually remembering; that
recurring near-miss is exactly what the flagged ender-recital / pre-commit-reachability guard
would enforce. It's now been surfaced 3×; worth building next time a hub session has capacity.

## Docs audit (Q-0104)

- Email draft is in `docs/eap/` (an existing tree); no new orphan doc created this session
  (the deliverable is an edit + chat lists). `check_docs`/gate green pre-push (real exit
  codes, the #2066 lesson).
- Telemetry row appended (Q-0194, opus-4.8). No claim file left (single-commit fast turn).
- Nothing valuable chat-only: the email is committed; the two lists are operational guidance
  for the owner's immediate use (the durable owner-action source stays the fm owner-queue).
