# Session — 2026-07-12 (part 2) — sign-in live, toggles verified, court-spam incident, fleet sweep

> **Status:** `complete`
> **Branch:** `claude/session-close-part2-2026-07-12` · continuation of #2043 (merged) in the same owner-live chat.
> **Venue:** owner-live chat (remote container). **📊 Model:** Fable 5 (Claude 5 family).

## Delivered after #2043 merged (all cross-repo work merged in its own repo)

1. **Mineverse OAuth reuse (owner-decided):** dashboard Discord app id+secret copied service-to-service
   → `auth_configured: true`. 2. **Both Actions toggles live-verified** (owner clicked; dispatches green;
   roster self-landed gens #17/#18) → roster bridge deleted, queue items resolved (fm #127/#132).
3. **Owner completed the redirect click; first sign-in failed** → root-caused live: **Cloudflare 403s
   urllib's default User-Agent on discord.com** (curl UA 200 vs python UA 403, same endpoint) → fixed in
   **mineverse #45** (UA header + server-side error logging), auto-deployed, **owner-verified full
   sign-in** (~20:50 local) → OQ-MINEVERSE-ENV-VARS RESOLVED (fm #136). 4. **My wrong queue item struck**
   (owner screenshot: Railway app had all-repos all along; failures were the missing Dockerfile; fm #134).
5. **"court"-spam incident:** websites chat flooded by stacked pacemaker ticks (one session had 4 pending
   identical wakes) → surplus pruned live + redundant bake bridge deleted + **ORDER 020 amended with the
   TICK PILE-UP signature** (fm #137). 6. **ORDER 021** (web-presence directory) + **ORDER 022** (websites
   deltas) delivered (fm #128/#130); the seat executed 019/021/022 same evening. 7. **Fleet sweep** (close):
   34 open PRs account-wide — 16 superbot-next (merge-wall backlog), 5 fleet-manager (incl. #121/#122
   owner-review consolidation/seat-reset plans), 2 substrate-kit pin-path (ratify-by-design), rest small.
   Full disposition: the next-session brief.

## Session enders

- **💡 Session idea (Q-0089):** *serve the fleet's canonical prompts/instructions from the control
  website* (versioned prompt-library pages with copy buttons + a "deployed-vs-canonical" drift check per
  seat) — the owner independently asked for exactly this; the reboot brief makes it the mechanism. New
  bit vs the existing prompt-library page: making the website THE paste source (not raw GitHub), with
  per-seat assembled bodies and version stamps the seats can self-quote for drift checks.
- **⟲ Previous-session review (Q-0102):** part 1 (this same chat, #2043) executed the owner queue but
  twice **mis-diagnosed walls** (Railway app access; "2 portal steps" when one secret was reusable) —
  both corrected only because the owner pushed back with ground truth. Improvement: before filing ANY
  owner-queue item, run the cheapest disconfirming probe (the deployments timeline / a vars listing would
  have killed both errors in one call); "verify the wall before parking the click" is now in the item-38
  strike note + capabilities lesson.
- **📄 Doc audit (Q-0104):** every conclusion has a durable home — fm owner-queue (resolutions + strikes),
  fm control/inbox (ORDER 019–022 + amendments), mineverse cards (#44/#45), capabilities.md (rescue venue
  + UA lesson), this card + the brief (`docs/owner/next-session-brief-2026-07-13.md`). current-state top
  refreshed; ledger checked pre-push.
- **⚑ Self-initiated (Q-0172):** the UA-fix PR (prerequisite of the verified sign-in goal), the tick
  pruning + ORDER 020 amendment (incident response), the queue strikes (drift-on-sight). Everything else
  owner-directed or owner-approved by name.
- **🛠 Friction → guard (Q-0194):** the pile-up class → ORDER 020 detection signature (enforcing, runs
  every manager wake); the mis-diagnosis class → the disconfirming-probe lesson recorded in the queue
  strike + capabilities (doc-level; a checker isn't cheap here — judgment rule, flagged for the kit's
  CONSTITUTION next release).
